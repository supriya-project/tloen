import dataclasses
from uuid import UUID

from ..bases import Command
from ..domain import Clip, Note


@dataclasses.dataclass
class ToggleClipNote(Command):
    clip_uuid: UUID
    pitch: float
    offset: float
    duration: float = 1 / 16

    async def do(self, harness):
        clip: Clip = harness.domain_application.registry[self.clip_uuid]
        moment = clip._interval_tree.get_moment_at(self.offset)
        for note in moment.start_intervals:
            if note.pitch == self.pitch:
                await clip.remove_notes([note])
                break
        else:
            await clip.add_notes(
                [
                    Note(
                        start_offset=self.offset,
                        stop_offset=self.offset + self.duration,
                        pitch=self.pitch,
                    ),
                ]
            )


@dataclasses.dataclass
class DoubleClip(Command):
    clip_uuid: UUID

    async def do(self, harness):
        clip: Clip = harness.domain_application.registry[self.clip_uuid]
        await clip.double()


@dataclasses.dataclass
class HalveClip(Command):
    clip_uuid: UUID

    async def do(self, harness):
        clip: Clip = harness.domain_application.registry[self.clip_uuid]
        await clip.halve()
