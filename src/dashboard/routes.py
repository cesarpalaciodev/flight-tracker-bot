from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
from datetime import datetime
import logging
import os

from src.utils.metrics import CURRENT_PRICES
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
    try:
        import json
        from src.utils.metrics import _METRICS_FILE
        if _METRICS_FILE.exists():
            with open(_METRICS_FILE) as f:
                data = json.load(f)
        else:
            data = {}
    except Exception:
        data = {}
    return {
        "flights_searched_total": int(data.get("flight_tracker_flights_searched_total", 0)),
        "price_checks_total": int(data.get("flight_tracker_price_checks_total", 0)),
        "price_alerts_sent_total": int(data.get("flight_tracker_price_alerts_sent_total", 0)),
        "api_requests_total": int(data.get("flight_tracker_api_requests_total", 0)),
        "rate_limit_hits_total": int(data.get("flight_tracker_rate_limit_hits_total", 0)),
    }


@router.get("/prices")
async def get_current_prices() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    prices = {}
    for dest in DESTINATIONS:
        for origin in ORIGINS:
            route_key = f"{origin}:{dest}"
            data = history.data.get(route_key, {})
            price = data.get("last_price")
            if price is not None:
                prices[route_key] = {
                    "origin": origin, "destination": dest,
                    "price": price, "currency": "COP",
                    "airline": data.get("airline", ""),
                    "last_update": data.get("last_update", ""),
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

    from src.utils.metrics import FLIGHTS_SEARCHED, PRICE_CHECKS, PRICE_ALERTS_SENT
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


@router.get("/price-chart")
async def get_price_chart(route: str = "MDE:ADZ") -> dict:
    try:
        db = Database(DATABASE_URL)
        records = db.get_price_history(route, limit=50)
        return {
            "route": route,
            "points": [
                {"price": r.price, "date": r.checked_at.isoformat(), "airline": r.airline}
                for r in records
            ]
        }
    except Exception:
        return {"route": route, "points": []}


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

    import json
    from src.utils.metrics import _METRICS_FILE
    try:
        if _METRICS_FILE.exists():
            with open(_METRICS_FILE) as f:
                mdata = json.load(f)
        else:
            mdata = {}
    except Exception:
        mdata = {}
    stats["metrics_captured"] = {
        "flights_searched": int(mdata.get("flight_tracker_flights_searched_total", 0)),
        "price_checks": int(mdata.get("flight_tracker_price_checks_total", 0)),
        "alerts_sent": int(mdata.get("flight_tracker_price_alerts_sent_total", 0)),
        "rate_limit_hits": int(mdata.get("flight_tracker_rate_limit_hits_total", 0)),
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