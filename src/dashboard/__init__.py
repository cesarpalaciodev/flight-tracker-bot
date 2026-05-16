import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from src.dashboard import routes, templates
from src.dashboard.auth import verify_token
from src.utils.config import API_KEY, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from src.utils.metrics import get_metrics_server

logger = logging.getLogger("dashboard")


def get_current_user(authorization: str = "") -> str:
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        chat_id = verify_token(token)
        if chat_id:
            return chat_id
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Dashboard v3.0 - Multi-User SaaS starting up...")
    try:
        metrics_server = get_metrics_server(port=9090)
        metrics_server.start()
    except Exception as e:
        logger.warning(f"Metrics server unavailable: {e}")
    yield


app = FastAPI(
    title="Flight Tracker Dashboard v3",
    description="Multi-user flight tracker SaaS",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
app.include_router(routes.router)


@app.get("/", response_class=HTMLResponse)
async def root() -> Response:
    return Response(
        content=templates.DASHBOARD_HTML,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "3.0.0"}
