from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
import logging
from database import Database
from keyboards import *
from utils import *
from config import RegisterStates, SubscriptionStates, TrainingStates, StatsStates

logger = logging.getLogger(__name__)


class Handlers:
    def __init__(self, db: Database):
        self.db = db
        self.logger = logging.getLogger('bot.handlers')

    @log_command
    async def start(self, message: types.Message, state: FSMContext):
        """Команда /start - начало работы или главное меню"""
        user_id = message.from_user.id
        self.logger.info(f"Start command from user {user_id} ({message.from_user.username})")

        if self.db.user_exists(user_id):
            await message.answer(
                f"С возвращением, {message.from_user.first_name}! 🎾\n"
                "Выберите действие в меню:",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "Добро пожаловать в Tennis Club Bot! 🎾\n"
                "Для регистрации введите ваше имя:"
            )
            await state.set_state(RegisterStates.first_name)

    async def register_first_name(self, message: types.Message, state: FSMContext):
        """Ввод имени при регистрации"""
        first_name = message.text
        self.logger.info(f"User {message.from_user.id} entered first name: {first_name}")
        await state.update_data(first_name=first_name)
        await message.answer("Отлично! Теперь введите вашу фамилию:")
        await state.set_state(RegisterStates.last_name)

    async def register_last_name(self, message: types.Message, state: FSMContext):
        """Ввод фамилии при регистрации"""
        last_name = message.text
        await state.update_data(last_name=last_name)
        await message.answer(
            "Введите ваш номер телефона:\n"
            "Формат: +7 XXX XXX XX XX или 8 XXX XXX XX XX"
        )
        await state.set_state(RegisterStates.phone)

    async def register_phone(self, message: types.Message, state: FSMContext):
        """Ввод телефона при регистрации"""
        phone = message.text

        if not validate_phone(phone):
            await message.answer(
                "❌ Неверный формат телефона. Попробуйте еще раз:"
            )
            return

        formatted_phone = format_phone(phone)
        user_data = await state.get_data()

        # Регистрируем пользователя
        self.db.register_user(
            telegram_id=message.from_user.id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=formatted_phone
        )

        await message.answer(
            "✅ Регистрация завершена!\n"
            "Теперь вы можете добавить абонемент и начать отслеживать тренировки.",
            reply_markup=get_main_menu()
        )
        await state.clear()

    async def show_balance(self, message: types.Message):
        """Показать баланс абонемента"""
        user = self.db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        subscription = self.db.get_active_subscription(user['id'])

        if subscription:
            message_text = (
                f"💰 <b>Ваш абонемент</b>\n"
                f"Номер: {subscription['subscription_number']}\n"
                f"Начальная сумма: {format_amount(subscription['initial_amount'])}\n"
                f"Текущий баланс: <b>{format_amount(subscription['current_balance'])}</b>\n"
                f"Дата начала: {format_date(subscription['start_date'])}"
            )
        else:
            message_text = (
                "❌ У вас нет активного абонемента.\n"
                "Добавьте новый абонемент через меню."
            )

        await message.answer(message_text, parse_mode=ParseMode.HTML)

    async def new_subscription_start(self, message: types.Message, state: FSMContext):
        """Начало создания нового абонемента"""
        await message.answer(
            "Введите номер нового абонемента:",
            reply_markup=remove_keyboard()
        )
        await state.set_state(SubscriptionStates.number)

    async def new_subscription_number(self, message: types.Message, state: FSMContext):
        """Ввод номера абонемента"""
        subscription_number = message.text
        await state.update_data(subscription_number=subscription_number)
        await message.answer("Введите сумму на абонементе:")
        await state.set_state(SubscriptionStates.amount)

    async def new_subscription_amount(self, message: types.Message, state: FSMContext):
        """Ввод суммы абонемента"""
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError("Сумма должна быть больше нуля")

            user = self.db.get_user(message.from_user.id)
            user_data = await state.get_data()

            subscription_id = self.db.create_subscription(
                user_id=user['id'],
                subscription_number=user_data['subscription_number'],
                initial_amount=amount
            )

            await message.answer(
                f"✅ Абонемент успешно создан!\n"
                f"Номер: {user_data['subscription_number']}\n"
                f"Сумма: {format_amount(amount)}",
                reply_markup=get_main_menu()
            )
            await state.clear()

        except ValueError as e:
            await message.answer(f"❌ Введите корректную сумму: {str(e)}")

    async def add_training_start(self, message: types.Message, state: FSMContext):
        """Начало добавления тренировки"""
        user = self.db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        subscription = self.db.get_active_subscription(user['id'])

        if not subscription:
            await message.answer(
                "❌ У вас нет активного абонемента.\n"
                "Сначала добавьте абонемент через меню.",
                reply_markup=get_main_menu()
            )
            return

        await message.answer(
            "Выберите продолжительность тренировки:",
            reply_markup=get_duration_keyboard()
        )
        await state.set_state(TrainingStates.duration)

    async def training_duration(self, message: types.Message, state: FSMContext):
        """Выбор продолжительности тренировки"""
        duration_text = message.text
        if duration_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_main_menu())
            await state.clear()
            return

        duration = int(duration_text.split()[0])
        await state.update_data(duration=duration)

        await message.answer(
            "Сколько человек было на тренировке?",
            reply_markup=get_participants_keyboard()
        )
        await state.set_state(TrainingStates.participants)

    async def training_participants(self, message: types.Message, state: FSMContext):
        """Выбор количества участников"""
        participants_text = message.text
        if participants_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_main_menu())
            await state.clear()
            return

        participants = int(participants_text.split()[0])
        training_data = await state.get_data()

        # Показываем стоимость
        price = self.db.get_price(training_data['duration'], participants)
        if price:
            await state.update_data(participants=participants, price=price)
            await message.answer(
                f"Стоимость тренировки: {format_amount(price)}\n"
                f"Выберите тип покрытия корта:",
                reply_markup=get_court_type_keyboard()
            )
            await state.set_state(TrainingStates.court)
        else:
            await message.answer(
                "❌ Не удалось определить стоимость тренировки.\n"
                "Попробуйте еще раз.",
                reply_markup=get_main_menu()
            )
            await state.clear()

    async def training_court(self, message: types.Message, state: FSMContext):
        """Выбор типа корта"""
        court_type = message.text
        if court_type == 'Пропустить':
            court_type = None
        await state.update_data(court_type=court_type)

        await message.answer(
            "Введите имя тренера (или нажмите 'Пропустить'):",
            reply_markup=get_coach_keyboard()
        )
        await state.set_state(TrainingStates.coach)

    async def training_coach(self, message: types.Message, state: FSMContext):
        """Ввод имени тренера"""
        coach = message.text
        if coach.lower() == 'пропустить':
            coach = None

        user = self.db.get_user(message.from_user.id)
        subscription = self.db.get_active_subscription(user['id'])
        training_data = await state.get_data()

        try:
            training_id = self.db.add_training_session(
                user_id=user['id'],
                subscription_id=subscription['id'],
                duration=training_data['duration'],
                participants=training_data['participants'],
                court_type=training_data['court_type'],
                coach=coach
            )

            # Получаем обновленный баланс
            updated_subscription = self.db.get_active_subscription(user['id'])

            message_text = (
                f"✅ Тренировка добавлена!\n"
                f"Продолжительность: {training_data['duration']} мин\n"
                f"Участников: {training_data['participants']}\n"
                f"Стоимость: {format_amount(training_data['price'])}\n"
                f"Тип корта: {training_data['court_type'] or 'Не указан'}\n"
                f"Тренер: {coach or 'Не указан'}\n"
                f"Баланс: {format_amount(updated_subscription['current_balance'])}"
            )

        except ValueError as e:
            message_text = f"❌ Ошибка: {str(e)}"

        await message.answer(message_text, reply_markup=get_main_menu())
        await state.clear()

    async def show_stats_start(self, message: types.Message, state: FSMContext):
        """Начало просмотра статистики"""
        await message.answer(
            "Выберите период для статистики:",
            reply_markup=get_stats_period_keyboard()
        )
        await state.set_state(StatsStates.period)

    async def show_stats(self, message: types.Message, state: FSMContext):
        """Показать статистику за выбранный период"""
        period_text = message.text
        if period_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_main_menu())
            await state.clear()
            return

        period_map = {
            '📅 За неделю': 'week',
            '📅 За месяц': 'month',
            '📅 За год': 'year',
            '📅 За все время': 'all'
        }

        period = period_map.get(period_text, 'month')
        user = self.db.get_user(message.from_user.id)

        # Получаем статистику
        spent_amount = self.db.get_spent_amount(user['id'], period)
        training_count = self.db.get_training_count(user['id'], period)

        # Статистика по типам тренировок
        individual = self.db.get_training_count(user['id'], period, 1)
        pair = self.db.get_training_count(user['id'], period, 2)
        group_3 = self.db.get_training_count(user['id'], period, 3)
        group_4 = self.db.get_training_count(user['id'], period, 4)

        message_text = (
            f"📊 <b>Статистика за {get_period_name(period)}</b>\n\n"
            f"💰 Потрачено: <b>{format_amount(spent_amount)}</b>\n"
            f"🎾 Всего тренировок: <b>{training_count}</b>\n\n"
            f"<b>По типам тренировок:</b>\n"
            f"• Индивидуальные: {individual}\n"
            f"• Вдвоем: {pair}\n"
            f"• Втроем: {group_3}\n"
            f"• Вчетвером: {group_4}"
        )

        await message.answer(message_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        await state.clear()

    async def show_training_history(self, message: types.Message):
        """Показать историю тренировок"""
        user = self.db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        trainings = self.db.get_user_trainings(user['id'], limit=10)

        if not trainings:
            await message.answer("У вас еще нет тренировок.")
            return

        message_text = "📋 <b>Последние тренировки:</b>\n\n"
        for training in trainings:
            message_text += (
                f"📅 {format_date(training['session_date'])}\n"
                f"   ⏱ {training['duration_minutes']} мин"
                f" | 👥 {training['participants_count']} чел."
                f" | 💰 {format_amount(training['amount_paid'])}\n"
            )
            if training['court_type'] or training['coach_name']:
                message_text += f"   🎾 {training['court_type'] or ''}"
                if training['coach_name']:
                    message_text += f" | 👨‍🏫 {training['coach_name']}"
                message_text += "\n"
            message_text += "\n"

        await message.answer(message_text, parse_mode=ParseMode.HTML)

    async def show_profile(self, message: types.Message):
        """Показать профиль пользователя"""
        user = self.db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        subscription = self.db.get_active_subscription(user['id'])
        total_trainings = self.db.get_training_count(user['id'], 'all')

        message_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"Имя: {user['first_name']} {user['last_name'] or ''}\n"
            f"Телефон: {user['phone'] or 'Не указан'}\n"
            f"Дата регистрации: {format_date(user['registration_date'])}\n\n"
            f"🎾 Всего тренировок: <b>{total_trainings}</b>\n"
        )

        if subscription:
            message_text += (
                f"💰 Активный абонемент: {subscription['subscription_number']}\n"
                f"Баланс: {format_amount(subscription['current_balance'])}"
            )
        else:
            message_text += "❌ Нет активного абонемента"

        await message.answer(message_text, parse_mode=ParseMode.HTML)

    async def cancel(self, message: types.Message, state: FSMContext):
        """Отмена операции"""
        await message.answer(
            "Действие отменено.",
            reply_markup=get_main_menu()
        )
        await state.clear()

    async def unknown_command(self, message: types.Message):
        """Неизвестная команда"""
        await message.answer(
            "Неизвестная команда. Используйте меню для навигации.",
            reply_markup=get_main_menu()
        )
