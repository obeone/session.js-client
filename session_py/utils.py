        # -*- coding: utf-8 -*-

"""
This module provides utility functions for the Session.py library.
"""

import asyncio
from typing import Union, overload
from .logs import get_logger

# Module-level logger used for warnings in utility helpers
logger = get_logger("utils")


def bytes_to_hex(data: bytes) -> str:
    """
    Converts a byte array to a hex string.

    :param data: The byte array to convert.
    :return: The hex string.
    """
    return data.hex()


def hex_to_bytes(hex_string: str) -> bytes:
    """
    Converts a hex string to a byte array.

    :param hex_string: The hex string to convert.
    :return: The byte array.
    """
    return bytes.fromhex(hex_string)


def concat_bytes(*args: bytes) -> bytes:
    """
    Concatenates multiple byte arrays into one.

    :param args: The byte arrays to concatenate.
    :return: The concatenated byte array.
    """
    return b"".join(args)


def bytes_to_base64(data: bytes) -> str:
    """
    Converts a byte array to a base64 string.

    :param data: The byte array to convert.
    :return: The base64 string.
    """
    import base64
    return base64.b64encode(data).decode('utf-8')


def base64_to_bytes(base64_string: str) -> bytes:
    """
    Converts a base64 string to a byte array.

    :param base64_string: The base64 string to convert.
    :return: The byte array.
    """
    import base64
    return base64.b64decode(base64_string)


@overload
def remove_prefix_if_needed(data: str) -> str: ...
    
@overload
def remove_prefix_if_needed(data: bytes) -> bytes: ...


def remove_prefix_if_needed(data: Union[str, bytes]) -> Union[str, bytes]:
    """
    Removes the '05' prefix from a session ID if it exists.

    :param data: The session ID string or bytes.
    :return: The session ID without the prefix.
    """
    if isinstance(data, str) and data.startswith('05'):
        return data[2:]
    if isinstance(data, bytes) and data.startswith(b'\x05'):
        return data[1:]
    return data


def is_hex(s: str) -> bool:
    """
    Checks if a string is a valid hex string.

    :param s: The string to check.
    :return: True if the string is a valid hex string, False otherwise.
    """
    return all(c in '0123456789abcdefABCDEF' for c in s) and len(s) % 2 == 0


def get_placeholder_display_name(session_id: str) -> str:
    """
    Generates a placeholder display name from a session ID.

    :param session_id: The session ID.
    :return: The placeholder display name.
    """
    return f"({session_id[:4]}...{session_id[-4:]})"

def now_ms() -> int:
    """
    Returns the current time in milliseconds.
    """
    import time
    return int(time.time() * 1000)

class Deferred(asyncio.Future):
    """
    A class that mimics the Deferred object from JavaScript.
    It is a future that can be resolved or rejected from outside.
    """
    def resolve(self, result):
        """
        Resolves the future with a result.
        """
        if not self.done():
            self.set_result(result)

    def reject(self, exception):
        """
        Rejects the future with an exception.
        """
        if not self.done():
            self.set_exception(exception)
