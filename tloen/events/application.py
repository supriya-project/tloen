import dataclasses

from supriya.commands import StatusResponse

from .bases import Command


@dataclasses.dataclass
class BootApplication(Command):
    async def execute(self, harness):
        await harness.domain_application.boot()


@dataclasses.dataclass
class ExitToTerminal(Command):
    async def execute(self, harness):
        await harness.exit()


@dataclasses.dataclass
class QuitApplication(Command):
    async def execute(self, harness):
        await harness.domain_application.quit()


@dataclasses.dataclass
class ApplicationBooting:
    ...


@dataclasses.dataclass
class ApplicationBooted:
    port: int


@dataclasses.dataclass
class ApplicationQuitting:
    ...


@dataclasses.dataclass
class ApplicationQuit:
    ...


@dataclasses.dataclass
class ApplicationStatusRefreshed:
    status: StatusResponse
