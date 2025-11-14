from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu():
    keyboard = [
        [KeyboardButton(text='💪 Тренировки'), KeyboardButton(text='💳 Абонементы')],
        [KeyboardButton(text='👤 Профиль')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_workouts_menu():
    keyboard = [
        [KeyboardButton(text='➕ Добавить тренировку'), KeyboardButton(text='📈 Статистика')],
        [KeyboardButton(text='📋 История тренировок'), KeyboardButton(text='🔙 Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_subscriptions_menu():
    keyboard = [
        [KeyboardButton(text='💰 Баланс'), KeyboardButton(text='🔄 Новый абонеент')],
        [KeyboardButton(text='🗂️ Архив'), KeyboardButton(text='💸 Пополнить')],
        [KeyboardButton(text='📊 Расходы'), KeyboardButton(text='🚫 Закрыть абонемент')],
        [KeyboardButton(text='🔙 Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_profile_menu():
    keyboard = [
        [KeyboardButton(text='ℹ️ Показать профиль'), KeyboardButton(text='✏️ Редактировать профиль')],
        [KeyboardButton(text='🔙 Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_duration_keyboard():
    keyboard = [
        [KeyboardButton(text='60 минут'), KeyboardButton(text='90 минут')],
        [KeyboardButton(text='120 минут'), KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_participants_keyboard():
    keyboard = [
        [KeyboardButton(text='1 человек'), KeyboardButton(text='2 человека')],
        [KeyboardButton(text='3 человека'), KeyboardButton(text='4 человека')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_court_type_keyboard():
    keyboard = [
        [KeyboardButton(text='Крытый корт'), KeyboardButton(text='Открытый корт')],
        [KeyboardButton(text='Грунт'), KeyboardButton(text='Хард')],
        [KeyboardButton(text='Пропустить')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_coach_keyboard():
    keyboard = [
        [KeyboardButton(text='Пропустить')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_stats_period_keyboard():
    keyboard = [
        [KeyboardButton(text='📅 За неделю'), KeyboardButton(text='📅 За месяц')],
        [KeyboardButton(text='📅 За год'), KeyboardButton(text='📅 За все время')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_participants_filter_keyboard():
    keyboard = [
        [KeyboardButton(text='Все'), KeyboardButton(text='1 человек'), KeyboardButton(text='2 человека')],
        [KeyboardButton(text='3 человека'), KeyboardButton(text='4 человека'), KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def remove_keyboard():
    return ReplyKeyboardRemove()


def get_edit_profile_menu():
    keyboard = [
        [KeyboardButton(text='Редактировать абонементы')],
        [KeyboardButton(text='Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_edit_subscription_menu():
    keyboard = [
        [KeyboardButton(text='Добавить старый абонемент')],
        [KeyboardButton(text='Редактировать абонемент')],
        [KeyboardButton(text='Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_subscriptions_keyboard(subscriptions):
    keyboard = [[KeyboardButton(text=f"Абонемент №{sub['id']} от {sub['start_date']}")] for sub in subscriptions]
    keyboard.append([KeyboardButton(text='Назад')])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_edit_subscription_field_menu():
    keyboard = [
        [KeyboardButton(text='Номер')],
        [KeyboardButton(text='Стоимость'), KeyboardButton(text='Дата начала')],
        [KeyboardButton(text='Дата окончания'), KeyboardButton(text='Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
