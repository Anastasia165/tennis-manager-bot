from datetime import datetime
import re

def validate_phone(phone: str) -> bool:
    """Проверка формата телефона"""
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(pattern, phone))

def format_phone(phone: str) -> str:
    """Форматирование телефона в единый формат"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    return f"+{digits}"

def format_date(date_str: str) -> str:
    """Форматирование даты"""
    date_obj = datetime.fromisoformat(date_str)
    return date_obj.strftime('%d.%m.%Y')

def format_amount(amount: float) -> str:
    """Форматирование суммы"""
    return f"{amount:,.2f} ₽".replace(',', ' ')

def get_period_name(period: str) -> str:
    periods = {
        'week': 'неделю',
        'month': 'месяц',
        'year': 'год',
        'all': 'все время'
    }
    return periods.get(period, period)
