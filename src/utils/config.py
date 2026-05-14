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


class AppConfig(BaseModel):
    destination: str = Field(default="ADZ")
    origins: list[str] = Field(default=["MDE", "PEI"])
    price_drop_threshold: float = Field(default=1.0)
    check_interval_hours: int = Field(default=8)
    adults: int = Field(default=2)
    return_days: int = Field(default=5)
    days_ahead_start: int = Field(default=68)
    days_ahead_end: int = Field(default=131)
    days_interval: int = Field(default=14)

    @field_validator("origins", mode="before")
    @classmethod
    def validate_origins(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

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


def _load_config() -> tuple[IgnavConfig, TelegramConfig, AppConfig]:
    try:
        api_key = os.getenv("IGNAV_API_KEY", "")
        telegram_token = os.getenv("TELEGRAM_TOKEN", "")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    except Exception:
        api_key = ""
        telegram_token = ""
        telegram_chat_id = ""

    try:
        ignav_cfg = IgnavConfig(api_key=api_key)
    except ValueError:
        ignav_cfg = IgnavConfig(api_key="")

    try:
        telegram_cfg = TelegramConfig(token=telegram_token, chat_id=telegram_chat_id)
    except ValueError:
        telegram_cfg = TelegramConfig(token="", chat_id="")

    app_cfg = AppConfig()

    return ignav_cfg, telegram_cfg, app_cfg


IGNV_CFG, TELEGRAM_CFG, APP_CFG = _load_config()

API_KEY: str = IGNV_CFG.api_key
TELEGRAM_TOKEN: str = TELEGRAM_CFG.token
TELEGRAM_CHAT_ID: str = TELEGRAM_CFG.chat_id

DESTINATION: str = APP_CFG.destination
ORIGINS: list[str] = APP_CFG.origins
PRICE_DROP_THRESHOLD: float = APP_CFG.price_drop_threshold
CHECK_INTERVAL_HOURS: int = APP_CFG.check_interval_hours
ADULTS: int = APP_CFG.adults
RETURN_DAYS: int = APP_CFG.return_days
DAYS_AHEAD_START: int = APP_CFG.days_ahead_start
DAYS_AHEAD_END: int = APP_CFG.days_ahead_end
DAYS_INTERVAL: int = APP_CFG.days_interval

PRICE_HISTORY_FILE: Path = BASE_DIR / "data" / "price_history.json"
LOG_FILE: Path = BASE_DIR / "logs" / "flight_tracker.log"

PRICE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_RATE_LIMIT_FILE: Path = BASE_DIR / "data" / "rate_limit.json"


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