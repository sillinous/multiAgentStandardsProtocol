@echo off
REM ============================================================================
REM APQC Dashboard Stop Script for Windows
REM ============================================================================
REM Uses the intelligent Dashboard Agent to stop all services
REM ============================================================================

echo.
echo ============================================================================
echo   APQC Dashboard Stop Script
echo ============================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

echo Stopping all dashboard services...
echo.

REM Use the agent to stop services
python dashboard_agent.py stop

echo.
echo ============================================================================
echo   All Services Stopped
echo ============================================================================
echo.
pause
