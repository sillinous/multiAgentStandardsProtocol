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
    'BacktestResults'
]
