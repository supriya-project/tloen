import pytest

from tloen.domain import Application


@pytest.mark.asyncio
async def test_1():
    """
    Add one track, delete it
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track = await parent.add_track()
    await track.delete()
    assert list(parent.tracks) == []
    assert track.application is None
    assert track.graph_order == ()
    assert track.parent is None
    assert track.provider is None


@pytest.mark.asyncio
async def test_2():
    """
    Add two tracks, delete the first
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track_one = await parent.add_track()
    track_two = await parent.add_track()
    await track_one.delete()
    assert list(parent.tracks) == [track_two]
    assert track_one.application is None
    assert track_one.graph_order == ()
    assert track_one.parent is None
    assert track_one.provider is None
    assert track_two.application is context.application
    assert track_two.graph_order == (3, 0, 0, 0, 2, 0)
    assert track_two.parent is parent.tracks
    assert track_two.provider is context.provider


@pytest.mark.asyncio
async def test_3():
    """
    Add one track, boot, add second track, delete the first
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track_one = await parent.add_track()
    await application.boot()
    track_two = await parent.add_track()
    with context.provider.server.osc_protocol.capture() as transcript:
        await track_one.delete()
    assert list(parent.tracks) == [track_two]
    assert track_one.application is None
    assert track_one.graph_order == ()
    assert track_one.parent is None
    assert track_one.provider is None
    assert track_two.application is context.application
    assert track_two.graph_order == (3, 0, 0, 0, 2, 0)
    assert track_two.parent is parent.tracks
    assert track_two.provider is context.provider
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [None, [["/n_set", 1009, "gate", 0]]]
