"""
Multi-Agent Orchestration Engine

The production brain that orchestrates complex multi-agent workflows using
all 4 protocols (Discovery, Reputation, Contracts, Resources).

Key Features:
- Execute complex workflows with dependencies
- Parallel agent execution
- Dynamic agent selection (Discovery + Reputation)
- SLA enforcement (Contracts)
- Budget control (Resources)
- Error handling and retries
- Real-time monitoring
- APQC PCF process support

Usage:
    from src.superstandard.orchestration import WorkflowOrchestrator, WorkflowDefinition, Task

    # Define workflow
    workflow = WorkflowDefinition(
        workflow_id="my-workflow",
        name="My Business Process",
        tasks=[
            Task(task_id="task-1", name="Analyze Data", capability="data_analysis"),
            Task(task_id="task-2", name="Generate Report",
                 capability="report_generation", depends_on=["task-1"])
        ]
    )

    # Execute
    orchestrator = WorkflowOrchestrator()
    await orchestrator.start()
    result = await orchestrator.execute_workflow(workflow)
"""

from .engine import (
    WorkflowOrchestrator,
    WorkflowDefinition,
    Task,
    TaskStatus,
    WorkflowStatus,
    ExecutionResult,
    get_orchestrator
)

__all__ = [
    'WorkflowOrchestrator',
    'WorkflowDefinition',
    'Task',
    'TaskStatus',
    'WorkflowStatus',
    'ExecutionResult',
    'get_orchestrator'
]
