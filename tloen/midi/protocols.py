import asyncio
import dataclasses
from typing import Callable, Dict, List, Optional, Type

import rtmidi

from .messages import (
    ControllerChangeMessage,
    MidiMessage,
    NoteOffMessage,
    NoteOnMessage,
)


@dataclasses.dataclass
class MidiCallback:
    procedure: Callable
    message_class: Optional[Type[MidiMessage]]
    channel: Optional[int]
    once: bool = False


class AsyncMidiProtocol:

    ### INITIALIZER ###

    def __init__(self):
        self.callbacks: Dict[
            Optional[Type[MidiMessage]], Dict[Optional[int], List[MidiCallback]]
        ] = {}
        self.is_running = False
        self.loop = None
        self.port = None

    ### PRIVATE METHODS ###

    def _match_callbacks(self, message: MidiMessage):
        callbacks: List[MidiCallback] = []
        for by_message_class in [
            self.callbacks.get(None, {}),
            self.callbacks.get(type(message), {}),
        ]:
            callbacks.extend(by_message_class.get(None, []))
            if message.channel_number is not None:
                callbacks.extend(by_message_class.get(message.channel_number, []))
        return callbacks

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
            kwargs = dict(
                channel_number=channel_number,
                pitch=data[0],
                velocity=data[1],
                timestamp=timestamp,
            )
            if data[1] == 0:
                return NoteOffMessage(**kwargs)
            else:
                return NoteOnMessage(**kwargs)
        elif message_type == 11:
            return ControllerChangeMessage(
                channel_number=channel_number,
                controller_number=data[0],
                controller_value=data[1],
                timestamp=timestamp,
            )
        return None

    ### PUBLIC METHODS ###

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
        for callback in self._match_callbacks(message):
            result = callback(message)
            if asyncio.iscoroutine(result):
                await result

    def register(
        self,
        procedure,
        *,
        message_class: Optional[Type[MidiMessage]] = None,
        channel: Optional[int] = None,
        once: bool = False,
    ):
        callback = MidiCallback(
            procedure=procedure,
            message_class=message_class,
            channel=channel,
            once=bool(once),
        )
        by_message_class = self.callbacks.setdefault(message_class, {})
        by_channel = by_message_class.setdefault(channel, [])
        by_channel.append(callback)
        return callback

    def unregister(self, callback: MidiCallback):
        by_message_class = self.callbacks.get(callback.message_class, {})
        by_channel = by_message_class.get(callback.channel, [])
        if callback in by_channel:
            by_channel.remove(callback)
        if not by_channel:
            by_message_class.pop(callback.channel, None)
        if not by_message_class:
            self.callbacks.pop(callback.message_class, None)
