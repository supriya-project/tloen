import pytest
import yaml

from tloen.domain import Application


@pytest.mark.asyncio
async def test_1():
    app_one = await Application.new(1, 1, 1)
    app_two = await Application.deserialize(app_one.serialize())
    assert app_one is not app_two
    assert yaml.dump(app_one.serialize()) == yaml.dump(app_two.serialize())


@pytest.mark.asyncio
async def test_2():
    app_one = await Application.new(1, 2, 1)
    track_one = app_one.contexts[0].tracks[0]
    track_two = app_one.contexts[0].tracks[1]
    await track_one.add_send(track_one)
    await track_one.add_send(track_two)
    await track_two.add_send(track_one)
    app_two = await Application.deserialize(app_one.serialize())
    assert app_one is not app_two
    assert yaml.dump(app_one.serialize()) == yaml.dump(app_two.serialize())
