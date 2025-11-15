"""
Workflow Template Library Demo

Demonstrates pre-built workflow templates for instant business value!

This shows how users can leverage ready-made workflows spanning multiple
business functions without building workflows from scratch.

Run:
    python examples/workflow_templates_demo.py
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.templates import get_template_library
from src.superstandard.agent_factory import get_registry


async def main():
    print("\n" + "="*80)
    print("📚 WORKFLOW TEMPLATE LIBRARY DEMO")
    print("   Instant Business Value with Pre-Built Workflows!")
    print("="*80)

    # Get template library
    library = get_template_library()

    # Show catalog
    library.show_catalog()

    # Demonstrate each template
    print("\n" + "="*80)
    print("🎯 TEMPLATE DEMONSTRATIONS")
    print("="*80)

    # Demo 1: New Product Launch
    print("\n📋 DEMO 1: New Product Launch - Strategy to Market")
    print("="*60)
    template = library.get_template("new_product_launch")
    print(f"\n   Template: {template.name}")
    print(f"   Description: {template.description}")
    print(f"   Spans {len(template.categories)} APQC categories:")
    for cat in template.categories:
        print(f"      - {cat}")
    print(f"\n   Workflow Phases ({len(template.tasks_template)} tasks):")

    # Group tasks by phase
    phase_1 = template.tasks_template[:3]
    phase_2 = template.tasks_template[3:9]
    phase_3 = template.tasks_template[9:]

    print(f"\n   Phase 1: Strategic Foundation ({len(phase_1)} tasks)")
    for task in phase_1:
        print(f"      → {task['name']}")

    print(f"\n   Phase 2: Product Development ({len(phase_2)} tasks)")
    for task in phase_2:
        print(f"      → {task['name']}")

    print(f"\n   Phase 3: Go-to-Market ({len(phase_3)} tasks)")
    for task in phase_3:
        print(f"      → {task['name']}")

    print(f"\n   Business Value: {template.business_value}")
    print(f"   Estimated Duration: {template.estimated_duration}")
    print(f"   Estimated Cost: {template.estimated_cost_range}")

    # Instantiate it!
    print(f"\n   ✨ Instantiating Template...")
    workflow = template.instantiate(params={
        "total_budget": 200.0,
        "use_case": "New SaaS Product Launch"
    })
    print(f"   ✅ Workflow Created: {workflow.name}")
    print(f"      Workflow ID: {workflow.workflow_id}")
    print(f"      Total Tasks: {len(workflow.tasks)}")
    print(f"      Budget: ${workflow.total_budget:.2f}")

    # Demo 2: Marketing Campaign
    print("\n📋 DEMO 2: Integrated Marketing Campaign")
    print("="*60)
    template = library.get_template("marketing_campaign")
    print(f"\n   Template: {template.name}")
    print(f"   Capabilities Required: {', '.join(template.capabilities_required[:3])}...")
    print(f"\n   Use Cases:")
    for uc in template.use_cases:
        print(f"      • {uc}")

    workflow = template.instantiate(params={"total_budget": 75.0})
    print(f"\n   ✅ Workflow Ready: {len(workflow.tasks)} tasks, ${workflow.total_budget:.2f} budget")

    # Demo 3: Strategic Planning
    print("\n📋 DEMO 3: Annual Strategic Planning")
    print("="*60)
    template = library.get_template("strategic_planning")
    print(f"\n   Template: {template.name}")
    print(f"   Perfect for: {template.use_cases[0]}")
    print(f"   Duration: {template.estimated_duration}")

    workflow = template.instantiate(params={"total_budget": 100.0})
    print(f"\n   ✅ Strategic Planning Workflow: {len(workflow.tasks)} comprehensive tasks")

    # Search templates
    print("\n" + "="*80)
    print("🔍 TEMPLATE SEARCH")
    print("="*80)

    print("\n   Searching for templates involving 'Product Development'...")
    results = library.search_templates(category="2.0 - Product Development")
    print(f"   Found {len(results)} templates:")
    for t in results:
        print(f"      • {t.name}")

    print("\n   Searching for 'lead generation' capability...")
    results = library.search_templates(capability="lead_generation")
    print(f"   Found {len(results)} templates:")
    for t in results:
        print(f"      • {t.name}")

    # Check agent availability
    print("\n" + "="*80)
    print("🤖 AGENT AVAILABILITY CHECK")
    print("="*80)

    registry = get_registry()
    count = registry.discover_agents()
    stats = registry.get_stats()

    print(f"\n   Discovered {count} agents:")
    print(f"   Total Capabilities: {stats['total_capabilities']}")
    print(f"   Categories Covered: {stats['total_categories']}")

    # Check coverage for each template
    print(f"\n   Template Capability Coverage:")
    for template in library.list_templates():
        available_caps = 0
        for cap in template.capabilities_required:
            if registry.search(capability=cap):
                available_caps += 1

        coverage = (available_caps / len(template.capabilities_required)) * 100
        status = "✅" if coverage == 100 else "⚠️"
        print(f"      {status} {template.name}: {coverage:.0f}% ({available_caps}/{len(template.capabilities_required)})")

    # Summary
    print("\n" + "="*80)
    print("✅ WORKFLOW TEMPLATE LIBRARY - READY FOR BUSINESS!")
    print("="*80)
    print(f"""
🎉 PRE-BUILT WORKFLOWS FOR INSTANT VALUE!

What we demonstrated:
✅ {len(library.list_templates())} production-ready workflow templates
✅ Spanning {len(set([c for t in library.list_templates() for c in t.categories]))} APQC categories
✅ Covering complete business processes end-to-end
✅ Instant instantiation with custom parameters

Template Benefits:
💡 No workflow building required - just configure and go!
💡 Best-practice process flows built-in
💡 Cross-functional collaboration embedded
💡 Proven patterns for common scenarios
💡 Easy customization with parameters

Business Impact:
📈 Accelerate time-to-value from weeks to minutes
📈 Leverage battle-tested process workflows
📈 Enable non-technical users to run complex workflows
📈 Standardize processes across organization
📈 Continuous improvement of templates

Available Templates:
{chr(10).join(f'   • {t.name} ({t.estimated_duration})' for t in library.list_templates())}

The platform provides IMMEDIATE BUSINESS VALUE with pre-built workflows! 🚀

Usage:
    library = get_template_library()
    template = library.get_template("new_product_launch")
    workflow = template.instantiate(params={{"budget": 200.0}})
    # Execute via orchestrator!
""")


if __name__ == "__main__":
    asyncio.run(main())
