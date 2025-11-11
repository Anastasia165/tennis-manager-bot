import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from database import Database
from handlers import Handlers
from config import config
import os
from logging_config import setup_logging


def main():
    # Инициализация логирования
    setup_logging()
    logger = logging.getLogger('bot.main')

    logger.info("Starting Tennis Manager Bot...")

    # Создаем папку для базы данных если её нет
    os.makedirs(os.path.dirname(config.DB_PATH) if os.path.dirname(config.DB_PATH) else '.', exist_ok=True)

    # Инициализация базы данных
    try:
        db = Database(config.DB_PATH)
        handlers = Handlers(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        logger.info("Bot application created successfully")
    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        return

    # Обработчик начала работы и регистрации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handlers.start)],
        states={
            config.STATES['REGISTER_FIRST_NAME']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_first_name)
            ],
            config.STATES['REGISTER_LAST_NAME']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_last_name)
            ],
            config.STATES['REGISTER_PHONE']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_phone)
            ],
            config.STATES['NEW_SUBSCRIPTION_NUMBER']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_subscription_number)
            ],
            config.STATES['NEW_SUBSCRIPTION_AMOUNT']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_subscription_amount)
            ],
            config.STATES['TRAINING_DURATION']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_duration)
            ],
            config.STATES['TRAINING_PARTICIPANTS']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_participants)
            ],
            config.STATES['TRAINING_COURT']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_court)
            ],
            config.STATES['TRAINING_COACH']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_coach)
            ],
            config.STATES['STATS_PERIOD']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.show_stats)
            ],
            config.STATES['CLOSE_SUBSCRIPTION_CONFIRM']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.close_subscription_confirm)
            ],
            config.STATES['TOP_UP_AMOUNT']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.top_up_subscription_amount)
            ],
            config.STATES['EXPENSES_PERIOD']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.show_expenses)
            ],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel)]
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex('^💪 Тренировки$'), handlers.show_workouts_menu))
    application.add_handler(MessageHandler(filters.Regex('^💳 Абонементы$'), handlers.show_subscriptions_menu))
    application.add_handler(MessageHandler(filters.Regex('^👤 Профиль$'), handlers.show_profile_menu))
    application.add_handler(MessageHandler(filters.Regex('^🔙 Назад$'), handlers.back_to_main_menu))
    application.add_handler(MessageHandler(filters.Regex('^➕ Добавить тренировку$'), handlers.add_training_start))
    application.add_handler(MessageHandler(filters.Regex('^💰 Баланс$'), handlers.show_balance))
    application.add_handler(MessageHandler(filters.Regex('^📈 Статистика$'), handlers.show_stats_start))
    application.add_handler(MessageHandler(filters.Regex('^🔄 Новый абонемент$'), handlers.new_subscription_start))
    application.add_handler(MessageHandler(filters.Regex('^📋 История тренировок$'), handlers.show_training_history))
    application.add_handler(MessageHandler(filters.Regex('^🗂️ Архив$'), handlers.show_archived_subscriptions))
    application.add_handler(MessageHandler(filters.Regex('^💸 Пополнить$'), handlers.top_up_subscription_start))
    application.add_handler(MessageHandler(filters.Regex('^📊 Расходы$'), handlers.show_expenses_start))
    application.add_handler(MessageHandler(filters.Regex('^🚫 Закрыть абонемент$'), handlers.close_subscription_start))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Показать профиль$'), handlers.show_profile))
    application.add_handler(MessageHandler(filters.Regex('^✏️ Редактировать профиль$'), handlers.edit_profile_start))
    application.add_handler(MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.unknown_command))

    # Запуск бота
    try:
        logger.info("Bot starting polling...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Bot stopped")


if __name__ == '__main__':
    main()
