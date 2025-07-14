# -*- coding: utf-8 -*-

"""
This module defines the base network interface for Session.py.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Request:
    """
    Represents a network request.
    """

    def __init__(self, url: str, method: Optional[str] = None, headers: Optional[Dict[str, str]] = None, body: Any = None, rpc_method: Optional[str] = None):
        """
        Initializes a Request object.

        :param url: The URL for the request.
        :param method: The HTTP method (GET, POST, etc.).
        :param headers: Optional HTTP headers.
        :param body: Optional request body.
        :param rpc_method: Optional JSON-RPC method name (for JSON-RPC requests).
        """
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.rpc_method = rpc_method

class Response:
    """
    Represents a network response.
    """

    def __init__(self, status_code: int, body: Any = None, headers: Optional[Dict[str, str]] = None):
        """
        Initializes a Response object.

        :param status_code: The HTTP status code.
        :param body: The response body.
        :param headers: Optional HTTP headers.
        """
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}

class Network(ABC):
    """
    Abstract base class for network implementations.
    """

    @abstractmethod
    async def on_request(self, request: Request) -> 'Response':
        """
        Performs a network request.

        :param request: The request to perform.
        :return: The response from the network.
        """
        raise NotImplementedError
