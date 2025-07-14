# -*- coding: utf-8 -*-

"""
This module defines the base storage interface for Session.py.
"""

from abc import ABC, abstractmethod
from typing import Any, List

class Storage(ABC):
    """
    Abstract base class for storage implementations.
    """

    @abstractmethod
    async def get(self, key: str) -> Any:
        """
        Retrieves a value from the storage.

        :param key: The key of the value to retrieve.
        :return: The value associated with the key, or None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """
        Saves a value to the storage.

        :param key: The key to associate with the value.
        :param value: The value to save.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Deletes a value from the storage.

        :param key: The key of the value to delete.
        """
        raise NotImplementedError

    @abstractmethod
    async def has(self, key: str) -> bool:
        """
        Checks if a key exists in the storage.

        :param key: The key to check.
        :return: True if the key exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def append_list(self, key: str, item: Any) -> None:
        """
        Appends an item to a list in the storage.
        If the list does not exist, it will be created.

        :param key: The key of the list.
        :param item: The item to append.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_list(self, key: str) -> List[Any]:
        """
        Retrieves a list from the storage.

        :param key: The key of the list to retrieve.
        :return: The list associated with the key, or an empty list if not found.
        """
        raise NotImplementedError
