from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from src.utils.config import API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from src.utils.metrics import get_metrics_server
from src.dashboard import routes, templates


logger = logging.getLogger("dashboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Dashboard v2.0 starting up...")
    try:
        metrics_server = get_metrics_server()
        metrics_server.start()
    except Exception as e:
        logger.warning(f"Metrics server unavailable: {e}")
    yield
    logger.info("Dashboard shutting down...")


app = FastAPI(
    title="Flight Tracker Dashboard v2",
    description="Multi-destination flight price tracker with Telegram alerts and Dashboard",
    version="2.0.0",
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
        "version": "2.0.0"
    }