import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

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


class SecurityConfig(BaseModel):
    jwt_secret: str = Field(default="change_this")
    dashboard_url: str = Field(default="http://localhost:8000")
    admin_chat_ids: list[str] = Field(default=[])
    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    stripe_price_premium: str = Field(default="")
    stripe_price_pro: str = Field(default="")
    nequi_api_url: str = Field(default="")
    nequi_api_token: str = Field(default="")
    crypto_wallet_usdt: str = Field(default="")
    crypto_wallet_btc: str = Field(default="")
    api_requests_limit_free: int = Field(default=10)
    api_requests_limit_premium: int = Field(default=500)
    api_requests_limit_pro: int = Field(default=-1)

    @field_validator("admin_chat_ids", mode="before")
    @classmethod
    def validate_admin_chat_ids(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


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


def _load_config() -> tuple[IgnavConfig, TelegramConfig, AppConfig, DatabaseConfig, SecurityConfig]:
    try:
        api_key = os.getenv("IGNAV_API_KEY", "")
        telegram_token = os.getenv("TELEGRAM_TOKEN", "")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/flight_tracker.db")
        redis_url = os.getenv("REDIS_URL", "")
    except Exception:
        api_key = telegram_token = telegram_chat_id = db_url = redis_url = ""

    from pydantic import ValidationError

    def safe_cfg(cfg_type, **kw):
        try:
            return cfg_type(**kw)
        except (ValueError, ValidationError):
            return cfg_type.model_construct(**dict.fromkeys(kw, ""))

    return (
        safe_cfg(IgnavConfig, api_key=api_key),
        safe_cfg(TelegramConfig, token=telegram_token, chat_id=telegram_chat_id),
        AppConfig(),
        DatabaseConfig(url=db_url, redis_url=redis_url),
        SecurityConfig(
            jwt_secret=os.getenv("JWT_SECRET", "change_this"),
            dashboard_url=os.getenv("DASHBOARD_URL", "http://localhost:8000"),
            admin_chat_ids=os.getenv("ADMIN_CHAT_IDS", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            stripe_price_premium=os.getenv("STRIPE_PRICE_PREMIUM", ""),
            stripe_price_pro=os.getenv("STRIPE_PRICE_PRO", ""),
            nequi_api_url=os.getenv("NEQUI_API_URL", ""),
            nequi_api_token=os.getenv("NEQUI_API_TOKEN", ""),
            crypto_wallet_usdt=os.getenv("CRYPTO_WALLET_USDT", ""),
            crypto_wallet_btc=os.getenv("CRYPTO_WALLET_BTC", ""),
            api_requests_limit_free=int(os.getenv("API_REQUESTS_LIMIT_FREE", "10")),
            api_requests_limit_premium=int(os.getenv("API_REQUESTS_LIMIT_PREMIUM", "500")),
            api_requests_limit_pro=int(os.getenv("API_REQUESTS_LIMIT_PRO", "-1")),
        ),
    )


IGNV_CFG, TELEGRAM_CFG, APP_CFG, DB_CFG, SEC_CFG = _load_config()

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

ADMIN_CHAT_IDS: list[str] = SEC_CFG.admin_chat_ids
STRIPE_SECRET_KEY: str = SEC_CFG.stripe_secret_key
STRIPE_WEBHOOK_SECRET: str = SEC_CFG.stripe_webhook_secret
STRIPE_PRICE_PREMIUM: str = SEC_CFG.stripe_price_premium
STRIPE_PRICE_PRO: str = SEC_CFG.stripe_price_pro
NEQUI_API_URL: str = SEC_CFG.nequi_api_url
NEQUI_API_TOKEN: str = SEC_CFG.nequi_api_token
CRYPTO_WALLET_USDT: str = SEC_CFG.crypto_wallet_usdt
CRYPTO_WALLET_BTC: str = SEC_CFG.crypto_wallet_btc

PRICE_HISTORY_FILE: Path = BASE_DIR / "data" / "price_history.json"
LOG_FILE: Path = BASE_DIR / "logs" / "flight_tracker.log"
DATA_DIR: Path = BASE_DIR / "data"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
_RATE_LIMIT_FILE: Path = DATA_DIR / "rate_limit.json"


def setup_logging(name: str = "flight_tracker") -> logging.Logger:
    from src.utils.logger import setup_logging as json_setup

    return json_setup(name=name, log_file=LOG_FILE, json_output=True)


def get_departure_date(days_ahead: int = 30) -> str:
    date = datetime.now() + timedelta(days=days_ahead)
    return date.strftime("%Y-%m-%d")


def build_route_key(origin: str, destination: str) -> str:
    return f"{origin}:{destination}"
