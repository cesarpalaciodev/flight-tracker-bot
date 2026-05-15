import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).parent.parent.parent

load_dotenv(BASE_DIR / ".env")


class IgnavConfig(BaseModel):
    api_key: str = Field(default="")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("IGNAV_API_KEY is required")
        if not v.startswith("ignav_"):
            raise ValueError("IGNAV_API_KEY must start with 'ignav_'")
        return v


class TelegramConfig(BaseModel):
    token: str = Field(default="")
    chat_id: str = Field(default="")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v:
            raise ValueError("TELEGRAM_TOKEN is required")
        if ":" not in v:
            raise ValueError("TELEGRAM_TOKEN must contain ':'")
        return v

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, v: str) -> str:
        if not v:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        return v.strip()


class DatabaseConfig(BaseModel):
    url: str = Field(default="sqlite:///data/flight_tracker.db")
    redis_url: str = Field(default="")


class AppConfig(BaseModel):
    destinations: list[str] = Field(default=["ADZ"])
    origins: list[str] = Field(default=["MDE", "PEI"])
    price_drop_threshold: float = Field(default=1.0)
    price_increase_threshold: float = Field(default=0.0)
    check_interval_hours: int = Field(default=8)
    adults: int = Field(default=2)
    return_days: int = Field(default=5)
    days_ahead_start: int = Field(default=68)
    days_ahead_end: int = Field(default=131)
    days_interval: int = Field(default=14)
    smtp_server: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    from_email: str = Field(default="")
    notify_email: str = Field(default="")

    @field_validator("origins", "destinations", mode="before")
    @classmethod
    def validate_list(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [x.strip().upper() for x in v.split(",")]
        return [x.upper() for x in v]

    @field_validator("adults")
    @classmethod
    def validate_adults(cls, v: int) -> int:
        if v < 1 or v > 9:
            raise ValueError("adults must be between 1 and 9")
        return v

    @field_validator("return_days")
    @classmethod
    def validate_return_days(cls, v: int) -> int:
        if v < 1 or v > 90:
            raise ValueError("return_days must be between 1 and 90")
        return v


def _load_config() -> tuple[IgnavConfig, TelegramConfig, AppConfig, DatabaseConfig]:
    try:
        api_key = os.getenv("IGNAV_API_KEY", "")
        telegram_token = os.getenv("TELEGRAM_TOKEN", "")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/flight_tracker.db")
        redis_url = os.getenv("REDIS_URL", "")
    except Exception:
        api_key = telegram_token = telegram_chat_id = db_url = redis_url = ""

    def safe_cfg(cfg_type, **kw):
        try:
            return cfg_type(**kw)
        except ValueError:
            return cfg_type(**{k: "" for k in kw})

    return (
        safe_cfg(IgnavConfig, api_key=api_key),
        safe_cfg(TelegramConfig, token=telegram_token, chat_id=telegram_chat_id),
        AppConfig(),
        DatabaseConfig(url=db_url, redis_url=redis_url),
    )


IGNV_CFG, TELEGRAM_CFG, APP_CFG, DB_CFG = _load_config()

API_KEY: str = IGNV_CFG.api_key
TELEGRAM_TOKEN: str = TELEGRAM_CFG.token
TELEGRAM_CHAT_ID: str = TELEGRAM_CFG.chat_id

DESTINATIONS: list[str] = APP_CFG.destinations
ORIGINS: list[str] = APP_CFG.origins
PRICE_DROP_THRESHOLD: float = APP_CFG.price_drop_threshold
PRICE_INCREASE_THRESHOLD: float = APP_CFG.price_increase_threshold
CHECK_INTERVAL_HOURS: int = APP_CFG.check_interval_hours
ADULTS: int = APP_CFG.adults
RETURN_DAYS: int = APP_CFG.return_days
DAYS_AHEAD_START: int = APP_CFG.days_ahead_start
DAYS_AHEAD_END: int = APP_CFG.days_ahead_end
DAYS_INTERVAL: int = APP_CFG.days_interval

DATABASE_URL: str = DB_CFG.url
REDIS_URL: str = DB_CFG.redis_url

SMTP_SERVER: str = APP_CFG.smtp_server
SMTP_PORT: int = APP_CFG.smtp_port
SMTP_USERNAME: str = APP_CFG.smtp_username
SMTP_PASSWORD: str = APP_CFG.smtp_password
FROM_EMAIL: str = APP_CFG.from_email
NOTIFY_EMAIL: str = APP_CFG.notify_email

PRICE_HISTORY_FILE: Path = BASE_DIR / "data" / "price_history.json"
LOG_FILE: Path = BASE_DIR / "logs" / "flight_tracker.log"
DATA_DIR: Path = BASE_DIR / "data"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
_RATE_LIMIT_FILE: Path = DATA_DIR / "rate_limit.json"


def setup_logging(name: str = "flight_tracker") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_departure_date(days_ahead: int = 30) -> str:
    date = datetime.now() + timedelta(days=days_ahead)
    return date.strftime("%Y-%m-%d")


def build_route_key(origin: str, destination: str) -> str:
    return f"{origin}:{destination}"