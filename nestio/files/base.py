import aiofiles
import tempfile
import os
from pathlib import Path

from .lock import LockManager


class BaseStorage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._lock_manager = LockManager()

    # Support for context manager
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    # --- format layer ---
    def _serialize(self, data): ...
    def _deserialize(self, text): ...

    # --- IO ---
    async def _load(self):
        try:
            async with aiofiles.open(self.path, "r", encoding="utf-8") as f:
                return self._deserialize(await f.read())
        except FileNotFoundError:
            return {}

    async def _save(self, data):
        content = self._serialize(data)

        with tempfile.NamedTemporaryFile(
            "w",
            dir=self.path.parent,
            delete=False,
            encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = tmp.name

        os.replace(temp_path, self.path)

    # --- helpers ---
    def _resolve_parent(self, data, path, create=False):
        keys = path.split(".")
        current = data

        for k in keys[:-1]:
            if k not in current:
                if create:
                    current[k] = {}
                else:
                    raise KeyError(path)

            if not isinstance(current[k], dict):
                raise TypeError(f"Invalid path: {path}")

            current = current[k]

        return current, keys[-1]
    
    def _deep_merge(self, original, new):
        for k, v in new.items():
            if isinstance(v, dict) and isinstance(original.get(k), dict):
                self._deep_merge(original[k], v)
            else:
                original[k] = v

    
    # ============================ #
    #         Basic CRUD           #
    # ---------------------------- #
    #  - get                       #
    #  - set                       #
    #  - delete                    #
    #  - update                    #
    # ============================ #
    async def get(self, path, default=None):
        data = await self._load()

        try:
            parent, key = self._resolve_parent(data, path)
            return parent.get(key, default)
        except Exception:
            return default

    async def set(self, path, value):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)
            parent[key] = value

            await self._save(data)

    async def delete(self, path):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key in parent:
                del parent[key]
                await self._save(data)

    async def update(self, path, new_data: dict):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = {}

            if not isinstance(parent[key], dict):
                raise TypeError("Target is not a dict")

            self._deep_merge(parent[key], new_data)

            await self._save(data)
            

    # ============================ #
    #       List Management        #
    # ---------------------------- #
    #  - append                    #
    #  - extend                    #
    #  - remove                    #
    #  - pop                       #
    #  - clear                     #
    # ============================ #

    async def append(self, path, value):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].append(value)

            await self._save(data)

    async def extend(self, path, *values):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].extend(values)

            await self._save(data)

    async def remove(self, path, value):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            parent[key].remove(value)

            await self._save(data)

    async def pop(self, path, index=-1):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            value = parent[key].pop(index)

            await self._save(data)

            return value

    async def clear(self, path):
        async with await self._lock_manager.get(path):
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if isinstance(parent[key], dict):
                parent[key].clear()
                await self._save(data)

            elif isinstance(parent[key], list):
                parent[key] = []
                await self._save(data)

            else:
                raise TypeError(f"Target is not a dict or list: {path}")