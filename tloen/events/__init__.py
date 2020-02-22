import dataclasses
from typing import Optional
from uuid import UUID


class Command:
    pass


class Event:
    pass


@dataclasses.dataclass
class ApplicationBoot(Command):
    async def execute(self, harness):
        await harness.domain_application.boot()


@dataclasses.dataclass
class ApplicationQuit(Command):
    async def execute(self, harness):
        await harness.domain_application.quit()


@dataclasses.dataclass
class TrackAdd(Command):
    context_uuid: UUID
    track_uuid: Optional[UUID]

    async def execute(self, harness):
        context = harness.domain_application.registry[self.context_uuid]
        track = await context.add_track()
        self.track_uuid = track.uuid


@dataclasses.dataclass
class TransportStart(Command):
    async def execute(self, harness):
        await harness.domain_application.transport.start()


@dataclasses.dataclass
class TransportStarted(Event):
    pass


@dataclasses.dataclass
class TransportStop(Command):
    async def execute(self, harness):
        await harness.domain_application.transport.stop()


@dataclasses.dataclass
class TransportStopped(Event):
    pass


@dataclasses.dataclass
class TransportTicked(Event):
    measure_offset: float
    numerator: int
    denominator: int


@dataclasses.dataclass
class TloenExit(Command):
    async def execute(self, harness):
        await harness.exit()
