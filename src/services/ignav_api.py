import logging
from datetime import datetime, timedelta
from typing import Optional

import requests

from src.models.flight import FlightData
from src.utils.rate_limiter import RateLimiter
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
    ONE_WAY_URL = "https://ignav.com/api/fares/one-way"
    ROUND_TRIP_URL = "https://ignav.com/api/fares/round-trip"
    CURRENCY = "COP"
    TIMEOUT = 30

    def __init__(self, api_key: str, logger_obj: Optional[logging.Logger] = None) -> None:
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.logger = logger_obj or logger
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": api_key, "Content-Type": "application/json"})
        self.rate_limiter = RateLimiter()
        self.cache = PriceCache()

    def _check_rate_limit(self) -> bool:
        allowed, msg = self.rate_limiter.is_allowed()
        if not allowed:
            self.logger.warning(msg)
            self.rate_limiter.wait_if_needed(self.logger)
            return False
        return True

    def _request(self, url: str, payload: dict) -> Optional[dict]:
        if not self._check_rate_limit():
            return None
        try:
            self.logger.info(f"POST {url.split('/')[-1]} {payload.get('origin', '')}->{payload.get('destination', '')}")
            response = self.session.post(url, json=payload, timeout=self.TIMEOUT)
            self.rate_limiter.record_request()
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.error("API rate limit exceeded (429)")
                self.rate_limiter.wait_if_needed(self.logger)
                return None
            else:
                self.logger.warning(f"API error {response.status_code}: {response.text[:200]}")
                return None
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout ({self.TIMEOUT}s)")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None

    def search_round_trip(
        self, origin: str, destination: str, departure_date: str, return_date: str, adults: int = 2
    ) -> Optional[dict]:
        payload = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
        }
        cached = self.cache.search_result(origin, destination, departure_date)
        if cached:
            self.logger.info(f"Cache hit for {origin}->{destination} on {departure_date}")
            return cached
        result = self._request(self.ROUND_TRIP_URL, payload)
        if result:
            self.cache.set_search_result(origin, destination, departure_date, result, ttl=3600)
        return result

    def get_cheapest(self, origin: str, destination: str, date: str) -> Optional[FlightData]:
        result = self.search_flight(origin, destination, date)
        if not result or not result.get("itineraries"):
            self.logger.info(f"No flights {origin} -> {destination} for {date}")
            return None
        flights = result["itineraries"]
        if isinstance(flights, list) and flights:
            flights.sort(key=lambda x: x.get("price", {}).get("amount", float("inf")))
            flight_data = flights[0]
            if isinstance(flight_data, dict):
                return FlightData.from_ignav_response(flight_data, origin, date, destination)
            return None
        if isinstance(flights, dict):
            return FlightData.from_ignav_response(flights, origin, date, destination)
        return None

    def search_flight(self, origin: str, destination: str, date: str) -> Optional[dict]:
        payload = {"origin": origin.upper(), "destination": destination.upper(), "departure_date": date}
        cached = self.cache.search_result(origin, destination, date)
        if cached:
            self.logger.info(f"Cache hit for {origin}->{destination} on {date}")
            return cached
        result = self._request(self.ONE_WAY_URL, payload)
        if result:
            self.cache.set_search_result(origin, destination, date, result, ttl=3600)
        return result

    def get_booking_link(self, ignav_id: str) -> Optional[str]:
        if not ignav_id:
            return None
        cached = self.cache.booking_link(ignav_id)
        if cached:
            self.logger.info(f"Booking link cache hit: {cached}")
            return cached
        try:
            self.logger.info(f"Getting booking link for: {ignav_id}")
            response = self.session.post(
                "https://ignav.com/api/fares/booking-links", json={"ignav_id": ignav_id}, timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                options = data.get("booking_options", [])
                if options:
                    links = options[0].get("links", [])
                    if links:
                        url = links[0].get("url", "")
                        if url:
                            self.cache.set_booking_link(ignav_id, url)
                            self.logger.info(f"Booking link found: {url[:80]}...")
                            return url
            self.logger.warning(f"Booking link error {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout:
            self.logger.warning("Booking link timeout")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Booking link request failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting booking link: {e}")
        return None

    def search_cheapest_round_trip(
        self, origin: str, destination: str, departure_dates: list[str], return_days: int = 5, adults: int = 2
    ) -> Optional[FlightData]:
        best_flight: Optional[FlightData] = None
        best_price = float("inf")
        for dep_date in departure_dates:
            return_date = (datetime.strptime(dep_date, "%Y-%m-%d") + timedelta(days=return_days)).strftime("%Y-%m-%d")
            result = self.search_round_trip(origin, destination, dep_date, return_date, adults)
            if not result or not result.get("itineraries"):
                continue
            flights = result["itineraries"]
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
