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

    # --- Conversation Handlers ---
    # Каждый диалог должен быть в своем ConversationHandler

    # 1. Диалог регистрации
    registration_conv = ConversationHandler(
        entry_points=[CommandHandler('start', handlers.start)],
        states={
            config.STATES['REGISTER_FIRST_NAME']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_first_name)],
            config.STATES['REGISTER_LAST_NAME']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_last_name)],
            config.STATES['REGISTER_PHONE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.register_phone)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 2. Диалог создания нового абонемента
    new_subscription_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔄 Новый абонемент$'), handlers.new_subscription_start)],
        states={
            config.STATES['NEW_SUBSCRIPTION_NUMBER']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_subscription_number)],
            config.STATES['NEW_SUBSCRIPTION_AMOUNT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_subscription_amount)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 3. Диалог добавления тренировки
    add_training_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить тренировку$'), handlers.add_training_start)],
        states={
            config.STATES['TRAINING_DURATION']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_duration)],
            config.STATES['TRAINING_PARTICIPANTS']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_participants)],
            config.STATES['TRAINING_COURT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_court)],
            config.STATES['TRAINING_COACH']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.training_coach)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 4. Диалог просмотра статистики
    stats_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📈 Статистика$'), handlers.show_stats_start)],
        states={
            config.STATES['STATS_PERIOD']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.show_stats)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 5. Диалог закрытия абонемента
    close_subscription_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🚫 Закрыть абонемент$'), handlers.close_subscription_start)],
        states={
            config.STATES['CLOSE_SUBSCRIPTION_CONFIRM']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.close_subscription_confirm)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 6. Диалог пополнения абонемента
    top_up_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^💸 Пополнить$'), handlers.top_up_subscription_start)],
        states={
            config.STATES['TOP_UP_AMOUNT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.top_up_subscription_amount)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'), handlers.cancel)]
    )

    # 7. Диалог просмотра расходов
    expenses_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📊 Расходы$'), handlers.show_expenses_start)],
        states={
            config.STATES['EXPENSES_PERIOD']: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.show_expenses)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel), MessageHandler(filters.Regex('^❌ Отмена$'),
                                                                             handlers.cancel)]
    )

    # 8. Диалог для редактирования профиля
    edit_profile_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^✏️ Редактировать профиль$'), handlers.edit_profile_start)],
        states={
            config.STATES['EDIT_PROFILE_CHOICE']: [MessageHandler(filters.Regex('^Редактировать абонементы$'),
                                                                  handlers.edit_subscription_choice),],
            config.STATES['EDIT_SUBSCRIPTION_CHOICE']: [MessageHandler(filters.Regex('^Добавить старый абонемент$'),
                                                                       handlers.add_old_sub_start),
                                                        MessageHandler(filters.Regex('^Редактировать абонемент$'),
                                                                       handlers.edit_sub_select_start),],
            config.STATES['ADD_OLD_SUB_NUMBER']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 handlers.add_old_sub_number)],
            config.STATES['ADD_OLD_SUB_VISITS']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 handlers.add_old_sub_visits)],
            config.STATES['ADD_OLD_SUB_COST']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                               handlers.add_old_sub_cost)],
            config.STATES['ADD_OLD_SUB_START_DATE']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                     handlers.add_old_sub_start_date)],
            config.STATES['ADD_OLD_SUB_END_DATE']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                   handlers.add_old_sub_end_date)],
            config.STATES['EDIT_SUB_SELECT']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                              handlers.edit_sub_select)],
            config.STATES['EDIT_SUB_FIELD']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                             handlers.edit_sub_field)],
            config.STATES['EDIT_SUB_NEW_VALUE']: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 handlers.edit_sub_new_value)],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^Назад$'), handlers.back_to_main_menu),
            CommandHandler('cancel', handlers.cancel)
        ],
    )

    # Добавляем все диалоги в приложение
    application.add_handler(registration_conv)
    application.add_handler(new_subscription_conv)
    application.add_handler(add_training_conv)
    application.add_handler(stats_conv)
    application.add_handler(close_subscription_conv)
    application.add_handler(top_up_conv)
    application.add_handler(expenses_conv)
    application.add_handler(edit_profile_handler)

    # Обработчики для навигации по меню (не являются частью диалогов)
    application.add_handler(MessageHandler(filters.Regex('^💪 Тренировки$'), handlers.show_workouts_menu))
    application.add_handler(MessageHandler(filters.Regex('^💳 Абонементы$'), handlers.show_subscriptions_menu))
    application.add_handler(MessageHandler(filters.Regex('^👤 Профиль$'), handlers.show_profile_menu))
    application.add_handler(MessageHandler(filters.Regex('^🔙 Назад$'), handlers.back_to_main_menu))

    # Обработчики для одиночных действий (не являются частью диалогов)
    application.add_handler(MessageHandler(filters.Regex('^💰 Баланс$'), handlers.show_balance))
    application.add_handler(MessageHandler(filters.Regex('^📋 История тренировок$'), handlers.show_training_history))
    application.add_handler(MessageHandler(filters.Regex('^🗂️ Архив$'), handlers.show_archived_subscriptions))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Показать профиль$'), handlers.show_profile))
    # application.add_handler(MessageHandler(filters.Regex('^✏️ Редактировать профиль$'), handlers.edit_profile_start))

    # Обработчик для неизвестных команд (должен быть последним)
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