from dotenv import load_dotenv
from pathlib import Path
from os import getenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "core/.env"

assert load_dotenv(ENV_PATH), f"env config is not exists"

BOT_TOKEN = getenv("BOT_TOKEN")
DATABASE_FILENAME = BASE_DIR / "database.db"
