import asyncio

import pytest

from tloen.domain import Application, AudioEffect


@pytest.mark.asyncio
async def test_gain(dc_index_synthdef_factory):
    application = Application(channel_count=1)
    context = await application.add_context()
    track = await context.add_track()
    await track.add_device(AudioEffect, synthdef=dc_index_synthdef_factory)
    await application.boot()
    await asyncio.sleep(0.1)
    assert track.rms_levels["prefader"] == (1.0,)
    assert track.rms_levels["postfader"] == (1.0,)
    assert context.master_track.rms_levels["input"] == (1.0,)
    with context.provider.server.osc_protocol.capture() as transcript:
        await track.parameters["gain"].set_(-6.0)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [None, [["/c_set", 0, -6.0]]]
    await asyncio.sleep(0.2)
    assert track.rms_levels["prefader"] == (1.0,)
    assert round(track.rms_levels["postfader"][0], 4) == 0.5012
    assert round(context.master_track.rms_levels["input"][0], 4) == 0.5012
