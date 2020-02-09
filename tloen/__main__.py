import asyncio
import time

from supriya.realtime import AsyncServer

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, VSplit
from prompt_toolkit.widgets import Box, Frame, TextArea

command_area = TextArea(text="awaiting command", width=60, height=20)
status_area = TextArea(text="awaiting status", width=60, height=20)
root_container = VSplit([Box(Frame(command_area)), Box(Frame(status_area))])
layout = Layout(container=root_container)

key_bindings = KeyBindings()

command_queue = asyncio.Queue()


@key_bindings.add("c-c")
def _(event):
    event.app.exit()


@key_bindings.add("c-b")
def _(event):
    event.app.loop.create_task(command_queue.put((time.time(), "boot")))


@key_bindings.add("c-q")
def _(event):
    event.app.loop.create_task(command_queue.put((time.time(), "quit")))


async def status_task(application):
    while not application.future.done():
        if getattr(application, "server", None) is not None:
            status_area.text = repr(application.server.status)
        else:
            status_area.text = "offline"
        await asyncio.sleep(0.5)


async def queue_task(application, queue):
    while not application.future.done():
        try:
            timestamp, command = await asyncio.wait_for(queue.get(), 1)
        except asyncio.TimeoutError:
            continue
        if command == "boot":
            if getattr(application, "server", None) is not None:
                command_area.text = f"already booted\n{timestamp}"
                continue
            command_area.text = f"booting\n{timestamp}"
            application.server = AsyncServer()
            await application.server.boot()
            command_area.text = f"booted\n{timestamp}"
            root_container.children.append(
                Box(Frame(TextArea(text="!!!"))).__pt_container__()
            )
        elif command == "quit":
            if getattr(application, "server", None) is None:
                command_area.text = f"already quit\n{timestamp}"
                continue
            command_area.text = f"quitting\n{timestamp}"
            await application.server.quit()
            application.server = None
            command_area.text = f"quit\n{timestamp}"
            root_container.children.pop()


application = Application(layout=layout, key_bindings=key_bindings, full_screen=True)
application.pre_run_callables = [
    lambda: loop.create_task(queue_task(application, command_queue)),
    lambda: loop.create_task(status_task(application)),
]

loop = asyncio.get_event_loop()
loop.run_until_complete(application.run_async())
