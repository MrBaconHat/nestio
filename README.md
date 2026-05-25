# nestio

**Async-first nested JSON storage with dot-path access and atomic writes.**

nestio lets you read and write deeply nested JSON files using simple dot-path keys — no manual file handling, no race conditions, no boilerplate.

---

## Installation

```bash
pip install nestio
```

---

## Quickstart

```python
import asyncio
from nestio import Json

async def main():
    db = Json("data/config.json")

    # Write nested values with dot-paths
    await db.set("user.name", "Alice")
    await db.set("user.settings.theme", "dark")
    await db.set("user.scores", [])

    # Read them back
    name = await db.get("user.name")           # "Alice"
    theme = await db.get("user.settings.theme") # "dark"

    # Append to a list
    await db.append("user.scores", 42)
    await db.append("user.scores", 99)

    # Deep-merge a dict
    await db.update("user.settings", {"language": "en", "theme": "light"})

    # Delete a key
    await db.delete("user.settings.theme")

    # Safe fallback if key doesn't exist
    missing = await db.get("user.age", default=0)  # 0

asyncio.run(main())
```

The resulting `data/config.json` would look like:

```json
{
    "user": {
        "name": "Alice",
        "settings": {
            "language": "en"
        },
        "scores": [42, 99]
    }
}
```

---

## API

All methods are `async` and must be awaited.

### `Json(path)`

Creates a storage instance pointing to a JSON file. The file and any parent directories are created automatically on first write.

```python
db = Json("path/to/file.json")
```

---

### `get(path, default=None)`

Returns the value at the given dot-path, or `default` if it doesn't exist.

```python
value = await db.get("server.host", default="localhost")
```

---

### `set(path, value)`

Sets the value at the given dot-path. Creates intermediate dicts as needed.

```python
await db.set("server.port", 8080)
```

---

### `delete(path)`

Removes the key at the given dot-path. Does nothing if the key doesn't exist.

```python
await db.delete("server.port")
```

---

### `append(path, value)`

Appends a value to a list at the given dot-path. Creates the list if it doesn't exist yet.

```python
await db.append("logs", {"level": "info", "msg": "started"})
```

---

### `update(path, new_data)`

Deep-merges a dict into the value at the given dot-path. Nested keys are merged recursively — existing keys not in `new_data` are preserved.

```python
await db.update("config", {"retries": 3, "timeout": 30})
```

---

## How it works

- **Dot-path access** — keys like `"a.b.c"` resolve through nested dicts automatically.
- **Atomic writes** — every save writes to a temp file first, then uses `os.replace()` to swap it in. Your file is never left in a half-written state.
- **Per-key locking** — concurrent writes to the same path are serialized with `asyncio.Lock`, while independent paths can write in parallel. Locks are cleaned up automatically after a TTL.

---

## Requirements

- Python 3.9+
- [`aiofiles`](https://github.com/Tinche/aiofiles)

---

## License

MIT © MrBaconHat
