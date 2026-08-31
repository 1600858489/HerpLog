from abc import ABC, abstractmethod
from typing import Any


class CacheClient(ABC):
    """Define the async cache contract implemented by Redis adapters."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return a cached value or None when the key is absent."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value, optionally with a time-to-live in seconds."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete one cache key."""
        raise NotImplementedError

    @abstractmethod
    async def expire(self, key: str, ttl_seconds: int) -> None:
        """Set the expiration time for one cache key."""
        raise NotImplementedError
