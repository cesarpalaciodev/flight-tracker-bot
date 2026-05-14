import pytest
import logging
from src.utils.security import SensitiveDataFilter, RequestBodyFilter, setup_secure_logging


class TestSensitiveDataFilter:
    def setup_method(self) -> None:
        self.filter = SensitiveDataFilter()

    def test_filters_ignav_api_key(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "API key: ignav_test123", (), None
        )
        self.filter.filter(record)
        assert "ignav_test123" not in record.msg
        assert "REDACTED" in record.msg

    def test_filters_telegram_token(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "Token: 123456:ABCDEF", (), None
        )
        self.filter.filter(record)
        assert "123456:ABCDEF" not in record.msg
        assert "REDACTED" in record.msg

    def test_filters_password(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "password=mypassword123", (), None
        )
        self.filter.filter(record)
        assert "mypassword123" not in record.msg
        assert "REDACTED" in record.msg

    def test_passes_clean_message(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "Flight found: MDE -> ADZ", (), None
        )
        result = self.filter.filter(record)
        assert result is True
        assert "MDE" in record.msg

    def test_filters_bearer_token(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "Bearer mysecrettoken", (), None
        )
        self.filter.filter(record)
        assert "mysecrettoken" not in record.msg


class TestRequestBodyFilter:
    def setup_method(self) -> None:
        self.filter = RequestBodyFilter()

    def test_filters_sensitive_json_keys(self) -> None:
        import json
        body = json.dumps({"api_key": "secret123", "origin": "MDE"})
        record = logging.LogRecord("name", logging.INFO, "", 0, body, (), None)
        self.filter.filter(record)

        result = json.loads(record.msg)
        assert result["api_key"] == "***REDACTED***"
        assert result["origin"] == "MDE"

    def test_passes_non_json(self) -> None:
        record = logging.LogRecord(
            "name", logging.INFO, "", 0, "Simple log message", (), None
        )
        result = self.filter.filter(record)
        assert result is True


class TestSetupSecureLogging:
    def test_returns_logger(self) -> None:
        logger = setup_secure_logging("test_logger")
        assert logger.name == "test_logger"

    def test_logger_has_secure_handlers(self) -> None:
        import sys
        logger = logging.getLogger("test_secure_logger_" + str(id(self)))
        result = setup_secure_logging("test_secure_logger_" + str(id(self)))
        assert len(result.handlers) > 0