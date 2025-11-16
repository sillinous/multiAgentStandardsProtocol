"""
Detect Seasonal Patterns Agent
APQC Level 5 Atomic Task: 3.1.2.2.1 - Detect seasonal patterns

This agent identifies seasonal patterns in time series data including quarterly cycles,
annual patterns, and recurring seasonal indices.

Process Group: 3.0 Market and Sell Products and Services
Parent Process: 3.1.2 Analyze Market Trends
Level: 5 (Atomic Task)
Dependencies: 3.1.2.2.6 (Moving Averages - for detrending)
Reusability: MEDIUM-HIGH - used in forecasting, inventory planning, sales planning
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

logger = logging.getLogger(__name__)


class SeasonalPeriod(Enum):
    """Common seasonal periods"""
    WEEKLY = 7
    MONTHLY = 30
    QUARTERLY = 90
    SEMI_ANNUAL = 180
    ANNUAL = 365


class SeasonalStrength(Enum):
    """Strength of seasonal pattern"""
    NONE = "none"              # No seasonality detected
    WEAK = "weak"              # 0.1-0.3
    MODERATE = "moderate"      # 0.3-0.6
    STRONG = "strong"          # 0.6-0.8
    VERY_STRONG = "very_strong"  # 0.8-1.0


@dataclass
class SeasonalComponent:
    """Detected seasonal component"""
    period: int  # Length of seasonal cycle
    strength: float  # 0-1 strength score
    indices: List[float]  # Seasonal indices for each period position
    peaks: List[int]  # Positions of seasonal peaks
    troughs: List[int]  # Positions of seasonal troughs
    confidence: float  # 0-1 confidence score


@dataclass
class SeasonalPatternResult:
    """Result of seasonal pattern detection"""
    has_seasonality: bool
    dominant_period: Optional[int]
    strength: SeasonalStrength
    components: List[SeasonalComponent] = field(default_factory=list)
    detrended_data: List[float] = field(default_factory=list)
    seasonal_forecast: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    calculation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "has_seasonality": self.has_seasonality,
            "dominant_period": self.dominant_period,
            "strength": self.strength.value,
            "components": [
                {
                    "period": c.period,
                    "strength": round(c.strength, 4),
                    "indices": [round(i, 4) for i in c.indices],
                    "peaks": c.peaks,
                    "troughs": c.troughs,
                    "confidence": round(c.confidence, 4)
                }
                for c in self.components
            ],
            "detrended_data": [round(d, 4) for d in self.detrended_data],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "calculation_time_ms": round(self.calculation_time_ms, 2)
        }


class DetectSeasonalPatternsAgent:
    """
    Level 5 Atomic Task Agent: Detect seasonal patterns

    APQC Process: 3.1.2.2.1 - Detect seasonal patterns

    Responsibilities:
    - Identify quarterly seasonal patterns
    - Identify annual seasonal patterns
    - Calculate seasonal indices
    - Detect peaks and troughs in seasonal cycles
    - Measure seasonality strength
    - Detrend data for clearer pattern visibility
    - Generate seasonal forecasts

    Methodology:
    - Classical seasonal decomposition
    - Autocorrelation analysis
    - Seasonal index calculation
    - Peak/trough detection
    - Strength measurement via variance analysis

    Value Proposition:
    - Improves demand forecasting accuracy
    - Enables better inventory planning
    - Supports seasonal pricing strategies
    - Identifies business cycles
    - Risk management for seasonal businesses
    - Revenue planning and budgeting

    Reusability: MEDIUM-HIGH
    - Used by forecasting agents
    - Used by inventory planning agents
    - Used by sales planning agents
    - Used by pricing optimization agents
    """

    def __init__(self):
        self.agent_id = "detect_seasonal_patterns_agent"
        self.agent_name = "Detect Seasonal Patterns Agent"
        self.version = "1.0.0"
        self.apqc_process = "3.1.2.2.1"

        # Detection thresholds
        self.MIN_CYCLES = 2  # Minimum cycles needed to detect seasonality
        self.SEASONALITY_THRESHOLD = 0.1  # Minimum strength to consider seasonal

        logger.info(f"📆 {self.agent_name} initialized (APQC {self.apqc_process})")

    async def execute(
        self,
        time_series: List[float],
        test_periods: Optional[List[int]] = None,
        auto_detect_period: bool = True
    ) -> SeasonalPatternResult:
        """
        Detect seasonal patterns in time series data

        Args:
            time_series: Time series data to analyze
            test_periods: Optional list of periods to test (e.g., [7, 30, 365])
            auto_detect_period: If True, automatically detect likely periods

        Returns:
            SeasonalPatternResult with detected patterns and components
        """
        start_time = datetime.now()

        if not time_series:
            raise ValueError("Time series cannot be empty")

        if len(time_series) < 14:  # Need at least 2 weeks of data
            logger.warning(f"Time series too short ({len(time_series)}) for reliable seasonality detection")

        # Determine which periods to test
        if test_periods is None:
            if auto_detect_period:
                test_periods = self._auto_select_periods(len(time_series))
            else:
                test_periods = [7, 30, 90, 365]  # Weekly, Monthly, Quarterly, Annual

        # Remove trend to make seasonality more visible
        detrended_data = self._detrend_data(time_series)

        # Detect seasonal components
        components = []
        for period in test_periods:
            if len(time_series) >= period * self.MIN_CYCLES:
                component = self._detect_component(detrended_data, period)
                if component.strength >= self.SEASONALITY_THRESHOLD:
                    components.append(component)

        # Sort by strength
        components.sort(key=lambda c: c.strength, reverse=True)

        # Determine if seasonality exists
        has_seasonality = len(components) > 0

        # Identify dominant period
        dominant_period = components[0].period if components else None

        # Classify overall strength
        strength = self._classify_strength(components[0].strength if components else 0)

        # Generate seasonal forecast if pattern detected
        seasonal_forecast = []
        if has_seasonality:
            seasonal_forecast = self._generate_seasonal_forecast(
                time_series,
                components[0],
                periods_ahead=min(components[0].period, 30)
            )

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = SeasonalPatternResult(
            has_seasonality=has_seasonality,
            dominant_period=dominant_period,
            strength=strength,
            components=components,
            detrended_data=detrended_data,
            seasonal_forecast=seasonal_forecast,
            metadata={
                "data_length": len(time_series),
                "tested_periods": test_periods,
                "components_detected": len(components),
                "auto_detected": auto_detect_period
            },
            calculation_time_ms=duration
        )

        logger.info(
            f"✅ Seasonality detection: {has_seasonality}, "
            f"dominant_period={dominant_period}, strength={strength.value}, "
            f"components={len(components)}"
        )

        return result

    def _auto_select_periods(self, data_length: int) -> List[int]:
        """Automatically select appropriate periods based on data length"""
        periods = []

        # Weekly pattern (7 days)
        if data_length >= 14:
            periods.append(7)

        # Bi-weekly (14 days)
        if data_length >= 28:
            periods.append(14)

        # Monthly pattern (~30 days)
        if data_length >= 60:
            periods.append(30)

        # Quarterly pattern (~90 days)
        if data_length >= 180:
            periods.append(90)

        # Semi-annual (~180 days)
        if data_length >= 360:
            periods.append(180)

        # Annual pattern (~365 days)
        if data_length >= 730:
            periods.append(365)

        return periods if periods else [min(7, data_length // 2)]

    def _detrend_data(self, data: List[float]) -> List[float]:
        """
        Remove linear trend from data using simple moving average

        This makes seasonal patterns more visible
        """
        if len(data) < 3:
            return data

        # Calculate moving average window (1/4 of data or 7, whichever is smaller)
        window = min(max(len(data) // 4, 3), 7)

        detrended = []
        for i in range(len(data)):
            # Calculate local mean
            start_idx = max(0, i - window // 2)
            end_idx = min(len(data), i + window // 2 + 1)
            local_mean = sum(data[start_idx:end_idx]) / (end_idx - start_idx)

            # Detrended value = actual - trend
            detrended.append(data[i] - local_mean)

        return detrended

    def _detect_component(self, data: List[float], period: int) -> SeasonalComponent:
        """
        Detect seasonal component for a specific period

        Uses classical seasonal decomposition approach
        """
        # Calculate seasonal indices
        indices = self._calculate_seasonal_indices(data, period)

        # Measure seasonality strength using autocorrelation
        strength = self._calculate_seasonality_strength(data, period)

        # Find peaks and troughs in seasonal pattern
        peaks, troughs = self._find_peaks_troughs(indices)

        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(data, period, strength, indices)

        return SeasonalComponent(
            period=period,
            strength=strength,
            indices=indices,
            peaks=peaks,
            troughs=troughs,
            confidence=confidence
        )

    def _calculate_seasonal_indices(
        self,
        data: List[float],
        period: int
    ) -> List[float]:
        """
        Calculate seasonal indices for each position in the period

        Seasonal index = average value at that position / overall average
        """
        if period <= 0 or period > len(data):
            return [1.0] * min(period, len(data))

        # Group data by position in period
        position_values = [[] for _ in range(period)]

        for i, value in enumerate(data):
            position = i % period
            position_values[position].append(value)

        # Calculate average for each position
        position_averages = []
        for values in position_values:
            if values:
                position_averages.append(sum(values) / len(values))
            else:
                position_averages.append(0)

        # Calculate overall average (excluding zeros)
        non_zero = [v for v in position_averages if v != 0]
        overall_avg = sum(non_zero) / len(non_zero) if non_zero else 1

        # Calculate seasonal indices (normalized)
        indices = [avg / overall_avg if overall_avg != 0 else 1.0
                   for avg in position_averages]

        return indices

    def _calculate_seasonality_strength(
        self,
        data: List[float],
        period: int
    ) -> float:
        """
        Calculate strength of seasonality using variance decomposition

        Strength = Variance(seasonal component) / Variance(total)
        """
        if len(data) < period * 2:
            return 0.0

        # Calculate seasonal component
        indices = self._calculate_seasonal_indices(data, period)
        seasonal_component = [indices[i % period] for i in range(len(data))]

        # Calculate variances
        mean_seasonal = sum(seasonal_component) / len(seasonal_component)
        var_seasonal = sum((x - mean_seasonal) ** 2 for x in seasonal_component) / len(seasonal_component)

        mean_data = sum(data) / len(data)
        var_data = sum((x - mean_data) ** 2 for x in data) / len(data)

        # Strength = proportion of variance explained by seasonality
        if var_data == 0:
            return 0.0

        strength = min(1.0, var_seasonal / var_data)

        return max(0.0, strength)

    def _find_peaks_troughs(self, indices: List[float]) -> Tuple[List[int], List[int]]:
        """Find peaks and troughs in seasonal indices"""
        if len(indices) < 3:
            return [], []

        peaks = []
        troughs = []

        for i in range(1, len(indices) - 1):
            # Peak: higher than neighbors
            if indices[i] > indices[i - 1] and indices[i] > indices[i + 1]:
                peaks.append(i)

            # Trough: lower than neighbors
            if indices[i] < indices[i - 1] and indices[i] < indices[i + 1]:
                troughs.append(i)

        return peaks, troughs

    def _calculate_confidence(
        self,
        data: List[float],
        period: int,
        strength: float,
        indices: List[float]
    ) -> float:
        """
        Calculate confidence in seasonal pattern detection

        Factors:
        - Number of complete cycles
        - Strength of pattern
        - Consistency of indices
        - Data quality
        """
        # Number of cycles
        num_cycles = len(data) / period
        cycle_confidence = min(1.0, num_cycles / 4)  # Full confidence at 4+ cycles

        # Strength confidence
        strength_confidence = strength

        # Consistency of indices (low variance = more consistent)
        if len(indices) > 1:
            mean_idx = sum(indices) / len(indices)
            variance = sum((x - mean_idx) ** 2 for x in indices) / len(indices)
            std_dev = math.sqrt(variance)
            consistency = max(0, 1 - std_dev)
        else:
            consistency = 0

        # Data quality (not too many zeros or outliers)
        zeros = sum(1 for x in data if x == 0)
        quality = 1 - (zeros / len(data))

        # Weighted average
        confidence = (
            cycle_confidence * 0.3 +
            strength_confidence * 0.4 +
            consistency * 0.2 +
            quality * 0.1
        )

        return max(0, min(1, confidence))

    def _classify_strength(self, strength: float) -> SeasonalStrength:
        """Classify seasonality strength"""
        if strength >= 0.8:
            return SeasonalStrength.VERY_STRONG
        elif strength >= 0.6:
            return SeasonalStrength.STRONG
        elif strength >= 0.3:
            return SeasonalStrength.MODERATE
        elif strength >= 0.1:
            return SeasonalStrength.WEAK
        else:
            return SeasonalStrength.NONE

    def _generate_seasonal_forecast(
        self,
        historical_data: List[float],
        component: SeasonalComponent,
        periods_ahead: int
    ) -> List[float]:
        """
        Generate simple seasonal forecast

        Forecast = recent average * seasonal_index
        """
        if not historical_data or not component.indices:
            return []

        # Use recent average as base
        recent_window = min(len(historical_data), component.period * 2)
        recent_avg = sum(historical_data[-recent_window:]) / recent_window

        # Generate forecast using seasonal indices
        forecast = []
        for i in range(periods_ahead):
            seasonal_idx = component.indices[i % len(component.indices)]
            forecast_value = recent_avg * seasonal_idx
            forecast.append(forecast_value)

        return forecast


# Example usage
async def main():
    """Example usage of DetectSeasonalPatternsAgent"""

    agent = DetectSeasonalPatternsAgent()

    # Example 1: Weekly seasonal pattern (7-day cycle)
    print("\n=== Example 1: Weekly Seasonal Pattern ===")
    weekly_pattern = [100 + 20 * math.sin(2 * math.pi * i / 7) + i * 0.5
                      for i in range(60)]  # 60 days

    result1 = await agent.execute(weekly_pattern, test_periods=[7, 30])

    print(f"Has seasonality: {result1.has_seasonality}")
    print(f"Dominant period: {result1.dominant_period} days")
    print(f"Strength: {result1.strength.value}")
    if result1.components:
        print(f"Seasonal indices (first 7): {[round(i, 2) for i in result1.components[0].indices[:7]]}")
        print(f"Peaks at positions: {result1.components[0].peaks}")
        print(f"Troughs at positions: {result1.components[0].troughs}")
        print(f"Confidence: {result1.components[0].confidence:.2%}")

    # Example 2: Quarterly seasonal pattern
    print("\n=== Example 2: Quarterly Seasonal Pattern ===")
    quarterly_base = [100] * 365
    for i in range(365):
        # Add quarterly seasonality
        quarter = (i // 90) % 4
        if quarter == 0:  # Q1 - low
            quarterly_base[i] *= 0.8
        elif quarter == 1:  # Q2 - medium
            quarterly_base[i] *= 1.0
        elif quarter == 2:  # Q3 - high
            quarterly_base[i] *= 1.3
        else:  # Q4 - very high (holiday season)
            quarterly_base[i] *= 1.5

    result2 = await agent.execute(quarterly_base, auto_detect_period=True)

    print(f"Has seasonality: {result2.has_seasonality}")
    print(f"Dominant period: {result2.dominant_period} days")
    print(f"Strength: {result2.strength.value}")
    print(f"Components detected: {len(result2.components)}")

    # Example 3: No seasonal pattern (random noise)
    print("\n=== Example 3: No Seasonal Pattern (Random) ===")
    import random
    random.seed(42)
    random_data = [100 + random.uniform(-10, 10) for _ in range(60)]

    result3 = await agent.execute(random_data)

    print(f"Has seasonality: {result3.has_seasonality}")
    print(f"Strength: {result3.strength.value}")
    print(f"Components detected: {len(result3.components)}")


if __name__ == "__main__":
    asyncio.run(main())
