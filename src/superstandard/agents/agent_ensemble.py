"""
Agent Ensemble System - Production Deployment of Evolved Agents

This module provides a production-ready system for deploying multiple specialist
agents as an ensemble. Routes trading decisions to the best specialist based on
current market conditions.

Features:
- Multiple specialist agents (bull, bear, volatile, etc.)
- Automatic market regime detection
- Intelligent routing to best specialist
- Weighted voting from multiple agents
- Performance tracking and analytics
- Hot-swapping of underperforming agents
- Production-ready error handling

This is how you actually DEPLOY evolved agents in production!

Author: Agentic Forge
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum
import statistics

from .personality import PersonalityProfile
from .genetic_breeding import AgentGenome


# ============================================================================
# Agent Specialist Types
# ============================================================================

class SpecialistType(str, Enum):
    """Specialist agent types for different market conditions"""
    BULL_SPECIALIST = "bull_specialist"      # Optimized for bull markets
    BEAR_SPECIALIST = "bear_specialist"      # Optimized for bear markets
    VOLATILE_SPECIALIST = "volatile_specialist"  # Optimized for high volatility
    SIDEWAYS_SPECIALIST = "sideways_specialist"  # Optimized for range-bound
    GENERALIST = "generalist"                # Works across all conditions


# ============================================================================
# Agent Specialist
# ============================================================================

@dataclass
class AgentSpecialist:
    """
    Specialist agent trained/evolved for specific market conditions.

    This wraps an evolved AgentGenome with deployment metadata.
    """
    specialist_type: SpecialistType
    genome: AgentGenome
    strategy_func: Callable

    # Performance tracking
    total_trades: int = 0
    winning_trades: int = 0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Deployment metadata
    deployed_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    version: str = "1.0.0"

    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    def get_performance_score(self) -> float:
        """
        Calculate overall performance score (0.0 to 1.0).

        Combines multiple metrics:
        - Win rate (30%)
        - Total return (30%)
        - Sharpe ratio (30%)
        - Drawdown penalty (10%)
        """
        win_rate_score = self.get_win_rate()

        # Normalize return (-50% to +50% → 0.0 to 1.0)
        return_score = min(max((self.total_return + 0.5) / 1.0, 0.0), 1.0)

        # Normalize Sharpe (-1 to 3 → 0.0 to 1.0)
        sharpe_score = min(max((self.sharpe_ratio + 1.0) / 4.0, 0.0), 1.0)

        # Drawdown penalty (0% to 100% → 1.0 to 0.0)
        dd_score = 1.0 - min(self.max_drawdown, 1.0)

        return (
            win_rate_score * 0.30 +
            return_score * 0.30 +
            sharpe_score * 0.30 +
            dd_score * 0.10
        )

    def to_dict(self) -> dict:
        """Export specialist data"""
        return {
            'specialist_type': self.specialist_type.value,
            'genome_id': self.genome.agent_id,
            'generation': self.genome.generation,
            'fitness': self.genome.fitness_score,
            'personality': {
                'openness': self.genome.personality.openness,
                'conscientiousness': self.genome.personality.conscientiousness,
                'extraversion': self.genome.personality.extraversion,
                'agreeableness': self.genome.personality.agreeableness,
                'neuroticism': self.genome.personality.neuroticism,
                'archetype': self.genome.personality.archetype
            },
            'performance': {
                'total_trades': self.total_trades,
                'win_rate': self.get_win_rate(),
                'total_return': self.total_return,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'performance_score': self.get_performance_score()
            },
            'metadata': {
                'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
                'last_updated': self.last_updated.isoformat() if self.last_updated else None,
                'version': self.version
            }
        }


# ============================================================================
# Market Regime Detector (Lightweight)
# ============================================================================

class SimpleRegimeDetector:
    """
    Simple market regime detector for ensemble routing.

    Analyzes recent market data to classify current regime.
    """

    @staticmethod
    def detect_regime(price_history: List[float], window: int = 20) -> str:
        """
        Detect current market regime from price history.

        Args:
            price_history: List of recent prices (most recent last)
            window: Number of bars to analyze

        Returns:
            Regime name: 'bull', 'bear', 'volatile', or 'sideways'
        """
        if len(price_history) < window:
            return 'sideways'  # Default

        recent = price_history[-window:]

        # Calculate trend
        total_return = (recent[-1] - recent[0]) / recent[0]

        # Calculate volatility
        returns = [(recent[i] - recent[i-1]) / recent[i-1] for i in range(1, len(recent))]
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0

        # Classify regime
        if volatility > 0.03:  # High volatility (3%+)
            return 'volatile'
        elif abs(total_return) < 0.02:  # Low movement (<2%)
            return 'sideways'
        elif total_return > 0.02:  # Uptrend (>2%)
            return 'bull'
        else:  # Downtrend (<-2%)
            return 'bear'


# ============================================================================
# Agent Ensemble Manager
# ============================================================================

class AgentEnsemble:
    """
    Manages multiple specialist agents as an ensemble.

    This is the PRODUCTION DEPLOYMENT PATTERN for evolved agents!

    Features:
    - Maintains roster of specialist agents
    - Detects current market regime
    - Routes decisions to best specialist
    - Supports weighted voting from multiple agents
    - Tracks performance of each specialist
    - Hot-swaps underperforming agents

    Example:
        # Create ensemble
        ensemble = AgentEnsemble()

        # Add specialists (evolved for different regimes)
        ensemble.add_specialist(bull_agent, SpecialistType.BULL_SPECIALIST)
        ensemble.add_specialist(bear_agent, SpecialistType.BEAR_SPECIALIST)

        # Get trading decision
        decision = ensemble.get_decision(current_bar, price_history)

        # Decision automatically routed to best specialist!
    """

    def __init__(self, use_voting: bool = False, voting_threshold: float = 0.6):
        """
        Initialize ensemble.

        Args:
            use_voting: If True, use weighted voting from multiple agents
            voting_threshold: Confidence threshold for voting (0.0 to 1.0)
        """
        self.specialists: Dict[SpecialistType, AgentSpecialist] = {}
        self.use_voting = use_voting
        self.voting_threshold = voting_threshold

        # Performance tracking
        self.total_decisions = 0
        self.routing_history: List[dict] = []
        self.regime_detector = SimpleRegimeDetector()

        # Generalist fallback
        self.generalist: Optional[AgentSpecialist] = None

    def add_specialist(
        self,
        genome: AgentGenome,
        specialist_type: SpecialistType,
        strategy_func: Callable
    ):
        """
        Add specialist agent to ensemble.

        Args:
            genome: Evolved agent genome
            specialist_type: What this agent specializes in
            strategy_func: Trading strategy function
        """
        specialist = AgentSpecialist(
            specialist_type=specialist_type,
            genome=genome,
            strategy_func=strategy_func,
            deployed_at=datetime.now()
        )

        self.specialists[specialist_type] = specialist

        if specialist_type == SpecialistType.GENERALIST:
            self.generalist = specialist

        print(f"✅ Added {specialist_type.value}: {genome.agent_id} "
              f"(gen {genome.generation}, fitness {genome.fitness_score:.3f})")

    def remove_specialist(self, specialist_type: SpecialistType):
        """Remove specialist from ensemble"""
        if specialist_type in self.specialists:
            removed = self.specialists.pop(specialist_type)
            print(f"🗑️  Removed {specialist_type.value}: {removed.genome.agent_id}")

    def get_decision(
        self,
        current_bar,
        price_history: List[float],
        **context
    ) -> Tuple[str, Dict]:
        """
        Get trading decision from ensemble.

        Args:
            current_bar: Current market bar
            price_history: List of recent prices
            **context: Additional context (volume, indicators, etc.)

        Returns:
            Tuple of (decision, metadata)
            - decision: 'buy', 'sell', or 'hold'
            - metadata: Routing info, confidence, specialist used, etc.
        """
        self.total_decisions += 1

        # Detect current regime
        regime = self.regime_detector.detect_regime(price_history)

        if self.use_voting:
            # Weighted voting from multiple agents
            decision, metadata = self._vote_decision(current_bar, price_history, regime, context)
        else:
            # Route to single best specialist
            decision, metadata = self._route_decision(current_bar, price_history, regime, context)

        # Log routing decision
        self.routing_history.append({
            'timestamp': datetime.now(),
            'regime': regime,
            'decision': decision,
            'specialist_used': metadata.get('specialist_used'),
            'confidence': metadata.get('confidence', 0.0)
        })

        # Keep only recent history
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]

        return decision, metadata

    def _route_decision(
        self,
        current_bar,
        price_history: List[float],
        regime: str,
        context: dict
    ) -> Tuple[str, Dict]:
        """Route decision to single best specialist"""

        # Map regime to specialist type
        regime_mapping = {
            'bull': SpecialistType.BULL_SPECIALIST,
            'bear': SpecialistType.BEAR_SPECIALIST,
            'volatile': SpecialistType.VOLATILE_SPECIALIST,
            'sideways': SpecialistType.SIDEWAYS_SPECIALIST
        }

        # Get preferred specialist
        preferred_type = regime_mapping.get(regime)

        # Try specialist for this regime
        if preferred_type and preferred_type in self.specialists:
            specialist = self.specialists[preferred_type]
        # Fallback to generalist
        elif self.generalist:
            specialist = self.generalist
        # No specialist available
        else:
            return 'hold', {
                'regime': regime,
                'specialist_used': None,
                'reason': 'no_specialist_available',
                'confidence': 0.0
            }

        # Get decision from specialist
        # Note: strategy_func signature: (current_bar, history) -> str
        # We'll need to build history from price_history
        decision = specialist.strategy_func(current_bar, context.get('bar_history', []))

        metadata = {
            'regime': regime,
            'specialist_used': specialist.specialist_type.value,
            'specialist_id': specialist.genome.agent_id,
            'generation': specialist.genome.generation,
            'confidence': 1.0,  # Single specialist = full confidence
            'method': 'routing'
        }

        return decision, metadata

    def _vote_decision(
        self,
        current_bar,
        price_history: List[float],
        regime: str,
        context: dict
    ) -> Tuple[str, Dict]:
        """Weighted voting from multiple specialists"""

        if not self.specialists:
            return 'hold', {'regime': regime, 'reason': 'no_specialists', 'confidence': 0.0}

        # Get decisions from all specialists
        votes = {}  # {decision: [(specialist, weight), ...]}

        for specialist_type, specialist in self.specialists.items():
            # Get decision
            decision = specialist.strategy_func(current_bar, context.get('bar_history', []))

            # Calculate weight based on performance
            weight = specialist.get_performance_score()

            # Boost weight for regime specialists
            if (regime == 'bull' and specialist_type == SpecialistType.BULL_SPECIALIST) or \
               (regime == 'bear' and specialist_type == SpecialistType.BEAR_SPECIALIST) or \
               (regime == 'volatile' and specialist_type == SpecialistType.VOLATILE_SPECIALIST) or \
               (regime == 'sideways' and specialist_type == SpecialistType.SIDEWAYS_SPECIALIST):
                weight *= 1.5  # 50% boost for regime match

            if decision not in votes:
                votes[decision] = []
            votes[decision].append((specialist, weight))

        # Tally votes
        vote_totals = {
            decision: sum(w for _, w in specialists)
            for decision, specialists in votes.items()
        }

        # Get winning decision
        total_weight = sum(vote_totals.values())

        if total_weight == 0:
            return 'hold', {'regime': regime, 'confidence': 0.0, 'method': 'voting'}

        winning_decision = max(vote_totals.items(), key=lambda x: x[1])
        decision = winning_decision[0]
        confidence = winning_decision[1] / total_weight

        # Check confidence threshold
        if confidence < self.voting_threshold:
            decision = 'hold'  # Not confident enough

        metadata = {
            'regime': regime,
            'confidence': confidence,
            'method': 'voting',
            'vote_distribution': {k: f"{v/total_weight:.2%}" for k, v in vote_totals.items()},
            'total_voters': len(self.specialists)
        }

        return decision, metadata

    def update_performance(
        self,
        specialist_type: SpecialistType,
        trade_result: dict
    ):
        """
        Update specialist performance after trade.

        Args:
            specialist_type: Which specialist made the trade
            trade_result: Trade result data (return, win/loss, etc.)
        """
        if specialist_type not in self.specialists:
            return

        specialist = self.specialists[specialist_type]
        specialist.total_trades += 1

        if trade_result.get('profit', 0) > 0:
            specialist.winning_trades += 1

        if 'return' in trade_result:
            specialist.total_return += trade_result['return']

        if 'sharpe' in trade_result:
            specialist.sharpe_ratio = trade_result['sharpe']

        if 'max_drawdown' in trade_result:
            specialist.max_drawdown = max(specialist.max_drawdown, trade_result['max_drawdown'])

        specialist.last_updated = datetime.now()

    def get_statistics(self) -> dict:
        """Get ensemble statistics"""
        if not self.specialists:
            return {'total_specialists': 0}

        # Regime distribution from routing history
        regime_counts = {}
        for entry in self.routing_history[-100:]:  # Last 100 decisions
            regime = entry.get('regime', 'unknown')
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

        # Specialist usage
        specialist_usage = {}
        for entry in self.routing_history[-100:]:
            specialist = entry.get('specialist_used', 'none')
            specialist_usage[specialist] = specialist_usage.get(specialist, 0) + 1

        return {
            'total_specialists': len(self.specialists),
            'total_decisions': self.total_decisions,
            'specialists': {
                stype.value: spec.to_dict()
                for stype, spec in self.specialists.items()
            },
            'regime_distribution': regime_counts,
            'specialist_usage': specialist_usage,
            'routing_method': 'voting' if self.use_voting else 'direct',
            'voting_threshold': self.voting_threshold if self.use_voting else None
        }

    def get_best_specialist(self) -> Optional[AgentSpecialist]:
        """Get best performing specialist"""
        if not self.specialists:
            return None

        return max(
            self.specialists.values(),
            key=lambda s: s.get_performance_score()
        )

    def get_worst_specialist(self) -> Optional[AgentSpecialist]:
        """Get worst performing specialist"""
        if not self.specialists:
            return None

        return min(
            self.specialists.values(),
            key=lambda s: s.get_performance_score()
        )

    def hot_swap(
        self,
        specialist_type: SpecialistType,
        new_genome: AgentGenome,
        new_strategy: Callable
    ):
        """
        Hot-swap underperforming specialist with new one.

        This is how you continuously improve the ensemble!
        """
        if specialist_type in self.specialists:
            old = self.specialists[specialist_type]
            print(f"🔄 Hot-swapping {specialist_type.value}:")
            print(f"   OLD: {old.genome.agent_id} (perf: {old.get_performance_score():.3f})")
            print(f"   NEW: {new_genome.agent_id} (fitness: {new_genome.fitness_score:.3f})")

        self.add_specialist(new_genome, specialist_type, new_strategy)
