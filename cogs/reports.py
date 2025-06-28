from typing import TypedDict
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
from sqlite3 import connect as db_connect, Cursor
from enum import auto, StrEnum

from core.config import DATABASE_FILENAME
from core.named_tuples import ReportTicket, ReportTicketMember

REPORT_TICKETS_CATEGORY_ID = 1388095067629158462
"""ID категории в которой будут создаваться тикеты"""
REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS: list[int] = [1388107221996408842]
"""Роли, какие нужно будет упомянуть, когда приходит новая жалоба"""


class Embeds:
    NOT_ENOUGH_PERMISSIONS_EMBED = lambda: Embed(
        title="Недостаточно прав",
        color=Color.red(),
        timestamp=datetime.now(),
    )
    UNEXPECTED_ERROR_EMBED = lambda: Embed(
        title="Ошибка программы",
        color=Color.red(),
        timestamp=datetime.now(),
    )
    THE_CHANNEL_IS_NOT_REPORT_TICKET_EMBED = lambda: Embed(
        title="Этот канал не является тикетом",
        color=Color.red(),
        timestamp=datetime.now(),
    )


class ComponentCustomIds(StrEnum):
    CLOSE_REPORT_TICKET = auto()
    CONFIRM_CLOSE_REPORT_TICKET = auto()


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

    class ModalTextValues(TypedDict):
        report_text: str

    async def callback(self, inter: ModalInteraction) -> None:
        modal_data: ReportUserModal.ModalTextValues = inter.text_values
        report_ticket_author = inter.author
        # закрыть окно
        await inter.response.defer()
        # создать канал для тикета
        report_tickets_category = await inter.guild.fetch_channel(REPORT_TICKETS_CATEGORY_ID)
        report_ticket_channel: TextChannel = await report_tickets_category.create_text_channel(
            name=f"report-{report_ticket_author.name}",
            topic=f"Жалоба на {self.target.name}",
            reason=f"Жалоба на {self.target.id} от {report_ticket_author.id}",
        )
        # настроить права канала
        await report_ticket_channel.set_permissions(
            target=inter.guild.default_role,
            view_channel=False,
        )
        await report_ticket_channel.set_permissions(
            target=report_ticket_author,
            view_channel=True,
        )
        # выполняем действия с базой данных
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            # создаём запись в report_tickets
            result = cur.execute(
                "INSERT INTO report_tickets (channel_id, user_discord_id, report_message) VALUES (?, ?, ?)",
                [
                    report_ticket_channel.id,
                    report_ticket_author.id,
                    modal_data["report_text"],
                ],
            )
            conn.commit()
            if report_ticket_id := result.lastrowid:  # ID созданной записи
                if result.rowcount:
                    # если пользователь хочет, чтобы target присутствовал в чате, настроить для него права
                    if self.target_has_access_to_report_ticket_channel:
                        await CRUD.add_report_ticket_member(
                            cur,
                            report_ticket_member=self.target,
                            report_ticket_channel=report_ticket_channel,
                            report_ticket_id=report_ticket_id,
                        )
                        conn.commit()
                    cur.close()
                    # отправить сообщение с кнопкой в тикет
                    await (
                        await report_ticket_channel.send(
                            embed=Embed(
                                title=f"report-ticket-{report_ticket_author.name}",
                                description=inter.text_values["report_text"],
                                timestamp=datetime.now(),
                                color=Color.yellow(),
                            ).add_field(
                                name="Жалобу подал(а)",
                                value=report_ticket_author.mention,
                                inline=True,
                            ),
                            components=[
                                Button(
                                    label="Закрыть тикет",
                                    style=ButtonStyle.primary,
                                    custom_id=ComponentCustomIds.CLOSE_REPORT_TICKET,
                                )
                            ],
                        )
                    ).pin()
                    # упомянуть роли администраторов тикетов, упомянуть участника который открыл тикет
                    # упомянуть человека, на которого был написан тикет если target_has_access_to_report_ticket_channel == True
                    user_ids_to_mention: list[int] = [report_ticket_author.id, self.target.id] if self.target_has_access_to_report_ticket_channel else [report_ticket_author.id]
                    await report_ticket_channel.send(
                        "".join(
                            [f"<@&{role_id}>" for role_id in REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS],
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
                    await inter.response.send_message(embed=Embeds.UNEXPECTED_ERROR_EMBED())
            else:
                await inter.response.send_message(embed=Embeds.UNEXPECTED_ERROR_EMBED())


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="report_member", description="Подать жалобу на участника и создать репорт-тикет")
    async def report_member(
        self,
        inter: AppCmdInter,
        target_member: Member,
        target_has_access_ticket_channel: bool = commands.Param(True, description="Будет ли обвиняемый участник присутствовать в репорт-тикете?"),
    ) -> None:
        await inter.response.send_modal(
            ReportUserModal(
                target=target_member,
                target_has_access_to_report_ticket_channel=target_has_access_ticket_channel,
            )
        )

    @commands.slash_command(name="add_member_to_rp_ticket", description="Добавить участника в репорт-тикет")
    async def add_member_to_report_ticket(
        self,
        inter: AppCmdInter,
        target_member: Member,
    ) -> None:
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            # получаем report_ticket
            if report_ticket := await CRUD.get_report_ticket(
                cur,
                channel_id=inter.channel_id,
            ):
                # проверяем права
                if Utils.is_report_ticket_administrator(member=inter.author, guild=inter.guild) or inter.author.guild_permissions.administrator:
                    # добавляем участника в тикет
                    if await CRUD.add_report_ticket_member(
                        cur,
                        report_ticket_member=target_member,
                        report_ticket_channel=inter.channel,
                        report_ticket_id=report_ticket.id,
                    ):
                        conn.commit()
                        cur.close()

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
                        embed=Embeds.NOT_ENOUGH_PERMISSIONS_EMBED(),
                        ephemeral=True,
                    )
            else:
                await inter.response.send_message(
                    embed=Embeds.THE_CHANNEL_IS_NOT_REPORT_TICKET_EMBED(),
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
            if report_ticket := await CRUD.get_report_ticket(cur, channel_id=inter.channel_id):
                # проверяем права
                if Utils.is_report_ticket_administrator(member=inter.author, guild=inter.guild) or inter.author.guild_permissions.administrator:
                    if target_member.id != report_ticket.user_discord_id:
                        if await CRUD.remove_report_ticket_member(
                            cur,
                            report_ticket_member=target_member,
                            report_ticket_channel=inter.channel,
                            report_ticket_id=report_ticket.id,
                        ):
                            conn.commit()
                            cur.close()
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
                                    title="Участника нету в тикете",
                                    color=Color.red(),
                                    timestamp=datetime.now(),
                                )
                            )
                    else:
                        await inter.response.send_message(
                            embed=Embed(
                                title="Вы являетесь создателем тикета, и не можете себя удалить",
                                color=Color.red(),
                                timestamp=datetime.now(),
                            ),
                            ephemeral=True,
                        )
                else:
                    await inter.response.send_message(
                        embed=Embeds.NOT_ENOUGH_PERMISSIONS_EMBED(),
                        ephemeral=True,
                    )
            else:
                await inter.response.send_message(
                    embed=Embeds.THE_CHANNEL_IS_NOT_REPORT_TICKET_EMBED(),
                    ephemeral=True,
                )

    @commands.slash_command(name="get_report_ticket_members", description="Получить список участников тикета")
    async def get_report_ticket_members(
        self,
        inter: AppCmdInter,
    ) -> None:
        with db_connect(DATABASE_FILENAME) as conn:
            cur = conn.cursor()
            if report_ticket := await CRUD.get_report_ticket(cur, channel_id=inter.channel_id):
                cur.execute(
                    "SELECT * FROM report_ticket_members WHERE report_ticket_id = ?",
                    [
                        report_ticket.id,
                    ],
                )
                if result := cur.fetchall():
                    if report_ticket_members := map(ReportTicketMember._make, result):
                        await inter.response.send_message(
                            embed=Embed(
                                title="Список участников",
                                description="".join(
                                    [
                                        f"<@{report_ticket_member_discord_id}>\n"
                                        for report_ticket_member_discord_id in [report_ticket_member.user_discord_id for report_ticket_member in report_ticket_members]
                                        + [report_ticket.user_discord_id]
                                    ],
                                ),
                                color=Color.green(),
                                timestamp=datetime.now(),
                            ),
                            ephemeral=True,
                        )
                else:
                    await inter.response.send_message(
                        embed=Embed(
                            title="Список участников",
                            description=f"<@{report_ticket.user_discord_id}>",
                            color=Color.green(),
                            timestamp=datetime.now(),
                        ),
                        ephemeral=True,
                    )
            else:
                await inter.response.send_message(
                    embed=Embeds.THE_CHANNEL_IS_NOT_REPORT_TICKET_EMBED(),
                    ephemeral=True,
                )

    @commands.slash_command(name="close_report_ticket", description="Закрывает репорт-тикет")
    async def close_report_ticket(self, inter: AppCmdInter) -> None:
        if Utils.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
            with db_connect(DATABASE_FILENAME) as conn:
                cur = conn.cursor()
                if await CRUD.get_report_ticket(cur, channel_id=inter.channel_id):
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
                                custom_id=ComponentCustomIds.CONFIRM_CLOSE_REPORT_TICKET,
                            )
                        ],
                        ephemeral=True,
                    )
                else:
                    await inter.response.send_message(
                        embed=Embeds.THE_CHANNEL_IS_NOT_REPORT_TICKET_EMBED(),
                        ephemeral=True,
                    )
        else:
            await inter.response.send_message(
                embed=Embeds.NOT_ENOUGH_PERMISSIONS_EMBED(),
                ephemeral=True,
            )

    @commands.Cog.listener("on_button_click")
    async def buttons_listener(self, inter: MessageInteraction) -> None:
        component_custom_id: ComponentCustomIds = inter.component.custom_id
        match component_custom_id:
            case ComponentCustomIds.CONFIRM_CLOSE_REPORT_TICKET:
                if Utils.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
                    await inter.channel.delete(reason=f"Тикет закрыт (by {inter.author.id})")
                else:
                    await inter.response.send_message(
                        embed=Embeds.NOT_ENOUGH_PERMISSIONS_EMBED(),
                        ephemeral=True,
                    )
            case ComponentCustomIds.CLOSE_REPORT_TICKET:
                if Utils.is_report_ticket_administrator(member=inter.author, guild=inter.guild):
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
                                custom_id=ComponentCustomIds.CONFIRM_CLOSE_REPORT_TICKET,
                            )
                        ],
                        ephemeral=True,
                    )
                else:
                    await inter.response.send_message(
                        embed=Embeds.NOT_ENOUGH_PERMISSIONS_EMBED(),
                        ephemeral=True,
                    )


class CRUD:
    @staticmethod
    async def add_report_ticket_member(
        cur: Cursor,
        *,
        report_ticket_member: Member,
        report_ticket_channel: TextChannel,
        report_ticket_id: int,
    ) -> bool:
        """
        Создаёт новую запись в таблице report_ticket_members и настраивает права для канала report_ticket_channel

        :param report_ticket_member:
        Участник, для которого будут настраиваться права
        :param report_ticket_channel:
        Тикет канал, который будет настраиваться
        :param report_ticket_id:
        ID тикета
        :return:
        True если операция прошла успешно, иначе False
        """
        await report_ticket_channel.set_permissions(
            target=report_ticket_member,
            view_channel=True,
        )
        result = cur.execute(
            "INSERT OR REPLACE INTO report_ticket_members (user_discord_id, report_ticket_id) VALUES (?, ?)",
            [
                report_ticket_member.id,
                report_ticket_id,
            ],
        )
        return bool(result.rowcount)

    @staticmethod
    async def remove_report_ticket_member(
        cur: Cursor,
        *,
        report_ticket_member: Member,
        report_ticket_channel: TextChannel,
        report_ticket_id: int,
    ) -> bool:
        """
        Удаляет запись из таблицы report_ticket_members и настраивает права для канала report_ticket_channel

        :param report_ticket_member:
        Участник, для которого будут настраиваться права
        :param report_ticket_channel:
        Тикет канал, который будет настраиваться
        :param report_ticket_id:
        ID тикета
        :return:
        True если операция прошла успешно, иначе False
        """
        await report_ticket_channel.set_permissions(
            target=report_ticket_member,
            view_channel=False,
        )
        result = cur.execute(
            "DELETE FROM report_ticket_members WHERE user_discord_id = ? AND report_ticket_id = ?",
            [
                report_ticket_member.id,
                report_ticket_id,
            ],
        )

        return bool(result.rowcount)

    @staticmethod
    async def get_report_ticket(cur: Cursor, *, channel_id: int) -> ReportTicket | None:
        cur.execute(
            "SELECT * FROM report_tickets WHERE channel_id = ?",
            [
                channel_id,
            ],
        )
        if result := cur.fetchone():
            return ReportTicket._make(result)
        else:
            return None


class Utils:
    @staticmethod
    def is_report_ticket_administrator(*, member: Member, guild: Guild) -> bool:
        """
        Вернёт True если пользователь имеет хотя бы одну роль из ролей администраторов жалоб

        :param member:
        Участник, роли которого которого нужно проверить
        :param guild:
        Сервер, на котором находится участник
        """
        return any([guild.get_role(role_id) in member.roles for role_id in REPORT_TICKETS_ADMINISTRATOR_ROLE_IDS])


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(ReportCog(bot=bot))
