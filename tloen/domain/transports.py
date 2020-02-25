import enum
from typing import Dict, Set, Union

from supriya.clock import AsyncTempoClock

from .. import events
from .bases import ApplicationObject
from .parameters import Action, Parameter, ParameterGroup


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
        self._parameters: Dict[str, Union[Action, Parameter]] = {}
        self._clock = AsyncTempoClock()
        self._dependencies: Set[ApplicationObject] = set()
        self._mutate(slice(None), [self._parameter_group])
        self._tick_event_id = None

    ### PRIVATE METHODS ###

    async def _application_perform_callback(
        self, current_moment, desired_moment, event, midi_message
    ):
        await self.application.perform([midi_message], moment=current_moment)

    def _tick_callback(self, current_moment, desired_moment, event):
        self.application.pubsub.publish(events.TransportTicked(desired_moment))
        return 1 / desired_moment.time_signature[1] / 4

    ### PUBLIC METHODS ###

    async def cue(self, *args, **kwargs):
        return await self._clock.cue(*args, **kwargs)

    async def cancel(self, *args, **kwargs):
        return await self._clock.cancel(*args, **kwargs)

    async def perform(self, midi_messages):
        if (
            self.application is None
            or self.application.status != self.application.Status.REALTIME
        ):
            return
        self._debug_tree(
            self, "Perform", suffix=repr([type(_).__name__ for _ in midi_messages])
        )
        self.schedule(self._application_perform_callback, args=midi_messages)
        if not self.is_running:
            await self.start()

    async def schedule(self, *args, **kwargs):
        return await self._clock.schedule(*args, **kwargs)

    def serialize(self):
        return {
            "kind": type(self).__name__,
            "spec": {
                "tempo": self._clock.beats_per_minute,
                "time_signature": list(self._clock.time_signature),
            },
        }

    @classmethod
    async def deserialize(cls, data, transport_object):
        await transport_object.set_tempo(data["spec"]["tempo"])
        await transport_object.set_time_signature(*data["spec"]["time_signature"])

    async def set_tempo(self, beats_per_minute: float):
        await self._clock.change(beats_per_minute=beats_per_minute)

    async def set_time_signature(self, numerator, denominator):
        await self._clock.change(time_signature=[numerator, denominator])

    async def start(self):
        async with self.lock([self]):
            self._tick_event_id = await self.cue(self._tick_callback)
            for dependency in self._dependencies:
                dependency._start()
            await self._clock.start()
        self.application.pubsub.publish(events.TransportStarted())

    async def stop(self):
        await self._clock.stop()
        async with self.lock([self]):
            for dependency in self._dependencies:
                dependency._stop()
            await self.application.flush()
            await self.cancel(self._tick_event_id)
        self.application.pubsub.publish(events.TransportStopped())

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
