from sqlite3 import connect as db_connect

from core.logger import logger
from core.config import DATABASE_FILENAME


def create_tables() -> None:
    with db_connect(DATABASE_FILENAME) as conn:
        cur = conn.cursor()
        cur.executescript(open("./sql/create_tables.sql").read())

        conn.commit()
        cur.close()

    logger.info("Database tables created")
