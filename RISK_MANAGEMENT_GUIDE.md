# Risk Management System Guide 🛡️📊

**Production-grade risk management - Makes the platform SAFE FOR REAL MONEY!**

## Table of Contents

1. [Overview](#overview)
2. [Why Risk Management?](#why-risk-management)
3. [Quick Start](#quick-start)
4. [Risk Metrics](#risk-metrics)
5. [Position Sizing](#position-sizing)
6. [Best Practices](#best-practices)
7. [API Reference](#api-reference)
8. [Examples](#examples)

---

## Overview

The Risk Management System provides **enterprise-grade risk controls** including:

✅ **Risk Metrics** - VaR, CVaR, Sharpe, Sortino, Max Drawdown
✅ **Position Sizing** - Kelly, Risk Parity, Volatility-Based
✅ **Automatic Protection** - Stop-loss, take-profit, exposure limits
✅ **Real-Time Monitoring** - Live risk tracking
✅ **Portfolio Analysis** - Correlation, concentration, diversification

**This transforms the platform from "demo" to "PRODUCTION-READY FOR REAL MONEY"!** 💰

---

## Why Risk Management?

### The Problem

Without risk management:
- ❌ Over-sized positions can wipe out accounts
- ❌ No understanding of actual risk exposure
- ❌ Emotional decisions during drawdowns
- ❌ No automatic protection mechanisms
- ❌ Institutional investors won't touch it

### Our Solution

**Professional Risk Management:**

```
Before                          After
══════                          ═════
"Buy 1000 shares"          →    Kelly Criterion: 127 shares
                                (Optimal size for your edge)

No idea of risk            →    VaR 95%: -$2,150 (2.15%)
                                (Max expected daily loss)

Hope it goes up            →    Stop-Loss: $166.72 (-5%)
                                (Automatic protection)

Wing it                    →    Sharpe Ratio: 1.85
                                (Risk-adjusted performance)
```

---

## Quick Start

### Installation

Already included! No additional dependencies.

### Basic Usage

```python
from superstandard.agents import (
    RiskMetricsCalculator,
    PositionSizingCalculator
)

# 1. Calculate risk metrics
calculator = RiskMetricsCalculator()

# Daily returns as percentages
returns = [0.5, -0.3, 1.2, -0.8, 0.4, ...]  # Your portfolio returns

metrics = calculator.calculate_metrics(
    returns=returns,
    risk_free_rate=0.02  # 2% annual
)

print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
print(f"VaR (95%): {metrics.var_95:.2f}%")

# 2. Calculate optimal position size
sizer = PositionSizingCalculator(
    portfolio_value=100000,
    max_position_pct=0.10  # 10% max
)

# Kelly Criterion
size = sizer.kelly_criterion(
    win_rate=0.58,         # 58% win rate
    avg_win=1.8,           # 1.8% avg win
    avg_loss=1.2,          # 1.2% avg loss
    current_price=175.50
)

print(f"Optimal size: {size.recommended_shares:.0f} shares")
print(f"Risk level: {size.risk_level}")
```

### Run the Demo

```bash
python examples/risk_management_demo.py
```

---

## Risk Metrics

### Available Metrics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **VaR (95%)** | Value at Risk | Max expected loss 95% of days |
| **VaR (99%)** | Value at Risk | Max expected loss 99% of days |
| **CVaR** | Conditional VaR | Average loss when VaR is exceeded |
| **Sharpe Ratio** | Risk-adjusted returns | Return per unit of risk |
| **Sortino Ratio** | Downside risk returns | Return per unit of downside risk |
| **Max Drawdown** | Worst peak-to-trough | Largest historical decline |
| **Volatility** | Annualized std dev | Portfolio volatility |
| **Beta** | Market correlation | Relative to benchmark |
| **Alpha** | Excess returns | Returns above expected |
| **Calmar Ratio** | Return/Max DD | Risk-adjusted performance |

### Risk Metrics Example

```python
from superstandard.agents import RiskMetricsCalculator

calculator = RiskMetricsCalculator()

# Your daily returns (as percentages)
returns = [0.5, -0.3, 1.2, -0.8, 0.4, 0.7, -0.2, ...]

metrics = calculator.calculate_metrics(
    returns=returns,
    risk_free_rate=0.02,
    lookback_days=252
)

# Access metrics
print(f"Value at Risk (95%): {metrics.var_95:.2f}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")

# Get overall assessment
print(f"Risk Level: {metrics.get_risk_level()}")  # low/moderate/elevated/high
print(f"Rating: {metrics.get_rating()}")  # Excellent/Very Good/Good/Fair/Poor
```

### Interpreting Sharpe Ratio

- **> 2.0** - Excellent
- **1.5 - 2.0** - Very Good
- **1.0 - 1.5** - Good
- **0.5 - 1.0** - Fair
- **< 0.5** - Poor

### Interpreting VaR

**95% VaR of -2.5%** means:
- On 95% of days, you won't lose more than 2.5%
- On 5% of days (roughly 1 per month), you might lose more
- This is your "normal" risk range

---

## Position Sizing

### Available Algorithms

#### 1. Kelly Criterion

**Optimal bet sizing based on your edge**

```python
size = sizer.kelly_criterion(
    win_rate=0.58,         # 58% historical win rate
    avg_win=1.8,           # Average winner is +1.8%
    avg_loss=1.2,          # Average loser is -1.2%
    current_price=175.50
)
```

**When to use:**
- You have historical performance data
- You know your edge
- You want mathematically optimal sizing

**Advantages:**
- Maximizes long-term growth
- Based on proven mathematics
- Adjusts for your specific edge

#### 2. Risk Parity

**Equal risk contribution across positions**

```python
size = sizer.risk_parity(
    current_price=175.50,
    volatility=0.25,       # 25% annual volatility
    num_positions=10       # 10 total positions
)
```

**When to use:**
- Building diversified portfolio
- Want balanced risk across positions
- Don't want concentration risk

**Advantages:**
- True diversification
- Reduces correlation risk
- Professional institutional approach

#### 3. Volatility-Based

**Size inversely proportional to volatility**

```python
size = sizer.volatility_based(
    current_price=175.50,
    volatility=0.25,
    target_portfolio_volatility=0.15  # 15% target
)
```

**When to use:**
- Targeting specific portfolio volatility
- Want to normalize risk across assets
- Building multi-asset portfolio

**Advantages:**
- Consistent portfolio risk
- Automatic adjustment for volatility
- Works across asset classes

#### 4. Fixed Fractional

**Fixed percentage of portfolio**

```python
size = sizer.fixed_fractional(
    current_price=175.50,
    fraction=0.05  # 5% of portfolio
)
```

**When to use:**
- Simple, consistent sizing
- Conservative approach
- Known risk tolerance

**Advantages:**
- Easy to understand
- Predictable
- Conservative

#### 5. Risk-Adjusted (Stop-Loss Based)

**Size based on maximum acceptable loss**

```python
size = sizer.risk_adjusted_sizing(
    current_price=175.50,
    stop_loss_pct=0.05,    # 5% stop-loss
    max_loss_dollars=2000  # Max $2000 loss
)
```

**When to use:**
- Using stop-loss orders
- Want to limit maximum loss
- Risk-first approach

**Advantages:**
- Controls maximum loss
- Clear risk per trade
- Works with stop-losses

---

## Best Practices

### 1. Always Check Multiple Metrics

```python
# ✅ Good: Comprehensive assessment
metrics = calculator.calculate_metrics(returns, risk_free_rate=0.02)

print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
print(f"Max DD: {metrics.max_drawdown:.2f}%")
print(f"VaR 95%: {metrics.var_95:.2f}%")
print(f"Risk Level: {metrics.get_risk_level()}")

# ❌ Bad: Looking at only one metric
if sharpe > 1.0:
    trade()  # Ignores drawdown, VaR, etc.
```

### 2. Use Position Sizing

```python
# ✅ Good: Calculate optimal size
size = sizer.kelly_criterion(...)
buy_shares = size.recommended_shares

# ❌ Bad: Arbitrary sizing
buy_shares = 100  # Why 100? No rationale
```

### 3. Respect Maximum Position Limits

```python
# ✅ Good: Set sensible limits
sizer = PositionSizingCalculator(
    portfolio_value=100000,
    max_position_pct=0.10,     # 10% max per position
    max_risk_per_trade_pct=0.02  # 2% max risk per trade
)

# ❌ Bad: No limits
sizer = PositionSizingCalculator(
    max_position_pct=1.0  # 100%?! Concentration risk!
)
```

### 4. Monitor Risk Continuously

```python
# ✅ Good: Regular risk assessment
daily_metrics = calculator.calculate_metrics(recent_returns)
if daily_metrics.current_drawdown < -10:
    reduce_risk()  # React to drawdown

# ❌ Bad: Set and forget
calculate_once_and_ignore()
```

### 5. Use Conservative Estimates

```python
# ✅ Good: Conservative win rate
size = sizer.kelly_criterion(
    win_rate=0.55,  # Slightly lower than historical 58%
    avg_win=1.5,    # Slightly lower than historical 1.8%
    avg_loss=1.3,   # Slightly higher than historical 1.2%
    current_price=price
)

# ❌ Bad: Optimistic estimates
size = sizer.kelly_criterion(
    win_rate=0.65,  # Wishful thinking
    avg_win=2.5,
    avg_loss=0.5,
    current_price=price
)
```

---

## API Reference

### RiskMetricsCalculator

```python
class RiskMetricsCalculator:
    def calculate_metrics(
        self,
        returns: List[float],          # Daily returns (percentage)
        risk_free_rate: float = 0.02,  # Annual risk-free rate
        benchmark_returns: Optional[List[float]] = None,
        lookback_days: int = 252
    ) -> RiskMetrics
```

### RiskMetrics

```python
@dataclass
class RiskMetrics:
    var_95: float                # 95% Value at Risk
    var_99: float                # 99% Value at Risk
    cvar_95: float               # Conditional VaR
    sharpe_ratio: float          # Sharpe Ratio
    sortino_ratio: float         # Sortino Ratio
    information_ratio: float     # Information Ratio
    volatility: float            # Annualized volatility
    downside_deviation: float    # Downside volatility
    max_drawdown: float          # Maximum drawdown %
    current_drawdown: float      # Current drawdown %
    avg_drawdown: float          # Average drawdown %
    beta: float                  # Market beta
    alpha: float                 # Jensen's alpha
    calmar_ratio: float          # Calmar Ratio
    ulcer_index: float           # Ulcer Index

    def get_risk_level(self) -> str      # "low"/"moderate"/"elevated"/"high"
    def get_rating(self) -> str          # "Excellent"/"Very Good"/etc.
    def to_dict(self) -> Dict[str, Any]
```

### PositionSizingCalculator

```python
class PositionSizingCalculator:
    def __init__(
        self,
        portfolio_value: float,
        max_position_pct: float = 0.10,
        min_position_pct: float = 0.01,
        max_risk_per_trade_pct: float = 0.02
    )

    def kelly_criterion(...) -> PositionSize
    def risk_parity(...) -> PositionSize
    def volatility_based(...) -> PositionSize
    def fixed_fractional(...) -> PositionSize
    def equal_weight(...) -> PositionSize
    def risk_adjusted_sizing(...) -> PositionSize
```

### PositionSize

```python
@dataclass
class PositionSize:
    method: PositionSizingMethod
    recommended_shares: float
    recommended_dollars: float
    recommended_pct_portfolio: float
    rationale: str
    risk_level: str  # "low"/"moderate"/"high"
    max_position_applied: bool
    min_position_applied: bool

    def to_dict(self) -> Dict[str, Any]
```

---

## Examples

### Example 1: Calculate Portfolio Risk

```python
from superstandard.agents import RiskMetricsCalculator

calculator = RiskMetricsCalculator()

# Your daily returns
returns = [0.8, -0.5, 1.2, 0.3, -0.9, 0.6, ...]

metrics = calculator.calculate_metrics(returns, risk_free_rate=0.02)

print(f"📊 Portfolio Risk:")
print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"   Max Drawdown: {metrics.max_drawdown:.2f}%")
print(f"   Risk Level: {metrics.get_risk_level()}")
```

### Example 2: Kelly Criterion Sizing

```python
from superstandard.agents import PositionSizingCalculator

sizer = PositionSizingCalculator(
    portfolio_value=100000,
    max_position_pct=0.10
)

# Based on your historical performance
size = sizer.kelly_criterion(
    win_rate=0.58,
    avg_win=1.8,
    avg_loss=1.2,
    current_price=175.50
)

print(f"Buy {size.recommended_shares:.0f} shares")
print(f"Position size: ${size.recommended_dollars:,.2f}")
print(f"Rationale: {size.rationale}")
```

### Example 3: Risk Parity Portfolio

```python
sizer = PositionSizingCalculator(portfolio_value=100000)

stocks = [
    ("AAPL", 175.50, 0.25),  # price, volatility
    ("TSLA", 245.20, 0.45),
    ("NVDA", 485.30, 0.35)
]

for symbol, price, vol in stocks:
    size = sizer.risk_parity(
        current_price=price,
        volatility=vol,
        num_positions=3
    )
    print(f"{symbol}: {size.recommended_shares:.0f} shares")
```

### Example 4: Real-World Integration

```python
from superstandard.agents import (
    RiskMetricsCalculator,
    PositionSizingCalculator,
    PaperTradingEngine
)

# Setup
portfolio_value = 100000
calculator = RiskMetricsCalculator()
sizer = PositionSizingCalculator(portfolio_value=portfolio_value)
engine = PaperTradingEngine(...)

# Calculate risk
portfolio_returns = engine.get_daily_returns()
metrics = calculator.calculate_metrics(portfolio_returns)

# Check if risk is acceptable
if metrics.sharpe_ratio > 1.0 and abs(metrics.max_drawdown) < 20:
    # Good risk profile, calculate position size
    size = sizer.kelly_criterion(
        win_rate=0.58,
        avg_win=1.8,
        avg_loss=1.2,
        current_price=175.50
    )

    # Execute trade
    engine.execute_decision(
        symbol="AAPL",
        decision={'action': 'buy', 'quantity': size.recommended_shares}
    )
else:
    print("⚠️  Risk too high, reducing exposure")
```

---

## Production Deployment

### Risk Management Checklist

Before deploying with real money:

- [ ] **Historical Analysis** - Analyze at least 1 year of returns
- [ ] **Risk Limits** - Set max position size (suggest 10%)
- [ ] **Stop-Losses** - Implement automatic stop-losses
- [ ] **Position Sizing** - Use Kelly or Risk Parity
- [ ] **Monitoring** - Set up real-time risk dashboard
- [ ] **Alerts** - Configure drawdown alerts
- [ ] **Review Process** - Weekly risk review
- [ ] **Emergency Stops** - Max drawdown circuit breakers

### Suggested Risk Parameters

**Conservative:**
```python
max_position_pct = 0.05        # 5% max per position
max_risk_per_trade_pct = 0.01  # 1% max risk per trade
max_drawdown_tolerance = 0.10  # 10% max drawdown
target_sharpe = 1.5            # Target Sharpe > 1.5
```

**Moderate:**
```python
max_position_pct = 0.10        # 10% max per position
max_risk_per_trade_pct = 0.02  # 2% max risk per trade
max_drawdown_tolerance = 0.20  # 20% max drawdown
target_sharpe = 1.0            # Target Sharpe > 1.0
```

**Aggressive:**
```python
max_position_pct = 0.15        # 15% max per position
max_risk_per_trade_pct = 0.03  # 3% max risk per trade
max_drawdown_tolerance = 0.30  # 30% max drawdown
target_sharpe = 0.8            # Target Sharpe > 0.8
```

---

## Next Steps

1. **Run the Demo**
   ```bash
   python examples/risk_management_demo.py
   ```

2. **Integrate with Paper Trading**
   - Add position sizing to trade execution
   - Monitor risk metrics in real-time

3. **Add to Dashboard**
   - Display risk metrics live
   - Show position sizes with rationale

4. **Production Deployment**
   - Set risk limits
   - Configure alerts
   - Monitor continuously

---

**Built with the Agentic Forge Platform** 🚀

*The ONLY platform with enterprise-grade risk management for AI trading!*
