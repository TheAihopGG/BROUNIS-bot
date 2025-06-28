from typing import NamedTuple


class ReportTicket(NamedTuple):
    id: int
    channel_id: int
    user_discord_id: int
    report_message: str


class ReportTicketMember(NamedTuple):
    id: int
    user_discord_id: int
    report_ticket_id: int


class ReportTicketModeratorRole(NamedTuple):
    id: int
    role_id: int


class GuildSettings(NamedTuple):
    id: int
    guild_id: int
    report_tickets_category_id: int
