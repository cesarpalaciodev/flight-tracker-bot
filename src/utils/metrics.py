import json
import logging
import threading
from pathlib import Path

from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger("metrics")
_METRICS_FILE = Path(__file__).parent.parent.parent / "data" / "metrics.json"
_lock = threading.Lock()


def _load_persisted() -> dict:
    try:
        if _METRICS_FILE.exists():
            with open(_METRICS_FILE) as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Corrupted metrics file: {e}, starting fresh")
    except OSError as e:
        logger.error(f"Cannot read metrics file: {e}")
    return {}


def _save_persisted(data: dict) -> None:
    try:
        _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_METRICS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        logger.error(f"Cannot save metrics file: {e}")


class PersistentCounter:
    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.prom_counter = Counter(name, documentation, labelnames=list(labelnames) if labelnames else [])
        self._value = 0.0
        self._labelnames = labelnames

        persisted = _load_persisted()
        if name in persisted:
            saved = persisted[name]
            if isinstance(saved, (int, float)):
                self._value = saved
                self.prom_counter.inc(saved)
            elif isinstance(saved, dict):
                for labels, val in saved.items():
                    self._value += val
                    try:
                        if labelnames:
                            self.prom_counter.labels(**eval(labels)).inc(val)
                        else:
                            self.prom_counter.inc(val)
                    except Exception as e:
                        logger.error(f"Failed to load prometheus label {labels}: {e}")
                        self.prom_counter.inc(val)

    def inc(self, amount: float = 1, labels: dict | None = None) -> None:
        with _lock:
            self._value += amount
            try:
                if labels:
                    self.prom_counter.labels(**labels).inc(amount)
                else:
                    self.prom_counter.inc(amount)
            except Exception as e:
                logger.error(f"Prometheus inc error for {self.name}: {e}")

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
                logger.error(f"Metrics save error for {self.name}: {e}")

    def get(self) -> float:
        return self._value


FLIGHTS_SEARCHED = PersistentCounter("flight_tracker_flights_searched_total", "Total number of flights searched")
PRICE_CHECKS = PersistentCounter("flight_tracker_price_checks_total", "Total number of price checks performed")
PRICE_ALERTS_SENT = PersistentCounter(
    "flight_tracker_price_alerts_sent_total", "Total number of price drop alerts sent"
)
CURRENT_PRICES = Gauge(
    "flight_tracker_current_price_cop", "Current lowest price in COP", ["origin", "destination", "airline"]
)
API_REQUESTS = Counter("flight_tracker_api_requests_total", "Total API requests made", ["status"])
API_LATENCY = Histogram("flight_tracker_api_latency_seconds", "API request latency", ["endpoint"])
RATE_LIMIT_HITS = PersistentCounter("flight_tracker_rate_limit_hits_total", "Number of times rate limit was hit")


class MetricsServer:
    def __init__(self, port: int = 9090, logger_obj: logging.Logger | None = None) -> None:
        self.port = port
        self.logger = logger_obj or logger
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        try:
            start_http_server(self.port)
            self._started = True
            self.logger.info(f"Metrics server started on port {self.port}")
        except OSError as e:
            self.logger.warning(f"Metrics server on port {self.port} unavailable: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {e}")

    @property
    def is_started(self) -> bool:
        return self._started


METRICS_SERVER: MetricsServer | None = None


def get_metrics_server(port: int = 9090, logger_obj: logging.Logger | None = None) -> MetricsServer:
    global METRICS_SERVER
    if METRICS_SERVER is None:
        METRICS_SERVER = MetricsServer(port, logger_obj)
    return METRICS_SERVER
