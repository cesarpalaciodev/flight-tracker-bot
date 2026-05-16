from src.models.database import AlertLog, Database, PriceRecord


class PriceRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_price(
        self,
        chat_id: str,
        route: str,
        origin: str,
        destination: str,
        price: float,
        currency: str = "COP",
        airline: str = "",
        departure_date: str = "",
        return_date: str = "",
        booking_link: str = "",
        luggage_match: int = 0,
        budget_match: int = 0,
    ) -> PriceRecord:
        return self.db.save_price(
            chat_id,
            route,
            origin,
            destination,
            price,
            currency,
            airline,
            departure_date,
            return_date,
            booking_link,
            luggage_match,
            budget_match,
        )

    def get_history(self, chat_id: str, route: str = "", limit: int = 30) -> list[PriceRecord]:
        return self.db.get_price_history(chat_id, route, limit)

    def log_alert(
        self, chat_id: str, route: str, alert_type: str, old_price: float, new_price: float, difference: float
    ) -> AlertLog:
        return self.db.log_alert(chat_id, route, alert_type, old_price, new_price, difference)

    def get_alerts(self, chat_id: str = "", limit: int = 50) -> list[AlertLog]:
        return self.db.get_alerts(chat_id, limit)

    def get_admin_stats(self) -> dict:
        return self.db.get_admin_stats()
