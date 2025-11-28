"""
NEXUS Trading Module

Provides core trading functionality for the Trading Suite:
- Backtesting engine for strategy validation
- Paper trading for risk-free testing
- Strategy storage and versioning
- Risk metrics and analysis
- Real-time market data via WebSocket
"""

# Lazy imports to handle optional dependencies gracefully
def __getattr__(name):
    """Lazy import of trading modules"""
    try:
        if name == "BacktestEngine":
            from .backtesting_engine import BacktestEngine
            return BacktestEngine
        elif name == "BacktestConfig":
            from .backtesting_engine import BacktestConfig
            return BacktestConfig
        elif name == "BacktestMetrics":
            from .backtesting_engine import BacktestMetrics
            return BacktestMetrics
        elif name == "StrategyStorage":
            from .strategy_storage import StrategyStorage
            return StrategyStorage
        elif name == "Strategy":
            from .strategy_storage import Strategy
            return Strategy
        elif name == "PaperTradingEngine":
            from .paper_trading import PaperTradingEngine
            return PaperTradingEngine
        elif name == "RiskMetricsCalculator":
            from .risk_metrics import RiskMetricsCalculator
            return RiskMetricsCalculator
        elif name == "MarketDataWebSocketManager":
            from .market_data_ws import MarketDataWebSocketManager
            return MarketDataWebSocketManager
    except ImportError:
        pass
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BacktestEngine",
    "BacktestConfig",
    "BacktestMetrics",
    "StrategyStorage",
    "Strategy",
    "PaperTradingEngine",
    "RiskMetricsCalculator",
    "MarketDataWebSocketManager",
]
