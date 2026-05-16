from unittest.mock import MagicMock, patch

from src.services.telegram import TelegramService


class TestTelegramService:
    def test_init(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        assert service.token == "123456:ABC"
        assert service.chat_id == "987654321"
        assert service.logger == mock_logger

    def test_send_message_success(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = service.send_message("Test message")

            assert result is True
            mock_logger.info.assert_called_once_with("Message sent to Telegram")

    def test_send_message_failure(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            result = service.send_message("Test message")

            assert result is False
            mock_logger.error.assert_called_once_with("Telegram error: 500")

    def test_send_message_network_error(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        with patch("requests.post") as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.RequestException("Network error")

            result = service.send_message("Test message")

            assert result is False
            mock_logger.error.assert_called_once()

    def test_send_flight_alert(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        with patch.object(service, "send_message", return_value=True) as mock_send:
            result = service.send_flight_alert(
                old_price=200000,
                new_price=150000,
                flight_data={
                    "origin": "MDE",
                    "destination": "ADZ",
                    "airline": "Avianca",
                    "date": "2026-06-15",
                    "return_date": "2026-06-20"
                },
                booking_link="https://www.avianca.com/booking/123"
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert "PRECIO BAJO" in call_args
            assert "200,000" in call_args
            assert "150,000" in call_args
            assert "50,000" in call_args
            assert "MDE" in call_args
            assert "ADZ" in call_args

    def test_send_price_summary(self, mock_logger: MagicMock) -> None:
        service = TelegramService("123456:ABC", "987654321", mock_logger)

        mock_flight = MagicMock()
        mock_flight.origin = "MDE"
        mock_flight.destination = "ADZ"
        mock_flight.price = 150000
        mock_flight.currency = "COP"
        mock_flight.airline = "Avianca"
        mock_flight.date = "2026-06-15"
        mock_flight.return_date = "2026-06-20"

        results = [(mock_flight, "https://www.avianca.com/booking/123")]

        with patch.object(service, "send_message", return_value=True) as mock_send:
            result = service.send_price_summary(results, "Ida y Vuelta")

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert "MEJORES PRECIOS" in call_args
            assert "MDE" in call_args
            assert "150,000" in call_args
