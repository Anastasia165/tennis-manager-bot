from sqlalchemy import create_engine, func, desc, asc
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from models import Base, User, Subscription, PriceList, TrainingSession, TrainingParticipant, Transaction
from utils import log_database_operation

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger('bot.database')
        self.logger.info(f"Initializing database: {db_path}")
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Методы для работы с пользователями
    @log_database_operation
    def user_exists(self, telegram_id: int) -> bool:
        with self.get_session() as session:
            return session.query(User).filter(User.telegram_id == telegram_id).first() is not None

    @log_database_operation
    def register_user(self, telegram_id: int, first_name: str, last_name: str = None, phone: str = None):
        self.logger.info(f"Registering new user: {telegram_id}, {first_name} {last_name}")
        with self.get_session() as session:
            new_user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            session.add(new_user)

    def get_user(self, telegram_id: int) -> Optional[User]:
        try:
            with self.get_session() as session:
                return session.query(User).filter(User.telegram_id == telegram_id).first()
        except Exception as e:
            self.logger.error(f"Error getting user {telegram_id}: {e}")
            return None

    # Методы для работы с абонементами
    def create_subscription(self, user_id: int, subscription_number: str, initial_amount: float):
        with self.get_session() as session:
            new_subscription = Subscription(
                user_id=user_id,
                subscription_number=subscription_number,
                initial_amount=initial_amount,
                current_balance=initial_amount,
                start_date=datetime.now().date()
            )
            session.add(new_subscription)
            session.flush()
            return new_subscription.id

    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        with self.get_session() as session:
            return session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == 'active'
            ).order_by(Subscription.created_at.desc()).first()

    def close_subscription(self, subscription_id: int):
        with self.get_session() as session:
            subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription:
                subscription.status = 'closed'
                subscription.end_date = datetime.now().date()

    def top_up_subscription(self, subscription_id: int, amount: float):
        with self.get_session() as session:
            subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription:
                subscription.current_balance += amount
                new_transaction = Transaction(
                    user_id=subscription.user_id,
                    subscription_id=subscription_id,
                    transaction_type='top-up',
                    amount=amount,
                    description='Пополнение абонемента'
                )
                session.add(new_transaction)

    def get_archived_subscriptions(self, user_id: int) -> List[Subscription]:
        with self.get_session() as session:
            return session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == 'closed'
            ).order_by(Subscription.end_date.desc()).all()

    def update_subscription_balance(self, subscription_id: int, amount: float):
        with self.get_session() as session:
            subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription and subscription.current_balance >= amount:
                subscription.current_balance -= amount
                return True
            return False

    # Методы для работы с тренировками
    def get_price(self, duration: int, participants: int) -> Optional[float]:
        with self.get_session() as session:
            price = session.query(PriceList.price).filter(
                PriceList.duration_minutes == duration,
                PriceList.participants_count == participants,
                PriceList.is_active == True
            ).first()
            return price[0] if price else None

    @log_database_operation
    def add_training_session(self, user_id: int, subscription_id: int, duration: int,
                             participants: int, court_type: str = None, coach: str = None):
        self.logger.info(
            f"Adding training session: user={user_id}, duration={duration}, "
            f"participants={participants}, court={court_type}, coach={coach}"
        )
        with self.get_session() as session:
            price = self.get_price(duration, participants)
            if not price:
                raise ValueError("Цена не найдена для указанных параметров")

            subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()

            if not subscription or subscription.current_balance < price:
                raise ValueError("Недостаточно средств на абонементе")

            now = datetime.now()
            new_training_session = TrainingSession(
                session_date=now.date(),
                session_time=now.time(),
                duration_minutes=duration,
                court_type=court_type,
                coach_name=coach
            )
            session.add(new_training_session)
            session.flush()
            training_id = new_training_session.id

            new_participant = TrainingParticipant(
                training_session_id=training_id,
                user_id=user_id,
                subscription_id=subscription_id,
                amount_paid=price,
                participants_count=participants
            )
            session.add(new_participant)

            subscription.current_balance -= price

            new_transaction = Transaction(
                user_id=user_id,
                subscription_id=subscription_id,
                training_session_id=training_id,
                transaction_type='expense',
                amount=price,
                description=f"Тренировка: {duration}мин, {participants} чел."
            )
            session.add(new_transaction)
            self.logger.info(f"Training session added successfully: ID {training_id}")
            return training_id

    # Методы для статистики
    def get_spent_amount(self, user_id: int, period: str = 'month') -> float:
        with self.get_session() as session:
            date_filter = self._get_date_filter(period)
            return session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == 'expense',
                Transaction.created_at >= date_filter
            ).scalar() or 0

    def get_training_count(self, user_id: int, period: str = 'month', participants: int = None) -> int:
        with self.get_session() as session:
            date_filter = self._get_date_filter(period)
            query = session.query(func.count(TrainingParticipant.id)).join(TrainingSession).filter(
                TrainingParticipant.user_id == user_id,
                TrainingSession.session_date >= date_filter
            )
            if participants:
                query = query.filter(TrainingParticipant.participants_count == participants)

            return query.scalar() or 0

    def _get_date_filter(self, period: str) -> str:
        """Возвращает дату для фильтрации по периоду"""
        today = datetime.now().date()
        if period == 'week':
            return (today - timedelta(days=7))
        elif period == 'month':
            return today.replace(day=1)
        elif period == 'year':
            return today.replace(month=1, day=1)
        else:  # all time
            return datetime(2000, 1, 1).date()

    def get_user_trainings(self, user_id: int, limit: int = 10) -> List[Dict]:
        with self.get_session() as session:
            trainings = session.query(
                TrainingSession.session_date,
                TrainingSession.duration_minutes,
                TrainingParticipant.participants_count,
                TrainingParticipant.amount_paid,
                TrainingSession.court_type,
                TrainingSession.coach_name
            ).join(TrainingParticipant).filter(
                TrainingParticipant.user_id == user_id
            ).order_by(
                TrainingSession.session_date.desc(),
                TrainingSession.session_time.desc()
            ).limit(limit).all()
            return [training._asdict() for training in trainings]

    def get_transactions(self, user_id: int, period: str) -> List[Dict]:
        with self.get_session() as session:
            date_filter = self._get_date_filter(period)
            transactions = session.query(
                Transaction.transaction_type.label('type'),
                Transaction.amount,
                Transaction.created_at.label('date')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= date_filter
            ).order_by(Transaction.created_at.desc()).all()
            return [transaction._asdict() for transaction in transactions]

    def add_old_subscription(self, user_id: int, subscription_number: str, initial_amount: float,
                             visits: int, start_date: str, end_date: Optional[str] = None):
        with self.get_session() as session:
            status = 'closed' if end_date else 'active'
            new_subscription = Subscription(
                user_id=user_id,
                subscription_number=subscription_number,
                initial_amount=initial_amount,
                current_balance=initial_amount,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
                status=status
            )
            session.add(new_subscription)
            session.flush()
            return new_subscription.id

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        with self.get_session() as session:
            return session.query(Subscription).filter(Subscription.id == subscription_id).first()

    def update_subscription(self, subscription_id: int, field: str, value):
        with self.get_session() as session:
            subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription:
                if field == 'initial_amount':
                    expenses = session.query(func.sum(Transaction.amount)).filter(
                        Transaction.subscription_id == subscription_id,
                        Transaction.transaction_type == 'expense'
                    ).scalar() or 0
                    new_balance = float(value) - expenses
                    subscription.initial_amount = value
                    subscription.current_balance = new_balance
                else:
                    setattr(subscription, field, value)

    def get_all_user_subscriptions(self, user_id: int) -> List[Subscription]:
        with self.get_session() as session:
            return session.query(Subscription).filter(Subscription.user_id == user_id).order_by(
                Subscription.start_date.desc()).all()
