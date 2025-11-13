"""
Multi-Objective Pareto Evolution Engine
========================================

Evolves agents optimizing MULTIPLE objectives simultaneously using Pareto dominance.

Instead of finding a single "best" agent, discovers the PARETO FRONTIER -
the set of agents where no other agent is strictly better on ALL objectives.

This is RESEARCH-GRADE multi-objective optimization enabling sophisticated
trade-off analysis between competing goals (return vs risk, consistency vs growth, etc.).

Key Concepts:
- Pareto Dominance: Agent A dominates B if A is better/equal on all objectives and strictly better on at least one
- Pareto Frontier: The set of non-dominated solutions (the "best trade-offs")
- NSGA-II: Non-dominated Sorting Genetic Algorithm II - state-of-the-art multi-objective evolution
- Crowding Distance: Diversity metric to maintain spread of solutions along the frontier

Objectives Supported:
- Return: Total profit/loss
- Sharpe Ratio: Risk-adjusted return
- Win Rate: Fraction of winning trades
- Max Drawdown: Worst peak-to-trough decline
- Consistency: Variance of returns
- Trade Frequency: Number of trades executed
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Callable, Optional
from enum import Enum
import math
from copy import deepcopy

from .genetic_breeding import AgentGenome, EvolutionEngine, CrossoverMethod, SelectionStrategy


# ============================================================================
# Objective Definitions
# ============================================================================

class ObjectiveType(str, Enum):
    """Types of objectives for multi-objective optimization"""
    RETURN = "return"  # Maximize total return
    SHARPE_RATIO = "sharpe_ratio"  # Maximize risk-adjusted return
    WIN_RATE = "win_rate"  # Maximize fraction of winning trades
    MAX_DRAWDOWN = "max_drawdown"  # Minimize maximum drawdown
    CONSISTENCY = "consistency"  # Minimize variance of returns
    TRADE_FREQUENCY = "trade_frequency"  # Control trade frequency
    PROFIT_FACTOR = "profit_factor"  # Maximize ratio of wins to losses


@dataclass
class Objective:
    """Definition of an optimization objective"""
    objective_type: ObjectiveType
    minimize: bool = False  # True to minimize, False to maximize
    weight: float = 1.0  # Importance weight (optional, for display only)
    target_value: Optional[float] = None  # Optional target value


@dataclass
class MultiObjectiveScore:
    """Score for an agent across multiple objectives"""
    agent_id: str
    objectives: Dict[ObjectiveType, float]  # Objective -> Value
    dominance_rank: int = 0  # 0 = non-dominated (Pareto front)
    crowding_distance: float = 0.0  # Diversity metric

    def dominates(self, other: 'MultiObjectiveScore', objective_configs: List[Objective]) -> bool:
        """
        Check if this solution dominates another.

        Dominates if:
        - Better or equal on ALL objectives
        - Strictly better on AT LEAST ONE objective
        """
        at_least_one_better = False

        for obj_config in objective_configs:
            obj_type = obj_config.objective_type

            self_value = self.objectives.get(obj_type, 0.0)
            other_value = other.objectives.get(obj_type, 0.0)

            if obj_config.minimize:
                # Minimizing: lower is better
                if self_value > other_value:
                    return False  # Worse on this objective
                elif self_value < other_value:
                    at_least_one_better = True
            else:
                # Maximizing: higher is better
                if self_value < other_value:
                    return False  # Worse on this objective
                elif self_value > other_value:
                    at_least_one_better = True

        return at_least_one_better


# ============================================================================
# Multi-Objective Evaluation
# ============================================================================

class MultiObjectiveEvaluator:
    """
    Evaluates agents on multiple objectives simultaneously.

    Takes backtest results and extracts multiple performance metrics
    to enable Pareto-based evolution.
    """

    @staticmethod
    def evaluate(
        agent_id: str,
        backtest_metrics: Dict[str, Any],
        objectives: List[Objective]
    ) -> MultiObjectiveScore:
        """
        Evaluate agent on all objectives.

        Args:
            agent_id: Unique identifier
            backtest_metrics: Results from backtesting
            objectives: List of objectives to evaluate

        Returns:
            MultiObjectiveScore with values for all objectives
        """
        objective_values = {}

        for obj in objectives:
            if obj.objective_type == ObjectiveType.RETURN:
                objective_values[obj.objective_type] = backtest_metrics.get('total_return_percent', 0.0)

            elif obj.objective_type == ObjectiveType.SHARPE_RATIO:
                objective_values[obj.objective_type] = backtest_metrics.get('sharpe_ratio', 0.0)

            elif obj.objective_type == ObjectiveType.WIN_RATE:
                objective_values[obj.objective_type] = backtest_metrics.get('win_rate', 0.0)

            elif obj.objective_type == ObjectiveType.MAX_DRAWDOWN:
                # Drawdown is negative, so minimizing means less negative
                objective_values[obj.objective_type] = backtest_metrics.get('max_drawdown_percent', 0.0)

            elif obj.objective_type == ObjectiveType.CONSISTENCY:
                # Calculate from returns variance (lower is better)
                # Simplified: use negative Sharpe as proxy for inconsistency
                sharpe = backtest_metrics.get('sharpe_ratio', 0.0)
                objective_values[obj.objective_type] = -abs(sharpe) if sharpe != 0 else -1.0

            elif obj.objective_type == ObjectiveType.TRADE_FREQUENCY:
                objective_values[obj.objective_type] = backtest_metrics.get('total_trades', 0)

            elif obj.objective_type == ObjectiveType.PROFIT_FACTOR:
                objective_values[obj.objective_type] = backtest_metrics.get('profit_factor', 0.0)

        return MultiObjectiveScore(
            agent_id=agent_id,
            objectives=objective_values
        )


# ============================================================================
# NSGA-II Algorithm Components
# ============================================================================

class NSGA2:
    """
    Non-dominated Sorting Genetic Algorithm II

    State-of-the-art multi-objective evolutionary algorithm that:
    1. Sorts population into Pareto fronts (non-dominated sorting)
    2. Calculates crowding distance for diversity
    3. Selects best solutions considering both dominance and diversity

    Reference: Deb et al. (2002) "A fast and elitist multiobjective genetic algorithm: NSGA-II"
    """

    @staticmethod
    def fast_non_dominated_sort(
        scores: List[MultiObjectiveScore],
        objectives: List[Objective]
    ) -> List[List[MultiObjectiveScore]]:
        """
        Sort solutions into Pareto fronts.

        Returns:
            List of fronts, where front[0] is the Pareto frontier (best solutions)
        """
        fronts = [[]]

        # For each solution, calculate domination relationships
        domination_count = {}  # How many solutions dominate this one
        dominated_solutions = {}  # Which solutions does this one dominate

        for p in scores:
            domination_count[p.agent_id] = 0
            dominated_solutions[p.agent_id] = []

            for q in scores:
                if p.agent_id == q.agent_id:
                    continue

                if p.dominates(q, objectives):
                    dominated_solutions[p.agent_id].append(q)
                elif q.dominates(p, objectives):
                    domination_count[p.agent_id] += 1

            # If not dominated by anyone, it's in the first front
            if domination_count[p.agent_id] == 0:
                p.dominance_rank = 0
                fronts[0].append(p)

        # Build subsequent fronts
        i = 0
        while len(fronts[i]) > 0:
            next_front = []

            for p in fronts[i]:
                for q in dominated_solutions[p.agent_id]:
                    domination_count[q.agent_id] -= 1

                    if domination_count[q.agent_id] == 0:
                        q.dominance_rank = i + 1
                        next_front.append(q)

            i += 1
            if next_front:
                fronts.append(next_front)

        return fronts

    @staticmethod
    def calculate_crowding_distance(
        front: List[MultiObjectiveScore],
        objectives: List[Objective]
    ):
        """
        Calculate crowding distance for diversity.

        Crowding distance measures how isolated a solution is from its neighbors.
        Higher distance = more isolated = more diverse = better for maintaining spread.

        Modifies scores in-place with crowding_distance values.
        """
        if len(front) <= 2:
            for score in front:
                score.crowding_distance = float('inf')
            return

        # Initialize distances
        for score in front:
            score.crowding_distance = 0.0

        # Calculate distance for each objective
        for obj in objectives:
            obj_type = obj.objective_type

            # Sort by this objective
            front_sorted = sorted(front, key=lambda s: s.objectives.get(obj_type, 0.0))

            # Boundary points get infinite distance
            front_sorted[0].crowding_distance = float('inf')
            front_sorted[-1].crowding_distance = float('inf')

            # Normalize objective range
            obj_min = front_sorted[0].objectives.get(obj_type, 0.0)
            obj_max = front_sorted[-1].objectives.get(obj_type, 0.0)
            obj_range = obj_max - obj_min

            if obj_range == 0:
                continue

            # Calculate distance for intermediate points
            for i in range(1, len(front_sorted) - 1):
                if front_sorted[i].crowding_distance != float('inf'):
                    prev_val = front_sorted[i - 1].objectives.get(obj_type, 0.0)
                    next_val = front_sorted[i + 1].objectives.get(obj_type, 0.0)
                    front_sorted[i].crowding_distance += (next_val - prev_val) / obj_range

    @staticmethod
    def crowded_comparison(
        score1: MultiObjectiveScore,
        score2: MultiObjectiveScore
    ) -> int:
        """
        Compare two solutions using crowded comparison operator.

        Returns:
            -1 if score1 is better, 1 if score2 is better, 0 if equal
        """
        if score1.dominance_rank < score2.dominance_rank:
            return -1
        elif score1.dominance_rank > score2.dominance_rank:
            return 1
        else:
            # Same rank, prefer higher crowding distance
            if score1.crowding_distance > score2.crowding_distance:
                return -1
            elif score1.crowding_distance < score2.crowding_distance:
                return 1
            else:
                return 0


# ============================================================================
# Multi-Objective Evolution Engine
# ============================================================================

@dataclass
class ParetoEvolutionConfig:
    """Configuration for Pareto evolution"""
    population_size: int = 50
    num_generations: int = 20
    objectives: List[Objective] = field(default_factory=list)
    crossover_method: CrossoverMethod = CrossoverMethod.UNIFORM
    mutation_rate: float = 0.1


@dataclass
class ParetoEvolutionResult:
    """Results from Pareto evolution"""
    pareto_frontier: List[Tuple[AgentGenome, MultiObjectiveScore]]
    all_fronts: List[List[Tuple[AgentGenome, MultiObjectiveScore]]]
    generation_history: List[Dict[str, Any]]
    final_population: List[Tuple[AgentGenome, MultiObjectiveScore]]


class ParetoEvolutionEngine:
    """
    Multi-objective evolution engine using NSGA-II.

    Evolves a population of agents optimizing multiple objectives simultaneously,
    discovering the Pareto frontier of optimal trade-offs.
    """

    def __init__(self, config: ParetoEvolutionConfig):
        self.config = config
        self.evolution_engine = EvolutionEngine()
        self.evaluator = MultiObjectiveEvaluator()

    def evolve(
        self,
        fitness_func: Callable[[AgentGenome], Dict[str, Any]],
        initial_population: Optional[List[AgentGenome]] = None
    ) -> ParetoEvolutionResult:
        """
        Run multi-objective evolution.

        Args:
            fitness_func: Function that takes genome and returns backtest metrics
            initial_population: Optional starting population

        Returns:
            ParetoEvolutionResult with Pareto frontier and evolution history
        """
        # Initialize population
        if initial_population:
            population = initial_population[:self.config.population_size]
        else:
            population = self.evolution_engine.initialize_population(
                self.config.population_size
            )

        generation_history = []

        # Evolution loop
        for gen in range(self.config.num_generations):
            print(f"\n🧬 Generation {gen + 1}/{self.config.num_generations}")

            # Evaluate all agents on all objectives
            scores = []
            for genome in population:
                metrics = fitness_func(genome)
                score = self.evaluator.evaluate(genome.agent_id, metrics, self.config.objectives)
                scores.append(score)

            # Non-dominated sorting
            fronts = NSGA2.fast_non_dominated_sort(scores, self.config.objectives)

            # Calculate crowding distance for each front
            for front in fronts:
                NSGA2.calculate_crowding_distance(front, self.config.objectives)

            # Create genome-score pairs
            genome_score_map = {score.agent_id: score for score in scores}
            population_with_scores = [(genome, genome_score_map[genome.agent_id]) for genome in population]

            # Record history
            pareto_front_size = len(fronts[0]) if fronts else 0
            avg_crowding = sum(s.crowding_distance for s in fronts[0]) / len(fronts[0]) if fronts[0] else 0

            generation_history.append({
                'generation': gen + 1,
                'pareto_front_size': pareto_front_size,
                'total_fronts': len(fronts),
                'avg_crowding_distance': avg_crowding,
                'best_objectives': {
                    obj.objective_type.value: fronts[0][0].objectives.get(obj.objective_type, 0.0)
                    for obj in self.config.objectives
                } if fronts and fronts[0] else {}
            })

            print(f"   Pareto Front: {pareto_front_size} agents")
            print(f"   Total Fronts: {len(fronts)}")

            # Selection for next generation
            if gen < self.config.num_generations - 1:
                population = self._create_next_generation(population_with_scores, fronts)

        # Final evaluation
        final_scores = []
        for genome in population:
            metrics = fitness_func(genome)
            score = self.evaluator.evaluate(genome.agent_id, metrics, self.config.objectives)
            final_scores.append(score)

        final_fronts = NSGA2.fast_non_dominated_sort(final_scores, self.config.objectives)
        for front in final_fronts:
            NSGA2.calculate_crowding_distance(front, self.config.objectives)

        genome_score_map = {score.agent_id: score for score in final_scores}
        final_population_with_scores = [(genome, genome_score_map[genome.agent_id]) for genome in population]

        # Extract Pareto frontier
        pareto_frontier = []
        for score in final_fronts[0] if final_fronts else []:
            genome = next(g for g in population if g.agent_id == score.agent_id)
            pareto_frontier.append((genome, score))

        # All fronts
        all_fronts = []
        for front in final_fronts:
            front_pairs = []
            for score in front:
                genome = next(g for g in population if g.agent_id == score.agent_id)
                front_pairs.append((genome, score))
            all_fronts.append(front_pairs)

        return ParetoEvolutionResult(
            pareto_frontier=pareto_frontier,
            all_fronts=all_fronts,
            generation_history=generation_history,
            final_population=final_population_with_scores
        )

    def _create_next_generation(
        self,
        population_with_scores: List[Tuple[AgentGenome, MultiObjectiveScore]],
        fronts: List[List[MultiObjectiveScore]]
    ) -> List[AgentGenome]:
        """
        Create next generation using tournament selection and genetic operators.
        """
        # Sort by crowded comparison
        population_sorted = sorted(
            population_with_scores,
            key=lambda x: (x[1].dominance_rank, -x[1].crowding_distance)
        )

        # Elitism: Keep top solutions
        elite_size = self.config.population_size // 4
        next_gen = [genome for genome, _ in population_sorted[:elite_size]]

        # Generate offspring
        while len(next_gen) < self.config.population_size:
            # Tournament selection
            parent1 = self._tournament_select(population_sorted)
            parent2 = self._tournament_select(population_sorted)

            # Crossover
            child = self.evolution_engine.crossover(
                parent1, parent2, self.config.crossover_method
            )

            # Mutation
            if self.evolution_engine.random.random() < self.config.mutation_rate:
                child = self.evolution_engine.mutate(child, strength=0.1)

            next_gen.append(child)

        return next_gen[:self.config.population_size]

    def _tournament_select(
        self,
        population_with_scores: List[Tuple[AgentGenome, MultiObjectiveScore]],
        tournament_size: int = 3
    ) -> AgentGenome:
        """Select parent using tournament selection"""
        tournament = self.evolution_engine.random.sample(
            population_with_scores,
            min(tournament_size, len(population_with_scores))
        )

        winner = min(tournament, key=lambda x: (x[1].dominance_rank, -x[1].crowding_distance))
        return winner[0]
