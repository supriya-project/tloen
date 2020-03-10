import asyncio
import dataclasses


@dataclasses.dataclass
class Command:
    future: asyncio.Future = dataclasses.field(init=False, compare=False, hash=False)

    def __post_init__(self):
        try:
            self.future = asyncio.get_running_loop().create_future()
        except Exception:
            self.future = None


@dataclasses.dataclass
class Event:
    pass
