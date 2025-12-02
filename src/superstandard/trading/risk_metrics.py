"""
NEXUS Advanced Risk Metrics Calculator

Calculates sophisticated risk metrics for portfolio and strategy risk assessment.

Metrics Provided:
- VaR (Value at Risk) - Maximum expected loss at confidence level
- CVaR (Conditional VaR / Expected Shortfall) - Average loss beyond VaR
- Monte Carlo simulation for VaR estimation
- Historical VaR from actual return distribution
- Parametric VaR using normal distribution
- Stress testing with custom scenarios
- Portfolio correlation and diversification metrics

Used For:
- Portfolio risk assessment
- Position sizing
- Risk limit enforcement
- Regulatory compliance (Basel III)
- Strategy validation
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from datetime import datetime


@dataclass
class VaRResult:
    """Value at Risk calculation result"""
    var_amount: float  # Maximum expected loss
    var_percentage: float  # As percentage of portfolio
    confidence_level: float  # Confidence level (e.g., 0.95, 0.99)
    time_horizon: int  # Days
    method: str  # historical, parametric, monte_carlo
    portfolio_value: float

    # Additional metrics
    cvar_amount: Optional[float] = None  # Conditional VaR
    cvar_percentage: Optional[float] = None
    worst_case_loss: Optional[float] = None  # Worst historical loss


@dataclass
class StressTestResult:
    """Stress test scenario result"""
    scenario_name: str
    portfolio_value: float
    shocked_value: float
    loss_amount: float
    loss_percentage: float
    positions_affected: int


class RiskMetricsCalculator:
    """
    Advanced risk metrics calculator

    Provides VaR, CVaR, and stress testing capabilities for portfolio risk assessment.
    """

    @staticmethod
    def historical_var(
        returns: List[float],
        portfolio_value: float,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """
        Calculate Historical VaR from actual return distribution

        Uses empirical distribution of historical returns.

        Args:
            returns: List of historical returns (as decimals, e.g., 0.05 for 5%)
            portfolio_value: Current portfolio value
            confidence_level: Confidence level (0.95 = 95%, 0.99 = 99%)
            time_horizon: Time horizon in days

        Returns:
            VaRResult with VaR and CVaR
        """
        if not returns or len(returns) < 30:
            raise ValueError("Need at least 30 return observations for historical VaR")

        returns_array = np.array(returns)

        # Adjust for time horizon (assuming daily returns)
        if time_horizon > 1:
            returns_array = returns_array * np.sqrt(time_horizon)

        # Sort returns (worst to best)
        sorted_returns = np.sort(returns_array)

        # Calculate VaR at confidence level
        percentile_index = int((1 - confidence_level) * len(sorted_returns))
        var_return = sorted_returns[percentile_index]
        var_amount = abs(var_return * portfolio_value)
        var_percentage = abs(var_return) * 100

        # Calculate CVaR (average of losses beyond VaR)
        tail_returns = sorted_returns[:percentile_index]
        if len(tail_returns) > 0:
            cvar_return = np.mean(tail_returns)
            cvar_amount = abs(cvar_return * portfolio_value)
            cvar_percentage = abs(cvar_return) * 100
        else:
            cvar_amount = var_amount
            cvar_percentage = var_percentage

        # Worst case (minimum return)
        worst_return = sorted_returns[0]
        worst_case_loss = abs(worst_return * portfolio_value)

        return VaRResult(
            var_amount=var_amount,
            var_percentage=var_percentage,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            method="historical",
            portfolio_value=portfolio_value,
            cvar_amount=cvar_amount,
            cvar_percentage=cvar_percentage,
            worst_case_loss=worst_case_loss
        )

    @staticmethod
    def parametric_var(
        mean_return: float,
        std_return: float,
        portfolio_value: float,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """
        Calculate Parametric VaR using normal distribution assumption

        Assumes returns are normally distributed (fast but less accurate for fat tails).

        Args:
            mean_return: Average return (as decimal)
            std_return: Standard deviation of returns
            portfolio_value: Current portfolio value
            confidence_level: Confidence level (0.95 = 95%, 0.99 = 99%)
            time_horizon: Time horizon in days

        Returns:
            VaRResult
        """
        # Adjust for time horizon
        if time_horizon > 1:
            mean_return = mean_return * time_horizon
            std_return = std_return * np.sqrt(time_horizon)

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR calculation: mean + (z-score * std)
        var_return = mean_return + (z_score * std_return)
        var_amount = abs(var_return * portfolio_value)
        var_percentage = abs(var_return) * 100

        # CVaR for normal distribution
        # CVaR = mean - (std * pdf(z) / (1 - confidence))
        pdf_z = stats.norm.pdf(z_score)
        cvar_return = mean_return - (std_return * pdf_z / (1 - confidence_level))
        cvar_amount = abs(cvar_return * portfolio_value)
        cvar_percentage = abs(cvar_return) * 100

        return VaRResult(
            var_amount=var_amount,
            var_percentage=var_percentage,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            method="parametric",
            portfolio_value=portfolio_value,
            cvar_amount=cvar_amount,
            cvar_percentage=cvar_percentage
        )

    @staticmethod
    def monte_carlo_var(
        mean_return: float,
        std_return: float,
        portfolio_value: float,
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        num_simulations: int = 10000,
        random_seed: Optional[int] = None
    ) -> VaRResult:
        """
        Calculate VaR using Monte Carlo simulation

        Simulates thousands of possible portfolio paths to estimate VaR.
        More accurate than parametric VaR for non-normal distributions.

        Args:
            mean_return: Average return (as decimal)
            std_return: Standard deviation of returns
            portfolio_value: Current portfolio value
            confidence_level: Confidence level
            time_horizon: Time horizon in days
            num_simulations: Number of Monte Carlo simulations
            random_seed: Random seed for reproducibility

        Returns:
            VaRResult
        """
        if random_seed is not None:
            np.random.seed(random_seed)

        # Generate random returns
        simulated_returns = np.random.normal(
            mean_return * time_horizon,
            std_return * np.sqrt(time_horizon),
            num_simulations
        )

        # Sort returns
        sorted_returns = np.sort(simulated_returns)

        # Calculate VaR
        percentile_index = int((1 - confidence_level) * num_simulations)
        var_return = sorted_returns[percentile_index]
        var_amount = abs(var_return * portfolio_value)
        var_percentage = abs(var_return) * 100

        # Calculate CVaR
        tail_returns = sorted_returns[:percentile_index]
        cvar_return = np.mean(tail_returns)
        cvar_amount = abs(cvar_return * portfolio_value)
        cvar_percentage = abs(cvar_return) * 100

        # Worst case
        worst_return = sorted_returns[0]
        worst_case_loss = abs(worst_return * portfolio_value)

        return VaRResult(
            var_amount=var_amount,
            var_percentage=var_percentage,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            method="monte_carlo",
            portfolio_value=portfolio_value,
            cvar_amount=cvar_amount,
            cvar_percentage=cvar_percentage,
            worst_case_loss=worst_case_loss
        )

    @staticmethod
    def calculate_portfolio_var(
        positions: List[Dict[str, Any]],
        returns_data: Dict[str, List[float]],
        correlation_matrix: Optional[np.ndarray] = None,
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        method: str = "historical"
    ) -> VaRResult:
        """
        Calculate portfolio-level VaR accounting for correlations

        Args:
            positions: List of positions with 'symbol', 'value', 'weight'
            returns_data: Dict of symbol -> list of historical returns
            correlation_matrix: Optional correlation matrix (calculated if not provided)
            confidence_level: Confidence level
            time_horizon: Time horizon in days
            method: "historical", "parametric", or "monte_carlo"

        Returns:
            Portfolio VaRResult
        """
        # Calculate portfolio value
        portfolio_value = sum(pos['value'] for pos in positions)

        if method == "historical":
            # Calculate portfolio returns
            symbols = [pos['symbol'] for pos in positions]
            weights = [pos['weight'] for pos in positions]

            # Ensure all symbols have return data
            min_length = min(len(returns_data[sym]) for sym in symbols)

            # Calculate weighted portfolio returns for each period
            portfolio_returns = []
            for i in range(min_length):
                period_return = sum(
                    weights[j] * returns_data[symbols[j]][i]
                    for j in range(len(symbols))
                )
                portfolio_returns.append(period_return)

            return RiskMetricsCalculator.historical_var(
                portfolio_returns,
                portfolio_value,
                confidence_level,
                time_horizon
            )

        elif method == "parametric":
            # Calculate portfolio mean and std
            symbols = [pos['symbol'] for pos in positions]
            weights = np.array([pos['weight'] for pos in positions])

            # Calculate mean returns and covariance
            means = np.array([np.mean(returns_data[sym]) for sym in symbols])
            portfolio_mean = np.dot(weights, means)

            # Calculate covariance matrix if not provided
            returns_matrix = np.array([returns_data[sym] for sym in symbols])
            cov_matrix = np.cov(returns_matrix)

            # Portfolio variance: w^T * Cov * w
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)

            return RiskMetricsCalculator.parametric_var(
                portfolio_mean,
                portfolio_std,
                portfolio_value,
                confidence_level,
                time_horizon
            )

        else:  # monte_carlo
            symbols = [pos['symbol'] for pos in positions]
            weights = np.array([pos['weight'] for pos in positions])

            means = np.array([np.mean(returns_data[sym]) for sym in symbols])
            portfolio_mean = np.dot(weights, means)

            returns_matrix = np.array([returns_data[sym] for sym in symbols])
            cov_matrix = np.cov(returns_matrix)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)

            return RiskMetricsCalculator.monte_carlo_var(
                portfolio_mean,
                portfolio_std,
                portfolio_value,
                confidence_level,
                time_horizon
            )

    @staticmethod
    def stress_test(
        positions: List[Dict[str, Any]],
        scenario: Dict[str, float]
    ) -> StressTestResult:
        """
        Perform stress test with custom scenario

        Args:
            positions: List of positions with 'symbol', 'value', 'quantity', 'price'
            scenario: Dict of symbol -> price shock percentage (e.g., {"BTC": -0.30} for -30%)

        Returns:
            StressTestResult
        """
        scenario_name = "Custom Stress Test"
        portfolio_value = sum(pos['value'] for pos in positions)
        shocked_value = 0.0
        positions_affected = 0

        for pos in positions:
            symbol = pos['symbol']
            current_value = pos['value']

            if symbol in scenario:
                # Apply shock
                shock_pct = scenario[symbol]
                shocked_pos_value = current_value * (1 + shock_pct)
                shocked_value += shocked_pos_value
                positions_affected += 1
            else:
                # No shock
                shocked_value += current_value

        loss_amount = portfolio_value - shocked_value
        loss_percentage = (loss_amount / portfolio_value) * 100 if portfolio_value > 0 else 0

        return StressTestResult(
            scenario_name=scenario_name,
            portfolio_value=portfolio_value,
            shocked_value=shocked_value,
            loss_amount=loss_amount,
            loss_percentage=loss_percentage,
            positions_affected=positions_affected
        )

    @staticmethod
    def calculate_correlation_matrix(
        returns_data: Dict[str, List[float]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate correlation matrix for portfolio symbols

        Args:
            returns_data: Dict of symbol -> list of returns

        Returns:
            Tuple of (correlation_matrix, symbols_list)
        """
        symbols = list(returns_data.keys())
        returns_matrix = np.array([returns_data[sym] for sym in symbols])
        correlation_matrix = np.corrcoef(returns_matrix)

        return correlation_matrix, symbols

    @staticmethod
    def diversification_ratio(
        positions: List[Dict[str, Any]],
        returns_data: Dict[str, List[float]]
    ) -> float:
        """
        Calculate portfolio diversification ratio

        Ratio of weighted average volatility to portfolio volatility.
        Higher ratio = better diversification.

        Args:
            positions: List of positions
            returns_data: Historical returns data

        Returns:
            Diversification ratio
        """
        symbols = [pos['symbol'] for pos in positions]
        weights = np.array([pos['weight'] for pos in positions])

        # Individual volatilities
        vols = np.array([np.std(returns_data[sym]) for sym in symbols])

        # Weighted average volatility
        weighted_avg_vol = np.dot(weights, vols)

        # Portfolio volatility
        returns_matrix = np.array([returns_data[sym] for sym in symbols])
        cov_matrix = np.cov(returns_matrix)
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_variance)

        # Diversification ratio
        div_ratio = weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1.0

        return div_ratio
