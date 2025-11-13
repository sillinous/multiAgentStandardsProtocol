"""
Ensemble Service - Backend service for managing agent ensembles via API

This service provides:
- Ensemble lifecycle management (create, delete, list)
- Specialist management (add, remove, hot-swap)
- Decision routing and execution
- Performance tracking and analytics
- WebSocket streaming for real-time updates
- Multi-ensemble support

This is the production backend for deploying evolved agents!

Author: Agentic Forge
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from uuid import uuid4
import asyncio
from enum import Enum

from fastapi import WebSocket

from superstandard.agents.agent_ensemble import (
    AgentEnsemble,
    AgentSpecialist,
    SpecialistType,
    SimpleRegimeDetector
)
from superstandard.agents.genetic_breeding import AgentGenome
from superstandard.agents.personality import PersonalityProfile
from superstandard.trading.market_simulation import MarketBar


# ============================================================================
# Message Types
# ============================================================================

class EnsembleMessageType(str, Enum):
    """Message types for WebSocket streaming"""
    ENSEMBLE_CREATED = "ensemble_created"
    SPECIALIST_ADDED = "specialist_added"
    SPECIALIST_REMOVED = "specialist_removed"
    SPECIALIST_SWAPPED = "specialist_swapped"
    DECISION_MADE = "decision_made"
    PERFORMANCE_UPDATED = "performance_updated"
    ENSEMBLE_DELETED = "ensemble_deleted"
    STATS_UPDATE = "stats_update"
    ERROR = "error"


# ============================================================================
# Ensemble Registry Entry
# ============================================================================

@dataclass
class EnsembleRegistryEntry:
    """
    Registry entry for a managed ensemble.

    Tracks ensemble instance, metadata, and performance history.
    """
    ensemble_id: str
    name: str
    ensemble: AgentEnsemble
    created_at: datetime = field(default_factory=datetime.now)
    last_decision_at: Optional[datetime] = None
    total_decisions: int = 0
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Export registry entry data"""
        return {
            'ensemble_id': self.ensemble_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_decision_at': self.last_decision_at.isoformat() if self.last_decision_at else None,
            'total_decisions': self.total_decisions,
            'recent_decisions': self.decision_history[-10:],  # Last 10 decisions
            'metadata': self.metadata,
            'ensemble_stats': self.ensemble.get_statistics()
        }


# ============================================================================
# Ensemble Manager
# ============================================================================

class EnsembleManager:
    """
    Global ensemble manager for API service.

    Manages multiple ensembles, routes decisions, tracks performance,
    and broadcasts updates via WebSocket.

    This is the backend service for production ensemble deployment!
    """

    def __init__(self):
        """Initialize ensemble manager"""
        self.ensembles: Dict[str, EnsembleRegistryEntry] = {}
        self.clients: List[WebSocket] = []  # Connected WebSocket clients
        self.total_ensembles_created = 0
        self.total_decisions_made = 0

    # ========================================================================
    # WebSocket Client Management
    # ========================================================================

    async def register_client(self, websocket: WebSocket):
        """Register WebSocket client for real-time updates"""
        await websocket.accept()
        self.clients.append(websocket)

        # Send current state
        await self._send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'total_ensembles': len(self.ensembles),
            'ensemble_ids': list(self.ensembles.keys())
        })

    async def unregister_client(self, websocket: WebSocket):
        """Unregister WebSocket client"""
        if websocket in self.clients:
            self.clients.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []

        for client in self.clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            await self.unregister_client(client)

    async def _send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    # ========================================================================
    # Ensemble Lifecycle
    # ========================================================================

    async def create_ensemble(
        self,
        name: str,
        use_voting: bool = False,
        voting_threshold: float = 0.6,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new ensemble.

        Args:
            name: Ensemble name
            use_voting: Enable weighted voting
            voting_threshold: Confidence threshold for voting
            metadata: Additional metadata

        Returns:
            ensemble_id
        """
        ensemble_id = str(uuid4())

        # Create ensemble
        ensemble = AgentEnsemble(
            use_voting=use_voting,
            voting_threshold=voting_threshold
        )

        # Create registry entry
        entry = EnsembleRegistryEntry(
            ensemble_id=ensemble_id,
            name=name,
            ensemble=ensemble,
            metadata=metadata or {}
        )

        self.ensembles[ensemble_id] = entry
        self.total_ensembles_created += 1

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.ENSEMBLE_CREATED,
            'ensemble_id': ensemble_id,
            'name': name,
            'use_voting': use_voting,
            'timestamp': datetime.now().isoformat()
        })

        return ensemble_id

    async def delete_ensemble(self, ensemble_id: str) -> bool:
        """Delete ensemble"""
        if ensemble_id not in self.ensembles:
            return False

        entry = self.ensembles.pop(ensemble_id)

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.ENSEMBLE_DELETED,
            'ensemble_id': ensemble_id,
            'name': entry.name,
            'timestamp': datetime.now().isoformat()
        })

        return True

    def get_ensemble(self, ensemble_id: str) -> Optional[EnsembleRegistryEntry]:
        """Get ensemble by ID"""
        return self.ensembles.get(ensemble_id)

    def list_ensembles(self) -> List[Dict[str, Any]]:
        """List all ensembles"""
        return [entry.to_dict() for entry in self.ensembles.values()]

    # ========================================================================
    # Specialist Management
    # ========================================================================

    async def add_specialist(
        self,
        ensemble_id: str,
        genome_data: Dict[str, Any],
        specialist_type: str,
        strategy_name: Optional[str] = None
    ) -> bool:
        """
        Add specialist to ensemble.

        Args:
            ensemble_id: Target ensemble
            genome_data: Agent genome data (personality traits, fitness, etc.)
            specialist_type: Specialist type (bull, bear, volatile, etc.)
            strategy_name: Optional strategy name for reference

        Returns:
            Success flag
        """
        entry = self.get_ensemble(ensemble_id)
        if not entry:
            return False

        # Reconstruct genome from data
        personality = PersonalityProfile(
            openness=genome_data['personality']['openness'],
            conscientiousness=genome_data['personality']['conscientiousness'],
            extraversion=genome_data['personality']['extraversion'],
            agreeableness=genome_data['personality']['agreeableness'],
            neuroticism=genome_data['personality']['neuroticism']
        )

        genome = AgentGenome(
            agent_id=genome_data.get('agent_id', str(uuid4())),
            generation=genome_data.get('generation', 0),
            personality=personality,
            parents=genome_data.get('parents', []),
            fitness_score=genome_data.get('fitness_score', 0.0),
            mutations=genome_data.get('mutations', [])
        )

        # Create simple strategy (this can be customized later)
        def default_strategy(current_bar, history):
            """Simple SMA crossover strategy"""
            if len(history) < 20:
                return 'hold'

            prices = [bar.close for bar in history[-20:]] + [current_bar.close]
            sma = sum(prices) / len(prices)

            # Personality affects thresholds
            risk_tolerance = personality.get_modifier('risk_tolerance')
            threshold = 0.01 * (1 + risk_tolerance)

            if current_bar.close > sma * (1 + threshold):
                return 'buy'
            elif current_bar.close < sma * (1 - threshold):
                return 'sell'
            return 'hold'

        # Add to ensemble
        spec_type = SpecialistType(specialist_type)
        entry.ensemble.add_specialist(genome, spec_type, default_strategy)

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.SPECIALIST_ADDED,
            'ensemble_id': ensemble_id,
            'specialist_type': specialist_type,
            'agent_id': genome.agent_id,
            'generation': genome.generation,
            'fitness': genome.fitness_score,
            'timestamp': datetime.now().isoformat()
        })

        return True

    async def hot_swap_specialist(
        self,
        ensemble_id: str,
        specialist_type: str,
        new_genome_data: Dict[str, Any]
    ) -> bool:
        """Hot-swap specialist with new one"""
        entry = self.get_ensemble(ensemble_id)
        if not entry:
            return False

        # Reconstruct new genome
        personality = PersonalityProfile(
            openness=new_genome_data['personality']['openness'],
            conscientiousness=new_genome_data['personality']['conscientiousness'],
            extraversion=new_genome_data['personality']['extraversion'],
            agreeableness=new_genome_data['personality']['agreeableness'],
            neuroticism=new_genome_data['personality']['neuroticism']
        )

        new_genome = AgentGenome(
            agent_id=new_genome_data.get('agent_id', str(uuid4())),
            generation=new_genome_data.get('generation', 0),
            personality=personality,
            parents=new_genome_data.get('parents', []),
            fitness_score=new_genome_data.get('fitness_score', 0.0),
            mutations=new_genome_data.get('mutations', [])
        )

        # Create strategy
        def default_strategy(current_bar, history):
            if len(history) < 20:
                return 'hold'
            prices = [bar.close for bar in history[-20:]] + [current_bar.close]
            sma = sum(prices) / len(prices)
            risk_tolerance = personality.get_modifier('risk_tolerance')
            threshold = 0.01 * (1 + risk_tolerance)

            if current_bar.close > sma * (1 + threshold):
                return 'buy'
            elif current_bar.close < sma * (1 - threshold):
                return 'sell'
            return 'hold'

        # Hot-swap
        spec_type = SpecialistType(specialist_type)
        entry.ensemble.hot_swap(spec_type, new_genome, default_strategy)

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.SPECIALIST_SWAPPED,
            'ensemble_id': ensemble_id,
            'specialist_type': specialist_type,
            'new_agent_id': new_genome.agent_id,
            'new_generation': new_genome.generation,
            'new_fitness': new_genome.fitness_score,
            'timestamp': datetime.now().isoformat()
        })

        return True

    # ========================================================================
    # Decision Making
    # ========================================================================

    async def get_decision(
        self,
        ensemble_id: str,
        market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get trading decision from ensemble.

        Args:
            ensemble_id: Target ensemble
            market_data: Current market data (bar, price_history, etc.)

        Returns:
            Decision result with metadata
        """
        entry = self.get_ensemble(ensemble_id)
        if not entry:
            return None

        # Extract market data
        current_price = market_data.get('current_price', 100.0)
        price_history = market_data.get('price_history', [])

        # Create mock bar
        current_bar = type('MarketBar', (), {
            'close': current_price,
            'open': current_price,
            'high': current_price,
            'low': current_price,
            'volume': 1000000
        })()

        # Get decision
        decision, metadata = entry.ensemble.get_decision(
            current_bar,
            price_history,
            bar_history=[]
        )

        # Update entry
        entry.last_decision_at = datetime.now()
        entry.total_decisions += 1
        self.total_decisions_made += 1

        # Record decision
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'metadata': metadata,
            'current_price': current_price
        }
        entry.decision_history.append(decision_record)

        # Keep only recent history
        if len(entry.decision_history) > 100:
            entry.decision_history = entry.decision_history[-100:]

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.DECISION_MADE,
            'ensemble_id': ensemble_id,
            'decision': decision,
            'regime': metadata.get('regime'),
            'specialist_used': metadata.get('specialist_used'),
            'confidence': metadata.get('confidence', 0.0),
            'timestamp': datetime.now().isoformat()
        })

        return {
            'decision': decision,
            'metadata': metadata,
            'timestamp': decision_record['timestamp']
        }

    # ========================================================================
    # Performance Tracking
    # ========================================================================

    async def update_performance(
        self,
        ensemble_id: str,
        specialist_type: str,
        performance_data: Dict[str, Any]
    ) -> bool:
        """Update specialist performance"""
        entry = self.get_ensemble(ensemble_id)
        if not entry:
            return False

        spec_type = SpecialistType(specialist_type)
        entry.ensemble.update_performance(spec_type, performance_data)

        # Broadcast
        await self.broadcast({
            'type': EnsembleMessageType.PERFORMANCE_UPDATED,
            'ensemble_id': ensemble_id,
            'specialist_type': specialist_type,
            'performance_data': performance_data,
            'timestamp': datetime.now().isoformat()
        })

        return True

    # ========================================================================
    # Statistics & Analytics
    # ========================================================================

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global ensemble statistics"""
        return {
            'total_ensembles': len(self.ensembles),
            'total_ensembles_created': self.total_ensembles_created,
            'total_decisions_made': self.total_decisions_made,
            'active_clients': len(self.clients),
            'ensembles': [
                {
                    'ensemble_id': entry.ensemble_id,
                    'name': entry.name,
                    'specialists_count': len(entry.ensemble.specialists),
                    'total_decisions': entry.total_decisions,
                    'created_at': entry.created_at.isoformat()
                }
                for entry in self.ensembles.values()
            ]
        }


# ============================================================================
# Global Instance
# ============================================================================

# Singleton ensemble manager instance
ensemble_manager = EnsembleManager()
