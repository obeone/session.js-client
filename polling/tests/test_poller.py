import asyncio

from polling.poller import Poller, NetworkModule

class DummyNetwork(NetworkModule):
    def __init__(self) -> None:
        self.calls = 0

    async def fetch_messages(self):
        self.calls += 1
        return ["msg"]

def test_start_and_stop_polling():
    async def run() -> int:
        network = DummyNetwork()
        poller = Poller(network, interval=0.01)
        await poller.start_polling()
        await asyncio.sleep(0.05)
        await poller.stop_polling()
        return network.calls

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    calls = loop.run_until_complete(run())
    loop.close()
    asyncio.set_event_loop(None)

    assert calls >= 1
