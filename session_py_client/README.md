# Session.py

Session.py provides a minimal Python interface for interacting with [Session messenger](https://getsession.org). It mirrors the API of the TypeScript/Bun version while focusing on async Python workflows.

## Installation

```
pip install session_py_client
```

or install from the repository:

```
pip install -e .
```

## Quick Start

```python
import asyncio
from session_py_client import Session
from network import Network

async def main():
    network = Network("https://backend.getsession.org")
    session = Session(network=network)
    await session.set_mnemonic("my seed words")
    await session.send_message("sid_recipient", "Hello from Python")

asyncio.run(main())
```

### Receiving Messages

`Session` can use a `Poller` to periodically fetch messages:

```python
import asyncio
from polling.poller import Poller, NetworkModule

class MessageNetwork(NetworkModule):
    async def fetch_messages(self):
        # implement fetching from your server
        return []

async def main():
    session = Session()
    network = MessageNetwork()
    poller = Poller(network, interval=3.0)
    session.add_poller(poller)

asyncio.run(main())
```

### Handling Avatars

```python
from session_py_client.profile import Profile, Avatar, serialize_profile, upload_avatar

async def update_avatar(session: Session, avatar_bytes: bytes):
    result = await upload_avatar(session, avatar_bytes)
    profile = Profile(display_name="Bot", avatar=Avatar(url=result["avatarPointer"], key=result["profileKey"]))
    data = serialize_profile(profile)
    await session.network.on_request("set_profile", data)
```

## Migrating from TypeScript/Bun

1. Replace `import { Session } from "session.js"` with `from session_py_client import Session`.
2. Network modules now use `asyncio` and should implement `on_request` or `fetch_messages` where needed.
3. Polling is provided by `polling.Poller` instead of Bun timers.
4. Avatars use `upload_avatar`/`download_avatar` helpers from `session_py_client.profile`.

The overall API remains similar but leverages Python async patterns.

