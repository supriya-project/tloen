import dataclasses
from typing import Optional
from uuid import UUID

from supriya.enums import AddAction, CalculationRate
from supriya.typing import Default

import tloen.domain  # noqa
from tloen.midi import MidiMessage, NoteOffMessage, NoteOnMessage

from .bases import Allocatable, AllocatableContainer, Mixer, Performable
from .devices import DeviceObject
from .sends import Send, Target
from .synthdefs import build_patch_synthdef
from .tracks import UserTrackObject


@dataclasses.dataclass(frozen=True)
class Transfer:
    in_pitch: Optional[int] = None
    out_pitch: Optional[int] = None

    def __call__(self, midi_message: MidiMessage) -> Optional[MidiMessage]:
        if isinstance(midi_message, (NoteOnMessage, NoteOffMessage)):
            if self.in_pitch is None or self.in_pitch == midi_message.pitch:
                if self.out_pitch:
                    midi_message = dataclasses.replace(
                        midi_message, pitch=self.out_pitch,
                    )
                return midi_message
            else:
                return None
        return midi_message

    @classmethod
    async def deserialize(cls, data, application):
        return cls(
            in_pitch=data["spec"].get("in_pitch"),
            out_pitch=data["spec"].get("out_pitch"),
        )

    def serialize(self):
        serialized = {
            "kind": type(self).__name__,
            "spec": {"in_pitch": self.in_pitch, "out_pitch": self.out_pitch},
        }
        for mapping in [
            serialized.get("meta", {}),
            serialized.get("spec", {}),
            serialized,
        ]:
            for key in tuple(mapping):
                if not mapping[key]:
                    mapping.pop(key)
        return serialized


class Chain(UserTrackObject):
    def __init__(self, *, channel_count=None, name=None, transfer=None, uuid=None):
        UserTrackObject.__init__(
            self, channel_count=channel_count, name=name, uuid=uuid,
        )
        # how external notes are filtered / transformed into internal notes
        self._transfer = transfer or Transfer()

    ### PRIVATE METHODS ###

    def _cleanup(self):
        Chain._update_activation(self)

    def _perform_input(self, moment, midi_messages):
        next_performer, midi_messages = Performable._perform_input(
            self, moment, midi_messages,
        )
        if self.devices:
            next_performer = self.devices[0]._perform_input
        for message in midi_messages:
            out_message = self.transfer(message)
            if out_message is None:
                continue
            yield next_performer, [out_message]

    def _set_parent(self, new_parent):
        if self.is_soloed:
            mixer = self.mixer
            if mixer is not None:
                mixer._soloed_tracks.remove(self)
        UserTrackObject._set_parent(self, new_parent)
        if self.is_soloed:
            mixer = self.mixer
            if mixer is not None:
                mixer._soloed_tracks.add(self)

    @classmethod
    def _update_activation(cls, object_):
        parentage = []
        for x in object_.parentage:
            if isinstance(x, Chain):
                parentage.append(x)
            elif isinstance(x, RackDevice):
                parentage.append(x)
                break
        any_chains_are_soloed = bool(parentage[-1]._soloed_tracks)
        to_activate, to_deactivate = [], []
        if isinstance(parentage[-1], RackDevice):
            chains = parentage[-1].chains[:]
        else:
            chains = [object_]
        for chain in chains:
            should_mute = chain.is_muted
            should_solo = chain.is_soloed
            active = True
            if any_chains_are_soloed:
                active = should_solo
            if should_mute:
                active = False
            if not chain.is_active and active:
                to_activate.append(chain)
            elif chain.is_active and not active:
                to_deactivate.append(chain)
        for track in to_activate:
            track._activate()
        for track in to_deactivate:
            track._deactivate()

    ### PUBLIC METHODS ###

    @classmethod
    async def deserialize(cls, data, application) -> bool:
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry.get(parent_uuid)
        if parent is None:
            return True
        transfer = await Transfer.deserialize(data["spec"]["transfer"], application)
        chain = cls(
            channel_count=data["spec"].get("channel_count"),
            name=data["meta"].get("name"),
            transfer=transfer,
            uuid=UUID(data["meta"]["uuid"]),
        )
        parent.chains._append(chain)
        if data["spec"].get("is_cued"):
            await chain.cue()
        if data["spec"].get("is_muted"):
            await chain.mute()
        if data["spec"].get("is_soloed"):
            await chain.solo(exclusive=False)
        return False

    def serialize(self):
        serialized, auxiliary_entities = super().serialize()
        serialized.setdefault("spec", {}).update(transfer=self.transfer.serialize(),)
        return serialized, auxiliary_entities

    async def move(self, container, position):
        async with self.lock([self, container]):
            container.chains._mutate(slice(position, position), [self])

    async def solo(self, exclusive=True):
        async with self.lock([self]):
            if self.is_soloed:
                return
            mixer = self.mixer
            if mixer:
                if exclusive:
                    for chain in tuple(mixer._soloed_tracks):
                        chain._is_soloed = False
                        mixer._soloed_tracks.remove(chain)
                mixer._soloed_tracks.add(self)
            self._is_soloed = True
            self._update_activation(self)

    async def unsolo(self, exclusive=False):
        async with self.lock([self]):
            if not self.is_soloed:
                return
            mixer = self.mixer
            chains = (self,)
            if mixer:
                if not exclusive:
                    chains = tuple(mixer._soloed_tracks)
                for chain in chains:
                    mixer._soloed_tracks.remove(chain)
                    chain._is_soloed = False
            self._update_activation(self)

    ### PUBLIC PROPERTIES ###

    @property
    def default_receive_target(self):
        for parent in self.parentage[1:]:
            if hasattr(parent, "devices"):
                return parent
        return None

    @property
    def default_send_target(self):
        for parent in self.parentage[1:]:
            if hasattr(parent, "chains"):
                return parent
        return None

    @property
    def transfer(self):
        return self._transfer


class ChainContainer(AllocatableContainer):
    def _collect_for_cleanup(self, new_items, old_items):
        items = set()
        for item in [self] + new_items:
            mixer = item.mixer or item.root
            if mixer is not None:
                items.add(mixer)
        items.update(old_items)
        return items

    @property
    def mixer(self) -> Optional["RackDevice"]:
        for parent in self.parentage:
            if isinstance(parent, RackDevice):
                return parent
        return None


class RackDevice(DeviceObject, Mixer):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, uuid=None):
        DeviceObject.__init__(self, channel_count=channel_count, name=name, uuid=uuid)
        Mixer.__init__(self)
        self._chains = ChainContainer("input", AddAction.ADD_AFTER)
        self._send_target = Target(label="SendTarget")
        self._mutate(
            slice(None), [self._parameter_group, self._chains, self._send_target]
        )

    ### PRIVATE METHODS ###

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
            input_pair=(self.node_proxy, AddAction.ADD_TO_HEAD),
            output_pair=(self.node_proxy, AddAction.ADD_TO_TAIL),
        )

    def _allocate_audio_buses(self, provider, channel_count):
        self._audio_bus_proxies["output"] = provider.add_bus_group(
            calculation_rate=CalculationRate.AUDIO,
            channel_count=self.effective_channel_count,
        )

    def _allocate_synths(
        self, provider, channel_count, *, input_pair=None, output_pair=None
    ):
        input_target, input_action = input_pair
        self._node_proxies["input"] = provider.add_synth(
            add_action=input_action,
            synthdef=Send.build_synthdef(
                self.parent.effective_channel_count, self.effective_channel_count
            ),
            target_node=input_target,
            in_=self.track_object.audio_bus_proxies["output"],
            out=self.audio_bus_proxies["output"],
            name="RackIn",
        )
        output_target, output_action = output_pair
        self._node_proxies["output"] = provider.add_synth(
            add_action=output_action,
            synthdef=self.build_output_synthdef(
                self.effective_channel_count, self.parent.effective_channel_count
            ),
            target_node=output_target,
            in_=self.audio_bus_proxies["output"],
            out=self.track_object.audio_bus_proxies["output"],
            name="RackOut",
        )

    def _reallocate(self, difference):
        channel_count = self.effective_channel_count
        output_bus_group = self._audio_bus_proxies.pop("output")
        for bus_group in [output_bus_group]:
            bus_group.free()
        self._allocate_audio_buses(self.provider, channel_count)
        input_synth = self._node_proxies.pop("input")
        output_synth = self._node_proxies.pop("output")
        self._allocate_synths(
            self.provider,
            self.effective_channel_count,
            input_pair=(input_synth, AddAction.ADD_AFTER),
            output_pair=(output_synth, AddAction.ADD_AFTER),
        )
        for synth in [input_synth, output_synth]:
            synth.free()

    def _cleanup(self):
        Chain._update_activation(self)

    def _perform_input(self, moment, midi_messages):
        next_performer, midi_messages = Performable._perform_input(
            self, moment, midi_messages,
        )
        performers = [next_performer]
        if self.chains:
            performers = [chain._perform_input for chain in self.chains]
        for message in midi_messages:
            for performer in performers:
                yield performer, [message]

    ### PUBLIC METHODS ###

    async def add_chain(
        self,
        *,
        channel_count: Optional[int] = None,
        name: Optional[str] = None,
        transfer: Optional[Transfer] = None,
    ) -> Chain:
        async with self.lock([self]):
            chain = Chain(channel_count=channel_count, name=name, transfer=transfer)
            await chain.add_send(Default())
            self._chains._append(chain)
            return chain

    @classmethod
    def build_output_synthdef(cls, source_channel_count, target_channel_count):
        return build_patch_synthdef(
            source_channel_count, target_channel_count, hard_gate=True, mix_out=True
        )

    async def remove_chains(self, *chains: Chain):
        async with self.lock([self, *chains]):
            if not all(chain in self.chains for chain in chains):
                raise ValueError
            for chain in chains:
                self._chains._remove(chain)

    def serialize(self):
        serialized, auxiliary_entities = super().serialize()
        chains = []
        for chain in self.chains:
            chains.append(str(chain.uuid))
            aux = chain.serialize()
            auxiliary_entities.append(aux[0])
            auxiliary_entities.extend(aux[1])
        serialized["spec"]["chains"] = chains
        return serialized, auxiliary_entities

    @classmethod
    async def deserialize(cls, data, application) -> bool:
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry.get(parent_uuid)
        if parent is None:
            return True
        rack = cls(
            channel_count=data["spec"].get("channel_count"),
            name=data["meta"].get("name"),
            uuid=UUID(data["meta"]["uuid"]),
        )
        parent.devices._append(rack)
        return False

    async def set_channel_count(self, channel_count: Optional[int]):
        async with self.lock([self]):
            if channel_count is not None:
                assert 1 <= channel_count <= 8
                channel_count = int(channel_count)
            self._set(channel_count=channel_count)

    async def ungroup(self):
        async with self.lock([self]):
            if len(self.chains) > 1:
                raise ValueError("Can only ungroup single chain")
            pass

    ### PUBLIC PROPERTIES ###

    @property
    def chains(self) -> ChainContainer:
        return self._chains

    @property
    def default_receive_target(self):
        for parent in self.parentage[1:]:
            if hasattr(parent, "tracks"):
                if hasattr(parent, "master_track"):
                    return parent.master_track
                return parent

    @property
    def send_target(self) -> Target:
        return self._send_target
