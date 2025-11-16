#!/usr/bin/env python3
"""
🎯 Workflow Orchestrator Demo Script
=====================================

Demonstrates the visual workflow orchestration system capabilities:
1. Creating workflows programmatically
2. Loading pre-built templates
3. Executing workflows
4. Monitoring execution status
5. Export/import workflows

Run this script to test the workflow engine without the UI.
"""

import asyncio
import json
from datetime import datetime

from workflow_engine import (
    WorkflowManager,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    NodePosition,
    NodeType,
    TriggerType
)


async def demo_create_simple_workflow():
    """Demo 1: Create a simple workflow programmatically"""
    print("\n" + "="*70)
    print("DEMO 1: Creating a Simple Workflow")
    print("="*70)

    manager = WorkflowManager()

    # Create a simple 3-node workflow
    workflow = WorkflowDefinition(
        id="demo_simple_workflow",
        name="Demo: Simple Financial Analysis",
        description="A simple workflow demonstrating agent orchestration",
        trigger=TriggerType.MANUAL,
        nodes=[
            WorkflowNode(
                id="node_1",
                type=NodeType.AGENT,
                label="Financial Data Collection",
                position=NodePosition(x=100, y=100),
                agent_id="expert_9_4",
                agent_name="Manage Accounting and Financial Reporting",
                category_id="9.0",
                category_name="Financial Resources",
                description="Collects financial data from various sources"
            ),
            WorkflowNode(
                id="node_2",
                type=NodeType.AGENT,
                label="Financial Analysis",
                position=NodePosition(x=400, y=100),
                agent_id="expert_9_2",
                agent_name="Manage Financial Planning and Budgeting",
                category_id="9.0",
                category_name="Financial Resources",
                description="Analyzes collected financial data"
            ),
            WorkflowNode(
                id="node_3",
                type=NodeType.OUTPUT,
                label="Analysis Report",
                position=NodePosition(x=700, y=100),
                description="Final analysis report output"
            )
        ],
        edges=[
            WorkflowEdge(
                id="edge_1",
                source="node_1",
                target="node_2",
                label="Financial Data"
            ),
            WorkflowEdge(
                id="edge_2",
                source="node_2",
                target="node_3",
                label="Analysis Results"
            )
        ],
        tags=["finance", "analysis", "demo"]
    )

    # Save workflow
    workflow_id = manager.create_workflow(workflow)
    print(f"✅ Created workflow: {workflow_id}")
    print(f"   Name: {workflow.name}")
    print(f"   Nodes: {len(workflow.nodes)}")
    print(f"   Edges: {len(workflow.edges)}")

    # Export workflow
    exported = manager.export_workflow(workflow_id, format="json")
    print(f"\n📤 Exported workflow (preview):")
    print(json.dumps(json.loads(exported)['name'], indent=2))

    return manager, workflow_id


async def demo_use_template():
    """Demo 2: Use a pre-built template"""
    print("\n" + "="*70)
    print("DEMO 2: Using a Pre-Built Template")
    print("="*70)

    manager = WorkflowManager()

    # List available templates
    templates = manager.template_library.list_templates()
    print(f"\n📚 Available Templates: {len(templates)}")

    for i, template in enumerate(templates[:5], 1):
        print(f"\n{i}. {template.name}")
        print(f"   Category: {template.category}")
        print(f"   Difficulty: {template.difficulty}")
        print(f"   Nodes: {template.workflow.nodes.__len__() if template.workflow.nodes else 0}")
        print(f"   Usage: {template.usage_count} times")

    # Use the first template
    template = templates[0]
    print(f"\n✨ Using template: {template.name}")

    workflow_id = manager.create_workflow(template.workflow)
    print(f"✅ Created workflow from template: {workflow_id}")

    return manager, workflow_id


async def demo_execute_workflow():
    """Demo 3: Execute a workflow"""
    print("\n" + "="*70)
    print("DEMO 3: Executing a Workflow")
    print("="*70)

    manager = WorkflowManager()

    # Get a template
    template = manager.template_library.get_template("financial_marketing_roi")
    if not template:
        print("❌ Template not found")
        return

    workflow_id = manager.create_workflow(template.workflow)
    print(f"📝 Created workflow: {workflow_id}")

    # Execute workflow with inputs
    print(f"\n▶️  Executing workflow...")

    start_time = datetime.now()

    execution = await manager.execute_workflow(
        workflow_id,
        inputs={
            "period": "Q4 2024",
            "regions": ["North America", "Europe"],
            "currency": "USD"
        }
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print results
    print(f"\n✅ Execution completed!")
    print(f"   Execution ID: {execution.id}")
    print(f"   Status: {execution.status}")
    print(f"   Duration: {execution.duration:.2f}s (actual: {duration:.2f}s)")
    print(f"   Nodes: {execution.completed_nodes}/{execution.total_nodes} completed")

    if execution.failed_nodes > 0:
        print(f"   ⚠️  Failed nodes: {execution.failed_nodes}")

    print(f"\n📊 Node Execution Summary:")
    for node_id, status in execution.node_states.items():
        print(f"   • {node_id}: {status}")

    print(f"\n📝 Events ({len(execution.events)}):")
    for event in execution.events[:5]:  # Show first 5 events
        print(f"   • {event['event_type']}: {event['data']}")

    return manager, execution


async def demo_workflow_validation():
    """Demo 4: Workflow validation"""
    print("\n" + "="*70)
    print("DEMO 4: Workflow Validation")
    print("="*70)

    manager = WorkflowManager()

    # Create invalid workflow (with cycle)
    print("\n❌ Testing invalid workflow (with cycle)...")

    invalid_workflow = WorkflowDefinition(
        id="invalid_workflow",
        name="Invalid Workflow with Cycle",
        description="This workflow has a cycle and should fail validation",
        nodes=[
            WorkflowNode(
                id="node_a",
                type=NodeType.AGENT,
                label="Node A",
                position=NodePosition(x=100, y=100)
            ),
            WorkflowNode(
                id="node_b",
                type=NodeType.AGENT,
                label="Node B",
                position=NodePosition(x=300, y=100)
            ),
            WorkflowNode(
                id="node_c",
                type=NodeType.AGENT,
                label="Node C",
                position=NodePosition(x=500, y=100)
            )
        ],
        edges=[
            WorkflowEdge(id="edge_1", source="node_a", target="node_b"),
            WorkflowEdge(id="edge_2", source="node_b", target="node_c"),
            WorkflowEdge(id="edge_3", source="node_c", target="node_a")  # Creates cycle!
        ]
    )

    from workflow_engine import WorkflowValidator

    is_valid, errors = WorkflowValidator.validate_workflow(invalid_workflow)

    if is_valid:
        print("   ⚠️  Workflow passed validation (unexpected!)")
    else:
        print("   ✅ Workflow failed validation (expected)")
        print(f"   Errors found: {len(errors)}")
        for error in errors:
            print(f"      • {error}")

    # Create valid workflow
    print("\n✅ Testing valid workflow...")

    valid_workflow = WorkflowDefinition(
        id="valid_workflow",
        name="Valid Workflow",
        description="This workflow should pass validation",
        nodes=[
            WorkflowNode(
                id="node_1",
                type=NodeType.AGENT,
                label="Start",
                position=NodePosition(x=100, y=100),
                agent_id="expert_1_1"
            ),
            WorkflowNode(
                id="node_2",
                type=NodeType.AGENT,
                label="Process",
                position=NodePosition(x=300, y=100),
                agent_id="expert_2_1"
            ),
            WorkflowNode(
                id="node_3",
                type=NodeType.OUTPUT,
                label="End",
                position=NodePosition(x=500, y=100)
            )
        ],
        edges=[
            WorkflowEdge(id="edge_1", source="node_1", target="node_2"),
            WorkflowEdge(id="edge_2", source="node_2", target="node_3")
        ]
    )

    is_valid, errors = WorkflowValidator.validate_workflow(valid_workflow)

    if is_valid:
        print("   ✅ Workflow passed validation")
        workflow_id = manager.create_workflow(valid_workflow)
        print(f"   ✅ Workflow saved: {workflow_id}")
    else:
        print("   ❌ Workflow failed validation (unexpected!)")
        for error in errors:
            print(f"      • {error}")


async def demo_template_library():
    """Demo 5: Template library features"""
    print("\n" + "="*70)
    print("DEMO 5: Template Library Features")
    print("="*70)

    manager = WorkflowManager()

    # Get all templates
    all_templates = manager.template_library.list_templates()
    print(f"\n📚 Total Templates: {len(all_templates)}")

    # Group by category
    categories = {}
    for template in all_templates:
        if template.category not in categories:
            categories[template.category] = []
        categories[template.category].append(template)

    print(f"\n📊 Templates by Category:")
    for category, templates in sorted(categories.items()):
        print(f"\n   {category} ({len(templates)} templates):")
        for template in templates:
            print(f"      • {template.name}")
            print(f"        Difficulty: {template.difficulty}")
            rating = getattr(template, 'average_rating', 0.0)
            print(f"        Rating: {rating:.1f}/5.0")
            print(f"        Usage: {template.usage_count}")

    # Show most popular templates
    print(f"\n🏆 Most Popular Templates:")
    popular = sorted(all_templates, key=lambda t: t.usage_count, reverse=True)[:3]
    for i, template in enumerate(popular, 1):
        print(f"\n   {i}. {template.name}")
        print(f"      Usage: {template.usage_count} times")
        rating = getattr(template, 'average_rating', 0.0)
        print(f"      Rating: {rating:.1f}/5.0")
        print(f"      Category: {template.category}")

    # Show highest rated templates
    print(f"\n⭐ Highest Rated Templates:")
    rated = sorted(all_templates, key=lambda t: getattr(t, 'average_rating', 0.0), reverse=True)[:3]
    for i, template in enumerate(rated, 1):
        print(f"\n   {i}. {template.name}")
        rating = getattr(template, 'average_rating', 0.0)
        print(f"      Rating: {rating:.1f}/5.0")
        print(f"      Usage: {template.usage_count} times")
        print(f"      Category: {template.category}")


async def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🎯 WORKFLOW ORCHESTRATOR DEMONSTRATION")
    print("="*70)
    print("\nThis demo showcases the visual workflow orchestration system")
    print("for drag-and-drop composition of 118+ APQC agents.")
    print("\nFeatures demonstrated:")
    print("  1. Creating workflows programmatically")
    print("  2. Using pre-built templates")
    print("  3. Executing workflows")
    print("  4. Workflow validation")
    print("  5. Template library features")

    try:
        # Run all demos
        await demo_create_simple_workflow()
        await demo_use_template()
        await demo_execute_workflow()
        await demo_workflow_validation()
        await demo_template_library()

        print("\n" + "="*70)
        print("✅ All demos completed successfully!")
        print("="*70)

        print("\n📝 Next Steps:")
        print("   1. Start the dashboard server:")
        print("      python dashboard_server.py")
        print("\n   2. Open the workflow designer:")
        print("      http://localhost:8080/workflow_designer.html")
        print("\n   3. Explore the visual interface and create your own workflows!")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
