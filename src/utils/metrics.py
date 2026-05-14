from prometheus_client import Counter, Gauge, Histogram, start_http_server
import logging
from typing import Optional


FLIGHTS_SEARCHED = Counter(
    "flight_tracker_flights_searched_total",
    "Total number of flights searched"
)

PRICE_CHECKS = Counter(
    "flight_tracker_price_checks_total",
    "Total number of price checks performed"
)

PRICE_ALERTS_SENT = Counter(
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

RATE_LIMIT_HITS = Counter(
    "flight_tracker_rate_limit_hits_total",
    "Number of times rate limit was hit"
)

SERVICE_UPTIME = Gauge(
    "flight_tracker_uptime_seconds",
    "Service uptime in seconds"
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