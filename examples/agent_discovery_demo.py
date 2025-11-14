#!/usr/bin/env python3
"""
Agent Discovery Protocol (ADP) Demonstration

Shows how agents dynamically discover each other by capability,
enabling true dynamic multi-agent ecosystems without hardcoded references.

This demo demonstrates:
1. Agent registration with rich metadata
2. Capability-based discovery
3. Advanced filtering (cost, latency, reputation)
4. Smart agent reuse (find-or-create pattern)
5. Status tracking and updates
6. Integration with FactoryMetaAgent

THE MISSING PIECE: Dynamic agent discovery that makes multi-agent systems scalable!

Usage:
    python examples/agent_discovery_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.discovery import (
    get_discovery_service,
    AgentCapability,
    AgentMetadata,
    AgentStatus
)
from src.superstandard.a2a.bus import get_message_bus
from src.superstandard.meta_agents.factory import FactoryMetaAgent, AgentSpec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_registration():
    """Demo 1: Basic agent registration"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Agent Registration & Discovery")
    print("=" * 80)

    discovery = get_discovery_service()
    await discovery.start()

    # Register several agents with different capabilities
    agents = [
        {
            "agent_id": "agent-data-001",
            "name": "DataAnalysisAgent-Pro",
            "agent_type": "data_analyst",
            "capabilities": [
                AgentCapability("data_analysis", "1.0.0", {}, "Statistical data analysis"),
                AgentCapability("visualization", "1.0.0", {}, "Data visualization")
            ],
            "metadata": AgentMetadata(
                avg_latency_ms=450.0,
                avg_quality_score=0.95,
                success_rate=0.98,
                cost_per_request=0.15,
                reputation_score=0.92,
                tags=["premium", "fast", "accurate"]
            )
        },
        {
            "agent_id": "agent-data-002",
            "name": "DataAnalysisAgent-Budget",
            "agent_type": "data_analyst",
            "capabilities": [
                AgentCapability("data_analysis", "1.0.0", {}, "Basic data analysis")
            ],
            "metadata": AgentMetadata(
                avg_latency_ms=1200.0,
                avg_quality_score=0.85,
                success_rate=0.92,
                cost_per_request=0.05,
                reputation_score=0.78,
                tags=["budget", "basic"]
            )
        },
        {
            "agent_id": "agent-market-001",
            "name": "MarketResearchAgent",
            "agent_type": "market_researcher",
            "capabilities": [
                AgentCapability("market_analysis", "1.0.0", {}, "Market trend analysis"),
                AgentCapability("competitor_analysis", "1.0.0", {}, "Competitor research")
            ],
            "metadata": AgentMetadata(
                avg_latency_ms=2000.0,
                avg_quality_score=0.93,
                success_rate=0.96,
                cost_per_request=0.25,
                reputation_score=0.89,
                tags=["specialized", "market"]
            )
        },
        {
            "agent_id": "agent-nlp-001",
            "name": "NLPAgent",
            "agent_type": "nlp_processor",
            "capabilities": [
                AgentCapability("text_analysis", "1.0.0", {}, "Natural language processing"),
                AgentCapability("sentiment_analysis", "1.0.0", {}, "Sentiment detection")
            ],
            "metadata": AgentMetadata(
                avg_latency_ms=300.0,
                avg_quality_score=0.97,
                success_rate=0.99,
                cost_per_request=0.10,
                reputation_score=0.95,
                tags=["nlp", "fast", "premium"]
            )
        }
    ]

    print("\n📝 Registering agents...")
    for agent_data in agents:
        await discovery.register_agent(**agent_data)

    print(f"\n✅ Registered {len(agents)} agents")
    print()

    return discovery


async def demo_capability_search(discovery):
    """Demo 2: Search by capabilities"""
    print("\n" + "=" * 80)
    print("DEMO 2: Capability-Based Discovery")
    print("=" * 80)

    # Search for data analysis capability
    print("\n🔍 Query: Find agents with 'data_analysis' capability")
    results = await discovery.find_agents(
        required_capabilities=["data_analysis"]
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name} ({agent.agent_type})")
        print(f"     Cost: ${agent.metadata.cost_per_request}/request")
        print(f"     Quality: {agent.metadata.avg_quality_score * 100:.1f}%")

    # Search for multiple capabilities
    print("\n🔍 Query: Find agents with BOTH 'market_analysis' AND 'competitor_analysis'")
    results = await discovery.find_agents(
        required_capabilities=["market_analysis", "competitor_analysis"]
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name}")

    # Search with no matches
    print("\n🔍 Query: Find agents with 'quantum_computing' capability")
    results = await discovery.find_agents(
        required_capabilities=["quantum_computing"]
    )

    print(f"   Found: {len(results)} agents")
    if not results:
        print("   (No agents found - as expected!)")

    print()


async def demo_advanced_filtering(discovery):
    """Demo 3: Advanced filtering"""
    print("\n" + "=" * 80)
    print("DEMO 3: Advanced Filtering")
    print("=" * 80)

    # Filter by cost
    print("\n🔍 Query: Data analysis agents under $0.10/request")
    results = await discovery.find_agents(
        required_capabilities=["data_analysis"],
        filters={
            "cost_per_request": {"max": 0.10}
        }
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name}: ${agent.metadata.cost_per_request}/request")

    # Filter by reputation
    print("\n🔍 Query: Agents with reputation score >= 0.90")
    results = await discovery.find_agents(
        filters={
            "min_reputation": 0.90
        }
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name}: {agent.metadata.reputation_score * 100:.1f}% reputation")

    # Filter by latency AND quality
    print("\n🔍 Query: Fast (<500ms) AND high-quality (>90%) agents")
    results = await discovery.find_agents(
        filters={
            "avg_latency_ms": {"max": 500},
            "min_success_rate": 0.90
        }
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name}: {agent.metadata.avg_latency_ms:.0f}ms, "
              f"{agent.metadata.success_rate * 100:.1f}% success")

    # Filter by tags
    print("\n🔍 Query: Premium agents")
    results = await discovery.find_agents(
        filters={
            "tags": ["premium"]
        }
    )

    print(f"   Found: {len(results)} agents")
    for agent in results:
        print(f"   • {agent.name} (tags: {', '.join(agent.metadata.tags)})")

    print()


async def demo_sorted_results(discovery):
    """Demo 4: Sorted search results"""
    print("\n" + "=" * 80)
    print("DEMO 4: Sorted Search Results")
    print("=" * 80)

    # Sort by reputation (highest first)
    print("\n🔍 Query: All agents, sorted by reputation (best first)")
    results = await discovery.find_agents(
        filters={},
        sort_by="-reputation_score",  # - means descending
        only_available=False
    )

    print(f"   Found: {len(results)} agents")
    for i, agent in enumerate(results, 1):
        print(f"   {i}. {agent.name}: "
              f"{agent.metadata.reputation_score * 100:.1f}% reputation")

    # Sort by cost (cheapest first)
    print("\n🔍 Query: All agents, sorted by cost (cheapest first)")
    results = await discovery.find_agents(
        filters={},
        sort_by="cost_per_request",  # ascending
        only_available=False
    )

    print(f"   Found: {len(results)} agents")
    for i, agent in enumerate(results, 1):
        print(f"   {i}. {agent.name}: ${agent.metadata.cost_per_request}/request")

    # Sort by latency (fastest first)
    print("\n🔍 Query: All agents, sorted by latency (fastest first)")
    results = await discovery.find_agents(
        filters={},
        sort_by="avg_latency_ms",  # ascending
        only_available=False
    )

    print(f"   Found: {len(results)} agents")
    for i, agent in enumerate(results, 1):
        print(f"   {i}. {agent.name}: {agent.metadata.avg_latency_ms:.0f}ms")

    print()


async def demo_factory_integration():
    """Demo 5: Integration with FactoryMetaAgent"""
    print("\n" + "=" * 80)
    print("DEMO 5: FactoryMetaAgent with Smart Reuse")
    print("=" * 80)

    discovery = get_discovery_service()
    bus = get_message_bus()
    await bus.start()

    factory = FactoryMetaAgent(bus, discovery)

    # Create agent spec
    spec = AgentSpec(
        agent_type="data_analyst",
        name="NewDataAnalysisAgent",
        capabilities=["data_analysis"],
        configuration={"model": "advanced"},
        description="Data analysis agent"
    )

    # First call: No existing agent, will create
    print("\n🏭 First call: find_or_create (no existing agent)")
    agent1 = await factory.find_or_create_agent(spec, reuse_existing=True)
    print(f"   Result: {agent1.name} ({agent1.agent_id})")

    # Second call: Agent exists, will reuse!
    print("\n🏭 Second call: find_or_create (agent exists!)")
    agent2 = await factory.find_or_create_agent(spec, reuse_existing=True)
    print(f"   Result: {agent2.name} ({agent2.agent_id})")

    if agent1.agent_id == agent2.agent_id:
        print("\n✅ SUCCESS: Same agent reused! No duplicate creation!")
    else:
        print("\n❌ Different agents created")

    # Third call: Force create new (reuse_existing=False)
    print("\n🏭 Third call: find_or_create (reuse disabled)")
    agent3 = await factory.find_or_create_agent(spec, reuse_existing=False)
    print(f"   Result: {agent3.name} ({agent3.agent_id})")

    if agent3.agent_id != agent2.agent_id:
        print("✅ New agent created as requested")

    await bus.stop()
    print()


async def demo_status_tracking(discovery):
    """Demo 6: Agent status tracking"""
    print("\n" + "=" * 80)
    print("DEMO 6: Agent Status Tracking")
    print("=" * 80)

    print("\n📊 Current agent statuses:")
    all_agents = await discovery.find_agents(filters={}, only_available=False)
    for agent in all_agents:
        print(f"   • {agent.name}: {agent.status.value}")

    # Update some statuses
    print("\n📝 Updating statuses...")
    await discovery.update_status("agent-data-001", AgentStatus.BUSY)
    await discovery.update_status("agent-market-001", AgentStatus.OFFLINE)

    print("\n📊 Updated statuses:")
    all_agents = await discovery.find_agents(filters={}, only_available=False)
    for agent in all_agents:
        print(f"   • {agent.name}: {agent.status.value}")

    # Search only available
    print("\n🔍 Query: Only AVAILABLE agents")
    available = await discovery.find_agents(filters={}, only_available=True)
    print(f"   Found: {len(available)} available agents")
    for agent in available:
        print(f"   • {agent.name}")

    print()


async def demo_statistics(discovery):
    """Demo 7: Discovery statistics"""
    print("\n" + "=" * 80)
    print("DEMO 7: Discovery Service Statistics")
    print("=" * 80)

    stats = await discovery.get_stats()

    print("\n📊 Discovery Service Stats:")
    print(f"   Total Registrations: {stats['total_registrations']}")
    print(f"   Total Discoveries: {stats['total_discoveries']}")
    print(f"   Registered Agents: {stats['registered_agents']}")
    print(f"   Active Agents: {stats['active_agents']}")
    print(f"   Busy Agents: {stats['busy_agents']}")
    print(f"   Offline Agents: {stats['offline_agents']}")

    capabilities = await discovery.list_capabilities()
    print(f"\n📋 Available Capabilities ({len(capabilities)}):")
    for cap in capabilities:
        print(f"   • {cap}")

    types = await discovery.list_agent_types()
    print(f"\n🏷️  Agent Types ({len(types)}):")
    for agent_type in types:
        print(f"   • {agent_type}")

    print()


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("🔍 AGENT DISCOVERY PROTOCOL (ADP) DEMONSTRATION")
    print("=" * 80)
    print("\nShowing how agents dynamically discover each other by capability")
    print("WITHOUT hardcoded references - the missing piece of multi-agent systems!")
    print()

    try:
        # Demo 1: Basic registration
        discovery = await demo_basic_registration()

        # Demo 2: Capability search
        await demo_capability_search(discovery)

        # Demo 3: Advanced filtering
        await demo_advanced_filtering(discovery)

        # Demo 4: Sorted results
        await demo_sorted_results(discovery)

        # Demo 5: Factory integration (smart reuse!)
        await demo_factory_integration()

        # Demo 6: Status tracking
        await demo_status_tracking(discovery)

        # Demo 7: Statistics
        await demo_statistics(discovery)

        # Final summary
        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETE!")
        print("=" * 80)

        print("\n🌟 What You Just Saw:")
        print("   1. ✅ Dynamic agent registration with rich metadata")
        print("   2. ✅ Capability-based discovery (find by what they can do)")
        print("   3. ✅ Advanced filtering (cost, latency, reputation, tags)")
        print("   4. ✅ Sorted search results (by any metric)")
        print("   5. ✅ Smart agent reuse (find-or-create pattern)")
        print("   6. ✅ Status tracking (available, busy, offline)")
        print("   7. ✅ Discovery statistics and monitoring")

        print("\n💡 Key Benefits:")
        print("   • No hardcoded agent references")
        print("   • Dynamic agent discovery at runtime")
        print("   • Cost-aware agent selection")
        print("   • Performance-based filtering")
        print("   • Automatic agent reuse (saves resources)")
        print("   • Scalable multi-agent ecosystems")

        print("\n🚀 This Is The Missing Piece!")
        print("   Agent Discovery Protocol makes multi-agent systems truly dynamic!")
        print()

        await discovery.stop()

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
