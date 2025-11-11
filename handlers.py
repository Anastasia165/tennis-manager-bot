from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging
from database import Database
from keyboards import *
from utils import *
from config import config

logger = logging.getLogger(__name__)


class Handlers:
    def __init__(self, db: Database):
        self.db = db
        self.logger = logging.getLogger('bot.handlers')

    @log_command
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.logger.info(f"Start command from user {user.id} ({user.username})")
        telegram_id = user.id

        if self.db.user_exists(telegram_id):
            await update.message.reply_text(
                f"С возвращением, {user.first_name}! 🎾\n"
                "Выберите действие в меню:",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "Добро пожаловать в Tennis Club Bot! 🎾\n"
                "Для регистрации введите ваше имя:"
            )
            return config.STATES['REGISTER_FIRST_NAME']

    @log_command
    async def register_first_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        first_name = update.message.text
        user = update.effective_user
        self.logger.info(f"User {user.id} entered first name: {first_name}")
        context.user_data['first_name'] = update.message.text
        await update.message.reply_text("Отлично! Теперь введите вашу фамилию:")
        return config.STATES['REGISTER_LAST_NAME']

    async def register_last_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['last_name'] = update.message.text
        await update.message.reply_text(
            "Введите ваш номер телефона:\n"
            "Формат: +7 XXX XXX XX XX или 8 XXX XXX XX XX"
        )
        return config.STATES['REGISTER_PHONE']

    async def register_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        phone = update.message.text

        if not validate_phone(phone):
            await update.message.reply_text(
                "❌ Неверный формат телефона. Попробуйте еще раз:"
            )
            return config.STATES['REGISTER_PHONE']

        formatted_phone = format_phone(phone)
        context.user_data['phone'] = formatted_phone

        # Регистрируем пользователя
        self.db.register_user(
            telegram_id=update.effective_user.id,
            first_name=context.user_data['first_name'],
            last_name=context.user_data['last_name'],
            phone=formatted_phone
        )

        await update.message.reply_text(
            "✅ Регистрация завершена!\n"
            "Теперь вы можете добавить абонемент и начать отслеживать тренировки.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )

    async def show_workouts_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Меню тренировок:",
            reply_markup=get_workouts_menu()
        )

    async def show_subscriptions_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Меню абонементов:",
            reply_markup=get_subscriptions_menu()
        )

    async def show_profile_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Меню профиля:",
            reply_markup=get_profile_menu()
        )

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        subscription = self.db.get_active_subscription(user['id'])

        if subscription:
            message = (
                f"💰 <b>Ваш абонемент</b>\n"
                f"Номер: {subscription['subscription_number']}\n"
                f"Начальная сумма: {format_amount(subscription['initial_amount'])}\n"
                f"Текущий баланс: <b>{format_amount(subscription['current_balance'])}</b>\n"
                f"Дата начала: {format_date(subscription['start_date'])}"
            )
        else:
            message = (
                "❌ У вас нет активного абонемента.\n"
                "Добавьте новый абонемент через меню."
            )

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    async def new_subscription_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        if self.db.get_active_subscription(user['id']):
            await update.message.reply_text(
                "❌ У вас уже есть активный абонемент.\n"
                "Чтобы завести новый, сначала нужно закрыть текущий.",
                reply_markup=get_subscriptions_menu()
            )
            return ConversationHandler.END

        await update.message.reply_text(
            "Введите номер нового абонемента:",
            reply_markup=ReplyKeyboardRemove()
        )
        return config.STATES['NEW_SUBSCRIPTION_NUMBER']

    async def new_subscription_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['subscription_number'] = update.message.text
        await update.message.reply_text("Введите сумму на абонементе:")
        return config.STATES['NEW_SUBSCRIPTION_AMOUNT']

    async def new_subscription_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = float(update.message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError

            user = self.db.get_user(update.effective_user.id)
            self.db.create_subscription(
                user_id=user['id'],
                subscription_number=context.user_data['subscription_number'],
                initial_amount=amount
            )

            await update.message.reply_text(
                f"✅ Абонемент успешно создан!\n"
                f"Номер: {context.user_data['subscription_number']}\n"
                f"Сумма: {format_amount(amount)}",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Введите корректную сумму:")
            return config.STATES['NEW_SUBSCRIPTION_AMOUNT']

    async def close_subscription_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        subscription = self.db.get_active_subscription(user['id'])

        if not subscription:
            await update.message.reply_text("❌ У вас нет активного абонемента.", reply_markup=get_main_menu())
            return ConversationHandler.END

        if subscription['current_balance'] != 0:
            await update.message.reply_text(
                f"❌ Нельзя закрыть абонемент с ненулевым балансом.\n"
                f"Текущий баланс: {format_amount(subscription['current_balance'])}",
                reply_markup=get_subscriptions_menu()
            )
            return ConversationHandler.END

        await update.message.reply_text(
            "Вы уверены, что хотите закрыть текущий абонемент?\n"
            "Это действие нельзя будет отменить.",
            reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True)
        )
        return config.STATES['CLOSE_SUBSCRIPTION_CONFIRM']

    async def close_subscription_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text == 'Да':
            user = self.db.get_user(update.effective_user.id)
            subscription = self.db.get_active_subscription(user['id'])
            self.db.close_subscription(subscription['id'])
            await update.message.reply_text(
                "✅ Абонемент успешно закрыт.",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "Действие отменено.",
                reply_markup=get_subscriptions_menu()
            )
        return ConversationHandler.END

    async def top_up_subscription_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        if not self.db.get_active_subscription(user['id']):
            await update.message.reply_text("❌ У вас нет активного абонемента.", reply_markup=get_main_menu())
            return ConversationHandler.END

        await update.message.reply_text(
            "Введите сумму для пополнения:",
            reply_markup=ReplyKeyboardRemove()
        )
        return config.STATES['TOP_UP_AMOUNT']

    async def top_up_subscription_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = float(update.message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError

            user = self.db.get_user(update.effective_user.id)
            subscription = self.db.get_active_subscription(user['id'])
            self.db.top_up_subscription(subscription['id'], amount)

            await update.message.reply_text(
                f"✅ Баланс абонемента пополнен на {format_amount(amount)}.",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Введите корректную сумму:")
            return config.STATES['TOP_UP_AMOUNT']

    async def show_archived_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        subscriptions = self.db.get_archived_subscriptions(user['id'])

        if not subscriptions:
            await update.message.reply_text("У вас нет закрытых абонементов.", reply_markup=get_subscriptions_menu())
            return

        message = "🗂️ <b>Архив абонементов:</b>\n\n"
        for sub in subscriptions:
            message += (
                f"<b>Номер: {sub['subscription_number']}</b>\n"
                f"Дата: {format_date(sub['start_date'])} - {format_date(sub['end_date'])}\n"
                f"Начальная сумма: {format_amount(sub['initial_amount'])}\n\n"
            )

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_subscriptions_menu())

    async def show_expenses_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Выберите период для просмотра расходов:",
            reply_markup=get_stats_period_keyboard()
        )
        return config.STATES['EXPENSES_PERIOD']

    async def show_expenses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        period_text = update.message.text
        if period_text == '❌ Отмена':
            await update.message.reply_text("Отменено", reply_markup=get_subscriptions_menu())
            return ConversationHandler.END

        period_map = {
            '📅 За неделю': 'week',
            '📅 За месяц': 'month',
            '📅 За год': 'year',
            '📅 За все время': 'all'
        }
        period = period_map.get(period_text, 'month')
        user = self.db.get_user(update.effective_user.id)
        
        transactions = self.db.get_transactions(user['id'], period)

        if not transactions:
            await update.message.reply_text(f"За {get_period_name(period)} не было расходов.", reply_markup=get_subscriptions_menu())
            return

        message = f"📊 <b>Расходы за {get_period_name(period)}:</b>\n\n"
        total_spent = 0
        for trans in transactions:
            if trans['type'] == 'expense':
                total_spent += trans['amount']
                message += (
                    f"📅 {format_date(trans['date'])}: -{format_amount(trans['amount'])}\n"
                    f"   <i>Тренировка</i>\n"
                )
        
        message += f"\n<b>Итого потрачено: {format_amount(total_spent)}</b>"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_subscriptions_menu())
        return ConversationHandler.END

    async def edit_profile_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Эта функция находится в разработке.", reply_markup=get_profile_menu())

    async def add_training_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        subscription = self.db.get_active_subscription(user['id'])

        if not subscription:
            await update.message.reply_text(
                "❌ У вас нет активного абонемента.\n"
                "Сначала добавьте абонемент через меню.",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

        await update.message.reply_text(
            "Выберите продолжительность тренировки:",
            reply_markup=get_duration_keyboard()
        )
        return config.STATES['TRAINING_DURATION']


    async def training_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        duration_text = update.message.text
        if duration_text == '❌ Отмена':
            await update.message.reply_text("Отменено", reply_markup=get_main_menu())
            return ConversationHandler.END

        duration = int(duration_text.split()[0])
        context.user_data['duration'] = duration

        await update.message.reply_text(
            "Сколько человек было на тренировке?",
            reply_markup=get_participants_keyboard()
        )
        return config.STATES['TRAINING_PARTICIPANTS']

    async def training_participants(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        participants_text = update.message.text
        if participants_text == '❌ Отмена':
            await update.message.reply_text("Отменено", reply_markup=get_main_menu())
            return ConversationHandler.END

        participants = int(participants_text.split()[0])
        context.user_data['participants'] = participants

        # Показываем стоимость
        price = self.db.get_price(context.user_data['duration'], participants)
        if price:
            context.user_data['price'] = price
            await update.message.reply_text(
                f"Стоимость тренировки: {format_amount(price)}\n"
                f"Выберите тип покрытия корта:",
                reply_markup=get_court_type_keyboard()
            )
            return config.STATES['TRAINING_COURT']
        else:
            await update.message.reply_text(
                "❌ Не удалось определить стоимость тренировки.\n"
                "Попробуйте еще раз.",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

    async def training_court(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        court_type = update.message.text
        if court_type == 'Пропустить':
            court_type = None
        context.user_data['court_type'] = court_type

        await update.message.reply_text(
            "Введите имя тренера или нажмите 'Пропустить':",
            reply_markup=get_coach_keyboard()
        )
        return config.STATES['TRAINING_COACH']

    async def training_coach(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        coach = update.message.text
        if coach.lower() == 'пропустить':
            coach = None

        user = self.db.get_user(update.effective_user.id)
        subscription = self.db.get_active_subscription(user['id'])

        try:
            self.db.add_training_session(
                user_id=user['id'],
                subscription_id=subscription['id'],
                duration=context.user_data['duration'],
                participants=context.user_data['participants'],
                court_type=context.user_data['court_type'],
                coach=coach
            )

            # Получаем обновленный баланс
            updated_subscription = self.db.get_active_subscription(user['id'])
            new_balance = updated_subscription['current_balance'] if updated_subscription else 0

            message = (
                f"✅ Тренировка добавлена!\n"
                f"Продолжительность: {context.user_data['duration']} мин\n"
                f"Участников: {context.user_data['participants']}\n"
                f"Стоимость: {format_amount(context.user_data['price'])}\n"
                f"Тип корта: {context.user_data['court_type'] or 'Не указан'}\n"
                f"Тренер: {coach or 'Не указан'}\n"
                f"Новый баланс: {format_amount(new_balance)}"
            )

        except ValueError as e:
            message = f"❌ Ошибка: {str(e)}"

        await update.message.reply_text(message, reply_markup=get_main_menu())
        return ConversationHandler.END

    async def show_stats_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Выберите период для статистики:",
            reply_markup=get_stats_period_keyboard()
        )
        return config.STATES['STATS_PERIOD']

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        period_text = update.message.text
        if period_text == '❌ Отмена':
            await update.message.reply_text("Отменено", reply_markup=get_main_menu())
            return ConversationHandler.END

        period_map = {
            '📅 За неделю': 'week',
            '📅 За месяц': 'month',
            '📅 За год': 'year',
            '📅 За все время': 'all'
        }

        period = period_map.get(period_text, 'month')
        user = self.db.get_user(update.effective_user.id)

        # Получаем статистику
        spent_amount = self.db.get_spent_amount(user['id'], period)
        training_count = self.db.get_training_count(user['id'], period)

        # Статистика по типам тренировок
        individual = self.db.get_training_count(user['id'], period, 1)
        pair = self.db.get_training_count(user['id'], period, 2)
        group_3 = self.db.get_training_count(user['id'], period, 3)
        group_4 = self.db.get_training_count(user['id'], period, 4)

        message = (
            f"📊 <b>Статистика за {get_period_name(period)}</b>\n\n"
            f"💰 Потрачено: <b>{format_amount(spent_amount)}</b>\n"
            f"🎾 Всего тренировок: <b>{training_count}</b>\n\n"
            f"<b>По типам тренировок:</b>\n"
            f"• Индивидуальные: {individual}\n"
            f"• Вдвоем: {pair}\n"
            f"• Втроем: {group_3}\n"
            f"• Вчетвером: {group_4}"
        )

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return ConversationHandler.END

    async def show_training_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        trainings = self.db.get_user_trainings(user['id'], limit=10)

        if not trainings:
            await update.message.reply_text("У вас еще нет тренировок.")
            return

        message = "📋 <b>Последние тренировки:</b>\n\n"
        for training in trainings:
            message += (
                f"📅 {format_date(training['session_date'])}\n"
                f"   ⏱ {training['duration_minutes']} мин"
                f" | 👥 {training['participants_count']} чел."
                f" | 💰 {format_amount(training['amount_paid'])}\n"
            )
            if training['court_type'] or training['coach_name']:
                message += f"   🎾 {training['court_type'] or ''}"
                if training['coach_name']:
                    message += f" | 👨‍🏫 {training['coach_name']}"
                message += "\n"
            message += "\n"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)

        if user is None:
            await update.message.reply_text(
                "Ваш профиль не найден. Пожалуйста, зарегистрируйтесь, используя команду /start."
            )
            return

        subscription = self.db.get_active_subscription(user['id'])
        total_trainings = self.db.get_training_count(user['id'], 'all')

        message = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"Имя: {user['first_name']} {user['last_name'] or ''}\n"
            f"Телефон: {user['phone'] or 'Не указан'}\n"
            f"Дата регистрации: {format_date(user['registration_date'])}\n\n"
            f"🎾 Всего тренировок: <b>{total_trainings}</b>\n"
        )

        if subscription:
            message += (
                f"💰 Активный абонемент: {subscription['subscription_number']}\n"
                f"Баланс: {format_amount(subscription['current_balance'])}"
            )
        else:
            message += "❌ Нет активного абонемента"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Неизвестная команда. Используйте меню для навигации.",
            reply_markup=get_main_menu()
        )
