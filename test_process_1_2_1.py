#!/usr/bin/env python3
"""
Test script for Process 1.2.1 - Define Strategic Options agents
"""
import asyncio
import json
from datetime import datetime


async def test_all_agents():
    """Test all 4 Process 1.2.1 agents"""
    print("=" * 80)
    print("TESTING PROCESS 1.2.1 - DEFINE STRATEGIC OPTIONS")
    print("=" * 80)
    print()

    # Import all agents
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_2_develop_strategy.p_1_2_1_strategic_options.a_1_2_1_1_identify_alternatives import IdentifyAlternativesAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_2_develop_strategy.p_1_2_1_strategic_options.a_1_2_1_2_analyze_positioning import AnalyzePositioningAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_2_develop_strategy.p_1_2_1_strategic_options.a_1_2_1_3_define_growth import DefineGrowthAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_2_develop_strategy.p_1_2_1_strategic_options.a_1_2_1_4_explore_partnerships import ExplorePartnershipsAgent

    agents = [
        ("1.2.1.1", "Identify Strategic Alternatives", IdentifyAlternativesAgent),
        ("1.2.1.2", "Analyze Competitive Positioning Options", AnalyzePositioningAgent),
        ("1.2.1.3", "Define Growth Strategies", DefineGrowthAgent),
        ("1.2.1.4", "Explore Partnership and Alliance Opportunities", ExplorePartnershipsAgent),
    ]

    results = []

    for hierarchy_id, name, AgentClass in agents:
        print(f"Testing Agent {hierarchy_id} - {name}")
        print("-" * 80)

        try:
            # Instantiate agent
            agent = AgentClass()
            print(f"✓ Agent instantiated: {agent.config.agent_id}")
            print(f"  PCF Metadata: Level {agent.config.pcf_metadata.level} - {agent.config.pcf_metadata.activity_name}")

            # Execute agent
            start_time = datetime.utcnow()
            result = await agent.execute({"test": True})
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            print(f"✓ Agent executed successfully in {duration:.2f}s")

            # Display KPIs
            if "kpis" in result:
                print(f"  KPIs:")
                for kpi_name, kpi_value in result["kpis"].items():
                    print(f"    - {kpi_name}: {kpi_value}")

            # Display key results based on agent type
            if hierarchy_id == "1.2.1.1":
                print(f"  Alternatives Generated: {result['kpis']['alternatives_generated']}")
                print(f"  Diversity Score: {result['kpis']['diversity_score']}/10")
                print(f"  Feasibility Score: {result['kpis']['feasibility_score']}/10")
            elif hierarchy_id == "1.2.1.2":
                print(f"  Positioning Options: {result['kpis']['positioning_options']}")
                print(f"  Competitive Advantage: {result['kpis']['competitive_advantage_score']}/10")
                print(f"  Differentiation Strength: {result['kpis']['differentiation_strength']}/10")
            elif hierarchy_id == "1.2.1.3":
                print(f"  Growth Options: {result['kpis']['growth_options_identified']}")
                print(f"  Expected Growth Rate: {result['kpis']['expected_growth_rate']}")
                print(f"  Capital Requirements: {result['kpis']['capital_requirements']}")
            elif hierarchy_id == "1.2.1.4":
                print(f"  Partners Identified: {result['kpis']['partners_identified']}")
                print(f"  Strategic Fit: {result['kpis']['strategic_fit_score']}/10")
                print(f"  Synergy Potential: {result['kpis']['synergy_potential']}")

            results.append({
                "hierarchy_id": hierarchy_id,
                "name": name,
                "status": "SUCCESS",
                "duration": duration,
                "kpis": result.get("kpis", {})
            })

            print(f"✓ Agent {hierarchy_id} test PASSED")

        except Exception as e:
            print(f"✗ Agent {hierarchy_id} test FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "hierarchy_id": hierarchy_id,
                "name": name,
                "status": "FAILED",
                "error": str(e)
            })

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    total_count = len(results)
    print(f"Agents Tested: {total_count}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print()

    if success_count == total_count:
        print("🎉 ALL PROCESS 1.2.1 AGENTS PASSED!")
        print()
        print("Process 1.2.1 - Define Strategic Options COMPLETE!")
        print("  - 1.2.1.1: Identify Strategic Alternatives ✓")
        print("  - 1.2.1.2: Analyze Competitive Positioning ✓")
        print("  - 1.2.1.3: Define Growth Strategies ✓")
        print("  - 1.2.1.4: Explore Partnerships ✓")
        print()
        print("Ready to proceed with Process 1.2.2!")
    else:
        print("❌ Some tests failed. Please review errors above.")

    return success_count == total_count


if __name__ == "__main__":
    success = asyncio.run(test_all_agents())
    exit(0 if success else 1)
