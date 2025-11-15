"""
Backtesting Visualization API

FastAPI backend for comprehensive backtesting with visualization support.

Features:
- Run backtests with any strategy
- Generate equity curves and performance metrics
- Trade-by-trade analysis
- Strategy comparison
- What-if scenarios
- Export results
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json


# ============================================================================
# Backtesting Models
# ============================================================================

@dataclass
class BacktestRequest:
    """Request for running a backtest"""
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    parameters: Dict[str, Any] = None


@dataclass
class BacktestResults:
    """Complete backtest results with visualizations"""

    # Metadata
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    duration_days: int

    # Performance Summary
    initial_capital: float
    final_value: float
    total_return: float
    total_return_pct: float
    annualized_return: float

    # Risk Metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float

    # Trading Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # Time Series Data (for charts)
    equity_curve: List[Dict[str, Any]]  # [{'date': '2024-01-01', 'value': 100000}, ...]
    drawdown_curve: List[Dict[str, Any]]

    # Trade Details
    trades: List[Dict[str, Any]]

    # Monthly/Daily Returns
    monthly_returns: List[Dict[str, Any]]
    daily_returns: List[float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'strategy_name': self.strategy_name,
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'duration_days': self.duration_days,
            'performance': {
                'initial_capital': self.initial_capital,
                'final_value': self.final_value,
                'total_return': self.total_return,
                'total_return_pct': self.total_return_pct,
                'annualized_return': self.annualized_return
            },
            'risk_metrics': {
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'max_drawdown': self.max_drawdown,
                'max_drawdown_pct': self.max_drawdown_pct,
                'volatility': self.volatility
            },
            'trading_stats': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.win_rate,
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'profit_factor': self.profit_factor
            },
            'time_series': {
                'equity_curve': self.equity_curve,
                'drawdown_curve': self.drawdown_curve
            },
            'trades': self.trades,
            'monthly_returns': self.monthly_returns,
            'daily_returns': self.daily_returns
        }


# ============================================================================
# Backtesting API
# ============================================================================

def create_backtesting_app() -> FastAPI:
    """Create FastAPI app for backtesting"""

    app = FastAPI(title="Backtesting & Visualization API")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Endpoints
    # ========================================================================

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "Backtesting & Visualization API",
            "version": "1.0.0",
            "features": [
                "Strategy backtesting",
                "Advanced visualizations",
                "Trade analysis",
                "Performance metrics",
                "Strategy comparison"
            ]
        }

    @app.get("/backtest/dashboard", response_class=FileResponse)
    async def serve_dashboard():
        """Serve backtesting dashboard HTML"""
        dashboard_path = Path(__file__).parent / "backtesting_dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        raise HTTPException(status_code=404, detail="Dashboard not found")

    @app.post("/api/backtest/run")
    async def run_backtest(request: Dict[str, Any]):
        """Run a backtest and return results"""

        # Extract parameters
        strategy_name = request.get('strategy_name', 'balanced_trader')
        symbols = request.get('symbols', ['AAPL'])
        start_date = request.get('start_date', '2023-01-01')
        end_date = request.get('end_date', '2024-01-01')
        initial_capital = request.get('initial_capital', 100000.0)

        # Generate mock backtest results for demo
        # In production, this would run the actual BacktestEngine
        results = generate_mock_backtest(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )

        return JSONResponse(content=results.to_dict())

    @app.get("/api/backtest/strategies")
    async def list_strategies():
        """List available strategies"""
        return {
            'strategies': [
                {
                    'name': 'balanced_trader',
                    'description': 'Balanced risk/reward strategy',
                    'category': 'ensemble'
                },
                {
                    'name': 'conservative_value',
                    'description': 'Low-risk value investing',
                    'category': 'ensemble'
                },
                {
                    'name': 'aggressive_growth',
                    'description': 'High-growth momentum strategy',
                    'category': 'ensemble'
                },
                {
                    'name': 'sentiment_driven',
                    'description': 'Sentiment-based trading',
                    'category': 'sentiment'
                },
                {
                    'name': 'mean_reversion',
                    'description': 'Mean reversion strategy',
                    'category': 'technical'
                }
            ]
        }

    @app.get("/api/backtest/symbols")
    async def list_symbols():
        """List available symbols"""
        return {
            'stocks': [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
                'NVDA', 'META', 'BRK.B', 'JPM', 'V'
            ],
            'crypto': [
                'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD',
                'XRP-USD', 'DOT-USD', 'DOGE-USD', 'AVAX-USD', 'MATIC-USD'
            ],
            'indices': [
                '^GSPC', '^DJI', '^IXIC', '^RUT'
            ]
        }

    return app


# ============================================================================
# Mock Data Generator (for demo)
# ============================================================================

def generate_mock_backtest(
    strategy_name: str,
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_capital: float
) -> BacktestResults:
    """Generate mock backtest results for demo purposes"""

    import random
    from datetime import datetime, timedelta

    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    duration = (end - start).days

    # Generate equity curve
    equity_curve = []
    drawdown_curve = []
    trades = []
    monthly_returns = []
    daily_returns = []

    current_value = initial_capital
    peak_value = initial_capital
    current_date = start

    # Simulate daily returns
    for day in range(duration):
        # Random daily return (-2% to +2%)
        daily_return = random.gauss(0.05, 0.8)  # Mean 0.05%, std 0.8%
        daily_returns.append(daily_return)

        # Update value
        current_value *= (1 + daily_return / 100)

        # Update peak
        if current_value > peak_value:
            peak_value = current_value

        # Calculate drawdown
        drawdown = (current_value - peak_value) / peak_value * 100

        # Add to curves
        equity_curve.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'value': round(current_value, 2)
        })

        drawdown_curve.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'drawdown': round(drawdown, 2)
        })

        # Simulate trades (random)
        if random.random() < 0.05:  # 5% chance of trade per day
            symbol = random.choice(symbols)
            action = random.choice(['buy', 'sell'])
            quantity = random.randint(10, 100)
            price = random.uniform(100, 500)
            pnl = random.gauss(0, 500)

            trades.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': round(price, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl / (price * quantity) * 100, 2) if action == 'sell' else 0
            })

        current_date += timedelta(days=1)

    # Calculate monthly returns
    current_month = start.month
    monthly_value = initial_capital

    for i, point in enumerate(equity_curve):
        date = datetime.fromisoformat(point['date'])
        if date.month != current_month or i == len(equity_curve) - 1:
            month_return = (point['value'] - monthly_value) / monthly_value * 100
            monthly_returns.append({
                'month': date.strftime('%Y-%m'),
                'return': round(month_return, 2)
            })
            current_month = date.month
            monthly_value = point['value']

    # Calculate performance metrics
    final_value = current_value
    total_return = final_value - initial_capital
    total_return_pct = (total_return / initial_capital) * 100
    annualized_return = ((final_value / initial_capital) ** (365 / duration) - 1) * 100

    # Risk metrics
    import statistics
    import math

    volatility = statistics.stdev(daily_returns) * math.sqrt(252) if len(daily_returns) > 1 else 0
    sharpe_ratio = (annualized_return - 2) / volatility if volatility > 0 else 0  # Assume 2% risk-free rate

    negative_returns = [r for r in daily_returns if r < 0]
    downside_deviation = statistics.stdev(negative_returns) * math.sqrt(252) if len(negative_returns) > 1 else 0
    sortino_ratio = (annualized_return - 2) / downside_deviation if downside_deviation > 0 else 0

    max_drawdown = min(dd['drawdown'] for dd in drawdown_curve)
    max_drawdown_pct = max_drawdown

    # Trading statistics
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
    losing_trades = len([t for t in trades if t.get('pnl', 0) < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    wins = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
    losses = [abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]

    avg_win = statistics.mean(wins) if wins else 0
    avg_loss = statistics.mean(losses) if losses else 0
    profit_factor = sum(wins) / sum(losses) if sum(losses) > 0 else 0

    return BacktestResults(
        strategy_name=strategy_name,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration,
        initial_capital=initial_capital,
        final_value=final_value,
        total_return=total_return,
        total_return_pct=total_return_pct,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=abs(max_drawdown),
        max_drawdown_pct=abs(max_drawdown_pct),
        volatility=volatility,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        equity_curve=equity_curve,
        drawdown_curve=drawdown_curve,
        trades=trades,
        monthly_returns=monthly_returns,
        daily_returns=daily_returns
    )
