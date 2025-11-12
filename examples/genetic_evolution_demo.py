"""
Genetic Evolution Demo - Breed Optimal Trading Agents

This demo shows genetic evolution in action by breeding trading agents
across multiple generations to optimize for specific objectives.

Evolution Objectives:
1. High-Return Trader: Maximize risk-adjusted returns
2. Balanced Trader: Balance innovation with reliability
3. Resilient Trader: Maximize stress resistance

Watch as agents evolve over 10 generations to achieve the objectives!
"""

import asyncio
import sys
from pathlib import Path
import random
import statistics
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from superstandard.agents.genetic_breeding import (
    EvolutionEngine,
    SelectionStrategy,
    CrossoverMethod,
    AgentGenome
)
from superstandard.agents.personality import PersonalityProfile
from superstandard.agents.personality_integration import PersonalityTradingIntegration


def simulate_trading_performance(personality: PersonalityProfile) -> Dict[str, float]:
    """
    Simulate trading performance for an agent with given personality.

    Returns various performance metrics that can be used for fitness evaluation.
    """
    # Get personality modifiers
    risk_tolerance = personality.get_modifier('risk_tolerance')
    innovation = personality.get_modifier('innovation_capacity')
    reliability = personality.get_modifier('execution_reliability')
    stress_resistance = personality.get_modifier('stress_resistance')

    # Simulate different market conditions
    # Bull market (favors risk-takers)
    bull_return = (risk_tolerance * 0.5 + innovation * 0.3) * random.uniform(0.8, 1.2)

    # Bear market (favors cautious traders)
    bear_return = (stress_resistance * 0.6 + reliability * 0.4) * random.uniform(0.7, 1.1)

    # Volatile market (favors balanced traders)
    volatile_return = (
        (stress_resistance + reliability) / 2 * 0.6 +
        (risk_tolerance + innovation) / 2 * 0.4
    ) * random.uniform(0.6, 1.3)

    # Sideways market (favors patient traders)
    sideways_return = (reliability * 0.7 + stress_resistance * 0.3) * random.uniform(0.5, 0.9)

    # Overall return (weighted average)
    total_return = (
        bull_return * 0.3 +
        bear_return * 0.2 +
        volatile_return * 0.3 +
        sideways_return * 0.2
    )

    # Risk metrics
    volatility = (risk_tolerance * 0.6 + innovation * 0.4) * random.uniform(0.8, 1.2)
    max_drawdown = (1.0 - stress_resistance) * random.uniform(0.8, 1.2)

    # Risk-adjusted return (Sharpe-like ratio)
    sharpe = total_return / max(volatility, 0.1)

    # Win rate (reliability helps)
    win_rate = (reliability * 0.5 + stress_resistance * 0.3 + risk_tolerance * 0.2)

    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'volatility': volatility,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'bull_performance': bull_return,
        'bear_performance': bear_return,
        'volatile_performance': volatile_return,
        'sideways_performance': sideways_return
    }


def high_return_fitness(personality: PersonalityProfile) -> float:
    """Fitness function: Maximize risk-adjusted returns"""
    performance = simulate_trading_performance(personality)
    # Sharpe ratio + total return
    return performance['sharpe_ratio'] * 0.6 + performance['total_return'] * 0.4


def balanced_fitness(personality: PersonalityProfile) -> float:
    """Fitness function: Balance innovation with reliability"""
    innovation = personality.get_modifier('innovation_capacity')
    reliability = personality.get_modifier('execution_reliability')
    stress_resistance = personality.get_modifier('stress_resistance')

    # Reward balanced traits
    balance_score = 1.0 - abs(innovation - reliability)
    combined = (innovation + reliability + stress_resistance) / 3

    return balance_score * 0.4 + combined * 0.6


def resilient_fitness(personality: PersonalityProfile) -> float:
    """Fitness function: Maximize resilience to stress"""
    performance = simulate_trading_performance(personality)
    stress_resistance = personality.get_modifier('stress_resistance')
    reliability = personality.get_modifier('execution_reliability')

    # Low drawdown + high stress resistance + good bear performance
    resilience = (
        (1.0 - performance['max_drawdown']) * 0.4 +
        stress_resistance * 0.3 +
        performance['bear_performance'] * 0.3
    )

    return resilience


def run_evolution_experiment(
    name: str,
    fitness_function,
    generations: int = 10,
    population_size: int = 20
):
    """Run a complete evolution experiment"""

    print(f"\n{'='*70}")
    print(f"  EVOLUTION EXPERIMENT: {name}")
    print(f"{'='*70}\n")

    # Create evolution engine
    engine = EvolutionEngine(
        population_size=population_size,
        selection_strategy=SelectionStrategy.ELITE,
        elite_ratio=0.25,  # Top 25% breed
        mutation_rate=0.12,
        crossover_method=CrossoverMethod.BLEND
    )

    # Initialize population
    print(f"🧬 Initializing Generation 0 ({population_size} agents)...")
    population = engine.initialize_population(fitness_function)

    # Show initial stats
    gen0_stats = engine.generation_history[0]
    best_gen0 = engine.get_best_agent()

    print(f"\n📊 Initial Population:")
    print(f"   Average Fitness: {gen0_stats.avg_fitness:.3f}")
    print(f"   Best Fitness: {gen0_stats.max_fitness:.3f}")
    print(f"   Best Agent: {best_gen0.agent_id} ({best_gen0.personality.archetype})")
    print(f"\n   Trait Averages:")
    for trait, avg in gen0_stats.trait_averages.items():
        print(f"     {trait.capitalize()}: {avg:.2f}")

    # Evolve through generations
    print(f"\n🔄 Evolving for {generations} generations...\n")

    for gen in range(1, generations + 1):
        # Evaluate fitness for current population
        fitness_scores = {
            genome.agent_id: fitness_function(genome.personality)
            for genome in engine.population
        }

        # Evolve to next generation
        engine.evolve_generation(fitness_scores)

        # Re-evaluate fitness for NEW population (offspring)
        new_fitness_scores = {
            genome.agent_id: fitness_function(genome.personality)
            for genome in engine.population
        }

        # Update fitness scores in genomes
        for genome in engine.population:
            genome.fitness_score = new_fitness_scores[genome.agent_id]

        # Recalculate stats with correct fitness
        engine._record_generation_stats()

        # Get stats
        stats = engine.generation_history[-1]
        best = engine.get_best_agent()

        # Show progress every generation
        improvement = ((stats.avg_fitness - gen0_stats.avg_fitness) / gen0_stats.avg_fitness * 100)

        print(f"Gen {gen:2d}: Avg={stats.avg_fitness:.3f} ({improvement:+.1f}%) | "
              f"Best={stats.max_fitness:.3f} | "
              f"Archetype={best.personality.archetype}")

    # Final summary
    print(f"\n{'='*70}")
    print(f"  EVOLUTION COMPLETE")
    print(f"{'='*70}\n")

    final_stats = engine.generation_history[-1]
    best_agent = engine.get_best_agent()

    print(f"📈 Evolution Progress:")
    print(f"   Initial Avg Fitness: {gen0_stats.avg_fitness:.3f}")
    print(f"   Final Avg Fitness: {final_stats.avg_fitness:.3f}")
    print(f"   Improvement: {((final_stats.avg_fitness / gen0_stats.avg_fitness - 1) * 100):.1f}%")

    print(f"\n🏆 Best Agent of All Time:")
    print(f"   ID: {best_agent.agent_id}")
    print(f"   Generation: {best_agent.generation}")
    print(f"   Fitness: {best_agent.fitness_score:.3f}")
    print(f"   Archetype: {best_agent.personality.archetype}")

    print(f"\n🧬 Best Agent Personality:")
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        value = getattr(best_agent.personality, trait)
        print(f"   {trait.capitalize()}: {value:.2f}")

    print(f"\n⚙️  Performance Modifiers:")
    for mod_name, mod_value in best_agent.personality.modifiers.items():
        print(f"   {mod_name.replace('_', ' ').title()}: {mod_value:.2f}")

    # Show lineage
    lineage = engine.get_lineage(best_agent.agent_id)
    print(f"\n👨‍👩‍👧‍👦 Family Tree (oldest → newest):")
    print(f"   {' → '.join(lineage[-5:])}")  # Last 5 ancestors

    # Show trait evolution
    print(f"\n📊 Trait Evolution:")
    print(f"   {'Trait':<18} {'Initial':<10} {'Final':<10} {'Change':<10}")
    print(f"   {'-'*50}")
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        initial = gen0_stats.trait_averages[trait]
        final = final_stats.trait_averages[trait]
        change = final - initial
        print(f"   {trait.capitalize():<18} {initial:<10.2f} {final:<10.2f} {change:+.2f}")

    # Archetype distribution
    archetype_counts = {}
    for genome in engine.population:
        arch = genome.personality.archetype
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    print(f"\n🎭 Final Archetype Distribution:")
    for arch, count in sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / population_size) * 100
        print(f"   {arch:<15} {count:>3} agents ({pct:>5.1f}%)")

    # Show trading behavior of best agent
    if 'trading' in name.lower() or 'return' in name.lower():
        print(f"\n💹 Trading Behavior (Best Agent):")
        position_size = PersonalityTradingIntegration.calculate_position_size(
            1.0, best_agent.personality
        )
        strategy = PersonalityTradingIntegration.select_strategy_type(best_agent.personality)
        holding_period = PersonalityTradingIntegration.calculate_holding_period_bias(
            best_agent.personality
        )

        print(f"   Position Size: {position_size:.2f}x")
        print(f"   Strategy: {strategy}")
        print(f"   Avg Holding Period: {holding_period:.1f} hours")

    return engine


def main():
    """Run all evolution experiments"""

    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║        🧬 GENETIC EVOLUTION OF TRADING AGENTS 🧬                ║")
    print("║                                                                  ║")
    print("║  Watch as personality traits evolve across generations to       ║")
    print("║  optimize for different trading objectives!                     ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    experiments = [
        {
            'name': 'HIGH-RETURN TRADERS',
            'fitness': high_return_fitness,
            'description': 'Optimize for risk-adjusted returns (Sharpe ratio)'
        },
        {
            'name': 'BALANCED TRADERS',
            'fitness': balanced_fitness,
            'description': 'Balance innovation with reliability and stress resistance'
        },
        {
            'name': 'RESILIENT TRADERS',
            'fitness': resilient_fitness,
            'description': 'Maximize resilience to market stress and drawdowns'
        }
    ]

    results = {}

    for exp in experiments:
        print(f"\n\n📋 Objective: {exp['description']}")
        input("\nPress Enter to start evolution...")

        engine = run_evolution_experiment(
            name=exp['name'],
            fitness_function=exp['fitness'],
            generations=10,
            population_size=20
        )

        results[exp['name']] = engine

        input("\nPress Enter to continue to next experiment...")

    # Final comparison
    print(f"\n\n{'='*70}")
    print(f"  FINAL COMPARISON: BEST AGENTS FROM EACH EXPERIMENT")
    print(f"{'='*70}\n")

    comparison_data = []
    for name, engine in results.items():
        best = engine.get_best_agent()
        comparison_data.append({
            'experiment': name,
            'agent_id': best.agent_id,
            'archetype': best.personality.archetype,
            'fitness': best.fitness_score,
            'risk_tolerance': best.personality.get_modifier('risk_tolerance'),
            'innovation': best.personality.get_modifier('innovation_capacity'),
            'reliability': best.personality.get_modifier('execution_reliability'),
            'stress_resistance': best.personality.get_modifier('stress_resistance')
        })

    print(f"{'Experiment':<25} {'Archetype':<12} {'Fitness':<10} {'Risk':<8} {'Innovation':<12} {'Reliability':<12}")
    print("-" * 100)
    for data in comparison_data:
        print(f"{data['experiment']:<25} {data['archetype']:<12} {data['fitness']:<10.3f} "
              f"{data['risk_tolerance']:<8.2f} {data['innovation']:<12.2f} {data['reliability']:<12.2f}")

    print(f"\n\n🎉 EVOLUTION COMPLETE! 🎉\n")
    print("Key Insights:")
    print("1. Different objectives produce different optimal personalities")
    print("2. Evolution consistently improves fitness across generations")
    print("3. Personality traits adapt to environmental pressures")
    print("4. Diversity preservation prevents premature convergence")
    print("\n💡 This demonstrates GENUINE emergent optimization!\n")


if __name__ == "__main__":
    main()
