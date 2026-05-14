import pytest
from pathlib import Path
from src.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_init(self, temp_data_dir: Path) -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = RateLimiter()

            assert limiter.data["requests"] == []
            assert limiter.data["daily_count"] == 0
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file

    def test_is_allowed_initially(self, temp_data_dir: Path) -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = RateLimiter()

            allowed, msg = limiter.is_allowed()

            assert allowed is True
            assert msg == "OK"
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file

    def test_record_request(self, temp_data_dir: Path) -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = RateLimiter()

            limiter.record_request()

            assert len(limiter.data["requests"]) == 1
            assert limiter.data["daily_count"] == 1
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file

    def test_rate_limit_exceeded_per_minute(self, temp_data_dir: Path) -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = RateLimiter()
            limiter.MAX_REQUESTS_PER_MINUTE = 2

            limiter.record_request()
            limiter.record_request()
            limiter.record_request()

            allowed, msg = limiter.is_allowed()

            assert allowed is False
            assert "max 2 requests/minute" in msg
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file

    def test_rate_limit_exceeded_per_hour(self, temp_data_dir: Path) -> None:
        from src.utils import rate_limiter

        original_file = rate_limiter._RATE_LIMIT_FILE
        rate_limiter._RATE_LIMIT_FILE = temp_data_dir / "rate_limit.json"

        try:
            limiter = RateLimiter()
            limiter.MAX_REQUESTS_PER_HOUR = 3

            for _ in range(4):
                limiter.record_request()

            allowed, msg = limiter.is_allowed()

            assert allowed is False
            assert "max 3 requests/hour" in msg
        finally:
            rate_limiter._RATE_LIMIT_FILE = original_file