"""
Utility helpers for Session Python client.
"""

from __future__ import annotations

import asyncio
import base64
from enum import Enum
from typing import Any, Iterable, Generic, TypeVar, Union


class SessionValidationErrorCode(str, Enum):
    """Error codes used for validation errors."""

    INVALID_OPTIONS = "invalid_options"


class SessionValidationError(Exception):
    """Validation error, indicates developer provided invalid input."""

    def __init__(self, code: SessionValidationErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


T = TypeVar("T")


class Deferred(Generic[T]):
    """A simple deferred future implementation."""

    def __init__(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        self.future: asyncio.Future[T] = loop.create_future()

    @property
    def promise(self) -> asyncio.Future[T]:
        """Return the underlying future."""

        return self.future

    def resolve(self, value: T) -> None:
        """Resolve the future with a value."""

        if not self.future.done():
            self.future.set_result(value)

    def reject(self, reason: Exception) -> None:
        """Reject the future with an exception."""

        if not self.future.done():
            self.future.set_exception(reason)


def Uint8ArrayToHex(data: bytes | bytearray) -> str:
    """Convert bytes-like object to hex string."""

    return bytes(data).hex()


def hexToUint8Array(hex_string: str) -> bytes:
    """Convert hex string to bytes, ignoring invalid trailing characters."""

    if not hex_string:
        return b""
    output = bytearray()
    length = len(hex_string) // 2
    for i in range(length):
        pair = hex_string[2 * i : 2 * i + 2]
        try:
            output.append(int(pair, 16))
        except ValueError:
            break
    return bytes(output)


def concatUInt8Array(*arrays: Iterable[bytes]) -> bytes:
    """Concatenate multiple byte sequences."""

    return b"".join(bytes(a) for a in arrays)


def removePrefixIfNeeded(value: Union[str, bytes, bytearray]) -> Union[str, bytes]:
    """Remove 0x05 prefix from string or bytes if present."""

    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
        if data[:1] == b"\x05":
            return data[1:]
        return data
    if isinstance(value, str) and value.startswith("05"):
        return value[2:]
    return value


def isHex(value: str) -> bool:
    """Check if a string consists only of hex pairs."""

    return bool(value) and bool(__import__("re").fullmatch(r"([0-9a-fA-F]{2})+", value))


def Uint8ArrayToBase64(data: bytes | bytearray) -> str:
    """Encode bytes-like object to base64 string."""

    return base64.b64encode(bytes(data)).decode("ascii")


def base64ToUint8Array(data: str) -> bytes:
    """Decode base64 string to bytes."""

    return base64.b64decode(data)


def checkStorage(storage: Any) -> None:
    """Validate that a storage object implements required methods."""

    if not isinstance(storage, object):
        raise SessionValidationError(
            SessionValidationErrorCode.INVALID_OPTIONS, "Provided storage is invalid"
        )
    for method in ("get", "set", "delete", "has"):
        attr = getattr(storage, method, None)
        if not callable(attr):
            raise SessionValidationError(
                SessionValidationErrorCode.INVALID_OPTIONS,
                f"Provided storage does not have method {method}",
            )


def checkNetwork(network: Any) -> None:
    """Validate that a network object implements required methods."""

    if not isinstance(network, object):
        raise SessionValidationError(
            SessionValidationErrorCode.INVALID_OPTIONS, "Provided network is invalid"
        )
    attr = getattr(network, "on_request", None)
    if not callable(attr):
        raise SessionValidationError(
            SessionValidationErrorCode.INVALID_OPTIONS,
            "Provided network does not have method on_request",
        )


def get_placeholder_display_name(session_id: str) -> str:
    """Return a shortened placeholder name for a session ID.

    Args:
        session_id (str): The original session identifier.

    Returns:
        str: The placeholder display name with the first and last four
            characters of the session ID.

    """

    return f"({session_id[:4]}...{session_id[-4:]})"

