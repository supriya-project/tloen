import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HorizontalAlign, Layout, VSplit, HSplit
from prompt_toolkit.widgets import Box
from tloen.widgets import FancyFrame, Label

transport_label = Label(" | ".join([
    "<play>",
    "<pause>",
    "<stop>",
    "<tap>",
    "4 / 4",
    "130 bpm",
    "0001.01.01",
]), dont_extend_width=True)

transport_section = FancyFrame(
    Box(transport_label, padding_left=1, padding_right=1),
    height=3,
    title="transport",
    title_align=HorizontalAlign.LEFT,
)

logo_section = Box(Label("t / l / ö / n", dont_extend_width=True))

server_status_label = Label(" | ".join([
    "<quit>",
    "online",
    "57110",
    "avg: 04.07%",
    "peak: 15.12%",
    "target: 44100",
    "actual: 44100.0",
    "s: 0",
    "g: 2",
    "d: 4",
    "u: 0",
]), dont_extend_width=True)

server_status_section = FancyFrame(
    Box(server_status_label, padding_left=1, padding_right=1),
    height=3,
    title="server",
    title_align=HorizontalAlign.RIGHT,
)

upper_status_bar = VSplit([transport_section, logo_section, server_status_section])

"""
session_section = FancyFrame()

arrangement_section = FancyFrame()

session_or_arrangement = DynamicContainer(

browser_section = FancyFrame()

details_section = FancyFrame()
"""

lower_status_bar = FancyFrame(Box(Label("..."), padding_left=1, padding_right=1), title="status", height=3)

layout = Layout(container=HSplit([upper_status_bar, lower_status_bar]))

key_bindings = KeyBindings()


@key_bindings.add("c-c")
def _(event):
    event.app.exit()


application = Application(layout=layout, key_bindings=key_bindings, full_screen=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.run_async())
