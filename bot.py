import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from handlers import Handlers
from config import config, RegisterStates, SubscriptionStates, TrainingStates, StatsStates
from logging_config import setup_logging


async def main():
    # Инициализация логирования
    setup_logging()
    logger = logging.getLogger('bot.main')

    logger.info("Starting Tennis Manager Bot...")

    # Проверка наличия токена
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    # Создаем папку для базы данных если её нет
    os.makedirs(os.path.dirname(config.DB_PATH) if os.path.dirname(config.DB_PATH) else '.', exist_ok=True)

    # Инициализация базы данных
    try:
        db = Database(config.DB_PATH)
        handlers_instance = Handlers(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Инициализация бота и диспетчера
    try:
        bot = Bot(token=config.BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        logger.info("Bot application created successfully")
    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        return

    # === Обработчики команд ===

    # Команда /start
    @dp.message(Command("start"))
    async def start_command(message: types.Message, state):
        await handlers_instance.start(message, state)

    # === Регистрация ===
    @dp.message(RegisterStates.first_name)
    async def register_first_name_handler(message: types.Message, state):
        await handlers_instance.register_first_name(message, state)

    @dp.message(RegisterStates.last_name)
    async def register_last_name_handler(message: types.Message, state):
        await handlers_instance.register_last_name(message, state)

    @dp.message(RegisterStates.phone)
    async def register_phone_handler(message: types.Message, state):
        await handlers_instance.register_phone(message, state)

    # === Абонемент ===
    @dp.message(SubscriptionStates.number)
    async def subscription_number_handler(message: types.Message, state):
        await handlers_instance.new_subscription_number(message, state)

    @dp.message(SubscriptionStates.amount)
    async def subscription_amount_handler(message: types.Message, state):
        await handlers_instance.new_subscription_amount(message, state)

    # === Тренировка ===
    @dp.message(TrainingStates.duration)
    async def training_duration_handler(message: types.Message, state):
        await handlers_instance.training_duration(message, state)

    @dp.message(TrainingStates.participants)
    async def training_participants_handler(message: types.Message, state):
        await handlers_instance.training_participants(message, state)

    @dp.message(TrainingStates.court)
    async def training_court_handler(message: types.Message, state):
        await handlers_instance.training_court(message, state)

    @dp.message(TrainingStates.coach)
    async def training_coach_handler(message: types.Message, state):
        await handlers_instance.training_coach(message, state)

    # === Статистика ===
    @dp.message(StatsStates.period)
    async def stats_period_handler(message: types.Message, state):
        await handlers_instance.show_stats(message, state)

    # === Обработчики меню ===
    @dp.message(F.text == '🎾 Добавить тренировку')
    async def add_training_handler(message: types.Message, state):
        await handlers_instance.add_training_start(message, state)

    @dp.message(F.text == '💰 Баланс абонемента')
    async def show_balance_handler(message: types.Message):
        await handlers_instance.show_balance(message)

    @dp.message(F.text == '📊 Статистика')
    async def show_stats_start_handler(message: types.Message, state):
        await handlers_instance.show_stats_start(message, state)

    @dp.message(F.text == '📝 Новый абонемент')
    async def new_subscription_handler(message: types.Message, state):
        await handlers_instance.new_subscription_start(message, state)

    @dp.message(F.text == '📋 История тренировок')
    async def show_history_handler(message: types.Message):
        await handlers_instance.show_training_history(message)

    @dp.message(F.text == '👤 Профиль')
    async def show_profile_handler(message: types.Message):
        await handlers_instance.show_profile(message)

    @dp.message(F.text == '❌ Отмена')
    async def cancel_handler(message: types.Message, state):
        await handlers_instance.cancel(message, state)

    # === Обработчик неизвестных команд ===
    @dp.message()
    async def unknown_handler(message: types.Message):
        await handlers_instance.unknown_command(message)

    # Запуск бота
    try:
        logger.info("Bot starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
