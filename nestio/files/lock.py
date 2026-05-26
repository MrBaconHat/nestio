import asyncio
import time


class LockManager:
    def __init__(self, ttl=300):
        self._locks = {}
        self._last_used = {}
        self._ttl = ttl
        self._global = asyncio.Lock()

    async def get(self, key: str) -> asyncio.Lock:
        async with self._global:
            now = time.monotonic()

            # cleanup old locks
            for k in list(self._locks.keys()):
                if now - self._last_used.get(k, 0) > self._ttl:
                    del self._locks[k]
                    del self._last_used[k]

            if key not in self._locks:
                self._locks[key] = asyncio.Lock()

            self._last_used[key] = now
            return self._locks[key]