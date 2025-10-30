import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from database import Database
from handlers import Handlers
from config import config
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    # Создаем папку для базы данных если её нет
    os.makedirs(os.path.dirname(config.DB_PATH) if os.path.dirname(config.DB_PATH) else '.', exist_ok=True)

    # Инициализация базы данных
    db = Database(config.DB_PATH)
    handlers = Handlers(db)

    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()

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
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel)]
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex('^🎾 Добавить тренировку$'), handlers.add_training_start))
    application.add_handler(MessageHandler(filters.Regex('^💰 Баланс абонемента$'), handlers.show_balance))
    application.add_handler(MessageHandler(filters.Regex('^📊 Статистика$'), handlers.show_stats_start))
    application.add_handler(MessageHandler(filters.Regex('^📝 Новый абонемент$'), handlers.new_subscription_start))
    application.add_handler(MessageHandler(filters.Regex('^📋 История тренировок$'), handlers.show_training_history))
    application.add_handler(MessageHandler(filters.Regex('^👤 Профиль$'), handlers.show_profile))
    application.add_handler(MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.unknown_command))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()