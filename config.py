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
        'STATS_PERIOD': 10,
        'CLOSE_SUBSCRIPTION_CONFIRM': 11,
        'TOP_UP_AMOUNT': 12,
        'EXPENSES_PERIOD': 13,
        'EDIT_PROFILE_CHOICE': 14,
        'EDIT_SUBSCRIPTION_CHOICE': 15,
        'ADD_OLD_SUB_NUMBER': 16,
        'ADD_OLD_SUB_VISITS': 17,
        'ADD_OLD_SUB_COST': 18,
        'ADD_OLD_SUB_START_DATE': 19,
        'ADD_OLD_SUB_END_DATE': 20,
        'EDIT_SUB_SELECT': 21,
        'EDIT_SUB_FIELD': 22,
        'EDIT_SUB_NEW_VALUE': 23,
    })


config = Config()
