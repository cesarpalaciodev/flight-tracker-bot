@echo off
setlocal

echo ============================================
echo Flight Tracker 24/7 - Windows Service Setup
echo ============================================
echo.

set SERVICE_NAME=FlightTracker
set APP_NAME=FlightTracker
set EXE_PATH=%~dp0main_24_7.py
set PYTHON=python
set SCRIPT_DIR=%~dp0

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] nssm not found in PATH.
    echo [INFO] Please install nssm first:
    echo   - Download from: https://nssm.cc/download
    echo   - Or run: choco install nssm   ^(if you have Chocolatey^)
    echo   - Then add nssm to your PATH or run this script from nssm directory
    echo.
    pause
    exit /b 1
)

echo [INFO] Installing FlightTracker service...
nssm install "%SERVICE_NAME%" "%PYTHON%" "%EXE_PATH%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install service
    pause
    exit /b 1
)

nssm set "%SERVICE_NAME%" AppDirectory "%SCRIPT_DIR%"
nssm set "%SERVICE_NAME%" DisplayName "Flight Tracker 24/7"
nssm set "%SERVICE_NAME%" Description "Flight price tracker running 24/7 - searches cheapest flights and sends alerts via Telegram"
nssm set "%SERVICE_NAME%" Start SERVICE_AUTO_START

echo.
echo [SUCCESS] Service installed!
echo.
echo To start the service:
echo   nssm start %SERVICE_NAME%
echo.
echo Other commands:
echo   nssm stop %SERVICE_NAME%     - Stop the service
echo   nssm restart %SERVICE_NAME% - Restart the service
echo   nssm remove %SERVICE_NAME%  - Uninstall the service
echo   nssm edit %SERVICE_NAME%    - Configure service settings
echo.
echo To start automatically on Windows boot, the service is already configured
echo with SERVICE_AUTO_START.
echo.
pause