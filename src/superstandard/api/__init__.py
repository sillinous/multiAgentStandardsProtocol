"""API and Dashboard Components"""

from .dashboard_api import (
    create_dashboard_app,
    get_dashboard_state,
    DashboardState,
    DashboardEvent,
    EventType,
    PortfolioSnapshot,
    SentimentSnapshot,
    ConnectionManager
)
from .backtesting_api import (
    create_backtesting_app,
    BacktestRequest,
    BacktestResults
)
from .mission_control_api import (
    create_mission_control_app,
    StrategyState,
    PortfolioState,
    RiskMetrics,
    Opportunity,
    RiskAlert,
    MissionControlState
)

__all__ = [
    # Dashboard API
    'create_dashboard_app',
    'get_dashboard_state',
    'DashboardState',
    'DashboardEvent',
    'EventType',
    'PortfolioSnapshot',
    'SentimentSnapshot',
    'ConnectionManager',

    # Backtesting API
    'create_backtesting_app',
    'BacktestRequest',
    'BacktestResults',

    # Mission Control API
    'create_mission_control_app',
    'StrategyState',
    'PortfolioState',
    'RiskMetrics',
    'Opportunity',
    'RiskAlert',
    'MissionControlState'
]
