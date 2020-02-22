import dataclasses
from typing import Optional
from uuid import UUID


@dataclasses.dataclass
class ApplicationBoot:
    async def execute(self, harness):
        await harness.dsp_application.boot()


@dataclasses.dataclass
class ApplicationQuit:
    async def execute(self, harness):
        await harness.dsp_application.quit()


@dataclasses.dataclass
class TrackAdd:
    context_uuid: UUID
    track_uuid: Optional[UUID]

    async def execute(self, harness):
        context = harness.dsp_application.registry[self.context_uuid]
        track = await context.add_track()
        self.track_uuid = track.uuid


@dataclasses.dataclass
class TloenExit:
    async def execute(self, harness):
        await harness.dsp_application.quit()
        harness.tui_application.exit()
        harness.exit_future.set_result(True)
