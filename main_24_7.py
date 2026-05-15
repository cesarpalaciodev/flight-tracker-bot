import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.models.database import Database
from src.utils import config
from src.utils.cache import PriceCache
from src.utils.exceptions import FlightTrackerError, handle_api_error
from src.utils.metrics import FLIGHTS_SEARCHED, PRICE_CHECKS, PRICE_ALERTS_SENT


def get_departure_dates(days_ahead_start: int, days_ahead_end: int, interval: int) -> list[str]:
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        dates.append((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"))
    return dates


def check_prices_for_user(
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    logger: logging.Logger,
    db: Database,
    chat_id: str,
) -> None:
    user = db.get_user_config(chat_id)
    if not user or not user.active:
        return

    sub = db.get_subscription(chat_id)
    if sub and sub.api_requests_limit > 0 and sub.api_requests_month >= sub.api_requests_limit:
        logger.info(f"User {chat_id} has reached API limit ({sub.api_requests_month}/{sub.api_requests_limit})")
        if sub.status == "trial":
            telegram.send_to(chat_id, "⚠️ Has alcanzado el límite de tu prueba gratis. /subscribe para continuar.")
        return

    origins = [o.strip() for o in user.origins.split(",")]
    destinations_list = [d.strip() for d in user.destinations.split(",")]
    results = []
    departure_dates = get_departure_dates(config.DAYS_AHEAD_START, config.DAYS_AHEAD_END, config.DAYS_INTERVAL)

    for dest in destinations_list:
        for origin in origins:
            route = config.build_route_key(origin, dest)
            logger.info(f"[{chat_id}] Checking {route} ({user.adults} adults)...")

            flight = api.search_cheapest_round_trip(
                origin, dest, departure_dates, return_days=user.return_days, adults=user.adults
            )

            if not flight:
                logger.info(f"[{chat_id}] No results for {route}")
                continue

            logger.info(f"[{chat_id}] Best price: ${flight.price:,.0f}")

            booking_link = api.get_booking_link(flight.booking_link)
            time.sleep(2)

            luggage_match = 0
            budget_match = 0
            if user.luggage and user.luggage != "carry_on":
                luggage_match = 1
            if user.max_budget and flight.price <= user.max_budget:
                budget_match = 1

            previous = history.get_last_price(f"{chat_id}:{route}")
            if previous is not None:
                price_diff = flight.price - previous
                if price_diff < 0 and abs(price_diff) >= (user.price_drop_threshold or config.PRICE_DROP_THRESHOLD):
                    logger.info(f"[{chat_id}] PRICE DROPPED! ${previous:,.0f} → ${flight.price:,.0f}")
                    telegram.send_flight_alert(
                        previous, flight.price, flight.to_dict(), booking_link or "", chat_id=chat_id
                    )
                    db.log_alert(chat_id, route, "price_drop", previous, flight.price, previous - flight.price)
                    PRICE_ALERTS_SENT.inc()
                elif price_diff > config.PRICE_INCREASE_THRESHOLD > 0:
                    logger.info(f"[{chat_id}] PRICE INCREASED! ${previous:,.0f} → ${flight.price:,.0f}")
                    telegram.send_flight_alert(
                        previous, flight.price, flight.to_dict(), booking_link or "", chat_id=chat_id
                    )
                    db.log_alert(chat_id, route, "price_increase", previous, flight.price, flight.price - previous)
                    PRICE_ALERTS_SENT.inc()

            history.update_price(
                f"{chat_id}:{route}",
                {
                    "price": flight.price,
                    "last_update": datetime.now().isoformat(),
                    "airline": flight.airline,
                    "booking_link": flight.booking_link,
                },
            )

            db.save_price(
                chat_id,
                route,
                origin,
                dest,
                flight.price,
                flight.currency,
                flight.airline,
                flight.date,
                flight.return_date,
                booking_link or "",
                luggage_match,
                budget_match,
            )
            FLIGHTS_SEARCHED.inc()
            results.append((flight, booking_link or ""))

    if sub:
        search_count = len(results)
        db.set_subscription(chat_id, api_requests_month=(sub.api_requests_month or 0) + max(1, search_count))

    if results:
        logger.info(f"[{chat_id}] Sending price summary...")
        telegram.send_price_summary(results, chat_id=chat_id)
        PRICE_ALERTS_SENT.inc()


def check_all_users(
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    logger: logging.Logger,
    db: Optional[Database] = None,
) -> None:
    if not db:
        return
    users = db.get_all_active_users()
    logger.info(f"Checking prices for {len(users)} active users")
    for user in users:
        try:
            check_prices_for_user(api, telegram, history, logger, db, user.chat_id)
        except Exception as e:
            logger.error(f"Error checking for user {user.chat_id}: {e}")


def run_check(
    logger: logging.Logger,
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    db: Optional[Database] = None,
) -> None:
    logger.info(f"{'=' * 50}\nMulti-user check - {datetime.now()}\n{'=' * 50}")
    check_all_users(api, telegram, history, logger, db)
    logger.info("Check completed")


def process_multi_user_commands(telegram: TelegramService, db: Optional[Database] = None) -> None:
    if not db:
        return
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

    tick = 0
    run_check(logger, api, telegram, history, db)

    while True:
        time.sleep(config.CHECK_INTERVAL_HOURS * 3600)
        tick += 1
        run_check(logger, api, telegram, history, db)
        if tick % 3 == 0:
            process_multi_user_commands(telegram, db)
            tick = 0


if __name__ == "__main__":
    main()
