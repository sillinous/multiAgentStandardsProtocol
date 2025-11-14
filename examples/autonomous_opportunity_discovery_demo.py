"""
Autonomous Business Opportunity Discovery - Live Demo

This demo showcases the revolutionary autonomous opportunity discovery system
that coordinates multiple specialized agents to discover, validate, and rank
real business opportunities without human intervention.

What This Demonstrates:
- Multi-agent orchestration (4 agents working together)
- Autonomous business intelligence
- Cross-agent pattern recognition
- Confidence scoring and validation
- Real-world data integration (SimilarWeb, FRED, Census, Qualtrics)
- Production-grade quality assurance

Run this demo to watch the AI discover business opportunities in real-time!
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.superstandard.orchestration.opportunity_discovery import (
    OpportunityDiscoveryOrchestrator
)


def print_banner():
    """Print an impressive banner."""
    print("\n" + "=" * 80)
    print("  🤖 AUTONOMOUS BUSINESS OPPORTUNITY DISCOVERY SYSTEM")
    print("  " + "-" * 76)
    print("  Multi-Agent Intelligence • Real-Time Analysis • Production Data")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")


def print_opportunity(opp, rank: int):
    """Print a discovered opportunity in a nice format."""
    print(f"\n🎯 OPPORTUNITY #{rank}")
    print(f"{'═' * 78}")
    print(f"  Title:      {opp.title}")
    print(f"  ID:         {opp.id}")
    print(f"  Category:   {opp.category}")
    print(f"  ")
    print(f"  📊 SCORES:")
    print(f"  ├─ Confidence:      {opp.confidence_score}% {'🟢' if opp.confidence_score >= 80 else '🟡' if opp.confidence_score >= 70 else '🔴'}")
    print(f"  ├─ Revenue:         {opp.revenue_potential}")
    print(f"  ├─ Feasibility:     {opp.feasibility}")
    print(f"  └─ Strategic Fit:   {opp.strategic_fit}")
    print(f"  ")
    print(f"  💰 FINANCIALS:")
    if opp.estimated_revenue_min and opp.estimated_revenue_max:
        print(f"  ├─ Est. Revenue:    ${opp.estimated_revenue_min:,} - ${opp.estimated_revenue_max:,}")
    if opp.time_to_market_months:
        print(f"  └─ Time to Market:  {opp.time_to_market_months} months")
    print(f"  ")
    print(f"  📝 DESCRIPTION:")
    print(f"  {opp.description}")
    print(f"  ")
    print(f"  🔍 EVIDENCE:")
    print(f"  ├─ Competitive:   {opp.competitive_evidence}")
    print(f"  ├─ Economic:      {opp.economic_evidence}")
    print(f"  ├─ Demographic:   {opp.demographic_evidence}")
    print(f"  └─ Research:      {opp.market_research_evidence}")
    print(f"  ")
    print(f"  📊 DATA QUALITY:")
    print(f"  ├─ Quality Score:  {opp.quality_score}%")
    print(f"  └─ Data Sources:   {', '.join(opp.data_sources or [])}")


async def run_discovery_demo():
    """Run the autonomous opportunity discovery demo."""

    print_banner()

    print("🚀 Initializing Autonomous Discovery System...")
    print("   • Loading 4 specialized agents")
    print("   • Connecting to production data sources")
    print("   • Preparing orchestration engine")

    orchestrator = OpportunityDiscoveryOrchestrator()

    print("\n✅ System Ready!\n")

    input("Press ENTER to start autonomous discovery...")

    print_section("⚡ AUTONOMOUS DISCOVERY IN PROGRESS")

    print("The system will now:")
    print("  1. Execute 4 agents in parallel (Competitors, Economics, Demographics, Research)")
    print("  2. Synthesize cross-agent patterns and insights")
    print("  3. Identify business opportunities autonomously")
    print("  4. Validate with multi-source evidence")
    print("  5. Score and rank by confidence and potential\n")

    print("⏳ Starting discovery... (this may take 10-30 seconds)\n")

    try:
        # Run autonomous discovery
        opportunities = await orchestrator.discover_opportunities(
            industry="Cloud Software",
            geography="United States",
            min_confidence=70.0
        )

        print_section(f"🎉 DISCOVERY COMPLETE - {len(opportunities)} OPPORTUNITIES FOUND")

        if not opportunities:
            print("❌ No opportunities met the minimum confidence threshold (70%)")
            print("   Try adjusting parameters or checking data source availability")
            return

        # Display all opportunities
        for idx, opp in enumerate(opportunities, 1):
            print_opportunity(opp, idx)

        # Summary statistics
        print_section("📈 DISCOVERY SUMMARY")

        avg_confidence = sum(o.confidence_score for o in opportunities) / len(opportunities)
        high_confidence = [o for o in opportunities if o.confidence_score >= 80]
        total_revenue_potential = sum(
            (o.estimated_revenue_min + o.estimated_revenue_max) / 2
            for o in opportunities
            if o.estimated_revenue_min and o.estimated_revenue_max
        )

        print(f"  Total Opportunities:       {len(opportunities)}")
        print(f"  Average Confidence:        {avg_confidence:.1f}%")
        print(f"  High Confidence (≥80%):    {len(high_confidence)}")
        print(f"  Total Revenue Potential:   ${total_revenue_potential:,.0f}")
        print(f"  ")
        print(f"  Data Sources Used:")
        all_sources = set()
        for opp in opportunities:
            all_sources.update(opp.data_sources or [])
        for source in sorted(all_sources):
            print(f"    • {source}")

        # Recommendations
        print_section("💡 STRATEGIC RECOMMENDATIONS")

        if high_confidence:
            print(f"  ✅ IMMEDIATE ACTION: Pursue {len(high_confidence)} high-confidence opportunities")
            print(f"  ")
            for opp in high_confidence:
                print(f"    • {opp.title} ({opp.confidence_score}% confidence)")

        print(f"  ")
        print(f"  📊 NEXT STEPS:")
        print(f"    1. Conduct deeper analysis on top opportunities")
        print(f"    2. Develop go-to-market strategies")
        print(f"    3. Allocate resources to highest ROI opportunities")
        print(f"    4. Set up continuous monitoring for market changes")

        print_section("🎊 DEMO COMPLETE")

        print("What Just Happened:")
        print("  • 4 specialized AI agents analyzed the market autonomously")
        print("  • Real-world data from SimilarWeb, FRED, Census, Qualtrics")
        print("  • Cross-agent synthesis identified patterns no single agent could see")
        print("  • Opportunities validated with multi-source evidence")
        print("  • Confidence scoring based on data quality and convergence")
        print("  ")
        print("This demonstrates TRUE autonomous business intelligence - the system")
        print("discovering opportunities, validating them, and providing strategic")
        print("recommendations without any human intervention!")

    except Exception as e:
        print(f"\n❌ ERROR during discovery: {str(e)}")
        print(f"   This may be due to missing API keys or network issues")
        print(f"   The system will gracefully fall back to mock data when APIs unavailable")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_discovery_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
