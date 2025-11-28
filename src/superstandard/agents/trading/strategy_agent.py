"""
Phase 7: Tier 2 Intelligence Layer - Strategy Agent

Main orchestrator for autonomous goal-driven multi-agent workflows.
Decomposes goals, plans execution, monitors progress, and learns from outcomes.
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

from .goal_decomposition import GoalDecomposer, TaskTree
from .workflow_orchestration import (
    WorkflowOrchestrator,
    WorkflowExecutionResult,
    ExecutionStatus,
)
from .message_bus import MessageBus
from .capability_registry import CapabilityRegistry
from .capability_matching import CapabilityMatcher
from .workflow_validator import WorkflowValidator
from src.models.model_factory import ModelFactory

# Tier 3: Autonomy Layer
from .foresight import ForesightAnalyzer
from .predictive_planning import PredictivePlanning
from .advanced_coordination import HierarchicalCoordinator
from .self_optimization import WorkflowOptimizer

logger = logging.getLogger(__name__)


class GoalPriority(int, Enum):
    """Goal priority levels"""

    CRITICAL = 1
    HIGH = 5
    NORMAL = 10
    LOW = 15


@dataclass
class Goal:
    """High-level objective"""

    goal_id: str
    description: str
    priority: int = GoalPriority.NORMAL.value
    deadline: Optional[datetime] = None
    success_criteria: List[str] = field(default_factory=list)
    constraints: Dict = field(default_factory=dict)
    context: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class WorkflowPlan:
    """Complete plan for achieving a goal"""

    plan_id: str
    goal: Goal
    task_tree: TaskTree
    estimated_total_duration_ms: float
    estimated_success_probability: float
    resource_requirements: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "strategy_agent"
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal.to_dict(),
            "task_tree": self.task_tree.to_dict(),
            "estimated_total_duration_ms": self.estimated_total_duration_ms,
            "estimated_success_probability": self.estimated_success_probability,
            "resource_requirements": self.resource_requirements,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "metadata": self.metadata,
        }


class StrategyAgent:
    """
    Core strategic agent for autonomous goal-driven orchestration.

    Responsibilities:
    1. Parse and understand high-level goals
    2. Decompose into actionable sub-tasks
    3. Create multi-step workflows
    4. Monitor execution and adapt in real-time
    5. Report results and learn from outcomes
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        message_bus: MessageBus,
        capability_matcher: CapabilityMatcher,
        shared_memory=None,
        health_monitor=None,
        learning_system=None,
    ):
        self.registry = registry
        self.message_bus = message_bus
        self.capability_matcher = capability_matcher
        self.shared_memory = shared_memory
        self.health_monitor = health_monitor
        self.learning_system = learning_system

        # Initialize Tier 2 sub-components
        self.goal_decomposer = GoalDecomposer(registry)
        self.orchestrator = WorkflowOrchestrator(message_bus, capability_matcher)
        self.validator = WorkflowValidator(registry, health_monitor)
        self.llm = ModelFactory.create_model("anthropic")

        # Initialize Tier 3 sub-components (Autonomy Layer)
        self.foresight = ForesightAnalyzer(health_monitor, shared_memory)
        self.predictive_planner = PredictivePlanning(self)
        self.coordinator = HierarchicalCoordinator(message_bus, registry)
        self.optimizer = WorkflowOptimizer(shared_memory)

        # Agent state
        self.current_goals: List[Goal] = []
        self.active_workflows: Dict[str, WorkflowPlan] = {}
        self.workflow_history: List[WorkflowExecutionResult] = []
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_execution_time_ms": 0.0,
            "avg_success_rate": 0.0,
        }

        logger.info("StrategyAgent initialized with Tier 3 Autonomy Layer")

    async def accept_goal(
        self,
        goal_description: str,
        priority: int = GoalPriority.NORMAL.value,
        success_criteria: Optional[List[str]] = None,
        constraints: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> str:
        """
        Accept a high-level goal and begin orchestration.

        Returns: workflow_id for tracking
        """
        goal_id = str(uuid.uuid4())
        goal = Goal(
            goal_id=goal_id,
            description=goal_description,
            priority=priority,
            success_criteria=success_criteria or [],
            constraints=constraints or {},
            context=context or {},
        )

        logger.info(f"Accepting goal: {goal_description[:100]}")
        self.current_goals.append(goal)

        # Begin planning asynchronously
        asyncio.create_task(self._process_goal(goal))

        return goal_id

    
    async def _process_goal(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process goal task with AI-powered analysis.

        Implements APQC process: 
        Domain: default

        Uses smart processing for intelligent analysis, recommendations,
        and decision-making capabilities.
        """
        from superstandard.services.smart_processing import get_processor
        from datetime import datetime

        task_type = input_data.get("task_type", "default")
        self.log("info", f"Processing {task_type} task with AI-powered analysis")

        start_time = datetime.now()

        # Get domain-specific smart processor
        processor = get_processor("default")

        # Prepare context for processing
        processing_context = {
            "apqc_process": "",
            "apqc_id": self.APQC_PROCESS_ID,
            "agent_capabilities": self.capabilities_list,
            "input_data": input_data.get("data", {}),
            "task_context": input_data.get("context", {}),
            "priority": input_data.get("priority", "medium"),
        }

        # Execute smart processing
        processing_result = await processor.process(processing_context, task_type)

        # Extract analysis results
        analysis_results = processing_result.get("analysis", {})
        if not analysis_results:
            analysis_results = {
                "status": processing_result.get("status", "completed"),
                "domain": processing_result.get("domain", "default"),
                "insights": processing_result.get("insights", [])
            }

        # Generate recommendations if not provided
        recommendations = []
        if "recommendations" in processing_result:
            recommendations = processing_result["recommendations"]
        elif "optimization_recommendations" in processing_result:
            recommendations = processing_result["optimization_recommendations"]
        elif "resolution_recommendations" in processing_result:
            recommendations = processing_result["resolution_recommendations"]
        else:
            # Generate default recommendations based on analysis
            recommendations = [{
                "type": "process_optimization",
                "priority": "medium",
                "action": "Review analysis results and implement suggested improvements",
                "confidence": 0.75
            }]

        # Make decisions based on context
        decisions = []
        if "decision" in processing_result or "recommendation" in processing_result:
            decisions.append({
                "decision_type": processing_result.get("decision", processing_result.get("recommendation", "proceed")),
                "confidence": processing_result.get("confidence", 0.8),
                "rationale": processing_result.get("reasoning", "Based on AI analysis"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            decisions.append({
                "decision_type": "proceed",
                "confidence": 0.85,
                "rationale": "Analysis complete, proceeding with standard workflow",
                "timestamp": datetime.now().isoformat()
            })

        # Generate artifacts
        artifacts = []
        if input_data.get("generate_report", False):
            artifacts.append({
                "type": "analysis_report",
                "name": f"{self.config.agent_name}_ai_report",
                "format": "json",
                "content_summary": "AI-powered analysis results",
                "generated_at": datetime.now().isoformat()
            })

        # Compute metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = {
            "processing_time_ms": processing_time,
            "ai_powered": True,
            "processor_used": processor.domain,
            "recommendations_count": len(recommendations),
            "decisions_count": len(decisions),
            "confidence_score": decisions[0].get("confidence", 0.8) if decisions else 0.8
        }

        # Generate events
        events = [{
            "event_type": "ai_task_completed",
            "agent_id": self.config.agent_id,
            "apqc_process": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "summary": f"AI-powered processing of {task_type} task completed",
            "ai_enhanced": True
        }]

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "output": {
                "analysis": analysis_results,
                "recommendations": recommendations,
                "decisions": decisions,
                "artifacts": artifacts,
                "metrics": metrics,
                "events": events,
            },
        }

