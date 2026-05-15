import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, start_http_server


_METRICS_FILE = Path(__file__).parent.parent.parent / "data" / "metrics.json"
_lock = threading.Lock()


def _load_persisted() -> dict:
    try:
        if _METRICS_FILE.exists():
            with open(_METRICS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_persisted(data: dict) -> None:
    try:
        _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_METRICS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class PersistentCounter:
    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.prom_counter = Counter(name, documentation, labelnames=list(labelnames) if labelnames else [])
        self._value = 0.0
        self._labelnames = labelnames

        persisted = _load_persisted()
        if name in persisted:
            saved = persisted[name]
            if isinstance(saved, dict):
                for labels, val in saved.items():
                    self._value += val
                    try:
                        if labelnames:
                            self.prom_counter.labels(**eval(labels)).inc(val)
                        else:
                            self.prom_counter.inc(val)
                    except Exception:
                        self.prom_counter.inc(val)
            elif isinstance(saved, (int, float)):
                self._value = saved
                self.prom_counter.inc(saved)

    def inc(self, amount: float = 1, labels: Optional[dict] = None) -> None:
        with _lock:
            self._value += amount
            try:
                if labels:
                    self.prom_counter.labels(**labels).inc(amount)
                else:
                    self.prom_counter.inc(amount)
            except Exception as e:
                import traceback
                logging.getLogger("metrics").error(f"Prometheus inc error: {e}\n{traceback.format_exc()}")

            try:
                persisted = _load_persisted()
                if labels:
                    label_key = str(sorted(labels.items()))
                    if self.name not in persisted:
                        persisted[self.name] = {}
                    persisted[self.name][label_key] = persisted[self.name].get(label_key, 0) + amount
                else:
                    persisted[self.name] = persisted.get(self.name, 0) + amount
                _save_persisted(persisted)
            except Exception as e:
                import traceback
                logging.getLogger("metrics").error(f"Metrics save error: {e}\n{traceback.format_exc()}")

    def get(self) -> float:
        return self._value


FLIGHTS_SEARCHED = PersistentCounter(
    "flight_tracker_flights_searched_total",
    "Total number of flights searched"
)

PRICE_CHECKS = PersistentCounter(
    "flight_tracker_price_checks_total",
    "Total number of price checks performed"
)

PRICE_ALERTS_SENT = PersistentCounter(
    "flight_tracker_price_alerts_sent_total",
    "Total number of price drop alerts sent"
)

CURRENT_PRICES = Gauge(
    "flight_tracker_current_price_cop",
    "Current lowest price in COP",
    ["origin", "destination", "airline"]
)

API_REQUESTS = Counter(
    "flight_tracker_api_requests_total",
    "Total API requests made",
    ["status"]
)

API_LATENCY = Histogram(
    "flight_tracker_api_latency_seconds",
    "API request latency",
    ["endpoint"]
)

RATE_LIMIT_HITS = PersistentCounter(
    "flight_tracker_rate_limit_hits_total",
    "Number of times rate limit was hit"
)


class MetricsServer:
    def __init__(self, port: int = 8000, logger: Optional[logging.Logger] = None) -> None:
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        try:
            start_http_server(self.port)
            self._started = True
            self.logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {e}")

    @property
    def is_started(self) -> bool:
        return self._started


METRICS_SERVER: Optional[MetricsServer] = None


def get_metrics_server(port: int = 8000, logger: Optional[logging.Logger] = None) -> MetricsServer:
    global METRICS_SERVER
    if METRICS_SERVER is None:
        METRICS_SERVER = MetricsServer(port, logger)
    return METRICS_SERVER