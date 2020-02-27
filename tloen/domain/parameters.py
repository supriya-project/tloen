from typing import Callable, Optional
from uuid import UUID, uuid4

from supriya.clock import Moment
from supriya.enums import AddAction, DoneAction
from supriya.synthdefs import SynthDefBuilder
from supriya.ugens import Line, Out

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


class Parameter(Allocatable):

    ### INITIALIZER ###

    def __init__(self, name, spec, *, callback=None, has_bus=False, uuid=None):
        if not name:
            raise ValueError(name)
        Allocatable.__init__(self, channel_count=1, name=name)
        if not isinstance(spec, ParameterSpec):
            raise ValueError(spec)
        if callback is not None and not callable(callback):
            raise ValueError(callback)
        self._callback = callback
        self._client = None
        self._has_bus = bool(has_bus)
        self._is_builtin = False
        self._spec = spec
        self._value = self.spec.default
        self._uuid = uuid or uuid4()

    ### SPECIAL METHODS ###

    def __str__(self):
        if self.has_bus:
            bus_proxy_id = int(self.bus_proxy) if self.bus_proxy is not None else "?"
            node_proxy_id = int(self.node_proxy) if self.node_proxy is not None else "?"
        else:
            bus_proxy_id, node_proxy_id = "-", "-"
        obj_name = type(self).__name__
        return "\n".join(
            [
                f'<{obj_name} "{self.name}" {self.value} [{node_proxy_id}] [{bus_proxy_id}] {self.uuid}>',
                *(f"    {line}" for child in self for line in str(child).splitlines()),
            ]
        )

    ### PRIVATE METHODS ###

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)
        if not self.has_bus:
            return
        self._node_proxies["node"] = provider.add_group(
            target_node=target_node, add_action=add_action, name=self.label
        )

    def _applicate(self, new_application):
        Allocatable._applicate(self, new_application)
        self._client = self.parent.parent

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

    def _deapplicate(self, old_application):
        Allocatable._deapplicate(self, old_application)
        self._client = None

    def _preallocate(self, provider, client):
        self._debug_tree(self, "Pre-Allocating", suffix=f"{hex(id(provider))}")
        if not self.has_bus:
            return
        self._control_bus_proxies["?"] = provider.add_bus("control")
        self._control_bus_proxies["?"].set_(self.spec.default)

    ### PUBLIC METHODS ###

    def get(self):
        pass

    def modulate(self):
        modulation = self.node_proxies.get("modulation")
        if modulation is not None:
            modulation.free()

    async def ramp(
        self, from_value, to_value, total_time, *, initial_time=0, moment=None
    ):
        # from_ = self.spec(from_value)
        # to_ = self.spec(to_value)
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            modulation = self.node_proxies.get("modulation")
            if modulation is not None:
                modulation.free()

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(
            bussed=self.has_bus or None if not self.is_builtin else None,
            channel_count=None,
            value=self.value,
        )
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    @classmethod
    def deserialize(cls, data):
        parameter = cls(
            name=data["meta"].get("name"),
            uuid=UUID(data["meta"]["uuid"]),
            has_bus=data["spec"].get("bussed"),
            spec=Float(),
        )
        parameter._value = data["spec"]["value"]
        return parameter

    async def set_(self, value, *, moment=None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            self._value = self.spec(value)
            modulation = self.node_proxies.get("modulation")
            if modulation is not None:
                modulation.free()
            if self.bus_proxy is not None:
                self.bus_proxy.set_(self._value)
            if self.callback is not None and self.client is not None:
                self.callback(self.client, self._value)

    ### PUBLIC PROPERTIES ###

    @property
    def bus_proxy(self):
        return self._control_bus_proxies.get("?")

    @property
    def callback(self):
        return self._callback

    @property
    def client(self) -> ApplicationObject:
        return self._client

    @property
    def has_bus(self):
        return self._has_bus

    @property
    def is_builtin(self):
        return self._is_builtin

    @property
    def spec(self) -> ParameterSpec:
        return self._spec

    @property
    def uuid(self) -> UUID:
        return self._uuid

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
        if any(x.has_bus for x in self):
            self._node_proxies["node"] = provider.add_group(
                target_node=target_node, add_action=self.add_action, name=self.label
            )


class ParameterObject(ApplicationObject):
    def __init__(self, uuid: UUID = None):
        self._client: Optional[ApplicationObject] = None
        self._uuid = uuid or uuid4()

    ### PRIVATE METHODS ###

    def _applicate(self, new_application):
        Allocatable._applicate(self, new_application)
        self._client = self.parent.parent

    def _deapplicate(self, old_application):
        Allocatable._deapplicate(self, old_application)
        self._client = None

    ### PUBLIC PROPERTIES ###

    @property
    def client(self) -> Optional[ApplicationObject]:
        return self._client

    @property
    def uuid(self) -> UUID:
        return self._uuid


class BusParameter(Allocatable, ParameterObject):

    ### INITIALIZER ###

    def __init__(self, name: str, spec: ParameterSpec, *, uuid: UUID = None):
        ParameterObject.__init__(self, uuid=uuid)
        Allocatable.__init__(self, name=name)
        self._spec = spec
        self._value = self.spec.default

    ### SPECIAL METHODS ###

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
        if not self.has_bus:
            return
        self._control_bus_proxies["bus"] = provider.add_bus("control")
        self._control_bus_proxies["bus"].set_(self.spec.default)

    ### PUBLIC METHODS ###

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(
            channel_count=None, spec=self.spec.serialize(), value=self.value,
        )
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, value, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            if self.application is None:
                return
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


class BufferParameter(Allocatable, ParameterObject):

    ### INITIALIZER ###

    def __init__(self, name: str, *, path: str = None, uuid: UUID = None):
        ParameterObject.__init__(self, uuid=uuid)
        Allocatable.__init__(self, name=name)
        self._path = path

    ### SPECIAL METHODS ###

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

    def _allocate(self, provider, target_node, add_action):
        Allocatable._allocate(self, provider, target_node, add_action)

    ### PUBLIC METHODS ###

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(
            channel_count=None, path=self.path,
        )
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, path, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            if self.application is None:
                return
            if path == self.path:
                return
            self._path = path

    ### PUBLIC PROPERTIES ###

    @property
    def buffer_proxy(self):
        return self._buffer_proxy

    @property
    def path(self):
        return self.path


class CallbackParameter(ParameterObject):

    ### INITIALIZER ###

    def __init__(
        self, name: str, spec: ParameterSpec, callback: Callable, *, uuid: UUID = None
    ):
        ParameterObject.__init__(self, uuid=uuid)
        ApplicationObject.__init__(self, name=name)
        self._callback = callback
        self._spec = spec
        self._value = self.spec.default

    ### SPECIAL METHODS ###

    def __str__(self):
        obj_name = type(self).__name__
        return "\n".join([f'<{obj_name} "{self.name}" ({self.value}) {self.uuid}>'])

    ### PUBLIC METHODS ###

    def serialize(self):
        serialized = super().serialize()
        serialized["spec"].update(
            spec=self.spec.serialize(), value=self.value,
        )
        for mapping in [serialized["meta"], serialized.get("spec", {}), serialized]:
            for key in tuple(mapping):
                if mapping[key] is None:
                    mapping.pop(key)
        return serialized

    async def set_(self, value, *, moment: Moment = None):
        async with self.lock(
            [self], seconds=moment.seconds if moment is not None else None
        ):
            if self.application is None:
                return
            self._value = self.spec(value)
            self.callback(self._value)

    ### PUBLIC PROPERTIES ###

    @property
    def callback(self) -> Callable:
        return self.callback

    @property
    def spec(self) -> ParameterSpec:
        return self._spec

    @property
    def value(self):
        return self._value
