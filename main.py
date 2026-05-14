"""
Flight Tracker - Searches for cheap flights to Santa Marta.
Finds lowest round-trip prices.
"""

import logging
from datetime import datetime, timedelta
from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.utils import config


def get_departure_dates(days_ahead_start: int = 7, days_ahead_end: int = 60, interval: int = 7) -> list:
    """Generates list of departure dates."""
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        date = datetime.now() + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates


def check_prices_and_notify(
    api: IgnavAPIService,
    telegram: TelegramService,
    history: PriceHistory,
    logger: logging.Logger
) -> None:
    """Checks round-trip prices and sends notifications."""
    
    results = []
    departure_dates = get_departure_dates(7, 60, 7)
    adults = 2
    
    for origin in config.ORIGINS:
        route = config.build_route_key(origin, config.DESTINATION)
        logger.info(f"Checking {route} (round-trip, {adults} adults)...")
        
        flight = api.search_cheapest_round_trip(
            origin,
            config.DESTINATION,
            departure_dates,
            return_days=5,
            adults=adults
        )
        
        if not flight:
            logger.warning(f"No flight found for {route}")
            continue
        
        logger.info(f"Best price: ${flight.price:,.0f} COP")
        
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
        telegram.send_price_summary(results, "Ida y Vuelta")


def main() -> None:
    """Main entry point."""
    logger = config.setup_logging()
    
    logger.info("=" * 50)
    logger.info("Flight Tracker - Santa Marta (Round Trip)")
    logger.info("=" * 50)
    
    if not config.API_KEY:
        logger.error("Configure IGNAV_API_KEY in .env")
        print("\n⚠️  Configure your Ignav API key:")
        print("   1. Go to https://ignav.com")
        print("   2. Register")
        print("   3. Get your API key")
        return
    
    api = IgnavAPIService(config.API_KEY, logger)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, logger)
    history = PriceHistory(config.PRICE_HISTORY_FILE)
    
    check_prices_and_notify(api, telegram, history, logger)
    
    logger.info("Search completed")


if __name__ == "__main__":
    main()