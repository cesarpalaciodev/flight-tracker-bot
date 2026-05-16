import logging
import time
from datetime import datetime

from src.models.price_history import PriceHistory
from src.models.database import Database
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.services.price_service import PriceService
from src.repositories.user_repository import UserRepository
from src.repositories.price_repository import PriceRepository
from src.utils.logger import get_logger
from src.utils.cache import PriceCache


log = get_logger("main_24_7")


def process_multi_user_commands(telegram: TelegramService, db: Database) -> None:
    commands = telegram.listen_commands(timeout=5)
    telegram.process_multi_user_commands(commands, db)


def main() -> None:
    log.info("Flight Tracker 24/7 v3.0 starting", extra={"ctx": {"interval_hours": config.CHECK_INTERVAL_HOURS}})

    if not config.API_KEY:
        log.error("IGNAV_API_KEY not configured")
        return
    if not config.TELEGRAM_TOKEN:
        log.error("TELEGRAM_TOKEN not configured")
        return

    api = IgnavAPIService(config.API_KEY)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    history = PriceHistory(config.PRICE_HISTORY_FILE)
    cache = PriceCache(config.REDIS_URL)

    db = None
    try:
        db = Database(config.DATABASE_URL)
        log.info("Database connected", extra={"ctx": {"url": config.DATABASE_URL}})
    except Exception as e:
        log.error(f"Database unavailable: {e}")
        return

    user_repo = UserRepository(db)
    price_repo = PriceRepository(db)
    price_service = PriceService(api, telegram, history, user_repo, price_repo)

    tick = 0
    price_service.run_check()

    while True:
        time.sleep(config.CHECK_INTERVAL_HOURS * 3600)
        tick += 1
        price_service.run_check()
        if tick % 3 == 0:
            process_multi_user_commands(telegram, db)
            tick = 0


if __name__ == "__main__":
    main()
