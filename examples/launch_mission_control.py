"""
Launch Mission Control Dashboard

The ultimate unified command center for the Agentic Forge platform.

Mission Control integrates:
- Multi-strategy portfolio management (3+ strategies running simultaneously)
- Real-time risk monitoring (Sharpe, VaR, drawdown, etc.)
- Live strategy comparison charts
- AI chat interface for natural language control
- Hot opportunities feed from sentiment + technical analysis
- Risk alerts and protections
- One-click strategy deployment

Access: http://localhost:8002/mission-control

Features:
1. **6-Panel Unified Interface**
   - Chat panel for conversational control
   - Multi-strategy portfolio with live P&L
   - Risk metrics dashboard
   - Strategy comparison charts
   - Hot opportunities feed
   - Risk alerts panel

2. **Multi-Strategy Management**
   - Run 3+ strategies simultaneously
   - Individual strategy tracking
   - Auto-allocation optimization
   - Live performance comparison

3. **Real-Time Risk Monitoring**
   - Sharpe & Sortino ratios
   - Value at Risk (VaR/CVaR)
   - Drawdown tracking
   - Position concentration
   - Volatility monitoring

4. **AI Chat Interface**
   - Natural language queries
   - Sentiment analysis on demand
   - Risk explanations
   - Portfolio summaries
   - Strategy deployment

5. **One-Click Deployment**
   - Deploy strategies from backtest
   - Automatic risk protections
   - Kelly Criterion position sizing
   - Real-time monitoring

6. **Cross-Platform**
   - Desktop optimized
   - Mobile responsive
   - Touch-friendly controls
   - Real-time WebSocket updates

Usage:
    python examples/launch_mission_control.py

Then open: http://localhost:8002/mission-control

API Endpoints:
    GET  /mission-control                    - Dashboard UI
    GET  /api/mission-control/portfolio      - Portfolio state
    GET  /api/mission-control/risk           - Risk metrics
    GET  /api/mission-control/opportunities  - Hot opportunities
    GET  /api/mission-control/alerts         - Risk alerts
    POST /api/mission-control/chat           - AI chat
    POST /api/mission-control/deploy-strategy - Deploy strategy
    WS   /api/mission-control/ws             - Real-time updates

Examples:

    # Get portfolio state
    curl http://localhost:8002/api/mission-control/portfolio

    # Chat with AI
    curl -X POST http://localhost:8002/api/mission-control/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "Show me BTC sentiment"}'

    # Deploy strategy
    curl -X POST http://localhost:8002/api/mission-control/deploy-strategy \
         -H "Content-Type: application/json" \
         -d '{"strategy_name": "balanced_trader", "allocation_pct": 25}'

Revolutionary Features:
- NASA-style mission control for AI trading
- Multiple strategies running in parallel
- Real-time risk monitoring with protections
- AI chat for natural language control
- One-click deployment from analysis to execution
- Cross-panel synchronization
- Mobile-first responsive design
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from superstandard.api.mission_control_api import create_mission_control_app
import uvicorn


def main():
    """Launch Mission Control"""

    print("=" * 80)
    print(" 🚀 MISSION CONTROL - LAUNCHING ")
    print("=" * 80)
    print()
    print("Unified Command Center for Agentic Forge")
    print()
    print("Features:")
    print("  ✅ Multi-Strategy Portfolio Management")
    print("  ✅ Real-Time Risk Monitoring")
    print("  ✅ Live Strategy Comparison")
    print("  ✅ AI Chat Interface")
    print("  ✅ Hot Opportunities Feed")
    print("  ✅ Risk Alerts & Protections")
    print("  ✅ One-Click Deployment")
    print()
    print("Access the dashboard at:")
    print("  🌐 http://localhost:8002/mission-control")
    print()
    print("API Documentation:")
    print("  📚 http://localhost:8002/docs")
    print()
    print("=" * 80)
    print()

    app = create_mission_control_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )


if __name__ == "__main__":
    main()
