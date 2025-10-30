import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_IDS: list = field(
        default_factory=lambda: list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else [])
    DB_PATH: str = os.getenv('DB_PATH', 'data/tennis_club.db')

    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')

    STATES: dict = field(default_factory=lambda: {
        'REGISTER_FIRST_NAME': 1,
        'REGISTER_LAST_NAME': 2,
        'REGISTER_PHONE': 3,
        'NEW_SUBSCRIPTION_NUMBER': 4,
        'NEW_SUBSCRIPTION_AMOUNT': 5,
        'TRAINING_DURATION': 6,
        'TRAINING_PARTICIPANTS': 7,
        'TRAINING_COURT': 8,
        'TRAINING_COACH': 9,
        'STATS_PERIOD': 10
    })


config = Config()
