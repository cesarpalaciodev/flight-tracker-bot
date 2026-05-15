import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import requests


AIRLINE_BOOKING_URLS = {
    "Avianca": "https://www.avianca.com/booking",
    "LATAM": "https://www.latam.com/",
    "Wingo": "https://www.wingo.com/",
    "Viva Air": "https://www.vivaair.com/",
    "JetSMART": "https://www.jetsmart.com/",
}


class TelegramService:
    BASE_URL = "https://api.telegram.org/bot{token}"
    TIMEOUT = 30

    ONBOARDING_STEPS = [
        {
            "key": "origins",
            "question": "Paso 1/6: ¿Desde qué ciudad(es) viajas?\nEj: MDE, BOG, PEI (separadas por comas)",
        },
        {"key": "destinations", "question": "Paso 2/6: ¿A dónde quieres ir?\nEj: ADZ, CTG, BOG (separadas por comas)"},
        {"key": "dates", "question": "Paso 3/6: ¿Fechas aproximadas?\nEj: junio 2026 o 'flexible'"},
        {"key": "passengers", "question": "Paso 4/6: ¿Cuántas personas y equipaje?\nEj: '2 adultos, maleta de mano'"},
        {"key": "budget", "question": "Paso 5/6: ¿Presupuesto máximo por persona?\nEj: 600000 o 'sin límite'"},
        {"key": "non_stop", "question": "Paso 6/6: ¿Solo vuelos directos? (sí/no)"},
    ]

    def __init__(self, token: str, chat_id: str | list[str] = "", logger: Optional[logging.Logger] = None) -> None:
        if not token:
            raise ValueError("Telegram token is required")
        self.token = token
        self.chat_ids: list[str] = (
            [chat_id]
            if isinstance(chat_id, str) and chat_id
            else (chat_id if isinstance(chat_id, list) else [])
            if chat_id
            else []
        )
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
            for _ in range(retries):
                try:
                    r = requests.post(url, json=payload, timeout=60)
                    if r.status_code == 200:
                        self.logger.info(f"Message sent to {chat_id}")
                        success = True
                        break
                    self.logger.error(f"Telegram error {r.status_code} for {chat_id}: {r.text[:200]}")
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Request error to {chat_id}: {e}")
                    time.sleep(5)
        return success

    def send_to(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        url = f"{self.BASE_URL.format(token=self.token)}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}, timeout=10)
            if r.status_code == 200:
                self.logger.info(f"Sent to {chat_id}")
                return True
            self.logger.error(f"Telegram error {r.status_code} sending to {chat_id}: {r.text[:200]}")
            return False
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout sending to {chat_id}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error sending to {chat_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending to {chat_id}: {e}")
            return False

    def listen_commands(self, timeout: int = 30) -> list[dict]:
        url = f"{self.BASE_URL.format(token=self.token)}/getUpdates"
        try:
            resp = requests.get(
                url, params={"offset": self._last_update_id + 1, "timeout": timeout}, timeout=timeout + 5
            )
            if resp.status_code == 200:
                data = resp.json()
                commands = []
                for update in data.get("result", []):
                    self._last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "").strip()
                    chat_id = str(msg["chat"]["id"])
                    if chat_id not in self.chat_ids:
                        self.chat_ids.append(chat_id)
                    commands.append(
                        {
                            "chat_id": chat_id,
                            "text": text,
                            "command": text.split()[0].lower() if text.startswith("/") else "",
                            "args": text.split()[1:] if text.startswith("/") else [],
                            "from": msg.get("from", {}),
                        }
                    )
                return commands
        except Exception as e:
            self.logger.debug(f"GetUpdates failed: {e}")
        return []

    def handle_onboarding(self, chat_id: str, text: str, db) -> Optional[str]:
        user = db.get_or_create_user(chat_id)
        step = user.onboarding_step
        if step == 0:
            db.set_user_config(chat_id, onboarding_step=1)
            return self.ONBOARDING_STEPS[0]["question"]
        elif step == 1:
            origins = [o.strip().upper() for o in text.replace(",", " ").split()]
            db.set_user_config(chat_id, origins=",".join(origins), onboarding_step=2)
            return self.ONBOARDING_STEPS[1]["question"]
        elif step == 2:
            dests = [d.strip().upper() for d in text.replace(",", " ").split()]
            db.set_user_config(chat_id, destinations=",".join(dests), onboarding_step=3)
            return self.ONBOARDING_STEPS[2]["question"]
        elif step == 3:
            db.set_user_config(chat_id, onboarding_step=4)
            return self.ONBOARDING_STEPS[3]["question"]
        elif step == 4:
            luggage = "carry_on"
            adults = 2
            text_lower = text.lower()
            if "mano" in text_lower or "carry" in text_lower:
                luggage = "carry_on"
            elif "bodega" in text_lower or "checked" in text_lower:
                luggage = "checked"
            elif "ambas" in text_lower or "both" in text_lower:
                luggage = "both"
            for word in text_lower.split():
                if word.isdigit() and 1 <= int(word) <= 9:
                    adults = int(word)
                    break
            db.set_user_config(chat_id, adults=adults, luggage=luggage, onboarding_step=5)
            return self.ONBOARDING_STEPS[4]["question"]
        elif step == 5:
            text_clean = text.replace("$", "").replace(",", "").replace(".", "").strip()
            budget = None
            if text_clean.isdigit():
                budget = float(text_clean)
            db.set_user_config(chat_id, max_budget=budget, onboarding_step=6)
            return self.ONBOARDING_STEPS[5]["question"]
        elif step == 6:
            non_stop = 1 if text.lower() in ("sí", "si", "yes", "s") else 0
            db.set_user_config(chat_id, non_stop_only=non_stop, onboarding_step=0, onboarded=1)
            sub = db.get_subscription(chat_id)
            if sub:
                db.set_subscription(
                    chat_id, status="trial", api_requests_limit=10, trial_ends_at=datetime.utcnow() + timedelta(days=7)
                )
            msg = (
                "✅ ¡Configuración completa!\n\n"
                "🔍 Ahora buscaré los mejores vuelos para ti.\n"
                "🎁 Tienes **7 días de prueba gratis** (10 búsquedas).\n\n"
                "📋 Comandos:\n"
                "/subscribe - Ver planes y suscribirte\n"
                "/config - Ver tu configuración\n"
                "/price - Ver últimos precios\n"
                "/help - Todos los comandos"
            )
            return msg
        return None

    def process_multi_user_commands(self, commands: list[dict], db) -> None:
        for cmd in commands:
            chat_id = cmd["chat_id"]
            text = cmd["text"]
            command = cmd["command"]

            if command in ("/start", "/onboarding"):
                user = db.get_or_create_user(chat_id)
                if user.onboarded:
                    self.send_to(
                        chat_id, "✅ Ya estás registrado. Usa /help para comandos o /subscribe para ver planes."
                    )
                else:
                    msg = (
                        "🤖 ¡Bienvenido a Flight Tracker Premium!\n\n"
                        "Te guiaré por 6 pasos para configurar tu búsqueda.\n"
                        "Responde cada pregunta para continuar.\n\n"
                        "¿Listo? Escribe /start para comenzar."
                    )
                    if command == "/start" and not user.onboarded:
                        msg = self.ONBOARDING_STEPS[0]["question"]
                        db.set_user_config(chat_id, onboarding_step=1)
                    self.send_to(chat_id, msg)
                continue

            if not db.get_user_config(chat_id):
                self.send_to(chat_id, "❌ Usa /start para registrarte primero.")
                continue

            user = db.get_user_config(chat_id)
            if user.onboarded == 0 and user.onboarding_step > 0:
                result = self.handle_onboarding(chat_id, text, db)
                if result:
                    self.send_to(chat_id, result)
                if user.onboarding_step == 0 and user.onboarded == 1:
                    sub = db.get_subscription(chat_id)
                    self.send_plan_info(chat_id, sub)
                continue

            if not command:
                self.send_to(chat_id, "Usa /help para ver comandos disponibles.")
                continue

            if command == "/help":
                self.send_to(chat_id, self._help_text())
            elif command == "/config":
                self._send_config(chat_id, db, user)
            elif command == "/subscribe":
                self._send_subscribe(chat_id, db)
            elif command == "/plan":
                sub = db.get_subscription(chat_id)
                self.send_plan_info(chat_id, sub)
            elif command == "/cancel":
                db.set_subscription(chat_id, status="cancelled")
                self.send_to(chat_id, "❌ Suscripción cancelada. Tus alertas se detendrán al final del periodo.")
            elif command == "/price":
                self._send_user_prices(chat_id, db)
            elif command == "/stats":
                self._send_user_stats(chat_id, db)
            elif command == "/set_origins" and cmd["args"]:
                origins = ",".join([o.strip().upper() for o in " ".join(cmd["args"]).split(",")])
                db.set_user_config(chat_id, origins=origins)
                self.send_to(chat_id, f"✅ Orígenes: {origins}")
            elif command == "/set_destinations" and cmd["args"]:
                dests = ",".join([d.strip().upper() for d in " ".join(cmd["args"]).split(",")])
                db.set_user_config(chat_id, destinations=dests)
                self.send_to(chat_id, f"✅ Destinos: {dests}")
            elif command == "/set_adults" and cmd["args"]:
                try:
                    a = int(cmd["args"][0])
                    if 1 <= a <= 9:
                        db.set_user_config(chat_id, adults=a)
                        self.send_to(chat_id, f"✅ Pasajeros: {a}")
                except ValueError:
                    self.send_to(chat_id, "❌ Usa: /set_adults NUMERO")
            elif command == "/set_luggage" and cmd["args"]:
                opt = cmd["args"][0].lower()
                mapping = {
                    "mano": "carry_on",
                    "bodega": "checked",
                    "ambas": "both",
                    "carry": "carry_on",
                    "checked": "checked",
                    "both": "both",
                }
                if opt in mapping:
                    db.set_user_config(chat_id, luggage=mapping[opt])
                    self.send_to(chat_id, f"✅ Equipaje: {opt}")
                else:
                    self.send_to(chat_id, "❌ Opciones: mano, bodega, ambas")
            elif command == "/set_budget" and cmd["args"]:
                try:
                    b = float(cmd["args"][0].replace("$", "").replace(",", ""))
                    db.set_user_config(chat_id, max_budget=b)
                    self.send_to(chat_id, f"✅ Presupuesto: ${b:,.0f} COP")
                except ValueError:
                    self.send_to(chat_id, "❌ Usa: /set_budget MONTO")
            elif command == "/delete_my_data":
                self.send_to(chat_id, "⚠️ Esto eliminará todos tus datos. Confirma con /confirm_delete")
            elif command == "/confirm_delete":
                self._delete_user(chat_id, db)

    def send_flight_alert(
        self, old_price: float, new_price: float, flight_data: dict, booking_link: str = "", chat_id: str = ""
    ) -> bool:
        drop = old_price - new_price
        origin = flight_data.get("origin", "")
        dest = flight_data.get("destination", "")
        airline = flight_data.get("airline", "")
        date = flight_data.get("date", "")
        return_date = flight_data.get("return_date", "")
        emoji, label = ("🔽", "PRECIO BAJO") if drop > 0 else ("🔼", "PRECIO SUBIO")
        text = f"{emoji} {label}\n\n✈️ {origin} → {dest}\n💰 ${old_price:,.0f} → ${new_price:,.0f}\n📉 Diferencia: ${abs(drop):,.0f}\n\n🏷️ {airline}\n📅 Ida: {date}\n"
        if return_date:
            text += f"📅 Vuelta: {return_date}\n"
        if booking_link and booking_link.startswith("http"):
            text += f'\n🔗 <a href="{booking_link}">Reservar</a>'
        text += "\n\n💡 Usa /help para comandos"
        if chat_id:
            return self.send_to(chat_id, text)
        return self.send_message(text)

    def send_price_summary(self, results: list, chat_id: str = "") -> bool:
        flights = [r[0] for r in results]
        flights.sort(key=lambda x: x.price)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = f"✈️ MEJORES PRECIOS\n📅 {now}\n" + "━" * 25 + "\n\n"
        for i, flight in enumerate(flights[:5], 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1] if i <= 5 else f"{i}."
            link = AIRLINE_BOOKING_URLS.get(flight.airline, AIRLINE_BOOKING_URLS["Avianca"])
            text += f'{emoji} {flight.origin} → {flight.destination}\n   💵 ${flight.price:,.0f}\n   🏷️ {flight.airline}\n   📅 {flight.date} → {flight.return_date}\n   🔗 <a href="{link}">COMPRAR</a>\n\n'
        text += "━" * 25 + "\n💡 /config para personalizar\n🔄 Próximo check en 8h"
        if chat_id:
            return self.send_to(chat_id, text)
        return self.send_message(text)

    def send_plan_info(self, chat_id: str, sub) -> bool:
        status = sub.status if sub else "none"
        plan = sub.plan if sub else "trial"
        used = sub.api_requests_month if sub else 0
        limit = sub.api_requests_limit if sub else 10
        trial_end = sub.trial_ends_at.strftime("%Y-%m-%d") if sub and sub.trial_ends_at else "N/A"
        text = (
            f"📊 <b>Tu Plan: {plan.upper()}</b>\n\n"
            f"Estado: {status}\n"
            f"Búsquedas: {used}/{limit} este mes\n"
            f"Prueba gratis hasta: {trial_end if status == 'trial' else '—'}\n\n"
            f"Planes disponibles:\n"
            f"🎁 <b>Gratuito</b> — 10 búsquedas/mes\n"
            f"🚀 <b>Premium ($5/mes)</b> — 500 búsquedas, 3 rutas, dashboard\n"
            f"💼 <b>Pro ($10/mes)</b> — Ilimitado, 10 rutas, SMS, dashboard\n\n"
            "Para suscribirte: /subscribe"
        )
        return self.send_to(chat_id, text)

    def _help_text(self) -> str:
        return (
            "🤖 <b>Flight Tracker Comandos</b>\n\n"
            "/start - Iniciar / reconfigurar\n"
            "/help - Mostrar comandos\n"
            "/config - Ver configuración\n"
            "/subscribe - Ver planes y suscribirte\n"
            "/plan - Ver tu plan actual\n"
            "/cancel - Cancelar suscripción\n"
            "/price - Ver últimos precios\n"
            "/stats - Estadísticas\n"
            "/set_origins MDE,BOG - Cambiar orígenes\n"
            "/set_destinations ADZ,CTG - Cambiar destinos\n"
            "/set_adults 2 - Cambiar pasajeros\n"
            "/set_luggage mano|bodega|ambas - Equipaje\n"
            "/set_budget 500000 - Presupuesto máximo\n"
            "/delete_my_data - Eliminar mi cuenta"
        )

    def _send_config(self, chat_id: str, db, user) -> None:
        if not user:
            self.send_to(chat_id, "❌ Usa /start para registrarte.")
            return
        luggage_map = {"carry_on": "Maleta de mano", "checked": "Maleta en bodega", "both": "Ambas"}
        luggage_str = luggage_map.get(user.luggage, user.luggage)
        non_stop = "Sí" if user.non_stop_only else "No"
        budget = f"${user.max_budget:,.0f}" if user.max_budget else "Sin límite"
        text = (
            "⚙️ <b>Tu Configuración</b>\n\n"
            f"✈️ Orígenes: {user.origins}\n"
            f"📍 Destinos: {user.destinations}\n"
            f"👥 Pasajeros: {user.adults}\n"
            f"🧳 Equipaje: {luggage_str}\n"
            f"💰 Presupuesto: {budget}\n"
            f"🛫 Solo directos: {non_stop}\n\n"
            "Usa /help para cambiar"
        )
        self.send_to(chat_id, text)

    def _send_subscribe(self, chat_id: str, db) -> None:
        from src.services.payments import get_payment_service

        ps = get_payment_service()
        methods = ps.get_available_methods()
        text = (
            "💳 <b>Elige tu plan y método de pago</b>\n\n"
            f"1️⃣ <b>Premium ($5/mes)</b> — 500 búsquedas, 3 rutas\n"
            f"2️⃣ <b>Pro ($10/mes)</b> — Ilimitado, 10 rutas + SMS\n\n"
            "Responde con:\n"
            "/pay premium stripe\n"
            "/pay premium nequi\n"
            "/pay premium crypto USDT\n"
            "/pay pro stripe\n"
            "/pay pro crypto BTC\n"
        )
        if not methods:
            text += "\n⚠️ No hay métodos de pago configurados. Contacta al administrador."
        self.send_to(chat_id, text)

    def _send_user_prices(self, chat_id: str, db) -> None:
        user = db.get_user_config(chat_id)
        if not user:
            self.send_to(chat_id, "❌ Usa /start para registrarte.")
            return
        origins = [o.strip() for o in user.origins.split(",")]
        dests = [d.strip() for d in user.destinations.split(",")]
        records = db.get_price_history(chat_id, limit=20)
        if not records:
            self.send_to(chat_id, "📊 Aún no hay datos. El bot buscará pronto.")
            return
        seen = set()
        text = "📊 <b>Últimos precios</b>\n\n"
        for rec in records:
            key = f"{rec.origin}:{rec.destination}"
            if key not in seen:
                seen.add(key)
                text += f"✈️ {rec.origin} → {rec.destination}: <b>${rec.price:,.0f}</b> ({rec.airline})\n"
        self.send_to(chat_id, text)

    def _send_user_stats(self, chat_id: str, db) -> None:
        user = db.get_user_config(chat_id)
        sub = db.get_subscription(chat_id) if chat_id else None
        records = db.get_price_history(chat_id, limit=5)
        prices = [r.price for r in records if r.price]
        text = (
            f"📊 <b>Tus Estadísticas</b>\n\n🔍 Búsquedas: {len(records)}\n💰 Precio más bajo: ${min(prices):,.0f}"
            if prices
            else "💰 Sin datos aún" + f"\n💵 Precio más alto: ${max(prices):,.0f}"
            if prices
            else "" + f"\n📅 Plan: {(sub.plan if sub else 'trial').upper()}\n🔔 Estado: {sub.status if sub else 'N/A'}"
        )
        self.send_to(chat_id, text)

    def _delete_user(self, chat_id: str, db) -> None:
        with db.get_session() as session:
            session.query(type(db).AlertLog).filter(type(db).AlertLog.chat_id == chat_id).delete()
            session.query(type(db).PriceRecord).filter(type(db).PriceRecord.chat_id == chat_id).delete()
            session.query(type(db).Subscription).filter(type(db).Subscription.chat_id == chat_id).delete()
            session.query(type(db).UserConfig).filter(type(db).UserConfig.chat_id == chat_id).delete()
            session.commit()
        self.send_to(chat_id, "🗑️ Todos tus datos han sido eliminados. Adiós.")
