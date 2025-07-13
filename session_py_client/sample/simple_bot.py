import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from network import Network
from polling.poller import Poller, NetworkModule
from session_py_client import Session, generate_mnemonic


class MessageNetwork(NetworkModule):
    """Network module fetching messages using the base network layer."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def fetch_messages(self):
        """Fetch new messages from the server."""
        return await self._session.network.on_request("fetch_messages", None)


async def main() -> None:
    """Run a simple echo bot that replies to incoming messages."""
    base_url = os.environ.get("SESSION_BASE_URL", "https://backend.getsession.org")
    mnemonic = os.environ.get("SESSION_MNEMONIC")

    network = Network(base_url)
    session = Session(network=network)

    if not mnemonic:
        mnemonic = generate_mnemonic()
        print("Mnemonic:", mnemonic)
    await session.set_mnemonic(mnemonic)
    print("Contact ID:", session.get_session_id())

    poller = Poller(MessageNetwork(session), interval=5.0)
    session.add_poller(poller)

    def on_messages(msgs):
        for msg in msgs:
            sender = msg.get("from")
            text = msg.get("body")
            print("Received from", sender + ":", text)
            if sender:
                asyncio.create_task(
                    session.send_message(sender, f"Echo: {text}")
                )

    session.on("messages", on_messages)

    await asyncio.sleep(30)
    await network.close()


if __name__ == "__main__":
    asyncio.run(main())
