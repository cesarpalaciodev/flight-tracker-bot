import pytest
from pydantic import ValidationError

from src.utils.config import AppConfig, IgnavConfig, TelegramConfig


class TestIgnavConfig:
    def test_valid_api_key(self) -> None:
        config = IgnavConfig(api_key="ignav_test_key_123")
        assert config.api_key == "ignav_test_key_123"

    def test_empty_api_key_allowed(self) -> None:
        with pytest.raises(ValidationError):
            IgnavConfig(api_key="")

    def test_api_key_prefix_validation(self) -> None:
        with pytest.raises(ValidationError):
            IgnavConfig(api_key="invalid_key")

    def test_api_key_required(self) -> None:
        with pytest.raises(ValidationError):
            IgnavConfig(api_key="")


class TestTelegramConfig:
    def test_valid_telegram_config(self) -> None:
        config = TelegramConfig(token="123456:ABCDEF", chat_id="987654321")
        assert config.token == "123456:ABCDEF"
        assert config.chat_id == "987654321"

    def test_empty_token_raises(self) -> None:
        with pytest.raises(ValidationError):
            TelegramConfig(token="", chat_id="123")

    def test_token_without_colon_raises(self) -> None:
        with pytest.raises(ValidationError):
            TelegramConfig(token="invalidtoken", chat_id="123")

    def test_chat_id_trimmed(self) -> None:
        config = TelegramConfig(token="123:abc", chat_id="  987654321  ")
        assert config.chat_id == "987654321"


class TestAppConfig:
    def test_default_values(self) -> None:
        config = AppConfig()
        assert config.destinations == ["ADZ"]
        assert config.origins == ["MDE", "PEI"]
        assert config.adults == 2
        assert config.return_days == 5
        assert config.check_interval_hours == 8

    def test_custom_origins_string(self) -> None:
        config = AppConfig(origins="MDE, BOG, PEI")
        assert config.origins == ["MDE", "BOG", "PEI"]

    def test_custom_origins_list(self) -> None:
        config = AppConfig(origins=["BOG"])
        assert config.origins == ["BOG"]

    def test_adults_validation_low(self) -> None:
        with pytest.raises(ValidationError):
            AppConfig(adults=0)

    def test_adults_validation_high(self) -> None:
        with pytest.raises(ValidationError):
            AppConfig(adults=10)

    def test_return_days_validation(self) -> None:
        with pytest.raises(ValidationError):
            AppConfig(return_days=0)

        with pytest.raises(ValidationError):
            AppConfig(return_days=100)
