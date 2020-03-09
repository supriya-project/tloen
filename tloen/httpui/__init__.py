import asyncio
import aiohttp.web

from ..pubsub import PubSub


class Application:
    def __init__(self, command_queue: asyncio.Queue, pubsub=None, registry=None):
        self.command_queue = command_queue
        self.pubsub = pubsub or PubSub()
        self.registry = registry if registry is not None else {}
        self.app = aiohttp.web.Application()
        self.runner = aiohttp.web.AppRunner(self.app)
        self.app.add_routes([
            aiohttp.web.get("/application", self.get_application),
        ])

    async def exit(self):
        await self.runner.cleanup()

    async def get_application(self, request):
        return aiohttp.web.json_response(self.registry.application.serialize())

    async def run_async(self):
        await self.runner.setup()
        await aiohttp.web.TCPSite(self.runner, 'localhost', 8080).start()
