"""Application error hierarchy with context support."""



class AppError(Exception):
    """Base application error with context."""

    def __init__(self, message: str, context: dict | None = None, cause: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
        }


class ConfigError(AppError):
    """Configuration error."""

    pass


class DatabaseError(AppError):
    """Database operation failed."""

    pass


class CacheError(AppError):
    """Cache operation failed."""

    pass


class APIError(AppError):
    """External API request failed."""

    def __init__(self, message: str, status_code: int | None = None, response: str | None = None, **kwargs):
        ctx = kwargs.pop("context", {})
        ctx.update({"status_code": status_code, "response_preview": (response or "")[:200]})
        super().__init__(message, context=ctx, **kwargs)
        self.status_code = status_code
        self.response = response


class APIRateLimited(APIError):
    """API rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        super().__init__("API rate limit exceeded", status_code=429, context={"retry_after": retry_after})
        self.retry_after = retry_after


class APITimeout(APIError):
    """API request timed out."""

    def __init__(self, timeout_sec: float):
        super().__init__(f"API request timed out after {timeout_sec}s", context={"timeout": timeout_sec})
        self.timeout = timeout_sec


class TelegramError(AppError):
    """Telegram message failed."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message, context={"status_code": status_code})
        self.status_code = status_code


class FlightNotFoundError(AppError):
    """No flights found for a route."""

    def __init__(self, origin: str, destination: str, date: str):
        super().__init__(
            f"No flights for {origin} -> {destination} on {date}",
            context={
                "origin": origin,
                "destination": destination,
                "date": date,
            },
        )


class PriceAlertError(AppError):
    """Failed to send price alert."""

    pass


class ProviderError(AppError):
    """External provider call failed."""

    pass
