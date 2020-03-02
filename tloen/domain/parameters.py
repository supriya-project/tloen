from typing import Callable, Optional
from uuid import UUID, uuid4

from supriya.clock import Moment
from supriya.enums import AddAction, DoneAction
from supriya.synthdefs import SynthDefBuilder
from supriya.ugens import Line, Out
from supriya.utils import locate

from .bases import Allocatable, AllocatableContainer, ApplicationObject


class ParameterSpec:
    def __init__(self, default):
        self._default = default

    def __call__(self, value):
        return ...

    @property
    def default(self):
        return self._default


class Boolean(ParameterSpec):

    ### INITIALIZER ###

    def __init__(self, default=True):
        ParameterSpec.__init__(self, bool(default))

    ### SPECIAL METHODS ###

    def __call__(self, value):
        return bool(value)

    def serialize(self):
        return {"type": type(self).__name__.lower(), "default": self.default}


class Float(ParameterSpec):

    ### INITIALIZER ###

    def __init__(
        self, default: float = 0.0, minimum: float = 0.0, maximum: float = 1.0
    ):
        self.minimum, self.maximum = sorted(float(_) for _ in [minimum, maximum])
        ParameterSpec.__init__(self, self(default))

    ### SPECIAL METHODS ###

    def __call__(self, value):
        value = float(value)
        if value < self.minimum:
            return self.minimum
        if value > self.maximum:
            return self.maximum
        return value

    def serialize(self):
        return {
            "type": type(self).__name__.lower(),
            "default": self.default,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


class Integer(ParameterSpec):

    ### INITIALIZER ###

    def __init__(self, default: int = 0, minimum: int = 0, maximum: int = 1):
        self.minimum, self.maximum = sorted(int(_) for _ in [minimum, maximum])
        ParameterSpec.__init__(self, self(default))

    ### SPECIAL METHODS ###

    def __call__(self, value):
        value = int(value)
        if value < self.minimum:
            return self.minimum
        if value > self.maximum:
            return self.maximum
        return value

    def serialize(self):
        return {
            "type": type(self).__name__.lower(),
            "default": self.default,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


class Null(ParameterSpec):
    def __init__(self):
        ParameterSpec.__init__(self, None)

    def __call__(self, value):
        return None

    def serialize(self):
        return {"type": type(self).__name__.lower()}


class ParameterObject(ApplicationObject):
    def __init__(self, *, is_builtin: bool = False, uuid: UUID = None):
        self._client: Optional[ApplicationObject] = None
        self._is_builtin = bool(is_builtin)
        self._uuid = uuid or uuid4()

    ### PRIVATE METHODS ###

    def _applicate(self, new_application):
        Allocatable._applicate(self, new_application)
        self._client = self.parent.parent

    def _deapplicate(self, old_application):
        Allocatable._deapplicate(self, old_application)
        self._client = None

    def _preallocate(self, provider, client):
        ...

    ### PUBLIC METHODS ###

    @classmethod
    def deserialize(cls, data):
        return {
            "BufferParameter": BufferParameter,
            "BusParameter": BusParameter,
            "CallbackParameter": CallbackParameter,
        }[data["kind"]].deserialize(data)

    ### PUBLIC PROPERTIES ###

    @property
    def client(self) -> Optional[ApplicationObject]:
        return self._client

    @property
    def uuid(self) -> UUID:
        return self._uuid


class BufferParameter(Allocatable, ParameterObject):

    ### INITIALIZER ###

    def __init__(
        self,
        name: str,
        *,
        channel_count: Optional[int] = None,
        path: str = None,
        is_builtin: bool = False,
        uuid: UUID = None,
    ):
        ParameterObject.__init__(self, is_builtin=is_builtin, uuid=uuid)
        Allocatable.__init__(self, name=name)
        self._path = path
        self._channel_count = channel_count

    ### SPECIAL METHODS ###

    def __float__(self):
        return float(self.bus_proxy)

    def __int__(self):
        return int(self.bus_proxy)

    def __str__(self):
        buffer_proxy_id = (
            int(self.buffer_proxy) if self.buffer_proxy is not None else "?"
        )
        obj_name = type(self).__name__
        return "\n".join(
            [
                f'<{obj_name} "{self.name}" ({self.path}) [{buffer_proxy_id}] {self.uuid}>',
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _allocate_buffer(self, provider):
        self._buffer_proxies["buffer_"] = provider.add_buffer(
            channel_count=self.channel_count, file_path=locate(self.path),
        )

    def _preallocate(self, provider, client):
        self._client = client
        self._provider = provider
        self._debug_tree(self, "Pre-Allocating", suffix=f"{hex(id(provider))}")
        if self.path is None:
            return
        self._allocate_buffer(provider)

    ### PUBLIC METHODS ###

    @classmethod
    def deserialize(cls, data):
        ...

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(channel_count=None, path=self.path)
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, path, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            if path == self.path:
                return
            self._path = path
            if self.provider is None:
                return
            # Deallocate old buffer after allocating new buffer
            # TODO: Deallocation should be aware of what notes are using the buffer
            old_buffer = self.buffer_proxy
            self._allocate_buffer(self.provider)
            if old_buffer is not None:
                old_buffer.free()

    ### PUBLIC PROPERTIES ###

    @property
    def buffer_proxy(self):
        return self._buffer_proxies.get("buffer_")

    @property
    def channel_count(self):
        return self._channel_count

    @property
    def path(self):
        return self._path


class BusParameter(Allocatable, ParameterObject):

    ### INITIALIZER ###

    def __init__(
        self,
        name: str,
        spec: ParameterSpec,
        *,
        is_builtin: bool = False,
        uuid: UUID = None,
    ):
        ParameterObject.__init__(self, is_builtin=is_builtin, uuid=uuid)
        Allocatable.__init__(self, name=name)
        self._spec = spec
        self._value = self.spec.default

    ### SPECIAL METHODS ###

    def __float__(self):
        return float(self.bus_proxy)

    def __int__(self):
        return int(self.bus_proxy)

    def __str__(self):
        bus_proxy_id = int(self.bus_proxy) if self.bus_proxy is not None else "?"
        node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f'<{obj_name} "{self.name}" ({self.value}) [{node_proxy_id}] [{bus_proxy_id}] {self.uuid}>',
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        self._node_proxies["node"] = provider.add_group(
            target_node=target_node, add_action=add_action, name=self.label
        )

    @classmethod
    def _build_ramp_synthdef(cls):
        with SynthDefBuilder(
            out=(0.0, "scalar"),
            start_value=(0.0, "scalar"),
            stop_value=(1.0, "scalar"),
            total_time=(1.0, "scalar"),
            initial_time=(0.0, "scalar"),
        ) as builder:
            line = Line.kr(
                start=builder["initial_time"] / builder["total_time"],
                stop=1.0,
                duration=builder["total_time"] - builder["initial_time"],
                done_action=DoneAction.NOTHING,
            )
            Out.kr(
                bus=builder["out"],
                source=line.scale(
                    0.0, 1.0, builder["start_value"], builder["stop_value"]
                ),
            )
        return builder.build("mixer/ramp")

    def _preallocate(self, provider, client):
        self._debug_tree(self, "Pre-Allocating", suffix=f"{hex(id(provider))}")
        self._client = client
        self._provider = provider
        self._control_bus_proxies["bus"] = provider.add_bus("control")
        self._control_bus_proxies["bus"].set_(self.spec.default)

    ### PUBLIC METHODS ###

    @classmethod
    def deserialize(cls, data):
        if data["spec"].get("spec"):
            spec = ParameterSpec.deserialize(data["spec"]["spec"])
        else:
            spec = Float()
        return cls(
            name=data["meta"]["name"],
            uuid=data["meta"]["uuid"],
            spec=spec,
        )

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(channel_count=None, value=self.value)
        if not self._is_builtin:
            serialized["spec"]["spec"] = self.spec.serialize()
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, value, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            self._value = self.spec(value)
            if self.bus_proxy is not None:
                self.bus_proxy.set_(self._value)

    ### PUBLIC PROPERTIES ###

    @property
    def bus_proxy(self):
        return self._control_bus_proxies.get("bus")

    @property
    def spec(self) -> ParameterSpec:
        return self._spec

    @property
    def value(self):
        return self._value


class CallbackParameter(ParameterObject):

    ### INITIALIZER ###

    def __init__(
        self,
        name: str,
        spec: ParameterSpec,
        callback: Callable,
        *,
        is_builtin: bool = False,
        uuid: UUID = None,
    ):
        ParameterObject.__init__(self, is_builtin=is_builtin, uuid=uuid)
        ApplicationObject.__init__(self, name=name)
        self._callback = callback
        self._spec = spec
        self._value = self.spec.default

    ### SPECIAL METHODS ###

    def __str__(self):
        obj_name = type(self).__name__
        return "\n".join([f'<{obj_name} "{self.name}" ({self.value}) {self.uuid}>'])

    ### PRIVATE METHODS ###

    def _preallocate(self, provider, client):
        self._debug_tree(self, "Pre-Allocating", suffix=f"{hex(id(provider))}")
        self._client = client

    ### PUBLIC METHODS ###

    @classmethod
    def deserialize(cls, data):
        ...

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"]["value"] = self.value
        if not self._is_builtin:
            serialized["spec"]["spec"] = self.spec.serialize()
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, value, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            self._value = self.spec(value)
            if self.client is not None:
                self.callback(self.client, self.value)

    ### PUBLIC PROPERTIES ###

    @property
    def callback(self) -> Callable:
        return self._callback

    @property
    def spec(self) -> ParameterSpec:
        return self._spec

    @property
    def value(self):
        return self._value


class ParameterGroup(AllocatableContainer):
    def __init__(self):
        AllocatableContainer.__init__(
            self,
            target_node_name="node",
            add_action=AddAction.ADD_TO_HEAD,
            label="Parameters",
        )

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        target_node = self.parent.node_proxies[self.target_node_name]
        if any(isinstance(x, BusParameter) for x in self):
            self._node_proxies["node"] = provider.add_group(
                target_node=target_node, add_action=self.add_action, name=self.label
            )
