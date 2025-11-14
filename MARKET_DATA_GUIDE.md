# Real Market Data Integration Guide 📊

Complete guide to using real market data and paper trading with the Agentic Forge platform.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Alpaca API Setup](#alpaca-api-setup)
4. [Fetching Historical Data](#fetching-historical-data)
5. [Backtesting with Real Data](#backtesting-with-real-data)
6. [Paper Trading](#paper-trading)
7. [Real-Time Data](#real-time-data)
8. [API Reference](#api-reference)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Real Market Data Integration connects your agent ensembles to live financial markets through the Alpaca API, enabling:

- ✅ **Real Historical Data** - Fetch actual market data for backtesting
- ✅ **Paper Trading** - Test strategies with simulated money in real market conditions
- ✅ **Real-Time Prices** - Monitor current market prices
- ✅ **Position Management** - Track and manage trading positions
- ✅ **Order Execution** - Execute market and limit orders

**Key Features:**
- Seamless integration with existing BacktestEngine
- Automatic position sizing and risk management
- Comprehensive execution tracking
- Support for multiple timeframes (1Min, 5Min, 1Hour, 1Day)
- Paper trading (simulated) and live trading modes

---

## Getting Started

### Prerequisites

1. **Alpaca Account** (Free)
   - Sign up at: https://alpaca.markets/
   - Provides free paper trading account with $100,000 simulated capital
   - No credit card required for paper trading

2. **API Credentials**
   - Get your API Key and Secret from Alpaca dashboard
   - Keep these secure - never commit to version control!

### Installation

```bash
# Install Alpaca SDK
pip install alpaca-py

# Or install all dependencies
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file** (copy from `.env.example`):
```bash
cp .env.example .env
```

2. **Add your Alpaca credentials**:
```env
ALPACA_API_KEY=your_api_key_here
ALPACA_API_SECRET=your_api_secret_here
ALPACA_PAPER=true  # Use paper trading (simulated)
```

3. **Load environment variables**:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Alpaca API Setup

### Creating an Account

1. Go to https://alpaca.markets/
2. Click "Sign Up" and create account
3. Verify your email
4. Navigate to "Paper Trading" section
5. Generate API keys (Key ID and Secret Key)

### API Key Management

**⚠️ Security Best Practices:**
- Store keys in `.env` file (never commit to git!)
- Use environment variables in production
- Rotate keys periodically
- Use paper trading for testing

**Paper vs Live Trading:**
```python
from superstandard.agents import AlpacaConfig

# Paper trading (simulated money)
paper_config = AlpacaConfig(
    api_key="your_key",
    api_secret="your_secret",
    paper_trading=True  # Safe for testing
)

# Live trading (REAL MONEY - use with caution!)
live_config = AlpacaConfig(
    api_key="your_key",
    api_secret="your_secret",
    paper_trading=False  # ⚠️ REAL MONEY!
)
```

---

## Fetching Historical Data

### Basic Usage

```python
from superstandard.agents import AlpacaClient, AlpacaConfig

# Create client
config = AlpacaConfig()
client = AlpacaClient(config)

# Fetch 30 days of daily bars
bars = client.get_historical_bars(
    symbol="AAPL",
    days=30,
    timeframe="1Day"
)

# Access data
for bar in bars:
    print(f"{bar.timestamp.date()}: Close=${bar.close:.2f}")
```

### Supported Timeframes

- `"1Min"` - 1-minute bars
- `"5Min"` - 5-minute bars
- `"15Min"` - 15-minute bars
- `"1Hour"` - 1-hour bars
- `"1Day"` - Daily bars (default)

### Using the Data Adapter

The `RealMarketDataAdapter` provides caching and seamless integration with BacktestEngine:

```python
from superstandard.agents import create_real_data_adapter
from datetime import datetime, timedelta

# Create adapter
adapter = create_real_data_adapter()

# Fetch data for backtesting
start_date = datetime.now() - timedelta(days=90)
end_date = datetime.now()

bars = adapter.fetch_backtest_data(
    symbol="SPY",
    start_date=start_date,
    end_date=end_date,
    timeframe="1Day"
)

# Data is automatically formatted for BacktestEngine
```

### Fetching Multiple Symbols

```python
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]

data = adapter.fetch_multiple_symbols(
    symbols=symbols,
    start_date=start_date,
    end_date=end_date,
    timeframe="1Day"
)

for symbol, bars in data.items():
    print(f"{symbol}: {len(bars)} bars")
```

---

## Backtesting with Real Data

### Replace Synthetic Data

Before (synthetic data):
```python
from superstandard.agents import HistoricalDataGenerator

# Generate fake data
fake_data = HistoricalDataGenerator.generate_price_data(
    start_date=start_date,
    end_date=end_date,
    initial_price=100.0
)
```

After (real data):
```python
from superstandard.agents import create_real_data_adapter

# Fetch real market data
adapter = create_real_data_adapter()
real_data = adapter.fetch_backtest_data(
    symbol="SPY",
    start_date=start_date,
    end_date=end_date
)
```

### Complete Backtest Example

```python
from superstandard.agents import (
    create_real_data_adapter,
    BacktestEngine,
    BacktestConfig,
    TemplateLibrary
)
from datetime import datetime, timedelta

# 1. Fetch real data
adapter = create_real_data_adapter()
start = datetime.now() - timedelta(days=90)
end = datetime.now()

real_bars = adapter.fetch_backtest_data(
    symbol="SPY",
    start_date=start,
    end_date=end,
    timeframe="1Day"
)

# 2. Deploy ensemble
library = TemplateLibrary()
template = library.get_template("balanced_trader")
ensemble = template.create_ensemble()

# 3. Configure backtest
config = BacktestConfig(
    symbol="SPY",
    start_date=start,
    end_date=end,
    initial_capital=10000.0,
    commission_rate=0.001,  # 0.1% commission
    slippage_rate=0.0005    # 0.05% slippage
)

# 4. Run backtest with real data
engine = BacktestEngine(config)
result = engine.run(ensemble, real_bars)

# 5. Analyze results
print(f"Total Return: {result.metrics.total_return_percent:.2f}%")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.metrics.max_drawdown_percent:.2f}%")
print(f"Win Rate: {result.metrics.win_rate * 100:.1f}%")
```

---

## Paper Trading

### Setup Paper Trading Engine

```python
from superstandard.agents import (
    PaperTradingEngine,
    PaperTradingConfig,
    AlpacaConfig
)

# Configure paper trading
config = PaperTradingConfig(
    alpaca_config=AlpacaConfig(),
    position_size_percent=0.1,      # Use 10% per trade
    max_position_count=5,           # Max 5 concurrent positions
    stop_loss_percent=0.05,         # 5% stop loss
    take_profit_percent=0.10,       # 10% take profit
    enable_logging=True
)

# Create engine
trading_engine = PaperTradingEngine(config)
```

### Execute Agent Decisions

```python
from superstandard.agents import TemplateLibrary

# Deploy ensemble
library = TemplateLibrary()
template = library.get_template("aggressive_trader")
ensemble = template.create_ensemble()

# Get market data and make decision
market_data = {"current_price": 150.00}
decision = ensemble.make_decision(market_data)

# Execute decision in paper trading
result = trading_engine.execute_decision("AAPL", decision)

if result.success:
    print(f"✅ Trade executed: {result.message}")
    print(f"Order ID: {result.order_id}")
else:
    print(f"❌ Trade failed: {result.error}")
```

### Manual Trading

```python
from superstandard.agents import OrderSide

# Place manual buy order
result = trading_engine.execute_manual_trade(
    symbol="AAPL",
    side=OrderSide.BUY,
    quantity=10
)

# Place manual sell order
result = trading_engine.execute_manual_trade(
    symbol="AAPL",
    side=OrderSide.SELL,
    quantity=10
)
```

### Monitor Positions

```python
# Get all positions
positions = trading_engine.get_positions()

for pos in positions:
    print(f"{pos.symbol}:")
    print(f"  Quantity: {pos.quantity}")
    print(f"  Market Value: ${pos.market_value:,.2f}")
    print(f"  P&L: ${pos.unrealized_pl:,.2f} ({pos.unrealized_pl_percent * 100:.2f}%)")

# Get specific position
position = trading_engine.get_position("AAPL")
if position:
    print(f"AAPL position: {position.quantity} shares")
```

### Close Positions

```python
# Close specific position
trading_engine.close_position("AAPL")

# Close all positions
trading_engine.close_all_positions()
```

### Track Performance

```python
# Get performance metrics
metrics = trading_engine.get_performance_metrics()

print(f"Account Value: ${metrics['account_value']:,.2f}")
print(f"Total Trades: {metrics['total_trades']}")
print(f"Successful: {metrics['successful_trades']}")
print(f"Win Rate: {metrics['win_rate'] * 100:.1f}%")
print(f"Total P&L: ${metrics['total_unrealized_pl']:,.2f}")

# Get execution history
history = trading_engine.get_execution_history(limit=10)

for result in history:
    print(f"{result.timestamp}: {result.side.value} {result.quantity} {result.symbol}")

# Get account summary
summary = trading_engine.get_account_summary()
print(summary)
```

---

## Real-Time Data

### Get Current Prices

```python
from superstandard.agents import AlpacaClient, AlpacaConfig

client = AlpacaClient(AlpacaConfig())

# Get current price
price = client.get_current_price("AAPL")
print(f"AAPL: ${price:.2f}")

# Get latest bar
bar = client.get_latest_bar("AAPL")
print(f"Latest: Open=${bar.open:.2f}, Close=${bar.close:.2f}")
```

### Monitor Multiple Symbols

```python
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

for symbol in symbols:
    price = client.get_current_price(symbol)
    print(f"{symbol}: ${price:.2f}")
```

### Account Information

```python
# Get account info
account = client.get_account()

print(f"Portfolio Value: ${account.portfolio_value:,.2f}")
print(f"Cash: ${account.cash:,.2f}")
print(f"Buying Power: ${account.buying_power:,.2f}")
print(f"Equity: ${account.equity:,.2f}")
```

---

## API Reference

### AlpacaClient

Main client for Alpaca API interaction.

**Methods:**

```python
# Market Data
get_historical_bars(symbol: str, days: int, timeframe: str) -> List[MarketDataBar]
get_latest_bar(symbol: str) -> MarketDataBar
get_current_price(symbol: str) -> float

# Account
get_account() -> AccountInfo

# Positions
get_positions() -> List[Position]
get_position(symbol: str) -> Position

# Orders
place_market_order(symbol, side, quantity, time_in_force) -> Order
place_limit_order(symbol, side, quantity, limit_price, time_in_force) -> Order
get_orders(status: str) -> List[Order]
cancel_order(order_id: str) -> bool

# Position Management
close_position(symbol: str) -> bool
close_all_positions() -> bool
```

### RealMarketDataAdapter

Adapter for fetching real data for backtesting.

**Methods:**

```python
fetch_backtest_data(symbol, start_date, end_date, timeframe) -> List[MarketBar]
fetch_multiple_symbols(symbols, start_date, end_date, timeframe) -> Dict[str, List[MarketBar]]
get_latest_price(symbol: str) -> float
clear_cache()
```

### PaperTradingEngine

Engine for executing trades based on agent decisions.

**Methods:**

```python
execute_decision(symbol: str, decision: Decision) -> TradeExecutionResult
execute_manual_trade(symbol, side, quantity) -> TradeExecutionResult
get_positions() -> List[Position]
get_position(symbol: str) -> Position
close_position(symbol: str) -> bool
close_all_positions() -> bool
get_performance_metrics() -> Dict[str, Any]
get_execution_history(limit, symbol) -> List[TradeExecutionResult]
get_account_summary() -> Dict[str, Any]
```

---

## Best Practices

### 1. **Always Use Paper Trading First**
```python
# ✅ Good: Test with paper trading
config = AlpacaConfig(paper_trading=True)

# ❌ Bad: Jumping straight to live trading
config = AlpacaConfig(paper_trading=False)  # REAL MONEY!
```

### 2. **Implement Position Sizing**
```python
# ✅ Good: Risk-managed position sizing
config = PaperTradingConfig(
    position_size_percent=0.1,  # 10% per position
    max_position_count=5        # Max 5 positions
)

# ❌ Bad: All-in on single position
config = PaperTradingConfig(
    position_size_percent=1.0,  # 100% - risky!
    max_position_count=1
)
```

### 3. **Use Stop Losses**
```python
# ✅ Good: Protect against large losses
config = PaperTradingConfig(
    stop_loss_percent=0.05,      # 5% stop loss
    take_profit_percent=0.10     # 10% take profit
)
```

### 4. **Backtest Before Trading**
```python
# ✅ Good: Validate strategy with historical data
result = backtest_engine.run(ensemble, real_bars)
if result.metrics.sharpe_ratio > 1.5:
    # Strategy looks good, try paper trading
    pass
```

### 5. **Monitor Performance**
```python
# ✅ Good: Regular monitoring
metrics = trading_engine.get_performance_metrics()
if metrics['win_rate'] < 0.4:
    print("⚠️  Strategy underperforming!")
```

### 6. **Handle Errors Gracefully**
```python
# ✅ Good: Error handling
try:
    result = trading_engine.execute_decision(symbol, decision)
    if not result.success:
        logger.error(f"Trade failed: {result.error}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### 7. **Respect Rate Limits**
```python
# ✅ Good: Add delays for bulk operations
import time

for symbol in symbols:
    price = client.get_current_price(symbol)
    time.sleep(0.1)  # 100ms delay
```

---

## Troubleshooting

### Common Issues

#### 1. **"Alpaca SDK not installed"**
```bash
pip install alpaca-py
```

#### 2. **"API credentials not provided"**
```bash
# Check .env file
export ALPACA_API_KEY='your_key'
export ALPACA_API_SECRET='your_secret'

# Verify in Python
import os
print(os.getenv('ALPACA_API_KEY'))  # Should print your key
```

#### 3. **"Insufficient funds"**
- Paper trading accounts start with $100,000
- Check account: `client.get_account().cash`
- Reduce `position_size_percent` in config

#### 4. **"Max position count reached"**
```python
# Close some positions
trading_engine.close_position("AAPL")

# Or increase limit
config = PaperTradingConfig(max_position_count=10)
```

#### 5. **"No data returned"**
- Check symbol is valid
- Verify market is open (no data on weekends/holidays)
- Try different timeframe
- Check date range is reasonable

#### 6. **Rate Limiting**
```python
# Add caching to reduce API calls
adapter = RealMarketDataAdapter(
    RealDataConfig(
        alpaca_config=config,
        cache_enabled=True,
        cache_ttl_seconds=300  # 5 minutes
    )
)
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs from Alpaca client
```

### Testing Without API Keys

For development without Alpaca account:
```python
# Use synthetic data generator
from superstandard.agents import HistoricalDataGenerator

fake_data = HistoricalDataGenerator.generate_price_data(
    start_date=start,
    end_date=end,
    initial_price=100.0,
    volatility=0.02
)
```

---

## Next Steps

1. **Run the Demo**
   ```bash
   python examples/real_market_data_demo.py
   ```

2. **Build Your Own Strategy**
   - Create custom agent personalities
   - Define ensemble composition
   - Backtest with real data
   - Paper trade to validate

3. **Monitor Live**
   - Use dashboard for real-time monitoring
   - Track performance metrics
   - Analyze execution history

4. **Go Live** (when ready)
   - Extensive backtesting (6+ months data)
   - Paper trading validation (30+ days)
   - Small position sizes initially
   - Continuous monitoring

---

## Resources

- **Alpaca Documentation**: https://alpaca.markets/docs/
- **Alpaca Dashboard**: https://app.alpaca.markets/
- **Platform Docs**: `COMPLETE_PLATFORM_GUIDE.md`
- **Backtesting Guide**: `BACKTESTING_GUIDE.md`
- **Paper Trading Guide**: `PAPER_TRADING_GUIDE.md`

---

## Support

Having issues? Check:
1. This guide's [Troubleshooting](#troubleshooting) section
2. Alpaca API status: https://status.alpaca.markets/
3. Platform GitHub issues

---

**Built with the Agentic Forge Platform** 🚀

*Connecting autonomous agents to real financial markets.*
