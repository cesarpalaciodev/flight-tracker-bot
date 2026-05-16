import time
from datetime import datetime, timedelta

from src.models.price_history import PriceHistory
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService
from src.repositories.user_repository import UserRepository
from src.repositories.price_repository import PriceRepository
from src.utils import config
from src.utils.metrics import FLIGHTS_SEARCHED, PRICE_CHECKS, PRICE_ALERTS_SENT
from src.utils.logger import get_logger
from src.utils.error_handler import ErrorBoundary
from src.utils.exceptions import AppError, PriceAlertError


log = get_logger("price_service")


def get_departure_dates(days_ahead_start: int, days_ahead_end: int, interval: int) -> list[str]:
    dates = []
    for i in range(days_ahead_start, days_ahead_end, interval):
        dates.append((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"))
    return dates


class PriceService:
    def __init__(
        self,
        api: IgnavAPIService,
        telegram: TelegramService,
        history: PriceHistory,
        user_repo: UserRepository,
        price_repo: PriceRepository,
    ):
        self.api = api
        self.telegram = telegram
        self.history = history
        self.user_repo = user_repo
        self.price_repo = price_repo

    def check_prices_for_user(self, chat_id: str) -> None:
        with ErrorBoundary(context={"chat_id": chat_id, "method": "check_prices_for_user"}):
            user = self.user_repo.get_by_chat_id(chat_id)
            if not user or not user.active:
                return

            sub = self.user_repo.get_subscription(chat_id)
            if sub and sub.api_requests_limit > 0 and sub.api_requests_month >= sub.api_requests_limit:
                log.info(
                    f"User {chat_id} reached API limit",
                    extra={"ctx": {"used": sub.api_requests_month, "limit": sub.api_requests_limit}},
                )
                if sub.status == "trial":
                    self.telegram.send_to(chat_id, "⚠️ Límite de prueba alcanzado. /subscribe para continuar.")
                return

            origins = [o.strip() for o in user.origins.split(",")]
            destinations_list = [d.strip() for d in user.destinations.split(",")]
            results = []
            departure_dates = get_departure_dates(config.DAYS_AHEAD_START, config.DAYS_AHEAD_END, config.DAYS_INTERVAL)

            for dest in destinations_list:
                for origin in origins:
                    route = config.build_route_key(origin, dest)
                    log.info(f"Checking {route}", extra={"ctx": {"chat_id": chat_id, "adults": user.adults}})

                    flight = self.api.search_cheapest_round_trip(
                        origin, dest, departure_dates, return_days=user.return_days, adults=user.adults
                    )
                    if not flight:
                        log.info(f"No results for {route}", extra={"ctx": {"chat_id": chat_id}})
                        continue

                    log.info(
                        f"Best price ${flight.price:,.0f}", extra={"ctx": {"chat_id": chat_id, "price": flight.price}}
                    )
                    booking_link = self.api.get_booking_link(flight.booking_link)
                    time.sleep(2)

                    luggage_match = 1 if user.luggage and user.luggage != "carry_on" else 0
                    budget_match = 1 if user.max_budget and flight.price <= user.max_budget else 0

                    previous = self.history.get_last_price(f"{chat_id}:{route}")
                    if previous is not None:
                        price_diff = flight.price - previous
                        threshold = user.price_drop_threshold or config.PRICE_DROP_THRESHOLD
                        if price_diff < 0 and abs(price_diff) >= threshold:
                            log.info(
                                f"Price drop {previous}→{flight.price}",
                                extra={"ctx": {"chat_id": chat_id, "route": route}},
                            )
                            self.telegram.send_flight_alert(
                                previous, flight.price, flight.to_dict(), booking_link or "", chat_id=chat_id
                            )
                            self.price_repo.log_alert(
                                chat_id, route, "price_drop", previous, flight.price, previous - flight.price
                            )
                            PRICE_ALERTS_SENT.inc()
                        elif price_diff > config.PRICE_INCREASE_THRESHOLD > 0:
                            log.info(
                                f"Price increase {previous}→{flight.price}",
                                extra={"ctx": {"chat_id": chat_id, "route": route}},
                            )
                            self.telegram.send_flight_alert(
                                previous, flight.price, flight.to_dict(), booking_link or "", chat_id=chat_id
                            )
                            self.price_repo.log_alert(
                                chat_id, route, "price_increase", previous, flight.price, flight.price - previous
                            )
                            PRICE_ALERTS_SENT.inc()

                    self.history.update_price(
                        f"{chat_id}:{route}",
                        {
                            "price": flight.price,
                            "last_update": datetime.now().isoformat(),
                            "airline": flight.airline,
                            "booking_link": flight.booking_link,
                        },
                    )

                    self.price_repo.save_price(
                        chat_id,
                        route,
                        origin,
                        dest,
                        flight.price,
                        flight.currency,
                        flight.airline,
                        flight.date,
                        flight.return_date,
                        booking_link or "",
                        luggage_match,
                        budget_match,
                    )
                    FLIGHTS_SEARCHED.inc()
                    results.append((flight, booking_link or ""))

            if sub:
                self.user_repo.set_subscription(
                    chat_id, api_requests_month=(sub.api_requests_month or 0) + max(1, len(results))
                )

            if results:
                log.info(f"Sending price summary to {chat_id}")
                self.telegram.send_price_summary(results, chat_id=chat_id)
                PRICE_ALERTS_SENT.inc()

    def check_all_users(self) -> None:
        users = self.user_repo.get_all_active()
        log.info(f"Checking {len(users)} active users", extra={"ctx": {"user_count": len(users)}})
        for user in users:
            with ErrorBoundary(context={"chat_id": user.chat_id, "method": "check_all_users"}):
                self.check_prices_for_user(user.chat_id)

    def run_check(self) -> None:
        log.info("Multi-user check start")
        self.check_all_users()
        log.info("Multi-user check complete")
