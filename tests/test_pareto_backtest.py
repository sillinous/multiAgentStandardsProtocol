"""
Comprehensive Tests for Pareto Evolution and Backtesting

Tests multi-objective optimization and historical strategy validation.
"""

import pytest
from datetime import datetime, timedelta
from superstandard.agents.pareto_evolution import (
    ParetoEvolutionEngine,
    ParetoEvolutionConfig,
    NSGA2,
    Objective,
    ObjectiveType,
    MultiObjectiveScore,
    MultiObjectiveEvaluator
)
from superstandard.agents.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    MarketBar,
    HistoricalDataGenerator
)


# ============================================================================
# NSGA-II Algorithm Tests
# ============================================================================

@pytest.mark.unit
class TestNSGA2:
    """Test NSGA-II multi-objective optimization algorithms"""

    def test_dominance_check(self, sample_objectives):
        """Test Pareto dominance comparison"""
        score1 = MultiObjectiveScore(agent_id="agent-1")
        score1.objectives = {
            ObjectiveType.RETURN: 0.25,      # Better
            ObjectiveType.SHARPE_RATIO: 1.8,  # Better
            ObjectiveType.MAX_DRAWDOWN: -0.10  # Better (less drawdown)
        }

        score2 = MultiObjectiveScore(agent_id="agent-2")
        score2.objectives = {
            ObjectiveType.RETURN: 0.20,
            ObjectiveType.SHARPE_RATIO: 1.5,
            ObjectiveType.MAX_DRAWDOWN: -0.15
        }

        # score1 should dominate score2
        assert score1.dominates(score2, sample_objectives)
        assert not score2.dominates(score1, sample_objectives)

    def test_non_dominated_sorting(self, sample_objectives):
        """Test fast non-dominated sorting"""
        scores = []

        # Create population with clear fronts
        # Front 0 (best): High return, low drawdown
        for i in range(3):
            score = MultiObjectiveScore(agent_id=f"front0-{i}")
            score.objectives = {
                ObjectiveType.RETURN: 0.30 + i * 0.01,
                ObjectiveType.SHARPE_RATIO: 2.0 + i * 0.1,
                ObjectiveType.MAX_DRAWDOWN: -0.08 - i * 0.01
            }
            scores.append(score)

        # Front 1 (middle)
        for i in range(3):
            score = MultiObjectiveScore(agent_id=f"front1-{i}")
            score.objectives = {
                ObjectiveType.RETURN: 0.20 + i * 0.01,
                ObjectiveType.SHARPE_RATIO: 1.5 + i * 0.1,
                ObjectiveType.MAX_DRAWDOWN: -0.12 - i * 0.01
            }
            scores.append(score)

        # Front 2 (worst)
        for i in range(2):
            score = MultiObjectiveScore(agent_id=f"front2-{i}")
            score.objectives = {
                ObjectiveType.RETURN: 0.10 + i * 0.01,
                ObjectiveType.SHARPE_RATIO: 1.0 + i * 0.1,
                ObjectiveType.MAX_DRAWDOWN: -0.20 - i * 0.01
            }
            scores.append(score)

        fronts = NSGA2.fast_non_dominated_sort(scores, sample_objectives)

        assert len(fronts) >= 2
        assert len(fronts[0]) == 3  # First front should have 3 solutions
        assert all(s.dominance_rank == 0 for s in fronts[0])

    def test_crowding_distance(self, sample_objectives):
        """Test crowding distance calculation"""
        front = []

        # Create solutions along Pareto frontier
        for i in range(5):
            score = MultiObjectiveScore(agent_id=f"agent-{i}")
            score.objectives = {
                ObjectiveType.RETURN: 0.10 + i * 0.05,
                ObjectiveType.SHARPE_RATIO: 2.0 - i * 0.2,
                ObjectiveType.MAX_DRAWDOWN: -0.10 - i * 0.02
            }
            front.append(score)

        NSGA2.calculate_crowding_distance(front, sample_objectives)

        # Boundary solutions should have infinite distance
        assert front[0].crowding_distance == float('inf')
        assert front[-1].crowding_distance == float('inf')

        # Middle solutions should have finite distance
        assert 0 < front[2].crowding_distance < float('inf')


# ============================================================================
# Pareto Evolution Engine Tests
# ============================================================================

@pytest.mark.unit
class TestParetoEvolutionEngine:
    """Test Pareto evolution engine"""

    def test_engine_initialization(self, sample_objectives):
        """Test engine initializes correctly"""
        config = ParetoEvolutionConfig(
            population_size=20,
            num_generations=10,
            objectives=sample_objectives,
            mutation_rate=0.1
        )

        engine = ParetoEvolutionEngine(config)

        assert engine.config.population_size == 20
        assert engine.config.num_generations == 10
        assert len(engine.config.objectives) == 3

    def test_multi_objective_evaluation(self, sample_objectives):
        """Test multi-objective score evaluation"""
        evaluator = MultiObjectiveEvaluator()

        metrics = {
            'total_return_percent': 25.5,
            'sharpe_ratio': 1.85,
            'max_drawdown_percent': -12.3,
            'win_rate': 0.65
        }

        score = evaluator.evaluate("test-agent", metrics, sample_objectives)

        assert score.agent_id == "test-agent"
        assert ObjectiveType.RETURN in score.objectives
        assert ObjectiveType.SHARPE_RATIO in score.objectives
        assert ObjectiveType.MAX_DRAWDOWN in score.objectives


# ============================================================================
# Backtesting Engine Tests
# ============================================================================

@pytest.mark.unit
class TestBacktestEngine:
    """Test backtesting functionality"""

    def test_market_bar_creation(self):
        """Test MarketBar creation"""
        bar = MarketBar(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=102.0,
            volume=1000000
        )

        assert bar.open == 100.0
        assert bar.close == 102.0
        assert bar.high > bar.low

    def test_historical_data_generation(self):
        """Test synthetic market data generation"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        data = HistoricalDataGenerator.generate_price_data(
            start_date=start_date,
            end_date=end_date,
            initial_price=100.0,
            volatility=0.02
        )

        assert len(data) == 30  # One bar per day
        assert all(isinstance(bar, MarketBar) for bar in data)
        assert data[0].close > 0

    def test_backtest_config_validation(self):
        """Test backtest configuration"""
        config = BacktestConfig(
            symbol="BTC/USD",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            initial_capital=10000.0,
            commission_rate=0.001,
            slippage_rate=0.0005
        )

        assert config.symbol == "BTC/USD"
        assert config.initial_capital == 10000.0
        assert 0 < config.commission_rate < 1
        assert 0 < config.slippage_rate < 1

    @pytest.mark.slow
    def test_backtest_execution(self, sample_market_data, mock_ensemble):
        """Test complete backtest execution"""
        config = BacktestConfig(
            symbol="TEST/USD",
            start_date=datetime.now() - timedelta(days=100),
            end_date=datetime.now(),
            initial_capital=10000.0
        )

        engine = BacktestEngine(config)
        result = engine.run(mock_ensemble, sample_market_data)

        # Verify result structure
        assert result.backtest_id is not None
        assert result.metrics is not None
        assert len(result.equity_curve) > 0
        assert result.metrics.total_decisions > 0

    def test_backtest_metrics_calculation(self, sample_market_data, mock_ensemble):
        """Test backtest metrics are calculated correctly"""
        config = BacktestConfig(
            symbol="TEST/USD",
            start_date=datetime.now() - timedelta(days=100),
            end_date=datetime.now(),
            initial_capital=10000.0
        )

        engine = BacktestEngine(config)
        result = engine.run(mock_ensemble, sample_market_data)

        metrics = result.metrics

        # Verify all metrics are present
        assert hasattr(metrics, 'total_return_percent')
        assert hasattr(metrics, 'sharpe_ratio')
        assert hasattr(metrics, 'max_drawdown_percent')
        assert hasattr(metrics, 'win_rate')
        assert hasattr(metrics, 'total_trades')

        # Verify metrics are reasonable
        assert -100 <= metrics.total_return_percent <= 1000
        assert -10 <= metrics.sharpe_ratio <= 10
        assert -100 <= metrics.max_drawdown_percent <= 0
        assert 0 <= metrics.win_rate <= 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestParetoBacktestIntegration:
    """Integration tests combining Pareto evolution with backtesting"""

    def test_pareto_evolution_with_backtesting(self, sample_objectives, sample_genomes):
        """Test Pareto evolution using backtest-based fitness"""
        config = ParetoEvolutionConfig(
            population_size=10,
            num_generations=5,
            objectives=sample_objectives,
            mutation_rate=0.1
        )

        engine = ParetoEvolutionEngine(config)

        # Mock fitness function returning backtest-like metrics
        def fitness_func(genome):
            # Simulate different performance based on personality
            openness = genome.personality.openness
            conscientiousness = genome.personality.conscientiousness

            return {
                'total_return_percent': 10.0 + (openness * 20),
                'sharpe_ratio': 1.0 + (conscientiousness * 1.5),
                'max_drawdown_percent': -15.0 + (openness * 5),
                'win_rate': 0.5 + (conscientiousness * 0.3)
            }

        # Run evolution
        result = engine.evolve(fitness_func, initial_population=sample_genomes)

        # Verify results
        assert len(result.pareto_frontier) > 0
        assert len(result.all_fronts) > 0
        assert len(result.generation_history) == config.num_generations

        # Verify Pareto frontier is actually non-dominated
        frontier_genomes, frontier_scores = zip(*result.pareto_frontier)
        fronts = NSGA2.fast_non_dominated_sort(list(frontier_scores), sample_objectives)
        assert len(fronts[0]) == len(result.pareto_frontier)  # All should be in first front


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
