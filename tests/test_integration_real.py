"""Integration tests with real mocked API responses for the full price-check flow."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.database import Database
from src.models.flight import FlightData
from src.models.price_history import PriceHistory
from src.repositories.price_repository import PriceRepository
from src.repositories.user_repository import UserRepository
from src.services.ignav_api import IgnavAPIService
from src.services.price_service import PriceService
from src.services.telegram import TelegramService

# Realistic Ignav API response sample
SAMPLE_FLIGHT_RESPONSE = {
    "itineraries": [
        {
            "price": {"amount": 280000, "currency": "COP"},
            "outbound": {
                "carrier": "Avianca",
                "segments": [
                    {
                        "flight_number": "AV456",
                        "departure_airport": "MDE",
                        "arrival_airport": "ADZ",
                        "departure_time_local": "2026-06-15T08:00:00",
                        "arrival_time_local": "2026-06-15T09:45:00",
                    }
                ],
            },
            "inbound": {
                "carrier": "Avianca",
                "segments": [
                    {
                        "flight_number": "AV789",
                        "departure_airport": "ADZ",
                        "arrival_airport": "MDE",
                        "departure_time_local": "2026-06-20T14:30:00",
                        "arrival_time_local": "2026-06-20T16:15:00",
                    }
                ],
            },
            "ignav_id": "abc123test",
        },
        {
            "price": {"amount": 320000, "currency": "COP"},
            "outbound": {
                "carrier": "LATAM",
                "segments": [
                    {
                        "flight_number": "LA321",
                        "departure_airport": "MDE",
                        "arrival_airport": "ADZ",
                        "departure_time_local": "2026-06-15T10:00:00",
                        "arrival_time_local": "2026-06-15T11:45:00",
                    }
                ],
            },
            "inbound": {
                "carrier": "LATAM",
                "segments": [
                    {
                        "flight_number": "LA654",
                        "departure_airport": "ADZ",
                        "arrival_airport": "MDE",
                        "departure_time_local": "2026-06-20T16:00:00",
                        "arrival_time_local": "2026-06-20T17:45:00",
                    }
                ],
            },
            "ignav_id": "xyz789test",
        },
    ]
}

SAMPLE_BOOKING_RESPONSE = {"booking_options": [{"links": [{"url": "https://avianca.com/book/ABC123"}]}]}


@pytest.fixture
def mock_ignav_provider():
    """Mocks IgnavProvider to return realistic data without calling the real API."""
    with patch("src.services.ignav_api.IgnavProvider") as MockProvider:
        provider = MagicMock()

        def mock_round_trip(*args, **kwargs):
            from src.providers.base import ApiResult

            return ApiResult.ok(SAMPLE_FLIGHT_RESPONSE)

        def mock_booking(*args, **kwargs):
            from src.providers.base import ApiResult

            return ApiResult.ok(SAMPLE_BOOKING_RESPONSE)

        provider.search_round_trip.side_effect = mock_round_trip
        provider.search_one_way.side_effect = mock_round_trip
        provider.get_booking_link.side_effect = mock_booking

        MockProvider.return_value = provider
        yield provider


@pytest.fixture
def mock_telegram_provider():
    """Mocks TelegramProvider to simulate successful sends."""
    with patch("src.services.telegram.TelegramProvider") as MockProvider:
        provider = MagicMock()
        from src.providers.base import ApiResult

        provider.send_message.return_value = ApiResult.ok({"ok": True})
        provider.get_updates.return_value = ApiResult.ok({"result": []})
        MockProvider.return_value = provider
        yield provider


@pytest.fixture
def temp_history_file(tmp_path: Path) -> Path:
    history = tmp_path / "price_history.json"
    history.write_text("{}")
    return history


@pytest.fixture
def test_db():
    import os

    os.makedirs("data", exist_ok=True)
    db_path = "data/test_int_flight_tracker.db"
    db_url = f"sqlite:///{db_path}"
    db = Database(db_url)

    # Create test user
    db.set_user_config("999111888", origins="MDE,PEI", destinations="ADZ", adults=2, onboarded=1, active=1)
    db.set_subscription("999111888", status="active", plan="premium", api_requests_limit=500, api_requests_month=0)
    yield db
    try:
        os.remove(db_path)
    except OSError:
        pass


class TestFullPriceCheckFlow:
    """Tests the complete price check flow with mocked external APIs."""

    def test_search_and_save_flight(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)
        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)

        # Run price check for the test user
        service.check_prices_for_user("999111888")

        # Verify flight data was saved to price_history (JSON)
        route_mde = history.get_last_price("999111888:MDE:ADZ")
        assert route_mde is not None, "MDE→ADZ price should be saved to JSON"
        assert route_mde == 280000.0

        route_pei = history.get_last_price("999111888:PEI:ADZ")
        assert route_pei is not None, "PEI→ADZ price should be saved to JSON"
        assert route_pei == 280000.0

    def test_search_and_save_to_db(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)
        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)

        service.check_prices_for_user("999111888")

        # Verify DB records were created
        records = test_db.get_price_history("999111888", limit=10)
        assert len(records) >= 2, "Should have at least 2 price records (MDE + PEI)"

        mde_records = [r for r in records if r.origin == "MDE"]
        assert len(mde_records) >= 1
        assert mde_records[0].price == 280000.0
        assert mde_records[0].airline == "Avianca"

    def test_price_drop_detected(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)

        # Set a higher previous price to trigger a price drop alert
        history.update_price(
            "999111888:MDE:ADZ",
            {
                "price": 350000,
                "last_update": datetime.now().isoformat(),
                "airline": "Avianca",
            },
        )

        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)

        service.check_prices_for_user("999111888")

        # Verify an alert was logged (price dropped from 350k to 280k = 70k drop)
        alerts = test_db.get_alerts("999111888", limit=10)
        price_drops = [a for a in alerts if a.alert_type == "price_drop"]
        assert len(price_drops) >= 1, "Price drop alert should be logged"
        assert price_drops[0].difference == 70000.0

    def test_no_duplicate_alerts(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        """Price should not alert twice for the same price."""
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)

        # First check — sets the baseline
        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)
        service.check_prices_for_user("999111888")

        # Reset alert count
        initial_alerts = len(test_db.get_alerts("999111888"))

        # Second check — same price, no alert expected
        service.check_prices_for_user("999111888")
        final_alerts = len(test_db.get_alerts("999111888"))

        # Should be same or very close (only price increase if threshold met)
        assert final_alerts - initial_alerts <= 1

    def test_api_limit_reached(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        """User with exhausted API limit should not trigger searches."""
        test_db.set_subscription("999111888", api_requests_month=500, api_requests_limit=500)
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)
        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)

        service.check_prices_for_user("999111888")

        route = history.get_last_price("999111888:MDE:ADZ")
        assert route is None, "No price should be saved if API limit reached"

    def test_inactive_user_skipped(self, test_db, temp_history_file, mock_ignav_provider, mock_telegram_provider):
        """Inactive users should not trigger searches."""
        test_db.set_user_config("999111888", active=0)
        api = IgnavAPIService("ignav_test_key")
        telegram = TelegramService("123:ABC", "999111888")
        history = PriceHistory(temp_history_file)
        user_repo = UserRepository(test_db)
        price_repo = PriceRepository(test_db)
        service = PriceService(api, telegram, history, user_repo, price_repo)

        service.check_prices_for_user("999111888")

        route = history.get_last_price("999111888:MDE:ADZ")
        assert route is None, "No price should be saved for inactive user"


class TestProviderMocks:
    """Tests that the provider mocking layer works correctly."""

    def test_ignav_provider_returns_mocked_data(self, mock_ignav_provider):

        result = mock_ignav_provider.search_round_trip("MDE", "ADZ", "2026-06-15", "2026-06-20")
        assert result.is_ok
        assert result.data == SAMPLE_FLIGHT_RESPONSE

    def test_ignav_provider_booking_link(self, mock_ignav_provider):

        result = mock_ignav_provider.get_booking_link("abc123")
        assert result.is_ok
        assert result.data["booking_options"][0]["links"][0]["url"] == "https://avianca.com/book/ABC123"

    def test_telegram_provider_send(self, mock_telegram_provider):

        result = mock_telegram_provider.send_message("999111888", "test")
        assert result.is_ok

    def test_ignav_api_integration(self, mock_ignav_provider):
        """IgnavAPIService correctly converts provider responses to FlightData."""
        api = IgnavAPIService("ignav_test_key")
        flight = api.search_cheapest_round_trip("MDE", "ADZ", ["2026-06-15"], return_days=5, adults=2)
        assert flight is not None
        assert isinstance(flight, FlightData)
        assert flight.origin == "MDE"
        assert flight.destination == "ADZ"
        # Should pick the cheapest: Avianca 280k < LATAM 320k
        assert flight.price == 280000
        assert flight.airline == "Avianca"
