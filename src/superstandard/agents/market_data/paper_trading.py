"""
Paper Trading Integration for Agent Ensembles

Connects AgentEnsemble decisions to real paper trading via Alpaca API.
Enables live testing of agent strategies in simulated market conditions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from .alpaca_client import AlpacaClient, AlpacaConfig, OrderSide, TimeInForce
from ..agent_ensemble import AgentEnsemble, Decision


logger = logging.getLogger(__name__)


class TradingMode(str, Enum):
    """Trading execution mode"""
    PAPER = "paper"  # Paper trading (simulated)
    LIVE = "live"    # Live trading (real money)


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading"""

    alpaca_config: AlpacaConfig
    mode: TradingMode = TradingMode.PAPER
    position_size_percent: float = 0.1  # Use 10% of portfolio per trade
    max_position_count: int = 5  # Maximum concurrent positions
    stop_loss_percent: Optional[float] = None  # e.g., 0.05 for 5% stop loss
    take_profit_percent: Optional[float] = None  # e.g., 0.10 for 10% take profit
    enable_logging: bool = True

    def __post_init__(self):
        if self.position_size_percent <= 0 or self.position_size_percent > 1:
            raise ValueError("position_size_percent must be between 0 and 1")
        if self.max_position_count <= 0:
            raise ValueError("max_position_count must be positive")


@dataclass
class TradeExecutionResult:
    """Result of trade execution"""

    success: bool
    order_id: Optional[str] = None
    symbol: str = ""
    side: Optional[OrderSide] = None
    quantity: float = 0.0
    price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    message: str = ""


class PaperTradingEngine:
    """
    Paper trading engine for agent ensembles

    Executes agent decisions in paper trading environment, tracking
    performance and managing positions.

    Features:
    - Automatic position sizing based on portfolio value
    - Max position limits
    - Optional stop loss and take profit
    - Real-time performance tracking
    - Integration with AgentEnsemble

    Example:
        config = PaperTradingConfig(
            alpaca_config=AlpacaConfig(),
            position_size_percent=0.1,
            max_position_count=5
        )

        engine = PaperTradingEngine(config)

        # Execute ensemble decision
        decision = ensemble.make_decision(market_data)
        result = engine.execute_decision("AAPL", decision)

        # Get current positions
        positions = engine.get_positions()

        # Get performance metrics
        metrics = engine.get_performance_metrics()
    """

    def __init__(self, config: PaperTradingConfig):
        """Initialize paper trading engine"""
        self.config = config
        self.client = AlpacaClient(config.alpaca_config)

        # Track execution history
        self.execution_history: List[TradeExecutionResult] = []
        self.total_trades: int = 0
        self.successful_trades: int = 0

        logger.info(f"Paper trading engine initialized (mode={config.mode})")

    # ========================================================================
    # Trade Execution
    # ========================================================================

    def execute_decision(
        self,
        symbol: str,
        decision: Decision
    ) -> TradeExecutionResult:
        """
        Execute an agent ensemble decision

        Args:
            symbol: Stock symbol to trade
            decision: Decision from AgentEnsemble

        Returns:
            TradeExecutionResult with execution details
        """
        try:
            # Check if we should trade based on decision confidence
            if decision.action == "hold":
                return TradeExecutionResult(
                    success=True,
                    symbol=symbol,
                    message="Decision is HOLD, no trade executed"
                )

            # Get current account info
            account = self.client.get_account()

            # Check position limits
            current_positions = self.client.get_positions()
            if len(current_positions) >= self.config.max_position_count:
                return TradeExecutionResult(
                    success=False,
                    symbol=symbol,
                    error="Max position count reached",
                    message=f"Already holding {len(current_positions)} positions"
                )

            # Calculate position size
            position_value = account.portfolio_value * self.config.position_size_percent
            current_price = self.client.get_current_price(symbol)
            quantity = int(position_value / current_price)

            if quantity == 0:
                return TradeExecutionResult(
                    success=False,
                    symbol=symbol,
                    error="Insufficient funds",
                    message=f"Calculated quantity is 0 (price=${current_price:.2f})"
                )

            # Determine order side
            if decision.action == "buy":
                side = OrderSide.BUY
            elif decision.action == "sell":
                # Check if we have a position to sell
                position = self.client.get_position(symbol)
                if not position:
                    return TradeExecutionResult(
                        success=False,
                        symbol=symbol,
                        error="No position to sell",
                        message=f"No existing position in {symbol}"
                    )
                side = OrderSide.SELL
                quantity = position.quantity  # Sell entire position
            else:
                return TradeExecutionResult(
                    success=False,
                    symbol=symbol,
                    error="Invalid action",
                    message=f"Unknown action: {decision.action}"
                )

            # Execute market order
            order = self.client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                time_in_force=TimeInForce.DAY
            )

            # Record execution
            result = TradeExecutionResult(
                success=True,
                order_id=order.order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=current_price,
                message=(
                    f"Executed {side.value} order: {quantity} shares @ ${current_price:.2f} "
                    f"(confidence={decision.confidence:.2f})"
                )
            )

            self.execution_history.append(result)
            self.total_trades += 1
            self.successful_trades += 1

            if self.config.enable_logging:
                logger.info(result.message)

            return result

        except Exception as e:
            logger.error(f"Error executing decision: {e}")

            result = TradeExecutionResult(
                success=False,
                symbol=symbol,
                error=str(e),
                message=f"Trade execution failed: {str(e)}"
            )

            self.execution_history.append(result)
            self.total_trades += 1

            return result

    def execute_manual_trade(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float
    ) -> TradeExecutionResult:
        """
        Execute a manual trade (not from ensemble decision)

        Args:
            symbol: Stock symbol
            side: Buy or sell
            quantity: Number of shares

        Returns:
            TradeExecutionResult
        """
        try:
            order = self.client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity
            )

            current_price = self.client.get_current_price(symbol)

            result = TradeExecutionResult(
                success=True,
                order_id=order.order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=current_price,
                message=f"Manual trade: {side.value} {quantity} {symbol}"
            )

            self.execution_history.append(result)
            self.total_trades += 1
            self.successful_trades += 1

            logger.info(result.message)

            return result

        except Exception as e:
            logger.error(f"Error executing manual trade: {e}")

            result = TradeExecutionResult(
                success=False,
                symbol=symbol,
                side=side,
                quantity=quantity,
                error=str(e),
                message=f"Manual trade failed: {str(e)}"
            )

            self.execution_history.append(result)
            self.total_trades += 1

            return result

    # ========================================================================
    # Position Management
    # ========================================================================

    def get_positions(self):
        """Get all current positions"""
        return self.client.get_positions()

    def get_position(self, symbol: str):
        """Get position for specific symbol"""
        return self.client.get_position(symbol)

    def close_position(self, symbol: str) -> bool:
        """Close a position"""
        return self.client.close_position(symbol)

    def close_all_positions(self) -> bool:
        """Close all positions"""
        return self.client.close_all_positions()

    # ========================================================================
    # Performance Tracking
    # ========================================================================

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for paper trading

        Returns:
            Dictionary with performance metrics
        """
        account = self.client.get_account()
        positions = self.client.get_positions()

        # Calculate win rate from execution history
        winning_trades = sum(
            1 for result in self.execution_history
            if result.success and result.side == OrderSide.SELL
        )
        total_closed_trades = sum(
            1 for result in self.execution_history
            if result.success and result.side == OrderSide.SELL
        )
        win_rate = winning_trades / total_closed_trades if total_closed_trades > 0 else 0.0

        # Calculate total P&L from positions
        total_unrealized_pl = sum(pos.unrealized_pl for pos in positions)

        return {
            'account_value': account.portfolio_value,
            'cash': account.cash,
            'equity': account.equity,
            'buying_power': account.buying_power,
            'total_positions': len(positions),
            'total_unrealized_pl': total_unrealized_pl,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.total_trades - self.successful_trades,
            'win_rate': win_rate,
            'success_rate': self.successful_trades / self.total_trades if self.total_trades > 0 else 0.0
        }

    def get_execution_history(
        self,
        limit: Optional[int] = None,
        symbol: Optional[str] = None
    ) -> List[TradeExecutionResult]:
        """
        Get execution history

        Args:
            limit: Maximum number of results
            symbol: Filter by symbol

        Returns:
            List of TradeExecutionResult objects
        """
        history = self.execution_history

        if symbol:
            history = [r for r in history if r.symbol == symbol]

        if limit:
            history = history[-limit:]

        return history

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive account summary

        Returns:
            Dictionary with account details, positions, and performance
        """
        account = self.client.get_account()
        positions = self.client.get_positions()
        metrics = self.get_performance_metrics()

        return {
            'account': {
                'account_id': account.account_id,
                'portfolio_value': account.portfolio_value,
                'cash': account.cash,
                'equity': account.equity,
                'buying_power': account.buying_power
            },
            'positions': [
                {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'side': pos.side.value,
                    'market_value': pos.market_value,
                    'unrealized_pl': pos.unrealized_pl,
                    'unrealized_pl_percent': pos.unrealized_pl_percent,
                    'current_price': pos.current_price
                }
                for pos in positions
            ],
            'performance': metrics,
            'config': {
                'mode': self.config.mode.value,
                'position_size_percent': self.config.position_size_percent,
                'max_position_count': self.config.max_position_count
            }
        }
