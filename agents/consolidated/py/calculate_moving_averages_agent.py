"""
Calculate Moving Averages Agent
APQC Level 5 Atomic Task: 3.1.2.2.6 - Calculate moving averages

This agent calculates various types of moving averages (SMA, EMA, WMA) for time series data,
providing the foundation for trend analysis and smoothing operations.

Process Group: 3.0 Market and Sell Products and Services
Parent Process: 3.1.2 Analyze Market Trends
Level: 5 (Atomic Task)
Dependencies: None (foundational)
Reusability: HIGH - used by many trend analysis agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from dataclasses import dataclass, field
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class MovingAverageType(Enum):
    """Types of moving averages supported"""
    SIMPLE = "simple"  # SMA - Simple Moving Average
    EXPONENTIAL = "exponential"  # EMA - Exponential Moving Average
    WEIGHTED = "weighted"  # WMA - Weighted Moving Average
    TRIANGULAR = "triangular"  # TMA - Triangular Moving Average
    HULL = "hull"  # HMA - Hull Moving Average


@dataclass
class MovingAverageConfig:
    """Configuration for moving average calculation"""
    ma_type: MovingAverageType = MovingAverageType.SIMPLE
    window_size: int = 20
    alpha: Optional[float] = None  # For EMA (if None, calculated from window)
    weights: Optional[List[float]] = None  # For custom WMA
    min_periods: Optional[int] = None  # Minimum periods required

    def __post_init__(self):
        """Validate configuration"""
        if self.window_size < 2:
            raise ValueError("Window size must be at least 2")

        if self.ma_type == MovingAverageType.EXPONENTIAL and self.alpha is None:
            # Standard EMA alpha = 2 / (window + 1)
            self.alpha = 2.0 / (self.window_size + 1)

        if self.min_periods is None:
            self.min_periods = self.window_size


@dataclass
class MovingAverageResult:
    """Result of moving average calculation"""
    ma_type: str
    window_size: int
    values: List[float]  # Calculated MA values (same length as input, NaN for insufficient data)
    metadata: Dict[str, Any] = field(default_factory=dict)
    calculation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "ma_type": self.ma_type,
            "window_size": self.window_size,
            "values": self.values,
            "metadata": self.metadata,
            "calculation_time_ms": self.calculation_time_ms,
            "data_points": len(self.values),
            "valid_points": sum(1 for v in self.values if not np.isnan(v))
        }


class CalculateMovingAveragesAgent:
    """
    Level 5 Atomic Task Agent: Calculate moving averages

    APQC Process: 3.1.2.2.6 - Calculate moving averages

    Responsibilities:
    - Calculate Simple Moving Average (SMA)
    - Calculate Exponential Moving Average (EMA)
    - Calculate Weighted Moving Average (WMA)
    - Calculate Triangular Moving Average (TMA)
    - Calculate Hull Moving Average (HMA)
    - Provide smoothed time series data
    - Handle edge cases (insufficient data)

    Value Proposition:
    - Foundation for all trend analysis
    - Reduces noise in time series data
    - Identifies trend direction and strength
    - Supports multiple MA types for different use cases
    - High-performance calculations using NumPy

    Reusability: HIGH
    - Used by trend pattern detectors
    - Used by forecasting agents
    - Used by signal generators
    - Used by technical analysis agents
    """

    def __init__(self):
        self.agent_id = "calculate_moving_averages_agent"
        self.agent_name = "Calculate Moving Averages Agent"
        self.version = "1.0.0"
        self.apqc_process = "3.1.2.2.6"

        logger.info(f"📊 {self.agent_name} initialized (APQC {self.apqc_process})")

    async def execute(
        self,
        time_series: List[float],
        config: MovingAverageConfig
    ) -> MovingAverageResult:
        """
        Calculate moving average for time series data

        Args:
            time_series: List of numeric values (prices, volumes, etc.)
            config: Configuration specifying MA type and parameters

        Returns:
            MovingAverageResult with calculated values

        Raises:
            ValueError: If input data is invalid
        """
        start_time = datetime.now()

        # Validate input
        if not time_series:
            raise ValueError("Time series data cannot be empty")

        if len(time_series) < config.min_periods:
            logger.warning(
                f"Time series length ({len(time_series)}) < min_periods ({config.min_periods})"
            )

        # Convert to numpy array for efficient computation
        data = np.array(time_series, dtype=float)

        # Calculate based on type
        if config.ma_type == MovingAverageType.SIMPLE:
            ma_values = self._calculate_sma(data, config.window_size)
        elif config.ma_type == MovingAverageType.EXPONENTIAL:
            ma_values = self._calculate_ema(data, config.window_size, config.alpha)
        elif config.ma_type == MovingAverageType.WEIGHTED:
            ma_values = self._calculate_wma(data, config.window_size, config.weights)
        elif config.ma_type == MovingAverageType.TRIANGULAR:
            ma_values = self._calculate_tma(data, config.window_size)
        elif config.ma_type == MovingAverageType.HULL:
            ma_values = self._calculate_hma(data, config.window_size)
        else:
            raise ValueError(f"Unsupported MA type: {config.ma_type}")

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds() * 1000

        # Create result
        result = MovingAverageResult(
            ma_type=config.ma_type.value,
            window_size=config.window_size,
            values=ma_values.tolist(),
            metadata={
                "alpha": config.alpha if config.ma_type == MovingAverageType.EXPONENTIAL else None,
                "min_periods": config.min_periods,
                "input_length": len(time_series),
                "calculated_at": datetime.now().isoformat()
            },
            calculation_time_ms=duration
        )

        logger.info(
            f"✅ Calculated {config.ma_type.value} MA "
            f"(window={config.window_size}, points={len(time_series)}, "
            f"time={duration:.2f}ms)"
        )

        return result

    def _calculate_sma(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        Calculate Simple Moving Average (SMA)

        SMA = (P1 + P2 + ... + Pn) / n

        Args:
            data: Input time series
            window: Window size

        Returns:
            Array of SMA values
        """
        sma = np.full(len(data), np.nan)

        for i in range(window - 1, len(data)):
            sma[i] = np.mean(data[i - window + 1:i + 1])

        return sma

    def _calculate_ema(
        self,
        data: np.ndarray,
        window: int,
        alpha: float
    ) -> np.ndarray:
        """
        Calculate Exponential Moving Average (EMA)

        EMA = alpha * Price + (1 - alpha) * EMA_previous
        where alpha = 2 / (window + 1)

        Args:
            data: Input time series
            window: Window size
            alpha: Smoothing factor

        Returns:
            Array of EMA values
        """
        ema = np.full(len(data), np.nan)

        # Initialize with SMA for first window
        ema[window - 1] = np.mean(data[:window])

        # Calculate EMA iteratively
        for i in range(window, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

        return ema

    def _calculate_wma(
        self,
        data: np.ndarray,
        window: int,
        weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        Calculate Weighted Moving Average (WMA)

        WMA = (w1*P1 + w2*P2 + ... + wn*Pn) / (w1 + w2 + ... + wn)
        Default weights: Linear (1, 2, 3, ..., n)

        Args:
            data: Input time series
            window: Window size
            weights: Optional custom weights (must match window size)

        Returns:
            Array of WMA values
        """
        wma = np.full(len(data), np.nan)

        # Generate linear weights if not provided
        if weights is None:
            weights = np.arange(1, window + 1, dtype=float)
        else:
            weights = np.array(weights, dtype=float)

        if len(weights) != window:
            raise ValueError(f"Weights length ({len(weights)}) must match window ({window})")

        weight_sum = np.sum(weights)

        for i in range(window - 1, len(data)):
            window_data = data[i - window + 1:i + 1]
            wma[i] = np.dot(window_data, weights) / weight_sum

        return wma

    def _calculate_tma(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        Calculate Triangular Moving Average (TMA)

        TMA = SMA of SMA (double smoothing)

        Args:
            data: Input time series
            window: Window size

        Returns:
            Array of TMA values
        """
        # First SMA
        sma1 = self._calculate_sma(data, window)

        # SMA of SMA
        tma = self._calculate_sma(sma1, window)

        return tma

    def _calculate_hma(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        Calculate Hull Moving Average (HMA)

        HMA = WMA(2 * WMA(n/2) - WMA(n)), using sqrt(n) as period

        Reduces lag while maintaining smoothness

        Args:
            data: Input time series
            window: Window size

        Returns:
            Array of HMA values
        """
        half_window = window // 2
        sqrt_window = int(np.sqrt(window))

        # Calculate WMA with half period
        wma_half = self._calculate_wma(data, half_window)

        # Calculate WMA with full period
        wma_full = self._calculate_wma(data, window)

        # Calculate 2 * WMA(half) - WMA(full)
        raw_hma = 2 * wma_half - wma_full

        # Apply WMA to the result with sqrt(n) period
        hma = self._calculate_wma(raw_hma, sqrt_window)

        return hma

    async def calculate_multiple_mas(
        self,
        time_series: List[float],
        configs: List[MovingAverageConfig]
    ) -> Dict[str, MovingAverageResult]:
        """
        Calculate multiple moving averages in parallel

        Useful for comparing different MA types or window sizes

        Args:
            time_series: Input time series
            configs: List of MA configurations

        Returns:
            Dictionary mapping config description to results
        """
        tasks = []
        keys = []

        for config in configs:
            key = f"{config.ma_type.value}_{config.window_size}"
            keys.append(key)
            tasks.append(self.execute(time_series, config))

        results = await asyncio.gather(*tasks)

        return dict(zip(keys, results))

    def get_crossover_signals(
        self,
        fast_ma: List[float],
        slow_ma: List[float]
    ) -> List[str]:
        """
        Detect crossover signals between two moving averages

        Returns:
            List of signals: "bullish_cross", "bearish_cross", or "neutral"
        """
        signals = []

        for i in range(len(fast_ma)):
            if i == 0 or np.isnan(fast_ma[i]) or np.isnan(slow_ma[i]):
                signals.append("neutral")
                continue

            fast_prev = fast_ma[i - 1]
            slow_prev = slow_ma[i - 1]
            fast_curr = fast_ma[i]
            slow_curr = slow_ma[i]

            if np.isnan(fast_prev) or np.isnan(slow_prev):
                signals.append("neutral")
                continue

            # Bullish cross: fast crosses above slow
            if fast_prev <= slow_prev and fast_curr > slow_curr:
                signals.append("bullish_cross")
            # Bearish cross: fast crosses below slow
            elif fast_prev >= slow_prev and fast_curr < slow_curr:
                signals.append("bearish_cross")
            else:
                signals.append("neutral")

        return signals


# Example usage
async def main():
    """Example usage of CalculateMovingAveragesAgent"""

    # Sample time series data (e.g., stock prices)
    prices = [
        100, 102, 101, 105, 107, 106, 108, 110, 109, 111,
        113, 112, 115, 117, 116, 118, 120, 119, 121, 123,
        122, 125, 127, 126, 128, 130, 129, 131, 133, 132
    ]

    agent = CalculateMovingAveragesAgent()

    # Calculate SMA with 10-period window
    sma_config = MovingAverageConfig(
        ma_type=MovingAverageType.SIMPLE,
        window_size=10
    )

    sma_result = await agent.execute(prices, sma_config)
    print(f"\nSMA-10 Results:")
    print(f"  Type: {sma_result.ma_type}")
    print(f"  Window: {sma_result.window_size}")
    print(f"  Valid points: {sum(1 for v in sma_result.values if not np.isnan(v))}")
    print(f"  Last 5 values: {[round(v, 2) if not np.isnan(v) else None for v in sma_result.values[-5:]]}")
    print(f"  Calculation time: {sma_result.calculation_time_ms:.2f}ms")

    # Calculate EMA with 10-period window
    ema_config = MovingAverageConfig(
        ma_type=MovingAverageType.EXPONENTIAL,
        window_size=10
    )

    ema_result = await agent.execute(prices, ema_config)
    print(f"\nEMA-10 Results:")
    print(f"  Type: {ema_result.ma_type}")
    print(f"  Alpha: {ema_result.metadata['alpha']:.4f}")
    print(f"  Last 5 values: {[round(v, 2) if not np.isnan(v) else None for v in ema_result.values[-5:]]}")

    # Calculate multiple MAs in parallel
    configs = [
        MovingAverageConfig(MovingAverageType.SIMPLE, 10),
        MovingAverageConfig(MovingAverageType.SIMPLE, 20),
        MovingAverageConfig(MovingAverageType.EXPONENTIAL, 10),
        MovingAverageConfig(MovingAverageType.WEIGHTED, 10),
    ]

    multiple_results = await agent.calculate_multiple_mas(prices, configs)
    print(f"\nMultiple MAs calculated: {list(multiple_results.keys())}")

    # Detect crossovers between fast and slow SMAs
    fast_ma = multiple_results['simple_10'].values
    slow_ma = multiple_results['simple_20'].values

    crossovers = agent.get_crossover_signals(fast_ma, slow_ma)
    crossover_points = [(i, sig) for i, sig in enumerate(crossovers) if sig != "neutral"]

    if crossover_points:
        print(f"\nCrossover signals detected:")
        for idx, signal in crossover_points:
            print(f"  Position {idx}: {signal}")
    else:
        print("\nNo crossover signals detected")


if __name__ == "__main__":
    asyncio.run(main())
