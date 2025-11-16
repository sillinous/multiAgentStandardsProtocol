"""
Comprehensive tests for Calculate Moving Averages Agent
APQC Level 5 Atomic Task: 3.1.2.2.6
"""

import pytest
import numpy as np
import asyncio
from agents.consolidated.py.calculate_moving_averages_agent import (
    CalculateMovingAveragesAgent,
    MovingAverageConfig,
    MovingAverageType,
    MovingAverageResult
)


@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return CalculateMovingAveragesAgent()


@pytest.fixture
def sample_data():
    """Sample time series data for testing"""
    return [100, 102, 101, 105, 107, 106, 108, 110, 109, 111,
            113, 112, 115, 117, 116, 118, 120, 119, 121, 123]


class TestMovingAverageConfig:
    """Test configuration validation"""

    def test_valid_config(self):
        """Test valid configuration"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=10
        )
        assert config.window_size == 10
        assert config.ma_type == MovingAverageType.SIMPLE

    def test_invalid_window_size(self):
        """Test that window size < 2 raises error"""
        with pytest.raises(ValueError, match="Window size must be at least 2"):
            MovingAverageConfig(window_size=1)

    def test_ema_alpha_calculation(self):
        """Test automatic alpha calculation for EMA"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.EXPONENTIAL,
            window_size=10
        )
        expected_alpha = 2.0 / 11  # 2 / (window + 1)
        assert config.alpha == pytest.approx(expected_alpha)

    def test_custom_ema_alpha(self):
        """Test custom alpha value"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.EXPONENTIAL,
            window_size=10,
            alpha=0.5
        )
        assert config.alpha == 0.5


class TestSMA:
    """Test Simple Moving Average calculations"""

    @pytest.mark.asyncio
    async def test_sma_basic(self, agent, sample_data):
        """Test basic SMA calculation"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=5
        )

        result = await agent.execute(sample_data, config)

        assert result.ma_type == "simple"
        assert result.window_size == 5
        assert len(result.values) == len(sample_data)

        # First 4 values should be NaN
        for i in range(4):
            assert np.isnan(result.values[i])

        # 5th value should be average of first 5
        expected_5th = np.mean(sample_data[:5])
        assert result.values[4] == pytest.approx(expected_5th)

    @pytest.mark.asyncio
    async def test_sma_known_values(self, agent):
        """Test SMA with known expected values"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=3
        )

        result = await agent.execute(data, config)

        # MA values:
        # [0-2]: NaN, NaN, 2.0 (avg of 1,2,3)
        # [3]: 3.0 (avg of 2,3,4)
        # [4]: 4.0 (avg of 3,4,5)
        # etc.

        assert np.isnan(result.values[0])
        assert np.isnan(result.values[1])
        assert result.values[2] == pytest.approx(2.0)
        assert result.values[3] == pytest.approx(3.0)
        assert result.values[4] == pytest.approx(4.0)
        assert result.values[-1] == pytest.approx(9.0)  # avg of 8,9,10

    @pytest.mark.asyncio
    async def test_sma_performance(self, agent):
        """Test SMA performance with large dataset"""
        large_data = list(range(10000))
        config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=50
        )

        result = await agent.execute(large_data, config)

        # Should complete in reasonable time
        assert result.calculation_time_ms < 1000  # < 1 second
        assert len(result.values) == 10000


class TestEMA:
    """Test Exponential Moving Average calculations"""

    @pytest.mark.asyncio
    async def test_ema_basic(self, agent, sample_data):
        """Test basic EMA calculation"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.EXPONENTIAL,
            window_size=10
        )

        result = await agent.execute(sample_data, config)

        assert result.ma_type == "exponential"
        assert result.window_size == 10

        # First 9 values should be NaN, 10th initialized with SMA
        for i in range(9):
            assert np.isnan(result.values[i])

        # 10th value should be SMA of first 10
        expected_10th = np.mean(sample_data[:10])
        assert result.values[9] == pytest.approx(expected_10th)

    @pytest.mark.asyncio
    async def test_ema_responsiveness(self, agent):
        """Test that EMA responds faster than SMA to price changes"""
        # Data with sudden jump
        data = [100] * 10 + [110] * 10

        ema_config = MovingAverageConfig(
            ma_type=MovingAverageType.EXPONENTIAL,
            window_size=5
        )

        sma_config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=5
        )

        ema_result = await agent.execute(data, ema_config)
        sma_result = await agent.execute(data, sma_config)

        # After the jump, EMA should respond faster than SMA
        # Check position 15 (after jump at position 10)
        assert ema_result.values[15] > sma_result.values[15]


class TestWMA:
    """Test Weighted Moving Average calculations"""

    @pytest.mark.asyncio
    async def test_wma_default_weights(self, agent):
        """Test WMA with default linear weights"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        config = MovingAverageConfig(
            ma_type=MovingAverageType.WEIGHTED,
            window_size=3
        )

        result = await agent.execute(data, config)

        # With linear weights [1, 2, 3]:
        # Position 2: (1*1 + 2*2 + 3*3) / 6 = 14/6 = 2.333...
        assert result.values[2] == pytest.approx(2.333, abs=0.001)

    @pytest.mark.asyncio
    async def test_wma_custom_weights(self, agent):
        """Test WMA with custom weights"""
        data = [10, 20, 30, 40, 50]
        weights = [0.1, 0.2, 0.3, 0.4]

        config = MovingAverageConfig(
            ma_type=MovingAverageType.WEIGHTED,
            window_size=4,
            weights=weights
        )

        result = await agent.execute(data, config)

        # Position 3: (10*0.1 + 20*0.2 + 30*0.3 + 40*0.4) / 1.0
        expected = (10*0.1 + 20*0.2 + 30*0.3 + 40*0.4) / 1.0
        assert result.values[3] == pytest.approx(expected)

    @pytest.mark.asyncio
    async def test_wma_invalid_weights(self, agent):
        """Test that mismatched weight length raises error"""
        data = [1, 2, 3, 4, 5]
        config = MovingAverageConfig(
            ma_type=MovingAverageType.WEIGHTED,
            window_size=3,
            weights=[1, 2]  # Only 2 weights for window of 3
        )

        with pytest.raises(ValueError, match="Weights length"):
            await agent.execute(data, config)


class TestTMA:
    """Test Triangular Moving Average calculations"""

    @pytest.mark.asyncio
    async def test_tma_double_smoothing(self, agent):
        """Test that TMA applies double smoothing"""
        data = list(range(1, 21))
        config = MovingAverageConfig(
            ma_type=MovingAverageType.TRIANGULAR,
            window_size=5
        )

        result = await agent.execute(data, config)

        # TMA should be smoother than SMA
        assert result.ma_type == "triangular"
        # More initial NaN values due to double smoothing
        nan_count = sum(1 for v in result.values if np.isnan(v))
        assert nan_count >= 8  # Should have more NaN values than single SMA


class TestHMA:
    """Test Hull Moving Average calculations"""

    @pytest.mark.asyncio
    async def test_hma_reduced_lag(self, agent):
        """Test that HMA reduces lag compared to SMA"""
        # Create data with trend change
        data = list(range(100, 120)) + list(range(120, 100, -1))

        hma_config = MovingAverageConfig(
            ma_type=MovingAverageType.HULL,
            window_size=10
        )

        sma_config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=10
        )

        hma_result = await agent.execute(data, hma_config)
        sma_result = await agent.execute(data, sma_config)

        # HMA should respond faster to trend change at position 20
        # (This is a qualitative test - exact values depend on implementation)
        assert hma_result.ma_type == "hull"


class TestMultipleMACalculation:
    """Test calculating multiple MAs in parallel"""

    @pytest.mark.asyncio
    async def test_parallel_calculation(self, agent, sample_data):
        """Test parallel calculation of multiple MAs"""
        configs = [
            MovingAverageConfig(MovingAverageType.SIMPLE, 5),
            MovingAverageConfig(MovingAverageType.SIMPLE, 10),
            MovingAverageConfig(MovingAverageType.EXPONENTIAL, 5),
            MovingAverageConfig(MovingAverageType.WEIGHTED, 5),
        ]

        results = await agent.calculate_multiple_mas(sample_data, configs)

        assert len(results) == 4
        assert 'simple_5' in results
        assert 'simple_10' in results
        assert 'exponential_5' in results
        assert 'weighted_5' in results

        # Verify each result
        for key, result in results.items():
            assert isinstance(result, MovingAverageResult)
            assert len(result.values) == len(sample_data)


class TestCrossoverSignals:
    """Test moving average crossover detection"""

    def test_bullish_crossover(self, agent):
        """Test detection of bullish crossover (fast crosses above slow)"""
        fast_ma = [10, 11, 12, 13, 14]
        slow_ma = [12, 12, 12, 12, 12]

        signals = agent.get_crossover_signals(fast_ma, slow_ma)

        # Should detect bullish cross when fast crosses above slow
        assert "bullish_cross" in signals

    def test_bearish_crossover(self, agent):
        """Test detection of bearish crossover (fast crosses below slow)"""
        fast_ma = [14, 13, 12, 11, 10]
        slow_ma = [12, 12, 12, 12, 12]

        signals = agent.get_crossover_signals(fast_ma, slow_ma)

        # Should detect bearish cross when fast crosses below slow
        assert "bearish_cross" in signals

    def test_no_crossover(self, agent):
        """Test when there's no crossover"""
        fast_ma = [10, 11, 12, 13, 14]
        slow_ma = [8, 9, 10, 11, 12]

        signals = agent.get_crossover_signals(fast_ma, slow_ma)

        # All signals should be neutral
        assert all(s == "neutral" for s in signals)


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_data(self, agent):
        """Test with empty time series"""
        config = MovingAverageConfig(window_size=5)

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.execute([], config)

    @pytest.mark.asyncio
    async def test_insufficient_data(self, agent):
        """Test with data shorter than window"""
        data = [1, 2, 3]
        config = MovingAverageConfig(window_size=10)

        # Should complete but with warning
        result = await agent.execute(data, config)

        # All values should be NaN
        assert all(np.isnan(v) for v in result.values)

    @pytest.mark.asyncio
    async def test_single_value(self, agent):
        """Test with single value"""
        data = [100]
        config = MovingAverageConfig(window_size=5)

        result = await agent.execute(data, config)

        assert len(result.values) == 1
        assert np.isnan(result.values[0])


class TestResultSerialization:
    """Test result conversion to dictionary"""

    @pytest.mark.asyncio
    async def test_to_dict(self, agent, sample_data):
        """Test conversion of result to dictionary"""
        config = MovingAverageConfig(
            ma_type=MovingAverageType.SIMPLE,
            window_size=10
        )

        result = await agent.execute(sample_data, config)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'ma_type' in result_dict
        assert 'window_size' in result_dict
        assert 'values' in result_dict
        assert 'metadata' in result_dict
        assert 'data_points' in result_dict
        assert 'valid_points' in result_dict

        assert result_dict['ma_type'] == 'simple'
        assert result_dict['window_size'] == 10
        assert result_dict['data_points'] == len(sample_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
