import logging
from functools import wraps
from typing import Any, Callable
import re
from datetime import datetime


def format_amount(amount: float) -> str:
    """Форматирует сумму в строку с валютой."""
    return f"{amount:,.2f} ₽".replace(',', ' ')

def format_date(date_str: str) -> str:
    """Форматирует дату из строки YYYY-MM-DD в DD.MM.YYYY."""
    if not date_str:
        return "N/A"
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')
        except ValueError:
            return date_str


def validate_phone(phone: str) -> bool:
    """Проверяет, соответствует ли номер телефона российскому формату."""
    # Удаляем все, кроме цифр
    cleaned_phone = re.sub(r'\D', '', phone)
    # Проверяем, начинается ли номер с 7, 8 или 9 и имеет ли он 11 цифр
    # или начинается с 9 и имеет 10 цифр
    if re.match(r'^(7|8)?(\d{10})$', cleaned_phone):
        return True
    return False


def format_phone(phone: str) -> str:
    """Форматирует номер телефона в стандартный российский формат +7."""
    cleaned_phone = re.sub(r'\D', '', phone)
    if len(cleaned_phone) == 11 and (cleaned_phone.startswith('7') or cleaned_phone.startswith('8')):
        return '+7' + cleaned_phone[1:]
    if len(cleaned_phone) == 10:
        return '+7' + cleaned_phone
    return phone  # Возвращаем как есть, если формат неизвестен


def get_period_name(period: str) -> str:
    """Возвращает человекочитаемое название периода."""
    return {
        'week': 'неделю',
        'month': 'месяц',
        'year': 'год',
        'all': 'все время'
    }.get(period, '')


def log_command(func: Callable) -> Callable:
    """Декоратор для логирования команд бота"""

    @wraps(func)
    async def wrapper(update: Any, context: Any, *args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(f'bot.commands')

        user = update.effective_user
        command = func.__name__

        logger.info(
            f"Command '{command}' from user {user.id} ({user.username or 'no username'})"
        )

        try:
            result = await func(update, context, *args, **kwargs)
            logger.info(f"Command '{command}' completed successfully")
            return result
        except Exception as e:
            logger.error(
                f"Command '{command}' failed for user {user.id}: {str(e)}",
                exc_info=True
            )
            raise

    return wrapper


def log_database_operation(func: Callable) -> Callable:
    """Декоратор для логирования операций с БД"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger('bot.database')

        logger.debug(f"DB operation: {func.__name__} - args: {args[1:]} kwargs: {kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"DB operation {func.__name__} completed")
            return result
        except Exception as e:
            logger.error(
                f"DB operation {func.__name__} failed: {str(e)}",
                exc_info=True
            )
            raise

    return wrapper
