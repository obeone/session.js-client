"""
Async message poller.
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, Optional


class NetworkModule:
    """Simple network interface for fetching messages."""

    async def fetch_messages(self) -> Iterable[Any]:
        """Retrieve new messages from the server."""
        raise NotImplementedError


class Poller:
    """Poll messages at a fixed interval using asyncio."""

    def __init__(self, network: NetworkModule, interval: float = 3.0) -> None:
        self._network = network
        self._interval = interval
        self._task: Optional[asyncio.Task[None]] = None
        self._running: bool = False

    async def start_polling(self) -> None:
        """Start polling in background until stopped."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop_polling(self) -> None:
        """Stop the polling loop if running."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def poll(self) -> Iterable[Any]:
        """Fetch messages once using the network module."""
        return await self._network.fetch_messages()

    async def _poll_loop(self) -> None:
        """Internal loop executed while polling is active."""
        try:
            while self._running:
                await self.poll()
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            pass
