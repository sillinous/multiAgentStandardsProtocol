"""
Comprehensive Tests for Continuous Evolution in Production

Tests the revolutionary autonomous self-improvement system including:
- Performance degradation detection
- A/B testing framework
- Champion management
- Auto-promotion logic
"""

import pytest
from datetime import datetime, timedelta
from superstandard.agents.continuous_evolution import (
    ContinuousEvolutionEngine,
    ContinuousEvolutionConfig,
    DegradationDetectionConfig,
    ABTestConfig,
    PerformanceDegradationDetector,
    PerformanceMetrics,
    ABTest,
    ABTestStatus,
    EvolutionTrigger
)


# ============================================================================
# Performance Degradation Detection Tests
# ============================================================================

@pytest.mark.unit
class TestPerformanceDegradationDetector:
    """Test degradation detection algorithms"""

    def test_detector_initialization(self):
        """Test detector initializes with correct configuration"""
        config = DegradationDetectionConfig(
            window_size=100,
            baseline_window=500,
            win_rate_threshold=0.10
        )

        detector = PerformanceDegradationDetector(config)

        assert detector.config.window_size == 100
        assert detector.config.baseline_window == 500
        assert len(detector.metrics_history) == 0
        assert len(detector.recent_metrics) == 0

    def test_record_metrics(self):
        """Test recording performance metrics"""
        config = DegradationDetectionConfig(window_size=50)
        detector = PerformanceDegradationDetector(config)

        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            win_rate=0.65,
            total_return=15.5,
            sharpe_ratio=1.8,
            max_drawdown=-0.12,
            total_decisions=100,
            confidence_avg=0.75
        )

        detector.record_metrics(metrics)

        assert len(detector.metrics_history) == 1
        assert len(detector.recent_metrics) == 1
        assert detector.metrics_history[0].win_rate == 0.65

    def test_no_degradation_with_insufficient_data(self):
        """Test no degradation detected without enough data"""
        config = DegradationDetectionConfig(
            window_size=50,
            min_decisions_before_check=30
        )
        detector = PerformanceDegradationDetector(config)

        # Add only 20 metrics (below minimum)
        for i in range(20):
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                win_rate=0.6,
                total_return=10.0,
                sharpe_ratio=1.5,
                max_drawdown=-0.10,
                total_decisions=i,
                confidence_avg=0.7
            )
            detector.record_metrics(metrics)

        is_degraded, details = detector.check_degradation()

        assert not is_degraded
        assert details['reason'] == 'insufficient_data'

    def test_detect_win_rate_degradation(self):
        """Test detection of win rate degradation"""
        config = DegradationDetectionConfig(
            window_size=20,
            baseline_window=50,
            win_rate_threshold=0.10,
            min_decisions_before_check=10
        )
        detector = PerformanceDegradationDetector(config)

        # Create baseline (good performance)
        for i in range(50):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=50-i),
                win_rate=0.70,  # Good win rate
                total_return=15.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                total_decisions=i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        # Add degraded recent performance
        for i in range(20):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=20-i),
                win_rate=0.55,  # Degraded by >15% (0.70 → 0.55)
                total_return=10.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                total_decisions=50+i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        is_degraded, details = detector.check_degradation()

        assert is_degraded
        assert details['degraded'] is True
        assert len(details['flags']) > 0
        assert any(flag['metric'] == 'win_rate' for flag in details['flags'])

    def test_detect_sharpe_degradation(self):
        """Test detection of Sharpe ratio degradation"""
        config = DegradationDetectionConfig(
            window_size=15,
            baseline_window=40,
            sharpe_threshold=0.20,
            min_decisions_before_check=10
        )
        detector = PerformanceDegradationDetector(config)

        # Baseline with good Sharpe
        for i in range(40):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=40-i),
                win_rate=0.65,
                total_return=15.0,
                sharpe_ratio=2.0,  # Good Sharpe
                max_drawdown=-0.10,
                total_decisions=i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        # Recent degraded Sharpe
        for i in range(15):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=15-i),
                win_rate=0.65,
                total_return=15.0,
                sharpe_ratio=1.5,  # Degraded by 25% (2.0 → 1.5)
                max_drawdown=-0.10,
                total_decisions=40+i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        is_degraded, details = detector.check_degradation()

        assert is_degraded
        assert any(flag['metric'] == 'sharpe_ratio' for flag in details['flags'])


# ============================================================================
# A/B Testing Framework Tests
# ============================================================================

@pytest.mark.unit
class TestABTestFramework:
    """Test A/B testing functionality"""

    def test_ab_test_initialization(self, sample_genome):
        """Test A/B test creation"""
        config = ABTestConfig(traffic_split=0.20)

        ab_test = ABTest(
            test_id="test-123",
            ensemble_id="ensemble-456",
            champion_genome=sample_genome,
            challenger_genome=sample_genome,
            started_at=datetime.now(),
            config=config
        )

        assert ab_test.test_id == "test-123"
        assert ab_test.status == ABTestStatus.RUNNING
        assert ab_test.winner is None
        assert len(ab_test.champion_decisions) == 0
        assert len(ab_test.challenger_decisions) == 0

    def test_record_champion_decision(self, sample_genome):
        """Test recording champion decisions"""
        config = ABTestConfig()
        ab_test = ABTest(
            test_id="test-123",
            ensemble_id="ensemble-456",
            champion_genome=sample_genome,
            challenger_genome=sample_genome,
            started_at=datetime.now(),
            config=config
        )

        # Record winning decision
        ab_test.record_decision(
            is_challenger=False,
            decision="buy",
            outcome=150.0,  # Positive outcome
            confidence=0.85
        )

        assert len(ab_test.champion_decisions) == 1
        assert ab_test.champion_decisions[0]['decision'] == "buy"
        assert ab_test.champion_decisions[0]['outcome'] == 150.0

    def test_ab_test_metrics_update(self, sample_genome):
        """Test automatic metrics calculation"""
        config = ABTestConfig()
        ab_test = ABTest(
            test_id="test-123",
            ensemble_id="ensemble-456",
            champion_genome=sample_genome,
            challenger_genome=sample_genome,
            started_at=datetime.now(),
            config=config
        )

        # Record multiple decisions
        for i in range(10):
            outcome = 100.0 if i % 2 == 0 else -50.0  # 50% win rate
            ab_test.record_decision(
                is_challenger=False,
                decision="buy" if i % 2 == 0 else "sell",
                outcome=outcome,
                confidence=0.7
            )

        assert ab_test.champion_win_rate == 0.5  # 5 wins out of 10
        assert len(ab_test.champion_decisions) == 10

    def test_challenger_wins_evaluation(self, sample_genome):
        """Test challenger wins when significantly better"""
        config = ABTestConfig(
            min_decisions_per_strategy=10,
            confidence_level=0.95
        )
        ab_test = ABTest(
            test_id="test-123",
            ensemble_id="ensemble-456",
            champion_genome=sample_genome,
            challenger_genome=sample_genome,
            started_at=datetime.now(),
            config=config
        )

        # Champion: 50% win rate
        for i in range(20):
            outcome = 100.0 if i % 2 == 0 else -50.0
            ab_test.record_decision(
                is_challenger=False,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        # Challenger: 70% win rate (significantly better)
        for i in range(20):
            outcome = 100.0 if i < 14 else -50.0
            ab_test.record_decision(
                is_challenger=True,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        status = ab_test.evaluate()

        assert status == ABTestStatus.CHALLENGER_WINS
        assert ab_test.winner == "challenger"
        assert ab_test.challenger_win_rate > ab_test.champion_win_rate * 1.05

    def test_champion_wins_evaluation(self, sample_genome):
        """Test champion wins when better"""
        config = ABTestConfig(min_decisions_per_strategy=10)
        ab_test = ABTest(
            test_id="test-123",
            ensemble_id="ensemble-456",
            champion_genome=sample_genome,
            challenger_genome=sample_genome,
            started_at=datetime.now(),
            config=config
        )

        # Champion: 70% win rate
        for i in range(20):
            outcome = 100.0 if i < 14 else -50.0
            ab_test.record_decision(
                is_challenger=False,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        # Challenger: 50% win rate
        for i in range(20):
            outcome = 100.0 if i % 2 == 0 else -50.0
            ab_test.record_decision(
                is_challenger=True,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        status = ab_test.evaluate()

        assert status == ABTestStatus.CHAMPION_WINS
        assert ab_test.winner == "champion"


# ============================================================================
# Continuous Evolution Engine Tests
# ============================================================================

@pytest.mark.unit
class TestContinuousEvolutionEngine:
    """Test main continuous evolution engine"""

    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        config = ContinuousEvolutionConfig(
            enabled=True,
            auto_promote=True,
            backup_champions=5
        )

        engine = ContinuousEvolutionEngine(config)

        assert engine.config.enabled is True
        assert engine.config.auto_promote is True
        assert len(engine.active_ab_tests) == 0
        assert len(engine.evolution_history) == 0

    def test_create_ab_test(self, sample_genome):
        """Test A/B test creation"""
        config = ContinuousEvolutionConfig()
        engine = ContinuousEvolutionEngine(config)

        ab_test = engine.create_ab_test(
            ensemble_id="test-ensemble",
            champion_genome=sample_genome,
            challenger_genome=sample_genome
        )

        assert ab_test.test_id in engine.active_ab_tests
        assert ab_test.ensemble_id == "test-ensemble"
        assert ab_test.status == ABTestStatus.RUNNING

    def test_record_decision_outcome(self, sample_genome):
        """Test recording decision outcomes"""
        config = ContinuousEvolutionConfig()
        engine = ContinuousEvolutionEngine(config)

        ab_test = engine.create_ab_test(
            ensemble_id="test-ensemble",
            champion_genome=sample_genome,
            challenger_genome=sample_genome
        )

        engine.record_decision_outcome(
            test_id=ab_test.test_id,
            is_challenger=False,
            decision="buy",
            outcome=125.0,
            confidence=0.8
        )

        test = engine.active_ab_tests[ab_test.test_id]
        assert len(test.champion_decisions) == 1

    def test_evolution_summary(self, sample_genome):
        """Test evolution summary generation"""
        config = ContinuousEvolutionConfig()
        engine = ContinuousEvolutionEngine(config)

        # Create an A/B test
        ab_test = engine.create_ab_test(
            ensemble_id="test-ensemble",
            champion_genome=sample_genome,
            challenger_genome=sample_genome
        )

        summary = engine.get_evolution_summary("test-ensemble")

        assert summary['total_evolution_cycles'] == 0
        assert summary['active_ab_tests'] == 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestContinuousEvolutionIntegration:
    """Integration tests for complete evolution workflow"""

    def test_complete_evolution_cycle(self, sample_genome):
        """Test complete evolution cycle from degradation to promotion"""
        config = ContinuousEvolutionConfig(
            auto_promote=True,
            degradation_config=DegradationDetectionConfig(
                window_size=20,
                baseline_window=50,
                win_rate_threshold=0.10,
                min_decisions_before_check=10
            ),
            ab_test_config=ABTestConfig(
                min_decisions_per_strategy=15,
                traffic_split=0.20
            )
        )

        engine = ContinuousEvolutionEngine(config)

        # Simulate degradation detection
        detector = engine.degradation_detector

        # Good baseline
        for i in range(50):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=50-i),
                win_rate=0.70,
                total_return=15.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                total_decisions=i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        # Degraded recent
        for i in range(20):
            metrics = PerformanceMetrics(
                timestamp=datetime.now() - timedelta(hours=20-i),
                win_rate=0.55,  # Degraded
                total_return=10.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                total_decisions=50+i,
                confidence_avg=0.75
            )
            detector.record_metrics(metrics)

        # Check degradation
        is_degraded, details = detector.check_degradation()
        assert is_degraded

        # Create A/B test (simulating evolution)
        champion = sample_genome
        challenger = AgentGenome(
            agent_id="challenger-123",
            generation=1,
            personality_traits={'openness': 0.8, 'conscientiousness': 0.9}
        )

        ab_test = engine.create_ab_test(
            ensemble_id="test-ensemble",
            champion_genome=champion,
            challenger_genome=challenger
        )

        # Simulate A/B test where challenger wins
        # Champion: 50% win rate
        for i in range(20):
            outcome = 100.0 if i % 2 == 0 else -50.0
            engine.record_decision_outcome(
                test_id=ab_test.test_id,
                is_challenger=False,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        # Challenger: 70% win rate
        for i in range(20):
            outcome = 100.0 if i < 14 else -50.0
            engine.record_decision_outcome(
                test_id=ab_test.test_id,
                is_challenger=True,
                decision="buy",
                outcome=outcome,
                confidence=0.7
            )

        # Evaluate (should promote challenger)
        status = ab_test.evaluate()

        assert status == ABTestStatus.CHALLENGER_WINS
        assert ab_test.winner == "challenger"

        # Verify improvement
        improvement = ab_test.challenger_win_rate - ab_test.champion_win_rate
        assert improvement > 0.15  # 15%+ improvement


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
