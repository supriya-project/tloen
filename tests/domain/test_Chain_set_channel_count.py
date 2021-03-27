import asyncio

import pytest
from uqbar.strings import normalize

from tloen.domain import Allocatable, ParameterObject


@pytest.mark.asyncio
async def test_channel_count(channel_count_application):
    items = [channel_count_application]
    items.extend(
        x
        for x in channel_count_application.depth_first()
        if not isinstance(x, ParameterObject) and x.name
    )
    assert {
        x.name: (x.channel_count, x.effective_channel_count) for x in items[1:]
    } == {
        "Chain": (None, 2),
        "Context": (None, 2),
        "Device": (None, 2),
        "One": (None, 2),
        "Rack": (None, 2),
        "Three": (None, 2),
        "Two": (None, 2),
    }
    await channel_count_application["Chain"].set_channel_count(4)
    assert {
        x.name: (x.channel_count, x.effective_channel_count) for x in items[1:]
    } == {
        "Chain": (4, 4),
        "Context": (None, 2),
        "Device": (None, 4),
        "One": (None, 2),
        "Rack": (None, 2),
        "Three": (None, 2),
        "Two": (None, 2),
    }


@pytest.mark.asyncio
async def test_audio_buses(channel_count_application):
    for node in channel_count_application.depth_first(prototype=Allocatable):
        for audio_bus_proxy in node.audio_bus_proxies.values():
            assert audio_bus_proxy.channel_count == node.effective_channel_count
    await channel_count_application["Chain"].set_channel_count(4)
    for node in channel_count_application.depth_first(prototype=Allocatable):
        for audio_bus_proxy in node.audio_bus_proxies.values():
            assert audio_bus_proxy.channel_count == node.effective_channel_count


@pytest.mark.asyncio
async def test_levels(channel_count_application):
    await channel_count_application.boot()
    master_levels = channel_count_application.primary_context.master_track.rms_levels
    track_levels = channel_count_application.primary_context["One"].rms_levels
    await asyncio.sleep(0.2)
    assert [round(x, 2) for x in track_levels["postfader"]] == [1.0, 0.0]
    assert [round(x, 2) for x in master_levels["input"]] == [1.0, 0.0]
    await channel_count_application["Chain"].set_channel_count(4)
    await asyncio.sleep(0.2)
    assert [round(x, 2) for x in track_levels["postfader"]] == [0.41, 0.0]
    assert [round(x, 2) for x in master_levels["input"]] == [0.41, 0.0]


@pytest.mark.asyncio
async def test_query(channel_count_application):
    # TODO: Chain input isn't quite correct.
    #       They need a dedicated receive in their receives group
    #       to patch the rack's parent bus group to their bus group.
    #       Then the rack doesn't need an input - it delegates to the chain receives.
    context = channel_count_application["Context"]
    await channel_count_application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["Chain"].set_channel_count(4)
    await asyncio.sleep(0.1)
    assert len(transcript.sent_messages) == 1
    after = format(await context.query(), "unindexed")
    assert after == normalize(
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
                                    ... mixer/patch[fb,gain]/4x4 (Input)
                                        active: 1.0, gain: 0.0, gate: 1.0, in_: 22.0, lag: 0.01, out: 44.0
                                    ... mixer/levels/4 (InputLevels)
                                        out: 44.0, gate: 1.0, lag: 0.01
                                    ... group (Devices)
                                        ... group (Device)
                                            ... mixer/patch[replace]/4x4 (DeviceIn)
                                                active: 1.0, gate: 1.0, in_: 44.0, lag: 0.01, out: 48.0
                                            ... group (Body)
                                                ... 15a77f27cd96f4488c4a9b094478d045
                                                    out: 48.0, index: 0.0
                                            ... mixer/patch[hard,mix]/4x4 (DeviceOut)
                                                active: 1.0, gate: 1.0, hard_gate: 1.0, in_: 48.0, lag: 0.01, mix: 1.0, out: 44.0
                                    ... mixer/levels/4 (PrefaderLevels)
                                        out: 44.0, gate: 1.0, lag: 0.01
                                    ... group (PreFaderSends)
                                    ... mixer/patch[gain,hard,replace]/4x4 (Output)
                                        active: 1.0, gain: c2, gate: 1.0, hard_gate: 1.0, in_: 44.0, lag: 0.01, out: 44.0
                                    ... group (PostFaderSends)
                                        ... mixer/patch[gain]/4x2 (Send)
                                            active: 1.0, gain: 0.0, gate: 1.0, in_: 44.0, lag: 0.01, out: 20.0
                                    ... mixer/levels/4 (PostfaderLevels)
                                        out: 44.0, gate: 1.0, lag: 0.01
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
