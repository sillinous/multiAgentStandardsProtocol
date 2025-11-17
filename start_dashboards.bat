@echo off
REM ============================================================================
REM APQC Dashboard Startup Script for Windows
REM ============================================================================
REM Uses the intelligent Dashboard Agent to manage all services
REM ============================================================================

echo.
echo ============================================================================
echo   APQC Dashboard Startup - Powered by Dashboard Agent
echo ============================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

echo Running Dashboard Agent setup...
echo.

REM Run setup
python dashboard_agent.py setup
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Setup failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   Setup Complete! Starting services...
echo ============================================================================
echo.

REM Start services
python dashboard_agent.py start
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   Services Started Successfully!
echo ============================================================================
echo.
echo Access your dashboards at:
echo   Main Dashboard: http://localhost:8080/dashboard
echo   APQC Factory:   http://localhost:8765/apqc
echo.
echo To stop services, run: stop_dashboards.bat
echo Or use: python dashboard_agent.py stop
echo.
echo Press any key to open the main dashboard in your browser...
pause > nul

REM Open the main dashboard
start http://localhost:8080/dashboard

echo.
echo Browser opened! Enjoy your dashboards.
echo.
echo To view status: python dashboard_agent.py status
echo.
pause
