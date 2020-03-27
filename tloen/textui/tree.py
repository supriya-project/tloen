from functools import singledispatchmethod
from typing import Dict
from uuid import UUID

import urwid
from urwid.command_map import ACTIVATE
from urwid.signals import connect_signal
from urwid.util import is_mouse_press

from ..bases import Event
from ..domain.applications import ApplicationLoaded
from ..pubsub import PubSub


class TloenTreeIcon(urwid.SelectableIcon):

    signals = ["click"]

    def __init__(self, text, cursor_position=0, on_press=None):
        urwid.SelectableIcon.__init__(self, text, cursor_position)
        if on_press:
            connect_signal(self, "click", on_press)

    def keypress(self, size, key):
        if self._command_map[key] != ACTIVATE:
            return key
        self._emit("click")

    def mouse_event(self, size, event, button, x, y, focus):
        if button != 1 or not is_mouse_press(event):
            return False
        self._emit("click")
        return True


class TloenTreeWidget(urwid.TreeWidget):
    indent_cols = 2

    def get_indented_widget(self):
        if self.get_node().get_depth() == 0:  # Hide the root widget; we don't care.
            return urwid.Pile([])  # Simulate a zero-height widget
        return super().get_indented_widget()

    def get_indent_cols(self):
        # Dedent to account for an invisible root widget.
        return self.indent_cols * (self.get_node().get_depth() - 1)

    def keypress(self, size, key):
        if self.is_leaf:
            return key
        if key in ("+", "-"):
            self.toggle()
        elif self._w.selectable():
            return self.__super.keypress(size, key)
        else:
            return key

    @property
    def expanded_icon(self):
        if not self.get_node().has_children():
            return urwid.SelectableIcon("\u25cc", 0)
        return TloenTreeIcon("\u25bc", 0, self.toggle)

    @property
    def unexpanded_icon(self):
        if not self.get_node().has_children():
            return urwid.SelectableIcon("\u25cc", 0)
        return TloenTreeIcon("\u25b6", 0, self.toggle)

    def get_display_text(self):
        value = self.get_node().get_value()
        uuid = value.get("uuid")
        kind = value.get("kind")
        name = self.get_node().get_context().registry[UUID(uuid)].name
        return f"{kind}: {uuid} ({name})"

    def selectable(self):
        return self.get_node().get_depth() > 0

    def toggle(self, *args):
        if self.expanded:
            self.expanded = False
        else:
            self.expanded = True
        self.update_expanded_icon()


class TloenParentNode(urwid.ParentNode):
    def __init__(self, value, context=None, parent=None, key=None, depth=None):
        urwid.ParentNode.__init__(self, value, depth=depth, key=key, parent=parent)
        self._context = context
        self._is_focused = False

    def blur(self):
        pass

    def focus(self):
        pass

    def get_context(self):
        return self._context

    def load_child_keys(self):
        return self.get_value().get("children", [])

    def load_child_node(self, key):
        return type(self)(
            context=self.get_context(),
            depth=self.get_depth() + 1,
            key=key,
            parent=self,
            value=self.get_context().widget_data[key],
        )

    def load_parent(self):
        widget_data = self.get_context().widget_data
        parent_uuid = self.get_value().get("parent")
        return type(self)(
            context=self.get_context(),
            depth=self.get_depth() - 1,
            key=parent_uuid,
            value=widget_data[parent_uuid],
        )

    def load_widget(self):
        widget_mapping = self.get_context().widget_mapping
        key = self.get_key()
        if key not in widget_mapping:
            widget_mapping[key] = TloenTreeWidget(self)
        return widget_mapping[key]

    @property
    def is_focused(self):
        return self._is_focused


class TloenTreeWalker(urwid.TreeWalker):
    def __init__(self, start_from):
        self.set_focus(start_from)


class TloenTreeListBox(urwid.TreeListBox):
    def unhandled_input(self, size, input):
        if input == "-":
            self.collapse_focus_parent(size)
        else:
            return input

    def change_focus(
        self,
        size,
        position,
        offset_inset=0,
        coming_from=None,
        cursor_coords=None,
        snap_rows=None,
    ):
        _, old_node = self.body.get_focus()
        if old_node is not None:
            old_node.blur()
        super().change_focus(
            size,
            position,
            offset_inset=offset_inset,
            coming_from=coming_from,
            cursor_coords=cursor_coords,
            snap_rows=snap_rows,
        )
        _, new_node = self.body.get_focus()
        new_node.focus()

    def focus_home(self, size):
        widget, pos = self.body.get_focus()
        node = pos.get_root()
        if node.has_children():
            node = node.get_first_child()
        self.change_focus(size, node)


class Tree(urwid.WidgetWrap):
    def __init__(self, command_queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.pubsub.subscribe(
            self.handle_event, ApplicationLoaded,
        )
        self.registry = registry if registry is not None else {}
        self.widget_mapping: Dict[UUID, urwid.Widget] = {}
        self.widget_data = self._build_widget_data()
        urwid.WidgetWrap.__init__(self, self._build_widget())

    def _build_widget(self):
        widget = TloenTreeListBox(
            urwid.TreeWalker(
                TloenParentNode(context=self, depth=0, value=self.widget_data[None],)
            )
        )
        return widget

    def _build_widget_data(self):
        ...

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...


class ContextTree(Tree):
    def __init__(self, command_queue, pubsub=None, registry=None):
        Tree.__init__(self, command_queue, pubsub=pubsub, registry=registry)
        self.pubsub.subscribe(self.handle_event, ApplicationLoaded)

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...

    @handle_event.register
    def _handle_application_loaded(self, event: ApplicationLoaded):
        self.widget_data = self._build_widget_data()
        self._w = self._build_widget()

    def _build_widget_data(self):
        widget_data = {}
        for entity_data in self.registry.application.serialize()["entities"]:
            kind = entity_data["kind"]
            meta = entity_data.get("meta", {})
            spec = entity_data.get("spec", {})
            if kind == "Application":
                widget_data[None] = dict(children=spec.get("contexts", []), kind=kind,)
                continue
            if kind == "Context":
                widget_data[meta.get("uuid")] = dict(
                    children=spec.get("tracks", []), kind=kind, uuid=meta.get("uuid"),
                )
            elif kind == "Track":
                widget_data[meta.get("uuid")] = dict(
                    children=spec.get("tracks", []),
                    kind=kind,
                    parent=meta.get("parent"),
                    uuid=meta.get("uuid"),
                )
        return widget_data


class DeviceTree(Tree):
    def __init__(self, command_queue, pubsub=None, registry=None):
        Tree.__init__(self, command_queue, pubsub=pubsub, registry=registry)
        self.pubsub.subscribe(self.handle_event)

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...

    def _build_widget_data(self):
        widget_data = {None: {}}
        return widget_data


class ParameterTree(Tree):
    def __init__(self, command_queue, pubsub=None, registry=None):
        Tree.__init__(self, command_queue, pubsub=pubsub, registry=registry)
        self.pubsub.subscribe(self.handle_event)

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...

    def _build_widget_data(self):
        widget_data = {None: {}}
        return widget_data
