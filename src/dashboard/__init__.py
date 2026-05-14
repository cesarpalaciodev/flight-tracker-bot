from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from src.utils.config import API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from src.utils.metrics import (
    FLIGHTS_SEARCHED,
    PRICE_CHECKS,
    PRICE_ALERTS_SENT,
    CURRENT_PRICES,
    API_REQUESTS,
    RATE_LIMIT_HITS,
    get_metrics_server,
)
from src.dashboard import routes, templates


logger = logging.getLogger("dashboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Dashboard starting up...")
    metrics_server = get_metrics_server()
    metrics_server.start()
    yield
    logger.info("Dashboard shutting down...")


app = FastAPI(
    title="Flight Tracker Dashboard",
    description="Real-time flight price monitoring dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return templates.DASHBOARD_HTML


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/status")
async def get_status() -> dict:
    return {
        "api_key_configured": bool(API_KEY),
        "telegram_configured": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID),
        "features": {
            "price_tracking": True,
            "telegram_alerts": bool(TELEGRAM_TOKEN),
            "metrics": True,
            "price_history": True
        }
    }