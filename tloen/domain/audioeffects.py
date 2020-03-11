from typing import Union

from supriya import ugens
from supriya.enums import AddAction
from supriya.synthdefs import SynthDef, SynthDefFactory

from .devices import AllocatableDevice
from .parameters import BusParameter, Float


class AudioEffect(AllocatableDevice):

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        synthdef: Union[SynthDef, SynthDefFactory],
        name=None,
        synthdef_kwargs=None,
        parameters=None,
        parameter_map=None,
        uuid=None,
    ):
        AllocatableDevice.__init__(
            self,
            name=name,
            parameters=parameters,
            parameter_map=parameter_map,
            synthdef=synthdef,
            synthdef_kwargs=synthdef_kwargs,
            uuid=uuid,
        )

    ### PRIVATE METHODS ###

    def _allocate_synths(self, provider, channel_count, *, synth_pair=None):
        synthdef = self.synthdef
        if isinstance(synthdef, SynthDefFactory):
            synthdef = synthdef.build(channel_count=self.effective_channel_count)
        synth_target, synth_action = synth_pair or (
            self.node_proxies["body"],
            AddAction.ADD_TO_HEAD,
        )
        self._node_proxies["synth"] = provider.add_synth(
            add_action=synth_action,
            synthdef=synthdef,
            target_node=synth_target,
            **self._build_kwargs(),
        )

    def _reallocate(self, difference):
        channel_count = self.effective_channel_count
        synth_synth = self._node_proxies.pop("synth")
        self._free_audio_buses()
        self._allocate_audio_buses(self.provider, channel_count)
        self._allocate_synths(
            self.provider,
            self.effective_channel_count,
            synth_pair=(synth_synth, AddAction.ADD_AFTER),
        )
        synth_synth.free()


class Limiter(AudioEffect):

    ### INITIALIZER ###

    # TODO: This should support a multiple-mono approach

    def __init__(self, *, name=None, uuid=None):
        AudioEffect.__init__(
            self,
            name=name,
            parameters={
                parameter.name: parameter
                for parameter in [
                    BusParameter("frequency_1", Float(default=0.025)),
                    BusParameter("frequency_2", Float(default=0.1)),
                    BusParameter(
                        "band_1_gain", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_2_gain", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_3_gain", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_1_limit", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_2_limit", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_3_limit", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_1_pregain", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_2_pregain", Float(default=0, minimum=-96, maximum=6)
                    ),
                    BusParameter(
                        "band_3_pregain", Float(default=0, minimum=-96, maximum=6)
                    ),
                ]
            },
            parameter_map={
                name: name
                for name in [
                    "frequency_1",
                    "frequency_2",
                    "band_1_gain",
                    "band_2_gain",
                    "band_3_gain",
                    "band_1_limit",
                    "band_2_limit",
                    "band_3_limit",
                    "band_1_pregain",
                    "band_2_pregain",
                    "band_3_pregain",
                ]
            },
            synthdef=self.build_synthdef(),
            uuid=uuid,
        )

    def build_synthdef(self):
        def signal_block(builder, source, state):
            frequency_1 = builder["frequency_1"].minimum(builder["frequency_2"])
            frequency_2 = builder["frequency_1"].maximum(builder["frequency_2"])
            band_1 = ugens.LPF.ar(frequency=frequency_1, source=source)
            band_2 = ugens.LPF.ar(frequency=frequency_2, source=source - band_1)
            band_3 = source - band_2 - band_1  # TODO: optimize this
            bands = [band_1, band_2, band_3]
            limiters = []
            for i, band in enumerate(bands, 1):
                limiter = ugens.Limiter.ar(
                    source=band * builder[f"band_{i}_pregain"].db_to_amplitude(),
                    level=builder[f"band_{i}_limit"].db_to_amplitude(),
                )
                limiters.append(limiter * builder[f"band_{i}_gain"].db_to_amplitude())
            return ugens.Mix.multichannel(
                sources=limiters, channel_count=state["channel_count"],
            )

        factory = (
            SynthDefFactory(
                frequency_1=200,
                frequency_2=2000,
                band_1_gain=0,
                band_1_limit=0,
                band_1_pregain=0,
                band_2_gain=0,
                band_2_limit=0,
                band_2_pregain=0,
                band_3_gain=0,
                band_3_limit=0,
                band_3_pregain=0,
            )
            .with_channel_count(2)
            .with_gate()
            .with_input()
            .with_output(replacing=True)
            .with_signal_block(signal_block)
        )
        return factory
