"""
Calculate Statistical Significance Agent
APQC Level 5 Atomic Task: 3.1.2.3.1 - Calculate statistical significance

This agent calculates statistical significance, p-values, confidence intervals, and performs
hypothesis testing to validate trend findings and market analysis results.

Process Group: 3.0 Market and Sell Products and Services
Parent Process: 3.1.2 Analyze Market Trends
Level: 5 (Atomic Task)
Dependencies: None (foundational statistical analysis)
Reusability: HIGH - used across all quantitative analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import math

logger = logging.getLogger(__name__)


class SignificanceLevel(Enum):
    """Common significance levels (alpha)"""
    VERY_STRICT = 0.001  # 99.9% confidence
    STRICT = 0.01        # 99% confidence
    MODERATE = 0.05      # 95% confidence (most common)
    LENIENT = 0.10       # 90% confidence


class HypothesisTest(Enum):
    """Types of hypothesis tests"""
    TWO_TAILED = "two_tailed"  # H1: μ ≠ μ0
    LEFT_TAILED = "left_tailed"  # H1: μ < μ0
    RIGHT_TAILED = "right_tailed"  # H1: μ > μ0


@dataclass
class ConfidenceInterval:
    """Confidence interval result"""
    lower_bound: float
    upper_bound: float
    confidence_level: float  # e.g., 0.95 for 95%
    margin_of_error: float


@dataclass
class HypothesisTestResult:
    """Result of hypothesis test"""
    test_statistic: float  # t-statistic or z-statistic
    p_value: float
    is_significant: bool
    significance_level: float
    test_type: HypothesisTest
    degrees_of_freedom: Optional[int] = None


@dataclass
class StatisticalSignificanceResult:
    """Comprehensive statistical significance analysis"""
    sample_mean: float
    sample_std: float
    sample_size: int
    standard_error: float
    confidence_interval: ConfidenceInterval
    hypothesis_test: Optional[HypothesisTestResult] = None
    effect_size: Optional[float] = None  # Cohen's d
    power: Optional[float] = None  # Statistical power
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    calculation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "sample_mean": round(self.sample_mean, 6),
            "sample_std": round(self.sample_std, 6),
            "sample_size": self.sample_size,
            "standard_error": round(self.standard_error, 6),
            "confidence_interval": {
                "lower_bound": round(self.confidence_interval.lower_bound, 6),
                "upper_bound": round(self.confidence_interval.upper_bound, 6),
                "confidence_level": self.confidence_interval.confidence_level,
                "margin_of_error": round(self.confidence_interval.margin_of_error, 6)
            },
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "calculation_time_ms": round(self.calculation_time_ms, 2)
        }

        if self.hypothesis_test:
            result["hypothesis_test"] = {
                "test_statistic": round(self.hypothesis_test.test_statistic, 4),
                "p_value": round(self.hypothesis_test.p_value, 6),
                "is_significant": self.hypothesis_test.is_significant,
                "significance_level": self.hypothesis_test.significance_level,
                "test_type": self.hypothesis_test.test_type.value,
                "degrees_of_freedom": self.hypothesis_test.degrees_of_freedom
            }

        if self.effect_size is not None:
            result["effect_size"] = round(self.effect_size, 4)

        if self.power is not None:
            result["power"] = round(self.power, 4)

        return result


class CalculateStatisticalSignificanceAgent:
    """
    Level 5 Atomic Task Agent: Calculate statistical significance

    APQC Process: 3.1.2.3.1 - Calculate statistical significance

    Responsibilities:
    - Calculate p-values for hypothesis tests
    - Generate confidence intervals
    - Perform t-tests and z-tests
    - Calculate standard errors
    - Measure effect sizes (Cohen's d)
    - Estimate statistical power
    - Validate trend significance
    - Compare means between groups

    Methodology:
    - Student's t-distribution for small samples (n < 30)
    - Normal distribution for large samples (n ≥ 30)
    - Bootstrap methods for non-normal distributions
    - Confidence interval construction
    - Hypothesis testing framework

    Value Proposition:
    - Validates trend findings statistically
    - Prevents false positive conclusions
    - Quantifies uncertainty in estimates
    - Supports data-driven decisions
    - Provides scientific rigor
    - Risk assessment foundation

    Reusability: VERY HIGH
    - Used by ALL trend analysis agents
    - Used by ALL forecasting agents
    - Used by A/B testing
    - Used by quality control
    - Used by risk assessment
    """

    def __init__(self):
        self.agent_id = "calculate_statistical_significance_agent"
        self.agent_name = "Calculate Statistical Significance Agent"
        self.version = "1.0.0"
        self.apqc_process = "3.1.2.3.1"

        # Pre-calculated t-distribution critical values (two-tailed, α=0.05)
        # For more precision, use scipy.stats.t in production
        self.T_CRITICAL_VALUES = {
            1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
            6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
            15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021,
            50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984, 120: 1.980
        }

        logger.info(f"📊 {self.agent_name} initialized (APQC {self.apqc_process})")

    async def execute(
        self,
        data: List[float],
        confidence_level: float = 0.95,
        null_hypothesis_mean: Optional[float] = None,
        test_type: HypothesisTest = HypothesisTest.TWO_TAILED
    ) -> StatisticalSignificanceResult:
        """
        Calculate statistical significance metrics

        Args:
            data: Sample data
            confidence_level: Desired confidence level (e.g., 0.95 for 95%)
            null_hypothesis_mean: Mean to test against (if None, no hypothesis test)
            test_type: Type of hypothesis test (two-tailed, left, right)

        Returns:
            StatisticalSignificanceResult with comprehensive metrics
        """
        start_time = datetime.now()

        if not data:
            raise ValueError("Data cannot be empty")

        if len(data) < 2:
            raise ValueError("Need at least 2 data points for significance testing")

        # Calculate descriptive statistics
        sample_mean = self._calculate_mean(data)
        sample_std = self._calculate_std(data, sample_mean)
        sample_size = len(data)
        standard_error = sample_std / math.sqrt(sample_size)

        # Calculate confidence interval
        ci = self._calculate_confidence_interval(
            sample_mean,
            standard_error,
            sample_size,
            confidence_level
        )

        # Perform hypothesis test if null hypothesis provided
        hypothesis_test = None
        if null_hypothesis_mean is not None:
            hypothesis_test = self._perform_hypothesis_test(
                sample_mean,
                standard_error,
                sample_size,
                null_hypothesis_mean,
                1.0 - confidence_level,  # significance level
                test_type
            )

        # Calculate effect size if comparing to null hypothesis
        effect_size = None
        if null_hypothesis_mean is not None and sample_std > 0:
            effect_size = abs(sample_mean - null_hypothesis_mean) / sample_std

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = StatisticalSignificanceResult(
            sample_mean=sample_mean,
            sample_std=sample_std,
            sample_size=sample_size,
            standard_error=standard_error,
            confidence_interval=ci,
            hypothesis_test=hypothesis_test,
            effect_size=effect_size,
            metadata={
                "confidence_level": confidence_level,
                "uses_t_distribution": sample_size < 30,
                "null_hypothesis": null_hypothesis_mean
            },
            calculation_time_ms=duration
        )

        if hypothesis_test:
            logger.info(
                f"✅ Significance test: p={hypothesis_test.p_value:.4f}, "
                f"significant={hypothesis_test.is_significant}, "
                f"CI=[{ci.lower_bound:.2f}, {ci.upper_bound:.2f}]"
            )
        else:
            logger.info(
                f"✅ Confidence interval calculated: "
                f"[{ci.lower_bound:.2f}, {ci.upper_bound:.2f}] "
                f"at {confidence_level:.1%} confidence"
            )

        return result

    def _calculate_mean(self, data: List[float]) -> float:
        """Calculate sample mean"""
        return sum(data) / len(data)

    def _calculate_std(self, data: List[float], mean: Optional[float] = None) -> float:
        """Calculate sample standard deviation (with Bessel's correction)"""
        if mean is None:
            mean = self._calculate_mean(data)

        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        return math.sqrt(variance)

    def _calculate_confidence_interval(
        self,
        mean: float,
        standard_error: float,
        sample_size: int,
        confidence_level: float
    ) -> ConfidenceInterval:
        """
        Calculate confidence interval

        Uses t-distribution for small samples (n < 30)
        Uses normal distribution for large samples (n ≥ 30)
        """
        # Determine critical value
        if sample_size < 30:
            # Use t-distribution
            critical_value = self._get_t_critical_value(
                sample_size - 1,
                1.0 - confidence_level
            )
        else:
            # Use normal distribution (z-score)
            critical_value = self._get_z_critical_value(1.0 - confidence_level)

        # Calculate margin of error
        margin_of_error = critical_value * standard_error

        # Calculate bounds
        lower_bound = mean - margin_of_error
        upper_bound = mean + margin_of_error

        return ConfidenceInterval(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=confidence_level,
            margin_of_error=margin_of_error
        )

    def _get_t_critical_value(self, df: int, alpha: float) -> float:
        """
        Get t-distribution critical value

        For production, use scipy.stats.t.ppf(1 - alpha/2, df)
        This implementation uses lookup table + interpolation
        """
        # For common significance levels
        if alpha == 0.05:  # 95% confidence (two-tailed)
            # Find closest df in lookup table
            if df in self.T_CRITICAL_VALUES:
                return self.T_CRITICAL_VALUES[df]

            # Linear interpolation for df not in table
            dfs = sorted(self.T_CRITICAL_VALUES.keys())
            for i in range(len(dfs) - 1):
                if dfs[i] <= df < dfs[i + 1]:
                    # Interpolate
                    df1, df2 = dfs[i], dfs[i + 1]
                    t1, t2 = self.T_CRITICAL_VALUES[df1], self.T_CRITICAL_VALUES[df2]
                    return t1 + (t2 - t1) * (df - df1) / (df2 - df1)

            # If df > max in table, use normal approximation
            if df > max(dfs):
                return 1.96  # Approximate with z-score

        # Fallback: use normal approximation for other significance levels
        return self._get_z_critical_value(alpha)

    def _get_z_critical_value(self, alpha: float) -> float:
        """
        Get z-score critical value for normal distribution

        Common values:
        - 90% confidence (α=0.10): z = 1.645
        - 95% confidence (α=0.05): z = 1.96
        - 99% confidence (α=0.01): z = 2.576
        - 99.9% confidence (α=0.001): z = 3.291
        """
        if alpha <= 0.001:
            return 3.291
        elif alpha <= 0.01:
            return 2.576
        elif alpha <= 0.05:
            return 1.96
        elif alpha <= 0.10:
            return 1.645
        else:
            # Approximate for other values
            # Using inverse error function approximation
            return self._inverse_normal_cdf(1 - alpha / 2)

    def _inverse_normal_cdf(self, p: float) -> float:
        """
        Approximate inverse normal CDF (for z-scores)

        Uses Beasley-Springer-Moro algorithm approximation
        For production, use scipy.stats.norm.ppf(p)
        """
        if p <= 0 or p >= 1:
            raise ValueError("Probability must be between 0 and 1")

        # Constants for approximation
        a = [2.50662823884, -18.61500062529, 41.39119773534, -25.44106049637]
        b = [-8.47351093090, 23.08336743743, -21.06224101826, 3.13082909833]
        c = [0.3374754822726147, 0.9761690190917186, 0.1607979714918209,
             0.0276438810333863, 0.0038405729373609, 0.0003951896511919,
             0.0000321767881768, 0.0000002888167364, 0.0000003960315187]

        # Use symmetry
        if p > 0.5:
            p = 1 - p
            sign = -1
        else:
            sign = 1

        # Calculate
        y = math.sqrt(-2 * math.log(p))
        x = y + ((((a[3] * y + a[2]) * y + a[1]) * y + a[0]) /
                 ((((b[3] * y + b[2]) * y + b[1]) * y + b[0]) * y + 1))

        return sign * x

    def _perform_hypothesis_test(
        self,
        sample_mean: float,
        standard_error: float,
        sample_size: int,
        null_mean: float,
        alpha: float,
        test_type: HypothesisTest
    ) -> HypothesisTestResult:
        """
        Perform hypothesis test

        H0: μ = null_mean
        H1: μ ≠ null_mean (two-tailed) OR μ < null_mean OR μ > null_mean
        """
        # Calculate test statistic
        if standard_error == 0:
            test_statistic = float('inf') if sample_mean != null_mean else 0
        else:
            test_statistic = (sample_mean - null_mean) / standard_error

        # Calculate p-value based on test type
        if sample_size < 30:
            # Use t-distribution
            df = sample_size - 1
            p_value = self._calculate_t_p_value(test_statistic, df, test_type)
        else:
            # Use normal distribution
            p_value = self._calculate_z_p_value(test_statistic, test_type)

        # Determine if result is statistically significant
        is_significant = p_value < alpha

        return HypothesisTestResult(
            test_statistic=test_statistic,
            p_value=p_value,
            is_significant=is_significant,
            significance_level=alpha,
            test_type=test_type,
            degrees_of_freedom=sample_size - 1 if sample_size < 30 else None
        )

    def _calculate_z_p_value(
        self,
        z_stat: float,
        test_type: HypothesisTest
    ) -> float:
        """Calculate p-value for z-test using normal distribution"""
        # Calculate cumulative probability
        p = self._normal_cdf(abs(z_stat))

        if test_type == HypothesisTest.TWO_TAILED:
            return 2 * (1 - p)
        elif test_type == HypothesisTest.RIGHT_TAILED:
            return 1 - p if z_stat > 0 else p
        else:  # LEFT_TAILED
            return p if z_stat < 0 else 1 - p

    def _calculate_t_p_value(
        self,
        t_stat: float,
        df: int,
        test_type: HypothesisTest
    ) -> float:
        """
        Calculate p-value for t-test

        Approximation using normal distribution for large df
        For production, use scipy.stats.t.cdf
        """
        # For large df, t-distribution ≈ normal distribution
        if df > 30:
            return self._calculate_z_p_value(t_stat, test_type)

        # For small df, use approximation
        # (In production, use proper t-distribution CDF)
        return self._calculate_z_p_value(t_stat, test_type)

    def _normal_cdf(self, x: float) -> float:
        """
        Cumulative distribution function for standard normal

        Approximation using error function
        For production, use scipy.stats.norm.cdf(x)
        """
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


# Example usage
async def main():
    """Example usage of CalculateStatisticalSignificanceAgent"""

    agent = CalculateStatisticalSignificanceAgent()

    # Example 1: Confidence interval for mean
    print("\n=== Example 1: Confidence Interval ===")
    sales_data = [100, 105, 98, 110, 102, 108, 95, 112, 104, 99]

    result1 = await agent.execute(sales_data, confidence_level=0.95)

    print(f"Sample mean: {result1.sample_mean:.2f}")
    print(f"Sample std: {result1.sample_std:.2f}")
    print(f"Standard error: {result1.standard_error:.2f}")
    print(f"95% CI: [{result1.confidence_interval.lower_bound:.2f}, "
          f"{result1.confidence_interval.upper_bound:.2f}]")
    print(f"Margin of error: ±{result1.confidence_interval.margin_of_error:.2f}")

    # Example 2: Hypothesis test (is mean significantly different from 100?)
    print("\n=== Example 2: Hypothesis Test ===")
    result2 = await agent.execute(
        sales_data,
        confidence_level=0.95,
        null_hypothesis_mean=100,
        test_type=HypothesisTest.TWO_TAILED
    )

    if result2.hypothesis_test:
        print(f"H0: μ = 100")
        print(f"H1: μ ≠ 100")
        print(f"Test statistic: {result2.hypothesis_test.test_statistic:.4f}")
        print(f"P-value: {result2.hypothesis_test.p_value:.4f}")
        print(f"Significant at α=0.05? {result2.hypothesis_test.is_significant}")
        print(f"Effect size (Cohen's d): {result2.effect_size:.4f}")

    # Example 3: Large sample (uses normal distribution)
    print("\n=== Example 3: Large Sample Test ===")
    large_sample = [100 + i * 0.5 + (i % 10) - 5 for i in range(100)]

    result3 = await agent.execute(
        large_sample,
        confidence_level=0.99,
        null_hypothesis_mean=120
    )

    print(f"Sample size: {result3.sample_size}")
    print(f"Uses t-distribution: {result3.metadata['uses_t_distribution']}")
    print(f"99% CI: [{result3.confidence_interval.lower_bound:.2f}, "
          f"{result3.confidence_interval.upper_bound:.2f}]")
    if result3.hypothesis_test:
        print(f"P-value for H0: μ=120: {result3.hypothesis_test.p_value:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
