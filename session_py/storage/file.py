# -*- coding: utf-8 -*-

"""
This module provides a file-based storage implementation for Session.py.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Storage


class FileStorage(Storage):
    """
    A storage implementation that persists data to a JSON file.

    This class provides a simple way to store session data on disk,
    ensuring persistence across application restarts. It uses an
    asyncio.Lock to handle concurrent access safely.
    """

    def __init__(self, file_path: str = 'session_storage.json'):
        """
        Initializes the FileStorage instance.

        It loads existing data from the specified file or creates a new one.

        :param file_path: The path to the JSON file used for storage.
                          Defaults to 'session_storage.json' in the current
                          working directory.
        """
        self._file_path = Path(file_path)
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._load_data()

    def _load_data(self) -> None:
        """
        Loads data from the JSON file into memory.
        If the file does not exist or is empty, it initializes an empty dictionary.
        """
        try:
            if self._file_path.exists():
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        self._data = json.loads(content)
        except (IOError, json.JSONDecodeError):
            self._data = {}

    async def _save_data(self) -> None:
        """
        Saves the current in-memory data to the JSON file.
        This operation is protected by a lock to prevent race conditions.
        """
        async with self._lock:
            try:
                with open(self._file_path, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=4)
            except IOError:
                # In a real application, you might want to log this error.
                pass

    async def get(self, key: str) -> Any:
        """
        Retrieves a value from the storage.

        :param key: The key of the value to retrieve.
        :return: The value associated with the key, or None if not found.
        """
        return self._data.get(key)

    async def set(self, key: str, value: Any) -> None:
        """
        Saves a value to the storage and persists it to the file.

        :param key: The key to associate with the value.
        :param value: The value to save.
        """
        self._data[key] = value
        await self._save_data()

    async def delete(self, key: str) -> None:
        """
        Deletes a value from the storage and persists the change.

        :param key: The key of the value to delete.
        """
        if key in self._data:
            del self._data[key]
            await self._save_data()

    async def has(self, key: str) -> bool:
        """
        Checks if a key exists in the storage.

        :param key: The key to check.
        :return: True if the key exists, False otherwise.
        """
        return key in self._data

    async def append_list(self, key: str, item: Any) -> None:
        """
        Appends an item to a list in the storage.
        If the list does not exist, it will be created.
        The change is persisted to the file.

        :param key: The key of the list.
        :param item: The item to append.
        """
        current_list = self._data.get(key, [])
        if not isinstance(current_list, list):
            # If the existing value is not a list, we start a new list.
            # Depending on requirements, raising an error could be an alternative.
            current_list = []
        current_list.append(item)
        self._data[key] = current_list
        await self._save_data()

    async def get_list(self, key: str) -> List[Any]:
        """
        Retrieves a list from the storage.

        :param key: The key of the list to retrieve.
        :return: The list associated with the key, or an empty list if not found.
        """
        value = self._data.get(key, [])
        if isinstance(value, list):
            return value
        return []
