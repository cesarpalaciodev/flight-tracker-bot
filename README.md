# Flight Tracker v2.0

![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FastAPI](https://img.shields.io/badge/dashboard-FastAPI-green)
![Docker](https://img.shields.io/badge/docker-multi--stage-blue)
![DB](https://img.shields.io/badge/database-SQLAlchemy-orange)
![Redis](https://img.shields.io/badge/cache-Redis-red)
![Tests](https://img.shields.io/badge/tests-pytest-yellow)
![Security](https://img.shields.io/badge/security-bandit-black)

Automated flight price tracker with multi-destination support, Telegram alerts, Web Dashboard, Redis cache, and SQLAlchemy database.

---

## Features

- **Multi-destination** — Track any route, customizable origins and destinations
- **Telegram alerts** — Price drops and price increases detected
- **Telegram commands** — `/help`, `/config`, `/set_origins`, `/set_destinations`, `/set_adults`, `/set_days`, `/set_threshold`, `/price`, `/stats`
- **Web Dashboard** — Real-time metrics, price comparison, statistics, CSV export, chart visualization
- **Database** — SQLAlchemy (SQLite/PostgreSQL), price history, alert log, user configuration
- **Redis cache** — Fast API response caching with local fallback
- **Rate limiting** — Built-in API protection (10 req/min, 100 req/hour)
- **Prometheus metrics** — Flights searched, alerts sent, API requests, rate limit hits
- **Log sanitization** — API keys, tokens, passwords automatically redacted
- **CSV export** — One-click price history download from dashboard
- **Docker** — Multi-stage build, non-root user, health checks
- **Grafana** — Pre-built dashboard template for metrics visualization

---

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
```

Fill in your credentials (see Configuration section).

### 3. Run

```bash
# One-time check
python main.py

# 24/7 continuous
python main_24_7.py

# Web dashboard
python main_dashboard.py
# or: uvicorn src.dashboard:app --host 0.0.0.0 --port 8000
```

---

## Configuration

### .env

```env
IGNAV_API_KEY=ignav_your_api_key
TELEGRAM_TOKEN=123456:ABC-DEF1234
TELEGRAM_CHAT_ID=123456789
DATABASE_URL=sqlite:///data/flight_tracker.db
REDIS_URL=                      # Optional: redis://localhost:6379
DASHBOARD_TOKEN=                # Optional: auth for dashboard
```

### Getting Credentials

| Service | How to get |
|---------|------------|
| **Ignav API** | Register at [ignav.com](https://ignav.com) (free: 1000 req/month) |
| **Telegram Bot** | Message @BotFather, create bot, copy token |
| **Chat ID** | Message @userinfobot, get your numeric ID |

---

## Deployment

### Docker

```bash
# Bot only
docker compose up -d

# Bot + Dashboard
docker compose --profile dashboard up -d

# Bot + Prometheus monitoring
docker compose --profile monitoring up -d
```

### Cloud

The project includes deployment configs for:

- **Railway** — `railway.json`
- **Render** — `render.yaml`

### Windows Service

```cmd
choco install nssm
install_service.bat
```

---

## Web Dashboard

Access at `http://localhost:8000`

### Tabs

| Tab | Features |
|-----|----------|
| **Routes** | Live prices, simulate checks, price comparison table, CSV export |
| **Statistics** | Price stats (low/high/avg), flights searched, alerts sent, metric counters |
| **Alerts** | Recent price drop/increase alert history from database |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Dashboard UI |
| GET | `/api/metrics` | Prometheus metrics |
| GET | `/api/prices` | Current prices for all routes |
| GET | `/api/price-comparison` | Ranked route comparison |
| GET | `/api/statistics` | Full statistics + alert history |
| GET | `/api/export/csv` | Download price history as CSV |
| POST | `/api/simulate-check` | Test price drop simulations |
| GET | `/api/config` | Current bot configuration |
| GET | `/api/routes` | All tracked routes |

---

## Telegram Commands

Send these to your bot:

| Command | Description |
|---------|-------------|
| `/start` | Activate bot |
| `/help` | Show all commands |
| `/config` | Show current configuration |
| `/set_origins MDE,PEI,BOG` | Change origin airports |
| `/set_destinations ADZ,CTG` | Change destination airports |
| `/set_adults 2` | Change passenger count |
| `/set_days 5` | Change trip duration (days) |
| `/set_threshold 50000` | Set price alert threshold (COP) |
| `/price` | Show latest prices |
| `/stats` | Show statistics |

---

## Database

Uses SQLAlchemy ORM with the following models:

| Model | Table | Description |
|-------|-------|-------------|
| `PriceRecord` | `price_history` | Every price check result |
| `AlertLog` | `alert_log` | Every sent price alert |
| `UserConfig` | `user_config` | Per-user Telegram settings |

Supported backends: **SQLite** (default), **PostgreSQL** (via `DATABASE_URL` env).

### Viewing Data

```bash
# SQLite (default)
pip install sqlite3-web
python -m sqlite3_web data/flight_tracker.db
```

Or use [DB Browser for SQLite](https://sqlitebrowser.org).

---

## Cache

Redis cache with automatic local fallback. Configure via `REDIS_URL` env variable. Stores:

- Flight search results (1h TTL)
- Booking links (2h TTL)

---

## Project Structure

```
flight_tracker/
├── main.py                   # One-time check
├── main_24_7.py              # 24/7 continuous runner
├── main_dashboard.py         # Web dashboard entry
├── start_dashboard.bat       # Windows dashboard launcher
├── Dockerfile                # Multi-stage build
├── docker-compose.yml        # Compose with dashboard + monitoring profiles
├── .env.example              # Config template
├── pyproject.toml            # Python project config
├── requirements.txt          # Dependencies
├── railway.json              # Railway deploy config
├── render.yaml               # Render deploy config
├── prometheus.yml            # Metrics scraper config
├── grafana_dashboard.json    # Grafana dashboard template
├── install_service.bat       # Windows service installer
├── service_manager.bat       # Service management menu
├── DEPLOY_WINDOWS.md         # Windows deployment guide
├── tests/                    # Unit tests
│   ├── conftest.py
│   ├── test_flight.py
│   ├── test_ignav_api.py
│   ├── test_price_history.py
│   ├── test_rate_limiter.py
│   ├── test_telegram.py
│   ├── test_config.py
│   ├── test_security.py
│   └── test_integration.py
└── src/
    ├── models/
    │   ├── flight.py          # Flight data model
    │   ├── price_history.py   # JSON price storage
    │   └── database.py        # SQLAlchemy models + DB operations
    ├── services/
    │   ├── ignav_api.py       # API client with rate limiting + caching
    │   ├── telegram.py        # Bot with command parsing + multi-user
    │   ├── export.py          # CSV export + statistics
    │   └── email.py           # Email alert service
    ├── dashboard/
    │   ├── __init__.py        # FastAPI app
    │   ├── routes.py          # All API endpoints
    │   └── templates.py       # Dashboard HTML (dark mode, Chart.js)
    └── utils/
        ├── config.py          # Pydantic-validated configuration
        ├── metrics.py         # Prometheus metrics
        ├── rate_limiter.py    # API rate limiting
        ├── security.py        # Log sanitization filters
        ├── cache.py           # Redis + local cache
        └── exceptions.py      # Typed exception hierarchy
```

---

## Security

- **Credentials** — `.env` excluded via `.gitignore`, never committed
- **Log sanitization** — API keys, tokens, passwords redacted from all logs
- **Rate limiting** — Max 10 requests/minute, 100 requests/hour
- **Docker** — Non-root user, `dumb-init`, minimal image, health checks
- **CI/CD** — GitLeaks (secret detection), Bandit (Python security), Safety (dependency CVEs), Trivy (container vulns), Dependabot

---

## License

MIT

---

## Contributing

```bash
git clone https://github.com/cesarpalaciodev/flight-tracker-bot.git
cd flight-tracker-bot
pip install -r requirements.txt
pytest tests/
```

Pull requests welcome.