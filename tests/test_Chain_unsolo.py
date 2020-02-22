import asyncio

import pytest

from tloen.domain import Application, AudioEffect, RackDevice


@pytest.mark.asyncio
async def test_repeat(dc_index_synthdef_factory):
    """
    Unsoloing more than once is a no-op
    """
    application = Application(channel_count=2)
    context = await application.add_context()
    track = await context.add_track()
    rack = await track.add_device(RackDevice)
    await rack.add_chain(name="a")
    await rack.add_chain(name="b")
    await rack["a"].add_device(
        AudioEffect, synthdef=dc_index_synthdef_factory, synthdef_kwargs=dict(index=0)
    )
    await rack["b"].add_device(
        AudioEffect, synthdef=dc_index_synthdef_factory, synthdef_kwargs=dict(index=1)
    )
    await application.boot()
    await rack["a"].solo()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in context.master_track.rms_levels["input"]] == [1, 0]
    await rack["a"].unsolo()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in context.master_track.rms_levels["input"]] == [1, 1]
    with rack.provider.server.osc_protocol.capture() as transcript:
        await rack["a"].unsolo()
    assert not len(transcript.sent_messages)


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
    await chain_b.solo(exclusive=False)
    await chain_c.solo(exclusive=False)
    assert [chain.is_active for chain in rack.chains] == [True, True, True, False]
    await chain_a.unsolo(exclusive=True)
    assert [chain.is_active for chain in rack.chains] == [False, True, True, False]
    await chain_d.solo(exclusive=False)
    assert [chain.is_active for chain in rack.chains] == [False, True, True, True]
    await chain_b.unsolo()
    assert [chain.is_active for chain in rack.chains] == [True, True, True, True]
