import pytest
from src.models.flight import FlightData


class TestFlightData:
    def test_from_ignav_response_valid(self, sample_flight_response: dict) -> None:
        flight = FlightData.from_ignav_response(
            sample_flight_response["itineraries"][0],
            origin="MDE",
            date="2026-06-15",
            destination="ADZ",
            return_date="2026-06-20"
        )

        assert flight is not None
        assert flight.origin == "MDE"
        assert flight.destination == "ADZ"
        assert flight.price == 150000
        assert flight.currency == "COP"
        assert flight.airline == "Avianca"
        assert flight.date == "2026-06-15"
        assert flight.return_date == "2026-06-20"
        assert flight.outbound_flight == "AV456"
        assert flight.inbound_flight == "AV789"

    def test_from_ignav_response_missing_data(self) -> None:
        flight = FlightData.from_ignav_response(
            {},
            origin="MDE",
            date="2026-06-15",
            destination="ADZ"
        )

        assert flight is not None
        assert flight.origin == "MDE"
        assert flight.price == 0

    def test_from_ignav_response_invalid_data(self) -> None:
        flight = FlightData.from_ignav_response(
            "invalid" if False else [],  # type: ignore
            origin="MDE",
            date="2026-06-15",
            destination="ADZ"
        )

        assert flight is None

    def test_to_dict(self, sample_flight_response: dict) -> None:
        flight = FlightData.from_ignav_response(
            sample_flight_response["itineraries"][0],
            origin="MDE",
            date="2026-06-15",
            destination="ADZ"
        )

        assert flight is not None
        data = flight.to_dict()

        assert isinstance(data, dict)
        assert data["origin"] == "MDE"
        assert data["destination"] == "ADZ"
        assert data["price"] == 150000
        assert "airline" in data
        assert "date" in data

    def test_str_representation(self, sample_flight_response: dict) -> None:
        flight = FlightData.from_ignav_response(
            sample_flight_response["itineraries"][0],
            origin="MDE",
            date="2026-06-15",
            destination="ADZ"
        )

        assert flight is not None
        str_repr = str(flight)

        assert "MDE" in str_repr
        assert "ADZ" in str_repr
        assert "150,000" in str_repr
        assert "Avianca" in str_repr