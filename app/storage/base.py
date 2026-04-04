from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Union


class BaseStorage(ABC):
    @abstractmethod
    async def save(self, path: str, content: Union[bytes, BinaryIO]) -> str:
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass
