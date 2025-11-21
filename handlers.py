import logging
from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode

from database import Database
from keyboards import *
from utils import *
from config import (
    RegistrationStates, NewSubscriptionStates, AddTrainingStates, StatsStates,
    CloseSubscriptionStates, TopUpStates, ExpensesStates, EditProfileStates
)

logger = logging.getLogger(__name__)

router = Router()


class Handlers:
    def __init__(self, db: Database):
        self.db = db
        self.logger = logging.getLogger('bot.handlers')

    @log_command
    async def start(self, message: Message, state: FSMContext):
        user = message.from_user
        self.logger.info(f"Start command from user {user.id} ({user.username})")
        telegram_id = user.id

        if self.db.user_exists(telegram_id):
            await message.answer(
                f"С возвращением, {user.first_name}! 🎾\n"
                "Выберите действие в меню:",
                reply_markup=get_main_menu()
            )
            await state.clear()
        else:
            await message.answer(
                "Добро пожаловать в Tennis Bot! 🎾\n"
                "Для регистрации введите ваше имя:"
            )
            await state.set_state(RegistrationStates.REGISTER_FIRST_NAME)

    @log_command
    async def register_first_name(self, message: Message, state: FSMContext):
        first_name = message.text
        user = message.from_user
        self.logger.info(f"User {user.id} entered first name: {first_name}")
        await state.update_data(first_name=first_name)
        await message.answer("Отлично! Теперь введите вашу фамилию:")
        await state.set_state(RegistrationStates.REGISTER_LAST_NAME)

    async def register_last_name(self, message: Message, state: FSMContext):
        await state.update_data(last_name=message.text)
        await message.answer(
            "Введите ваш номер телефона:\n"
            "Формат: +7 XXX XXX XX XX или 8 XXX XXX XX XX"
        )
        await state.set_state(RegistrationStates.REGISTER_PHONE)

    async def register_phone(self, message: Message, state: FSMContext):
        phone = message.text

        if not validate_phone(phone):
            await message.answer(
                "❌ Неверный формат телефона. Попробуйте еще раз:"
            )
            await state.set_state(RegistrationStates.REGISTER_PHONE)
            return

        formatted_phone = format_phone(phone)
        user_data = await state.get_data()

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

    async def main_menu(self, message: Message, state: FSMContext):
        await message.answer("Главное меню:", reply_markup=get_main_menu())

    async def show_workouts_menu(self, message: Message, state: FSMContext):
        await message.answer("Меню тренировок:", reply_markup=get_workouts_menu())

    async def show_subscriptions_menu(self, message: Message, state: FSMContext):
        await message.answer("Меню абонементов:", reply_markup=get_subscriptions_menu())

    async def show_profile_menu(self, message: Message, state: FSMContext):
        await message.answer("Меню профиля:", reply_markup=get_profile_menu())

    async def back_to_main_menu(self, message: Message, state: FSMContext):
        await message.answer("Главное меню:", reply_markup=get_main_menu())

    async def show_balance(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        subscription = self.db.get_active_subscription(user.id)

        if subscription:
            text = (
                f"💰 <b>Ваш абонемент</b>\n"
                f"Номер: {subscription.subscription_number}\n"
                f"Начальная сумма: {format_amount(subscription.initial_amount)}\n"
                f"Текущий баланс: <b>{format_amount(subscription.current_balance)}</b>\n"
                f"Дата начала: {format_date(subscription.start_date)}"
            )
        else:
            text = (
                "❌ У вас нет активного абонемента.\n"
                "Добавьте новый абонемент через меню."
            )
        await message.answer(text, parse_mode=ParseMode.HTML)

    async def new_subscription_start(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        if self.db.get_active_subscription(user.id):
            await message.answer(
                "❌ У вас уже есть активный абонемент.\n"
                "Чтобы завести новый, сначала нужно закрыть текущий.",
                reply_markup=get_subscriptions_menu()
            )
            await state.clear()
            return

        await message.answer("Введите номер нового абонемента:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(NewSubscriptionStates.NEW_SUBSCRIPTION_NUMBER)

    async def new_subscription_number(self, message: Message, state: FSMContext):
        await state.update_data(subscription_number=message.text)
        await message.answer("Введите сумму на абонементе:")
        await state.set_state(NewSubscriptionStates.NEW_SUBSCRIPTION_AMOUNT)

    async def new_subscription_amount(self, message: Message, state: FSMContext):
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError

            user = self.db.get_user(message.from_user.id)
            user_data = await state.get_data()
            self.db.create_subscription(
                user_id=user.id,
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

        except ValueError:
            await message.answer("❌ Введите корректную сумму:")
            await state.set_state(NewSubscriptionStates.NEW_SUBSCRIPTION_AMOUNT)

    async def close_subscription_start(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        subscription = self.db.get_active_subscription(user.id)

        if not subscription:
            await message.answer("❌ У вас нет активного абонемента.", reply_markup=get_main_menu())
            await state.clear()
            return

        if subscription.current_balance != 0:
            await message.answer(
                f"❌ Нельзя закрыть абонемент с ненулевым балансом.\n"
                f"Текущий баланс: {format_amount(subscription.current_balance)}",
                reply_markup=get_subscriptions_menu()
            )
            await state.clear()
            return

        await message.answer(
            "Вы уверены, что хотите закрыть текущий абонемент?\n"
            "Это действие нельзя будет отменить.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Да'), KeyboardButton(text='Нет')]], resize_keyboard=True)
        )
        await state.set_state(CloseSubscriptionStates.CLOSE_SUBSCRIPTION_CONFIRM)

    async def close_subscription_confirm(self, message: Message, state: FSMContext):
        if message.text == 'Да':
            user = self.db.get_user(message.from_user.id)
            subscription = self.db.get_active_subscription(user.id)
            self.db.close_subscription(subscription.id)
            await message.answer("✅ Абонемент успешно закрыт.", reply_markup=get_main_menu())
        else:
            await message.answer("Действие отменено.", reply_markup=get_subscriptions_menu())
        await state.clear()

    async def top_up_subscription_start(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        if not self.db.get_active_subscription(user.id):
            await message.answer("❌ У вас нет активного абонемента.", reply_markup=get_main_menu())
            await state.clear()
            return

        await message.answer("Введите сумму для пополнения:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TopUpStates.TOP_UP_AMOUNT)

    async def top_up_subscription_amount(self, message: Message, state: FSMContext):
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError

            user = self.db.get_user(message.from_user.id)
            subscription = self.db.get_active_subscription(user.id)
            self.db.top_up_subscription(subscription.id, amount)

            await message.answer(
                f"✅ Баланс абонемента пополнен на {format_amount(amount)}.",
                reply_markup=get_main_menu()
            )
            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректную сумму:")
            await state.set_state(TopUpStates.TOP_UP_AMOUNT)

    async def show_archived_subscriptions(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        subscriptions = self.db.get_archived_subscriptions(user.id)

        if not subscriptions:
            await message.answer("У вас нет закрытых абонементов.", reply_markup=get_subscriptions_menu())
            return

        text = "🗂️ <b>Архив абонементов:</b>\n\n"
        for sub in subscriptions:
            text += (
                f"<b>Номер: {sub.subscription_number}</b>\n"
                f"Дата: {format_date(sub.start_date)} - {format_date(sub.end_date)}\n"
                f"Начальная сумма: {format_amount(sub.initial_amount)}\n\n"
            )

        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_subscriptions_menu())

    async def show_expenses_start(self, message: Message, state: FSMContext):
        await message.answer("Выберите период для просмотра расходов:", reply_markup=get_stats_period_keyboard())
        await state.set_state(ExpensesStates.EXPENSES_PERIOD)

    async def show_expenses(self, message: Message, state: FSMContext):
        period_text = message.text
        if period_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_subscriptions_menu())
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

        transactions = self.db.get_transactions(user.id, period)

        if not transactions:
            await message.answer(f"За {get_period_name(period)} не было расходов.", reply_markup=get_subscriptions_menu())
            return

        text = f"📊 <b>Расходы за {get_period_name(period)}:</b>\n\n"
        total_spent = 0
        for trans in transactions:
            if trans.type == 'expense':
                total_spent += trans.amount
                text += (
                    f"📅 {format_date(trans.date)}: -{format_amount(trans.amount)}\n"
                    f"   <i>Тренировка</i>\n"
                )

        text += f"\n<b>Итого потрачено: {format_amount(total_spent)}</b>"

        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_subscriptions_menu())
        await state.clear()

    async def add_training_start(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        # Добавьте проверку на существование пользователя
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы в системе.\n"
                "Пожалуйста, начните с команды /start",
                reply_markup=get_main_menu()
            )
            await state.clear()
            return

        subscription = self.db.get_active_subscription(user.id)

        if not subscription:
            await message.answer(
                "❌ У вас нет активного абонемента.\n"
                "Сначала добавьте абонемент через меню.",
                reply_markup=get_main_menu()
            )
            await state.clear()
            return

        await message.answer("Выберите продолжительность тренировки:", reply_markup=get_duration_keyboard())
        await state.set_state(AddTrainingStates.TRAINING_DURATION)

    async def training_duration(self, message: Message, state: FSMContext):
        duration_text = message.text
        if duration_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_main_menu())
            await state.clear()
            return

        duration = int(duration_text.split()[0])
        await state.update_data(duration=duration)

        await message.answer("Сколько человек было на тренировке?", reply_markup=get_participants_keyboard())
        await state.set_state(AddTrainingStates.TRAINING_PARTICIPANTS)

    async def training_participants(self, message: Message, state: FSMContext):
        participants_text = message.text
        if participants_text == '❌ Отмена':
            await message.answer("Отменено", reply_markup=get_main_menu())
            await state.clear()
            return

        participants = int(participants_text.split()[0])
        user_data = await state.get_data()
        price = self.db.get_price(user_data['duration'], participants)

        if price:
            await state.update_data(participants=participants, price=price)
            await message.answer(
                f"Стоимость тренировки: {format_amount(price)}\n"
                f"Выберите тип покрытия корта:",
                reply_markup=get_court_type_keyboard()
            )
            await state.set_state(AddTrainingStates.TRAINING_COURT)
        else:
            await message.answer(
                "❌ Не удалось определить стоимость тренировки.\n"
                "Попробуйте еще раз.",
                reply_markup=get_main_menu()
            )
            await state.clear()

    async def training_court(self, message: Message, state: FSMContext):
        court_type = message.text
        if court_type == 'Пропустить':
            court_type = None
        await state.update_data(court_type=court_type)

        await message.answer(
            "Введите имя тренера или нажмите 'Пропустить':",
            reply_markup=get_coach_keyboard()
        )
        await state.set_state(AddTrainingStates.TRAINING_COACH)

    async def training_coach(self, message: Message, state: FSMContext):
        coach = message.text
        if coach.lower() == 'пропустить':
            coach = None

        user = self.db.get_user(message.from_user.id)
        subscription = self.db.get_active_subscription(user.id)
        user_data = await state.get_data()

        try:
            self.db.add_training_session(
                user_id=user.id,
                subscription_id=subscription.id,
                duration=user_data['duration'],
                participants=user_data['participants'],
                court_type=user_data['court_type'],
                coach=coach
            )

            updated_subscription = self.db.get_active_subscription(user.id)
            new_balance = updated_subscription.current_balance if updated_subscription else 0

            text = (
                f"✅ Тренировка добавлена!\n"
                f"Продолжительность: {user_data['duration']} мин\n"
                f"Участников: {user_data['participants']}\n"
                f"Стоимость: {format_amount(user_data['price'])}\n"
                f"Тип корта: {user_data['court_type'] or 'Не указан'}\n"
                f"Тренер: {coach or 'Не указан'}\n"
                f"Новый баланс: {format_amount(new_balance)}"
            )

        except ValueError as e:
            text = f"❌ Ошибка: {str(e)}"

        await message.answer(text, reply_markup=get_main_menu())
        await state.clear()

    async def show_stats_start(self, message: Message, state: FSMContext):
        await message.answer("Выберите период для статистики:", reply_markup=get_stats_period_keyboard())
        await state.set_state(StatsStates.STATS_PERIOD)

    async def show_stats(self, message: Message, state: FSMContext):
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

        spent_amount = self.db.get_spent_amount(user.id, period)
        training_count = self.db.get_training_count(user.id, period)
        individual = self.db.get_training_count(user.id, period, 1)
        pair = self.db.get_training_count(user.id, period, 2)
        group_3 = self.db.get_training_count(user.id, period, 3)
        group_4 = self.db.get_training_count(user.id, period, 4)

        text = (
            f"📊 <b>Статистика за {get_period_name(period)}</b>\n\n"
            f"💰 Потрачено: <b>{format_amount(spent_amount)}</b>\n"
            f"🎾 Всего тренировок: <b>{training_count}</b>\n\n"
            f"<b>По типам тренировок:</b>\n"
            f"• Индивидуальные: {individual}\n"
            f"• Вдвоем: {pair}\n"
            f"• Втроем: {group_3}\n"
            f"• Вчетвером: {group_4}"
        )

        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        await state.clear()

    async def show_training_history(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        trainings = self.db.get_user_trainings(user.id, limit=10)

        if not trainings:
            await message.answer("У вас еще нет тренировок.")
            return

        text = "📋 <b>Последние тренировки:</b>\n\n"
        for training in trainings:
            text += (
                f"📅 {format_date(training['session_date'])}\n"
                f"   ⏱ {training['duration_minutes']} мин"
                f" | 👥 {training['participants_count']} чел."
                f" | 💰 {format_amount(training['amount_paid'])}\n"
            )
            if training['court_type'] or training['coach_name']:
                text += f"   🎾 {training['court_type'] or ''}"
                if training['coach_name']:
                    text += f" | 👨‍🏫 {training['coach_name']}"
                text += "\n"
            text += "\n"

        await message.answer(text, parse_mode=ParseMode.HTML)

    async def show_profile(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)

        if user is None:
            await message.answer("Ваш профиль не найден. Пожалуйста, зарегистрируйтесь, используя команду /start.")
            return

        subscription = self.db.get_active_subscription(user.id)
        total_trainings = self.db.get_training_count(user.id, 'all')

        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"Имя: {user['first_name']} {user['last_name'] or ''}\n"
            f"Телефон: {user['phone'] or 'не указан'}\n"
            f"Дата регистрации: {format_date(user['registration_date'])}\n\n"
            f"Всего тренировок: <b>{total_trainings}</b>\n"
        )

        if subscription:
            text += (
                f"💳 Активный абонемент: {subscription.subscription_number}\n"
                f"Баланс: {format_amount(subscription.current_balance)}"
            )
        else:
            text += "У вас нет активного абонемента"

        await message.answer(text, parse_mode=ParseMode.HTML)

    async def edit_profile_start(self, message: Message, state: FSMContext):
        await message.answer("Выберите, что вы хотите сделать:", reply_markup=get_edit_profile_menu())
        await state.set_state(EditProfileStates.EDIT_PROFILE_CHOICE)

    async def edit_subscription_choice(self, message: Message, state: FSMContext):
        text = message.text
        if text == "Редактировать абонементы":
            await message.answer("Редактирование абонементов:", reply_markup=get_edit_subscription_menu())
            await state.set_state(EditProfileStates.EDIT_SUBSCRIPTION_CHOICE)
        else:
            await self.back_to_main_menu(message, state)

    async def add_old_sub_start(self, message: Message, state: FSMContext):
        await message.answer("Введите номер старого абонемента:", reply_markup=remove_keyboard())
        await state.set_state(EditProfileStates.ADD_OLD_SUB_NUMBER)

    async def add_old_sub_number(self, message: Message, state: FSMContext):
        await state.update_data(old_sub_number=message.text)
        await message.answer("Введите количество посещений:")
        await state.set_state(EditProfileStates.ADD_OLD_SUB_VISITS)

    async def add_old_sub_visits(self, message: Message, state: FSMContext):
        try:
            await state.update_data(old_sub_visits=int(message.text))
            await message.answer("Введите стоимость абонемента:")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_COST)
        except ValueError:
            await message.answer("Пожалуйста, введите число.")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_VISITS)

    async def add_old_sub_cost(self, message: Message, state: FSMContext):
        try:
            await state.update_data(old_sub_cost=float(message.text.replace(',', '.')))
            await message.answer("Введите дату начала в формате ГГГГ-ММ-ДД:")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_START_DATE)
        except ValueError:
            await message.answer("Пожалуйста, введите число.")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_COST)

    async def add_old_sub_start_date(self, message: Message, state: FSMContext):
        date_text = message.text
        if not validate_date(date_text):
            await message.answer("❌ Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД:")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_START_DATE)
            return

        await state.update_data(old_sub_start_date=date_text)
        await message.answer("Введите дату окончания в формате ГГГГ-ММ-ДД (или отправьте 'пропустить'):")
        await state.set_state(EditProfileStates.ADD_OLD_SUB_END_DATE)

    async def add_old_sub_end_date(self, message: Message, state: FSMContext):
        end_date = message.text
        if end_date.lower() == 'пропустить':
            end_date = None
        elif not validate_date(end_date):
            await message.answer("❌ Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД или 'пропустить':")
            await state.set_state(EditProfileStates.ADD_OLD_SUB_END_DATE)
            return

        user = self.db.get_user(message.from_user.id)
        user_data = await state.get_data()
        self.logger.info(f"old_sub_number {user_data}")
        self.db.add_old_subscription(
            user_id=user.id,
            subscription_number=user_data['old_sub_number'],
            initial_amount=user_data['old_sub_cost'],
            visits=user_data['old_sub_visits'],
            start_date=user_data['old_sub_start_date'],
            end_date=end_date
        )
        await message.answer("Старый абонемент успешно добавлен!", reply_markup=get_main_menu())
        await state.clear()

    async def edit_sub_select_start(self, message: Message, state: FSMContext):
        user = self.db.get_user(message.from_user.id)
        subscriptions = self.db.get_all_user_subscriptions(user.id)
        if not subscriptions:
            await message.answer("У вас нет абонементов для редактирования.", reply_markup=get_main_menu())
            await state.clear()
            return

        await message.answer(
            "Выберите абонемент для редактирования:",
            reply_markup=get_subscriptions_keyboard(subscriptions)
        )
        await state.set_state(EditProfileStates.EDIT_SUB_SELECT)

    async def edit_sub_select(self, message: Message, state: FSMContext):
        selected_sub_text = message.text
        sub_id = int(selected_sub_text.split('№')[1].split(' ')[0])
        await state.update_data(edit_sub_id=sub_id)
        await message.answer(
            "Что вы хотите отредактировать?",
            reply_markup=get_edit_subscription_field_menu()
        )
        await state.set_state(EditProfileStates.EDIT_SUB_FIELD)

    async def edit_sub_field(self, message: Message, state: FSMContext):
        field_map = {
            'Номер': 'subscription_number',
            'Стоимость': 'initial_amount',
            'Дата начала': 'start_date',
            'Дата окончания': 'end_date'
        }
        field_to_edit = message.text
        if field_to_edit not in field_map:
            await message.answer("Неверное поле. Попробуйте еще раз.", reply_markup=get_edit_subscription_field_menu())
            await state.set_state(EditProfileStates.EDIT_SUB_FIELD)
            return

        await state.update_data(edit_sub_field=field_map[field_to_edit])
        await message.answer(f"Введите новое значение для '{field_to_edit}':", reply_markup=remove_keyboard())
        await state.set_state(EditProfileStates.EDIT_SUB_NEW_VALUE)

    async def edit_sub_new_value(self, message: Message, state: FSMContext):
        new_value = message.text
        user_data = await state.get_data()
        sub_id = user_data['edit_sub_id']
        field = user_data['edit_sub_field']
        field_name_map = {
            'subscription_number': 'Номер',
            'initial_amount': 'Стоимость',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания'
        }
        field_name = field_name_map.get(field, field)

        if field in ['start_date', 'end_date']:
            if new_value.lower() != 'пропустить' and not validate_date(new_value):
                await message.answer(f"❌ Неверный формат даты для поля '{field_name}'. Введите дату в формате ГГГГ-ММ-ДД или 'пропустить':")
                await state.set_state(EditProfileStates.EDIT_SUB_NEW_VALUE)
                return
            if new_value.lower() == 'пропустить':
                new_value = None
        elif field == 'initial_amount':
            try:
                new_value = float(new_value.replace(',', '.'))
            except ValueError:
                await message.answer(f"❌ Поле '{field_name}' должно быть числом. Попробуйте еще раз:")
                await state.set_state(EditProfileStates.EDIT_SUB_NEW_VALUE)
                return

        try:
            self.db.update_subscription(sub_id, field, new_value)
            await message.answer("✅ Абонемент успешно обновлен!", reply_markup=get_main_menu())
            await state.clear()
        except Exception as e:
            self.logger.error(f"Failed to update subscription {sub_id} with field {field}: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при обновлении. Попробуйте позже.", reply_markup=get_main_menu())
            await state.clear()

    async def cancel(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_menu())

    async def unknown_command(self, message: Message, state: FSMContext):
        await message.answer("Неизвестная команда. Используйте меню для навигации.", reply_markup=get_main_menu())


def register_handlers(dp: Router, db: Database):
    handlers = Handlers(db)

    dp.message.register(handlers.start, Command("start"))
    dp.message.register(handlers.cancel, Command("cancel"))
    dp.message.register(handlers.cancel, F.text == '❌ Отмена')

    # Registration
    dp.message.register(handlers.register_first_name, RegistrationStates.REGISTER_FIRST_NAME)
    dp.message.register(handlers.register_last_name, RegistrationStates.REGISTER_LAST_NAME)
    dp.message.register(handlers.register_phone, RegistrationStates.REGISTER_PHONE)

    # Main Menu
    dp.message.register(handlers.show_workouts_menu, F.text == '💪 Тренировки')
    dp.message.register(handlers.show_subscriptions_menu, F.text == '💳 Абонементы')
    dp.message.register(handlers.show_profile_menu, F.text == '👤 Профиль')
    dp.message.register(handlers.back_to_main_menu, F.text == '🔙 Назад')

    # Workouts
    dp.message.register(handlers.add_training_start, F.text == '➕ Добавить тренировку')
    dp.message.register(handlers.training_duration, AddTrainingStates.TRAINING_DURATION)
    dp.message.register(handlers.training_participants, AddTrainingStates.TRAINING_PARTICIPANTS)
    dp.message.register(handlers.training_court, AddTrainingStates.TRAINING_COURT)
    dp.message.register(handlers.training_coach, AddTrainingStates.TRAINING_COACH)
    dp.message.register(handlers.show_stats_start, F.text == '📈 Статистика')
    dp.message.register(handlers.show_stats, StatsStates.STATS_PERIOD)
    dp.message.register(handlers.show_training_history, F.text == '📋 История тренировок')

    # Subscriptions
    dp.message.register(handlers.show_balance, F.text == '💰 Баланс')
    dp.message.register(handlers.new_subscription_start, F.text == '🔄 Новый абонемент')
    dp.message.register(handlers.new_subscription_number, NewSubscriptionStates.NEW_SUBSCRIPTION_NUMBER)
    dp.message.register(handlers.new_subscription_amount, NewSubscriptionStates.NEW_SUBSCRIPTION_AMOUNT)
    dp.message.register(handlers.show_archived_subscriptions, F.text == '🗂️ Архив')
    dp.message.register(handlers.top_up_subscription_start, F.text == '💸 Пополнить')
    dp.message.register(handlers.top_up_subscription_amount, TopUpStates.TOP_UP_AMOUNT)
    dp.message.register(handlers.show_expenses_start, F.text == '📊 Расходы')
    dp.message.register(handlers.show_expenses, ExpensesStates.EXPENSES_PERIOD)
    dp.message.register(handlers.close_subscription_start, F.text == '🚫 Закрыть абонемент')
    dp.message.register(handlers.close_subscription_confirm, CloseSubscriptionStates.CLOSE_SUBSCRIPTION_CONFIRM)

    # Profile
    dp.message.register(handlers.show_profile, F.text == 'ℹ️ Показать профиль')
    dp.message.register(handlers.edit_profile_start, F.text == '✏️ Редактировать профиль')
    dp.message.register(handlers.edit_subscription_choice, EditProfileStates.EDIT_PROFILE_CHOICE)
    dp.message.register(handlers.add_old_sub_start, EditProfileStates.EDIT_SUBSCRIPTION_CHOICE, F.text == 'Добавить старый абонемент')
    dp.message.register(handlers.add_old_sub_number, EditProfileStates.ADD_OLD_SUB_NUMBER)
    dp.message.register(handlers.add_old_sub_visits, EditProfileStates.ADD_OLD_SUB_VISITS)
    dp.message.register(handlers.add_old_sub_cost, EditProfileStates.ADD_OLD_SUB_COST)
    dp.message.register(handlers.add_old_sub_start_date, EditProfileStates.ADD_OLD_SUB_START_DATE)
    dp.message.register(handlers.add_old_sub_end_date, EditProfileStates.ADD_OLD_SUB_END_DATE)
    dp.message.register(handlers.edit_sub_select_start, EditProfileStates.EDIT_SUBSCRIPTION_CHOICE, F.text == 'Редактировать абонемент')
    dp.message.register(handlers.edit_sub_select, EditProfileStates.EDIT_SUB_SELECT)
    dp.message.register(handlers.edit_sub_field, EditProfileStates.EDIT_SUB_FIELD)
    dp.message.register(handlers.edit_sub_new_value, EditProfileStates.EDIT_SUB_NEW_VALUE)

    # Unknown
    dp.message.register(handlers.unknown_command, StateFilter(None))