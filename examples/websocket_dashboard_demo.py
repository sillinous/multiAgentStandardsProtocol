#!/usr/bin/env python3
"""
WebSocket Dashboard Demo

Demonstrates the production WebSocket server with live event streaming.

This demo:
1. Starts the production WebSocket server
2. Simulates agent executions and opportunity discoveries
3. Broadcasts events in real-time to connected dashboard clients
4. Runs indefinitely until Ctrl+C

Usage:
    # Install dependencies first:
    pip install aiohttp

    # Run the demo:
    python examples/websocket_dashboard_demo.py

    # Then open browser to:
    http://localhost:8000/dashboard

The dashboard will show real-time updates as events occur!
"""

import asyncio
import logging
import sys
from pathlib import Path
import random
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.api.websocket_server import DashboardWebSocketServer
from src.superstandard.monitoring.dashboard import get_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventSimulator:
    """Simulates realistic agent execution events"""

    def __init__(self):
        self.dashboard = get_dashboard()
        self.agent_names = [
            "IdentifyCompetitorsAgent",
            "IdentifyEconomicTrendsAgent",
            "IdentifyDemographicsAgent",
            "IdentifyMarketGapsAgent"
        ]
        self.opportunities = [
            {
                "title": "AI-Powered Market Research Platform",
                "description": "Strong demand for automated market research tools in tech sector. Low competition, high growth potential.",
                "category": "SaaS Product",
                "confidence": 0.89,
                "revenue": "$500K-$2M ARR"
            },
            {
                "title": "Demographics Analytics Service",
                "description": "Growing need for real-time demographics insights. Census data integration opportunity.",
                "category": "Data Service",
                "confidence": 0.82,
                "revenue": "$200K-$800K ARR"
            },
            {
                "title": "Economic Trends API",
                "description": "Demand for easy-to-use economic data API. FRED data integration with ML predictions.",
                "category": "API Service",
                "confidence": 0.78,
                "revenue": "$100K-$500K ARR"
            },
            {
                "title": "Competitive Intelligence Platform",
                "description": "Businesses need automated competitive monitoring. Multi-source data aggregation opportunity.",
                "category": "Analytics Platform",
                "confidence": 0.85,
                "revenue": "$300K-$1.5M ARR"
            }
        ]

    async def simulate_agent_execution(self):
        """Simulate an agent execution"""
        agent_name = random.choice(self.agent_names)
        agent_id = f"agent-{random.randint(1000, 9999)}"

        # Agent started
        await self.dashboard.agent_started(
            agent_id=agent_id,
            agent_name=agent_name,
            task_description=f"Analyzing market data"
        )

        # Simulate work
        duration = random.uniform(800, 2500)
        await asyncio.sleep(duration / 1000)

        # Agent completed
        success = random.random() > 0.1  # 90% success rate
        quality_score = random.uniform(92, 99) if success else random.uniform(60, 85)

        await self.dashboard.agent_completed(
            agent_id=agent_id,
            agent_name=agent_name,
            task_description=f"Analyzing market data",
            duration_ms=duration,
            success=success,
            data_source=f"{agent_name.replace('Agent', '')} Data Source",
            quality_score=quality_score
        )

        return success

    async def simulate_opportunity_discovery(self):
        """Simulate opportunity discovery"""
        opp = random.choice(self.opportunities)

        await self.dashboard.opportunity_discovered(
            opportunity_id=f"opp-{random.randint(1000, 9999)}",
            title=opp["title"],
            description=opp["description"],
            confidence_score=opp["confidence"],
            revenue_potential=opp["revenue"],
            category=opp["category"]
        )

    async def simulate_synthesis(self):
        """Simulate synthesis phase"""
        phase = random.choice([
            "Data Collection",
            "Pattern Analysis",
            "Insight Generation",
            "Quality Assessment"
        ])

        await self.dashboard.synthesis_started(
            phase=phase,
            description=f"Starting {phase} synthesis"
        )

        # Simulate synthesis work
        duration = random.uniform(1500, 3500)
        await asyncio.sleep(duration / 1000)

        patterns_found = random.randint(5, 20)
        await self.dashboard.synthesis_completed(
            phase=phase,
            duration_ms=duration,
            patterns_found=patterns_found
        )

    async def run_simulation_loop(self):
        """Run continuous event simulation"""
        logger.info("🎬 Starting event simulation...")
        logger.info("   Events will be broadcast to all connected dashboard clients")
        logger.info("")

        iteration = 0
        opportunities_discovered = 0

        try:
            while True:
                iteration += 1
                logger.info(f"📍 Simulation iteration {iteration}")

                # Simulate 2-3 agent executions
                num_agents = random.randint(2, 3)
                for i in range(num_agents):
                    success = await self.simulate_agent_execution()
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                # Occasionally simulate synthesis
                if random.random() > 0.6:
                    await self.simulate_synthesis()
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                # Occasionally discover opportunity
                if random.random() > 0.5 and opportunities_discovered < 10:
                    await self.simulate_opportunity_discovery()
                    opportunities_discovered += 1
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                # Update system health
                await self.dashboard.system_health_updated(
                    cpu_percent=random.uniform(10, 30),
                    memory_percent=random.uniform(30, 50),
                    active_agents=random.randint(0, 3)
                )

                # Wait before next iteration
                await asyncio.sleep(random.uniform(3, 6))

        except KeyboardInterrupt:
            logger.info("\n⚠️  Simulation stopped by user")


async def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🚀 WEBSOCKET DASHBOARD DEMO")
    print("=" * 80)
    print("\nThis demo will:")
    print("  1. Start production WebSocket server")
    print("  2. Simulate real-time agent executions and discoveries")
    print("  3. Broadcast events to connected dashboard clients")
    print("\nInstructions:")
    print("  • Open http://localhost:8000/dashboard in your browser")
    print("  • Watch events appear in real-time as they're generated!")
    print("  • Press Ctrl+C to stop")
    print("\n" + "=" * 80)
    print()

    # Create WebSocket server
    server = DashboardWebSocketServer(
        host='0.0.0.0',
        port=8000
    )

    # Start server
    await server.start()

    # Create event simulator
    simulator = EventSimulator()

    try:
        # Run simulation
        await simulator.run_simulation_loop()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Received shutdown signal")

    finally:
        # Stop server
        await server.stop()
        logger.info("\n👋 Demo complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
