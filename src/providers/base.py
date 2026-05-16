"""Base provider for external API calls with retry, rate limiting, and error normalization."""

import time
from enum import Enum
from typing import Any

import requests

from src.utils.logger import get_logger


class ApiStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


class ApiResult:
    """Normalized response from any external API."""

    def __init__(self, status: ApiStatus, data: Any = None, error: str = "", status_code: int = 0):
        self.status = status
        self.data = data
        self.error = error
        self.status_code = status_code

    @property
    def is_ok(self) -> bool:
        return self.status == ApiStatus.SUCCESS

    @classmethod
    def ok(cls, data: Any, status_code: int = 200) -> "ApiResult":
        return cls(ApiStatus.SUCCESS, data, status_code=status_code)

    @classmethod
    def fail(cls, error: str, status_code: int = 0) -> "ApiResult":
        return cls(ApiStatus.ERROR, error=error, status_code=status_code)

    @classmethod
    def rate_limited(cls, retry_after: int = 0) -> "ApiResult":
        return cls(ApiStatus.RATE_LIMITED, error=f"Rate limited. Retry after {retry_after}s", status_code=429)

    @classmethod
    def timeout(cls, timeout_sec: float = 0) -> "ApiResult":
        return cls(ApiStatus.TIMEOUT, error=f"Request timed out after {timeout_sec}s")


class BaseProvider:
    """Base class for external API providers with built-in retry and error handling."""

    BASE_URL = ""
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    RATE_LIMIT_WAIT = 60
    PROVIDER_NAME = "base"

    def __init__(self):
        self.log = get_logger(f"provider.{self.PROVIDER_NAME}")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _classify_error(self, response: requests.Response) -> ApiResult:
        if response.status_code == 429:
            return ApiResult.rate_limited()
        if response.status_code == 404:
            return ApiResult(ApiStatus.NOT_FOUND, status_code=404, error="Resource not found")
        return ApiResult.fail(error=response.text[:300], status_code=response.status_code)

    def _request(
        self,
        method: str,
        url: str,
        json_data: dict | None = None,
        params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
    ) -> ApiResult:
        last_error: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                hdrs = {**(headers or {})}
                resp = self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    timeout=timeout or self.DEFAULT_TIMEOUT,
                    headers=hdrs if hdrs else None,
                )
                if resp.status_code == 200:
                    return ApiResult.ok(data=resp.json(), status_code=200)
                if resp.status_code in (429, 503):
                    self.log.warning(f"Rate limited on {url}, waiting {self.RATE_LIMIT_WAIT}s")
                    time.sleep(self.RATE_LIMIT_WAIT)
                    continue
                return self._classify_error(resp)

            except requests.exceptions.Timeout as e:
                last_error = e
                self.log.warning(f"Timeout on {url} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                return ApiResult.timeout(timeout_sec=timeout or self.DEFAULT_TIMEOUT)

            except requests.exceptions.ConnectionError as e:
                last_error = e
                self.log.warning(f"Connection error on {url} (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                return ApiResult.fail(error=str(e))

            except requests.exceptions.RequestException as e:
                self.log.error(f"Request failed on {url}: {e}")
                return ApiResult.fail(error=str(e))

        return ApiResult.fail(error=str(last_error or "Max retries exceeded"))

    def _get(self, url: str, params: dict | None = None, timeout: int | None = None) -> ApiResult:
        return self._request("GET", url, params=params, timeout=timeout)

    def _post(self, url: str, json_data: dict | None = None, timeout: int | None = None) -> ApiResult:
        return self._request("POST", url, json_data=json_data, timeout=timeout)

    def close(self) -> None:
        self.session.close()
