"""
Flight Tracker 24/7 - Buscador de vuelos a Santa Marta
Ejecuta cada hora y envía los mejores precios por Telegram.
"""

import logging
import time
from datetime import datetime, timedelta
from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.utils import config


CHECK_INTERVAL_HOURS = 8


def get_departure_dates(days_ahead_start: int = 7, days_ahead_end: int = 60, interval: int = 7) -> list:
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        date = datetime.now() + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates


def check_prices(api: IgnavAPIService, telegram: TelegramService, history: PriceHistory, logger: logging.Logger) -> None:
    results = []
    departure_dates = get_departure_dates(68, 131, 14)
    adults = 2
    return_days = 5
    
    for origin in config.ORIGINS:
        route = config.build_route_key(origin, config.DESTINATION)
        logger.info(f"Verificando {route} (ida y vuelta, {adults} personas)...")
        
        flight = api.search_cheapest_round_trip(
            origin, config.DESTINATION, departure_dates,
            return_days=return_days, adults=adults
        )
        
        if not flight:
            logger.warning(f"No se encontró vuelo para {route}")
            continue

        logger.info(f"Mejor precio: ${flight.price:,.0f} COP ({adults} personas)")
        
        booking_link = api.get_booking_link(flight.booking_link)
        
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
        telegram.send_price_summary(results, "Ida y Vuelta (2 personas, 5 noches)")


def run_check(logger: logging.Logger, api: IgnavAPIService, telegram: TelegramService, history: PriceHistory) -> None:
    logger.info("=" * 50)
    logger.info(f"Verificacion - {datetime.now()}")
    logger.info("=" * 50)
    
    check_prices(api, telegram, history, logger)
    
    logger.info("Verificacion completada")


def main() -> None:
    logger = config.setup_logging()
    
    logger.info("=" * 50)
    logger.info("Flight Tracker 24/7 - Santa Marta")
    logger.info(f"Ejecutando cada {CHECK_INTERVAL_HOURS} hora")
    logger.info(f"2 personas | Ida y Vuelta | 5 noches")
    logger.info("=" * 50)
    
    if not config.API_KEY:
        logger.error("Configura IGNAV_API_KEY en .env")
        print("\n⚠️  Configura tu API key de Ignav en .env")
        return
    
    api = IgnavAPIService(config.API_KEY, logger)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, logger)
    history = PriceHistory(config.PRICE_HISTORY_FILE)
    
    run_check(logger, api, telegram, history)
    
    logger.info(f"\nPróxima verificación en {CHECK_INTERVAL_HOURS} hora...")
    
    while True:
        time.sleep(CHECK_INTERVAL_HOURS * 3600)
        run_check(logger, api, telegram, history)


if __name__ == "__main__":
    main()