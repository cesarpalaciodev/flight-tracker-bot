import logging
from datetime import datetime, timedelta
from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.utils import config


def get_departure_dates(
    days_ahead_start: int,
    days_ahead_end: int,
    interval: int
) -> list[str]:
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        date = datetime.now() + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates


def check_prices(
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    logger: logging.Logger
) -> None:
    results = []
    departure_dates = get_departure_dates(
        config.DAYS_AHEAD_START,
        config.DAYS_AHEAD_END,
        config.DAYS_INTERVAL
    )
    adults = config.ADULTS
    return_days = config.RETURN_DAYS

    for origin in config.ORIGINS:
        route = config.build_route_key(origin, config.DESTINATION)
        logger.info(f"Checking {route} (round-trip, {adults} adults)...")

        flight = api.search_cheapest_round_trip(
            origin, config.DESTINATION, departure_dates,
            return_days=return_days, adults=adults
        )

        if not flight:
            logger.warning(f"No flight found for {route}")
            continue

        logger.info(f"Best price: ${flight.price:,.0f} COP ({adults} adults)")

        booking_link = api.get_booking_link(flight.booking_link)

        previous = history.get_last_price(route)

        if previous is not None:
            if flight.price < previous - config.PRICE_DROP_THRESHOLD:
                logger.info(f"PRICE DROPPED! ${previous:,.0f} -> ${flight.price:,.0f}")
                telegram.send_flight_alert(
                    previous,
                    flight.price,
                    flight.to_dict(),
                    booking_link or ""
                )

        history.update_price(
            route,
            {
                "price": flight.price,
                "last_update": datetime.now().isoformat(),
                "airline": flight.airline,
                "booking_link": flight.booking_link
            }
        )

        results.append((flight, booking_link or ""))

    if results:
        telegram.send_price_summary(results, f"{config.ADULTS} personas, {config.RETURN_DAYS} noches")


def run_check(
    logger: logging.Logger,
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory
) -> None:
    logger.info("=" * 50)
    logger.info(f"Check - {datetime.now()}")
    logger.info("=" * 50)

    check_prices(api, telegram, history, logger)

    logger.info("Check completed")


def main() -> None:
    logger = config.setup_logging()

    logger.info("=" * 50)
    logger.info("Flight Tracker 24/7 - Santa Marta")
    logger.info(f"Running every {config.CHECK_INTERVAL_HOURS} hours")
    logger.info(f"{config.ADULTS} adults | Round Trip | {config.RETURN_DAYS} nights")
    logger.info("=" * 50)

    if not config.API_KEY:
        logger.error("Configure IGNAV_API_KEY in .env")
        print("\n⚠️  Configure your Ignav API key in .env")
        return

    api = IgnavAPIService(config.API_KEY, logger)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, logger)
    history = PriceHistory(config.PRICE_HISTORY_FILE)

    run_check(logger, api, telegram, history)

    logger.info(f"Next check in {config.CHECK_INTERVAL_HOURS} hours...")

    while True:
        import time as time_module
        time_module.sleep(config.CHECK_INTERVAL_HOURS * 3600)
        run_check(logger, api, telegram, history)


if __name__ == "__main__":
    main()