import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from session_py_client import Session, generate_mnemonic
from network import Network
from polling.poller import Poller, NetworkModule


class MessageNetwork(NetworkModule):
    """
    Network module fetching messages from the base network layer.

    Args:
        session (Session): Active session used to perform requests.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def fetch_messages(self) -> list:
        """
        Fetch new messages from the server.

        Returns:
            list: Raw message dictionaries returned by the network.
        """
        return await self._session.network.on_request("fetch_messages", None)


async def main() -> None:
    """
    Run a simple echo bot that replies to incoming messages.

    The bot generates a mnemonic if none is provided, prints the mnemonic and
    contact ID, then polls for messages and echoes each one back to the sender.
    It runs until interrupted.
    """
    base_url = os.environ.get("SESSION_BASE_URL", "https://backend.getsession.org")
    mnemonic = os.environ.get("SESSION_MNEMONIC")

    async with Network(base_url) as network:
        session = Session(network=network)

        if not mnemonic:
            mnemonic = generate_mnemonic()
            print("Mnemonic:", mnemonic)
        await session.set_mnemonic(mnemonic)
        print("Contact ID:", session.get_session_id())

        poller = Poller(MessageNetwork(session), interval=5.0)
        session.add_poller(poller)

        def on_messages(msgs: list) -> None:
            """
            Handle newly received messages.

            Args:
                msgs (list): List of message dictionaries.
            """
            for msg in msgs:
                sender = msg.get("from")
                text = msg.get("body")
                print("Received from", sender + ":", text)
                if sender:
                    asyncio.create_task(
                        session.send_message(sender, f"Echo: {text}")
                    )

        session.on("messages", on_messages)

        await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
