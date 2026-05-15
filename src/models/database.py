from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class PriceRecord(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route = Column(String(20), nullable=False, index=True)
    origin = Column(String(5), nullable=False)
    destination = Column(String(5), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(5), default="COP")
    airline = Column(String(50), nullable=False)
    departure_date = Column(String(10))
    return_date = Column(String(10))
    booking_link = Column(String(500))
    raw_data = Column(JSON, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AlertLog(Base):
    __tablename__ = "alert_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)
    old_price = Column(Float)
    new_price = Column(Float)
    difference = Column(Float)
    sent_via = Column(String(20), default="telegram")
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserConfig(Base):
    __tablename__ = "user_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(20), unique=True, nullable=False, index=True)
    origins = Column(String(100), default="MDE,PEI")
    destinations = Column(String(100), default="ADZ")
    price_drop_threshold = Column(Float, default=1.0)
    price_increase_threshold = Column(Float, default=0.0)
    adults = Column(Integer, default=2)
    return_days = Column(Integer, default=5)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

    def save_price(self, route: str, origin: str, destination: str, price: float,
                   currency: str, airline: str, departure_date: str = "",
                   return_date: str = "", booking_link: str = "", raw_data: Optional[dict] = None) -> PriceRecord:
        with self.get_session() as session:
            record = PriceRecord(
                route=route, origin=origin, destination=destination,
                price=price, currency=currency, airline=airline,
                departure_date=departure_date, return_date=return_date,
                booking_link=booking_link, raw_data=raw_data,
            )
            session.add(record)
            session.commit()
            return record

    def get_latest_price(self, route: str) -> Optional[float]:
        with self.get_session() as session:
            record = session.query(PriceRecord)\
                .filter(PriceRecord.route == route)\
                .order_by(PriceRecord.checked_at.desc())\
                .first()
            return record.price if record else None

    def get_price_history(self, route: str, limit: int = 30) -> List[PriceRecord]:
        with self.get_session() as session:
            return session.query(PriceRecord)\
                .filter(PriceRecord.route == route)\
                .order_by(PriceRecord.checked_at.desc())\
                .limit(limit)\
                .all()

    def log_alert(self, route: str, alert_type: str, old_price: float,
                  new_price: float, difference: float) -> AlertLog:
        with self.get_session() as session:
            log = AlertLog(
                route=route, alert_type=alert_type,
                old_price=old_price, new_price=new_price, difference=difference,
            )
            session.add(log)
            session.commit()
            return log

    def get_alerts(self, limit: int = 50) -> List[AlertLog]:
        with self.get_session() as session:
            return session.query(AlertLog)\
                .order_by(AlertLog.sent_at.desc())\
                .limit(limit)\
                .all()

    def get_user_config(self, chat_id: str) -> Optional[UserConfig]:
        with self.get_session() as session:
            return session.query(UserConfig)\
                .filter(UserConfig.chat_id == chat_id)\
                .first()

    def set_user_config(self, chat_id: str, **kwargs) -> UserConfig:
        with self.get_session() as session:
            config = session.query(UserConfig)\
                .filter(UserConfig.chat_id == chat_id)\
                .first()
            if config:
                for k, v in kwargs.items():
                    if hasattr(config, k):
                        setattr(config, k, v)
            else:
                config = UserConfig(chat_id=chat_id, **kwargs)
                session.add(config)
            session.commit()
            return config