"""
NEXUS Backtesting API Routes

Exposes backtesting functionality for strategy validation.

Features:
- Run backtests with custom strategies
- Retrieve backtest results
- Get performance metrics
- View equity curves
- Analyze trades
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json

# Import backtesting engine
try:
    from superstandard.trading.backtesting_engine import (
        BacktestEngine,
        BacktestConfig,
        BacktestMetrics,
        OrderSide
    )
    BACKTEST_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Backtesting engine not available: {e}")
    BACKTEST_AVAILABLE = False

router = APIRouter(prefix="/api/backtest", tags=["backtesting"])

# In-memory storage for backtest results (production would use database)
backtest_results: Dict[str, Dict[str, Any]] = {}


# Pydantic Models
class BacktestRequest(BaseModel):
    """Request to run a backtest"""
    strategy_id: str
    symbol: str
    start_date: str  # ISO format
    end_date: str  # ISO format
    timeframe: str = "1d"

    # Configuration
    initial_capital: float = Field(default=10000.0, gt=0)
    commission_rate: float = Field(default=0.001, ge=0, le=0.1)
    slippage_bps: float = Field(default=5.0, ge=0)
    leverage: int = Field(default=1, ge=1, le=125)

    # Risk parameters
    stop_loss_pct: Optional[float] = Field(default=None, ge=0, le=100)
    take_profit_pct: Optional[float] = Field(default=None, ge=0)
    max_drawdown_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # Strategy parameters
    strategy_params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "sma_crossover",
                "symbol": "SOL/USD",
                "start_date": "2023-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z",
                "timeframe": "1d",
                "initial_capital": 10000.0,
                "commission_rate": 0.001,
                "stop_loss_pct": 5.0,
                "take_profit_pct": 10.0,
                "strategy_params": {
                    "fast_period": 10,
                    "slow_period": 30
                }
            }
        }


class BacktestSummary(BaseModel):
    """Summary of backtest results"""
    backtest_id: str
    status: str  # running, completed, failed
    strategy_id: str
    symbol: str
    start_date: str
    end_date: str

    # Key metrics (if completed)
    total_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    total_trades: Optional[int] = None
    win_rate: Optional[float] = None

    created_at: str
    completed_at: Optional[str] = None


# ============================================================================
# Example Strategies
# ============================================================================

async def simple_buy_hold_strategy(timestamp, bar, historical_data):
    """
    Simple buy and hold strategy (example)
    """
    # Buy on first bar
    if len(historical_data) == 1:
        return (OrderSide.BUY, 100.0)

    return None


async def sma_crossover_strategy(timestamp, bar, historical_data, fast_period=10, slow_period=30):
    """
    Simple Moving Average crossover strategy (example)

    Buy when fast SMA crosses above slow SMA
    Sell when fast SMA crosses below slow SMA
    """
    if len(historical_data) < slow_period:
        return None

    # Calculate SMAs
    fast_sma = historical_data['close'].rolling(fast_period).mean()
    slow_sma = historical_data['close'].rolling(slow_period).mean()

    # Get current and previous values
    current_fast = fast_sma.iloc[-1]
    current_slow = slow_sma.iloc[-1]
    prev_fast = fast_sma.iloc[-2]
    prev_slow = slow_sma.iloc[-2]

    # Crossover detection
    if prev_fast <= prev_slow and current_fast > current_slow:
        # Golden cross - buy signal
        return (OrderSide.BUY, 100.0)
    elif prev_fast >= prev_slow and current_fast < current_slow:
        # Death cross - sell signal
        return (OrderSide.SELL, 100.0)

    return None


# ============================================================================
# Backtest Endpoints
# ============================================================================

@router.post("/run")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Run a backtest

    Executes strategy backtest asynchronously and returns backtest ID
    """
    if not BACKTEST_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backtesting engine not available")

    # Generate backtest ID
    backtest_id = f"bt_{datetime.utcnow().timestamp()}"

    # Parse dates
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    # Create config
    config = BacktestConfig(
        initial_capital=request.initial_capital,
        commission_rate=request.commission_rate,
        slippage_bps=request.slippage_bps,
        leverage=request.leverage,
        stop_loss_pct=request.stop_loss_pct,
        take_profit_pct=request.take_profit_pct,
        max_drawdown_pct=request.max_drawdown_pct
    )

    # Store initial status
    backtest_results[backtest_id] = {
        "backtest_id": backtest_id,
        "status": "running",
        "strategy_id": request.strategy_id,
        "symbol": request.symbol,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "config": config.__dict__,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "metrics": None,
        "error": None
    }

    # Run backtest in background
    background_tasks.add_task(
        _execute_backtest,
        backtest_id,
        request.strategy_id,
        request.symbol,
        start_date,
        end_date,
        request.timeframe,
        config,
        request.strategy_params
    )

    return {
        "backtest_id": backtest_id,
        "status": "queued",
        "message": "Backtest started. Use /api/backtest/status/{backtest_id} to check progress."
    }


async def _execute_backtest(
    backtest_id: str,
    strategy_id: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
    config: Any,  # BacktestConfig if available
    strategy_params: Dict[str, Any]
):
    """Execute backtest (runs in background)"""
    try:
        # Create engine
        engine = BacktestEngine(config)

        # Select strategy
        if strategy_id == "buy_hold":
            strategy_func = simple_buy_hold_strategy
        elif strategy_id == "sma_crossover":
            # Wrap strategy with parameters
            async def strategy_func(timestamp, bar, historical_data):
                return await sma_crossover_strategy(
                    timestamp, bar, historical_data,
                    fast_period=strategy_params.get('fast_period', 10),
                    slow_period=strategy_params.get('slow_period', 30)
                )
        else:
            raise ValueError(f"Unknown strategy: {strategy_id}")

        # Run backtest
        metrics = await engine.run_backtest(
            strategy_func=strategy_func,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        # Get additional data
        equity_curve = engine.get_equity_curve()
        trades_df = engine.get_trades_df()

        # Update results
        backtest_results[backtest_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "metrics": {
                "total_return": metrics.total_return,
                "total_return_pct": metrics.total_return_pct,
                "annualized_return": metrics.annualized_return,
                "cagr": metrics.cagr,
                "volatility": metrics.volatility,
                "max_drawdown": metrics.max_drawdown,
                "max_drawdown_pct": metrics.max_drawdown_pct,
                "sharpe_ratio": metrics.sharpe_ratio,
                "sortino_ratio": metrics.sortino_ratio,
                "calmar_ratio": metrics.calmar_ratio,
                "total_trades": metrics.total_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "win_rate": metrics.win_rate,
                "avg_win": metrics.avg_win,
                "avg_loss": metrics.avg_loss,
                "profit_factor": metrics.profit_factor,
                "start_capital": metrics.start_capital,
                "end_capital": metrics.end_capital,
                "peak_capital": metrics.peak_capital,
                "total_commission": metrics.total_commission,
            },
            "equity_curve": equity_curve.to_dict()['equity'],
            "trades": trades_df.to_dict('records') if not trades_df.empty else []
        })

    except Exception as e:
        backtest_results[backtest_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e)
        })


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str) -> Dict[str, Any]:
    """
    Get backtest status

    Returns current status and results (if completed)
    """
    if backtest_id not in backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    result = backtest_results[backtest_id]

    response = {
        "backtest_id": result["backtest_id"],
        "status": result["status"],
        "strategy_id": result["strategy_id"],
        "symbol": result["symbol"],
        "created_at": result["created_at"],
        "completed_at": result["completed_at"]
    }

    if result["status"] == "completed" and result["metrics"]:
        response["metrics"] = result["metrics"]

    if result["status"] == "failed":
        response["error"] = result["error"]

    return response


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str) -> Dict[str, Any]:
    """
    Get full backtest results

    Includes metrics, equity curve, and trade list
    """
    if backtest_id not in backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    result = backtest_results[backtest_id]

    if result["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Backtest not completed. Status: {result['status']}"
        )

    return result


@router.get("/list")
async def list_backtests(limit: int = 20) -> List[BacktestSummary]:
    """
    List recent backtests

    Returns summary of recent backtests
    """
    summaries = []

    # Sort by creation time (most recent first)
    sorted_results = sorted(
        backtest_results.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:limit]

    for result in sorted_results:
        summary = BacktestSummary(
            backtest_id=result["backtest_id"],
            status=result["status"],
            strategy_id=result["strategy_id"],
            symbol=result["symbol"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            created_at=result["created_at"],
            completed_at=result["completed_at"]
        )

        if result["status"] == "completed" and result["metrics"]:
            metrics = result["metrics"]
            summary.total_return_pct = metrics["total_return_pct"]
            summary.sharpe_ratio = metrics["sharpe_ratio"]
            summary.max_drawdown_pct = metrics["max_drawdown_pct"]
            summary.total_trades = metrics["total_trades"]
            summary.win_rate = metrics["win_rate"]

        summaries.append(summary)

    return summaries


@router.get("/strategies")
async def list_strategies() -> List[Dict[str, Any]]:
    """
    List available strategies for backtesting
    """
    return [
        {
            "strategy_id": "buy_hold",
            "name": "Buy and Hold",
            "description": "Simple buy and hold strategy",
            "parameters": {}
        },
        {
            "strategy_id": "sma_crossover",
            "name": "SMA Crossover",
            "description": "Moving average crossover strategy",
            "parameters": {
                "fast_period": {"type": "int", "default": 10, "min": 1, "max": 100},
                "slow_period": {"type": "int", "default": 30, "min": 1, "max": 200}
            }
        }
    ]


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str) -> Dict[str, str]:
    """Delete backtest results"""
    if backtest_id not in backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    del backtest_results[backtest_id]

    return {
        "status": "success",
        "message": f"Backtest {backtest_id} deleted"
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check backtesting system health"""
    return {
        "status": "healthy" if BACKTEST_AVAILABLE else "unavailable",
        "engine_available": BACKTEST_AVAILABLE,
        "active_backtests": len([r for r in backtest_results.values() if r["status"] == "running"]),
        "completed_backtests": len([r for r in backtest_results.values() if r["status"] == "completed"]),
        "failed_backtests": len([r for r in backtest_results.values() if r["status"] == "failed"]),
        "total_backtests": len(backtest_results)
    }
