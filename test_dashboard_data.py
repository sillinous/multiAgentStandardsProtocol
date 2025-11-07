#!/usr/bin/env python3
"""
Test script to populate the dashboard with sample agents and data.
This demonstrates all dashboard features working together.

Usage:
    python test_dashboard_data.py

Then visit http://localhost:8080/dashboard/network to see live data!
"""

import asyncio
import aiohttp
from datetime import datetime

API_BASE = "http://localhost:8080"


async def register_sample_agents():
    """Register sample agents to populate the dashboard."""

    sample_agents = [
        {
            "agent_id": "agent-data-collector-001",
            "agent_type": "collector",
            "capabilities": ["data_collection", "api_integration"],
            "endpoints": {"api": "http://localhost:9001"},
            "metadata": {"region": "us-east-1", "department": "data-engineering"}
        },
        {
            "agent_id": "agent-analyzer-002",
            "agent_type": "analyzer",
            "capabilities": ["data_analysis", "ml_inference"],
            "endpoints": {"api": "http://localhost:9002"},
            "metadata": {"region": "us-west-2", "department": "ml-ops"}
        },
        {
            "agent_id": "agent-coordinator-003",
            "agent_type": "coordinator",
            "capabilities": ["task_coordination", "workflow_management"],
            "endpoints": {"api": "http://localhost:9003"},
            "metadata": {"region": "eu-central-1", "department": "orchestration"}
        },
        {
            "agent_id": "agent-validator-004",
            "agent_type": "validator",
            "capabilities": ["data_validation", "quality_check"],
            "endpoints": {"api": "http://localhost:9004"},
            "metadata": {"region": "ap-south-1", "department": "quality"}
        },
        {
            "agent_id": "agent-reporter-005",
            "agent_type": "reporter",
            "capabilities": ["report_generation", "visualization"],
            "endpoints": {"api": "http://localhost:9005"},
            "metadata": {"region": "us-east-1", "department": "business-intelligence"}
        },
    ]

    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("Registering Sample Agents")
        print("=" * 60)

        for agent in sample_agents:
            try:
                async with session.post(
                    f"{API_BASE}/api/anp/agents/register",
                    json=agent
                ) as response:
                    result = await response.json()
                    if result.get("success"):
                        print(f"✅ Registered: {agent['agent_id']} ({agent['agent_type']})")
                    else:
                        print(f"❌ Failed: {agent['agent_id']}")
            except Exception as e:
                print(f"❌ Error registering {agent['agent_id']}: {e}")

        print()


async def create_coordination_sessions():
    """Create sample coordination sessions."""

    sessions = [
        {
            "name": "Data Pipeline Processing",
            "coordination_type": "pipeline",
            "description": "Process customer data through multiple stages",
            "metadata": {"priority": "high"}
        },
        {
            "name": "ML Model Training Swarm",
            "coordination_type": "swarm",
            "description": "Distributed model training across multiple agents",
            "metadata": {"priority": "medium"}
        },
        {
            "name": "Quality Assurance Workflow",
            "coordination_type": "supervisor",
            "description": "Supervised QA process with validation checks",
            "metadata": {"priority": "high"}
        },
    ]

    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("Creating Coordination Sessions")
        print("=" * 60)

        for sess in sessions:
            try:
                async with session.post(
                    f"{API_BASE}/api/acp/sessions",
                    json=sess
                ) as response:
                    result = await response.json()
                    if result.get("success"):
                        print(f"✅ Created: {sess['name']} ({sess['coordination_type']})")
                    else:
                        print(f"❌ Failed: {sess['name']}")
            except Exception as e:
                print(f"❌ Error creating session {sess['name']}: {e}")

        print()


async def submit_test_thoughts():
    """Submit sample thoughts to collective consciousness."""

    thoughts = [
        {
            "agent_id": "agent-analyzer-002",
            "thought_type": "observation",
            "content": "Data quality has improved 25% over the last week",
            "confidence": 0.85,
            "context": {"metric": "data_quality", "improvement": 0.25}
        },
        {
            "agent_id": "agent-coordinator-003",
            "thought_type": "insight",
            "content": "Pipeline bottleneck identified at data transformation stage",
            "confidence": 0.92,
            "context": {"stage": "transformation", "impact": "high"}
        },
        {
            "agent_id": "agent-validator-004",
            "thought_type": "inference",
            "content": "Anomaly pattern suggests potential data source issue",
            "confidence": 0.78,
            "context": {"anomaly_type": "source", "severity": "medium"}
        },
    ]

    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("Submitting Collective Thoughts")
        print("=" * 60)

        for thought in thoughts:
            try:
                async with session.post(
                    f"{API_BASE}/api/aconsp/collectives/main/thoughts",
                    json=thought
                ) as response:
                    result = await response.json()
                    if result.get("success"):
                        print(f"✅ Thought from {thought['agent_id']}: {thought['content'][:50]}...")
                    else:
                        print(f"❌ Failed to submit thought")
            except Exception as e:
                print(f"❌ Error submitting thought: {e}")

        print()


async def main():
    """Run all test data population."""
    print("\n" + "=" * 60)
    print("SuperStandard Dashboard Test Data Population")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Register agents
    await register_sample_agents()

    # Create coordination sessions
    await create_coordination_sessions()

    # Submit thoughts
    await submit_test_thoughts()

    print("=" * 60)
    print("✅ Test Data Population Complete!")
    print("=" * 60)
    print()
    print("📊 View the dashboards:")
    print(f"   - Network:        {API_BASE}/dashboard/network")
    print(f"   - Coordination:   {API_BASE}/dashboard/coordination")
    print(f"   - Consciousness:  {API_BASE}/dashboard/consciousness")
    print(f"   - Admin:          {API_BASE}/dashboard/admin")
    print(f"   - User Panel:     {API_BASE}/dashboard/user")
    print()
    print("🔄 WebSocket connections will show real-time updates!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
