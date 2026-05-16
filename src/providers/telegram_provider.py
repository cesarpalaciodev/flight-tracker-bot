"""Telegram API provider — all Telegram HTTP calls centralized here."""

from src.providers.base import ApiResult, BaseProvider


class TelegramProvider(BaseProvider):
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    PROVIDER_NAME = "telegram"

    def __init__(self, token: str):
        super().__init__()
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
