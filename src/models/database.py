from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship


class Base(DeclarativeBase):
    pass


class UserConfig(Base):
    __tablename__ = "user_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(20), unique=True, nullable=False, index=True)
    onboarded = Column(Integer, default=0)
    origins = Column(String(200), default="MDE,PEI")
    destinations = Column(String(200), default="ADZ")
    luggage = Column(String(20), default="carry_on")
    cabin_class = Column(String(20), default="economy")
    max_budget = Column(Float, nullable=True)
    preferred_airlines = Column(String(200), default="")
    non_stop_only = Column(Integer, default=0)
    trip_days_flexible = Column(Integer, default=3)
    adults = Column(Integer, default=2)
    return_days = Column(Integer, default=5)
    price_drop_threshold = Column(Float, default=1.0)
    price_increase_threshold = Column(Float, default=0.0)
    active = Column(Integer, default=1)
    onboarding_step = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="user", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(20), ForeignKey("user_config.chat_id"), unique=True, nullable=False, index=True)
    plan = Column(String(20), default="trial")
    status = Column(String(20), default="trial")
    trial_ends_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    paid_until = Column(DateTime, nullable=True)
    payment_method = Column(String(20), default="")
    stripe_customer_id = Column(String(100), default="")
    stripe_session_id = Column(String(100), default="")
    crypto_tx_hash = Column(String(100), default="")
    api_requests_month = Column(Integer, default=0)
    api_requests_limit = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserConfig", back_populates="subscription")


class PriceRecord(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(20), ForeignKey("user_config.chat_id"), nullable=False, index=True)
    route = Column(String(20), nullable=False)
    origin = Column(String(5), nullable=False)
    destination = Column(String(5), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(5), default="COP")
    airline = Column(String(50), nullable=False)
    departure_date = Column(String(10))
    return_date = Column(String(10))
    booking_link = Column(String(500))
    luggage_match = Column(Integer, default=0)
    budget_match = Column(Integer, default=0)
    raw_data = Column(JSON, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AlertLog(Base):
    __tablename__ = "alert_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(20), ForeignKey("user_config.chat_id"), nullable=False, index=True)
    route = Column(String(20), nullable=False)
    alert_type = Column(String(20), nullable=False)
    old_price = Column(Float)
    new_price = Column(Float)
    difference = Column(Float)
    sent_via = Column(String(20), default="telegram")
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Database:
    def __init__(self, db_url: str = "sqlite:///data/flight_tracker.db"):
        self.engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def get_or_create_user(self, chat_id: str) -> UserConfig:
        with self.get_session() as session:
            user = session.query(UserConfig).filter(UserConfig.chat_id == chat_id).first()
            if user:
                return user
            user = UserConfig(chat_id=chat_id)
            session.add(user)
            session.flush()
            sub = Subscription(chat_id=chat_id)
            session.add(sub)
            session.commit()
            return user

    def get_user_config(self, chat_id: str) -> Optional[UserConfig]:
        with self.get_session() as session:
            return session.query(UserConfig).filter(UserConfig.chat_id == chat_id).first()

    def set_user_config(self, chat_id: str, **kwargs) -> UserConfig:
        with self.get_session() as session:
            user = session.query(UserConfig).filter(UserConfig.chat_id == chat_id).first()
            if user:
                for k, v in kwargs.items():
                    if hasattr(user, k):
                        setattr(user, k, v)
            else:
                kw = {"chat_id": chat_id}
                kw.update(kwargs)
                user = UserConfig(**kw)
                session.add(user)
                sub = Subscription(chat_id=chat_id)
                session.add(sub)
            session.commit()
            return user

    def get_all_active_users(self) -> List[UserConfig]:
        with self.get_session() as session:
            return session.query(UserConfig).filter(UserConfig.active == 1).all()

    def get_subscription(self, chat_id: str) -> Optional[Subscription]:
        with self.get_session() as session:
            return session.query(Subscription).filter(Subscription.chat_id == chat_id).first()

    def set_subscription(self, chat_id: str, **kwargs) -> Subscription:
        with self.get_session() as session:
            sub = session.query(Subscription).filter(Subscription.chat_id == chat_id).first()
            if sub:
                for k, v in kwargs.items():
                    if hasattr(sub, k):
                        setattr(sub, k, v)
            else:
                kw = {"chat_id": chat_id}
                kw.update(kwargs)
                sub = Subscription(**kw)
                session.add(sub)
            session.commit()
            return sub

    def save_price(
        self,
        chat_id: str,
        route: str,
        origin: str,
        destination: str,
        price: float,
        currency: str = "COP",
        airline: str = "",
        departure_date: str = "",
        return_date: str = "",
        booking_link: str = "",
        luggage_match: int = 0,
        budget_match: int = 0,
    ) -> PriceRecord:
        with self.get_session() as session:
            record = PriceRecord(
                chat_id=chat_id,
                route=route,
                origin=origin,
                destination=destination,
                price=price,
                currency=currency,
                airline=airline,
                departure_date=departure_date,
                return_date=return_date,
                booking_link=booking_link,
                luggage_match=luggage_match,
                budget_match=budget_match,
            )
            session.add(record)
            session.commit()
            return record

    def get_price_history(self, chat_id: str, route: str = "", limit: int = 30) -> List[PriceRecord]:
        with self.get_session() as session:
            q = session.query(PriceRecord).filter(PriceRecord.chat_id == chat_id)
            if route:
                q = q.filter(PriceRecord.route == route)
            return q.order_by(PriceRecord.checked_at.desc()).limit(limit).all()

    def log_alert(
        self, chat_id: str, route: str, alert_type: str, old_price: float, new_price: float, difference: float
    ) -> AlertLog:
        with self.get_session() as session:
            log = AlertLog(
                chat_id=chat_id,
                route=route,
                alert_type=alert_type,
                old_price=old_price,
                new_price=new_price,
                difference=difference,
            )
            session.add(log)
            session.commit()
            return log

    def get_alerts(self, chat_id: str = "", limit: int = 50) -> List[AlertLog]:
        with self.get_session() as session:
            q = session.query(AlertLog)
            if chat_id:
                q = q.filter(AlertLog.chat_id == chat_id)
            return q.order_by(AlertLog.sent_at.desc()).limit(limit).all()

    def get_admin_stats(self) -> dict:
        with self.get_session() as session:
            total_users = session.query(UserConfig).count()
            active_subs = session.query(Subscription).filter(Subscription.status.in_(["active", "trial"])).count()
            total_searches = session.query(PriceRecord).count()
            total_alerts = session.query(AlertLog).count()
            return {
                "total_users": total_users,
                "active_subscriptions": active_subs,
                "total_searches": total_searches,
                "total_alerts": total_alerts,
            }
