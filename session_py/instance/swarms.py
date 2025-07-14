# -*- coding: utf-8 -*-

"""
This module handles fetching swarms.
"""

import json
import random
import asyncio
import logging
from typing import TYPE_CHECKING, List
import aiohttp

from session_py.types.swarm import Swarm
from session_py.types.snode import Snode
from session_py.errors import SessionRuntimeError, SessionRuntimeErrorCode, SessionFetchError, SessionFetchErrorCode
from session_py.network.base import Request
from session_py.utils import remove_prefix_if_needed
from session_py.instance.snode_batch import do_snode_batch_request

if TYPE_CHECKING:
    from .session import Session


async def get_swarms_for(
    self: 'Session',
    session_id: str,
    max_attempts: int = 3,
    retry_delay: int = 1
) -> List[Swarm]:
    """
    Fetches the list of swarms for a given session ID with a retry mechanism.

    This function attempts to fetch the swarm list up to `max_attempts` times.
    On failure (e.g., network error, server disconnected), it waits for
    `retry_delay` seconds and tries again with a different service node.

    Args:
        self: The Session instance.
        session_id: The session public key (hex or base58).
        max_attempts: The maximum number of fetch attempts.
        retry_delay: The delay in seconds between retries.

    Returns:
        List[Swarm]: List of Swarm objects for the session.

    Raises:
        SessionRuntimeError: If no snodes are available.
        SessionFetchError: If all attempts to fetch the swarm fail.
    """
    available_snodes = await self.get_snodes()
    if not available_snodes:
        raise SessionRuntimeError(code=SessionRuntimeErrorCode.EMPTY_USER, message="No snodes available")

    last_exception = None

    for attempt in range(max_attempts):
        if not available_snodes:
            logging.warning("Ran out of snodes to try for swarm fetch.")
            break

        snode = random.choice(available_snodes)
        available_snodes.remove(snode)  # Avoid reusing the same snode on retry
        url = f"https://{snode.host}:{snode.port}/storage_rpc/v1"

        subrequests = [{
            "method": "get_swarm",
            "params": {"pubkey": session_id}
        }]

        try:
            batch_result = await do_snode_batch_request(
                url=url,
                subrequests=subrequests,
                timeout=10
            )

            if not batch_result or not isinstance(batch_result, list):
                raise SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="Empty or invalid batch response")

            body = batch_result[0]
            snodes_list = body.get("body", {}).get("snodes", [])

            if not snodes_list:
                error_code = body.get("code")
                if error_code == 421:
                    raise SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="421 handled. Retry this request with a new snode.")
                raise SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="No snodes found in batch response")

            swarm_snodes = [
                Snode(
                    host=s.get("ip") or s.get("public_ip"),
                    port=s.get("port") or s.get("storage_port"),
                    pubkey_x25519=s.get("x25519") or s.get("pubkey_x25519"),
                    pubkey_ed25519=s.get("ed25519") or s.get("pubkey_ed25519")
                )
                for s in snodes_list
            ]
            return [Swarm(snodes=swarm_snodes)]

        except (SessionFetchError, aiohttp.ClientError) as e:
            last_exception = e
            logging.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed to fetch swarm from {snode.host}: {e}. "
                f"Retrying in {retry_delay}s..."
            )
            await asyncio.sleep(retry_delay)
        except Exception as e:
            last_exception = e
            logging.error(f"An unexpected error occurred during swarm fetch attempt {attempt + 1}: {e}")
            # Breaking on unexpected errors to avoid unpredictable retry behavior
            break

    raise SessionFetchError(
        code=SessionFetchErrorCode.SNODE_ERROR,
        message=f"Failed to fetch swarms after {max_attempts} attempts. Last error: {last_exception}"
    ) from last_exception


async def get_our_swarm(self: 'Session') -> Swarm:
    """
    Fetches the swarm for the current user.
    """
    if not self.session_id:
        raise SessionRuntimeError(code=SessionRuntimeErrorCode.EMPTY_USER, message='Instance is not initialized; use set_mnemonic first')
    
    if self.our_swarm:
        return self.our_swarm

    self.our_swarms = await self.get_swarms_for(self.session_id)
    self.our_swarm = random.choice(self.our_swarms)
    
    if not self.our_swarm:
        raise SessionRuntimeError(code=SessionRuntimeErrorCode.EMPTY_USER, message="No swarms found for this instance")
        
    return self.our_swarm
