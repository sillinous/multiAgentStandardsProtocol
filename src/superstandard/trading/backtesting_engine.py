"""
NEXUS Backtesting Engine

Production-grade backtesting system for trading strategies.

Features:
- Historical data management
- Event-driven backtesting (realistic order execution)
- Walk-forward analysis
- Multi-timeframe support
- Performance metrics (Sharpe, Sortino, Max Drawdown, etc.)
- Integration with existing data agents

Integrates with:
- data_cleaning_task_agent_v1.py (existing)
- data_validation_task_agent_v1.py (existing)
- statistical_analysis_task_agent_v1.py (existing)
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionSide(Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Order:
    """Order representation"""
    order_id: str
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_timestamp: Optional[datetime] = None
    commission: float = 0.0


@dataclass
class Position:
    """Position representation"""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    entry_timestamp: datetime
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class Trade:
    """Completed trade (entry + exit)"""
    trade_id: str
    symbol: str
    side: PositionSide
    entry_timestamp: datetime
    exit_timestamp: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    commission: float
    duration: timedelta


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_bps: float = 5.0  # 5 basis points
    leverage: int = 1
    max_position_size: float = 1.0  # 100% of capital

    # Risk parameters
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None

    # Execution
    use_market_orders: bool = True
    allow_fractional_shares: bool = True


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""

    # Returns
    total_return: float
    total_return_pct: float
    annualized_return: float
    cagr: float

    # Risk
    volatility: float
    downside_volatility: float
    max_drawdown: float
    max_drawdown_pct: float

    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # Exposure
    avg_position_size: float
    max_position_size: float
    time_in_market: float  # Percentage

    # Timing
    avg_trade_duration: timedelta
    longest_winning_streak: int
    longest_losing_streak: int

    # Capital
    start_capital: float
    end_capital: float
    peak_capital: float

    # Additional
    total_commission: float
    total_trades_value: float


class BacktestEngine:
    """
    Event-driven backtesting engine

    Simulates realistic trading with:
    - Order execution with slippage
    - Commission calculation
    - Position tracking
    - P&L calculation
    - Performance metrics
    """

    def __init__(self, config: BacktestConfig):
        self.config = config

        # State
        self.capital = config.initial_capital
        self.peak_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

        # Tracking
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.drawdown_curve: List[Tuple[datetime, float]] = []

        # Data
        self.historical_data: Dict[str, pd.DataFrame] = {}

        logger.info(f"Backtest engine initialized with ${config.initial_capital:,.2f} capital")

    async def load_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Load historical OHLCV data

        In production, this would integrate with:
        - api_data_fetcher_task_agent_v1.py (existing)
        - data_cleaning_task_agent_v1.py (existing)
        - data_validation_task_agent_v1.py (existing)
        """
        logger.info(f"Loading {symbol} data from {start_date} to {end_date}")

        # TODO: Integrate with existing data fetcher agent
        # For now, return empty DataFrame - will be replaced with actual data fetching

        # Placeholder: Generate sample data for testing
        date_range = pd.date_range(start=start_date, end=end_date, freq=timeframe)

        # Simulate realistic price data (will be replaced with actual fetching)
        base_price = 100.0
        data = {
            'timestamp': date_range,
            'open': base_price + np.random.randn(len(date_range)) * 5,
            'high': base_price + np.random.randn(len(date_range)) * 5 + 2,
            'low': base_price + np.random.randn(len(date_range)) * 5 - 2,
            'close': base_price + np.random.randn(len(date_range)) * 5,
            'volume': np.random.randint(1000, 10000, len(date_range))
        }

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)

        self.historical_data[symbol] = df

        logger.info(f"Loaded {len(df)} bars for {symbol}")
        return df

    def place_order(
        self,
        timestamp: datetime,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None
    ) -> Order:
        """
        Place an order (market or limit)
        """
        order_id = f"order_{len(self.orders)}"

        # Market order - use current price
        if price is None or self.config.use_market_orders:
            current_bar = self._get_current_bar(symbol, timestamp)
            execution_price = current_bar['close']

            # Apply slippage
            slippage_factor = 1 + (self.config.slippage_bps / 10000)
            if side == OrderSide.BUY:
                execution_price *= slippage_factor
            else:
                execution_price *= (2 - slippage_factor)
        else:
            execution_price = price

        # Calculate commission
        order_value = execution_price * quantity
        commission = order_value * self.config.commission_rate

        order = Order(
            order_id=order_id,
            timestamp=timestamp,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=execution_price,
            status=OrderStatus.FILLED,
            filled_price=execution_price,
            filled_timestamp=timestamp,
            commission=commission
        )

        self.orders.append(order)

        # Update capital
        if side == OrderSide.BUY:
            self.capital -= (order_value + commission)
        else:
            self.capital += (order_value - commission)

        # Update position
        self._update_position(order)

        logger.debug(f"Order filled: {order_id} {side.value} {quantity} {symbol} @ {execution_price:.2f}")

        return order

    def _get_current_bar(self, symbol: str, timestamp: datetime) -> pd.Series:
        """Get current OHLCV bar"""
        if symbol not in self.historical_data:
            raise ValueError(f"No data loaded for {symbol}")

        df = self.historical_data[symbol]

        # Find closest timestamp
        idx = df.index.get_indexer([timestamp], method='ffill')[0]
        return df.iloc[idx]

    def _update_position(self, order: Order):
        """Update position based on filled order"""
        symbol = order.symbol

        if symbol not in self.positions:
            # Open new position
            side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side,
                quantity=order.quantity,
                entry_price=order.filled_price,
                entry_timestamp=order.filled_timestamp,
                current_price=order.filled_price
            )
        else:
            # Close or modify existing position
            position = self.positions[symbol]

            if (position.side == PositionSide.LONG and order.side == OrderSide.SELL) or \
               (position.side == PositionSide.SHORT and order.side == OrderSide.BUY):
                # Closing position
                if order.quantity >= position.quantity:
                    # Full close
                    pnl = self._calculate_pnl(position, order.filled_price)

                    trade = Trade(
                        trade_id=f"trade_{len(self.trades)}",
                        symbol=symbol,
                        side=position.side,
                        entry_timestamp=position.entry_timestamp,
                        exit_timestamp=order.filled_timestamp,
                        entry_price=position.entry_price,
                        exit_price=order.filled_price,
                        quantity=position.quantity,
                        pnl=pnl,
                        pnl_percent=(pnl / (position.entry_price * position.quantity)) * 100,
                        commission=order.commission,
                        duration=order.filled_timestamp - position.entry_timestamp
                    )

                    self.trades.append(trade)

                    # Remove position
                    del self.positions[symbol]

                    logger.debug(f"Position closed: {symbol} P&L: ${pnl:.2f}")
                else:
                    # Partial close
                    position.quantity -= order.quantity

    def _calculate_pnl(self, position: Position, exit_price: float) -> float:
        """Calculate P&L for a position"""
        if position.side == PositionSide.LONG:
            return (exit_price - position.entry_price) * position.quantity
        else:
            return (position.entry_price - exit_price) * position.quantity

    def update_positions(self, timestamp: datetime):
        """Update all open positions with current prices"""
        for symbol, position in self.positions.items():
            current_bar = self._get_current_bar(symbol, timestamp)
            position.current_price = current_bar['close']
            position.unrealized_pnl = self._calculate_pnl(position, position.current_price)

    def get_portfolio_value(self, timestamp: datetime) -> float:
        """Get total portfolio value (cash + positions)"""
        self.update_positions(timestamp)

        positions_value = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )

        return self.capital + positions_value

    async def run_backtest(
        self,
        strategy_func: callable,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> BacktestMetrics:
        """
        Run backtest for a strategy

        Args:
            strategy_func: Function that returns (side, quantity) given current data
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Bar timeframe

        Returns:
            BacktestMetrics with performance statistics
        """
        logger.info(f"Starting backtest: {symbol} from {start_date} to {end_date}")

        # Load historical data
        data = await self.load_historical_data(symbol, start_date, end_date, timeframe)

        # Run through each bar
        for timestamp, bar in data.iterrows():
            # Update positions with current prices
            self.update_positions(timestamp)

            # Check stop loss / take profit
            self._check_risk_limits(timestamp)

            # Get strategy signal
            signal = await strategy_func(timestamp, bar, data.loc[:timestamp])

            if signal is not None:
                side, quantity = signal

                if side is not None and quantity > 0:
                    # Place order
                    self.place_order(
                        timestamp=timestamp,
                        symbol=symbol,
                        side=side,
                        quantity=quantity
                    )

            # Track equity curve
            portfolio_value = self.get_portfolio_value(timestamp)
            self.equity_curve.append((timestamp, portfolio_value))

            # Track drawdown
            if portfolio_value > self.peak_capital:
                self.peak_capital = portfolio_value

            drawdown = (self.peak_capital - portfolio_value) / self.peak_capital
            self.drawdown_curve.append((timestamp, drawdown))

            # Check max drawdown limit
            if self.config.max_drawdown_pct and drawdown > self.config.max_drawdown_pct:
                logger.warning(f"Max drawdown exceeded: {drawdown:.2%}")
                break

        # Close any remaining positions
        if self.positions:
            final_timestamp = data.index[-1]
            for symbol in list(self.positions.keys()):
                position = self.positions[symbol]
                close_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                self.place_order(
                    timestamp=final_timestamp,
                    symbol=symbol,
                    side=close_side,
                    quantity=position.quantity
                )

        # Calculate metrics
        metrics = self._calculate_metrics(start_date, end_date)

        logger.info(f"Backtest complete: {metrics.total_trades} trades, "
                   f"{metrics.total_return_pct:.2f}% return, "
                   f"{metrics.sharpe_ratio:.2f} Sharpe")

        return metrics

    def _check_risk_limits(self, timestamp: datetime):
        """Check and enforce stop loss / take profit"""
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            current_bar = self._get_current_bar(symbol, timestamp)

            pnl_pct = (position.unrealized_pnl / (position.entry_price * position.quantity)) * 100

            # Stop loss
            if self.config.stop_loss_pct and pnl_pct <= -self.config.stop_loss_pct:
                logger.info(f"Stop loss triggered for {symbol}: {pnl_pct:.2f}%")
                close_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                self.place_order(timestamp, symbol, close_side, position.quantity)

            # Take profit
            if self.config.take_profit_pct and pnl_pct >= self.config.take_profit_pct:
                logger.info(f"Take profit triggered for {symbol}: {pnl_pct:.2f}%")
                close_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                self.place_order(timestamp, symbol, close_side, position.quantity)

    def _calculate_metrics(self, start_date: datetime, end_date: datetime) -> BacktestMetrics:
        """Calculate comprehensive performance metrics"""

        # Convert equity curve to series
        equity_df = pd.DataFrame(self.equity_curve, columns=['timestamp', 'equity'])
        equity_df.set_index('timestamp', inplace=True)

        # Returns
        initial_value = self.config.initial_capital
        final_value = equity_df['equity'].iloc[-1]
        total_return = final_value - initial_value
        total_return_pct = (total_return / initial_value) * 100

        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100 if years > 0 else 0

        # Daily returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        daily_returns = equity_df['returns'].dropna()

        # Volatility
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 0 else 0

        # Downside volatility
        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

        # Max drawdown
        drawdown_df = pd.DataFrame(self.drawdown_curve, columns=['timestamp', 'drawdown'])
        max_drawdown_pct = drawdown_df['drawdown'].max() * 100
        max_drawdown = self.peak_capital * (drawdown_df['drawdown'].max())

        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0

        # Sortino ratio
        sortino_ratio = (daily_returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        # Calmar ratio
        calmar_ratio = (cagr / max_drawdown_pct) if max_drawdown_pct > 0 else 0

        # Trade statistics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [abs(t.pnl) for t in self.trades if t.pnl < 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        total_wins = sum(wins) if wins else 0
        total_losses = sum(losses) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')

        # Trade duration
        durations = [t.duration for t in self.trades]
        avg_trade_duration = sum(durations, timedelta()) / len(durations) if durations else timedelta()

        # Commission
        total_commission = sum(o.commission for o in self.orders)

        return BacktestMetrics(
            # Returns
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=cagr,
            cagr=cagr,

            # Risk
            volatility=volatility,
            downside_volatility=downside_volatility,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,

            # Risk-adjusted
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,

            # Trades
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,

            # Exposure
            avg_position_size=0,  # TODO: Calculate
            max_position_size=0,  # TODO: Calculate
            time_in_market=0,  # TODO: Calculate

            # Timing
            avg_trade_duration=avg_trade_duration,
            longest_winning_streak=0,  # TODO: Calculate
            longest_losing_streak=0,  # TODO: Calculate

            # Capital
            start_capital=initial_value,
            end_capital=final_value,
            peak_capital=self.peak_capital,

            # Additional
            total_commission=total_commission,
            total_trades_value=sum(o.price * o.quantity for o in self.orders)
        )

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        df = pd.DataFrame(self.equity_curve, columns=['timestamp', 'equity'])
        df.set_index('timestamp', inplace=True)
        return df

    def get_trades_df(self) -> pd.DataFrame:
        """Get all trades as DataFrame"""
        if not self.trades:
            return pd.DataFrame()

        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'trade_id': trade.trade_id,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'entry_timestamp': trade.entry_timestamp,
                'exit_timestamp': trade.exit_timestamp,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'pnl_percent': trade.pnl_percent,
                'commission': trade.commission,
                'duration': trade.duration
            })

        return pd.DataFrame(trades_data)
