import logging
from functools import wraps
from typing import Any, Callable


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
