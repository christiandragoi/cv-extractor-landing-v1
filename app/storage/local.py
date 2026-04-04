import aiofiles
from pathlib import Path
from typing import Union, BinaryIO
from app.storage.base import BaseStorage


class LocalStorage(BaseStorage):
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        full = (self.root / path).resolve()
        try:
            full.relative_to(self.root.resolve())
        except ValueError:
            raise ValueError("Invalid path - directory traversal detected")
        return full

    async def save(self, path: str, content: Union[bytes, BinaryIO]) -> str:
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(content)
        else:
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(content.read())
        return str(full_path)

    async def read(self, path: str) -> bytes:
        full_path = self._full_path(path)
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        full_path = self._full_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()
