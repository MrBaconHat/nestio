import aiofiles
import tempfile

import os
from pathlib import Path

from copy import deepcopy

from typing import Any
from collections.abc import Iterable
from abc import ABC, abstractmethod

import time
import asyncio

from ..utils.lock import LockManager
from ..utils.storage import StorageManager

_LOCK_MANAGER = LockManager()


class BaseStorage(ABC):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._storage = StorageManager(
            path=self.path,
            serializer=self._serialize,
            deserializer=self._deserialize
        )

    # --- format layer ---
    @abstractmethod
    def _serialize(self, data): ...

    @abstractmethod
    def _deserialize(self, text): ...

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
        data = await self._storage.get_data()
        
        if path is None:
            return deepcopy(data)

        try:
            parent, key = self._resolve_parent(data, path)
            return deepcopy(parent.get(key, default))
        except (KeyError, TypeError):
            return default

    async def set(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)
            parent[key] = value

            await self._storage.set_data(data)

            return parent[key]
        
    async def setdefault(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = value
                await self._storage.set_data(data)
                
            return parent[key]

    # Aliases
    async def set_default(self, path: str, value: Any) -> Any: return await self.setdefault(path, value)
        

    async def delete(self, path: str) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path)
            
            if key not in parent:
                raise KeyError(f"Key not found: {path}")

            if key in parent:
                value = parent[key]
                del parent[key]
                
                await self._storage.set_data(data)

                return value

    async def update(self, path: str, new_data: dict[str, Any], strict_keys: bool = False) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                if strict_keys:
                    raise KeyError(f"Key not found: {path}")
                    
                parent[key] = {}

            if not isinstance(parent[key], dict):
                raise TypeError("Target is not a dict")

            self._deep_merge(parent[key], new_data)

            await self._storage.set_data(data)

            return parent[key]

    async def exists(self, path: str) -> bool:
        sentinel = object()
        return await self.get(path, sentinel) is not sentinel

    async def increment(self, path: str, amount: int = 1) -> int:
        async with await self._lock:
            data = await self._storage.get_data()
            parent, key = self._resolve_parent(data, path, create=True)

            value = parent.get(key, 0)
            if isinstance(value, (int, float)):
                parent[key] = value + amount
                await self._storage.set_data(data)
                
                return parent[key]
                
            else:
                raise TypeError(f"Target is not a number: {path}")

    async def decrement(self, path: str, amount: int = 1):
        async with await self._lock:
            data = await self._storage.get_data()
            parent, key = self._resolve_parent(data, path, create=True)

            value = parent.get(key, 0)
            if isinstance(value, (int, float)):
                parent[key] = value - amount
                await self._storage.set_data(data)
                
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
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].append(value)

            await self._storage.set_data(data)

            return parent[key]

    async def extend(self, path: str, values: Iterable[Any]) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = []

            if not isinstance(parent[key], list):
                raise TypeError("Target is not a list")

            parent[key].extend(values)

            await self._storage.set_data(data)

            return parent[key]

    async def remove(self, path: str, value: Any) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(f"Key not found: {path}")

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            parent[key].remove(value)

            await self._storage.set_data(data)

            return parent[key]

    async def pop(self, path: str, index: int = -1) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if not isinstance(parent[key], list):
                raise TypeError(f"Target is not a list: {path}")

            value = parent[key].pop(index)

            await self._storage.set_data(data)

            return value

    async def clear(self, path: str) -> Any:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path)

            if key not in parent:
                raise KeyError(path)

            if isinstance(parent[key], dict) or isinstance(parent[key], list):
                old = parent[key]
                parent[key].clear()

                await self._storage.set_data(data)
                
                return old

            else:
                raise TypeError(f"Target is not a dict or list: {path}")


    # ============================
    # Boolean Managers
    # ============================
    async def toggle(self, path: str) -> bool:
        async with await self._lock:
            data = await self._storage.get_data()

            parent, key = self._resolve_parent(data, path, create=True)

            if key not in parent:
                parent[key] = False

            bool_value = parent[key]
            if not isinstance(bool_value, bool):
                raise TypeError(f"Target is not a boolean: {path}")

            parent[key] = not bool_value
            await self._storage.set_data(data)

            return parent[key]

    # ========================
    # Multiples
    # ========================
    async def get_many(self, *paths: str) -> tuple[Any, ...]:
        async with await self._lock:
            data = await self._storage.get_data()
            result = []

            for path in paths:
                try:
                    parent, key = self._resolve_parent(data, path)
                    result.append(parent.get(key))
                except Exception:
                   result.append(None)

            return tuple(result)

    # ========================
    # Flush
    # ========================
    async def flush(self):
        async with await self._lock:
            await self._storage.flush(force=True)