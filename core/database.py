from aiosqlite import connect as db_connect

from core.config import DATABASE_FILENAME


async def create_tables() -> None:
    async with db_connect(DATABASE_FILENAME) as conn:
        async with conn.cursor() as cur:
            await cur.execute(open("./sql/create_tables.sql").read())

        await conn.commit()
