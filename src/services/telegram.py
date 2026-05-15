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


def create_airline_link(
    origin: str, destination: str, departure_date: str, return_date: str, adults: int = 2
) -> str:
    date_str = departure_date.replace("-", "")
    return_date_str = return_date.replace("-", "")
    return (
        f"{AIRLINE_BOOKING_URLS['Avianca']}"
        f"?type=roundTrip&origin={origin}&destination={destination}"
        f"&outboundDate={date_str}&inboundDate={return_date_str}&adults={adults}"
    )


class TelegramService:
    BASE_URL = "https://api.telegram.org/bot{token}"
    TIMEOUT = 30

    def __init__(self, token: str, chat_id: str | list[str] = "",
                 logger: Optional[logging.Logger] = None) -> None:
        if not token:
            raise ValueError("Telegram token is required")
        self.token = token
        self.chat_ids: list[str] = [chat_id] if isinstance(chat_id, str) and chat_id else (chat_id if isinstance(chat_id, list) else [])
        self.logger = logger or logging.getLogger(__name__)
        self._last_update_id = 0

    def add_chat(self, chat_id: str) -> None:
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML", retries: int = 3) -> bool:
        url = f"{self.BASE_URL.format(token=self.token)}/sendMessage"
        payload = {"text": text, "parse_mode": parse_mode}
        success = False
        for chat_id in self.chat_ids:
            payload["chat_id"] = chat_id
            for attempt in range(retries):
                try:
                    response = requests.post(url, json=payload, timeout=60)
                    if response.status_code == 200:
                        self.logger.info(f"Message sent to {chat_id}")
                        success = True
                        break
                    self.logger.error(f"Telegram error {response.status_code} for {chat_id}")
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Attempt {attempt + 1} to {chat_id}: {e}")
                    if attempt < retries - 1:
                        time.sleep(10)
        return success

    def listen_commands(self, timeout: int = 30) -> list[dict]:
        url = f"{self.BASE_URL.format(token=self.token)}/getUpdates"
        try:
            resp = requests.get(
                url,
                params={"offset": self._last_update_id + 1, "timeout": timeout},
                timeout=timeout + 5
            )
            if resp.status_code == 200:
                data = resp.json()
                commands = []
                for update in data.get("result", []):
                    self._last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "").strip()
                    if text.startswith("/"):
                        commands.append({
                            "chat_id": str(msg["chat"]["id"]),
                            "command": text.split()[0].lower(),
                            "args": text.split()[1:],
                            "full_text": text,
                            "from": msg.get("from", {}),
                        })
                        if str(msg["chat"]["id"]) not in self.chat_ids:
                            self.chat_ids.append(str(msg["chat"]["id"]))
                return commands
        except Exception as e:
            self.logger.debug(f"GetUpdates failed: {e}")
        return []

    def send_flight_alert(self, old_price: float, new_price: float,
                          flight_data: dict, booking_link: str = "") -> bool:
        drop = old_price - new_price
        origin = flight_data.get("origin", "")
        dest = flight_data.get("destination", "")
        airline = flight_data.get("airline", "")
        date = flight_data.get("date", "")
        return_date = flight_data.get("return_date", "")

        if drop > 0:
            emoji, label = "🔽", "PRECIO BAJO"
        else:
            emoji, label = "🔼", "PRECIO SUBIO"

        text = f"{emoji} {label}\n\n"
        text += f"✈️ {origin} → {dest}\n"
        text += f"💰 ${old_price:,.0f} → ${new_price:,.0f}\n"
        text += f"📉 Diferencia: ${abs(drop):,.0f}\n\n"
        text += f"🏷️ {airline}\n"
        text += f"📅 Ida: {date}\n"
        if return_date:
            text += f"📅 Vuelta: {return_date}\n"
        if booking_link and booking_link.startswith("http"):
            text += f"\n🔗 <a href=\"{booking_link}\">Reservar</a>"
        text += "\n\n💡 Configura alertas con /help"
        return self.send_message(text)

    def send_price_summary(self, results: list, trip_type: str) -> bool:
        flights = [r[0] for r in results]
        booking_links = {}
        for r in results:
            flight = r[0]
            link = r[1] if len(r) > 1 else ""
            airline = flight.airline
            if (link and link.startswith("http") and "ignav.com" not in link
                    and "\\" not in link and ":" not in link[:5]):
                booking_links[flight.origin] = link
            elif airline in AIRLINE_BOOKING_URLS:
                booking_links[flight.origin] = AIRLINE_BOOKING_URLS[airline]
            else:
                booking_links[flight.origin] = AIRLINE_BOOKING_URLS["Avianca"]

        flights.sort(key=lambda x: x.price)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        text = f"✈️ MEJORES PRECIOS\n📅 {now}\n" + "━" * 25 + "\n\n"
        for i, flight in enumerate(flights[:5], 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1] if i <= 5 else f"{i}."
            link = booking_links.get(
                flight.origin,
                AIRLINE_BOOKING_URLS.get(flight.airline, AIRLINE_BOOKING_URLS["Avianca"])
            )
            text += f"{emoji} {flight.origin} → {flight.destination}\n"
            text += f"   💵 ${flight.price:,.0f} {flight.currency}\n"
            text += f"   🏷️ {flight.airline}\n"
            text += f"   📅 {flight.date} → {flight.return_date}\n"
            text += f"   🔗 <a href=\"{link}\">COMPRAR</a>\n\n"
        text += "━" * 25 + "\n"
        text += "💡 Los precios pueden cambiar rapidamente\n"
        text += "✨ /config para personalizar\n"
        text += "🔄 Próximo check en 8h"
        return self.send_message(text)

    def send_help(self, chat_id: str) -> bool:
        text = (
            "🤖 <b>Flight Tracker Comandos</b>\n\n"
            "/start - Iniciar bot\n"
            "/help - Mostrar comandos\n"
            "/config - Ver configuración\n"
            "/set_origins MDE,BOG,PEI - Cambiar orígenes\n"
            "/set_destinations ADZ,CTG - Cambiar destinos\n"
            "/set_adults 2 - Cambiar pasajeros\n"
            "/set_days 5 - Cambiar días de viaje\n"
            "/set_threshold 50000 - Umbral alerta (COP)\n"
            "/price - Ver últimos precios\n"
            "/history - Historial de precios\n"
            "/status - Estado del bot\n"
            "/stats - Estadísticas generales"
        )
        return self._send_text(chat_id, text)

    def send_config(self, chat_id: str, db: object = None) -> bool:
        config = (
            "⚙️ <b>Tu Configuración</b>\n\n"
            f"✈️ Orígenes: MDE, PEI\n"
            f"📍 Destinos: ADZ\n"
            f"👥 Pasajeros: 2\n"
            f"📅 Días de viaje: 5\n"
            f"📉 Umbral baja precio: activado\n"
            f"📈 Alerta de subida: activado\n\n"
            "Usa /help para comandos disponibles"
        )
        if db:
            try:
                from src.models.database import Database
                if isinstance(db, Database):
                    uc = db.get_user_config(chat_id)
                    if uc:
                        config = (
                            "⚙️ <b>Tu Configuración</b>\n\n"
                            f"✈️ Orígenes: {uc.origins}\n"
                            f"📍 Destinos: {uc.destinations}\n"
                            f"👥 Pasajeros: {uc.adults}\n"
                            f"📅 Días: {uc.return_days}\n"
                            f"📉 Umbral baja: ${uc.price_drop_threshold:,.0f}\n"
                            f"📈 Alerta subida: activada\n"
                            f"🔔 Estado: {'Activo' if uc.enabled else 'Pausado'}\n\n"
                            "Usa /help para comandos"
                        )
            except Exception:
                pass
        return self._send_text(chat_id, config)

    def send_stats(self, chat_id: str, stats: dict) -> bool:
        text = (
            "📊 <b>Flight Tracker Stats</b>\n\n"
            f"🔍 Vuelos buscados: {stats.get('total_searches', 0)}\n"
            f"📉 Alertas enviadas: {stats.get('total_alerts', 0)}\n"
            f"💰 Precio más bajo: ${stats.get('lowest_price', 0):,.0f}\n"
            f"💵 Precio más alto: ${stats.get('highest_price', 0):,.0f}\n"
            f"🛩️ Aerolíneas seguidas: {stats.get('airlines_count', 0)}\n"
            f"🔄 Próximo check: en 8h\n"
            f"⏱️ Uptime: {stats.get('uptime', 'N/A')}"
        )
        return self._send_text(chat_id, text)

    def _send_text(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        url = f"{self.BASE_URL.format(token=self.token)}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False