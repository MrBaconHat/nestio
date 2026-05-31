import asyncio
from nestio.files import JSON, TOML, YAML, TOON, MSGPACK


async def main():
    print("nestio demo\n" + "-" * 30)

    # JSON
    db = JSON("examples/demo.json")
    await db.set("user.name", "Alice")
    await db.set("user.age", 30)
    await db.set("user.tags", ["admin", "user"])
    await db.append("user.tags", "developer")
    await db.update("user", {"location": "Boulder"})
    print("JSON    ->", await db.get("user"))

    # TOML
    cfg = TOML("examples/demo.toml")
    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)
    await cfg.update("server", {"debug": True})
    print("TOML    ->", await cfg.get("server"))

    # YAML
    yml = YAML("examples/demo.yaml")
    await yml.set("app.name", "nestio")
    await yml.set("app.version", "0.2.0")
    print("YAML    ->", await yml.get("app"))

    # TOON
    toon = TOON("examples/demo.toon")
    await toon.set("context.task", "nestio demo")
    await toon.set("friends", ["ana", "luis", "sam"])
    print("TOON    ->", await toon.get("context"))

    # MessagePack
    cache = MSGPACK("examples/demo.msgpack")
    await cache.set("session.user_id", 1234)
    await cache.set("session.permissions", ["read", "write"])
    await cache.append("session.permissions", "admin")
    await cache.update("session", {"last_active": "2023-10-01"})
    print("MSGPACK ->", await cache.get("session"))
    print("MSGPACK: LAST ACTIVE:", await cache.get("session.last_active"))

    print("-" * 30)
    print("One interface, multiple file formats!")


    # Testing the context manager
    async with JSON("examples/demo.json") as db:
        await db.set("user.name", "Alice")
        await db.set("user.age", 30)
        await db.set("user.tags", ["admin", "user"])
        await db.extend("user.tags", ["developer", "user", "djfjrjdjfj"])
        await db.update("user", {"location": "Boulder"})

        print("JSON    ->", await db.get("user"))


asyncio.run(main())
