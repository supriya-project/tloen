import urwid


def exit_on_q(input):
    if input in ("q", "Q"):
        raise urwid.ExitMainLoop()


# transport
# scene list
# context view
#    context status
#    track
#        track controls
#        track volumes
#        track clips
# details view
#     browser
#     device tree (title shows for which track)
#     parameter tree (title shows for which object)
# clip editor


transport = urwid.LineBox(urwid.Text("..."), title="transport", title_align="left")

logo = urwid.Text("\nT /// L /// Ö /// N", align="center")

scenes = urwid.LineBox(
    urwid.Text("<< [a   ] [b   ] [c   ] >>", align="right"),
    title="scenes",
    title_align="right",
)

tracks = urwid.LineBox(
    urwid.Text("\n".join(["..."] * 10)), title="tracks", title_align="left"
)

browser = urwid.LineBox(
    urwid.Text("\n".join(["..."] * 10)), title="browser", title_align="left"
)

devices = urwid.LineBox(
    urwid.Text("\n".join(["..."] * 10)), title="devices", title_align="left"
)

parameters = urwid.LineBox(
    urwid.Text("\n".join(["..."] * 10)), title="parameters", title_align="left"
)

clip = urwid.LineBox(urwid.Text("..."), title="clip", title_align="left",)

status = urwid.LineBox(urwid.Button("..."), title="status", title_align="left",)

view = urwid.Pile(
    [
        urwid.Columns([transport, logo, scenes], dividechars=1),
        urwid.Columns([("weight", 1, browser), ("weight", 4, tracks)], dividechars=1),
        urwid.Columns(
            [("weight", 2, clip), ("weight", 1, devices), ("weight", 1, parameters)],
            dividechars=1,
        ),
        status,
    ]
)

view = urwid.Filler(view, top=1, bottom=1)

view = urwid.Padding(view, left=1, right=1)

if __name__ == "__main__":
    loop = urwid.MainLoop(view, unhandled_input=exit_on_q)
    loop.run()
