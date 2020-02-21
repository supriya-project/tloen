import asyncio

import pytest

from tloen.core import Application, AudioEffect, Chain, RackDevice


@pytest.mark.parametrize(
    "chain_names, levels",
    [
        (["outer/a/a"], [1, 0, 0, 0, 1, 1, 1, 1]),
        (["outer/a/b"], [0, 1, 1, 1, 1, 1, 1, 1]),
        (["inner/a/a"], [1, 1, 1, 0, 1, 1, 1, 1]),
        (["inner/a/b"], [1, 1, 0, 1, 1, 1, 1, 1]),
        (["outer/b/a"], [1, 1, 1, 1, 1, 0, 0, 0]),
        (["outer/b/b"], [1, 1, 1, 1, 0, 1, 1, 1]),
        (["inner/b/a"], [1, 1, 1, 1, 1, 1, 1, 0]),
        (["inner/b/b"], [1, 1, 1, 1, 1, 1, 0, 1]),
    ],
)
@pytest.mark.asyncio
async def test_levels(chain_mute_solo_application, chain_names, levels):
    await chain_mute_solo_application.boot()
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.solo()
    await asyncio.sleep(0.2)
    assert [
        int(_)
        for _ in chain_mute_solo_application.primary_context.master_track.rms_levels[
            "input"
        ]
    ] == levels


@pytest.mark.parametrize(
    "soloed_chain_names, muted_chain_names",
    [
        (["outer/a/a"], ["outer/a/b"]),
        (["outer/a/b"], ["outer/a/a"]),
        (["inner/a/a"], ["inner/a/b"]),
        (["inner/a/b"], ["inner/a/a"]),
        (["outer/b/a"], ["outer/b/b"]),
        (["outer/b/b"], ["outer/b/a"]),
        (["inner/b/a"], ["inner/b/b"]),
        (["inner/b/b"], ["inner/b/a"]),
    ],
)
@pytest.mark.asyncio
async def test_transcript(chain_mute_solo_application, soloed_chain_names, muted_chain_names):
    await chain_mute_solo_application.boot()
    for soloed_chain_name in soloed_chain_names:
        soloed_chain = chain_mute_solo_application.primary_context[soloed_chain_name]
        with chain_mute_solo_application.primary_context.provider.server.osc_protocol.capture() as transcript:
            await soloed_chain.solo()
        osc_messages = []
        for muted_chain_name in muted_chain_names:
            muted_chain = chain_mute_solo_application.primary_context[muted_chain_name]
            osc_messages.append(
                ["/n_set", muted_chain.node_proxies["output"].identifier, "active", 0]
            )
        assert len(transcript.sent_messages) == 1
        _, message = transcript.sent_messages[0]
        assert message.to_list() == [None, osc_messages]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "chain_names, expected",
    [
        (["outer/a/a"], [1, 0, 1, 1, 1, 1, 1, 1]),
        (["outer/a/b"], [0, 1, 1, 1, 1, 1, 1, 1]),
        (["inner/a/a"], [1, 1, 1, 0, 1, 1, 1, 1]),
        (["inner/a/b"], [1, 1, 0, 1, 1, 1, 1, 1]),
        (["outer/b/a"], [1, 1, 1, 1, 1, 0, 1, 1]),
        (["outer/b/b"], [1, 1, 1, 1, 0, 1, 1, 1]),
        (["inner/b/a"], [1, 1, 1, 1, 1, 1, 1, 0]),
        (["inner/b/b"], [1, 1, 1, 1, 1, 1, 0, 1]),
    ],
)
@pytest.mark.asyncio
async def test_is_active(chain_mute_solo_application, booted, chain_names, expected):
    if booted:
        await chain_mute_solo_application.boot()
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.solo()
    all_chains = list(
        chain_mute_solo_application.primary_context.depth_first(prototype=Chain)
    )
    actual = [bool(chain.is_active) for chain in all_chains]
    assert actual == [bool(x) for x in expected]


@pytest.mark.parametrize("booted", [True, False])
@pytest.mark.parametrize(
    "chain_names, expected",
    [
        (["outer/a/a"], [1, 0, 0, 0, 0, 0, 0, 0]),
        (["outer/a/b"], [0, 1, 0, 0, 0, 0, 0, 0]),
        (["inner/a/a"], [0, 0, 1, 0, 0, 0, 0, 0]),
        (["inner/a/b"], [0, 0, 0, 1, 0, 0, 0, 0]),
        (["outer/b/a"], [0, 0, 0, 0, 1, 0, 0, 0]),
        (["outer/b/b"], [0, 0, 0, 0, 0, 1, 0, 0]),
        (["inner/b/a"], [0, 0, 0, 0, 0, 0, 1, 0]),
        (["inner/b/b"], [0, 0, 0, 0, 0, 0, 0, 1]),
    ],
)
@pytest.mark.asyncio
async def test_is_soloed(chain_mute_solo_application, booted, chain_names, expected):
    if booted:
        await chain_mute_solo_application.boot()
    for chain_name in chain_names:
        chain = chain_mute_solo_application.primary_context[chain_name]
        await chain.solo()
    all_chains = list(
        chain_mute_solo_application.primary_context.depth_first(prototype=Chain)
    )
    actual = [bool(chain.is_soloed) for chain in all_chains]
    assert actual == [bool(x) for x in expected]


@pytest.mark.asyncio
async def test_repeat(chain_mute_solo_application):
    await chain_mute_solo_application.boot()
    await chain_mute_solo_application.primary_context["outer/a/a"].solo()
    with chain_mute_solo_application.primary_context.provider.server.osc_protocol.capture() as transcript:
        await chain_mute_solo_application.primary_context["outer/a/a"].solo()
    assert not len(transcript.sent_messages)


@pytest.mark.asyncio
async def test_move(dc_index_synthdef_factory):
    application = Application(channel_count=4)
    context = await application.add_context()
    master_track = context.master_track
    track = await context.add_track()
    rack_one = await track.add_device(RackDevice, name="one")
    rack_two = await track.add_device(RackDevice, name="one")
    chain_a = await rack_one.add_chain(name="a")
    chain_b = await rack_one.add_chain(name="b")
    chain_c = await rack_two.add_chain(name="c")
    chain_d = await rack_two.add_chain(name="d")
    for i, chain in enumerate([chain_a, chain_b, chain_c, chain_d]):
        await chain.add_device(
            AudioEffect,
            synthdef=dc_index_synthdef_factory,
            synthdef_kwargs=dict(index=i),
        )
    await application.boot()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in master_track.rms_levels["input"]] == [1, 1, 1, 1]
    await chain_b.solo()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in master_track.rms_levels["input"]] == [0, 1, 1, 1]
    await chain_b.move(rack_two, 0)
    await asyncio.sleep(0.2)
    assert [int(_) for _ in master_track.rms_levels["input"]] == [1, 1, 0, 0]
    await chain_b.move(rack_one, 0)
    await asyncio.sleep(0.2)
    assert [int(_) for _ in master_track.rms_levels["input"]] == [0, 1, 1, 1]
    await chain_b.delete()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in master_track.rms_levels["input"]] == [1, 0, 1, 1]


@pytest.mark.asyncio
async def test_exclusivity():
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    rack = await track.add_device(RackDevice)
    chain_a = await rack.add_chain(name="a")
    chain_b = await rack.add_chain(name="b")
    chain_c = await rack.add_chain(name="c")
    chain_d = await rack.add_chain(name="d")
    await chain_a.solo()
    assert [chain.is_active for chain in rack.chains] == [True, False, False, False]
    await chain_b.solo(exclusive=False)
    assert [chain.is_active for chain in rack.chains] == [True, True, False, False]
    await chain_c.solo()
    assert [chain.is_active for chain in rack.chains] == [False, False, True, False]
    await chain_d.solo(exclusive=False)
    assert [chain.is_active for chain in rack.chains] == [False, False, True, True]
