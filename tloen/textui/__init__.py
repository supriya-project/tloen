import asyncio
from typing import Any, Dict
from uuid import UUID

from prompt_toolkit import Application as PtkApplication
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit

from .. import events
from ..pubsub import PubSub
from .status import StatusWidget
from .transport import TransportWidget

key_bindings = KeyBindings()


@key_bindings.add("c-b")
def _boot_application(event):
    command = events.BootApplication()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-q")
def _quit_application(event):
    command = events.QuitApplication()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-c")
def _exit_to_terminal(event):
    command = events.ExitToTerminal()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-space")
def _toggle_transport(event):
    command = events.ToggleTransport()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-u")
def _nudge_transport_tempo_up(event):
    command = events.NudgeTransportTempoUp()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-d")
def _nudge_transport_tempo_down(event):
    command = events.NudgeTransportTempoDown()
    event.app.command_queue.put_nowait(command)


class Application(PtkApplication):
    def __init__(self, command_queue: asyncio.Queue, pubsub=None, **kwargs):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry: Dict[UUID, Any] = {}
        status_widget = StatusWidget(pubsub=self.pubsub)
        transport_widget = TransportWidget(pubsub=self.pubsub)
        PtkApplication.__init__(
            self,
            full_screen=True,
            key_bindings=key_bindings,
            min_redraw_interval=0.05,
            layout=Layout(container=HSplit([transport_widget, status_widget])),
            **kwargs,
        )
