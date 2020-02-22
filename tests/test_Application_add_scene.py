import pytest

from tloen.domain import Application, Track


@pytest.mark.asyncio
async def test_1():
    application = Application()
    context_one = await application.add_context()
    context_two = await application.add_context()
    for context in context_one, context_two:
        track = await context.add_track()
        await track.add_track()
        await context.add_track()
    for track in application.recurse(Track):
        assert len(application.scenes) == 0
        assert len(track.slots) == len(application.scenes)
    scene_one = application.add_scene()
    assert scene_one in application.scenes
    assert application.scenes.index(scene_one) == 0
    for track in application.recurse(Track):
        assert len(application.scenes) == 1
        assert len(track.slots) == len(application.scenes)
    scene_two = application.add_scene()
    assert scene_two in application.scenes
    assert application.scenes.index(scene_two) == 1
    for track in application.recurse(Track):
        assert len(application.scenes) == 2
        assert len(track.slots) == len(application.scenes)


@pytest.mark.asyncio
async def test_2():
    application = Application()
    for _ in range(3):
        application.add_scene()
    assert len(application.scenes) == 3
    context = await application.add_context()
    track = await context.add_track()
    assert len(track.slots) == 3
