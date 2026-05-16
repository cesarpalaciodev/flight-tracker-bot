"""Ignav API provider — all Ignav HTTP calls centralized here."""

import logging
from typing import Optional

from src.providers.base import BaseProvider, ApiResult


class IgnavProvider(BaseProvider):
    BASE_URL = "https://ignav.com/api/fares"

    def __init__(self, api_key: str, logger_obj: Optional[logging.Logger] = None):
        super().__init__(logger_obj)
        self.session.headers.update({"X-Api-Key": api_key})

    def search_round_trip(
        self, origin: str, destination: str, departure_date: str, return_date: str, adults: int = 2
    ) -> ApiResult:
        return self._post(
            "/round-trip",
            json_data={
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
            },
        )

    def search_one_way(self, origin: str, destination: str, date: str) -> ApiResult:
        return self._post(
            "/one-way",
            json_data={
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": date,
            },
        )

    def get_booking_link(self, ignav_id: str) -> ApiResult:
        return self._post("https://ignav.com/api/fares/booking-links", json_data={"ignav_id": ignav_id})
