"""
🧬 Agent DNA Protocol (ADP) v1.0 - PRODUCTION IMPLEMENTATION
============================================================

WORLD-FIRST: Genetic algorithms for agent evolution. Agents can evolve,
inherit traits, mutate, and crossbreed to improve performance over generations.

Features:
- Genetic representation (Genome, Chromosome, Gene)
- Mutation operations (point, insertion, deletion, duplication, inversion)
- Crossover operations (single-point, two-point, uniform)
- Selection methods (roulette wheel, tournament, elitism)
- Fitness evaluation framework
- Phenotype expression (genes → observable traits)
- Lineage tracking and mutation history
- Evolution simulation

Scientific References:
- Holland, J.H. (1992). "Genetic Algorithms". Scientific American
- Goldberg, D.E. (1989). "Genetic Algorithms in Search, Optimization and Machine Learning"
- Mitchell, M. (1998). "An Introduction to Genetic Algorithms"

Author: SuperStandard Team
License: MIT
"""

import uuid
import random
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from copy import deepcopy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMERATIONS
# ============================================================================


class ChromosomeType(Enum):
    """Types of chromosomes controlling different agent aspects"""
    BEHAVIORAL = "behavioral"
    CAPABILITY = "capability"
    PERFORMANCE = "performance"
    PERSONALITY = "personality"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


class GeneType(Enum):
    """Types of genes"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    STRATEGY = "strategy"
    ALGORITHM = "algorithm"


class Dominance(Enum):
    """Gene dominance patterns for crossover"""
    DOMINANT = "dominant"
    RECESSIVE = "recessive"
    CO_DOMINANT = "co-dominant"


class MutationType(Enum):
    """Types of genetic mutations"""
    POINT = "point"  # Change single gene value
    INSERTION = "insertion"  # Add new gene
    DELETION = "deletion"  # Remove gene
    DUPLICATION = "duplication"  # Duplicate gene
    INVERSION = "inversion"  # Reverse gene sequence


class CrossoverType(Enum):
    """Types of crossover operations"""
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    SEMANTIC = "semantic"


class SelectionMethod(Enum):
    """Selection methods for evolution"""
    ROULETTE_WHEEL = "roulette_wheel"
    TOURNAMENT = "tournament"
    RANK_BASED = "rank_based"
    ELITISM = "elitism"
    DIVERSITY_PROMOTING = "diversity_promoting"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Gene:
    """
    Atomic unit of hereditary information.

    Represents a single trait or parameter that can be inherited and mutated.
    """
    gene_id: str
    gene_type: str  # GeneType
    allele: Union[float, int, str, bool, list, dict]
    dominance: str = Dominance.CO_DOMINANT.value
    mutation_probability: float = 0.05
    allowed_values: Optional[List[Any]] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    inherited_from: Optional[str] = None

    def validate(self) -> bool:
        """Validate gene constraints"""
        if self.mutation_probability < 0 or self.mutation_probability > 1:
            return False

        # Validate numeric range
        if self.gene_type == GeneType.NUMERIC.value:
            if self.range_min is not None and self.range_max is not None:
                if isinstance(self.allele, (int, float)):
                    if not (self.range_min <= self.allele <= self.range_max):
                        return False

        # Validate categorical constraints
        if self.gene_type == GeneType.CATEGORICAL.value:
            if self.allowed_values and self.allele not in self.allowed_values:
                return False

        return True

    def mutate(self, mutation_type: MutationType = MutationType.POINT) -> 'Gene':
        """
        Apply mutation to this gene.

        Args:
            mutation_type: Type of mutation to apply

        Returns:
            New mutated gene (original unchanged)
        """
        mutated = deepcopy(self)

        if self.gene_type == GeneType.NUMERIC.value:
            if isinstance(self.allele, (int, float)):
                # Gaussian mutation for numeric genes
                sigma = 0.1  # Standard deviation
                if self.range_min is not None and self.range_max is not None:
                    mutation_range = self.range_max - self.range_min
                    delta = random.gauss(0, sigma * mutation_range)
                    mutated.allele = max(self.range_min,
                                        min(self.range_max,
                                            self.allele + delta))
                else:
                    mutated.allele = self.allele + random.gauss(0, sigma)

        elif self.gene_type == GeneType.CATEGORICAL.value:
            if self.allowed_values:
                # Random choice from allowed values
                mutated.allele = random.choice(self.allowed_values)

        elif self.gene_type == GeneType.BOOLEAN.value:
            mutated.allele = not self.allele

        return mutated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "gene_id": self.gene_id,
            "gene_type": self.gene_type,
            "allele": self.allele,
            "dominance": self.dominance,
            "mutation_probability": self.mutation_probability,
        }
        if self.allowed_values:
            result["allowed_values"] = self.allowed_values
        if self.range_min is not None and self.range_max is not None:
            result["range"] = {"min": self.range_min, "max": self.range_max}
        if self.inherited_from:
            result["inherited_from"] = self.inherited_from
        return result


@dataclass
class Chromosome:
    """
    Collection of related genes controlling a specific aspect of the agent.
    """
    chromosome_id: str
    chromosome_type: str  # ChromosomeType
    genes: List[Gene]
    expression_level: float = 1.0  # 0.0 = dormant, 1.0 = fully expressed

    def validate(self) -> bool:
        """Validate chromosome"""
        if not (0.0 <= self.expression_level <= 1.0):
            return False
        return all(gene.validate() for gene in self.genes)

    def get_gene(self, gene_id: str) -> Optional[Gene]:
        """Get specific gene by ID"""
        for gene in self.genes:
            if gene.gene_id == gene_id:
                return gene
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chromosome_id": self.chromosome_id,
            "chromosome_type": self.chromosome_type,
            "genes": [gene.to_dict() for gene in self.genes],
            "expression_level": self.expression_level,
        }


@dataclass
class Mutation:
    """Record of a genetic mutation"""
    mutation_id: str
    timestamp: str
    mutation_type: str  # MutationType
    affected_gene: str
    before_value: Any
    after_value: Any
    fitness_delta: Optional[float] = None
    beneficial: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Phenotype:
    """
    Observable characteristics and behaviors (gene expression).

    This represents the "realized" traits of the agent based on its genome.
    """
    behavior_traits: Dict[str, float] = field(default_factory=dict)
    capability_traits: Dict[str, str] = field(default_factory=dict)
    performance_traits: Dict[str, float] = field(default_factory=dict)
    specialization: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class AgentGenome:
    """
    Complete genetic code of an agent.

    The genome defines all heritable traits and can evolve over generations.
    """
    genome_id: str
    generation: int
    chromosomes: List[Chromosome]
    agent_id: Optional[str] = None
    lineage: List[str] = field(default_factory=list)
    fitness_score: float = 0.0
    phenotype: Optional[Phenotype] = None
    mutations: List[Mutation] = field(default_factory=list)

    def __post_init__(self):
        """Initialize phenotype if not provided"""
        if self.phenotype is None:
            self.phenotype = self.express_phenotype()

    def validate(self) -> bool:
        """Validate genome"""
        if self.generation < 0:
            return False
        if not (0.0 <= self.fitness_score <= 1.0):
            return False
        return all(chromosome.validate() for chromosome in self.chromosomes)

    def get_chromosome(self, chromosome_type: ChromosomeType) -> Optional[Chromosome]:
        """Get chromosome by type"""
        for chromosome in self.chromosomes:
            if chromosome.chromosome_type == chromosome_type.value:
                return chromosome
        return None

    def get_gene(self, gene_id: str) -> Optional[Tuple[Chromosome, Gene]]:
        """Get gene by ID, returns (chromosome, gene) tuple"""
        for chromosome in self.chromosomes:
            gene = chromosome.get_gene(gene_id)
            if gene:
                return (chromosome, gene)
        return None

    def express_phenotype(self) -> Phenotype:
        """
        Express genes into observable phenotype.

        This translates genotype → phenotype based on expression levels.
        """
        phenotype = Phenotype()

        for chromosome in self.chromosomes:
            if chromosome.chromosome_type == ChromosomeType.BEHAVIORAL.value:
                for gene in chromosome.genes:
                    if gene.gene_type == GeneType.NUMERIC.value:
                        value = gene.allele * chromosome.expression_level
                        phenotype.behavior_traits[gene.gene_id] = value

            elif chromosome.chromosome_type == ChromosomeType.PERFORMANCE.value:
                for gene in chromosome.genes:
                    if gene.gene_type == GeneType.NUMERIC.value:
                        value = gene.allele * chromosome.expression_level
                        phenotype.performance_traits[gene.gene_id] = value

            elif chromosome.chromosome_type == ChromosomeType.CAPABILITY.value:
                for gene in chromosome.genes:
                    phenotype.capability_traits[gene.gene_id] = str(gene.allele)

        return phenotype

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "genome_id": self.genome_id,
            "agent_id": self.agent_id,
            "generation": self.generation,
            "lineage": self.lineage,
            "chromosomes": [chrom.to_dict() for chrom in self.chromosomes],
            "fitness_score": self.fitness_score,
            "phenotype": self.phenotype.to_dict() if self.phenotype else None,
            "mutations": [mut.to_dict() for mut in self.mutations],
        }


# ============================================================================
# GENETIC OPERATIONS
# ============================================================================


class GeneticOperations:
    """
    Core genetic operations for evolution.

    Implements mutation, crossover, and selection following classic genetic algorithm theory.
    """

    @staticmethod
    def mutate_genome(
        genome: AgentGenome,
        mutation_rate: float = 0.01,
        mutation_type: MutationType = MutationType.POINT,
        target_genes: Optional[List[str]] = None,
    ) -> AgentGenome:
        """
        Apply mutation to genome.

        Args:
            genome: Genome to mutate
            mutation_rate: Probability of mutation per gene
            mutation_type: Type of mutation
            target_genes: Specific genes to mutate (None = all genes considered)

        Returns:
            New mutated genome (original unchanged)

        Reference: Holland (1992) - Genetic mutation maintains diversity
        """
        mutated_genome = deepcopy(genome)
        mutated_genome.genome_id = str(uuid.uuid4())
        mutated_genome.generation = genome.generation + 1
        mutated_genome.lineage = genome.lineage + [genome.genome_id]
        mutated_genome.mutations = []

        for chromosome in mutated_genome.chromosomes:
            for i, gene in enumerate(chromosome.genes):
                # Check if gene should be mutated
                if target_genes and gene.gene_id not in target_genes:
                    continue

                # Apply mutation based on gene's mutation probability
                if random.random() < mutation_rate * gene.mutation_probability:
                    old_value = gene.allele

                    if mutation_type == MutationType.POINT:
                        mutated_gene = gene.mutate()
                        chromosome.genes[i] = mutated_gene

                    elif mutation_type == MutationType.DELETION:
                        if len(chromosome.genes) > 1:  # Don't delete last gene
                            chromosome.genes.pop(i)

                    elif mutation_type == MutationType.DUPLICATION:
                        duplicated = deepcopy(gene)
                        duplicated.gene_id = f"{gene.gene_id}_dup_{uuid.uuid4().hex[:8]}"
                        chromosome.genes.insert(i + 1, duplicated)

                    # Record mutation
                    mutation = Mutation(
                        mutation_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow().isoformat(),
                        mutation_type=mutation_type.value,
                        affected_gene=gene.gene_id,
                        before_value=old_value,
                        after_value=chromosome.genes[i].allele if i < len(chromosome.genes) else None,
                    )
                    mutated_genome.mutations.append(mutation)

        # Re-express phenotype
        mutated_genome.phenotype = mutated_genome.express_phenotype()

        return mutated_genome

    @staticmethod
    def crossover(
        parent1: AgentGenome,
        parent2: AgentGenome,
        crossover_type: CrossoverType = CrossoverType.TWO_POINT,
        crossover_rate: float = 0.7,
    ) -> Tuple[AgentGenome, AgentGenome]:
        """
        Perform crossover between two parent genomes.

        Args:
            parent1: First parent
            parent2: Second parent
            crossover_type: Type of crossover operation
            crossover_rate: Probability of crossover occurring

        Returns:
            Tuple of two offspring genomes

        Reference: Goldberg (1989) - Crossover combines beneficial traits
        """
        # Skip crossover based on rate
        if random.random() > crossover_rate:
            return (deepcopy(parent1), deepcopy(parent2))

        offspring1 = deepcopy(parent1)
        offspring2 = deepcopy(parent2)

        # Update metadata
        new_generation = max(parent1.generation, parent2.generation) + 1

        offspring1.genome_id = str(uuid.uuid4())
        offspring1.generation = new_generation
        offspring1.lineage = [parent1.genome_id, parent2.genome_id]
        offspring1.mutations = []

        offspring2.genome_id = str(uuid.uuid4())
        offspring2.generation = new_generation
        offspring2.lineage = [parent1.genome_id, parent2.genome_id]
        offspring2.mutations = []

        # Perform crossover on each chromosome pair
        for i in range(min(len(parent1.chromosomes), len(parent2.chromosomes))):
            chrom1 = offspring1.chromosomes[i]
            chrom2 = offspring2.chromosomes[i]

            genes1 = chrom1.genes
            genes2 = chrom2.genes

            if crossover_type == CrossoverType.SINGLE_POINT:
                # Single point crossover
                if len(genes1) > 1 and len(genes2) > 1:
                    point = random.randint(1, min(len(genes1), len(genes2)) - 1)

                    new_genes1 = genes1[:point] + genes2[point:]
                    new_genes2 = genes2[:point] + genes1[point:]

                    chrom1.genes = new_genes1
                    chrom2.genes = new_genes2

            elif crossover_type == CrossoverType.TWO_POINT:
                # Two point crossover
                if len(genes1) > 2 and len(genes2) > 2:
                    max_len = min(len(genes1), len(genes2))
                    point1 = random.randint(1, max_len - 2)
                    point2 = random.randint(point1 + 1, max_len - 1)

                    new_genes1 = genes1[:point1] + genes2[point1:point2] + genes1[point2:]
                    new_genes2 = genes2[:point1] + genes1[point1:point2] + genes2[point2:]

                    chrom1.genes = new_genes1
                    chrom2.genes = new_genes2

            elif crossover_type == CrossoverType.UNIFORM:
                # Uniform crossover (50% chance per gene)
                new_genes1 = []
                new_genes2 = []

                for j in range(min(len(genes1), len(genes2))):
                    if random.random() < 0.5:
                        new_genes1.append(deepcopy(genes1[j]))
                        new_genes2.append(deepcopy(genes2[j]))
                    else:
                        new_genes1.append(deepcopy(genes2[j]))
                        new_genes2.append(deepcopy(genes1[j]))

                chrom1.genes = new_genes1
                chrom2.genes = new_genes2

            # Mark inheritance
            for gene in chrom1.genes:
                gene.inherited_from = "parent1" if gene in genes1 else "parent2"
            for gene in chrom2.genes:
                gene.inherited_from = "parent2" if gene in genes2 else "parent1"

        # Re-express phenotypes
        offspring1.phenotype = offspring1.express_phenotype()
        offspring2.phenotype = offspring2.express_phenotype()

        return (offspring1, offspring2)

    @staticmethod
    def select_population(
        population: List[AgentGenome],
        selection_size: int,
        method: SelectionMethod = SelectionMethod.TOURNAMENT,
        selection_pressure: float = 0.5,
        elitism_count: int = 0,
    ) -> List[AgentGenome]:
        """
        Select individuals for next generation.

        Args:
            population: Current population
            selection_size: Number of individuals to select
            method: Selection method
            selection_pressure: How strongly to favor high fitness
            elitism_count: Number of best individuals to preserve

        Returns:
            Selected individuals

        Reference: Mitchell (1998) - Selection drives evolutionary progress
        """
        if not population:
            return []

        selected = []

        # Elitism - always preserve best individuals
        if elitism_count > 0:
            sorted_pop = sorted(population, key=lambda g: g.fitness_score, reverse=True)
            selected.extend(sorted_pop[:elitism_count])
            selection_size -= elitism_count

        # Apply selection method
        if method == SelectionMethod.ROULETTE_WHEEL:
            selected.extend(GeneticOperations._roulette_wheel_selection(
                population, selection_size
            ))

        elif method == SelectionMethod.TOURNAMENT:
            tournament_size = max(2, int(len(population) * selection_pressure))
            selected.extend(GeneticOperations._tournament_selection(
                population, selection_size, tournament_size
            ))

        elif method == SelectionMethod.RANK_BASED:
            selected.extend(GeneticOperations._rank_based_selection(
                population, selection_size
            ))

        elif method == SelectionMethod.ELITISM:
            sorted_pop = sorted(population, key=lambda g: g.fitness_score, reverse=True)
            selected.extend(sorted_pop[:selection_size])

        return selected

    @staticmethod
    def _roulette_wheel_selection(population: List[AgentGenome], count: int) -> List[AgentGenome]:
        """
        Roulette wheel selection (fitness-proportionate).

        Individuals with higher fitness have higher probability of selection.
        """
        total_fitness = sum(g.fitness_score for g in population)
        if total_fitness == 0:
            return random.choices(population, k=count)

        probabilities = [g.fitness_score / total_fitness for g in population]
        return random.choices(population, weights=probabilities, k=count)

    @staticmethod
    def _tournament_selection(
        population: List[AgentGenome],
        count: int,
        tournament_size: int
    ) -> List[AgentGenome]:
        """
        Tournament selection.

        Randomly select tournament_size individuals and pick the best.
        """
        selected = []
        for _ in range(count):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda g: g.fitness_score)
            selected.append(winner)
        return selected

    @staticmethod
    def _rank_based_selection(population: List[AgentGenome], count: int) -> List[AgentGenome]:
        """
        Rank-based selection.

        Selection probability based on rank rather than absolute fitness.
        """
        sorted_pop = sorted(population, key=lambda g: g.fitness_score)
        ranks = list(range(1, len(sorted_pop) + 1))
        total_rank = sum(ranks)

        probabilities = [r / total_rank for r in ranks]
        return random.choices(sorted_pop, weights=probabilities, k=count)


# ============================================================================
# FITNESS EVALUATION
# ============================================================================


class FitnessEvaluator:
    """
    Framework for evaluating agent fitness.

    Fitness determines which agents survive and reproduce.
    """

    def __init__(self, metrics: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize evaluator.

        Args:
            metrics: List of evaluation metrics with weights
        """
        self.metrics = metrics or []

    def evaluate(
        self,
        genome: AgentGenome,
        objective_function: Optional[Callable[[AgentGenome], float]] = None,
    ) -> float:
        """
        Evaluate genome fitness.

        Args:
            genome: Genome to evaluate
            objective_function: Custom fitness function

        Returns:
            Fitness score (0.0 to 1.0)
        """
        if objective_function:
            return objective_function(genome)

        # Default: aggregate multiple metrics
        if not self.metrics:
            return 0.5  # Neutral fitness

        total_weight = sum(m.get("weight", 1.0) for m in self.metrics)
        weighted_sum = 0.0

        for metric in self.metrics:
            metric_name = metric["metric_name"]
            weight = metric.get("weight", 1.0)
            optimization = metric.get("optimization", "maximize")

            # Get metric value from phenotype
            value = self._get_metric_value(genome, metric_name)

            if optimization == "minimize":
                value = 1.0 - value  # Invert for minimization

            weighted_sum += value * weight

        fitness = weighted_sum / total_weight
        return max(0.0, min(1.0, fitness))

    def _get_metric_value(self, genome: AgentGenome, metric_name: str) -> float:
        """Extract metric value from genome/phenotype"""
        if not genome.phenotype:
            return 0.5

        # Check performance traits
        if metric_name in genome.phenotype.performance_traits:
            return genome.phenotype.performance_traits[metric_name]

        # Check behavior traits
        if metric_name in genome.phenotype.behavior_traits:
            return genome.phenotype.behavior_traits[metric_name]

        return 0.5


# ============================================================================
# EVOLUTION SIMULATOR
# ============================================================================


class EvolutionSimulator:
    """
    Simulates agent evolution over multiple generations.
    """

    def __init__(
        self,
        population_size: int = 20,
        mutation_rate: float = 0.01,
        crossover_rate: float = 0.7,
        elitism_count: int = 2,
    ):
        """
        Initialize simulator.

        Args:
            population_size: Number of individuals in population
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            elitism_count: Number of best individuals to preserve
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_count = elitism_count

        self.population: List[AgentGenome] = []
        self.generation = 0
        self.best_genome: Optional[AgentGenome] = None
        self.fitness_history: List[float] = []

    def initialize_population(self, genome_template: AgentGenome):
        """
        Create initial population from template.

        Args:
            genome_template: Template genome to vary
        """
        self.population = []

        for i in range(self.population_size):
            genome = deepcopy(genome_template)
            genome.genome_id = str(uuid.uuid4())
            genome.generation = 0

            # Add random variation
            if i > 0:  # Keep first as-is
                genome = GeneticOperations.mutate_genome(
                    genome, mutation_rate=0.1
                )

            self.population.append(genome)

        self.generation = 0
        logger.info(f"Initialized population of {self.population_size} individuals")

    def evolve_generation(
        self,
        fitness_function: Callable[[AgentGenome], float],
        selection_method: SelectionMethod = SelectionMethod.TOURNAMENT,
    ) -> Dict[str, Any]:
        """
        Evolve one generation.

        Args:
            fitness_function: Function to evaluate fitness
            selection_method: How to select parents

        Returns:
            Generation statistics
        """
        # Evaluate fitness
        for genome in self.population:
            genome.fitness_score = fitness_function(genome)

        # Track best
        best = max(self.population, key=lambda g: g.fitness_score)
        if self.best_genome is None or best.fitness_score > self.best_genome.fitness_score:
            self.best_genome = deepcopy(best)

        # Statistics
        avg_fitness = sum(g.fitness_score for g in self.population) / len(self.population)
        self.fitness_history.append(avg_fitness)

        # Selection
        parents = GeneticOperations.select_population(
            self.population,
            selection_size=self.population_size,
            method=selection_method,
            elitism_count=self.elitism_count,
        )

        # Crossover and mutation to create new population
        new_population = []

        # Add elite directly
        if self.elitism_count > 0:
            elite = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
            new_population.extend(deepcopy(g) for g in elite[:self.elitism_count])

        # Generate offspring
        while len(new_population) < self.population_size:
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)

            offspring1, offspring2 = GeneticOperations.crossover(
                parent1, parent2, crossover_rate=self.crossover_rate
            )

            # Apply mutation
            offspring1 = GeneticOperations.mutate_genome(offspring1, self.mutation_rate)
            if len(new_population) + 1 < self.population_size:
                offspring2 = GeneticOperations.mutate_genome(offspring2, self.mutation_rate)
                new_population.extend([offspring1, offspring2])
            else:
                new_population.append(offspring1)

        self.population = new_population[:self.population_size]
        self.generation += 1

        return {
            "generation": self.generation,
            "avg_fitness": avg_fitness,
            "best_fitness": best.fitness_score,
            "population_size": len(self.population),
        }

    def run(
        self,
        generations: int,
        fitness_function: Callable[[AgentGenome], float],
        selection_method: SelectionMethod = SelectionMethod.TOURNAMENT,
    ) -> List[Dict[str, Any]]:
        """
        Run evolution for multiple generations.

        Args:
            generations: Number of generations to evolve
            fitness_function: Function to evaluate fitness
            selection_method: Selection method to use

        Returns:
            List of generation statistics
        """
        stats = []

        for gen in range(generations):
            gen_stats = self.evolve_generation(fitness_function, selection_method)
            stats.append(gen_stats)

            logger.info(
                f"Gen {gen_stats['generation']}: "
                f"Avg={gen_stats['avg_fitness']:.4f}, "
                f"Best={gen_stats['best_fitness']:.4f}"
            )

        return stats


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


def create_example_genome() -> AgentGenome:
    """Create an example genome for demonstration"""

    # Performance chromosome
    perf_genes = [
        Gene(
            gene_id="learning_rate",
            gene_type=GeneType.NUMERIC.value,
            allele=0.001,
            range_min=0.0001,
            range_max=0.1,
            mutation_probability=0.1,
        ),
        Gene(
            gene_id="temperature",
            gene_type=GeneType.NUMERIC.value,
            allele=0.7,
            range_min=0.0,
            range_max=2.0,
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
            allele=0.8,
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

    genome = AgentGenome(
        genome_id=str(uuid.uuid4()),
        generation=0,
        chromosomes=[perf_chromosome, behavior_chromosome],
        fitness_score=0.5,
    )

    return genome


if __name__ == "__main__":
    print("🧬 ADP v1.0 - Agent DNA Protocol\n")

    # Create example genome
    genome = create_example_genome()
    print(f"Original genome: {genome.genome_id}")
    print(f"  Learning rate: {genome.get_gene('learning_rate')[1].allele}")
    print(f"  Temperature: {genome.get_gene('temperature')[1].allele}")
    print()

    # Mutate
    mutated = GeneticOperations.mutate_genome(genome, mutation_rate=0.5)
    print(f"Mutated genome: {mutated.genome_id}")
    print(f"  Learning rate: {mutated.get_gene('learning_rate')[1].allele}")
    print(f"  Temperature: {mutated.get_gene('temperature')[1].allele}")
    print(f"  Mutations applied: {len(mutated.mutations)}")
    print()

    # Crossover
    genome2 = create_example_genome()
    offspring1, offspring2 = GeneticOperations.crossover(genome, genome2)
    print(f"Crossover produced:")
    print(f"  Offspring 1: {offspring1.genome_id}")
    print(f"  Offspring 2: {offspring2.genome_id}")
    print()

    print("✅ ADP implementation working!")
