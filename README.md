# Flight Tracker - Cheap Flight Finder to Santa Marta

![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://img.shields.io/github/actions/workflow/status/cesarpalaciodev/flight-tracker-bot/ci.yml?branch=main)
![Coverage](https://img.shields.io/codecov/c/github/cesarpalaciodev/flight-tracker-bot/main)
![Security](https://img.shields.io/github/actions/workflow/status/cesarpalaciodev/flight-tracker-bot/trivy-scan)
![Dependabot](https://img.shields.io/badge/dependabot-enabled-brightgreen?logo=dependabot)
![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)
![Prometheus](https://img.shields.io/badge/prometheus-metrics-orange?logo=prometheus)
![FastAPI](https://img.shields.io/badge/fastapi-web%20dashboard-green?logo=fastapi)
![Tests](https://img.shields.io/badge/tests-11%20files-blue)

Automated flight search from **Medellín (MDE)** and **Pereira (PEI)** to **Santa Marta (ADZ)**, with Telegram alerts when prices drop.

---

## Features

- Search flights from multiple origins (MDE, PEI)
- Round-trip search with configurable return dates
- Compare with historical prices
- Telegram alerts when prices drop
- Price history stored locally
- Rate limiting protection
- Prometheus metrics
- **Web dashboard with real-time monitoring**
- Complete operation logging
- Runs 24/7 as a Windows Service or Docker container

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your credentials.

### 3. Run Once

```bash
python main.py
```

---

## Installation

### Windows Service (Recommended)

See [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md) for detailed instructions.

```cmd
choco install nssm
right-click install_service.bat -> Run as administrator
```

### Docker

```bash
# Run bot only
docker compose up -d

# Run bot + dashboard
docker compose --profile dashboard up -d

# Run with monitoring
docker compose --profile monitoring up -d
```

---

## Configuration

### 1. Get Ignav API Key

1. Go to [ignav.com](https://ignav.com)
2. Register for free (1,000 monthly requests free)
3. Copy your API key from the dashboard

### 2. Set Up Telegram Bot

1. Search for **@BotFather** on Telegram
2. Send `/newbot` to create a new bot
3. Copy the **Bot Token**
4. Get your **Chat ID** by messaging **@userinfobot**

### 3. Edit .env

```env
IGNAV_API_KEY=your_ignav_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/cesarpalaciodev/flight-tracker-bot.git
cd flight-tracker-bot

# Install dependencies with dev tools
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/
```

### Project Structure

```
flight_tracker/
├── main.py                 # Run-once entry point
├── main_24_7.py           # Continuous 24/7 runner
├── main_dashboard.py      # FastAPI dashboard entry point
├── pyproject.toml         # Project configuration
├── .env.example           # Template for .env
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker Compose setup
├── prometheus.yml         # Prometheus config
├── install_service.bat    # Windows Service installer
├── service_manager.bat    # Service management menu
├── DEPLOY_WINDOWS.md      # Windows deployment guide
├── tests/                 # Unit tests
│   ├── conftest.py        # Test fixtures
│   ├── test_flight.py
│   ├── test_ignav_api.py
│   ├── test_price_history.py
│   ├── test_rate_limiter.py
│   ├── test_telegram.py
│   ├── test_config.py     # Config validation tests
│   ├── test_security.py   # Security filter tests
│   └── test_integration.py # Integration tests
└── src/
    ├── models/
    │   ├── flight.py
    │   └── price_history.py
    ├── services/
    │   ├── email.py
    │   ├── ignav_api.py
    │   └── telegram.py
    ├── dashboard/
    │   ├── __init__.py    # FastAPI app
    │   ├── routes.py      # API routes
    │   └── templates.py   # Dashboard HTML
    └── utils/
        ├── config.py       # Pydantic-validated config
        ├── metrics.py      # Prometheus metrics
        ├── rate_limiter.py # API rate limiting
        └── security.py     # Log sanitization filters
```

---

## Configuration Options

All configuration is managed through the `AppConfig` pydantic model in `src/utils/config.py`:

| Variable | Description | Default |
|----------|-------------|---------|
| `destination` | Airport code | `ADZ` |
| `origins` | Origin airports | `["MDE", "PEI"]` |
| `price_drop_threshold` | Minimum drop to alert (COP) | `1.0` |
| `check_interval_hours` | Hours between checks | `8` |
| `adults` | Number of passengers | `2` |
| `return_days` | Days for return trip | `5` |
| `days_ahead_start` | Days ahead to start search | `68` |
| `days_ahead_end` | Days ahead to end search | `131` |
| `days_interval` | Days between search dates | `14` |

---

## Alert Format

```
🔽 PRECIO BAJO

✈️ MDE → ADZ
💰 $200,000 → $150,000
📉 Ahorro: $50,000

🏷️ Avianca
📅 Ida: 2026-06-15
📅 Vuelta: 2026-06-20

🔗 Reservar
```

---

## Metrics

Prometheus metrics available at `http://localhost:9090`:

- `flight_tracker_flights_searched_total`
- `flight_tracker_price_checks_total`
- `flight_tracker_price_alerts_sent_total`
- `flight_tracker_current_price_cop`
- `flight_tracker_api_requests_total`
- `flight_tracker_rate_limit_hits_total`

---

## Web Dashboard

A real-time web dashboard is available to monitor flight prices, metrics, and price history.

### Run Dashboard

```bash
# Install dependencies
pip install -e ".[dashboard]"

# Start dashboard
python main_dashboard.py
# or
uvicorn src.dashboard:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000` in your browser.

### Dashboard Features

- **Real-time metrics**: Flights searched, price checks, alerts sent
- **Current prices**: Live view of tracked routes
- **Price comparison**: Ranked comparison of all routes
- **Simulate checks**: Test price drop alerts with simulated data
- **Auto-refresh**: Updates every 30 seconds

### Dashboard API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/health` | GET | Health check |
| `/api/metrics` | GET | All Prometheus metrics |
| `/api/prices` | GET | Current prices |
| `/api/price-history/{route}` | GET | Historical data for a route |
| `/api/price-comparison` | GET | Ranked route comparison |
| `/api/statistics` | GET | Overall statistics |
| `/api/simulate-check` | POST | Simulate a price check |

---

## Security

### Secrets Management

All credentials are loaded from `.env` which is excluded from Git. Never commit credentials.

### Log Sanitization

Sensitive data is automatically redacted from logs:
- API keys (`ignav_*`)
- Telegram tokens (`digit:dashed`)
- Chat IDs
- Authorization headers
- Passwords

### Docker Security

- Runs as non-root user (`appuser`)
- Uses `dumb-init` to handle signals properly
- Minimal image (`bookworm-slim`)
- CA certificates included
- Health checks enabled

### CI/CD Security Scans

Every push runs:
- **GitLeaks**: Secret detection in code
- **Bandit**: Python security patterns
- **Safety**: Dependency vulnerability check
- **Trivy**: Container vulnerability scan
- **Dependabot**: Automatic dependency updates

### Rate Limiting

The API client includes built-in rate limiting:
- Max 10 requests per minute
- Max 100 requests per hour
- Automatic backoff on rate limit detection

---

## License

MIT License - Free to use and modify.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest tests/`
5. Run linting: `uv run ruff check .`
6. Run security scan: `uv run bandit -r src/`
7. Submit a pull request