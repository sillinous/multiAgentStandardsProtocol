"""
Real-Time Evolution Service - Live Genetic Breeding with WebSocket Streaming

This service manages live evolution runs and streams updates to connected clients
via WebSocket. Allows users to watch agents evolve in real-time in the browser!

Features:
- Background evolution execution
- WebSocket streaming of progress
- Start/Stop/Status API
- Multiple evolution objectives
- Real personality traits evolving

Author: Agentic Forge
"""

import asyncio
import json
from typing import Optional, Dict, List, Callable
from datetime import datetime
from enum import Enum
import uuid

from fastapi import WebSocket
from pydantic import BaseModel

# Import evolution components
import sys
sys.path.insert(0, '..')
from superstandard.agents.personality import PersonalityProfile
from superstandard.agents.genetic_breeding import (
    EvolutionEngine,
    AgentGenome,
    CrossoverMethod,
    SelectionStrategy
)
from superstandard.trading.market_simulation import (
    MarketSimulator,
    MarketRegime,
    AgentBacktester,
    MarketBar
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass


# ============================================================================
# Evolution Configuration Models
# ============================================================================

class EvolutionObjective(str, Enum):
    """Evolution objectives matching the dashboard"""
    HIGH_RETURN = "high_return"
    BALANCED = "balanced"
    RESILIENT = "resilient"


class EvolutionConfig(BaseModel):
    """Configuration for evolution run"""
    objective: EvolutionObjective = EvolutionObjective.BALANCED
    population_size: int = 20
    generations: int = 10
    mutation_rate: float = 0.15
    market_regime: str = "volatile"  # bull, bear, volatile, sideways


class EvolutionStatus(str, Enum):
    """Evolution run status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# ============================================================================
# Real-Time Evolution Manager
# ============================================================================

class EvolutionManager:
    """
    Manages real-time evolution runs with WebSocket streaming.

    Runs genetic breeding in background and broadcasts updates to all
    connected WebSocket clients.
    """

    def __init__(self):
        self.status = EvolutionStatus.IDLE
        self.current_run_id: Optional[str] = None
        self.current_generation = 0
        self.total_generations = 0
        self.config: Optional[EvolutionConfig] = None

        # Evolution state
        self.engine: Optional[EvolutionEngine] = None
        self.market_data: List[MarketBar] = []
        self.initial_fitness = 0.0

        # WebSocket clients
        self.clients: List[WebSocket] = []

        # Background task
        self.evolution_task: Optional[asyncio.Task] = None

    async def register_client(self, websocket: WebSocket):
        """Register a new WebSocket client"""
        await websocket.accept()
        self.clients.append(websocket)

        # Send current status
        await self._send_to_client(websocket, {
            "type": "status",
            "status": self.status.value,
            "current_generation": self.current_generation,
            "total_generations": self.total_generations,
            "run_id": self.current_run_id
        })

    async def unregister_client(self, websocket: WebSocket):
        """Unregister a WebSocket client"""
        if websocket in self.clients:
            self.clients.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []

        for client in self.clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.append(client)

        # Clean up disconnected clients
        for client in disconnected:
            self.clients.remove(client)

    async def _send_to_client(self, client: WebSocket, message: dict):
        """Send message to specific client"""
        try:
            await client.send_json(message)
        except Exception:
            pass

    async def start_evolution(self, config: EvolutionConfig) -> str:
        """
        Start evolution run with given configuration.

        Returns:
            run_id: Unique identifier for this run
        """
        if self.status == EvolutionStatus.RUNNING:
            raise ValueError("Evolution already running")

        # Generate run ID
        self.current_run_id = f"evolution_{uuid.uuid4().hex[:8]}"
        self.config = config
        self.status = EvolutionStatus.RUNNING
        self.current_generation = 0
        self.total_generations = config.generations

        # Broadcast start event
        await self.broadcast({
            "type": "evolution_started",
            "run_id": self.current_run_id,
            "config": config.dict(),
            "timestamp": datetime.now().isoformat()
        })

        # Start evolution in background
        self.evolution_task = asyncio.create_task(self._run_evolution())

        return self.current_run_id

    async def stop_evolution(self):
        """Stop current evolution run"""
        if self.evolution_task and not self.evolution_task.done():
            self.evolution_task.cancel()
            try:
                await self.evolution_task
            except asyncio.CancelledError:
                pass

        self.status = EvolutionStatus.IDLE

        await self.broadcast({
            "type": "evolution_stopped",
            "run_id": self.current_run_id,
            "timestamp": datetime.now().isoformat()
        })

    def get_status(self) -> dict:
        """Get current evolution status"""
        return {
            "status": self.status.value,
            "run_id": self.current_run_id,
            "current_generation": self.current_generation,
            "total_generations": self.total_generations,
            "config": self.config.dict() if self.config else None
        }

    # ========================================================================
    # Evolution Execution
    # ========================================================================

    async def _run_evolution(self):
        """Run evolution process (executed in background)"""
        try:
            # Generate market data based on config
            await self._generate_market_data()

            # Create fitness function
            fitness_func = self._create_fitness_function()

            # Initialize population
            await self._initialize_population(fitness_func)

            # Evolve!
            for gen in range(1, self.config.generations + 1):
                self.current_generation = gen

                # Broadcast generation start
                await self.broadcast({
                    "type": "generation_started",
                    "generation": gen,
                    "timestamp": datetime.now().isoformat()
                })

                # Evolve to next generation
                await self._evolve_generation(fitness_func)

                # Small delay to allow UI to update
                await asyncio.sleep(0.1)

            # Completed!
            self.status = EvolutionStatus.COMPLETED

            await self.broadcast({
                "type": "evolution_completed",
                "run_id": self.current_run_id,
                "final_generation": self.current_generation,
                "timestamp": datetime.now().isoformat()
            })

        except asyncio.CancelledError:
            self.status = EvolutionStatus.IDLE
            raise
        except Exception as e:
            self.status = EvolutionStatus.ERROR

            await self.broadcast({
                "type": "evolution_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    async def _generate_market_data(self):
        """Generate market data for fitness evaluation"""
        regime_map = {
            "bull": MarketRegime.BULL,
            "bear": MarketRegime.BEAR,
            "volatile": MarketRegime.VOLATILE,
            "sideways": MarketRegime.SIDEWAYS
        }

        regime = regime_map.get(self.config.market_regime, MarketRegime.VOLATILE)

        simulator = MarketSimulator(initial_price=100.0, seed=42)
        self.market_data = simulator.generate_bars(100, regime=regime)

        await self.broadcast({
            "type": "market_generated",
            "regime": self.config.market_regime,
            "bars": len(self.market_data),
            "timestamp": datetime.now().isoformat()
        })

    def _create_fitness_function(self) -> Callable:
        """Create fitness function based on objective"""

        def evaluate_fitness(personality: PersonalityProfile) -> float:
            """Evaluate trading fitness"""
            personality._calculate_modifiers()

            # Create simple strategy
            def strategy(current_bar, history):
                if len(history) < 20:
                    return 'hold'

                prices = [bar.close for bar in history[-20:]] + [current_bar.close]
                sma = sum(prices) / len(prices)

                if current_bar.close > sma:
                    return 'buy'
                elif current_bar.close < sma:
                    return 'sell'
                return 'hold'

            # Backtest
            risk_tolerance = personality.get_modifier('risk_tolerance')
            position_size = 0.5 + (risk_tolerance * 0.5)

            backtester = AgentBacktester(initial_capital=10000.0)
            metrics = backtester.backtest(self.market_data, strategy, position_size)

            # Objective-specific fitness
            if self.config.objective == EvolutionObjective.HIGH_RETURN:
                # Optimize for return
                return_score = min(max(metrics.total_return, -0.5), 0.5) / 0.5
                sharpe_score = min(max(metrics.sharpe_ratio, -1.0), 3.0) / 3.0
                return (return_score * 0.7 + sharpe_score * 0.3 + 1.0) / 2.0

            elif self.config.objective == EvolutionObjective.RESILIENT:
                # Optimize for low drawdown + stress resistance
                dd_score = 1.0 - min(metrics.max_drawdown, 1.0)
                stress = personality.get_modifier('stress_resistance')
                return (dd_score * 0.6 + stress * 0.4)

            else:  # BALANCED
                return metrics.get_fitness_score()

        return evaluate_fitness

    async def _initialize_population(self, fitness_func: Callable):
        """Initialize population"""
        genomes = []

        for i in range(self.config.population_size):
            personality = PersonalityProfile.random()
            genome = AgentGenome(
                agent_id=f"agent_{i}",
                generation=0,
                personality=personality,
                parents=[],
                fitness_score=fitness_func(personality),
                mutations=[]
            )
            genomes.append(genome)

        # Create engine
        self.engine = EvolutionEngine(
            population_size=self.config.population_size,
            selection_strategy=SelectionStrategy.TOURNAMENT,
            elite_ratio=0.20,
            mutation_rate=self.config.mutation_rate,
            crossover_method=CrossoverMethod.BLEND
        )

        self.engine.population = genomes

        # Record initial fitness
        self.initial_fitness = sum(g.fitness_score for g in genomes) / len(genomes)

        # Broadcast initial population
        await self._broadcast_population_update(0)

    async def _evolve_generation(self, fitness_func: Callable):
        """Evolve one generation"""
        # Get current fitness scores
        fitness_scores = {g.agent_id: g.fitness_score for g in self.engine.population}

        # Evolve
        self.engine.evolve_generation(fitness_scores)

        # Re-evaluate fitness for new population
        for genome in self.engine.population:
            genome.fitness_score = fitness_func(genome.personality)

        # Update stats
        self.engine._record_generation_stats()

        # Broadcast update
        await self._broadcast_population_update(self.current_generation)

    async def _broadcast_population_update(self, generation: int):
        """Broadcast population statistics"""
        if not self.engine or not self.engine.population:
            return

        # Calculate statistics
        fitnesses = [g.fitness_score for g in self.engine.population]
        avg_fitness = sum(fitnesses) / len(fitnesses)
        max_fitness = max(fitnesses)
        min_fitness = min(fitnesses)

        # Get best agent
        best_agent = max(self.engine.population, key=lambda g: g.fitness_score)

        # Calculate trait averages
        trait_averages = {
            'openness': sum(g.personality.openness for g in self.engine.population) / len(self.engine.population),
            'conscientiousness': sum(g.personality.conscientiousness for g in self.engine.population) / len(self.engine.population),
            'extraversion': sum(g.personality.extraversion for g in self.engine.population) / len(self.engine.population),
            'agreeableness': sum(g.personality.agreeableness for g in self.engine.population) / len(self.engine.population),
            'neuroticism': sum(g.personality.neuroticism for g in self.engine.population) / len(self.engine.population)
        }

        # Count archetypes
        archetype_counts = {}
        for genome in self.engine.population:
            archetype = genome.personality.archetype or "Unknown"
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1

        # Calculate improvement
        improvement = ((avg_fitness - self.initial_fitness) / self.initial_fitness * 100) if self.initial_fitness > 0 else 0

        # Broadcast update
        await self.broadcast({
            "type": "population_update",
            "generation": generation,
            "stats": {
                "avg_fitness": avg_fitness,
                "max_fitness": max_fitness,
                "min_fitness": min_fitness,
                "improvement": improvement
            },
            "traits": trait_averages,
            "archetypes": archetype_counts,
            "best_agent": {
                "id": best_agent.agent_id,
                "fitness": best_agent.fitness_score,
                "generation": best_agent.generation,
                "personality": {
                    "openness": best_agent.personality.openness,
                    "conscientiousness": best_agent.personality.conscientiousness,
                    "extraversion": best_agent.personality.extraversion,
                    "agreeableness": best_agent.personality.agreeableness,
                    "neuroticism": best_agent.personality.neuroticism,
                    "archetype": best_agent.personality.archetype
                }
            },
            "timestamp": datetime.now().isoformat()
        })


# Global evolution manager instance
evolution_manager = EvolutionManager()
