# -*- coding: utf-8 -*-

"""
This module provides a utility for sending batch JSON-RPC 2.0 requests to Session service nodes.
"""

import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

async def do_snode_batch_request(
    url: str,
    subrequests: List[Dict[str, Any]],
    proxy: Optional[str] = None,
    timeout: int = 10
) -> List[Dict[str, Any]]:
    """
    Sends a batch JSON-RPC 2.0 request to a Session service node.

    :param url: The full HTTPS URL to the service node's /storage_rpc/v1 endpoint.
    :param subrequests: A list of dicts, each representing a JSON-RPC subrequest (with 'method' and 'params').
    :param proxy: Optional proxy URL.
    :param timeout: Timeout in seconds.
    :return: A list of responses, one per subrequest.
    :raises Exception: On network or protocol error.

    Example:
        responses = await do_snode_batch_request(
            url="https://1.2.3.4:22021/storage_rpc/v1",
            subrequests=[
                {"method": "get_swarm", "params": {"pubKey": "..."}},
                {"method": "retrieve", "params": {...}}
            ]
        )
    """
    # The Session service node expects a batch as a JSON-RPC 2.0 request
    # See: https://loki-project.github.io/loki-docs/API/ServiceNodes/JSONRPC/#batch-requests-to-the-sn-api
    subrequest_bodies = []
    for sub in subrequests:
        subrequest_bodies.append({
            "method": sub["method"],
            "params": sub.get("params", {})
        })

    batch_request = {
        "jsonrpc": "2.0",
        "method": "batch",
        "params": {"requests": subrequest_bodies}
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "WhatsApp",
        "Accept-Language": "en-us"
    }
    request_body = json.dumps(batch_request)
    logger.debug(f"Sending batch request to {url} with body: {request_body}")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.post(url, data=request_body, headers=headers, proxy=proxy, ssl=False) as resp:
            if resp.status != 200:
                raise Exception(f"Batch request failed: {resp.status}")
            
            response_json = await resp.json()
            logger.debug(f"Received batch response: {response_json}")
            # The batch response has an envelope, we need to extract the results
            return response_json.get('results', [])
