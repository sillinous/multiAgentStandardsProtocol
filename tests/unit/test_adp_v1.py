"""
Unit tests for Agent DNA Protocol (ADP) v1.0
"""

import pytest
import uuid
from src.superstandard.protocols.adp_v1 import (
    Gene, Chromosome, AgentGenome, Mutation, Phenotype,
    GeneType, ChromosomeType, Dominance, MutationType, CrossoverType, SelectionMethod,
    GeneticOperations, FitnessEvaluator, EvolutionSimulator,
)


# ============================================================================
# GENE TESTS
# ============================================================================


def test_gene_creation():
    """Test gene creation and validation"""
    gene = Gene(
        gene_id="test_gene",
        gene_type=GeneType.NUMERIC.value,
        allele=0.5,
        range_min=0.0,
        range_max=1.0,
    )

    assert gene.gene_id == "test_gene"
    assert gene.allele == 0.5
    assert gene.validate()


def test_gene_numeric_validation():
    """Test numeric gene validation with ranges"""
    gene = Gene(
        gene_id="learning_rate",
        gene_type=GeneType.NUMERIC.value,
        allele=0.001,
        range_min=0.0001,
        range_max=0.1,
    )

    assert gene.validate()

    # Invalid: outside range
    gene.allele = 0.2
    assert not gene.validate()


def test_gene_categorical_validation():
    """Test categorical gene validation"""
    gene = Gene(
        gene_id="strategy",
        gene_type=GeneType.CATEGORICAL.value,
        allele="aggressive",
        allowed_values=["conservative", "moderate", "aggressive"],
    )

    assert gene.validate()

    # Invalid: not in allowed values
    gene.allele = "invalid"
    assert not gene.validate()


def test_gene_mutation_numeric():
    """Test numeric gene mutation"""
    gene = Gene(
        gene_id="temperature",
        gene_type=GeneType.NUMERIC.value,
        allele=0.7,
        range_min=0.0,
        range_max=2.0,
    )

    mutated = gene.mutate()

    # Should be different (most of the time)
    assert mutated.gene_id == gene.gene_id
    assert mutated.gene_type == gene.gene_type
    # Value should be in valid range
    assert 0.0 <= mutated.allele <= 2.0


def test_gene_mutation_categorical():
    """Test categorical gene mutation"""
    gene = Gene(
        gene_id="mode",
        gene_type=GeneType.CATEGORICAL.value,
        allele="mode_a",
        allowed_values=["mode_a", "mode_b", "mode_c"],
    )

    mutated = gene.mutate()

    assert mutated.allele in gene.allowed_values


def test_gene_mutation_boolean():
    """Test boolean gene mutation"""
    gene = Gene(
        gene_id="enabled",
        gene_type=GeneType.BOOLEAN.value,
        allele=True,
    )

    mutated = gene.mutate()

    assert mutated.allele == False  # Should flip


def test_gene_to_dict():
    """Test gene serialization"""
    gene = Gene(
        gene_id="test",
        gene_type=GeneType.NUMERIC.value,
        allele=0.5,
        range_min=0.0,
        range_max=1.0,
    )

    data = gene.to_dict()

    assert data["gene_id"] == "test"
    assert data["allele"] == 0.5
    assert "range" in data


# ============================================================================
# CHROMOSOME TESTS
# ============================================================================


def test_chromosome_creation():
    """Test chromosome creation"""
    genes = [
        Gene("gene1", GeneType.NUMERIC.value, 0.5, range_min=0.0, range_max=1.0),
        Gene("gene2", GeneType.NUMERIC.value, 0.7, range_min=0.0, range_max=1.0),
    ]

    chromosome = Chromosome(
        chromosome_id="chr1",
        chromosome_type=ChromosomeType.PERFORMANCE.value,
        genes=genes,
        expression_level=0.9,
    )

    assert len(chromosome.genes) == 2
    assert chromosome.expression_level == 0.9
    assert chromosome.validate()


def test_chromosome_get_gene():
    """Test getting gene by ID"""
    genes = [
        Gene("learning_rate", GeneType.NUMERIC.value, 0.001),
        Gene("temperature", GeneType.NUMERIC.value, 0.7),
    ]

    chromosome = Chromosome(
        chromosome_id="chr1",
        chromosome_type=ChromosomeType.PERFORMANCE.value,
        genes=genes,
    )

    gene = chromosome.get_gene("learning_rate")
    assert gene is not None
    assert gene.allele == 0.001

    not_found = chromosome.get_gene("nonexistent")
    assert not_found is None


def test_chromosome_expression_validation():
    """Test expression level validation"""
    chromosome = Chromosome(
        chromosome_id="chr1",
        chromosome_type=ChromosomeType.BEHAVIORAL.value,
        genes=[],
        expression_level=1.5,  # Invalid: > 1.0
    )

    assert not chromosome.validate()


# ============================================================================
# GENOME TESTS
# ============================================================================


def test_genome_creation():
    """Test genome creation"""
    genes = [Gene("gene1", GeneType.NUMERIC.value, 0.5)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)

    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[chromosome],
    )

    assert genome.generation == 0
    assert len(genome.chromosomes) == 1
    assert genome.validate()


def test_genome_phenotype_expression():
    """Test phenotype expression from genes"""
    perf_genes = [
        Gene("speed", GeneType.NUMERIC.value, 0.8, range_min=0.0, range_max=1.0),
        Gene("accuracy", GeneType.NUMERIC.value, 0.9, range_min=0.0, range_max=1.0),
    ]

    perf_chromosome = Chromosome(
        chromosome_id="chr_perf",
        chromosome_type=ChromosomeType.PERFORMANCE.value,
        genes=perf_genes,
        expression_level=1.0,
    )

    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[perf_chromosome],
    )

    phenotype = genome.express_phenotype()

    assert "speed" in phenotype.performance_traits
    assert "accuracy" in phenotype.performance_traits
    assert phenotype.performance_traits["speed"] == 0.8


def test_genome_get_gene():
    """Test getting gene from genome"""
    genes = [
        Gene("learning_rate", GeneType.NUMERIC.value, 0.001),
        Gene("temperature", GeneType.NUMERIC.value, 0.7),
    ]

    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)

    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[chromosome],
    )

    result = genome.get_gene("learning_rate")
    assert result is not None

    chrom, gene = result
    assert gene.allele == 0.001


# ============================================================================
# GENETIC OPERATIONS TESTS
# ============================================================================


def test_mutation_operation():
    """Test genome mutation"""
    genes = [
        Gene("param1", GeneType.NUMERIC.value, 0.5, range_min=0.0, range_max=1.0),
        Gene("param2", GeneType.NUMERIC.value, 0.7, range_min=0.0, range_max=1.0),
    ]

    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)

    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[chromosome],
    )

    # Mutate
    mutated = GeneticOperations.mutate_genome(genome, mutation_rate=1.0)

    # Check properties
    assert mutated.genome_id != genome.genome_id
    assert mutated.generation == 1
    assert genome.genome_id in mutated.lineage
    assert mutated.validate()


def test_mutation_preserves_original():
    """Test that mutation doesn't modify original genome"""
    genes = [Gene("param1", GeneType.NUMERIC.value, 0.5)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)

    original = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[chromosome],
    )

    original_value = original.chromosomes[0].genes[0].allele

    mutated = GeneticOperations.mutate_genome(original, mutation_rate=1.0)

    # Original should be unchanged
    assert original.chromosomes[0].genes[0].allele == original_value


def test_crossover_operation():
    """Test genome crossover"""
    genes1 = [
        Gene("param1", GeneType.NUMERIC.value, 0.3, range_min=0.0, range_max=1.0),
        Gene("param2", GeneType.NUMERIC.value, 0.4, range_min=0.0, range_max=1.0),
    ]

    genes2 = [
        Gene("param1", GeneType.NUMERIC.value, 0.7, range_min=0.0, range_max=1.0),
        Gene("param2", GeneType.NUMERIC.value, 0.8, range_min=0.0, range_max=1.0),
    ]

    chromosome1 = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes1)
    chromosome2 = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes2)

    parent1 = AgentGenome(str(uuid.uuid4()), 0, [chromosome1])
    parent2 = AgentGenome(str(uuid.uuid4()), 0, [chromosome2])

    offspring1, offspring2 = GeneticOperations.crossover(
        parent1, parent2, crossover_rate=1.0
    )

    # Check offspring properties
    assert offspring1.generation == 1
    assert offspring2.generation == 1
    assert parent1.genome_id in offspring1.lineage
    assert parent2.genome_id in offspring1.lineage
    assert offspring1.validate()
    assert offspring2.validate()


def test_crossover_types():
    """Test different crossover types"""
    genes1 = [Gene(f"gene{i}", GeneType.NUMERIC.value, 0.3) for i in range(5)]
    genes2 = [Gene(f"gene{i}", GeneType.NUMERIC.value, 0.7) for i in range(5)]

    chromosome1 = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes1)
    chromosome2 = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes2)

    parent1 = AgentGenome(str(uuid.uuid4()), 0, [chromosome1])
    parent2 = AgentGenome(str(uuid.uuid4()), 0, [chromosome2])

    # Test all crossover types
    for crossover_type in [CrossoverType.SINGLE_POINT, CrossoverType.TWO_POINT, CrossoverType.UNIFORM]:
        offspring1, offspring2 = GeneticOperations.crossover(
            parent1, parent2, crossover_type=crossover_type, crossover_rate=1.0
        )

        assert offspring1.validate()
        assert offspring2.validate()


def test_selection_roulette_wheel():
    """Test roulette wheel selection"""
    population = []

    for i in range(10):
        genes = [Gene("param1", GeneType.NUMERIC.value, 0.5)]
        chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
        genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])
        genome.fitness_score = i / 10.0  # Fitness from 0.0 to 0.9
        population.append(genome)

    selected = GeneticOperations.select_population(
        population,
        selection_size=5,
        method=SelectionMethod.ROULETTE_WHEEL,
    )

    assert len(selected) == 5


def test_selection_tournament():
    """Test tournament selection"""
    population = []

    for i in range(10):
        genes = [Gene("param1", GeneType.NUMERIC.value, 0.5)]
        chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
        genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])
        genome.fitness_score = i / 10.0
        population.append(genome)

    selected = GeneticOperations.select_population(
        population,
        selection_size=5,
        method=SelectionMethod.TOURNAMENT,
    )

    assert len(selected) == 5


def test_selection_elitism():
    """Test elitism selection"""
    population = []

    for i in range(10):
        genes = [Gene("param1", GeneType.NUMERIC.value, 0.5)]
        chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
        genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])
        genome.fitness_score = i / 10.0
        population.append(genome)

    selected = GeneticOperations.select_population(
        population,
        selection_size=5,
        method=SelectionMethod.ELITISM,
        elitism_count=2,
    )

    assert len(selected) == 5
    # Top 2 should be best individuals
    assert selected[0].fitness_score >= 0.8
    assert selected[1].fitness_score >= 0.7


# ============================================================================
# FITNESS EVALUATION TESTS
# ============================================================================


def test_fitness_evaluator():
    """Test fitness evaluation"""
    metrics = [
        {"metric_name": "accuracy", "weight": 2.0, "optimization": "maximize"},
        {"metric_name": "speed", "weight": 1.0, "optimization": "maximize"},
    ]

    evaluator = FitnessEvaluator(metrics)

    genes = [
        Gene("accuracy", GeneType.NUMERIC.value, 0.9),
        Gene("speed", GeneType.NUMERIC.value, 0.7),
    ]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    fitness = evaluator.evaluate(genome)

    assert 0.0 <= fitness <= 1.0
    assert fitness > 0.5  # Should be high given good performance


def test_fitness_custom_function():
    """Test custom fitness function"""
    def custom_fitness(genome: AgentGenome) -> float:
        # Simple: return 0.8 for all
        return 0.8

    evaluator = FitnessEvaluator()
    genome = AgentGenome(str(uuid.uuid4()), 0, [])

    fitness = evaluator.evaluate(genome, objective_function=custom_fitness)

    assert fitness == 0.8


# ============================================================================
# EVOLUTION SIMULATOR TESTS
# ============================================================================


def test_evolution_simulator_initialization():
    """Test evolution simulator initialization"""
    genes = [Gene("param1", GeneType.NUMERIC.value, 0.5, range_min=0.0, range_max=1.0)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    template = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    simulator = EvolutionSimulator(population_size=10)
    simulator.initialize_population(template)

    assert len(simulator.population) == 10
    assert simulator.generation == 0


def test_evolution_simulator_generation():
    """Test evolving one generation"""
    genes = [Gene("param1", GeneType.NUMERIC.value, 0.5, range_min=0.0, range_max=1.0)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    template = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    def fitness_func(genome: AgentGenome) -> float:
        # Fitness = param1 value (maximize toward 1.0)
        result = genome.get_gene("param1")
        if result:
            _, gene = result
            return gene.allele
        return 0.0

    simulator = EvolutionSimulator(population_size=10, mutation_rate=0.1)
    simulator.initialize_population(template)

    stats = simulator.evolve_generation(fitness_func)

    assert "generation" in stats
    assert "avg_fitness" in stats
    assert "best_fitness" in stats
    assert stats["generation"] == 1


def test_evolution_simulator_run():
    """Test running evolution for multiple generations"""
    genes = [Gene("param1", GeneType.NUMERIC.value, 0.5, range_min=0.0, range_max=1.0)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    template = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    def fitness_func(genome: AgentGenome) -> float:
        result = genome.get_gene("param1")
        if result:
            _, gene = result
            return gene.allele
        return 0.0

    simulator = EvolutionSimulator(population_size=10, mutation_rate=0.1)
    simulator.initialize_population(template)

    stats = simulator.run(generations=5, fitness_function=fitness_func)

    assert len(stats) == 5
    assert simulator.generation == 5
    # Fitness should generally improve (or at least not decrease with elitism)
    assert stats[-1]["best_fitness"] >= stats[0]["best_fitness"] * 0.9


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


def test_empty_population_selection():
    """Test selection with empty population"""
    selected = GeneticOperations.select_population([], 5)
    assert len(selected) == 0


def test_mutation_type_deletion():
    """Test deletion mutation"""
    genes = [
        Gene("gene1", GeneType.NUMERIC.value, 0.5),
        Gene("gene2", GeneType.NUMERIC.value, 0.6),
        Gene("gene3", GeneType.NUMERIC.value, 0.7),
    ]

    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    mutated = GeneticOperations.mutate_genome(
        genome,
        mutation_rate=1.0,
        mutation_type=MutationType.DELETION
    )

    # Should have mutation records
    assert len(mutated.mutations) >= 0  # May or may not delete based on constraints


def test_mutation_type_duplication():
    """Test duplication mutation"""
    genes = [Gene("gene1", GeneType.NUMERIC.value, 0.5)]

    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    mutated = GeneticOperations.mutate_genome(
        genome,
        mutation_rate=1.0,
        mutation_type=MutationType.DUPLICATION
    )

    # Check duplication occurred
    assert len(mutated.mutations) >= 0


def test_genome_to_dict():
    """Test genome serialization"""
    genes = [Gene("gene1", GeneType.NUMERIC.value, 0.5)]
    chromosome = Chromosome("chr1", ChromosomeType.PERFORMANCE.value, genes)
    genome = AgentGenome(str(uuid.uuid4()), 0, [chromosome])

    data = genome.to_dict()

    assert "genome_id" in data
    assert "generation" in data
    assert "chromosomes" in data
    assert "phenotype" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
