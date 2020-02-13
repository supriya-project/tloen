from functools import partial
from typing import Optional

from prompt_toolkit.formatted_text import AnyFormattedText, Template
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import (
    AnyContainer,
    Container,
    DynamicContainer,
    HSplit,
    HorizontalAlign,
    VSplit,
    Window,
)
from prompt_toolkit.layout.dimension import AnyDimension
from prompt_toolkit.widgets.base import Label, Button


class Direction:
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class Border:
    LIGHT_HORIZONTAL = "\u2500"
    LIGHT_VERTICAL = "\u2502"
    LIGHT_TOP_LEFT = "\u250c"
    LIGHT_TOP_RIGHT = "\u2510"
    LIGHT_BOTTOM_LEFT = "\u2514"
    LIGHT_BOTTOM_RIGHT = "\u2518"
    LIGHT_LEFT = "\u2574"
    LIGHT_RIGHT = "\u2576"
    LIGHT_ARC_TOP_RIGHT = "\u256e"
    LIGHT_ARC_TOP_LEFT = "\u256d"
    LIGHT_ARC_BOTTOM_RIGHT = "\u256f"
    LIGHT_ARC_BOTTOM_LEFT = "\u2570"


class Triangle:
    BLACK_DOWN = "\u25bc"
    BLACK_DOWN_SMALL = "\u25be"
    BLACK_LEFT = "\u25c0"
    BLACK_LEFT_SMALL = "\u25c2"
    BLACK_RIGHT = "\u25b6"
    BLACK_RIGHT_SMALL = "\u25b8"
    BLACK_UP = "\u25b2"
    BLACK_UP_SMALL = "\u25b4"
    WHITE_DOWN = "\u25bd"
    WHITE_DOWN_SMALL = "\u25bf"
    WHITE_LEFT = "\u25c1"
    WHITE_LEFT_SMALL = "\u25c3"
    WHITE_RIGHT = "\u25b7"
    WHITE_RIGHT_SMALL = "\u25b9"
    WHITE_UP = "\u25b3"
    WHITE_UP_SMALL = "\u25b5"


class Pointer:
    BLACK_LEFT = "\u25c4"
    BLACK_RIGHT = "\u25ba"
    WHITE_LEFT = "\u25c5"
    WHITE_RIGHT = "\u25bb"


class Scrollbar:

    def __init__(self, vertical=True, total_dimension=10, visible_dimension=5, offset=0):
        self.total_dimenion = 0
        self.visible_dimension = 0
        self.offset = 0
        self.vertical = bool(vertical)
        if self.vertical:
            self.scroll_window = Window(width=1, char=Border.LIGHT_VERTICAL)
            self.container = HSplit([
                Button(width=1, text=Triangle.BLACK_UP, handler=lambda: self.scroll(Direction.UP)),
                self.scroll_window,
                Button(width=1, text=Triangle.BLACK_DOWN, handler=lambda: self.scroll(Direction.DOWN)),
            ])
        else:
            self.scroll_window = Window(height=1, char=Border.LIGHT_HORIZONTAL)
            self.container = VSplit([
                Button(width=1, text=Triangle.BLACK_LEFT, handler=lambda: self.scroll(Direction.LEFT)),
                self.scroll_window,
                Button(width=1, text=Triangle.BLACK_RIGHT, handler=lambda: self.scroll(Direction.RIGHT)),
            ])

    def __pt_container__(self) -> Container:
        return self.container

    def scroll(self, direction):
        pass

    def set_scroll(self, total_dimension, visible_dimension, offset):
        self.total_dimension = total_dimension
        self.visible_dimension = visible_dimension
        self.offset = offset


class FancyFrame:
    def __init__(
        self,
        body: AnyContainer,
        title: AnyFormattedText = "",
        title_align: HorizontalAlign = HorizontalAlign.LEFT,
        style: str = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        key_bindings: Optional[KeyBindings] = None,
        modal: bool = False,
    ) -> None:
        self.title = title
        self.body = body
        fill = partial(Window, style="class:frame.border")
        style = "class:frame " + style
        top_children = [
            fill(width=1, height=1, char=Border.LIGHT_ARC_TOP_LEFT),
            Label(
                lambda: Template("{}{}{}").format(
                    Border.LIGHT_LEFT, self.title, Border.LIGHT_RIGHT
                )
                if self.title
                else "",
                style="class:frame.label",
                dont_extend_width=True,
            ),
            fill(width=1, height=1, char=Border.LIGHT_ARC_TOP_RIGHT),
        ]
        if title_align in [
            HorizontalAlign.LEFT,
            HorizontalAlign.CENTER,
            HorizontalAlign.JUSTIFY,
        ]:
            top_children.insert(2, fill(char=Border.LIGHT_HORIZONTAL))
        if title_align in [
            HorizontalAlign.RIGHT,
            HorizontalAlign.CENTER,
            HorizontalAlign.JUSTIFY,
        ]:
            top_children.insert(1, fill(char=Border.LIGHT_HORIZONTAL))
        top_row = VSplit(top_children, height=1)
        middle_row = VSplit(
            [
                fill(width=1, char=Border.LIGHT_VERTICAL),
                DynamicContainer(lambda: self.body),
                fill(width=1, char=Border.LIGHT_VERTICAL),
            ],
            padding=0,
        )
        bottom_row = VSplit(
            [
                fill(width=1, height=1, char=Border.LIGHT_ARC_BOTTOM_LEFT),
                fill(char=Border.LIGHT_HORIZONTAL),
                fill(width=1, height=1, char=Border.LIGHT_ARC_BOTTOM_RIGHT),
            ]
        )
        self.container = HSplit(
            [top_row, middle_row, bottom_row],
            width=width,
            height=height,
            style=style,
            key_bindings=key_bindings,
            modal=modal,
        )

    def __pt_container__(self) -> Container:
        return self.container

    def resize(self, height=..., width=...):
        if height is not ...:
            self.__pt_container__().height = height
        if width is not ...:
            self.__pt_container__().width = width


class ServerStatusWidget:
    def __init__(self, application):
        self.application = application

    def __pt_container__(self):
        return self.container


class TransportWidget:
    def __init__(self, application):
        self.application = application

    def __pt_container__(self):
        return self.container


class BrowserWidget:
    def __init__(self, application):
        self.application = application

    def __pt_container__(self):
        return self.container
