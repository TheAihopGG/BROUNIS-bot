from datetime import datetime
from disnake import Color, Embed, MessageInteraction
from disnake.ext import commands

from core.logger import logger
from core.config import BOT_TOKEN

bot = commands.InteractionBot()
bot.load_extensions("cogs")


@bot.event
async def on_ready() -> None:
    logger.info("Bot ready")


@bot.listen("close_ticket")
async def close_ticket(inter: MessageInteraction) -> None:
    await inter.channel.delete(reason=f"Тикет закрыт (by {inter.author.id})")
    await inter.author.send(
        embed=Embed(
            title="Тикет закрыт",
            timestamp=datetime.now(),
            color=Color.green(),
        )
    )


bot.run(BOT_TOKEN)
