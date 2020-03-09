import dataclasses
from uuid import UUID

from ..bases import Command
from ..domain import Context


@dataclasses.dataclass
class AddTrack(Command):
    context_uuid: UUID

    async def execute(self, harness):
        context: Context = harness.domain_application.registry[self.context_uuid]
        await context.add_track()
