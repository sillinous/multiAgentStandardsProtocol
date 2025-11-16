@echo off
REM ============================================================================
REM APQC Dashboard Quick Start Script (Windows)
REM ============================================================================
REM This script starts both the backend and frontend servers for the
REM APQC Real-Time Agent Monitoring Dashboard.
REM
REM Usage:
REM   start_dashboard.bat
REM ============================================================================

echo ================================================================
echo.
echo   APQC Real-Time Agent Monitoring Dashboard
echo.
echo ================================================================
echo.

REM Configuration
set BACKEND_PORT=8765
set FRONTEND_PORT=8080

REM Check Python
echo Checking requirements...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo Python found

REM Install dependencies
echo Installing dependencies...
pip install -r requirements-dashboard.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create directories
if not exist logs mkdir logs
if not exist backups mkdir backups

echo.
echo Starting APQC Dashboard...
echo.

REM Start Backend
echo Starting Backend Server (Port %BACKEND_PORT%)...
start "APQC Dashboard Backend" /MIN python dashboard_server.py

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend
echo Starting Frontend Server (Port %FRONTEND_PORT%)...
cd dashboard_frontend
start "APQC Dashboard Frontend" /MIN python -m http.server %FRONTEND_PORT%
cd ..

REM Wait for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ================================================================
echo.
echo   APQC Dashboard is running!
echo.
echo ================================================================
echo.
echo   Dashboard:     http://localhost:%FRONTEND_PORT%
echo   Backend API:   http://localhost:%BACKEND_PORT%
echo   WebSocket:     ws://localhost:%BACKEND_PORT%/ws
echo   API Docs:      http://localhost:%BACKEND_PORT%/docs
echo.
echo   Press Ctrl+C to stop the dashboard
echo.
echo ================================================================
echo.

REM Open browser
start http://localhost:%FRONTEND_PORT%

echo Dashboard opened in browser
echo.
pause
