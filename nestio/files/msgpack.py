try:
    import msgpack
except ImportError:
    raise ImportError("msgpack is not installed. Please install it with `pip install msgpack`")

import tempfile
import os
import aiofiles
from .base import BaseStorage


class MSGPACK(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data) -> bytes:
        return msgpack.packb(data, use_bin_type=True)

    def _deserialize(self, data: bytes) -> dict:
        return msgpack.unpackb(data, raw=False)

    async def _load(self):
        try:
            async with aiofiles.open(self.path, "rb") as f:
                return self._deserialize(await f.read())
        except FileNotFoundError:
            return {}

    async def _save(self, data):
        content = self._serialize(data)

        with tempfile.NamedTemporaryFile(
            "wb",
            dir=self.path.parent,
            delete=False,
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = tmp.name

        os.replace(temp_path, self.path)
