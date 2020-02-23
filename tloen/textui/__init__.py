import asyncio
from typing import Any, Dict
from uuid import UUID

from prompt_toolkit import Application as PtkApplication
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout

from .. import events
from ..pubsub import PubSub
from .status import StatusWidget

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


@key_bindings.add("space")
def _start_transport(event):
    if not event.domain_application.transport.is_running:
        command = events.StartTransport()
    else:
        command = events.StopTransport()
    event.app.command_queue.put_nowait(command)


class Application(PtkApplication):
    def __init__(self, command_queue: asyncio.Queue, pubsub=None, **kwargs):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry: Dict[UUID, Any] = {}
        status_widget = StatusWidget(pubsub=self.pubsub)
        PtkApplication.__init__(
            self,
            full_screen=True,
            key_bindings=key_bindings,
            layout=Layout(container=status_widget,),
            **kwargs,
        )
