#!/usr/bin/env python3
"""
Agent Reputation Protocol (ARP) Demonstration

Shows how agent reputations evolve over time based on actual performance.
THE SYSTEM LEARNS which agents are best and automatically optimizes selection!

This demo demonstrates:
1. Recording task outcomes
2. Multi-dimensional reputation scoring
3. Reputation trends (improving, stable, declining)
4. Automatic discovery integration
5. Top agent rankings
6. Real-time reputation evolution

THE SELF-IMPROVING SYSTEM IN ACTION! 🧠

Usage:
    python examples/agent_reputation_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.reputation import (
    get_reputation_service,
    ReputationDimension
)
from src.superstandard.protocols.discovery import (
    get_discovery_service,
    AgentCapability,
    AgentMetadata
)
from src.superstandard.protocols.integration import enable_auto_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_reputation():
    """Demo 1: Basic reputation tracking"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Reputation Tracking")
    print("=" * 80)

    reputation = get_reputation_service()
    await reputation.start()

    agent_id = "agent-data-001"

    print(f"\n📝 Recording task outcomes for {agent_id}...")
    print()

    # Record some successful tasks
    for i in range(5):
        await reputation.record_outcome(
            agent_id=agent_id,
            task_id=f"task-{i+1}",
            success=True,
            quality_score=random.uniform(0.92, 0.98),
            duration_ms=random.uniform(400, 600),
            cost=0.15
        )
        print(f"   Task {i+1}: ✅ Success")

    # Get reputation
    rep = await reputation.get_reputation(agent_id)

    print(f"\n📊 Reputation after 5 tasks:")
    print(f"   Overall Score: {rep.overall_score:.1%}")
    print(f"   Success Rate: {rep.successful_tasks}/{rep.total_tasks}")
    print(f"   Avg Quality: {rep.avg_quality:.1%}")
    print(f"   Avg Duration: {rep.avg_duration_ms:.0f}ms")
    print(f"   Confidence: {rep.confidence_level:.1%}")
    print()

    return reputation


async def demo_reputation_evolution():
    """Demo 2: Watch reputation evolve over time"""
    print("\n" + "=" * 80)
    print("DEMO 2: Reputation Evolution Over Time")
    print("=" * 80)

    reputation = get_reputation_service()

    agent_id = "agent-market-001"

    print(f"\n🎯 Simulating 50 task executions for {agent_id}...")
    print("   (Watch reputation change in real-time!)")
    print()

    checkpoints = [10, 20, 30, 40, 50]
    for i in range(50):
        # Gradually improving performance
        success_rate = 0.7 + (i / 50) * 0.25  # 70% → 95%
        quality_base = 0.80 + (i / 50) * 0.15  # 80% → 95%

        success = random.random() < success_rate
        quality = random.uniform(quality_base - 0.05, quality_base + 0.05) if success else random.uniform(0.3, 0.6)
        duration = random.uniform(800, 1200) if success else random.uniform(2000, 4000)

        await reputation.record_outcome(
            agent_id=agent_id,
            task_id=f"task-{i+1}",
            success=success,
            quality_score=quality,
            duration_ms=duration,
            cost=0.20
        )

        # Show progress at checkpoints
        if (i + 1) in checkpoints:
            rep = await reputation.get_reputation(agent_id)
            print(f"   After {i+1:2d} tasks: {rep.overall_score:.1%} ({rep.reputation_trend})")

    # Final reputation
    rep = await reputation.get_reputation(agent_id)
    print(f"\n✅ Final Reputation:")
    print(f"   Overall: {rep.overall_score:.1%}")
    print(f"   Trend: {rep.reputation_trend}")
    print(f"   Success Rate: {rep.successful_tasks}/{rep.total_tasks} = {rep.successful_tasks/rep.total_tasks:.1%}")
    print()


async def demo_multi_dimensional():
    """Demo 3: Multi-dimensional reputation scores"""
    print("\n" + "=" * 80)
    print("DEMO 3: Multi-Dimensional Reputation Scores")
    print("=" * 80)

    reputation = get_reputation_service()

    agent_id = "agent-nlp-001"

    print(f"\n📊 Recording varied performance for {agent_id}...")

    # High quality, but slow and expensive
    for i in range(15):
        await reputation.record_outcome(
            agent_id=agent_id,
            task_id=f"task-{i+1}",
            success=True,
            quality_score=random.uniform(0.95, 0.99),  # Very high quality
            duration_ms=random.uniform(2000, 3000),  # Slow
            cost=0.30  # Expensive
        )

    rep = await reputation.get_reputation(agent_id)

    print(f"\n📈 Dimension Breakdown:")
    for dim_name, dim_score in rep.dimension_scores.items():
        print(f"   {dim_name:20s}: {dim_score.score:.1%} ({dim_score.trend})")

    print(f"\n💡 Analysis:")
    print(f"   • High quality ({rep.dimension_scores['quality'].score:.1%}) but slow ({rep.dimension_scores['speed'].score:.1%})")
    print(f"   • Overall: {rep.overall_score:.1%}")
    print()


async def demo_agent_comparison():
    """Demo 4: Compare multiple agents"""
    print("\n" + "=" * 80)
    print("DEMO 4: Agent Comparison & Rankings")
    print("=" * 80)

    reputation = get_reputation_service()

    # Create 4 agents with different profiles
    agents = {
        "agent-premium": {
            "name": "Premium Agent",
            "profile": "High quality, expensive",
            "success_rate": 0.98,
            "quality_range": (0.95, 0.99),
            "duration_range": (300, 500),
            "cost": 0.25
        },
        "agent-fast": {
            "name": "Fast Agent",
            "profile": "Very fast, lower quality",
            "success_rate": 0.90,
            "quality_range": (0.80, 0.90),
            "duration_range": (200, 400),
            "cost": 0.15
        },
        "agent-budget": {
            "name": "Budget Agent",
            "profile": "Cheap, acceptable quality",
            "success_rate": 0.85,
            "quality_range": (0.75, 0.85),
            "duration_range": (1000, 1500),
            "cost": 0.05
        },
        "agent-unreliable": {
            "name": "Unreliable Agent",
            "profile": "Inconsistent performance",
            "success_rate": 0.70,
            "quality_range": (0.50, 0.95),  # High variance
            "duration_range": (500, 2000),
            "cost": 0.10
        }
    }

    print("\n🏭 Simulating 30 tasks for each agent...")

    for agent_id, profile in agents.items():
        for i in range(30):
            success = random.random() < profile["success_rate"]
            quality = random.uniform(*profile["quality_range"]) if success else random.uniform(0.3, 0.6)
            duration = random.uniform(*profile["duration_range"])

            await reputation.record_outcome(
                agent_id=agent_id,
                task_id=f"task-{i+1}",
                success=success,
                quality_score=quality,
                duration_ms=duration,
                cost=profile["cost"]
            )

    # Show rankings
    print("\n🏆 Agent Rankings (by overall reputation):")
    top_agents = await reputation.get_top_agents(limit=10)

    for i, rep in enumerate(top_agents, 1):
        agent_profile = agents[rep.agent_id]
        print(f"\n   {i}. {agent_profile['name']}")
        print(f"      Profile: {agent_profile['profile']}")
        print(f"      Overall: {rep.overall_score:.1%}")
        print(f"      Success: {rep.successful_tasks}/{rep.total_tasks} = {rep.successful_tasks/rep.total_tasks:.1%}")
        print(f"      Quality: {rep.avg_quality:.1%}")
        print(f"      Speed: {rep.avg_duration_ms:.0f}ms")
        print(f"      Cost: ${rep.avg_cost:.2f}")

    print()


async def demo_discovery_integration():
    """Demo 5: Automatic discovery integration"""
    print("\n" + "=" * 80)
    print("DEMO 5: Discovery Integration (THE MAGIC!)")
    print("=" * 80)

    # Enable auto-sync
    enable_auto_sync()

    discovery = get_discovery_service()
    reputation = get_reputation_service()
    await discovery.start()

    agent_id = "agent-integrated-001"

    # Register agent with discovery
    await discovery.register_agent(
        agent_id=agent_id,
        name="IntegratedAgent",
        agent_type="data_analyst",
        capabilities=[
            AgentCapability("data_analysis", "1.0.0", {}, "Data analysis")
        ],
        metadata=AgentMetadata(
            reputation_score=0.5,  # Initial default
            tags=["test", "integrated"]
        )
    )

    print(f"\n📝 Agent registered with discovery")
    print(f"   Initial reputation: 0.50 (default)")
    print()

    print("🎯 Recording successful tasks...")

    # Record tasks - reputation auto-updates discovery!
    for i in range(10):
        await reputation.record_outcome(
            agent_id=agent_id,
            task_id=f"task-{i+1}",
            success=True,
            quality_score=random.uniform(0.90, 0.98),
            duration_ms=random.uniform(400, 600),
            cost=0.15
        )

    # Check discovery - reputation should be updated!
    agent_from_discovery = await discovery.get_agent(agent_id)
    rep_from_service = await reputation.get_reputation(agent_id)

    print(f"\n✅ Reputation automatically synced to discovery!")
    print(f"   Reputation Service: {rep_from_service.overall_score:.1%}")
    print(f"   Discovery Metadata: {agent_from_discovery.metadata.reputation_score:.1%}")
    print(f"   Success Rate: {agent_from_discovery.metadata.success_rate:.1%}")
    print(f"   Avg Quality: {agent_from_discovery.metadata.avg_quality_score:.1%}")
    print()

    print("💡 This means:")
    print("   • Discovery searches now use REAL reputation data!")
    print("   • Agents with better performance rank higher!")
    print("   • THE SYSTEM LEARNS AND OPTIMIZES ITSELF!")
    print()


async def demo_reputation_trend():
    """Demo 6: Reputation trends (improving/declining)"""
    print("\n" + "=" * 80)
    print("DEMO 6: Reputation Trends (Learning Over Time)")
    print("=" * 80)

    reputation = get_reputation_service()

    agent_id = "agent-learning-001"

    print(f"\n🎓 Simulating learning agent (performance improves over time)...")
    print()

    phases = [
        ("Learning Phase", 20, 0.70, 0.75),
        ("Improving Phase", 20, 0.85, 0.88),
        ("Expert Phase", 20, 0.95, 0.97),
    ]

    for phase_name, num_tasks, success_rate, quality_base in phases:
        print(f"   {phase_name}:")

        for i in range(num_tasks):
            success = random.random() < success_rate
            quality = random.uniform(quality_base - 0.05, quality_base + 0.05) if success else random.uniform(0.3, 0.6)

            await reputation.record_outcome(
                agent_id=agent_id,
                task_id=f"task-{i+1}",
                success=success,
                quality_score=quality,
                duration_ms=random.uniform(400, 800),
                cost=0.15
            )

        rep = await reputation.get_reputation(agent_id)
        print(f"      Reputation: {rep.overall_score:.1%} ({rep.reputation_trend})")

    rep = await reputation.get_reputation(agent_id)

    print(f"\n✅ Final State:")
    print(f"   Overall: {rep.overall_score:.1%}")
    print(f"   Trend: {rep.reputation_trend}")
    print(f"   Success: {rep.successful_tasks}/{rep.total_tasks} = {rep.successful_tasks/rep.total_tasks:.1%}")
    print()


async def demo_stats():
    """Demo 7: Service statistics"""
    print("\n" + "=" * 80)
    print("DEMO 7: Reputation Service Statistics")
    print("=" * 80)

    reputation = get_reputation_service()

    stats = await reputation.get_stats()

    print("\n📊 Service Stats:")
    print(f"   Total Outcomes Recorded: {stats['total_outcomes_recorded']}")
    print(f"   Agents Tracked: {stats['total_agents_tracked']}")
    print(f"   Reputation Updates: {stats['total_reputation_updates']}")
    print(f"   Agents with Reputation: {stats['agents_with_reputation']}")
    print(f"   Avg Overall Score: {stats['avg_overall_score']:.1%}")
    print()


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("🧠 AGENT REPUTATION PROTOCOL (ARP) DEMONSTRATION")
    print("=" * 80)
    print("\nShowing how agents learn from experience and the system")
    print("automatically optimizes agent selection based on real performance!")
    print()

    try:
        # Demo 1: Basic reputation
        await demo_basic_reputation()

        # Demo 2: Evolution over time
        await demo_reputation_evolution()

        # Demo 3: Multi-dimensional scores
        await demo_multi_dimensional()

        # Demo 4: Agent comparison
        await demo_agent_comparison()

        # Demo 5: Discovery integration (THE MAGIC!)
        await demo_discovery_integration()

        # Demo 6: Trends
        await demo_reputation_trend()

        # Demo 7: Statistics
        await demo_stats()

        # Final summary
        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETE!")
        print("=" * 80)

        print("\n🌟 What You Just Saw:")
        print("   1. ✅ Task outcomes recorded and reputation calculated")
        print("   2. ✅ Reputation evolving over time (improving/declining)")
        print("   3. ✅ Multi-dimensional scoring (quality, speed, cost, etc.)")
        print("   4. ✅ Agent rankings (best to worst)")
        print("   5. ✅ Auto-sync with discovery (THE MAGIC!)")
        print("   6. ✅ Learning trends (agents improving over time)")
        print("   7. ✅ Service statistics and monitoring")

        print("\n💡 Key Insights:")
        print("   • Reputation reflects REAL performance, not guesses")
        print("   • Recent performance weighted more heavily")
        print("   • Multi-dimensional scoring captures nuanced behavior")
        print("   • Discovery automatically uses reputation for selection")
        print("   • THE SYSTEM OPTIMIZES ITSELF OVER TIME!")

        print("\n🚀 This Changes Everything!")
        print("   • Agents with better track records get selected more")
        print("   • Poor performers get filtered out automatically")
        print("   • Cost/quality trade-offs visible and measurable")
        print("   • The platform learns and improves continuously")

        print("\n🎯 Result: SELF-IMPROVING MULTI-AGENT ECOSYSTEM!")
        print()

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
