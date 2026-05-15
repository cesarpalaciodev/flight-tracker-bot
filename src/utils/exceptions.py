import logging
from typing import Optional


class FlightTrackerError(Exception):
    """Base exception for Flight Tracker."""
    pass


class APIError(FlightTrackerError):
    """API request failed."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class APIRateLimited(APIError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__("API rate limit exceeded")
        self.retry_after = retry_after


class APITimeout(APIError):
    """API request timed out."""
    def __init__(self, timeout: float):
        super().__init__(f"API request timed out after {timeout}s")
        self.timeout = timeout


class TelegramError(FlightTrackerError):
    """Telegram message failed."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ConfigError(FlightTrackerError):
    """Configuration error."""
    pass


class DatabaseError(FlightTrackerError):
    """Database operation failed."""
    pass


class CacheError(FlightTrackerError):
    """Cache operation failed."""
    pass


class FlightNotFoundError(FlightTrackerError):
    """No flights found for the given route."""
    def __init__(self, origin: str, destination: str, date: str):
        super().__init__(f"No flights found for {origin} -> {destination} on {date}")
        self.origin = origin
        self.destination = destination
        self.date = date


class PriceAlertError(FlightTrackerError):
    """Failed to send price alert."""
    pass


def handle_api_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    if isinstance(error, APIRateLimited):
        logger.warning(f"[{context}] API rate limited. Waiting {error.retry_after or 60}s")
    elif isinstance(error, APITimeout):
        logger.error(f"[{context}] API timeout: {error.timeout}s")
    elif isinstance(error, APIError):
        logger.error(f"[{context}] API error: {error}")
    elif isinstance(error, TelegramError):
        logger.warning(f"[{context}] Telegram error (code {error.status_code}): {error}")
    elif isinstance(error, FlightTrackerError):
        logger.error(f"[{context}] {error}")
    else:
        logger.exception(f"[{context}] Unexpected error: {error}")