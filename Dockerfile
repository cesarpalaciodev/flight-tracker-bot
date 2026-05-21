FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="Flight Tracker v3"
LABEL org.opencontainers.image.description="Multi-user flight price tracker SaaS"
LABEL org.opencontainers.image.source="https://github.com/cesarpalaciodev/flight-tracker-bot"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser && \
    mkdir -p /app/logs /app/data /app/exports && \
    chown -R appuser:appuser /app && \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl dumb-init && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

HEALTHCHECK --interval=30m --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "-u", "main_24_7.py"]