"""
Coordinator Meta-Agent

Orchestrates multi-agent workflows using A2A protocol.
Implements supervisor and swarm coordination patterns.
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..a2a.protocol import (
    AgentInfo,
    Capability,
    A2AEnvelope,
    MessageType,
    Priority,
    create_task_assignment,
    create_status_update
)
from ..a2a.bus import A2AMessageBus, get_message_bus


@dataclass
class Task:
    """Represents a task in a workflow"""
    task_id: str
    task_type: str
    assigned_to: Optional[str] = None
    parameters: Dict[str, Any] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if self.parameters is None:
            self.parameters = {}


@dataclass
class WorkflowPhase:
    """Represents a phase in a workflow"""
    phase_id: str
    name: str
    tasks: List[Task]
    status: str = "pending"  # pending, in_progress, completed, failed
    parallel: bool = False  # Can tasks run in parallel?


class CoordinatorMetaAgent:
    """
    Coordinator Meta-Agent - Orchestrates Multi-Agent Workflows

    Implements coordination patterns:
    - Supervisor Pattern: Coordinates subordinate agents
    - Swarm Pattern: Enables peer-to-peer collaboration
    - Pipeline Pattern: Sequential task execution
    - Parallel Pattern: Concurrent task execution

    Uses A2A protocol for all agent communication.
    """

    def __init__(self, name: str = "CoordinatorMetaAgent", bus: Optional[A2AMessageBus] = None):
        """
        Initialize coordinator meta-agent

        Args:
            name: Name for this coordinator
            bus: A2A message bus (uses global if not provided)
        """
        self.logger = logging.getLogger(__name__)
        self.bus = bus or get_message_bus()

        # Coordinator's own agent info
        self.agent_info = AgentInfo(
            agent_id=f"coordinator-meta-{uuid.uuid4().hex[:8]}",
            agent_type="meta-agent",
            name=name,
            capabilities=[
                Capability(
                    name="workflow_orchestration",
                    version="1.0.0",
                    description="Orchestrates multi-agent workflows"
                ),
                Capability(
                    name="task_coordination",
                    version="1.0.0",
                    description="Coordinates task assignment and tracking"
                )
            ],
            metadata={
                "role": "coordinator",
                "meta_level": 1
            }
        )

        # Register with bus
        self.bus.register_agent(self.agent_info)

        # Register message handlers
        self.bus.register_handler(
            self.agent_info.agent_id,
            {
                MessageType.TASK_COMPLETED,
                MessageType.TASK_FAILED,
                MessageType.STATUS_UPDATE
            },
            self._handle_message
        )

        # Workflow state
        self.workflows: Dict[str, List[WorkflowPhase]] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_futures: Dict[str, asyncio.Future] = {}

        self.logger.info(f"✅ CoordinatorMetaAgent initialized: {self.agent_info.agent_id}")

    async def _handle_message(self, envelope: A2AEnvelope) -> Optional[A2AEnvelope]:
        """Handle incoming A2A messages"""
        if not envelope.message:
            return None

        message = envelope.message
        message_type = message.message_type

        if message_type == MessageType.TASK_COMPLETED:
            await self._handle_task_completed(envelope)
        elif message_type == MessageType.TASK_FAILED:
            await self._handle_task_failed(envelope)
        elif message_type == MessageType.STATUS_UPDATE:
            await self._handle_status_update(envelope)

        return None

    async def _handle_task_completed(self, envelope: A2AEnvelope):
        """Handle task completion message"""
        content = envelope.message.content
        task_id = content.get("task_id")

        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "completed"
            task.result = content.get("result", {})
            task.completed_at = datetime.utcnow().isoformat()

            self.logger.info(f"✅ Task completed: {task_id}")

            # Resolve future if waiting
            if task_id in self.task_futures:
                future = self.task_futures[task_id]
                if not future.done():
                    future.set_result(task.result)

    async def _handle_task_failed(self, envelope: A2AEnvelope):
        """Handle task failure message"""
        content = envelope.message.content
        task_id = content.get("task_id")

        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "failed"
            task.result = {"error": content.get("error", "Unknown error")}
            task.completed_at = datetime.utcnow().isoformat()

            self.logger.error(f"❌ Task failed: {task_id}")

            # Resolve future with exception
            if task_id in self.task_futures:
                future = self.task_futures[task_id]
                if not future.done():
                    future.set_exception(Exception(content.get("error", "Task failed")))

    async def _handle_status_update(self, envelope: A2AEnvelope):
        """Handle status update message"""
        content = envelope.message.content
        self.logger.info(
            f"📊 Status update from {envelope.from_agent}: {content.get('status')}"
        )

    async def execute_workflow(
        self,
        workflow_id: str,
        phases: List[WorkflowPhase],
        agents: List[AgentInfo]
    ) -> Dict[str, Any]:
        """
        Execute a multi-phase workflow

        Args:
            workflow_id: Unique workflow identifier
            phases: List of workflow phases
            agents: List of available agents

        Returns:
            Workflow execution results
        """
        self.logger.info(f"🚀 Executing workflow: {workflow_id}")
        self.logger.info(f"   Phases: {len(phases)}")
        self.logger.info(f"   Agents: {len(agents)}")

        self.workflows[workflow_id] = phases

        results = {}

        for phase in phases:
            self.logger.info(f"▶️  Starting phase: {phase.name}")
            phase.status = "in_progress"

            # Send status update
            status_envelope = create_status_update(
                self.agent_info,
                f"phase_started",
                {"phase": phase.name, "workflow_id": workflow_id}
            )
            await self.bus.send(status_envelope)

            try:
                if phase.parallel:
                    # Execute tasks in parallel
                    phase_results = await self._execute_tasks_parallel(
                        phase.tasks,
                        agents
                    )
                else:
                    # Execute tasks sequentially
                    phase_results = await self._execute_tasks_sequential(
                        phase.tasks,
                        agents
                    )

                results[phase.phase_id] = phase_results
                phase.status = "completed"

                self.logger.info(f"✅ Phase completed: {phase.name}")

                # Send status update
                status_envelope = create_status_update(
                    self.agent_info,
                    f"phase_completed",
                    {
                        "phase": phase.name,
                        "workflow_id": workflow_id,
                        "results": phase_results
                    }
                )
                await self.bus.send(status_envelope)

            except Exception as e:
                phase.status = "failed"
                self.logger.error(f"❌ Phase failed: {phase.name}: {e}")
                results[phase.phase_id] = {"error": str(e)}
                raise

        self.logger.info(f"✅ Workflow completed: {workflow_id}")

        return results

    async def _execute_tasks_parallel(
        self,
        tasks: List[Task],
        agents: List[AgentInfo]
    ) -> Dict[str, Any]:
        """Execute tasks in parallel"""
        self.logger.info(f"⚡ Executing {len(tasks)} tasks in parallel")

        # Create futures for all tasks
        task_coroutines = []
        for task in tasks:
            task_coroutines.append(self._execute_task(task, agents))

        # Wait for all to complete
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect results
        task_results = {}
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                task_results[task.task_id] = {"error": str(result)}
            else:
                task_results[task.task_id] = result

        return task_results

    async def _execute_tasks_sequential(
        self,
        tasks: List[Task],
        agents: List[AgentInfo]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially"""
        self.logger.info(f"➡️  Executing {len(tasks)} tasks sequentially")

        task_results = {}
        for task in tasks:
            result = await self._execute_task(task, agents)
            task_results[task.task_id] = result

        return task_results

    async def _execute_task(
        self,
        task: Task,
        agents: List[AgentInfo]
    ) -> Dict[str, Any]:
        """Execute a single task"""
        self.logger.info(f"🎯 Executing task: {task.task_id} (type: {task.task_type})")

        # Find suitable agent
        agent = self._select_agent(task, agents)
        if not agent:
            raise ValueError(f"No suitable agent found for task {task.task_id}")

        # Assign task
        task.assigned_to = agent.agent_id
        task.status = "assigned"
        self.tasks[task.task_id] = task

        # Create task assignment message
        envelope = create_task_assignment(
            self.agent_info,
            agent,
            task.task_id,
            task.task_type,
            task.parameters,
            Priority.NORMAL
        )

        # Create future for result
        future = asyncio.Future()
        self.task_futures[task.task_id] = future

        # Send task assignment
        await self.bus.send(envelope)

        task.status = "in_progress"
        self.logger.info(f"📤 Task assigned to {agent.name}")

        # Wait for completion (with timeout)
        try:
            result = await asyncio.wait_for(future, timeout=60.0)
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"⏱️  Task {task.task_id} timed out")
            task.status = "failed"
            raise
        finally:
            # Cleanup
            if task.task_id in self.task_futures:
                del self.task_futures[task.task_id]

    def _select_agent(self, task: Task, agents: List[AgentInfo]) -> Optional[AgentInfo]:
        """Select best agent for a task"""
        # Simple selection: first agent with matching capability
        for agent in agents:
            for capability in agent.capabilities:
                if capability.name == task.task_type:
                    return agent

        # Fallback: return first agent
        return agents[0] if agents else None

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        if workflow_id not in self.workflows:
            return None

        phases = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "total_phases": len(phases),
            "phases": [
                {
                    "phase_id": phase.phase_id,
                    "name": phase.name,
                    "status": phase.status,
                    "tasks": len(phase.tasks)
                }
                for phase in phases
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics"""
        return {
            "coordinator_id": self.agent_info.agent_id,
            "name": self.agent_info.name,
            "active_workflows": len(self.workflows),
            "total_tasks": len(self.tasks),
            "active_tasks": len([t for t in self.tasks.values() if t.status == "in_progress"]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"])
        }
