from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu():
    """Главное меню"""
    keyboard = [
        [KeyboardButton(text='🎾 Добавить тренировку'), KeyboardButton(text='💰 Баланс абонемента')],
        [KeyboardButton(text='📊 Статистика'), KeyboardButton(text='📝 Новый абонемент')],
        [KeyboardButton(text='📋 История тренировок'), KeyboardButton(text='👤 Профиль')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_duration_keyboard():
    """Клавиатура выбора продолжительности тренировки"""
    keyboard = [
        [KeyboardButton(text='60 минут'), KeyboardButton(text='90 минут')],
        [KeyboardButton(text='120 минут'), KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_participants_keyboard():
    """Клавиатура выбора количества участников"""
    keyboard = [
        [KeyboardButton(text='1 человек'), KeyboardButton(text='2 человека')],
        [KeyboardButton(text='3 человека'), KeyboardButton(text='4 человека')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_court_type_keyboard():
    """Клавиатура выбора типа корта"""
    keyboard = [
        [KeyboardButton(text='Крытый корт'), KeyboardButton(text='Открытый корт')],
        [KeyboardButton(text='Грунт'), KeyboardButton(text='Хард')],
        [KeyboardButton(text='Пропустить')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_stats_period_keyboard():
    """Клавиатура выбора периода статистики"""
    keyboard = [
        [KeyboardButton(text='📅 За неделю'), KeyboardButton(text='📅 За месяц')],
        [KeyboardButton(text='📅 За год'), KeyboardButton(text='📅 За все время')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_participants_filter_keyboard():
    """Клавиатура фильтрации по количеству участников"""
    keyboard = [
        [KeyboardButton(text='Все'), KeyboardButton(text='1 человек'), KeyboardButton(text='2 человека')],
        [KeyboardButton(text='3 человека'), KeyboardButton(text='4 человека'), KeyboardButton(text='❌ Отмена')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_coach_keyboard():
    """Клавиатура для ввода тренера"""
    keyboard = [
        [KeyboardButton(text='Пропустить')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def remove_keyboard():
    """Скрыть клавиатуру"""
    return ReplyKeyboardRemove()