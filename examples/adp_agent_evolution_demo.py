"""
🧬 Agent DNA Protocol (ADP) - Agent Evolution Demo
===================================================

Demonstrates genetic evolution of agents over multiple generations.

This example shows:
1. Creating an initial agent genome
2. Defining a fitness function
3. Running evolution for 10 generations
4. Tracking fitness improvements
5. Analyzing the evolved agent

The agent evolves its learning_rate and temperature parameters to maximize
performance on a simulated task.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.superstandard.protocols.adp_v1 import (
    Gene, Chromosome, AgentGenome,
    GeneType, ChromosomeType, SelectionMethod,
    EvolutionSimulator,
)
import uuid


def create_initial_genome() -> AgentGenome:
    """
    Create initial agent genome with performance parameters.

    This genome contains genes for:
    - learning_rate: How quickly the agent learns
    - temperature: Exploration vs exploitation
    - batch_size: Processing batch size
    - risk_tolerance: Behavioral trait
    """
    # Performance chromosome
    perf_genes = [
        Gene(
            gene_id="learning_rate",
            gene_type=GeneType.NUMERIC.value,
            allele=0.01,  # Start with moderate learning rate
            range_min=0.0001,
            range_max=0.1,
            mutation_probability=0.1,
        ),
        Gene(
            gene_id="temperature",
            gene_type=GeneType.NUMERIC.value,
            allele=1.0,  # Start with balanced exploration
            range_min=0.1,
            range_max=2.0,
            mutation_probability=0.08,
        ),
        Gene(
            gene_id="batch_size",
            gene_type=GeneType.CATEGORICAL.value,
            allele="medium",
            allowed_values=["small", "medium", "large"],
            mutation_probability=0.05,
        ),
    ]

    perf_chromosome = Chromosome(
        chromosome_id="chr_performance_001",
        chromosome_type=ChromosomeType.PERFORMANCE.value,
        genes=perf_genes,
        expression_level=1.0,
    )

    # Behavioral chromosome
    behavior_genes = [
        Gene(
            gene_id="risk_tolerance",
            gene_type=GeneType.NUMERIC.value,
            allele=0.5,
            range_min=0.0,
            range_max=1.0,
            mutation_probability=0.05,
        ),
        Gene(
            gene_id="cooperation",
            gene_type=GeneType.NUMERIC.value,
            allele=0.7,
            range_min=0.0,
            range_max=1.0,
            mutation_probability=0.05,
        ),
    ]

    behavior_chromosome = Chromosome(
        chromosome_id="chr_behavioral_001",
        chromosome_type=ChromosomeType.BEHAVIORAL.value,
        genes=behavior_genes,
        expression_level=0.95,
    )

    # Create genome
    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        agent_id="evolving_agent_001",
        generation=0,
        chromosomes=[perf_chromosome, behavior_chromosome],
        fitness_score=0.0,
    )

    return genome


def fitness_function(genome: AgentGenome) -> float:
    """
    Evaluate agent fitness based on parameter optimization.

    Fitness criteria:
    1. Learning rate should be around 0.001 (optimal for this task)
    2. Temperature should be around 0.7 (balanced)
    3. Batch size = "medium" is optimal
    4. Risk tolerance around 0.6 is ideal

    Returns fitness score 0.0 to 1.0
    """
    fitness = 0.0
    total_weight = 0.0

    # Get genes
    lr_result = genome.get_gene("learning_rate")
    temp_result = genome.get_gene("temperature")
    batch_result = genome.get_gene("batch_size")
    risk_result = genome.get_gene("risk_tolerance")

    # Evaluate learning rate (target: 0.001)
    if lr_result:
        _, lr_gene = lr_result
        lr = lr_gene.allele
        # Gaussian fitness around 0.001
        lr_fitness = max(0, 1.0 - abs(lr - 0.001) / 0.01)
        fitness += lr_fitness * 3.0  # Weight: 3.0
        total_weight += 3.0

    # Evaluate temperature (target: 0.7)
    if temp_result:
        _, temp_gene = temp_result
        temp = temp_gene.allele
        temp_fitness = max(0, 1.0 - abs(temp - 0.7) / 0.5)
        fitness += temp_fitness * 2.0  # Weight: 2.0
        total_weight += 2.0

    # Evaluate batch size (target: "medium")
    if batch_result:
        _, batch_gene = batch_result
        if batch_gene.allele == "medium":
            fitness += 1.5  # Weight: 1.5
        elif batch_gene.allele == "small":
            fitness += 0.75
        total_weight += 1.5

    # Evaluate risk tolerance (target: 0.6)
    if risk_result:
        _, risk_gene = risk_result
        risk = risk_gene.allele
        risk_fitness = max(0, 1.0 - abs(risk - 0.6) / 0.4)
        fitness += risk_fitness * 1.0  # Weight: 1.0
        total_weight += 1.0

    return fitness / total_weight if total_weight > 0 else 0.0


def print_genome_summary(genome: AgentGenome, generation: int):
    """Print summary of genome parameters"""
    print(f"\n{'='*70}")
    print(f"Generation {generation} - Best Agent")
    print(f"{'='*70}")
    print(f"Genome ID: {genome.genome_id[:16]}...")
    print(f"Fitness Score: {genome.fitness_score:.4f}")
    print(f"\nPerformance Parameters:")

    lr_result = genome.get_gene("learning_rate")
    if lr_result:
        _, gene = lr_result
        print(f"  Learning Rate: {gene.allele:.6f}")

    temp_result = genome.get_gene("temperature")
    if temp_result:
        _, gene = temp_result
        print(f"  Temperature: {gene.allele:.4f}")

    batch_result = genome.get_gene("batch_size")
    if batch_result:
        _, gene = batch_result
        print(f"  Batch Size: {gene.allele}")

    print(f"\nBehavioral Traits:")

    risk_result = genome.get_gene("risk_tolerance")
    if risk_result:
        _, gene = risk_result
        print(f"  Risk Tolerance: {gene.allele:.4f}")

    coop_result = genome.get_gene("cooperation")
    if coop_result:
        _, gene = coop_result
        print(f"  Cooperation: {gene.allele:.4f}")

    if genome.phenotype:
        print(f"\nExpressed Traits:")
        if genome.phenotype.performance_traits:
            for trait, value in genome.phenotype.performance_traits.items():
                print(f"  {trait}: {value:.4f}")

    print(f"{'='*70}")


def main():
    """Run agent evolution demonstration"""
    print("\n🧬 AGENT DNA PROTOCOL (ADP) v1.0 - Evolution Demo")
    print("="*70)
    print("\nObjective: Evolve an agent to optimize its parameters")
    print("Evolving parameters: learning_rate, temperature, batch_size, risk_tolerance")
    print("\nStarting evolution...\n")

    # Create initial genome
    initial_genome = create_initial_genome()

    print("Initial Agent:")
    print_genome_summary(initial_genome, 0)

    # Initialize evolution simulator
    simulator = EvolutionSimulator(
        population_size=20,
        mutation_rate=0.05,
        crossover_rate=0.7,
        elitism_count=2,  # Keep 2 best agents each generation
    )

    # Initialize population
    simulator.initialize_population(initial_genome)

    print(f"\n\nEvolution Parameters:")
    print(f"  Population Size: {simulator.population_size}")
    print(f"  Mutation Rate: {simulator.mutation_rate}")
    print(f"  Crossover Rate: {simulator.crossover_rate}")
    print(f"  Elitism Count: {simulator.elitism_count}")
    print(f"  Generations: 10")

    # Run evolution
    print(f"\n\n{'Generation':<12} {'Avg Fitness':<15} {'Best Fitness':<15} {'Improvement'}")
    print("-" * 70)

    previous_best = 0.0

    all_stats = simulator.run(
        generations=10,
        fitness_function=fitness_function,
        selection_method=SelectionMethod.TOURNAMENT,
    )

    # Print generation statistics
    for stats in all_stats:
        improvement = stats['best_fitness'] - previous_best
        improvement_str = f"+{improvement:.4f}" if improvement > 0 else f"{improvement:.4f}"

        print(
            f"{stats['generation']:<12} "
            f"{stats['avg_fitness']:<15.4f} "
            f"{stats['best_fitness']:<15.4f} "
            f"{improvement_str}"
        )

        previous_best = stats['best_fitness']

    # Final results
    print(f"\n\n{'='*70}")
    print("EVOLUTION COMPLETE!")
    print(f"{'='*70}")

    final_best = simulator.best_genome

    if final_best:
        print_genome_summary(final_best, final_best.generation)

        # Compare to initial
        initial_fitness = fitness_function(initial_genome)
        final_fitness = final_best.fitness_score
        improvement = final_fitness - initial_fitness

        print(f"\n\nEvolution Results:")
        print(f"  Initial Fitness: {initial_fitness:.4f}")
        print(f"  Final Fitness: {final_fitness:.4f}")
        print(f"  Improvement: {improvement:.4f} ({improvement/initial_fitness*100:.1f}%)")
        print(f"  Generations: {final_best.generation}")

        # Parameter comparison
        print(f"\n\nParameter Evolution:")
        print(f"{'Parameter':<20} {'Initial':<15} {'Final':<15} {'Optimal':<15}")
        print("-" * 70)

        # Learning rate
        init_lr = initial_genome.get_gene("learning_rate")[1].allele
        final_lr = final_best.get_gene("learning_rate")[1].allele
        print(f"{'learning_rate':<20} {init_lr:<15.6f} {final_lr:<15.6f} {'0.001000':<15}")

        # Temperature
        init_temp = initial_genome.get_gene("temperature")[1].allele
        final_temp = final_best.get_gene("temperature")[1].allele
        print(f"{'temperature':<20} {init_temp:<15.4f} {final_temp:<15.4f} {'0.7000':<15}")

        # Batch size
        init_batch = initial_genome.get_gene("batch_size")[1].allele
        final_batch = final_best.get_gene("batch_size")[1].allele
        print(f"{'batch_size':<20} {init_batch:<15} {final_batch:<15} {'medium':<15}")

        # Risk tolerance
        init_risk = initial_genome.get_gene("risk_tolerance")[1].allele
        final_risk = final_best.get_gene("risk_tolerance")[1].allele
        print(f"{'risk_tolerance':<20} {init_risk:<15.4f} {final_risk:<15.4f} {'0.6000':<15}")

    print(f"\n\n✅ Evolution demonstration complete!")
    print(f"\nKey Insights:")
    print(f"  • Genetic algorithms successfully optimized agent parameters")
    print(f"  • Tournament selection preserved diversity while improving fitness")
    print(f"  • Elitism ensured best agents weren't lost")
    print(f"  • Parameters converged toward optimal values")


if __name__ == "__main__":
    main()
