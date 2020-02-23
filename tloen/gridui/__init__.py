import asyncio
from typing import Any, Dict
from uuid import UUID

from monome import SerialOsc

from ..pubsub import PubSub


class Application:
    def __init__(self, command_queue: asyncio.Queue, pubsub=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry: Dict[UUID, Any] = {}
        self.serial_osc = SerialOsc()
        self.serial_osc.device_added_event.add_handler(self.on_device_added)
        self.serial_osc.device_removed_event.add_handler(self.on_device_removed)

    async def run_async(self):
        await self.serial_osc.connect()

    def on_device_added(self, id_, type_, port):
        print("SerialOsc +", repr(id_), repr(type_), repr(port))

    def on_device_removed(self, id_, type_, port):
        print("SerialOsc -", repr(id_), repr(type_), repr(port))
