import pytest

from tloen.domain import Application, Track


@pytest.mark.asyncio
async def test_1():
    """
    Add one track
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track = await parent.add_track()
    assert isinstance(track, Track)
    assert len(track.postfader_sends) == 1
    assert list(parent.tracks) == [track]
    assert track.application is context.application
    assert track.graph_order == (3, 0, 0, 0, 1, 0)
    assert track.parent is parent.tracks
    assert track.postfader_sends[0].effective_target is parent
    assert track.provider is context.provider


@pytest.mark.asyncio
async def test_2():
    """
    Add two tracks
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track_one = await parent.add_track()
    track_two = await parent.add_track()
    assert list(parent.tracks) == [track_one, track_two]
    assert track_one.application is context.application
    assert track_one.graph_order == (3, 0, 0, 0, 1, 0)
    assert track_one.parent is parent.tracks
    assert track_one.provider is context.provider
    assert track_two.application is context.application
    assert track_two.graph_order == (3, 0, 0, 0, 1, 1)
    assert track_two.parent is parent.tracks
    assert track_two.provider is context.provider


@pytest.mark.asyncio
async def test_3():
    """
    Add one track, boot, add second track
    """
    application = Application()
    context = await application.add_context()
    parent = await context.add_track()
    track_one = await parent.add_track()
    await application.boot()
    with context.provider.server.osc_protocol.capture() as transcript:
        track_two = await parent.add_track()
    assert context.provider is not None
    assert len(transcript.sent_messages) == 1
    assert list(parent.tracks) == [track_one, track_two]
    assert track_one.application is context.application
    assert track_one.graph_order == (3, 0, 0, 0, 1, 0)
    assert track_one.parent is parent.tracks
    assert track_one.provider is context.provider
    assert track_two.application is context.application
    assert track_two.graph_order == (3, 0, 0, 0, 1, 1)
    assert track_two.parent is parent.tracks
    assert track_two.provider is context.provider
    _, message = transcript.sent_messages[0]
    assert message.to_list() == [
        None,
        [
            ["/g_new", 1059, 1, 1008],
            [
                "/s_new",
                "mixer/patch[fb,gain]/2x2",
                1060,
                1,
                1059,
                "in_",
                32.0,
                "out",
                34.0,
            ],
            ["/s_new", "mixer/levels/2", 1061, 1, 1059, "out", 34.0],
            ["/s_new", "mixer/levels/2", 1062, 1, 1059, "out", 34.0],
            [
                "/s_new",
                "mixer/patch[gain,hard,replace]/2x2",
                1063,
                1,
                1059,
                "gain",
                "c7",
                "in_",
                34.0,
                "out",
                34.0,
            ],
            ["/s_new", "mixer/levels/2", 1064, 1, 1059, "out", 34.0],
            ["/g_new", 1065, 3, 1060],
            ["/g_new", 1066, 0, 1059],
            ["/g_new", 1067, 0, 1066],
            ["/g_new", 1068, 3, 1067],
            ["/g_new", 1069, 3, 1066],
            ["/g_new", 1070, 3, 1061],
            ["/g_new", 1071, 2, 1063],
            ["/g_new", 1072, 3, 1063],
            [
                "/s_new",
                "mixer/patch[gain]/2x2",
                1073,
                0,
                1072,
                "in_",
                34.0,
                "out",
                18.0,
            ],
            ["/c_set", 7, 0.0, 8, 0.0],
        ],
    ]
