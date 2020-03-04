import asyncio
from typing import Optional

import rtmidi

from .messages import (
    ControllerChangeMessage,
    MidiMessage,
    NoteOffMessage,
    NoteOnMessage,
)


class AsyncMidiProtocol:
    def __init__(self):
        self.is_running = False
        self.loop = None
        self.port = None

    def _rtmidi_callback(self, *args):
        midi_message = self._translate_message(*args)
        if midi_message is None:
            return
        self.loop.call_soon_threadsafe(self.message_received, midi_message)

    def _translate_message(self, *args) -> Optional[MidiMessage]:
        event, timestamp = args[0]
        status_byte, data = event[0], event[1:]
        message_type = status_byte >> 4
        channel_number = status_byte & 0x0F
        if message_type == 8:
            return NoteOffMessage(
                channel_number=channel_number,
                pitch=data[0],
                velocity=data[1],
                timestamp=timestamp,
            )
        elif message_type == 9:
            class_ = NoteOnMessage
            if data[1] == 0:
                class_ = NoteOffMessage
            return class_(
                channel_number=channel_number,
                pitch=data[0],
                velocity=data[1],
                timestamp=timestamp,
            )
        elif message_type == 11:
            return ControllerChangeMessage(
                channel_number=channel_number,
                controller_number=data[0],
                controller_value=data[1],
                timestamp=timestamp,
            )
        return

    async def connect(self, port):
        if self.is_running:
            raise RuntimeError
        self.loop = asyncio.get_running_loop()
        self.port = port
        self.midi_in = rtmidi.MidiIn()
        self.midi_in.open_port(port)
        self.midi_in.ignore_types(active_sense=True, sysex=True, timing=True)
        self.midi_in.set_callback(self.rtmidi_callback)

    async def disconnect(self):
        if not self.is_running:
            return
        self.midi_in.close_port()
        self.is_running = False
        self.loop = None
        self.port = None

    async def message_received(self, message):
        pass

    def register(self, procedure, *, message_class=None, channel=None):
        pass

    def unregister(self, callback):
        pass
