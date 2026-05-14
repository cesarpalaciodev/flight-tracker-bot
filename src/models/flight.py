from dataclasses import dataclass
from typing import Optional


@dataclass
class FlightData:
    origin: str
    destination: str
    price: float
    currency: str
    airline: str
    departure_time: str
    arrival_time: str
    departure_airport: str
    arrival_airport: str
    booking_link: str
    date: str
    return_date: str = ""
    outbound_airline: str = ""
    inbound_airline: str = ""
    outbound_flight: str = ""
    inbound_flight: str = ""
    
    def to_dict(self) -> dict:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "price": self.price,
            "currency": self.currency,
            "airline": self.airline,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "departure_airport": self.departure_airport,
            "arrival_airport": self.arrival_airport,
            "booking_link": self.booking_link,
            "date": self.date,
            "return_date": self.return_date,
            "outbound_airline": self.outbound_airline,
            "inbound_airline": self.inbound_airline,
            "outbound_flight": self.outbound_flight,
            "inbound_flight": self.inbound_flight
        }
    
    @classmethod
    def from_ignav_response(
        cls,
        data: dict,
        origin: str,
        date: str,
        destination: str = "SMR",
        return_date: str = ""
    ) -> Optional["FlightData"]:
        try:
            price_info = data.get("price", {})
            
            outbound = data.get("outbound", {})
            inbound = data.get("inbound", {})
            
            outbound_carrier = outbound.get("carrier", "N/A")
            inbound_carrier = inbound.get("carrier", "N/A")
            
            outbound_segments = outbound.get("segments", [])
            inbound_segments = inbound.get("segments", [])
            
            outbound_flight = outbound_segments[0].get("flight_number", "") if outbound_segments else ""
            inbound_flight = inbound_segments[0].get("flight_number", "") if inbound_segments else ""
            
            outbound_dep = outbound_segments[0] if outbound_segments else {}
            inbound_arr = inbound_segments[-1] if inbound_segments else {}
            
            return cls(
                origin=origin,
                destination=destination,
                price=price_info.get("amount", 0),
                currency=price_info.get("currency", "COP"),
                airline=outbound_carrier,
                departure_time=outbound_dep.get("departure_time_local", ""),
                arrival_time=inbound_arr.get("arrival_time_local", ""),
                departure_airport=outbound_dep.get("departure_airport", origin),
                arrival_airport=inbound_arr.get("arrival_airport", destination),
                booking_link=data.get("ignav_id", ""),
                date=date,
                return_date=return_date,
                outbound_airline=outbound_carrier,
                inbound_airline=inbound_carrier,
                outbound_flight=outbound_flight,
                inbound_flight=inbound_flight
            )
        except (KeyError, TypeError, AttributeError):
            return None
    
    def __str__(self) -> str:
        return f"Flight {self.origin} -> {self.destination} | ${self.price:,.0f} {self.currency} | {self.airline}"