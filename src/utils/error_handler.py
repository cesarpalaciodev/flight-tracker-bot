"""Centralized error handling: safe wrappers for async and sync operations."""

import logging
import traceback
from typing import Any, Callable, Optional, TypeVar

from src.utils.logger import get_logger

T = TypeVar("T")

log = get_logger("error_handler")


def safe_call(
    fn: Callable[..., T],
    default: T = None,
    log_level: str = "error",
    context: Optional[dict] = None,
    reraise: bool = False,
    **kwargs,
) -> T:
    """Wraps any callable with full error logging. Returns default on failure."""
    try:
        return fn(**kwargs)
    except Exception as e:
        ctx = {**(context or {}), "function": fn.__name__, "error_type": type(e).__name__}
        msg = f"safe_call failed: {e}"
        if log_level == "warning":
            log.warning(msg, extra={"ctx": ctx})
        else:
            log.error(msg, extra={"ctx": ctx})
            log.error(traceback.format_exc(), extra={"ctx": ctx})
        if reraise:
            raise
        return default


def safe_async(coro, default=None, context: Optional[dict] = None, reraise: bool = False) -> Any:
    """Wraps an async call with error logging. Not used in this codebase (sync)."""
    return safe_call(lambda: coro, default=default, context=context, reraise=reraise)


class ErrorBoundary:
    """Context manager that catches and logs all exceptions from a block."""

    def __init__(self, context: Optional[dict] = None, reraise: bool = False, logger_name: str = "error_boundary"):
        self.context = context or {}
        self.reraise = reraise
        self.log = get_logger(logger_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        ctx = {**self.context, "error_type": exc_type.__name__}
        self.log.error(f"Boundary caught: {exc_val}", extra={"ctx": ctx})
        self.log.error("".join(traceback.format_exception(exc_type, exc_val, exc_tb)), extra={"ctx": ctx})
        return not self.reraise


def silence(exception_types=(Exception,), context: Optional[dict] = None):
    """Decorator that catches exceptions from a function and logs them."""

    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except exception_types as e:
                ctx = {**(context or {}), "function": fn.__name__, "error_type": type(e).__name__}
                get_logger(fn.__module__).error(f"Silenced: {e}", extra={"ctx": ctx})
                return None

        return wrapper

    return decorator
