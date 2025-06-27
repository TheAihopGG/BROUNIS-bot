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
CREATE INDEX IF NOT EXISTS report_ticket_id_index ON report_ticket_members(id);
CREATE INDEX IF NOT EXISTS report_ticket_member_id_index ON report_ticket_members(id);