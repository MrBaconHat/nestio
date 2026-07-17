import os
import asyncio
import aiofiles
import tempfile
import traceback

from datetime import datetime, timedelta

from copy import deepcopy

from .lock import LockManager

from pathlib import Path

from typing import Callable
from dataclasses import dataclass


@dataclass
class FileState:
    data: dict
    dirty: bool
    loaded: bool
    last_modified: datetime
    flush_task: asyncio.Task | None = None


FILE_STORAGES: dict[str, FileState] = {}


class StorageManager:
    def __init__(
        self, 
        path: Path, 
        serializer: Callable, 
        deserializer: Callable
    ):
        self.path = path
        self.serializer = serializer
        self.deserializer = deserializer

        if str(self.path) not in FILE_STORAGES:
            FILE_STORAGES[str(self.path)] = FileState(
                data={},
                dirty=False,
                loaded=False,
                last_modified=datetime.utcnow(),
                flush_task=asyncio.create_task(self.__flush_loop())
            )

        self.__lock_m = LockManager()


    @property
    async def _lock(self):
        return await self.__lock_m.get(f"RTS:{str(self.path)}")

    @property
    def file(self) -> FileState:
        return FILE_STORAGES[str(self.path)]
        

    def _atomic_save(self, content: str):
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


    async def flush(self, force: bool = False):
        if not self.file.dirty and not force:
            return
            
        async with await self._lock:
            content = self.serializer(self.file.data)

            try:
                await asyncio.to_thread(
                    self._atomic_save,
                    content
                )

            # if the disk is full
            except Exception as e:
                traceback.print_exception(
                    type(e), e, e.__traceback__, chain=True
                )
                return
                
            
            self.file.dirty = False

    async def __flush_loop(self):
        while True:
            if datetime.utcnow() - self.file.last_modified > timedelta(seconds=3) and self.file.dirty:
                await self.flush()

            await asyncio.sleep(0.3)


    async def __ensure_loaded(self):
        if self.file.loaded:
            return

        try:
            async with aiofiles.open(self.path, "r") as f:
                self.file.data = self.deserializer(await f.read())
            
                self.file.loaded = True
                self.file.last_modified = datetime.utcnow()

        except FileNotFoundError:
            self.file.data = {}
            self.file.loaded = True
            self.file.dirty = True


    async def get_data(self):
        async with await self._lock:
            if not self.file.loaded:
                await self.__ensure_loaded()

            return deepcopy(self.file.data)

    async def set_data(self, data):
        async with await self._lock:
            self.file.data = deepcopy(data)

            self.file.last_modified = datetime.utcnow()
            self.file.dirty = True

            if not self.file.loaded:
                self.file.loaded = True