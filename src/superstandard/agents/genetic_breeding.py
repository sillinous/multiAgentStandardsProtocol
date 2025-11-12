"""
Genetic Agent Breeding System

Implements evolutionary algorithms to breed agents with optimal personality traits.
Personality traits serve as "DNA" that can be combined and mutated across generations.

Key Features:
- Crossover: Combine traits from two parent agents
- Mutation: Introduce random variations
- Selection: Elite, tournament, and diversity-preserving strategies
- Multi-generational evolution
- Fitness-based improvement
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
from enum import Enum
import random
import copy
from datetime import datetime
import statistics

from .personality import PersonalityProfile, PersonalityTrait


class SelectionStrategy(Enum):
    """Strategies for selecting parents for breeding"""
    ELITE = "elite"  # Top N performers breed
    TOURNAMENT = "tournament"  # Random tournaments, winners breed
    ROULETTE = "roulette"  # Fitness-proportional selection
    DIVERSITY = "diversity"  # Maintain trait diversity


class CrossoverMethod(Enum):
    """Methods for combining parent traits"""
    UNIFORM = "uniform"  # Each trait 50/50 from parents
    WEIGHTED = "weighted"  # Weight by parent fitness
    BLEND = "blend"  # Average with random variance
    SINGLE_POINT = "single_point"  # Split point in trait list


@dataclass
class AgentGenome:
    """
    Agent genetic information (personality traits as DNA).
    """
    agent_id: str
    generation: int
    personality: PersonalityProfile
    parents: List[str] = field(default_factory=list)
    fitness_score: float = 0.0
    performance_history: Dict[str, float] = field(default_factory=dict)
    birth_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    mutations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'generation': self.generation,
            'personality': self.personality.to_dict(),
            'parents': self.parents,
            'fitness_score': self.fitness_score,
            'performance_history': self.performance_history,
            'birth_time': self.birth_time,
            'mutations': self.mutations
        }


@dataclass
class GenerationStats:
    """Statistics for a generation of agents"""
    generation_num: int
    population_size: int
    avg_fitness: float
    max_fitness: float
    min_fitness: float
    trait_averages: Dict[str, float]
    trait_diversity: Dict[str, float]  # Standard deviation
    best_agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class GeneticBreeder:
    """
    Core genetic breeding engine for agents.

    Handles crossover, mutation, and offspring generation.
    """

    def __init__(
        self,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.15,
        crossover_method: CrossoverMethod = CrossoverMethod.BLEND
    ):
        """
        Initialize the breeder.

        Args:
            mutation_rate: Probability of mutation per trait (0.0 to 1.0)
            mutation_strength: Maximum change in trait value when mutating
            crossover_method: Method for combining parent traits
        """
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.crossover_method = crossover_method

    def breed(
        self,
        parent1: AgentGenome,
        parent2: AgentGenome,
        offspring_id: str,
        generation: int
    ) -> AgentGenome:
        """
        Breed two parent agents to create offspring.

        Args:
            parent1: First parent genome
            parent2: Second parent genome
            offspring_id: ID for the offspring
            generation: Generation number

        Returns:
            New agent genome
        """
        # Perform crossover
        offspring_personality = self._crossover(
            parent1.personality,
            parent2.personality,
            parent1.fitness_score,
            parent2.fitness_score
        )

        # Apply mutation
        mutations_applied = self._mutate(offspring_personality)

        # Create offspring genome
        offspring = AgentGenome(
            agent_id=offspring_id,
            generation=generation,
            personality=offspring_personality,
            parents=[parent1.agent_id, parent2.agent_id],
            mutations=mutations_applied
        )

        return offspring

    def _crossover(
        self,
        personality1: PersonalityProfile,
        personality2: PersonalityProfile,
        fitness1: float,
        fitness2: float
    ) -> PersonalityProfile:
        """
        Combine traits from two parent personalities.

        Args:
            personality1: First parent personality
            personality2: Second parent personality
            fitness1: First parent fitness score
            fitness2: Second parent fitness score

        Returns:
            New personality with combined traits
        """
        if self.crossover_method == CrossoverMethod.UNIFORM:
            # Each trait has 50/50 chance from either parent
            return self._uniform_crossover(personality1, personality2)

        elif self.crossover_method == CrossoverMethod.WEIGHTED:
            # Weight by fitness scores
            return self._weighted_crossover(personality1, personality2, fitness1, fitness2)

        elif self.crossover_method == CrossoverMethod.BLEND:
            # Average with random variance
            return self._blend_crossover(personality1, personality2)

        elif self.crossover_method == CrossoverMethod.SINGLE_POINT:
            # Split at random point
            return self._single_point_crossover(personality1, personality2)

        else:
            return self._blend_crossover(personality1, personality2)

    def _uniform_crossover(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile
    ) -> PersonalityProfile:
        """50/50 chance for each trait"""
        traits = {}
        for trait in PersonalityTrait:
            traits[trait.value] = random.choice([
                getattr(p1, trait.value),
                getattr(p2, trait.value)
            ])
        return PersonalityProfile(**traits)

    def _weighted_crossover(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        f1: float,
        f2: float
    ) -> PersonalityProfile:
        """Weight by fitness scores"""
        total_fitness = f1 + f2
        if total_fitness == 0:
            weight1 = 0.5
        else:
            weight1 = f1 / total_fitness

        traits = {}
        for trait in PersonalityTrait:
            v1 = getattr(p1, trait.value)
            v2 = getattr(p2, trait.value)
            traits[trait.value] = v1 * weight1 + v2 * (1 - weight1)

        return PersonalityProfile(**traits)

    def _blend_crossover(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile
    ) -> PersonalityProfile:
        """Average with random variance"""
        traits = {}
        for trait in PersonalityTrait:
            v1 = getattr(p1, trait.value)
            v2 = getattr(p2, trait.value)
            # Average
            avg = (v1 + v2) / 2.0
            # Add random variance (-0.1 to +0.1)
            variance = random.uniform(-0.1, 0.1)
            # Clamp to [0, 1]
            traits[trait.value] = max(0.0, min(1.0, avg + variance))

        return PersonalityProfile(**traits)

    def _single_point_crossover(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile
    ) -> PersonalityProfile:
        """Split traits at random point"""
        trait_list = list(PersonalityTrait)
        split_point = random.randint(1, len(trait_list) - 1)

        traits = {}
        for i, trait in enumerate(trait_list):
            if i < split_point:
                traits[trait.value] = getattr(p1, trait.value)
            else:
                traits[trait.value] = getattr(p2, trait.value)

        return PersonalityProfile(**traits)

    def _mutate(self, personality: PersonalityProfile) -> List[str]:
        """
        Apply random mutations to personality traits.

        Args:
            personality: Personality to mutate (modified in-place)

        Returns:
            List of mutations applied (for tracking)
        """
        mutations_applied = []

        for trait in PersonalityTrait:
            if random.random() < self.mutation_rate:
                # Apply mutation
                current_value = getattr(personality, trait.value)
                # Random change within mutation_strength
                delta = random.uniform(-self.mutation_strength, self.mutation_strength)
                new_value = max(0.0, min(1.0, current_value + delta))
                setattr(personality, trait.value, new_value)

                mutations_applied.append(
                    f"{trait.value}: {current_value:.2f} → {new_value:.2f}"
                )

        # Recalculate modifiers after mutation
        personality._calculate_modifiers()
        personality.archetype = personality._determine_archetype()

        return mutations_applied


class EvolutionEngine:
    """
    Manages multi-generational evolution of agent populations.
    """

    def __init__(
        self,
        population_size: int = 20,
        selection_strategy: SelectionStrategy = SelectionStrategy.ELITE,
        elite_ratio: float = 0.2,
        mutation_rate: float = 0.1,
        crossover_method: CrossoverMethod = CrossoverMethod.BLEND
    ):
        """
        Initialize evolution engine.

        Args:
            population_size: Number of agents per generation
            selection_strategy: How to select parents
            elite_ratio: Fraction of top performers that breed
            mutation_rate: Probability of mutation per trait
            crossover_method: Method for combining parent traits
        """
        self.population_size = population_size
        self.selection_strategy = selection_strategy
        self.elite_ratio = elite_ratio
        self.breeder = GeneticBreeder(
            mutation_rate=mutation_rate,
            crossover_method=crossover_method
        )

        # Track evolution history
        self.current_generation = 0
        self.population: List[AgentGenome] = []
        self.generation_history: List[GenerationStats] = []
        self.all_genomes: Dict[str, AgentGenome] = {}  # All agents ever created

    def initialize_population(
        self,
        fitness_evaluator: Optional[Callable[[PersonalityProfile], float]] = None
    ) -> List[AgentGenome]:
        """
        Create initial random population.

        Args:
            fitness_evaluator: Optional function to evaluate initial fitness

        Returns:
            List of initial genomes
        """
        self.population = []
        self.current_generation = 0

        for i in range(self.population_size):
            agent_id = f"gen0_agent_{i:03d}"
            personality = PersonalityProfile.random()

            genome = AgentGenome(
                agent_id=agent_id,
                generation=0,
                personality=personality
            )

            if fitness_evaluator:
                genome.fitness_score = fitness_evaluator(personality)

            self.population.append(genome)
            self.all_genomes[agent_id] = genome

        # Record generation stats
        self._record_generation_stats()

        return self.population

    def evolve_generation(
        self,
        fitness_scores: Dict[str, float]
    ) -> List[AgentGenome]:
        """
        Evolve to next generation based on fitness scores.

        Args:
            fitness_scores: Dict mapping agent_id to fitness score

        Returns:
            New generation of genomes
        """
        # Update fitness scores
        for genome in self.population:
            if genome.agent_id in fitness_scores:
                genome.fitness_score = fitness_scores[genome.agent_id]

        # Select parents
        parents = self._select_parents()

        # Create next generation
        next_generation = []
        self.current_generation += 1

        for i in range(self.population_size):
            # Select two random parents
            parent1, parent2 = random.sample(parents, 2)

            # Breed offspring
            offspring_id = f"gen{self.current_generation}_agent_{i:03d}"
            offspring = self.breeder.breed(
                parent1, parent2, offspring_id, self.current_generation
            )

            next_generation.append(offspring)
            self.all_genomes[offspring_id] = offspring

        # Update population
        self.population = next_generation

        # Record stats
        self._record_generation_stats()

        return self.population

    def _select_parents(self) -> List[AgentGenome]:
        """
        Select agents that will breed based on selection strategy.

        Returns:
            List of parent genomes
        """
        if self.selection_strategy == SelectionStrategy.ELITE:
            return self._elite_selection()
        elif self.selection_strategy == SelectionStrategy.TOURNAMENT:
            return self._tournament_selection()
        elif self.selection_strategy == SelectionStrategy.ROULETTE:
            return self._roulette_selection()
        elif self.selection_strategy == SelectionStrategy.DIVERSITY:
            return self._diversity_selection()
        else:
            return self._elite_selection()

    def _elite_selection(self) -> List[AgentGenome]:
        """Select top performers"""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
        num_elite = max(2, int(self.population_size * self.elite_ratio))
        return sorted_pop[:num_elite]

    def _tournament_selection(self, tournament_size: int = 3) -> List[AgentGenome]:
        """Select via tournaments"""
        parents = []
        num_parents = max(2, int(self.population_size * self.elite_ratio))

        for _ in range(num_parents):
            # Random tournament
            contestants = random.sample(self.population, min(tournament_size, len(self.population)))
            winner = max(contestants, key=lambda g: g.fitness_score)
            parents.append(winner)

        return parents

    def _roulette_selection(self) -> List[AgentGenome]:
        """Fitness-proportional selection"""
        total_fitness = sum(g.fitness_score for g in self.population)
        if total_fitness == 0:
            return random.sample(self.population, max(2, int(self.population_size * self.elite_ratio)))

        parents = []
        num_parents = max(2, int(self.population_size * self.elite_ratio))

        for _ in range(num_parents):
            spin = random.uniform(0, total_fitness)
            cumulative = 0
            for genome in self.population:
                cumulative += genome.fitness_score
                if cumulative >= spin:
                    parents.append(genome)
                    break

        return parents if parents else self.population[:2]

    def _diversity_selection(self) -> List[AgentGenome]:
        """Select to maintain diversity"""
        # Start with top performers
        sorted_pop = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
        num_parents = max(2, int(self.population_size * self.elite_ratio))
        parents = [sorted_pop[0]]  # Best performer

        # Add diverse agents
        for _ in range(num_parents - 1):
            max_diversity = -1
            most_diverse = None

            for candidate in sorted_pop:
                if candidate in parents:
                    continue

                # Calculate diversity from current parents
                diversity = 0
                for parent in parents:
                    for trait in PersonalityTrait:
                        diversity += abs(
                            getattr(candidate.personality, trait.value) -
                            getattr(parent.personality, trait.value)
                        )

                if diversity > max_diversity:
                    max_diversity = diversity
                    most_diverse = candidate

            if most_diverse:
                parents.append(most_diverse)

        return parents

    def _record_generation_stats(self):
        """Record statistics for current generation"""
        if not self.population:
            return

        fitness_scores = [g.fitness_score for g in self.population]
        trait_values = {trait.value: [] for trait in PersonalityTrait}

        for genome in self.population:
            for trait in PersonalityTrait:
                trait_values[trait.value].append(getattr(genome.personality, trait.value))

        trait_averages = {
            trait: statistics.mean(values)
            for trait, values in trait_values.items()
        }

        trait_diversity = {
            trait: statistics.stdev(values) if len(values) > 1 else 0.0
            for trait, values in trait_values.items()
        }

        best_genome = max(self.population, key=lambda g: g.fitness_score)

        stats = GenerationStats(
            generation_num=self.current_generation,
            population_size=len(self.population),
            avg_fitness=statistics.mean(fitness_scores),
            max_fitness=max(fitness_scores),
            min_fitness=min(fitness_scores),
            trait_averages=trait_averages,
            trait_diversity=trait_diversity,
            best_agent_id=best_genome.agent_id
        )

        self.generation_history.append(stats)

    def get_best_agent(self) -> Optional[AgentGenome]:
        """Get the best performing agent in current generation"""
        if not self.population:
            return None
        return max(self.population, key=lambda g: g.fitness_score)

    def get_lineage(self, agent_id: str) -> List[str]:
        """
        Get family tree for an agent.

        Args:
            agent_id: Agent to trace

        Returns:
            List of ancestor IDs (oldest first)
        """
        lineage = []
        genome = self.all_genomes.get(agent_id)

        if not genome:
            return lineage

        # Trace back through parents
        to_process = [agent_id]
        processed = set()

        while to_process:
            current_id = to_process.pop(0)
            if current_id in processed:
                continue

            processed.add(current_id)
            current = self.all_genomes.get(current_id)

            if current:
                lineage.append(current_id)
                to_process.extend(current.parents)

        return list(reversed(lineage))


if __name__ == "__main__":
    # Demo: Evolve agents for high innovation
    print("=== Genetic Agent Breeding Demo ===\n")

    def innovation_fitness(personality: PersonalityProfile) -> float:
        """Fitness function: reward high innovation capacity"""
        return personality.get_modifier('innovation_capacity')

    # Create evolution engine
    engine = EvolutionEngine(
        population_size=10,
        selection_strategy=SelectionStrategy.ELITE,
        elite_ratio=0.3,
        mutation_rate=0.15
    )

    # Initialize population
    print("Initializing Generation 0...")
    population = engine.initialize_population(innovation_fitness)

    print(f"Initial average innovation: {engine.generation_history[0].trait_averages['openness']:.2f}")
    print(f"Best agent: {engine.get_best_agent().agent_id}")
    print(f"Best fitness: {engine.get_best_agent().fitness_score:.2f}\n")

    # Evolve for 5 generations
    for gen in range(1, 6):
        print(f"--- Generation {gen} ---")

        # Evaluate fitness (using current personalities)
        fitness_scores = {
            genome.agent_id: innovation_fitness(genome.personality)
            for genome in engine.population
        }

        # Evolve
        engine.evolve_generation(fitness_scores)

        stats = engine.generation_history[-1]
        best = engine.get_best_agent()

        print(f"Avg openness: {stats.trait_averages['openness']:.2f}")
        print(f"Avg innovation: {stats.avg_fitness:.2f}")
        print(f"Best: {best.agent_id} (fitness: {best.fitness_score:.2f})")
        print(f"Archetype: {best.personality.archetype}\n")

    # Show evolution progress
    print("\n=== Evolution Progress ===")
    print(f"{'Gen':<6} {'Avg Fitness':<12} {'Max Fitness':<12} {'Openness':<10}")
    print("-" * 50)
    for stats in engine.generation_history:
        print(f"{stats.generation_num:<6} {stats.avg_fitness:<12.3f} {stats.max_fitness:<12.3f} {stats.trait_averages['openness']:<10.3f}")

    # Show best agent lineage
    best = engine.get_best_agent()
    lineage = engine.get_lineage(best.agent_id)
    print(f"\n=== Best Agent Lineage ===")
    print(f"Agent: {best.agent_id}")
    print(f"Ancestors: {' → '.join(lineage)}")
