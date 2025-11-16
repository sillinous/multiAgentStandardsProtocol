"""
Generate Short-term Forecast Agent
APQC Level 5 Atomic Task: 3.1.2.4.1 - Generate short-term forecast

This agent generates short-term forecasts (1-3 months) using multiple forecasting
methods including moving averages, exponential smoothing, linear regression, and
seasonal adjustments.

Process Group: 3.0 Market and Sell Products and Services
Parent Process: 3.1.2.4 Forecast Future Trends
Level: 5 (Atomic Task)
Dependencies: 3.1.2.2.6 (Moving Averages), 3.1.2.2.4 (Trend Direction)
Reusability: HIGH - used by many planning and decision agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import math

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Fallback implementations without numpy
    class np:
        @staticmethod
        def array(x):
            return x
        @staticmethod
        def mean(x):
            return sum(x) / len(x) if len(x) > 0 else 0
        @staticmethod
        def std(x):
            mean_val = sum(x) / len(x)
            variance = sum((xi - mean_val) ** 2 for xi in x) / len(x)
            return math.sqrt(variance)
        @staticmethod
        def polyfit(x, y, deg):
            # Simple linear regression for degree 1
            n = len(x)
            if n == 0:
                return [0, 0]
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            if n * sum_x2 - sum_x ** 2 == 0:
                return [0, sum_y / n]
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            return [slope, intercept]

logger = logging.getLogger(__name__)


class ForecastMethod(Enum):
    """Forecasting methods supported"""
    MOVING_AVERAGE = "moving_average"  # Simple moving average projection
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"  # Exponential smoothing
    LINEAR_REGRESSION = "linear_regression"  # Linear trend extrapolation
    SEASONAL_ADJUSTED = "seasonal_adjusted"  # Seasonal decomposition forecast
    ENSEMBLE = "ensemble"  # Weighted combination of methods


class ForecastHorizon(Enum):
    """Forecast time horizons"""
    VERY_SHORT = "very_short"  # 1-2 periods
    SHORT = "short"  # 3-10 periods
    MEDIUM = "medium"  # 11-30 periods
    LONG = "long"  # 31+ periods


@dataclass
class ForecastConfig:
    """Configuration for forecast generation"""
    method: ForecastMethod = ForecastMethod.EXPONENTIAL_SMOOTHING
    horizon: int = 10  # Number of periods to forecast
    confidence_level: float = 0.95  # For confidence bands
    alpha: Optional[float] = None  # Exponential smoothing parameter
    seasonal_period: Optional[int] = None  # For seasonal adjustment
    ma_window: int = 10  # Moving average window
    ensemble_weights: Optional[Dict[str, float]] = None  # For ensemble method

    def __post_init__(self):
        """Validate configuration"""
        if self.horizon < 1:
            raise ValueError("Forecast horizon must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        if self.method == ForecastMethod.EXPONENTIAL_SMOOTHING and self.alpha is None:
            # Standard alpha = 0.3 for short-term forecasting
            self.alpha = 0.3
        if self.alpha is not None and not 0 < self.alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")


@dataclass
class ForecastMetrics:
    """Forecast quality metrics"""
    mae: float  # Mean Absolute Error (on historical data)
    mape: float  # Mean Absolute Percentage Error
    rmse: float  # Root Mean Squared Error
    forecast_bias: float  # Average forecast error (positive = overforecast)
    trend_strength: float  # Strength of detected trend (0-1)
    seasonality_strength: float  # Strength of seasonality (0-1)


@dataclass
class ForecastPoint:
    """Single forecast point with confidence interval"""
    period: int  # Periods ahead from last data point
    value: float  # Forecasted value
    lower_bound: float  # Lower confidence bound
    upper_bound: float  # Upper confidence bound
    uncertainty: float  # Forecast uncertainty (increases with horizon)


@dataclass
class ShortTermForecastResult:
    """Result of short-term forecast"""
    method: str
    forecast_points: List[ForecastPoint]
    metrics: ForecastMetrics
    historical_fit: List[float]  # Fitted values for historical data
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    calculation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "method": self.method,
            "forecast_points": [
                {
                    "period": fp.period,
                    "value": round(fp.value, 4),
                    "lower_bound": round(fp.lower_bound, 4),
                    "upper_bound": round(fp.upper_bound, 4),
                    "uncertainty": round(fp.uncertainty, 4)
                }
                for fp in self.forecast_points
            ],
            "metrics": {
                "mae": round(self.metrics.mae, 4),
                "mape": round(self.metrics.mape, 4),
                "rmse": round(self.metrics.rmse, 4),
                "forecast_bias": round(self.metrics.forecast_bias, 4),
                "trend_strength": round(self.metrics.trend_strength, 4),
                "seasonality_strength": round(self.metrics.seasonality_strength, 4)
            },
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "calculation_time_ms": round(self.calculation_time_ms, 2)
        }


class GenerateShortTermForecastAgent:
    """
    Level 5 Atomic Task Agent: Generate short-term forecast

    APQC Process: 3.1.2.4.1 - Generate short-term forecast

    Responsibilities:
    - Generate forecasts for 1-3 months (configurable horizon)
    - Calculate confidence intervals
    - Apply multiple forecasting methods
    - Adjust for seasonality
    - Measure forecast accuracy
    - Quantify forecast uncertainty

    Methodology:
    - Exponential smoothing (default, responsive to recent changes)
    - Linear regression (captures trends)
    - Moving average (smooth projection)
    - Seasonal adjustment (handles periodic patterns)
    - Ensemble methods (combines multiple approaches)

    Value Proposition:
    - Data-driven short-term planning
    - Quantified forecast uncertainty
    - Multiple method comparison
    - Confidence intervals for risk assessment
    - Foundation for inventory, staffing, budgeting

    Reusability: HIGH
    - Used by inventory planning agents
    - Used by demand forecasting agents
    - Used by budget planning agents
    - Used by capacity planning agents
    """

    def __init__(self):
        self.agent_id = "generate_short_term_forecast_agent"
        self.agent_name = "Generate Short-term Forecast Agent"
        self.version = "1.0.0"
        self.apqc_process = "3.1.2.4.1"

        logger.info(f"🔮 {self.agent_name} initialized (APQC {self.apqc_process})")

    async def execute(
        self,
        time_series: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Generate short-term forecast

        Args:
            time_series: Historical data
            config: Forecast configuration

        Returns:
            ShortTermForecastResult with forecasts and confidence intervals

        Raises:
            ValueError: If input data is invalid
        """
        start_time = datetime.now()

        if not time_series:
            raise ValueError("Time series cannot be empty")

        if len(time_series) < 3:
            raise ValueError("Time series must have at least 3 data points")

        # Generate forecast based on method
        if config.method == ForecastMethod.MOVING_AVERAGE:
            result = self._forecast_moving_average(time_series, config)
        elif config.method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            result = self._forecast_exponential_smoothing(time_series, config)
        elif config.method == ForecastMethod.LINEAR_REGRESSION:
            result = self._forecast_linear_regression(time_series, config)
        elif config.method == ForecastMethod.SEASONAL_ADJUSTED:
            result = self._forecast_seasonal_adjusted(time_series, config)
        elif config.method == ForecastMethod.ENSEMBLE:
            result = self._forecast_ensemble(time_series, config)
        else:
            raise ValueError(f"Unsupported forecast method: {config.method}")

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds() * 1000
        result.calculation_time_ms = duration

        logger.info(
            f"✅ Forecast generated: {config.method.value}, "
            f"horizon={config.horizon}, MAE={result.metrics.mae:.2f}, "
            f"time={duration:.2f}ms"
        )

        return result

    def _forecast_moving_average(
        self,
        data: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Forecast using moving average method

        Projects the last moving average value forward
        """
        window = min(config.ma_window, len(data))

        # Calculate moving average for historical data
        ma_values = []
        for i in range(len(data)):
            if i < window - 1:
                ma_values.append(float('nan'))
            else:
                ma = sum(data[i - window + 1:i + 1]) / window
                ma_values.append(ma)

        # Last MA value is the forecast
        last_ma = ma_values[-1] if not math.isnan(ma_values[-1]) else data[-1]

        # Calculate forecast uncertainty (std of recent data)
        recent_data = data[-window:]
        std = self._calculate_std(recent_data)

        # Generate forecast points
        forecast_points = []
        z_critical = self._get_z_critical(config.confidence_level)

        for h in range(1, config.horizon + 1):
            # Uncertainty increases with horizon
            uncertainty = std * math.sqrt(h)
            margin = z_critical * uncertainty

            forecast_points.append(ForecastPoint(
                period=h,
                value=last_ma,
                lower_bound=last_ma - margin,
                upper_bound=last_ma + margin,
                uncertainty=uncertainty
            ))

        # Calculate metrics
        metrics = self._calculate_metrics(data, ma_values, config)

        return ShortTermForecastResult(
            method=config.method.value,
            forecast_points=forecast_points,
            historical_fit=ma_values,
            metrics=metrics,
            metadata={
                "window_size": window,
                "last_ma": round(last_ma, 4),
                "forecast_std": round(std, 4)
            }
        )

    def _forecast_exponential_smoothing(
        self,
        data: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Forecast using exponential smoothing

        Uses weighted average with exponential decay
        """
        alpha = config.alpha

        # Calculate smoothed values for historical data
        smoothed = [data[0]]  # Initialize with first value

        for i in range(1, len(data)):
            smooth_value = alpha * data[i] + (1 - alpha) * smoothed[i - 1]
            smoothed.append(smooth_value)

        # Last smoothed value is base forecast
        last_smooth = smoothed[-1]

        # Calculate residuals for uncertainty
        residuals = [data[i] - smoothed[i] for i in range(len(data))]
        residual_std = self._calculate_std(residuals)

        # Generate forecast points
        forecast_points = []
        z_critical = self._get_z_critical(config.confidence_level)

        for h in range(1, config.horizon + 1):
            # For simple exponential smoothing, forecast is flat
            # Uncertainty increases with horizon
            uncertainty = residual_std * math.sqrt(h)
            margin = z_critical * uncertainty

            forecast_points.append(ForecastPoint(
                period=h,
                value=last_smooth,
                lower_bound=last_smooth - margin,
                upper_bound=last_smooth + margin,
                uncertainty=uncertainty
            ))

        # Calculate metrics
        metrics = self._calculate_metrics(data, smoothed, config)

        return ShortTermForecastResult(
            method=config.method.value,
            forecast_points=forecast_points,
            historical_fit=smoothed,
            metrics=metrics,
            metadata={
                "alpha": alpha,
                "last_smoothed": round(last_smooth, 4),
                "residual_std": round(residual_std, 4)
            }
        )

    def _forecast_linear_regression(
        self,
        data: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Forecast using linear regression

        Extrapolates the linear trend
        """
        # Fit linear regression to historical data
        x = list(range(len(data)))
        y = data

        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate fitted values
        fitted = [slope * xi + intercept for xi in x]

        # Calculate residual standard deviation
        residuals = [data[i] - fitted[i] for i in range(len(data))]
        residual_std = self._calculate_std(residuals)

        # Generate forecast points
        forecast_points = []
        z_critical = self._get_z_critical(config.confidence_level)

        for h in range(1, config.horizon + 1):
            future_x = len(data) + h - 1
            forecast_value = slope * future_x + intercept

            # Uncertainty increases with distance from data
            # Formula: std * sqrt(1 + 1/n + (x - x_mean)^2 / sum((x - x_mean)^2))
            x_mean = sum(x) / len(x)
            x_var_sum = sum((xi - x_mean) ** 2 for xi in x)

            leverage = 1 + 1/len(data) + (future_x - x_mean) ** 2 / x_var_sum
            uncertainty = residual_std * math.sqrt(leverage * h)
            margin = z_critical * uncertainty

            forecast_points.append(ForecastPoint(
                period=h,
                value=forecast_value,
                lower_bound=forecast_value - margin,
                upper_bound=forecast_value + margin,
                uncertainty=uncertainty
            ))

        # Calculate metrics
        metrics = self._calculate_metrics(data, fitted, config)

        return ShortTermForecastResult(
            method=config.method.value,
            forecast_points=forecast_points,
            historical_fit=fitted,
            metrics=metrics,
            metadata={
                "slope": round(slope, 6),
                "intercept": round(intercept, 4),
                "residual_std": round(residual_std, 4)
            }
        )

    def _forecast_seasonal_adjusted(
        self,
        data: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Forecast with seasonal adjustment

        Decomposes into trend + seasonal + residual
        """
        if config.seasonal_period is None:
            # Auto-detect seasonal period
            config.seasonal_period = self._detect_seasonal_period(data)

        period = config.seasonal_period

        if period < 2 or len(data) < 2 * period:
            # Not enough data for seasonal decomposition, fall back to exponential smoothing
            logger.warning("Insufficient data for seasonal forecast, using exponential smoothing")
            return self._forecast_exponential_smoothing(data, config)

        # Calculate seasonal indices
        seasonal_indices = self._calculate_seasonal_indices(data, period)

        # Deseasonalize data
        deseasonalized = []
        for i, value in enumerate(data):
            season_idx = i % period
            deseasonalized.append(value / seasonal_indices[season_idx])

        # Fit trend to deseasonalized data
        x = list(range(len(deseasonalized)))
        coeffs = np.polyfit(x, deseasonalized, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate fitted values
        fitted = []
        for i in range(len(data)):
            trend_value = slope * i + intercept
            season_idx = i % period
            fitted_value = trend_value * seasonal_indices[season_idx]
            fitted.append(fitted_value)

        # Calculate residual standard deviation
        residuals = [data[i] - fitted[i] for i in range(len(data))]
        residual_std = self._calculate_std(residuals)

        # Generate forecast points
        forecast_points = []
        z_critical = self._get_z_critical(config.confidence_level)

        for h in range(1, config.horizon + 1):
            future_x = len(data) + h - 1
            trend_value = slope * future_x + intercept
            season_idx = future_x % period
            forecast_value = trend_value * seasonal_indices[season_idx]

            # Uncertainty increases with horizon
            uncertainty = residual_std * math.sqrt(h)
            margin = z_critical * uncertainty

            forecast_points.append(ForecastPoint(
                period=h,
                value=forecast_value,
                lower_bound=forecast_value - margin,
                upper_bound=forecast_value + margin,
                uncertainty=uncertainty
            ))

        # Calculate metrics
        metrics = self._calculate_metrics(data, fitted, config)

        return ShortTermForecastResult(
            method=config.method.value,
            forecast_points=forecast_points,
            historical_fit=fitted,
            metrics=metrics,
            metadata={
                "seasonal_period": period,
                "seasonal_indices": [round(si, 4) for si in seasonal_indices],
                "trend_slope": round(slope, 6),
                "residual_std": round(residual_std, 4)
            }
        )

    def _forecast_ensemble(
        self,
        data: List[float],
        config: ForecastConfig
    ) -> ShortTermForecastResult:
        """
        Ensemble forecast combining multiple methods

        Weighted average of different forecasting approaches
        """
        # Default weights if not provided
        if config.ensemble_weights is None:
            weights = {
                "exponential_smoothing": 0.4,
                "linear_regression": 0.3,
                "moving_average": 0.3
            }
        else:
            weights = config.ensemble_weights

        # Generate forecasts using each method
        forecasts = {}

        if weights.get("moving_average", 0) > 0:
            ma_config = ForecastConfig(
                method=ForecastMethod.MOVING_AVERAGE,
                horizon=config.horizon,
                confidence_level=config.confidence_level,
                ma_window=config.ma_window
            )
            forecasts["moving_average"] = self._forecast_moving_average(data, ma_config)

        if weights.get("exponential_smoothing", 0) > 0:
            es_config = ForecastConfig(
                method=ForecastMethod.EXPONENTIAL_SMOOTHING,
                horizon=config.horizon,
                confidence_level=config.confidence_level,
                alpha=config.alpha
            )
            forecasts["exponential_smoothing"] = self._forecast_exponential_smoothing(data, es_config)

        if weights.get("linear_regression", 0) > 0:
            lr_config = ForecastConfig(
                method=ForecastMethod.LINEAR_REGRESSION,
                horizon=config.horizon,
                confidence_level=config.confidence_level
            )
            forecasts["linear_regression"] = self._forecast_linear_regression(data, lr_config)

        # Combine forecasts
        forecast_points = []
        for h in range(config.horizon):
            combined_value = 0
            combined_lower = 0
            combined_upper = 0
            combined_uncertainty = 0

            for method_name, weight in weights.items():
                if method_name in forecasts:
                    fp = forecasts[method_name].forecast_points[h]
                    combined_value += weight * fp.value
                    combined_lower += weight * fp.lower_bound
                    combined_upper += weight * fp.upper_bound
                    combined_uncertainty += weight * fp.uncertainty

            forecast_points.append(ForecastPoint(
                period=h + 1,
                value=combined_value,
                lower_bound=combined_lower,
                upper_bound=combined_upper,
                uncertainty=combined_uncertainty
            ))

        # Use exponential smoothing fitted values as baseline
        fitted = forecasts.get("exponential_smoothing", forecasts[list(forecasts.keys())[0]]).historical_fit

        # Calculate combined metrics
        metrics = self._calculate_metrics(data, fitted, config)

        return ShortTermForecastResult(
            method=config.method.value,
            forecast_points=forecast_points,
            historical_fit=fitted,
            metrics=metrics,
            metadata={
                "ensemble_weights": weights,
                "methods_used": list(forecasts.keys())
            }
        )

    def _calculate_metrics(
        self,
        actual: List[float],
        fitted: List[float],
        config: ForecastConfig
    ) -> ForecastMetrics:
        """Calculate forecast quality metrics"""

        # Filter out NaN values
        valid_pairs = [(a, f) for a, f in zip(actual, fitted) if not math.isnan(f)]

        if not valid_pairs:
            return ForecastMetrics(
                mae=0, mape=0, rmse=0, forecast_bias=0,
                trend_strength=0, seasonality_strength=0
            )

        actual_clean = [pair[0] for pair in valid_pairs]
        fitted_clean = [pair[1] for pair in valid_pairs]

        # Mean Absolute Error
        errors = [abs(a - f) for a, f in zip(actual_clean, fitted_clean)]
        mae = sum(errors) / len(errors)

        # Mean Absolute Percentage Error
        mape_values = [abs((a - f) / a) * 100 for a, f in zip(actual_clean, fitted_clean) if a != 0]
        mape = sum(mape_values) / len(mape_values) if mape_values else 0

        # Root Mean Squared Error
        squared_errors = [(a - f) ** 2 for a, f in zip(actual_clean, fitted_clean)]
        rmse = math.sqrt(sum(squared_errors) / len(squared_errors))

        # Forecast Bias
        bias_errors = [a - f for a, f in zip(actual_clean, fitted_clean)]
        forecast_bias = sum(bias_errors) / len(bias_errors)

        # Trend strength (R² of linear regression)
        trend_strength = self._calculate_trend_strength(actual_clean)

        # Seasonality strength (if seasonal period provided)
        seasonality_strength = 0
        if config.seasonal_period is not None:
            seasonality_strength = self._calculate_seasonality_strength(actual_clean, config.seasonal_period)

        return ForecastMetrics(
            mae=mae,
            mape=mape,
            rmse=rmse,
            forecast_bias=forecast_bias,
            trend_strength=trend_strength,
            seasonality_strength=seasonality_strength
        )

    def _calculate_trend_strength(self, data: List[float]) -> float:
        """Calculate trend strength using R²"""
        if len(data) < 3:
            return 0

        x = list(range(len(data)))
        coeffs = np.polyfit(x, data, 1)

        # Predicted values
        y_pred = [coeffs[0] * xi + coeffs[1] for xi in x]

        # R²
        y_mean = sum(data) / len(data)
        ss_tot = sum((yi - y_mean) ** 2 for yi in data)
        ss_res = sum((data[i] - y_pred[i]) ** 2 for i in range(len(data)))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return max(0, min(1, r_squared))

    def _calculate_seasonality_strength(self, data: List[float], period: int) -> float:
        """Calculate seasonality strength"""
        if len(data) < 2 * period:
            return 0

        # Calculate seasonal indices
        seasonal_indices = self._calculate_seasonal_indices(data, period)

        # Variance of seasonal indices indicates seasonality strength
        mean_index = sum(seasonal_indices) / len(seasonal_indices)
        variance = sum((si - mean_index) ** 2 for si in seasonal_indices) / len(seasonal_indices)

        # Normalize to 0-1 range
        strength = min(1, variance * 10)  # Scale factor

        return strength

    def _calculate_seasonal_indices(self, data: List[float], period: int) -> List[float]:
        """Calculate seasonal indices"""
        seasonal_sums = [0.0] * period
        seasonal_counts = [0] * period

        for i, value in enumerate(data):
            season_idx = i % period
            seasonal_sums[season_idx] += value
            seasonal_counts[season_idx] += 1

        # Average for each season
        seasonal_averages = [
            seasonal_sums[i] / seasonal_counts[i] if seasonal_counts[i] > 0 else 0
            for i in range(period)
        ]

        # Normalize so average index is 1.0
        overall_avg = sum(seasonal_averages) / period if period > 0 else 1

        if overall_avg == 0:
            return [1.0] * period

        seasonal_indices = [avg / overall_avg for avg in seasonal_averages]

        return seasonal_indices

    def _detect_seasonal_period(self, data: List[float]) -> int:
        """Auto-detect seasonal period"""
        # Simple autocorrelation-based detection
        # Try common periods: 7 (weekly), 12 (monthly), 4 (quarterly)

        if len(data) < 14:
            return 4  # Default to quarterly

        max_period = min(len(data) // 2, 12)
        best_period = 4
        best_correlation = 0

        for period in [4, 7, 12]:
            if period > max_period:
                continue

            correlation = self._calculate_autocorrelation(data, period)
            if correlation > best_correlation:
                best_correlation = correlation
                best_period = period

        return best_period

    def _calculate_autocorrelation(self, data: List[float], lag: int) -> float:
        """Calculate autocorrelation at given lag"""
        if len(data) <= lag:
            return 0

        mean_val = sum(data) / len(data)

        numerator = sum(
            (data[i] - mean_val) * (data[i - lag] - mean_val)
            for i in range(lag, len(data))
        )

        denominator = sum((x - mean_val) ** 2 for x in data)

        if denominator == 0:
            return 0

        return numerator / denominator

    def _calculate_std(self, data: List[float]) -> float:
        """Calculate standard deviation"""
        if len(data) < 2:
            return 0

        mean_val = sum(data) / len(data)
        variance = sum((x - mean_val) ** 2 for x in data) / len(data)

        return math.sqrt(variance)

    def _get_z_critical(self, confidence_level: float) -> float:
        """Get z critical value for confidence level"""
        # Common z-values
        z_values = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }

        return z_values.get(confidence_level, 1.96)


# Example usage
async def main():
    """Example usage of GenerateShortTermForecastAgent"""

    # Sample time series data (e.g., monthly sales)
    sales_data = [
        100, 105, 110, 108, 115, 120, 118, 125, 130, 128,
        135, 140, 138, 145, 150, 148, 155, 160, 158, 165,
        170, 168, 175, 180, 178, 185, 190, 188, 195, 200
    ]

    agent = GenerateShortTermForecastAgent()

    # Example 1: Exponential smoothing forecast
    print("\n=== Exponential Smoothing Forecast ===")
    es_config = ForecastConfig(
        method=ForecastMethod.EXPONENTIAL_SMOOTHING,
        horizon=6,  # 6 periods ahead
        confidence_level=0.95,
        alpha=0.3
    )

    es_result = await agent.execute(sales_data, es_config)

    print(f"Method: {es_result.method}")
    print(f"Metrics:")
    print(f"  MAE: {es_result.metrics.mae:.2f}")
    print(f"  MAPE: {es_result.metrics.mape:.2f}%")
    print(f"  RMSE: {es_result.metrics.rmse:.2f}")
    print(f"  Bias: {es_result.metrics.forecast_bias:.2f}")
    print(f"\nForecast (next 6 periods):")
    for fp in es_result.forecast_points:
        print(f"  Period +{fp.period}: {fp.value:.2f} "
              f"[{fp.lower_bound:.2f}, {fp.upper_bound:.2f}]")

    # Example 2: Linear regression forecast
    print("\n=== Linear Regression Forecast ===")
    lr_config = ForecastConfig(
        method=ForecastMethod.LINEAR_REGRESSION,
        horizon=6,
        confidence_level=0.95
    )

    lr_result = await agent.execute(sales_data, lr_config)

    print(f"Trend slope: {lr_result.metadata['slope']:.4f}")
    print(f"Forecast (next 6 periods):")
    for fp in lr_result.forecast_points[:3]:  # Show first 3
        print(f"  Period +{fp.period}: {fp.value:.2f} "
              f"[{fp.lower_bound:.2f}, {fp.upper_bound:.2f}]")

    # Example 3: Seasonal adjusted forecast
    print("\n=== Seasonal Adjusted Forecast ===")
    seasonal_config = ForecastConfig(
        method=ForecastMethod.SEASONAL_ADJUSTED,
        horizon=6,
        confidence_level=0.95,
        seasonal_period=4  # Quarterly seasonality
    )

    seasonal_result = await agent.execute(sales_data, seasonal_config)

    print(f"Seasonal period: {seasonal_result.metadata['seasonal_period']}")
    print(f"Seasonal indices: {seasonal_result.metadata['seasonal_indices']}")
    print(f"Seasonality strength: {seasonal_result.metrics.seasonality_strength:.2%}")
    print(f"Forecast (next 6 periods):")
    for fp in seasonal_result.forecast_points[:3]:  # Show first 3
        print(f"  Period +{fp.period}: {fp.value:.2f}")

    # Example 4: Ensemble forecast
    print("\n=== Ensemble Forecast ===")
    ensemble_config = ForecastConfig(
        method=ForecastMethod.ENSEMBLE,
        horizon=6,
        confidence_level=0.95,
        ensemble_weights={
            "exponential_smoothing": 0.4,
            "linear_regression": 0.4,
            "moving_average": 0.2
        }
    )

    ensemble_result = await agent.execute(sales_data, ensemble_config)

    print(f"Methods: {ensemble_result.metadata['methods_used']}")
    print(f"Weights: {ensemble_result.metadata['ensemble_weights']}")
    print(f"Forecast (next 6 periods):")
    for fp in ensemble_result.forecast_points:
        print(f"  Period +{fp.period}: {fp.value:.2f} "
              f"[{fp.lower_bound:.2f}, {fp.upper_bound:.2f}] "
              f"±{fp.uncertainty:.2f}")

    # Compare methods
    print("\n=== Method Comparison ===")
    print(f"{'Method':<25} {'MAE':<10} {'MAPE':<10} {'Bias':<10}")
    print("-" * 55)
    for name, result in [
        ("Exponential Smoothing", es_result),
        ("Linear Regression", lr_result),
        ("Seasonal Adjusted", seasonal_result),
        ("Ensemble", ensemble_result)
    ]:
        print(f"{name:<25} {result.metrics.mae:<10.2f} "
              f"{result.metrics.mape:<10.2f} {result.metrics.forecast_bias:<10.2f}")


if __name__ == "__main__":
    asyncio.run(main())
