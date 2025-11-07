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

    async def _process_goal(self, goal: Goal) -> None:
        """Process goal: plan and execute"""
        try:
            # Plan workflow
            plan = await self.plan_workflow(goal)
            if not plan:
                logger.error(f"Failed to create plan for goal: {goal.goal_id}")
                return

            # Execute workflow
            result = await self.execute_workflow(plan)

            # Store result
            self.workflow_history.append(result)
            self._update_performance_metrics(result)

            # Learn from outcome
            await self._learn_from_execution(plan, result)

        except Exception as e:
            logger.error(f"Error processing goal {goal.goal_id}: {str(e)}", exc_info=True)

    async def plan_workflow(self, goal: Goal) -> Optional[WorkflowPlan]:
        """
        Decompose goal into workflow plan.

        Process:
        1. Goal decomposition → task tree
        2. Capability matching → agent selection
        3. Workflow validation → safety checks
        """
        logger.info(f"Planning workflow for goal: {goal.goal_id}")

        try:
            # Decompose goal
            task_tree = await self.goal_decomposer.decompose_goal(
                goal_description=goal.description,
                context=goal.context,
            )

            # Estimate duration and success probability
            estimated_duration = self._estimate_total_duration(task_tree)
            success_prob = self._estimate_success_probability(task_tree)

            # Create workflow plan
            plan = WorkflowPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                task_tree=task_tree,
                estimated_total_duration_ms=estimated_duration,
                estimated_success_probability=success_prob,
                resource_requirements=self._estimate_resource_requirements(task_tree),
            )

            # Validate plan
            is_valid, errors = await self.validator.validate_workflow(plan)
            if not is_valid:
                logger.warning(f"Plan validation errors: {errors}")

            self.active_workflows[plan.plan_id] = plan

            logger.info(f"Workflow plan created: {plan.plan_id}")
            logger.info(f"  Tasks: {len(task_tree.leaf_tasks)}")
            logger.info(f"  Est. Duration: {estimated_duration:.0f}ms")
            logger.info(f"  Est. Success Rate: {success_prob:.1%}")

            return plan

        except Exception as e:
            logger.error(f"Error planning workflow: {str(e)}", exc_info=True)
            return None

    async def execute_workflow(self, plan: WorkflowPlan) -> WorkflowExecutionResult:
        """Execute workflow with monitoring and adaptation"""
        logger.info(f"Executing workflow: {plan.plan_id}")

        # Tier 3: Use foresight to optimize plan execution
        optimized_plan = await self.use_foresight_to_optimize_plan(plan)

        # Tier 3: Schedule with predictive planning
        scheduled = await self.schedule_with_foresight(optimized_plan)
        logger.info(f"Scheduled for execution at: {scheduled.scheduled_start_time}")

        # Execute through orchestrator
        result = await self.orchestrator.execute_workflow(
            task_tree=optimized_plan.task_tree,
            goal_description=optimized_plan.goal.description,
        )

        # Tier 3: Analyze and optimize workflow performance
        efficiency = await self.optimizer.analyze_workflow_efficiency(
            plan.plan_id,
            {
                "start_time": result.start_time,
                "end_time": result.end_time,
                "tasks": [
                    {
                        "task_id": task_id,
                        "agent": task_result.assigned_agent,
                        "duration_ms": task_result.duration_ms,
                    }
                    for task_id, task_result in result.task_results.items()
                ],
            },
        )
        logger.info(f"Workflow efficiency: {efficiency.efficiency_percent:.1f}%")

        # Store in shared memory if available
        if self.shared_memory:
            try:
                await self.shared_memory.store_workflow_result(result.to_dict())
            except Exception as e:
                logger.warning(f"Failed to store workflow result: {str(e)}")

        return result

    async def get_execution_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        if plan_id not in self.active_workflows:
            return None

        plan = self.active_workflows[plan_id]

        # Find corresponding workflow in orchestrator
        for workflow_id, context in self.orchestrator.active_workflows.items():
            if context.workflow_id == plan_id:
                status = self.orchestrator.get_execution_status(workflow_id)
                if status:
                    return status.to_dict()

        return None

    async def cancel_workflow(self, plan_id: str, reason: str = "") -> None:
        """Cancel workflow execution"""
        if plan_id in self.active_workflows:
            plan = self.active_workflows[plan_id]

            # Find and cancel corresponding workflow
            for workflow_id in list(self.orchestrator.active_workflows.keys()):
                await self.orchestrator.cancel_workflow(workflow_id, reason)

            logger.info(f"Workflow cancelled: {plan_id}")

    def _estimate_total_duration(self, task_tree: TaskTree) -> float:
        """Estimate total workflow duration"""
        # Simple estimation: max path length * average task duration
        # In practice, use actual agent metrics from registry
        avg_task_duration_ms = 1000.0

        # Get critical path
        dag = self._build_dag_from_tree(task_tree)
        critical_path = dag.get_critical_path()

        return len(critical_path) * avg_task_duration_ms

    def _estimate_success_probability(self, task_tree: TaskTree) -> float:
        """Estimate workflow success probability"""
        # Simple: assume 85% per-task success rate
        # In practice, use agent health metrics from Phase 6
        if not task_tree.leaf_tasks:
            return 0.0

        per_task_success = 0.85
        return per_task_success ** len(task_tree.leaf_tasks)

    def _estimate_resource_requirements(self, task_tree: TaskTree) -> Dict[str, Any]:
        """Estimate resource requirements"""
        return {
            "estimated_memory_mb": len(task_tree.leaf_tasks) * 100,
            "estimated_api_calls": len(task_tree.leaf_tasks) * 2,
            "estimated_concurrent_agents": min(5, len(task_tree.leaf_tasks)),
        }

    def _build_dag_from_tree(self, task_tree: TaskTree):
        """Build DAG from task tree"""
        from .goal_decomposition import DAG

        dag = DAG()
        for task_id, task in task_tree.all_tasks.items():
            dag.add_task(task_id, task)

        for task_id, task in task_tree.all_tasks.items():
            for dep_id in task.dependencies:
                if dep_id in task_tree.all_tasks:
                    dag.add_dependency(dep_id, task_id)

        return dag

    def _update_performance_metrics(self, result: WorkflowExecutionResult) -> None:
        """Update performance metrics"""
        self.performance_metrics["total_workflows"] += 1

        if result.overall_success_rate >= 0.8:
            self.performance_metrics["successful_workflows"] += 1
        else:
            self.performance_metrics["failed_workflows"] += 1

        # Update averages
        total = self.performance_metrics["total_workflows"]
        old_avg_time = self.performance_metrics["avg_execution_time_ms"]
        self.performance_metrics["avg_execution_time_ms"] = (
            old_avg_time * (total - 1) + result.duration_ms
        ) / total

        old_avg_success = self.performance_metrics["avg_success_rate"]
        self.performance_metrics["avg_success_rate"] = (
            old_avg_success * (total - 1) + result.overall_success_rate
        ) / total

    async def _learn_from_execution(
        self,
        plan: WorkflowPlan,
        result: WorkflowExecutionResult,
    ) -> None:
        """Extract and store learnings from execution"""
        if not self.learning_system:
            return

        learnings = []

        # Analyze task success rates
        for task_id, task_result in result.task_results.items():
            if task_result.status.value == "completed":
                learning = {
                    "type": "successful_task",
                    "task": task_id,
                    "agent": task_result.assigned_agent,
                    "duration_ms": task_result.duration_ms,
                    "timestamp": datetime.now().isoformat(),
                }
                learnings.append(learning)

        # Analyze failure patterns
        failed_tasks = [tr for tr in result.task_results.values() if tr.status.value == "failed"]
        if failed_tasks:
            learning = {
                "type": "workflow_failure",
                "failed_tasks": [tr.task_id for tr in failed_tasks],
                "total_failures": len(failed_tasks),
                "timestamp": datetime.now().isoformat(),
            }
            learnings.append(learning)

        # Store learnings
        if learnings:
            try:
                for learning in learnings:
                    await self.learning_system.record_learning(
                        agent_name="strategy_agent",
                        learning_data=learning,
                    )
            except Exception as e:
                logger.warning(f"Failed to record learnings: {str(e)}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "total_workflows": self.performance_metrics["total_workflows"],
            "successful_workflows": self.performance_metrics["successful_workflows"],
            "failed_workflows": self.performance_metrics["failed_workflows"],
            "success_rate": (
                self.performance_metrics["successful_workflows"]
                / max(1, self.performance_metrics["total_workflows"])
            ),
            "avg_execution_time_ms": self.performance_metrics["avg_execution_time_ms"],
            "avg_success_rate": self.performance_metrics["avg_success_rate"],
        }

    # ===== Tier 3: Autonomy Layer Methods =====

    async def use_foresight_to_optimize_plan(self, plan: WorkflowPlan) -> WorkflowPlan:
        """
        Apply foresight predictions to optimize workflow plan.

        Uses:
        - Resource predictions to adjust parallelism
        - Failure patterns to select fallback agents
        - Performance analysis to reorder tasks
        """
        try:
            # Predict resource needs
            resource_pred = await self.foresight.predict_resource_needs(
                {
                    "workflow_id": plan.plan_id,
                    "tasks": [t.task_id for t in plan.task_tree.leaf_tasks],
                    "agents": [
                        t.assigned_agents[0] for t in plan.task_tree.leaf_tasks if t.assigned_agents
                    ],
                    "estimated_duration_ms": plan.estimated_total_duration_ms,
                }
            )

            # Detect failure patterns
            failure_patterns = []
            for task in plan.task_tree.leaf_tasks:
                for agent in task.assigned_agents:
                    patterns = await self.foresight.detect_failure_patterns(agent)
                    failure_patterns.extend(patterns)

            # Apply optimizations based on predictions
            optimized_plan = WorkflowPlan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                task_tree=plan.task_tree,
                estimated_total_duration_ms=plan.estimated_total_duration_ms,
                estimated_success_probability=plan.estimated_success_probability,
                resource_requirements=(
                    resource_pred.to_dict()
                    if hasattr(resource_pred, "to_dict")
                    else {
                        "memory_mb": resource_pred.predicted_memory_mb,
                        "cpu_percent": resource_pred.predicted_cpu_percent,
                    }
                ),
            )

            logger.info(
                f"Applied foresight optimization to plan {plan.plan_id}: "
                f"detected {len(failure_patterns)} failure patterns"
            )

            return optimized_plan

        except Exception as e:
            logger.warning(f"Error in foresight optimization: {str(e)}")
            return plan

    async def schedule_with_foresight(self, plan: WorkflowPlan) -> Any:
        """
        Schedule workflow using predictive planning.

        Determines:
        - Optimal execution time
        - Resource pre-staging actions
        - Fallback schedules for high-risk workflows
        """
        try:
            plan_dict = {
                "plan_id": plan.plan_id,
                "goal": plan.goal.description,
                "agents": [
                    t.assigned_agents[0] for t in plan.task_tree.leaf_tasks if t.assigned_agents
                ],
                "tasks": [t.task_id for t in plan.task_tree.leaf_tasks],
                "estimated_duration_ms": plan.estimated_total_duration_ms,
            }

            # Schedule workflow
            scheduled = await self.predictive_planner.schedule_workflow(plan_dict, self.foresight)

            # Pre-stage resources
            staging = await self.predictive_planner.pre_stage_resources(plan_dict, self.foresight)

            logger.info(
                f"Scheduled workflow {plan.plan_id}: "
                f"start={scheduled.scheduled_start_time.isoformat()}, "
                f"concurrency={scheduled.recommended_concurrency}, "
                f"risk={scheduled.risk_level}"
            )

            return scheduled

        except Exception as e:
            logger.warning(f"Error in predictive scheduling: {str(e)}")
            from datetime import datetime
            from .predictive_planning import ScheduledPlan

            return ScheduledPlan(
                plan_id=plan.plan_id,
                original_goal=plan.goal.description,
                scheduled_start_time=datetime.now(),
                estimated_completion_time=datetime.now(),
            )

    async def enable_advanced_coordination_for_large_teams(
        self, plan: WorkflowPlan
    ) -> WorkflowPlan:
        """
        Enable hierarchical coordination for large-scale workflows.

        For workflows with >10 agents:
        - Create agent teams by capability/function
        - Assign team coordinators
        - Implement consensus protocols
        """
        leaf_agents = []
        for task in plan.task_tree.leaf_tasks:
            leaf_agents.extend(task.assigned_agents)

        if len(set(leaf_agents)) <= 10:
            return plan  # No coordination needed for small teams

        logger.info(f"Enabling advanced coordination for {len(set(leaf_agents))} agents")

        try:
            # Create teams
            trading_agents = [a for a in set(leaf_agents) if "trading" in a or "risk" in a]
            analysis_agents = [a for a in set(leaf_agents) if "sentiment" in a or "chart" in a]
            utility_agents = [
                a for a in set(leaf_agents) if a not in trading_agents and a not in analysis_agents
            ]

            if trading_agents:
                trading_team = await self.coordinator.create_team(
                    trading_agents, team_type="hierarchical"
                )
            if analysis_agents:
                analysis_team = await self.coordinator.create_team(
                    analysis_agents, team_type="parallel"
                )
            if utility_agents:
                utility_team = await self.coordinator.create_team(
                    utility_agents, team_type="parallel"
                )

            logger.info("Created coordination teams for large workflow")

        except Exception as e:
            logger.warning(f"Error enabling advanced coordination: {str(e)}")

        return plan

    async def continuously_optimize_workflows(self) -> None:
        """
        Background task: continuously optimize workflows based on learnings.

        Periodically:
        - Analyzes completed workflows
        - Identifies bottlenecks
        - Suggests and applies optimizations
        """
        logger.info("Starting continuous workflow optimization")

        while True:
            try:
                # Analyze recent workflows
                for plan_id, plan in list(self.active_workflows.items()):
                    status = await self.get_execution_status(plan_id)
                    if status and status.get("status") == "completed":
                        # Identify bottlenecks
                        bottlenecks = await self.optimizer.identify_bottlenecks(plan_id)

                        if bottlenecks:
                            # Suggest improvements
                            improvements = await self.optimizer.suggest_improvements(plan_id)

                            logger.info(
                                f"Found {len(bottlenecks)} bottlenecks, "
                                f"suggesting {len(improvements)} improvements"
                            )

                            # Track learning metrics
                            metrics = await self.optimizer.get_learning_metrics()
                            logger.debug(f"Optimization metrics: {metrics}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in continuous optimization: {str(e)}")
                await asyncio.sleep(60)

    def get_autonomy_metrics(self) -> Dict[str, Any]:
        """Get Tier 3 autonomy layer metrics."""
        return {
            "foresight_predictions": len(self.foresight.predictions),
            "scheduled_workflows": len(self.predictive_planner.scheduled_workflows),
            "active_teams": len(self.coordinator.teams),
            "optimization_metrics": self.optimizer.learning_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    async def run(self) -> None:
        """Main agent loop"""
        logger.info("StrategyAgent running with Tier 3 Autonomy Layer...")

        # Start background optimization loop
        asyncio.create_task(self.continuously_optimize_workflows())

        while True:
            try:
                # Check for new goals from message bus
                # In practice, would listen for incoming goals

                # Check status of active workflows
                for plan_id in list(self.active_workflows.keys()):
                    status = await self.get_execution_status(plan_id)
                    if status and status.get("status") == "completed":
                        del self.active_workflows[plan_id]

                # Trigger preemptive actions based on foresight
                await self.predictive_planner.trigger_preemptive_actions(self.foresight)

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in StrategyAgent loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
