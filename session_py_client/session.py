from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Iterable, Optional

from .utils import (
    checkNetwork,
    checkStorage,
    SessionValidationError,
    SessionValidationErrorCode,
    Uint8ArrayToHex,
)
from .storage import InMemoryStorage, Storage
from .crypto import generate_keypair, Keypair
from polling.poller import Poller


class Session:
    """Simplified Session client."""

    def __init__(self, *, storage: Optional[Storage] = None, network: Optional[Any] = None) -> None:
        if storage is None:
            storage = InMemoryStorage()
        checkStorage(storage)
        self.storage = storage

        self.network = network
        if network is not None:
            checkNetwork(network)

        self.mnemonic: Optional[str] = None
        self.keypair: Optional[Keypair] = None
        self.session_id: Optional[str] = None

        self.pollers: set[Poller] = set()
        self.events: Dict[str, list[Callable[..., None]]] = {}

    async def set_mnemonic(self, mnemonic: str) -> None:
        """Set mnemonic and derive new keypair and session identifier."""

        if self.mnemonic is not None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Mnemonic already set")
        self.mnemonic = mnemonic
        self.keypair = generate_keypair()
        self.session_id = Uint8ArrayToHex(self.keypair.ed25519.publicKey)
        self.storage.set("mnemonic", mnemonic)

    def get_session_id(self) -> str:
        """Return the current session identifier."""

        if self.session_id is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Session not initialized")
        return self.session_id

    async def send_message(self, to: str, text: str, attachments: Optional[Iterable[Any]] = None) -> Any:
        """Send a visible message to recipient using the network module."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        body = {"to": to, "text": text}
        if attachments is not None:
            body["attachments"] = list(attachments)
        return await self.network.on_request("send_message", body)

    async def delete_message(self, to: str, timestamp: int, hash_: str) -> Any:
        """Propagate a deletion request for a single message."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        body = {"to": to, "timestamp": timestamp, "hash": hash_}
        return await self.network.on_request("delete_message", body)

    async def delete_messages(self, to: str, timestamps: Iterable[int], hashes: Iterable[str]) -> Any:
        """Propagate deletion requests for multiple messages."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        body = {"to": to, "timestamps": list(timestamps), "hashes": list(hashes)}
        return await self.network.on_request("delete_messages", body)

    async def mark_messages_as_read(
        self,
        from_id: str,
        message_timestamps: Iterable[int],
        read_at: Optional[int] = None,
    ) -> Any:
        """Mark provided messages as read."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        body = {"from": from_id, "timestamps": list(message_timestamps), "read_at": read_at}
        return await self.network.on_request("mark_messages_as_read", body)

    async def show_typing_indicator(self, conversation: str) -> Any:
        """Show a typing indicator for a conversation."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        return await self.network.on_request("show_typing_indicator", {"conversation": conversation})

    async def add_reaction(self, message_timestamp: int, message_author: str, emoji: str) -> Any:
        """Add an emoji reaction to a message."""

        if self.network is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")
        body = {"timestamp": message_timestamp, "author": message_author, "emoji": emoji}
        return await self.network.on_request("add_reaction", body)

    def on(self, event: str, callback: Callable[..., None]) -> None:
        """Register an event callback."""

        self.events.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable[..., None]) -> None:
        """Remove a previously registered callback."""

        if event in self.events:
            self.events[event] = [cb for cb in self.events[event] if cb != callback]

    def _emit(self, event: str, *args: Any) -> None:
        """Invoke callbacks for the specified event."""

        for cb in self.events.get(event, []):
            cb(*args)

    def add_poller(self, poller: Poller) -> None:
        """Attach a poller and emit ``messages`` events on new data."""

        self.pollers.add(poller)
        asyncio.create_task(self._poll_loop(poller))

    async def _poll_loop(self, poller: Poller) -> None:
        """Internal loop reading messages from poller."""

        while True:
            messages = await poller.poll()
            if messages:
                self._emit("messages", messages)
            await asyncio.sleep(getattr(poller, "_interval", 3.0))
