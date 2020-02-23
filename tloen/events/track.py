import dataclasses
from typing import Optional
from uuid import UUID

from .bases import Command


@dataclasses.dataclass
class AddTrack(Command):
    context_uuid: UUID
    track_uuid: Optional[UUID]

    async def execute(self, harness):
        context = harness.domain_application.registry[self.context_uuid]
        track = await context.add_track()
        self.track_uuid = track.uuid
