# -*- coding: utf-8 -*-

"""
This module handles attaching pollers to a Session instance.
"""

from typing import TYPE_CHECKING, List, Dict, Any
from session_py.polling.poller import Poller
from session_py.errors import SessionValidationError, SessionValidationErrorCode

if TYPE_CHECKING:
    from .session import Session


async def on_messages_received(self: 'Session', messages: List[Dict[str, Any]]):
    """
    Handles a list of received messages, decrypts them (in a real implementation),
    and emits the 'on_message' event for each.

    :param messages: A list of received message dictionaries.
    """
    # A real implementation would decrypt messages here.
    # For now, we assume they are already decrypted.
    for message in messages:
        self.on_message.emit(message)

async def update_last_hashes(self: 'Session', hashes: List[Dict[str, Any]]):
    """
    Updates the last seen hashes for swarms in storage.

    :param hashes: A list of dictionaries, each containing 'swarm_id' and 'hash'.
    """
    if not self.storage:
        return
    last_hashes = await self.storage.get('lastHashes') or {}
    for h in hashes:
        last_hashes[h['swarm_id']] = h['hash']
    await self.storage.set('lastHashes', last_hashes)

def on_swarm_connection_failed(self: 'Session', swarm):
    """
    Handles a failed connection to a swarm.

    :param swarm: The swarm object that failed to connect.
    """
    # In a real implementation, this would trigger a swarm re-selection
    # and potentially a backoff strategy.
    print(f"Swarm connection failed for {swarm}. Re-selection logic not implemented yet.")
