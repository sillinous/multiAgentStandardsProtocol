"""
Real Market Data Integration Demo

Demonstrates using real market data from Alpaca API for:
1. Fetching historical data
2. Running backtests with real data
3. Paper trading with agent decisions

Prerequisites:
- Alpaca account (free at https://alpaca.markets/)
- Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.agents import (
    # Market Data
    AlpacaClient,
    AlpacaConfig,
    RealMarketDataAdapter,
    create_real_data_adapter,
    PaperTradingEngine,
    PaperTradingConfig,
    OrderSide,

    # Ensemble & Templates
    TemplateLibrary,

    # Backtesting
    BacktestEngine,
    BacktestConfig
)


# ============================================================================
# Configuration
# ============================================================================

# Check for API keys
if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_API_SECRET'):
    print("⚠️  ALPACA_API_KEY and ALPACA_API_SECRET environment variables required!")
    print("\nGet your free API keys at: https://alpaca.markets/")
    print("\nSet them in your environment or .env file:")
    print("  export ALPACA_API_KEY='your_key_here'")
    print("  export ALPACA_API_SECRET='your_secret_here'")
    sys.exit(1)


# ============================================================================
# Demo 1: Fetch Real Historical Data
# ============================================================================

def demo_1_fetch_real_data():
    """Fetch real historical market data"""
    print("\n" + "="*80)
    print("DEMO 1: Fetching Real Historical Market Data")
    print("="*80)

    # Create Alpaca client
    config = AlpacaConfig()
    client = AlpacaClient(config)

    # Fetch historical data for AAPL
    print("\n📊 Fetching 30 days of AAPL data...")
    bars = client.get_historical_bars(
        symbol="AAPL",
        days=30,
        timeframe="1Day"
    )

    print(f"\n✅ Fetched {len(bars)} bars")
    print("\nLatest 5 bars:")
    for bar in bars[-5:]:
        print(f"  {bar.timestamp.date()}: "
              f"Open=${bar.open:.2f} "
              f"High=${bar.high:.2f} "
              f"Low=${bar.low:.2f} "
              f"Close=${bar.close:.2f} "
              f"Volume={bar.volume:,}")

    return bars


# ============================================================================
# Demo 2: Backtest with Real Data
# ============================================================================

def demo_2_backtest_with_real_data():
    """Run backtest using real market data"""
    print("\n" + "="*80)
    print("DEMO 2: Backtesting with Real Market Data")
    print("="*80)

    # Create real data adapter
    adapter = create_real_data_adapter()

    # Fetch real data
    print("\n📊 Fetching 90 days of SPY data...")
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()

    real_bars = adapter.fetch_backtest_data(
        symbol="SPY",
        start_date=start_date,
        end_date=end_date,
        timeframe="1Day"
    )

    print(f"✅ Fetched {len(real_bars)} bars")

    # Deploy an ensemble
    print("\n🤖 Deploying Balanced Trader ensemble...")
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()

    # Configure backtest
    backtest_config = BacktestConfig(
        symbol="SPY",
        start_date=start_date,
        end_date=end_date,
        initial_capital=10000.0,
        commission_rate=0.001,
        slippage_rate=0.0005
    )

    # Run backtest with real data
    print("\n⚡ Running backtest with real market data...")
    engine = BacktestEngine(backtest_config)
    result = engine.run(ensemble, real_bars)

    # Display results
    print(f"\n📈 Backtest Results:")
    print(f"   Total Return: {result.metrics.total_return_percent:.2f}%")
    print(f"   Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {result.metrics.max_drawdown_percent:.2f}%")
    print(f"   Win Rate: {result.metrics.win_rate * 100:.1f}%")
    print(f"   Total Trades: {result.metrics.total_trades}")
    print(f"   Total Decisions: {result.metrics.total_decisions}")

    return result


# ============================================================================
# Demo 3: Paper Trading
# ============================================================================

def demo_3_paper_trading():
    """Execute paper trades based on agent decisions"""
    print("\n" + "="*80)
    print("DEMO 3: Paper Trading with Agent Decisions")
    print("="*80)

    # Create paper trading engine
    config = PaperTradingConfig(
        alpaca_config=AlpacaConfig(),
        position_size_percent=0.1,  # Use 10% per trade
        max_position_count=3
    )

    trading_engine = PaperTradingEngine(config)

    # Get account info
    print("\n💰 Paper Trading Account:")
    account = trading_engine.client.get_account()
    print(f"   Portfolio Value: ${account.portfolio_value:,.2f}")
    print(f"   Cash: ${account.cash:,.2f}")
    print(f"   Buying Power: ${account.buying_power:,.2f}")

    # Deploy ensemble
    print("\n🤖 Deploying Aggressive Trader ensemble...")
    library = TemplateLibrary()
    template = library.get_template("aggressive_trader")
    ensemble = template.create_ensemble()

    # Fetch current market data
    print("\n📊 Fetching current market data for AAPL...")
    adapter = create_real_data_adapter()
    recent_bars = adapter.fetch_backtest_data(
        symbol="AAPL",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        timeframe="1Day"
    )

    # Make decision
    print("\n🧠 Agent ensemble analyzing market conditions...")
    if recent_bars:
        latest_bar = recent_bars[-1]
        decision = ensemble.make_decision(
            market_data={"current_price": latest_bar.close}
        )

        print(f"\n✅ Decision: {decision.action.upper()}")
        print(f"   Confidence: {decision.confidence * 100:.1f}%")
        print(f"   Reasoning: {decision.reasoning}")

        # Execute paper trade
        if decision.action != "hold":
            print(f"\n💼 Executing paper trade...")
            result = trading_engine.execute_decision("AAPL", decision)

            if result.success:
                print(f"   ✅ {result.message}")
                print(f"   Order ID: {result.order_id}")
            else:
                print(f"   ❌ Trade failed: {result.error}")
        else:
            print("   ℹ️  No trade executed (decision was HOLD)")

    # Show current positions
    print("\n📊 Current Positions:")
    positions = trading_engine.get_positions()
    if positions:
        for pos in positions:
            print(f"   {pos.symbol}: {pos.quantity:.2f} shares @ ${pos.current_price:.2f}")
            print(f"      Market Value: ${pos.market_value:,.2f}")
            print(f"      P&L: ${pos.unrealized_pl:,.2f} ({pos.unrealized_pl_percent * 100:.2f}%)")
    else:
        print("   No open positions")

    # Show performance metrics
    print("\n📈 Paper Trading Performance:")
    metrics = trading_engine.get_performance_metrics()
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Successful: {metrics['successful_trades']}")
    print(f"   Failed: {metrics['failed_trades']}")
    print(f"   Success Rate: {metrics['success_rate'] * 100:.1f}%")

    return trading_engine


# ============================================================================
# Demo 4: Real-Time Price Monitoring
# ============================================================================

def demo_4_real_time_monitoring():
    """Monitor real-time prices"""
    print("\n" + "="*80)
    print("DEMO 4: Real-Time Price Monitoring")
    print("="*80)

    client = AlpacaClient(AlpacaConfig())

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    print("\n📊 Current Prices:")
    for symbol in symbols:
        try:
            price = client.get_current_price(symbol)
            print(f"   {symbol}: ${price:.2f}")
        except Exception as e:
            print(f"   {symbol}: Error - {e}")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("🚀 REAL MARKET DATA INTEGRATION DEMO")
    print("="*80)
    print("\nThis demo showcases:")
    print("  1. Fetching real historical market data from Alpaca")
    print("  2. Running backtests with real data")
    print("  3. Paper trading with agent ensemble decisions")
    print("  4. Real-time price monitoring")
    print("\n⚠️  Note: This uses PAPER TRADING (simulated money)")
    print("="*80)

    try:
        # Run demos
        demo_1_fetch_real_data()
        demo_2_backtest_with_real_data()
        demo_3_paper_trading()
        demo_4_real_time_monitoring()

        print("\n" + "="*80)
        print("✅ All demos completed successfully!")
        print("="*80)

        print("\n📚 Next Steps:")
        print("  1. Explore the code in examples/real_market_data_demo.py")
        print("  2. Read MARKET_DATA_GUIDE.md for detailed documentation")
        print("  3. Try modifying the demo to test your own strategies")
        print("  4. Use the REST API for programmatic access")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
