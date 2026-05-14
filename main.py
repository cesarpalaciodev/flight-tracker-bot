"""
Flight Tracker - Buscador de vuelos a Santa Marta
Busca vuelos ida y vuelta y encuentra el precio más bajo.
"""

import logging
from datetime import datetime, timedelta
from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.utils import config


def get_departure_dates(days_ahead_start: int = 7, days_ahead_end: int = 60, interval: int = 7) -> list:
    """Genera lista de fechas de salida."""
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
    """Verifica precios ida y vuelta y notifica."""
    
    results = []
    departure_dates = get_departure_dates(7, 60, 7)
    adults = 2
    
    for origin in config.ORIGINS:
        route = config.build_route_key(origin, config.DESTINATION)
        logger.info(f"Verificando {route} (ida y vuelta, {adults} personas)...")
        
        flight = api.search_cheapest_round_trip(
            origin,
            config.DESTINATION,
            departure_dates,
            return_days=5,
            adults=adults
        )
        
        if not flight:
            logger.warning(f"No se encontró vuelo para {route}")
            continue
        
        logger.info(f"Mejor precio: ${flight.price:,.0f} ({flight.trip_type})")
        
        booking_link = api.get_booking_link(flight.booking_link)
        
        previous = history.get_last_price(route)
        
        if previous is not None:
            if flight.price < previous - config.PRICE_DROP_THRESHOLD:
                logger.info(f"¡PRECIO BAJÓ! ${previous:,.0f} -> ${flight.price:,.0f}")
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
        telegram.send_price_summary([f[0] for f in results], "Ida y Vuelta", config.API_KEY)


def main() -> None:
    """Punto de entrada principal."""
    logger = config.setup_logging()
    
    logger.info("=" * 50)
    logger.info("Flight Tracker 24/7 - Santa Marta (Ida y Vuelta)")
    logger.info("=" * 50)
    
    if not config.API_KEY:
        logger.error("Configura IGNAV_API_KEY en .env")
        print("\n⚠️  Configura tu API key de Ignav:")
        print("   1. Ve a https://ignav.com")
        print("   2. Regístrate")
        print("   3. Obtén tu API key")
        return
    
    api = IgnavAPIService(config.API_KEY, logger)
    telegram = TelegramService(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, logger)
    history = PriceHistory(config.PRICE_HISTORY_FILE)
    
    check_prices_and_notify(api, telegram, history, logger)
    
    logger.info("Búsqueda completada")


if __name__ == "__main__":
    main()