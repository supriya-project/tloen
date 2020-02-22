import pytest

from tloen.domain import Application


@pytest.mark.asyncio
async def test_1():
    application = await Application.new()
    await application.boot()
    await application.quit()
    assert application.status == Application.Status.OFFLINE
    assert application.primary_context.provider is None
