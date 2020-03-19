from functools import singledispatchmethod
from typing import Dict
from uuid import UUID, uuid4

import urwid

from ..bases import Event
from ..domain.applications import ApplicationLoaded
from ..pubsub import PubSub


class TloenTreeWidget(urwid.TreeWidget):
    indent_cols = 2

    def keypress(self, size, key):
        if self.is_leaf:
            return key
        if key == "+":
            self.expanded = True
            self.update_expanded_icon()
        elif key == "-":
            self.expanded = False
            self.update_expanded_icon()
        elif self._w.selectable():
            return self.__super.keypress(size, key)
        else:
            return key

    @property
    def expanded_icon(self):
        return urwid.SelectableIcon("\u25bc", 0)

    @property
    def unexpanded_icon(self):
        return urwid.SelectableIcon("\u25b6", 0)

    def get_display_text(self):
        return str(self.get_node().get_value()["uuid"])

    def selectable(self):
        return True


class TloenParentNode(urwid.ParentNode):
    def __init__(self, value, context=None, parent=None, key=None, depth=None):
        urwid.ParentNode.__init__(self, value, depth=depth, key=key, parent=parent)
        self._context = context

    def get_context(self):
        return self._context

    def load_child_keys(self):
        return [_["uuid"] for _ in self.get_value().get("children", [])]

    def load_child_node(self, key):
        return type(self)(
            context=self.get_context(),
            depth=self.get_depth() + 1,
            key=key,
            parent=self,
            value=[x for x in self.get_value()["children"] if x["uuid"] == key][0],
        )

    def load_widget(self):
        widget_mapping = self.get_context().widget_mapping
        key = self.get_key()
        if key not in widget_mapping:
            widget_mapping[key] = TloenTreeWidget(self)
        return widget_mapping[key]


class TloenTreeListBox(urwid.TreeListBox):
    def unhandled_input(self, size, input):
        if input == "-":
            self.collapse_focus_parent(size)
        else:
            return input


class Tree(urwid.WidgetWrap):
    def __init__(self, command_queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.pubsub.subscribe(
            self.handle_event, ApplicationLoaded,
        )
        self.registry = registry if registry is not None else {}
        self.widget_mapping: Dict[UUID, urwid.Widget] = {}
        self.widget_data = {
            "uuid": uuid4(),
            "children": [
                {"uuid": uuid4(), "children": []},
                {"uuid": uuid4(), "children": []},
            ],
        }
        urwid.WidgetWrap.__init__(
            self,
            TloenTreeListBox(
                urwid.TreeWalker(
                    TloenParentNode(context=self, value=self.widget_data,)
                )
            ),
        )

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...

    @handle_event.register
    def _handle_application_loaded(self, event: ApplicationLoaded):
        ...
