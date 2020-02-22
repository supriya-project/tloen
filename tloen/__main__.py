import asyncio

from .harness import Harness


async def main():
    await Harness().run()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
