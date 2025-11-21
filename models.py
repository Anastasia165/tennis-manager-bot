from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    phone = Column(String)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    training_participants = relationship("TrainingParticipant", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    subscription_number = Column(String, unique=True, nullable=False)
    initial_amount = Column(DECIMAL(10, 2), nullable=False)
    current_balance = Column(DECIMAL(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String, default='active')
    visits = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    training_participants = relationship("TrainingParticipant", back_populates="subscription")
    transactions = relationship("Transaction", back_populates="subscription")


class PriceList(Base):
    __tablename__ = 'price_list'
    id = Column(Integer, primary_key=True, autoincrement=True)
    duration_minutes = Column(Integer, nullable=False)
    participants_count = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)


class TrainingSession(Base):
    __tablename__ = 'training_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_date = Column(Date, nullable=False)
    session_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    court_type = Column(String)
    coach_name = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    participants = relationship("TrainingParticipant", back_populates="training_session")
    transactions = relationship("Transaction", back_populates="training_session")


class TrainingParticipant(Base):
    __tablename__ = 'training_participants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    training_session_id = Column(Integer, ForeignKey('training_sessions.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id', ondelete="CASCADE"), nullable=False)
    amount_paid = Column(DECIMAL(10, 2), nullable=False)
    participants_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    training_session = relationship("TrainingSession", back_populates="participants")
    user = relationship("User", back_populates="training_participants")
    subscription = relationship("Subscription", back_populates="training_participants")


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id', ondelete="CASCADE"), nullable=False)
    training_session_id = Column(Integer, ForeignKey('training_sessions.id', ondelete="SET NULL"), nullable=True)
    transaction_type = Column(String, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    subscription = relationship("Subscription", back_populates="transactions")
    training_session = relationship("TrainingSession", back_populates="transactions")
