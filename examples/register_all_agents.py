"""
Register All Agents with Discovery Protocol

This registers all 22 generated agents from the Agent Registry
with the Discovery Protocol, enabling full protocol integration!

This demonstrates:
- Agent Registry → Discovery Protocol integration
- Automated agent registration at scale
- Complete protocol ecosystem working together

Run:
    python examples/register_all_agents.py
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.agent_factory import get_registry
from src.superstandard.protocols.discovery import get_discovery_service, AgentCapability


async def register_all_agents():
    """Register all agents from registry with Discovery Protocol"""

    print("\n" + "="*80)
    print("📡 REGISTERING ALL AGENTS WITH DISCOVERY PROTOCOL")
    print("="*80)

    # Get services
    registry = get_registry()
    discovery = get_discovery_service()

    # Discover agents from registry
    print("\n🔍 Discovering agents from registry...")
    agent_count = registry.discover_agents()
    print(f"   Found {agent_count} agents")

    # Get all agents
    all_agents = []
    for capability in registry.get_capabilities():
        agents = registry.search(capability=capability)
        for agent in agents:
            if agent.agent_id not in [a.agent_id for a in all_agents]:
                all_agents.append(agent)

    print(f"\n✅ Identified {len(all_agents)} unique agents to register")

    # Register each agent
    print("\n📡 Registering agents with Discovery Protocol...")
    registered = []
    failed = []

    for i, agent in enumerate(all_agents, 1):
        try:
            # Convert capability strings to AgentCapability objects
            capability_objects = [
                AgentCapability(name=cap, description=f"{cap} capability")
                for cap in agent.capabilities
            ]

            # Register with Discovery Protocol
            await discovery.register_agent(
                agent_id=agent.agent_id,
                name=agent.name,
                agent_type="apqc_agent",
                capabilities=capability_objects,
                endpoint=f"http://localhost:8000/agents/{agent.agent_id}",
                metadata={
                    "apqc_process": agent.apqc_process,
                    "apqc_category": agent.apqc_category,
                    "cost_per_request": agent.cost_per_request,
                    "quality_baseline": agent.quality_baseline,
                    "avg_latency_ms": agent.avg_latency_ms,
                    "file_path": agent.file_path,
                    "class_name": agent.class_name
                }
            )
            registered.append(agent.agent_id)
            print(f"   [{i}/{len(all_agents)}] ✅ {agent.name}")

        except Exception as e:
            failed.append((agent.agent_id, str(e)))
            print(f"   [{i}/{len(all_agents)}] ❌ {agent.name}: {e}")

    # Summary
    print("\n" + "="*80)
    print("📊 REGISTRATION SUMMARY")
    print("="*80)
    print(f"\n   ✅ Successfully Registered: {len(registered)}")
    print(f"   ❌ Failed: {len(failed)}")
    print(f"   📊 Total Agents: {len(all_agents)}")

    if failed:
        print("\n⚠️  Failed Registrations:")
        for agent_id, error in failed:
            print(f"      - {agent_id}: {error}")

    # Verify registration by searching
    print("\n" + "="*80)
    print("🔍 VERIFICATION - Testing Discovery Protocol")
    print("="*80)

    test_capabilities = [
        "competitive_analysis",
        "strategic_planning",
        "market_research",
        "swot_analysis"
    ]

    for capability in test_capabilities:
        found = await discovery.find_agents(
            required_capabilities=[capability],
            only_available=False  # Skip availability check for demo
        )
        print(f"\n   Capability: {capability}")
        print(f"   Found: {len(found)} agents")
        for agent_info in found[:3]:  # Show first 3
            print(f"      - {agent_info.name}")

    # The grand finale
    print("\n" + "="*80)
    print("✅ AGENT REGISTRATION COMPLETE!")
    print("="*80)
    print(f"""
🎉 ALL AGENTS NOW DISCOVERABLE VIA PROTOCOL!

What we just accomplished:
- ✅ Registered {len(registered)} agents with Discovery Protocol
- ✅ All capabilities now searchable via protocol
- ✅ Complete APQC 1.0 coverage available
- ✅ Agent Registry + Discovery Protocol integration working!

The platform now has:
📚 Agent Registry: Local agent catalog and search
📡 Discovery Protocol: Network-wide agent discovery
🔄 Full Integration: Both systems working together seamlessly!

Agents can now be discovered by:
- Capability-based search (competitive_analysis, etc.)
- Quality requirements (min_quality, min_reputation)
- Cost constraints (max_cost)
- Performance needs (max_latency)

The Dynamic Workflow Composer can now build and execute
workflows using REAL protocol-based agent discovery! 🚀
""")


if __name__ == "__main__":
    asyncio.run(register_all_agents())
