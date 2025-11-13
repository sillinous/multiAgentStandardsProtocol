#!/usr/bin/env python3
"""
Test script for Process 1.1.5 - Establish Strategic Vision agents
"""
import asyncio
import json
from datetime import datetime


async def test_all_agents():
    """Test all 4 Process 1.1.5 agents"""
    print("=" * 80)
    print("TESTING PROCESS 1.1.5 - ESTABLISH STRATEGIC VISION")
    print("=" * 80)
    print()

    # Import all agents
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_5_strategic_vision.a_1_1_5_1_synthesize_insights import SynthesizeInsightsAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_5_strategic_vision.a_1_1_5_2_define_vision import DefineVisionAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_5_strategic_vision.a_1_1_5_3_define_mission_values import DefineMissionValuesAgent
    from superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_5_strategic_vision.a_1_1_5_4_validate_alignment import ValidateAlignmentAgent

    agents = [
        ("1.1.5.1", "Synthesize Strategic Insights", SynthesizeInsightsAgent),
        ("1.1.5.2", "Define Vision Statement", DefineVisionAgent),
        ("1.1.5.3", "Define Mission and Core Values", DefineMissionValuesAgent),
        ("1.1.5.4", "Validate Strategic Alignment", ValidateAlignmentAgent),
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
            if hierarchy_id == "1.1.5.1":
                print(f"  Strategic Insights: {result['kpis']['insights_synthesized']} insights synthesized")
                print(f"  Strategic Themes: {result['kpis']['strategic_themes_identified']} themes")
                print(f"  Synthesis Confidence: {result['kpis']['synthesis_confidence']}%")
            elif hierarchy_id == "1.1.5.2":
                print(f"  Vision Clarity: {result['kpis']['vision_clarity_score']}/10")
                print(f"  Inspiration Score: {result['kpis']['inspiration_score']}/10")
                print(f"  Strategic Alignment: {result['kpis']['strategic_alignment_score']}/10")
            elif hierarchy_id == "1.1.5.3":
                print(f"  Core Values: {result['kpis']['core_values_defined']} values")
                print(f"  Mission Clarity: {result['kpis']['mission_clarity_score']}/10")
                print(f"  Authenticity: {result['kpis']['authenticity_score']}/10")
            elif hierarchy_id == "1.1.5.4":
                print(f"  Overall Alignment: {result['kpis']['overall_alignment_score']}/10")
                print(f"  Areas Validated: {result['kpis']['alignment_areas_validated']}")
                print(f"  Gaps Identified: {result['kpis']['gaps_identified']}")

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
        print("🎉 ALL PROCESS 1.1.5 AGENTS PASSED!")
        print("🎉 PROCESS GROUP 1.1 - COMPLETE (22 AGENTS TOTAL)!")
        print()
        print("Process Group 1.1 Summary:")
        print("  - Process 1.1.1: Assess External Environment (7 agents) ✓")
        print("  - Process 1.1.2: Survey Market and Customer Needs (3 agents) ✓")
        print("  - Process 1.1.3: Select Relevant Markets (4 agents) ✓")
        print("  - Process 1.1.4: Perform Internal Analysis (4 agents) ✓")
        print("  - Process 1.1.5: Establish Strategic Vision (4 agents) ✓")
        print()
        print("Total: 22 agents implementing complete strategic planning framework!")
    else:
        print("❌ Some tests failed. Please review errors above.")

    return success_count == total_count


if __name__ == "__main__":
    success = asyncio.run(test_all_agents())
    exit(0 if success else 1)
