import asyncio

import pytest

from session_py_client import Session
from polling.poller import Poller, NetworkModule


class DummyNetwork:
    def __init__(self):
        self.requests = []

    async def on_request(self, type_, body):
        self.requests.append((type_, body))
        return {"ok": True}


class DummyPollerNetwork(NetworkModule):
    def __init__(self):
        self.calls = 0

    async def fetch_messages(self):
        self.calls += 1
        return [f"msg{self.calls}"]


def test_set_and_get_session_id():
    network = DummyNetwork()
    session = Session(network=network)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(session.set_mnemonic("seed"))
    sid = session.get_session_id()
    loop.close()
    asyncio.set_event_loop(None)

    assert isinstance(sid, str) and len(sid) > 0


def test_send_message_calls_network():
    network = DummyNetwork()
    session = Session(network=network)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(session.set_mnemonic("seed"))
    loop.run_until_complete(session.send_message("b", "hi"))
    loop.close()
    asyncio.set_event_loop(None)

    assert network.requests[0][0] == "send_message"


def test_poller_emits_event():
    network = DummyPollerNetwork()
    poller = Poller(network, interval=0.01)
    session = Session()

    received = asyncio.Event()

    def on_messages(msgs):
        received.set()

    session.on("messages", on_messages)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        session.add_poller(poller)
        await asyncio.sleep(0.05)

    loop.run_until_complete(run())
    loop.close()
    asyncio.set_event_loop(None)

    assert received.is_set()
