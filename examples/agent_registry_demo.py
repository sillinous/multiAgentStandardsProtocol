"""
Agent Registry Demo

Demonstrates the Agent Registry & Catalog System for discovering, searching,
and browsing all available agents.

This shows:
1. Auto-discovery of generated agents
2. Capability-based search
3. Category filtering
4. Marketplace view
5. Export catalog

Run:
    python examples/agent_registry_demo.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.agent_factory import AgentRegistry, get_registry


def main():
    print("\n" + "="*80)
    print("🏪 AGENT REGISTRY & CATALOG DEMO")
    print("="*80)

    # Create registry
    print("\n📚 Creating Agent Registry...")
    registry = get_registry()

    # Discover agents
    print("\n🔍 Discovering agents...")
    count = registry.discover_agents()
    print(f"   Found {count} agents")

    # Show statistics
    stats = registry.get_stats()
    print("\n📊 Registry Statistics:")
    print(f"   Total Agents: {stats['total_agents']}")
    print(f"   Total Capabilities: {stats['total_capabilities']}")
    print(f"   Total Categories: {stats['total_categories']}")
    print(f"   Average Cost: ${stats['avg_cost']:.2f}/request")
    print(f"   Average Quality: {stats['avg_quality']:.0%}")

    # Show all capabilities
    print("\n🎯 Available Capabilities:")
    capabilities = registry.get_capabilities()
    for cap in capabilities:
        agents = registry.search(capability=cap)
        print(f"   - {cap} ({len(agents)} agents)")

    # Show all categories
    print("\n📁 Categories:")
    categories = registry.get_categories()
    for cat in categories:
        agents = registry.get_by_category(cat)
        print(f"   - {cat} ({len(agents)} agents)")

    # Search examples
    print("\n" + "="*80)
    print("🔎 SEARCH EXAMPLES")
    print("="*80)

    # Search by capability
    print("\n1️⃣  Search by Capability: 'competitive_analysis'")
    results = registry.search(capability="competitive_analysis")
    for agent in results:
        print(f"   ✓ {agent.name}")
        print(f"     ID: {agent.agent_id}")
        print(f"     Cost: ${agent.cost_per_request:.2f}/req")
        print(f"     Quality: {agent.quality_baseline:.0%}")

    # Search by category
    print("\n2️⃣  Search by Category: 'Vision and Strategy'")
    results = registry.search(category="Vision and Strategy")
    for agent in results:
        print(f"   ✓ {agent.name}")
        print(f"     Process: {agent.apqc_process}")
        print(f"     Capabilities: {', '.join(agent.capabilities)}")

    # Search with filters
    print("\n3️⃣  Search with Filters: max_cost=$10, min_quality=0.85")
    results = registry.search(max_cost=10.0, min_quality=0.85)
    print(f"   Found {len(results)} agents:")
    for agent in results:
        print(f"   ✓ {agent.name} - ${agent.cost_per_request:.2f}, {agent.quality_baseline:.0%}")

    # Get specific agent
    print("\n4️⃣  Get Specific Agent: 'apqc-1.1.1.1'")
    agent = registry.get_by_id("apqc-1.1.1.1")
    if agent:
        print(f"   ✓ Found: {agent.name}")
        print(f"     Description: {agent.metadata.get('description', 'N/A')}")
        print(f"     File: {agent.file_path}")
        print(f"     Class: {agent.class_name}")

    # Show marketplace
    registry.show_marketplace()

    # Export catalog
    print("\n" + "="*80)
    print("💾 EXPORT CATALOG")
    print("="*80)

    output_path = registry.export_catalog("agent_catalog.json")
    print(f"\n✅ Catalog exported successfully!")
    print(f"   View at: {output_path}")

    # Summary
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print(f"""
Agent Registry Features Demonstrated:

✅ Auto-discovery of agents from directory
✅ Capability-based search
✅ Category filtering
✅ Cost and quality filters
✅ Agent retrieval by ID
✅ Marketplace view
✅ Catalog export to JSON
✅ Comprehensive statistics

The Agent Registry makes all generated agents instantly discoverable
and searchable - enabling easy composition into workflows!

Next Steps:
- Generate 15-20 more APQC 1.0 agents
- Integrate with Discovery Protocol
- Build visual marketplace dashboard
""")


if __name__ == "__main__":
    main()
