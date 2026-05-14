FROM python:3.12-slim

LABEL org.opencontainers.image.title="Flight Tracker"
LABEL org.opencontainers.image.description="Automated flight price tracker with Telegram alerts"
LABEL org.opencontainers.image.source="https://github.com/cesarpalaciodev/flight-tracker-bot"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/data && \
    chmod +x /app/install_service.sh 2>/dev/null || true

USER 1000

ENTRYPOINT ["python", "main_24_7.py"]