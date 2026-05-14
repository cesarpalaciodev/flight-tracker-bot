import logging
import time
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from src.models.flight import FlightData


AIRLINES_URLS = {
    "Avianca": "https://www.avianca.com/co/es/",
    "LATAM": "https://www.latam.com/",
    "Wingo": "https://www.wingo.com/",
    "Viva Air": "https://www.vivaair.com/",
}


class IgnavAPIService:
    ONE_WAY_URL = "https://ignav.com/api/fares/one-way"
    ROUND_TRIP_URL = "https://ignav.com/api/fares/round-trip"
    CURRENCY = "COP"
    TIMEOUT = 30
    
    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        self.api_key = api_key
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        })
    
    def search_round_trip(self, origin: str, destination: str, departure_date: str, return_date: str, adults: int = 2) -> Optional[dict]:
        if not self.api_key:
            self.logger.warning("API key not configured")
            return None
        
        payload = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults
        }
        
        self.logger.info(f"Searching {origin} -> {destination} (round-trip)")
        
        try:
            response = self.session.post(self.ROUND_TRIP_URL, json=payload, timeout=self.TIMEOUT)
            self.logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.error("Rate limit exceeded")
            else:
                self.logger.warning(f"API error {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            self.logger.error("Request timeout")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Connection error: {e}")
        
        return None
    
    def search_flight(self, origin: str, destination: str, date: str) -> Optional[dict]:
        if not self.api_key:
            self.logger.warning("API key not configured")
            return None
        
        payload = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": date
        }
        
        self.logger.info(f"Searching {origin} -> {destination} for {date}")
        
        try:
            response = self.session.post(self.ONE_WAY_URL, json=payload, timeout=self.TIMEOUT)
            self.logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.error("Rate limit exceeded")
            else:
                self.logger.warning(f"API error {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            self.logger.error("Request timeout")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Connection error: {e}")
        
        return None
    
    def get_cheapest(self, origin: str, destination: str, date: str) -> Optional["FlightData"]:
        from src.models.flight import FlightData
        
        result = self.search_flight(origin, destination, date)
        
        if not result or not result.get("itineraries"):
            self.logger.info(f"No flights for {origin} -> {destination}")
            return None
        
        flights = result["itineraries"]
        
        if isinstance(flights, list) and flights:
            flights.sort(key=lambda x: x.get("price", {}).get("amount", float("inf")))
            return FlightData.from_ignav_response(flights[0], origin, date, destination)
        
        return FlightData.from_ignav_response(flights, origin, date, destination)
    
    def get_booking_link(self, ignav_id: str) -> Optional[str]:
        if not ignav_id:
            return None
        
        try:
            self.logger.info(f"Getting link for: {ignav_id}")
            response = self.session.post(
                "https://ignav.com/api/fares/booking-links",
                json={"ignav_id": ignav_id},
                timeout=15
            )
            
            self.logger.info(f"Booking link response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Booking data: {data}")
                options = data.get("booking_options", [])
                if options:
                    links = options[0].get("links", [])
                    if links:
                        url = links[0].get("url", "")
                        self.logger.info(f"Link found: {url}")
                        return url
            else:
                self.logger.warning(f"Error getting link: {response.text}")
        except Exception as e:
            self.logger.error(f"Exception getting link: {e}")
        
        return None
    
    def search_cheapest_round_trip(self, origin: str, destination: str, departure_dates: list, return_days: int = 5, adults: int = 2) -> Optional["FlightData"]:
        from src.models.flight import FlightData
        
        best_flight = None
        best_price = float("inf")
        
        for dep_date in departure_dates:
            ret_date = datetime.strptime(dep_date, "%Y-%m-%d") + timedelta(days=return_days)
            return_date = ret_date.strftime("%Y-%m-%d")
            
            self.logger.info(f"Searching {origin} -> {destination}: {dep_date} - {return_date} ({adults} adults)")
            
            result = self.search_round_trip(origin, destination, dep_date, return_date, adults)
            
            if not result or not result.get("itineraries"):
                continue
            
            flights = result["itineraries"]
            
            same_airline_flights = []
            for f in flights:
                outbound = f.get("outbound", {})
                inbound = f.get("inbound", {})
                out_carrier = outbound.get("carrier", "")
                in_carrier = inbound.get("carrier", "")
                if out_carrier and in_carrier and out_carrier == in_carrier:
                    same_airline_flights.append(f)
            
            if same_airline_flights:
                same_airline_flights.sort(key=lambda x: x.get("price", {}).get("amount", float("inf")))
                cheapest = same_airline_flights[0]
                price = cheapest.get("price", {}).get("amount", 0)
                
                if price < best_price:
                    best_price = price
                    best_flight = FlightData.from_ignav_response(cheapest, origin, dep_date, destination, return_date=return_date)
        
        if best_flight:
            self.logger.info(f"Best price: ${best_flight.price:,.0f} COP ({adults} adults)")
        
        return best_flight