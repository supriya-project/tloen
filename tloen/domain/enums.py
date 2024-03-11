import enum


class ApplicationStatus(enum.IntEnum):
    OFFLINE = 0
    REALTIME = 1
    NONREALTIME = 2


class EventType(enum.IntEnum):
    CHANGE = 0
    SCHEDULE = 1
    MIDI_PERFORM = 2
    DEVICE_NOTE_OFF = 3
    DEVICE_NOTE_ON = 4
    CLIP_LAUNCH = 5
    CLIP_EDIT = 6
    CLIP_PERFORM = 7
