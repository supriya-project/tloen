from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings

from .. import commands


key_bindings = KeyBindings()


@key_bindings.add("c-b")
def _(event):
    event.app.command_queue.put_nowait(commands.ApplicationBoot())


@key_bindings.add("c-q")
def _(event):
    event.app.command_queue.put_nowait(commands.ApplicationQuit())


@key_bindings.add("c-c")
def _(event):
    event.app.command_queue.put_nowait(commands.TloenExit())


def create_application(command_queue):
    application = Application(
        full_screen=True,
        key_bindings=key_bindings,
    )
    application.command_queue = command_queue
    return application
