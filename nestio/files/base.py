import aiofiles
import tempfile
import os
from pathlib import Path

from typing import Any
from collections.abc import Iterable
from abc import ABC, abstractmethod

import time
import asyncio
import atexit

from .lock import LockManager

_LOCK_MANAGER = LockManager()


class BaseStorage(ABC):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.__batch = Batch(self)
        
        self._in_batch: bool = False
        self._batch_data: dict[str, Any] | None = None

    # Support for context manager
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    # --- format layer ---
    @abstractmethod
    def _serialize(self, data): ...

    @abstractmethod
    def _deserialize(self, text): ...

    # --- IO ---
    async def _load(self):
        if self._in_batch:
            return self._batch_data
            
        try:
            async with aiofiles.open(self.path, "r", encoding="utf-8") as f:
                return self._deserialize(await f.read())
        except FileNotFoundError:
            return {}

    async def _save(self, data):
        if self._in_batch:
            return
            
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

    @property
    async def _lock(self):
        return await _LOCK_MANAGER.get(str(self.path))
    
    # ============================ #
    #         Basic CRUD           #
    # ---------------------------- #
    #  - get                       #
    #  - set                       #
    #  - delete                    #
    #  - update                    #
    # ============================ #
    async def get(self, path: str | None = None, default: Any = None) -> Any:
        data = await self._load()
        
        if path is None:
            return data

        try:
            parent, key = self._resolve_parent(data, path)
            return parent.get(key, default)
        except (KeyError, TypeError):
            return default

    async def set(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)
            parent[key] = value

            await self._save(data)
            return parent[key]
        
    async def setdefault(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = value
                await self._save(data)
                
            return parent[key]

    # Aliases
    async def set_default(self, path: str, value: Any) -> Any: return await self.setdefault(path, value)
        

    async def delete(self, path: str) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path)
            
            if key not in parent:
                raise KeyError(f"Key not found: {path}")

            if key in parent:
                value = parent[key]
                del parent[key]
                await self._save(data)

                return value

    async def update(self, path: str, new_data: dict[str, Any], strict_keys: bool = False) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                if strict_keys:
                    raise KeyError(f"Key not found: {path}")
                    
                parent[key] = {}

            if not isinstance(parent[key], dict):
                raise TypeError("Target is not a dict")

            self._deep_merge(parent[key], new_data)

            await self._save(data)
            return parent[key]

    async def exists(self, path: str) -> bool:
        sentinel = object()
        return await self.get(path, sentinel) is not sentinel

    async def increment(self, path: str, amount: int = 1) -> int:
        async with await self._lock:
            data = await self._load()
            parent, key = self._resolve_parent(data, path, create=True)

            value = parent.get(key, 0)
            if isinstance(value, (int, float)):
                parent[key] = value + amount
                await self._save(data)
                return parent[key]
                
            else:
                raise TypeError(f"Target is not a number: {path}")

    # ============================ #
    #       List Management        #
    # ---------------------------- #
    #  - append                    #
    #  - extend                    #
    #  - remove                    #
    #  - pop                       #
    #  - clear                     #
    # ============================ #

    async def append(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].append(value)

            await self._save(data)
            return parent[key]

    async def extend(self, path: str, values: Iterable[Any]) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].extend(values)

            await self._save(data)
            return parent[key]

    async def remove(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(f"Key not found: {path}")

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            parent[key].remove(value)

            await self._save(data)
            return parent[key]

    async def pop(self, path: str, index: int = -1) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            value = parent[key].pop(index)

            await self._save(data)
            return value

    async def clear(self, path: str) -> Any:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if isinstance(parent[key], dict):
                old = parent[key].copy()
                parent[key].clear()
                await self._save(data)
                return old

            elif isinstance(parent[key], list):
                old = parent[key].copy()
                parent[key] = []
                await self._save(data)
                return old

            else:
                raise TypeError(f"Target is not a dict or list: {path}")


    # ============================
    # Boolean Managers
    # ============================
    async def toggle(self, path: str) -> bool:
        async with await self._lock:
            data = await self._load()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = False

            bool_value = parent[key]
            if not isinstance(bool_value, bool):
                raise TypeError(f"Target is not a boolean: {path}")

            parent[key] = not bool_value
            await self._save(data)

            return parent[key]

    # ========================
    # Multiples
    # ========================
    async def get_many(self, *paths: str) -> tuple[Any, ...]:
        async with await self._lock:
            data = await self._load()
            result = []

            for path in paths:
                try:
                    parent, key = self._resolve_parent(data, path)
                    result.append(parent.get(key))
                except Exception:
                   result.append(None)

            return tuple(result)


class Cache:
    def __init__(self, storage):
        self.__storage = storage

        self._cache = {}
        self._last_updated = time.monotonic()
        self._dirty: bool = False

        # start flush loop
        self._task = asyncio.create_task(self._flush_loop())

        # register sync exit handler
        atexit.register(self._sync_exit)

    def __getitem__(self, key):
        if key not in self._cache:
            raise KeyError(key)

        return self._cache[key]
        
        
    async def _flush_loop(self):
        try:
            while True:
                await asyncio.sleep(5)

                if self._dirty:
                    await self.__storage._save(self._cache)
                    self._dirty = False

        except asyncio.CancelledError:
            # cleanup when stopping
            pass

    def _sync_exit(self):
        try:
            asyncio.run(self._shutdown())
        except RuntimeError:
        # event loop might already be closed
            pass

    async def _shutdown(self):
        self._dirty = False

        # final flush
        if self._cache:
            await self.__storage._save(self._cache)

        # stop loop task safely
        if hasattr(self, "_task"):
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass



# ==== Experimental ============================================================
class Batch:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    async def __aenter__(self):
        self.lock = await self.storage._lock
        await self.lock.acquire()
        
        self.data = await self.storage._load()

        self.storage._in_batch = True
        self.storage._batch_data = self.data

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            self.storage._in_batch = False

            if exc_type is None:
                await self.storage._save(self.data)

        finally:
            self.storage._batch_data = None
            self.lock.release()