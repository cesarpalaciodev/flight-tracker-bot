import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent.parent.parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("IGNAV_API_KEY", "")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DESTINATION = "ADZ"
ORIGINS = ["MDE", "PEI"]

PRICE_HISTORY_FILE = BASE_DIR / "data" / "price_history.json"
LOG_FILE = BASE_DIR / "logs" / "flight_tracker.log"

PRICE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

PRICE_DROP_THRESHOLD = 1


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("flight_tracker")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
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