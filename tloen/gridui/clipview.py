from functools import singledispatchmethod
from typing import Dict
from uuid import UUID

from monome import GridApp, GridBuffer

from ..domain.bases import ApplicationObject
from ..domain.transports import TransportStopped, TransportTicked
from ..pubsub import PubSub


class ClipView(GridApp):
    def __init__(self, pubsub=None, registry=None):
        GridApp.__init__(self)
        self.pubsub = pubsub or PubSub()
        self.registry: Dict[UUID, ApplicationObject] = registry or {}
        self.pubsub.subscribe(
            self.handle_event, TransportStopped, TransportTicked,
        )

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _handle_transport_stopped(self, event: TransportStopped):
        pass

    @handle_event.register
    def _handle_transport_ticked(self, event: TransportTicked):
        column = int(event.moment.measure_offset * 16)
        self.buffers["tick"].led_all(0)
        self.buffers["tick"].led_level_col(column, 0, [2] * 8)
        composite = self.buffers["grid"] | self.buffers["tick"]
        composite.render(self.grid)

    def on_grid_ready(self):
        self.grid.led_all(1)
        self.buffers = {
            "grid": GridBuffer(self.grid.width, self.grid.height),
            "notes": GridBuffer(self.grid.width, self.grid.height),
            "tick": GridBuffer(self.grid.width, self.grid.height),
        }
        for x in [0, 4, 8, 12]:
            self.buffers["grid"].led_level_col(x, 0, [1] * self.grid.height)

    def on_grid_disconnect(self):
        self.grid.led_all(0)
