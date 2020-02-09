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
from prompt_toolkit.widgets.base import Label


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
