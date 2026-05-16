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
from src.utils import config
from src.utils.cache import PriceCache


def process_multi_user_commands(telegram: TelegramService, db: Database) -> None:
    commands = telegram.listen_commands(timeout=5)
    telegram.process_multi_user_commands(commands, db)


def main() -> None:
    logger = config.setup_logging()
    logger.info(f"{'=' * 50}")
    logger.info("Flight Tracker 24/7 v3.0 — Multi-User SaaS")
    logger.info(f"Running every {config.CHECK_INTERVAL_HOURS}h")
    logger.info(f"{'=' * 50}")

    if not config.API_KEY:
        logger.error("Configure IGNAV_API_KEY")
        return
    if not config.TELEGRAM_TOKEN:
        logger.error("Configure TELEGRAM_TOKEN")
        return

    api = IgnavAPIService(config.API_KEY, logger)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, logger)
    history = PriceHistory(config.PRICE_HISTORY_FILE)
    cache = PriceCache(config.REDIS_URL)

    db = None
    try:
        db = Database(config.DATABASE_URL)
        logger.info(f"Database connected: {config.DATABASE_URL}")
    except Exception as e:
        logger.warning(f"Database unavailable: {e}")
        logger.error("Cannot run without database")
        return

    user_repo = UserRepository(db)
    price_repo = PriceRepository(db)
    price_service = PriceService(api, telegram, history, user_repo, price_repo, logger)

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
