import dataclasses
from uuid import UUID

from ..bases import Command
from ..domain import Track


@dataclasses.dataclass
class CueTrack(Command):
    track_uuid: UUID

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.cue()


@dataclasses.dataclass
class DeleteTrack(Command):
    track_uuid: UUID

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.delete()


@dataclasses.dataclass
class MuteTrack(Command):
    track_uuid: UUID

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.mute()


@dataclasses.dataclass
class SoloTrack(Command):
    track_uuid: UUID
    exclusive: bool = True

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.solo(exclusive=self.exclusive)


@dataclasses.dataclass
class UncueTrack(Command):
    track_uuid: UUID

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.uncue()


@dataclasses.dataclass
class UnmuteTrack(Command):
    track_uuid: UUID

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.unmute()


@dataclasses.dataclass
class UnsoloTrack(Command):
    track_uuid: UUID
    exclusive: bool = False

    async def execute(self, harness):
        track: Track = harness.domain_application.registry[self.track_uuid]
        await track.unsolo(exclusive=self.exclusive)
