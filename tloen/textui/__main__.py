import urwid


def on_a_press(*args, **kwargs):
    list_walker.append(button_row)


def on_b_press(*args, **kwargs):
    list_walker[2:] = []


button_row = urwid.LineBox(
    urwid.Columns(
        [
            urwid.Button("add more", on_press=on_a_press),
            urwid.Button("remove one", on_press=on_b_press),
        ]
    )
)

list_walker = urwid.SimpleListWalker([button_row])

list_box = urwid.ListBox(list_walker)


if __name__ == "__main__":
    loop = urwid.MainLoop(list_box)
    loop.run()
