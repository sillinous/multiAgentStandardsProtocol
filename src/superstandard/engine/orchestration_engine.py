"""
AI-Powered Orchestration Engine
================================

Intelligent orchestration of composite agents with AI-driven:
- Dynamic routing and task assignment
- Parallel execution optimization
- Intelligent error recovery
- Real-time progress monitoring
- Cross-agent communication coordination

Integrates with smart_processing for domain-specific intelligence.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from uuid import uuid4
import json


class ExecutionStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Status of individual step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """Represents a single step in workflow execution"""
    step_id: str
    agent_id: str
    agent_name: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": (self.completed_at - self.started_at).total_seconds() * 1000 if self.completed_at and self.started_at else None,
            "has_output": bool(self.output_data),
            "error": self.error,
            "metrics": self.metrics,
            "ai_analysis": self.ai_analysis
        }


@dataclass
class WorkflowExecution:
    """Tracks a complete workflow execution"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[ExecutionStep] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    ai_orchestration: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": (self.completed_at - self.started_at).total_seconds() * 1000 if self.completed_at and self.started_at else None,
            "steps_total": len(self.steps),
            "steps_completed": len([s for s in self.steps if s.status == StepStatus.COMPLETED]),
            "steps_failed": len([s for s in self.steps if s.status == StepStatus.FAILED]),
            "progress_percent": (len([s for s in self.steps if s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]]) / len(self.steps) * 100) if self.steps else 0,
            "steps": [s.to_dict() for s in self.steps],
            "ai_orchestration": self.ai_orchestration,
            "error": self.error
        }


class OrchestrationEngine:
    """
    AI-Powered Workflow Orchestration Engine

    Features:
    - Intelligent step ordering based on dependencies
    - Parallel execution for independent steps
    - AI-driven error recovery and retry logic
    - Real-time monitoring and progress tracking
    - Cross-agent data passing and transformation
    """

    def __init__(self):
        self.logger = logging.getLogger("OrchestrationEngine")
        self.executions: Dict[str, WorkflowExecution] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}

        # Callbacks for real-time updates
        self.on_step_start: Optional[Callable] = None
        self.on_step_complete: Optional[Callable] = None
        self.on_workflow_complete: Optional[Callable] = None

        self.logger.info("OrchestrationEngine initialized")

    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow with AI-powered orchestration

        Args:
            workflow_id: Unique workflow identifier (e.g., APQC code)
            workflow_name: Human-readable workflow name
            agent_ids: List of agent IDs to execute
            input_data: Initial input data
            options: Execution options (parallel, retry, etc.)

        Returns:
            WorkflowExecution with complete results
        """
        options = options or {}
        execution_id = str(uuid4())[:8]

        # Create execution record
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_data=input_data,
            context=options.get("context", {})
        )

        # Create steps for each agent
        for i, agent_id in enumerate(agent_ids):
            step = ExecutionStep(
                step_id=f"{execution_id}-step-{i+1}",
                agent_id=agent_id,
                agent_name=self._get_agent_name(agent_id)
            )
            execution.steps.append(step)

        self.executions[execution_id] = execution

        # AI-powered orchestration analysis
        execution.ai_orchestration = await self._analyze_workflow(
            agent_ids, input_data, options
        )

        # Start execution
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now()

        try:
            # Determine execution strategy
            strategy = execution.ai_orchestration.get("strategy", "sequential")

            if strategy == "parallel" and options.get("allow_parallel", True):
                await self._execute_parallel(execution, options)
            else:
                await self._execute_sequential(execution, options)

            # Mark completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()

            # Generate final output
            execution.output_data = self._aggregate_results(execution)

            # AI summary of execution
            execution.ai_orchestration["summary"] = await self._generate_execution_summary(execution)

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            self.logger.error(f"Workflow execution failed: {e}")

        # Callback
        if self.on_workflow_complete:
            await self.on_workflow_complete(execution)

        return execution

    async def _analyze_workflow(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to analyze and optimize workflow execution"""
        try:
            from superstandard.services.smart_processing import get_processor
            from superstandard.services.ai_service import get_ai_service

            ai_service = get_ai_service()

            # Analyze workflow structure
            analysis = await ai_service.analyze(
                prompt=f"""Analyze this workflow for optimal execution:
                - Agents: {len(agent_ids)} steps
                - First agents: {agent_ids[:3]}
                - Input type: {list(input_data.keys()) if input_data else 'none'}

                Determine:
                1. Can any steps run in parallel?
                2. What's the optimal execution order?
                3. What are potential bottlenecks?
                4. Estimated complexity (low/medium/high)
                """,
                data={"agent_ids": agent_ids[:10], "input_keys": list(input_data.keys())}
            )

            return {
                "strategy": analysis.get("strategy", "sequential"),
                "parallel_groups": analysis.get("parallel_groups", []),
                "estimated_duration": analysis.get("estimated_duration", "unknown"),
                "complexity": analysis.get("complexity", "medium"),
                "optimization_notes": analysis.get("notes", []),
                "ai_confidence": analysis.get("confidence", 0.7)
            }

        except Exception as e:
            self.logger.warning(f"AI analysis failed, using defaults: {e}")
            return {
                "strategy": "sequential",
                "parallel_groups": [],
                "complexity": "unknown",
                "ai_confidence": 0.0
            }

    async def _execute_sequential(
        self,
        execution: WorkflowExecution,
        options: Dict[str, Any]
    ):
        """Execute steps sequentially with AI-powered data passing"""
        current_data = execution.input_data.copy()
        max_retries = options.get("max_retries", 2)

        for step in execution.steps:
            # Callback
            if self.on_step_start:
                await self.on_step_start(execution, step)

            step.status = StepStatus.RUNNING
            step.started_at = datetime.now()
            step.input_data = current_data.copy()

            try:
                # Execute the agent
                result = await self._execute_agent(
                    step.agent_id,
                    current_data,
                    execution.context
                )

                step.output_data = result.get("output", {})
                step.metrics = result.get("metrics", {})
                step.ai_analysis = result.get("ai_analysis", {})
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()

                # Update current data for next step
                if step.output_data:
                    current_data.update(step.output_data)

            except Exception as e:
                step.error = str(e)
                step.status = StepStatus.FAILED
                step.completed_at = datetime.now()

                # AI-powered error recovery
                if options.get("auto_recover", True):
                    recovery = await self._attempt_recovery(step, e, max_retries)
                    if recovery.get("recovered"):
                        step.status = StepStatus.COMPLETED
                        step.output_data = recovery.get("output", {})
                        current_data.update(step.output_data)
                    elif not options.get("stop_on_error", True):
                        continue
                    else:
                        raise

            # Callback
            if self.on_step_complete:
                await self.on_step_complete(execution, step)

    async def _execute_parallel(
        self,
        execution: WorkflowExecution,
        options: Dict[str, Any]
    ):
        """Execute independent steps in parallel"""
        parallel_groups = execution.ai_orchestration.get("parallel_groups", [])

        if not parallel_groups:
            # Fall back to sequential
            await self._execute_sequential(execution, options)
            return

        current_data = execution.input_data.copy()

        for group in parallel_groups:
            # Get steps for this group
            group_steps = [s for s in execution.steps if s.agent_id in group]

            # Execute group in parallel
            tasks = []
            for step in group_steps:
                step.status = StepStatus.RUNNING
                step.started_at = datetime.now()
                step.input_data = current_data.copy()

                task = asyncio.create_task(
                    self._execute_agent(step.agent_id, current_data, execution.context)
                )
                tasks.append((step, task))

            # Wait for all tasks in group
            for step, task in tasks:
                try:
                    result = await task
                    step.output_data = result.get("output", {})
                    step.metrics = result.get("metrics", {})
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.now()

                    # Merge outputs
                    current_data.update(step.output_data)

                except Exception as e:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    step.completed_at = datetime.now()

    async def _execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single agent with smart processing"""
        try:
            from superstandard.services.smart_processing import get_processor

            # Determine domain from agent ID
            domain = self._get_domain_from_agent(agent_id)
            processor = get_processor(domain)

            # Execute with smart processing
            result = await processor.process(
                {
                    "agent_id": agent_id,
                    "data": input_data,
                    "context": context
                },
                task_type="workflow_step"
            )

            return {
                "output": result.get("result", result),
                "metrics": {
                    "domain": domain,
                    "ai_powered": True,
                    "timestamp": datetime.now().isoformat()
                },
                "ai_analysis": result.get("analysis", {})
            }

        except Exception as e:
            self.logger.error(f"Agent execution failed: {agent_id} - {e}")
            raise

    async def _attempt_recovery(
        self,
        step: ExecutionStep,
        error: Exception,
        max_retries: int
    ) -> Dict[str, Any]:
        """AI-powered error recovery"""
        try:
            from superstandard.services.ai_service import get_ai_service

            ai_service = get_ai_service()

            # Analyze error and get recovery strategy
            recovery_analysis = await ai_service.analyze(
                prompt=f"""Analyze this workflow step failure and suggest recovery:
                Agent: {step.agent_id}
                Error: {str(error)}
                Input data keys: {list(step.input_data.keys())}

                Suggest:
                1. Can this be retried?
                2. Should we skip this step?
                3. Is there alternative data we can use?
                """,
                data={"agent_id": step.agent_id, "error": str(error)}
            )

            if recovery_analysis.get("can_retry", False):
                # Retry the step
                for attempt in range(max_retries):
                    try:
                        result = await self._execute_agent(
                            step.agent_id,
                            step.input_data,
                            {}
                        )
                        return {"recovered": True, "output": result.get("output", {})}
                    except Exception:
                        continue

            return {"recovered": False, "reason": recovery_analysis.get("reason", "Max retries exceeded")}

        except Exception:
            return {"recovered": False, "reason": "Recovery analysis failed"}

    async def _generate_execution_summary(
        self,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Generate AI summary of workflow execution"""
        try:
            from superstandard.services.ai_service import get_ai_service

            ai_service = get_ai_service()

            completed_steps = [s for s in execution.steps if s.status == StepStatus.COMPLETED]
            failed_steps = [s for s in execution.steps if s.status == StepStatus.FAILED]

            summary = await ai_service.analyze(
                prompt=f"""Summarize this workflow execution:
                - Workflow: {execution.workflow_name}
                - Total steps: {len(execution.steps)}
                - Completed: {len(completed_steps)}
                - Failed: {len(failed_steps)}
                - Duration: {(execution.completed_at - execution.started_at).total_seconds() if execution.completed_at and execution.started_at else 'unknown'}s

                Provide:
                1. Brief summary (1-2 sentences)
                2. Key outcomes
                3. Any recommendations
                """,
                data={"workflow_id": execution.workflow_id}
            )

            return {
                "summary": summary.get("summary", "Workflow execution completed"),
                "outcomes": summary.get("outcomes", []),
                "recommendations": summary.get("recommendations", []),
                "performance_rating": summary.get("rating", "good")
            }

        except Exception:
            return {
                "summary": f"Workflow completed with {len([s for s in execution.steps if s.status == StepStatus.COMPLETED])}/{len(execution.steps)} steps successful",
                "outcomes": [],
                "recommendations": []
            }

    def _aggregate_results(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate results from all steps"""
        aggregated = {}

        for step in execution.steps:
            if step.status == StepStatus.COMPLETED and step.output_data:
                aggregated[step.agent_id] = step.output_data

        return {
            "aggregated_outputs": aggregated,
            "final_state": execution.steps[-1].output_data if execution.steps else {},
            "steps_completed": len([s for s in execution.steps if s.status == StepStatus.COMPLETED]),
            "total_steps": len(execution.steps)
        }

    def _get_agent_name(self, agent_id: str) -> str:
        """Get human-readable name for agent"""
        # Map APQC codes to names (simplified)
        apqc_names = {
            "1": "Develop Vision and Strategy",
            "2": "Develop and Manage Products and Services",
            "3": "Market and Sell Products and Services",
            "4": "Deliver Physical Products",
            "5": "Deliver Services",
            "6": "Manage Customer Service",
            "7": "Develop and Manage Human Capital",
            "8": "Manage Financial Resources",
            "9": "Acquire, Construct, and Manage Assets",
            "10": "Manage Enterprise Risk",
            "11": "Manage External Relationships",
            "12": "Develop and Manage Business Capabilities",
            "13": "Manage Knowledge and Information Technology"
        }

        # Get top-level category
        top_level = agent_id.split(".")[0] if "." in agent_id else agent_id
        return apqc_names.get(top_level, f"Agent {agent_id}")

    def _get_domain_from_agent(self, agent_id: str) -> str:
        """Determine domain from agent ID"""
        top_level = agent_id.split(".")[0] if "." in agent_id else agent_id

        domain_map = {
            "1": "operations",  # Vision/Strategy
            "2": "operations",  # Products/Services
            "3": "customer_service",  # Marketing/Sales
            "4": "operations",  # Delivery
            "5": "operations",  # Services
            "6": "customer_service",  # Customer Service
            "7": "hr",  # Human Capital
            "8": "finance",  # Financial
            "9": "operations",  # Assets
            "10": "operations",  # Risk
            "11": "operations",  # External Relations
            "12": "operations",  # Business Capabilities
            "13": "it"  # IT/Knowledge
        }

        return domain_map.get(top_level, "operations")

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)

    def list_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent executions"""
        executions = sorted(
            self.executions.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:limit]

        return [e.to_dict() for e in executions]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.now()

            if execution_id in self.active_executions:
                self.active_executions[execution_id].cancel()

            return True
        return False


# Global instance
orchestration_engine = OrchestrationEngine()


def get_orchestration_engine() -> OrchestrationEngine:
    """Get the global orchestration engine instance"""
    return orchestration_engine
