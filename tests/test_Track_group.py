import pytest

from tloen.core import Application, Track


@pytest.mark.asyncio
async def test_1():
    track_a = Track()
    track_b = Track()
    group_track = await Track.group([track_a, track_b])
    assert isinstance(group_track, Track)
    assert list(group_track.tracks) == [track_a, track_b]
    assert group_track.application is track_a.application
    assert group_track.channel_count is None
    assert group_track.name is None
    assert group_track.parent is None
    assert group_track.provider is track_a.provider
    assert not group_track.is_cued
    assert not group_track.is_muted
    assert not group_track.is_soloed
    assert track_a.parent is group_track.tracks
    assert track_b.parent is group_track.tracks


@pytest.mark.asyncio
async def test_2():
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track()
    track_b = await context.add_track()
    track_c = await context.add_track()
    group_track = await Track.group([track_b, track_c])
    assert list(context.tracks) == [track_a, group_track]
    assert list(group_track.tracks) == [track_b, track_c]
    assert group_track.application is application
    assert group_track.parent is context.tracks
    assert group_track.provider is context.provider
    assert track_b.provider is context.provider
    assert track_c.provider is context.provider


@pytest.mark.asyncio
async def test_3():
    application = Application()
    context = await application.add_context()
    track_a = await context.add_track()
    track_b = await context.add_track()
    track_c = await context.add_track()
    await application.boot()
    group_track = await Track.group([track_b, track_c])
    assert list(context.tracks) == [track_a, group_track]
    assert list(group_track.tracks) == [track_b, track_c]
    assert group_track.application is application
    assert group_track.parent is context.tracks
    assert group_track.provider is context.provider
    assert track_b.provider is context.provider
    assert track_c.provider is context.provider
