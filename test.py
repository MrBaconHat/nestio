from nestio import Json
import asyncio 

async def main():
    file = Json("test.json")
    await file.set("test.hi", {"yay": "hello"})
    print(await file.get("test.hi"))

asyncio.run(main())