"""
SuperStandard ACP (Agent Coordination Protocol) Demo

This example demonstrates:
1. Creating a coordination session
2. Multiple agents joining a pipeline coordination
3. Task creation and assignment
4. Task execution with status updates
5. Shared state management across agents
6. Progress monitoring

Usage:
    python examples/acp_coordination/multi_agent_pipeline.py
"""

import asyncio
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crates.agentic_protocols.python.acp_implementation import CoordinationManager


async def simulate_agent_work(agent_name: str, task_description: str, duration: float):
    """Simulate an agent performing work on a task."""
    print(f"      [{agent_name}] Starting work on: {task_description}")
    await asyncio.sleep(duration)
    print(f"      [{agent_name}] Completed: {task_description}")


async def main():
    print("\n" + "="*70)
    print("SuperStandard ACP v1.0 - Multi-Agent Pipeline Coordination Demo")
    print("="*70 + "\n")

    # Create coordination manager
    manager = CoordinationManager()
    print("[*] Created Coordination Manager\n")

    # Step 1: Create a pipeline coordination for a data processing workflow
    print("Step 1: Creating pipeline coordination session")
    print("-" * 70)

    coordination = await manager.create_coordination(
        coordinator_id="supervisor-main",
        coordination_type="pipeline",
        goal="Process customer data through collection → analysis → reporting pipeline",
        context={"project": "customer-insights", "priority": "high"}
    )
    coord_id = coordination["coordination_id"]
    print(f"[+] Created coordination session: {coord_id}")
    print(f"    Type: {coordination['coordination_type']}")
    print(f"    Goal: {coordination['goal']}")
    print(f"    Status: {coordination['status']}")
    print()

    # Step 2: Agents join the coordination
    print("\nStep 2: Agents joining the coordination")
    print("-" * 70)

    # Data Collector Agent joins
    print("[*] Data Collector Agent joining...")
    result = await manager.join_coordination(
        coordination_id=coord_id,
        agent_id="data-collector-1",
        agent_type="collector",
        capabilities=["api_fetch", "data_extraction"],
        role="data_provider"
    )
    print(f"[+] {result['agent_name']} joined as {result['role']}")

    # Data Analyzer Agent joins
    print("[*] Data Analyzer Agent joining...")
    result = await manager.join_coordination(
        coordination_id=coord_id,
        agent_id="data-analyzer-1",
        agent_type="analyzer",
        capabilities=["data_analysis", "aggregation"],
        role="processor"
    )
    print(f"[+] {result['agent_name']} joined as {result['role']}")

    # Report Generator Agent joins
    print("[*] Report Generator Agent joining...")
    result = await manager.join_coordination(
        coordination_id=coord_id,
        agent_id="report-generator-1",
        agent_type="generator",
        capabilities=["reporting", "visualization"],
        role="output_generator"
    )
    print(f"[+] {result['agent_name']} joined as {result['role']}")

    print(f"\n[*] Total agents in coordination: 3")

    # Step 3: Create tasks for the pipeline
    print("\nStep 3: Creating tasks for the pipeline")
    print("-" * 70)

    # Task 1: Data Collection
    print("[*] Creating Task 1: Data Collection")
    task1 = await manager.create_task(
        coordination_id=coord_id,
        task_type="data_collection",
        description="Fetch customer data from CRM API",
        priority=1,
        input_data={"source": "crm_api", "date_range": "last_30_days"},
        dependencies=[]
    )
    print(f"[+] Created task: {task1['task_id']}")
    print(f"    Description: {task1['description']}")
    print(f"    Priority: {task1['priority']}")

    # Task 2: Data Analysis
    print("\n[*] Creating Task 2: Data Analysis")
    task2 = await manager.create_task(
        coordination_id=coord_id,
        task_type="data_analysis",
        description="Analyze customer behavior patterns",
        priority=2,
        input_data={"analysis_type": "behavior_patterns"},
        dependencies=[task1['task_id']]
    )
    print(f"[+] Created task: {task2['task_id']}")
    print(f"    Description: {task2['description']}")
    print(f"    Dependencies: {len(task2['dependencies'])} task(s)")

    # Task 3: Report Generation
    print("\n[*] Creating Task 3: Report Generation")
    task3 = await manager.create_task(
        coordination_id=coord_id,
        task_type="report_generation",
        description="Generate executive summary report",
        priority=3,
        input_data={"format": "pdf", "include_charts": True},
        dependencies=[task2['task_id']]
    )
    print(f"[+] Created task: {task3['task_id']}")
    print(f"    Description: {task3['description']}")
    print(f"    Output format: PDF with charts")

    # Step 4: Assign tasks to agents
    print("\nStep 4: Assigning tasks to agents")
    print("-" * 70)

    # Assign Task 1 to Data Collector
    print("[*] Assigning Task 1 to data-collector-1...")
    result = await manager.assign_task(
        coordination_id=coord_id,
        task_id=task1['task_id'],
        agent_id="data-collector-1"
    )
    print(f"[+] Task assigned: {result['status']}")

    # Assign Task 2 to Data Analyzer
    print("[*] Assigning Task 2 to data-analyzer-1...")
    result = await manager.assign_task(
        coordination_id=coord_id,
        task_id=task2['task_id'],
        agent_id="data-analyzer-1"
    )
    print(f"[+] Task assigned: {result['status']}")

    # Assign Task 3 to Report Generator
    print("[*] Assigning Task 3 to report-generator-1...")
    result = await manager.assign_task(
        coordination_id=coord_id,
        task_id=task3['task_id'],
        agent_id="report-generator-1"
    )
    print(f"[+] Task assigned: {result['status']}")

    # Step 5: Execute tasks in pipeline order
    print("\nStep 5: Executing pipeline tasks")
    print("-" * 70)

    # Execute Task 1
    print("\n[*] Task 1: Data Collection (data-collector-1)")
    await simulate_agent_work("data-collector-1", "Fetching customer data from CRM API", 1.0)
    result = await manager.update_task_status(
        coordination_id=coord_id,
        task_id=task1['task_id'],
        status="completed",
        output_data={
            "records_fetched": 1500,
            "data_location": "s3://bucket/customer-data.json",
            "timestamp": time.time()
        }
    )
    print(f"      [+] Task 1 completed: {result['status']}")

    # Update shared state with collected data
    print("\n      [*] Updating shared state with collected data...")
    await manager.update_shared_state(
        coordination_id=coord_id,
        agent_id="data-collector-1",
        updates={
            "collected_records": 1500,
            "data_ready": True,
            "collection_timestamp": time.time()
        }
    )
    print("      [+] Shared state updated")

    # Execute Task 2
    print("\n[*] Task 2: Data Analysis (data-analyzer-1)")
    await simulate_agent_work("data-analyzer-1", "Analyzing customer behavior patterns", 1.5)
    result = await manager.update_task_status(
        coordination_id=coord_id,
        task_id=task2['task_id'],
        status="completed",
        output_data={
            "insights_found": 25,
            "top_pattern": "increased_weekend_activity",
            "analysis_location": "s3://bucket/analysis-results.json"
        }
    )
    print(f"      [+] Task 2 completed: {result['status']}")

    # Update shared state with analysis results
    print("\n      [*] Updating shared state with analysis results...")
    await manager.update_shared_state(
        coordination_id=coord_id,
        agent_id="data-analyzer-1",
        updates={
            "analysis_complete": True,
            "insights_count": 25,
            "analysis_timestamp": time.time()
        }
    )
    print("      [+] Shared state updated")

    # Execute Task 3
    print("\n[*] Task 3: Report Generation (report-generator-1)")
    await simulate_agent_work("report-generator-1", "Generating executive summary report", 1.0)
    result = await manager.update_task_status(
        coordination_id=coord_id,
        task_id=task3['task_id'],
        status="completed",
        output_data={
            "report_location": "s3://bucket/executive-summary.pdf",
            "pages": 15,
            "charts": 8
        }
    )
    print(f"      [+] Task 3 completed: {result['status']}")

    # Final shared state update
    print("\n      [*] Updating shared state with final results...")
    await manager.update_shared_state(
        coordination_id=coord_id,
        agent_id="report-generator-1",
        updates={
            "report_complete": True,
            "report_url": "https://reports.example.com/executive-summary.pdf",
            "completion_timestamp": time.time()
        }
    )
    print("      [+] Shared state updated")

    # Step 6: Check coordination progress
    print("\nStep 6: Checking coordination progress")
    print("-" * 70)

    progress = await manager.get_progress(coord_id)
    print(f"[*] Coordination Progress:")
    print(f"    Total tasks: {progress['total_tasks']}")
    print(f"    Completed: {progress['completed_tasks']}")
    print(f"    In progress: {progress['in_progress_tasks']}")
    print(f"    Pending: {progress['pending_tasks']}")
    print(f"    Failed: {progress['failed_tasks']}")
    print(f"    Completion: {progress['completion_percentage']:.1f}%")

    print(f"\n[*] Task Breakdown:")
    for task in progress['tasks']:
        print(f"    - {task['description']}")
        print(f"      Status: {task['status']}")
        print(f"      Assigned to: {task.get('assigned_to', 'Unassigned')}")

    print(f"\n[*] Shared State:")
    for key, value in progress['shared_state'].items():
        if 'timestamp' not in key:
            print(f"    {key}: {value}")

    # Step 7: Complete coordination
    print("\nStep 7: Completing coordination")
    print("-" * 70)

    result = await manager.complete_coordination(coord_id)
    print(f"[+] Coordination completed: {result['status']}")
    print(f"    Final state: {result['final_status']}")

    print("\n" + "="*70)
    print("Pipeline coordination completed successfully!")
    print("="*70)
    print("\nKey Takeaways:")
    print("- 3 agents collaborated in a pipeline pattern")
    print("- Tasks executed in dependency order")
    print("- Shared state synchronized across all agents")
    print("- 100% task completion achieved")


if __name__ == "__main__":
    asyncio.run(main())
