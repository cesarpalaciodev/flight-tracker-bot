import logging
import os
import re


class SensitiveDataFilter(logging.Filter):
    PATTERNS = [  # noqa: RUF012
        (
            re.compile(r"(IGNAV_API_KEY|api_key|API_KEY)[=:]\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?", re.IGNORECASE),
            r"\1=***REDACTED***",
        ),
        (
            re.compile(r"(TELEGRAM_TOKEN|TELEGRAM_BOT_TOKEN)[=:]\s*['\"]?(\d+:[\w\-]+)['\"]?", re.IGNORECASE),
            r"\1=***REDACTED***",
        ),
        (
            re.compile(r"(TELEGRAM_CHAT_ID|chat_id|CHAT_ID)[=:]\s*['\"]?(\d+)['\"]?", re.IGNORECASE),
            r"\1=***REDACTED***",
        ),
        (re.compile(r"(token|Bearer)\s+['\"]?([a-zA-Z0-9_\-:\.]+)['\"]?", re.IGNORECASE), r"\1 ***REDACTED***"),
        (
            re.compile(r"(X-Api-Key|api-key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?", re.IGNORECASE),
            r"\1: ***REDACTED***",
        ),
        (re.compile(r"ignav_[a-zA-Z0-9_\-]+"), "ignav_***REDACTED***"),
        (re.compile(r"(\d{6,}:)[a-zA-Z0-9_\-]+"), r"\1***REDACTED***"),
        (re.compile(r"(password|passwd|pwd)[=:]\s*['\"]?[^\s'\"]{4,}['\"]?", re.IGNORECASE), r"\1=***REDACTED***"),
        (re.compile(r"sign=[a-zA-Z0-9_\-]+"), "sign=***REDACTED***"),
        (re.compile(r"sig=[a-zA-Z0-9_\-]+"), "sig=***REDACTED***"),
        (re.compile(r"_ga=[^;]+;?"), "_ga=***REDACTED***;"),
        (re.compile(r"auth=[^;&]+;?"), "auth=***REDACTED***;"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and record.msg:
            record.msg = self._sanitize(str(record.msg))
        if hasattr(record, "args") and record.args:
            record.args = tuple(self._sanitize(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True

    def _sanitize(self, text: str) -> str:
        result = text
        for pattern, replacement in self.PATTERNS:
            result = pattern.sub(replacement, result)
        return result


class RequestBodyFilter(logging.Filter):
    SENSITIVE_KEYS = {  # noqa: RUF012
        "api_key",
        "token",
        "password",
        "secret",
        "auth",
        "ignav_id",
        "x-api-key",
        "authorization",
        "chat_id",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and record.msg:
            record.msg = self._filter_json(str(record.msg))
        return True

    def _filter_json(self, text: str) -> str:
        import json

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                filtered = self._filter_dict(data)
                return json.dumps(filtered)
        except (json.JSONDecodeError, TypeError):
            return text

    def _filter_dict(self, data: dict) -> dict:
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in self.SENSITIVE_KEYS or any(sk in key_lower for sk in self.SENSITIVE_KEYS):
                result[key] = "***REDACTED***"
            elif isinstance(value, dict):
                result[key] = self._filter_dict(value)
            elif isinstance(value, list):
                result[key] = self._filter_list(value)
            else:
                result[key] = value
        return result

    def _filter_list(self, data: list) -> list:
        return [self._filter_dict(item) if isinstance(item, dict) else item for item in data]


def setup_secure_logging(name: str = "flight_tracker") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(os.getenv("LOG_FILE", "logs/flight_tracker.log"))
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    file_handler.addFilter(RequestBodyFilter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)

    return logger
