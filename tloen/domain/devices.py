from typing import Callable, Dict, Optional, Set, Type, Union
from uuid import UUID, uuid4

from supriya.enums import AddAction, CalculationRate
from supriya.synthdefs import SynthDef, SynthDefFactory

from tloen.midi import MidiMessage, NoteOffMessage, NoteOnMessage

from .bases import Allocatable, Performable
from .parameters import (
    Boolean,
    CallbackParameter,
    ParameterGroup,
    ParameterObject,
)
from .sends import Patch
from .synthdefs import build_patch_synthdef


class DeviceIn(Patch):

    ### PUBLIC METHODS ###

    @classmethod
    def build_synthdef(
        cls,
        source_channel_count,
        target_channel_count,
        *,
        feedback=False,
        calculation_rate=CalculationRate.AUDIO,
    ):
        return build_patch_synthdef(
            source_channel_count,
            target_channel_count,
            calculation_rate=calculation_rate,
            replace_out=True,
        )

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} [{node_proxy_id}]",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PUBLIC PROPERTIES ###

    @property
    def source(self):
        return self.parent.track_object if self.parent is not None else None

    @property
    def source_anchor(self):
        return self.source

    @property
    def source_bus(self):
        source = self.effective_source
        return source.audio_bus_proxies.get("output") if source is not None else None

    @property
    def target_bus(self):
        target = self.effective_target
        if target is not None:
            return target.audio_bus_proxies.get("output")
        return None

    @property
    def target(self):
        return self.parent

    @property
    def target_anchor(self):
        return self.target


class DeviceOut(Patch):

    ### PRIVATE METHODS ###

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        self._allocate_synths(self.parent.node_proxy, AddAction.ADD_TO_TAIL)

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} [{node_proxy_id}]",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PUBLIC METHODS ###

    @classmethod
    def build_synthdef(
        cls,
        source_channel_count,
        target_channel_count,
        *,
        feedback=False,
        calculation_rate=CalculationRate.AUDIO,
    ):
        return build_patch_synthdef(
            source_channel_count,
            target_channel_count,
            calculation_rate=calculation_rate,
            mix_out=True,
            hard_gate=True,
        )

    ### PUBLIC PROPERTIES ###

    @property
    def source(self):
        return self.parent

    @property
    def source_anchor(self):
        return self.source

    @property
    def source_bus(self):
        source = self.effective_source
        if source is not None:
            return source.audio_bus_proxies.get("output")
        return None

    @property
    def target(self):
        return self.parent.track_object if self.parent is not None else None

    @property
    def target_anchor(self):
        return self.target

    @property
    def target_bus(self):
        target = self.effective_target
        return target.audio_bus_proxies.get("output") if target is not None else None


class DeviceObject(Allocatable, Performable):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, parameters=None, uuid=None):
        Allocatable.__init__(self, channel_count=channel_count, name=name)
        Performable.__init__(self)
        self._parameter_group = ParameterGroup()
        self._parameters: Dict[str, ParameterObject] = {}
        self._add_parameter(
            CallbackParameter(
                callback=lambda client, value: client._set_active(value),
                is_builtin=True,
                name="active",
                spec=Boolean(),
            ),
        )
        for parameter in (parameters or {}).values():
            self._add_parameter(parameter)
        self._uuid = uuid or uuid4()
        self._input_notes: Set[float] = set()
        self._output_notes: Set[float] = set()
        self._event_handlers: Dict[Type[MidiMessage], Callable] = {
            NoteOnMessage: self._handle_note_on,
            NoteOffMessage: self._handle_note_off,
        }
        self._mutate(slice(None), [self._parameter_group])

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} [{node_proxy_id}]",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _handle_note_off(self, moment, midi_message):
        self._input_notes.remove(midi_message.pitch)
        return [midi_message]

    def _handle_note_on(self, moment, midi_message):
        result = []
        if midi_message.pitch in self._input_notes:
            result.extend(self._handle_note_off(moment, midi_message))
        self._input_notes.add(midi_message.pitch)
        result.append(midi_message)
        return result

    def _perform_input(self, moment, midi_messages):
        Performable._perform_input(self, moment, midi_messages)
        out_messages = []
        for message in midi_messages:
            event_handler = self._event_handlers.get(type(message))
            if not event_handler:
                out_messages.append(message)
                continue
            out_messages.extend(event_handler(moment, message))
        yield self._perform_output, out_messages

    def _set_active(self, is_active):
        if self.is_active == is_active:
            return

    ### PUBLIC METHODS ###

    async def activate(self):
        async with self.lock([self]):
            self._is_active = True

    async def deactivate(self):
        async with self.lock([self]):
            self._is_active = False

    @classmethod
    async def deserialize(cls, data, application) -> bool:
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry.get(parent_uuid)
        if parent is None:
            return True
        device = cls(name=data["meta"].get("name"), uuid=UUID(data["meta"]["uuid"]),)
        parent.devices._append(device)
        return False

    async def delete(self):
        async with self.lock([self]):
            if self.parent is None:
                raise ValueError
            self.parent._remove(self)

    def duplicate(self):
        pass

    @classmethod
    async def group(cls, devices):
        async with cls.lock(devices):
            pass

    async def move(self, container, position):
        async with self.lock([self, container]):
            container.devices._mutate(slice(position, position), [self])

    async def set_channel_count(self, channel_count: Optional[int]):
        async with self.lock([self]):
            if channel_count is not None:
                assert 1 <= channel_count <= 8
                channel_count = int(channel_count)
            self._set(channel_count=channel_count)

    ### PUBLIC PROPERTIES ###

    @property
    def is_active(self):
        return self.parameters["active"].value

    @property
    def parameters(self):
        return self._parameters

    @property
    def track_object(self):
        from .tracks import TrackObject

        for parent in self.parentage[1:]:
            if isinstance(parent, TrackObject):
                return parent
        return None

    @property
    def uuid(self) -> UUID:
        return self._uuid


class AllocatableDevice(DeviceObject):

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        buffer_map=None,
        name=None,
        parameter_map=None,
        parameters=None,
        synthdef: Union[SynthDef, SynthDefFactory] = None,
        synthdef_kwargs=None,
        uuid=None,
    ):
        DeviceObject.__init__(self, name=name, parameters=parameters, uuid=uuid)
        self._device_in = DeviceIn()
        self._device_out = DeviceOut()
        self._parameter_map = parameter_map or {}
        self._synthdef = synthdef
        self._synthdef_kwargs = dict(synthdef_kwargs or {})
        self._mutate(
            slice(None), [self._parameter_group, self._device_in, self._device_out]
        )

    ### PRIVATE METHODS ###

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        channel_count = self.effective_channel_count
        self._node_proxies["node"] = provider.add_group(
            target_node=target_node, add_action=add_action, name=self.label
        )
        self._node_proxies["parameters"] = provider.add_group(
            target_node=self.node_proxy,
            add_action=AddAction.ADD_TO_HEAD,
            name="Parameters",
        )
        self._node_proxies["body"] = provider.add_group(
            target_node=self.node_proxy, add_action=AddAction.ADD_TO_TAIL, name="Body"
        )
        self._allocate_audio_buses(provider, channel_count)
        self._allocate_synths(provider, self.effective_channel_count)

    def _allocate_synths(self, provider, channel_count):
        pass

    def _allocate_audio_buses(self, provider, channel_count):
        self._audio_bus_proxies["output"] = provider.add_bus_group(
            calculation_rate=CalculationRate.AUDIO, channel_count=channel_count
        )

    def _free_audio_buses(self):
        self._audio_bus_proxies.pop("output").free()

    def _reallocate(self, difference):
        channel_count = self.effective_channel_count
        self._free_audio_buses()
        self._allocate_audio_buses(self.provider, channel_count)

    ### PUBLIC PROPERTIES ###

    @property
    def device_in(self):
        return self._device_in

    @property
    def device_out(self):
        return self._device_out

    @property
    def synthdef(self) -> Union[SynthDef, SynthDefFactory]:
        return self._synthdef

    @property
    def synthdef_kwargs(self):
        return self._synthdef_kwargs
