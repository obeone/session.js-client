# Session.py

A Python library for the Session messenger.

## Installation

```bash
pip install session.py
```

## Usage

### Initialization

First, you need to initialize a `Session` instance. You can do this by providing a 13-word mnemonic.

```python
import asyncio
from session_py import Session

async def main():
    # Create a new session instance
    session = Session()

    # Set the mnemonic
    # IMPORTANT: Replace this with your actual 13-word mnemonic
    mnemonic = "your 13 word mnemonic here"
    session.set_mnemonic(mnemonic)

    print(f"Session ID: {session.get_session_id()}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Sending a message

To send a message, you need the Session ID of the recipient.

```python
import asyncio
from session_py import Session

async def main():
    # Create a new session instance
    session = Session()

    # Set the mnemonic
    mnemonic = "your 13 word mnemonic here"
    session.set_mnemonic(mnemonic)

    # The recipient's Session ID
    recipient_session_id = "05..."  # Replace with a valid Session ID

    # Send a message
    await session.send_message(
        to=recipient_session_id,
        text="Hello, world!"
    )

    print("Message sent!")

if __name__ == '__main__':
    asyncio.run(main())
```

### Receiving messages

You can use a `Poller` to listen for incoming messages.

```python
import asyncio
from session_py import Session, Poller

async def main():
    # Create a new session instance
    session = Session()

    # Set the mnemonic
    mnemonic = "your 13 word mnemonic here"
    session.set_mnemonic(mnemonic)

    # Create a poller
    poller = Poller(session)

    # Define a message handler
    @poller.on_message
    def handle_message(message):
        print(f"New message from {message['author_session_id']}: {message['text']}")

    # Start polling
    await poller.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
```

## Disclaimer

This is an unofficial library. Use it at your own risk.
