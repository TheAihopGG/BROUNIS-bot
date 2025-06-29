# BROUNIS-bot

## Todo

- [x] create cog: ReportCog
- [x] create command: /report_member
- [x] create command: /add_member_to_rp_ticket
- [x] create command: /remove_member_from_ticket
- [x] create command: /get_report_ticket_members
- [x] create command: /close_ticket
- [x] create command: /add_rp_ticket_moder_role
- [x] create command: /remove_rp_ticket_moder_role
- [x] test and fix cog: ReportCog
- [x] test and fix command: /report_member
- [x] test and fix command: /add_member_to_rp_ticket
- [x] test and fix command: /remove_member_from_ticket
- [x] test and fix command: /get_report_ticket_members
- [x] test and fix command: /close_ticket
- [x] test and fix command: /add_rp_ticket_moder_role
- [x] test and fix command: /remove_rp_ticket_moder_role

## Использование команд

### ReportCog

#### /report_member

Подать жалобу на участника

/report_member `target_member`: User `target_has_access_ticket_channel`: bool

##### Параметры

- `target_member`

  Участник, на которого подаётся жалоба

- `target_has_access_to_report_ticket_channel`

  Будет ли обвиняемый пользователь присутствовать в канале тикета

#### /add_member_to_rp_ticket

Добавить участника в репорт-тикет
Нужно иметь модератора репорт-тикетов

/add_member_to_rp_ticket `target_member`: Member

##### Параметры

- `target_member`

  Добавляемый участник

#### /remove_member_from_ticket

Удалить участника из репорт-тикета
Нужно иметь модератора репорт-тикетов

/remove_member_from_ticket `target_member`: Member

##### Параметры

- `target_member`

  Удаляемый участник

#### /get_report_ticket_members

Получить список участников в репорт-тикете

/get_report_ticket_members

#### /close_ticket

Закрыть тикет
Нужно иметь модератора репорт-тикетов

/close_ticket

### /add_rp_ticket_moder_role

Добавляет роль в список модераторов репорт-тикетов

/add_rp_ticket_admin_role `role`: Role

##### Параметры

- `role` Роль в дискорде, которая будет добавлена

### /remove_rp_ticket_moder_role

Удаляет роль из списка модераторов репорт-тикетов

/remove_rp_ticket_moder_role `role`: Role

##### Параметры

- `role` Роль в дискорде, которая будет удалена

### /get_rp_ticket_moder_roles

Отправляет список ролей модераторов репорт-тикетов

/get_rp_ticket_moder_roles

### /set_rp_ticket_category

Устанавливает категорию как категорию для репорт-тикетов

/set_rp_ticket_category `category`: CategoryChannel

##### Параметры

- `category` Категория, которая будет установлена как категория для репорт-тикетов

### /start_event

Запускает ивент

/start_event

### /restart_event

Перезапускает текущий ивент

/restart_event

### /stop_event

Останавливает ивент

/stop_event

### /enable_events

Включает ивенты на сервере

/enable_events

### /disable_events

Выключает ивенты на сервере

/disable_events

### /set_events_delay

Устанавливает задержу между ивентами

/set_events_delay `delay_in_minutes`: int

### /set_events_news_channel

Устанавливает выбранный канал как канал для уведомлений об ивентах

/set_events_news_channel `channel`: TextChannel

#### Параметры

- `channel` Канал, который будет установлена как канал для уведомлений об ивентах

### /set_events_warning_message

Устанавливает выбранный канал как канал для уведомлений об ивентах

/set_events_news_channel `message_text`: TextChannel `event_name`: str `apply_to_all_events`: bool

#### Параметры

- `message_text` Сообщение

- `event_name` Название ивента, для которого будет применено это сообщение (опционально). Если не указан, будет использоваться параметр `apply_to_all_events`

- `apply_to_all_events` Если true, сообщение применится ко всем ивентам (опционально). По умолчанию false