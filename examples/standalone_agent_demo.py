"""
🚀 Standalone Agent Instantiation Demo
=======================================

Demonstrates the agent runtime system WITHOUT needing a web server.
This shows agents actually running with autonomous behavior!
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.agents.runtime import AgentFactory, RuntimeAgent


async def main():
    print("=" * 80)
    print("🚀 LIVE AGENT INSTANTIATION - STANDALONE DEMO")
    print("=" * 80)
    print()

    # ========================================================================
    # PART 1: Create Agent Factory
    # ========================================================================
    print("📋 PART 1: Initialize Agent Factory")
    print("-" * 80)

    factory = AgentFactory()

    print(f"✅ AgentFactory initialized")
    print(f"   Available agent types: {', '.join(factory.get_available_types())}")
    print()

    # ========================================================================
    # PART 2: Instantiate Agents
    # ========================================================================
    print("\n📋 PART 2: Instantiate Real Agents")
    print("-" * 80)

    agent_specs = [
        ("analyst-001", "analytics", ["data_analysis", "pattern_detection"]),
        ("processor-001", "generic", ["data_processing", "transformation"]),
        ("monitor-001", "generic", ["health_monitoring", "alerting"])
    ]

    print("\n🤖 Creating agents...")
    for agent_id, agent_type, capabilities in agent_specs:
        print(f"\n   Creating {agent_id} ({agent_type})...")

        try:
            runtime_agent = await factory.create_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                auto_start=True
            )

            print(f"   ✅ {agent_id} INSTANTIATED and RUNNING!")
            print(f"      State: {runtime_agent.state.value}")
            print(f"      Queue size: {runtime_agent.task_queue.qsize()}")

        except Exception as e:
            print(f"   ❌ Failed to create {agent_id}: {e}")

    print("\n" + "=" * 80)

    # ========================================================================
    # PART 3: Check Running Agents
    # ========================================================================
    print("\n📊 PART 3: Check Running Agents")
    print("-" * 80)

    running_agents = factory.get_running_agents()
    print(f"\n🏃 Running Agents: {len(running_agents)}")

    for agent in running_agents:
        print(f"\n   Agent: {agent['agent_id']}")
        print(f"   Type: {agent['agent_type']}")
        print(f"   State: {agent['state']}")
        print(f"   Instantiated: {agent['instantiated']}")
        print(f"   Queue Size: {agent['queue_size']}")
        print(f"   Tasks Completed: {agent['stats']['tasks_completed']}")

    print("\n" + "=" * 80)

    # ========================================================================
    # PART 4: Submit Tasks to Agents
    # ========================================================================
    print("\n📝 PART 4: Submit Tasks to Running Agents")
    print("-" * 80)

    tasks = [
        ("analyst-001", {"type": "analyze", "data": {"metric": "revenue", "value": 15000}}),
        ("processor-001", {"type": "process", "data": {"records": [1, 2, 3, 4, 5]}}),
        ("monitor-001", {"type": "monitor", "target": "system", "interval": 30})
    ]

    print("\n📤 Submitting tasks...")
    for agent_id, task in tasks:
        try:
            task_id = await factory.submit_task(agent_id, task)
            print(f"   ✅ Task submitted to {agent_id}: {task_id}")
        except Exception as e:
            print(f"   ❌ Failed to submit task to {agent_id}: {e}")

    # Wait for tasks to process
    print("\n⏳ Waiting 3 seconds for agents to process tasks...")
    await asyncio.sleep(3)

    print("\n" + "=" * 80)

    # ========================================================================
    # PART 5: Check Agent Status After Execution
    # ========================================================================
    print("\n📊 PART 5: Agent Status After Task Execution")
    print("-" * 80)

    for agent_id, _ in tasks:
        status = factory.get_agent_status(agent_id)
        if status:
            print(f"\n   Agent: {agent_id}")
            print(f"   State: {status['state']}")
            print(f"   Tasks Completed: {status['stats']['tasks_completed']}")
            print(f"   Tasks Failed: {status['stats']['tasks_failed']}")
            print(f"   Avg Task Time: {status['stats'].get('avg_task_time', 0):.3f}s")
            uptime = status['stats'].get('uptime_seconds')
            if uptime is not None:
                print(f"   Uptime: {uptime:.1f}s")
            else:
                print(f"   Uptime: N/A")

    print("\n" + "=" * 80)

    # ========================================================================
    # PART 6: Lifecycle Management
    # ========================================================================
    print("\n⚙️ PART 6: Lifecycle Management")
    print("-" * 80)

    # Pause an agent
    print("\n⏸️ Pausing processor-001...")
    await factory.pause_agent("processor-001")
    status = factory.get_agent_status("processor-001")
    print(f"   Status: {status['state']}")

    await asyncio.sleep(1)

    # Resume the agent
    print("\n▶️ Resuming processor-001...")
    await factory.resume_agent("processor-001")
    status = factory.get_agent_status("processor-001")
    print(f"   Status: {status['state']}")

    await asyncio.sleep(1)

    # Stop an agent
    print("\n⭕ Stopping monitor-001...")
    await factory.stop_agent("monitor-001")

    # Check running agents again
    running_agents = factory.get_running_agents()
    print(f"\n   Running agents now: {len(running_agents)}")
    for agent in running_agents:
        print(f"      - {agent['agent_id']} ({agent['state']})")

    print("\n" + "=" * 80)

    # ========================================================================
    # PART 7: Cleanup
    # ========================================================================
    print("\n🧹 PART 7: Cleanup")
    print("-" * 80)

    print("\n⭕ Stopping all remaining agents...")
    await factory.stop_all_agents()

    running_agents = factory.get_running_agents()
    print(f"   Running agents: {len(running_agents)}")

    print("\n" + "=" * 80)

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n🎉 DEMO COMPLETE!")
    print("=" * 80)
    print("\n✅ What we demonstrated:")
    print("   1. ✓ Created REAL running agents (not just registry entries)")
    print("   2. ✓ Agents have autonomous behavior loops")
    print("   3. ✓ Submitted tasks and agents executed them")
    print("   4. ✓ Monitored agent status and performance")
    print("   5. ✓ Paused, resumed, and stopped agents")
    print("\n💡 Key Insight:")
    print("   These agents are ACTUALLY RUNNING with:")
    print("   - Autonomous behavior loops")
    print("   - Task queues")
    print("   - State machines (IDLE → WORKING → PAUSED → STOPPED)")
    print("   - Performance tracking")
    print("   - Lifecycle management")
    print("\n🎯 This is the foundation for:")
    print("   - Multi-agent orchestration")
    print("   - Autonomous task execution")
    print("   - Production agent systems")
    print()


if __name__ == "__main__":
    print()
    asyncio.run(main())
