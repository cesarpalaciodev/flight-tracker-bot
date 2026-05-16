"""Telegram API provider — all Telegram HTTP calls centralized here."""

import logging
from typing import Optional

from src.providers.base import BaseProvider, ApiResult


class TelegramProvider(BaseProvider):
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    def __init__(self, token: str, logger_obj: Optional[logging.Logger] = None):
        super().__init__(logger_obj)
        self.token = token
        self.BASE_URL = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> ApiResult:
        return self._post(
            "/sendMessage",
            json_data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            },
        )

    def get_updates(self, offset: int, timeout: int = 30) -> ApiResult:
        return self._get("/getUpdates", params={"offset": offset, "timeout": timeout}, timeout=timeout + 5)
