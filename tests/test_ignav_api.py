from unittest.mock import MagicMock, patch

import pytest

from src.models.flight import FlightData
from src.providers.base import ApiResult
from src.services.ignav_api import IgnavAPIService


class TestIgnavAPIService:
    def test_init_without_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API key is required"):
            IgnavAPIService("")

    def test_init_with_api_key(self) -> None:
        service = IgnavAPIService("ignav_test_key")
        assert service.provider is not None
        assert service.cache is not None

    def test_search_flight_success(self, sample_flight_response: dict) -> None:
        service = IgnavAPIService("ignav_test_key")
        mock_provider = MagicMock()
        mock_provider.search_one_way.return_value = ApiResult.ok(sample_flight_response)
        service.provider = mock_provider
        result = service.search_flight("MDE", "ADZ", "2026-06-15")
        assert result == sample_flight_response

    def test_search_flight_no_results(self) -> None:
        service = IgnavAPIService("ignav_test_key")
        mock_provider = MagicMock()
        mock_provider.search_one_way.return_value = ApiResult.fail("not found", 404)
        service.provider = mock_provider
        result = service.search_flight("MDE", "ADZ", "2026-06-15")
        assert result is None

    def test_get_cheapest_returns_flight(self, sample_flight_response: dict) -> None:
        with patch.object(IgnavAPIService, "search_flight") as mock_search:
            mock_search.return_value = sample_flight_response
            service = IgnavAPIService("ignav_test_key")
            result = service.get_cheapest("MDE", "ADZ", "2026-06-15")
            assert result is not None
            assert isinstance(result, FlightData)
            assert result.price == 150000

    def test_get_cheapest_no_flights(self) -> None:
        with patch.object(IgnavAPIService, "search_flight", return_value=None):
            service = IgnavAPIService("ignav_test_key")
            result = service.get_cheapest("MDE", "ADZ", "2026-06-15")
            assert result is None

    def test_get_booking_link_success(self, sample_booking_response: dict) -> None:
        service = IgnavAPIService("ignav_test_key")
        mock_provider = MagicMock()
        mock_provider.get_booking_link.return_value = ApiResult.ok(sample_booking_response)
        service.provider = mock_provider
        result = service.get_booking_link("abc123test")
        assert result == "https://www.avianca.com/booking/123"

    def test_get_booking_link_empty_id(self) -> None:
        service = IgnavAPIService("ignav_test_key")
        result = service.get_booking_link("")
        assert result is None

    def test_search_cheapest_round_trip(self, sample_round_trip_response: dict) -> None:
        with patch.object(IgnavAPIService, "search_round_trip") as mock_search:
            mock_search.return_value = sample_round_trip_response
            service = IgnavAPIService("ignav_test_key")
            result = service.search_cheapest_round_trip(
                origin="MDE", destination="ADZ", departure_dates=["2026-06-15"], return_days=5, adults=2
            )
            assert result is not None
            assert isinstance(result, FlightData)
            assert result.price == 280000
            assert result.airline == "LATAM"
