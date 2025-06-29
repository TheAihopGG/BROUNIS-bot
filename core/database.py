from aiosqlite import connect as db_connect

from core.logger import logger
from core.config import DATABASE_FILENAME


async def create_tables() -> None:
    async with db_connect(DATABASE_FILENAME) as conn:
        await conn.executescript(open("./sql/create_tables.sql").read())
        await conn.commit()
    logger.info("Database tables created")
