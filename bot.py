from disnake.ext import commands
from asyncio import run as asyncio_run

from core.logger import logger
from core.config import BOT_TOKEN
from core.database import create_tables

bot = commands.InteractionBot()
bot.load_extensions("cogs")

asyncio_run(create_tables())


@bot.event
async def on_ready() -> None:
    logger.info("Bot ready")


bot.run(BOT_TOKEN)
