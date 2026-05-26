# nestio

**One interface, multiple file formats.**

nestio gives you a single, consistent API for reading and writing nested data — regardless of file format. Switch between JSON, TOML, YAML, TOON, or MessagePack without changing any of your logic. Just swap the class.

---

## Installation

```bash
pip install nestio
```

---

## Supported formats

| Format      | Class      | File ext  | Best for |
|-------------|------------|-----------|----------|
| JSON        | `JSON`     | `.json`   | General purpose, APIs, configs |
| TOML        | `TOML`     | `.toml`   | Configuration files |
| YAML        | `YAML`     | `.yaml`   | Human-friendly configs |
| TOON        | `TOON`     | `.toon`   | LLM input — compact, token-efficient |
| MessagePack | `MSGPACK`  | `.msgpack`| Binary, fast, compact serialization |

---

## The idea

Every class shares the exact same five methods. Your logic never changes — only the format does:

```python
# Works identically for JSON, TOML, YAML, TOON, or MSGPACK
await storage.set("user.settings.theme", "dark")
await storage.get("user.settings.theme")
await storage.append("user.scores", 42)
await storage.update("user.settings", {"language": "en"})
await storage.delete("user.settings.theme")
```

---

## Quickstart

### JSON

```python
import asyncio
from nestio.files import JSON

async def main():
    db = JSON("data/config.json")

    await db.set("user.name", "Alice")
    await db.set("user.settings.theme", "dark")
    await db.set("user.scores", [])

    name  = await db.get("user.name")            # "Alice"
    theme = await db.get("user.settings.theme")  # "dark"

    await db.append("user.scores", 42)
    await db.update("user.settings", {"language": "en"})
    await db.delete("user.settings.theme")

asyncio.run(main())
```

### TOML

```python
import asyncio
from nestio.files import TOML

async def main():
    cfg = TOML("data/config.toml")

    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)
    await cfg.update("server", {"debug": True})

    host = await cfg.get("server.host")  # "localhost"

asyncio.run(main())
```

### YAML

```python
import asyncio
from nestio.files import YAML

async def main():
    cfg = YAML("data/config.yaml")

    await cfg.set("server.host", "localhost")
    await cfg.set("tags", ["web", "api"])
    await cfg.append("tags", "async")

    tags = await cfg.get("tags")  # ["web", "api", "async"]

asyncio.run(main())
```

### TOON

[TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon) is a compact format designed for LLM input — YAML-style nesting, CSV-style rows for uniform arrays, up to 40% fewer tokens than JSON.

```python
import asyncio
from nestio.files import TOON

async def main():
    store = TOON("data/context.toon")

    await store.set("context.task", "Our favorite hikes")
    await store.set("friends", ["ana", "luis", "sam"])
    await store.update("context", {"season": "spring_2025"})

    task = await store.get("context.task")  # "Our favorite hikes"

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

### MessagePack

MessagePack is a binary format — smaller and faster to read/write than text-based formats, great for local caches and high-frequency storage.

```python
import asyncio
from nestio.files import MSGPACK

async def main():
    cache = MSGPACK("data/cache.msgpack")

    await cache.set("session.user_id", 1234)
    await cache.set("session.token", "abc123")
    await cache.set("session.permissions", ["read", "write"])

    user_id = await cache.get("session.user_id")  # 1234

    await cache.append("session.permissions", "admin")
    await cache.delete("session.token")

asyncio.run(main())
```

---

## API

All five methods work the same across every format. All are `async` and must be awaited.

Import from the submodule or top level — both work:

```python
from nestio.files import JSON   # explicit
from nestio import JSON         # shortcut
```

---

### `get(path, default=None)`

Returns the value at the dot-path, or `default` if it doesn't exist.

```python
value = await db.get("server.host", default="localhost")
```

### `set(path, value)`

Sets the value at the dot-path. Creates intermediate dicts as needed.

```python
await db.set("server.port", 8080)
```

### `delete(path)`

Removes the key at the dot-path. Does nothing if the key doesn't exist.

```python
await db.delete("server.port")
```

### `append(path, value)`

Appends a value to a list at the dot-path. Creates the list if it doesn't exist yet.

```python
await db.append("logs", {"level": "info", "msg": "started"})
```

### `update(path, new_data)`

Deep-merges a dict into the value at the dot-path. Existing keys not in `new_data` are preserved.

```python
await db.update("config", {"retries": 3, "timeout": 30})
```

---

## How it works

- **Dot-path access** — keys like `"a.b.c"` resolve through nested dicts automatically.
- **Atomic writes** — every save writes to a temp file first, then uses `os.replace()` to swap it in. Your file is never half-written.
- **Per-key locking** — concurrent writes to the same path are serialized with `asyncio.Lock`, while independent paths write in parallel. Locks clean up automatically after a TTL.

---

## Requirements

- Python 3.9+
- [`aiofiles`](https://github.com/Tinche/aiofiles)
- [`pyyaml`](https://pyyaml.org/) *(YAML)*
- [`tomli`](https://github.com/hukkin/tomli) *(TOML, Python < 3.11 only)*
- [`tomli-w`](https://github.com/hukkin/tomli-w) *(TOML)*
- [`toons`](https://toons.readthedocs.io/en/stable/) *(TOON)*
- [`msgpack`](https://msgpack.org/) *(MessagePack)*

---

## License

MIT © MrBaconHat
