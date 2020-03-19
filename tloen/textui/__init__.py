import asyncio

import urwid

from ..commands.applications import (
    BootApplication,
    ExitToTerminal,
    QuitApplication,
)
from ..commands.slots import FireSlot
from ..commands.transports import ToggleTransport
from ..pubsub import PubSub
from .tree import Tree


class Application:
    def __init__(self, command_queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry = registry if registry is not None else {}

        self.widget = Tree(
            self.command_queue, pubsub=self.pubsub, registry=self.registry,
        )

        self.handlers = {
            "ctrl q": QuitApplication(),
            "ctrl b": BootApplication(),
            "ctrl c": ExitToTerminal(),
            "ctrl g": FireSlot(),
            " ": ToggleTransport(),
        }

    def unhandled_input(self, key):
        command = self.handlers.get(key)
        if command is None:
            return
        self.command_queue.put_nowait(command)

    async def run_async(self):
        loop = asyncio.get_running_loop()
        self.exit_future = loop.create_future()
        self.main_loop = urwid.MainLoop(
            self.widget,
            event_loop=urwid.AsyncioEventLoop(loop=loop),
            unhandled_input=self.unhandled_input,
        )
        try:
            self.main_loop.start()
            self.main_loop.screen.tty_signal_keys(
                "undefined", "undefined", "undefined", "undefined", "undefined"
            )
            await self.exit_future
        finally:
            self.main_loop.stop()

    def exit(self):
        self.exit_future.set_result(True)
