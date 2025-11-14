#!/usr/bin/env python3
"""
Live Dashboard Demo - Real-Time Monitoring of Autonomous Discovery

This demo showcases the complete integration of:
1. Autonomous Business Opportunity Discovery System
2. Real-Time Dashboard with Event Broadcasting
3. Production Agents with Quality Monitoring

Run this script and open dashboard.html in your browser to see
the autonomous agents working in real-time!

Usage:
    python examples/live_dashboard_demo.py

Then open: dashboard.html in your browser
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import webbrowser
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.orchestration.opportunity_discovery import (
    OpportunityDiscoveryOrchestrator,
    BusinessOpportunity
)
from src.superstandard.monitoring.dashboard import (
    DashboardState,
    get_dashboard,
    EventType
)
from src.superstandard.services.factory import ServiceFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveDashboardDemo:
    """
    Live Dashboard Demo orchestrating the complete system.

    This demo:
    - Initializes the dashboard state
    - Runs the opportunity discovery system
    - Broadcasts all events in real-time
    - Exports dashboard data for browser visualization
    """

    def __init__(self):
        """Initialize the live demo."""
        self.dashboard = get_dashboard()
        self.service_factory = ServiceFactory()
        self.orchestrator = OpportunityDiscoveryOrchestrator(
            service_factory=self.service_factory,
            dashboard_state=self.dashboard
        )

        # Output file for dashboard data
        self.output_file = Path(__file__).parent.parent / "dashboard_data.json"

        logger.info("✅ Live Dashboard Demo initialized")

    async def export_dashboard_state(self):
        """Export current dashboard state to JSON for browser consumption."""
        state_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.dashboard.metrics,
            "events": [event.to_dict() for event in self.dashboard.event_history],
            "opportunities": self.dashboard.opportunities,
            "active_agents": len([
                a for a in self.dashboard.active_agents.values()
                if a["status"] == "running"
            ])
        }

        try:
            with open(self.output_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.info(f"📊 Dashboard state exported to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to export dashboard state: {e}")

    async def run_discovery_scenario(
        self,
        industry: str,
        geography: str,
        min_confidence: float = 0.75
    ):
        """
        Run a complete discovery scenario with real-time dashboard updates.

        Args:
            industry: Target industry (e.g., "technology")
            geography: Geographic focus (e.g., "United States")
            min_confidence: Minimum confidence threshold (0.0 to 1.0)
        """
        logger.info("=" * 80)
        logger.info("🚀 LIVE DASHBOARD DEMO - AUTONOMOUS OPPORTUNITY DISCOVERY")
        logger.info("=" * 80)
        logger.info(f"📊 Industry: {industry}")
        logger.info(f"🌍 Geography: {geography}")
        logger.info(f"🎯 Min Confidence: {min_confidence * 100}%")
        logger.info("")
        logger.info("💡 Open dashboard.html in your browser to see real-time updates!")
        logger.info("")

        # Broadcast system startup
        await self.dashboard.system_health_updated(
            cpu_percent=15.0,
            memory_percent=45.0,
            active_agents=0
        )

        try:
            # Run the discovery process
            logger.info("🔍 Starting autonomous discovery process...")
            logger.info("")

            opportunities = await self.orchestrator.discover_opportunities(
                industry=industry,
                geography=geography,
                min_confidence=min_confidence
            )

            # Export final state
            await self.export_dashboard_state()

            # Display results
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ DISCOVERY COMPLETE - RESULTS SUMMARY")
            logger.info("=" * 80)
            logger.info(f"📈 Total Opportunities Found: {len(opportunities)}")
            logger.info(f"🎯 Average Confidence: {sum(o.confidence_score for o in opportunities) / len(opportunities) * 100:.1f}%" if opportunities else "N/A")
            logger.info("")

            if opportunities:
                logger.info("🏆 TOP OPPORTUNITIES:")
                logger.info("")

                for i, opp in enumerate(opportunities[:5], 1):
                    logger.info(f"{i}. {opp.title}")
                    logger.info(f"   Category: {opp.category}")
                    logger.info(f"   Confidence: {opp.confidence_score * 100:.1f}%")
                    logger.info(f"   Revenue: {opp.revenue_potential}")
                    logger.info(f"   Description: {opp.description[:100]}...")
                    logger.info("")

            # Dashboard stats
            stats = self.dashboard.get_dashboard_stats()
            logger.info("=" * 80)
            logger.info("📊 DASHBOARD STATISTICS")
            logger.info("=" * 80)
            logger.info(f"Total Events: {stats['metrics']['total_events']}")
            logger.info(f"Agents Executed: {stats['metrics']['total_agents_executed']}")
            logger.info(f"Opportunities Discovered: {stats['metrics']['total_opportunities_discovered']}")
            logger.info(f"Average Quality Score: {stats['metrics']['avg_quality_score']:.1f}%")
            logger.info(f"System Uptime: {stats['system_uptime_seconds']:.1f}s")
            logger.info("")

            logger.info("=" * 80)
            logger.info("✅ Demo Complete! Check dashboard.html for visual results.")
            logger.info("=" * 80)

            return opportunities

        except Exception as e:
            logger.error(f"❌ Error during discovery: {e}")

            await self.dashboard.error_occurred(
                source="LiveDashboardDemo",
                error_message=str(e),
                error_type=type(e).__name__
            )

            await self.export_dashboard_state()
            raise

    async def run_multiple_scenarios(self):
        """Run multiple discovery scenarios to showcase the system."""
        scenarios = [
            {
                "industry": "technology",
                "geography": "United States",
                "min_confidence": 0.75
            },
            {
                "industry": "healthcare",
                "geography": "California",
                "min_confidence": 0.70
            },
            {
                "industry": "financial_services",
                "geography": "New York",
                "min_confidence": 0.80
            }
        ]

        all_opportunities = []

        for i, scenario in enumerate(scenarios, 1):
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"SCENARIO {i}/{len(scenarios)}")
            logger.info("=" * 80)

            opportunities = await self.run_discovery_scenario(**scenario)
            all_opportunities.extend(opportunities)

            if i < len(scenarios):
                logger.info("⏸️  Waiting 3 seconds before next scenario...")
                await asyncio.sleep(3)

        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 ALL SCENARIOS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Opportunities Across All Scenarios: {len(all_opportunities)}")
        logger.info("")

        return all_opportunities


async def main():
    """Main entry point for the live dashboard demo."""
    demo = LiveDashboardDemo()

    # Check if user wants to run single or multiple scenarios
    print("\n" + "=" * 80)
    print("🎯 LIVE DASHBOARD DEMO - AUTONOMOUS OPPORTUNITY DISCOVERY")
    print("=" * 80)
    print("\nSelect demo mode:")
    print("1. Single Scenario (Technology in United States)")
    print("2. Multiple Scenarios (Technology, Healthcare, Financial Services)")
    print("3. Custom Scenario (Enter your own parameters)")
    print()

    try:
        choice = input("Enter choice (1-3, default=1): ").strip() or "1"

        if choice == "1":
            # Single scenario
            await demo.run_discovery_scenario(
                industry="technology",
                geography="United States",
                min_confidence=0.75
            )

        elif choice == "2":
            # Multiple scenarios
            await demo.run_multiple_scenarios()

        elif choice == "3":
            # Custom scenario
            print("\nEnter custom parameters:")
            industry = input("Industry (e.g., technology, healthcare): ").strip() or "technology"
            geography = input("Geography (e.g., United States, California): ").strip() or "United States"
            min_conf = input("Min Confidence (0.0-1.0, default=0.75): ").strip() or "0.75"

            await demo.run_discovery_scenario(
                industry=industry,
                geography=geography,
                min_confidence=float(min_conf)
            )

        else:
            print("Invalid choice. Running default scenario...")
            await demo.run_discovery_scenario(
                industry="technology",
                geography="United States",
                min_confidence=0.75
            )

        # Open dashboard in browser
        dashboard_path = Path(__file__).parent.parent / "dashboard.html"
        if dashboard_path.exists():
            print(f"\n🌐 Opening dashboard in browser...")
            print(f"   File: {dashboard_path}")
            try:
                webbrowser.open(f"file://{dashboard_path.absolute()}")
            except Exception as e:
                print(f"   ⚠️  Could not auto-open browser: {e}")
                print(f"   Please open manually: file://{dashboard_path.absolute()}")
        else:
            print(f"\n⚠️  Dashboard HTML not found at {dashboard_path}")
            print(f"   Expected location: {dashboard_path}")

        # Export final dashboard state
        data_path = Path(__file__).parent.parent / "dashboard_data.json"
        if data_path.exists():
            print(f"\n📊 Dashboard data exported to: {data_path}")
            print(f"   You can load this in the dashboard for offline viewing.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        logger.info("Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
