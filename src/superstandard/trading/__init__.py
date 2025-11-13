"""
Trading Module - Market Simulation, Backtesting, and Agent Validation
"""

from .market_simulation import (
    MarketBar,
    MarketRegime,
    MarketEvent,
    MarketSimulator,
    AgentBacktester,
    PerformanceMetrics
)

from .historical_data import (
    HistoricalDataFetcher,
    MarketRegimeDetector,
    DataSource
)

__all__ = [
    'MarketBar',
    'MarketRegime',
    'MarketEvent',
    'MarketSimulator',
    'AgentBacktester',
    'PerformanceMetrics',
    'HistoricalDataFetcher',
    'MarketRegimeDetector',
    'DataSource'
]
