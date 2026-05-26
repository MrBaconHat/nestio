try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w
from ..base import BaseStorage


class TOML(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data):
        return tomli_w.dumps(data)

    def _deserialize(self, text):
        return tomllib.loads(text) if text.strip() else {}
