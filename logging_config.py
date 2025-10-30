import logging
import logging.handlers
import os
from datetime import datetime
import sys


def setup_logging():
    """Настройка системы логирования"""

    # Создаем папку для логов если её нет
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Удаляем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 1. Файловый обработчик (ротация по дням)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'tennis_bot.log'),
        when='midnight',
        interval=1,
        backupCount=30,  # Храним 30 дней логов
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 2. Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 3. Обработчик для ошибок (отдельный файл)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'errors.log'),
        when='midnight',
        interval=1,
        backupCount=90,  # Храним 90 дней ошибок
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)

    # Логируем старт системы
    logger.info("=== Tennis Bot Logging System Started ===")


def get_logger(name):
    """Получить логгер с указанным именем"""
    return logging.getLogger(name)