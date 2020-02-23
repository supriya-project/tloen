import asyncio

from . import domain, gridui, pubsub, textui
from .events import ApplicationStatusRefreshed


class Harness:
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
        self.exit_future = loop.create_future()
        self.pubsub = pubsub.PubSub()
        self.command_queue = asyncio.Queue()
        self.domain_application = domain.Application()
        self.gridui_application = gridui.Application(
            command_queue=self.command_queue, pubsub=self.pubsub
        )
        self.textui_application = textui.Application(
            command_queue=self.command_queue, pubsub=self.pubsub
        )
        self.update_period = 0.1

    async def run(self):
        self.domain_application = await domain.Application.new(
            context_count=1, track_count=4, scene_count=8, pubsub=self.pubsub
        )
        loop = asyncio.get_running_loop()
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
        self.textui_application.exit()
        self.exit_future.set_result(True)
