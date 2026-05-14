import pytest
import json
from pathlib import Path
from src.models.price_history import PriceHistory


class TestPriceHistory:
    def test_init_creates_file(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"

        history = PriceHistory(file_path)

        assert file_path.exists()
        assert history.data == {}

    def test_update_and_get_price(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"
        history = PriceHistory(file_path)

        history.update_price(
            "MDE:ADZ",
            {
                "price": 150000,
                "last_update": "2026-06-15T10:00:00",
                "airline": "Avianca",
                "booking_link": "abc123"
            }
        )

        assert history.get_last_price("MDE:ADZ") == 150000

    def test_get_last_price_not_found(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"
        history = PriceHistory(file_path)

        result = history.get_last_price("NONEXISTENT:ROUTE")

        assert result is None

    def test_get_price_drop(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"
        history = PriceHistory(file_path)

        history.update_price(
            "MDE:ADZ",
            {
                "price": 200000,
                "last_update": "2026-06-15T10:00:00",
                "airline": "Avianca",
                "booking_link": "abc123"
            }
        )

        drop = history.get_price_drop("MDE:ADZ", 150000)

        assert drop == 50000

    def test_get_price_drop_no_history(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"
        history = PriceHistory(file_path)

        drop = history.get_price_drop("NEW:ROUTE", 150000)

        assert drop is None

    def test_persistence(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"

        history1 = PriceHistory(file_path)
        history1.update_price(
            "MDE:ADZ",
            {
                "price": 250000,
                "last_update": "2026-06-15T10:00:00",
                "airline": "LATAM",
                "booking_link": "xyz789"
            }
        )

        history2 = PriceHistory(file_path)

        assert history2.get_last_price("MDE:ADZ") == 250000

    def test_multiple_routes(self, temp_data_dir: Path) -> None:
        file_path = temp_data_dir / "price_history.json"
        history = PriceHistory(file_path)

        history.update_price(
            "MDE:ADZ",
            {"price": 150000, "last_update": "", "airline": "", "booking_link": ""}
        )
        history.update_price(
            "PEI:ADZ",
            {"price": 180000, "last_update": "", "airline": "", "booking_link": ""}
        )

        assert history.get_last_price("MDE:ADZ") == 150000
        assert history.get_last_price("PEI:ADZ") == 180000