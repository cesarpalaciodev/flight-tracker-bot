@echo off
setlocal

echo ============================================
echo Flight Tracker - Service Management
echo ============================================
echo.

set SERVICE_NAME=FlightTracker

:menu
cls
echo ============================================
echo Flight Tracker Service Manager
echo ============================================
echo.
echo 1. Start service
echo 2. Stop service
echo 3. Restart service
echo 4. View service status
echo 5. Uninstall service
echo 6. Open service configuration
echo 7. View logs
echo 8. Exit
echo.
set /p choice="Select an option (1-8): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto status
if "%choice%"=="5" goto uninstall
if "%choice%"=="6" goto config
if "%choice%"=="7" goto logs
if "%choice%"=="8" goto end

echo.
echo [ERROR] Invalid option
timeout /t 2 >nul
goto menu

:start
echo.
nssm start "%SERVICE_NAME%"
if %errorlevel%==0 (
    echo [OK] Service started successfully
) else (
    echo [ERROR] Could not start service
)
timeout /t 2 >nul
goto menu

:stop
echo.
nssm stop "%SERVICE_NAME%"
if %errorlevel%==0 (
    echo [OK] Service stopped successfully
) else (
    echo [ERROR] Could not stop service
)
timeout /t 2 >nul
goto menu

:restart
echo.
nssm restart "%SERVICE_NAME%"
if %errorlevel%==0 (
    echo [OK] Service restarted successfully
) else (
    echo [ERROR] Could not restart service
)
timeout /t 2 >nul
goto menu

:status
echo.
nssm status "%SERVICE_NAME%"
sc query %SERVICE_NAME%
timeout /t 4 >nul
goto menu

:uninstall
echo.
set /p confirm="Are you sure you want to uninstall the service? (Y/N): "
if /i "%confirm%"=="Y" (
    nssm stop "%SERVICE_NAME%" 2>nul
    nssm remove "%SERVICE_NAME%" confirm
    echo [OK] Service uninstalled
) else (
    echo Cancelled
)
timeout /t 2 >nul
goto menu

:config
echo.
nssm edit "%SERVICE_NAME%"
goto menu

:logs
echo.
echo Opening logs...
if exist "logs\flight_tracker.log" (
    start "" "logs\flight_tracker.log"
) else (
    echo [INFO] No logs found yet
)
timeout /t 2 >nul
goto menu

:end
exit