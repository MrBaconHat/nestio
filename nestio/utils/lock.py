import asyncio
import time

from cachetools import TTLCache


class LockManager:
    def __init__(self, ttl=60):
        self._locks = TTLCache(maxsize=1000, ttl=ttl)

    async def get(self, key: str) -> asyncio.Lock:
        return self._locks.setdefault(key, asyncio.Lock())