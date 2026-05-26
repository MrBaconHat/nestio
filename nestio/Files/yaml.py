import yaml
from ..base import BaseStorage


class YAML(BaseStorage):
    def __init__(self, path: str):
        super().__init__(path)

    def _serialize(self, data):
        return yaml.dump(data, sort_keys=False)

    def _deserialize(self, text):
        return yaml.safe_load(text) or {}
