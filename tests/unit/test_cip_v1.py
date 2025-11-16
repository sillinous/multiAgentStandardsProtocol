"""
Unit tests for Collective Intelligence Protocol (CIP) v1.0
"""

import pytest
from src.superstandard.protocols.cip_v1 import (
    SwarmContext, EmergenceMetrics, AgentEstimate, VotingOption, Vote,
    CollectiveDecisionResult,
    PoolingStrategy, ConflictResolution, DecisionMethod, AggregationMethod,
    KnowledgePool, CollectiveDecision, WisdomOfCrowds, ConsensusBuilder,
    SwarmOptimizer,
)


# ============================================================================
# DATA MODEL TESTS
# ============================================================================


def test_swarm_context_creation():
    """Test swarm context creation"""
    context = SwarmContext(
        swarm_id="swarm_001",
        swarm_size=10,
        topology="fully_connected",
    )

    assert context.swarm_id == "swarm_001"
    assert context.swarm_size == 10


def test_emergence_metrics_creation():
    """Test emergence metrics"""
    metrics = EmergenceMetrics(
        diversity_index=0.8,
        coherence_score=0.6,
        synergy_factor=1.5,
    )

    assert metrics.diversity_index == 0.8
    assert metrics.synergy_factor == 1.5


def test_agent_estimate_creation():
    """Test agent estimate"""
    estimate = AgentEstimate(
        agent_id="agent_1",
        estimate=15000000,
        confidence=0.8,
        reasoning="Based on historical trends",
    )

    assert estimate.agent_id == "agent_1"
    assert estimate.estimate == 15000000
    assert estimate.confidence == 0.8


def test_voting_option_creation():
    """Test voting option"""
    option = VotingOption(
        option_id="option_a",
        description="Invest in AI",
        metadata={"cost": 1000000},
    )

    assert option.option_id == "option_a"
    assert option.metadata["cost"] == 1000000


def test_vote_creation():
    """Test vote creation"""
    vote = Vote(
        agent_id="agent_1",
        option_id="option_a",
        weight=1.5,
        confidence=0.9,
    )

    assert vote.agent_id == "agent_1"
    assert vote.weight == 1.5


# ============================================================================
# KNOWLEDGE POOLING TESTS
# ============================================================================


def test_knowledge_pool_weighted_merge():
    """Test weighted merge pooling"""
    contributions = [
        {
            "agent_id": "agent_1",
            "confidence": 0.9,
            "knowledge": {"fact_a": 10, "fact_b": "value1"},
        },
        {
            "agent_id": "agent_2",
            "confidence": 0.7,
            "knowledge": {"fact_a": 12, "fact_b": "value2"},
        },
    ]

    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.WEIGHTED_MERGE,
        confidence_threshold=0.5,
    )

    assert "fact_a" in pooled
    # Should be weighted average of 10 (0.9 weight) and 12 (0.7 weight)
    expected = (10 * 0.9 + 12 * 0.7) / (0.9 + 0.7)
    assert abs(pooled["fact_a"] - expected) < 0.01


def test_knowledge_pool_union():
    """Test union pooling"""
    contributions = [
        {"knowledge": {"fact_a": 1, "fact_b": 2}},
        {"knowledge": {"fact_c": 3, "fact_d": 4}},
    ]

    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.UNION,
    )

    assert len(pooled) == 4
    assert "fact_a" in pooled
    assert "fact_c" in pooled


def test_knowledge_pool_intersection():
    """Test intersection pooling"""
    contributions = [
        {"knowledge": {"fact_a": 1, "fact_b": 2, "fact_c": 3}},
        {"knowledge": {"fact_a": 1, "fact_b": 5, "fact_d": 4}},
    ]

    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.INTERSECTION,
    )

    # Only fact_a and fact_b are in both
    assert len(pooled) == 2
    assert "fact_a" in pooled
    assert "fact_b" in pooled
    assert "fact_c" not in pooled


def test_knowledge_pool_voting():
    """Test voting merge"""
    contributions = [
        {"knowledge": {"fact_a": "value1"}},
        {"knowledge": {"fact_a": "value1"}},
        {"knowledge": {"fact_a": "value2"}},
    ]

    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.VOTING,
    )

    # value1 should win (2 votes vs 1)
    assert pooled["fact_a"] == "value1"


def test_knowledge_pool_confidence_threshold():
    """Test confidence threshold filtering"""
    contributions = [
        {"confidence": 0.9, "knowledge": {"fact_a": 1}},
        {"confidence": 0.3, "knowledge": {"fact_b": 2}},  # Below threshold
    ]

    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.WEIGHTED_MERGE,
        confidence_threshold=0.7,
    )

    assert "fact_a" in pooled
    assert "fact_b" not in pooled  # Filtered out


# ============================================================================
# COLLECTIVE DECISION TESTS
# ============================================================================


def test_collective_decision_simple_majority():
    """Test simple majority voting"""
    options = [
        VotingOption("option_a", "Option A"),
        VotingOption("option_b", "Option B"),
    ]

    votes = [
        Vote("agent_1", "option_a"),
        Vote("agent_2", "option_a"),
        Vote("agent_3", "option_b"),
    ]

    result = CollectiveDecision.make_decision(
        options, votes, method=DecisionMethod.SIMPLE_MAJORITY
    )

    assert result.winning_option == "option_a"
    assert result.votes_by_option["option_a"] == 2.0
    assert result.votes_by_option["option_b"] == 1.0
    assert result.total_votes == 3.0


def test_collective_decision_weighted_voting():
    """Test weighted voting"""
    options = [
        VotingOption("option_a", "Option A"),
        VotingOption("option_b", "Option B"),
    ]

    votes = [
        Vote("agent_1", "option_a", weight=1.5),
        Vote("agent_2", "option_b", weight=2.0),
        Vote("agent_3", "option_a", weight=1.0),
    ]

    result = CollectiveDecision.make_decision(
        options, votes, method=DecisionMethod.WEIGHTED_VOTING
    )

    assert result.winning_option == "option_a"  # 2.5 vs 2.0
    assert result.votes_by_option["option_a"] == 2.5
    assert result.votes_by_option["option_b"] == 2.0


def test_collective_decision_quadratic_voting():
    """Test quadratic voting"""
    options = [
        VotingOption("option_a", "Option A"),
        VotingOption("option_b", "Option B"),
    ]

    votes = [
        Vote("agent_1", "option_a", weight=4.0),  # sqrt(4) = 2 votes
        Vote("agent_2", "option_b", weight=9.0),  # sqrt(9) = 3 votes
    ]

    result = CollectiveDecision.make_decision(
        options, votes, method=DecisionMethod.QUADRATIC_VOTING
    )

    assert result.winning_option == "option_b"  # 3 vs 2


def test_collective_decision_consensus_level():
    """Test consensus level calculation"""
    options = [
        VotingOption("option_a", "Option A"),
        VotingOption("option_b", "Option B"),
    ]

    votes = [
        Vote("agent_1", "option_a"),
        Vote("agent_2", "option_a"),
        Vote("agent_3", "option_a"),
        Vote("agent_4", "option_b"),
    ]

    result = CollectiveDecision.make_decision(
        options, votes, method=DecisionMethod.SIMPLE_MAJORITY
    )

    # 3 out of 4 voted for winner
    assert result.consensus_level == 0.75


def test_collective_decision_emergence_metrics():
    """Test emergence metrics calculation"""
    options = [
        VotingOption("option_a", "Option A"),
        VotingOption("option_b", "Option B"),
    ]

    votes = [
        Vote("agent_1", "option_a"),
        Vote("agent_2", "option_b"),
    ]

    result = CollectiveDecision.make_decision(
        options, votes, method=DecisionMethod.SIMPLE_MAJORITY
    )

    assert result.emergence_metrics is not None
    assert 0.0 <= result.emergence_metrics.diversity_index <= 1.0
    assert 0.0 <= result.emergence_metrics.coherence_score <= 1.0


def test_collective_decision_quorum():
    """Test quorum requirement"""
    options = [VotingOption("option_a", "Option A")]
    votes = [Vote("agent_1", "option_a")]

    # Should raise error if quorum not met
    with pytest.raises(ValueError, match="Quorum not met"):
        CollectiveDecision.make_decision(
            options, votes, quorum_required=5  # Need 5 voters, only have 1
        )


# ============================================================================
# WISDOM OF CROWDS TESTS
# ============================================================================


def test_wisdom_of_crowds_mean():
    """Test mean aggregation"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 120),
        AgentEstimate("agent_3", 110),
    ]

    result = WisdomOfCrowds.aggregate_estimates(
        estimates, method=AggregationMethod.MEAN
    )

    assert result["aggregate"] == 110.0
    assert result["count"] == 3


def test_wisdom_of_crowds_median():
    """Test median aggregation"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 200),  # Outlier
        AgentEstimate("agent_3", 110),
    ]

    result = WisdomOfCrowds.aggregate_estimates(
        estimates, method=AggregationMethod.MEDIAN
    )

    assert result["aggregate"] == 110.0  # Median is robust to outliers


def test_wisdom_of_crowds_trimmed_mean():
    """Test trimmed mean (outlier removal)"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 105),
        AgentEstimate("agent_3", 110),
        AgentEstimate("agent_4", 1000),  # Extreme outlier
    ]

    result = WisdomOfCrowds.aggregate_estimates(
        estimates,
        method=AggregationMethod.TRIMMED_MEAN,
        outlier_threshold=2.0,
    )

    # Outlier should be removed, mean of 100, 105, 110 = 105
    assert 100 <= result["aggregate"] <= 110


def test_wisdom_of_crowds_confidence_weighted():
    """Test confidence-weighted aggregation"""
    estimates = [
        AgentEstimate("agent_1", 100, confidence=0.9),  # High confidence
        AgentEstimate("agent_2", 200, confidence=0.1),  # Low confidence
    ]

    result = WisdomOfCrowds.aggregate_estimates(
        estimates, method=AggregationMethod.CONFIDENCE_WEIGHTED
    )

    # Should be closer to 100 (high confidence) than 200
    assert result["aggregate"] < 150


def test_wisdom_of_crowds_agreement():
    """Test agreement calculation"""
    # High agreement (similar estimates)
    estimates1 = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 101),
        AgentEstimate("agent_3", 102),
    ]

    result1 = WisdomOfCrowds.aggregate_estimates(estimates1)

    # Low agreement (diverse estimates)
    estimates2 = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 200),
        AgentEstimate("agent_3", 300),
    ]

    result2 = WisdomOfCrowds.aggregate_estimates(estimates2)

    # High agreement should have higher score
    assert result1["agreement"] > result2["agreement"]


def test_wisdom_of_crowds_empty():
    """Test empty estimates"""
    result = WisdomOfCrowds.aggregate_estimates([])

    assert result["aggregate"] == 0.0
    assert result["count"] == 0


# ============================================================================
# CONSENSUS BUILDING TESTS
# ============================================================================


def test_consensus_building():
    """Test consensus building"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 200),
        AgentEstimate("agent_3", 150),
    ]

    result = ConsensusBuilder.build_consensus(
        estimates,
        max_iterations=10,
        convergence_threshold=0.1,
    )

    assert "consensus" in result
    assert "iterations" in result
    assert "converged" in result
    # Consensus should be somewhere between min and max
    assert 100 <= result["consensus"] <= 200


def test_consensus_convergence():
    """Test that consensus converges"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 200),
        AgentEstimate("agent_3", 150),
    ]

    result = ConsensusBuilder.build_consensus(
        estimates,
        max_iterations=20,
        convergence_threshold=0.05,
    )

    # Should converge (CV should decrease)
    if result["iterations"] > 1:
        assert result["history"][-1]["cv"] <= result["history"][0]["cv"]


def test_consensus_already_agreed():
    """Test consensus when estimates already agree"""
    estimates = [
        AgentEstimate("agent_1", 100),
        AgentEstimate("agent_2", 100),
        AgentEstimate("agent_3", 100),
    ]

    result = ConsensusBuilder.build_consensus(
        estimates,
        convergence_threshold=0.01,
    )

    # Should converge immediately
    assert result["converged"]
    assert result["iterations"] <= 1
    assert abs(result["consensus"] - 100) < 1.0


# ============================================================================
# SWARM OPTIMIZATION TESTS
# ============================================================================


def test_swarm_optimizer_initialization():
    """Test swarm optimizer initialization"""
    optimizer = SwarmOptimizer(
        dimensions=3,
        population_size=10,
    )

    assert optimizer.dimensions == 3
    assert optimizer.population_size == 10
    assert len(optimizer.particles) == 0  # Not initialized yet


def test_swarm_optimizer_sphere_function():
    """Test PSO on simple sphere function"""
    # Minimize sphere function: f(x) = sum(x_i^2)
    # Optimal solution is [0, 0, 0] with f(x) = 0
    def sphere(x):
        return sum(xi ** 2 for xi in x)

    optimizer = SwarmOptimizer(
        dimensions=3,
        population_size=20,
        inertia_weight=0.7,
        cognitive_weight=1.5,
        social_weight=1.5,
    )

    result = optimizer.optimize(
        objective_function=sphere,
        bounds=[(-10, 10)] * 3,
        max_iterations=50,
        minimize=True,
    )

    # Should find solution close to 0
    assert result["best_fitness"] < 1.0
    assert len(result["best_position"]) == 3
    # Each dimension should be close to 0
    for x in result["best_position"]:
        assert abs(x) < 1.0


def test_swarm_optimizer_maximize():
    """Test PSO maximization"""
    # Maximize: -sphere (inverted sphere)
    def neg_sphere(x):
        return -sum(xi ** 2 for xi in x)

    optimizer = SwarmOptimizer(dimensions=2, population_size=15)

    result = optimizer.optimize(
        objective_function=neg_sphere,
        bounds=[(-5, 5)] * 2,
        max_iterations=30,
        minimize=False,  # Maximize
    )

    # Maximum should be at [0, 0] with value 0
    assert result["best_fitness"] > -1.0


def test_swarm_optimizer_history():
    """Test that optimization history is tracked"""
    def sphere(x):
        return sum(xi ** 2 for xi in x)

    optimizer = SwarmOptimizer(dimensions=2, population_size=10)

    result = optimizer.optimize(
        objective_function=sphere,
        bounds=[(-5, 5)] * 2,
        max_iterations=20,
        minimize=True,
    )

    assert "history" in result
    assert len(result["history"]) == 20
    # Fitness should generally improve
    assert result["history"][-1]["best_fitness"] <= result["history"][0]["best_fitness"]


def test_swarm_optimizer_bounds():
    """Test that particles respect bounds"""
    def simple_func(x):
        return x[0]

    optimizer = SwarmOptimizer(dimensions=1, population_size=10)

    bounds = [(0, 1)]  # Constrained to [0, 1]

    result = optimizer.optimize(
        objective_function=simple_func,
        bounds=bounds,
        max_iterations=10,
        minimize=True,
    )

    # Best position should be within bounds
    assert 0 <= result["best_position"][0] <= 1


def test_swarm_optimizer_convergence():
    """Test that swarm converges over time"""
    def sphere(x):
        return sum(xi ** 2 for xi in x)

    optimizer = SwarmOptimizer(dimensions=2, population_size=20)

    result = optimizer.optimize(
        objective_function=sphere,
        bounds=[(-10, 10)] * 2,
        max_iterations=50,
        minimize=True,
    )

    # Later iterations should have better fitness
    early_fitness = result["history"][4]["best_fitness"]
    late_fitness = result["history"][-1]["best_fitness"]

    assert late_fitness <= early_fitness


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_end_to_end_decision_making():
    """Integration test: Full decision-making workflow"""
    # Scenario: Team deciding on project priority

    # 1. Knowledge pooling - gather context
    context_contributions = [
        {
            "agent_id": "analyst",
            "confidence": 0.9,
            "knowledge": {"market_opportunity": "high", "risk": "medium"},
        },
        {
            "agent_id": "engineer",
            "confidence": 0.8,
            "knowledge": {"technical_feasibility": "high", "risk": "low"},
        },
    ]

    pooled = KnowledgePool.pool_knowledge(context_contributions)
    assert "market_opportunity" in pooled

    # 2. Collective decision - vote on option
    options = [
        VotingOption("project_a", "AI Platform"),
        VotingOption("project_b", "Mobile App"),
    ]

    votes = [
        Vote("analyst", "project_a", weight=1.5),
        Vote("engineer", "project_a", weight=1.2),
        Vote("designer", "project_b", weight=1.0),
    ]

    decision = CollectiveDecision.make_decision(options, votes)
    assert decision.winning_option == "project_a"

    # 3. Wisdom of crowds - estimate timeline
    estimates = [
        AgentEstimate("analyst", 90, confidence=0.8),
        AgentEstimate("engineer", 120, confidence=0.9),
        AgentEstimate("designer", 100, confidence=0.7),
    ]

    timeline = WisdomOfCrowds.aggregate_estimates(estimates)
    assert 90 <= timeline["aggregate"] <= 120


def test_emergence_metrics_calculation():
    """Test emergence metrics in collective decision"""
    options = [
        VotingOption("a", "A"),
        VotingOption("b", "B"),
        VotingOption("c", "C"),
    ]

    # Diverse votes (high diversity)
    votes = [
        Vote("agent_1", "a"),
        Vote("agent_2", "b"),
        Vote("agent_3", "c"),
    ]

    result = CollectiveDecision.make_decision(options, votes)

    # Should have high diversity (3 different options)
    assert result.emergence_metrics.diversity_index > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
