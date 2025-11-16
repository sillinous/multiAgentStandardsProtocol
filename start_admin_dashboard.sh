#!/bin/bash

# APQC Dashboard with Admin Panel - Quick Start Script
# =====================================================

echo "🚀 Starting APQC Dashboard with Admin Panel..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r admin_requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        # Create basic .env
        cat > .env << EOF
# APQC Dashboard Configuration
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30
ENABLE_METRICS=true
ENABLE_AUDIT_LOG=true
DATA_RETENTION_DAYS=90
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=24
EOF
    fi
fi

# Start the dashboard
echo ""
echo "✅ Setup complete!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🎯 APQC Dashboard with Admin Panel"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  📊 Dashboard:    http://localhost:8765"
echo "  🔧 Admin Panel:  Click 'Admin Panel' button in dashboard"
echo ""
echo "  🔑 Default Admin Credentials:"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "  ⚠️  IMPORTANT: Change the default password immediately!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Start server
python dashboard_server.py
