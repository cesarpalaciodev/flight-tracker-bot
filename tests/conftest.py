import pytest
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_logger() -> MagicMock:
    logger = MagicMock(spec=logging.Logger)
    return logger


@pytest.fixture
def sample_flight_response() -> dict:
    return {
        "itineraries": [
            {
                "price": {"amount": 150000, "currency": "COP"},
                "outbound": {
                    "carrier": "Avianca",
                    "segments": [
                        {
                            "flight_number": "AV456",
                            "departure_airport": "MDE",
                            "arrival_airport": "ADZ",
                            "departure_time_local": "2026-06-15T08:00:00",
                            "arrival_time_local": "2026-06-15T09:45:00"
                        }
                    ]
                },
                "inbound": {
                    "carrier": "Avianca",
                    "segments": [
                        {
                            "flight_number": "AV789",
                            "departure_airport": "ADZ",
                            "arrival_airport": "MDE",
                            "departure_time_local": "2026-06-20T14:30:00",
                            "arrival_time_local": "2026-06-20T16:15:00"
                        }
                    ]
                },
                "ignav_id": "abc123test"
            }
        ]
    }


@pytest.fixture
def sample_round_trip_response() -> dict:
    return {
        "itineraries": [
            {
                "price": {"amount": 280000, "currency": "COP"},
                "outbound": {
                    "carrier": "LATAM",
                    "segments": [
                        {
                            "flight_number": "LA456",
                            "departure_airport": "MDE",
                            "arrival_airport": "ADZ",
                            "departure_time_local": "2026-06-15T10:00:00",
                            "arrival_time_local": "2026-06-15T11:45:00"
                        }
                    ]
                },
                "inbound": {
                    "carrier": "LATAM",
                    "segments": [
                        {
                            "flight_number": "LA789",
                            "departure_airport": "ADZ",
                            "arrival_airport": "MDE",
                            "departure_time_local": "2026-06-20T15:30:00",
                            "arrival_time_local": "2026-06-20T17:15:00"
                        }
                    ]
                },
                "ignav_id": "xyz789test"
            },
            {
                "price": {"amount": 320000, "currency": "COP"},
                "outbound": {
                    "carrier": "Avianca",
                    "segments": [
                        {
                            "flight_number": "AV456",
                            "departure_airport": "MDE",
                            "arrival_airport": "ADZ",
                            "departure_time_local": "2026-06-15T08:00:00",
                            "arrival_time_local": "2026-06-15T09:45:00"
                        }
                    ]
                },
                "inbound": {
                    "carrier": "Avianca",
                    "segments": [
                        {
                            "flight_number": "AV789",
                            "departure_airport": "ADZ",
                            "arrival_airport": "MDE",
                            "departure_time_local": "2026-06-20T14:30:00",
                            "arrival_time_local": "2026-06-20T16:15:00"
                        }
                    ]
                },
                "ignav_id": "def456test"
            }
        ]
    }


@pytest.fixture
def sample_booking_response() -> dict:
    return {
        "booking_options": [
            {
                "links": [
                    {"url": "https://www.avianca.com/booking/123"}
                ]
            }
        ]
    }


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_price_history() -> dict:
    return {
        "MDE:ADZ": {
            "last_price": 250000,
            "last_update": datetime.now().isoformat(),
            "airline": "Avianca",
            "booking_link": "abc123"
        },
        "PEI:ADZ": {
            "last_price": 280000,
            "last_update": datetime.now().isoformat(),
            "airline": "LATAM",
            "booking_link": "xyz789"
        }
    }