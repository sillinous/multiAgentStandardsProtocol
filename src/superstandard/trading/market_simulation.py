"""
Market Simulation Engine - Realistic Synthetic Market Data Generation

This module provides comprehensive market simulation capabilities for testing
and training trading agents. It generates realistic synthetic market data with
various regimes, events, and statistical properties found in real markets.

Features:
- Multiple market regimes (bull, bear, volatile, sideways, crash, recovery)
- Realistic statistical properties (fat tails, volatility clustering, momentum)
- Event injection (news shocks, volatility spikes, trend reversals)
- Agent backtesting framework with performance metrics
- Integration with genetic breeding for agent evolution

Author: Agentic Forge
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
import random
import math


# ============================================================================
# Market Data Structures
# ============================================================================

@dataclass
class MarketBar:
    """OHLCV market bar - standard candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def midpoint(self) -> float:
        """Get midpoint price"""
        return (self.high + self.low) / 2.0

    def body_size(self) -> float:
        """Get size of candlestick body"""
        return abs(self.close - self.open)

    def wick_size(self) -> float:
        """Get total wick size"""
        return (self.high - self.low) - self.body_size()

    def is_bullish(self) -> bool:
        """Check if bar is bullish (close > open)"""
        return self.close > self.open

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


class MarketRegime(Enum):
    """Market regime types with characteristic properties"""
    BULL = "bull"                 # Trending up, low-moderate volatility
    BEAR = "bear"                 # Trending down, moderate volatility
    VOLATILE = "volatile"         # High volatility, choppy, no clear trend
    SIDEWAYS = "sideways"         # Range-bound, low volatility
    CRASH = "crash"               # Rapid decline, extreme volatility
    RECOVERY = "recovery"         # Rapid rise after crash, high volatility

    def get_params(self) -> Dict[str, float]:
        """Get regime parameters (drift, volatility, momentum)"""
        params = {
            MarketRegime.BULL: {
                'drift': 0.0008,          # +0.08% per bar average
                'volatility': 0.015,      # 1.5% volatility
                'momentum': 0.15,         # Moderate momentum
                'mean_reversion': 0.05    # Low mean reversion
            },
            MarketRegime.BEAR: {
                'drift': -0.0006,         # -0.06% per bar average
                'volatility': 0.020,      # 2.0% volatility
                'momentum': 0.10,         # Lower momentum
                'mean_reversion': 0.08    # Moderate mean reversion
            },
            MarketRegime.VOLATILE: {
                'drift': 0.0,             # No trend
                'volatility': 0.035,      # 3.5% volatility (high!)
                'momentum': 0.05,         # Low momentum
                'mean_reversion': 0.15    # High mean reversion
            },
            MarketRegime.SIDEWAYS: {
                'drift': 0.0,             # No trend
                'volatility': 0.010,      # 1.0% volatility (low)
                'momentum': 0.03,         # Very low momentum
                'mean_reversion': 0.25    # Very high mean reversion
            },
            MarketRegime.CRASH: {
                'drift': -0.003,          # -0.3% per bar (severe!)
                'volatility': 0.050,      # 5.0% volatility (extreme!)
                'momentum': 0.20,         # High momentum (down)
                'mean_reversion': 0.02    # Very low mean reversion
            },
            MarketRegime.RECOVERY: {
                'drift': 0.002,           # +0.2% per bar (strong!)
                'volatility': 0.030,      # 3.0% volatility
                'momentum': 0.18,         # High momentum (up)
                'mean_reversion': 0.03    # Low mean reversion
            }
        }
        return params[self]


@dataclass
class MarketEvent:
    """Market event (news shock, volatility spike, etc.)"""
    timestamp: datetime
    event_type: str               # 'news_shock', 'volatility_spike', 'trend_reversal'
    magnitude: float              # Impact magnitude (0.0 to 1.0)
    direction: int                # +1 (positive) or -1 (negative)
    description: str

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'magnitude': self.magnitude,
            'direction': self.direction,
            'description': self.description
        }


# ============================================================================
# Market Simulator - Core Engine
# ============================================================================

class MarketSimulator:
    """
    Realistic market data simulator with multiple regimes and events.

    Generates synthetic OHLCV data with realistic statistical properties:
    - Fat tails (extreme events occur more often than normal distribution)
    - Volatility clustering (high volatility periods cluster together)
    - Momentum (trends persist)
    - Mean reversion (prices return to average)
    """

    def __init__(
        self,
        initial_price: float = 100.0,
        timeframe_minutes: int = 60,
        seed: Optional[int] = None
    ):
        self.initial_price = initial_price
        self.timeframe_minutes = timeframe_minutes
        self.bars: List[MarketBar] = []
        self.events: List[MarketEvent] = []
        self.current_regime = MarketRegime.SIDEWAYS

        if seed is not None:
            random.seed(seed)

        # State variables
        self.current_price = initial_price
        self.current_volatility = 0.015  # 1.5% base volatility
        self.regime_bars_remaining = 0

    def set_regime(self, regime: MarketRegime, duration_bars: int):
        """Set market regime for specified duration"""
        self.current_regime = regime
        self.regime_bars_remaining = duration_bars
        print(f"📊 Market regime changed to {regime.value} for {duration_bars} bars")

    def inject_event(
        self,
        event_type: str,
        magnitude: float,
        direction: int,
        description: str
    ) -> MarketEvent:
        """Inject a market event at current time"""
        timestamp = self._get_next_timestamp()
        event = MarketEvent(
            timestamp=timestamp,
            event_type=event_type,
            magnitude=magnitude,
            direction=direction,
            description=description
        )
        self.events.append(event)
        print(f"⚡ Event injected: {description}")
        return event

    def generate_bars(
        self,
        num_bars: int,
        regime: Optional[MarketRegime] = None,
        event_probability: float = 0.02  # 2% chance of event per bar
    ) -> List[MarketBar]:
        """
        Generate synthetic market bars.

        Args:
            num_bars: Number of bars to generate
            regime: Market regime (if None, continues current regime)
            event_probability: Probability of random event per bar

        Returns:
            List of MarketBar objects
        """
        if regime is not None:
            self.set_regime(regime, num_bars)

        generated_bars = []

        for i in range(num_bars):
            # Check if regime should change (if duration expired)
            if self.regime_bars_remaining > 0:
                self.regime_bars_remaining -= 1

            # Random event injection
            if random.random() < event_probability:
                self._inject_random_event()

            # Generate bar
            bar = self._generate_single_bar()
            self.bars.append(bar)
            generated_bars.append(bar)

        return generated_bars

    def _generate_single_bar(self) -> MarketBar:
        """Generate a single market bar with realistic properties"""
        timestamp = self._get_next_timestamp()

        # Get regime parameters
        params = self.current_regime.get_params()
        drift = params['drift']
        base_volatility = params['volatility']
        momentum = params['momentum']
        mean_reversion = params['mean_reversion']

        # Apply volatility clustering (GARCH-like behavior)
        self.current_volatility = (
            0.95 * self.current_volatility +
            0.05 * base_volatility +
            random.gauss(0, 0.002)
        )
        self.current_volatility = max(0.005, min(0.10, self.current_volatility))

        # Calculate price change with fat tails
        # Use student-t distribution for fat tails (extreme events more likely)
        if random.random() < 0.05:  # 5% chance of extreme move
            # Fat tail event - larger move
            price_change_pct = random.gauss(0, self.current_volatility * 2.5)
        else:
            # Normal move
            price_change_pct = random.gauss(0, self.current_volatility)

        # Apply drift (regime trend)
        price_change_pct += drift

        # Apply momentum (trends persist)
        if len(self.bars) > 0:
            last_bar = self.bars[-1]
            last_move = (last_bar.close - last_bar.open) / last_bar.open
            price_change_pct += last_move * momentum

        # Apply mean reversion (pull toward initial price)
        deviation = (self.current_price - self.initial_price) / self.initial_price
        price_change_pct -= deviation * mean_reversion

        # Check for events and apply impact
        event_impact = self._get_event_impact(timestamp)
        price_change_pct += event_impact

        # Calculate OHLC
        open_price = self.current_price
        close_price = open_price * (1 + price_change_pct)

        # Generate high/low with realistic wicks
        range_size = abs(close_price - open_price) * random.uniform(1.2, 2.5)
        wick_top = random.uniform(0, range_size * 0.6)
        wick_bottom = random.uniform(0, range_size * 0.6)

        high_price = max(open_price, close_price) + wick_top
        low_price = min(open_price, close_price) - wick_bottom

        # Generate volume (higher during volatile periods)
        base_volume = 1000000
        volume_multiplier = 1.0 + (self.current_volatility / 0.015)
        if abs(price_change_pct) > 0.02:  # Large move increases volume
            volume_multiplier *= 1.5
        volume = base_volume * volume_multiplier * random.uniform(0.7, 1.3)

        # Update current price
        self.current_price = close_price

        return MarketBar(
            timestamp=timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume
        )

    def _get_next_timestamp(self) -> datetime:
        """Get timestamp for next bar"""
        if len(self.bars) == 0:
            return datetime.now()
        else:
            return self.bars[-1].timestamp + timedelta(minutes=self.timeframe_minutes)

    def _inject_random_event(self):
        """Inject a random market event"""
        event_types = [
            ('news_shock', 'Major news announcement'),
            ('volatility_spike', 'Sudden volatility increase'),
            ('trend_reversal', 'Market trend reversal')
        ]

        event_type, description = random.choice(event_types)
        magnitude = random.uniform(0.3, 0.9)
        direction = random.choice([-1, 1])

        self.inject_event(event_type, magnitude, direction, description)

    def _get_event_impact(self, timestamp: datetime) -> float:
        """Calculate price impact from recent events"""
        impact = 0.0

        # Events have decaying impact over time
        for event in self.events:
            bars_since_event = (timestamp - event.timestamp).total_seconds() / (self.timeframe_minutes * 60)

            if bars_since_event <= 0:  # Current bar
                if event.event_type == 'news_shock':
                    impact += event.magnitude * 0.03 * event.direction
                elif event.event_type == 'volatility_spike':
                    self.current_volatility *= (1 + event.magnitude * 0.5)
                elif event.event_type == 'trend_reversal':
                    impact += event.magnitude * 0.02 * event.direction

        return impact

    def get_price_series(self) -> List[float]:
        """Get close prices as a list"""
        return [bar.close for bar in self.bars]

    def get_returns(self) -> List[float]:
        """Get percentage returns"""
        prices = self.get_price_series()
        if len(prices) < 2:
            return []
        return [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]

    def get_statistics(self) -> Dict[str, float]:
        """Calculate market statistics"""
        if len(self.bars) < 2:
            return {}

        returns = self.get_returns()
        prices = self.get_price_series()

        # Calculate statistics
        avg_return = sum(returns) / len(returns)
        volatility = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5

        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe = (avg_return / volatility) if volatility > 0 else 0.0

        # Max drawdown
        peak = prices[0]
        max_dd = 0.0
        for price in prices:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd

        return {
            'avg_return': avg_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_return': (prices[-1] - prices[0]) / prices[0],
            'num_bars': len(self.bars),
            'num_events': len(self.events)
        }


# ============================================================================
# Agent Backtesting Framework
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    num_trades: int
    profitable_trades: int
    losing_trades: int

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'num_trades': self.num_trades,
            'profitable_trades': self.profitable_trades,
            'losing_trades': self.losing_trades
        }

    def get_fitness_score(self) -> float:
        """
        Calculate overall fitness score for genetic breeding.

        Combines multiple metrics into single score (0.0 to 1.0):
        - Sharpe ratio (40% weight)
        - Total return (30% weight)
        - Win rate (20% weight)
        - Max drawdown penalty (10% weight)
        """
        # Normalize Sharpe (cap at 3.0)
        sharpe_score = min(max(self.sharpe_ratio, -1.0), 3.0) / 3.0

        # Normalize return (cap at ±50%)
        return_score = min(max(self.total_return, -0.5), 0.5) / 0.5

        # Win rate is already 0-1
        win_score = self.win_rate

        # Drawdown penalty (lower is better)
        dd_score = 1.0 - min(self.max_drawdown, 1.0)

        # Weighted combination
        fitness = (
            sharpe_score * 0.40 +
            return_score * 0.30 +
            win_score * 0.20 +
            dd_score * 0.10
        )

        # Scale to 0-1
        return (fitness + 1.0) / 2.0


class AgentBacktester:
    """
    Backtest trading agents on simulated market data.

    Tests agent decision-making against historical or synthetic data
    and calculates comprehensive performance metrics.
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0.0
        self.entry_price = 0.0
        self.trades: List[Dict] = []

    def backtest(
        self,
        market_data: List[MarketBar],
        strategy_func: Callable[[MarketBar, List[MarketBar]], str],
        position_size: float = 1.0
    ) -> PerformanceMetrics:
        """
        Run backtest on market data.

        Args:
            market_data: List of market bars to test on
            strategy_func: Function(current_bar, history) -> 'buy'/'sell'/'hold'
            position_size: Position size as fraction of capital (0.0 to 1.0)

        Returns:
            PerformanceMetrics object
        """
        self.capital = self.initial_capital
        self.position = 0.0
        self.trades = []

        for i, bar in enumerate(market_data):
            history = market_data[:i] if i > 0 else []

            # Get strategy decision
            decision = strategy_func(bar, history)

            # Execute decision
            if decision == 'buy' and self.position == 0.0:
                # Enter long position
                position_value = self.capital * position_size
                self.position = position_value / bar.close
                self.entry_price = bar.close
                self.capital -= position_value

            elif decision == 'sell' and self.position > 0.0:
                # Exit position
                exit_value = self.position * bar.close
                pnl = exit_value - (self.position * self.entry_price)
                self.capital += exit_value

                # Record trade
                self.trades.append({
                    'entry_price': self.entry_price,
                    'exit_price': bar.close,
                    'pnl': pnl,
                    'return': pnl / (self.position * self.entry_price)
                })

                self.position = 0.0

        # Close any open position
        if self.position > 0.0 and len(market_data) > 0:
            last_bar = market_data[-1]
            exit_value = self.position * last_bar.close
            pnl = exit_value - (self.position * self.entry_price)
            self.capital += exit_value

            self.trades.append({
                'entry_price': self.entry_price,
                'exit_price': last_bar.close,
                'pnl': pnl,
                'return': pnl / (self.position * self.entry_price)
            })

            self.position = 0.0

        # Calculate metrics
        return self._calculate_metrics()

    def _calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from trades"""
        if len(self.trades) == 0:
            return PerformanceMetrics(
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                num_trades=0,
                profitable_trades=0,
                losing_trades=0
            )

        # Total return
        total_return = (self.capital - self.initial_capital) / self.initial_capital

        # Win/loss statistics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]

        win_rate = len(winning_trades) / len(self.trades)
        avg_win = sum(t['return'] for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t['return'] for t in losing_trades) / len(losing_trades) if losing_trades else 0.0

        # Sharpe ratio
        returns = [t['return'] for t in self.trades]
        avg_return = sum(returns) / len(returns)
        volatility = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe_ratio = (avg_return / volatility) if volatility > 0 else 0.0

        # Max drawdown
        equity_curve = [self.initial_capital]
        capital = self.initial_capital
        for trade in self.trades:
            capital += trade['pnl']
            equity_curve.append(capital)

        peak = equity_curve[0]
        max_dd = 0.0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        return PerformanceMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_dd,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            num_trades=len(self.trades),
            profitable_trades=len(winning_trades),
            losing_trades=len(losing_trades)
        )
