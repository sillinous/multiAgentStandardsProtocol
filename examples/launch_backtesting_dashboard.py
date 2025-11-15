"""
Launch Advanced Backtesting Dashboard

Starts the backtesting visualization server with beautiful charts and analytics.

Features:
- Interactive equity curves
- Drawdown visualization
- Performance metrics
- Trade-by-trade analysis
- Monthly returns
- Strategy comparison
- Mobile-responsive design
- Crypto + Stock support

Usage:
    python examples/launch_backtesting_dashboard.py

Then open: http://localhost:8001/backtest/dashboard
"""

import sys
from pathlib import Path
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.api.backtesting_api import create_backtesting_app


def main():
    """Launch the backtesting dashboard"""
    print("\n" + "=" * 80)
    print("  📊 LAUNCHING ADVANCED BACKTESTING DASHBOARD")
    print("=" * 80)

    print("\n🎨 Features:")
    print("   • Interactive equity curves with Chart.js")
    print("   • Real-time drawdown visualization")
    print("   • Comprehensive performance metrics")
    print("   • Trade-by-trade drill-down")
    print("   • Monthly returns analysis")
    print("   • Strategy comparison tools")
    print("   • Crypto + Stock support")
    print("   • Mobile-responsive design")

    print("\n🔗 Access Dashboard:")
    print("   Main Dashboard:  http://localhost:8001/backtest/dashboard")
    print("   API Docs:        http://localhost:8001/docs")
    print("   API Status:      http://localhost:8001/")

    print("\n💡 Supported Assets:")
    print("   Stocks: AAPL, MSFT, GOOGL, TSLA, NVDA, ...")
    print("   Crypto: BTC-USD, ETH-USD, BNB-USD, SOL-USD, ...")

    print("\n🎯 Available Strategies:")
    print("   • Balanced Trader")
    print("   • Conservative Value")
    print("   • Aggressive Growth")
    print("   • Sentiment Driven")
    print("   • Mean Reversion")

    print("\n📊 Visualizations:")
    print("   • Equity Curve (with fill)")
    print("   • Drawdown Chart")
    print("   • Monthly Returns Bar Chart")
    print("   • Performance Metrics Cards")
    print("   • Trade History Table")

    print("\n🚀 Starting server...")
    print("   Press CTRL+C to stop")
    print("=" * 80 + "\n")

    # Create app
    app = create_backtesting_app()

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Backtesting dashboard stopped. Thanks for using the Agentic Forge!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
