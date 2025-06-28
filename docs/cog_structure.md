# Структура расширения (ког)

```python
class ComponentCustomIds(StrEnum):
    ...


class Cog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

class CRUD:
    ...

class Utils:
    ...

class Embeds:
    ...

def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(ExampleCog(bot))
```

## Разбор

### class `ComponentCustomIds`

Перечисление с значениями custom_id у ui компонентов

### class `Cog`

Класс расширения

### class `CRUD`

Содержит статические методы для работы с данными

### class `Utils`

Содержит статические вспомогательные методы

### class `Embeds`

Содержит часто используемые эмбеды

Ембеды представлены в виде ламбда функций. Это сделано для того, чтобы `datetime.now()` возвращал время в момент отправки сообщения, а не при загрузке модуля.

### function `setup`

Функция для регистрации расширения в боте
