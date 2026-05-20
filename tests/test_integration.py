from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.flight import FlightData
from src.services.ignav_api import IgnavAPIService
from src.services.telegram import TelegramService


class TestPriceCheckFlow:
    def test_price_drop_detected(self, sample_flight_response: dict) -> None:
        with patch.object(IgnavAPIService, "search_round_trip", return_value=sample_flight_response):
            with patch.object(IgnavAPIService, "get_booking_link", return_value="https://example.com"):
                api = IgnavAPIService("ignav_test_key")
                flight = api.search_cheapest_round_trip("MDE", "ADZ", ["2026-06-15"], return_days=5, adults=2)
                assert flight is not None
                assert flight.price == 150000


class TestTelegramMessageFormat:
    def test_flight_alert_message_format(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = __import__("src.providers.base", fromlist=["ApiResult"]).ApiResult.ok(
            {"ok": True}
        )
        service.provider = mock_provider
        service.send_flight_alert(
            old_price=200000,
            new_price=150000,
            flight_data={
                "origin": "MDE",
                "destination": "ADZ",
                "airline": "Avianca",
                "date": "2026-06-15",
                "return_date": "2026-06-20",
            },
            booking_link="https://avianca.com/booking",
        )
        call_args = mock_provider.send_message.call_args[0]
        assert "PRECIO BAJO" in call_args[1]


class TestRateLimiterIntegration:
    def test_rate_limiter_records_request(self, temp_data_dir: "Path") -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = rate_limiter.RateLimiter()
            initial_count = limiter.data["daily_count"]

            limiter.record_request()

            assert limiter.data["daily_count"] == initial_count + 1
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file


class TestConfigValidation:
    def test_missing_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API key is required"):
            IgnavAPIService("")

    def test_missing_telegram_token_raises(self) -> None:
        with pytest.raises(ValueError, match="Telegram token is required"):
            TelegramService("", "123456")

    def test_empty_chat_id_allowed(self) -> None:
        service = TelegramService("123:abc", "")
        assert service.chat_ids == []


class TestFlightDataEdgeCases:
    def test_empty_flight_data(self) -> None:
        flight = FlightData.from_ignav_response({}, "MDE", "2026-06-15", "ADZ")
        assert flight is not None
        assert flight.price == 0

    def test_flight_data_with_missing_segments(self) -> None:
        data = {"price": {"amount": 100000, "currency": "COP"}, "outbound": {}, "inbound": {}, "ignav_id": "test123"}
        flight = FlightData.from_ignav_response(data, "MDE", "2026-06-15", "ADZ")
        assert flight is not None
        assert flight.price == 100000
        assert flight.airline == "N/A"
