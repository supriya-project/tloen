import asyncio
from uuid import UUID
from typing import Any, Dict
from prompt_toolkit import Application as PtkApplication
from .key_bindings import key_bindings


class Application(PtkApplication):

    def __init__(self, command_queue: asyncio.Queue, **kwargs):
        self.command_queue = command_queue
        self.registry: Dict[UUID, Any] = {}
        PtkApplication.__init__(self, full_screen=True, key_bindings=key_bindings, **kwargs)
