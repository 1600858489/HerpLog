from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class StoredFileMetadata:
    """Describe a stored file without coupling it to a business entity."""

    storage_key: str
    mime_type: str
    size: int


class FileStorage(ABC):
    """Define the async file storage contract for local and object storage adapters."""

    @abstractmethod
    async def save(self, file: BinaryIO, storage_key: str) -> StoredFileMetadata:
        """Persist a file under a caller-provided storage key."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """Delete a stored file by key."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Return whether a storage key exists."""
        raise NotImplementedError

    @abstractmethod
    async def get_url(self, storage_key: str) -> str:
        """Return a client-accessible URL for a stored file."""
        raise NotImplementedError
