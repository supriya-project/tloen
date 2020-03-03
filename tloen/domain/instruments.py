from typing import Dict, Union

from supriya import conversions
from supriya.assets.synthdefs import default
from supriya.provider import SynthProxy
from supriya.synthdefs import SynthDef, SynthDefFactory
from supriya.ugens import PlayBuf

from .devices import AllocatableDevice
from .parameters import BufferParameter


class Instrument(AllocatableDevice):

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        name=None,
        parameter_map=None,
        parameters=None,
        synthdef: Union[SynthDef, SynthDefFactory] = None,
        synthdef_kwargs=None,
        uuid=None,
    ):
        # TODO: Polyphony Limit
        # TODO: Polyphony Mode
        AllocatableDevice.__init__(
            self,
            name=name,
            parameters=parameters,
            parameter_map=parameter_map,
            synthdef=synthdef,
            synthdef_kwargs=synthdef_kwargs,
            uuid=uuid,
        )
        self._notes_to_synths: Dict[float, SynthProxy] = {}

    ### PRIVATE METHODS ###

    def _deallocate(self, old_provider, *, dispose_only=False):
        AllocatableDevice._deallocate(self, old_provider, dispose_only=dispose_only)
        self._notes_to_synths.clear()

    def _handle_note_off(self, moment, midi_message):
        self._input_notes.remove(midi_message.pitch)
        synth = self._notes_to_synths.pop(midi_message.pitch, None)
        if synth is not None:
            synth.free()
        return []

    def _handle_note_on(self, moment, midi_message):
        pitch = midi_message.pitch
        if pitch in self._input_notes:
            self._handle_note_off(moment, midi_message)
        self._input_notes.add(midi_message.pitch)
        self._notes_to_synths[pitch] = self.node_proxies["body"].add_synth(
            synthdef=self.synthdef,
            out=self._audio_bus_proxies["output"],
            # TODO: Handle these via a note-to-args map
            frequency=conversions.midi_note_number_to_frequency(pitch),
            amplitude=conversions.midi_velocity_to_amplitude(midi_message.velocity),
            **self.synthdef_kwargs,
        )
        return []


class BasicSynth(Instrument):
    def __init__(self, *, name=None, uuid=None):
        Instrument.__init__(
            self, name=name, uuid=uuid, synthdef=self.build_synthdef(),
        )

    def build_synthdef(self):
        return default


class BasicSampler(Instrument):
    def __init__(self, *, name=None, uuid=None):
        Instrument.__init__(
            self,
            name=name,
            uuid=uuid,
            synthdef=self.build_synthdef(),
            parameters={"buffer_id": BufferParameter(name="buffer_id")},
            parameter_map={"buffer_id": "buffer_id"},
        )

    def _handle_note_on(self, moment, midi_message):
        if self.parameters["buffer_id"].buffer_proxy is None:
            return []
        pitch = midi_message.pitch
        if pitch in self._input_notes:
            self._handle_note_off(moment, midi_message)
        self._input_notes.add(midi_message.pitch)
        self._notes_to_synths[pitch] = self.node_proxies["body"].add_synth(
            synthdef=self.synthdef.build(channel_count=2),
            out=self._audio_bus_proxies["output"],
            amplitude=conversions.midi_velocity_to_amplitude(midi_message.velocity),
            buffer_id=self.parameters["buffer_id"].buffer_proxy,
            **self.synthdef_kwargs,
        )
        return []

    def _handle_note_off(self, moment, midi_message):
        return []

    def build_synthdef(self):
        def signal_block(builder, source, state):
            # TODO: Sampler should be aware of the shape of the sample
            #       In order to handle up- / down-mixing
            player = (
                PlayBuf.ar(
                    buffer_id=builder["buffer_id"], channel_count=1, done_action=2,
                )
                * builder["amplitude"]
            )
            return [player] * state["channel_count"]

        factory = (
            SynthDefFactory()
            .with_channel_count(2)
            .with_gate(attack_time=0, release_time=0.01)
            .with_output()
            .with_parameter("amplitude", 1, "control")
            .with_parameter("buffer_id", 0, "scalar")
            .with_signal_block(signal_block)
        )
        return factory
