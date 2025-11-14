#!/usr/bin/env python3
"""
Resource Allocation Protocol (RAP) Demonstration

Shows how resource allocation prevents runaway costs and ensures fair resource distribution.
PRODUCTION-SAFE BUDGET CONTROL! 💰

This demo demonstrates:
1. Basic resource allocation and quota enforcement
2. Budget tracking and cost management
3. Automatic quota exceeded detection
4. Contract-based resource allocation (integration)
5. Reputation-based priority allocation (integration)
6. Resource analytics and top consumers
7. Real-time usage monitoring

PREVENTS RUNAWAY COSTS IN PRODUCTION! 🛡️

Usage:
    python examples/resource_allocation_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.resources import (
    get_resource_service,
    ResourceType,
    ResourceQuota,
    AllocationStatus
)
from src.superstandard.protocols.contracts import (
    get_contract_service,
    SLATerms,
    PricingTerms
)
from src.superstandard.protocols.reputation import (
    get_reputation_service
)
from src.superstandard.protocols.integration import enable_auto_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_allocation():
    """Demo 1: Basic resource allocation"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Resource Allocation & Quota Enforcement")
    print("=" * 80)

    resources = get_resource_service()
    await resources.start()

    agent_id = "agent-data-001"

    print(f"\n📝 Requesting resource allocation for {agent_id}...")

    # Request allocation
    allocation = await resources.request_allocation(
        agent_id=agent_id,
        quotas={
            ResourceType.API_CALLS.value: ResourceQuota(
                ResourceType.API_CALLS,
                limit=100,
                description="API call quota"
            ),
            ResourceType.BUDGET_USD.value: ResourceQuota(
                ResourceType.BUDGET_USD,
                limit=10.00,
                description="Budget quota"
            )
        },
        priority=5,
        duration_hours=24,
        auto_approve=True
    )

    print(f"\n✅ Allocation created:")
    print(f"   ID: {allocation.allocation_id}")
    print(f"   Status: {allocation.status.value}")
    print(f"   Priority: {allocation.priority}")
    print(f"   Expires: {allocation.expires_at}")
    print(f"   Quotas:")
    print(f"      API Calls: {allocation.quotas[ResourceType.API_CALLS.value].limit}")
    print(f"      Budget: ${allocation.quotas[ResourceType.BUDGET_USD.value].limit:.2f}")

    # Activate allocation
    await resources.activate_allocation(agent_id)
    print(f"\n🚀 Allocation activated!")

    # Simulate usage
    print(f"\n📊 Simulating resource usage...")
    for i in range(5):
        usage = await resources.record_usage(
            agent_id=agent_id,
            api_calls=random.randint(10, 20),
            cost_usd=random.uniform(1.0, 2.0),
            compute_seconds=random.uniform(50, 100),
            task_id=f"task-{i+1}"
        )
        print(f"   Task {i+1}: {usage.api_calls} calls, ${usage.cost_usd:.2f}")

    # Get usage summary
    summary = await resources.get_usage_summary(agent_id)
    print(f"\n📈 Usage Summary:")
    print(f"   API Calls: {summary['usage']['api_calls']['used']}/{summary['usage']['api_calls']['limit']} ({summary['usage']['api_calls']['percent']:.1f}%)")
    print(f"   Budget: ${summary['usage']['budget_usd']['used']:.2f}/${summary['usage']['budget_usd']['limit']:.2f} ({summary['usage']['budget_usd']['percent']:.1f}%)")
    print(f"   Remaining: ${summary['usage']['budget_usd']['remaining']:.2f}")
    print()


async def demo_budget_exceeded():
    """Demo 2: Budget exceeded detection"""
    print("\n" + "=" * 80)
    print("DEMO 2: Budget Exceeded Detection (PRODUCTION SAFETY!)")
    print("=" * 80)

    resources = get_resource_service()

    agent_id = "agent-expensive-001"

    print(f"\n📝 Creating allocation with LOW budget...")

    # Create allocation with very low budget
    await resources.request_allocation(
        agent_id=agent_id,
        quotas={
            ResourceType.API_CALLS.value: ResourceQuota(ResourceType.API_CALLS, 50),
            ResourceType.BUDGET_USD.value: ResourceQuota(ResourceType.BUDGET_USD, 5.00)
        },
        auto_approve=True
    )

    print(f"   Budget: $5.00")
    print(f"   API Calls: 50")
    print()

    print(f"🔥 Simulating expensive operations...")

    # Use up the budget
    for i in range(10):
        await resources.record_usage(
            agent_id=agent_id,
            api_calls=8,
            cost_usd=0.80,
            task_id=f"expensive-task-{i+1}"
        )

        # Check if budget exceeded
        budget_exceeded = await resources.is_budget_exceeded(agent_id)
        remaining = await resources.get_remaining_budget(agent_id)

        if budget_exceeded:
            print(f"   ⚠️  Task {i+1}: BUDGET EXCEEDED! (remaining: ${remaining:.2f})")
            print(f"   🛑 STOPPING EXECUTION! (This prevents runaway costs!)")
            break
        else:
            print(f"   ✅ Task {i+1}: OK (remaining: ${remaining:.2f})")

    # Get allocation
    allocation = await resources.get_allocation(agent_id)
    print(f"\n🚨 Final Status: {allocation.status.value}")
    print(f"   This is how RAP prevents cost explosions in production!")
    print()


async def demo_multiple_agents():
    """Demo 3: Multiple agents and top consumers"""
    print("\n" + "=" * 80)
    print("DEMO 3: Multiple Agents & Resource Analytics")
    print("=" * 80)

    resources = get_resource_service()

    # Create 4 agents with different usage patterns
    agents = {
        "agent-heavy": {"calls": (80, 120), "cost": (8.0, 12.0), "name": "Heavy User"},
        "agent-medium": {"calls": (40, 60), "cost": (4.0, 6.0), "name": "Medium User"},
        "agent-light": {"calls": (10, 20), "cost": (1.0, 2.0), "name": "Light User"},
        "agent-minimal": {"calls": (2, 5), "cost": (0.2, 0.5), "name": "Minimal User"}
    }

    print(f"\n🏭 Simulating 4 agents with different usage patterns...")
    print()

    for agent_id, profile in agents.items():
        # Allocate resources
        await resources.request_allocation(
            agent_id=agent_id,
            auto_approve=True
        )

        # Simulate usage
        for _ in range(10):
            await resources.record_usage(
                agent_id=agent_id,
                api_calls=random.randint(*profile["calls"]),
                cost_usd=random.uniform(*profile["cost"])
            )

        summary = await resources.get_usage_summary(agent_id)
        print(f"   {profile['name']:15s}: {summary['usage']['api_calls']['used']:4d} calls, ${summary['usage']['budget_usd']['used']:6.2f}")

    # Show top consumers
    print(f"\n🏆 Top Resource Consumers:")
    top_consumers = await resources.get_top_consumers(limit=4)

    for i, consumer in enumerate(top_consumers, 1):
        agent_profile = agents[consumer['agent_id']]
        print(f"\n   {i}. {agent_profile['name']}")
        print(f"      Total Cost: ${consumer['total_cost_usd']:.2f}")
        print(f"      API Calls: {consumer['api_calls']}")
        print(f"      Compute: {consumer['compute_seconds']:.1f}s")

    print()


async def demo_contract_integration():
    """Demo 4: Contract-based resource allocation (integration!)"""
    print("\n" + "=" * 80)
    print("DEMO 4: Contract-Based Resource Allocation (INTEGRATION!)")
    print("=" * 80)

    # Enable integration
    enable_auto_sync()

    contracts = get_contract_service()
    resources = get_resource_service()

    await contracts.start()

    provider_id = "agent-nlp-provider"
    consumer_id = "agent-app-001"

    print(f"\n📝 Creating contract between {provider_id} and {consumer_id}...")

    # Create contract with pricing terms
    contract = await contracts.create_contract(
        provider_id=provider_id,
        consumer_id=consumer_id,
        sla=SLATerms(
            max_latency_ms=1000.0,
            min_quality=0.90,
            min_success_rate=0.95
        ),
        pricing=PricingTerms(
            per_request=0.15,  # $0.15 per request
            monthly_cap=50.00  # $50/month max
        )
    )

    print(f"\n✅ Contract created!")
    print(f"   Contract ID: {contract.contract_id}")
    print(f"   Pricing: ${contract.pricing.per_request:.2f} per request")
    print(f"   Monthly Cap: ${contract.pricing.monthly_cap:.2f}")
    print()

    # Check if resource allocation was auto-created!
    print(f"🔍 Checking for auto-created resource allocation...")
    allocation = await resources.get_allocation(consumer_id)

    if allocation:
        print(f"\n💰 MAGIC! Resource allocation auto-created from contract!")
        print(f"   Agent: {consumer_id}")
        print(f"   Budget: ${allocation.quotas[ResourceType.BUDGET_USD.value].limit:.2f} (from contract!)")
        print(f"   API Calls: {allocation.quotas[ResourceType.API_CALLS.value].limit} (calculated!)")
        print()
        print(f"💡 This is the power of protocol integration!")
        print(f"   Contracts automatically configure resource limits!")
    else:
        print(f"   ⚠️  No allocation found (integration may need debugging)")

    print()


async def demo_reputation_integration():
    """Demo 5: Reputation-based priority allocation"""
    print("\n" + "=" * 80)
    print("DEMO 5: Reputation-Based Priority Allocation (SMART!)")
    print("=" * 80)

    # Enable integration
    enable_auto_sync()

    reputation = get_reputation_service()
    resources = get_resource_service()

    await reputation.start()

    # Create 3 agents with different reputations
    agents = [
        ("agent-excellent", "Excellent Agent", 0.95),
        ("agent-good", "Good Agent", 0.75),
        ("agent-poor", "Poor Agent", 0.40)
    ]

    print(f"\n🎯 Creating agents with different reputations...")
    print()

    for agent_id, name, target_rep in agents:
        # Build reputation
        for i in range(20):
            success_rate = target_rep + random.uniform(-0.05, 0.05)
            await reputation.record_outcome(
                agent_id=agent_id,
                task_id=f"task-{i}",
                success=random.random() < success_rate,
                quality_score=random.uniform(target_rep - 0.05, target_rep + 0.05),
                duration_ms=random.uniform(400, 600)
            )

        rep = await reputation.get_reputation(agent_id)
        print(f"   {name:20s}: {rep.overall_score:.1%} reputation")

    print(f"\n📊 Requesting resource allocations (watch priority assignment!)...")
    print()

    for agent_id, name, target_rep in agents:
        # Request allocation (integration will set priority based on reputation!)
        allocation = await resources.request_allocation(
            agent_id=agent_id,
            quotas={
                ResourceType.API_CALLS.value: ResourceQuota(ResourceType.API_CALLS, 1000)
            },
            auto_approve=True
        )

        rep = await reputation.get_reputation(agent_id)
        print(f"   {name:20s}:")
        print(f"      Reputation: {rep.overall_score:.1%}")
        print(f"      Priority: {allocation.priority}/10 (auto-assigned!)")
        print(f"      API Quota: {allocation.quotas[ResourceType.API_CALLS.value].limit:.0f} (boosted!)")
        print()

    print(f"💡 High-reputation agents get:")
    print(f"   • Higher priority (9-10 vs 1-5)")
    print(f"   • Larger quotas (1.5x vs 0.5x multiplier)")
    print(f"   • Better resource access")
    print(f"\n   THE SYSTEM REWARDS GOOD PERFORMANCE!")
    print()


async def demo_stats():
    """Demo 6: Service statistics"""
    print("\n" + "=" * 80)
    print("DEMO 6: Resource Service Statistics")
    print("=" * 80)

    resources = get_resource_service()

    stats = await resources.get_stats()

    print("\n📊 Service Stats:")
    print(f"   Total Allocations: {stats['total_allocations']}")
    print(f"   Active Allocations: {stats['active_count']}")
    print(f"   Exhausted Allocations: {stats['exhausted_count']}")
    print(f"   Total Usage Records: {stats['total_usage_records']}")
    print(f"   Total Cost: ${stats['total_cost_usd']:.2f}")
    print(f"   Total API Calls: {stats['total_api_calls']}")
    print(f"   Budget Exceeded Count: {stats['budget_exceeded_count']}")
    print(f"   Avg Cost per Agent: ${stats['avg_cost_per_agent']:.2f}")
    print()


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("💰 RESOURCE ALLOCATION PROTOCOL (RAP) DEMONSTRATION")
    print("=" * 80)
    print("\nShowing how RAP prevents runaway costs and ensures fair")
    print("resource distribution in production multi-agent systems!")
    print()

    try:
        # Demo 1: Basic allocation
        await demo_basic_allocation()

        # Demo 2: Budget exceeded
        await demo_budget_exceeded()

        # Demo 3: Multiple agents
        await demo_multiple_agents()

        # Demo 4: Contract integration
        await demo_contract_integration()

        # Demo 5: Reputation integration
        await demo_reputation_integration()

        # Demo 6: Statistics
        await demo_stats()

        # Final summary
        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETE!")
        print("=" * 80)

        print("\n🌟 What You Just Saw:")
        print("   1. ✅ Basic resource allocation and quota enforcement")
        print("   2. ✅ Automatic budget exceeded detection")
        print("   3. ✅ Multi-agent resource analytics")
        print("   4. ✅ Contract-based auto-allocation (integration!)")
        print("   5. ✅ Reputation-based priority allocation (integration!)")
        print("   6. ✅ Service statistics and monitoring")

        print("\n💡 Key Insights:")
        print("   • Budget caps prevent runaway costs")
        print("   • Automatic enforcement ensures compliance")
        print("   • Contract pricing auto-configures limits")
        print("   • High-reputation agents get priority")
        print("   • Complete audit trail for all usage")

        print("\n🚀 This Changes Everything!")
        print("   • Deploy autonomous agents safely in production")
        print("   • Predictable, controlled costs")
        print("   • Fair resource distribution")
        print("   • Integration with contracts and reputation")
        print("   • Real-time cost tracking and analytics")

        print("\n🎯 Result: PRODUCTION-SAFE MULTI-AGENT SYSTEMS!")
        print()

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
