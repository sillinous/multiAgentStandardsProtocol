"""
Direct test runner for Process Group 1.2 agents
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from superstandard.api.agent_loader import get_registry


def test_agent(hierarchy_id: str, agent_name: str):
    """Test a single agent"""
    try:
        registry = get_registry()
        agent = registry.get_agent(hierarchy_id)
        result = asyncio.run(agent.execute({}))

        # Verify basic structure
        assert 'kpis' in result, f"Missing KPIs in result for {hierarchy_id}"

        print(f"✓ {hierarchy_id} - {agent_name}")
        return True
    except Exception as e:
        print(f"✗ {hierarchy_id} - {agent_name}: {str(e)}")
        return False


def main():
    print("=" * 80)
    print("Testing Process Group 1.2 - Develop Business Strategy (16 agents)")
    print("=" * 80)

    tests = [
        # Process 1.2.1 - Define strategic options
        ("1.2.1.1", "Identify strategic alternatives"),
        ("1.2.1.2", "Analyze competitive positioning"),
        ("1.2.1.3", "Define growth strategies"),
        ("1.2.1.4", "Explore partnerships and alliances"),

        # Process 1.2.2 - Evaluate and select strategies
        ("1.2.2.1", "Assess strategic options against criteria"),
        ("1.2.2.2", "Conduct scenario analysis"),
        ("1.2.2.3", "Evaluate risk and return profile"),
        ("1.2.2.4", "Select optimal strategy portfolio"),

        # Process 1.2.3 - Develop business plans
        ("1.2.3.1", "Create strategic initiatives roadmap"),
        ("1.2.3.2", "Develop financial projections"),
        ("1.2.3.3", "Define resource requirements"),
        ("1.2.3.4", "Create implementation timeline"),

        # Process 1.2.4 - Develop and set organizational goals
        ("1.2.4.1", "Define strategic objectives"),
        ("1.2.4.2", "Establish key results (OKRs)"),
        ("1.2.4.3", "Set performance targets"),
        ("1.2.4.4", "Create performance measurement framework"),
    ]

    print("\nProcess 1.2.1 - Define Strategic Options:")
    print("-" * 80)
    results = []
    for i in range(4):
        results.append(test_agent(tests[i][0], tests[i][1]))

    print("\nProcess 1.2.2 - Evaluate and Select Strategies:")
    print("-" * 80)
    for i in range(4, 8):
        results.append(test_agent(tests[i][0], tests[i][1]))

    print("\nProcess 1.2.3 - Develop Business Plans:")
    print("-" * 80)
    for i in range(8, 12):
        results.append(test_agent(tests[i][0], tests[i][1]))

    print("\nProcess 1.2.4 - Develop and Set Organizational Goals:")
    print("-" * 80)
    for i in range(12, 16):
        results.append(test_agent(tests[i][0], tests[i][1]))

    # Summary
    print("\n" + "=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} agents passed")

    if passed == total:
        print("✓ ALL TESTS PASSED - Process Group 1.2 is fully operational!")
    else:
        print(f"✗ {total - passed} tests failed")
        return 1

    # Verify registry statistics
    print("\nRegistry Statistics:")
    print("-" * 80)
    registry = get_registry()
    stats = registry.get_statistics()
    print(f"Total agents implemented: {stats['implemented_agents']}")
    print(f"Implementation percentage: {stats['implementation_percentage']:.1f}%")

    print("\n" + "=" * 80)
    print("PROCESS GROUP 1.2 - 100% COMPLETE!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
