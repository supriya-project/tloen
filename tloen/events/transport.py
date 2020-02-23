import dataclasses

from supriya.clock import Moment

from .bases import Command, Event


@dataclasses.dataclass
class StartTransport(Command):
    async def execute(self, harness):
        await harness.domain_application.transport.start()


@dataclasses.dataclass
class StopTransport(Command):
    async def execute(self, harness):
        await harness.domain_application.transport.stop()


@dataclasses.dataclass
class TransportStarted(Event):
    pass


@dataclasses.dataclass
class TransportStopped(Event):
    pass


@dataclasses.dataclass
class TransportTicked(Event):
    moment: Moment
