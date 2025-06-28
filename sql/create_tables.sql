CREATE TABLE IF NOT EXISTS report_tickets (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER UNIQUE,
    user_discord_id INTEGER,
    report_message VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS report_ticket_members (
    id INTEGER PRIMARY KEY,
    user_discord_id INTEGER,
    report_ticket_id INTEGER,
    FOREIGN KEY (report_ticket_id) REFERENCES report_tickets(id)
);
CREATE TABLE IF NOT EXISTS report_ticket_moderator_roles (
    id INTEGER PRIMARY KEY,
    role_id INTEGER
);
CREATE TABLE IF NOT EXISTS guild_settings (
    id INTEGER PRIMARY KEY,
    guild_id INTEGER UNIQUE,
    report_tickets_category_id INTEGER DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS report_ticket_id_index ON report_ticket_members(id);
CREATE INDEX IF NOT EXISTS report_ticket_member_id_index ON report_ticket_members(id);
CREATE INDEX IF NOT EXISTS report_ticket_moderator_role_id_index ON report_ticket_moderator_roles(id);
CREATE INDEX IF NOT EXISTS guild_settings_id_index ON guild_settings(id);