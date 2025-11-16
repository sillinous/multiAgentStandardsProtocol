"""
Unit Tests for Temporal Agent Protocol (TAP) v1.0

Comprehensive tests ensuring:
- Temporal data models
- Timeline management
- Time-travel queries
- Causal inference
- What-if simulations
- Event tracking
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from superstandard.protocols.tap_v1 import (
    # Data models
    TimeRange,
    TemporalContext,
    TemporalEvent,
    DivergencePoint,
    TemporalMetadata,
    TemporalQuery,
    CausalInference,
    AlternativeAction,
    WhatIfSimulation,
    TimelineManagement,
    TemporalOperation,
    TemporalResponse,
    TAPMessage,

    # Enums
    TemporalResolution,
    TimelineState,
    CausalityModel,
    OperationType,
    QueryType,
    MergeStrategy,

    # Core classes
    Timeline,
    CausalityAnalyzer,
    TemporalEngine,
)


@pytest.mark.unit
class TestDataModels:
    """Test TAP data models."""

    def test_time_range_creation(self):
        """Test creating a time range."""
        time_range = TimeRange(
            start_time="2025-11-16T10:00:00Z",
            end_time="2025-11-16T14:00:00Z",
            inclusive=True
        )

        assert time_range.start_time == "2025-11-16T10:00:00Z"
        assert time_range.end_time == "2025-11-16T14:00:00Z"
        assert time_range.inclusive is True

    def test_time_range_contains(self):
        """Test time range containment check."""
        time_range = TimeRange(
            start_time="2025-11-16T10:00:00Z",
            end_time="2025-11-16T14:00:00Z"
        )

        assert time_range.contains("2025-11-16T12:00:00Z")
        assert time_range.contains("2025-11-16T10:00:00Z")  # inclusive
        assert time_range.contains("2025-11-16T14:00:00Z")  # inclusive
        assert not time_range.contains("2025-11-16T09:00:00Z")
        assert not time_range.contains("2025-11-16T15:00:00Z")

    def test_temporal_context_creation(self):
        """Test creating temporal context."""
        context = TemporalContext(
            current_time="2025-11-16T15:00:00Z",
            timeline_id="test_timeline",
            temporal_resolution=TemporalResolution.SECOND.value
        )

        assert context.timeline_id == "test_timeline"
        assert context.temporal_resolution == "second"

    def test_temporal_event_creation(self):
        """Test creating a temporal event."""
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T12:00:00Z",
            event_type="budget_allocation",
            agent_id="finance_agent",
            data={"amount": 1000000},
            causes=["evt_000"],
            causal_strength=0.9
        )

        assert event.event_id == "evt_001"
        assert event.event_type == "budget_allocation"
        assert event.agent_id == "finance_agent"
        assert len(event.causes) == 1
        assert event.causal_strength == 0.9

    def test_temporal_metadata_creation(self):
        """Test creating temporal metadata."""
        metadata = TemporalMetadata(
            timeline_state=TimelineState.STABLE.value,
            version=1,
            divergence_points=[
                DivergencePoint(
                    timestamp="2025-11-16T10:00:00Z",
                    reason="Alternative action taken"
                )
            ]
        )

        assert metadata.timeline_state == "stable"
        assert metadata.version == 1
        assert len(metadata.divergence_points) == 1

    def test_alternative_action_creation(self):
        """Test creating alternative action."""
        action = AlternativeAction(
            agent_id="budget_agent",
            action={"type": "allocate_budget"},
            parameters={"amount": 2000000}
        )

        assert action.agent_id == "budget_agent"
        assert action.action["type"] == "allocate_budget"
        assert action.parameters["amount"] == 2000000

    def test_what_if_simulation_creation(self):
        """Test creating what-if simulation."""
        simulation = WhatIfSimulation(
            fork_point="2025-11-16T10:00:00Z",
            alternative_action=AlternativeAction(
                agent_id="test_agent",
                action={"type": "test"},
                parameters={}
            ),
            simulation_horizon=3600,
            comparison_metrics=["roi", "risk_score"]
        )

        assert simulation.fork_point == "2025-11-16T10:00:00Z"
        assert simulation.simulation_horizon == 3600
        assert len(simulation.comparison_metrics) == 2

    def test_tap_message_creation(self):
        """Test creating TAP message."""
        message = TAPMessage(
            protocol="TAP",
            version="1.0.0",
            temporal_operation=TemporalOperation(
                operation_type=OperationType.TEMPORAL_QUERY.value,
                temporal_context=TemporalContext()
            )
        )

        assert message.protocol == "TAP"
        assert message.version == "1.0.0"
        assert message.temporal_operation is not None


@pytest.mark.unit
class TestTimeline:
    """Test Timeline functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timeline = Timeline(timeline_id="test_timeline")

    def test_timeline_creation(self):
        """Test creating a timeline."""
        assert self.timeline.timeline_id == "test_timeline"
        assert len(self.timeline.events) == 0
        assert len(self.timeline.events_by_time) == 0

    def test_add_event(self):
        """Test adding events to timeline."""
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T12:00:00Z",
            event_type="test_event"
        )

        self.timeline.add_event(event)

        assert len(self.timeline.events) == 1
        assert "evt_001" in self.timeline.events
        assert len(self.timeline.events_by_time) == 1

    def test_events_sorted_by_time(self):
        """Test that events are sorted by timestamp."""
        # Add events out of order
        event2 = TemporalEvent(
            event_id="evt_002",
            timestamp="2025-11-16T14:00:00Z",
            event_type="later_event"
        )
        event1 = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T12:00:00Z",
            event_type="earlier_event"
        )

        self.timeline.add_event(event2)
        self.timeline.add_event(event1)

        # Should be sorted
        assert self.timeline.events_by_time[0].event_id == "evt_001"
        assert self.timeline.events_by_time[1].event_id == "evt_002"

    def test_get_events_in_range(self):
        """Test querying events in a time range."""
        # Add events
        events = [
            TemporalEvent(
                event_id="evt_001",
                timestamp="2025-11-16T10:00:00Z",
                event_type="event1"
            ),
            TemporalEvent(
                event_id="evt_002",
                timestamp="2025-11-16T12:00:00Z",
                event_type="event2"
            ),
            TemporalEvent(
                event_id="evt_003",
                timestamp="2025-11-16T14:00:00Z",
                event_type="event3"
            )
        ]

        for event in events:
            self.timeline.add_event(event)

        # Query range
        time_range = TimeRange(
            start_time="2025-11-16T11:00:00Z",
            end_time="2025-11-16T13:00:00Z"
        )

        results = self.timeline.get_events_in_range(time_range)

        # Should only get evt_002
        assert len(results) == 1
        assert results[0].event_id == "evt_002"

    def test_record_and_query_state(self):
        """Test recording and querying state."""
        # Record state changes
        self.timeline.record_state(
            entity_id="budget",
            state={"amount": 1000000},
            timestamp="2025-11-16T10:00:00Z"
        )
        self.timeline.record_state(
            entity_id="budget",
            state={"amount": 1500000},
            timestamp="2025-11-16T12:00:00Z"
        )

        # Query state at different times
        state_10am = self.timeline.get_state_at_time(
            "budget",
            "2025-11-16T10:30:00Z"
        )
        state_1pm = self.timeline.get_state_at_time(
            "budget",
            "2025-11-16T13:00:00Z"
        )

        assert state_10am["amount"] == 1000000
        assert state_1pm["amount"] == 1500000

    def test_fork_timeline(self):
        """Test forking a timeline."""
        # Add some events to parent
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T10:00:00Z",
            event_type="parent_event"
        )
        self.timeline.add_event(event)

        # Fork the timeline
        fork_point = "2025-11-16T12:00:00Z"
        forked = self.timeline.fork("forked_timeline", fork_point)

        assert forked.timeline_id == "forked_timeline"
        assert forked.parent_timeline == self.timeline
        assert forked.fork_point == fork_point

    def test_forked_timeline_inherits_parent_state(self):
        """Test that forked timeline can access parent state."""
        # Record state in parent
        self.timeline.record_state(
            entity_id="data",
            state={"value": 100},
            timestamp="2025-11-16T10:00:00Z"
        )

        # Fork after state was recorded
        forked = self.timeline.fork(
            "forked_timeline",
            fork_point="2025-11-16T12:00:00Z"
        )

        # Query state from before fork point
        state = forked.get_state_at_time("data", "2025-11-16T11:00:00Z")

        assert state is not None
        assert state["value"] == 100


@pytest.mark.unit
class TestCausalityAnalyzer:
    """Test causality analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CausalityAnalyzer()

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        assert self.analyzer is not None

    def test_temporal_precedence(self):
        """Test that causes must precede effects."""
        effect = TemporalEvent(
            event_id="effect",
            timestamp="2025-11-16T12:00:00Z",
            event_type="revenue_increase"
        )

        # Cause after effect (invalid)
        invalid_cause = TemporalEvent(
            event_id="invalid_cause",
            timestamp="2025-11-16T13:00:00Z",
            event_type="marketing_campaign"
        )

        # Valid cause before effect
        valid_cause = TemporalEvent(
            event_id="valid_cause",
            timestamp="2025-11-16T11:00:00Z",
            event_type="marketing_campaign"
        )

        results = self.analyzer.infer_causality(
            effect,
            [invalid_cause, valid_cause],
            threshold=0.0
        )

        # Should only find valid_cause
        assert len(results) >= 1
        assert all(event.event_id != "invalid_cause" for event, _ in results)

    def test_same_agent_causality_boost(self):
        """Test that same agent increases causal confidence."""
        effect = TemporalEvent(
            event_id="effect",
            timestamp="2025-11-16T12:00:00Z",
            event_type="task_complete",
            agent_id="agent_1"
        )

        same_agent_cause = TemporalEvent(
            event_id="same_agent",
            timestamp="2025-11-16T11:00:00Z",
            event_type="task_start",
            agent_id="agent_1"
        )

        different_agent_cause = TemporalEvent(
            event_id="different_agent",
            timestamp="2025-11-16T11:00:00Z",
            event_type="task_start",
            agent_id="agent_2"
        )

        results = self.analyzer.infer_causality(
            effect,
            [same_agent_cause, different_agent_cause],
            threshold=0.0
        )

        # Find the same_agent result
        same_agent_result = next(
            (r for r in results if r[0].event_id == "same_agent"),
            None
        )
        different_agent_result = next(
            (r for r in results if r[0].event_id == "different_agent"),
            None
        )

        # Same agent should have higher confidence
        if same_agent_result and different_agent_result:
            assert same_agent_result[1] > different_agent_result[1]

    def test_temporal_proximity_boost(self):
        """Test that temporal proximity increases confidence."""
        effect = TemporalEvent(
            event_id="effect",
            timestamp="2025-11-16T12:00:00Z",
            event_type="result"
        )

        recent_cause = TemporalEvent(
            event_id="recent",
            timestamp="2025-11-16T11:59:00Z",  # 1 minute before
            event_type="action"
        )

        distant_cause = TemporalEvent(
            event_id="distant",
            timestamp="2025-11-16T08:00:00Z",  # 4 hours before
            event_type="action"
        )

        results = self.analyzer.infer_causality(
            effect,
            [recent_cause, distant_cause],
            threshold=0.0
        )

        recent_result = next(
            (r for r in results if r[0].event_id == "recent"),
            None
        )
        distant_result = next(
            (r for r in results if r[0].event_id == "distant"),
            None
        )

        # Recent cause should have higher confidence
        if recent_result and distant_result:
            assert recent_result[1] > distant_result[1]

    def test_build_causal_chain(self):
        """Test building causal chains."""
        # Create chain: A -> B -> C
        events = {
            "A": TemporalEvent(
                event_id="A",
                timestamp="2025-11-16T10:00:00Z",
                event_type="start",
                causes=[]
            ),
            "B": TemporalEvent(
                event_id="B",
                timestamp="2025-11-16T11:00:00Z",
                event_type="middle",
                causes=["A"]
            ),
            "C": TemporalEvent(
                event_id="C",
                timestamp="2025-11-16T12:00:00Z",
                event_type="end",
                causes=["B"]
            )
        }

        chains = self.analyzer.build_causal_chain("C", events, max_depth=5)

        # Should find chain: C -> B -> A
        assert len(chains) >= 1
        # Chain should contain all three events
        assert any(len(chain) == 3 for chain in chains)


@pytest.mark.unit
class TestTemporalEngine:
    """Test temporal engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TemporalEngine()

    def test_engine_initialization(self):
        """Test engine initialization."""
        assert self.engine is not None
        assert "main" in self.engine.timelines

    def test_create_timeline(self):
        """Test creating a timeline."""
        timeline = self.engine.create_timeline("test_timeline")

        assert timeline.timeline_id == "test_timeline"
        assert "test_timeline" in self.engine.timelines

    def test_create_duplicate_timeline_fails(self):
        """Test that creating duplicate timeline raises error."""
        self.engine.create_timeline("test")

        with pytest.raises(ValueError):
            self.engine.create_timeline("test")

    def test_fork_timeline(self):
        """Test forking a timeline."""
        # Add event to main timeline
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T10:00:00Z",
            event_type="test"
        )
        self.engine.add_event("main", event)

        # Fork the timeline
        forked = self.engine.fork_timeline(
            "main",
            "forked",
            fork_point="2025-11-16T12:00:00Z"
        )

        assert forked.timeline_id == "forked"
        assert "forked" in self.engine.timelines

    def test_add_and_query_event(self):
        """Test adding and querying events."""
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T12:00:00Z",
            event_type="test_event"
        )

        self.engine.add_event("main", event)

        # Query events in range
        time_range = TimeRange(
            start_time="2025-11-16T11:00:00Z",
            end_time="2025-11-16T13:00:00Z"
        )

        events = self.engine.events_in_range("main", time_range)

        assert len(events) >= 1
        assert any(e.event_id == "evt_001" for e in events)

    def test_state_at_time(self):
        """Test querying state at a specific time."""
        # Record state changes
        self.engine.record_state(
            "main",
            "entity_1",
            {"value": 100},
            "2025-11-16T10:00:00Z"
        )
        self.engine.record_state(
            "main",
            "entity_1",
            {"value": 200},
            "2025-11-16T12:00:00Z"
        )

        # Query at different times
        state_11am = self.engine.state_at_time(
            "main",
            "entity_1",
            "2025-11-16T11:00:00Z"
        )
        state_1pm = self.engine.state_at_time(
            "main",
            "entity_1",
            "2025-11-16T13:00:00Z"
        )

        assert state_11am["value"] == 100
        assert state_1pm["value"] == 200

    def test_causal_chain_query(self):
        """Test querying causal chains."""
        # Create chain of events
        events = [
            TemporalEvent(
                event_id="evt_1",
                timestamp="2025-11-16T10:00:00Z",
                event_type="start",
                causes=[]
            ),
            TemporalEvent(
                event_id="evt_2",
                timestamp="2025-11-16T11:00:00Z",
                event_type="middle",
                causes=["evt_1"]
            ),
            TemporalEvent(
                event_id="evt_3",
                timestamp="2025-11-16T12:00:00Z",
                event_type="end",
                causes=["evt_2"]
            )
        ]

        for event in events:
            self.engine.add_event("main", event)

        # Query causal chain
        chains = self.engine.causal_chain("main", "evt_3", max_depth=5)

        assert len(chains) >= 1

    def test_infer_causality(self):
        """Test causality inference."""
        # Add events
        effect = TemporalEvent(
            event_id="effect",
            timestamp="2025-11-16T12:00:00Z",
            event_type="revenue_spike",
            agent_id="sales_agent"
        )

        cause1 = TemporalEvent(
            event_id="cause1",
            timestamp="2025-11-16T11:00:00Z",
            event_type="marketing_campaign",
            agent_id="marketing_agent"
        )

        cause2 = TemporalEvent(
            event_id="cause2",
            timestamp="2025-11-16T10:00:00Z",
            event_type="product_launch",
            agent_id="product_agent"
        )

        self.engine.add_event("main", effect)
        self.engine.add_event("main", cause1)
        self.engine.add_event("main", cause2)

        # Infer causality
        results = self.engine.infer_causality(
            "main",
            "effect",
            ["cause1", "cause2"],
            threshold=0.0
        )

        # Should find some causal relationships
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_what_if_simulation(self):
        """Test what-if simulation."""
        # Add some history
        event = TemporalEvent(
            event_id="evt_001",
            timestamp="2025-11-16T09:00:00Z",
            event_type="initial_state"
        )
        self.engine.add_event("main", event)

        # Run what-if simulation
        alternative = AlternativeAction(
            agent_id="test_agent",
            action={"type": "alternative_action"},
            parameters={"param": "value"}
        )

        results = await self.engine.what_if_simulation(
            timeline_id="main",
            fork_point="2025-11-16T10:00:00Z",
            alternative_action=alternative,
            simulation_horizon=3600,
            comparison_metrics=["metric1", "metric2"]
        )

        assert "simulation_timeline" in results
        assert results["original_timeline"] == "main"
        assert results["fork_point"] == "2025-11-16T10:00:00Z"


@pytest.mark.unit
class TestTAPIntegration:
    """Integration tests for TAP."""

    def test_full_time_travel_workflow(self):
        """Test complete time-travel debugging workflow."""
        engine = TemporalEngine()

        # Simulate agent execution with state changes
        timeline_id = "execution_timeline"
        engine.create_timeline(timeline_id)

        # Record execution events
        events = [
            TemporalEvent(
                event_id="start",
                timestamp="2025-11-16T10:00:00Z",
                event_type="execution_start",
                agent_id="test_agent",
                data={"state": "initializing"}
            ),
            TemporalEvent(
                event_id="process",
                timestamp="2025-11-16T10:05:00Z",
                event_type="processing",
                agent_id="test_agent",
                data={"state": "processing", "items": 100},
                causes=["start"]
            ),
            TemporalEvent(
                event_id="error",
                timestamp="2025-11-16T10:10:00Z",
                event_type="error_occurred",
                agent_id="test_agent",
                data={"state": "error", "error": "OutOfMemory"},
                causes=["process"]
            )
        ]

        for event in events:
            engine.add_event(timeline_id, event)

        # Record state changes
        engine.record_state(
            timeline_id,
            "agent_memory",
            {"used_mb": 100},
            "2025-11-16T10:00:00Z"
        )
        engine.record_state(
            timeline_id,
            "agent_memory",
            {"used_mb": 800},
            "2025-11-16T10:05:00Z"
        )
        engine.record_state(
            timeline_id,
            "agent_memory",
            {"used_mb": 1024},
            "2025-11-16T10:10:00Z"
        )

        # Time-travel: check state before error
        state_before_error = engine.state_at_time(
            timeline_id,
            "agent_memory",
            "2025-11-16T10:08:00Z"
        )

        assert state_before_error["used_mb"] == 800

        # Find causal chain leading to error
        chains = engine.causal_chain(timeline_id, "error", max_depth=5)

        assert len(chains) >= 1
        # Chain should include start -> process -> error
        assert any("process" in chain and "start" in chain for chain in chains)

    @pytest.mark.asyncio
    async def test_what_if_alternative_timeline(self):
        """Test what-if simulation creating alternative timeline."""
        engine = TemporalEngine()

        # Set up initial state
        engine.record_state(
            "main",
            "budget",
            {"allocated": 1000000, "spent": 0},
            "2025-11-16T09:00:00Z"
        )

        # Record normal execution
        event = TemporalEvent(
            event_id="allocation_1",
            timestamp="2025-11-16T10:00:00Z",
            event_type="budget_allocation",
            data={"amount": 500000, "project": "A"}
        )
        engine.add_event("main", event)

        # Run what-if: allocate differently
        alternative = AlternativeAction(
            agent_id="budget_agent",
            action={"type": "allocate_budget"},
            parameters={"amount": 750000, "project": "B"}
        )

        results = await engine.what_if_simulation(
            timeline_id="main",
            fork_point="2025-11-16T10:00:00Z",
            alternative_action=alternative,
            simulation_horizon=3600,
            comparison_metrics=["roi", "risk"]
        )

        # Verify simulation created alternative timeline
        assert "simulation_timeline" in results
        sim_timeline_id = results["simulation_timeline"]
        assert sim_timeline_id in engine.timelines

    def test_tap_message_roundtrip(self):
        """Test TAP message serialization."""
        message = TAPMessage(
            protocol="TAP",
            version="1.0.0",
            temporal_query=TemporalQuery(
                query_type=QueryType.STATE_AT_TIME.value,
                query_time="2025-11-16T12:00:00Z",
                entity_id="test_entity"
            )
        )

        data = message.to_dict()

        assert data['protocol'] == "TAP"
        assert data['version'] == "1.0.0"
        assert 'temporal_query' in data
        assert data['temporal_query']['query_type'] == "state_at_time"
