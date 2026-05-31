from pathlib import Path
import os


class Env:
    # Set the default.env path(its usually in the root of the project)
    def __init__(self, path: str = ".env"):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Env file not found: {self.path}")

        try:
            from dotenv import load_dotenv
        except ImportError:
            raise ImportError("Please install python-dotenv to use this module")

        load_dotenv(self.path)
        

    def __getitem__(self, key):
        return os.getenv(key)

    def require(self, key):
        value = os.getenv(key)
        if not value:
            raise KeyError(f"Missing Environment Variable: {key}")

        return value

    def get(self, key, default=None):
        return os.getenv(key, default)

    def get_int(self, key):
        return int(os.getenv(key))

    def get_float(self, key):
        return float(os.getenv(key))

    def get_bool(self, key):
        return os.getenv(key).lower() in ("true", "1", "t", "y", "yes")

    def get_list(self, key, sep=","):
        value = os.getenv(key)

        if not value:
            return []

        return [v.strip() for v in value.split(sep)]