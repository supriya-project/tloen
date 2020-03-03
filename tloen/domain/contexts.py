from typing import Optional
from uuid import UUID, uuid4

from supriya.enums import AddAction
from supriya.osc import find_free_port
from supriya.provider import Provider
from supriya.querytree import QueryTreeGroup
from supriya.typing import Default

import tloen.domain  # noqa

from .bases import Allocatable, Mixer
from .sends import DirectOut
from .tracks import CueTrack, MasterTrack, Track, TrackContainer


class Context(Allocatable, Mixer):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None, uuid=None):
        Allocatable.__init__(self, channel_count=channel_count, name=name)
        Mixer.__init__(self)
        self._uuid = uuid or uuid4()
        self._master_track = MasterTrack()
        self._master_track.postfader_sends._append(
            DirectOut(0, self.effective_channel_count)
        )
        self._cue_track = CueTrack()
        self._cue_track.postfader_sends._append(
            DirectOut(self.effective_channel_count, 2)
        )
        self._tracks = TrackContainer("node", AddAction.ADD_TO_HEAD, label="Tracks")
        self._mutate(slice(None), [self._tracks, self._master_track, self._cue_track])

    ### SPECIAL METHODS ###

    def __str__(self):
        obj_name = type(self).__name__
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        provider = self.provider if self.provider is not None else "<?>"
        return "\n".join(
            [
                f"<{obj_name} {provider} [{node_proxy_id}] {self.uuid}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _allocate(self, new_provider, target_node, add_action):
        super()._allocate(new_provider, target_node, add_action)
        self._node_proxies["node"] = new_provider.add_group(
            target_node=target_node, add_action=add_action, name=self.label
        )

    async def _boot(self):
        provider = await Provider.realtime_async(port=find_free_port())
        async with provider.at(wait=True):
            self._set(provider=provider)

    def _cleanup(self):
        Track._update_activation(self)

    ### PUBLIC METHODS ###

    async def add_track(self, *, name=None) -> Track:
        async with self.lock([self]):
            track = Track(name=name)
            await track.add_send(Default())
            self._tracks._append(track)
            return track

    def capture(self):
        return self.provider.server.osc_protocol.capture()

    async def delete(self):
        async with self.lock([self]):
            if self.parent:
                await self.parent.remove_contexts(self)

    async def move(self, container: "tloen.domain.Application", position: int):
        async with self.lock([self, container]):
            container._contexts._mutate(slice(position, position), [self])

    async def perform(self, midi_messages, moment=None):
        self._debug_tree(
            self, "Perform", suffix=repr([type(_).__name__ for _ in midi_messages])
        )
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            for track in self.recurse(prototype=Track):
                await track.perform(midi_messages, moment=moment)

    async def query(self):
        if self.provider.server is None:
            raise ValueError
        return QueryTreeGroup(
            node_id=self.node_proxy.identifier,
            children=[
                QueryTreeGroup(
                    node_id=self.tracks.node_proxy.identifier,
                    children=[await track.query() for track in self.tracks],
                ),
                await self.master_track.query(),
                await self.cue_track.query(),
            ],
        ).annotate(self.provider.annotation_map)

    async def remove_tracks(self, *tracks: "tloen.domain.Track"):
        async with self.lock([self, *tracks]):
            if not all(track in self.tracks for track in tracks):
                raise ValueError
            for track in tracks:
                self._tracks._remove(track)

    def serialize(self):
        serialized, auxiliary_entities = super().serialize()
        serialized["spec"].update(
            cue_track=str(self.cue_track.uuid),
            master_track=str(self.master_track.uuid),
            tracks=[str(track.uuid) for track in self.tracks]
        )
        for track in [self.cue_track, self.master_track, *self.tracks]:
            aux = track.serialize()
            auxiliary_entities.append(aux[0])
            auxiliary_entities.extend(aux[1])
        return serialized, auxiliary_entities

    @classmethod
    def deserialize(cls, data):
        context = cls(
            channel_count=data["spec"].get("channel_count"),
            name=data["meta"].get("name"),
            uuid=UUID(data["meta"]["uuid"]),
        )
        master_track = MasterTrack.deserialize(data["spec"]["master_track"])
        cue_track = CueTrack.deserialize(data["spec"]["cue_track"])
        context._replace(context.master_track, master_track)
        context._replace(context.cue_track, cue_track)
        context._master_track = master_track
        context._cue_track = cue_track
        for track_data in data["spec"].get("tracks", []):
            context.tracks._append(Track.deserialize(track_data))
        return context

    async def set_channel_count(self, channel_count: Optional[int]):
        async with self.lock([self]):
            if channel_count is not None:
                assert 1 <= channel_count <= 8
                channel_count = int(channel_count)
            self._set(channel_count=channel_count)

    ### PUBLIC PROPERTIES ###

    @property
    def cue_track(self) -> CueTrack:
        return self._cue_track

    @property
    def master_track(self) -> MasterTrack:
        return self._master_track

    @property
    def tracks(self) -> TrackContainer:
        return self._tracks

    @property
    def uuid(self) -> UUID:
        return self._uuid
