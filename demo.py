import asyncio
from nestio.files import JSON, TOML, YAML, TOON


async def main():
    print("nestio demo\n" + "-" * 30)

    # JSON
    db = JSON("demo_data/demo.json")
    await db.set("user.name", "Alice")
    await db.set("user.age", 30)
    await db.set("user.tags", ["admin", "user"])
    await db.append("user.tags", "developer")
    await db.update("user", {"location": "Boulder"})
    print("JSON  ->", await db.get("user"))

    # TOML
    cfg = TOML("demo_data/demo.toml")
    await cfg.set("server.host", "localhost")
    await cfg.set("server.port", 8080)
    await cfg.update("server", {"debug": True})
    print("TOML  ->", await cfg.get("server"))

    # YAML
    yml = YAML("demo_data/demo.yaml")
    await yml.set("app.name", "nestio")
    await yml.set("app.version", "0.1.1")
    print("YAML  ->", await yml.get("app"))

    # TOON
    toon = TOON("demo_data/demo.toon")
    await toon.set("context.task", "nestio demo")
    await toon.set("friends", ["ana", "luis", "sam"])
    print("TOON  ->", await toon.get("context"))

    print("-" * 30)
    print("All formats working!")


asyncio.run(main())
