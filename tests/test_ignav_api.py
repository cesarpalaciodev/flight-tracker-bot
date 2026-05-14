import pytest
import logging
from unittest.mock import MagicMock, patch
from src.services.ignav_api import IgnavAPIService
from src.models.flight import FlightData


class TestIgnavAPIService:
    def test_init_without_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API key is required"):
            IgnavAPIService("")

    def test_init_with_api_key(self, mock_logger: MagicMock) -> None:
        service = IgnavAPIService("ignav_test_key", mock_logger)

        assert service.api_key == "ignav_test_key"
        assert service.logger == mock_logger

    def test_search_flight_success(
        self,
        mock_logger: MagicMock,
        sample_flight_response: dict
    ) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (True, "OK")
            MockRateLimiter.return_value = mock_limiter

            with patch.object(IgnavAPIService, "session") as mock_session:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = sample_flight_response
                mock_session.post.return_value = mock_response

                service = IgnavAPIService("ignav_test_key", mock_logger)
                service.session = mock_session

                result = service.search_flight("MDE", "ADZ", "2026-06-15")

                assert result == sample_flight_response
                mock_limiter.record_request.assert_called_once()

    def test_search_flight_rate_limited(self, mock_logger: MagicMock) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (False, "Rate limit: max 10 requests/minute")
            mock_limiter.wait_if_needed = MagicMock()
            MockRateLimiter.return_value = mock_limiter

            service = IgnavAPIService("ignav_test_key", mock_logger)
            service.rate_limiter = mock_limiter

            service._check_rate_limit()

            mock_limiter.wait_if_needed.assert_called_once_with(mock_logger)
            mock_logger.warning.assert_called_once()

    def test_get_cheapest_returns_flight(
        self,
        mock_logger: MagicMock,
        sample_flight_response: dict
    ) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (True, "OK")
            MockRateLimiter.return_value = mock_limiter

            with patch.object(IgnavAPIService, "search_flight", return_value=sample_flight_response):
                service = IgnavAPIService("ignav_test_key", mock_logger)
                result = service.get_cheapest("MDE", "ADZ", "2026-06-15")

                assert result is not None
                assert isinstance(result, FlightData)
                assert result.price == 150000

    def test_get_cheapest_no_flights(self, mock_logger: MagicMock) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (True, "OK")
            MockRateLimiter.return_value = mock_limiter

            service = IgnavAPIService("ignav_test_key", mock_logger)

            with patch.object(
                service, "search_flight", return_value={"itineraries": []}
            ):
                result = service.get_cheapest("MDE", "ADZ", "2026-06-15")

                assert result is None

    def test_get_booking_link_success(
        self,
        mock_logger: MagicMock,
        sample_booking_response: dict
    ) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (True, "OK")
            MockRateLimiter.return_value = mock_limiter

            with patch.object(IgnavAPIService, "session") as mock_session:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = sample_booking_response
                mock_session.post.return_value = mock_response

                service = IgnavAPIService("ignav_test_key", mock_logger)
                service.session = mock_session

                result = service.get_booking_link("abc123test")

                assert result == "https://www.avianca.com/booking/123"
                mock_limiter.record_request.assert_called_once()

    def test_get_booking_link_empty_id(self, mock_logger: MagicMock) -> None:
        with patch("src.services.ignav_api.RateLimiter"):
            service = IgnavAPIService("ignav_test_key", mock_logger)

            result = service.get_booking_link("")

            assert result is None

    def test_search_cheapest_round_trip(
        self,
        mock_logger: MagicMock,
        sample_round_trip_response: dict
    ) -> None:
        with patch("src.services.ignav_api.RateLimiter") as MockRateLimiter:
            mock_limiter = MagicMock()
            mock_limiter.is_allowed.return_value = (True, "OK")
            MockRateLimiter.return_value = mock_limiter

            with patch.object(
                IgnavAPIService, "search_round_trip", return_value=sample_round_trip_response
            ):
                service = IgnavAPIService("ignap_test_key", mock_logger)

                result = service.search_cheapest_round_trip(
                    origin="MDE",
                    destination="ADZ",
                    departure_dates=["2026-06-15"],
                    return_days=5,
                    adults=2
                )

                assert result is not None
                assert isinstance(result, FlightData)
                assert result.price == 280000
                assert result.airline == "LATAM"