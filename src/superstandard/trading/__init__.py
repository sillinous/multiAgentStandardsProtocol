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

__all__ = [
    'MarketBar',
    'MarketRegime',
    'MarketEvent',
    'MarketSimulator',
    'AgentBacktester',
    'PerformanceMetrics'
]
