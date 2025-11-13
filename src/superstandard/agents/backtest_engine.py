"""
Backtesting Engine for Trading Strategies
==========================================

Simulates trading strategies on historical data to evaluate performance
before production deployment.

Features:
- Multi-timeframe backtesting
- Complete trade log with entry/exit prices
- Performance metrics (win rate, Sharpe ratio, max drawdown)
- Equity curve generation
- Position sizing and risk management
- Commission and slippage modeling
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import random


# ============================================================================
# Market Data Types
# ============================================================================

@dataclass
class MarketBar:
    """OHLCV market data bar"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Trade:
    """Executed trade record"""
    trade_id: int
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: Optional[float]
    size: float
    pnl: Optional[float]
    pnl_percent: Optional[float]
    commission: float
    slippage: float
    status: str  # 'open' or 'closed'


@dataclass
class BacktestConfig:
    """Configuration for backtest execution"""
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    position_size: float = 1.0  # Fraction of capital per trade
    use_voting: bool = False
    voting_threshold: float = 0.6


@dataclass
class BacktestMetrics:
    """Performance metrics from backtest"""
    total_return: float
    total_return_percent: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    profit_factor: float
    avg_trade_duration: float  # In hours
    final_equity: float


@dataclass
class BacktestResult:
    """Complete backtest results"""
    backtest_id: str
    config: BacktestConfig
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]]
    trades: List[Trade]
    decision_log: List[Dict[str, Any]]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


# ============================================================================
# Historical Data Generator
# ============================================================================

class HistoricalDataGenerator:
    """
    Generates synthetic historical market data for backtesting.

    In production, this would be replaced with real historical data
    from exchanges, data providers, or databases.
    """

    @staticmethod
    def generate_price_data(
        start_date: datetime,
        end_date: datetime,
        initial_price: float = 100.0,
        volatility: float = 0.02
    ) -> List[MarketBar]:
        """
        Generate synthetic OHLCV data with realistic patterns.

        Args:
            start_date: Start of backtest period
            end_date: End of backtest period
            initial_price: Starting price
            volatility: Daily volatility factor

        Returns:
            List of MarketBar objects
        """
        bars = []
        current_date = start_date
        current_price = initial_price

        while current_date <= end_date:
            # Generate daily bar with trend and noise
            trend = random.uniform(-volatility, volatility)
            open_price = current_price

            # Intraday volatility
            high_price = open_price * (1 + abs(random.gauss(0, volatility)))
            low_price = open_price * (1 - abs(random.gauss(0, volatility)))
            close_price = open_price * (1 + trend)

            # Ensure OHLC consistency
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            volume = random.uniform(1000000, 10000000)

            bars.append(MarketBar(
                timestamp=current_date,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            ))

            current_price = close_price
            current_date += timedelta(hours=1)  # Hourly bars

        return bars


# ============================================================================
# Backtesting Engine
# ============================================================================

class BacktestEngine:
    """
    Core backtesting engine that simulates trading strategies on historical data.

    Features:
    - Position management (long/short)
    - Commission and slippage modeling
    - Equity curve tracking
    - Trade logging
    - Performance metrics calculation
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.equity = config.initial_capital
        self.equity_curve = []
        self.trades = []
        self.decision_log = []
        self.current_position = None
        self.trade_id_counter = 0

    def run(
        self,
        ensemble,
        historical_data: List[MarketBar]
    ) -> BacktestResult:
        """
        Execute backtest on historical data using ensemble.

        Args:
            ensemble: AgentEnsemble to test
            historical_data: List of MarketBar objects

        Returns:
            BacktestResult with complete metrics and logs
        """
        start_time = datetime.now()

        # Initialize
        self.equity = self.config.initial_capital
        self.equity_curve = []
        self.trades = []
        self.decision_log = []
        self.current_position = None

        # Simulate trading
        for i, bar in enumerate(historical_data):
            # Get price history for agent decision
            lookback = 50
            bar_history = historical_data[max(0, i - lookback):i + 1]
            price_history = [b.close for b in bar_history]

            if len(price_history) < 20:
                continue

            # Get ensemble decision
            decision, metadata = ensemble.get_decision(
                bar,
                price_history,
                bar_history=bar_history
            )

            # Log decision
            self.decision_log.append({
                'timestamp': bar.timestamp.isoformat(),
                'decision': decision,
                'price': bar.close,
                'regime': metadata.get('regime'),
                'confidence': metadata.get('confidence', 0.0)
            })

            # Execute decision
            self._execute_decision(decision, bar)

            # Update equity curve
            current_equity = self._calculate_equity(bar)
            self.equity_curve.append({
                'timestamp': bar.timestamp.isoformat(),
                'equity': current_equity,
                'drawdown': self._calculate_drawdown()
            })

        # Close any open positions
        if self.current_position:
            self._close_position(historical_data[-1])

        # Calculate metrics
        metrics = self._calculate_metrics()

        end_time = datetime.now()

        return BacktestResult(
            backtest_id=f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            config=self.config,
            metrics=metrics,
            equity_curve=self.equity_curve,
            trades=self.trades,
            decision_log=self.decision_log,
            started_at=start_time,
            completed_at=end_time,
            duration_seconds=(end_time - start_time).total_seconds()
        )

    def _execute_decision(self, decision: str, bar: MarketBar):
        """Execute trading decision with position management"""

        if decision == 'buy' and not self.current_position:
            self._open_long_position(bar)

        elif decision == 'sell' and not self.current_position:
            self._open_short_position(bar)

        elif decision == 'sell' and self.current_position and self.current_position.direction == 'long':
            self._close_position(bar)

        elif decision == 'buy' and self.current_position and self.current_position.direction == 'short':
            self._close_position(bar)

    def _open_long_position(self, bar: MarketBar):
        """Open a long position"""
        entry_price = bar.close * (1 + self.config.slippage_rate)  # Slippage
        position_value = self.equity * self.config.position_size
        size = position_value / entry_price
        commission = position_value * self.config.commission_rate

        self.trade_id_counter += 1
        self.current_position = Trade(
            trade_id=self.trade_id_counter,
            entry_time=bar.timestamp,
            exit_time=None,
            direction='long',
            entry_price=entry_price,
            exit_price=None,
            size=size,
            pnl=None,
            pnl_percent=None,
            commission=commission,
            slippage=entry_price - bar.close,
            status='open'
        )

        self.equity -= commission

    def _open_short_position(self, bar: MarketBar):
        """Open a short position"""
        entry_price = bar.close * (1 - self.config.slippage_rate)  # Slippage
        position_value = self.equity * self.config.position_size
        size = position_value / entry_price
        commission = position_value * self.config.commission_rate

        self.trade_id_counter += 1
        self.current_position = Trade(
            trade_id=self.trade_id_counter,
            entry_time=bar.timestamp,
            exit_time=None,
            direction='short',
            entry_price=entry_price,
            exit_price=None,
            size=size,
            pnl=None,
            pnl_percent=None,
            commission=commission,
            slippage=bar.close - entry_price,
            status='open'
        )

        self.equity -= commission

    def _close_position(self, bar: MarketBar):
        """Close the current position"""
        if not self.current_position:
            return

        if self.current_position.direction == 'long':
            exit_price = bar.close * (1 - self.config.slippage_rate)
            pnl = (exit_price - self.current_position.entry_price) * self.current_position.size
        else:  # short
            exit_price = bar.close * (1 + self.config.slippage_rate)
            pnl = (self.current_position.entry_price - exit_price) * self.current_position.size

        exit_commission = exit_price * self.current_position.size * self.config.commission_rate
        pnl -= (self.current_position.commission + exit_commission)

        self.current_position.exit_time = bar.timestamp
        self.current_position.exit_price = exit_price
        self.current_position.pnl = pnl
        self.current_position.pnl_percent = (pnl / (self.current_position.entry_price * self.current_position.size)) * 100
        self.current_position.status = 'closed'
        self.current_position.commission += exit_commission

        self.equity += pnl
        self.trades.append(self.current_position)
        self.current_position = None

    def _calculate_equity(self, bar: MarketBar) -> float:
        """Calculate current equity including open positions"""
        equity = self.equity

        if self.current_position:
            if self.current_position.direction == 'long':
                unrealized_pnl = (bar.close - self.current_position.entry_price) * self.current_position.size
            else:
                unrealized_pnl = (self.current_position.entry_price - bar.close) * self.current_position.size

            equity += unrealized_pnl

        return equity

    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if not self.equity_curve:
            return 0.0

        peak_equity = max(e['equity'] for e in self.equity_curve)
        current_equity = self.equity_curve[-1]['equity']

        drawdown = ((current_equity - peak_equity) / peak_equity) * 100
        return drawdown

    def _calculate_metrics(self) -> BacktestMetrics:
        """Calculate comprehensive performance metrics"""

        if not self.trades:
            return BacktestMetrics(
                total_return=0.0,
                total_return_percent=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                average_win=0.0,
                average_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                avg_trade_duration=0.0,
                final_equity=self.equity
            )

        # Basic metrics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]

        total_return = self.equity - self.config.initial_capital
        total_return_percent = (total_return / self.config.initial_capital) * 100

        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0.0

        average_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        average_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0.0

        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)

        # Drawdown
        max_drawdown_percent = min((e['drawdown'] for e in self.equity_curve), default=0.0)
        peak_equity = max(e['equity'] for e in self.equity_curve)
        max_drawdown = peak_equity * (abs(max_drawdown_percent) / 100)

        # Sharpe ratio (simplified)
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i]['equity'] - self.equity_curve[i-1]['equity']) / self.equity_curve[i-1]['equity']
            returns.append(ret)

        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in self.trades if t.exit_time]
        avg_trade_duration = sum(durations) / len(durations) if durations else 0.0

        return BacktestMetrics(
            total_return=total_return,
            total_return_percent=total_return_percent,
            win_rate=win_rate,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_drawdown=max_drawdown,
            max_drawdown_percent=abs(max_drawdown_percent),
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            avg_trade_duration=avg_trade_duration,
            final_equity=self.equity
        )
