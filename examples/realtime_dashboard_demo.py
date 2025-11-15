"""
Real-Time Dashboard Demo
Demonstrates live monitoring of autonomous agent operations
"""

import asyncio
import random
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.superstandard.dashboard import get_event_bus, get_dashboard, DashboardEvent


async def simulate_agent_execution(agent_id: str, agent_name: str, task: str, duration_ms: float):
    """Simulate an agent execution with dashboard events"""
    event_bus = get_event_bus()

    # Start event
    await event_bus.publish(
        DashboardEvent.agent_started(agent_id, agent_name, task)
    )

    print(f"   🤖 {agent_name} started: {task}")

    # Simulate execution
    await asyncio.sleep(duration_ms / 1000.0)

    # Complete event (90% success rate)
    success = random.random() > 0.1
    await event_bus.publish(
        DashboardEvent.agent_completed(agent_id, agent_name, task, duration_ms, success)
    )

    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"   {status} {agent_name} completed in {duration_ms:.0f}ms")

    return success


async def simulate_workflow(workflow_id: str, workflow_name: str, agents: list):
    """Simulate a complete workflow with multiple agents"""
    event_bus = get_event_bus()

    print(f"\n🚀 Starting workflow: {workflow_name}")
    print(f"   Total tasks: {len(agents)}")

    # Workflow started event
    await event_bus.publish(
        DashboardEvent.workflow_started(workflow_id, workflow_name, len(agents))
    )

    start_time = asyncio.get_event_loop().time()

    # Execute all agents
    results = []
    total_cost = 0.0

    for agent_id, agent_name, task, cost in agents:
        duration_ms = random.uniform(500, 2000)
        success = await simulate_agent_execution(agent_id, agent_name, task, duration_ms)
        results.append(success)
        total_cost += cost

    # Calculate results
    tasks_completed = sum(results)
    tasks_failed = len(results) - tasks_completed
    duration_seconds = asyncio.get_event_loop().time() - start_time

    # Workflow completed event
    await event_bus.publish(
        DashboardEvent.workflow_completed(
            workflow_id, workflow_name, duration_seconds,
            tasks_completed, tasks_failed, total_cost
        )
    )

    print(f"\n✨ Workflow '{workflow_name}' completed!")
    print(f"   Duration: {duration_seconds:.2f}s")
    print(f"   Tasks completed: {tasks_completed}/{len(agents)}")
    print(f"   Tasks failed: {tasks_failed}")
    print(f"   Total cost: ${total_cost:.2f}")


async def run_demo():
    """Run dashboard demo with simulated operations"""
    print("\n" + "=" * 80)
    print("🎯 REAL-TIME DASHBOARD DEMO")
    print("=" * 80)
    print("\n📊 Dashboard will show live updates at: http://localhost:8000")
    print("   (Start the dashboard server in another terminal with:)")
    print("   python src/superstandard/dashboard/dashboard_server.py")
    print("\n🔄 Starting simulated autonomous operations...")
    print("=" * 80 + "\n")

    # Wait a bit for user to open dashboard
    await asyncio.sleep(2)

    # Demo 1: Strategic Planning Workflow
    workflow_1_agents = [
        ("apqc-1.1.1.1", "Competitor Assessment Agent", "Analyze top 5 competitors", 8.50),
        ("apqc-1.1.2.1", "Market Trend Analysis Agent", "Identify market trends Q1 2024", 7.00),
        ("apqc-1.1.3.1", "SWOT Analysis Agent", "Perform company SWOT", 6.00),
        ("apqc-1.4.1.1", "Strategic Planning Agent", "Develop 2024 strategy", 10.00),
        ("apqc-1.5.1.1", "KPI Development Agent", "Define strategic KPIs", 6.50),
    ]

    await simulate_workflow(
        "workflow-strategic-001",
        "Strategic Planning Cycle 2024",
        workflow_1_agents
    )

    await asyncio.sleep(1)

    # Demo 2: New Product Launch Workflow
    workflow_2_agents = [
        ("apqc-2.1.1.1", "Product Ideation Agent", "Generate product concepts", 7.50),
        ("apqc-2.1.2.1", "Requirements Gathering Agent", "Elicit requirements", 6.50),
        ("apqc-2.2.1.1", "Product Design Agent", "Design user experience", 9.00),
        ("apqc-2.3.1.1", "Prototype Development Agent", "Build MVP prototype", 10.00),
        ("apqc-2.3.2.1", "User Testing Agent", "Conduct user testing", 7.00),
        ("apqc-3.2.1.1", "Marketing Campaign Planning Agent", "Plan launch campaign", 9.00),
        ("apqc-3.2.2.1", "Content Marketing Agent", "Create launch content", 7.50),
        ("apqc-3.3.1.1", "Lead Generation Agent", "Generate pre-launch leads", 9.50),
    ]

    await simulate_workflow(
        "workflow-product-launch-001",
        "New Product Launch - AI Analytics Suite",
        workflow_2_agents
    )

    await asyncio.sleep(1)

    # Demo 3: Financial Planning Workflow
    workflow_3_agents = [
        ("apqc-5.1.1.1", "Financial Planning & Analysis Agent", "Annual FP&A", 11.00),
        ("apqc-5.1.2.1", "Budgeting & Forecasting Agent", "2024 budget", 10.00),
        ("apqc-5.4.1.1", "Investment Analysis Agent", "Evaluate investments", 10.50),
        ("apqc-5.5.1.1", "Financial Risk Management Agent", "Risk assessment", 11.50),
        ("apqc-5.6.1.1", "Tax Planning & Compliance Agent", "Tax strategy", 12.00),
    ]

    await simulate_workflow(
        "workflow-financial-planning-001",
        "Annual Financial Planning 2024",
        workflow_3_agents
    )

    await asyncio.sleep(1)

    # Demo 4: Operational Excellence Workflow
    workflow_4_agents = [
        ("apqc-4.1.1.1", "Production Planning Agent", "Q1 production plan", 9.00),
        ("apqc-4.2.1.1", "Quality Management Agent", "Quality audit", 8.50),
        ("apqc-4.3.1.1", "Inventory Optimization Agent", "Optimize inventory", 7.50),
        ("apqc-4.4.1.1", "Supply Chain Coordination Agent", "Coordinate suppliers", 10.00),
        ("apqc-4.7.1.1", "Performance Analytics Agent", "Analyze performance", 7.00),
    ]

    await simulate_workflow(
        "workflow-ops-excellence-001",
        "Operational Excellence Initiative",
        workflow_4_agents
    )

    await asyncio.sleep(1)

    # Demo 5: Continuous Operations (simulating ongoing work)
    print("\n🔄 Simulating continuous autonomous operations...")
    print("   (Watch the dashboard for real-time updates!)")

    for i in range(10):
        # Pick random agents from our library
        all_agents = workflow_1_agents + workflow_2_agents + workflow_3_agents + workflow_4_agents
        agent = random.choice(all_agents)

        asyncio.create_task(
            simulate_agent_execution(
                agent[0],
                agent[1],
                agent[2],
                random.uniform(300, 1500)
            )
        )

        await asyncio.sleep(random.uniform(0.5, 2.0))

    # Wait for all tasks to complete
    await asyncio.sleep(3)

    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print("\n📊 Check the dashboard to see:")
    print("   ✅ 4 workflows executed")
    print("   ✅ 30+ agent executions")
    print("   ✅ Real-time metrics updated")
    print("   ✅ Live event stream")
    print("\n💡 The dashboard continues to run - execute more agents to see live updates!")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
