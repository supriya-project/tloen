import pytest
from uqbar.strings import normalize


def test_dc_index_synthdef_factory(dc_index_synthdef_factory):
    synthdef = dc_index_synthdef_factory.build(name="test")
    assert normalize(str(synthdef)) == normalize(
        """
        synthdef:
            name: test
            ugens:
            -   Control.ir: null
            -   Control.kr: null
            -   BinaryOpUGen(EQUAL).kr/0:
                    left: Control.kr[0:index]
                    right: 0.0
            -   BinaryOpUGen(EQUAL).kr/1:
                    left: Control.kr[0:index]
                    right: 1.0
            -   DC.ar:
                    source: 1.0
            -   BinaryOpUGen(MULTIPLICATION).ar/0:
                    left: DC.ar[0]
                    right: BinaryOpUGen(EQUAL).kr/0[0]
            -   BinaryOpUGen(MULTIPLICATION).ar/1:
                    left: DC.ar[0]
                    right: BinaryOpUGen(EQUAL).kr/1[0]
            -   Out.ar:
                    bus: Control.ir[0:out]
                    source[0]: BinaryOpUGen(MULTIPLICATION).ar/0[0]
                    source[1]: BinaryOpUGen(MULTIPLICATION).ar/1[0]
        """
    )


@pytest.mark.asyncio
async def test_track_mute_solo_application(track_mute_solo_application):
    await track_mute_solo_application.boot()
    assert format(
        await track_mute_solo_application.primary_context.query(), "unindexed"
    ) == normalize(
        """
        NODE TREE ... group (Context)
            ... group (Tracks)
                ... group (a)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/8x8 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 16.0, lag: 0.01, out: 24.0
                    ... group (SubTracks)
                    ... mixer/levels/8 (InputLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                        ... group (AudioEffect)
                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                active: 1.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 32.0
                            ... group (Body)
                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                    out: 32.0, index: 0.0
                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 32.0, lag: 0.01, mix: 1.0, out: 24.0
                    ... mixer/levels/8 (PrefaderLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                        active: 1.0, gain: c0, gate: 1.0, hard_gate: 1.0, in_: 24.0, lag: 0.01, out: 24.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/8x8 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 216.0
                    ... mixer/levels/8 (PostfaderLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
                ... group (b)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/8x8 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 40.0, lag: 0.01, out: 48.0
                    ... group (SubTracks)
                        ... group (ba)
                            ... group (Parameters)
                                ... group (gain)
                                ... group (panning)
                            ... group (Receives)
                            ... mixer/patch[fb,gain]/8x8 (Input)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 56.0, lag: 0.01, out: 64.0
                            ... group (SubTracks)
                            ... mixer/levels/8 (InputLevels)
                                out: 64.0, gate: 1.0, lag: 0.01
                            ... group (Devices)
                                ... group (AudioEffect)
                                    ... mixer/patch[replace]/8x8 (DeviceIn)
                                        active: 1.0, gate: 1.0, in_: 64.0, lag: 0.01, out: 72.0
                                    ... group (Body)
                                        ... 7e3d216f841357d2a2e2ab2c3415df6f
                                            out: 72.0, index: 2.0
                                    ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                        active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 72.0, lag: 0.01, mix: 1.0, out: 64.0
                            ... mixer/levels/8 (PrefaderLevels)
                                out: 64.0, gate: 1.0, lag: 0.01
                            ... group (PreFaderSends)
                            ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                active: 1.0, gain: c4, gate: 1.0, hard_gate: 1.0, in_: 64.0, lag: 0.01, out: 64.0
                            ... group (PostFaderSends)
                                ... mixer/patch[gain]/8x8 (Send)
                                    active: 1.0, gain: 0.0, gate: 1.0, in_: 64.0, lag: 0.01, out: 48.0
                            ... mixer/levels/8 (PostfaderLevels)
                                out: 64.0, gate: 1.0, lag: 0.01
                        ... group (bb)
                            ... group (Parameters)
                                ... group (gain)
                                ... group (panning)
                            ... group (Receives)
                            ... mixer/patch[fb,gain]/8x8 (Input)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 80.0, lag: 0.01, out: 88.0
                            ... group (SubTracks)
                            ... mixer/levels/8 (InputLevels)
                                out: 88.0, gate: 1.0, lag: 0.01
                            ... group (Devices)
                                ... group (AudioEffect)
                                    ... mixer/patch[replace]/8x8 (DeviceIn)
                                        active: 1.0, gate: 1.0, in_: 88.0, lag: 0.01, out: 96.0
                                    ... group (Body)
                                        ... 7e3d216f841357d2a2e2ab2c3415df6f
                                            out: 96.0, index: 3.0
                                    ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                        active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 96.0, lag: 0.01, mix: 1.0, out: 88.0
                            ... mixer/levels/8 (PrefaderLevels)
                                out: 88.0, gate: 1.0, lag: 0.01
                            ... group (PreFaderSends)
                            ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                active: 1.0, gain: c6, gate: 1.0, hard_gate: 1.0, in_: 88.0, lag: 0.01, out: 88.0
                            ... group (PostFaderSends)
                                ... mixer/patch[gain]/8x8 (Send)
                                    active: 1.0, gain: 0.0, gate: 1.0, in_: 88.0, lag: 0.01, out: 48.0
                            ... mixer/levels/8 (PostfaderLevels)
                                out: 88.0, gate: 1.0, lag: 0.01
                    ... mixer/levels/8 (InputLevels)
                        out: 48.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                        ... group (AudioEffect)
                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                active: 1.0, gate: 1.0, in_: 48.0, lag: 0.01, out: 104.0
                            ... group (Body)
                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                    out: 104.0, index: 1.0
                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 104.0, lag: 0.01, mix: 1.0, out: 48.0
                    ... mixer/levels/8 (PrefaderLevels)
                        out: 48.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                        active: 1.0, gain: c2, gate: 1.0, hard_gate: 1.0, in_: 48.0, lag: 0.01, out: 48.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/8x8 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 48.0, lag: 0.01, out: 216.0
                    ... mixer/levels/8 (PostfaderLevels)
                        out: 48.0, gate: 1.0, lag: 0.01
                ... group (c)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/8x8 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 112.0, lag: 0.01, out: 120.0
                    ... group (SubTracks)
                        ... group (ca)
                            ... group (Parameters)
                                ... group (gain)
                                ... group (panning)
                            ... group (Receives)
                            ... mixer/patch[fb,gain]/8x8 (Input)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 128.0, lag: 0.01, out: 136.0
                            ... group (SubTracks)
                            ... mixer/levels/8 (InputLevels)
                                out: 136.0, gate: 1.0, lag: 0.01
                            ... group (Devices)
                                ... group (AudioEffect)
                                    ... mixer/patch[replace]/8x8 (DeviceIn)
                                        active: 1.0, gate: 1.0, in_: 136.0, lag: 0.01, out: 144.0
                                    ... group (Body)
                                        ... 7e3d216f841357d2a2e2ab2c3415df6f
                                            out: 144.0, index: 5.0
                                    ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                        active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 144.0, lag: 0.01, mix: 1.0, out: 136.0
                            ... mixer/levels/8 (PrefaderLevels)
                                out: 136.0, gate: 1.0, lag: 0.01
                            ... group (PreFaderSends)
                            ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                active: 1.0, gain: c10, gate: 1.0, hard_gate: 1.0, in_: 136.0, lag: 0.01, out: 136.0
                            ... group (PostFaderSends)
                                ... mixer/patch[gain]/8x8 (Send)
                                    active: 1.0, gain: 0.0, gate: 1.0, in_: 136.0, lag: 0.01, out: 120.0
                            ... mixer/levels/8 (PostfaderLevels)
                                out: 136.0, gate: 1.0, lag: 0.01
                        ... group (cb)
                            ... group (Parameters)
                                ... group (gain)
                                ... group (panning)
                            ... group (Receives)
                            ... mixer/patch[fb,gain]/8x8 (Input)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 152.0, lag: 0.01, out: 160.0
                            ... group (SubTracks)
                                ... group (cba)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 168.0, lag: 0.01, out: 176.0
                                    ... group (SubTracks)
                                    ... mixer/levels/8 (InputLevels)
                                        out: 176.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (AudioEffect)
                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 176.0, lag: 0.01, out: 184.0
                                            ... group (Body)
                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                    out: 184.0, index: 7.0
                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 184.0, lag: 0.01, mix: 1.0, out: 176.0
                                    ... mixer/levels/8 (PrefaderLevels)
                                        out: 176.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                        active: 1.0, gain: c14, gate: 1.0, hard_gate: 1.0, in_: 176.0, lag: 0.01, out: 176.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/8x8 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 176.0, lag: 0.01, out: 160.0
                                    ... mixer/levels/8 (PostfaderLevels)
                                        out: 176.0, gate: 1.0, lag: 0.01
                            ... mixer/levels/8 (InputLevels)
                                out: 160.0, gate: 1.0, lag: 0.01
                            ... group (Devices)
                                ... group (AudioEffect)
                                    ... mixer/patch[replace]/8x8 (DeviceIn)
                                        active: 1.0, gate: 1.0, in_: 160.0, lag: 0.01, out: 192.0
                                    ... group (Body)
                                        ... 7e3d216f841357d2a2e2ab2c3415df6f
                                            out: 192.0, index: 6.0
                                    ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                        active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 192.0, lag: 0.01, mix: 1.0, out: 160.0
                            ... mixer/levels/8 (PrefaderLevels)
                                out: 160.0, gate: 1.0, lag: 0.01
                            ... group (PreFaderSends)
                            ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                active: 1.0, gain: c12, gate: 1.0, hard_gate: 1.0, in_: 160.0, lag: 0.01, out: 160.0
                            ... group (PostFaderSends)
                                ... mixer/patch[gain]/8x8 (Send)
                                    active: 1.0, gain: 0.0, gate: 1.0, in_: 160.0, lag: 0.01, out: 120.0
                            ... mixer/levels/8 (PostfaderLevels)
                                out: 160.0, gate: 1.0, lag: 0.01
                    ... mixer/levels/8 (InputLevels)
                        out: 120.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                        ... group (AudioEffect)
                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                active: 1.0, gate: 1.0, in_: 120.0, lag: 0.01, out: 200.0
                            ... group (Body)
                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                    out: 200.0, index: 4.0
                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 200.0, lag: 0.01, mix: 1.0, out: 120.0
                    ... mixer/levels/8 (PrefaderLevels)
                        out: 120.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                        active: 1.0, gain: c8, gate: 1.0, hard_gate: 1.0, in_: 120.0, lag: 0.01, out: 120.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/8x8 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 120.0, lag: 0.01, out: 216.0
                    ... mixer/levels/8 (PostfaderLevels)
                        out: 120.0, gate: 1.0, lag: 0.01
            ... group (MasterTrack)
                ... group (Parameters)
                    ... group (gain)
                ... group (Receives)
                ... mixer/patch[fb,gain]/8x8 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 208.0, lag: 0.01, out: 216.0
                ... mixer/levels/8 (InputLevels)
                    out: 216.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/8 (PrefaderLevels)
                    out: 216.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/8x8 (Output)
                    active: 1.0, gain: c16, gate: 1.0, hard_gate: 1.0, in_: 216.0, lag: 0.01, out: 216.0
                ... group (PostFaderSends)
                    ... mixer/patch/8x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 216.0, lag: 0.01, out: 0.0
                ... mixer/levels/8 (PostfaderLevels)
                    out: 216.0, gate: 1.0, lag: 0.01
            ... group (CueTrack)
                ... group (Parameters)
                    ... group (gain)
                    ... group (mix)
                ... group (Receives)
                ... mixer/patch[fb,gain]/2x2 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 224.0, lag: 0.01, out: 226.0
                ... mixer/levels/2 (InputLevels)
                    out: 226.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/2 (PrefaderLevels)
                    out: 226.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/2x2 (Output)
                    active: 1.0, gain: c17, gate: 1.0, hard_gate: 1.0, in_: 226.0, lag: 0.01, out: 226.0
                ... group (PostFaderSends)
                    ... mixer/patch/2x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 226.0, lag: 0.01, out: 2.0
                ... mixer/levels/2 (PostfaderLevels)
                    out: 226.0, gate: 1.0, lag: 0.01
        """
    )


@pytest.mark.asyncio
async def test_channel_count_application(channel_count_application):
    await channel_count_application.boot()
    assert format(
        await channel_count_application.primary_context.query(), "unindexed"
    ) == normalize(
        """
        NODE TREE ... group (Context)
            ... group (Tracks)
                ... group (One)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/2x2 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 16.0, lag: 0.01, out: 18.0
                    ... group (SubTracks)
                    ... mixer/levels/2 (InputLevels)
                        out: 18.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                        ... group (Rack)
                            ... mixer/patch[gain]/2x2 (RackIn)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 18.0, lag: 0.01, out: 20.0
                            ... group (ChainContainer)
                                ... group (Chain)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/2x2 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 22.0, lag: 0.01, out: 24.0
                                    ... mixer/levels/2 (InputLevels)
                                        out: 24.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (Device)
                                            ... mixer/patch[replace]/2x2 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 26.0
                                            ... group (Body)
                                                ... ab5b942cf898e9d22891fff080fee99e
                                                    out: 26.0, index: 0.0
                                            ... mixer/patch[hard,mix]/2x2 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 26.0, lag: 0.01, mix: 1.0, out: 24.0
                                    ... mixer/levels/2 (PrefaderLevels)
                                        out: 24.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/2x2 (Output)
                                        active: 1.0, gain: c2, gate: 1.0, hard_gate: 1.0, in_: 24.0, lag: 0.01, out: 24.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/2x2 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 20.0
                                    ... mixer/levels/2 (PostfaderLevels)
                                        out: 24.0, gate: 1.0, lag: 0.01
                            ... mixer/patch[hard,mix]/2x2 (RackOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 20.0, lag: 0.01, mix: 1.0, out: 18.0
                    ... mixer/levels/2 (PrefaderLevels)
                        out: 18.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/2x2 (Output)
                        active: 1.0, gain: c0, gate: 1.0, hard_gate: 1.0, in_: 18.0, lag: 0.01, out: 18.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/2x2 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 18.0, lag: 0.01, out: 38.0
                    ... mixer/levels/2 (PostfaderLevels)
                        out: 18.0, gate: 1.0, lag: 0.01
                ... group (Two)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/2x2 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 28.0, lag: 0.01, out: 30.0
                    ... group (SubTracks)
                        ... group (Three)
                            ... group (Parameters)
                                ... group (gain)
                                ... group (panning)
                            ... group (Receives)
                            ... mixer/patch[fb,gain]/2x2 (Input)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 32.0, lag: 0.01, out: 34.0
                            ... group (SubTracks)
                            ... mixer/levels/2 (InputLevels)
                                out: 34.0, gate: 1.0, lag: 0.01
                            ... group (Devices)
                            ... mixer/levels/2 (PrefaderLevels)
                                out: 34.0, gate: 1.0, lag: 0.01
                            ... group (PreFaderSends)
                            ... mixer/patch[gain,hard,replace]/2x2 (Output)
                                active: 1.0, gain: c6, gate: 1.0, hard_gate: 1.0, in_: 34.0, lag: 0.01, out: 34.0
                            ... group (PostFaderSends)
                                ... mixer/patch[gain]/2x2 (Send)
                                    active: 1.0, gain: 0.0, gate: 1.0, in_: 34.0, lag: 0.01, out: 30.0
                            ... mixer/levels/2 (PostfaderLevels)
                                out: 34.0, gate: 1.0, lag: 0.01
                    ... mixer/levels/2 (InputLevels)
                        out: 30.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                    ... mixer/levels/2 (PrefaderLevels)
                        out: 30.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/2x2 (Output)
                        active: 1.0, gain: c4, gate: 1.0, hard_gate: 1.0, in_: 30.0, lag: 0.01, out: 30.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/2x2 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 30.0, lag: 0.01, out: 38.0
                    ... mixer/levels/2 (PostfaderLevels)
                        out: 30.0, gate: 1.0, lag: 0.01
            ... group (MasterTrack)
                ... group (Parameters)
                    ... group (gain)
                ... group (Receives)
                ... mixer/patch[fb,gain]/2x2 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 36.0, lag: 0.01, out: 38.0
                ... mixer/levels/2 (InputLevels)
                    out: 38.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/2 (PrefaderLevels)
                    out: 38.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/2x2 (Output)
                    active: 1.0, gain: c8, gate: 1.0, hard_gate: 1.0, in_: 38.0, lag: 0.01, out: 38.0
                ... group (PostFaderSends)
                    ... mixer/patch/2x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 38.0, lag: 0.01, out: 0.0
                ... mixer/levels/2 (PostfaderLevels)
                    out: 38.0, gate: 1.0, lag: 0.01
            ... group (CueTrack)
                ... group (Parameters)
                    ... group (gain)
                    ... group (mix)
                ... group (Receives)
                ... mixer/patch[fb,gain]/2x2 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 40.0, lag: 0.01, out: 42.0
                ... mixer/levels/2 (InputLevels)
                    out: 42.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/2 (PrefaderLevels)
                    out: 42.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/2x2 (Output)
                    active: 1.0, gain: c9, gate: 1.0, hard_gate: 1.0, in_: 42.0, lag: 0.01, out: 42.0
                ... group (PostFaderSends)
                    ... mixer/patch/2x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 42.0, lag: 0.01, out: 2.0
                ... mixer/levels/2 (PostfaderLevels)
                    out: 42.0, gate: 1.0, lag: 0.01
        """
    )


@pytest.mark.asyncio
async def test_chain_mute_solo_application(chain_mute_solo_application):
    await chain_mute_solo_application.boot()
    assert format(
        await chain_mute_solo_application.primary_context.query(), "unindexed"
    ) == normalize(
        """
        NODE TREE ... group (Context)
            ... group (Tracks)
                ... group (Track)
                    ... group (Parameters)
                        ... group (gain)
                        ... group (panning)
                    ... group (Receives)
                    ... mixer/patch[fb,gain]/8x8 (Input)
                        active: 1.0, gain: 0.0, gate: 1.0, in_: 16.0, lag: 0.01, out: 24.0
                    ... group (SubTracks)
                    ... mixer/levels/8 (InputLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
                    ... group (Devices)
                        ... group (outer/a)
                            ... mixer/patch[gain]/8x8 (RackIn)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 32.0
                            ... group (ChainContainer)
                                ... group (outer/a/a)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 40.0, lag: 0.01, out: 48.0
                                    ... mixer/levels/8 (InputLevels)
                                        out: 48.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (AudioEffect)
                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 48.0, lag: 0.01, out: 56.0
                                            ... group (Body)
                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                    out: 56.0, index: 0.0
                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 56.0, lag: 0.01, mix: 1.0, out: 48.0
                                    ... mixer/levels/8 (PrefaderLevels)
                                        out: 48.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                        active: 1.0, gain: c2, gate: 1.0, hard_gate: 1.0, in_: 48.0, lag: 0.01, out: 48.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/8x8 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 48.0, lag: 0.01, out: 32.0
                                    ... mixer/levels/8 (PostfaderLevels)
                                        out: 48.0, gate: 1.0, lag: 0.01
                                ... group (outer/a/b)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 64.0, lag: 0.01, out: 72.0
                                    ... mixer/levels/8 (InputLevels)
                                        out: 72.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (inner/a)
                                            ... mixer/patch[gain]/8x8 (RackIn)
                                                active: 1.0, gain: 0.0, gate: 1.0, in_: 72.0, lag: 0.01, out: 80.0
                                            ... group (ChainContainer)
                                                ... group (inner/a/a)
                                                    ... group (Parameters)
                                                        ... group (gain)
                                                        ... group (panning)
                                                    ... group (Receives)
                                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 88.0, lag: 0.01, out: 96.0
                                                    ... mixer/levels/8 (InputLevels)
                                                        out: 96.0, gate: 1.0, lag: 0.01
                                                    ... group (Devices)
                                                        ... group (AudioEffect)
                                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                                active: 1.0, gate: 1.0, in_: 96.0, lag: 0.01, out: 104.0
                                                            ... group (Body)
                                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                                    out: 104.0, index: 2.0
                                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 104.0, lag: 0.01, mix: 1.0, out: 96.0
                                                    ... mixer/levels/8 (PrefaderLevels)
                                                        out: 96.0, gate: 1.0, lag: 0.01
                                                    ... group (PreFaderSends)
                                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                                        active: 1.0, gain: c6, gate: 1.0, hard_gate: 1.0, in_: 96.0, lag: 0.01, out: 96.0
                                                    ... group (PostFaderSends)
                                                        ... mixer/patch[gain]/8x8 (Send)
                                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 96.0, lag: 0.01, out: 80.0
                                                    ... mixer/levels/8 (PostfaderLevels)
                                                        out: 96.0, gate: 1.0, lag: 0.01
                                                ... group (inner/a/b)
                                                    ... group (Parameters)
                                                        ... group (gain)
                                                        ... group (panning)
                                                    ... group (Receives)
                                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 112.0, lag: 0.01, out: 120.0
                                                    ... mixer/levels/8 (InputLevels)
                                                        out: 120.0, gate: 1.0, lag: 0.01
                                                    ... group (Devices)
                                                        ... group (AudioEffect)
                                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                                active: 1.0, gate: 1.0, in_: 120.0, lag: 0.01, out: 128.0
                                                            ... group (Body)
                                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                                    out: 128.0, index: 3.0
                                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 128.0, lag: 0.01, mix: 1.0, out: 120.0
                                                    ... mixer/levels/8 (PrefaderLevels)
                                                        out: 120.0, gate: 1.0, lag: 0.01
                                                    ... group (PreFaderSends)
                                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                                        active: 1.0, gain: c8, gate: 1.0, hard_gate: 1.0, in_: 120.0, lag: 0.01, out: 120.0
                                                    ... group (PostFaderSends)
                                                        ... mixer/patch[gain]/8x8 (Send)
                                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 120.0, lag: 0.01, out: 80.0
                                                    ... mixer/levels/8 (PostfaderLevels)
                                                        out: 120.0, gate: 1.0, lag: 0.01
                                            ... mixer/patch[hard,mix]/8x8 (RackOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 80.0, lag: 0.01, mix: 1.0, out: 72.0
                                        ... group (AudioEffect)
                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 72.0, lag: 0.01, out: 136.0
                                            ... group (Body)
                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                    out: 136.0, index: 1.0
                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 136.0, lag: 0.01, mix: 1.0, out: 72.0
                                    ... mixer/levels/8 (PrefaderLevels)
                                        out: 72.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                        active: 1.0, gain: c4, gate: 1.0, hard_gate: 1.0, in_: 72.0, lag: 0.01, out: 72.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/8x8 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 72.0, lag: 0.01, out: 32.0
                                    ... mixer/levels/8 (PostfaderLevels)
                                        out: 72.0, gate: 1.0, lag: 0.01
                            ... mixer/patch[hard,mix]/8x8 (RackOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 32.0, lag: 0.01, mix: 1.0, out: 24.0
                        ... group (outer/b)
                            ... mixer/patch[gain]/8x8 (RackIn)
                                active: 1.0, gain: 0.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 144.0
                            ... group (ChainContainer)
                                ... group (outer/b/a)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 152.0, lag: 0.01, out: 160.0
                                    ... mixer/levels/8 (InputLevels)
                                        out: 160.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (AudioEffect)
                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 160.0, lag: 0.01, out: 168.0
                                            ... group (Body)
                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                    out: 168.0, index: 4.0
                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 168.0, lag: 0.01, mix: 1.0, out: 160.0
                                    ... mixer/levels/8 (PrefaderLevels)
                                        out: 160.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                        active: 1.0, gain: c10, gate: 1.0, hard_gate: 1.0, in_: 160.0, lag: 0.01, out: 160.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/8x8 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 160.0, lag: 0.01, out: 144.0
                                    ... mixer/levels/8 (PostfaderLevels)
                                        out: 160.0, gate: 1.0, lag: 0.01
                                ... group (outer/b/b)
                                    ... group (Parameters)
                                        ... group (gain)
                                        ... group (panning)
                                    ... group (Receives)
                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 176.0, lag: 0.01, out: 184.0
                                    ... mixer/levels/8 (InputLevels)
                                        out: 184.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (inner/b)
                                            ... mixer/patch[gain]/8x8 (RackIn)
                                                active: 1.0, gain: 0.0, gate: 1.0, in_: 184.0, lag: 0.01, out: 192.0
                                            ... group (ChainContainer)
                                                ... group (inner/b/a)
                                                    ... group (Parameters)
                                                        ... group (gain)
                                                        ... group (panning)
                                                    ... group (Receives)
                                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 200.0, lag: 0.01, out: 208.0
                                                    ... mixer/levels/8 (InputLevels)
                                                        out: 208.0, gate: 1.0, lag: 0.01
                                                    ... group (Devices)
                                                        ... group (AudioEffect)
                                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                                active: 1.0, gate: 1.0, in_: 208.0, lag: 0.01, out: 216.0
                                                            ... group (Body)
                                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                                    out: 216.0, index: 6.0
                                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 216.0, lag: 0.01, mix: 1.0, out: 208.0
                                                    ... mixer/levels/8 (PrefaderLevels)
                                                        out: 208.0, gate: 1.0, lag: 0.01
                                                    ... group (PreFaderSends)
                                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                                        active: 1.0, gain: c14, gate: 1.0, hard_gate: 1.0, in_: 208.0, lag: 0.01, out: 208.0
                                                    ... group (PostFaderSends)
                                                        ... mixer/patch[gain]/8x8 (Send)
                                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 208.0, lag: 0.01, out: 192.0
                                                    ... mixer/levels/8 (PostfaderLevels)
                                                        out: 208.0, gate: 1.0, lag: 0.01
                                                ... group (inner/b/b)
                                                    ... group (Parameters)
                                                        ... group (gain)
                                                        ... group (panning)
                                                    ... group (Receives)
                                                    ... mixer/patch[fb,gain]/8x8 (Input)
                                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 224.0, lag: 0.01, out: 232.0
                                                    ... mixer/levels/8 (InputLevels)
                                                        out: 232.0, gate: 1.0, lag: 0.01
                                                    ... group (Devices)
                                                        ... group (AudioEffect)
                                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                                active: 1.0, gate: 1.0, in_: 232.0, lag: 0.01, out: 240.0
                                                            ... group (Body)
                                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                                    out: 240.0, index: 7.0
                                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 240.0, lag: 0.01, mix: 1.0, out: 232.0
                                                    ... mixer/levels/8 (PrefaderLevels)
                                                        out: 232.0, gate: 1.0, lag: 0.01
                                                    ... group (PreFaderSends)
                                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                                        active: 1.0, gain: c16, gate: 1.0, hard_gate: 1.0, in_: 232.0, lag: 0.01, out: 232.0
                                                    ... group (PostFaderSends)
                                                        ... mixer/patch[gain]/8x8 (Send)
                                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 232.0, lag: 0.01, out: 192.0
                                                    ... mixer/levels/8 (PostfaderLevels)
                                                        out: 232.0, gate: 1.0, lag: 0.01
                                            ... mixer/patch[hard,mix]/8x8 (RackOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 192.0, lag: 0.01, mix: 1.0, out: 184.0
                                        ... group (AudioEffect)
                                            ... mixer/patch[replace]/8x8 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 184.0, lag: 0.01, out: 248.0
                                            ... group (Body)
                                                ... 7e3d216f841357d2a2e2ab2c3415df6f
                                                    out: 248.0, index: 5.0
                                            ... mixer/patch[hard,mix]/8x8 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 248.0, lag: 0.01, mix: 1.0, out: 184.0
                                    ... mixer/levels/8 (PrefaderLevels)
                                        out: 184.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                                        active: 1.0, gain: c12, gate: 1.0, hard_gate: 1.0, in_: 184.0, lag: 0.01, out: 184.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/8x8 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 184.0, lag: 0.01, out: 144.0
                                    ... mixer/levels/8 (PostfaderLevels)
                                        out: 184.0, gate: 1.0, lag: 0.01
                            ... mixer/patch[hard,mix]/8x8 (RackOut)
                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 144.0, lag: 0.01, mix: 1.0, out: 24.0
                    ... mixer/levels/8 (PrefaderLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
                    ... group (PreFaderSends)
                    ... mixer/patch[gain,hard,replace]/8x8 (Output)
                        active: 1.0, gain: c0, gate: 1.0, hard_gate: 1.0, in_: 24.0, lag: 0.01, out: 24.0
                    ... group (PostFaderSends)
                        ... mixer/patch[gain]/8x8 (Send)
                            active: 1.0, gain: 0.0, gate: 1.0, in_: 24.0, lag: 0.01, out: 264.0
                    ... mixer/levels/8 (PostfaderLevels)
                        out: 24.0, gate: 1.0, lag: 0.01
            ... group (MasterTrack)
                ... group (Parameters)
                    ... group (gain)
                ... group (Receives)
                ... mixer/patch[fb,gain]/8x8 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 256.0, lag: 0.01, out: 264.0
                ... mixer/levels/8 (InputLevels)
                    out: 264.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/8 (PrefaderLevels)
                    out: 264.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/8x8 (Output)
                    active: 1.0, gain: c18, gate: 1.0, hard_gate: 1.0, in_: 264.0, lag: 0.01, out: 264.0
                ... group (PostFaderSends)
                    ... mixer/patch/8x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 264.0, lag: 0.01, out: 0.0
                ... mixer/levels/8 (PostfaderLevels)
                    out: 264.0, gate: 1.0, lag: 0.01
            ... group (CueTrack)
                ... group (Parameters)
                    ... group (gain)
                    ... group (mix)
                ... group (Receives)
                ... mixer/patch[fb,gain]/2x2 (Input)
                    active: 1.0, gain: 0.0, gate: 1.0, in_: 272.0, lag: 0.01, out: 274.0
                ... mixer/levels/2 (InputLevels)
                    out: 274.0, gate: 1.0, lag: 0.01
                ... group (Devices)
                ... mixer/levels/2 (PrefaderLevels)
                    out: 274.0, gate: 1.0, lag: 0.01
                ... group (PreFaderSends)
                ... mixer/patch[gain,hard,replace]/2x2 (Output)
                    active: 1.0, gain: c19, gate: 1.0, hard_gate: 1.0, in_: 274.0, lag: 0.01, out: 274.0
                ... group (PostFaderSends)
                    ... mixer/patch/2x2 (DirectOut)
                        active: 1.0, gate: 1.0, in_: 274.0, lag: 0.01, out: 2.0
                ... mixer/levels/2 (PostfaderLevels)
                    out: 274.0, gate: 1.0, lag: 0.01
        """
    )
