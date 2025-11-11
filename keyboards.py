from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

def get_main_menu():
    keyboard = [
        ['💪 Тренировки', '💳 Абонементы'],
        ['👤 Профиль']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_workouts_menu():
    keyboard = [
        ['➕ Добавить тренировку', '📈 Статистика'],
        ['📋 История тренировок', '🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_subscriptions_menu():
    keyboard = [
        ['💰 Баланс', '🔄 Новый абонемент'],
        ['🗂️ Архив', '💸 Пополнить'],
        ['📊 Расходы', '🚫 Закрыть абонемент'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_profile_menu():
    keyboard = [
        ['ℹ️ Показать профиль', '✏️ Редактировать профиль'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_duration_keyboard():
    keyboard = [
        ['60 минут', '90 минут'],
        ['120 минут', '❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_participants_keyboard():
    keyboard = [
        ['1 человек', '2 человека'],
        ['3 человека', '4 человека'],
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_court_type_keyboard():
    keyboard = [
        ['Крытый корт', 'Открытый корт'],
        ['Грунт', 'Хард'],
        ['Пропустить']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_stats_period_keyboard():
    keyboard = [
        ['📅 За неделю', '📅 За месяц'],
        ['📅 За год', '📅 За все время'],
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_participants_filter_keyboard():
    keyboard = [
        ['Все', '1 человек', '2 человека'],
        ['3 человека', '4 человека', '❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def remove_keyboard():
    return ReplyKeyboardRemove()