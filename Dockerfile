FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="Flight Tracker"
LABEL org.opencontainers.image.description="Automated flight price tracker with Telegram alerts"
LABEL org.opencontainers.image.source="https://github.com/cesarpalaciodev/flight-tracker-bot"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.maintainer="cesarpalaciodev"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONFAULTHANDLER=1
ENV PIP_ROOT_USER_ACTION=prevent_credential_confirmation

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser && \
    mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-recommends \
        ca-certificates \
        curl \
        dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip install --no-cache-dir --user --break-system-packages -r requirements.txt && \
    rm -f /root/.local/bin/python* /root/.local/bin/pip*

COPY --chown=appuser:appuser . .

USER appuser

HEALTHCHECK --interval=30m --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["dumb-init", "--", "python", "-u", "main_24_7.py"]