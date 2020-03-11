import dataclasses
from typing import Union
from uuid import UUID

from supriya.typing import Default

from ..bases import Command
from ..domain import Track


@dataclasses.dataclass
class AddReceiveToTrack(Command):
    track_uuid: UUID
    source: Union[Default, UUID]

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        source = Default()
        if isinstance(self.source, UUID):
            source: Track = harness.domain_application.registry[self.source]
        await track.add_receive(source)


@dataclasses.dataclass
class AddSendToTrack(Command):
    track_uuid: UUID
    target: Union[Default, UUID]

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        target = Default()
        if isinstance(self.target, UUID):
            target: Track = harness.domain_application.registry[self.target]
        await track.add_send(target)


@dataclasses.dataclass
class CueTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.cue()


@dataclasses.dataclass
class DeleteTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.delete()


@dataclasses.dataclass
class DuplicateTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.duplicate()


@dataclasses.dataclass
class MuteTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.mute()


@dataclasses.dataclass
class SoloTrack(Command):
    track_uuid: UUID
    exclusive: bool = True

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.solo(exclusive=self.exclusive)


@dataclasses.dataclass
class UncueTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.uncue()


@dataclasses.dataclass
class UnmuteTrack(Command):
    track_uuid: UUID

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.unmute()


@dataclasses.dataclass
class UnsoloTrack(Command):
    track_uuid: UUID
    exclusive: bool = False

    async def do(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.unsolo(exclusive=self.exclusive)
