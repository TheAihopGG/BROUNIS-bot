from disnake import (
    Guild,
    Member,
    Embed,
    TextInputStyle,
    ModalInteraction,
    MessageInteraction,
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
from sqlite3 import connect as db_connect

from core.config import DATABASE_FILENAME
from core.named_tuples import ReportTicket, ReportTicketMember

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
UNEXPECTED_ERROR_EMBED = Embed(
    title="Ошибка программы",
    color=Color.red(),
    timestamp=datetime.now(),
)


class ReportUserModal(Modal):
    def __init__(
        self,
        target: Member,
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
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            result = cur.execute(
                "INSERT INTO report_tickets (channel_id, user_discord_id, report_message) VALUES (?, ?, ?)",
                [
                    report_ticket_channel.id,
                    self.user.id,
                    inter.text_values["report_text"],
                ],
            )
            conn.commit()
            report_ticket_id = result.lastrowid
            if result.rowcount:
                # если пользователь хочет, чтобы target присутствовал в чате, настроить для него права
                if self.target_has_access_to_report_ticket_channel:
                    await report_ticket_channel.set_permissions(
                        target=self.target,
                        view_channel=True,
                    )
                    # и также добавляем его в базу данных
                    result = cur.execute(
                        "INSERT OR REPLACE INTO report_ticket_members (user_discord_id, report_ticket_id) VALUES (?, ?)",
                        [
                            self.target.id,
                            report_ticket_id,
                        ],
                    )
                    conn.commit()
                cur.close()
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
            else:
                await inter.response.send_message(embed=UNEXPECTED_ERROR_EMBED)


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="report_member", description="Подать жалобу на пользователя и создать тикет")
    async def report(
        self,
        inter: AppCmdInter,
        target_member: Member,
        target_has_access_ticket_channel: bool = commands.Param(True, description="Будет ли обвиняемый пользователь присутствовать в тикете"),
    ) -> None:
        await inter.response.send_modal(
            ReportUserModal(
                target=target_member,
                target_has_access_to_report_ticket_channel=target_has_access_ticket_channel,
            )
        )

    @commands.slash_command(name="add_member_to_ticket", description="Добавить участника в тикет")
    async def add_member_to_report_ticket(
        self,
        inter: AppCmdInter,
        target_member: Member,
    ) -> None:
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            # получаем report_ticket
            cur.execute(
                "SELECT * FROM report_tickets WHERE channel_id = ?",
                [
                    inter.channel.id,
                ],
            )
            if report_ticket := ReportTicket._make(cur.fetchone()):
                if inter.author.id == report_ticket.user_discord_id or self.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
                    cur.execute(
                        "INSERT OR REPLACE INTO report_ticket_members (user_discord_id, report_ticket_id) VALUES (?, ?)",
                        [
                            target_member.id,
                            report_ticket.id,
                        ],
                    )
                    conn.commit()
                    cur.close()
                    if cur.rowcount:
                        report_ticket_channel = inter.guild.get_channel(report_ticket.channel_id)
                        await report_ticket_channel.set_permissions(
                            target=target_member,
                            view_channel=True,
                        )
                        await inter.response.send_message(
                            embed=Embed(
                                title="Участник был добавлен в тикет",
                                description=f"<@{target_member.id}>",
                                color=Color.green(),
                                timestamp=datetime.now(),
                            )
                        )
                    else:
                        await inter.response.send_message(
                            embed=Embed(
                                title="Участник уже добавлен в тикет",
                                color=Color.red(),
                                timestamp=datetime.now(),
                            )
                        )
                else:
                    await inter.response.send_message(
                        embed=NOT_ENOUGH_PERMISSIONS_EMBED,
                        ephemeral=True,
                    )

    @commands.slash_command(name="remove_member_from_ticket", description="Удалить участника из тикета")
    async def remove_member_from_report_ticket(
        self,
        inter: AppCmdInter,
        target_member: Member,
    ) -> None:
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            # получаем report_ticket
            cur.execute(
                "SELECT * FROM report_tickets WHERE channel_id = ?",
                [
                    inter.channel.id,
                ],
            )
            if report_ticket := ReportTicket._make(cur.fetchone()):
                if inter.author.id == report_ticket.user_discord_id or self.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
                    cur.execute(
                        "DELETE FROM report_ticket_members WHERE user_discord_id = ? AND report_ticket_id = ?",
                        [
                            target_member.id,
                            report_ticket.id,
                        ],
                    )
                    conn.commit()
                    cur.close()
                    if cur.rowcount:
                        report_ticket_channel = inter.guild.get_channel(report_ticket.channel_id)
                        await report_ticket_channel.set_permissions(
                            target=target_member,
                            view_channel=False,
                        )
                        await inter.response.send_message(
                            embed=Embed(
                                title="Участник был удалён из тикета",
                                description=f"<@{target_member.id}>",
                                color=Color.green(),
                                timestamp=datetime.now(),
                            )
                        )
                    else:
                        await inter.response.send_message(
                            embed=Embed(
                                title="Участник нету в тикете",
                                color=Color.red(),
                                timestamp=datetime.now(),
                            )
                        )

    @commands.slash_command(name="get_report_ticket_members", description="Получить список участников тикета")
    async def get_report_ticket_members(
        self,
        inter: AppCmdInter,
    ) -> None:
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM report_tickets WHERE channel_id = ?",
                [
                    inter.channel.id,
                ],
            )
            if report_ticket := ReportTicket._make(cur.fetchone()):
                cur.execute(
                    "SELECT * FROM report_ticket_members WHERE report_ticket_id = ?",
                    [
                        report_ticket.id,
                    ],
                )
                if report_ticket_members := map(ReportTicketMember._make, cur.fetchall()):
                    await inter.response.send_message(
                        embed=Embed(
                            title="Список участников",
                            description="".join(
                                [
                                    f"<@{report_ticket_member_discord_id}>\n"
                                    for report_ticket_member_discord_id in [report_ticket_member.user_discord_id for report_ticket_member in report_ticket_members] + [report_ticket.user_discord_id]
                                ],
                            ),
                        ),
                    )
                else:
                    await inter.response.send_message(
                        embed=Embed(
                            title="Список участников",
                            description=f"<@{report_ticket.user_discord_id}>",
                        ),
                    )

    @commands.Cog.listener("on_button_click")
    async def close_ticket(self, inter: MessageInteraction) -> None:
        global CLOSE_REPORT_TICKET_CUSTOM_ID
        global CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID

        if inter.component.custom_id == CONFIRM_CLOSE_REPORT_TICKET_CUSTOM_ID:
            if self.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
                await inter.channel.delete(reason=f"Тикет закрыт (by {inter.author.id})")
            else:
                await inter.response.send_message(
                    embed=NOT_ENOUGH_PERMISSIONS_EMBED,
                    ephemeral=True,
                )
        elif inter.component.custom_id == CLOSE_REPORT_TICKET_CUSTOM_ID:
            if self.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
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

    def is_report_ticket_administrator(self, member: Member, guild: Guild) -> bool:
        """Вернёт True если пользователь имеет хотя бы одну роль из ролей администраторов жалоб"""
        return any([guild.get_role(role_id) in member.roles for role_id in REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS])


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(ReportCog(bot=bot))
