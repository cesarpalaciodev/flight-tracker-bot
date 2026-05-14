from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from src.utils.metrics import (
    FLIGHTS_SEARCHED,
    PRICE_CHECKS,
    PRICE_ALERTS_SENT,
    CURRENT_PRICES,
    API_REQUESTS,
    RATE_LIMIT_HITS,
    SERVICE_UPTIME,
)
from src.models.price_history import PriceHistory
from src.utils.config import PRICE_HISTORY_FILE, ORIGINS, DESTINATION


router = APIRouter(prefix="/api", tags=["metrics"])
logger = logging.getLogger("dashboard_routes")


@router.get("/metrics")
async def get_metrics() -> dict:
    return {
        "flights_searched_total": FLIGHTS_SEARCHED._value.get(),
        "price_checks_total": PRICE_CHECKS._value.get(),
        "price_alerts_sent_total": PRICE_ALERTS_SENT._value.get(),
        "api_requests_total": {
            k: v._value.get() for k, v in API_REQUESTS._metrics.items()
        },
        "rate_limit_hits_total": RATE_LIMIT_HITS._value.get(),
    }


@router.get("/prices")
async def get_current_prices() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    prices = {}

    for origin in ORIGINS:
        route_key = f"{origin}:{DESTINATION}"
        price = history.get_last_price(route_key)
        if price is not None:
            prices[route_key] = {
                "origin": origin,
                "destination": DESTINATION,
                "price": price,
                "currency": "COP"
            }

    return {
        "timestamp": datetime.now().isoformat(),
        "routes": prices
    }


@router.get("/price-history/{route}")
async def get_route_price_history(route: str) -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    route_key = route.upper()

    data = history.data.get(route_key, {})
    last_price = data.get("last_price")
    last_update = data.get("last_update")
    airline = data.get("airline")

    return {
        "route": route_key,
        "last_price": last_price,
        "last_update": last_update,
        "airline": airline,
        "currency": "COP"
    }


@router.get("/price-comparison")
async def compare_prices() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    comparisons = []

    for origin in ORIGINS:
        route_key = f"{origin}:{DESTINATION}"
        current_price = history.get_last_price(route_key)
        data = history.data.get(route_key, {})

        comparisons.append({
            "route": route_key,
            "origin": origin,
            "destination": DESTINATION,
            "current_price": current_price,
            "airline": data.get("airline"),
            "last_update": data.get("last_update"),
            "currency": "COP"
        })

    comparisons.sort(key=lambda x: x["current_price"] or float("inf"))

    return {
        "timestamp": datetime.now().isoformat(),
        "routes": comparisons
    }


@router.post("/simulate-check")
async def simulate_price_check(
    origin: str = Query(default="MDE"),
    price: float = Query(default=150000),
    airline: str = Query(default="Avianca")
) -> dict:
    route_key = f"{origin.upper()}:{DESTINATION}"
    history = PriceHistory(PRICE_HISTORY_FILE)

    history.update_price(
        route_key,
        {
            "price": price,
            "last_update": datetime.now().isoformat(),
            "airline": airline,
            "booking_link": f"sim_{origin}_{price}"
        }
    )

    CURRENT_PRICES.labels(
        origin=origin.upper(),
        destination=DESTINATION,
        airline=airline
    ).set(price)

    PRICE_CHECKS.inc()
    FLIGHTS_SEARCHED.inc()

    previous = history.get_last_price(route_key)
    price_drop = None
    if previous and price < previous:
        price_drop = previous - price
        PRICE_ALERTS_SENT.inc()
        logger.info(f"Price drop simulated: {price_drop}")

    return {
        "status": "ok",
        "route": route_key,
        "price_recorded": price,
        "price_drop_from_previous": price_drop,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/routes")
async def get_routes() -> dict:
    routes = []
    for origin in ORIGINS:
        routes.append({
            "origin": origin,
            "destination": DESTINATION,
            "route_key": f"{origin}:{DESTINATION}"
        })

    return {
        "routes": routes,
        "count": len(routes)
    }


@router.get("/statistics")
async def get_statistics() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    stats = {
        "total_routes": len(ORIGINS),
        "routes_with_data": 0,
        "lowest_price": None,
        "highest_price": None,
        "total_updates": 0,
    }

    prices = []
    for origin in ORIGINS:
        route_key = f"{origin}:{DESTINATION}"
        price = history.get_last_price(route_key)
        if price is not None:
            stats["routes_with_data"] += 1
            prices.append(price)
            stats["total_updates"] += 1

    if prices:
        stats["lowest_price"] = min(prices)
        stats["highest_price"] = max(prices)

    stats["metrics_captured"] = {
        "flights_searched": FLIGHTS_SEARCHED._value.get(),
        "price_checks": PRICE_CHECKS._value.get(),
        "alerts_sent": PRICE_ALERTS_SENT._value.get(),
        "rate_limit_hits": RATE_LIMIT_HITS._value.get(),
    }

    return stats