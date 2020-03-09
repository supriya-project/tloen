import asyncio
import signal
from collections.abc import Mapping

from . import domain, gridui, httpui, pubsub, textui
from .domain.applications import ApplicationStatusRefreshed


class Registry(Mapping):

    def __init__(self, application):
        self.set_application(application)

    def __getitem__(self, key):
        return self._registry[key]

    def __iter__(self):
        return iter(self._registry)

    def __len__(self):
        return len(self._registry)

    def set_application(self, application):
        self._application = application
        self._registry = application.registry
        self._transport = application.transport

    @property
    def application(self):
        return self._application

    @property
    def transport(self):
        return self._transport


class Harness:
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
        self.exit_future = loop.create_future()
        self.pubsub = pubsub.PubSub()
        self.command_queue = asyncio.Queue()
        self.undo_stack = []
        self.domain_application = domain.Application()
        self.registry = Registry(self.domain_application)
        self.gridui_application = gridui.Application(
            command_queue=self.command_queue,
            pubsub=self.pubsub,
            registry=self.registry,
        )
        self.httpui_application = httpui.Application(
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
        rack = await track.add_device(domain.RackDevice)
        for i, sample_path in enumerate(
            [
                "tloen:samples/808/bass-drum.wav",
                "tloen:samples/808/snare-drum.wav",
                "tloen:samples/808/clap.wav",
                "tloen:samples/808/maraca.wav",
                "tloen:samples/808/closed-hat.wav",
                "tloen:samples/808/low-tom-tom.wav",
                "tloen:samples/808/mid-tom-tom.wav",
                "tloen:samples/808/high-tom-tom.wav",
            ]
        ):
            chain = await rack.add_chain(transfer=domain.Transfer(in_pitch=i + 60))
            sampler = await chain.add_device(domain.BasicSampler)
            await sampler.parameters["buffer_id"].set_(sample_path)
        await track.slots[0].add_clip()
        return domain_application

    async def run(self, gridui=True, textui=True):
        def handler(*args):
            return True

        self.domain_application = await self.build_application()
        self.registry.set_application(self.domain_application)
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, handler)
        loop.add_signal_handler(signal.SIGTSTP, handler)
        loop.create_task(self.gridui_application.run_async())
        loop.create_task(self.httpui_application.run_async())
        loop.create_task(self.textui_application.run_async())
        loop.create_task(self.periodic_update())
        while not self.exit_future.done():
            command = await self.command_queue.get()
            success = await command.do(self)
            if success and hasattr(command, "undo"):
                self.undo_stack.append(command)

    async def periodic_update(self):
        while not self.exit_future.done():
            if self.domain_application.status == domain.Application.Status.REALTIME:
                status = self.domain_application.primary_context.provider.server.status
                self.pubsub.publish(ApplicationStatusRefreshed(status))
            await asyncio.sleep(self.update_period)

    async def exit(self):
        await self.domain_application.quit()
        self.gridui_application.exit()
        self.textui_application.exit()
        self.exit_future.set_result(True)
