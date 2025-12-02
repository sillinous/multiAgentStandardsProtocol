@echo off
echo ========================================
echo  APQC Agent Platform Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Install dependencies
echo Checking dependencies...
pip install fastapi uvicorn sqlalchemy pydantic python-multipart --quiet

REM Start the server
echo.
echo Starting server on port 8000...
echo.
echo Admin Panel:  http://localhost:8000/admin
echo Dashboard:    http://localhost:8000/dashboard
echo API Docs:     http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 --reload

pause
