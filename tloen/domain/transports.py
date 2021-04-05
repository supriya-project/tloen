import asyncio
import dataclasses
import enum
from typing import Dict, Optional, Set, Tuple

from supriya.clocks import AsyncTempoClock, Moment

from ..bases import Event
from .bases import ApplicationObject
from .parameters import ParameterGroup, ParameterObject


class Transport(ApplicationObject):

    ### CLASS VARIABLES ###

    class EventType(enum.IntEnum):
        CHANGE = 0
        SCHEDULE = 1
        MIDI_PERFORM = 2
        DEVICE_NOTE_OFF = 3
        DEVICE_NOTE_ON = 4
        CLIP_LAUNCH = 5
        CLIP_EDIT = 6
        CLIP_PERFORM = 7

    ### INITIALIZER ###

    def __init__(self):
        ApplicationObject.__init__(self)
        self._parameter_group = ParameterGroup()
        self._parameters: Dict[str, ParameterObject] = {}
        self._clock = AsyncTempoClock()
        self._dependencies: Set[ApplicationObject] = set()
        self._mutate(slice(None), [self._parameter_group])
        self._tick_event_id = None

    ### PRIVATE METHODS ###

    async def _application_perform_callback(self, clock_context, midi_message):
        await self.application.perform(
            [midi_message], moment=clock_context.current_moment
        )

    @classmethod
    async def _deserialize(cls, data, transport_object):
        await transport_object.set_tempo(data["spec"]["tempo"])
        await transport_object.set_time_signature(*data["spec"]["time_signature"])

    def _serialize(self):
        return {
            "kind": type(self).__name__,
            "spec": {
                "tempo": self._clock.beats_per_minute,
                "time_signature": list(self._clock.time_signature),
            },
        }

    def _tick_callback(self, clock_context):
        self.application.pubsub.publish(TransportTicked(clock_context.desired_moment))
        return 1 / clock_context.desired_moment.time_signature[1] / 4

    ### PUBLIC METHODS ###

    async def cue(self, *args, **kwargs) -> int:
        return self._clock.cue(*args, **kwargs)

    async def cancel(self, *args, **kwargs) -> Optional[Tuple]:
        return self._clock.cancel(*args, **kwargs)

    async def perform(self, midi_messages):
        if (
            self.application is None
            or self.application.status != self.application.Status.REALTIME
        ):
            return
        self._debug_tree(
            self, "Perform", suffix=repr([type(_).__name__ for _ in midi_messages])
        )
        await self.schedule(self._application_perform_callback, args=midi_messages)
        if not self.is_running:
            await self.start()

    async def reschedule(self, *args, **kwargs) -> Optional[int]:
        return self._clock.reschedule(*args, **kwargs)

    async def schedule(self, *args, **kwargs) -> int:
        return self._clock.schedule(*args, **kwargs)

    async def set_tempo(self, beats_per_minute: float):
        self._clock.change(beats_per_minute=beats_per_minute)

    async def set_time_signature(self, numerator, denominator):
        self._clock.change(time_signature=[numerator, denominator])

    async def start(self):
        async with self.lock([self]):
            self._tick_event_id = await self.cue(self._tick_callback)
            await asyncio.gather(*[_._start() for _ in self._dependencies])
            await self._clock.start()
        self.application.pubsub.publish(TransportStarted())

    async def stop(self):
        await self._clock.stop()
        async with self.lock([self]):
            await asyncio.gather(*[_._stop() for _ in self._dependencies])
            await self.cancel(self._tick_event_id)
        self.application.pubsub.publish(TransportStopped())

    ### PUBLIC PROPERTIES ###

    @property
    def clock(self):
        return self._clock

    @property
    def is_running(self):
        return self._clock.is_running

    @property
    def parameters(self):
        return self._parameters


@dataclasses.dataclass
class TransportStarted(Event):
    pass


@dataclasses.dataclass
class TransportStopped(Event):
    pass


@dataclasses.dataclass
class TransportTicked(Event):  # TODO: ClipView needs to know start delta
    moment: Moment
