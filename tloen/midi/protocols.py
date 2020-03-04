class AsyncMidiProtocol:

    def __init__(self):
        self.loop = None
        self.is_running = False

    async def connect(self, port):
        if self.is_running:
            raise RuntimeError

    async def disconnect(self):
        if not self.is_running:
            return
