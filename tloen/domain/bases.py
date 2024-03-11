import logging
from collections import deque
from contextlib import AsyncExitStack, asynccontextmanager
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Set,
    Union,
)

from supriya.clocks import Moment
from supriya.commands import FailResponse, NodeQueryRequest, SynthQueryRequest
from supriya.enums import AddAction
from supriya.providers import (
    BusGroupProxy,
    BusProxy,
    NodeProxy,
    OscCallbackProxy,
    Provider,
    SynthProxy,
)
from supriya.querytree import QueryTreeGroup, QueryTreeSynth
from supriya.typing import Missing
from uqbar.containers import UniqueTreeTuple

import tloen.domain  # noqa
from tloen.midi import MidiMessage, NoteOffMessage, NoteOnMessage

logger = logging.getLogger("tloen.domain")


class ApplicationObject(UniqueTreeTuple):

    ### INITIALIZER ###

    def __init__(self, *, name=None):
        self._application: Optional["tloen.domain.Application"] = None
        UniqueTreeTuple.__init__(self, name=name)
        self._cached_state = self._get_state()

    ### SPECIAL METHODS ###

    def __str__(self):
        return "\n".join(
            [
                f"<{type(self).__name__}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _add_parameter(self, parameter):
        if parameter.name in self._parameters:
            raise ValueError(f"Parameter {parameter.name} already added")
        self._parameters[parameter.name] = parameter
        self._parameter_group._append(parameter)

    def _append(self, node):
        self._mutate(slice(len(self), len(self)), [node])

    def _applicate(self, new_application):
        self._debug_tree(self, "Applicating", suffix=hex(id(new_application)))
        if not hasattr(self, "uuid"):
            return
        if self.uuid in new_application._registry:
            raise RuntimeError
        new_application._registry[self.uuid] = self

    def _cleanup(self):
        pass

    def _deapplicate(self, old_application):
        self._debug_tree(self, "Deapplicating", suffix=repr(None))
        if not hasattr(self, "uuid"):
            return
        old_application._registry.pop(self.uuid)

    @classmethod
    def _debug_tree(cls, node, prefix, suffix=None):
        parts = [
            (prefix + ":").ljust(15),
            ".." * node.depth,
            " " if node.depth else "",
            type(node).__name__,
            f"({node.name})" if node.name else "",
            f" ({suffix})" if suffix else "",
        ]
        logger.debug("".join(parts))

    def _deserialize_parameters(self, parameters_data):
        from tloen.domain.parameters import ParameterObject

        for parameter_data in parameters_data:
            new_parameter = ParameterObject.deserialize(parameter_data)
            old_parameter = self.parameters.get(new_parameter.name)
            if old_parameter is not None:
                old_parameter._value = new_parameter.value
                old_parameter._uuid = new_parameter.uuid
            else:
                self._parameter_group._append(new_parameter)
                self._parameters[new_parameter.name] = new_parameter

    def _get_state(self):
        index = None
        if self.parent:
            index = self.parent.index(self)
        return dict(application=self.application, parent=self.parent, index=index)

    def _get_state_difference(self, **kwargs):
        # self._debug_tree(self, "Reconciling")
        old_state = self._cached_state
        self._cached_state = new_state = self._get_state()
        difference = {}
        for key in old_state:
            if old_state[key] == new_state[key]:
                continue
            difference[key] = old_state[key], new_state[key]
        return difference

    def _reconcile(self, **kwargs):
        difference = self._get_state_difference()
        if "application" in difference:
            old_application, new_application = difference.pop("application")
            if old_application:
                self._deapplicate(old_application)
            if new_application:
                self._applicate(new_application)
            for child in self:
                child._set(application=new_application)

    def _remove(self, node):
        index = self.index(node)
        self._mutate(slice(index, index + 1), [])

    def _replace(self, old_node, new_node):
        index = self.index(old_node)
        self._mutate(slice(index, index + 1), [new_node])

    def _serialize(self):
        serialized = {
            "kind": type(self).__name__,
            "meta": {
                "name": self.name,
                "uuid": str(self.uuid) if hasattr(self, "uuid") else None,
            },
            "spec": {
                "channel_count": getattr(self, "channel_count", None),
                "parameters": [],
            },
        }
        if (
            self.parent is not None
            and self.parent.parent is not None
            and hasattr(self.parent.parent, "uuid")
        ):
            serialized["meta"]["parent"] = str(self.parent.parent.uuid)
        auxiliary_entities = []
        for parameter in getattr(self, "parameters", {}).values():
            serialized["spec"]["parameters"].append(str(parameter.uuid))
            aux = parameter._serialize()
            auxiliary_entities.append(aux[0])
            auxiliary_entities.extend(aux[1])
        return serialized, auxiliary_entities

    def _set(
        self,
        application: Optional[Union[Missing, "tloen.domain.Application"]] = Missing(),
        **kwargs,
    ):
        if not isinstance(application, Missing):
            self._application = application
        self._reconcile()

    def _set_items(self, new_items, old_items, start_index, stop_index):
        UniqueTreeTuple._set_items(self, new_items, old_items, start_index, stop_index)
        for item in new_items:
            item._set(application=self.application)
        for item in old_items:
            item._set(application=None)

    ### PUBLIC METHODS ###

    @classmethod
    @asynccontextmanager
    async def lock(cls, objects, seconds=None):
        yield

    def rename(self, name):
        pass

    ### PUBLIC PROPERTIES ###

    @property
    def application(self) -> Optional["tloen.domain.Application"]:
        return self._application

    @property
    def cached_state(self) -> Mapping[str, Any]:
        return MappingProxyType(self._cached_state)

    @property
    def context(self) -> Optional["tloen.domain.Context"]:
        from .contexts import Context

        for parent in self.parentage:
            if isinstance(parent, Context):
                return parent
        return None

    @property
    def label(self):
        return self.name or type(self).__name__

    @property
    def provider(self):
        return None


class Allocatable(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self, *, channel_count=None, name=None):
        self._audio_bus_proxies: Dict[str, Union[BusProxy, BusGroupProxy]] = {}
        self._buffer_proxies = {}
        self._channel_count: Optional[int] = channel_count
        self._control_bus_proxies: Dict[str, Union[BusProxy, BusGroupProxy]] = {}
        self._is_active = True
        self._node_proxies: Dict[str, NodeProxy] = {}
        self._osc_callback_proxies: Dict[str, OscCallbackProxy] = {}
        self._provider: Optional[Provider] = None
        ApplicationObject.__init__(self, name=name)

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = self.name or type(self).__name__
        return "\n".join(
            [
                f"<{obj_name} [{node_proxy_id}]>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _activate(self):
        self._debug_tree(self, "Activating")
        self._is_active = True

    def _allocate(self, provider, target_node, add_action):
        self._debug_tree(
            self,
            "Allocating",
            suffix=f"{hex(id(provider))} {target_node!r} {add_action}",
        )

    def _deallocate(self, old_provider, *, dispose_only=False):
        self._debug_tree(self, "Deallocating", suffix=repr(None))
        node = self._node_proxies.pop("node", None)
        if node is not None and not dispose_only:
            node["gate"] = 0
        self._node_proxies.clear()
        for key, value in sorted(self._node_proxies.items()):
            if isinstance(value, SynthProxy):
                self._node_proxies.pop(key)["gate"] = 0
        while self._audio_bus_proxies:
            _, bus_proxy = self._audio_bus_proxies.popitem()
            bus_proxy.free()
        while self._buffer_proxies:
            _, buffer_proxy = self._buffer_proxies.popitem()
            buffer_proxy.free()
        while self._control_bus_proxies:
            _, bus_proxy = self._control_bus_proxies.popitem()
            bus_proxy.free()
        while self._osc_callback_proxies:
            _, osc_callback_proxy = self._osc_callback_proxies.popitem()
            osc_callback_proxy.unregister()

    def _deactivate(self):
        self._debug_tree(self, "Deactivating")
        self._is_active = False

    def _get_state(self):
        state = ApplicationObject._get_state(self)
        state.update(channel_count=self.effective_channel_count, provider=self.provider)
        return state

    def _move(self, target_node, add_action):
        self._debug_tree(
            self, "Moving", suffix=f"{target_node.identifier} {add_action}"
        )
        self.node_proxy.move(add_action=add_action, target_node=target_node)

    def _reallocate(self, difference):
        self._debug_tree(self, "Reallocating")

    def _reconcile(
        self,
        target_node: Optional[NodeProxy] = None,
        add_action: Optional[int] = None,
        dispose_only: bool = False,
        **kwargs,
    ):
        difference = self._get_state_difference()
        if "provider" in difference:
            old_provider, new_provider = difference.pop("provider")
            if old_provider:
                self._deallocate(old_provider, dispose_only=dispose_only)
                for child in self:
                    child._set(provider=None, dispose_only=True)
            if new_provider:
                for parameter in getattr(self, "parameters", {}).values():
                    parameter._preallocate(new_provider, self)
                self._allocate(new_provider, target_node, add_action)
                target_node, add_action = self.node_proxy, AddAction.ADD_TO_HEAD
                for child in self:
                    child._set(
                        provider=new_provider,
                        target_node=target_node,
                        add_action=add_action,
                    )
                    if isinstance(child, Allocatable) and child.node_proxy is not None:
                        target_node, add_action = child.node_proxy, AddAction.ADD_AFTER
            self._reconcile_dependents()
        elif self.provider:
            if "index" in difference or "parent" in difference:
                self._move(target_node, add_action)
            if "channel_count" in difference:
                self._reallocate(difference)
            for child in self:
                child._reconcile()
            self._reconcile_dependents()
        if "application" in difference:
            old_application, new_application = difference.pop("application")
            if old_application:
                self._deapplicate(old_application)
            if new_application:
                self._applicate(new_application)
            for child in self:
                child._set(application=new_application)

    def _reconcile_dependents(self):
        pass

    def _set(
        self,
        application: Optional[Union[Missing, "tloen.domain.Application"]] = Missing(),
        channel_count: Optional[Union[Missing, int]] = Missing(),
        provider: Optional[Union[Missing, Provider]] = Missing(),
        target_node: Optional[NodeProxy] = None,
        add_action: Optional[AddAction] = None,
        **kwargs,
    ):
        if not isinstance(application, Missing):
            self._application = application
            if application is None:
                provider = None
        if not isinstance(provider, Missing):
            self._provider = provider
        if not isinstance(channel_count, Missing):
            self._channel_count = channel_count
        self._reconcile(target_node=target_node, add_action=add_action, **kwargs)

    def _collect_for_cleanup(self, new_items, old_items):
        return []

    def _set_items(self, new_items, old_items, start_index, stop_index):
        target_node, add_action = self, AddAction.ADD_TO_HEAD
        if new_items:
            if start_index == len(self):
                target_node, add_action = self, AddAction.ADD_TO_TAIL
            elif start_index:
                while start_index and not isinstance(self[start_index], Allocatable):
                    start_index -= 1
                if start_index:
                    target_node, add_action = self[start_index], AddAction.ADD_AFTER
        to_cleanup = self._collect_for_cleanup(new_items, old_items)
        UniqueTreeTuple._set_items(self, new_items, old_items, start_index, stop_index)
        for item in new_items:
            item._set(
                application=self.application,
                provider=self.provider,
                target_node=target_node.node_proxy,
                add_action=add_action,
            )
            if isinstance(item, Allocatable) and item.node_proxy is not None:
                target_node, add_action = item, AddAction.ADD_AFTER
        for item in old_items:
            item._set(application=None, provider=None)
        for item in to_cleanup:
            item._cleanup()

    ### PUBLIC METHODS ###

    @classmethod
    @asynccontextmanager
    async def lock(cls, objects, seconds=None):
        exit_stack = AsyncExitStack()
        async with exit_stack:
            providers = set()
            for object_ in objects:
                provider = getattr(object_, "provider", None)
                if provider is not None and provider not in providers:
                    await exit_stack.enter_async_context(provider.at(seconds))
                    providers.add(provider)
            yield

    async def query(self):
        if self.provider.server is None:
            raise ValueError
        query_tree = {}
        stack = [self.node_proxy.identifier]
        while stack:
            node_id = stack.pop()
            if node_id in query_tree:
                continue
            response = await NodeQueryRequest(node_id).communicate_async(
                server=self.provider.server
            )
            if isinstance(response, FailResponse):
                raise RuntimeError(repr(response))
            if (response.next_node_id or -1) > 0:
                stack.append(response.next_node_id)
            if (response.head_node_id or -1) > 0:
                stack.append(response.head_node_id)
            if response.is_group:
                query_tree[node_id] = QueryTreeGroup.from_response(response)
            else:
                # Run hypothetical SynthQueryRequest here
                synth_response = await SynthQueryRequest(node_id).communicate_async(
                    server=self.provider.server
                )
                query_tree[node_id] = QueryTreeSynth.from_response(synth_response)
            if response.parent_id in query_tree:
                query_tree[response.parent_id]._children += (query_tree[node_id],)
        query_tree_group = query_tree[self.node_proxy.identifier]
        return query_tree_group.annotate(self.provider.annotation_map)

    ### PUBLIC PROPERTIES ###

    @property
    def audio_bus_proxies(self) -> Mapping[str, Union[BusProxy, BusGroupProxy]]:
        return MappingProxyType(self._audio_bus_proxies)

    @property
    def buffer_proxies(self) -> Mapping[str, Any]:
        return MappingProxyType(self._buffer_proxies)

    @property
    def channel_count(self) -> Optional[int]:
        return self._channel_count

    @property
    def control_bus_proxies(self) -> Mapping[str, Union[BusProxy, BusGroupProxy]]:
        return MappingProxyType(self._control_bus_proxies)

    @property
    def effective_channel_count(self) -> int:
        for object_ in self.parentage:
            channel_count = getattr(object_, "channel_count", None)
            if channel_count:
                return channel_count
        return 2

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def node_proxies(self) -> Mapping[str, NodeProxy]:
        return MappingProxyType(self._node_proxies)

    @property
    def node_proxy(self) -> Optional[NodeProxy]:
        return self._node_proxies.get("node")

    @property
    def osc_callback_proxies(self) -> Mapping[str, OscCallbackProxy]:
        return MappingProxyType(self._osc_callback_proxies)

    @property
    def provider(self) -> Optional[Provider]:
        return self._provider


class Container(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self, *, label=None):
        ApplicationObject.__init__(self)
        self._label = label

    ### SPECIAL METHODS ###

    def __str__(self):
        return "\n".join(
            [
                f"<{self.label}>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    @property
    def label(self):
        return self._label or type(self).__name__


class AllocatableContainer(Allocatable):

    ### INITIALIZER ###

    def __init__(
        self,
        target_node_name: str,
        add_action: int,
        *,
        label=None,
        target_node_parent: Optional[Allocatable] = None,
    ):
        Allocatable.__init__(self)
        self._target_node_name = str(target_node_name)
        self._add_action = AddAction.from_expr(add_action)
        self._label = label
        self._target_node_parent = target_node_parent

    ### SPECIAL METHODS ###

    def __str__(self):
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        return "\n".join(
            [
                f"<{self.label} [{node_proxy_id}]>",
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        parent = self.target_node_parent or self.parent
        target_node = parent.node_proxies[self.target_node_name]
        self._node_proxies["node"] = provider.add_group(
            target_node=target_node, add_action=self.add_action, name=self.label
        )

    ### PUBLIC PROPERTIES ###

    @property
    def add_action(self):
        return self._add_action

    @property
    def label(self):
        return self._label or type(self).__name__

    @property
    def target_node_name(self):
        return self._target_node_name

    @property
    def target_node_parent(self):
        return self._target_node_parent


class Mixer:
    def __init__(self):
        from .tracks import TrackObject

        self._soloed_tracks: Set[TrackObject] = set()


class Performable(ApplicationObject):

    ### CLASS VARIABLES ###

    class CaptureEntry(NamedTuple):
        moment: Moment
        label: str
        message: MidiMessage

    class Capture:
        def __init__(self, performable: "Performable"):
            self.performable = performable
            self.entries: List["Performable.CaptureEntry"] = []

        def __enter__(self):
            self.performable._captures.add(self)
            self.entries[:] = []
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.performable._captures.remove(self)

        def __getitem__(self, i):
            return self.entries[i]

        def __iter__(self):
            return iter(self.entries)

        def __len__(self):
            return len(self.entries)

    ### INITIALIZER ###

    def __init__(self):
        self._input_pitches: Dict[float, List[float]] = {}
        self._output_pitches: Set[float] = set()
        self._captures: Set["Performable.Capture"] = set()

    ### PRIVATE METHODS ###

    def _next_performer(self) -> Optional[Callable]:
        if self.parent is None:
            return None
        index = self.parent.index(self)
        if index < len(self.parent) - 1:
            return self.parent[index + 1]._perform_input
        for parent in self.parentage[1:]:
            if parent is None:
                return None
            elif hasattr(parent, "_perform_output"):
                return parent._perform_output
        return None

    def _perform_input(self, moment, midi_messages):
        for message in midi_messages:
            self._update_captures(moment, message, "I")
            if isinstance(message, NoteOnMessage):
                self._input_pitches[message.pitch] = [message.pitch]
            elif (
                isinstance(message, NoteOffMessage)
                and message.pitch in self._input_pitches
            ):
                self._input_pitches.pop(message.pitch, None)
        return self._perform_output, midi_messages

    def _perform_output(self, moment, midi_messages):
        next_performer = self._next_performer()
        for message in midi_messages:
            self._update_captures(moment, message, "O")
            if isinstance(message, NoteOnMessage):
                if message.pitch in self._output_pitches:
                    continue
                else:
                    self._output_pitches.add(message.pitch)
            elif isinstance(message, NoteOffMessage):
                if message.pitch not in self._output_pitches:
                    continue
                else:
                    self._output_pitches.remove(message.pitch)
            yield next_performer, [message]

    @classmethod
    def _perform_loop(cls, moment, performer, midi_messages):
        stack: Deque = deque()
        stack.append((performer, midi_messages))
        out_messages = []
        while stack:
            in_performer, in_messages = stack.popleft()
            for out_performer, out_messages in in_performer(moment, in_messages):
                if out_messages and out_performer is not None:
                    stack.append((out_performer, out_messages))
        return out_messages

    def _update_captures(self, moment, message, label):
        if not self._captures:
            return
        entry = self.CaptureEntry(moment=moment, message=message, label=label)
        for capture in self._captures:
            capture.entries.append(entry)

    ### PUBLIC METHODS ###

    def capture(self):
        return self.Capture(self)

    async def perform(self, midi_messages, moment=None):
        self._debug_tree(
            self, "Perform", suffix=repr([type(_).__name__ for _ in midi_messages])
        )
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            self._perform_loop(moment, self._perform_input, midi_messages)
