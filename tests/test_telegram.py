from unittest.mock import MagicMock, patch

from src.services.telegram import TelegramService
from src.providers.base import ApiResult


class TestTelegramService:
    def test_init(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        assert service.chat_ids == ["987654321"]

    def test_send_message_success(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ApiResult.ok({"ok": True})
        service.provider = mock_provider
        result = service.send_message("Test message")
        assert result is True

    def test_send_message_failure(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ApiResult.fail("error", 500)
        service.provider = mock_provider
        result = service.send_message("Test message")
        assert result is False

    def test_send_to_success(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ApiResult.ok({"ok": True})
        service.provider = mock_provider
        result = service.send_to("987654321", "Test message")
        assert result is True

    def test_send_flight_alert(self) -> None:
        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ApiResult.ok({"ok": True})
        service.provider = mock_provider
        result = service.send_flight_alert(
            old_price=200000, new_price=150000,
            flight_data={"origin": "MDE", "destination": "ADZ", "airline": "Avianca",
                         "date": "2026-06-15", "return_date": "2026-06-20"},
            booking_link="https://avianca.com"
        )
        assert result is True

    def test_send_price_summary(self) -> None:
        mock_flight = MagicMock()
        mock_flight.origin = "MDE"
        mock_flight.destination = "ADZ"
        mock_flight.price = 150000
        mock_flight.currency = "COP"
        mock_flight.airline = "Avianca"
        mock_flight.date = "2026-06-15"
        mock_flight.return_date = "2026-06-20"

        service = TelegramService("123456:ABC", "987654321")
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ApiResult.ok({"ok": True})
        service.provider = mock_provider

        result = service.send_price_summary([(mock_flight, "https://avianca.com")])
        assert result is True
