# nestio

**Async local storage for Python. One interface, multiple file formats.**

Stop writing the same boilerplate every time you need local storage.

nestio provides a consistent async API for JSON, TOML, YAML, TOON, and MessagePack — plus a typed `.env` loader — with:

- **Dot-path access** — `"user.settings.theme"`
- **Atomic writes** — never leave files half-written
- **Automatic locking** — safe concurrent writes out of the box
- **One API across every supported format**

Supported formats: **JSON • TOML • YAML • TOON • MessagePack**

> Same API. Same code. Different format.

---

## Why nestio?

**Without nestio:**

```python
import json

with open("config.json", "r") as f:
    data = json.load(f)

data["user"]["settings"]["theme"] = "dark"

with open("config.json", "w") as f:
    json.dump(data, f, indent=4)
```

**With nestio:**

```python
from nestio.files import JSON

db = JSON("config.json")
await db.set("user.settings.theme", "dark")
```

Same logic. Less boilerplate.

---

## Installation

```bash
pip install nestio
```

![PyPI Version](https://img.shields.io/pypi/v/nestio?labelColor=1b1b1f&color=4ade80)
![Python 3.9+](https://img.shields.io/pypi/pyversions/nestio?labelColor=1b1b1f&color=4ade80)
![License MIT](https://img.shields.io/pypi/l/nestio?labelColor=1b1b1f&color=4ade80)

---

## Features

| Feature | Supported |
|---------|-----------|
| Async API | ✅ |
| Dot-path access | ✅ |
| Atomic writes | ✅ |
| Automatic locking | ✅ |
| JSON | ✅ |
| TOML | ✅ |
| YAML | ✅ |
| MessagePack | ✅ |
| TOON | ✅ |
| `.env` loader | ✅ |

---

## Supported formats

| Format      | Class      | File ext   | Best for |
|-------------|------------|------------|----------|
| JSON        | `JSON`     | `.json`    | General purpose, APIs, configs |
| TOML        | `TOML`     | `.toml`    | Configuration files |
| YAML        | `YAML`     | `.yaml`    | Human-friendly configs |
| TOON        | `TOON`     | `.toon`    | LLM input — compact, token-efficient |
| MessagePack | `MSGPACK`  | `.msgpack` | Binary, fast, compact serialization |

---

## Quickstart

### File storage

```python
import asyncio
from nestio.files import JSON  # swap for TOML, YAML, TOON, or MSGPACK — API is identical

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
from nestio.files import TOML

cfg = TOML("data/config.toml")
await cfg.set("server.host", "localhost")
await cfg.set("server.port", 8080)
await cfg.update("server", {"debug": True})
```

### YAML

```python
from nestio.files import YAML

cfg = YAML("data/config.yaml")
await cfg.set("server.host", "localhost")
await cfg.set("tags", ["web", "api"])
await cfg.append("tags", "async")
```

### MessagePack

```python
from nestio.files import MSGPACK

cache = MSGPACK("data/cache.msgpack")
await cache.set("session.user_id", 1234)
await cache.set("session.permissions", ["read", "write"])
await cache.append("session.permissions", "admin")
```

### TOON

```python
from nestio.files import TOON

store = TOON("data/context.toon")
await store.set("context.task", "Our favorite hikes")
await store.set("friends", ["ana", "luis", "sam"])
await store.update("context", {"season": "spring_2025"})
```

### Environment variables

`nestio.env` gives you a typed wrapper around your `.env` file — no more scattered `os.getenv()` calls.

```python
from nestio.env import Env

env = Env(".env")  # raises FileNotFoundError if missing

# Basic access
debug = env.get("DEBUG", default="false")
host  = env["HOST"]          # same as os.getenv("HOST")

# Typed getters
port    = env.get_int("PORT")        # int
ratio   = env.get_float("RATIO")     # float
verbose = env.get_bool("VERBOSE")    # True for "true", "1", "yes", "y", "t"
tags    = env.get_list("TAGS")       # splits on "," by default
tags    = env.get_list("TAGS", sep=" ")  # custom separator

# Required variables — raises KeyError if missing or empty
secret  = env.require("SECRET_KEY")
```

Given a `.env` file like:

```
HOST=localhost
PORT=8080
DEBUG=true
TAGS=web,api,async
SECRET_KEY=supersecret
```

---

## File storage API

All five methods work the same across every format. All are `async` and must be awaited.

Import from the submodule or the top level — both work:

```python
from nestio.files import JSON   # explicit
from nestio import JSON         # shortcut
```

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

## Format-specific notes

### TOON

[TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon) is a compact, human-readable format designed for LLM input. It combines YAML-style indentation for nested objects with CSV-style rows for uniform arrays — achieving up to 40% fewer tokens than JSON while maintaining full round-trip fidelity.

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

MessagePack is a binary format — files are not human-readable, but they're smaller and faster to parse than any text-based format. Best for local caches and high-frequency storage where you don't need to inspect files manually.

---

## Roadmap

- [x] JSON support
- [x] TOML support
- [x] YAML support
- [x] MessagePack support
- [x] TOON support
- [x] Atomic writes
- [x] Async locking
- [x] `.env` loader
- [ ] Benchmarks
- [ ] Automatic format detection
- [ ] More examples

---

## Why I built nestio

I found myself repeatedly writing the same file handling code in async projects:

- Load a file
- Navigate nested dictionaries
- Modify values
- Save safely
- Handle concurrent writes

nestio was created to remove that boilerplate and provide a consistent interface across multiple storage formats.

---

## Requirements

- Python 3.9+
- [`aiofiles`](https://github.com/Tinche/aiofiles)
- [`pyyaml`](https://pyyaml.org/) *(YAML)*
- [`tomli`](https://github.com/hukkin/tomli) *(TOML, Python < 3.11 only)*
- [`tomli-w`](https://github.com/hukkin/tomli-w) *(TOML)*
- [`toons`](https://toons.readthedocs.io/en/stable/) *(TOON)*
- [`msgpack`](https://msgpack.org/) *(MessagePack)*
- [`python-dotenv`](https://github.com/theskumar/python-dotenv) *(.env loader)*

---

## License

MIT © MrBaconHat
