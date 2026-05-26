import toons
from ..base import BaseStorage


class TOON(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data: dict) -> str:
        return toons.dumps(data)

    def _deserialize(self, text: str) -> dict:
        return toons.loads(text)
