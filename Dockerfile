# Stage 1: Build dependencies
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir --prefix=/install uv && \
    uv pip install --prefix=/install --no-cache-dir \
        -r requirements.txt \
        fastapi uvicorn prometheus-client \
        sqlalchemy redis stripe pyjwt cryptography

# Stage 2: Runtime image
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="Flight Tracker v3"
LABEL org.opencontainers.image.description="Multi-user flight price tracker SaaS with Telegram bot, Dashboard, and payments"
LABEL org.opencontainers.image.source="https://github.com/cesarpalaciodev/flight-tracker-bot"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONFAULTHANDLER=1

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser && \
    mkdir -p /app/logs /app/data /app/exports && \
    chown -R appuser:appuser /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl dumb-init \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . /app

WORKDIR /app
USER appuser

HEALTHCHECK --interval=30m --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "-u", "main_24_7.py"]