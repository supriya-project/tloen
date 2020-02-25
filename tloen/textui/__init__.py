import asyncio

import urwid

from .. import events
from ..pubsub import PubSub
from .status import StatusWidget
from .transport import TransportWidget


class Application:
    def __init__(self, command_queue, pubsub=None):
        self.command_queue = command_queue
        self.registry = {}
        self.pubsub = pubsub or PubSub()
        self.logo_widget = urwid.Text("\nt / l / ö / n", align="center")
        self.widget = urwid.Filler(
            urwid.Padding(
                urwid.Columns(
                    [
                        self.logo_widget,
                        (51, TransportWidget(self.pubsub)),
                        (110, StatusWidget(self.pubsub)),
                    ],
                    dividechars=1,
                ),
                left=1,
                right=1,
            ),
            valign="top",
            top=1,
            bottom=1,

        )
        self.handlers = {
            "ctrl q": events.QuitApplication(),
            "ctrl b": events.BootApplication(),
            "ctrl c": events.ExitToTerminal(),
            " ": events.ToggleTransport(),
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
