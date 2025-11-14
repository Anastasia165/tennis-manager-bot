import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State

load_dotenv()


class RegistrationStates(StatesGroup):
    REGISTER_FIRST_NAME = State()
    REGISTER_LAST_NAME = State()
    REGISTER_PHONE = State()


class NewSubscriptionStates(StatesGroup):
    NEW_SUBSCRIPTION_NUMBER = State()
    NEW_SUBSCRIPTION_AMOUNT = State()


class AddTrainingStates(StatesGroup):
    TRAINING_DURATION = State()
    TRAINING_PARTICIPANTS = State()
    TRAINING_COURT = State()
    TRAINING_COACH = State()


class StatsStates(StatesGroup):
    STATS_PERIOD = State()


class CloseSubscriptionStates(StatesGroup):
    CLOSE_SUBSCRIPTION_CONFIRM = State()


class TopUpStates(StatesGroup):
    TOP_UP_AMOUNT = State()


class ExpensesStates(StatesGroup):
    EXPENSES_PERIOD = State()


class EditProfileStates(StatesGroup):
    EDIT_PROFILE_CHOICE = State()
    EDIT_SUBSCRIPTION_CHOICE = State()
    ADD_OLD_SUB_NUMBER = State()
    ADD_OLD_SUB_VISITS = State()
    ADD_OLD_SUB_COST = State()
    ADD_OLD_SUB_START_DATE = State()
    ADD_OLD_SUB_END_DATE = State()
    EDIT_SUB_SELECT = State()
    EDIT_SUB_FIELD = State()
    EDIT_SUB_NEW_VALUE = State()


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