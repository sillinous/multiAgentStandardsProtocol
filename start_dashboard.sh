#!/bin/bash

# ============================================================================
# APQC Dashboard Quick Start Script
# ============================================================================
# This script starts both the backend and frontend servers for the
# APQC Real-Time Agent Monitoring Dashboard.
#
# Usage:
#   ./start_dashboard.sh
#
# Or with custom ports:
#   BACKEND_PORT=8765 FRONTEND_PORT=8080 ./start_dashboard.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=${BACKEND_PORT:-8765}
FRONTEND_PORT=${FRONTEND_PORT:-8080}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║  🎯 APQC Real-Time Agent Monitoring Dashboard              ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}📋 Checking requirements...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -r requirements-dashboard.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Create logs directory
mkdir -p logs
mkdir -p backups

echo ""
echo -e "${PURPLE}🚀 Starting APQC Dashboard...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}👋 Shutting down dashboard...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ Dashboard stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend Server
echo -e "${BLUE}🔧 Starting Backend Server (Port ${BACKEND_PORT})...${NC}"
cd "$PROJECT_DIR"
python3 dashboard_server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
    cat logs/backend.log
    exit 1
fi

# Verify backend is responding
if ! curl -s http://localhost:${BACKEND_PORT}/ > /dev/null; then
    echo -e "${RED}❌ Backend not responding. Check logs/backend.log${NC}"
    cat logs/backend.log
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Backend running (PID: ${BACKEND_PID})${NC}"

# Start Frontend Server
echo ""
echo -e "${BLUE}🌐 Starting Frontend Server (Port ${FRONTEND_PORT})...${NC}"
cd "$PROJECT_DIR/dashboard_frontend"
python3 -m http.server ${FRONTEND_PORT} > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 2

# Check if frontend is running
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}❌ Frontend failed to start. Check logs/frontend.log${NC}"
    cat ../logs/frontend.log
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Frontend running (PID: ${FRONTEND_PID})${NC}"

# Display status
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  ✅ APQC Dashboard is running!                             ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Dashboard:     ${NC}http://localhost:${FRONTEND_PORT}"
echo -e "${BLUE}🔌 Backend API:   ${NC}http://localhost:${BACKEND_PORT}"
echo -e "${BLUE}📡 WebSocket:     ${NC}ws://localhost:${BACKEND_PORT}/ws"
echo -e "${BLUE}📋 API Docs:      ${NC}http://localhost:${BACKEND_PORT}/docs"
echo ""
echo -e "${YELLOW}💡 Monitoring:${NC}"
echo -e "   • Backend Log:  ${BLUE}tail -f logs/backend.log${NC}"
echo -e "   • Frontend Log: ${BLUE}tail -f logs/frontend.log${NC}"
echo ""
echo -e "${PURPLE}Press Ctrl+C to stop the dashboard${NC}"
echo ""

# Keep script running
wait
