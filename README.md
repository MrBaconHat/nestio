# nestio

**Async-first nested storage with dot-path access and atomic writes.**

nestio lets you read and write deeply nested data files using simple dot-path keys — no manual file handling, no race conditions, no boilerplate. Supports multiple file formats, with more on the way.

---

## Installation

```bash
pip install nestio
```

---

## Supported Formats

| Format | Class  | File ext | Best for |
|--------|--------|----------|----------|
| JSON   | `JSON` | `.json`  | General purpose, APIs, configs |
| TOML   | `TOML` | `.toml`  | Configuration files |
| YAML   | `YAML` | `.yaml`  | Human-friendly configs |
| TOON   | `TOON` | `.toon`  | LLM input — compact, token-efficient |

---

## Quickstart

### JSON

```python
import asyncio
from nestio import JSON

async def main():
    db = JSON("data/config.json")

    await db.set("user.name", "Alice")
    await db.set("user.settings.theme", "dark")
    await db.set("user.scores", [])

    name = await db.get("user.name")            # "Alice"
    theme = await db.get("user.settings.theme") # "dark"

    await db.append("user.scores", 42)
    await db.update("user.settings", {"language": "en"})
    await db.delete("user.settings.theme")

asyncio.run(main())
```

### TOML

```python
import asyncio
from nestio import TOML

async def main():
    cfg = TOML("data/config.toml")

    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)

    host = await cfg.get("server.host") # "localhost"

    await cfg.update("server", {"port": 9090, "debug": True})
    await cfg.delete("server.host")

asyncio.run(main())
```

### YAML

```python
import asyncio
from nestio import YAML

async def main():
    cfg = YAML("data/config.yaml")

    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)
    await cfg.set("tags", ["web", "api"])

    host = await cfg.get("server.host") # "localhost"

    await cfg.append("tags", "async")
    await cfg.update("server", {"timeout": 30})
    await cfg.delete("server.port")

asyncio.run(main())
```

### TOON

[TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon) is a compact, human-readable format designed for LLM input. It uses YAML-style indentation for nested objects and CSV-style rows for uniform arrays — achieving up to 40% fewer tokens than JSON while maintaining full round-trip fidelity.

```python
import asyncio
from nestio import TOON

async def main():
    store = TOON("data/context.toon")

    await store.set("context.task", "Our favorite hikes")
    await store.set("context.location", "Boulder")
    await store.set("friends", ["ana", "luis", "sam"])

    task = await store.get("context.task") # "Our favorite hikes"

    await store.append("logs", "started")
    await store.update("context", {"season": "spring_2025"})
    await store.delete("context.location")

asyncio.run(main())
```

A `.toon` file produced by nestio looks like this:

```
context:
  task: Our favorite hikes
  season: spring_2025
friends[3]: ana,luis,sam
hikes[3]{id,name,distanceKm,wasSunny}:
  1,Blue Lake Trail,7.5,true
  2,Ridge Overlook,9.2,false
  3,Wildflower Loop,5.1,true
```

---

## API

All methods are `async` and must be awaited. `JSON`, `TOML`, `YAML`, and `TOON` all share the same interface.

### `JSON(path)` / `TOML(path)` / `YAML(path)` / `TOON(path)`

Creates a storage instance pointing to a file. The file and any parent directories are created automatically on first write.

```python
db    = JSON("path/to/file.json")
cfg   = TOML("path/to/file.toml")
cfg   = YAML("path/to/file.yaml")
store = TOON("path/to/file.toon")
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
- [`pyyaml`](https://pyyaml.org/) *(for YAML support)*
- [`tomli`](https://github.com/hukkin/tomli) *(Python < 3.11 only, for TOML support)*
- [`tomli-w`](https://github.com/hukkin/tomli-w) *(for TOML support)*
- [`toons`](https://toons.readthedocs.io/en/stable/) *(for TOON support)*

---

## License

MIT © MrBaconHat
