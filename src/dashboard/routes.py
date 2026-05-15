from fastapi import APIRouter, HTTPException, Query, Header, Request
from typing import Optional
from datetime import datetime
import logging
import json

from src.utils.metrics import CURRENT_PRICES
from src.utils.config import PRICE_HISTORY_FILE, ORIGINS, DESTINATIONS, DATABASE_URL
from src.utils.metrics import _METRICS_FILE
from src.services.export import export_price_history_csv, get_stats_summary
from src.models.price_history import PriceHistory
from src.models.database import Database, PriceRecord, UserConfig, AlertLog
from src.dashboard.auth import create_token, verify_token, verify_webhook_signature
from src.utils.secrets import ADMIN_CHAT_IDS


router = APIRouter(prefix="/api", tags=["dashboard"])
logger = logging.getLogger("dashboard_routes")


def get_db() -> Database:
    return Database(DATABASE_URL)


@router.get("/metrics")
async def get_metrics() -> dict:
    try:
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


@router.post("/login")
async def login(chat_id: str = Query(""), admin_chat_id: str = Query("")) -> dict:
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id required")
    db = get_db()
    user = db.get_user_config(chat_id)
    if not user:
        return {"error": "User not found. First register via Telegram /start"}
    token = create_token(chat_id)
    is_admin = chat_id in ADMIN_CHAT_IDS
    return {
        "token": token,
        "chat_id": chat_id,
        "is_admin": is_admin,
        "plan": db.get_subscription(chat_id).plan if db.get_subscription(chat_id) else "trial",
    }


@router.get("/user/{chat_id}")
async def get_user_data(chat_id: str) -> dict:
    db = get_db()
    user = db.get_user_config(chat_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sub = db.get_subscription(chat_id)
    alerts = db.get_alerts(chat_id, limit=10)
    return {
        "config": {
            "origins": user.origins,
            "destinations": user.destinations,
            "adults": user.adults,
            "luggage": user.luggage,
            "max_budget": user.max_budget,
            "non_stop_only": user.non_stop_only,
        },
        "subscription": {
            "plan": sub.plan if sub else "trial",
            "status": sub.status if sub else "none",
            "api_used": sub.api_requests_month if sub else 0,
            "api_limit": sub.api_requests_limit if sub else 10,
            "trial_ends": sub.trial_ends_at.isoformat() if sub and sub.trial_ends_at else None,
        },
        "recent_alerts": [
            {"type": a.alert_type, "route": a.route, "diff": a.difference, "time": a.sent_at.isoformat()}
            for a in alerts
        ],
    }


@router.get("/user/{chat_id}/prices")
async def get_user_prices(chat_id: str) -> dict:
    db = get_db()
    records = db.get_price_history(chat_id, limit=30)
    seen = {}
    for r in records:
        key = f"{r.origin}:{r.destination}"
        if key not in seen:
            seen[key] = {
                "origin": r.origin,
                "destination": r.destination,
                "price": r.price,
                "airline": r.airline,
                "date": r.checked_at.isoformat(),
                "luggage_match": r.luggage_match,
                "budget_match": r.budget_match,
            }
    return {"routes": list(seen.values())}


@router.post("/logout")
async def logout(token: str = Header(None)) -> dict:
    return {"status": "logged_out"}


@router.get("/admin/users")
async def admin_get_users() -> list:
    db = get_db()
    session = db.get_session()
    users = session.query(UserConfig).all()
    result = []
    for u in users:
        sub = db.get_subscription(u.chat_id)
        result.append(
            {
                "chat_id": u.chat_id,
                "onboarded": u.onboarded,
                "origins": u.origins,
                "destinations": u.destinations,
                "plan": sub.plan if sub else "trial",
                "status": sub.status if sub else "none",
                "api_used": sub.api_requests_month if sub else 0,
                "api_limit": sub.api_requests_limit if sub else 10,
            }
        )
    session.close()
    return result


@router.get("/admin/stats")
async def admin_get_stats() -> dict:
    db = get_db()
    return db.get_admin_stats()


@router.get("/admin/alerts")
async def admin_get_all_alerts(limit: int = 50) -> list:
    db = get_db()
    alerts = db.get_alerts(limit=limit)
    return [
        {
            "chat_id": a.chat_id,
            "type": a.alert_type,
            "route": a.route,
            "diff": a.difference,
            "time": a.sent_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/admin/disable-user/{chat_id}")
async def admin_disable_user(chat_id: str) -> dict:
    db = get_db()
    db.set_user_config(chat_id, active=0)
    return {"status": "disabled", "chat_id": chat_id}


@router.post("/admin/enable-user/{chat_id}")
async def admin_enable_user(chat_id: str) -> dict:
    db = get_db()
    db.set_user_config(chat_id, active=1)
    return {"status": "enabled", "chat_id": chat_id}


@router.get("/price-chart")
async def get_price_chart(route: str = "MDE:ADZ", chat_id: str = "") -> dict:
    try:
        db = get_db()
        records = db.get_price_history(chat_id, route, limit=50) if chat_id else []
        return {
            "route": route,
            "points": [{"price": r.price, "date": r.checked_at.isoformat(), "airline": r.airline} for r in records],
        }
    except Exception:
        return {"route": route, "points": []}


@router.get("/statistics")
async def get_statistics() -> dict:
    history = PriceHistory(PRICE_HISTORY_FILE)
    stats = get_stats_summary(history)
    try:
        db = get_db()
        stats["database"] = db.get_admin_stats()
        alerts = db.get_alerts(limit=5)
        stats["recent_alerts"] = [
            {"type": a.alert_type, "route": a.route, "diff": a.difference, "at": a.sent_at.isoformat()} for a in alerts
        ]
    except Exception:
        stats["database"] = {"error": "Database unavailable"}
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
    return stats


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "3.0.0"}
