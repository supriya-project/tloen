import dataclasses
from uuid import UUID

from ..bases import Command
from ..domain import Slot


@dataclasses.dataclass
class AddClip(Command):
    slot_uuid: UUID

    async def execute(self, harness):
        slot: Slot = harness.domain_application.registry[self.slot_uuid]
        await slot.add_clip()


@dataclasses.dataclass
class FireSlot(Command):
    # slot_uuid: UUID

    async def execute(self, harness):
        slot = harness.domain_application.contexts[0].tracks[0].slots[0]
        # slot: Slot = harness.domain_application.registry[self.slot_uuid]
        await slot.fire()


@dataclasses.dataclass
class RemoveClip(Command):
    slot_uuid: UUID

    async def execute(self, harness):
        slot: Slot = harness.domain_application.registry[self.slot_uuid]
        await slot.remove_clip()
