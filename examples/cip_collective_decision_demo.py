"""
🐝 Collective Intelligence Protocol (CIP) - Swarm Decision Demo
================================================================

Demonstrates collective decision-making using swarm intelligence.

This example shows:
1. Knowledge pooling from multiple agents
2. Collective decision-making with quadratic voting
3. Wisdom of crowds estimation
4. Consensus building
5. Emergence metrics analysis

Scenario: A team of agents deciding on strategic initiatives for 2026.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.superstandard.protocols.cip_v1 import (
    SwarmContext, VotingOption, Vote, AgentEstimate,
    KnowledgePool, CollectiveDecision, WisdomOfCrowds, ConsensusBuilder,
    PoolingStrategy, DecisionMethod, AggregationMethod,
)


def print_header(title: str):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def demo_knowledge_pooling():
    """Demonstrate knowledge pooling from multiple agents"""
    print_header("1. KNOWLEDGE POOLING - Gathering Strategic Intelligence")

    print("Scenario: Agents contribute market intelligence for decision-making\n")

    # Agents contribute knowledge with confidence levels
    contributions = [
        {
            "agent_id": "market_analyst",
            "confidence": 0.9,
            "knowledge": {
                "market_growth_rate": 0.15,
                "competition_level": "high",
                "customer_demand": 0.85,
                "market_saturation": 0.4,
            },
        },
        {
            "agent_id": "financial_analyst",
            "confidence": 0.85,
            "knowledge": {
                "market_growth_rate": 0.12,
                "roi_potential": 2.3,
                "budget_available": 5000000,
                "market_saturation": 0.35,
            },
        },
        {
            "agent_id": "tech_analyst",
            "confidence": 0.8,
            "knowledge": {
                "market_growth_rate": 0.18,
                "technical_feasibility": "high",
                "implementation_time": 180,
                "competition_level": "medium",
            },
        },
    ]

    # Display individual contributions
    print("Agent Contributions:")
    for contrib in contributions:
        print(f"\n  {contrib['agent_id']} (confidence: {contrib['confidence']}):")
        for key, value in contrib["knowledge"].items():
            print(f"    • {key}: {value}")

    # Pool knowledge using weighted merge
    pooled = KnowledgePool.pool_knowledge(
        contributions,
        strategy=PoolingStrategy.WEIGHTED_MERGE,
        confidence_threshold=0.7,
    )

    print(f"\n\nPooled Knowledge (Weighted by Confidence):")
    for key, value in pooled.items():
        print(f"  • {key}: {value}")

    print(f"\n✓ Knowledge pooling complete - {len(pooled)} facts aggregated")

    return pooled


def demo_collective_decision():
    """Demonstrate collective decision-making"""
    print_header("2. COLLECTIVE DECISION - Strategic Initiative Selection")

    print("Scenario: 15 agents vote on which initiative to prioritize in 2026\n")

    # Define strategic options
    options = [
        VotingOption(
            option_id="ai_transformation",
            description="Invest in AI and automation across all departments",
            metadata={
                "estimated_cost": 3000000,
                "expected_roi": 2.5,
                "time_to_value": 12,
                "risk_level": "medium",
            },
        ),
        VotingOption(
            option_id="market_expansion",
            description="Enter new geographic markets (Asia-Pacific)",
            metadata={
                "estimated_cost": 2000000,
                "expected_roi": 1.8,
                "time_to_value": 18,
                "risk_level": "high",
            },
        ),
        VotingOption(
            option_id="product_innovation",
            description="Develop next-generation product line",
            metadata={
                "estimated_cost": 2500000,
                "expected_roi": 2.2,
                "time_to_value": 15,
                "risk_level": "medium",
            },
        ),
    ]

    print("Available Options:")
    for i, option in enumerate(options, 1):
        print(f"\n  {i}. {option.description}")
        print(f"     Cost: ${option.metadata['estimated_cost']:,}")
        print(f"     Expected ROI: {option.metadata['expected_roi']}x")
        print(f"     Time to Value: {option.metadata['time_to_value']} months")
        print(f"     Risk: {option.metadata['risk_level']}")

    # Agents vote with expertise-based weights
    # Using quadratic voting to allow preference intensity
    votes = [
        # Strategic team (high weight)
        Vote("strategic_lead", "ai_transformation", weight=9.0, confidence=0.95),
        Vote("strategy_analyst_1", "ai_transformation", weight=4.0, confidence=0.85),
        Vote("strategy_analyst_2", "product_innovation", weight=4.0, confidence=0.80),

        # Financial team (high weight)
        Vote("cfo", "ai_transformation", weight=9.0, confidence=0.90),
        Vote("financial_analyst_1", "ai_transformation", weight=4.0, confidence=0.85),

        # Technical team (medium weight)
        Vote("cto", "ai_transformation", weight=4.0, confidence=0.88),
        Vote("tech_lead_1", "product_innovation", weight=4.0, confidence=0.82),
        Vote("tech_lead_2", "ai_transformation", weight=1.0, confidence=0.75),

        # Marketing team (medium weight)
        Vote("cmo", "market_expansion", weight=4.0, confidence=0.87),
        Vote("marketing_lead", "market_expansion", weight=4.0, confidence=0.83),
        Vote("growth_manager", "product_innovation", weight=1.0, confidence=0.78),

        # Operations team (lower weight)
        Vote("ops_manager_1", "ai_transformation", weight=1.0, confidence=0.75),
        Vote("ops_manager_2", "product_innovation", weight=1.0, confidence=0.70),

        # Product team
        Vote("product_lead", "product_innovation", weight=4.0, confidence=0.85),
        Vote("product_manager", "ai_transformation", weight=1.0, confidence=0.72),
    ]

    print(f"\n\nVoting Configuration:")
    print(f"  Method: Quadratic Voting (cost = votes²)")
    print(f"  Participating Agents: {len(votes)}")
    print(f"  Weights: Based on expertise and role")

    # Create swarm context
    swarm_context = SwarmContext(
        swarm_id="strategic_swarm_2026",
        swarm_size=15,
        topology="fully_connected",
        coordination_pattern="decentralized",
    )

    # Make collective decision
    result = CollectiveDecision.make_decision(
        options,
        votes,
        method=DecisionMethod.QUADRATIC_VOTING,
        quorum_required=0.0,
    )

    print(f"\n\nVoting Results:")
    print(f"  Winner: {result.winning_option}")
    print(f"  Consensus Level: {result.consensus_level:.1%}")
    print(f"  Total Votes Cast: {result.total_votes:.1f}")

    print(f"\n  Votes by Option:")
    for option_id, vote_count in sorted(
        result.votes_by_option.items(), key=lambda x: x[1], reverse=True
    ):
        option = next(o for o in options if o.option_id == option_id)
        percentage = (vote_count / result.total_votes * 100) if result.total_votes > 0 else 0
        print(f"    • {option.description[:50]}: {vote_count:.1f} ({percentage:.1f}%)")

    # Emergence metrics
    if result.emergence_metrics:
        print(f"\n  Emergence Metrics:")
        print(f"    • Diversity Index: {result.emergence_metrics.diversity_index:.3f}")
        print(f"    • Coherence Score: {result.emergence_metrics.coherence_score:.3f}")
        print(f"    • Robustness: {result.emergence_metrics.robustness:.3f}")

    print(f"\n✓ Decision made: {result.winning_option}")

    return result


def demo_wisdom_of_crowds():
    """Demonstrate wisdom of crowds estimation"""
    print_header("3. WISDOM OF CROWDS - Revenue Forecasting")

    print("Scenario: Estimating Q1 2026 revenue using collective intelligence\n")

    # Individual agent estimates
    estimates = [
        AgentEstimate(
            "financial_forecast_model",
            15200000,
            confidence=0.85,
            reasoning="Time series analysis of historical trends",
        ),
        AgentEstimate(
            "sales_pipeline_agent",
            16800000,
            confidence=0.90,
            reasoning="Current pipeline value + conversion rates",
        ),
        AgentEstimate(
            "market_analyst_agent",
            14500000,
            confidence=0.75,
            reasoning="Market conditions and competitive landscape",
        ),
        AgentEstimate(
            "operations_agent",
            15800000,
            confidence=0.80,
            reasoning="Capacity constraints and operational projections",
        ),
        AgentEstimate(
            "customer_success_agent",
            16200000,
            confidence=0.82,
            reasoning="Retention rates and upsell potential",
        ),
        AgentEstimate(
            "strategic_planning_agent",
            15500000,
            confidence=0.88,
            reasoning="Strategic initiatives impact analysis",
        ),
    ]

    print("Individual Estimates:")
    for est in estimates:
        print(f"\n  {est.agent_id}:")
        print(f"    Estimate: ${est.estimate:,}")
        print(f"    Confidence: {est.confidence:.0%}")
        print(f"    Reasoning: {est.reasoning}")

    # Aggregate using confidence-weighted method
    result = WisdomOfCrowds.aggregate_estimates(
        estimates,
        method=AggregationMethod.CONFIDENCE_WEIGHTED,
        outlier_threshold=2.0,
    )

    print(f"\n\nAggregated Forecast:")
    print(f"  Collective Estimate: ${result['aggregate']:,.0f}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Agreement Level: {result['agreement']:.1%}")
    print(f"  Standard Deviation: ${result['std_dev']:,.0f}")
    print(f"  Contributing Agents: {result['count']}")

    # Compare to simple average
    simple_avg = sum(e.estimate for e in estimates) / len(estimates)
    print(f"\n  Simple Average: ${simple_avg:,.0f}")
    print(f"  Confidence-Weighted: ${result['aggregate']:,.0f}")
    print(f"  Difference: ${abs(result['aggregate'] - simple_avg):,.0f}")

    print(f"\n✓ Crowd wisdom: ${result['aggregate']:,.0f} (high confidence)")

    return result


def demo_consensus_building():
    """Demonstrate consensus building"""
    print_header("4. CONSENSUS BUILDING - Timeline Estimation")

    print("Scenario: Building consensus on project timeline\n")

    # Initial diverse estimates
    initial_estimates = [
        AgentEstimate("optimistic_agent", 90, confidence=0.7),
        AgentEstimate("realistic_agent", 120, confidence=0.85),
        AgentEstimate("conservative_agent", 150, confidence=0.8),
        AgentEstimate("experienced_agent", 135, confidence=0.9),
        AgentEstimate("technical_agent", 110, confidence=0.75),
    ]

    print("Initial Estimates (days):")
    for est in initial_estimates:
        print(f"  • {est.agent_id}: {est.estimate} days (confidence: {est.confidence:.0%})")

    # Build consensus
    result = ConsensusBuilder.build_consensus(
        initial_estimates,
        max_iterations=10,
        convergence_threshold=0.05,  # 5% coefficient of variation
        method="delphi_method",
    )

    print(f"\n\nConsensus Process:")
    print(f"  Method: Delphi Method (iterative refinement)")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Converged: {'Yes' if result['converged'] else 'No'}")
    print(f"  Final CV: {result['final_cv']:.3f}")

    if result['history']:
        print(f"\n  Convergence History:")
        print(f"    {'Iteration':<12} {'Mean':<15} {'Std Dev':<15} {'CV':<10}")
        print(f"    {'-'*50}")
        for h in result['history'][:5]:  # Show first 5
            print(
                f"    {h['iteration']:<12} "
                f"{h['mean']:<15.1f} "
                f"{h['std_dev']:<15.1f} "
                f"{h['cv']:<10.3f}"
            )
        if len(result['history']) > 5:
            print(f"    ...")
            h = result['history'][-1]
            print(
                f"    {h['iteration']:<12} "
                f"{h['mean']:<15.1f} "
                f"{h['std_dev']:<15.1f} "
                f"{h['cv']:<10.3f}"
            )

    print(f"\n\nConsensus Result:")
    print(f"  Timeline: {result['consensus']:.0f} days")
    print(f"  Range: {min(e.estimate for e in initial_estimates):.0f} - "
          f"{max(e.estimate for e in initial_estimates):.0f} days")

    print(f"\n✓ Consensus reached: {result['consensus']:.0f} days")

    return result


def main():
    """Run collective intelligence demonstration"""
    print("\n" + "="*80)
    print("  🐝 COLLECTIVE INTELLIGENCE PROTOCOL (CIP) v1.0")
    print("  Swarm Decision-Making Demonstration")
    print("="*80)

    print("\n📋 Scenario: Strategic Planning for 2026")
    print("   A swarm of 15 agents collaborating to make strategic decisions")

    # 1. Knowledge pooling
    pooled_knowledge = demo_knowledge_pooling()

    # 2. Collective decision
    decision_result = demo_collective_decision()

    # 3. Wisdom of crowds
    revenue_forecast = demo_wisdom_of_crowds()

    # 4. Consensus building
    timeline_consensus = demo_consensus_building()

    # Summary
    print_header("SUMMARY - Collective Intelligence in Action")

    print("Key Results:\n")

    print(f"1. Knowledge Pooling:")
    print(f"   • Aggregated {len(pooled_knowledge)} strategic insights")
    print(f"   • Weighted by agent confidence and expertise")

    print(f"\n2. Strategic Decision:")
    print(f"   • Winner: {decision_result.winning_option}")
    print(f"   • Consensus: {decision_result.consensus_level:.1%}")
    print(f"   • Method: Quadratic Voting (preference intensity)")

    print(f"\n3. Revenue Forecast:")
    print(f"   • Collective Estimate: ${revenue_forecast['aggregate']:,.0f}")
    print(f"   • Confidence: {revenue_forecast['confidence']:.1%}")
    print(f"   • Agreement: {revenue_forecast['agreement']:.1%}")

    print(f"\n4. Timeline Consensus:")
    print(f"   • Agreed Timeline: {timeline_consensus['consensus']:.0f} days")
    print(f"   • Iterations: {timeline_consensus['iterations']}")
    print(f"   • Converged: {'Yes' if timeline_consensus['converged'] else 'No'}")

    print(f"\n\n{'='*80}")
    print("✅ COLLECTIVE INTELLIGENCE DEMONSTRATION COMPLETE")
    print("="*80)

    print("\nKey Insights:")
    print("  • Swarm intelligence produces more robust decisions than individuals")
    print("  • Quadratic voting captures preference intensity, not just choices")
    print("  • Confidence weighting improves accuracy of crowd wisdom")
    print("  • Consensus building converges diverse opinions iteratively")
    print("  • Emergence metrics reveal collective behavior patterns")

    print("\nApplications:")
    print("  ✓ Strategic planning and decision-making")
    print("  ✓ Forecasting and estimation")
    print("  ✓ Resource allocation")
    print("  ✓ Risk assessment")
    print("  ✓ Knowledge aggregation")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
