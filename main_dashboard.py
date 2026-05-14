from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from src.dashboard import app
from src.utils.metrics import get_metrics_server


logger = logging.getLogger("main_dashboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Flight Tracker Dashboard...")
    metrics_server = get_metrics_server(port=9090)
    metrics_server.start()
    yield
    logger.info("Shutting down...")


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )