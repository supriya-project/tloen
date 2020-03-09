import dataclasses
from typing import Union
from uuid import UUID

from ..bases import Command
from ..domain import BufferParameter, BusParameter, CallbackParameter


@dataclasses.dataclass
class SetParameterBuffer(Command):
    parameter_uuid: UUID
    path: str

    async def execute(self, harness):
        parameter: BufferParameter = harness.domain_application.registry[
            self.parameter_uuid
        ]
        await parameter.set_(self.path)


@dataclasses.dataclass
class SetParameterValue(Command):
    parameter_uuid: UUID
    value: float

    async def execute(self, harness):
        parameter: Union[
            BusParameter, CallbackParameter
        ] = harness.domain_application.registry[self.parameter_uuid]
        await parameter.set_(self.value)
