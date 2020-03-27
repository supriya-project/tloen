import pytest

from tloen.domain import Clip, Note


@pytest.mark.asyncio
async def test_1():
    clip = Clip()
    assert clip.notes == []
    await clip.add_notes([Note(0, 2), Note(0, 5), Note(5, 10), Note(20, 35)])
    assert clip.notes == [Note(0, 5), Note(5, 10), Note(20, 35)]
    await clip.add_notes([Note(25, 35)])
    assert clip.notes == [Note(0, 5), Note(5, 10), Note(20, 25), Note(25, 35)]
    await clip.add_notes([Note(0, 1, velocity=127)])
    assert clip.notes == [
        Note(0, 1, velocity=127),
        Note(5, 10),
        Note(20, 25),
        Note(25, 35),
    ]
