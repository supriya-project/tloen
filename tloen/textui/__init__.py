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
from .transport import TransportWidget
from .tree import ContextTree, DeviceTree, ParameterTree


class Application:
    def __init__(self, command_queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry = registry if registry is not None else {}

        transport_widget = TransportWidget(self.pubsub)

        context_tree = ContextTree(
            self.command_queue, pubsub=self.pubsub, registry=self.registry,
        )

        device_tree = DeviceTree(
            self.command_queue, pubsub=self.pubsub, registry=self.registry,
        )

        parameter_tree = ParameterTree(
            self.command_queue, pubsub=self.pubsub, registry=self.registry,
        )

        header = urwid.Columns([urwid.Text("\nt / l / ö / n"), transport_widget])

        body = urwid.Columns(
            [
                urwid.LineBox(context_tree, title="tracks", title_align="left"),
                urwid.LineBox(device_tree, title="devices", title_align="left"),
                urwid.LineBox(parameter_tree, title="parameters", title_align="left"),
            ],
            dividechars=1,
        )

        footer = urwid.LineBox(urwid.Text("..."))

        self.widget = urwid.Frame(body, header=header, footer=footer)

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
