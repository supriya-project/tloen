from prompt_toolkit.key_binding import KeyBindings

from .. import events


key_bindings = KeyBindings()


@key_bindings.add("c-b")
def _(event):
    command = events.ApplicationBoot()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-q")
def _(event):
    command = events.ApplicationQuit()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("c-c")
def _(event):
    command = events.TloenExit()
    event.app.command_queue.put_nowait(command)


@key_bindings.add("space")
def _(event):
    if not event.domain_application.transport.is_running:
        command = events.TransportStart()
    else:
        command = events.TransportStop()
    event.app.command_queue.put_nowait(command)
