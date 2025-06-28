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

def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(ExampleCog(bot))
```

## Разбор

### class `ComponentCustomIds`

Перечисление с значениями custom_id у ui компонентов

### class `Cog`

Класс расширения

### class `CRUD`

Содержит методы для работы с данными

### class `Utils`

Содержит вспомогательные методы

### function `setup`

Функция для регистрации расширения в боте
