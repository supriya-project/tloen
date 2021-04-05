from tloen.domain import Application
from tloen.domain.enums import ApplicationStatus


def test_1():
    application = Application()
    assert len(application.contexts) == 0
    assert application.status == ApplicationStatus.OFFLINE
