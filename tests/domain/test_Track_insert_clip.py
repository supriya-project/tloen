import pytest
from uqbar.strings import normalize

from tloen.domain import Application, Clip


@pytest.fixture
async def track():
    application = Application()
    context = await application.add_context()
    return await context.add_track()


@pytest.mark.asyncio
async def test_1(track):
    clip = await track.insert_clip(from_=0.0, to=1.0)
    assert isinstance(clip, Clip)
    assert list(track.clips) == [clip]
    assert clip.application is track.application
    assert clip.graph_order == (3, 0, 0, 0, 0, 0)
    assert clip.parent is track.clips


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "inputs, expectation",
    [
        (
            [(0.0, 1.0), (0.5, 1.5)],
            lambda track: normalize(
                f"""
                <Clips>
                    <Clip {track.clips[0].uuid} 0.0 0.5>
                    <Clip {track.clips[1].uuid} 0.5 1.5>
                """
            ),
        ),
        (
            [(1.0, 2.0), (0.5, 1.5)],
            lambda track: normalize(
                f"""
                <Clips>
                    <Clip {track.clips[0].uuid} 0.5 1.5>
                    <Clip {track.clips[1].uuid} 1.5 2.0>
                """
            ),
        ),
        (
            [(0.0, 2.0), (0.5, 1.5)],
            lambda track: normalize(
                f"""
                <Clips>
                    <Clip {track.clips[0].uuid} 0.0 0.5>
                    <Clip {track.clips[1].uuid} 0.5 1.5>
                    <Clip {track.clips[2].uuid} 1.5 2.0>
                """
            ),
        ),
        (
            [(0.0, 1.0), (2.0, 3.0), (0.5, 2.5)],
            lambda track: normalize(
                f"""
                <Clips>
                    <Clip {track.clips[0].uuid} 0.0 0.5>
                    <Clip {track.clips[1].uuid} 0.5 2.5>
                    <Clip {track.clips[2].uuid} 2.5 3.0>
                """
            ),
        ),
        (
            [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (0.5, 2.5)],
            lambda track: normalize(
                f"""
                <Clips>
                    <Clip {track.clips[0].uuid} 0.0 0.5>
                    <Clip {track.clips[1].uuid} 0.5 2.5>
                    <Clip {track.clips[2].uuid} 2.5 3.0>
                """
            ),
        ),
    ],
)
async def test_2(track, inputs, expectation):
    for from_, to in inputs:
        await track.insert_clip(from_=from_, to=to)
    actual = str(track.clips)
    expected = expectation(track)
    assert actual == expected
