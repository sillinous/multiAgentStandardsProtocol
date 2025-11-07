"""
Agent Ecosystem Coordinator
APQC Process Classification Framework: 11.1.1 - Manage Information Technology Risks

Central coordination hub for the technical debt management agent ecosystem.
Orchestrates communication, task assignment, and collaborative workflows.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict, deque
import uuid

from .technical_debt_tracking_agent import technical_debt_tracker, TechnicalDebtItem
from .architecture_review_agent import architecture_reviewer, ArchitecturalViolation
from .refactoring_coordinator_agent import refactoring_coordinator, RefactoringTask
from .code_quality_monitoring_agent import quality_monitor, QualityReport
from .documentation_maintenance_agent import documentation_maintainer, DocumentationReport

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles of agents in the ecosystem"""

    DEBT_TRACKER = "debt_tracker"
    ARCHITECTURE_REVIEWER = "architecture_reviewer"
    REFACTORING_COORDINATOR = "refactoring_coordinator"
    QUALITY_MONITOR = "quality_monitor"
    DOCUMENTATION_MAINTAINER = "documentation_maintainer"


class TaskStatus(Enum):
    """Status of coordinated tasks"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommunicationPriority(Enum):
    """Priority levels for inter-agent communication"""

    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class AgentMessage:
    """Message exchanged between agents"""

    id: str
    sender: AgentRole
    recipient: AgentRole
    message_type: str
    priority: CommunicationPriority
    subject: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    correlation_id: Optional[str] = None


@dataclass
class CoordinatedTask:
    """Task coordinated across multiple agents"""

    id: str
    title: str
    description: str
    primary_agent: AgentRole
    supporting_agents: List[AgentRole]
    dependencies: List[str]  # Task IDs this task depends on
    status: TaskStatus
    priority: int  # 1-10 scale
    estimated_duration: timedelta
    assigned_at: datetime
    due_date: Optional[datetime]
    progress_percentage: float = 0.0
    deliverables: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EcosystemMetrics:
    """Metrics for the agent ecosystem performance"""

    total_tasks_completed: int
    average_task_completion_time: float
    agent_utilization: Dict[AgentRole, float]
    communication_volume: Dict[str, int]
    collaboration_effectiveness: float
    knowledge_sharing_score: float
    overall_ecosystem_health: float


@dataclass
class WorkflowDefinition:
    """Definition of a coordinated workflow"""

    id: str
    name: str
    description: str
    trigger_conditions: List[str]
    steps: List[Dict[str, Any]]
    success_criteria: List[str]
    failure_conditions: List[str]
    estimated_duration: timedelta
    required_agents: List[AgentRole]


class AgentEcosystemCoordinator:
    """
    Central coordinator for the technical debt management agent ecosystem

    Implements APQC Process 11.1.1 - Manage Information Technology Risks
    Provides orchestration, communication, and collaboration management
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.agents = self._initialize_agents()
        self.message_queue: deque = deque(maxlen=1000)
        self.active_tasks: Dict[str, CoordinatedTask] = {}
        self.completed_tasks: deque = deque(maxlen=100)
        self.workflows = self._initialize_workflows()
        self.coordination_rules = self._initialize_coordination_rules()
        self.performance_metrics = self._initialize_metrics()

    def _initialize_agents(self) -> Dict[AgentRole, Any]:
        """Initialize references to all agents in the ecosystem"""
        return {
            AgentRole.DEBT_TRACKER: technical_debt_tracker,
            AgentRole.ARCHITECTURE_REVIEWER: architecture_reviewer,
            AgentRole.REFACTORING_COORDINATOR: refactoring_coordinator,
            AgentRole.QUALITY_MONITOR: quality_monitor,
            AgentRole.DOCUMENTATION_MAINTAINER: documentation_maintainer,
        }

    def _initialize_workflows(self) -> List[WorkflowDefinition]:
        """Initialize predefined workflows for common coordination scenarios"""
        return [
            WorkflowDefinition(
                id="comprehensive_debt_analysis",
                name="Comprehensive Technical Debt Analysis",
                description="Full ecosystem analysis of technical debt and quality",
                trigger_conditions=["manual_request", "scheduled_weekly"],
                steps=[
                    {"agent": "debt_tracker", "action": "scan_codebase", "parallel": False},
                    {
                        "agent": "architecture_reviewer",
                        "action": "analyze_architecture",
                        "parallel": True,
                    },
                    {
                        "agent": "quality_monitor",
                        "action": "run_quality_analysis",
                        "parallel": True,
                    },
                    {
                        "agent": "documentation_maintainer",
                        "action": "analyze_documentation_health",
                        "parallel": True,
                    },
                    {
                        "agent": "refactoring_coordinator",
                        "action": "analyze_and_prioritize_debt",
                        "parallel": False,
                    },
                ],
                success_criteria=[
                    "All analyses completed successfully",
                    "Refactoring plan generated",
                    "Reports exported",
                ],
                failure_conditions=[
                    "Critical agent failure",
                    "Timeout exceeded",
                    "Data inconsistency detected",
                ],
                estimated_duration=timedelta(hours=2),
                required_agents=[
                    AgentRole.DEBT_TRACKER,
                    AgentRole.ARCHITECTURE_REVIEWER,
                    AgentRole.QUALITY_MONITOR,
                    AgentRole.DOCUMENTATION_MAINTAINER,
                    AgentRole.REFACTORING_COORDINATOR,
                ],
            ),
            WorkflowDefinition(
                id="critical_issue_response",
                name="Critical Issue Response Workflow",
                description="Rapid response to critical technical debt or quality issues",
                trigger_conditions=["critical_violation_detected", "security_issue_found"],
                steps=[
                    {
                        "agent": "debt_tracker",
                        "action": "analyze_critical_items",
                        "parallel": False,
                    },
                    {
                        "agent": "quality_monitor",
                        "action": "verify_issue_severity",
                        "parallel": True,
                    },
                    {
                        "agent": "refactoring_coordinator",
                        "action": "create_emergency_plan",
                        "parallel": False,
                    },
                    {
                        "agent": "documentation_maintainer",
                        "action": "document_incident",
                        "parallel": True,
                    },
                ],
                success_criteria=[
                    "Critical issue assessed",
                    "Emergency plan created",
                    "Incident documented",
                ],
                failure_conditions=["Unable to assess severity", "Emergency plan creation failed"],
                estimated_duration=timedelta(hours=1),
                required_agents=[
                    AgentRole.DEBT_TRACKER,
                    AgentRole.QUALITY_MONITOR,
                    AgentRole.REFACTORING_COORDINATOR,
                    AgentRole.DOCUMENTATION_MAINTAINER,
                ],
            ),
            WorkflowDefinition(
                id="architecture_improvement",
                name="Architecture Improvement Initiative",
                description="Coordinated effort to improve system architecture",
                trigger_conditions=["architecture_violations_threshold", "manual_request"],
                steps=[
                    {
                        "agent": "architecture_reviewer",
                        "action": "comprehensive_analysis",
                        "parallel": False,
                    },
                    {"agent": "debt_tracker", "action": "identify_related_debt", "parallel": True},
                    {
                        "agent": "refactoring_coordinator",
                        "action": "plan_architectural_refactoring",
                        "parallel": False,
                    },
                    {
                        "agent": "documentation_maintainer",
                        "action": "create_architecture_docs",
                        "parallel": True,
                    },
                    {
                        "agent": "quality_monitor",
                        "action": "establish_quality_gates",
                        "parallel": True,
                    },
                ],
                success_criteria=[
                    "Architecture analysis completed",
                    "Refactoring plan approved",
                    "Documentation updated",
                    "Quality gates established",
                ],
                failure_conditions=[
                    "Architecture analysis failed",
                    "Stakeholder approval not obtained",
                ],
                estimated_duration=timedelta(days=3),
                required_agents=[
                    AgentRole.ARCHITECTURE_REVIEWER,
                    AgentRole.DEBT_TRACKER,
                    AgentRole.REFACTORING_COORDINATOR,
                    AgentRole.DOCUMENTATION_MAINTAINER,
                    AgentRole.QUALITY_MONITOR,
                ],
            ),
        ]

    def _initialize_coordination_rules(self) -> Dict[str, Dict]:
        """Initialize rules for agent coordination and communication"""
        return {
            "communication_rules": {
                "max_message_age_hours": 24,
                "response_timeout_hours": 8,
                "urgent_response_timeout_minutes": 30,
                "max_concurrent_conversations": 5,
            },
            "task_assignment_rules": {
                "max_tasks_per_agent": 3,
                "priority_threshold_for_preemption": 8,
                "load_balancing_enabled": True,
                "skill_matching_required": True,
            },
            "collaboration_rules": {
                "min_agents_for_consensus": 2,
                "data_sharing_protocols": ["encrypted", "versioned", "audited"],
                "conflict_resolution_method": "priority_based",
                "knowledge_sharing_mandatory": True,
            },
            "escalation_rules": {
                "task_overdue_escalation_hours": 24,
                "critical_issue_immediate_escalation": True,
                "stakeholder_notification_threshold": "high_priority",
                "automated_resolution_attempts": 3,
            },
        }

    def _initialize_metrics(self) -> EcosystemMetrics:
        """Initialize ecosystem performance metrics"""
        return EcosystemMetrics(
            total_tasks_completed=0,
            average_task_completion_time=0.0,
            agent_utilization={agent: 0.0 for agent in AgentRole},
            communication_volume=defaultdict(int),
            collaboration_effectiveness=0.0,
            knowledge_sharing_score=0.0,
            overall_ecosystem_health=0.0,
        )

    async def execute_workflow(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow with full coordination

        Args:
            workflow_id: ID of the workflow to execute
            context: Additional context for workflow execution

        Returns:
            Workflow execution results
        """
        logger.info(f"🚀 Starting workflow execution: {workflow_id}")

        workflow = next((w for w in self.workflows if w.id == workflow_id), None)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        execution_id = str(uuid.uuid4())
        start_time = datetime.now()

        execution_context = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "start_time": start_time,
            "context": context or {},
            "results": {},
            "errors": [],
            "status": "running",
        }

        try:
            # Create coordinated tasks for workflow steps
            await self._create_workflow_tasks(workflow, execution_context)

            # Execute workflow steps
            results = await self._execute_workflow_steps(workflow, execution_context)

            # Validate success criteria
            success = await self._validate_workflow_success(workflow, results)

            execution_context["status"] = "completed" if success else "failed"
            execution_context["results"] = results
            execution_context["completion_time"] = datetime.now()
            execution_context["duration"] = (
                execution_context["completion_time"] - start_time
            ).total_seconds()

            # Update metrics
            await self._update_workflow_metrics(workflow, execution_context)

            logger.info(f"✅ Workflow {workflow_id} completed: {execution_context['status']}")

            return execution_context

        except Exception as e:
            logger.error(f"❌ Workflow {workflow_id} failed: {e}")
            execution_context["status"] = "failed"
            execution_context["errors"].append(str(e))
            execution_context["completion_time"] = datetime.now()
            return execution_context

    async def _create_workflow_tasks(
        self, workflow: WorkflowDefinition, execution_context: Dict[str, Any]
    ):
        """Create coordinated tasks for workflow execution"""
        for i, step in enumerate(workflow.steps):
            task_id = f"{execution_context['execution_id']}_step_{i}"

            task = CoordinatedTask(
                id=task_id,
                title=f"{workflow.name} - Step {i+1}",
                description=f"Execute {step['action']} on {step['agent']}",
                primary_agent=AgentRole(step["agent"]),
                supporting_agents=[],
                dependencies=[],
                status=TaskStatus.PENDING,
                priority=8 if workflow.id == "critical_issue_response" else 5,
                estimated_duration=workflow.estimated_duration / len(workflow.steps),
                assigned_at=datetime.now(),
                due_date=datetime.now() + workflow.estimated_duration,
                context={
                    "workflow_id": workflow.id,
                    "step_index": i,
                    "action": step["action"],
                    "parallel": step.get("parallel", False),
                },
            )

            self.active_tasks[task_id] = task

    async def _execute_workflow_steps(
        self, workflow: WorkflowDefinition, execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow steps with proper coordination"""
        results = {}

        # Group steps by parallel execution capability
        step_groups = []
        current_group = []

        for step in workflow.steps:
            if step.get("parallel", False) and current_group:
                current_group.append(step)
            else:
                if current_group:
                    step_groups.append(current_group)
                current_group = [step]

        if current_group:
            step_groups.append(current_group)

        # Execute step groups
        for group_index, step_group in enumerate(step_groups):
            logger.info(f"Executing step group {group_index + 1} with {len(step_group)} steps")

            if len(step_group) == 1:
                # Sequential execution
                step = step_group[0]
                result = await self._execute_agent_action(
                    step["agent"], step["action"], execution_context
                )
                results[f"step_{group_index}_{step['agent']}"] = result
            else:
                # Parallel execution
                tasks = []
                for step in step_group:
                    task = self._execute_agent_action(
                        step["agent"], step["action"], execution_context
                    )
                    tasks.append((step["agent"], task))

                # Wait for all parallel tasks to complete
                for agent_name, task in tasks:
                    result = await task
                    results[f"step_{group_index}_{agent_name}"] = result

            # Update task status
            await self._update_step_completion(workflow, group_index, execution_context)

        return results

    async def _execute_agent_action(
        self, agent_name: str, action: str, execution_context: Dict[str, Any]
    ) -> Any:
        """Execute a specific action on an agent"""
        agent_role = AgentRole(agent_name)
        agent = self.agents[agent_role]

        logger.info(f"🔄 Executing {action} on {agent_name}")

        try:
            # Route to appropriate agent method
            if agent_role == AgentRole.DEBT_TRACKER:
                if action == "scan_codebase":
                    return await agent.scan_codebase()
                elif action == "analyze_critical_items":
                    # Filter for critical items only
                    all_results = await agent.scan_codebase()
                    critical_items = {
                        category: [item for item in items if item.severity.value == "critical"]
                        for category, items in all_results.items()
                    }
                    return critical_items

            elif agent_role == AgentRole.ARCHITECTURE_REVIEWER:
                if action == "analyze_architecture":
                    return await agent.analyze_architecture()
                elif action == "comprehensive_analysis":
                    return await agent.analyze_architecture()

            elif agent_role == AgentRole.QUALITY_MONITOR:
                if action == "run_quality_analysis":
                    return await agent.run_quality_analysis()
                elif action == "verify_issue_severity":
                    report = await agent.run_quality_analysis()
                    return self._extract_critical_violations(report)
                elif action == "establish_quality_gates":
                    report = await agent.run_quality_analysis()
                    return await agent.check_quality_gates(report)

            elif agent_role == AgentRole.DOCUMENTATION_MAINTAINER:
                if action == "analyze_documentation_health":
                    return await agent.analyze_documentation_health()
                elif action == "document_incident":
                    return await self._create_incident_documentation(execution_context)
                elif action == "create_architecture_docs":
                    return await self._create_architecture_documentation(execution_context)

            elif agent_role == AgentRole.REFACTORING_COORDINATOR:
                if action == "analyze_and_prioritize_debt":
                    # Get debt items and violations from previous steps
                    debt_items = self._extract_debt_items_from_context(execution_context)
                    violations = self._extract_violations_from_context(execution_context)
                    return await agent.analyze_and_prioritize_debt(debt_items, violations)
                elif action == "create_emergency_plan":
                    # Create emergency refactoring plan
                    critical_items = self._extract_critical_items_from_context(execution_context)
                    return await self._create_emergency_refactoring_plan(critical_items)
                elif action == "plan_architectural_refactoring":
                    arch_violations = self._extract_arch_violations_from_context(execution_context)
                    return await self._plan_architectural_refactoring(arch_violations)

            # Send coordination message
            await self._send_agent_message(
                sender=AgentRole.REFACTORING_COORDINATOR,  # Coordinator as sender
                recipient=agent_role,
                message_type="action_request",
                priority=CommunicationPriority.NORMAL,
                subject=f"Execute {action}",
                content={
                    "action": action,
                    "execution_context": execution_context,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return {"status": "completed", "action": action, "agent": agent_name}

        except Exception as e:
            logger.error(f"❌ Failed to execute {action} on {agent_name}: {e}")
            raise

    def _extract_debt_items_from_context(
        self, execution_context: Dict[str, Any]
    ) -> List[TechnicalDebtItem]:
        """Extract debt items from execution context"""
        debt_items = []
        for key, result in execution_context.get("results", {}).items():
            if "debt_tracker" in key and isinstance(result, dict):
                for category, items in result.items():
                    if isinstance(items, list):
                        debt_items.extend(items)
        return debt_items

    def _extract_violations_from_context(
        self, execution_context: Dict[str, Any]
    ) -> List[ArchitecturalViolation]:
        """Extract architectural violations from execution context"""
        violations = []
        for key, result in execution_context.get("results", {}).items():
            if "architecture_reviewer" in key and isinstance(result, dict):
                violations_data = result.get("violations", [])
                # Convert dict to ArchitecturalViolation objects if needed
                violations.extend(violations_data)
        return violations

    def _extract_critical_violations(self, quality_report: QualityReport) -> Dict[str, Any]:
        """Extract critical violations from quality report"""
        critical_violations = [
            v for v in quality_report.violations if v.severity.value in ["blocker", "critical"]
        ]

        return {
            "critical_violations": critical_violations,
            "total_critical": len(critical_violations),
            "severity_breakdown": {
                "blocker": len([v for v in critical_violations if v.severity.value == "blocker"]),
                "critical": len([v for v in critical_violations if v.severity.value == "critical"]),
            },
        }

    def _extract_critical_items_from_context(self, execution_context: Dict[str, Any]) -> List[Any]:
        """Extract critical items from execution context"""
        critical_items = []
        for key, result in execution_context.get("results", {}).items():
            if isinstance(result, dict):
                for category, items in result.items():
                    if isinstance(items, list):
                        critical_items.extend(
                            [
                                item
                                for item in items
                                if hasattr(item, "severity") and item.severity.value == "critical"
                            ]
                        )
        return critical_items

    def _extract_arch_violations_from_context(self, execution_context: Dict[str, Any]) -> List[Any]:
        """Extract architectural violations from execution context"""
        violations = []
        for key, result in execution_context.get("results", {}).items():
            if "architecture" in key and isinstance(result, dict):
                violations.extend(result.get("violations", []))
        return violations

    async def _create_incident_documentation(
        self, execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create incident documentation for critical issues"""
        incident_doc = {
            "incident_id": execution_context["execution_id"],
            "timestamp": datetime.now().isoformat(),
            "severity": "critical",
            "description": "Critical technical debt or quality issue detected",
            "affected_systems": [],
            "response_actions": [],
            "resolution_plan": execution_context.get("results", {}),
            "stakeholders_notified": [],
            "status": "investigating",
        }

        return incident_doc

    async def _create_architecture_documentation(
        self, execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create architecture documentation from analysis results"""
        arch_doc = {
            "document_type": "architectural_analysis",
            "generated_at": datetime.now().isoformat(),
            "analysis_results": execution_context.get("results", {}),
            "recommendations": [],
            "implementation_plan": {},
            "stakeholder_approval": "pending",
        }

        return arch_doc

    async def _create_emergency_refactoring_plan(self, critical_items: List[Any]) -> Dict[str, Any]:
        """Create emergency refactoring plan for critical issues"""
        emergency_plan = {
            "plan_type": "emergency_refactoring",
            "created_at": datetime.now().isoformat(),
            "critical_items": len(critical_items),
            "immediate_actions": [],
            "timeline": "24-48 hours",
            "resource_requirements": [],
            "risk_mitigation": [],
            "success_criteria": [],
        }

        # Add immediate actions based on critical items
        for item in critical_items[:5]:  # Top 5 critical items
            emergency_plan["immediate_actions"].append(
                {
                    "item_id": getattr(item, "id", "unknown"),
                    "action": "immediate_fix_required",
                    "estimated_hours": 2,
                    "assigned_to": "senior_developer",
                }
            )

        return emergency_plan

    async def _plan_architectural_refactoring(self, violations: List[Any]) -> Dict[str, Any]:
        """Plan architectural refactoring based on violations"""
        refactoring_plan = {
            "plan_type": "architectural_refactoring",
            "created_at": datetime.now().isoformat(),
            "violations_addressed": len(violations),
            "refactoring_phases": [],
            "estimated_duration": "2-4 weeks",
            "resource_requirements": [],
            "quality_gates": [],
        }

        return refactoring_plan

    async def _update_step_completion(
        self, workflow: WorkflowDefinition, step_index: int, execution_context: Dict[str, Any]
    ):
        """Update task status after step completion"""
        # Find and update relevant tasks
        for task_id, task in self.active_tasks.items():
            if (
                task.context.get("workflow_id") == workflow.id
                and task.context.get("step_index") == step_index
            ):
                task.status = TaskStatus.COMPLETED
                task.progress_percentage = 100.0

                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                break

    async def _validate_workflow_success(
        self, workflow: WorkflowDefinition, results: Dict[str, Any]
    ) -> bool:
        """Validate workflow success criteria"""
        for criteria in workflow.success_criteria:
            if not self._check_success_criteria(criteria, results):
                logger.warning(f"Success criteria not met: {criteria}")
                return False

        return True

    def _check_success_criteria(self, criteria: str, results: Dict[str, Any]) -> bool:
        """Check individual success criteria"""
        # Simple criteria checking - can be enhanced
        if "completed successfully" in criteria:
            return len(results) > 0 and all(
                result.get("status") != "failed"
                for result in results.values()
                if isinstance(result, dict)
            )
        elif "plan generated" in criteria:
            return any("plan" in str(result) for result in results.values())
        elif "reports exported" in criteria:
            return any("report" in str(result) for result in results.values())
        else:
            return True  # Default to true for unknown criteria

    async def _update_workflow_metrics(
        self, workflow: WorkflowDefinition, execution_context: Dict[str, Any]
    ):
        """Update ecosystem metrics after workflow completion"""
        self.performance_metrics.total_tasks_completed += len(workflow.steps)

        if execution_context.get("duration"):
            # Update average completion time
            current_avg = self.performance_metrics.average_task_completion_time
            new_duration = execution_context["duration"]
            total_completed = self.performance_metrics.total_tasks_completed

            self.performance_metrics.average_task_completion_time = (
                current_avg * (total_completed - len(workflow.steps)) + new_duration
            ) / total_completed

        # Update agent utilization
        for agent in workflow.required_agents:
            current_util = self.performance_metrics.agent_utilization[agent]
            self.performance_metrics.agent_utilization[agent] = min(100.0, current_util + 10.0)

        # Update communication volume
        self.performance_metrics.communication_volume["workflow_messages"] += (
            len(workflow.steps) * 2
        )

    async def _send_agent_message(
        self,
        sender: AgentRole,
        recipient: AgentRole,
        message_type: str,
        priority: CommunicationPriority,
        subject: str,
        content: Dict[str, Any],
        requires_response: bool = False,
        response_deadline: Optional[datetime] = None,
    ) -> str:
        """Send message between agents"""
        message_id = str(uuid.uuid4())

        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            priority=priority,
            subject=subject,
            content=content,
            requires_response=requires_response,
            response_deadline=response_deadline,
        )

        self.message_queue.append(message)

        logger.info(f"📨 Message sent: {sender.value} → {recipient.value} ({subject})")

        return message_id

    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "pending_messages": len(self.message_queue),
            "agent_status": {},
            "recent_activities": [],
            "performance_metrics": asdict(self.performance_metrics),
            "workflow_definitions": len(self.workflows),
            "system_health": "healthy",
        }

        # Agent status
        for role, agent in self.agents.items():
            agent_tasks = [
                task for task in self.active_tasks.values() if task.primary_agent == role
            ]
            status["agent_status"][role.value] = {
                "active_tasks": len(agent_tasks),
                "utilization": self.performance_metrics.agent_utilization[role],
                "last_activity": datetime.now().isoformat(),  # Simplified
                "status": "active",
            }

        # Recent activities
        recent_tasks = list(self.completed_tasks)[-10:]  # Last 10 completed tasks
        for task in recent_tasks:
            status["recent_activities"].append(
                {
                    "task_id": task.id,
                    "title": task.title,
                    "agent": task.primary_agent.value,
                    "completed_at": datetime.now().isoformat(),  # Simplified
                    "duration": task.estimated_duration.total_seconds(),
                }
            )

        return status

    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive technical debt analysis workflow"""
        logger.info("🔄 Starting comprehensive technical debt analysis...")

        context = {
            "analysis_type": "comprehensive",
            "requested_by": "system",
            "include_recommendations": True,
            "export_reports": True,
        }

        result = await self.execute_workflow("comprehensive_debt_analysis", context)

        # Generate summary report
        summary = await self._generate_analysis_summary(result)

        return {
            "workflow_result": result,
            "summary": summary,
            "recommendations": await self._extract_recommendations_from_results(result),
            "next_actions": await self._suggest_next_actions(result),
        }

    async def _generate_analysis_summary(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from comprehensive analysis results"""
        summary = {
            "execution_status": workflow_result.get("status", "unknown"),
            "duration_seconds": workflow_result.get("duration", 0),
            "agents_involved": len(
                set(
                    step.split("_")[2]
                    for step in workflow_result.get("results", {}).keys()
                    if "_" in step
                )
            ),
            "issues_identified": 0,
            "critical_issues": 0,
            "recommendations_generated": 0,
            "overall_health_score": 0.0,
        }

        # Analyze results for metrics
        results = workflow_result.get("results", {})
        for key, result in results.items():
            if isinstance(result, dict):
                if "violations" in result:
                    summary["issues_identified"] += len(result["violations"])
                    summary["critical_issues"] += len(
                        [
                            v
                            for v in result["violations"]
                            if hasattr(v, "severity") and v.severity.value == "critical"
                        ]
                    )
                elif "recommendations" in result:
                    summary["recommendations_generated"] += len(result["recommendations"])

        return summary

    async def _extract_recommendations_from_results(
        self, workflow_result: Dict[str, Any]
    ) -> List[str]:
        """Extract all recommendations from workflow results"""
        recommendations = []

        results = workflow_result.get("results", {})
        for key, result in results.items():
            if isinstance(result, dict):
                if "recommendations" in result:
                    recommendations.extend(result["recommendations"])
                elif "maintenance_recommendations" in result:
                    recommendations.extend(result["maintenance_recommendations"])

        return list(set(recommendations))  # Remove duplicates

    async def _suggest_next_actions(self, workflow_result: Dict[str, Any]) -> List[str]:
        """Suggest next actions based on analysis results"""
        next_actions = [
            "📋 Review generated refactoring plan and prioritize tasks",
            "👥 Assign refactoring tasks to development teams",
            "📊 Schedule regular technical debt monitoring",
            "🔍 Set up automated quality gates in CI/CD pipeline",
        ]

        # Add specific actions based on results
        if workflow_result.get("status") == "completed":
            next_actions.insert(
                0, "✅ Analysis completed successfully - proceed with implementation"
            )
        else:
            next_actions.insert(0, "⚠️  Analysis incomplete - review errors and retry")

        return next_actions

    async def export_ecosystem_report(self, output_path: str) -> str:
        """Export comprehensive ecosystem report"""
        report_data = {
            "export_timestamp": datetime.now().isoformat(),
            "ecosystem_status": await self.get_ecosystem_status(),
            "active_tasks": [asdict(task) for task in self.active_tasks.values()],
            "completed_tasks": [asdict(task) for task in list(self.completed_tasks)],
            "communication_log": [asdict(msg) for msg in list(self.message_queue)],
            "workflow_definitions": [asdict(wf) for wf in self.workflows],
            "coordination_rules": self.coordination_rules,
            "performance_metrics": asdict(self.performance_metrics),
        }

        # JSON serialization helper
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, timedelta):
                return obj.total_seconds()
            elif isinstance(obj, (AgentRole, TaskStatus, CommunicationPriority)):
                return obj.value
            return str(obj)

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2, default=json_serializer)

        logger.info(f"🗂️  Ecosystem report exported to {output_path}")
        return output_path


# Initialize the agent ecosystem coordinator
ecosystem_coordinator = AgentEcosystemCoordinator(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
