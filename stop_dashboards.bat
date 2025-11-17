@echo off
REM ============================================================================
REM APQC Dashboard Stop Script for Windows
REM ============================================================================
REM This script will stop all running dashboard servers
REM ============================================================================

echo.
echo ============================================================================
echo   APQC Dashboard Stop Script
echo ============================================================================
echo.

echo Stopping all Python server processes...
echo.

REM Kill uvicorn processes (Main Dashboard Server)
taskkill /F /FI "WINDOWTITLE eq Main Dashboard Server*" 2>nul
if %errorlevel% equ 0 (
    echo - Main Dashboard Server stopped
) else (
    echo - Main Dashboard Server was not running
)

REM Kill APQC Factory processes
taskkill /F /FI "WINDOWTITLE eq APQC Factory Server*" 2>nul
if %errorlevel% equ 0 (
    echo - APQC Factory Server stopped
) else (
    echo - APQC Factory Server was not running
)

REM Also kill by process name as backup
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Dashboard*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Factory*" 2>nul

echo.
echo ============================================================================
echo   All dashboard servers have been stopped!
echo ============================================================================
echo.
pause
