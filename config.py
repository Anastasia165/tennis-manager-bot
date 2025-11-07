import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from aiogram.fsm.state import State, StatesGroup

load_dotenv()


class RegisterStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    first_name = State()
    last_name = State()
    phone = State()


class SubscriptionStates(StatesGroup):
    """Состояния для создания абонемента"""
    number = State()
    amount = State()


class TrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""
    duration = State()
    participants = State()
    court = State()
    coach = State()


class StatsStates(StatesGroup):
    """Состояния для просмотра статистики"""
    period = State()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_IDS: list = field(
        default_factory=lambda: list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else [])
    DB_PATH: str = os.getenv('DB_PATH', 'data/tennis_club.db')

    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')


config = Config()
