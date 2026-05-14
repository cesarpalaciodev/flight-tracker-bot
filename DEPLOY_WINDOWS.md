# Windows Service Deployment Guide

This guide explains how to deploy Flight Tracker as a Windows Service so it runs 24/7 in the background without requiring a logged-in user.

## Prerequisites

### 1. Install Python
Make sure Python is installed and added to your PATH.
- Download from: https://www.python.org/downloads/
- During installation, check **"Add Python to PATH"**

Verify Python is installed:
```cmd
python --version
```

### 2. Install nssm
nssm (Non-Sucking Service Manager) is required to run the bot as a Windows Service.

#### Option A: Using Chocolatey (Recommended)
```cmd
choco install nssm
```

#### Option B: Manual Installation
1. Download nssm from https://nssm.cc/download
2. Extract the ZIP file
3. Copy `nssm.exe` to a location in your PATH (e.g., `C:\Windows\System32`)

Verify nssm is installed:
```cmd
where nssm
```

### 3. Install Python Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```cmd
copy .env.example .env
```

Edit `.env` with your API keys (see README.md for setup instructions).

## Installation

### Option A: Using the Installation Script
Run `install_service.bat` as Administrator:
```cmd
right-click install_service.bat
select "Run as administrator"
```

### Option B: Manual Installation
1. Open Command Prompt as Administrator
2. Navigate to the project directory
3. Run:
```cmd
nssm install FlightTracker python "C:\path\to\main_24_7.py"
nssm set FlightTracker AppDirectory "C:\path\to\flight_tracker"
nssm set FlightTracker DisplayName "Flight Tracker 24/7"
nssm set FlightTracker Description "Flight price tracker running 24/7"
nssm set FlightTracker Start SERVICE_AUTO_START
```

## Managing the Service

### Using Service Manager
1. Press `Win + R`, type `services.msc`
2. Find **Flight Tracker 24/7** in the list
3. Right-click for Start/Stop/Restart options

### Using Command Line
Run `service_manager.bat` for an interactive menu, or use these commands:

```cmd
:: Start the service
nssm start FlightTracker

:: Stop the service
nssm stop FlightTracker

:: Restart the service
nssm restart FlightTracker

:: Check status
nssm status FlightTracker

:: View/edit configuration
nssm edit FlightTracker

:: Uninstall service
nssm stop FlightTracker
nssm remove FlightTracker confirm
```

## Automatic Startup

The service is configured to start automatically with Windows (SERVICE_AUTO_START). This means:
- The bot will start running immediately after Windows boots
- No user needs to be logged in
- It runs 24/7 as long as the PC is on

## Viewing Logs

Logs are stored in `logs/flight_tracker.log`. You can view them with:
```cmd
notepad logs\flight_tracker.log
```

Or monitor logs in real-time:
```cmd
powershell Get-Content logs\flight_tracker.log -Wait -Tail 50
```

## Troubleshooting

### Service won't start
1. Check if Python is in PATH: `where python`
2. Check logs: `nssm status FlightTracker`
3. Verify .env file exists and has valid API keys
4. Try running the script manually: `python main_24_7.py`

### Service starts but no alerts
1. Verify Telegram bot token and chat ID
2. Check logs for API errors
3. Ensure the Ignav API key is valid

### PC restarts but service doesn't start
1. Open `services.msc`
2. Find Flight Tracker 24/7
3. Right-click > Properties
4. Set "Startup type" to "Automatic"

## Updating the Bot

1. Stop the service: `nssm stop FlightTracker`
2. Pull latest changes from Git or copy new files
3. Start the service: `nssm start FlightTracker`

## Alternative: Task Scheduler

If you prefer not to use nssm, you can use Windows Task Scheduler:

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task
3. Set trigger (e.g., daily, or on startup)
4. Action: Start a program
5. Program: `python`
6. Arguments: `main.py` (or `main_24_7.py` for continuous checking)
7. Add condition: "Start only if on AC power" (optional)

Note: Task Scheduler will show a brief terminal window when running. For fully silent operation, use the Windows Service method.