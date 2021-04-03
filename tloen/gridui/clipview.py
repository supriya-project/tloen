import asyncio
from functools import singledispatchmethod
from typing import Dict, Optional

from monome import GridApp, GridBuffer

from ..bases import Event
from ..commands.clips import ToggleClipNote
from ..domain.clips import Clip, ClipLaunched, ClipModified
from ..domain.transports import TransportStopped, TransportTicked
from ..pubsub import PubSub


class ClipView(GridApp):

    ### INITIALIZER ###

    def __init__(self, command_queue: asyncio.Queue, pubsub=None, registry=None):
        GridApp.__init__(self)
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry = registry if registry is not None else {}
        self.clip: Optional[Clip] = None
        self.buffers: Dict[str, GridBuffer] = {
            "grid": GridBuffer(self.grid.width or 16, self.grid.height or 8),
            "notes": GridBuffer(self.grid.width or 16, self.grid.height or 8),
            "press": GridBuffer(self.grid.width or 16, self.grid.height or 8),
            "tick": GridBuffer(self.grid.width or 16, self.grid.height or 8),
        }
        self.pubsub.subscribe(
            self.handle_event,
            TransportStopped,
            TransportTicked,
            ClipLaunched,
            ClipModified,
        )

    ### PRIVATE METHODS ###

    def _render(self):
        if self.grid.transport is None:
            return
        composite = (
            self.buffers["grid"]
            | self.buffers["tick"]
            | self.buffers["notes"]
            | self.buffers["press"]
        )
        composite.render(self.grid)

    def _update_notes(self):
        self.buffers["notes"].led_all(0)
        for note in self.clip.notes:
            y = 7 - (note.pitch - 60)
            x = int(note.start_offset * 16)
            if 0 <= x < 16 and 0 <= y < 8:
                self.buffers["notes"].led_set(x, y, 1)

    ### PUBLIC METHODS ###

    @singledispatchmethod
    def handle_event(self, event: Event):
        ...

    @handle_event.register
    def _handle_clip_launched(self, event: ClipLaunched):
        self.clip = self.registry[event.clip_uuid]
        self._update_notes()

    @handle_event.register
    def _handle_clip_modified(self, event: ClipModified):
        if self.clip is None or event.clip_uuid != self.clip.uuid:
            return
        self._update_notes()
        self._render()

    @handle_event.register
    def _handle_transport_stopped(self, event: TransportStopped):
        self.buffers["tick"].led_all(0)
        self._render()

    @handle_event.register
    def _handle_transport_ticked(self, event: TransportTicked):
        self.buffers["tick"].led_all(0)
        if self.clip is not None:
            pass
            # clip_offset = (
            #    event.moment.offset - self.clip._start_delta
            # ) % self.clip.duration
            # column = int(clip_offset * 16)
            # if column < 16:
            #    self.buffers["tick"].led_level_col(column, 0, [2] * 8)
        self._render()

    def on_grid_disconnect(self):
        if self.grid.transport is not None:
            self.grid.led_all(0)

    def on_grid_key(self, x, y, s):
        self.buffers["press"].led_set(x, y, s)
        if s and self.clip is not None:
            command = ToggleClipNote(
                clip_uuid=self.clip.uuid,
                pitch=(7 - y) + 60,
                offset=x / 16,
                duration=1 / 16,
            )
            self.command_queue.put_nowait(command)
        self._render()

    def on_grid_ready(self):
        self.grid.led_all(1)
        self.buffers = {
            "grid": GridBuffer(self.grid.width, self.grid.height),
            "notes": GridBuffer(self.grid.width, self.grid.height),
            "tick": GridBuffer(self.grid.width, self.grid.height),
            "press": GridBuffer(self.grid.width, self.grid.height),
        }
        for x in [0, 4, 8, 12]:
            self.buffers["grid"].led_level_col(x, 0, [1] * self.grid.height)
