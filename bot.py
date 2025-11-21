import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import Database
from handlers import register_handlers
from config import config
from logging_config import setup_logging


async def main():
    # Инициализация логирования
    setup_logging()
    logger = logging.getLogger('bot.main')

    logger.info("Starting Tennis Manager Bot...")

    # Создаем папку для базы данных если её нет
    os.makedirs(os.path.dirname(config.DB_PATH) if os.path.dirname(config.DB_PATH) else '.', exist_ok=True)

    # Инициализация базы данных
    db = Database(config.DB_PATH)
    logger.info("Database connection configured.")

    # FSM storage
    storage = MemoryStorage()

    # Инициализация бота и диспетчера
    try:
        bot = Bot(token=config.BOT_TOKEN)
        dp = Dispatcher(storage=storage)
        logger.info("Bot and Dispatcher created successfully")
    except Exception as e:
        logger.error(f"Failed to create bot and dispatcher: {e}")
        return

    # Регистрация хэндлеров
    register_handlers(dp, db)

    # Запуск бота
    try:
        logger.info("Bot starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Bot stopped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped manually")