from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
from datetime import datetime
import logging
import os

from src.utils.metrics import (
    FLIGHTS_SEARCHED, PRICE_CHECKS, PRICE_ALERTS_SENT,
    CURRENT_PRICES, API_REQUESTS, RATE_LIMIT_HITS,
)
from src.utils.config import (
    PRICE_HISTORY_FILE, ORIGINS, DESTINATIONS, DATA_DIR, DATABASE_URL
)
from src.services.export import export_price_history_csv, get_stats_summary
from src.models.price_history import PriceHistory
from src.models.database import Database, PriceRecord


router = APIRouter(prefix="/api", tags=["dashboard"])
logger = logging.getLogger("dashboard_routes")
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "")


def verify_token(authorization: str = Header(None)):
    if DASHBOARD_TOKEN:
        token = authorization.replace("Bearer ", "") if authorization else ""
        if token != DASHBOARD_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")
    return True


@router.get("/metrics")
async def get_metrics() -> dict:
    return {
        "flights_searched_total": int(FLIGHTS_SEARCHED._value.get()),
        "price_checks_total": int(PRICE_CHECKS._value.get()),
        "price_alerts_sent_total": int(PRICE_ALERTS_SENT._value.get()),
        "api_requests_total": sum(v._value.get() for v in API_REQUESTS._metrics.values()),
        "rate_limit_hits_total": int(RATE_LIMIT_HITS._value.get()),
    }


@router.get("/prices")
async def get_current_prices() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    prices = {}
    for dest in DESTINATIONS:
        for origin in ORIGINS:
            route_key = f"{origin}:{dest}"
            price = history.get_last_price(route_key)
            if price is not None:
                prices[route_key] = {
                    "origin": origin, "destination": dest,
                    "price": price, "currency": "COP"
                }
    return {"timestamp": datetime.now().isoformat(), "routes": prices}


@router.get("/price-comparison")
async def compare_prices() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    comparisons = []
    for dest in DESTINATIONS:
        for origin in ORIGINS:
            route_key = f"{origin}:{dest}"
            price = history.get_last_price(route_key)
            data = history.data.get(route_key, {})
            comparisons.append({
                "route": route_key, "origin": origin, "destination": dest,
                "current_price": price, "airline": data.get("airline"),
                "last_update": data.get("last_update"), "currency": "COP"
            })
    comparisons.sort(key=lambda x: x["current_price"] or float("inf"))
    return {"timestamp": datetime.now().isoformat(), "routes": comparisons}


@router.get("/price-history/{route}")
async def get_route_price_history(route: str) -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    route_key = route.upper()
    data = history.data.get(route_key, {})
    return {
        "route": route_key,
        "last_price": data.get("last_price"),
        "last_update": data.get("last_update"),
        "airline": data.get("airline"),
        "currency": "COP"
    }


@router.post("/simulate-check")
async def simulate_price_check(
    origin: str = Query("MDE"),
    destination: str = Query("ADZ"),
    price: float = Query(150000),
    airline: str = Query("Avianca")
) -> dict:
    route_key = f"{origin.upper()}:{destination.upper()}"
    history = PriceHistory(PRICE_HISTORY_FILE)

    previous = history.get_last_price(route_key)
    history.update_price(route_key, {
        "price": price, "last_update": datetime.now().isoformat(),
        "airline": airline, "booking_link": f"sim_{origin}_{price}"
    })

    CURRENT_PRICES.labels(origin=origin.upper(), destination=destination.upper(), airline=airline).set(price)
    PRICE_CHECKS.inc()
    FLIGHTS_SEARCHED.inc()

    price_drop = None
    if previous and price < previous:
        price_drop = previous - price
        PRICE_ALERTS_SENT.inc()

    return {
        "status": "ok", "route": route_key,
        "price_recorded": price,
        "previous_price": previous,
        "price_drop": price_drop,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/export/csv")
async def export_csv():
    history = PriceHistory(PRICE_HISTORY_FILE)
    csv_content = export_price_history_csv(history)
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=flight_prices_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@router.get("/statistics")
async def get_statistics() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    stats = get_stats_summary(history)

    db_stats = {}
    try:
        db = Database(DATABASE_URL)
        alerts = db.get_alerts(limit=5)
        with db.get_session() as session:
            db_stats["total_price_records"] = session.query(PriceRecord).limit(1000).count()
        db_stats["recent_alerts"] = [
            {"type": a.alert_type, "route": a.route, "diff": a.difference,
             "at": a.sent_at.isoformat()} for a in alerts
        ]
    except Exception:
        db_stats = {"error": "Database unavailable"}

    stats["metrics_captured"] = {
        "flights_searched": int(FLIGHTS_SEARCHED._value.get()),
        "price_checks": int(PRICE_CHECKS._value.get()),
        "alerts_sent": int(PRICE_ALERTS_SENT._value.get()),
        "rate_limit_hits": int(RATE_LIMIT_HITS._value.get()),
    }
    stats["database"] = db_stats
    return stats


@router.get("/routes")
async def get_routes() -> dict:
    return {
        "routes": [
            {"origin": o, "destination": d, "route_key": f"{o}:{d}"}
            for d in DESTINATIONS for o in ORIGINS
        ],
        "count": len(DESTINATIONS) * len(ORIGINS)
    }


@router.get("/config")
async def get_config() -> dict:
    return {
        "origins": ORIGINS,
        "destinations": DESTINATIONS,
        "adults": 2,
        "return_days": 5,
        "check_interval_hours": 8,
    }


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}