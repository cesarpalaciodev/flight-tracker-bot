import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

_BASE_DIR = Path(__file__).parent.parent.parent
_RATE_LIMIT_FILE: Path = _BASE_DIR / "data" / "rate_limit.json"


class RateLimiter:
    MAX_REQUESTS_PER_MINUTE = 10
    MAX_REQUESTS_PER_HOUR = 100

    def __init__(self) -> None:
        self.data: dict = self._load()

    def _load(self) -> dict:
        if _RATE_LIMIT_FILE.exists():
            try:
                with open(_RATE_LIMIT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"requests": [], "daily_count": 0, "last_reset": datetime.now().date().isoformat()}

    def _save(self) -> None:
        try:
            with open(_RATE_LIMIT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def _clean_old_requests(self) -> None:
        cutoff = datetime.now() - timedelta(minutes=2)
        self.data["requests"] = [
            r for r in self.data["requests"]
            if datetime.fromisoformat(r) > cutoff
        ]

    def _reset_daily(self) -> None:
        today = datetime.now().date().isoformat()
        if self.data.get("last_reset") != today:
            self.data["daily_count"] = 0
            self.data["last_reset"] = today

    def is_allowed(self) -> tuple[bool, str]:
        self._reset_daily()
        self._clean_old_requests()

        if len(self.data["requests"]) >= self.MAX_REQUESTS_PER_MINUTE:
            return False, f"Rate limit: max {self.MAX_REQUESTS_PER_MINUTE} requests/minute"

        if self.data["daily_count"] >= self.MAX_REQUESTS_PER_HOUR:
            return False, f"Rate limit: max {self.MAX_REQUESTS_PER_HOUR} requests/hour"

        return True, "OK"

    def record_request(self) -> None:
        self.data["requests"].append(datetime.now().isoformat())
        self.data["daily_count"] += 1
        self._save()

    def wait_if_needed(self, logger: Optional[logging.Logger] = None) -> None:
        allowed, msg = self.is_allowed()
        if not allowed:
            if logger:
                logger.warning(msg)
            time.sleep(60)
            self._clean_old_requests()