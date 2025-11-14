"""Market Data Integration - Real-time and Historical Data Providers"""

from .alpaca_client import (
    AlpacaClient,
    AlpacaConfig,
    MarketDataBar,
    Position,
    Order,
    OrderSide,
    OrderType,
    TimeInForce,
    AccountInfo
)
from .data_adapter import (
    RealMarketDataAdapter,
    RealDataConfig,
    create_real_data_adapter
)
from .paper_trading import (
    PaperTradingEngine,
    PaperTradingConfig,
    TradingMode,
    TradeExecutionResult
)

__all__ = [
    'AlpacaClient',
    'AlpacaConfig',
    'MarketDataBar',
    'Position',
    'Order',
    'OrderSide',
    'OrderType',
    'TimeInForce',
    'AccountInfo',
    'RealMarketDataAdapter',
    'RealDataConfig',
    'create_real_data_adapter',
    'PaperTradingEngine',
    'PaperTradingConfig',
    'TradingMode',
    'TradeExecutionResult'
]
