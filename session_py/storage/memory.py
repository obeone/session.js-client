# -*- coding: utf-8 -*-

"""
This module provides an in-memory storage implementation for Session.py.
"""

from typing import Any, Dict, List
from .base import Storage

class InMemoryStorage(Storage):
    """
    An in-memory storage implementation that stores data in a dictionary.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        """
        Retrieves a value from the in-memory storage.

        :param key: The key of the value to retrieve.
        :return: The value associated with the key, or None if not found.
        """
        return self._data.get(key)

    async def set(self, key: str, value: Any) -> None:
        """
        Saves a value to the in-memory storage.

        :param key: The key to associate with the value.
        :param value: The value to save.
        """
        self._data[key] = value

    async def delete(self, key: str) -> None:
        """
        Deletes a value from the in-memory storage.

        :param key: The key of the value to delete.
        """
        if key in self._data:
            del self._data[key]

    async def has(self, key: str) -> bool:
        """
        Checks if a key exists in the in-memory storage.

        :param key: The key to check.
        :return: True if the key exists, False otherwise.
        """
        return key in self._data

    async def append_list(self, key: str, item: Any) -> None:
        """
        Appends an item to a list in the in-memory storage.
        If the list does not exist, it will be created.

        :param key: The key of the list.
        :param item: The item to append.
        """
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(item)

    async def get_list(self, key: str) -> List[Any]:
        """
        Retrieves a list from the in-memory storage.

        :param key: The key of the list to retrieve.
        :return: The list associated with the key, or an empty list if not found.
        """
        return self._data.get(key, [])
