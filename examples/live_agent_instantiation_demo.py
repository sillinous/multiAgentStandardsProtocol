"""
🚀 Live Agent Instantiation Demo
=================================

Demonstrates the NEW agent instantiation system that creates REAL running agents!

This example shows:
1. Creating agents that actually run (not just registry entries)
2. Submitting tasks to running agents
3. Monitoring agent status and task completion
4. Lifecycle management (start, stop, pause, resume)

Run this after starting the API server:
    python -m uvicorn src.superstandard.api.server:app --reload --port 8080

Then in another terminal:
    python examples/live_agent_instantiation_demo.py

Author: SuperStandard Team
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8080"


async def main():
    print("=" * 80)
    print("🚀 LIVE AGENT INSTANTIATION DEMO")
    print("=" * 80)
    print()

    async with aiohttp.ClientSession() as session:

        # ====================================================================
        # PART 1: Register and Instantiate Agents
        # ====================================================================

        print("📋 PART 1: Register and Instantiate Agents")
        print("-" * 80)

        agents_to_create = [
            {
                "agent_id": "analyst-001",
                "agent_type": "analytics",
                "capabilities": ["data_analysis", "pattern_detection"],
                "metadata": {"purpose": "Data analysis agent"}
            },
            {
                "agent_id": "processor-001",
                "agent_type": "processor",
                "capabilities": ["data_processing", "transformation"],
                "metadata": {"purpose": "Data processor"}
            },
            {
                "agent_id": "monitor-001",
                "agent_type": "monitor",
                "capabilities": ["health_monitoring", "alerting"],
                "metadata": {"purpose": "System monitor"}
            }
        ]

        for agent_spec in agents_to_create:
            print(f"\n🤖 Creating {agent_spec['agent_id']}...")

            # Register and INSTANTIATE the agent
            async with session.post(
                f"{API_BASE}/api/anp/agents/register?instantiate=true",  # ← KEY: instantiate=true
                json={
                    "agent_id": agent_spec["agent_id"],
                    "agent_type": agent_spec["agent_type"],
                    "capabilities": agent_spec["capabilities"],
                    "endpoints": {"http": f"http://localhost:8080/agents/{agent_spec['agent_id']}"},
                    "metadata": agent_spec["metadata"]
                }
            ) as response:
                result = await response.json()

                if result.get("instantiated"):
                    print(f"   ✅ {agent_spec['agent_id']} INSTANTIATED and RUNNING!")
                    print(f"      Status: {result.get('message')}")
                else:
                    print(f"   ⚠️ {agent_spec['agent_id']} registered but NOT instantiated")

        print("\n" + "=" * 80)

        # ====================================================================
        # PART 2: Check Running Agents
        # ====================================================================

        print("\n📊 PART 2: Check Running Agents")
        print("-" * 80)

        async with session.get(f"{API_BASE}/api/agents/running") as response:
            result = await response.json()
            running_agents = result.get("agents", [])

            print(f"\n🏃 Running Agents: {len(running_agents)}")

            for agent in running_agents:
                print(f"\n   Agent: {agent['agent_id']}")
                print(f"   Type: {agent['agent_type']}")
                print(f"   State: {agent['state']}")
                print(f"   Tasks Completed: {agent['stats']['tasks_completed']}")
                print(f"   Queue Size: {agent['queue_size']}")
                print(f"   Uptime: {agent['stats'].get('uptime_seconds', 0):.1f}s")

        print("\n" + "=" * 80)

        # ====================================================================
        # PART 3: Submit Tasks to Running Agents
        # ====================================================================

        print("\n📝 PART 3: Submit Tasks to Running Agents")
        print("-" * 80)

        tasks = [
            ("analyst-001", {"type": "analyze", "data": {"metric": "revenue", "value": 15000}}),
            ("processor-001", {"type": "process", "data": {"records": [1, 2, 3, 4, 5]}}),
            ("monitor-001", {"type": "monitor", "target": "system", "interval": 30})
        ]

        task_ids = []
        for agent_id, task in tasks:
            print(f"\n📤 Submitting task to {agent_id}...")
            print(f"   Task: {task}")

            async with session.post(
                f"{API_BASE}/api/agents/{agent_id}/task",
                json=task
            ) as response:
                result = await response.json()

                if result.get("success"):
                    task_id = result.get("task_id")
                    task_ids.append((agent_id, task_id))
                    print(f"   ✅ Task submitted! Task ID: {task_id}")
                else:
                    print(f"   ❌ Task submission failed")

        # Wait for tasks to complete
        print("\n⏳ Waiting 3 seconds for tasks to complete...")
        await asyncio.sleep(3)

        print("\n" + "=" * 80)

        # ====================================================================
        # PART 4: Check Agent Status After Task Execution
        # ====================================================================

        print("\n📊 PART 4: Check Agent Status After Task Execution")
        print("-" * 80)

        for agent_id, task_id in task_ids:
            async with session.get(f"{API_BASE}/api/agents/{agent_id}/status") as response:
                result = await response.json()
                status = result.get("status", {})

                print(f"\n   Agent: {agent_id}")
                print(f"   State: {status.get('state')}")
                print(f"   Tasks Completed: {status['stats']['tasks_completed']}")
                print(f"   Tasks Failed: {status['stats']['tasks_failed']}")
                print(f"   Avg Task Time: {status['stats'].get('avg_task_time', 0):.3f}s")

        print("\n" + "=" * 80)

        # ====================================================================
        # PART 5: Lifecycle Management
        # ====================================================================

        print("\n⚙️ PART 5: Lifecycle Management")
        print("-" * 80)

        # Pause an agent
        print("\n⏸️ Pausing processor-001...")
        async with session.post(f"{API_BASE}/api/agents/processor-001/pause") as response:
            result = await response.json()
            print(f"   {result.get('message')}")

        await asyncio.sleep(1)

        # Check status
        async with session.get(f"{API_BASE}/api/agents/processor-001/status") as response:
            result = await response.json()
            print(f"   Status: {result['status']['state']}")

        # Resume the agent
        print("\n▶️ Resuming processor-001...")
        async with session.post(f"{API_BASE}/api/agents/processor-001/resume") as response:
            result = await response.json()
            print(f"   {result.get('message')}")

        await asyncio.sleep(1)

        # Stop an agent
        print("\n⭕ Stopping monitor-001...")
        async with session.post(f"{API_BASE}/api/agents/monitor-001/stop") as response:
            result = await response.json()
            print(f"   {result.get('message')}")

        # Check running agents again
        async with session.get(f"{API_BASE}/api/agents/running") as response:
            result = await response.json()
            print(f"\n   Running agents now: {result['count']}")

        print("\n" + "=" * 80)

        # ====================================================================
        # SUMMARY
        # ====================================================================

        print("\n🎉 DEMO COMPLETE!")
        print("=" * 80)
        print("\n✅ What we demonstrated:")
        print("   1. ✓ Created REAL running agents (not just registry entries)")
        print("   2. ✓ Submitted tasks and agents executed them autonomously")
        print("   3. ✓ Monitored agent status and task completion")
        print("   4. ✓ Paused, resumed, and stopped agents")
        print("\n💡 Key Insight:")
        print("   These agents are ACTUALLY RUNNING with autonomous behavior loops!")
        print("   They process tasks from their queues continuously until stopped.")
        print("\n🚀 Try the dashboards:")
        print("   - http://localhost:8080/dashboard/network (see agents)")
        print("   - http://localhost:8080/dashboard/admin (see activity)")
        print()


if __name__ == "__main__":
    print()
    print("⚠️ IMPORTANT: Make sure the API server is running first!")
    print("   Run: python -m uvicorn src.superstandard.api.server:app --reload --port 8080")
    print()
    input("Press Enter when server is ready...")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nMake sure the API server is running on http://localhost:8080")
