@echo off
REM ============================================================================
REM APQC Dashboard Startup Script for Windows
REM ============================================================================
REM This script will:
REM 1. Sync your local repo with GitHub
REM 2. Install required Python packages
REM 3. Initialize the APQC database (613 agents)
REM 4. Start both dashboard servers
REM ============================================================================

echo.
echo ============================================================================
echo   APQC Dashboard Startup Script
echo ============================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

echo [1/5] Syncing with GitHub...
echo ----------------------------------------------------------------------------
git fetch origin
if %errorlevel% neq 0 (
    echo ERROR: Failed to fetch from GitHub. Check your internet connection.
    pause
    exit /b 1
)

git reset --hard origin/main
if %errorlevel% neq 0 (
    echo ERROR: Failed to reset to main branch.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Local repo synced with GitHub!
echo.

echo [2/5] Installing Python dependencies...
echo ----------------------------------------------------------------------------
pip install fastapi uvicorn jinja2 pydantic python-multipart
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies. Is Python installed?
    pause
    exit /b 1
)

echo.
echo SUCCESS: Dependencies installed!
echo.

echo [3/5] Initializing APQC database...
echo ----------------------------------------------------------------------------
python apqc_agent_factory.py --init
if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize database.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Database initialized with 613 agents!
echo.

echo [4/5] Starting Main Dashboard Server (Port 8080)...
echo ----------------------------------------------------------------------------
echo Opening new window for Main Dashboard Server...
start "Main Dashboard Server (Port 8080)" cmd /k "python -m uvicorn src.superstandard.api.server:app --host 0.0.0.0 --port 8080"

REM Wait a few seconds for the first server to start
timeout /t 3 /nobreak > nul

echo.
echo [5/5] Starting APQC Factory Server (Port 8765)...
echo ----------------------------------------------------------------------------
echo Opening new window for APQC Factory Server...
start "APQC Factory Server (Port 8765)" cmd /k "python apqc_factory_server.py"

REM Wait a few seconds for the second server to start
timeout /t 3 /nobreak > nul

echo.
echo ============================================================================
echo   SERVERS STARTED SUCCESSFULLY!
echo ============================================================================
echo.
echo Main Dashboard Server:     http://localhost:8080/dashboard
echo APQC Factory Server:        http://localhost:8765/apqc
echo.
echo Available Dashboards:
echo   - Main Hub:               http://localhost:8080/dashboard
echo   - Admin Dashboard:        http://localhost:8080/dashboard/admin
echo   - User Control Panel:     http://localhost:8080/dashboard/user
echo   - Network Visualization:  http://localhost:8080/dashboard/network
echo   - Coordination Dashboard: http://localhost:8080/dashboard/coordination
echo   - Consciousness Monitor:  http://localhost:8080/dashboard/consciousness
echo   - APQC Hierarchy:         http://localhost:8765/apqc
echo   - API Documentation:      http://localhost:8765/docs
echo.
echo Two new command windows have been opened for the servers.
echo DO NOT CLOSE those windows - they are running the servers!
echo.
echo Press any key to open the main dashboard in your browser...
pause > nul

REM Open the main dashboard in default browser
start http://localhost:8080/dashboard

echo.
echo Browser opened! You can now access all dashboards.
echo.
echo To STOP the servers:
echo   - Close the two server command windows
echo   - Or run: stop_dashboards.bat
echo.
echo ============================================================================
echo.
pause
