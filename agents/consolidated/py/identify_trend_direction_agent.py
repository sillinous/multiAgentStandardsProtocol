"""
Identify Trend Direction Agent
APQC Level 5 Atomic Task: 3.1.2.2.4 - Identify trend direction

This agent classifies market trend direction and strength using multiple indicators
including moving averages, slope analysis, and momentum metrics.

Process Group: 3.0 Market and Sell Products and Services
Parent Process: 3.1.2 Analyze Market Trends
Level: 5 (Atomic Task)
Dependencies: 3.1.2.2.6 (Moving Averages)
Reusability: HIGH - used by many trend analysis and trading agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
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
        def isnan(x):
            return math.isnan(x) if isinstance(x, (int, float)) else False
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
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            return [slope, intercept]

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction classifications"""
    STRONG_UPTREND = "strong_uptrend"      # Clear upward momentum
    UPTREND = "uptrend"                    # Moderate upward trend
    SIDEWAYS = "sideways"                  # No clear direction
    DOWNTREND = "downtrend"                # Moderate downward trend
    STRONG_DOWNTREND = "strong_downtrend"  # Clear downward momentum


class TrendStrength(Enum):
    """Trend strength classifications"""
    VERY_WEAK = "very_weak"    # 0-20%
    WEAK = "weak"              # 20-40%
    MODERATE = "moderate"      # 40-60%
    STRONG = "strong"          # 60-80%
    VERY_STRONG = "very_strong"  # 80-100%


@dataclass
class TrendMetrics:
    """Comprehensive trend metrics"""
    slope: float  # Linear regression slope
    angle_degrees: float  # Trend angle in degrees
    r_squared: float  # Regression R² (goodness of fit)
    momentum: float  # Rate of change
    volatility: float  # Price volatility
    consistency: float  # Trend consistency score (0-1)


@dataclass
class TrendDirectionResult:
    """Result of trend direction analysis"""
    direction: TrendDirection
    strength: TrendStrength
    confidence: float  # 0-1
    metrics: TrendMetrics
    supporting_indicators: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    calculation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "direction": self.direction.value,
            "strength": self.strength.value,
            "confidence": round(self.confidence, 4),
            "metrics": {
                "slope": round(self.metrics.slope, 6),
                "angle_degrees": round(self.metrics.angle_degrees, 2),
                "r_squared": round(self.metrics.r_squared, 4),
                "momentum": round(self.metrics.momentum, 4),
                "volatility": round(self.metrics.volatility, 4),
                "consistency": round(self.metrics.consistency, 4)
            },
            "supporting_indicators": self.supporting_indicators,
            "timestamp": self.timestamp,
            "calculation_time_ms": round(self.calculation_time_ms, 2)
        }


class IdentifyTrendDirectionAgent:
    """
    Level 5 Atomic Task Agent: Identify trend direction

    APQC Process: 3.1.2.2.4 - Identify trend direction

    Responsibilities:
    - Classify trend direction (uptrend, downtrend, sideways)
    - Measure trend strength (weak, moderate, strong)
    - Calculate trend angle and slope
    - Assess trend consistency
    - Provide confidence scores
    - Generate actionable signals

    Methodology:
    - Linear regression for trend slope
    - Moving average comparisons
    - Momentum analysis (rate of change)
    - Volatility assessment
    - Multi-factor confidence scoring

    Value Proposition:
    - Clear classification of market direction
    - Quantified trend strength metrics
    - Data-driven decision support
    - Foundation for trading strategies
    - Risk assessment input

    Reusability: HIGH
    - Used by forecasting agents
    - Used by signal generators
    - Used by risk assessment
    - Used by portfolio management
    """

    def __init__(self):
        self.agent_id = "identify_trend_direction_agent"
        self.agent_name = "Identify Trend Direction Agent"
        self.version = "1.0.0"
        self.apqc_process = "3.1.2.2.4"

        # Classification thresholds
        self.SLOPE_THRESHOLD_STRONG = 0.05  # 5% slope for strong trend
        self.SLOPE_THRESHOLD_MODERATE = 0.02  # 2% slope for moderate trend
        self.R_SQUARED_THRESHOLD = 0.7  # R² threshold for trend consistency

        logger.info(f"📈 {self.agent_name} initialized (APQC {self.apqc_process})")

    async def execute(
        self,
        time_series: List[float],
        lookback_period: int = 20,
        use_ma_confirmation: bool = True
    ) -> TrendDirectionResult:
        """
        Identify trend direction and strength

        Args:
            time_series: Price or value data
            lookback_period: Number of periods to analyze
            use_ma_confirmation: Use moving averages for confirmation

        Returns:
            TrendDirectionResult with direction, strength, and metrics
        """
        start_time = datetime.now()

        if not time_series:
            raise ValueError("Time series cannot be empty")

        if len(time_series) < lookback_period:
            lookback_period = len(time_series)
            logger.warning(f"Lookback period adjusted to {lookback_period}")

        # Analyze the most recent period
        recent_data = time_series[-lookback_period:]

        # Calculate trend metrics
        metrics = self._calculate_trend_metrics(recent_data)

        # Classify direction
        direction = self._classify_direction(metrics, recent_data)

        # Determine strength
        strength = self._determine_strength(metrics)

        # Calculate confidence
        confidence = self._calculate_confidence(metrics, recent_data)

        # Add supporting indicators
        supporting = {}
        if use_ma_confirmation:
            supporting["ma_slope"] = self._calculate_ma_slope(recent_data)
            supporting["ma_position"] = self._analyze_price_vs_ma(recent_data)

        supporting["higher_highs"] = self._count_higher_highs(recent_data)
        supporting["higher_lows"] = self._count_higher_lows(recent_data)

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = TrendDirectionResult(
            direction=direction,
            strength=strength,
            confidence=confidence,
            metrics=metrics,
            supporting_indicators=supporting,
            calculation_time_ms=duration
        )

        logger.info(
            f"✅ Trend identified: {direction.value} ({strength.value}) "
            f"confidence={confidence:.2f}, slope={metrics.slope:.4f}"
        )

        return result

    def _calculate_trend_metrics(self, data: List[float]) -> TrendMetrics:
        """Calculate comprehensive trend metrics"""

        # Linear regression for trend slope
        x = list(range(len(data)))
        y = data

        # Calculate slope using polyfit
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Normalize slope relative to price level
        mean_price = sum(data) / len(data)
        normalized_slope = slope / mean_price if mean_price != 0 else 0

        # Calculate angle in degrees
        angle_radians = math.atan(slope)
        angle_degrees = math.degrees(angle_radians)

        # Calculate R² (goodness of fit)
        r_squared = self._calculate_r_squared(x, y, coeffs)

        # Calculate momentum (rate of change)
        if len(data) >= 2:
            momentum = (data[-1] - data[0]) / data[0] if data[0] != 0 else 0
        else:
            momentum = 0

        # Calculate volatility (standard deviation)
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        volatility = math.sqrt(variance) / mean if mean != 0 else 0

        # Calculate consistency (based on R² and volatility)
        consistency = r_squared * (1 - min(volatility, 1))

        return TrendMetrics(
            slope=normalized_slope,
            angle_degrees=angle_degrees,
            r_squared=r_squared,
            momentum=momentum,
            volatility=volatility,
            consistency=consistency
        )

    def _calculate_r_squared(self, x: List, y: List, coeffs: List) -> float:
        """Calculate R² (coefficient of determination)"""
        # Predicted values
        y_pred = [coeffs[0] * xi + coeffs[1] for xi in x]

        # Mean of actual values
        y_mean = sum(y) / len(y)

        # Total sum of squares
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)

        # Residual sum of squares
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(len(y)))

        # R²
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return max(0, min(1, r_squared))  # Clamp between 0 and 1

    def _classify_direction(
        self,
        metrics: TrendMetrics,
        data: List[float]
    ) -> TrendDirection:
        """Classify trend direction based on metrics"""

        slope = metrics.slope

        # Strong trends
        if slope > self.SLOPE_THRESHOLD_STRONG:
            return TrendDirection.STRONG_UPTREND
        elif slope < -self.SLOPE_THRESHOLD_STRONG:
            return TrendDirection.STRONG_DOWNTREND

        # Moderate trends
        elif slope > self.SLOPE_THRESHOLD_MODERATE:
            return TrendDirection.UPTREND
        elif slope < -self.SLOPE_THRESHOLD_MODERATE:
            return TrendDirection.DOWNTREND

        # Sideways
        else:
            return TrendDirection.SIDEWAYS

    def _determine_strength(self, metrics: TrendMetrics) -> TrendStrength:
        """Determine trend strength"""

        # Combine multiple factors for strength assessment
        strength_score = (
            abs(metrics.slope) * 100 +  # Slope contribution
            metrics.r_squared * 50 +     # Consistency contribution
            abs(metrics.momentum) * 30   # Momentum contribution
        ) / 180  # Normalize to 0-1

        strength_score = max(0, min(1, strength_score))

        if strength_score >= 0.8:
            return TrendStrength.VERY_STRONG
        elif strength_score >= 0.6:
            return TrendStrength.STRONG
        elif strength_score >= 0.4:
            return TrendStrength.MODERATE
        elif strength_score >= 0.2:
            return TrendStrength.WEAK
        else:
            return TrendStrength.VERY_WEAK

    def _calculate_confidence(
        self,
        metrics: TrendMetrics,
        data: List[float]
    ) -> float:
        """Calculate confidence in trend identification"""

        # Factors contributing to confidence:
        # 1. R² (how well data fits trend line)
        # 2. Consistency score
        # 3. Data sufficiency
        # 4. Volatility (lower is better for confidence)

        r2_confidence = metrics.r_squared
        consistency_confidence = metrics.consistency
        data_confidence = min(len(data) / 30, 1.0)  # 30+ points = full confidence
        volatility_confidence = max(0, 1 - metrics.volatility * 2)

        # Weighted average
        confidence = (
            r2_confidence * 0.4 +
            consistency_confidence * 0.3 +
            data_confidence * 0.2 +
            volatility_confidence * 0.1
        )

        return max(0, min(1, confidence))

    def _calculate_ma_slope(self, data: List[float], window: int = 10) -> float:
        """Calculate slope of moving average"""
        if len(data) < window:
            window = len(data)

        # Simple MA of recent data
        ma_values = []
        for i in range(window - 1, len(data)):
            ma = sum(data[i - window + 1:i + 1]) / window
            ma_values.append(ma)

        if len(ma_values) < 2:
            return 0

        # Slope of MA
        x = list(range(len(ma_values)))
        coeffs = np.polyfit(x, ma_values, 1)

        return coeffs[0] / (sum(ma_values) / len(ma_values))

    def _analyze_price_vs_ma(self, data: List[float], window: int = 10) -> str:
        """Analyze price position relative to moving average"""
        if len(data) < window:
            return "insufficient_data"

        ma = sum(data[-window:]) / window
        current_price = data[-1]

        diff_pct = (current_price - ma) / ma if ma != 0 else 0

        if diff_pct > 0.02:  # 2% above MA
            return "above_ma"
        elif diff_pct < -0.02:  # 2% below MA
            return "below_ma"
        else:
            return "at_ma"

    def _count_higher_highs(self, data: List[float]) -> int:
        """Count number of higher highs in sequence"""
        if len(data) < 2:
            return 0

        count = 0
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                count += 1

        return count

    def _count_higher_lows(self, data: List[float]) -> int:
        """Count number of higher lows in sequence"""
        if len(data) < 3:
            return 0

        lows = []
        for i in range(1, len(data) - 1):
            if data[i] < data[i - 1] and data[i] < data[i + 1]:
                lows.append(data[i])

        count = 0
        for i in range(1, len(lows)):
            if lows[i] > lows[i - 1]:
                count += 1

        return count


# Example usage
async def main():
    """Example usage of IdentifyTrendDirectionAgent"""

    agent = IdentifyTrendDirectionAgent()

    # Example 1: Strong uptrend
    uptrend_data = [100 + i * 2 + (i % 3) for i in range(30)]
    result = await agent.execute(uptrend_data, lookback_period=20)

    print("\n=== Strong Uptrend Example ===")
    print(f"Direction: {result.direction.value}")
    print(f"Strength: {result.strength.value}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Slope: {result.metrics.slope:.4f}")
    print(f"R²: {result.metrics.r_squared:.4f}")
    print(f"Supporting indicators: {result.supporting_indicators}")

    # Example 2: Sideways market
    sideways_data = [100 + (i % 5) - 2 for i in range(30)]
    result2 = await agent.execute(sideways_data, lookback_period=20)

    print("\n=== Sideways Market Example ===")
    print(f"Direction: {result2.direction.value}")
    print(f"Strength: {result2.strength.value}")
    print(f"Confidence: {result2.confidence:.2%}")

    # Example 3: Downtrend
    downtrend_data = [100 - i * 1.5 for i in range(30)]
    result3 = await agent.execute(downtrend_data, lookback_period=20)

    print("\n=== Downtrend Example ===")
    print(f"Direction: {result3.direction.value}")
    print(f"Strength: {result3.strength.value}")
    print(f"Confidence: {result3.confidence:.2%}")
    print(f"Slope: {result3.metrics.slope:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
