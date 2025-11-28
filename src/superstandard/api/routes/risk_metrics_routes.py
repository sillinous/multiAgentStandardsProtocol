"""
NEXUS Advanced Risk Metrics API Routes

Exposes sophisticated risk analysis functionality for portfolio management.

Features:
- VaR (Value at Risk) calculation - multiple methods
- CVaR (Conditional VaR / Expected Shortfall)
- Monte Carlo simulation
- Stress testing with custom scenarios
- Portfolio correlation analysis
- Diversification metrics

Endpoints:
- POST /api/risk/var/historical - Calculate historical VaR
- POST /api/risk/var/parametric - Calculate parametric VaR
- POST /api/risk/var/monte-carlo - Calculate Monte Carlo VaR
- POST /api/risk/var/portfolio - Calculate portfolio VaR with correlations
- POST /api/risk/stress-test - Run stress test scenario
- POST /api/risk/correlation - Calculate correlation matrix
- POST /api/risk/diversification - Calculate diversification ratio
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import numpy as np

# Import risk metrics calculator
try:
    from superstandard.trading.risk_metrics import (
        RiskMetricsCalculator,
        VaRResult,
        StressTestResult
    )
    RISK_METRICS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Risk metrics calculator not available: {e}")
    RISK_METRICS_AVAILABLE = False

router = APIRouter(prefix="/api/risk", tags=["risk_metrics"])


# ============================================================================
# Pydantic Models
# ============================================================================

class HistoricalVaRRequest(BaseModel):
    """Request for historical VaR calculation"""
    returns: List[float] = Field(..., description="Historical returns as decimals (e.g., [0.01, -0.02, 0.015])")
    portfolio_value: float = Field(..., gt=0, description="Current portfolio value")
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99, description="Confidence level (0.95 = 95%)")
    time_horizon: int = Field(default=1, ge=1, le=30, description="Time horizon in days")

    class Config:
        json_schema_extra = {
            "example": {
                "returns": [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015],
                "portfolio_value": 100000.0,
                "confidence_level": 0.95,
                "time_horizon": 1
            }
        }


class ParametricVaRRequest(BaseModel):
    """Request for parametric VaR calculation"""
    mean_return: float = Field(..., description="Average return (as decimal)")
    std_return: float = Field(..., gt=0, description="Standard deviation of returns")
    portfolio_value: float = Field(..., gt=0, description="Current portfolio value")
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99)
    time_horizon: int = Field(default=1, ge=1, le=30)

    class Config:
        json_schema_extra = {
            "example": {
                "mean_return": 0.001,
                "std_return": 0.02,
                "portfolio_value": 100000.0,
                "confidence_level": 0.95,
                "time_horizon": 1
            }
        }


class MonteCarloVaRRequest(BaseModel):
    """Request for Monte Carlo VaR calculation"""
    mean_return: float
    std_return: float = Field(..., gt=0)
    portfolio_value: float = Field(..., gt=0)
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99)
    time_horizon: int = Field(default=1, ge=1, le=30)
    num_simulations: int = Field(default=10000, ge=1000, le=100000, description="Number of simulations")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    class Config:
        json_schema_extra = {
            "example": {
                "mean_return": 0.001,
                "std_return": 0.02,
                "portfolio_value": 100000.0,
                "confidence_level": 0.95,
                "time_horizon": 1,
                "num_simulations": 10000
            }
        }


class PortfolioPosition(BaseModel):
    """Portfolio position"""
    symbol: str
    value: float = Field(..., gt=0)
    weight: float = Field(..., ge=0, le=1, description="Position weight (should sum to 1.0)")
    quantity: Optional[float] = None
    price: Optional[float] = None


class PortfolioVaRRequest(BaseModel):
    """Request for portfolio VaR with correlations"""
    positions: List[PortfolioPosition] = Field(..., min_items=2, description="Portfolio positions")
    returns_data: Dict[str, List[float]] = Field(..., description="Historical returns for each symbol")
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99)
    time_horizon: int = Field(default=1, ge=1, le=30)
    method: str = Field(default="historical", pattern="^(historical|parametric|monte_carlo)$")

    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {"symbol": "BTC/USD", "value": 50000, "weight": 0.5},
                    {"symbol": "ETH/USD", "value": 30000, "weight": 0.3},
                    {"symbol": "SOL/USD", "value": 20000, "weight": 0.2}
                ],
                "returns_data": {
                    "BTC/USD": [0.01, -0.02, 0.015, -0.01, 0.005],
                    "ETH/USD": [0.02, -0.015, 0.01, -0.005, 0.008],
                    "SOL/USD": [0.03, -0.025, 0.02, -0.015, 0.01]
                },
                "confidence_level": 0.95,
                "time_horizon": 1,
                "method": "historical"
            }
        }


class StressTestRequest(BaseModel):
    """Request for stress test"""
    positions: List[PortfolioPosition] = Field(..., min_items=1, description="Portfolio positions")
    scenario: Dict[str, float] = Field(..., description="Price shock per symbol (e.g., {'BTC/USD': -0.30})")
    scenario_name: Optional[str] = Field("Custom Stress Test", description="Name of the scenario")

    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {"symbol": "BTC/USD", "value": 50000, "weight": 0.5, "quantity": 1, "price": 50000},
                    {"symbol": "ETH/USD", "value": 30000, "weight": 0.3, "quantity": 10, "price": 3000},
                    {"symbol": "SOL/USD", "value": 20000, "weight": 0.2, "quantity": 200, "price": 100}
                ],
                "scenario": {
                    "BTC/USD": -0.30,
                    "ETH/USD": -0.25,
                    "SOL/USD": -0.40
                },
                "scenario_name": "Crypto Market Crash (-30% to -40%)"
            }
        }


class CorrelationRequest(BaseModel):
    """Request for correlation matrix"""
    returns_data: Dict[str, List[float]] = Field(..., description="Historical returns for each symbol")

    class Config:
        json_schema_extra = {
            "example": {
                "returns_data": {
                    "BTC/USD": [0.01, -0.02, 0.015, -0.01, 0.005],
                    "ETH/USD": [0.02, -0.015, 0.01, -0.005, 0.008],
                    "SOL/USD": [0.03, -0.025, 0.02, -0.015, 0.01]
                }
            }
        }


class DiversificationRequest(BaseModel):
    """Request for diversification ratio"""
    positions: List[PortfolioPosition]
    returns_data: Dict[str, List[float]]

    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {"symbol": "BTC/USD", "value": 50000, "weight": 0.5},
                    {"symbol": "ETH/USD", "value": 30000, "weight": 0.3},
                    {"symbol": "SOL/USD", "value": 20000, "weight": 0.2}
                ],
                "returns_data": {
                    "BTC/USD": [0.01, -0.02, 0.015, -0.01, 0.005],
                    "ETH/USD": [0.02, -0.015, 0.01, -0.005, 0.008],
                    "SOL/USD": [0.03, -0.025, 0.02, -0.015, 0.01]
                }
            }
        }


# ============================================================================
# VaR Calculation Endpoints
# ============================================================================

@router.post("/var/historical")
async def calculate_historical_var(request: HistoricalVaRRequest) -> Dict[str, Any]:
    """
    Calculate Historical VaR from actual return distribution

    Uses empirical distribution of historical returns (most accurate for non-normal distributions).
    Requires at least 30 historical return observations.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        result = RiskMetricsCalculator.historical_var(
            returns=request.returns,
            portfolio_value=request.portfolio_value,
            confidence_level=request.confidence_level,
            time_horizon=request.time_horizon
        )

        return {
            "method": result.method,
            "var_amount": result.var_amount,
            "var_percentage": result.var_percentage,
            "cvar_amount": result.cvar_amount,
            "cvar_percentage": result.cvar_percentage,
            "worst_case_loss": result.worst_case_loss,
            "confidence_level": result.confidence_level,
            "time_horizon_days": result.time_horizon,
            "portfolio_value": result.portfolio_value,
            "interpretation": f"At {result.confidence_level*100:.0f}% confidence, maximum expected loss over {result.time_horizon} day(s) is ${result.var_amount:,.2f} ({result.var_percentage:.2f}%)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/var/parametric")
async def calculate_parametric_var(request: ParametricVaRRequest) -> Dict[str, Any]:
    """
    Calculate Parametric VaR using normal distribution assumption

    Fast calculation assuming returns are normally distributed.
    Less accurate for fat-tailed distributions but computationally efficient.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        result = RiskMetricsCalculator.parametric_var(
            mean_return=request.mean_return,
            std_return=request.std_return,
            portfolio_value=request.portfolio_value,
            confidence_level=request.confidence_level,
            time_horizon=request.time_horizon
        )

        return {
            "method": result.method,
            "var_amount": result.var_amount,
            "var_percentage": result.var_percentage,
            "cvar_amount": result.cvar_amount,
            "cvar_percentage": result.cvar_percentage,
            "confidence_level": result.confidence_level,
            "time_horizon_days": result.time_horizon,
            "portfolio_value": result.portfolio_value,
            "interpretation": f"At {result.confidence_level*100:.0f}% confidence, maximum expected loss over {result.time_horizon} day(s) is ${result.var_amount:,.2f} ({result.var_percentage:.2f}%)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/var/monte-carlo")
async def calculate_monte_carlo_var(request: MonteCarloVaRRequest) -> Dict[str, Any]:
    """
    Calculate VaR using Monte Carlo simulation

    Simulates thousands of possible portfolio paths to estimate VaR.
    More accurate than parametric VaR for non-normal distributions.
    Computationally intensive but highly flexible.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        result = RiskMetricsCalculator.monte_carlo_var(
            mean_return=request.mean_return,
            std_return=request.std_return,
            portfolio_value=request.portfolio_value,
            confidence_level=request.confidence_level,
            time_horizon=request.time_horizon,
            num_simulations=request.num_simulations,
            random_seed=request.random_seed
        )

        return {
            "method": result.method,
            "var_amount": result.var_amount,
            "var_percentage": result.var_percentage,
            "cvar_amount": result.cvar_amount,
            "cvar_percentage": result.cvar_percentage,
            "worst_case_loss": result.worst_case_loss,
            "confidence_level": result.confidence_level,
            "time_horizon_days": result.time_horizon,
            "portfolio_value": result.portfolio_value,
            "num_simulations": request.num_simulations,
            "interpretation": f"At {result.confidence_level*100:.0f}% confidence, maximum expected loss over {result.time_horizon} day(s) is ${result.var_amount:,.2f} ({result.var_percentage:.2f}%)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/var/portfolio")
async def calculate_portfolio_var(request: PortfolioVaRRequest) -> Dict[str, Any]:
    """
    Calculate portfolio-level VaR accounting for correlations

    Considers correlation between portfolio positions for more accurate risk assessment.
    Supports multiple calculation methods: historical, parametric, monte_carlo.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        # Convert Pydantic models to dicts
        positions_dicts = [pos.dict() for pos in request.positions]

        result = RiskMetricsCalculator.calculate_portfolio_var(
            positions=positions_dicts,
            returns_data=request.returns_data,
            confidence_level=request.confidence_level,
            time_horizon=request.time_horizon,
            method=request.method
        )

        return {
            "method": result.method,
            "var_amount": result.var_amount,
            "var_percentage": result.var_percentage,
            "cvar_amount": result.cvar_amount,
            "cvar_percentage": result.cvar_percentage,
            "worst_case_loss": result.worst_case_loss,
            "confidence_level": result.confidence_level,
            "time_horizon_days": result.time_horizon,
            "portfolio_value": result.portfolio_value,
            "num_positions": len(request.positions),
            "interpretation": f"Portfolio VaR at {result.confidence_level*100:.0f}% confidence: ${result.var_amount:,.2f} ({result.var_percentage:.2f}%)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Stress Testing Endpoint
# ============================================================================

@router.post("/stress-test")
async def run_stress_test(request: StressTestRequest) -> Dict[str, Any]:
    """
    Run stress test with custom scenario

    Simulates impact of specified price shocks on portfolio.
    Useful for understanding portfolio vulnerability to extreme market events.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        # Convert Pydantic models to dicts
        positions_dicts = [pos.dict() for pos in request.positions]

        result = RiskMetricsCalculator.stress_test(
            positions=positions_dicts,
            scenario=request.scenario
        )

        return {
            "scenario_name": request.scenario_name or result.scenario_name,
            "portfolio_value": result.portfolio_value,
            "shocked_value": result.shocked_value,
            "loss_amount": result.loss_amount,
            "loss_percentage": result.loss_percentage,
            "positions_affected": result.positions_affected,
            "total_positions": len(request.positions),
            "scenario_shocks": request.scenario,
            "interpretation": f"Under '{request.scenario_name}' scenario, portfolio would lose ${result.loss_amount:,.2f} ({result.loss_percentage:.2f}%)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Portfolio Analysis Endpoints
# ============================================================================

@router.post("/correlation")
async def calculate_correlation_matrix(request: CorrelationRequest) -> Dict[str, Any]:
    """
    Calculate correlation matrix for portfolio symbols

    Shows how symbols move together.
    High correlation = less diversification benefit.
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        corr_matrix, symbols = RiskMetricsCalculator.calculate_correlation_matrix(request.returns_data)

        # Convert numpy array to nested list for JSON
        corr_matrix_list = corr_matrix.tolist()

        return {
            "symbols": symbols,
            "correlation_matrix": corr_matrix_list,
            "interpretation": "Correlation ranges from -1 (inverse) to +1 (perfect correlation). Values near 0 indicate low correlation."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/diversification")
async def calculate_diversification_ratio(request: DiversificationRequest) -> Dict[str, Any]:
    """
    Calculate portfolio diversification ratio

    Ratio of weighted average volatility to portfolio volatility.
    Higher ratio = better diversification (>1.0 indicates diversification benefit).
    """
    if not RISK_METRICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Risk metrics calculator not available")

    try:
        # Convert Pydantic models to dicts
        positions_dicts = [pos.dict() for pos in request.positions]

        div_ratio = RiskMetricsCalculator.diversification_ratio(
            positions=positions_dicts,
            returns_data=request.returns_data
        )

        # Interpretation
        if div_ratio > 1.5:
            interpretation = "Excellent diversification - portfolio benefits significantly from low correlation"
        elif div_ratio > 1.2:
            interpretation = "Good diversification - portfolio has meaningful diversification benefits"
        elif div_ratio > 1.0:
            interpretation = "Moderate diversification - some diversification benefits present"
        else:
            interpretation = "Poor diversification - portfolio positions are highly correlated"

        return {
            "diversification_ratio": div_ratio,
            "num_positions": len(request.positions),
            "interpretation": interpretation,
            "note": "Ratio > 1.0 indicates diversification benefit. Higher is better."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check risk metrics system health"""
    return {
        "status": "healthy" if RISK_METRICS_AVAILABLE else "unavailable",
        "risk_metrics_available": RISK_METRICS_AVAILABLE,
        "supported_methods": ["historical_var", "parametric_var", "monte_carlo_var", "portfolio_var", "stress_test", "correlation", "diversification"]
    }
