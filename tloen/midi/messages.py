import dataclasses
from typing import Optional


@dataclasses.dataclass
class MidiMessage:
    channel_number: Optional[int] = None


@dataclasses.dataclass
class ControllerChangeMessage(MidiMessage):
    channel_number: Optional[int] = None
    controller_number: Optional[int] = None
    controller_value: Optional[int] = None
    timestamp: Optional[float] = None


@dataclasses.dataclass
class NoteOffMessage(MidiMessage):
    channel_number: Optional[int] = None
    pitch: Optional[int] = 60
    velocity: Optional[int] = 100
    timestamp: Optional[float] = None


@dataclasses.dataclass
class NoteOnMessage(MidiMessage):
    channel_number: Optional[int] = None
    pitch: Optional[int] = 60
    velocity: Optional[int] = 100
    timestamp: Optional[float] = None
