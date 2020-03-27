import asyncio

from monome import SerialOsc

from ..pubsub import PubSub
from .clipview import ClipView


class Application:
    def __init__(self, command_queue: asyncio.Queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry = registry if registry is not None else {}
        self.serial_osc = SerialOsc()
        self.serial_osc.device_added_event.add_handler(self.on_device_added)
        self.serial_osc.device_removed_event.add_handler(self.on_device_removed)
        self.clip_view = ClipView(
            command_queue, pubsub=self.pubsub, registry=self.registry
        )

    async def run_async(self):
        await self.serial_osc.connect()

    def exit(self):
        if self.clip_view.grid.transport is not None:
            self.clip_view.grid.disconnect()

    def on_device_added(self, id_, type_, port):
        asyncio.get_running_loop().create_task(
            self.clip_view.grid.connect("127.0.0.1", port)
        )

    def on_device_removed(self, id_, type_, port):
        self.clip_view.grid.disconnect()
