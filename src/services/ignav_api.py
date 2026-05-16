import logging
from datetime import datetime, timedelta
from typing import Optional

from src.models.flight import FlightData
from src.providers.ignav_provider import IgnavProvider
from src.utils.cache import PriceCache


logger = logging.getLogger(__name__)

AIRLINES_URLS = {
    "Avianca": "https://www.avianca.com/co/es/",
    "LATAM": "https://www.latam.com/",
    "Wingo": "https://www.wingo.com/",
    "Viva Air": "https://www.vivaair.com/",
    "JetSMART": "https://www.jetsmart.com/",
}


class IgnavAPIService:
    CURRENCY = "COP"

    def __init__(self, api_key: str, logger_obj: Optional[logging.Logger] = None) -> None:
        if not api_key:
            raise ValueError("API key is required")
        self.provider = IgnavProvider(api_key, logger_obj)
        self.cache = PriceCache()
        self.logger = logger_obj or logger

    def search_round_trip(
        self, origin: str, destination: str, departure_date: str, return_date: str, adults: int = 2
    ) -> Optional[dict]:
        cached = self.cache.search_result(origin, destination, departure_date)
        if cached:
            self.logger.info(f"Cache hit for {origin}->{destination} on {departure_date}")
            return cached
        result = self.provider.search_round_trip(origin, destination, departure_date, return_date, adults)
        if result.is_ok and result.data:
            self.cache.set_search_result(origin, destination, departure_date, result.data, ttl=3600)
            return result.data
        return None

    def search_flight(self, origin: str, destination: str, date: str) -> Optional[dict]:
        cached = self.cache.search_result(origin, destination, date)
        if cached:
            self.logger.info(f"Cache hit for {origin}->{destination} on {date}")
            return cached
        result = self.provider.search_one_way(origin, destination, date)
        if result.is_ok and result.data:
            self.cache.set_search_result(origin, destination, date, result.data, ttl=3600)
            return result.data
        return None

    def get_cheapest(self, origin: str, destination: str, date: str) -> Optional[FlightData]:
        result_dict = self.search_flight(origin, destination, date)
        if not result_dict or not result_dict.get("itineraries"):
            self.logger.info(f"No flights {origin} -> {destination} for {date}")
            return None
        flights = result_dict["itineraries"]
        if isinstance(flights, list) and flights:
            flights.sort(key=lambda x: x.get("price", {}).get("amount", float("inf")))
            flight_data = flights[0]
            if isinstance(flight_data, dict):
                return FlightData.from_ignav_response(flight_data, origin, date, destination)
            return None
        if isinstance(flights, dict):
            return FlightData.from_ignav_response(flights, origin, date, destination)
        return None

    def get_booking_link(self, ignav_id: str) -> Optional[str]:
        if not ignav_id:
            return None
        cached = self.cache.booking_link(ignav_id)
        if cached:
            self.logger.info(f"Booking link cache hit")
            return cached
        result = self.provider.get_booking_link(ignav_id)
        if result.is_ok and result.data:
            options = result.data.get("booking_options", [])
            if options:
                links = options[0].get("links", [])
                if links:
                    url = links[0].get("url", "")
                    if url:
                        self.cache.set_booking_link(ignav_id, url)
                        self.logger.info(f"Booking link found")
                        return url
        return None

    def search_cheapest_round_trip(
        self, origin: str, destination: str, departure_dates: list[str], return_days: int = 5, adults: int = 2
    ) -> Optional[FlightData]:
        best_flight: Optional[FlightData] = None
        best_price = float("inf")
        for dep_date in departure_dates:
            return_date = (datetime.strptime(dep_date, "%Y-%m-%d") + timedelta(days=return_days)).strftime("%Y-%m-%d")
            result_dict = self.search_round_trip(origin, destination, dep_date, return_date, adults)
            if not result_dict or not result_dict.get("itineraries"):
                continue
            flights = result_dict["itineraries"]
            same_airline = []
            for f in flights:
                ob = f.get("outbound", {})
                ib = f.get("inbound", {})
                oc = ob.get("carrier", "")
                ic = ib.get("carrier", "")
                if oc and ic and oc == ic:
                    same_airline.append(f)
            if same_airline:
                same_airline.sort(key=lambda x: x.get("price", {}).get("amount", float("inf")))
                cheapest = same_airline[0]
                price = cheapest.get("price", {}).get("amount", 0)
                if price < best_price:
                    best_price = price
                    best_flight = FlightData.from_ignav_response(
                        cheapest, origin, dep_date, destination, return_date=return_date
                    )
        if best_flight:
            self.logger.info(f"Best price: ${best_flight.price:,.0f}")
        return best_flight
