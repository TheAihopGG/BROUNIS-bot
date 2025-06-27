from disnake import (
    Guild,
    Option,
    Embed,
    TextInputStyle,
    ModalInteraction,
    MessageInteraction,
    User,
    AppCmdInter,
    TextChannel,
    ButtonStyle,
    Permissions,
    Color,
)
from disnake.ui import (
    Modal,
    TextInput,
    Button,
)
from disnake.ext import commands
from datetime import datetime

from core.logger import logger

REPORT_TICKETS_CATEGORY_ID = 1388095067629158462
"""ID категории в которой будут создаваться тикеты"""
REQUIRED_PERMISSIONS_TO_VIEW_REPORT_TICKETS = Permissions(
    administrator=True,
)
"""Какие права нужны для просмотра жалоб"""
REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS: list[int] = [1388107221996408842]
"""Роли, какие нужно будет упомянуть, когда приходит новая жалоба"""
CLOSE_REPORT_TICKET_CUSTOM_ID = "close_report_ticket_custom_id"
CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID = "confirm_close_report_ticket_custom_id"

NOT_ENOUGH_PERMISSIONS_EMBED = Embed(
    title="Недостаточно прав",
    color=Color.red(),
    timestamp=datetime.now(),
)


class ReportUserModal(Modal):
    def __init__(
        self,
        target: User,
        target_has_access_to_report_ticket_channel: bool,
    ):
        self.target = target
        self.target_has_access_to_report_ticket_channel = target_has_access_to_report_ticket_channel
        components = [
            TextInput(
                label="Текст жалобы",
                placeholder="Он плохой человек",
                custom_id="report_text",
                style=TextInputStyle.paragraph,
                max_length=200,
            ),
        ]
        super().__init__(title="Подать жалобу (тикет)", components=components)

    async def callback(self, inter: ModalInteraction) -> None:
        self.user = inter.author
        await inter.response.defer()
        # создать канал
        report_tickets_category = await inter.guild.fetch_channel(REPORT_TICKETS_CATEGORY_ID)
        report_ticket_channel: TextChannel = await report_tickets_category.create_text_channel(
            name=f"report-{self.user.name}",
            topic=f"Жалоба на {self.target.name}",
            reason=f"Жалоба на {self.target.id} от {self.user.id}",
        )
        # настроить права канала
        await report_ticket_channel.set_permissions(
            target=inter.guild.default_role,
            view_channel=False,
        )
        await report_ticket_channel.set_permissions(
            target=self.user,
            view_channel=True,
        )
        # если пользователь хочет, чтобы target присутствовал в чате, настроить для него права
        if self.target_has_access_to_report_ticket_channel:
            await report_ticket_channel.set_permissions(
                target=self.target,
                view_channel=True,
            )
        await report_ticket_channel.send(
            embed=Embed(
                title=f"report-ticket-{self.user.name}",
                description=inter.text_values["report_text"],
                timestamp=datetime.now(),
                color=Color.yellow(),
            ).add_field(
                name="Жалобу подал(а)",
                value=self.user.mention,
                inline=True,
            ),
            components=[
                Button(
                    label="Закрыть тикет",
                    style=ButtonStyle.primary,
                    custom_id=CLOSE_REPORT_TICKET_CUSTOM_ID,
                )
            ],
        )
        # упомянуть людей
        role_ids_to_mention = REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS
        # если пользователь хочет, чтобы target присутствовал в чате, упомянуть и его
        user_ids_to_mention: list[int] = [self.user.id, self.target.id] if self.target_has_access_to_report_ticket_channel else [self.user.id]
        await report_ticket_channel.send(
            "".join(
                [f"<@&{role_id}>" for role_id in role_ids_to_mention],
            )
            + "".join(
                [f"<@{user_id}>" for user_id in user_ids_to_mention],
            ),
        )
        # ответить
        await inter.edit_original_response(
            embed=Embed(
                title="Жалоба успешно подана",
                color=Color.green(),
                timestamp=datetime.now(),
            ).add_field(
                name="Ссылка на канал",
                value=report_ticket_channel.mention,
                inline=True,
            ),
        )


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="report_user", description="Подать жалобу на пользователя и создать тикет")
    async def report(
        self,
        inter: AppCmdInter,
        target: User,
        target_has_access_ticket_channel: bool = commands.Param(True, description="Будет ли обвиняемый пользователь присутствовать в тикете"),
    ) -> None:
        await inter.response.send_modal(
            ReportUserModal(
                target=target,
                target_has_access_to_report_ticket_channel=target_has_access_ticket_channel,
            )
        )

    @commands.Cog.listener("on_button_click")
    async def close_ticket(self, inter: MessageInteraction) -> None:
        global CLOSE_REPORT_TICKET_CUSTOM_ID
        global CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID

        if inter.component.custom_id == CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID:
            if self.is_report_ticket_administrator(user=inter.author, guild=inter.guild):
                await inter.channel.delete(reason=f"Тикет закрыт (by {inter.author.id})")
            else:
                await inter.response.send_message(
                    embed=NOT_ENOUGH_PERMISSIONS_EMBED,
                    ephemeral=True,
                )
        elif inter.component.custom_id == CLOSE_REPORT_TICKET_CUSTOM_ID:
            if self.is_report_ticket_administrator(user=inter.author, guild=inter.guild):
                await inter.response.send_message(
                    embed=Embed(
                        title="Вы уверены что хотите закрыть тикет?",
                        timestamp=datetime.now(),
                        color=Color.yellow(),
                    ),
                    components=[
                        Button(
                            label="Да",
                            style=ButtonStyle.danger,
                            custom_id=CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID,
                        )
                    ],
                    ephemeral=True,
                )
            else:
                await inter.response.send_message(
                    embed=NOT_ENOUGH_PERMISSIONS_EMBED,
                    ephemeral=True,
                )

    def is_report_ticket_administrator(self, user: User, guild: Guild) -> bool:
        """Вернёт True если пользователь имеет хотя бы одну роль из ролей администраторов жалоб"""
        return any([guild.get_role(role_id) in user.roles for role_id in REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS])


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(ReportCog(bot=bot))
