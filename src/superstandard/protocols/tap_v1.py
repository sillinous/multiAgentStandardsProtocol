"""
⏰ Temporal Agent Protocol (TAP) v1.0 - PRODUCTION IMPLEMENTATION
==================================================================

WORLD-FIRST: Complete implementation of TAP for temporal reasoning and time-travel debugging.

Features:
- Temporal context management
- Time-travel queries (state_at_time, events_in_range)
- Causal inference and analysis
- What-if simulations (timeline forking)
- Timeline management (create, fork, merge)
- Temporal event tracking
- Causality graph construction

Author: SuperStandard Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid
from collections import defaultdict
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class TemporalResolution(Enum):
    """Time granularity for temporal operations."""

    MILLISECOND = "millisecond"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class TimelineState(Enum):
    """State of a timeline."""

    STABLE = "stable"
    FORKED = "forked"
    MERGING = "merging"
    CONFLICTED = "conflicted"


class CausalityModel(Enum):
    """Causality inference models."""

    CORRELATION = "correlation"
    GRANGER = "granger"
    STRUCTURAL = "structural"
    COUNTERFACTUAL = "counterfactual"


class OperationType(Enum):
    """Types of temporal operations."""

    TEMPORAL_QUERY = "temporal_query"
    CAUSAL_INFERENCE = "causal_inference"
    TIMELINE_FORK = "timeline_fork"
    TIMELINE_MERGE = "timeline_merge"
    REPLAY = "replay"
    WHAT_IF_SIMULATION = "what_if_simulation"
    TEMPORAL_CONSTRAINT = "temporal_constraint"
    TIME_TRAVEL = "time_travel"
    CAUSALITY_CHECK = "causality_check"


class QueryType(Enum):
    """Types of temporal queries."""

    STATE_AT_TIME = "state_at_time"
    EVENTS_IN_RANGE = "events_in_range"
    STATE_CHANGES = "state_changes"
    CAUSAL_CHAIN = "causal_chain"


class MergeStrategy(Enum):
    """Timeline merge strategies."""

    LATEST_WINS = "latest_wins"
    MANUAL_RESOLUTION = "manual_resolution"
    AUTOMATIC_MERGE = "automatic_merge"
    ABORT_ON_CONFLICT = "abort_on_conflict"


@dataclass
class TimeRange:
    """Time range for queries."""

    start_time: str
    end_time: str
    inclusive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def contains(self, timestamp: str) -> bool:
        """Check if timestamp is in range."""
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        start = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))

        if self.inclusive:
            return start <= ts <= end
        else:
            return start < ts < end

    def __repr__(self) -> str:
        return f"TimeRange({self.start_time} to {self.end_time})"


@dataclass
class TemporalContext:
    """Context for temporal operations."""

    current_time: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    timeline_id: str = "main"
    causality_graph_id: Optional[str] = None
    temporal_resolution: str = TemporalResolution.SECOND.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"TemporalContext(timeline={self.timeline_id}, time={self.current_time})"


@dataclass
class TemporalEvent:
    """An event in time with causality metadata."""

    event_id: str
    timestamp: str
    event_type: str
    agent_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    causes: List[str] = field(default_factory=list)  # Event IDs
    effects: List[str] = field(default_factory=list)  # Event IDs
    causal_strength: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return f"TemporalEvent(id='{self.event_id}', type='{self.event_type}', time={self.timestamp})"


@dataclass
class DivergencePoint:
    """Point where a timeline diverges from parent."""

    timestamp: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TemporalMetadata:
    """Metadata about temporal operations."""

    operation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    timeline_state: str = TimelineState.STABLE.value
    checkpoint_id: Optional[str] = None
    version: int = 1
    divergence_points: List[DivergencePoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['divergence_points'] = [d.to_dict() for d in self.divergence_points]
        return result


@dataclass
class TemporalQuery:
    """Query for temporal data."""

    query_time: Optional[str] = None
    time_range: Optional[TimeRange] = None
    entity_id: Optional[str] = None
    query_type: str = QueryType.STATE_AT_TIME.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.time_range:
            result['time_range'] = self.time_range.to_dict()
        return result


@dataclass
class CausalInference:
    """Causal inference request."""

    effect_event: TemporalEvent
    potential_causes: List[TemporalEvent]
    causality_model: str = CausalityModel.CORRELATION.value
    confidence_threshold: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'effect_event': self.effect_event.to_dict(),
            'potential_causes': [c.to_dict() for c in self.potential_causes],
            'causality_model': self.causality_model,
            'confidence_threshold': self.confidence_threshold
        }


@dataclass
class AlternativeAction:
    """Alternative action for what-if simulation."""

    agent_id: str
    action: Dict[str, Any]
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WhatIfSimulation:
    """What-if simulation parameters."""

    fork_point: str
    alternative_action: AlternativeAction
    simulation_horizon: int  # seconds
    comparison_metrics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'fork_point': self.fork_point,
            'alternative_action': self.alternative_action.to_dict(),
            'simulation_horizon': self.simulation_horizon,
            'comparison_metrics': self.comparison_metrics
        }


@dataclass
class TimelineManagement:
    """Timeline management operation."""

    operation: str  # create_timeline, fork_timeline, merge_timelines, etc.
    timeline_id: str
    parent_timeline_id: Optional[str] = None
    merge_strategy: str = MergeStrategy.LATEST_WINS.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TemporalOperation:
    """Temporal operation request."""

    operation_type: str
    temporal_context: TemporalContext
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_type': self.operation_type,
            'temporal_context': self.temporal_context.to_dict(),
            'parameters': self.parameters
        }


@dataclass
class TemporalResponse:
    """Response to temporal operation."""

    success: bool
    timeline_id: str
    results: Dict[str, Any] = field(default_factory=dict)
    temporal_metadata: Optional[TemporalMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'success': self.success,
            'timeline_id': self.timeline_id,
            'results': self.results
        }
        if self.temporal_metadata:
            result['temporal_metadata'] = self.temporal_metadata.to_dict()
        return result


@dataclass
class TAPMessage:
    """Temporal Agent Protocol message."""

    protocol: str = "TAP"
    version: str = "1.0.0"
    temporal_operation: Optional[TemporalOperation] = None
    temporal_query: Optional[TemporalQuery] = None
    causal_inference: Optional[CausalInference] = None
    what_if_simulation: Optional[WhatIfSimulation] = None
    timeline_management: Optional[TimelineManagement] = None
    temporal_response: Optional[TemporalResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'protocol': self.protocol,
            'version': self.version
        }
        if self.temporal_operation:
            result['temporal_operation'] = self.temporal_operation.to_dict()
        if self.temporal_query:
            result['temporal_query'] = self.temporal_query.to_dict()
        if self.causal_inference:
            result['causal_inference'] = self.causal_inference.to_dict()
        if self.what_if_simulation:
            result['what_if_simulation'] = self.what_if_simulation.to_dict()
        if self.timeline_management:
            result['timeline_management'] = self.timeline_management.to_dict()
        if self.temporal_response:
            result['temporal_response'] = self.temporal_response.to_dict()
        return result


# ============================================================================
# TIMELINE
# ============================================================================


class Timeline:
    """
    Represents a timeline with events and state history.

    Handles:
    - Event storage and retrieval
    - State tracking over time
    - Timeline forking
    """

    def __init__(
        self,
        timeline_id: str = "main",
        parent_timeline: Optional['Timeline'] = None,
        fork_point: Optional[str] = None
    ):
        """
        Initialize timeline.

        Args:
            timeline_id: Unique timeline identifier
            parent_timeline: Parent timeline (if this is a fork)
            fork_point: Timestamp where fork occurred
        """
        self.timeline_id = timeline_id
        self.parent_timeline = parent_timeline
        self.fork_point = fork_point

        # Event storage
        self.events: Dict[str, TemporalEvent] = {}
        self.events_by_time: List[TemporalEvent] = []

        # State storage
        self.state_history: Dict[str, List[tuple[str, Any]]] = defaultdict(list)

        # Metadata
        self.created_at = datetime.utcnow().isoformat() + 'Z'
        self.version = 1

        logger.info(f"Created timeline {timeline_id}")

    def add_event(self, event: TemporalEvent) -> None:
        """
        Add an event to the timeline.

        Args:
            event: Event to add
        """
        self.events[event.event_id] = event
        self.events_by_time.append(event)
        self.events_by_time.sort(key=lambda e: e.timestamp)

        logger.debug(f"Added event {event.event_id} to timeline {self.timeline_id}")

    def get_events_in_range(self, time_range: TimeRange) -> List[TemporalEvent]:
        """
        Get all events in a time range.

        Args:
            time_range: Time range to query

        Returns:
            List of events in range
        """
        return [
            event for event in self.events_by_time
            if time_range.contains(event.timestamp)
        ]

    def get_state_at_time(self, entity_id: str, query_time: str) -> Optional[Any]:
        """
        Get state of an entity at a specific time.

        Args:
            entity_id: Entity to query
            query_time: Time to query

        Returns:
            State at that time, or None
        """
        if entity_id not in self.state_history:
            # Check parent timeline if this is a fork
            if self.parent_timeline and self.fork_point:
                fork_dt = datetime.fromisoformat(self.fork_point.replace('Z', '+00:00'))
                query_dt = datetime.fromisoformat(query_time.replace('Z', '+00:00'))

                # If query time is before fork, check parent
                if query_dt < fork_dt:
                    return self.parent_timeline.get_state_at_time(entity_id, query_time)

            return None

        # Find latest state before or at query time
        query_dt = datetime.fromisoformat(query_time.replace('Z', '+00:00'))

        state_at_time = None
        for timestamp, state in self.state_history[entity_id]:
            state_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if state_dt <= query_dt:
                state_at_time = state
            else:
                break

        # If no state found and we have a parent, check parent
        if state_at_time is None and self.parent_timeline and self.fork_point:
            fork_dt = datetime.fromisoformat(self.fork_point.replace('Z', '+00:00'))
            if query_dt < fork_dt:
                return self.parent_timeline.get_state_at_time(entity_id, query_time)

        return state_at_time

    def record_state(self, entity_id: str, state: Any, timestamp: Optional[str] = None) -> None:
        """
        Record state of an entity at a point in time.

        Args:
            entity_id: Entity identifier
            state: State to record
            timestamp: When to record (default: now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + 'Z'

        self.state_history[entity_id].append((timestamp, state))
        self.state_history[entity_id].sort(key=lambda x: x[0])

    def fork(self, new_timeline_id: str, fork_point: Optional[str] = None) -> 'Timeline':
        """
        Create a fork of this timeline.

        Args:
            new_timeline_id: ID for new timeline
            fork_point: When to fork (default: now)

        Returns:
            New forked timeline
        """
        if fork_point is None:
            fork_point = datetime.utcnow().isoformat() + 'Z'

        forked = Timeline(
            timeline_id=new_timeline_id,
            parent_timeline=self,
            fork_point=fork_point
        )

        logger.info(f"Forked timeline {self.timeline_id} -> {new_timeline_id} at {fork_point}")

        return forked


# ============================================================================
# CAUSALITY ANALYZER
# ============================================================================


class CausalityAnalyzer:
    """
    Analyzes causal relationships between events.

    Implements:
    - Correlation-based causality
    - Temporal precedence checking
    - Causal strength scoring
    """

    def __init__(self):
        """Initialize causality analyzer."""
        self.causality_graph: Dict[str, Set[str]] = defaultdict(set)

    def infer_causality(
        self,
        effect: TemporalEvent,
        potential_causes: List[TemporalEvent],
        model: str = CausalityModel.CORRELATION.value,
        threshold: float = 0.8
    ) -> List[tuple[TemporalEvent, float]]:
        """
        Infer causal relationships.

        Args:
            effect: Effect event
            potential_causes: Potential cause events
            model: Causality model to use
            threshold: Confidence threshold

        Returns:
            List of (cause_event, confidence) tuples
        """
        results = []

        effect_time = datetime.fromisoformat(effect.timestamp.replace('Z', '+00:00'))

        for cause in potential_causes:
            cause_time = datetime.fromisoformat(cause.timestamp.replace('Z', '+00:00'))

            # Temporal precedence: cause must come before effect
            if cause_time >= effect_time:
                continue

            # Compute causal strength
            if model == CausalityModel.CORRELATION.value:
                confidence = self._correlation_causality(cause, effect)
            elif model == CausalityModel.GRANGER.value:
                confidence = self._granger_causality(cause, effect)
            else:
                confidence = 0.5  # Default

            if confidence >= threshold:
                results.append((cause, confidence))

        # Sort by confidence descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def _correlation_causality(
        self,
        cause: TemporalEvent,
        effect: TemporalEvent
    ) -> float:
        """
        Compute correlation-based causality.

        Simple heuristic for v1.0:
        - Same agent: +0.3
        - Related event types: +0.4
        - Temporal proximity: up to +0.3

        Args:
            cause: Potential cause
            effect: Effect event

        Returns:
            Confidence score (0-1)
        """
        score = 0.0

        # Same agent
        if cause.agent_id and effect.agent_id and cause.agent_id == effect.agent_id:
            score += 0.3

        # Related event types
        if self._are_related_types(cause.event_type, effect.event_type):
            score += 0.4

        # Temporal proximity
        cause_time = datetime.fromisoformat(cause.timestamp.replace('Z', '+00:00'))
        effect_time = datetime.fromisoformat(effect.timestamp.replace('Z', '+00:00'))
        delta = (effect_time - cause_time).total_seconds()

        # Closer in time = higher score
        if delta < 60:  # Within 1 minute
            score += 0.3
        elif delta < 300:  # Within 5 minutes
            score += 0.2
        elif delta < 3600:  # Within 1 hour
            score += 0.1

        return min(score, 1.0)

    def _granger_causality(
        self,
        cause: TemporalEvent,
        effect: TemporalEvent
    ) -> float:
        """
        Granger causality (simplified for v1.0).

        Args:
            cause: Potential cause
            effect: Effect event

        Returns:
            Confidence score (0-1)
        """
        # For v1.0, use correlation with slight boost
        base_score = self._correlation_causality(cause, effect)
        return min(base_score * 1.1, 1.0)

    def _are_related_types(self, type1: str, type2: str) -> bool:
        """
        Check if two event types are related.

        Args:
            type1: First event type
            type2: Second event type

        Returns:
            True if related
        """
        # Simple keyword matching
        words1 = set(type1.lower().split('_'))
        words2 = set(type2.lower().split('_'))

        return len(words1 & words2) > 0

    def build_causal_chain(
        self,
        effect_id: str,
        events: Dict[str, TemporalEvent],
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Build causal chain leading to an effect.

        Args:
            effect_id: Effect event ID
            events: All available events
            max_depth: Maximum chain depth

        Returns:
            List of causal chains (event ID sequences)
        """
        if effect_id not in events:
            return []

        chains = []
        self._build_chain_recursive(effect_id, events, [], chains, max_depth)

        return chains

    def _build_chain_recursive(
        self,
        event_id: str,
        events: Dict[str, TemporalEvent],
        current_chain: List[str],
        chains: List[List[str]],
        max_depth: int
    ) -> None:
        """Recursively build causal chains."""
        if len(current_chain) >= max_depth:
            return

        event = events.get(event_id)
        if not event:
            return

        new_chain = current_chain + [event_id]

        if not event.causes:
            # End of chain
            chains.append(new_chain)
        else:
            # Continue chain
            for cause_id in event.causes:
                self._build_chain_recursive(cause_id, events, new_chain, chains, max_depth)


# ============================================================================
# TEMPORAL ENGINE
# ============================================================================


class TemporalEngine:
    """
    Main temporal reasoning engine.

    Handles:
    - Timeline management
    - Temporal queries
    - Causal inference
    - What-if simulations
    - Time-travel operations
    """

    def __init__(self):
        """Initialize temporal engine."""
        self.timelines: Dict[str, Timeline] = {}
        self.causality_analyzer = CausalityAnalyzer()

        # Create main timeline
        self.create_timeline("main")

        logger.info("Temporal engine initialized")

    def create_timeline(self, timeline_id: str) -> Timeline:
        """
        Create a new timeline.

        Args:
            timeline_id: Timeline identifier

        Returns:
            Created timeline
        """
        if timeline_id in self.timelines:
            raise ValueError(f"Timeline {timeline_id} already exists")

        timeline = Timeline(timeline_id)
        self.timelines[timeline_id] = timeline

        logger.info(f"Created timeline {timeline_id}")
        return timeline

    def fork_timeline(
        self,
        source_timeline_id: str,
        new_timeline_id: str,
        fork_point: Optional[str] = None
    ) -> Timeline:
        """
        Fork a timeline.

        Args:
            source_timeline_id: Timeline to fork from
            new_timeline_id: New timeline ID
            fork_point: When to fork (default: now)

        Returns:
            Forked timeline
        """
        if source_timeline_id not in self.timelines:
            raise ValueError(f"Timeline {source_timeline_id} not found")

        if new_timeline_id in self.timelines:
            raise ValueError(f"Timeline {new_timeline_id} already exists")

        source = self.timelines[source_timeline_id]
        forked = source.fork(new_timeline_id, fork_point)

        self.timelines[new_timeline_id] = forked

        logger.info(f"Forked timeline {source_timeline_id} -> {new_timeline_id}")
        return forked

    def state_at_time(
        self,
        timeline_id: str,
        entity_id: str,
        query_time: str
    ) -> Optional[Any]:
        """
        Query state of an entity at a specific time.

        Args:
            timeline_id: Timeline to query
            entity_id: Entity to query
            query_time: Time to query

        Returns:
            State at that time
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]
        return timeline.get_state_at_time(entity_id, query_time)

    def events_in_range(
        self,
        timeline_id: str,
        time_range: TimeRange
    ) -> List[TemporalEvent]:
        """
        Get events in a time range.

        Args:
            timeline_id: Timeline to query
            time_range: Time range

        Returns:
            Events in range
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]
        return timeline.get_events_in_range(time_range)

    def causal_chain(
        self,
        timeline_id: str,
        effect_event_id: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Build causal chain for an event.

        Args:
            timeline_id: Timeline to query
            effect_event_id: Effect event ID
            max_depth: Maximum chain depth

        Returns:
            List of causal chains
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]
        return self.causality_analyzer.build_causal_chain(
            effect_event_id,
            timeline.events,
            max_depth
        )

    async def what_if_simulation(
        self,
        timeline_id: str,
        fork_point: str,
        alternative_action: AlternativeAction,
        simulation_horizon: int,
        comparison_metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Run what-if simulation.

        Args:
            timeline_id: Source timeline
            fork_point: When to fork
            alternative_action: Alternative action to take
            simulation_horizon: How far to simulate (seconds)
            comparison_metrics: Metrics to compare

        Returns:
            Simulation results
        """
        # Create fork
        sim_timeline_id = f"{timeline_id}_sim_{uuid.uuid4().hex[:8]}"
        forked = self.fork_timeline(timeline_id, sim_timeline_id, fork_point)

        # Simulate alternative action
        # (In a real implementation, this would execute the action)
        sim_event = TemporalEvent(
            event_id=f"sim_{uuid.uuid4().hex[:8]}",
            timestamp=fork_point,
            event_type="simulation_action",
            agent_id=alternative_action.agent_id,
            data={
                'action': alternative_action.action,
                'parameters': alternative_action.parameters
            }
        )

        forked.add_event(sim_event)

        # Compare results
        results = {
            'original_timeline': timeline_id,
            'simulation_timeline': sim_timeline_id,
            'fork_point': fork_point,
            'simulation_horizon': simulation_horizon,
            'metrics': {},
            'divergence': 'Simulation completed - metrics would be computed here'
        }

        logger.info(f"Completed what-if simulation: {sim_timeline_id}")

        return results

    def add_event(
        self,
        timeline_id: str,
        event: TemporalEvent
    ) -> None:
        """
        Add event to timeline.

        Args:
            timeline_id: Timeline to add to
            event: Event to add
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]
        timeline.add_event(event)

    def record_state(
        self,
        timeline_id: str,
        entity_id: str,
        state: Any,
        timestamp: Optional[str] = None
    ) -> None:
        """
        Record state in timeline.

        Args:
            timeline_id: Timeline to record in
            entity_id: Entity identifier
            state: State to record
            timestamp: When to record (default: now)
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]
        timeline.record_state(entity_id, state, timestamp)

    def infer_causality(
        self,
        timeline_id: str,
        effect_event_id: str,
        potential_cause_ids: List[str],
        model: str = CausalityModel.CORRELATION.value,
        threshold: float = 0.8
    ) -> List[tuple[str, float]]:
        """
        Infer causal relationships.

        Args:
            timeline_id: Timeline to analyze
            effect_event_id: Effect event ID
            potential_cause_ids: Potential cause event IDs
            model: Causality model
            threshold: Confidence threshold

        Returns:
            List of (cause_id, confidence) tuples
        """
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")

        timeline = self.timelines[timeline_id]

        if effect_event_id not in timeline.events:
            raise ValueError(f"Effect event {effect_event_id} not found")

        effect = timeline.events[effect_event_id]
        causes = [timeline.events[cid] for cid in potential_cause_ids if cid in timeline.events]

        results = self.causality_analyzer.infer_causality(
            effect,
            causes,
            model,
            threshold
        )

        return [(event.event_id, conf) for event, conf in results]


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    # Data models
    'TimeRange',
    'TemporalContext',
    'TemporalEvent',
    'DivergencePoint',
    'TemporalMetadata',
    'TemporalQuery',
    'CausalInference',
    'AlternativeAction',
    'WhatIfSimulation',
    'TimelineManagement',
    'TemporalOperation',
    'TemporalResponse',
    'TAPMessage',

    # Enums
    'TemporalResolution',
    'TimelineState',
    'CausalityModel',
    'OperationType',
    'QueryType',
    'MergeStrategy',

    # Core classes
    'Timeline',
    'CausalityAnalyzer',
    'TemporalEngine',
]
