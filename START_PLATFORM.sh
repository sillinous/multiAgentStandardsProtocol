#!/bin/bash
# ============================================================================
# APQC Agentic Platform - Linux/Mac Startup
# ============================================================================
#
# Run this script to start the platform:
#   chmod +x START_PLATFORM.sh
#   ./START_PLATFORM.sh
#
# Or just double-click if your system supports it!
#
# ============================================================================

echo "============================================================================"
echo "APQC AGENTIC PLATFORM"
echo "============================================================================"
echo ""
echo "Starting platform..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo ""
    echo "Please install Python 3.8 or later"
    echo ""
    exit 1
fi

# Install dependencies if needed
echo "Checking dependencies..."
python3 -m pip install --quiet fastapi uvicorn websockets pydantic

# Start the platform server
echo ""
echo "============================================================================"
echo "STARTING PLATFORM SERVER"
echo "============================================================================"
echo ""
echo "The platform will be available at: http://localhost:8080"
echo ""

# Open browser (try different commands for different systems)
sleep 2
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080 &
elif command -v open &> /dev/null; then
    open http://localhost:8080 &
fi

# Start server
python3 platform_server.py
