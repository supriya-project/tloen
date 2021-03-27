import pytest

from tloen.domain import Application


@pytest.mark.asyncio
async def test_repeat():
    """
    Unsoloing more than once is a no-op
    """
    application = Application()
    context = await application.add_context()
    await context.add_track(name="a")
    await context.add_track(name="b")
    await application.boot()
    await context["a"].solo()
    await context["a"].unsolo()
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["a"].unsolo()
    assert not len(transcript.sent_messages)


@pytest.mark.asyncio
async def test_stacked():
    """
    Unsoloing while a parent is soloed is a no-op
    """
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await track_a.add_track(name="b")
    await track_b.add_track(name="c")
    await context.add_track(name="d")
    await application.boot()
    await context["a"].solo()
    await context["b"].solo(exclusive=False)
    await context["c"].solo(exclusive=False)
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["c"].unsolo(exclusive=True)
        await context["b"].unsolo(exclusive=True)
    assert not len(transcript.sent_messages)
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["a"].unsolo()
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    # Unsoloing the root-most parent unsoloes muted tracks
    assert message.to_list() == [
        None,
        [["/n_set", context["d"].node_proxies["output"].identifier, "active", 1]],
    ]


@pytest.mark.asyncio
async def test_exclusivity():
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await context.add_track(name="b")
    track_c = await context.add_track(name="c")
    track_d = await context.add_track(name="d")
    await track_a.solo()
    await track_b.solo(exclusive=False)
    await track_c.solo(exclusive=False)
    assert [track.is_active for track in context.tracks] == [True, True, True, False]
    await track_a.unsolo(exclusive=True)
    assert [track.is_active for track in context.tracks] == [False, True, True, False]
    await track_d.solo(exclusive=False)
    assert [track.is_active for track in context.tracks] == [False, True, True, True]
    await track_b.unsolo()
    assert [track.is_active for track in context.tracks] == [True, True, True, True]
