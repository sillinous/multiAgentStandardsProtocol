"""
NEXUS Demo Data Generator

Creates realistic sample strategies and backtest results for demonstration.
Populates the platform with professional-looking trading data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import math


class DemoDataGenerator:
    """Generates realistic demo trading data"""

    SAMPLE_STRATEGIES = [
        {
            "name": "SMA Crossover Pro",
            "description": "Simple Moving Average crossover strategy with proven edge. Fast MA=10, Slow MA=30",
            "code": """async def sma_crossover_strategy(timestamp, bar, historical_data, fast_period=10, slow_period=30):
    '''SMA Crossover: Buy when fast > slow, sell when fast < slow'''
    if len(historical_data) < slow_period:
        return None

    closes = historical_data['close']
    fast_sma = closes.rolling(fast_period).mean().iloc[-1]
    slow_sma = closes.rolling(slow_period).mean().iloc[-1]

    if fast_sma > slow_sma and closes.iloc[-2] <= closes.iloc[-1]:
        return ('BUY', 0.95)
    elif fast_sma < slow_sma and closes.iloc[-2] >= closes.iloc[-1]:
        return ('SELL', 0.95)
    return None
""",
            "parameters": {"fast_period": 10, "slow_period": 30, "position_size": 0.95},
            "tags": ["momentum", "proven", "sma", "beginner"],
            "strategy_type": "ai_generated",
        },
        {
            "name": "RSI Momentum Reversal",
            "description": "RSI-based mean reversion strategy. Trades when RSI is oversold (<30) or overbought (>70)",
            "code": """async def rsi_reversal_strategy(timestamp, bar, historical_data, rsi_period=14, upper=70, lower=30):
    '''RSI Reversal: Buy oversold (RSI<30), sell overbought (RSI>70)'''
    if len(historical_data) < rsi_period:
        return None

    close = historical_data['close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    current_rsi = rsi.iloc[-1]
    if current_rsi < lower:
        return ('BUY', 0.90)
    elif current_rsi > upper:
        return ('SELL', 0.90)
    return None
""",
            "parameters": {"rsi_period": 14, "upper": 70, "lower": 30, "position_size": 0.90},
            "tags": ["reversal", "rsi", "momentum", "intermediate"],
            "strategy_type": "ai_generated",
        },
        {
            "name": "Bollinger Band Squeeze",
            "description": "Volatility breakout strategy. Enters on squeeze breakout, exits on band touch",
            "code": """async def bollinger_band_squeeze(timestamp, bar, historical_data, period=20, std_dev=2):
    '''Bollinger Bands: Buy on squeeze breakout above upper band'''
    if len(historical_data) < period:
        return None

    close = historical_data['close']
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    current = close.iloc[-1]
    prev = close.iloc[-2]

    if prev <= upper.iloc[-2] and current > upper.iloc[-1]:
        return ('BUY', 0.92)
    elif prev >= lower.iloc[-2] and current < lower.iloc[-1]:
        return ('SELL', 0.92)
    return None
""",
            "parameters": {"period": 20, "std_dev": 2, "position_size": 0.92},
            "tags": ["volatility", "breakout", "intermediate"],
            "strategy_type": "ai_generated",
        },
        {
            "name": "EMA Trend Follower",
            "description": "Exponential Moving Average trend following. Smooth responsive entries on trend change",
            "code": """async def ema_trend_follower(timestamp, bar, historical_data, short_ema=12, long_ema=26):
    '''EMA Trend: Follow trend with exponential moving averages'''
    if len(historical_data) < long_ema:
        return None

    close = historical_data['close']
    short = close.ewm(span=short_ema).mean()
    long = close.ewm(span=long_ema).mean()

    if short.iloc[-1] > long.iloc[-1] and short.iloc[-2] <= long.iloc[-2]:
        return ('BUY', 0.93)
    elif short.iloc[-1] < long.iloc[-1] and short.iloc[-2] >= long.iloc[-2]:
        return ('SELL', 0.93)
    return None
""",
            "parameters": {"short_ema": 12, "long_ema": 26, "position_size": 0.93},
            "tags": ["trend", "ema", "responsive", "advanced"],
            "strategy_type": "ai_generated",
        },
        {
            "name": "MACD Signal Trader",
            "description": "MACD histogram-based strategy. Trades MACD line crosses with signal line",
            "code": """async def macd_signal_strategy(timestamp, bar, historical_data, fast=12, slow=26, signal=9):
    '''MACD: Trade signal line crossovers'''
    if len(historical_data) < slow + signal:
        return None

    close = historical_data['close']
    exp1 = close.ewm(span=fast).mean()
    exp2 = close.ewm(span=slow).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line

    if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0:
        return ('BUY', 0.91)
    elif histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0:
        return ('SELL', 0.91)
    return None
""",
            "parameters": {"fast": 12, "slow": 26, "signal": 9, "position_size": 0.91},
            "tags": ["macd", "signal", "technical", "advanced"],
            "strategy_type": "ai_generated",
        },
    ]

    @staticmethod
    def generate_equity_curve(
        initial_capital: float,
        num_days: int,
        volatility: float = 0.02,
        trend: float = 0.0008,
    ) -> List[float]:
        """Generate realistic equity curve using random walk"""
        equity = [initial_capital]

        for _ in range(num_days):
            daily_return = random.gauss(trend, volatility)
            new_equity = equity[-1] * (1 + daily_return)
            equity.append(new_equity)

        return equity

    @staticmethod
    def calculate_metrics(equity_curve: List[float]) -> Dict[str, Any]:
        """Calculate trading metrics from equity curve"""
        returns = [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
        ]

        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1

        # Max drawdown
        peak = equity_curve[0]
        max_dd = 0
        for val in equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            if dd > max_dd:
                max_dd = dd

        # Sharpe ratio
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        sharpe = (avg_return / math.sqrt(variance)) * math.sqrt(252) if variance > 0 else 0

        # Win rate (approximate)
        winning_days = sum(1 for r in returns if r > 0)
        win_rate = winning_days / len(returns)

        return {
            "total_return_pct": round(total_return * 100, 2),
            "annualized_return_pct": round(annual_return * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sharpe * 1.2, 2),  # Simplified
            "win_rate_pct": round(win_rate * 100, 2),
            "total_trades": random.randint(50, 200),
            "winning_trades": random.randint(30, 120),
            "losing_trades": random.randint(20, 80),
            "avg_win": round(random.uniform(0.5, 3.0), 2),
            "avg_loss": round(random.uniform(-2.0, -0.3), 2),
            "profit_factor": round(random.uniform(1.2, 2.5), 2),
        }

    @staticmethod
    def generate_sample_strategy(strategy_template: Dict, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Generate complete sample strategy with backtest results"""
        equity_curve = DemoDataGenerator.generate_equity_curve(
            initial_capital, 252, volatility=0.015, trend=0.0005
        )
        metrics = DemoDataGenerator.calculate_metrics(equity_curve)

        start_date = datetime.utcnow() - timedelta(days=365)
        end_date = datetime.utcnow()

        return {
            **strategy_template,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "is_active": True,
            "is_favorite": random.choice([True, False, False]),
            "total_backtests": random.randint(3, 8),
            "best_sharpe_ratio": metrics["sharpe_ratio"],
            "best_total_return_pct": metrics["total_return_pct"],
            "avg_win_rate": metrics["win_rate_pct"],
            "backtest_results": {
                "latest": {
                    "symbol": "SOL/USD",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timeframe": "1d",
                    "initial_capital": initial_capital,
                    "final_capital": equity_curve[-1],
                    **metrics,
                    "equity_curve": [round(e, 2) for e in equity_curve[::10]],  # Sample every 10 days
                }
            },
        }

    @staticmethod
    def get_all_sample_strategies() -> List[Dict[str, Any]]:
        """Get all sample strategies with backtest results"""
        return [
            DemoDataGenerator.generate_sample_strategy(strategy)
            for strategy in DemoDataGenerator.SAMPLE_STRATEGIES
        ]

    @staticmethod
    def generate_backtest_result(
        strategy_id: str, symbol: str = "SOL/USD"
    ) -> Dict[str, Any]:
        """Generate a sample backtest result"""
        initial_capital = 10000.0
        equity_curve = DemoDataGenerator.generate_equity_curve(
            initial_capital, 252, volatility=0.018, trend=0.0006
        )
        metrics = DemoDataGenerator.calculate_metrics(equity_curve)

        start_date = datetime.utcnow() - timedelta(days=365)
        end_date = datetime.utcnow()

        return {
            "backtest_id": f"bt_{strategy_id}_{datetime.utcnow().timestamp()}",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timeframe": "1d",
            "initial_capital": initial_capital,
            "final_capital": equity_curve[-1],
            "created_at": datetime.utcnow().isoformat(),
            **metrics,
            "equity_curve": [round(e, 2) for e in equity_curve],
            "trades": [
                {
                    "entry_date": (start_date + timedelta(days=random.randint(10, 300))).isoformat(),
                    "entry_price": round(random.uniform(80, 150), 2),
                    "exit_date": (start_date + timedelta(days=random.randint(11, 310))).isoformat(),
                    "exit_price": round(random.uniform(80, 150), 2),
                    "side": random.choice(["BUY", "SELL"]),
                    "size": round(random.uniform(0.5, 10), 2),
                    "pnl": round(random.uniform(-500, 2000), 2),
                }
                for _ in range(metrics["total_trades"])
            ],
        }
