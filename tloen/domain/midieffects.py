import enum
from typing import Dict, List, Tuple

from supriya.clocks import TempoClock, TimeUnit

from tloen.midi import NoteOffMessage, NoteOnMessage

from .devices import DeviceObject
from .enums import EventType


class Chord(DeviceObject):
    def __init__(self, name=None, uuid=None):
        DeviceObject.__init__(self, name=name, uuid=uuid)
        self._transpositions = []

    def _handle_note_off(self, moment, midi_message):
        result = []
        pitch = midi_message.pitch
        for pitch in sorted(self._input_pitches.pop(pitch, [])):
            if pitch in self._output_pitches:
                self._output_pitches.remove(pitch)
                result.append(NoteOffMessage(pitch=pitch))
        return result

    def _handle_note_on(self, moment, midi_message):
        result = []
        pitch = midi_message.pitch
        if pitch in self._input_pitches:
            result.extend(self._handle_note_off(moment, midi_message))
        transpositions = sorted(set(pitch + _ for _ in self._transpositions or [0]))
        self._input_pitches[pitch] = transpositions
        for transposition in transpositions:
            if transposition in self._output_pitches:
                result.append(NoteOffMessage(pitch=transposition))
            result.append(
                NoteOnMessage(pitch=transposition, velocity=midi_message.velocity)
            )
            self._output_pitches.add(transposition)
        return result


class Arpeggiator(DeviceObject):

    ### CLASS VARIABLES ###

    class PatternStyle(enum.IntEnum):
        UP = 0
        DOWN = 1
        UP_DOWN = 2
        DOWN_UP = 3

    ### INITIALIZER ###

    def __init__(self, name=None, uuid=None):
        DeviceObject.__init__(self, name=name, uuid=uuid)
        self._input_pitches_to_velocities: Dict[float, float] = {}
        self._pattern: List[Tuple[float, float]] = ()
        self._pattern_style = self.PatternStyle.UP
        self._current_index = 0
        self._duration_scale = 1.0
        self._octaves = 0
        self._quantization = "1/16"
        self._callback_id = None
        self._previous_pitch = None

    ### PRIVATE METHODS ###

    def _applicate(self, new_application):
        DeviceObject._applicate(self, new_application)
        new_application.transport._dependencies.add(self)

    def _deapplicate(self, old_application):
        DeviceObject._applicate(self, old_application)
        old_application.transport._dependencies.remove(self)

    def _handle_note_off(self, moment, midi_message):
        self._input_pitches.pop(midi_message.pitch)
        self._input_pitches.pop(midi_message.pitch)
        self._pattern = self._rebuild_pattern()
        return []

    def _handle_note_on(self, moment, midi_message):
        self._input_pitches[midi_message.pitch] = [midi_message.pitch]
        self._input_pitches_to_velocities[midi_message.pitch] = midi_message.velocity
        self._pattern = self._rebuild_pattern()
        return []

    def _rebuild_pattern(self):
        if not self._input_pitches:
            return ()
        initial_pairs = sorted(self._input_pitches_to_velocities.items())
        octave_pairs = []
        pattern_pairs = []
        for octave in range(self._octaves + 1):
            for pitch, velocity in initial_pairs:
                octave_pairs.append((pitch + (12 * octave), velocity))
        if self._pattern_style == self.PatternStyle.UP:
            pattern_pairs.extend(octave_pairs)
        elif self._pattern_style == self.PatternStyle.DOWN:
            pattern_pairs.extend(reversed(octave_pairs))
        elif self._pattern_style == self.PatternStyle.UP_DOWN:
            pattern_pairs.extend(octave_pairs)
            pattern_pairs.extend(reversed(octave_pairs))
        elif self._pattern_style == self.PatternStyle.DOWN_UP:
            pattern_pairs.extend(reversed(octave_pairs))
            pattern_pairs.extend(octave_pairs)
        else:
            raise ValueError(self._pattern_style)
        return tuple(pattern_pairs)

    async def _start(self):
        self._debug_tree(self, "Starting")
        if self._callback_id is not None:
            return
        self._callback_id = self.application.clock.cue(
            self._transport_note_on_callback,
            event_type=EventType.MIDI_PERFORM,
            quantization=self._quantization,
        )

    async def _stop(self):
        self._debug_tree(self, "Stopping")
        if self._callback_id is not None:
            self.application.clock.cancel(self._callback_id)
        self._callback_id = None

    async def _transport_note_on_callback(self, clock_context, **kwargs):
        async with self.lock([self], seconds=clock_context.desired_moment.seconds):
            self._debug_tree(self, "Note On CB")
            delta = TempoClock.quantization_to_beats(self._quantization)
            if not len(self._pattern):
                return delta, TimeUnit.BEATS
            if self._current_index >= len(self._pattern):
                self._current_index = 0
            pitch, velocity = self._pattern[self._current_index]
            if len(self._pattern) > 1:
                while pitch == self._previous_pitch:
                    self._current_index += 1
                    if self._current_index >= len(self._pattern):
                        self._current_index = 0
                    pitch, velocity = self._pattern[self._current_index]
            self._previous_pitch = pitch
            self._current_index += 1
            midi_messages = []
            if pitch in self._output_pitches:
                midi_messages.append(NoteOffMessage(pitch=pitch))
            self._output_pitches.add(pitch)
            midi_messages.append(NoteOnMessage(pitch=pitch, velocity=velocity))
            for message in midi_messages:
                self._update_captures(
                    moment=clock_context.desired_moment, message=message, label="O"
                )
            self.application.clock.schedule(
                self._transport_note_off_callback,
                schedule_at=clock_context.desired_moment.offset
                + (delta * self._duration_scale),
                args=(pitch,),
            )
            performer = self._next_performer()
            if performer is not None:
                self._perform_loop(
                    clock_context.desired_moment, performer, midi_messages
                )
        return delta, TimeUnit.BEATS

    async def _transport_note_off_callback(self, clock_context, pitch, **kwargs):
        async with self.lock([self], seconds=clock_context.desired_moment.seconds):
            self._debug_tree(self, "Note Off CB")
            if pitch not in self._output_pitches:
                return
            midi_messages = [NoteOffMessage(pitch=pitch)]
            for message in midi_messages:
                self._update_captures(
                    moment=clock_context.desired_moment, message=message, label="O"
                )
            self._output_pitches.remove(pitch)
            performer = self._next_performer()
            if performer is None:
                return
            self._perform_loop(clock_context.desired_moment, performer, midi_messages)
