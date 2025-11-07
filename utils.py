import logging
import re
from functools import wraps
from typing import Any, Callable
from datetime import datetime


def log_command(func: Callable) -> Callable:
    """Декоратор для логирования команд бота"""

    @wraps(func)
    async def wrapper(self: Any, message: Any, *args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger('bot.commands')

        user = message.from_user
        command = func.__name__

        logger.info(
            f"Command '{command}' from user {user.id} ({user.username or 'no username'})"
        )

        try:
            result = await func(self, message, *args, **kwargs)
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


def format_amount(value: float) -> str:
    """Форматирование денежной суммы с правильным разделителем"""
    if value is None:
        return "0,00 ₽"
    return f"{value:,.2f}".replace(',', ' ').replace('.', ',') + " ₽"


def format_date(date_str: str) -> str:
    """Форматирование даты для отображения"""
    if date_str is None:
        return "Не указано"
    try:
        # Попытка распарсить дату в формате YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_obj.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        try:
            # Попытка распарсить дату в формате YYYY-MM-DD HH:MM:SS
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
            return date_obj.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            return date_str


def format_phone(phone: str) -> str:
    """Нормализация формата телефона"""
    if not phone:
        return phone

    # Убираем все символы кроме цифр
    digits = re.sub(r'\D', '', phone)

    # Если телефон начинается с 8, заменяем на 7
    if digits.startswith('8'):
        digits = '7' + digits[1:]

    # Если телефон не начинается с 7, добавляем 7
    if not digits.startswith('7'):
        digits = '7' + digits

    # Форматируем в стандартный вид: +7 XXX XXX XX XX
    if len(digits) >= 11:
        return f"+{digits[0]} {digits[1:4]} {digits[4:7]} {digits[7:9]} {digits[9:11]}"

    return f"+{digits}" if digits else phone


def validate_phone(phone: str) -> bool:
    """Валидация российских номеров телефонов"""
    if not phone:
        return False

    # Убираем все символы кроме цифр
    digits = re.sub(r'\D', '', phone)

    # Проверяем, что остались только цифры и их достаточно
    if not digits.isdigit():
        return False

    # Допускаем номера от 10 до 12 цифр
    # (8XXXXXXXXXX, 7XXXXXXXXXXX, +7XXXXXXXXXXX и т.д.)
    if len(digits) < 10 or len(digits) > 12:
        return False

    # Проверяем, что номер начинается с 7 или 8
    first_digit = digits[0]
    if first_digit not in ('7', '8'):
        return False

    return True


def get_period_name(period: str) -> str:
    """Преобразование кода периода в отображаемое имя"""
    periods = {
        'week': 'неделю',
        'month': 'месяц',
        'year': 'год',
        'all': 'все время'
    }
    return periods.get(period, 'месяц')
