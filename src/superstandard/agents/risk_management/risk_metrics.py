"""
Risk Metrics Calculator

Calculates comprehensive risk metrics for portfolio management.

Metrics Included:
- Value at Risk (VaR) - Historical and Parametric
- Conditional VaR (CVaR) - Expected Shortfall
- Sharpe Ratio - Risk-adjusted returns
- Sortino Ratio - Downside risk-adjusted returns
- Maximum Drawdown - Worst peak-to-trough decline
- Beta - Market correlation
- Volatility - Portfolio volatility
- Information Ratio - Active return vs tracking error
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
import math


# ============================================================================
# Risk Metrics Models
# ============================================================================

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for a portfolio"""

    # Value at Risk
    var_95: float  # 95% VaR (daily)
    var_99: float  # 99% VaR (daily)
    cvar_95: float  # 95% CVaR (Expected Shortfall)

    # Risk-Adjusted Returns
    sharpe_ratio: float  # Sharpe Ratio
    sortino_ratio: float  # Sortino Ratio
    information_ratio: float  # Information Ratio

    # Volatility Metrics
    volatility: float  # Annualized volatility
    downside_deviation: float  # Downside volatility

    # Drawdown Metrics
    max_drawdown: float  # Maximum drawdown (%)
    current_drawdown: float  # Current drawdown from peak
    avg_drawdown: float  # Average drawdown

    # Market Metrics
    beta: float  # Market beta
    alpha: float  # Jensen's alpha

    # Additional Metrics
    calmar_ratio: float  # Return / Max Drawdown
    ulcer_index: float  # Measure of downside volatility

    # Metadata
    calculation_date: datetime = field(default_factory=datetime.utcnow)
    lookback_days: int = 252  # Trading days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'cvar_95': self.cvar_95,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'information_ratio': self.information_ratio,
            'volatility': self.volatility,
            'downside_deviation': self.downside_deviation,
            'max_drawdown': self.max_drawdown,
            'current_drawdown': self.current_drawdown,
            'avg_drawdown': self.avg_drawdown,
            'beta': self.beta,
            'alpha': self.alpha,
            'calmar_ratio': self.calmar_ratio,
            'ulcer_index': self.ulcer_index,
            'calculation_date': self.calculation_date.isoformat(),
            'lookback_days': self.lookback_days
        }

    def get_risk_level(self) -> str:
        """Get overall risk level"""
        # Based on Sharpe ratio and max drawdown
        if self.sharpe_ratio > 2.0 and abs(self.max_drawdown) < 10:
            return "low"
        elif self.sharpe_ratio > 1.0 and abs(self.max_drawdown) < 20:
            return "moderate"
        elif self.sharpe_ratio > 0.5 and abs(self.max_drawdown) < 30:
            return "elevated"
        else:
            return "high"

    def get_rating(self) -> str:
        """Get qualitative rating"""
        if self.sharpe_ratio > 2.0:
            return "Excellent"
        elif self.sharpe_ratio > 1.5:
            return "Very Good"
        elif self.sharpe_ratio > 1.0:
            return "Good"
        elif self.sharpe_ratio > 0.5:
            return "Fair"
        else:
            return "Poor"


# ============================================================================
# Risk Metrics Calculator
# ============================================================================

class RiskMetricsCalculator:
    """
    Calculate comprehensive risk metrics for a portfolio

    Example:
        calculator = RiskMetricsCalculator()

        # Daily returns as percentages
        returns = [0.5, -0.3, 1.2, -0.8, 0.4, ...]

        metrics = calculator.calculate_metrics(
            returns=returns,
            risk_free_rate=0.02,  # 2% annual
            benchmark_returns=[0.4, -0.2, 1.0, ...]  # Optional
        )

        print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
        print(f"Max DD: {metrics.max_drawdown:.2f}%")
    """

    def __init__(self, confidence_level_95: float = 0.95, confidence_level_99: float = 0.99):
        """
        Initialize risk metrics calculator

        Args:
            confidence_level_95: Confidence level for 95% VaR
            confidence_level_99: Confidence level for 99% VaR
        """
        self.confidence_level_95 = confidence_level_95
        self.confidence_level_99 = confidence_level_99

    def calculate_metrics(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
        benchmark_returns: Optional[List[float]] = None,
        lookback_days: int = 252
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics

        Args:
            returns: List of daily returns (as percentages, e.g., 1.5 for 1.5%)
            risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%)
            benchmark_returns: Optional benchmark returns for beta/alpha
            lookback_days: Number of trading days for lookback

        Returns:
            RiskMetrics object with all calculated metrics
        """
        if not returns or len(returns) < 2:
            # Return default metrics if insufficient data
            return self._default_metrics(lookback_days)

        # Convert percentage returns to decimal
        returns_decimal = [r / 100.0 for r in returns]

        # Calculate VaR
        var_95 = self._calculate_var(returns, self.confidence_level_95)
        var_99 = self._calculate_var(returns, self.confidence_level_99)
        cvar_95 = self._calculate_cvar(returns, self.confidence_level_95)

        # Calculate volatility
        volatility = self._calculate_volatility(returns)
        downside_deviation = self._calculate_downside_deviation(returns)

        # Calculate risk-adjusted returns
        sharpe = self._calculate_sharpe_ratio(returns, risk_free_rate)
        sortino = self._calculate_sortino_ratio(returns, risk_free_rate)

        # Calculate drawdown metrics
        max_dd, current_dd, avg_dd = self._calculate_drawdown_metrics(returns_decimal)

        # Calculate market metrics
        beta = 1.0
        alpha = 0.0
        information_ratio = 0.0

        if benchmark_returns and len(benchmark_returns) == len(returns):
            beta = self._calculate_beta(returns, benchmark_returns)
            alpha = self._calculate_alpha(returns, benchmark_returns, risk_free_rate, beta)
            information_ratio = self._calculate_information_ratio(returns, benchmark_returns)

        # Calculate additional metrics
        calmar = self._calculate_calmar_ratio(returns, max_dd)
        ulcer = self._calculate_ulcer_index(returns_decimal)

        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            information_ratio=information_ratio,
            volatility=volatility,
            downside_deviation=downside_deviation,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            avg_drawdown=avg_dd,
            beta=beta,
            alpha=alpha,
            calmar_ratio=calmar,
            ulcer_index=ulcer,
            lookback_days=lookback_days
        )

    def _calculate_var(self, returns: List[float], confidence_level: float) -> float:
        """Calculate Value at Risk (Historical method)"""
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1

        return sorted_returns[index]

    def _calculate_cvar(self, returns: List[float], confidence_level: float) -> float:
        """Calculate Conditional VaR (Expected Shortfall)"""
        if not returns:
            return 0.0

        var = self._calculate_var(returns, confidence_level)

        # Average of returns below VaR
        tail_returns = [r for r in returns if r <= var]

        if not tail_returns:
            return var

        return sum(tail_returns) / len(tail_returns)

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0

        # Standard deviation of returns
        std_dev = statistics.stdev(returns)

        # Annualize (assuming daily returns)
        annualized_vol = std_dev * math.sqrt(252)

        return annualized_vol

    def _calculate_downside_deviation(self, returns: List[float]) -> float:
        """Calculate downside deviation (semi-variance)"""
        if not returns:
            return 0.0

        # Only negative returns
        negative_returns = [r for r in returns if r < 0]

        if not negative_returns:
            return 0.0

        # Standard deviation of negative returns
        return statistics.stdev(negative_returns) * math.sqrt(252)

    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float) -> float:
        """Calculate Sharpe Ratio"""
        if len(returns) < 2:
            return 0.0

        # Annualized return
        avg_return = statistics.mean(returns)
        annualized_return = (1 + avg_return / 100) ** 252 - 1

        # Annualized volatility
        volatility = self._calculate_volatility(returns)

        if volatility == 0:
            return 0.0

        # Sharpe ratio
        sharpe = (annualized_return - risk_free_rate) / (volatility / 100)

        return sharpe

    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float) -> float:
        """Calculate Sortino Ratio"""
        if len(returns) < 2:
            return 0.0

        # Annualized return
        avg_return = statistics.mean(returns)
        annualized_return = (1 + avg_return / 100) ** 252 - 1

        # Downside deviation
        downside_dev = self._calculate_downside_deviation(returns)

        if downside_dev == 0:
            return 0.0

        # Sortino ratio
        sortino = (annualized_return - risk_free_rate) / (downside_dev / 100)

        return sortino

    def _calculate_drawdown_metrics(self, returns_decimal: List[float]):
        """Calculate drawdown metrics"""
        if not returns_decimal:
            return 0.0, 0.0, 0.0

        # Build equity curve
        equity = [1.0]
        for r in returns_decimal:
            equity.append(equity[-1] * (1 + r))

        # Calculate drawdowns
        drawdowns = []
        peak = equity[0]

        for value in equity:
            if value > peak:
                peak = value

            dd = (value - peak) / peak * 100
            drawdowns.append(dd)

        max_dd = min(drawdowns) if drawdowns else 0.0
        current_dd = drawdowns[-1] if drawdowns else 0.0
        avg_dd = sum(drawdowns) / len(drawdowns) if drawdowns else 0.0

        return max_dd, current_dd, avg_dd

    def _calculate_beta(self, returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate beta relative to benchmark"""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 1.0

        # Covariance / Variance of benchmark
        n = len(returns)

        mean_r = sum(returns) / n
        mean_b = sum(benchmark_returns) / n

        covariance = sum((returns[i] - mean_r) * (benchmark_returns[i] - mean_b) for i in range(n)) / n
        variance_b = sum((b - mean_b) ** 2 for b in benchmark_returns) / n

        if variance_b == 0:
            return 1.0

        beta = covariance / variance_b

        return beta

    def _calculate_alpha(
        self,
        returns: List[float],
        benchmark_returns: List[float],
        risk_free_rate: float,
        beta: float
    ) -> float:
        """Calculate Jensen's alpha"""
        if len(returns) != len(benchmark_returns):
            return 0.0

        # Annualized returns
        avg_return = statistics.mean(returns)
        avg_benchmark = statistics.mean(benchmark_returns)

        annualized_return = (1 + avg_return / 100) ** 252 - 1
        annualized_benchmark = (1 + avg_benchmark / 100) ** 252 - 1

        # Jensen's alpha
        alpha = annualized_return - (risk_free_rate + beta * (annualized_benchmark - risk_free_rate))

        return alpha

    def _calculate_information_ratio(self, returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate Information Ratio"""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 0.0

        # Active returns
        active_returns = [returns[i] - benchmark_returns[i] for i in range(len(returns))]

        # Mean active return
        mean_active = statistics.mean(active_returns)

        # Tracking error (std dev of active returns)
        if len(active_returns) < 2:
            return 0.0

        tracking_error = statistics.stdev(active_returns)

        if tracking_error == 0:
            return 0.0

        # Information ratio
        ir = mean_active / tracking_error

        return ir

    def _calculate_calmar_ratio(self, returns: List[float], max_drawdown: float) -> float:
        """Calculate Calmar Ratio"""
        if abs(max_drawdown) == 0 or len(returns) < 2:
            return 0.0

        # Annualized return
        avg_return = statistics.mean(returns)
        annualized_return = (1 + avg_return / 100) ** 252 - 1

        # Calmar ratio
        calmar = annualized_return / abs(max_drawdown / 100)

        return calmar

    def _calculate_ulcer_index(self, returns_decimal: List[float]) -> float:
        """Calculate Ulcer Index (measure of downside volatility)"""
        if not returns_decimal:
            return 0.0

        # Build equity curve
        equity = [1.0]
        for r in returns_decimal:
            equity.append(equity[-1] * (1 + r))

        # Calculate percentage drawdowns squared
        squared_dd = []
        peak = equity[0]

        for value in equity:
            if value > peak:
                peak = value

            dd_pct = (value - peak) / peak * 100
            squared_dd.append(dd_pct ** 2)

        # Root mean square of drawdowns
        if not squared_dd:
            return 0.0

        ulcer = math.sqrt(sum(squared_dd) / len(squared_dd))

        return ulcer

    def _default_metrics(self, lookback_days: int) -> RiskMetrics:
        """Return default metrics when insufficient data"""
        return RiskMetrics(
            var_95=0.0,
            var_99=0.0,
            cvar_95=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            information_ratio=0.0,
            volatility=0.0,
            downside_deviation=0.0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            avg_drawdown=0.0,
            beta=1.0,
            alpha=0.0,
            calmar_ratio=0.0,
            ulcer_index=0.0,
            lookback_days=lookback_days
        )


# ============================================================================
# Utility Functions
# ============================================================================

def quick_risk_assessment(returns: List[float], risk_free_rate: float = 0.02) -> str:
    """
    Quick risk assessment

    Args:
        returns: List of daily returns (percentage)
        risk_free_rate: Annual risk-free rate

    Returns:
        String with risk assessment
    """
    calculator = RiskMetricsCalculator()
    metrics = calculator.calculate_metrics(returns, risk_free_rate)

    return f"""
Risk Assessment:
  Level: {metrics.get_risk_level().upper()}
  Rating: {metrics.get_rating()}

  Sharpe Ratio: {metrics.sharpe_ratio:.2f}
  Max Drawdown: {metrics.max_drawdown:.2f}%
  Volatility: {metrics.volatility:.2f}%
    """.strip()
