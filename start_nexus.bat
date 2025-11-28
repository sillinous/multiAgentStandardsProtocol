@echo off
echo.
echo ========================================
echo NEXUS TRADING PLATFORM
echo ========================================
echo.
echo Stopping any existing servers...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting NEXUS Trading Platform Server...
echo.
cd /d "%~dp0"

python -m uvicorn src.superstandard.api.server:app --host 0.0.0.0 --port 8080 --reload

pause
