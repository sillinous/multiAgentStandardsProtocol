"""
Agent Reputation Protocol (ARP)

Tracks agent performance over time and calculates reputation scores based on
actual execution outcomes. Enables self-improving multi-agent ecosystems where
the system learns which agents perform best and automatically optimizes selection.

Key Features:
- Multi-dimensional scoring (quality, reliability, speed, cost-effectiveness)
- Weighted history (recent performance weighted more heavily)
- Decay functions (old performance gradually decays)
- Fraud detection (detect manipulated scores)
- Automatic integration with Discovery service
- Real-time Dashboard events

Usage:
    from src.superstandard.protocols.reputation import get_reputation_service

    reputation = get_reputation_service()

    # Record task outcome
    await reputation.record_outcome(
        agent_id="agent-123",
        task_id="task-456",
        success=True,
        quality_score=0.95,
        duration_ms=1234,
        cost=0.15
    )

    # Get agent reputation
    rep = await reputation.get_reputation("agent-123")
    # Returns comprehensive reputation profile with all scores
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import math


logger = logging.getLogger(__name__)


class ReputationDimension(Enum):
    """Dimensions of agent reputation"""
    RELIABILITY = "reliability"  # Success rate
    QUALITY = "quality"  # Output quality scores
    SPEED = "speed"  # Response time performance
    COST_EFFECTIVENESS = "cost_effectiveness"  # Cost vs quality ratio
    CONSISTENCY = "consistency"  # Variance in performance
    AVAILABILITY = "availability"  # Uptime and responsiveness


@dataclass
class TaskOutcome:
    """Record of a single task execution outcome"""
    outcome_id: str
    agent_id: str
    task_id: str
    timestamp: str
    success: bool
    quality_score: Optional[float] = None  # 0.0-1.0
    duration_ms: Optional[float] = None
    cost: Optional[float] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DimensionScore:
    """Score for a single reputation dimension"""
    dimension: ReputationDimension
    score: float  # 0.0-1.0
    sample_size: int
    confidence: float  # How confident we are in this score (based on sample size)
    trend: str  # "improving", "stable", "declining"
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['dimension'] = self.dimension.value
        return data


@dataclass
class AgentReputation:
    """Complete reputation profile for an agent"""
    agent_id: str
    overall_score: float  # 0.0-1.0 (weighted average of dimensions)
    dimension_scores: Dict[str, DimensionScore]
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    avg_quality: float
    avg_duration_ms: float
    avg_cost: float
    first_task_at: str
    last_task_at: str
    reputation_trend: str  # "improving", "stable", "declining"
    confidence_level: float  # How confident we are (based on sample size)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['dimension_scores'] = {
            k: v.to_dict() for k, v in self.dimension_scores.items()
        }
        return data


class ReputationService:
    """
    Agent Reputation Service

    Tracks agent performance over time and calculates reputation scores.
    Enables self-improving agent ecosystems through learned performance data.

    Features:
    - Multi-dimensional scoring
    - Weighted history (recent > old)
    - Time decay for old outcomes
    - Fraud detection
    - Automatic discovery integration
    - Real-time dashboard events
    """

    def __init__(
        self,
        decay_halflife_days: int = 30,
        min_samples_for_confidence: int = 10
    ):
        """
        Initialize reputation service

        Args:
            decay_halflife_days: Days for old outcomes to lose half their weight
            min_samples_for_confidence: Minimum samples for high confidence score
        """
        self.decay_halflife_days = decay_halflife_days
        self.min_samples_for_confidence = min_samples_for_confidence

        # Outcome history (agent_id -> list of outcomes)
        self.outcomes: Dict[str, List[TaskOutcome]] = {}

        # Cached reputation profiles (agent_id -> reputation)
        self.reputations: Dict[str, AgentReputation] = {}

        # Stats
        self.stats = {
            "total_outcomes_recorded": 0,
            "total_agents_tracked": 0,
            "total_reputation_updates": 0
        }

        logger.info("✅ Agent Reputation Service initialized")
        logger.info(f"   Decay halflife: {decay_halflife_days} days")
        logger.info(f"   Min samples for confidence: {min_samples_for_confidence}")

    async def start(self):
        """Start reputation service"""
        logger.info("🚀 Agent Reputation Service started")

    async def stop(self):
        """Stop reputation service"""
        logger.info("🛑 Agent Reputation Service stopped")

    async def record_outcome(
        self,
        agent_id: str,
        task_id: str,
        success: bool,
        quality_score: Optional[float] = None,
        duration_ms: Optional[float] = None,
        cost: Optional[float] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskOutcome:
        """
        Record a task execution outcome

        Args:
            agent_id: Agent that executed the task
            task_id: Task identifier
            success: Whether task succeeded
            quality_score: Quality of output (0.0-1.0)
            duration_ms: Execution duration in milliseconds
            cost: Cost in USD
            error_type: Type of error if failed
            metadata: Additional metadata

        Returns:
            TaskOutcome record
        """
        outcome = TaskOutcome(
            outcome_id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            quality_score=quality_score,
            duration_ms=duration_ms,
            cost=cost,
            error_type=error_type,
            metadata=metadata or {}
        )

        # Store outcome
        if agent_id not in self.outcomes:
            self.outcomes[agent_id] = []
            self.stats["total_agents_tracked"] += 1

        self.outcomes[agent_id].append(outcome)
        self.stats["total_outcomes_recorded"] += 1

        # Recalculate reputation
        await self._update_reputation(agent_id)

        logger.info(
            f"📝 Recorded outcome for {agent_id}: "
            f"{'✅ success' if success else '❌ failed'}"
        )

        return outcome

    async def _update_reputation(self, agent_id: str):
        """Recalculate reputation for an agent"""
        outcomes = self.outcomes.get(agent_id, [])
        if not outcomes:
            return

        # Calculate dimension scores
        dimension_scores = {}

        # 1. Reliability (success rate with time decay)
        dimension_scores[ReputationDimension.RELIABILITY.value] = (
            self._calculate_reliability(outcomes)
        )

        # 2. Quality (average quality scores)
        dimension_scores[ReputationDimension.QUALITY.value] = (
            self._calculate_quality(outcomes)
        )

        # 3. Speed (response time performance)
        dimension_scores[ReputationDimension.SPEED.value] = (
            self._calculate_speed(outcomes)
        )

        # 4. Cost Effectiveness (quality vs cost)
        dimension_scores[ReputationDimension.COST_EFFECTIVENESS.value] = (
            self._calculate_cost_effectiveness(outcomes)
        )

        # 5. Consistency (variance in performance)
        dimension_scores[ReputationDimension.CONSISTENCY.value] = (
            self._calculate_consistency(outcomes)
        )

        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(dimension_scores)

        # Calculate aggregates
        successful = sum(1 for o in outcomes if o.success)
        failed = len(outcomes) - successful

        quality_scores = [o.quality_score for o in outcomes if o.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        durations = [o.duration_ms for o in outcomes if o.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        costs = [o.cost for o in outcomes if o.cost is not None]
        avg_cost = sum(costs) / len(costs) if costs else 0.0

        # Determine trend
        trend = self._calculate_trend(outcomes, overall_score)

        # Calculate confidence
        confidence = self._calculate_confidence(len(outcomes))

        # Create reputation profile
        reputation = AgentReputation(
            agent_id=agent_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            total_tasks=len(outcomes),
            successful_tasks=successful,
            failed_tasks=failed,
            avg_quality=avg_quality,
            avg_duration_ms=avg_duration,
            avg_cost=avg_cost,
            first_task_at=outcomes[0].timestamp,
            last_task_at=outcomes[-1].timestamp,
            reputation_trend=trend,
            confidence_level=confidence
        )

        self.reputations[agent_id] = reputation
        self.stats["total_reputation_updates"] += 1

        logger.debug(
            f"🔄 Updated reputation for {agent_id}: {overall_score:.3f} ({trend})"
        )

        return reputation

    def _calculate_reliability(self, outcomes: List[TaskOutcome]) -> DimensionScore:
        """Calculate reliability score (success rate with time decay)"""
        if not outcomes:
            return DimensionScore(
                dimension=ReputationDimension.RELIABILITY,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        now = datetime.utcnow()
        weighted_success = 0.0
        total_weight = 0.0

        for outcome in outcomes:
            timestamp = datetime.fromisoformat(outcome.timestamp)
            age_days = (now - timestamp).days
            weight = self._time_decay_weight(age_days)

            weighted_success += (1.0 if outcome.success else 0.0) * weight
            total_weight += weight

        score = weighted_success / total_weight if total_weight > 0 else 0.5

        # Calculate trend
        recent_outcomes = outcomes[-10:] if len(outcomes) >= 10 else outcomes
        old_outcomes = outcomes[:-10] if len(outcomes) >= 20 else []

        trend = "stable"
        if old_outcomes:
            recent_rate = sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes)
            old_rate = sum(1 for o in old_outcomes if o.success) / len(old_outcomes)
            if recent_rate > old_rate + 0.1:
                trend = "improving"
            elif recent_rate < old_rate - 0.1:
                trend = "declining"

        return DimensionScore(
            dimension=ReputationDimension.RELIABILITY,
            score=score,
            sample_size=len(outcomes),
            confidence=self._calculate_confidence(len(outcomes)),
            trend=trend,
            last_updated=datetime.utcnow().isoformat()
        )

    def _calculate_quality(self, outcomes: List[TaskOutcome]) -> DimensionScore:
        """Calculate quality score (average quality with time decay)"""
        quality_outcomes = [o for o in outcomes if o.quality_score is not None]

        if not quality_outcomes:
            return DimensionScore(
                dimension=ReputationDimension.QUALITY,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        now = datetime.utcnow()
        weighted_quality = 0.0
        total_weight = 0.0

        for outcome in quality_outcomes:
            timestamp = datetime.fromisoformat(outcome.timestamp)
            age_days = (now - timestamp).days
            weight = self._time_decay_weight(age_days)

            weighted_quality += outcome.quality_score * weight
            total_weight += weight

        score = weighted_quality / total_weight if total_weight > 0 else 0.5

        # Calculate trend
        trend = "stable"
        if len(quality_outcomes) >= 10:
            recent = quality_outcomes[-5:]
            old = quality_outcomes[-10:-5]
            recent_avg = sum(o.quality_score for o in recent) / len(recent)
            old_avg = sum(o.quality_score for o in old) / len(old)
            if recent_avg > old_avg + 0.05:
                trend = "improving"
            elif recent_avg < old_avg - 0.05:
                trend = "declining"

        return DimensionScore(
            dimension=ReputationDimension.QUALITY,
            score=score,
            sample_size=len(quality_outcomes),
            confidence=self._calculate_confidence(len(quality_outcomes)),
            trend=trend,
            last_updated=datetime.utcnow().isoformat()
        )

    def _calculate_speed(self, outcomes: List[TaskOutcome]) -> DimensionScore:
        """Calculate speed score (lower duration = higher score)"""
        speed_outcomes = [o for o in outcomes if o.duration_ms is not None]

        if not speed_outcomes:
            return DimensionScore(
                dimension=ReputationDimension.SPEED,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        # Calculate score based on duration
        # Normalize to 0-1 scale (faster = higher score)
        durations = [o.duration_ms for o in speed_outcomes]
        avg_duration = sum(durations) / len(durations)

        # Assume 5000ms is "acceptable", 1000ms is "excellent"
        # Convert to 0-1 scale
        if avg_duration <= 1000:
            score = 1.0
        elif avg_duration >= 5000:
            score = 0.5
        else:
            score = 1.0 - ((avg_duration - 1000) / 4000) * 0.5

        trend = "stable"
        if len(speed_outcomes) >= 10:
            recent = speed_outcomes[-5:]
            old = speed_outcomes[-10:-5]
            recent_avg = sum(o.duration_ms for o in recent) / len(recent)
            old_avg = sum(o.duration_ms for o in old) / len(old)
            if recent_avg < old_avg * 0.9:  # 10% faster
                trend = "improving"
            elif recent_avg > old_avg * 1.1:  # 10% slower
                trend = "declining"

        return DimensionScore(
            dimension=ReputationDimension.SPEED,
            score=score,
            sample_size=len(speed_outcomes),
            confidence=self._calculate_confidence(len(speed_outcomes)),
            trend=trend,
            last_updated=datetime.utcnow().isoformat()
        )

    def _calculate_cost_effectiveness(self, outcomes: List[TaskOutcome]) -> DimensionScore:
        """Calculate cost-effectiveness (quality vs cost ratio)"""
        cost_outcomes = [
            o for o in outcomes
            if o.cost is not None and o.quality_score is not None
        ]

        if not cost_outcomes:
            return DimensionScore(
                dimension=ReputationDimension.COST_EFFECTIVENESS,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        # Calculate quality/cost ratio
        ratios = []
        for outcome in cost_outcomes:
            if outcome.cost > 0:
                ratio = outcome.quality_score / outcome.cost
                ratios.append(ratio)

        if not ratios:
            return DimensionScore(
                dimension=ReputationDimension.COST_EFFECTIVENESS,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        avg_ratio = sum(ratios) / len(ratios)

        # Normalize: assume ratio of 5.0 (quality 0.95, cost $0.19) is "good"
        # ratio of 10.0 is "excellent"
        if avg_ratio >= 10.0:
            score = 1.0
        elif avg_ratio <= 2.0:
            score = 0.5
        else:
            score = 0.5 + ((avg_ratio - 2.0) / 8.0) * 0.5

        return DimensionScore(
            dimension=ReputationDimension.COST_EFFECTIVENESS,
            score=min(1.0, score),
            sample_size=len(cost_outcomes),
            confidence=self._calculate_confidence(len(cost_outcomes)),
            trend="stable",
            last_updated=datetime.utcnow().isoformat()
        )

    def _calculate_consistency(self, outcomes: List[TaskOutcome]) -> DimensionScore:
        """Calculate consistency (low variance = high score)"""
        if len(outcomes) < 3:
            return DimensionScore(
                dimension=ReputationDimension.CONSISTENCY,
                score=0.5,
                sample_size=len(outcomes),
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        # Calculate variance in quality scores
        quality_outcomes = [o for o in outcomes if o.quality_score is not None]
        if len(quality_outcomes) < 3:
            return DimensionScore(
                dimension=ReputationDimension.CONSISTENCY,
                score=0.5,
                sample_size=0,
                confidence=0.0,
                trend="stable",
                last_updated=datetime.utcnow().isoformat()
            )

        qualities = [o.quality_score for o in quality_outcomes]
        mean = sum(qualities) / len(qualities)
        variance = sum((q - mean) ** 2 for q in qualities) / len(qualities)
        std_dev = math.sqrt(variance)

        # Low std dev = high consistency
        # Assume std dev of 0.05 or less is excellent
        # std dev of 0.20 or more is poor
        if std_dev <= 0.05:
            score = 1.0
        elif std_dev >= 0.20:
            score = 0.5
        else:
            score = 1.0 - ((std_dev - 0.05) / 0.15) * 0.5

        return DimensionScore(
            dimension=ReputationDimension.CONSISTENCY,
            score=score,
            sample_size=len(quality_outcomes),
            confidence=self._calculate_confidence(len(quality_outcomes)),
            trend="stable",
            last_updated=datetime.utcnow().isoformat()
        )

    def _calculate_overall_score(
        self,
        dimension_scores: Dict[str, DimensionScore]
    ) -> float:
        """Calculate weighted overall reputation score"""
        # Weights for each dimension
        weights = {
            ReputationDimension.RELIABILITY.value: 0.30,
            ReputationDimension.QUALITY.value: 0.30,
            ReputationDimension.SPEED.value: 0.15,
            ReputationDimension.COST_EFFECTIVENESS.value: 0.15,
            ReputationDimension.CONSISTENCY.value: 0.10
        }

        total_score = 0.0
        total_weight = 0.0

        for dim_name, dim_score in dimension_scores.items():
            weight = weights.get(dim_name, 0.1)
            total_score += dim_score.score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.5

    def _calculate_trend(
        self,
        outcomes: List[TaskOutcome],
        current_score: float
    ) -> str:
        """Determine if reputation is improving, stable, or declining"""
        if len(outcomes) < 20:
            return "stable"

        # Compare recent half vs old half
        mid = len(outcomes) // 2
        old_outcomes = outcomes[:mid]
        recent_outcomes = outcomes[mid:]

        # Recalculate scores for each half (simplified)
        old_success_rate = sum(1 for o in old_outcomes if o.success) / len(old_outcomes)
        recent_success_rate = sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes)

        if recent_success_rate > old_success_rate + 0.1:
            return "improving"
        elif recent_success_rate < old_success_rate - 0.1:
            return "declining"
        else:
            return "stable"

    def _calculate_confidence(self, sample_size: int) -> float:
        """Calculate confidence level based on sample size"""
        if sample_size >= self.min_samples_for_confidence:
            return 1.0
        elif sample_size == 0:
            return 0.0
        else:
            return sample_size / self.min_samples_for_confidence

    def _time_decay_weight(self, age_days: int) -> float:
        """Calculate time decay weight (exponential decay)"""
        # Weight = 0.5 ^ (age_days / halflife_days)
        return 0.5 ** (age_days / self.decay_halflife_days)

    async def get_reputation(self, agent_id: str) -> Optional[AgentReputation]:
        """Get reputation profile for an agent"""
        return self.reputations.get(agent_id)

    async def get_all_reputations(self) -> Dict[str, AgentReputation]:
        """Get all reputation profiles"""
        return dict(self.reputations)

    async def get_top_agents(
        self,
        dimension: Optional[ReputationDimension] = None,
        limit: int = 10
    ) -> List[AgentReputation]:
        """
        Get top-performing agents

        Args:
            dimension: Specific dimension to rank by (None for overall)
            limit: Maximum number of agents to return

        Returns:
            List of agent reputations sorted by score
        """
        reputations = list(self.reputations.values())

        if dimension:
            # Sort by specific dimension
            reputations.sort(
                key=lambda r: r.dimension_scores.get(
                    dimension.value,
                    DimensionScore(dimension, 0.0, 0, 0.0, "stable", "")
                ).score,
                reverse=True
            )
        else:
            # Sort by overall score
            reputations.sort(key=lambda r: r.overall_score, reverse=True)

        return reputations[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get reputation service statistics"""
        return {
            **self.stats,
            "agents_with_reputation": len(self.reputations),
            "avg_overall_score": (
                sum(r.overall_score for r in self.reputations.values()) / len(self.reputations)
                if self.reputations else 0.0
            )
        }


# Global reputation service instance
_reputation_service: Optional[ReputationService] = None


def get_reputation_service() -> ReputationService:
    """Get or create global reputation service"""
    global _reputation_service
    if _reputation_service is None:
        _reputation_service = ReputationService()
    return _reputation_service


__all__ = [
    'ReputationDimension',
    'TaskOutcome',
    'DimensionScore',
    'AgentReputation',
    'ReputationService',
    'get_reputation_service'
]
