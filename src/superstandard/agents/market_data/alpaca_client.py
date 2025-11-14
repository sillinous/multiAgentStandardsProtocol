"""
Alpaca API Integration for Real Market Data and Paper Trading

Provides real-time market data, historical bars, and paper trading capabilities
through Alpaca's API.

Features:
- Real-time market data (bars, trades, quotes)
- Historical data retrieval
- Paper trading (positions, orders, account info)
- Seamless integration with BacktestEngine
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest,
        LimitOrderRequest,
        GetOrdersRequest
    )
    from alpaca.trading.enums import OrderSide as AlpacaOrderSide
    from alpaca.trading.enums import TimeInForce as AlpacaTimeInForce
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning(
        "Alpaca SDK not installed. Run: pip install alpaca-py\n"
        "Market data integration will be disabled."
    )


logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AlpacaConfig:
    """Configuration for Alpaca API client"""

    api_key: str = field(default_factory=lambda: os.getenv('ALPACA_API_KEY', ''))
    api_secret: str = field(default_factory=lambda: os.getenv('ALPACA_API_SECRET', ''))
    paper_trading: bool = field(default_factory=lambda: os.getenv('ALPACA_PAPER', 'true').lower() == 'true')

    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Alpaca API credentials not provided. Set ALPACA_API_KEY and "
                "ALPACA_API_SECRET environment variables."
            )


# ============================================================================
# Market Data Models
# ============================================================================

@dataclass
class MarketDataBar:
    """Market data bar (OHLCV) compatible with BacktestEngine"""

    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_backtest_bar(self):
        """Convert to BacktestEngine MarketBar format"""
        from ..backtest_engine import MarketBar
        return MarketBar(
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume
        )


# ============================================================================
# Trading Models
# ============================================================================

class OrderSide(str, Enum):
    """Order side (buy/sell)"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    """Time in force for orders"""
    DAY = "day"  # Good for day
    GTC = "gtc"  # Good till canceled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


@dataclass
class Order:
    """Trading order"""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    filled_quantity: float
    status: str
    submitted_at: datetime
    filled_at: Optional[datetime] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_avg_price: Optional[float] = None


@dataclass
class Position:
    """Current position in a symbol"""

    symbol: str
    quantity: float
    side: OrderSide
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_pl_percent: float
    current_price: float
    avg_entry_price: float


@dataclass
class AccountInfo:
    """Account information"""

    account_id: str
    cash: float
    portfolio_value: float
    buying_power: float
    equity: float
    long_market_value: float
    short_market_value: float
    initial_margin: float
    maintenance_margin: float
    last_equity: float
    daytrade_count: int


# ============================================================================
# Alpaca Client
# ============================================================================

class AlpacaClient:
    """
    Alpaca API client for real market data and paper trading

    Features:
    - Real-time and historical market data
    - Paper trading capabilities
    - Seamless integration with BacktestEngine

    Example:
        config = AlpacaConfig()
        client = AlpacaClient(config)

        # Get historical data
        bars = client.get_historical_bars("AAPL", days=30)

        # Place paper trade
        order = client.place_market_order("AAPL", OrderSide.BUY, 10)

        # Get positions
        positions = client.get_positions()
    """

    def __init__(self, config: AlpacaConfig):
        """Initialize Alpaca client with configuration"""
        if not ALPACA_AVAILABLE:
            raise ImportError(
                "Alpaca SDK not installed. Install with: pip install alpaca-py"
            )

        self.config = config

        # Initialize trading client
        self.trading_client = TradingClient(
            api_key=config.api_key,
            secret_key=config.api_secret,
            paper=config.paper_trading
        )

        # Initialize data client
        self.data_client = StockHistoricalDataClient(
            api_key=config.api_key,
            secret_key=config.api_secret
        )

        logger.info(
            f"Alpaca client initialized (paper_trading={config.paper_trading})"
        )

    # ========================================================================
    # Market Data Methods
    # ========================================================================

    def get_historical_bars(
        self,
        symbol: str,
        days: int = 30,
        timeframe: str = "1Day"
    ) -> List[MarketDataBar]:
        """
        Fetch historical market data bars

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            days: Number of days of history
            timeframe: Bar timeframe ("1Min", "5Min", "1Hour", "1Day")

        Returns:
            List of MarketDataBar objects
        """
        try:
            # Calculate date range
            end = datetime.now()
            start = end - timedelta(days=days)

            # Map timeframe string to Alpaca TimeFrame
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Min"),
                "15Min": TimeFrame(15, "Min"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }

            tf = timeframe_map.get(timeframe, TimeFrame.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start,
                end=end
            )

            # Fetch data
            bars_response = self.data_client.get_stock_bars(request)

            # Convert to MarketDataBar objects
            bars = []
            if symbol in bars_response.data:
                for bar in bars_response.data[symbol]:
                    bars.append(MarketDataBar(
                        timestamp=bar.timestamp,
                        symbol=symbol,
                        open=float(bar.open),
                        high=float(bar.high),
                        low=float(bar.low),
                        close=float(bar.close),
                        volume=int(bar.volume)
                    ))

            logger.info(f"Fetched {len(bars)} bars for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching historical bars: {e}")
            raise

    def get_latest_bar(self, symbol: str) -> Optional[MarketDataBar]:
        """
        Get the latest market data bar for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Latest MarketDataBar or None
        """
        bars = self.get_historical_bars(symbol, days=1, timeframe="1Min")
        return bars[-1] if bars else None

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Current price
        """
        bar = self.get_latest_bar(symbol)
        if bar:
            return bar.close
        raise ValueError(f"Could not fetch current price for {symbol}")

    # ========================================================================
    # Paper Trading Methods
    # ========================================================================

    def get_account(self) -> AccountInfo:
        """
        Get account information

        Returns:
            AccountInfo with current account state
        """
        try:
            account = self.trading_client.get_account()

            return AccountInfo(
                account_id=account.id,
                cash=float(account.cash),
                portfolio_value=float(account.portfolio_value),
                buying_power=float(account.buying_power),
                equity=float(account.equity),
                long_market_value=float(account.long_market_value),
                short_market_value=float(account.short_market_value),
                initial_margin=float(account.initial_margin),
                maintenance_margin=float(account.maintenance_margin),
                last_equity=float(account.last_equity),
                daytrade_count=account.daytrade_count
            )

        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            raise

    def get_positions(self) -> List[Position]:
        """
        Get all open positions

        Returns:
            List of Position objects
        """
        try:
            positions = self.trading_client.get_all_positions()

            result = []
            for pos in positions:
                result.append(Position(
                    symbol=pos.symbol,
                    quantity=float(pos.qty),
                    side=OrderSide.BUY if float(pos.qty) > 0 else OrderSide.SELL,
                    market_value=float(pos.market_value),
                    cost_basis=float(pos.cost_basis),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_pl_percent=float(pos.unrealized_plpc),
                    current_price=float(pos.current_price),
                    avg_entry_price=float(pos.avg_entry_price)
                ))

            return result

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol

        Args:
            symbol: Stock symbol

        Returns:
            Position or None if no position exists
        """
        try:
            pos = self.trading_client.get_open_position(symbol)

            return Position(
                symbol=pos.symbol,
                quantity=float(pos.qty),
                side=OrderSide.BUY if float(pos.qty) > 0 else OrderSide.SELL,
                market_value=float(pos.market_value),
                cost_basis=float(pos.cost_basis),
                unrealized_pl=float(pos.unrealized_pl),
                unrealized_pl_percent=float(pos.unrealized_plpc),
                current_price=float(pos.current_price),
                avg_entry_price=float(pos.avg_entry_price)
            )

        except Exception:
            return None

    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> Order:
        """
        Place a market order

        Args:
            symbol: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            time_in_force: Order time in force

        Returns:
            Order object
        """
        try:
            # Convert enums to Alpaca enums
            alpaca_side = AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL
            alpaca_tif = getattr(AlpacaTimeInForce, time_in_force.value.upper())

            # Create order request
            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=alpaca_side,
                time_in_force=alpaca_tif
            )

            # Submit order
            order = self.trading_client.submit_order(request)

            logger.info(f"Placed market order: {side.value} {quantity} {symbol}")

            return Order(
                order_id=order.id,
                symbol=order.symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=float(order.qty),
                filled_quantity=float(order.filled_qty) if order.filled_qty else 0.0,
                status=order.status.value,
                submitted_at=order.submitted_at,
                filled_at=order.filled_at,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None
            )

        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: float,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> Order:
        """
        Place a limit order

        Args:
            symbol: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            limit_price: Limit price
            time_in_force: Order time in force

        Returns:
            Order object
        """
        try:
            # Convert enums
            alpaca_side = AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL
            alpaca_tif = getattr(AlpacaTimeInForce, time_in_force.value.upper())

            # Create order request
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                limit_price=limit_price
            )

            # Submit order
            order = self.trading_client.submit_order(request)

            logger.info(
                f"Placed limit order: {side.value} {quantity} {symbol} @ ${limit_price}"
            )

            return Order(
                order_id=order.id,
                symbol=order.symbol,
                side=side,
                order_type=OrderType.LIMIT,
                quantity=float(order.qty),
                filled_quantity=float(order.filled_qty) if order.filled_qty else 0.0,
                status=order.status.value,
                submitted_at=order.submitted_at,
                filled_at=order.filled_at,
                limit_price=limit_price,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None
            )

        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise

    def get_orders(self, status: str = "all") -> List[Order]:
        """
        Get orders with optional status filter

        Args:
            status: Filter by status ("open", "closed", "all")

        Returns:
            List of Order objects
        """
        try:
            request = GetOrdersRequest(status=status)
            orders = self.trading_client.get_orders(request)

            result = []
            for order in orders:
                result.append(Order(
                    order_id=order.id,
                    symbol=order.symbol,
                    side=OrderSide.BUY if order.side == AlpacaOrderSide.BUY else OrderSide.SELL,
                    order_type=OrderType(order.type.value),
                    quantity=float(order.qty),
                    filled_quantity=float(order.filled_qty) if order.filled_qty else 0.0,
                    status=order.status.value,
                    submitted_at=order.submitted_at,
                    filled_at=order.filled_at,
                    limit_price=float(order.limit_price) if order.limit_price else None,
                    stop_price=float(order.stop_price) if order.stop_price else None,
                    filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None
                ))

            return result

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if canceled successfully
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Canceled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return False

    def close_position(self, symbol: str) -> bool:
        """
        Close an open position

        Args:
            symbol: Stock symbol

        Returns:
            True if closed successfully
        """
        try:
            self.trading_client.close_position(symbol)
            logger.info(f"Closed position in {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def close_all_positions(self) -> bool:
        """
        Close all open positions

        Returns:
            True if all positions closed successfully
        """
        try:
            self.trading_client.close_all_positions()
            logger.info("Closed all positions")
            return True
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return False
