try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w
from .base import BaseStorage


class Toml(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data):
        return tomli_w.dumps(data)

    def _deserialize(self, text):
        return tomllib.loads(text)

    async def _load(self):
        import aiofiles
        try:
            async with aiofiles.open(self.path, "rb") as f:
                content = await f.read()
                return tomllib.loads(content.decode("utf-8"))
        except FileNotFoundError:
            return {}

    async def _save(self, data):
        import tempfile
        import os

        content = tomli_w.dumps(data)

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
