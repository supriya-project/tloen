import abc
import logging
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Set, Type, Union
from uuid import UUID, uuid4

from supriya.enums import AddAction, CalculationRate
from supriya.typing import Default

import tloen.domain  # noqa
from tloen.midi import NoteOffMessage

from .bases import (
    Allocatable,
    AllocatableContainer,
    Container,
    Mixer,
    Performable,
)
from .clips import Clip, ClipContainer
from .devices import DeviceObject
from .parameters import BusParameter, Float, ParameterGroup, ParameterObject
from .sends import Receive, Send, Target
from .slots import ClipLaunched, Scene, Slot
from .synthdefs import build_patch_synthdef, build_peak_rms_synthdef

logger = logging.getLogger("tloen.domain")


class TrackObject(Allocatable, Performable):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, uuid=None):
        Allocatable.__init__(self, channel_count=channel_count, name=name)
        Performable.__init__(self)
        self._parameter_group = ParameterGroup()
        self._parameters: Dict[str, ParameterObject] = {}
        self._add_parameter(
            BusParameter(
                is_builtin=True,
                name="gain",
                spec=Float(minimum=-96, maximum=6.0, default=0.0),
            ),
        )
        self._uuid = uuid or uuid4()
        self._peak_levels = {}
        self._rms_levels = {}
        self._soloed_tracks: Set[TrackObject] = set()
        self._devices = AllocatableContainer(
            "input_levels", AddAction.ADD_AFTER, label="Devices"
        )
        self._postfader_sends = AllocatableContainer(
            "output", AddAction.ADD_AFTER, label="PostFaderSends"
        )
        self._prefader_sends = AllocatableContainer(
            "output", AddAction.ADD_BEFORE, label="PreFaderSends"
        )
        self._receive_target = Target(label="ReceiveTarget")
        self._receives = AllocatableContainer(
            "node",
            AddAction.ADD_AFTER,
            label="Receives",
            target_node_parent=self._parameter_group,
        )
        self._send_target = Target(label="SendTarget")
        self._mutate(
            slice(None),
            [
                self._parameter_group,
                self._send_target,
                self._receives,
                self._devices,
                self._prefader_sends,
                self._postfader_sends,
                self._receive_target,
            ],
        )

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} [{node_proxy_id}] {self.uuid}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _activate(self):
        Allocatable._activate(self)
        if not self.provider:
            return
        self.node_proxies["output"]["active"] = 1

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        channel_count = self.effective_channel_count
        self._node_proxies["node"] = provider.add_group(
            target_node=target_node, add_action=add_action, name=self.label
        )
        self._allocate_audio_buses(provider, channel_count)
        self._allocate_synths(
            provider,
            channel_count,
            input_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
            input_levels_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
            prefader_levels_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
            output_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
            postfader_levels_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
        )
        self._allocate_osc_callbacks(provider)

    def _allocate_audio_buses(self, provider, channel_count):
        self._audio_bus_proxies["input"] = provider.add_bus_group(
            calculation_rate=CalculationRate.AUDIO,
            channel_count=self.effective_channel_count,
        )
        self._audio_bus_proxies["output"] = provider.add_bus_group(
            calculation_rate=CalculationRate.AUDIO,
            channel_count=self.effective_channel_count,
        )

    def _allocate_synths(
        self,
        provider,
        channel_count,
        *,
        input_pair=None,
        input_levels_pair=None,
        prefader_levels_pair=None,
        output_pair=None,
        postfader_levels_pair=None,
    ):
        input_target, input_action = input_pair
        self._node_proxies["input"] = provider.add_synth(
            add_action=input_action,
            in_=self._audio_bus_proxies["input"],
            out=self._audio_bus_proxies["output"],
            synthdef=build_patch_synthdef(
                channel_count, channel_count, feedback=True, gain=True
            ),
            target_node=input_target,
            name="Input",
        )
        input_levels_target, input_levels_action = input_levels_pair
        self._node_proxies["input_levels"] = provider.add_synth(
            add_action=input_levels_action,
            out=self._audio_bus_proxies["output"],
            synthdef=build_peak_rms_synthdef(channel_count),
            target_node=input_levels_target,
            name="InputLevels",
        )
        prefader_levels_target, prefader_levels_action = prefader_levels_pair
        self._node_proxies["prefader_levels"] = provider.add_synth(
            add_action=prefader_levels_action,
            out=self._audio_bus_proxies["output"],
            synthdef=build_peak_rms_synthdef(channel_count),
            target_node=prefader_levels_target,
            name="PrefaderLevels",
        )
        output_target, output_action = output_pair
        self._node_proxies["output"] = provider.add_synth(
            active=self.is_active,
            add_action=output_action,
            gain=self.parameters["gain"].bus_proxy,
            in_=self._audio_bus_proxies["output"],
            out=self._audio_bus_proxies["output"],
            synthdef=build_patch_synthdef(
                channel_count,
                channel_count,
                gain=True,
                hard_gate=True,
                replace_out=True,
            ),
            target_node=output_target,
            name="Output",
        )
        postfader_levels_target, postfader_levels_action = postfader_levels_pair
        self._node_proxies["postfader_levels"] = provider.add_synth(
            add_action=postfader_levels_action,
            out=self._audio_bus_proxies["output"],
            synthdef=build_peak_rms_synthdef(channel_count),
            target_node=postfader_levels_target,
            name="PostfaderLevels",
        )

    def _allocate_osc_callbacks(self, provider):
        self._osc_callback_proxies["input"] = provider.register_osc_callback(
            pattern=["/levels", self.node_proxies["input_levels"].identifier],
            procedure=lambda osc_message: self._update_levels("input", osc_message),
        )
        self._osc_callback_proxies["prefader"] = provider.register_osc_callback(
            pattern=["/levels", self.node_proxies["prefader_levels"].identifier],
            procedure=lambda osc_message: self._update_levels("prefader", osc_message),
        )
        self._osc_callback_proxies["postfader"] = provider.register_osc_callback(
            pattern=["/levels", self.node_proxies["postfader_levels"].identifier],
            procedure=lambda osc_message: self._update_levels("postfader", osc_message),
        )

    def _deactivate(self):
        Allocatable._deactivate(self)
        if not self.provider:
            return
        self.node_proxies["output"]["active"] = 0

    def _perform_input(self, moment, midi_messages):
        next_perform, midi_messages = Performable._perform_input(
            self, moment, midi_messages,
        )
        if self.devices:
            next_performer = self.devices[0]._perform_input
        yield next_performer, midi_messages

    def _reallocate(self, difference):
        channel_count = self.effective_channel_count
        # buses
        input_bus_group = self._audio_bus_proxies.pop("input")
        output_bus_group = self._audio_bus_proxies.pop("output")
        for bus_group in [input_bus_group, output_bus_group]:
            bus_group.free()
        self._allocate_audio_buses(self.provider, channel_count)
        # synths
        input_synth = self._node_proxies.pop("input")
        input_levels_synth = self._node_proxies.pop("input_levels")
        prefader_levels_synth = self._node_proxies.pop("prefader_levels")
        output_synth = self._node_proxies.pop("output")
        postfader_levels_synth = self._node_proxies.pop("postfader_levels")
        self._allocate_synths(
            self.provider,
            self.effective_channel_count,
            input_pair=(input_synth, AddAction.ADD_AFTER),
            input_levels_pair=(input_levels_synth, AddAction.ADD_AFTER),
            prefader_levels_pair=(prefader_levels_synth, AddAction.ADD_AFTER),
            output_pair=(output_synth, AddAction.ADD_AFTER),
            postfader_levels_pair=(postfader_levels_synth, AddAction.ADD_AFTER),
        )
        for synth in [
            input_synth,
            input_levels_synth,
            prefader_levels_synth,
            output_synth,
            postfader_levels_synth,
        ]:
            synth.free()
        # osc callbacks
        input_callback = self._osc_callback_proxies.pop("input")
        prefader_callback = self._osc_callback_proxies.pop("prefader")
        postfader_callback = self._osc_callback_proxies.pop("postfader")
        for osc_callback in [input_callback, prefader_callback, postfader_callback]:
            osc_callback.unregister()
        self._allocate_osc_callbacks(self.provider)

    def _reconcile_dependents(self):
        for send in sorted(self.send_target._dependencies, key=lambda x: x.graph_order):
            send._reconcile()

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        devices = []
        sends = []
        for send in self.prefader_sends:
            sends.append(str(send.uuid))
            send_entities = send._serialize()
            send_entities[0]["spec"]["position"] = "prefader"
            auxiliary_entities.append(send_entities[0])
            auxiliary_entities.extend(send_entities[1])
        for send in self.postfader_sends:
            sends.append(str(send.uuid))
            send_entities = send._serialize()
            send_entities[0]["spec"]["position"] = "postfader"
            auxiliary_entities.append(send_entities[0])
            auxiliary_entities.extend(send_entities[1])
        for device in self.devices:
            devices.append(str(device.uuid))
            device_entities = device._serialize()
            auxiliary_entities.append(device_entities[0])
            auxiliary_entities.extend(device_entities[1])
        serialized["spec"].update(devices=devices, sends=sends)
        return serialized, auxiliary_entities

    def _set_active(self, is_active):
        if self._is_muted != is_active:
            return
        self._is_muted = not is_active
        self._update_activation(self)

    def _update_levels(self, key, osc_message):
        levels = list(osc_message.contents[2:])
        peak, rms = [], []
        while levels:
            peak.append(levels.pop(0))
            rms.append(levels.pop(0))
        self._peak_levels[key] = tuple(peak)
        self._rms_levels[key] = tuple(rms)

    ### PUBLIC METHODS ###

    async def add_device(self, device_class: Type[DeviceObject], **kwargs):
        async with self.lock([self]):
            device = device_class(**kwargs)
            self.devices._append(device)
            return device

    async def add_send(self, target, postfader=True):
        async with self.lock([self]):
            send = Send(target)
            if postfader:
                self.postfader_sends._append(send)
            else:
                self.prefader_sends._append(send)
            if send.effective_target is not None:
                send.effective_target.send_target._dependencies.add(send)
            return send

    async def add_receive(self, source):
        async with self.lock([self]):
            receive = Receive(source)
            self.receives._append(receive)
            if receive.effective_source is not None:
                receive.effective_source.receive_target._dependencies.add(receive)
            return receive

    async def remove_devices(self, *devices: DeviceObject):
        async with self.lock([self, *devices]):
            if not all(device in self.devices for device in devices):
                raise ValueError(devices)
            for device in devices:
                self.devices._remove(device)

    async def remove_sends(self, *sends: Send):
        async with self.lock([self, *sends]):
            if not all(
                send in self.prefader_sends or send in self.postfader_sends
                for send in sends
            ):
                raise ValueError(sends)
            for send in sends:
                if send in self.prefader_sends:
                    self.prefader_sends._remove(send)
                else:
                    self.postfader_sends._remove(send)
                if send.effective_target is not None:
                    send.effective_target.send_target._dependencies.remove(send)

    async def set_channel_count(self, channel_count: Optional[int]):
        async with self.lock([self]):
            if channel_count is not None:
                assert 1 <= channel_count <= 8
                channel_count = int(channel_count)
            self._set(channel_count=channel_count)

    def set_input(self, target: Union[None, Default, "TrackObject", str]):
        pass

    def set_output(self, target: Union[None, Default, "TrackObject", str]):
        pass

    ### PUBLIC PROPERTIES ###

    @property
    def devices(self) -> AllocatableContainer:
        return self._devices

    @property
    def mixer(self) -> Optional[Mixer]:
        for parent in self.parentage:
            if isinstance(parent, Mixer):
                return parent
        return None

    @property
    def parameters(self) -> Mapping[str, ParameterObject]:
        return MappingProxyType(self._parameters)

    @property
    def peak_levels(self):
        return MappingProxyType(self._peak_levels)

    @property
    def rms_levels(self):
        return MappingProxyType(self._rms_levels)

    @property
    def prefader_sends(self) -> AllocatableContainer:
        return self._prefader_sends

    @property
    def postfader_sends(self) -> AllocatableContainer:
        return self._postfader_sends

    @property
    def receive_target(self) -> Target:
        return self._receive_target

    @property
    def receives(self) -> AllocatableContainer:
        return self._receives

    @property
    def send_target(self) -> Target:
        return self._send_target

    @property
    def uuid(self) -> UUID:
        return self._uuid


class CueTrack(TrackObject):

    ### INITIALIZER ###

    def __init__(self, *, uuid=None):
        TrackObject.__init__(self, channel_count=2, uuid=uuid)
        self._add_parameter(
            BusParameter(
                is_builtin=True,
                name="mix",
                spec=Float(minimum=0.0, maximum=1.0, default=0.0),
            ),
        )

    ### PRIVATE METHODS ###

    @classmethod
    async def _deserialize(cls, data, application) -> bool:
        track = cls(uuid=UUID(data["meta"]["uuid"]))
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry[parent_uuid]
        parent._replace(parent.cue_track, track)
        parent._cue_track = track
        return False

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        serialized["meta"]["parent"] = str(self.parent.uuid)
        return serialized, auxiliary_entities


class MasterTrack(TrackObject):

    ### INITIALIZER ###

    def __init__(self, *, uuid=None):
        TrackObject.__init__(self, uuid=uuid)

    ### PRIVATE METHODS ###

    @classmethod
    async def _deserialize(cls, data, application) -> bool:
        track = cls(uuid=UUID(data["meta"]["uuid"]))
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry[parent_uuid]
        parent._replace(parent.master_track, track)
        parent._master_track = track
        return False

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        serialized["meta"]["parent"] = str(self.parent.uuid)
        return serialized, auxiliary_entities


class UserTrackObject(TrackObject):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, uuid=None):
        TrackObject.__init__(self, channel_count=channel_count, name=name, uuid=uuid)
        self._is_cued = False
        self._is_muted = False
        self._is_soloed = False
        self._add_parameter(
            BusParameter(
                is_builtin=True,
                name="panning",
                spec=Float(minimum=-1.0, maximum=1.0, default=0),
            ),
        )

    ### PRIVATE METHODS ###

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        serialized["spec"].update(
            is_cued=self.is_cued or None,
            is_muted=self.is_muted or None,
            is_soloed=self.is_soloed or None,
        )
        return serialized, auxiliary_entities

    ### PUBLIC METHODS ###

    async def cue(self):
        async with self.lock([self]):
            pass

    async def delete(self):
        async with self.lock([self]):
            if self.parent is None:
                raise ValueError
            self.parent._remove(self)

    async def duplicate(self):
        async with self.lock([self]):
            pass

    async def mute(self):
        async with self.lock([self]):
            self._set_active(False)

    @abc.abstractmethod
    async def solo(self, exclusive=True):
        raise NotImplementedError

    async def uncue(self):
        async with self.lock([self]):
            pass

    async def unmute(self):
        async with self.lock([self]):
            self._set_active(True)

    @abc.abstractmethod
    async def unsolo(self, exclusive=False):
        raise NotImplementedError

    ### PUBLIC PROPERTIES ###

    @property
    def is_cued(self) -> bool:
        return self._is_cued

    @property
    def is_muted(self) -> bool:
        return self._is_muted

    @property
    def is_soloed(self) -> bool:
        return self._is_soloed


class Track(UserTrackObject):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, uuid=None):
        UserTrackObject.__init__(
            self, channel_count=channel_count, name=name, uuid=uuid
        )
        self._active_slot_index: Optional[int] = None
        self._clip_launch_event_id: Optional[int] = None
        self._clip_perform_event_id: Optional[int] = None
        self._pending_slot_index: Optional[int] = None
        self._clips = ClipContainer(label="Clips")
        self._slots = Container(label="Slots")
        self._tracks = TrackContainer("input", AddAction.ADD_AFTER, label="SubTracks")
        self._mutate(slice(1, 1), [self._clips, self._slots, self._tracks])

    ### PRIVATE METHODS ###

    def _applicate(self, new_application):
        UserTrackObject._applicate(self, new_application)
        while len(new_application.scenes) < len(self.slots):
            new_application.scenes._append(Scene())
        while len(self.slots) < len(new_application.scenes):
            self.slots._append(Slot())

    def _cleanup(self):
        Track._update_activation(self)

    async def _clip_launch_callback(self, clock_context):
        self._debug_tree(
            self,
            "Launch/CB",
            suffix="{} {}".format(
                self._pending_slot_index, clock_context.desired_moment.offset
            ),
        )
        self._clip_launch_event_id = None
        # if a clip is active, perform note offs
        if self._active_slot_index is not None:
            midi_messages = [
                NoteOffMessage(pitch=pitch) for pitch in self._input_pitches
            ]
            if midi_messages:
                await self.perform(midi_messages, moment=clock_context.desired_moment)
            self.slots[self._active_slot_index].clip._is_playing = False
            self.slots[self._active_slot_index].clip._start_delta = 0.0
        # if pending clip is null-ish, null out variables
        if (
            self._pending_slot_index is None
            or (
                self._pending_slot_index is not None
                and not (0 <= self._pending_slot_index < len(self.slots))
            )
            or self.slots[self._pending_slot_index].clip is None
        ):
            self._active_slot_index = None
            self._pending_slot_index = None
            self._debug_tree(self, "Launch/CB", suffix="Bailing")
            return
        # set variables to new clip
        self._active_slot_index = self._pending_slot_index
        self.slots[self._active_slot_index].clip._is_playing = True
        self.slots[
            self._active_slot_index
        ].clip._start_delta = clock_context.desired_moment.offset
        # schedule perform callback
        if self._clip_perform_event_id is not None:
            await self.transport.cancel(self._clip_perform_event_id)
        self._clip_perform_event_id = await self.transport.schedule(
            self._clip_perform_callback,
            schedule_at=clock_context.desired_moment.offset,
            event_type=self.transport.EventType.CLIP_PERFORM,
        )
        self.application.pubsub.publish(
            ClipLaunched(clip_uuid=self.slots[self._active_slot_index].clip.uuid),
        )

    async def _clip_perform_callback(self, clock_context):
        self._debug_tree(self, "Perform/CB", suffix=str(self._active_slot_index))
        if self._active_slot_index is None:
            return None
        clip = self.slots[self._active_slot_index].clip
        note_moment = clip.at(
            clock_context.desired_moment.offset, start_delta=clip._start_delta
        )
        input_pitches = sorted(self._input_pitches)
        midi_messages = []
        for midi_message in note_moment.note_off_messages:
            midi_messages.append(midi_message)
            if midi_message.pitch in input_pitches:
                input_pitches.remove(midi_message.pitch)
        overlap_pitches = set(_.pitch for _ in note_moment.overlap_notes or [])
        for input_pitch in input_pitches:
            if input_pitch not in overlap_pitches:
                midi_messages.append(NoteOffMessage(pitch=input_pitch))
        midi_messages.extend(note_moment.note_on_messages)
        if midi_messages:
            await self.perform(midi_messages, clock_context.desired_moment)
        if note_moment.next_offset is None:
            return None
        return note_moment.next_offset - clock_context.desired_moment.offset

    @classmethod
    async def _deserialize(cls, data, application) -> bool:
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry.get(parent_uuid)
        if parent is None:
            return True
        track = cls(
            channel_count=data["spec"].get("channel_count"),
            name=data["meta"].get("name"),
            uuid=UUID(data["meta"]["uuid"]),
        )
        parent.tracks._append(track)
        if data["spec"].get("is_cued"):
            await track.cue()
        if data["spec"].get("is_muted"):
            await track.mute()
        if data["spec"].get("is_soloed"):
            await track.solo(exclusive=False)
        track.slots._mutate(slice(None, None), [])
        return False

    async def _fire(self, slot_index, quantization=None):
        if not self.application:
            return
        self._debug_tree(self, "Firing", suffix=str(slot_index))
        self._pending_slot_index = slot_index
        transport = self.transport
        await transport.cancel(self._clip_launch_event_id)
        self._clip_launch_event_id = await transport.cue(
            self._clip_launch_callback,
            # TODO: Get default quantization from transport itself
            quantization=quantization or "1M",
            event_type=transport.EventType.CLIP_LAUNCH,
        )
        if not transport.is_running:
            await transport.start()

    @classmethod
    def _recurse_activation(
        cls,
        track,
        any_tracks_are_soloed=False,
        tree_is_muted=False,
        tree_is_soloed=False,
    ):
        to_activate, to_deactivate = [], []
        should_mute = bool(tree_is_muted or track.is_muted)
        should_solo = bool(tree_is_soloed or track._soloed_tracks)
        active = True
        if any_tracks_are_soloed:
            active = should_solo
        if should_mute:
            active = False
        if not track.is_active and active:
            to_activate.append(track)
        elif track.is_active and not active:
            to_deactivate.append(track)
        for child in track.tracks:
            result = cls._recurse_activation(
                child,
                any_tracks_are_soloed=any_tracks_are_soloed,
                tree_is_muted=should_mute,
                tree_is_soloed=tree_is_soloed or track.is_soloed,
            )
            to_activate.extend(result[0])
            to_deactivate.extend(result[1])
        return to_activate, to_deactivate

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        serialized["spec"]["slots"] = []
        serialized["spec"]["tracks"] = []
        for slot in self.slots:
            serialized["spec"]["slots"].append(str(slot.uuid))
            slot_entities = slot._serialize()
            auxiliary_entities.append(slot_entities[0])
            auxiliary_entities.extend(slot_entities[1])
        for track in self.tracks:
            serialized["spec"]["tracks"].append(str(track.uuid))
            track_entities = track._serialize()
            auxiliary_entities.append(track_entities[0])
            auxiliary_entities.extend(track_entities[1])
        return serialized, auxiliary_entities

    def _set_parent(self, new_parent):
        from .contexts import Context

        if self.is_soloed:
            for node in self.parentage:
                if (
                    isinstance(node, (UserTrackObject, Context))
                    and self in node._soloed_tracks
                ):
                    node._soloed_tracks.remove(self)
        UserTrackObject._set_parent(self, new_parent)
        if self.is_soloed:
            for node in self.parentage:
                if isinstance(node, (UserTrackObject, Context)):
                    node._soloed_tracks.add(self)

    @classmethod
    def _update_activation(cls, object_):
        from .contexts import Context

        parentage = [
            x for x in object_.parentage if isinstance(x, (UserTrackObject, Context))
        ]
        any_tracks_are_soloed = bool(parentage[-1]._soloed_tracks)
        if isinstance(parentage[-1], Context):
            to_activate, to_deactivate = [], []
            for track in parentage[-1].tracks:
                result = Track._recurse_activation(
                    track, any_tracks_are_soloed=any_tracks_are_soloed
                )
                to_activate.extend(result[0])
                to_deactivate.extend(result[1])
        else:
            to_activate, to_deactivate = Track._recurse_activation(
                parentage[-1], any_tracks_are_soloed=any_tracks_are_soloed
            )
        for track in to_activate:
            track._activate()
        for track in to_deactivate:
            track._deactivate()

    ### PUBLIC METHODS ###

    async def add_track(self, *, name=None):
        async with self.lock([self]):
            track = Track(name=name)
            await track.add_send(Default())
            self._tracks._append(track)
            return track

    @classmethod
    async def group(cls, tracks, *, name=None):
        async with cls.lock(tracks):
            group_track = Track(name=name)
            if tracks[0].parent:
                index = tracks[0].parent.index(tracks[0])
                tracks[0].parent._mutate(slice(index, index), [group_track])
                await group_track.add_send(Default())
            group_track.tracks._mutate(slice(None), tracks)
            return group_track

    async def insert_clip(self, *, from_: float, to: float, **kwargs) -> Clip:
        if to <= from_:
            raise ValueError
        stop_marker = kwargs.pop("stop_marker", to - from_)
        clip = Clip(
            start_offset=from_, stop_offset=to, stop_marker=stop_marker, **kwargs
        )
        self._clips._add_clips(clip)
        return clip

    async def move(self, container, position):
        async with self.lock([self, container]):
            container.tracks._mutate(slice(position, position), [self])

    async def remove_tracks(self, *tracks: "Track"):
        async with self.lock([self, *tracks]):
            if not all(track in self.tracks for track in tracks):
                raise ValueError
            for track in tracks:
                self._tracks._remove(track)

    async def solo(self, exclusive=True):
        from .contexts import Context

        async with self.lock([self]):
            if self.is_soloed:
                return
            parentage = [
                x for x in self.parentage if isinstance(x, (UserTrackObject, Context))
            ]
            self._is_soloed = True
            if exclusive:
                for track in tuple(parentage[-1]._soloed_tracks):
                    track._is_soloed = False
                    for node in track.parentage:
                        if isinstance(node, (UserTrackObject, Context)):
                            node._soloed_tracks.remove(track)
            for node in parentage:
                node._soloed_tracks.add(self)
            self._update_activation(self)

    async def stop(self, quantization=None):
        await self._fire(None, quantization=quantization)

    async def ungroup(self):
        async with self.lock([self]):
            if self.parent:
                index = self.parent.index(self)
                self.parent._mutate(slice(index, index + 1), self.tracks[:])
            else:
                self.tracks._mutate(slice(None), [])

    async def unsolo(self, exclusive=False):
        from .contexts import Context

        async with self.lock([self]):
            if not self.is_soloed:
                return
            parentage = [
                x for x in self.parentage if isinstance(x, (UserTrackObject, Context))
            ]
            if exclusive:
                tracks = (self,)
            else:
                tracks = tuple(parentage[-1]._soloed_tracks)
            for track in tracks:
                track._is_soloed = False
                for node in track.parentage:
                    if isinstance(node, (UserTrackObject, Context)):
                        node._soloed_tracks.remove(track)
            self._update_activation(self)

    ### PUBLIC PROPERTIES ###

    @property
    def clips(self) -> Container:
        return self._clips

    @property
    def default_send_target(self):
        for parent in self.parentage[1:]:
            if hasattr(parent, "tracks"):
                if hasattr(parent, "master_track"):
                    return parent.master_track
                return parent

    @property
    def slots(self):
        return self._slots

    @property
    def tracks(self) -> "TrackContainer":
        return self._tracks


class TrackContainer(AllocatableContainer):
    def _collect_for_cleanup(self, new_items, old_items):
        items = set()
        for item in [self] + new_items:
            mixer = item.mixer or item.root
            if mixer is not None:
                items.add(mixer)
        items.update(old_items)
        return items

    @property
    def mixer(self) -> Optional["tloen.domain.Context"]:
        for parent in self.parentage:
            if isinstance(parent, tloen.domain.Context):
                return parent
        return None
