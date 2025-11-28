@echo off
REM ============================================================================
REM APQC Agentic Platform - Windows Startup
REM ============================================================================
REM
REM Double-click this file to start the platform!
REM
REM ============================================================================

echo ============================================================================
echo APQC AGENTIC PLATFORM
echo ============================================================================
echo.
echo Starting platform...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.8 or later from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
python -m pip install --quiet fastapi uvicorn websockets pydantic

REM Start the platform server
echo.
echo ============================================================================
echo STARTING PLATFORM SERVER
echo ============================================================================
echo.
echo The platform will open in your web browser automatically...
echo.

REM Start server and open browser
start http://localhost:8080
python platform_server.py

pause
