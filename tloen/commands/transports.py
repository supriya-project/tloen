import dataclasses

from ..bases import Command


@dataclasses.dataclass
class ToggleTransport(Command):
    async def do(self, harness):
        if harness.domain_application.transport.is_running:
            await harness.domain_application.transport.stop()
        else:
            await harness.domain_application.transport.start()


@dataclasses.dataclass
class SetTransportTempo(Command):
    tempo: float

    async def do(self, harness):
        await harness.domain_application.transport.set_tempo(self.tempo)


@dataclasses.dataclass
class NudgeTransportTempoUp(Command):
    async def do(self, harness):
        transport = harness.domain_application.transport
        new_tempo = min(transport.clock.beats_per_minute + 1.0, 1000.0)
        await transport.set_tempo(new_tempo)


@dataclasses.dataclass
class NudgeTransportTempoDown(Command):
    async def do(self, harness):
        transport = harness.domain_application.transport
        new_tempo = max(transport.clock.beats_per_minute - 1.0, 1.0)
        await transport.set_tempo(new_tempo)
