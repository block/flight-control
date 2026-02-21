import os
from abc import ABC, abstractmethod
from pathlib import Path

from orchestrator.config import settings


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, path: str, data: bytes) -> None: ...

    @abstractmethod
    async def read(self, path: str) -> bytes: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    async def save(self, path: str, data: bytes) -> None:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

    async def read(self, path: str) -> bytes:
        full_path = self.base_path / path
        return full_path.read_bytes()

    async def delete(self, path: str) -> None:
        full_path = self.base_path / path
        if full_path.exists():
            full_path.unlink()


def get_storage() -> StorageBackend:
    return LocalStorageBackend(settings.artifact_storage_path)
