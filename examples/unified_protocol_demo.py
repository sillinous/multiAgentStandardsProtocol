"""
Unified Protocol Demo - All Protocols Working Together!

This demo showcases the power of combining ALL SuperStandard protocols:
- ANP (Agent Network Protocol) - Discovery and registration
- ACP (Agent Coordination Protocol) - Task orchestration
- AConsP (Agent Consciousness Protocol) - Collective intelligence

Watch as agents:
1. Register on the network (ANP)
2. Discover each other via capabilities (ANP)
3. Join coordination session (ACP)
4. Execute coordinated tasks (ACP)
5. Share thoughts and insights (AConsP)
6. Discover emergent patterns (AConsP)

This demonstrates the world's first COMPLETE multi-agent protocol suite!

Usage:
    python examples/unified_protocol_demo.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability
from superstandard.agents.base.network_mixin import NetworkAwareMixin
from superstandard.agents.base.coordination_mixin import CoordinationMixin
from superstandard.agents.base.consciousness_mixin import ConsciousnessMixin

from superstandard.protocols.anp_implementation import AgentNetworkRegistry, AgentStatus
from superstandard.protocols.acp_implementation import CoordinationManager, CoordinationType
from superstandard.protocols.consciousness_protocol import CollectiveConsciousness, ThoughtType


# ============================================================================
# Create "Super Agent" with ALL Protocol Capabilities
# ============================================================================

class SuperAgent(NetworkAwareMixin, CoordinationMixin, ConsciousnessMixin, BaseAgent):
    """
    SuperAgent with ALL protocol capabilities:
    - Network awareness (ANP)
    - Coordination (ACP)
    - Consciousness (AConsP)

    This agent can:
    - Discover and register on networks
    - Participate in coordinated tasks
    - Share thoughts and emergent intelligence
    """

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with full protocol awareness."""
        task_id = task.get("task_id", "unknown")
        task_type = task.get("task_type", "generic")
        input_data = task.get("input_data", {})

        # Think about the task
        await self.think(
            ThoughtType.OBSERVATION,
            f"Received {task_type} task: {task.get('description')}",
            confidence=0.9
        )

        # Simulate work
        await asyncio.sleep(0.2)

        # Generate result based on agent type
        if self.agent_type == "analyst":
            result = {
                "analysis": f"Data analysis complete for {input_data.get('data', 'dataset')}",
                "confidence": 0.88,
                "insights": ["Pattern A detected", "Correlation found"]
            }
        elif self.agent_type == "processor":
            result = {
                "processed": f"Processed {input_data.get('items', 0)} items",
                "success_rate": 0.95,
                "output": "processed_data.json"
            }
        elif self.agent_type == "validator":
            result = {
                "validated": True,
                "quality_score": 0.92,
                "issues_found": 2
            }
        else:
            result = {
                "status": "completed",
                "output": "generic_result"
            }

        # Share insight with collective
        await self.think(
            ThoughtType.INSIGHT,
            f"Completed {task_type}: {result}",
            confidence=0.85,
            emotional_valence=0.5
        )

        return {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "success": True
        }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with full protocol awareness."""
        return await self.execute_task({"task_type": "analysis", "input_data": input_data})


# ============================================================================
# Unified Protocol Demonstration
# ============================================================================

async def run_unified_demo():
    """
    Demonstrate ALL protocols working together harmoniously.
    """
    print("=" * 80)
    print("UNIFIED PROTOCOL DEMONSTRATION")
    print("ANP + ACP + AConsP = Complete Multi-Agent Platform")
    print("=" * 80)
    print()

    # ========================================================================
    # PHASE 1: NETWORK SETUP (ANP)
    # ========================================================================

    print("PHASE 1: AGENT NETWORK PROTOCOL (ANP)")
    print("-" * 80)
    print()

    # Create network registry
    print("Creating agent network registry...")
    network = AgentNetworkRegistry()
    print("[OK] Network registry initialized\n")

    # Create super agents
    print("Creating SuperAgents with ALL protocol capabilities...")
    agents = [
        SuperAgent("analyst_001", "analyst", [AgentCapability.TESTING]),
        SuperAgent("processor_001", "processor", [AgentCapability.DEVELOPMENT]),
        SuperAgent("validator_001", "validator", [AgentCapability.QA_EVALUATION])
    ]
    print(f"[OK] Created {len(agents)} SuperAgents\n")

    # Register on network
    print("Registering agents on network (ANP)...")
    for agent in agents:
        await agent.register_on_network(
            network,
            endpoints={"http": f"http://localhost:800{agents.index(agent)}"},
            metadata={"version": "1.0.0"},
            auto_heartbeat=False  # Manual for demo
        )
    print()

    # Discover agents
    print("Discovering agents by capability (ANP)...")
    analyst = agents[0]
    discovered = await analyst.discover_agents(
        capabilities=["development"],
        health_status="healthy"
    )
    print(f"  Found {len(discovered)} agents with 'development' capability:")
    for agent_info in discovered:
        print(f"    - {agent_info['agent_id']} ({agent_info['agent_type']})")
    print()

    # Send heartbeats
    print("Sending heartbeats to network...")
    for agent in agents:
        await agent.send_heartbeat(health_status="healthy", load_score=0.2)
    print("[OK] All agents healthy\n")

    # ========================================================================
    # PHASE 2: COLLECTIVE CONSCIOUSNESS (AConsP)
    # ========================================================================

    print("PHASE 2: AGENT CONSCIOUSNESS PROTOCOL (AConsP)")
    print("-" * 80)
    print()

    # Create collective consciousness
    print("Creating collective consciousness field...")
    collective = CollectiveConsciousness("unified_demo_collective")
    print("[OK] Collective consciousness initialized\n")

    # Agents join collective
    print("Agents joining collective consciousness...")
    for agent in agents:
        await agent.join_collective(collective, auto_respond=True)
    print()

    # ========================================================================
    # PHASE 3: COORDINATION SESSION (ACP)
    # ========================================================================

    print("PHASE 3: AGENT COORDINATION PROTOCOL (ACP)")
    print("-" * 80)
    print()

    # Create coordination manager
    print("Creating coordination manager...")
    coordinator = CoordinationManager()
    print("[OK] Coordination manager initialized\n")

    # Create coordination session
    print("Creating PIPELINE coordination session...")
    session_id = await coordinator.create_session(
        "Data Processing Pipeline",
        CoordinationType.PIPELINE,
        metadata={"priority": "high"}
    )
    print(f"[OK] Session created: {session_id}\n")

    # Agents join coordination
    print("Agents joining coordination session...")
    await agents[0].join_coordination(coordinator, session_id, role="participant")  # Analyst
    await agents[1].join_coordination(coordinator, session_id, role="participant")  # Processor
    await agents[2].join_coordination(coordinator, session_id, role="participant")  # Validator
    print()

    # Add tasks to session
    print("Adding tasks to pipeline...")
    task_ids = []

    # Task 1: Analysis
    task1_id = await coordinator.add_task(
        session_id,
        "analysis",
        "Analyze incoming data stream",
        priority=10,
        input_data={"data": "dataset_A.csv"}
    )
    task_ids.append(task1_id)
    print(f"  Task 1 (analysis): {task1_id}")

    # Task 2: Processing (depends on task 1)
    task2_id = await coordinator.add_task(
        session_id,
        "processing",
        "Process analyzed data",
        priority=9,
        dependencies=[task1_id],
        input_data={"items": 1000}
    )
    task_ids.append(task2_id)
    print(f"  Task 2 (processing): {task2_id}")

    # Task 3: Validation (depends on task 2)
    task3_id = await coordinator.add_task(
        session_id,
        "validation",
        "Validate processed output",
        priority=8,
        dependencies=[task2_id],
        input_data={"output_file": "processed_data.json"}
    )
    task_ids.append(task3_id)
    print(f"  Task 3 (validation): {task3_id}\n")

    # ========================================================================
    # PHASE 4: UNIFIED EXECUTION
    # ========================================================================

    print("PHASE 4: UNIFIED EXECUTION (All Protocols Active)")
    print("-" * 80)
    print()

    print("Agents executing coordinated tasks with conscious awareness...\n")

    # Execute pipeline with all protocols active
    for i, agent in enumerate(agents):
        # Agent requests task
        task = await agent.request_task()

        if task:
            print(f"[{agent.agent_id}] Accepted: {task['description']}")

            # Report start
            await agent.report_progress(task['task_id'], 0.1, "Starting")

            # Execute task (which includes consciousness sharing)
            result = await agent.execute_task(task)

            # Report progress
            await agent.report_progress(task['task_id'], 0.8, "Near completion")

            # Submit result
            await agent.submit_result(task['task_id'], result, success=True)

            # Update network status
            await agent.send_heartbeat(health_status="healthy", load_score=0.5)

            print(f"[{agent.agent_id}] Completed: {task['task_id']}")
            print()

    # ========================================================================
    # PHASE 5: CONSCIOUSNESS COLLAPSE
    # ========================================================================

    print("PHASE 5: CONSCIOUSNESS COLLAPSE (Emergent Intelligence)")
    print("-" * 80)
    print()

    print("Triggering consciousness collapse to discover emergent patterns...\n")

    patterns = await agents[0].query_collective(
        "What insights emerged from our coordinated execution?",
        min_coherence=0.4
    )

    if patterns:
        print(f">>> {len(patterns)} EMERGENT PATTERN(S) DISCOVERED!\n")

        for i, pattern in enumerate(patterns, 1):
            print(f"PATTERN #{i}: {pattern.pattern_type.upper()}")
            print(f"  Coherence: {pattern.coherence_score:.0%}")
            print(f"  Novelty: {pattern.novelty_score:.0%}")
            print(f"  Contributing Agents: {', '.join(pattern.contributing_agents)}")
            print()
    else:
        print("No emergent patterns (threshold not met)")
        print()

    # ========================================================================
    # PHASE 6: UNIFIED STATE INSPECTION
    # ========================================================================

    print("PHASE 6: UNIFIED STATE INSPECTION")
    print("-" * 80)
    print()

    print("Inspecting agent states across ALL protocols...\n")

    for agent in agents:
        print(f"{agent.agent_id} ({agent.agent_type}):")

        # Network state (ANP)
        network_info = await agent.get_network_info()
        print(f"  Network: Registered={network_info['registered']}, "
              f"Heartbeat={network_info['last_heartbeat']}")

        # Coordination state (ACP)
        coord_info = await agent.get_coordination_state()
        print(f"  Coordination: Session={coord_info['in_session']}, "
              f"Role={coord_info['role']}, "
              f"Completed={coord_info['completed_tasks']}")

        # Consciousness state (AConsP)
        conscious_info = await agent.get_consciousness_state()
        print(f"  Consciousness: State={conscious_info['state']}, "
              f"Thoughts={conscious_info['thoughts_contributed']}, "
              f"Patterns={conscious_info['patterns_participated_in']}")

        print()

    # ========================================================================
    # PHASE 7: GRACEFUL SHUTDOWN
    # ========================================================================

    print("PHASE 7: GRACEFUL SHUTDOWN")
    print("-" * 80)
    print()

    print("Cleaning up all protocol connections...")

    for agent in agents:
        # Leave coordination
        await agent.leave_coordination()

        # Leave collective
        await agent.leave_collective()

        # Deregister from network
        await agent.deregister_from_network()

    print("[OK] All agents cleaned up\n")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print("=" * 80)
    print("UNIFIED PROTOCOL DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()

    print("What just happened:")
    print()
    print("1. ANP - Agents registered, discovered peers, sent heartbeats")
    print("2. AConsP - Agents joined collective consciousness, shared thoughts")
    print("3. ACP - Agents coordinated in pipeline, executed tasks")
    print("4. ALL TOGETHER - Agents used all protocols simultaneously!")
    print("5. EMERGENT - Patterns emerged from collective coordination")
    print()
    print("This is the world's FIRST complete multi-agent protocol suite!")
    print("ALL protocols working together in a single, unified system!")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print()
    print("       UNIFIED PROTOCOL DEMONSTRATION")
    print("       The Complete SuperStandard Multi-Agent Platform")
    print()
    print("=" * 80)
    print()

    asyncio.run(run_unified_demo())

    print("\nThe future of multi-agent systems is UNIFIED!\n")
