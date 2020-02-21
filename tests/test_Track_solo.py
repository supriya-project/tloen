import asyncio

import pytest

from tloen.core import Application, AudioEffect, Track


@pytest.mark.parametrize(
    "track_names, levels",
    [
        (["a"], [1, 0, 0, 0, 0, 0, 0, 0]),
        (["b"], [0, 1, 1, 1, 0, 0, 0, 0]),
        (["ba"], [0, 1, 1, 0, 0, 0, 0, 0]),
        (["bb"], [0, 1, 0, 1, 0, 0, 0, 0]),
        (["c"], [0, 0, 0, 0, 1, 1, 1, 1]),
        (["ca"], [0, 0, 0, 0, 1, 1, 0, 0]),
        (["cb"], [0, 0, 0, 0, 1, 0, 1, 1]),
        (["cba"], [0, 0, 0, 0, 1, 0, 1, 1]),
    ],
)
@pytest.mark.asyncio
async def test_levels(track_mute_solo_application, track_names, levels):
    await track_mute_solo_application.boot()
    for track_name in track_names:
        track = track_mute_solo_application.primary_context[track_name]
        await track.solo()
    await asyncio.sleep(0.2)
    assert [
        int(_)
        for _ in track_mute_solo_application.primary_context.master_track.rms_levels[
            "input"
        ]
    ] == levels


@pytest.mark.parametrize(
    "soloed_track_names, muted_track_names",
    [
        (["a"], ["b", "ba", "bb", "c", "ca", "cb", "cba"]),
        (["b"], ["a", "c", "ca", "cb", "cba"]),
        (["ba"], ["a", "bb", "c", "ca", "cb", "cba"]),
        (["bb"], ["a", "ba", "c", "ca", "cb", "cba"]),
        (["c"], ["a", "b", "ba", "bb"]),
        (["ca"], ["a", "b", "ba", "bb", "cb", "cba"]),
        (["cb"], ["a", "b", "ba", "bb", "ca"]),
        (["cba"], ["a", "b", "ba", "bb", "ca"]),
    ],
)
@pytest.mark.asyncio
async def test_transcript(track_mute_solo_application, soloed_track_names, muted_track_names):
    await track_mute_solo_application.boot()
    for soloed_track_name in soloed_track_names:
        soloed_track = track_mute_solo_application.primary_context[soloed_track_name]
        with track_mute_solo_application.primary_context.provider.server.osc_protocol.capture() as transcript:
            await soloed_track.solo()
        osc_messages = []
        for muted_track_name in muted_track_names:
            muted_track = track_mute_solo_application.primary_context[muted_track_name]
            osc_messages.append(
                ["/n_set", muted_track.node_proxies["output"].identifier, "active", 0]
            )
        assert len(transcript.sent_messages) == 1
        _, message = transcript.sent_messages[0]
        assert message.to_list() == [None, osc_messages]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "track_names, expected",
    [
        (["a"], [1, 0, 0, 0, 0, 0, 0, 0]),
        (["b"], [0, 1, 1, 1, 0, 0, 0, 0]),
        (["ba"], [0, 1, 1, 0, 0, 0, 0, 0]),
        (["bb"], [0, 1, 0, 1, 0, 0, 0, 0]),
        (["c"], [0, 0, 0, 0, 1, 1, 1, 1]),
        (["ca"], [0, 0, 0, 0, 1, 1, 0, 0]),
        (["cb"], [0, 0, 0, 0, 1, 0, 1, 1]),
        (["cba"], [0, 0, 0, 0, 1, 0, 1, 1]),
    ],
)
@pytest.mark.asyncio
async def test_is_active(track_mute_solo_application, booted, track_names, expected):
    if booted:
        await track_mute_solo_application.boot()
    for track_name in track_names:
        track = track_mute_solo_application.primary_context[track_name]
        await track.solo()
    all_tracks = list(
        track_mute_solo_application.primary_context.depth_first(prototype=Track)
    )
    actual = [bool(track.is_active) for track in all_tracks]
    assert actual == [bool(x) for x in expected]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "track_names, expected",
    [
        (["a"], [1, 0, 0, 0, 0, 0, 0, 0]),
        (["b"], [0, 1, 0, 0, 0, 0, 0, 0]),
        (["ba"], [0, 0, 1, 0, 0, 0, 0, 0]),
        (["bb"], [0, 0, 0, 1, 0, 0, 0, 0]),
        (["c"], [0, 0, 0, 0, 1, 0, 0, 0]),
        (["ca"], [0, 0, 0, 0, 0, 1, 0, 0]),
        (["cb"], [0, 0, 0, 0, 0, 0, 1, 0]),
        (["cba"], [0, 0, 0, 0, 0, 0, 0, 1]),
    ],
)
@pytest.mark.asyncio
async def test_is_soloed(track_mute_solo_application, booted, track_names, expected):
    if booted:
        await track_mute_solo_application.boot()
    for track_name in track_names:
        track = track_mute_solo_application.primary_context[track_name]
        await track.solo()
    all_tracks = list(
        track_mute_solo_application.primary_context.depth_first(prototype=Track)
    )
    actual = [bool(track.is_soloed) for track in all_tracks]
    assert actual == [bool(x) for x in expected]


@pytest.mark.asyncio
async def test_stacked():
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await track_a.add_track(name="b")
    await track_b.add_track(name="c")
    await application.boot()
    await application.primary_context["a"].solo()
    with application.primary_context.provider.server.osc_protocol.capture() as transcript:
        await application.primary_context["b"].solo()
        await application.primary_context["c"].solo()
    assert not len(transcript.sent_messages)


@pytest.mark.asyncio
async def test_repeat():
    application = Application()
    context = await application.add_context()
    await context.add_track(name="a")
    await application.boot()
    await application.primary_context["a"].solo()
    with application.primary_context.provider.server.osc_protocol.capture() as transcript:
        await application.primary_context["a"].solo()
    assert not len(transcript.sent_messages)


@pytest.mark.asyncio
async def test_move(dc_index_synthdef_factory):
    application = Application()
    context = await application.add_context()
    track_one = await context.add_track(name="one")
    await track_one.add_device(
        AudioEffect, synthdef=dc_index_synthdef_factory, synthdef_kwargs=dict(index=0)
    )
    await application.boot()
    await asyncio.sleep(0.2)
    assert context.master_track.rms_levels["input"] == (1.0, 0.0)
    track_two = Track(name="two")
    await track_two.add_device(
        AudioEffect, synthdef=dc_index_synthdef_factory, synthdef_kwargs=dict(index=1)
    )
    await track_two.solo()
    await track_two.move(context, 1)
    await asyncio.sleep(0.2)
    assert not track_one.is_active
    assert context.master_track.rms_levels["input"] == (0.0, 1.0)
    await track_one.move(track_two, 0)
    await asyncio.sleep(0.2)
    assert track_one.is_active
    assert context.master_track.rms_levels["input"] == (1.0, 1.0)
    await track_one.move(context, 0)
    await asyncio.sleep(0.2)
    assert not track_one.is_active
    assert context.master_track.rms_levels["input"] == (0.0, 1.0)
    await track_two.delete()
    await asyncio.sleep(0.2)
    assert track_one.is_active
    assert context.master_track.rms_levels["input"] == (1.0, 0.0)


@pytest.mark.asyncio
async def test_exclusivity():
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await context.add_track(name="b")
    track_c = await context.add_track(name="c")
    track_d = await context.add_track(name="d")
    await track_a.solo()
    assert [track.is_active for track in context.tracks] == [True, False, False, False]
    await track_b.solo(exclusive=False)
    assert [track.is_active for track in context.tracks] == [True, True, False, False]
    await track_c.solo()
    assert [track.is_active for track in context.tracks] == [False, False, True, False]
    await track_d.solo(exclusive=False)
    assert [track.is_active for track in context.tracks] == [False, False, True, True]
