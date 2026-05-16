"""Structured JSON logger for production logging."""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "ctx") and record.ctx:
            log_entry["ctx"] = record.ctx

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        if record.levelno >= logging.WARNING:
            log_entry["caller"] = f"{record.pathname}:{record.lineno}"

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ContextLogger:
    """Logger wrapper that injects context into every log call."""

    def __init__(self, name: str, context: dict | None = None):
        self._logger = logging.getLogger(name)
        self._context = context or {}

    def _log(self, level: int, msg: str, **kwargs):
        extra = kwargs.pop("extra", {})
        ctx = {**self._context, **extra.get("ctx", {})}
        record = self._logger.makeRecord(self._logger.name, level, "", 0, msg, (), None)
        record.ctx = ctx
        if level >= logging.WARNING:
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back:
                record.pathname = frame.f_back.f_code.co_filename
                record.lineno = frame.f_back.f_lineno
        self._logger.handle(record)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def exception(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)


def setup_logging(
    name: str = "flight_tracker",
    log_file: Path | None = None,
    json_output: bool = True,
) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    if json_output:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


def get_logger(name: str, context: dict | None = None) -> ContextLogger:
    return ContextLogger(name, context)
