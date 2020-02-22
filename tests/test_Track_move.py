import pytest

from tloen.core import Application


@pytest.mark.asyncio
async def test_1():
    """
    Unbooted, move one track before another
    """
    application = Application()
    context = await application.add_context()
    track_one = await context.add_track()
    track_two = await context.add_track()
    await track_two.move(context, 0)
    assert list(context.tracks) == [track_two, track_one]


@pytest.mark.asyncio
async def test_2():
    """
    Booted, move one track before another
    """
    application = Application()
    context = await application.add_context()
    track_one = await context.add_track()
    track_two = await context.add_track()
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await track_two.move(context, 0)
    assert list(context.tracks) == [track_two, track_one]
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [None, [["/g_head", 1001, 1016]]]


@pytest.mark.asyncio
async def test_3():
    """
    Booted, with cross-referencing sends, move one track before another
    """
    application = Application()
    context = await application.add_context()
    track_one = await context.add_track()
    track_two = await context.add_track()
    await track_one.add_send(track_two)
    await track_two.add_send(track_one)
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await track_two.move(context, 0)
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1061,
                0,
                1029,
                "in_",
                22.0,
                "out",
                18.0,
            ],
            [
                "/s_new",
                "mixer/patch[fb,gain]/2x2",
                1062,
                0,
                1015,
                "in_",
                18.0,
                "out",
                20.0,
            ],
            ["/g_head", 1001, 1016],
            ["/n_set", 1030, "gate", 0],
            ["/n_set", 1031, "gate", 0],
        ],
    ]


@pytest.mark.asyncio
async def test_4():
    """
    Booted, move one track inside another, reallocate custom send and default send
    """
    application = Application()
    context = await application.add_context()
    track_one = await context.add_track()
    track_two = await context.add_track()
    track_three = await context.add_track()
    await track_three.add_send(track_two)
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        await track_three.move(track_one, 0)
    assert list(context.tracks) == [track_one, track_two]
    assert list(track_one.tracks) == [track_three]
    assert track_three.parent is track_one.tracks
    assert len(transcript.sent_messages) == 1
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1075,
                0,
                1043,
                "in_",
                26.0,
                "out",
                18.0,
            ],
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1076,
                0,
                1043,
                "in_",
                26.0,
                "out",
                22.0,
            ],
            ["/g_tail", 1008, 1030],
            ["/n_set", 1060, "gate", 0],
            ["/n_set", 1044, "gate", 0],
        ],
    ]
