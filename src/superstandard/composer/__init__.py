"""
Dynamic Workflow Composer

Automatically composes and executes workflows from natural language requirements!

This module represents THE ULTIMATE INTEGRATION of all platform capabilities:
- Agent Registry for capability discovery
- Discovery Protocol for agent finding
- Reputation for agent selection
- Orchestration for execution
- Contracts for SLA enforcement
- Resources for budget management

Usage:
    from src.superstandard.composer import WorkflowComposer, get_composer

    composer = get_composer()
    workflow = await composer.compose_from_requirements(
        "Analyze competitors and develop strategic plan"
    )
    result = await composer.execute_workflow(workflow)
"""

from .workflow_composer import (
    WorkflowComposer,
    ComposedWorkflow,
    WorkflowRequirement,
    get_composer
)

__all__ = [
    'WorkflowComposer',
    'ComposedWorkflow',
    'WorkflowRequirement',
    'get_composer'
]
