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


SENT_PRICE_SUMMARY = False


def get_departure_dates(
    days_ahead_start: int, days_ahead_end: int, interval: int
) -> list[str]:
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        dates.append((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"))
    return dates


def check_prices(
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    logger: logging.Logger,
    db: Optional[Database] = None,
) -> None:
    global SENT_PRICE_SUMMARY
    SENT_PRICE_SUMMARY = False
    results = []
    departure_dates = get_departure_dates(
        config.DAYS_AHEAD_START, config.DAYS_AHEAD_END, config.DAYS_INTERVAL
    )

    for destination in config.DESTINATIONS:
        for origin in config.ORIGINS:
            route = config.build_route_key(origin, destination)
            logger.info(f"Checking {route} ({config.ADULTS} adults)...")

            flight = api.search_cheapest_round_trip(
                origin, destination, departure_dates,
                return_days=config.RETURN_DAYS, adults=config.ADULTS
            )

            if not flight:
                logger.info(f"No results for {route}")
                continue

            logger.info(f"Best price: ${flight.price:,.0f} COP")

            booking_link = api.get_booking_link(flight.booking_link)
            time.sleep(2)

            previous = history.get_last_price(route)
            if previous is not None:
                price_diff = flight.price - previous

                if price_diff < 0 and abs(price_diff) >= config.PRICE_DROP_THRESHOLD:
                    logger.info(f"PRICE DROPPED! ${previous:,.0f} → ${flight.price:,.0f}")
                    telegram.send_flight_alert(previous, flight.price, flight.to_dict(), booking_link or "")
                    if db:
                        db.log_alert(route, "price_drop", previous, flight.price, previous - flight.price)

                elif price_diff > config.PRICE_INCREASE_THRESHOLD > 0:
                    logger.info(f"PRICE INCREASED! ${previous:,.0f} → ${flight.price:,.0f}")
                    telegram.send_flight_alert(previous, flight.price, flight.to_dict(), booking_link or "")
                    if db:
                        db.log_alert(route, "price_increase", previous, flight.price, flight.price - previous)

            history.update_price(route, {
                "price": flight.price,
                "last_update": datetime.now().isoformat(),
                "airline": flight.airline,
                "booking_link": flight.booking_link,
            })

            if db:
                db.save_price(
                    route, origin, destination, flight.price,
                    flight.currency, flight.airline,
                    flight.date, flight.return_date, booking_link or "",
                )

            results.append((flight, booking_link or ""))

    if results and not SENT_PRICE_SUMMARY:
        logger.info("Sending price summary...")
        telegram.send_price_summary(results, f"{config.ADULTS} adults, {config.RETURN_DAYS} nights")
        SENT_PRICE_SUMMARY = True


def run_check(logger: logging.Logger, api: IgnavAPIService, telegram: TelegramService,
              history: PriceHistory, db: Optional[Database] = None) -> None:
    logger.info(f"{'=' * 50}\nCheck - {datetime.now()}\n{'=' * 50}")
    check_prices(api, telegram, history, logger, db)
    logger.info("Check completed")


def process_commands(telegram: TelegramService, db: Optional[Database] = None) -> None:
    commands = telegram.listen_commands(timeout=5)
    for cmd in commands:
        chat_id = cmd["chat_id"]
        command = cmd["command"]
        args = cmd["args"]

        if command == "/help":
            telegram.send_help(chat_id)
        elif command == "/config":
            telegram.send_config(chat_id, db)
        elif command in ("/start", "/status"):
            telegram.send_message("✅ Flight Tracker activo\n\nUsa /help para comandos")
        elif command == "/set_origins" and args:
            origins = [o.strip().upper() for o in " ".join(args).split(",")]
            telegram.send_message(f"✅ Orígenes actualizados: {', '.join(origins)}")
            if db:
                db.set_user_config(chat_id, origins=",".join(origins))
        elif command == "/set_destinations" and args:
            dests = [d.strip().upper() for d in " ".join(args).split(",")]
            telegram.send_message(f"✅ Destinos actualizados: {', '.join(dests)}")
        elif command == "/set_adults" and args:
            try:
                adults = int(args[0])
                if 1 <= adults <= 9:
                    telegram.send_message(f"✅ Pasajeros: {adults}")
            except ValueError:
                telegram.send_message("❌ Usa: /set_adults NUMERO")
        elif command == "/set_days" and args:
            try:
                days = int(args[0])
                if 1 <= days <= 90:
                    telegram.send_message(f"✅ Días de viaje: {days}")
            except ValueError:
                telegram.send_message("❌ Usa: /set_days NUMERO")
        elif command == "/set_threshold" and args:
            try:
                th = float(args[0])
                telegram.send_message(f"✅ Umbral de alerta: ${th:,.0f} COP")
            except ValueError:
                telegram.send_message("❌ Usa: /set_threshold MONTO")
        elif command in ("/price", "/prices"):
            from src.utils import config as cfg
            history = PriceHistory(cfg.PRICE_HISTORY_FILE)
            for dest in cfg.DESTINATIONS:
                text = f"📊 <b>Últimos precios - {dest}</b>\n\n"
                for origin in cfg.ORIGINS:
                    route = cfg.build_route_key(origin, dest)
                    price = history.get_last_price(route)
                    if price:
                        text += f"✈️ {origin} → {dest}: <b>${price:,.0f}</b>\n"
                    else:
                        text += f"✈️ {origin} → {dest}: <b>Sin datos</b>\n"
                telegram._send_text(chat_id, text)
        elif command == "/stats":
            stats = {"total_searches": 0, "total_alerts": 0, "lowest_price": 0,
                     "highest_price": 0, "airlines_count": 0, "uptime": "N/A"}
            from src.utils.metrics import FLIGHTS_SEARCHED, PRICE_ALERTS_SENT
            stats["total_searches"] = int(FLIGHTS_SEARCHED._value.get())
            stats["total_alerts"] = int(PRICE_ALERTS_SENT._value.get())
            telegram.send_stats(chat_id, stats)


def main() -> None:
    logger = config.setup_logging()

    logger.info(f"{'=' * 50}")
    logger.info(f"Flight Tracker 24/7 v2.0")
    logger.info(f"Destinations: {', '.join(config.DESTINATIONS)}")
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
        logger.warning(f"Database unavailable (continuing without DB): {e}")

    tick = 0
    run_check(logger, api, telegram, history, db)

    while True:
        time.sleep(config.CHECK_INTERVAL_HOURS * 3600)
        tick += 1
        run_check(logger, api, telegram, history, db)

        if tick % 3 == 0:
            process_commands(telegram, db)
            tick = 0


if __name__ == "__main__":
    main()