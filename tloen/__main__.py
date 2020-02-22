import asyncio

from . import core
from . import tui


class Harness:

    def __init__(self, loop):
        self.exit_future = loop.create_future()
        self.command_queue = asyncio.Queue()
        self.dsp_application = None
        self.tui_application = tui.create_application(self.command_queue)

    async def run(self):
        self.dsp_application = await core.Application.new(1, 1, 1)
        loop = asyncio.get_running_loop()
        loop.create_task(self.tui_application.run_async())
        while not self.exit_future.done():
            command = await self.command_queue.get()
            await command.execute(self)


loop = asyncio.get_event_loop()
harness = Harness(loop)
loop.run_until_complete(harness.run())
