import pytest

from tloen.core import Application


@pytest.mark.asyncio
async def test_repeat():
    """
    Unmuting more than once is a no-op
    """
    application = Application()
    context = await application.add_context()
    await context.add_track(name="a")
    await application.boot()
    await context["a"].mute()
    await context["a"].unmute()
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["a"].unmute()
    assert not len(transcript.sent_messages)


@pytest.mark.asyncio
async def test_stacked():
    """
    Unmuting while a parent is muted is a no-op
    """
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track(name="a")
    track_b = await track_a.add_track(name="b")
    await track_b.add_track(name="c")
    await application.boot()
    await context["a"].mute()
    await context["b"].mute()
    await context["c"].mute()
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["c"].unmute()
        await context["b"].unmute()
    assert not len(transcript.sent_messages)
    with context.provider.server.osc_protocol.capture() as transcript:
        await context["a"].unmute()
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    # Unmuting the root-most parent unmutes all children at once
    assert message.to_list() == [
        None,
        [
            ["/n_set", track.node_proxies["output"].identifier, "active", 1]
            for track in [context["a"], context["b"], context["c"]]
        ],
    ]
