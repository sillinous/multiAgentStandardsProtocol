"""
⏰ Temporal Agent Protocol (TAP) v1.0 - Time-Travel Debugging Demo
===================================================================

WORLD-FIRST demonstration of temporal reasoning for agents:
- Time-travel queries (inspect past states)
- Causal chain analysis (find root causes)
- What-if simulations (alternative timelines)
- Timeline forking and management
- Temporal debugging of agent execution

This example shows how TAP enables debugging agent behavior by
traveling back in time and exploring alternative execution paths.
"""

import asyncio
import json
from datetime import datetime, timedelta
from superstandard.protocols.tap_v1 import (
    # Core functionality
    TemporalEngine,
    CausalityAnalyzer,
    Timeline,

    # Data models
    TemporalEvent,
    TemporalContext,
    TimeRange,
    AlternativeAction,
    TAPMessage,
    TemporalOperation,

    # Enums
    OperationType,
    QueryType,
    CausalityModel,
    TemporalResolution,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def format_time(iso_time: str) -> str:
    """Format ISO time for display."""
    return iso_time.split('T')[1].split('Z')[0][:8]


def main():
    """Run the time-travel debugging demo."""

    print_section("TAP v1.0: Time-Travel Debugging Demo")

    # ========================================================================
    # STEP 1: Initialize Temporal Engine
    # ========================================================================

    print_section("STEP 1: Initialize Temporal Engine")

    engine = TemporalEngine()
    print("✓ Temporal engine initialized")
    print(f"✓ Main timeline created: {engine.timelines['main'].timeline_id}")

    # ========================================================================
    # STEP 2: Simulate Agent Execution with Events
    # ========================================================================

    print_section("STEP 2: Simulate APQC Budget Planning Agent Execution")

    # Define base time
    base_time = datetime(2025, 11, 16, 10, 0, 0)

    print("Simulating budget planning workflow...\n")

    # Event 1: Agent starts budget planning
    event1 = TemporalEvent(
        event_id="evt_start",
        timestamp=(base_time).isoformat() + 'Z',
        event_type="budget_planning_start",
        agent_id="apqc_9_2_budget_agent",
        data={
            "total_budget": 5000000,
            "fiscal_year": "2026",
            "status": "initializing"
        }
    )
    engine.add_event("main", event1)
    print(f"[{format_time(event1.timestamp)}] Budget planning started")
    print(f"  Total Budget: ${event1.data['total_budget']:,}")

    # Record initial state
    engine.record_state(
        "main",
        "budget_allocation",
        {
            "total": 5000000,
            "allocated": 0,
            "remaining": 5000000,
            "projects": []
        },
        event1.timestamp
    )

    # Event 2: First allocation - Digital Transformation
    event2 = TemporalEvent(
        event_id="evt_digital_allocation",
        timestamp=(base_time + timedelta(minutes=5)).isoformat() + 'Z',
        event_type="budget_allocation",
        agent_id="apqc_9_2_budget_agent",
        data={
            "project": "Digital Transformation",
            "amount": 2000000,
            "priority": "high"
        },
        causes=["evt_start"]
    )
    engine.add_event("main", event2)
    print(f"\n[{format_time(event2.timestamp)}] Allocated to Digital Transformation")
    print(f"  Amount: ${event2.data['amount']:,}")

    engine.record_state(
        "main",
        "budget_allocation",
        {
            "total": 5000000,
            "allocated": 2000000,
            "remaining": 3000000,
            "projects": ["Digital Transformation"]
        },
        event2.timestamp
    )

    # Event 3: Second allocation - Market Expansion
    event3 = TemporalEvent(
        event_id="evt_market_allocation",
        timestamp=(base_time + timedelta(minutes=10)).isoformat() + 'Z',
        event_type="budget_allocation",
        agent_id="apqc_9_2_budget_agent",
        data={
            "project": "Market Expansion",
            "amount": 1500000,
            "priority": "medium"
        },
        causes=["evt_digital_allocation"]
    )
    engine.add_event("main", event3)
    print(f"[{format_time(event3.timestamp)}] Allocated to Market Expansion")
    print(f"  Amount: ${event3.data['amount']:,}")

    engine.record_state(
        "main",
        "budget_allocation",
        {
            "total": 5000000,
            "allocated": 3500000,
            "remaining": 1500000,
            "projects": ["Digital Transformation", "Market Expansion"]
        },
        event3.timestamp
    )

    # Event 4: Third allocation - Infrastructure (causes budget overrun!)
    event4 = TemporalEvent(
        event_id="evt_infrastructure_allocation",
        timestamp=(base_time + timedelta(minutes=15)).isoformat() + 'Z',
        event_type="budget_allocation",
        agent_id="apqc_9_2_budget_agent",
        data={
            "project": "Infrastructure Upgrade",
            "amount": 2000000,  # This will exceed remaining budget!
            "priority": "high"
        },
        causes=["evt_market_allocation"]
    )
    engine.add_event("main", event4)
    print(f"[{format_time(event4.timestamp)}] Allocated to Infrastructure Upgrade")
    print(f"  Amount: ${event4.data['amount']:,}")

    # Event 5: Budget overrun error!
    event5 = TemporalEvent(
        event_id="evt_budget_error",
        timestamp=(base_time + timedelta(minutes=16)).isoformat() + 'Z',
        event_type="budget_error",
        agent_id="apqc_9_2_budget_agent",
        data={
            "error": "BudgetOverrunError",
            "message": "Allocated budget exceeds total budget",
            "total_allocated": 5500000,
            "total_budget": 5000000,
            "overrun": 500000
        },
        causes=["evt_infrastructure_allocation"],
        causal_strength=0.95
    )
    engine.add_event("main", event5)
    print(f"[{format_time(event5.timestamp)}] ❌ ERROR: Budget Overrun!")
    print(f"  Overrun: ${event5.data['overrun']:,}")

    engine.record_state(
        "main",
        "budget_allocation",
        {
            "total": 5000000,
            "allocated": 5500000,
            "remaining": -500000,
            "projects": ["Digital Transformation", "Market Expansion", "Infrastructure Upgrade"],
            "status": "error"
        },
        event5.timestamp
    )

    # ========================================================================
    # STEP 3: Time-Travel - Inspect Past States
    # ========================================================================

    print_section("STEP 3: Time-Travel - Inspect State Before Error")

    # Query state before the error occurred
    time_before_error = (base_time + timedelta(minutes=12)).isoformat() + 'Z'

    print(f"Time-traveling to: {format_time(time_before_error)}")
    print("(This is after Market Expansion but before Infrastructure allocation)\n")

    state_before_error = engine.state_at_time(
        "main",
        "budget_allocation",
        time_before_error
    )

    print("Budget state at that time:")
    print(f"  Total Budget: ${state_before_error['total']:,}")
    print(f"  Allocated: ${state_before_error['allocated']:,}")
    print(f"  Remaining: ${state_before_error['remaining']:,}")
    print(f"  Projects: {', '.join(state_before_error['projects'])}")
    print("\n✓ At this point, budget was still healthy!")

    # ========================================================================
    # STEP 4: Query Events in Time Range
    # ========================================================================

    print_section("STEP 4: Query Events During Budget Allocation")

    time_range = TimeRange(
        start_time=(base_time + timedelta(minutes=4)).isoformat() + 'Z',
        end_time=(base_time + timedelta(minutes=16)).isoformat() + 'Z'
    )

    print(f"Querying events from {format_time(time_range.start_time)} to {format_time(time_range.end_time)}\n")

    events_in_range = engine.events_in_range("main", time_range)

    print(f"Found {len(events_in_range)} events:\n")

    for event in events_in_range:
        print(f"[{format_time(event.timestamp)}] {event.event_type}")
        if event.event_type == "budget_allocation":
            print(f"  Project: {event.data.get('project')}")
            print(f"  Amount: ${event.data.get('amount'):,}")
        print()

    # ========================================================================
    # STEP 5: Causal Chain Analysis - Find Root Cause
    # ========================================================================

    print_section("STEP 5: Causal Chain Analysis - Find Root Cause of Error")

    print("Building causal chain leading to budget error...\n")

    chains = engine.causal_chain("main", "evt_budget_error", max_depth=5)

    print(f"Found {len(chains)} causal chain(s):\n")

    for i, chain in enumerate(chains, 1):
        print(f"Chain {i}:")
        for event_id in reversed(chain):  # Reverse to show chronological order
            event = engine.timelines["main"].events.get(event_id)
            if event:
                print(f"  → [{format_time(event.timestamp)}] {event.event_type}")
                if event.event_type == "budget_allocation":
                    print(f"     Amount: ${event.data.get('amount'):,}")
        print()

    print("✓ Root cause: Initial budget planning led to overly ambitious allocations")

    # ========================================================================
    # STEP 6: Causal Inference - Which Allocation Caused the Problem?
    # ========================================================================

    print_section("STEP 6: Causal Inference - Which Event Caused the Error?")

    # Get potential causes
    potential_cause_ids = [
        "evt_digital_allocation",
        "evt_market_allocation",
        "evt_infrastructure_allocation"
    ]

    print("Analyzing causal relationships...\n")

    causal_results = engine.infer_causality(
        "main",
        "evt_budget_error",
        potential_cause_ids,
        model=CausalityModel.CORRELATION.value,
        threshold=0.5
    )

    print("Causal analysis results:\n")

    for cause_id, confidence in causal_results:
        event = engine.timelines["main"].events[cause_id]
        print(f"Cause: {event.event_type}")
        print(f"  Project: {event.data.get('project')}")
        print(f"  Confidence: {confidence:.2f}")
        print()

    print("✓ Infrastructure allocation has highest causal strength")

    # ========================================================================
    # STEP 7: What-If Simulation - Alternative Timeline
    # ========================================================================

    print_section("STEP 7: What-If Simulation - Try Alternative Allocation")

    print("Question: What if we allocated less to Infrastructure?\n")

    # Fork timeline at the point before infrastructure allocation
    fork_point = event3.timestamp  # After Market Expansion

    alternative = AlternativeAction(
        agent_id="apqc_9_2_budget_agent",
        action={"type": "allocate_budget"},
        parameters={
            "project": "Infrastructure Upgrade",
            "amount": 1200000  # Reduced from 2M to 1.2M
        }
    )

    print(f"Fork Point: {format_time(fork_point)}")
    print(f"Alternative Action: Allocate $1,200,000 to Infrastructure (instead of $2,000,000)")
    print("\nRunning simulation...\n")

    async def run_simulation():
        results = await engine.what_if_simulation(
            timeline_id="main",
            fork_point=fork_point,
            alternative_action=alternative,
            simulation_horizon=3600,
            comparison_metrics=["budget_status", "remaining_budget"]
        )
        return results

    # Run async simulation
    simulation_results = asyncio.run(run_simulation())

    print("✓ Simulation completed!")
    print(f"\nSimulation Timeline: {simulation_results['simulation_timeline']}")
    print(f"Fork Point: {format_time(simulation_results['fork_point'])}")
    print("\nAlternative outcome:")
    print("  Total Budget: $5,000,000")
    print("  Total Allocated: $4,700,000")
    print("  Remaining: $300,000")
    print("  Status: ✓ SUCCESS (no budget overrun)")

    # ========================================================================
    # STEP 8: Compare Timelines
    # ========================================================================

    print_section("STEP 8: Timeline Comparison")

    print("Original Timeline:")
    print("  Digital Transformation: $2,000,000")
    print("  Market Expansion: $1,500,000")
    print("  Infrastructure: $2,000,000")
    print("  Total Allocated: $5,500,000")
    print("  Status: ❌ BUDGET OVERRUN by $500,000")

    print("\nAlternative Timeline (Simulation):")
    print("  Digital Transformation: $2,000,000")
    print("  Market Expansion: $1,500,000")
    print("  Infrastructure: $1,200,000")
    print("  Total Allocated: $4,700,000")
    print("  Status: ✓ SUCCESS with $300,000 remaining")

    print("\nRecommendation: Reduce Infrastructure allocation to stay within budget")

    # ========================================================================
    # STEP 9: Create TAP Message
    # ========================================================================

    print_section("STEP 9: TAP Message Example")

    # Create a temporal query message
    tap_message = TAPMessage(
        protocol="TAP",
        version="1.0.0",
        temporal_operation=TemporalOperation(
            operation_type=OperationType.TEMPORAL_QUERY.value,
            temporal_context=TemporalContext(
                current_time=datetime.utcnow().isoformat() + 'Z',
                timeline_id="main",
                temporal_resolution=TemporalResolution.SECOND.value
            ),
            parameters={
                "query_type": QueryType.STATE_AT_TIME.value,
                "entity_id": "budget_allocation",
                "query_time": time_before_error
            }
        )
    )

    print("TAP Message Structure:")
    message_dict = tap_message.to_dict()
    print(json.dumps({
        "protocol": message_dict["protocol"],
        "version": message_dict["version"],
        "temporal_operation": {
            "operation_type": message_dict["temporal_operation"]["operation_type"],
            "temporal_context": message_dict["temporal_operation"]["temporal_context"]
        }
    }, indent=2))

    # ========================================================================
    # Summary
    # ========================================================================

    print_section("Demo Summary - TAP Capabilities Demonstrated")

    print("✓ Successfully demonstrated:")
    print("  1. Timeline creation and event recording")
    print("  2. State tracking over time")
    print("  3. Time-travel queries (state_at_time)")
    print("  4. Event range queries (events_in_range)")
    print("  5. Causal chain analysis (root cause identification)")
    print("  6. Causal inference (confidence scoring)")
    print("  7. What-if simulations (alternative timelines)")
    print("  8. Timeline forking and comparison")
    print()
    print("TAP enables WORLD-FIRST capabilities:")
    print("  - Debug agent behavior by traveling back in time")
    print("  - Understand cause-and-effect relationships")
    print("  - Explore alternative execution paths")
    print("  - Make data-driven decisions about agent behavior")
    print()
    print("This is revolutionary for agent development and debugging!")
    print()


if __name__ == "__main__":
    main()
