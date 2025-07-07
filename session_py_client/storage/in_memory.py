from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class Storage(Protocol):
    """Interface for storage implementations."""

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value by key."""

    def set(self, key: str, value: str) -> None:
        """Store a value by key."""

    def delete(self, key: str) -> None:
        """Remove a value by key."""

    def has(self, key: str) -> bool:
        """Check if a key exists."""


class InMemoryStorage:
    """Simple in-memory storage using a dictionary."""

    def __init__(self) -> None:
        self._storage: dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        """Return the stored value for key if present."""

        return self._storage.get(key)

    def set(self, key: str, value: str) -> None:
        """Set key to given value."""

        self._storage[key] = value

    def delete(self, key: str) -> None:
        """Delete key from storage if it exists."""

        self._storage.pop(key, None)

    def has(self, key: str) -> bool:
        """Return ``True`` if key exists in storage."""

        return key in self._storage

