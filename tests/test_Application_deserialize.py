import pytest
from tloen.domain import Application


@pytest.mark.asyncio
async def test_1():
    app_one = await Application.new(1, 1, 1)
    app_two = await Application.deserialize(app_one.serialize())
    assert app_one is not app_two
    assert app_one.serialize() == app_two.serialize()
