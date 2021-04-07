import asyncio
from typing import Set

from .bases import ApplicationObject
from .events import TransportStarted, TransportStopped


class Transport(ApplicationObject):

    ### INITIALIZER ###

    def __init__(self):
        ApplicationObject.__init__(self)
        self._dependencies: Set[ApplicationObject] = set()
        self._tick_event_id = None

    ### PUBLIC METHODS ###

    async def start(self):
        async with self.lock([self]):
            self._tick_event_id = self.application.clock.cue(
                self.application._callback_transport_tick
            )
            await asyncio.gather(*[_._start() for _ in self._dependencies])
            await self.application.clock.start()
        self.application.pubsub.publish(TransportStarted())

    async def stop(self):
        await self.application.clock.stop()
        async with self.lock([self]):
            await asyncio.gather(*[_._stop() for _ in self._dependencies])
            self.application.clock.cancel(self._tick_event_id)
        self.application.pubsub.publish(TransportStopped())
