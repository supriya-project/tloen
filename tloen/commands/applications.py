import dataclasses

from ..bases import Command


@dataclasses.dataclass
class AddContext(Command):
    async def execute(self, harness):
        await harness.domain_application.add_context()


@dataclasses.dataclass
class AddScene(Command):
    async def execute(self, harness):
        await harness.domain_application.add_scene()


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
