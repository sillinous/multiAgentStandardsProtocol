"""
NEXUS Paper Trading Simulator

Simulates trading in real-time with virtual capital, enabling risk-free strategy testing.

Features:
- Virtual portfolio with simulated capital
- Real-time order execution at market prices
- Position tracking and management
- P&L calculation
- Order history and trade log
- Performance metrics
- Integration with live market data

Use Cases:
- Test strategies before live trading
- Forward-test backtested strategies
- Train traders without financial risk
- Validate AI-generated strategies in real market conditions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json


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
    """Trading order"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: Optional[float] = None  # Market order if None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: str = ""
    filled_at: Optional[str] = None
    commission: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class Position:
    """Trading position"""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_commission: float = 0.0


@dataclass
class Portfolio:
    """Trading portfolio"""
    portfolio_id: str
    initial_capital: float
    cash: float
    equity: float
    positions: Dict[str, Position]
    open_orders: List[Order]
    order_history: List[Order]
    total_pnl: float = 0.0
    total_commission: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class PaperTradingEngine:
    """
    Paper trading engine for simulated trading

    Simulates order execution and portfolio management without real capital.
    """

    def __init__(
        self,
        portfolio_id: str,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001  # 0.1%
    ):
        """
        Initialize paper trading engine

        Args:
            portfolio_id: Unique portfolio identifier
            initial_capital: Starting virtual capital
            commission_rate: Commission per trade (as decimal)
        """
        self.portfolio_id = portfolio_id
        self.commission_rate = commission_rate

        # Initialize portfolio
        self.portfolio = Portfolio(
            portfolio_id=portfolio_id,
            initial_capital=initial_capital,
            cash=initial_capital,
            equity=initial_capital,
            positions={},
            open_orders=[],
            order_history=[]
        )

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None,
        order_id: Optional[str] = None
    ) -> Order:
        """
        Place a trading order

        Args:
            symbol: Trading symbol
            side: Buy or sell
            quantity: Order quantity
            price: Limit price (None for market order)
            order_id: Optional order ID (auto-generated if not provided)

        Returns:
            Order object
        """
        if not order_id:
            order_id = f"order_{datetime.utcnow().timestamp()}"

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price
        )

        self.portfolio.open_orders.append(order)
        self.portfolio.updated_at = datetime.utcnow().isoformat()

        return order

    def execute_order(
        self,
        order_id: str,
        market_price: float
    ) -> bool:
        """
        Execute an order at market price

        Args:
            order_id: Order to execute
            market_price: Current market price

        Returns:
            True if executed, False otherwise
        """
        # Find order
        order = None
        for o in self.portfolio.open_orders:
            if o.order_id == order_id:
                order = o
                break

        if not order:
            return False

        # Check if limit price is acceptable (if limit order)
        if order.price is not None:
            if order.side == OrderSide.BUY and market_price > order.price:
                return False  # Price too high for buy
            if order.side == OrderSide.SELL and market_price < order.price:
                return False  # Price too low for sell

        # Calculate order value and commission
        order_value = order.quantity * market_price
        commission = order_value * self.commission_rate

        # Check if sufficient cash for buy orders
        if order.side == OrderSide.BUY:
            total_cost = order_value + commission
            if total_cost > self.portfolio.cash:
                order.status = OrderStatus.REJECTED
                self.portfolio.open_orders.remove(order)
                self.portfolio.order_history.append(order)
                return False

        # Execute order
        order.filled_price = market_price
        order.filled_quantity = order.quantity
        order.commission = commission
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.utcnow().isoformat()

        # Update portfolio
        self._update_portfolio(order)

        # Move to history
        self.portfolio.open_orders.remove(order)
        self.portfolio.order_history.append(order)
        self.portfolio.updated_at = datetime.utcnow().isoformat()

        return True

    def _update_portfolio(self, order: Order):
        """Update portfolio after order execution"""
        symbol = order.symbol

        if order.side == OrderSide.BUY:
            # Deduct cash
            total_cost = (order.filled_quantity * order.filled_price) + order.commission
            self.portfolio.cash -= total_cost
            self.portfolio.total_commission += order.commission

            # Update or create position
            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                # Average entry price calculation
                total_qty = pos.quantity + order.filled_quantity
                total_value = (pos.quantity * pos.entry_price) + (order.filled_quantity * order.filled_price)
                pos.quantity = total_qty
                pos.entry_price = total_value / total_qty
                pos.total_commission += order.commission
            else:
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    side=PositionSide.LONG,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    current_price=order.filled_price,
                    total_commission=order.commission
                )

        elif order.side == OrderSide.SELL:
            # Add cash
            total_proceeds = (order.filled_quantity * order.filled_price) - order.commission
            self.portfolio.cash += total_proceeds
            self.portfolio.total_commission += order.commission

            # Update position
            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]

                # Calculate realized P&L
                realized_pnl = (order.filled_price - pos.entry_price) * order.filled_quantity
                pos.realized_pnl += realized_pnl
                self.portfolio.total_pnl += realized_pnl

                # Reduce position
                pos.quantity -= order.filled_quantity
                pos.total_commission += order.commission

                # Remove position if fully closed
                if pos.quantity <= 0.0001:  # Account for floating point
                    del self.portfolio.positions[symbol]
            else:
                # Short selling - create short position
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    side=PositionSide.SHORT,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    current_price=order.filled_price,
                    total_commission=order.commission
                )

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current market prices and recalculate P&L

        Args:
            prices: Dictionary of symbol -> current price
        """
        for symbol, price in prices.items():
            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                pos.current_price = price

                # Calculate unrealized P&L
                if pos.side == PositionSide.LONG:
                    pos.unrealized_pnl = (price - pos.entry_price) * pos.quantity
                elif pos.side == PositionSide.SHORT:
                    pos.unrealized_pnl = (pos.entry_price - price) * pos.quantity

        # Update equity
        self.portfolio.equity = self.portfolio.cash + sum(
            pos.unrealized_pnl + (pos.quantity * pos.current_price)
            for pos in self.portfolio.positions.values()
            if pos.side == PositionSide.LONG
        ) + sum(
            pos.unrealized_pnl
            for pos in self.portfolio.positions.values()
            if pos.side == PositionSide.SHORT
        )

        self.portfolio.updated_at = datetime.utcnow().isoformat()

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order

        Args:
            order_id: Order to cancel

        Returns:
            True if cancelled, False if not found
        """
        for order in self.portfolio.open_orders:
            if order.order_id == order_id:
                order.status = OrderStatus.CANCELLED
                self.portfolio.open_orders.remove(order)
                self.portfolio.order_history.append(order)
                self.portfolio.updated_at = datetime.utcnow().isoformat()
                return True
        return False

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for symbol"""
        return self.portfolio.positions.get(symbol)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with metrics"""
        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.portfolio.positions.values()
        )

        total_return = self.portfolio.equity - self.portfolio.initial_capital
        total_return_pct = (total_return / self.portfolio.initial_capital) * 100

        return {
            "portfolio_id": self.portfolio.portfolio_id,
            "initial_capital": self.portfolio.initial_capital,
            "cash": self.portfolio.cash,
            "equity": self.portfolio.equity,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "total_pnl": self.portfolio.total_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "realized_pnl": self.portfolio.total_pnl,
            "total_commission": self.portfolio.total_commission,
            "positions_count": len(self.portfolio.positions),
            "open_orders_count": len(self.portfolio.open_orders),
            "total_trades": len(self.portfolio.order_history),
            "created_at": self.portfolio.created_at,
            "updated_at": self.portfolio.updated_at
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        return [
            {
                "symbol": pos.symbol,
                "side": pos.side.value,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "realized_pnl": pos.realized_pnl,
                "total_commission": pos.total_commission,
                "pnl_pct": (pos.unrealized_pnl / (pos.entry_price * pos.quantity)) * 100
            }
            for pos in self.portfolio.positions.values()
        ]

    def get_order_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history"""
        orders = sorted(
            self.portfolio.order_history,
            key=lambda o: o.created_at,
            reverse=True
        )[:limit]

        return [
            {
                "order_id": o.order_id,
                "symbol": o.symbol,
                "side": o.side.value,
                "quantity": o.quantity,
                "price": o.price,
                "filled_price": o.filled_price,
                "filled_quantity": o.filled_quantity,
                "status": o.status.value,
                "commission": o.commission,
                "created_at": o.created_at,
                "filled_at": o.filled_at
            }
            for o in orders
        ]

    def reset_portfolio(self):
        """Reset portfolio to initial state"""
        self.portfolio = Portfolio(
            portfolio_id=self.portfolio_id,
            initial_capital=self.portfolio.initial_capital,
            cash=self.portfolio.initial_capital,
            equity=self.portfolio.initial_capital,
            positions={},
            open_orders=[],
            order_history=[]
        )


# Global portfolio storage (production would use database)
_portfolios: Dict[str, PaperTradingEngine] = {}


def get_or_create_portfolio(
    portfolio_id: str,
    initial_capital: float = 10000.0
) -> PaperTradingEngine:
    """Get existing portfolio or create new one"""
    if portfolio_id not in _portfolios:
        _portfolios[portfolio_id] = PaperTradingEngine(portfolio_id, initial_capital)
    return _portfolios[portfolio_id]


def delete_portfolio(portfolio_id: str) -> bool:
    """Delete portfolio"""
    if portfolio_id in _portfolios:
        del _portfolios[portfolio_id]
        return True
    return False
