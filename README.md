# Flight Tracker - Cheap Flight Finder to Santa Marta

Automated flight search from **Medellín (MDE)** and **Pereira (PEI)** to **Santa Marta (ADZ)**, with Telegram alerts when prices drop.

---

## Features

- Search flights from multiple origins (MDE, PEI)
- Round-trip search with configurable return dates
- Compare with historical prices
- Telegram alerts when prices drop
- Price history stored locally
- Complete operation logging
- Runs 24/7 as a Windows Service

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Edit `.env` with your credentials (see Configuration section below).

### 3. Run Once

```bash
python main.py
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

## Deployment (24/7)

The bot can run as a **Windows Service** to search flights continuously without requiring a terminal or logged-in user.

See [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md) for detailed deployment instructions.

### Quick Deployment

1. **Install nssm** (Non-Sucking Service Manager):
   ```cmd
   choco install nssm
   ```
   Or download from https://nssm.cc/download

2. **Run the installer as Administrator**:
   ```cmd
   right-click install_service.bat
   select "Run as administrator"
   ```

3. **The service will start automatically** with Windows and run 24/7 in the background.

### Managing the Service

- **Start/Stop/Restart**: Run `service_manager.bat` or use `services.msc`
- **View logs**: `logs/flight_tracker.log`
- **Uninstall**: Run `service_manager.bat` and select option 5

---

## Project Structure

```
flight_tracker/
├── main.py                 # Run-once entry point
├── main_24_7.py           # Continuous 24/7 runner
├── .env                   # Environment variables (not committed)
├── .env.example           # Template for .env
├── requirements.txt       # Python dependencies
├── install_service.bat    # Windows Service installer
├── service_manager.bat    # Service management menu
├── DEPLOY_WINDOWS.md      # Deployment guide
├── src/
│   ├── models/
│   │   ├── flight.py      # Flight data model
│   │   └── price_history.py # Price history tracker
│   ├── services/
│   │   ├── ignav_api.py   # Ignav API integration
│   │   └── telegram.py    # Telegram bot
│   └── utils/
│       └── config.py      # Configuration
├── data/                  # Price history data
└── logs/                  # Application logs
```

---

## Advanced Configuration

### Price Drop Threshold

By default, alerts are sent when price drops by any amount. To change:

Edit `src/utils/config.py`:
```python
PRICE_DROP_THRESHOLD = 50000  # Change this value (COP)
```

### Search Origins

Edit `src/utils/config.py`:
```python
ORIGINS = ["MDE", "PEI"]  # Add more airport codes
```

### Search Intervals

Edit `main_24_7.py`:
```python
CHECK_INTERVAL_HOURS = 8  # How often to search (hours)
```

### Departure Dates Range

Edit `main_24_7.py`:
```python
departure_dates = get_departure_dates(68, 131, 14)
# From 68 days ahead to 131 days ahead, every 14 days
```

---

## Alert Format

When a price drops, you'll receive a Telegram message like:

```
 Best Price Drop!

 MDE → ADZ
 $500,000 → $350,000
 Savings: $150,000

 Avianca
 2026-05-23 (round trip)

 [BOOK NOW](link)
```

---

## Troubleshooting

### "API key not configured"

Edit the `.env` file and add your Ignav API key.

### "No flights found"

- Verify the search dates are valid
- Some routes may not have available flights

### "Telegram messages not arriving"

- Verify the Bot Token is correct
- Verify the Chat ID is correct
- Make sure you've started the bot (`/start`)

### Service won't start

1. Check if Python is in PATH: `where python`
2. Check logs: `nssm status FlightTracker`
3. Verify `.env` file exists with valid credentials
4. Try running manually: `python main_24_7.py`

---

## Tech Stack

- **Python 3.8+**
- **requests** - HTTP client
- **python-dotenv** - Environment variables
- **nssm** - Windows Service Manager
- **Telegram Bot API** - Alerts

---

## License

MIT License - Free to use and modify.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request