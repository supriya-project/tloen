import pytest

from tloen.domain import Application
from tloen.domain.enums import ApplicationStatus


@pytest.mark.asyncio
async def test_1():
    application = await Application.new()
    await application.boot()
    await application.quit()
    assert application.status == ApplicationStatus.OFFLINE
    assert application.primary_context.provider is None
