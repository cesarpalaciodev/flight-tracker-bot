import logging
import time
from datetime import datetime
from typing import Optional

import requests


AIRLINE_BOOKING_URLS = {
    "Avianca": "https://www.avianca.com/booking",
    "LATAM": "https://www.latam.com/",
    "Wingo": "https://www.wingo.com/",
    "Viva Air": "https://www.vivaair.com/",
    "JetSMART": "https://www.jetsmart.com/",
}


def create_airline_link(origin, destination, departure_date, return_date, adults=2):
    date_str = departure_date.replace("-", "")
    return_date_str = return_date.replace("-", "")
    return f"{AIRLINE_BOOKING_URLS['Avianca']}?type=roundTrip&origin={origin}&destination={destination}&outboundDate={date_str}&inboundDate={return_date_str}&adults={adults}"


class TelegramService:
    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"
    TIMEOUT = 30
    
    def __init__(self, token: str, chat_id: str, logger: Optional[logging.Logger] = None):
        self.token = token
        self.chat_id = chat_id
        self.logger = logger or logging.getLogger(__name__)
    
    def send_flight_alert(
        self,
        old_price: float,
        new_price: float,
        flight_data: dict,
        booking_link: str = ""
    ) -> bool:
        drop = old_price - new_price
        origin = flight_data.get("origin", "")
        destination = flight_data.get("destination", "")
        airline = flight_data.get("airline", "")
        date = flight_data.get("date", "")
        return_date = flight_data.get("return_date", "")
        
        text = f"🔽 PRECIO BAJO\n\n"
        text += f"✈️ {origin} → {destination}\n"
        text += f"💰 ${old_price:,.0f} → ${new_price:,.0f}\n"
        text += f"📉 Ahorro: ${drop:,.0f}\n\n"
        text += f"🏷️ {airline}\n"
        text += f"📅 Ida: {date}\n"
        if return_date:
            text += f"📅 Vuelta: {return_date}\n"
        
        if booking_link and booking_link.startswith("http"):
            text += f"\n<a href=\"{booking_link}\">🔗 Reservar</a>"
        
        return self.send_message(text)
    
    def send_message(self, text: str, parse_mode: str = "HTML", retries: int = 3) -> bool:
        url = self.BASE_URL.format(token=self.token)
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
        
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=60)
                if response.status_code == 200:
                    self.logger.info("Message sent to Telegram")
                    return True
                else:
                    self.logger.error(f"Telegram error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} - Error: {e}")
                if attempt < retries - 1:
                    time.sleep(10)
        return False
    
    def send_price_summary(self, results: list, trip_type: str) -> bool:
        flights = [r[0] for r in results]
        booking_links = {}
        for r in results:
            flight = r[0]
            link = r[1] if len(r) > 1 else ""
            airline = flight.airline
            if link and link.startswith("http") and "ignav.com" not in link and "\\" not in link and ":" not in link[:5]:
                booking_links[flight.origin] = link
            elif airline in AIRLINE_BOOKING_URLS:
                booking_links[flight.origin] = AIRLINE_BOOKING_URLS[airline]
            else:
                booking_links[flight.origin] = AIRLINE_BOOKING_URLS["Avianca"]
        
        flights.sort(key=lambda x: x.price)
        
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        text = f"✈️ MEJORES PRECIOS - SAN ANDRES\n"
        text += f"📅 Viaje: {fecha}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, flight in enumerate(flights[:3], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            
            booking_link = booking_links.get(flight.origin, AIRLINE_BOOKING_URLS.get(flight.airline, AIRLINE_BOOKING_URLS["Avianca"]))
            
            text += f"{emoji} {flight.origin} ➝ {flight.destination}\n"
            text += f"   💵 ${flight.price:,.0f} {flight.currency}\n"
            text += f"   🏷️ {flight.airline}\n"
            text += f"   📅 Ida: {flight.date} | Vuelta: {flight.return_date}\n"
            text += f"   🔗 <a href=\"{booking_link}\">COMPRAR</a>\n"
            text += "\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "💡 Los precios pueden cambiar rapidamente\n"
        text += "✨ Usa el link directo para comprar\n"
        
        return self.send_message(text)