import json
from .base import BaseStorage


class JSON(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data):
        return json.dumps(data, indent=4)

    def _deserialize(self, text):
        return json.loads(text)
