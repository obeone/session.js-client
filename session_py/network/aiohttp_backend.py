# -*- coding: utf-8 -*-

"""
This module provides an aiohttp-based network implementation for Session.py.
"""

import asyncio
import aiohttp
import json
from typing import Optional
from .base import Network, Request, Response
from ..errors import SessionFetchError, SessionFetchErrorCode
from session_py.logs import get_logger

logger = get_logger(__name__)

class AiohttpNetwork(Network):
    """
    An aiohttp-based network implementation for asynchronous HTTP requests.
    """

    def __init__(self, proxy: Optional[str] = None):
        """
        Initializes the AiohttpNetwork instance.

        :param proxy: Optional proxy URL to use for requests.
        """
        self.proxy = proxy

    async def on_request(self, request: Request) -> Response:
        """
        Performs a network request using aiohttp.

        :param request: The Request object containing request details.
        :return: A Response object with the response data.
        :raises SessionFetchError: If the request times out or fails.
        """
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                # Default to POST if body is present, otherwise GET
                method = request.method
                if method is None:
                    method = 'POST' if request.body is not None else 'GET'

                # Prepare payload: JSON-RPC 2.0 only for /json_rpc endpoints, else send body as-is
                data = request.body
                headers = request.headers or {}
                if isinstance(data, dict) and getattr(request, "rpc_method", None) and str(request.url).endswith("/json_rpc"):
                    payload = {
                        'jsonrpc': '2.0',
                        'id': 0,
                        'method': request.rpc_method,
                        'params': data
                    }
                    data = aiohttp.JsonPayload(payload)
                    headers['Content-Type'] = 'application/json'
                elif isinstance(data, dict):
                    # For /storage_rpc/v1 and similar, send as plain JSON (not JSON-RPC)
                    data = aiohttp.JsonPayload(data)
                    headers['Content-Type'] = 'application/json'

                # Disable SSL verification for service node requests (HTTPS, self-signed certs)
                ssl_param = False if str(request.url).startswith("https://") else None
                async with session.request(
                    method=method,
                    url=request.url,  # Utilise l'URL dynamique du Snode
                    headers=headers,
                    data=data,
                    proxy=self.proxy,
                    ssl=ssl_param
                ) as response:
                    raw_text = await response.text()
                    logger.debug("Received raw response text: %s", raw_text)
                    try:
                        body = json.loads(raw_text)
                    except json.JSONDecodeError:
                        # Not a JSON response, use raw text, especially for error messages
                        body = raw_text

                    if isinstance(body, dict) and 'error' in body:
                        raise SessionFetchError(
                            code=SessionFetchErrorCode.SNODE_ERROR,
                            message=f"Snode request failed: {body['error']['message']}"
                        )
                    
                    response_body = body
                    if isinstance(body, dict):
                        response_body = body.get('result', body)

                    return Response(
                        status_code=response.status,
                        body=response_body,
                        headers=dict(response.headers)
                    )
            except asyncio.TimeoutError:
                raise SessionFetchError(
                    code=SessionFetchErrorCode.TIMEOUT,
                    message=f"Request to {request.url} timed out"
                )
            except aiohttp.ClientError as e:
                raise SessionFetchError(
                    code=SessionFetchErrorCode.SNODE_ERROR,
                    message=f"Snode request failed: {e}"
                )
