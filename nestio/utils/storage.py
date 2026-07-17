import atexit
import asyncio
import aiofiles

import os

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
STORAGE_MANAGERS = set()


def sync_flush_all():
    for manager in STORAGE_MANAGERS:
        try:
            manager.sync_flush()

        except Exception as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, chain=True
            )
        
async def flush_all():
    await asyncio.gather(
        *[
            manager.flush(force=True)
            for manager in STORAGE_MANAGERS
        ]
    )

atexit.register(sync_flush_all)


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

        STORAGE_MANAGERS.add(self)

        self.__lock_m = LockManager()


    @property
    async def _lock(self):
        return await self.__lock_m.get(f"RTS:{str(self.path)}")

    @property
    def file(self) -> FileState | None:
        return FILE_STORAGES.get(str(self.path))
        

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


    def sync_flush(self):
        if not self.file or not self.file.loaded:
            return
            
        data = deepcopy(self.file.data)
        content = self.serializer(data)

        try:
            self._atomic_save(content)

        except Exception as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, chain=True
            )
        
    async def flush(self, force: bool = False):
        async with await self._lock:
            await self.__ensure_loaded()

            if not self.file.dirty and not force:
                return

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
        if not self.file:
            FILE_STORAGES[str(self.path)] = FileState(
                data={},
                dirty=False,
                loaded=False,
                last_modified=datetime.utcnow(),
                flush_task=asyncio.create_task(self.__flush_loop())
            )
            
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
            if not self.file or not self.file.loaded:
                await self.__ensure_loaded()

            return deepcopy(self.file.data)

    async def set_data(self, data):
        async with await self._lock:
            if not self.file:
                await self.__ensure_loaded()
                
            self.file.data = deepcopy(data)

            self.file.last_modified = datetime.utcnow()
            self.file.dirty = True

            if not self.file.loaded:
                self.file.loaded = True