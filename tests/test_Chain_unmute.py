import asyncio

import pytest

from tloen.domain import Application, AudioEffect, RackDevice


@pytest.mark.asyncio
async def test_repeat(dc_index_synthdef_factory):
    """
    Unmuting more than once is a no-op
    """
    application = Application(channel_count=1)
    context = await application.add_context()
    track = await context.add_track()
    rack = await track.add_device(RackDevice)
    chain = await rack.add_chain()
    await chain.add_device(AudioEffect, synthdef=dc_index_synthdef_factory)
    await application.boot()
    await chain.mute()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in context.master_track.rms_levels["input"]] == [0]
    await chain.unmute()
    await asyncio.sleep(0.2)
    assert [int(_) for _ in context.master_track.rms_levels["input"]] == [1]
    with context.provider.server.osc_protocol.capture() as transcript:
        await chain.unmute()
    assert not len(transcript.sent_messages)
