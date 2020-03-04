import asyncio
import enum
from collections import deque
from types import MappingProxyType
from typing import Deque, Dict, Mapping, Optional, Tuple
from uuid import UUID

from supriya.nonrealtime import Session
from supriya.provider import Provider
from uqbar.containers import UniqueTreeTuple

import tloen.domain  # noqa

from ..events import (
    ApplicationBooted,
    ApplicationBooting,
    ApplicationQuit,
    ApplicationQuitting,
    ApplicationStatusRefreshed,
)
from ..pubsub import PubSub
from .bases import Container
from .clips import Scene
from .contexts import Context
from .controllers import Controller
from .transports import Transport


class Application(UniqueTreeTuple):

    ### CLASS VARIABLES ###

    class Status(enum.IntEnum):
        OFFLINE = 0
        REALTIME = 1
        NONREALTIME = 2

    ### INITIALIZER ###

    def __init__(self, channel_count=2, pubsub=None):
        # non-tree objects
        self._channel_count = int(channel_count)
        self._pubsub = pubsub or PubSub()
        self._status = self.Status.OFFLINE
        self._registry: Dict[UUID, "tloen.domain.ApplicationObject"] = {}
        # tree objects
        self._contexts = Container(label="Contexts")
        self._controllers = Container(label="Controllers")
        self._scenes = Container(label="Scenes")
        self._transport = Transport()
        UniqueTreeTuple.__init__(
            self,
            children=[self._transport, self._controllers, self._scenes, self._contexts],
        )

    ### SPECIAL METHODS ###

    def __str__(self):
        return "\n".join(
            [
                f"<{type(self).__name__} [{self.status.name}] {hex(id(self))}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _set_items(self, new_items, old_items, start_index, stop_index):
        UniqueTreeTuple._set_items(self, new_items, old_items, start_index, stop_index)
        for item in new_items:
            item._set(application=self)
        for item in old_items:
            item._set(application=None)

    ### PUBLIC METHODS ###

    async def add_context(self, *, name=None):
        if self.status == self.Status.NONREALTIME:
            raise ValueError
        context = Context(name=name)
        self._contexts._append(context)
        if self.status == self.Status.REALTIME:
            await context._boot()
        return context

    def add_controller(self, *, name=None) -> Controller:
        controller = Controller(name=name)
        self._controllers._append(controller)
        return controller

    def add_scene(self, *, name=None) -> Scene:
        from .clips import Slot
        from .tracks import Track

        scene = Scene(name=name)
        self._scenes._append(scene)
        tracks: Deque[Track] = deque()
        for context in self.contexts:
            tracks.extend(context.tracks)
        while tracks:
            track = tracks.pop()
            if track.tracks:
                tracks.extend(track.tracks)
            while len(track.slots) < len(self.scenes):
                track.slots._append(Slot())
        return scene

    async def boot(self):
        if self.status == self.Status.REALTIME:
            return
        elif self.status == self.Status.NONREALTIME:
            raise ValueError
        elif not self.contexts:
            raise RuntimeError("No contexts to boot")
        self.pubsub.publish(ApplicationBooting())
        await asyncio.gather(*(context._boot() for context in self.contexts))
        self.pubsub.publish(
            ApplicationBooted(self.primary_context.provider.server.port,)
        )
        self.pubsub.publish(
            ApplicationStatusRefreshed(self.primary_context.provider.server.status,)
        )
        self._status = self.Status.REALTIME
        return self

    async def flush(self):
        pass

    @classmethod
    async def new(cls, context_count=1, track_count=4, scene_count=8, **kwargs):
        application = cls(**kwargs)
        for _ in range(context_count):
            context = await application.add_context()
            for _ in range(track_count):
                await context.add_track()
        for _ in range(scene_count):
            application.add_scene()
        return application

    async def perform(self, midi_messages, moment=None):
        if self.status != self.Status.REALTIME:
            return
        for context in self.contexts:
            await context.perform(midi_messages, moment=moment)

    async def quit(self):
        if self.status == self.Status.OFFLINE:
            return
        elif self.status == self.Status.NONREALTIME:
            raise ValueError
        self._status = self.Status.OFFLINE
        self.pubsub.publish(ApplicationQuitting())
        await self.transport.stop()
        for context in self.contexts:
            provider = context.provider
            async with provider.at():
                context._set(provider=None)
            if provider is not None:
                await provider.server.quit()
        self.pubsub.publish(ApplicationQuit())
        return self

    async def remove_contexts(self, *contexts: Context):
        if not all(context in self.contexts for context in contexts):
            raise ValueError
        for context in contexts:
            provider = context.provider
            if provider is not None:
                async with provider.at():
                    self._contexts._remove(context)
                await provider.server.quit()
            else:
                self._contexts._remove(context)
        if not len(self):
            self._status = self.Status.OFFLINE

    def remove_controllers(self, *controllers: Controller):
        if not all(controller in self.controllers for controller in controllers):
            raise ValueError
        for controller in controllers:
            self._controllers._remove(controller)

    def remove_scenes(self, *scenes: Scene):
        from .tracks import Track

        if not all(scene in self.scenes for scene in scenes):
            raise ValueError
        indices = sorted(self.scenes.index(scene) for scene in scenes)
        for scene in scenes:
            self.scenes._remove(scene)
        tracks: Deque[Track] = deque()
        for context in self.contexts:
            tracks.extend(context.tracks)
        while tracks:
            track = tracks.pop()
            if track.tracks:
                tracks.extend(track.tracks)
            for index in reversed(indices):
                track.slots._remove(track.slots[index])

    async def render(self) -> Session:
        if self.status != self.Status.OFFLINE:
            raise ValueError
        self._status == self.Status.NONREALTIME
        provider = Provider.nonrealtime()
        with provider.at():
            for context in self.contexts:
                context._set(provider=provider)
        # Magic happens here
        with provider.at(provider.session.duration or 10):
            for context in self.contexts:
                context._set(provider=None)
        self._status = self.Status.OFFLINE
        return provider.session

    def serialize(self):
        def clean(data):
            for mapping in [data.get("meta", {}), data.get("spec", {}), data]:
                for key in tuple(mapping):
                    value = mapping[key]
                    if value is None or (isinstance(value, (list, dict)) and not value):
                        mapping.pop(key)

        serialized = {
            "kind": type(self).__name__,
            "spec": {
                "channel_count": self.channel_count,
                "contexts": [],
                "transport": self.transport.serialize(),
            },
        }
        entities = [serialized]
        for context in self.contexts:
            serialized["spec"]["contexts"].append(str(context.uuid))
            aux = context.serialize()
            entities.append(aux[0])
            entities.extend(aux[1])
        for entity in entities:
            clean(entity)
        return {"entities": entities}

    @classmethod
    async def deserialize(cls, data):
        entities_data = deque(data["entities"])
        entity_data = entities_data.popleft()
        application = cls(channel_count=entity_data["spec"].get("channel_count", 2),)
        await application.transport.deserialize(
            entity_data["spec"]["transport"], application.transport,
        )
        while entities_data:
            entity_data = entities_data.popleft()
            if entity_data.get("visits", 0) > 2:
                continue  # discard it
            entity_class = getattr(tloen.domain, entity_data["kind"])
            if entity_class.deserialize(entity_data, application):
                entity_data["visits"] = entity_data.get("visits", 0) + 1
                entities_data.append(entity_data)
                continue
        return application

    async def set_channel_count(self, channel_count: int):
        assert 1 <= channel_count <= 8
        self._channel_count = int(channel_count)
        for context in self.contexts:
            if context.provider:
                async with context.provider.at():
                    context._reconcile()
            else:
                context._reconcile()

    ### PUBLIC PROPERTIES ###

    @property
    def channel_count(self) -> int:
        return self._channel_count

    @property
    def contexts(self) -> Tuple[Context, ...]:
        return self._contexts

    @property
    def controllers(self) -> Tuple[Controller, ...]:
        return self._controllers

    @property
    def parent(self) -> None:
        return None

    @property
    def primary_context(self) -> Optional[Context]:
        if not self.contexts:
            return None
        return self.contexts[0]

    @property
    def pubsub(self):
        return self._pubsub

    @property
    def registry(self) -> Mapping[UUID, "tloen.domain.ApplicationObject"]:
        return MappingProxyType(self._registry)

    @property
    def scenes(self):
        return self._scenes

    @property
    def status(self):
        return self._status

    @property
    def transport(self) -> Transport:
        return self._transport
