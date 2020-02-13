import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    DynamicContainer,
    HSplit,
    HorizontalAlign,
    Layout,
    VSplit,
    Window,
)
from prompt_toolkit.widgets import Box, Label
from tloen.widgets import FancyFrame, Triangle

transport_label = Label(
    " | ".join(
        ["<play>", "<pause>", "<stop>", "<tap>", "4 / 4", "130 bpm", "0001.01.01"]
    ),
    dont_extend_width=True,
)

transport_section = FancyFrame(
    Box(transport_label, padding_left=1, padding_right=1),
    height=3,
    title="transport",
    title_align=HorizontalAlign.LEFT,
)

logo_section = Box(Label("t / l / ö / n", dont_extend_width=True))

server_status_label = Label(
    " | ".join(
        [
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
        ]
    ),
    dont_extend_width=True,
)

server_status_section = FancyFrame(
    Box(server_status_label, padding_left=1, padding_right=1),
    height=3,
    title="server",
    title_align=HorizontalAlign.RIGHT,
)

upper_status_bar = VSplit([transport_section, logo_section, server_status_section])

session_section = VSplit(
    [
        FancyFrame(Box(
            VSplit(
                [
                    FancyFrame(Box(Label("...")), title="track-a", width=20),
                    FancyFrame(Box(Label("...")), title="track-b", width=20),
                    FancyFrame(Box(Label("...")), title="track-c", width=20),
                    FancyFrame(Box(Label("...")), title="track-d", width=20),
                    Window(),
                ],
                padding=1,
            ),
            padding_top=0,
            padding_left=1,
            padding_right=1,
            padding_bottom=0,
        )),
        FancyFrame(Box(Label("...")), title="master", width=20),
        Box(
            FancyFrame(Box(Label("\n".join([Triangle.WHITE_RIGHT] * 3), dont_extend_width=True), padding_left=1, padding_right=1)),
            padding_top=0,
            width=5,
        ),
    ],
    padding=1,
)

arrangement_section = FancyFrame(Box(Label("...")))

session_or_arrangement = DynamicContainer(lambda: session_section)

browser_section = FancyFrame(
    Box(
        HSplit([
            FancyFrame(Label(" search...")),
            Label("..."),
        ]),
        padding_top=0,
        padding_left=1,
        padding_right=1,
    ),
    title="browser",
    width=40,
)

details_section = FancyFrame(Box(Label("...")), height=20)

lower_status_bar = FancyFrame(
    Box(Label("..."), padding_left=1, padding_right=1), title="status", height=3
)

main_split = HSplit(
    [
        upper_status_bar,
        VSplit([
            browser_section,
            session_or_arrangement,
        ], padding=1),
        details_section,
        lower_status_bar,
    ]
)

layout = Layout(container=Box(main_split, padding=1))

key_bindings = KeyBindings()


@key_bindings.add("c-c")
def _(event):
    event.app.exit()


application = Application(layout=layout, key_bindings=key_bindings, full_screen=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.run_async())
