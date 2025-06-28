# BROUNIS-bot

## Todo

- [x] create cog: ReportCog
- [x] create command: /report_member
- [x] create command: /add_member_to_rp_ticket
- [x] create command: /remove_member_from_ticket
- [x] create command: /get_report_ticket_members
- [x] create command: /close_ticket
- [ ] test and fix cog: ReportCog
- [ ] test and fix command: /report_member
- [ ] test and fix command: /add_member_to_rp_ticket
- [ ] test and fix command: /remove_member_from_ticket
- [ ] test and fix command: /get_report_ticket_members
- [ ] test and fix command: /close_ticket

## Использование команд

### /report_member

Подать жалобу на участника

/report_member `target_member`: User `target_has_access_ticket_channel`: bool

#### Параметры

- `target_member`

  Участник, на которого подаётся жалоба

- `target_has_access_to_report_ticket_channel`

  Будет ли обвиняемый пользователь присутствовать в канале тикета

### /add_member_to_rp_ticket

Добавить участника в репорт-тикет
Нужно иметь модератора репорт-тикетов

/add_member_to_rp_ticket `target_member`: Member

#### Параметры

- `target_member`

  Добавляемый участник

### /remove_member_from_ticket

Удалить участника из репорт-тикета
Нужно иметь модератора репорт-тикетов

/remove_member_from_ticket `target_member`: Member

#### Параметры

- `target_member`

  Удаляемый участник

### /get_report_ticket_members

Получить список участников в репорт-тикете

/get_report_ticket_members

### /close_ticket

Закрыть тикет
Нужно иметь модератора репорт-тикетов

/close_ticket
