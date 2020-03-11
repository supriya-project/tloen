from typing import Union

from supriya.enums import AddAction
from supriya.synthdefs import SynthDef, SynthDefFactory
from supriya.ugens import LPF, Limiter, Mix

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
            out=self.audio_bus_proxies["output"],
            **self.synthdef_kwargs,
            **{
                source: self.parameters[target]
                for source, target in self.parameter_map.items()
            },
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


class LimiterDevice(AudioEffect):
    def __init__(self, *, name=None, uuid=None):
        AudioEffect.__init__(
            self,
            name=name,
            parameters={
                parameter.name: parameter
                for parameter in [
                    BusParameter("frequency_1", Float(default=0.025)),
                    BusParameter("frequency_2", Float(default=0.1)),
                ]
            },
            synthdef=self.build_synthdef(),
            uuid=uuid,
        )

    def build_synthdef(self):
        def signal_block(builder, source, state):
            frequency_1 = builder["frequency_1"].minimum(builder["frequency_2"])
            frequency_2 = builder["frequency_1"].maximum(builder["frequency_2"])
            band_1 = LPF.ar(frequency=frequency_1, source=source)
            band_2 = LPF.ar(frequency=frequency_2, source=source - band_1)
            band_3 = source - band_2 - band_1  # TODO: optimize this
            return Mix.multichannel(
                sources=[Limiter.ar(source=band) for band in [band_1, band_2, band_3]],
                channel_count=state["channel_count"],
            )

        factory = (
            SynthDefFactory(frequency_1=200, frequency_2=2000)
            .with_channel_count(2)
            .with_gate()
            .with_input()
            .with_output(replacing=True)
            .with_signal_block(signal_block)
        )
        return factory
