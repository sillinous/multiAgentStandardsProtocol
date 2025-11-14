"""
Launch Conversational Trading Dashboard

Starts the FastAPI server with the beautiful conversational trading dashboard.

This demonstrates the COMPLETE platform with:
- Real-time conversational interface
- Live portfolio tracking
- Multi-source sentiment analysis
- Explainable AI decisions
- WebSocket real-time updates

Usage:
    python examples/launch_dashboard.py

Then open your browser to: http://localhost:8000
"""

import sys
from pathlib import Path
import uvicorn
from fastapi.responses import FileResponse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.agents import (
    # Conversation
    ConversationalAgent,

    # Templates and ensembles
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,

    # Paper trading
    PaperTradingEngine,
    PaperTradingConfig,
    TradingMode
)

from superstandard.api.dashboard_api import create_dashboard_app


def main():
    """Launch the dashboard"""
    print("\n" + "=" * 80)
    print("  🚀 LAUNCHING CONVERSATIONAL TRADING DASHBOARD")
    print("=" * 80)

    print("\n📦 Initializing components...")

    # 1. Create ensemble
    print("   ✅ Creating balanced trader ensemble...")
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()

    # 2. Add sentiment + explainability
    print("   ✅ Adding sentiment analysis and explainable AI...")
    explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

    # 3. Create paper trading engine
    print("   ✅ Initializing paper trading engine...")
    config = PaperTradingConfig(
        initial_cash=100000.0,
        trading_mode=TradingMode.PAPER,
        max_position_size=10000.0
    )
    paper_engine = PaperTradingEngine(config=config)

    # 4. Create conversational agent
    print("   ✅ Creating conversational AI agent...")
    agent = ConversationalAgent(
        paper_trading_engine=paper_engine,
        explainable_ensemble=explainable,
        sentiment_enhancer=sentiment_enhancer
    )

    # 5. Create FastAPI app
    print("   ✅ Building dashboard API...")
    app = create_dashboard_app(
        conversational_agent=agent,
        paper_trading_engine=paper_engine,
        sentiment_enhancer=sentiment_enhancer,
        explainable_ensemble=explainable
    )

    # Add route to serve the dashboard HTML
    dashboard_html_path = Path(__file__).parent.parent / "src" / "superstandard" / "api" / "conversational_dashboard.html"

    @app.get("/dashboard", response_class=FileResponse)
    async def serve_dashboard():
        """Serve the dashboard HTML"""
        return FileResponse(dashboard_html_path)

    print("\n" + "=" * 80)
    print("  ✅ DASHBOARD READY!")
    print("=" * 80)

    print("\n🌟 Features Available:")
    print("   • 💬 Conversational AI Trader - Chat in plain English!")
    print("   • 📊 Real-Time Portfolio - Live position tracking")
    print("   • 💭 Multi-Source Sentiment - News, Twitter, Reddit")
    print("   • 🧠 Explainable AI - Transparent decision-making")
    print("   • ⚡ WebSocket Updates - Real-time streaming")

    print("\n🔗 Access Dashboard:")
    print("   Main Dashboard:  http://localhost:8000/dashboard")
    print("   API Docs:        http://localhost:8000/docs")
    print("   API Status:      http://localhost:8000/api/status")

    print("\n💡 Try These Commands in the Chat:")
    print('   • "What\'s the sentiment on AAPL?"')
    print('   • "Buy 100 shares of TSLA"')
    print('   • "Show me my portfolio"')
    print('   • "Why did you recommend that?"')
    print('   • "Make me more conservative"')

    print("\n🚀 Starting server...")
    print("   Press CTRL+C to stop")
    print("=" * 80 + "\n")

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped. Thanks for using the Agentic Forge!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
