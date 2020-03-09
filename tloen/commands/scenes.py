import dataclasses
from uuid import UUID

from ..bases import Command
from ..domain import Scene


@dataclasses.dataclass
class DeleteScene(Command):
    scene_uuid: UUID

    async def execute(self, harness):
        scene: Scene = harness.domain_application.registry[self.scene_uuid]
        await scene.delete()
