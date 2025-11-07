# Миграция TennisManagerBot на aiogram 3.x

Этот документ описывает процесс миграции проекта с `python-telegram-bot` на `aiogram 3.x`.

## Обзор изменений

### Старая архитектура (python-telegram-bot 20.7)
- Синхронный диспетчер `Application`
- ConversationHandler для управления состояниями
- Отдельные обработчики команд и сообщений
- Контекст хранился в `context.user_data`

### Новая архитектура (aiogram 3.4.1)
- Асинхронный диспетчер `Dispatcher`
- FSM (Finite State Machine) для управления состояниями
- Декораторы `@dp.message()` для обработки сообщений
- FSMContext для хранения данных пользователя

## Ключевые изменения

### 1. Конфигурация (config.py)

**Было:**
```python
STATES: dict = {
    'REGISTER_FIRST_NAME': 1,
    'REGISTER_LAST_NAME': 2,
    'REGISTER_PHONE': 3,
    # ... другие состояния ...
}
```

**Стало:**
```python
class RegisterStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    first_name = State()
    last_name = State()
    phone = State()

class SubscriptionStates(StatesGroup):
    """Состояния для создания абонемента"""
    number = State()
    amount = State()

class TrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""
    duration = State()
    participants = State()
    court = State()
    coach = State()

class StatsStates(StatesGroup):
    """Состояния для просмотра статистики"""
    period = State()
```

### 2. Обработчики (handlers.py)

**Было (python-telegram-bot):**
```python
async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("Текст")
    return config.STATES['REGISTER_FIRST_NAME']
```

**Стало (aiogram):**
```python
async def start(self, message: types.Message, state: FSMContext):
    user = message.from_user
    await state.update_data(first_name=message.text)
    await message.answer("Текст")
    await state.set_state(RegisterStates.first_name)
```

**Основные отличия:**
- `update.message` → `message`
- `update.effective_user` → `message.from_user`
- `context.user_data[key] = value` → `await state.update_data(key=value)`
- `update.message.reply_text()` → `message.answer()`
- `return STATE` → `await state.set_state(States.name)`
- `ConversationHandler.END` → `await state.clear()`

### 3. Клавиатуры (keyboards.py)

**Было:**
```python
from telegram import ReplyKeyboardMarkup, KeyboardButton

keyboard = [
    ['Кнопка 1', 'Кнопка 2'],
    ['Кнопка 3']
]
return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
```

**Стало:**
```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard = [
    [KeyboardButton(text='Кнопка 1'), KeyboardButton(text='Кнопка 2')],
    [KeyboardButton(text='Кнопка 3')]
]
return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
```

### 4. Регистрация обработчиков (bot.py)

**Было (ConversationHandler):**
```python
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', handlers.start)],
    states={
        config.STATES['REGISTER_FIRST_NAME']: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_first_name)
        ],
        # ... другие состояния ...
    },
    fallbacks=[CommandHandler('cancel', handlers.cancel)]
)
application.add_handler(conv_handler)
```

**Стало (Dispatcher с FSM):**
```python
@dp.message(Command("start"))
async def start_command(message: types.Message, state):
    await handlers_instance.start(message, state)

@dp.message(RegisterStates.first_name)
async def register_first_name_handler(message: types.Message, state):
    await handlers_instance.register_first_name(message, state)

@dp.message(F.text == '🎾 Добавить тренировку')
async def add_training_handler(message: types.Message, state):
    await handlers_instance.add_training_start(message, state)
```

**Преимущества:**
- Более явный код
- Декораторы вместо конфигурационных объектов
- Лучше читается и поддерживается

### 5. Запуск бота

**Было:**
```python
application = Application.builder().token(config.BOT_TOKEN).build()
application.run_polling()
```

**Стало:**
```python
async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    # ... регистрация обработчиков ...
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
```

## Требования

### Старые зависимости:
```
python-telegram-bot==20.7
python-dotenv==1.0.0
```

### Новые зависимости:
```
aiogram==3.4.1
python-dotenv==1.0.0
```

## Функциональность

Вся функциональность остается прежней:
- Регистрация пользователей ✓
- Управление абонементами ✓
- Добавление тренировок ✓
- Просмотр статистики ✓
- История тренировок ✓
- Профиль пользователя ✓

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
echo "BOT_TOKEN=your_token_here" > .env

# Запуск бота
python bot.py
```

## Улучшения

### Что улучшилось в aiogram 3:

1. **Асинхронность** - встроенная асинхронность во всем коде
2. **FSM** - более мощная система управления состояниями
3. **Фильтры** - модульная система фильтрации сообщений
4. **Декораторы** - явная регистрация обработчиков
5. **Type hints** - лучшая поддержка типов
6. **Производительность** - асинхронная обработка множества запросов

### Возможные оптимизации в будущем:

1. **Асинхронная БД** - использование `aiosqlite` вместо `sqlite3`
2. **Webhook** - переход с polling на webhook для лучшей производительности
3. **Redis хранилище** - замена MemoryStorage на RedisStorage для масштабирования
4. **Middleware** - добавление middleware для логирования и обработки ошибок
5. **Роутеры** - организация обработчиков в маршруты

## Заключение

Миграция на aiogram 3.x обеспечивает лучшую архитектуру, производительность и масштабируемость проекта. Весь функционал сохранен, а код стал чище и понятнее.
