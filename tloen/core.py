import asyncio
import signal
from collections.abc import Mapping
from typing import Dict
from uuid import UUID

from . import domain, gridui, pubsub, textui
from .domain.applications import ApplicationStatusRefreshed


class Registry(Mapping):
    def __init__(self, registry: Dict[UUID, domain.ApplicationObject]):
        self._registry = registry

    def __getitem__(self, key):
        return self._registry[key]

    def __iter__(self):
        return iter(self._registry)

    def __len__(self):
        return len(self._registry)

    def set_backing_registry(self, registry: Dict[UUID, domain.ApplicationObject]):
        self._registry = registry


class Harness:
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
        self.exit_future = loop.create_future()
        self.pubsub = pubsub.PubSub()
        self.command_queue = asyncio.Queue()
        self.domain_application = domain.Application()
        self.registry = Registry(self.domain_application.registry)
        self.gridui_application = gridui.Application(
            command_queue=self.command_queue,
            pubsub=self.pubsub,
            registry=self.registry,
        )
        self.textui_application = textui.Application(
            command_queue=self.command_queue,
            pubsub=self.pubsub,
            registry=self.registry,
        )
        self.update_period = 0.1

    async def build_application(self):
        domain_application = await domain.Application.new(
            context_count=1, track_count=4, scene_count=8, pubsub=self.pubsub
        )
        track = domain_application.contexts[0].tracks[0]
        sampler = await track.add_device(domain.BasicSampler)
        await sampler.parameters["buffer_id"].set_("tloen:samples/808/bd-long-03.wav")
        await track.slots[0].add_clip()
        return domain_application

    async def run(self, gridui=True, textui=True):
        def handler(*args):
            return True

        self.domain_application = await self.build_application()
        self.registry.set_backing_registry(self.domain_application.registry)
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, handler)
        loop.add_signal_handler(signal.SIGTSTP, handler)
        loop.create_task(self.gridui_application.run_async())
        loop.create_task(self.textui_application.run_async())
        loop.create_task(self.periodic_update())
        while not self.exit_future.done():
            command = await self.command_queue.get()
            await command.execute(self)

    async def periodic_update(self):
        while not self.exit_future.done():
            if self.domain_application.status == domain.Application.Status.REALTIME:
                status = self.domain_application.primary_context.provider.server.status
                self.pubsub.publish(ApplicationStatusRefreshed(status))
            await asyncio.sleep(self.update_period)

    async def exit(self):
        if self.domain_application is not None:
            await self.domain_application.quit()
        self.gridui_application.exit()
        self.textui_application.exit()
        self.exit_future.set_result(True)
