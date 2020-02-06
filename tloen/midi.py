import dataclasses
from typing import Optional


@dataclasses.dataclass
class MidiMessage:
    pass


@dataclasses.dataclass
class ControllerChangeMessage(MidiMessage):
    controller_number: Optional[int]
    controller_value: Optional[int]
    channel_number: Optional[int] = None
    timestamp: Optional[float] = None


@dataclasses.dataclass
class NoteOffMessage(MidiMessage):
    pitch: Optional[int]
    velocity: Optional[int] = 100
    channel_number: Optional[int] = None
    timestamp: Optional[float] = None


@dataclasses.dataclass
class NoteOnMessage(MidiMessage):
    pitch: Optional[int]
    velocity: Optional[int] = 100
    channel_number: Optional[int] = None
    timestamp: Optional[float] = None
