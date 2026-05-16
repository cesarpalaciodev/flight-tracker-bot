import json
import logging
import time
from typing import Any

import redis

logger = logging.getLogger(__name__)


class PriceCache:
    DEFAULT_TTL = 3600
    PREFIX = "flight_tracker:"

    def __init__(self, redis_url: str = ""):
        self.client: redis.Redis | None = None
        self.enabled = bool(redis_url)
        if self.enabled:
            try:
                self.client = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                self.client.ping()
                logger.info(f"Redis cache connected: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis cache unavailable, falling back to local cache: {e}")
                self.enabled = False
                self.client = None

        self._local: dict[str, tuple[float, Any]] = {}

    def _key(self, *parts: str) -> str:
        return f"{self.PREFIX}{':'.join(parts)}"

    def get(self, *parts: str) -> Any | None:
        key = self._key(*parts)
        if self.enabled and self.client:
            try:
                value = self.client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")
                self.enabled = False

        if key in self._local:
            expire_at, value = self._local[key]
            if time.time() < expire_at:
                return value
            del self._local[key]
        return None

    def set(self, value: Any, ttl: int = DEFAULT_TTL, *parts: str) -> None:
        key = self._key(*parts)
        if self.enabled and self.client:
            try:
                self.client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")
                self.enabled = False

        self._local[key] = (time.time() + ttl, value)

    def delete(self, *parts: str) -> None:
        key = self._key(*parts)
        if self.enabled and self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass
        self._local.pop(key, None)

    def clear(self) -> None:
        if self.enabled and self.client:
            try:
                for key in self.client.scan_iter(f"{self.PREFIX}*"):
                    self.client.delete(key)
            except Exception:
                pass
        self._local.clear()

    def get_or_set(self, ttl: int, *parts: str, factory) -> Any:
        cached = self.get(*parts)
        if cached is not None:
            return cached
        value = factory()
        self.set(value, ttl, *parts)
        return value

    def search_result(self, origin: str, destination: str, date: str) -> dict | None:
        return self.get("search", origin, destination, date)

    def set_search_result(self, origin: str, destination: str, date: str, data: dict, ttl: int = DEFAULT_TTL) -> None:
        self.set(data, ttl, "search", origin, destination, date)

    def booking_link(self, ignav_id: str) -> str | None:
        return self.get("booking", ignav_id)

    def set_booking_link(self, ignav_id: str, url: str, ttl: int = 7200) -> None:
        self.set(url, ttl, "booking", ignav_id)
