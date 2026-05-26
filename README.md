# nestio

**Async-first storage for Python — file formats and SQL, unified under one simple interface.**

nestio gives you dot-path access to nested file storage (JSON, TOML, YAML, TOON) and a chainable query builder for SQLite — all async, all atomic, no boilerplate.

---

## Installation

```bash
pip install nestio
```

---

## What's inside

### File storage — `nestio.files`

| Format | Class  | File ext | Best for |
|--------|--------|----------|----------|
| JSON   | `JSON` | `.json`  | General purpose, APIs, configs |
| TOML   | `TOML` | `.toml`  | Configuration files |
| YAML   | `YAML` | `.yaml`  | Human-friendly configs |
| TOON   | `TOON` | `.toon`  | LLM input — compact, token-efficient |

### SQL storage — `nestio.sql`

| Class   | Description |
|---------|-------------|
| `SQL`   | SQLite connection with async `execute()` |
| `Query` | Chainable query builder |

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

    host = await cfg.get("server.host")  # "localhost"

    await cfg.update("server", {"port": 9090, "debug": True})
    await cfg.delete("server.host")

asyncio.run(main())
```

### YAML

```python
import asyncio
from nestio.files import YAML

async def main():
    cfg = YAML("data/config.yaml")

    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)
    await cfg.set("tags", ["web", "api"])

    host = await cfg.get("server.host")  # "localhost"

    await cfg.append("tags", "async")
    await cfg.update("server", {"timeout": 30})
    await cfg.delete("server.port")

asyncio.run(main())
```

### TOON

[TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon) is a compact, human-readable format designed for LLM input. It uses YAML-style indentation for nested objects and CSV-style rows for uniform arrays — achieving up to 40% fewer tokens than JSON while maintaining full round-trip fidelity.

```python
import asyncio
from nestio.files import TOON

async def main():
    store = TOON("data/context.toon")

    await store.set("context.task", "Our favorite hikes")
    await store.set("context.location", "Boulder")
    await store.set("friends", ["ana", "luis", "sam"])

    task = await store.get("context.task")  # "Our favorite hikes"

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

### SQL

```python
import asyncio
from nestio.sql import SQL, Query

async def main():
    db = SQL("data/app.db")

    # Simple select
    rows = await db.execute(Query("users"))

    # With filters, ordering, and a limit
    rows = await db.execute(
        Query("users")
            .select("name", "age")
            .where("age", ">", 25)
            .order_by("age", "DESC")
            .limit(10)
    )

    for row in rows:
        print(row)

asyncio.run(main())
```

---

## File storage API

All methods are `async` and must be awaited. `JSON`, `TOML`, `YAML`, and `TOON` all share the same interface.

You can import from the top level or directly from the submodule — both work:

```python
from nestio import JSON          # top-level shortcut
from nestio.files import JSON    # explicit submodule
```

---

### `get(path, default=None)`

Returns the value at the given dot-path, or `default` if it doesn't exist.

```python
value = await db.get("server.host", default="localhost")
```

### `set(path, value)`

Sets the value at the given dot-path. Creates intermediate dicts as needed.

```python
await db.set("server.port", 8080)
```

### `delete(path)`

Removes the key at the given dot-path. Does nothing if the key doesn't exist.

```python
await db.delete("server.port")
```

### `append(path, value)`

Appends a value to a list at the given dot-path. Creates the list if it doesn't exist yet.

```python
await db.append("logs", {"level": "info", "msg": "started"})
```

### `update(path, new_data)`

Deep-merges a dict into the value at the given dot-path. Nested keys are merged recursively — existing keys not in `new_data` are preserved.

```python
await db.update("config", {"retries": 3, "timeout": 30})
```

---

## SQL API

### `SQL(path)`

Opens (or creates) a SQLite database at the given path.

```python
from nestio.sql import SQL
db = SQL("data/app.db")
```

### `await db.execute(query)`

Executes a `Query` and returns all matching rows as a list of tuples.

```python
rows = await db.execute(Query("users"))
```

### `Query(table)`

Builds a SELECT query for the given table. All methods are chainable.

```python
Query("orders")
    .select("id", "total")
    .where("status", "=", "shipped")
    .order_by("total", "DESC")
    .limit(5)
```

| Method | Description |
|--------|-------------|
| `.select(*columns)` | Columns to return (default: `*`) |
| `.where(column, operator, value)` | Add a filter condition — multiple calls are ANDed |
| `.order_by(column, direction)` | Sort results (`"ASC"` or `"DESC"`) |
| `.limit(n)` | Cap the number of returned rows |

---

## How it works

- **Dot-path access** — keys like `"a.b.c"` resolve through nested dicts automatically.
- **Atomic writes** — every file save writes to a temp file first, then uses `os.replace()` to swap it in. Your file is never left in a half-written state.
- **Per-key locking** — concurrent writes to the same path are serialized with `asyncio.Lock`, while independent paths can write in parallel. Locks are cleaned up automatically after a TTL.
- **SQL query builder** — `Query` compiles to parameterized SQL, so values are always safely escaped.

---

## Requirements

- Python 3.9+
- [`aiofiles`](https://github.com/Tinche/aiofiles)
- [`pyyaml`](https://pyyaml.org/) *(for YAML support)*
- [`tomli`](https://github.com/hukkin/tomli) *(Python < 3.11 only, for TOML support)*
- [`tomli-w`](https://github.com/hukkin/tomli-w) *(for TOML support)*
- [`toons`](https://toons.readthedocs.io/en/stable/) *(for TOON support)*
- `sqlite3` *(for SQL support — built into Python, no install needed)*

---

## License

MIT © MrBaconHat
