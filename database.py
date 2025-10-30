import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils import log_database_operation

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger('bot.database')
        self.logger.info(f"Initializing database: {db_path}")
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Инициализация базы данных"""
        self.logger.info("Initializing database tables...")
        try:
            with self.get_connection() as conn:
            # Таблица пользователей
                conn.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        first_name TEXT NOT NULL,
                        last_name TEXT,
                        phone TEXT,
                        registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')

            # Таблица абонементов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subscription_number TEXT UNIQUE NOT NULL,
                    initial_amount DECIMAL(10,2) NOT NULL,
                    current_balance DECIMAL(10,2) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Таблица прайс-листа
            conn.execute('''
                CREATE TABLE IF NOT EXISTS price_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    duration_minutes INTEGER NOT NULL,
                    participants_count INTEGER NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # Таблица тренировок
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date DATE NOT NULL,
                    session_time TIME NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    court_type TEXT,
                    coach_name TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица участников тренировок
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    training_session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    subscription_id INTEGER NOT NULL,
                    amount_paid DECIMAL(10,2) NOT NULL,
                    participants_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (training_session_id) REFERENCES training_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
                )
            ''')

            # Таблица транзакций
            conn.execute('''
                        CREATE TABLE IF NOT EXISTS transactions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            subscription_id INTEGER NOT NULL,
                            training_session_id INTEGER,
                            transaction_type TEXT NOT NULL,
                            amount DECIMAL(10,2) NOT NULL,
                            description TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
                            FOREIGN KEY (training_session_id) REFERENCES training_sessions(id) ON DELETE SET NULL
                            )
                        ''')

            # Заполняем прайс-лист начальными данными
            self._init_price_list(conn)
            conn.commit()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    def _init_price_list(self, conn):
        """Инициализация прайс-листа"""
        prices = [
            (60, 1, 1500, "Индивидуальная 60 мин"),
            (90, 1, 2000, "Индивидуальная 90 мин"),
            (120, 1, 2500, "Индивидуальная 120 мин"),
            (60, 2, 800, "Вдвоем 60 мин"),
            (90, 2, 1200, "Вдвоем 90 мин"),
            (120, 2, 1600, "Вдвоем 120 мин"),
            (60, 3, 600, "Втроем 60 мин"),
            (90, 3, 900, "Втроем 90 мин"),
            (120, 3, 1200, "Втроем 120 мин"),
            (60, 4, 500, "Вчетвером 60 мин"),
            (90, 4, 750, "Вчетвером 90 мин"),
            (120, 4, 1000, "Вчетвером 120 мин"),
        ]

        for duration, participants, price, description in prices:
            conn.execute('''
                INSERT OR IGNORE INTO price_list 
                (duration_minutes, participants_count, price, description)
                VALUES (?, ?, ?, ?)
            ''', (duration, participants, price, description))

    # Методы для работы с пользователями
    @log_database_operation
    def user_exists(self, telegram_id: int) -> bool:
        with self.get_connection() as conn:
            result = conn.execute(
                'SELECT 1 FROM users WHERE telegram_id = ?',
                (telegram_id,)
            ).fetchone()
            return result is not None

    @log_database_operation
    def register_user(self, telegram_id: int, first_name: str, last_name: str = None, phone: str = None):
        self.logger.info(f"Registering new user: {telegram_id}, {first_name} {last_name}")
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, phone)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, first_name, last_name, phone))

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    # Методы для работы с абонементами
    def create_subscription(self, user_id: int, subscription_number: str, initial_amount: float):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO subscriptions (user_id, subscription_number, initial_amount, current_balance, start_date)
                VALUES (?, ?, ?, ?, date('now'))
            ''', (user_id, subscription_number, initial_amount, initial_amount))
            return cursor.lastrowid

    def get_active_subscription(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND status = 'active' AND current_balance > 0
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def update_subscription_balance(self, subscription_id: int, amount: float):
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE subscriptions 
                SET current_balance = current_balance - ?
                WHERE id = ? AND current_balance >= ?
            ''', (amount, subscription_id, amount))
            return conn.total_changes > 0

    # Методы для работы с тренировками
    def get_price(self, duration: int, participants: int) -> Optional[float]:
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT price FROM price_list 
                WHERE duration_minutes = ? AND participants_count = ? AND is_active = TRUE
            ''', (duration, participants)).fetchone()
            return result[0] if result else None

    @log_database_operation
    def add_training_session(self, user_id: int, subscription_id: int, duration: int,
                             participants: int, court_type: str = None, coach: str = None):
        self.logger.info(
            f"Adding training session: user={user_id}, duration={duration}, "
            f"participants={participants}, court={court_type}, coach={coach}"
        )
        with self.get_connection() as conn:
            # Получаем цену
            price = self.get_price(duration, participants)
            if not price:
                raise ValueError("Цена не найдена для указанных параметров")

            # Проверяем баланс
            subscription = conn.execute(
                'SELECT current_balance FROM subscriptions WHERE id = ?',
                (subscription_id,)
            ).fetchone()

            if not subscription or subscription[0] < price:
                raise ValueError("Недостаточно средств на абонементе")

            # Создаем тренировку
            now = datetime.now()
            cursor = conn.execute('''
                INSERT INTO training_sessions (session_date, session_time, duration_minutes, court_type, coach_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (now.date(), now.time(), duration, court_type, coach))
            training_id = cursor.lastrowid

            # Добавляем участника
            conn.execute('''
                INSERT INTO training_participants 
                (training_session_id, user_id, subscription_id, amount_paid, participants_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (training_id, user_id, subscription_id, price, participants))

            # Обновляем баланс
            conn.execute('''
                UPDATE subscriptions SET current_balance = current_balance - ? 
                WHERE id = ?
            ''', (price, subscription_id))

            # Добавляем транзакцию
            conn.execute('''
                INSERT INTO transactions 
                (user_id, subscription_id, training_session_id, transaction_type, amount, description)
                VALUES (?, ?, ?, 'training', ?, ?)
            ''', (user_id, subscription_id, training_id, price,
                  f"Тренировка: {duration}мин, {participants} чел."))

            conn.commit()
            self.logger.info(f"Training session added successfully: ID {training_id}")
            return training_id

    # Методы для статистики
    def get_spent_amount(self, user_id: int, period: str = 'month') -> float:
        with self.get_connection() as conn:
            date_filter = self._get_date_filter(period)
            result = conn.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE user_id = ? AND transaction_type = 'training' 
                AND created_at >= ?
            ''', (user_id, date_filter)).fetchone()
            return result[0] if result else 0

    def get_training_count(self, user_id: int, period: str = 'month', participants: int = None) -> int:
        with self.get_connection() as conn:
            date_filter = self._get_date_filter(period)
            query = '''
                SELECT COUNT(*) FROM training_participants tp
                JOIN training_sessions ts ON tp.training_session_id = ts.id
                WHERE tp.user_id = ? AND ts.session_date >= ?
            '''
            params = [user_id, date_filter]

            if participants:
                query += ' AND tp.participants_count = ?'
                params.append(participants)

            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0

    def _get_date_filter(self, period: str) -> str:
        """Возвращает дату для фильтрации по периоду"""
        today = datetime.now().date()
        if period == 'week':
            return (today - timedelta(days=7)).isoformat()
        elif period == 'month':
            return today.replace(day=1).isoformat()
        elif period == 'year':
            return today.replace(month=1, day=1).isoformat()
        else:  # all time
            return '2000-01-01'

    def get_user_trainings(self, user_id: int, limit: int = 10) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT ts.session_date, ts.duration_minutes, tp.participants_count, 
                       tp.amount_paid, ts.court_type, ts.coach_name
                FROM training_participants tp
                JOIN training_sessions ts ON tp.training_session_id = ts.id
                WHERE tp.user_id = ?
                ORDER BY ts.session_date DESC, ts.session_time DESC
                LIMIT ?
            ''', (user_id, limit))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
