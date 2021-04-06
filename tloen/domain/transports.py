import asyncio
from typing import Set

from .bases import ApplicationObject
from .enums import ApplicationStatus
from .events import TransportStarted, TransportStopped, TransportTicked


class Transport(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self):
        ApplicationObject.__init__(self)
        self._dependencies: Set[ApplicationObject] = set()
        self._tick_event_id = None

    ### PRIVATE METHODS ###

    async def _application_perform_callback(self, clock_context, midi_message):
        await self.application.perform(
            [midi_message], moment=clock_context.current_moment
        )

    @classmethod
    async def _deserialize(cls, data, transport_object):
        # await transport_object.set_tempo(data["spec"]["tempo"])
        # await transport_object.set_time_signature(*data["spec"]["time_signature"])
        pass

    def _serialize(self):
        return {
            "kind": type(self).__name__,
            "spec": {
                "tempo": self.application.clock.beats_per_minute,
                "time_signature": list(self.application.clock.time_signature),
            },
        }

    def _tick_callback(self, clock_context):
        self.application.pubsub.publish(TransportTicked(clock_context.desired_moment))
        return 1 / clock_context.desired_moment.time_signature[1] / 4

    ### PUBLIC METHODS ###

    async def perform(self, midi_messages):
        if (
            self.application is None
            or self.application.status != ApplicationStatus.REALTIME
        ):
            return
        self._debug_tree(
            self, "Perform", suffix=repr([type(_).__name__ for _ in midi_messages])
        )
        self.application.clock.schedule(
            self._application_perform_callback, args=midi_messages
        )
        if not self.is_running:
            await self.start()

    async def start(self):
        async with self.lock([self]):
            self._tick_event_id = self.application.clock.cue(self._tick_callback)
            await asyncio.gather(*[_._start() for _ in self._dependencies])
            await self.application.clock.start()
        self.application.pubsub.publish(TransportStarted())

    async def stop(self):
        await self.application.clock.stop()
        async with self.lock([self]):
            await asyncio.gather(*[_._stop() for _ in self._dependencies])
            self.application.clock.cancel(self._tick_event_id)
        self.application.pubsub.publish(TransportStopped())

    ### PUBLIC PROPERTIES ###

    @property
    def clock(self):
        return self.application.clock

    @property
    def is_running(self):
        return self.application.clock.is_running
