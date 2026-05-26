from nestio.sql import Query, SQL # uses my custom sql, it uses sqllite
import asyncio

async def main():
    sql = SQL("tests/test.db")

    query = Query("User")
    query. \
        select("id", "name"). \
        where("id", "=", 1). \
        limit(1). \
        order_by("id", "DESC")

    print(await sql.execute(query))

asyncio.run(main())