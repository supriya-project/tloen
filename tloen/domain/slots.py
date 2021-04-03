import dataclasses
from uuid import UUID, uuid4

from ..bases import Event
from .bases import ApplicationObject
from .clips import Clip


class Slot(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self, *, name=None, uuid=None):
        ApplicationObject.__init__(self, name=name)
        self._uuid = uuid or uuid4()

    ### SPECIAL METHODS ###

    def __str__(self):
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} {self.uuid}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    @classmethod
    async def _deserialize(cls, data, application) -> bool:
        parent_uuid = UUID(data["meta"]["parent"])
        parent = application.registry.get(parent_uuid)
        if parent is None:
            return True
        slot = cls(uuid=UUID(data["meta"]["uuid"]))
        parent.slots._append(slot)
        return False

    def _serialize(self):
        serialized, auxiliary_entities = super()._serialize()
        if self.clip is not None:
            serialized["spec"]["clip"] = str(self.clip.uuid)
            clip_entities = self.clip._serialize()
            auxiliary_entities.append(clip_entities[0])
            auxiliary_entities.extend(clip_entities[1])
        return serialized, auxiliary_entities

    async def _set_clip(self, clip):
        async with self.lock([self]):
            if clip is self.clip:
                return
            if self.clip is not None:
                self._remove(self.clip)
            if clip is not None:
                self._append(clip)

    ### PUBLIC METHODS ###

    async def add_clip(self, *, notes=None, is_looping=True):
        clip = Clip(notes=notes, is_looping=is_looping)
        await self._set_clip(clip)
        return clip

    async def duplicate_clip(self):
        pass

    async def fire(self):
        if not self.application:
            return
        track = self.track
        if track is None:
            return
        await track._fire(self.parent.index(self))
        self.application.pubsub.publish(SlotFired(self.uuid))

    async def move_clip(self, slot):
        await slot._set_clip(self.clip)

    async def remove_clip(self):
        await self._set_clip(None)

    ### PUBLIC PROPERTIES ###

    @property
    def clip(self):
        try:
            return self[0]
        except IndexError:
            return None

    @property
    def track(self):
        from .tracks import Track

        for parent in self.parentage[1:]:
            if isinstance(parent, Track):
                return parent
        return None

    @property
    def uuid(self):
        return self._uuid


class Scene(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self, *, name=None, uuid=None):
        ApplicationObject.__init__(self, name=name)
        self._uuid = uuid or uuid4()

    ### SPECIAL METHODS ###

    def __str__(self):
        obj_name = type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} {self.uuid}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    @classmethod
    async def _deserialize(cls, data, application) -> bool:
        scene = cls(uuid=UUID(data["meta"]["uuid"]))
        application.scenes._append(scene)
        return False

    ### PUBLIC METHODS ###

    def delete(self):
        pass

    def duplicate(self):
        pass

    async def fire(self):
        pass

    ### PUBLIC PROPERTIES ###

    @property
    def uuid(self):
        return self._uuid


@dataclasses.dataclass
class ClipLaunched(Event):
    clip_uuid: UUID


@dataclasses.dataclass
class SlotFired(Event):
    slot_uuid: UUID
