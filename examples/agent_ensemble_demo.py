"""
Agent Ensemble Demo - Production Deployment of Evolved Agents

This demonstrates how to actually DEPLOY evolved agents in a production system
using the ensemble pattern.

Shows:
1. Evolving specialists for different market regimes
2. Creating and managing an ensemble
3. Routing decisions to appropriate specialists
4. Performance tracking and analytics
5. Hot-swapping underperforming agents

This is the PRODUCTION DEPLOYMENT pattern!

Run: python examples/agent_ensemble_demo.py
"""

import sys
sys.path.insert(0, 'src')

from superstandard.agents.personality import PersonalityProfile
from superstandard.agents.genetic_breeding import (
    EvolutionEngine,
    AgentGenome,
    CrossoverMethod,
    SelectionStrategy
)
from superstandard.agents.agent_ensemble import (
    AgentEnsemble,
    AgentSpecialist,
    SpecialistType,
    SimpleRegimeDetector
)
from superstandard.trading.market_simulation import (
    MarketSimulator,
    MarketRegime,
    MarketBar,
    AgentBacktester
)
from typing import List, Callable


# ============================================================================
# Strategy Creation from Personality
# ============================================================================

def create_strategy(personality: PersonalityProfile) -> Callable:
    """Create trading strategy from personality"""
    def strategy(current_bar: MarketBar, history: List[MarketBar]) -> str:
        if len(history) < 20:
            return 'hold'

        prices = [bar.close for bar in history[-20:]] + [current_bar.close]
        sma = sum(prices) / len(prices)

        if current_bar.close > sma * 1.01:
            return 'buy'
        elif current_bar.close < sma * 0.99:
            return 'sell'
        return 'hold'

    return strategy


# ============================================================================
# Evolve Specialists for Different Regimes
# ============================================================================

def evolve_specialist(regime: MarketRegime, objective_name: str) -> AgentGenome:
    """
    Evolve specialist agent for specific market regime.

    Returns best agent from evolution run.
    """
    print(f"\n{'='*80}")
    print(f"EVOLVING {objective_name.upper()}")
    print(f"{'='*80}\n")

    # Generate market data for this regime
    simulator = MarketSimulator(initial_price=100.0, seed=42)
    market_data = simulator.generate_bars(100, regime=regime)

    print(f"📊 Generated {regime.value} market: {len(market_data)} bars")

    # Fitness function
    def fitness_func(personality: PersonalityProfile) -> float:
        personality._calculate_modifiers()
        strategy = create_strategy(personality)

        backtester = AgentBacktester()
        metrics = backtester.backtest(market_data, strategy, 0.7)

        return metrics.get_fitness_score()

    # Initialize population
    print(f"🧬 Initializing population...")
    genomes = []

    for i in range(15):  # Smaller population for speed
        personality = PersonalityProfile.random()
        genome = AgentGenome(
            agent_id=f"{objective_name}_agent_{i}",
            generation=0,
            personality=personality,
            parents=[],
            fitness_score=fitness_func(personality),
            mutations=[]
        )
        genomes.append(genome)

    initial_avg = sum(g.fitness_score for g in genomes) / len(genomes)
    print(f"   Initial avg fitness: {initial_avg:.3f}")

    # Evolve
    engine = EvolutionEngine(
        population_size=15,
        selection_strategy=SelectionStrategy.ELITE,
        elite_ratio=0.30,
        mutation_rate=0.18,
        crossover_method=CrossoverMethod.BLEND
    )

    engine.population = genomes

    print(f"\n🚀 Evolving for 8 generations...\n")

    for gen in range(1, 9):
        engine.evolve_generation({g.agent_id: g.fitness_score for g in engine.population})

        for genome in engine.population:
            genome.fitness_score = fitness_func(genome.personality)

        engine._record_generation_stats()

        avg_fitness = sum(g.fitness_score for g in engine.population) / len(engine.population)
        improvement = ((avg_fitness - initial_avg) / initial_avg * 100) if initial_avg > 0 else 0

        print(f"Gen {gen}: avg={avg_fitness:.3f} improvement={improvement:+.1f}%")

    # Get best agent
    best_agent = max(engine.population, key=lambda g: g.fitness_score)

    print(f"\n🏆 Best {objective_name}:")
    print(f"   ID: {best_agent.agent_id}")
    print(f"   Generation: {best_agent.generation}")
    print(f"   Fitness: {best_agent.fitness_score:.3f}")
    print(f"   Personality: O={best_agent.personality.openness:.2f} "
          f"C={best_agent.personality.conscientiousness:.2f} "
          f"E={best_agent.personality.extraversion:.2f}")

    return best_agent


# ============================================================================
# Demo Scenarios
# ============================================================================

def demo_basic_ensemble():
    """Demo 1: Basic ensemble with routing"""
    print("\n" + "="*80)
    print("DEMO 1: BASIC ENSEMBLE WITH AUTOMATIC ROUTING")
    print("="*80)

    # Evolve specialists
    print("\n🧬 Evolving specialist agents for different market conditions...\n")

    bull_agent = evolve_specialist(MarketRegime.BULL, "bull_specialist")
    bear_agent = evolve_specialist(MarketRegime.BEAR, "bear_specialist")
    volatile_agent = evolve_specialist(MarketRegime.VOLATILE, "volatile_specialist")

    # Create ensemble
    print("\n" + "="*80)
    print("CREATING ENSEMBLE")
    print("="*80 + "\n")

    ensemble = AgentEnsemble(use_voting=False)  # Direct routing

    # Add specialists
    ensemble.add_specialist(bull_agent, SpecialistType.BULL_SPECIALIST, create_strategy(bull_agent.personality))
    ensemble.add_specialist(bear_agent, SpecialistType.BEAR_SPECIALIST, create_strategy(bear_agent.personality))
    ensemble.add_specialist(volatile_agent, SpecialistType.VOLATILE_SPECIALIST, create_strategy(volatile_agent.personality))

    print(f"\n✅ Ensemble created with {len(ensemble.specialists)} specialists")

    # Test routing across different markets
    print("\n" + "="*80)
    print("TESTING ROUTING ACROSS DIFFERENT MARKETS")
    print("="*80 + "\n")

    test_scenarios = [
        (MarketRegime.BULL, "Bull Market"),
        (MarketRegime.BEAR, "Bear Market"),
        (MarketRegime.VOLATILE, "Volatile Market"),
        (MarketRegime.SIDEWAYS, "Sideways Market")
    ]

    for regime, name in test_scenarios:
        print(f"📊 Testing {name}...")

        # Generate market
        simulator = MarketSimulator(initial_price=100.0)
        bars = simulator.generate_bars(30, regime=regime)

        # Get decision
        price_history = [bar.close for bar in bars]
        decision, metadata = ensemble.get_decision(bars[-1], price_history, bar_history=bars)

        print(f"   Detected regime: {metadata['regime']}")
        print(f"   Routed to: {metadata.get('specialist_used', 'N/A')}")
        print(f"   Decision: {decision}")
        print(f"   Confidence: {metadata.get('confidence', 0.0):.2%}\n")

    # Show ensemble statistics
    print("="*80)
    print("ENSEMBLE STATISTICS")
    print("="*80 + "\n")

    stats = ensemble.get_statistics()

    print(f"Total specialists: {stats['total_specialists']}")
    print(f"Total decisions made: {stats['total_decisions']}")
    print(f"Routing method: {stats['routing_method']}\n")

    print("Specialist usage distribution:")
    for specialist, count in stats.get('specialist_usage', {}).items():
        pct = (count / stats['total_decisions'] * 100) if stats['total_decisions'] > 0 else 0
        print(f"   {specialist}: {count} times ({pct:.1f}%)")

    print("\n✅ Basic ensemble demo complete!")


def demo_voting_ensemble():
    """Demo 2: Ensemble with weighted voting"""
    print("\n" + "="*80)
    print("DEMO 2: ENSEMBLE WITH WEIGHTED VOTING")
    print("="*80)

    print("\n🧬 Creating pre-trained specialists...\n")

    # Create simple specialists with different personalities
    specialists = []

    for i, (o, c, e) in enumerate([
        (0.8, 0.5, 0.7),  # Aggressive
        (0.4, 0.9, 0.4),  # Conservative
        (0.6, 0.7, 0.6),  # Balanced
    ]):
        personality = PersonalityProfile(
            openness=o,
            conscientiousness=c,
            extraversion=e,
            agreeableness=0.6,
            neuroticism=0.4
        )
        personality._calculate_modifiers()

        genome = AgentGenome(
            agent_id=f"voting_agent_{i}",
            generation=0,
            personality=personality,
            parents=[],
            fitness_score=0.6 + i * 0.1,  # Mock fitness
            mutations=[]
        )

        specialists.append(genome)

    # Create voting ensemble
    ensemble = AgentEnsemble(use_voting=True, voting_threshold=0.55)

    # Add specialists with different types (they'll all vote)
    specialist_types = [
        SpecialistType.BULL_SPECIALIST,
        SpecialistType.BEAR_SPECIALIST,
        SpecialistType.VOLATILE_SPECIALIST
    ]

    for i, genome in enumerate(specialists):
        ensemble.add_specialist(
            genome,
            specialist_types[i],
            create_strategy(genome.personality)
        )

    print(f"\n✅ Voting ensemble created with {len(ensemble.specialists)} voters")
    print(f"   Voting threshold: {ensemble.voting_threshold:.0%}\n")

    # Test voting
    simulator = MarketSimulator()
    bars = simulator.generate_bars(30, regime=MarketRegime.VOLATILE)
    price_history = [bar.close for bar in bars]

    decision, metadata = ensemble.get_decision(bars[-1], price_history, bar_history=bars)

    print(f"📊 Voting Result:")
    print(f"   Decision: {decision}")
    print(f"   Confidence: {metadata.get('confidence', 0.0):.2%}")
    print(f"   Total voters: {metadata.get('total_voters', 0)}")
    print(f"   Vote distribution: {metadata.get('vote_distribution', {})}\n")

    print("✅ Voting ensemble demo complete!")


def demo_hot_swapping():
    """Demo 3: Hot-swapping underperforming agents"""
    print("\n" + "="*80)
    print("DEMO 3: HOT-SWAPPING UNDERPERFORMING AGENTS")
    print("="*80)

    # Create ensemble with initial agent
    ensemble = AgentEnsemble()

    initial_personality = PersonalityProfile(
        openness=0.5, conscientiousness=0.5, extraversion=0.5,
        agreeableness=0.5, neuroticism=0.5
    )
    initial_personality._calculate_modifiers()

    initial_genome = AgentGenome(
        agent_id="initial_bull_specialist",
        generation=0,
        personality=initial_personality,
        parents=[],
        fitness_score=0.45,
        mutations=[]
    )

    print("\n📊 Initial specialist:")
    print(f"   ID: {initial_genome.agent_id}")
    print(f"   Fitness: {initial_genome.fitness_score:.3f}\n")

    ensemble.add_specialist(
        initial_genome,
        SpecialistType.BULL_SPECIALIST,
        create_strategy(initial_personality)
    )

    # Simulate some trades with poor performance
    print("⚠️  Simulating poor performance...")
    ensemble.update_performance(SpecialistType.BULL_SPECIALIST, {
        'profit': -100,
        'return': -0.05,
        'sharpe': -0.3,
        'max_drawdown': 0.15
    })

    specialist = ensemble.specialists[SpecialistType.BULL_SPECIALIST]
    print(f"   Performance score: {specialist.get_performance_score():.3f}")
    print(f"   Total return: {specialist.total_return*100:.2f}%\n")

    # Evolve replacement
    print("🧬 Evolving replacement agent...\n")
    improved_agent = evolve_specialist(MarketRegime.BULL, "improved_bull")

    # Hot-swap
    print("\n🔄 Performing hot-swap...\n")
    ensemble.hot_swap(
        SpecialistType.BULL_SPECIALIST,
        improved_agent,
        create_strategy(improved_agent.personality)
    )

    print("\n✅ Hot-swapping demo complete!")
    print("   This is how you continuously improve the ensemble in production!")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all ensemble demos"""
    print("\n" + "="*80)
    print("🎯 AGENT ENSEMBLE SYSTEM - PRODUCTION DEPLOYMENT DEMO")
    print("="*80)
    print("\nDemonstrates how to deploy evolved agents in production using")
    print("the ensemble pattern with automatic routing and performance tracking.")
    print()

    # Run demos
    demo_basic_ensemble()
    demo_voting_ensemble()
    demo_hot_swapping()

    # Final summary
    print("\n" + "="*80)
    print("✅ ALL ENSEMBLE DEMOS COMPLETE!")
    print("="*80)

    print("\n🌟 Key Takeaways:")
    print("   1. Evolve specialists for different market conditions")
    print("   2. Ensemble automatically routes to best specialist")
    print("   3. Weighted voting combines multiple agent opinions")
    print("   4. Performance tracking identifies underperformers")
    print("   5. Hot-swapping enables continuous improvement")

    print("\n🚀 Production Deployment Pattern:")
    print("   - Train/evolve specialists offline")
    print("   - Deploy as ensemble with routing")
    print("   - Monitor performance in production")
    print("   - Hot-swap underperformers with new agents")
    print("   - Continuous improvement without downtime!")

    print("\n💡 Business Value:")
    print("   - Robust multi-agent trading system")
    print("   - Adapts to changing market conditions")
    print("   - No single point of failure")
    print("   - Continuous optimization")
    print("   - Production-ready architecture")

    print()


if __name__ == "__main__":
    main()
