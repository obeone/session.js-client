# -*- coding: utf-8 -*-

"""
This module handles storing messages on the network.
"""

import json
import random
from typing import TYPE_CHECKING, Dict, Any
from session_py.errors import SessionFetchError, SessionFetchErrorCode
from session_py.network.base import Request

if TYPE_CHECKING:
    from .session import Session


async def _store_message(self: 'Session', message: Dict[str, Any], data: Dict[str, Any]) -> str:
    """
    Stores a message on the network.
    """
    message_to_self = data['destination'] == self.session_id
    swarms = [await self.get_our_swarm()] if message_to_self else await self.get_swarms_for(data['destination'])

    if not swarms:
        raise SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="No swarms available to store message")

    # This is a simplified implementation of the retry logic.
    for _ in range(5):
        swarm = random.choice(swarms)
        snode = random.choice(swarm.snodes)

        body = {
            "method": "store",
            "params": {
                "pubkey": data['destination'],
                "timestamp": self.get_now_with_network_offset(),
                "ttl": data['ttl'],
                "data": data['data64']
            }
        }

        req = Request(
            url=f"https://{snode.host}:{snode.port}/storage_rpc/v1",
            method="POST",
            body=json.dumps(body)
        )

        try:
            resp = await self.network.on_request(req)
            if resp.status_code == 200:
                # A real implementation would parse the response and return the hash
                return "hash_from_response"
            
            # If status code is not 200, treat as an error and retry
            raise SessionFetchError(
                code=SessionFetchErrorCode.SNODE_ERROR,
                message=f"Snode failed to store message with status {resp.status_code}"
            )

        except SessionFetchError as e:
            # Remove the failing swarm and retry with another
            swarms = [s for s in swarms if s != swarm]
            if not swarms:
                raise e  # No more swarms to try
    
    raise SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="Failed to store message after multiple retries")
