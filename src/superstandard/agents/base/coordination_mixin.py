"""
Coordination Mixin for BaseAgent - Seamless ACP Integration

This module provides a mixin that adds coordination capabilities to any BaseAgent,
enabling agents to participate in multi-agent coordination sessions for task
orchestration and collaborative work.

Usage:
    from superstandard.agents.base.base_agent import BaseAgent
    from superstandard.agents.base.coordination_mixin import CoordinationMixin
    from superstandard.protocols.acp_implementation import CoordinationType

    class MyAgent(CoordinationMixin, BaseAgent):
        async def execute_task(self, task):
            # Agent can now coordinate with others
            await self.join_coordination(session_id, role="participant")
            task = await self.request_task()
            result = await self.process_task(task)
            await self.submit_result(task['task_id'], result)
            return result

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import asyncio

# Import ACP protocol
try:
    from superstandard.protocols.acp_implementation import (
        CoordinationManager,
        CoordinationSession,
        CoordinationType,
        TaskStatus,
        Task,
    )
    ACP_AVAILABLE = True
except ImportError:
    ACP_AVAILABLE = False
    class CoordinationType:
        SWARM = "swarm"
    class TaskStatus:
        PENDING = "pending"


class CoordinationError(Exception):
    """Raised when coordination operations fail"""
    pass


class CoordinationMixin:
    """
    Mixin that adds coordination capabilities to BaseAgent.

    This mixin provides:
    - Session participation management
    - Task request and execution
    - Progress reporting
    - Result submission
    - Collaborative workflows

    Methods added to agent:
    - join_coordination(session_id, role) - Join coordination session
    - leave_coordination() - Leave session
    - request_task() - Request task from coordinator
    - accept_task(task_id) - Accept specific task
    - reject_task(task_id, reason) - Reject task
    - report_progress(task_id, progress) - Report task progress
    - submit_result(task_id, result) - Submit task result
    - get_coordination_state() - Get current coordination state
    """

    def __init__(self, *args, **kwargs):
        """Initialize coordination capabilities."""
        super().__init__(*args, **kwargs)

        # Coordination state
        self._coordination_manager: Optional['CoordinationManager'] = None
        self._coordination_enabled = ACP_AVAILABLE
        self._current_session_id: Optional[str] = None
        self._current_role: str = "participant"
        self._assigned_tasks: Dict[str, Dict[str, Any]] = {}
        self._completed_tasks: List[str] = []

    async def join_coordination(
        self,
        manager: 'CoordinationManager',
        session_id: str,
        role: str = "participant",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Join a coordination session.

        This allows the agent to participate in coordinated multi-agent workflows.

        Args:
            manager: The CoordinationManager
            session_id: Session ID to join
            role: Agent's role (coordinator, participant, observer)
            metadata: Additional metadata

        Returns:
            True if successfully joined

        Raises:
            CoordinationError: If ACP protocol not available

        Example:
            manager = CoordinationManager()
            session_id = await manager.create_session(...)
            await agent.join_coordination(manager, session_id, role="participant")
        """
        if not self._coordination_enabled:
            raise CoordinationError(
                "ACP protocol not available. Install acp_implementation module."
            )

        if self._current_session_id is not None:
            # Already in a session - leave first
            await self.leave_coordination()

        # Add participant to session
        success = await manager.add_participant(
            session_id,
            self.agent_id,
            self.agent_type,
            self.capabilities_list if hasattr(self, 'capabilities_list') else [],
            role,
            metadata or {}
        )

        if success:
            self._coordination_manager = manager
            self._current_session_id = session_id
            self._current_role = role

            print(f"[{self.agent_id}] Joined coordination session: {session_id}")
            print(f"  Role: {role}")

        return success

    async def leave_coordination(self) -> bool:
        """
        Leave current coordination session.

        Returns:
            True if successfully left
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return False

        # Remove participant
        success = await self._coordination_manager.remove_participant(
            self._current_session_id,
            self.agent_id
        )

        if success:
            self._coordination_manager = None
            self._current_session_id = None
            self._current_role = "participant"
            self._assigned_tasks.clear()

            print(f"[{self.agent_id}] Left coordination session")

        return success

    async def request_task(
        self,
        preferred_type: Optional[str] = None,
        max_priority: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Request a task from the coordinator.

        Args:
            preferred_type: Preferred task type
            max_priority: Only request tasks with priority <= this

        Returns:
            Task dictionary or None if no tasks available

        Raises:
            CoordinationError: If not in coordination session

        Example:
            task = await agent.request_task(preferred_type="analysis")
            if task:
                result = await agent.process(task)
                await agent.submit_result(task['task_id'], result)
        """
        if self._current_session_id is None or self._coordination_manager is None:
            raise CoordinationError("Agent must be in coordination session to request tasks")

        # Get available tasks
        session = self._coordination_manager.sessions.get(self._current_session_id)
        if not session:
            return None

        # Find suitable task
        for task_id, task in session.tasks.items():
            if task.status != TaskStatus.PENDING.value:
                continue

            # Check preferences
            if preferred_type and task.task_type != preferred_type:
                continue
            if max_priority and task.priority > max_priority:
                continue

            # Accept task
            success = await self.accept_task(task_id)
            if success:
                return {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "priority": task.priority,
                    "input_data": task.input_data,
                    "metadata": task.metadata
                }

        return None

    async def accept_task(self, task_id: str) -> bool:
        """
        Accept a specific task.

        Args:
            task_id: Task ID to accept

        Returns:
            True if task accepted

        Example:
            if await agent.accept_task("task-123"):
                # Process task
                result = await agent.process_task_123()
                await agent.submit_result("task-123", result)
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return False

        success = await self._coordination_manager.assign_task(
            self._current_session_id,
            task_id,
            self.agent_id
        )

        if success:
            # Start progress tracking
            await self._coordination_manager.update_task_progress(
                self._current_session_id,
                task_id,
                0.0,
                "Task accepted"
            )

            # Track locally
            session = self._coordination_manager.sessions.get(self._current_session_id)
            if session:
                task = session.tasks.get(task_id)
                if task:
                    self._assigned_tasks[task_id] = {
                        "task": task,
                        "started_at": datetime.utcnow(),
                        "progress": 0.0
                    }

        return success

    async def reject_task(self, task_id: str, reason: str = "") -> bool:
        """
        Reject a specific task.

        Args:
            task_id: Task ID to reject
            reason: Reason for rejection

        Returns:
            True if rejection recorded
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return False

        # For now, just log - could be extended to notify coordinator
        print(f"[{self.agent_id}] Rejected task {task_id}: {reason}")
        return True

    async def report_progress(
        self,
        task_id: str,
        progress: float,
        message: str = ""
    ) -> bool:
        """
        Report task progress.

        Args:
            task_id: Task ID
            progress: Progress (0.0 to 1.0)
            message: Progress message

        Returns:
            True if progress reported

        Example:
            await agent.report_progress("task-123", 0.5, "Half complete")
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return False

        success = await self._coordination_manager.update_task_progress(
            self._current_session_id,
            task_id,
            progress,
            message
        )

        if success and task_id in self._assigned_tasks:
            self._assigned_tasks[task_id]["progress"] = progress

        return success

    async def submit_result(
        self,
        task_id: str,
        result: Any,
        success: bool = True
    ) -> bool:
        """
        Submit task result.

        Args:
            task_id: Task ID
            result: Task result data
            success: Whether task succeeded

        Returns:
            True if result submitted

        Example:
            result = {"output": "analysis complete", "score": 0.95}
            await agent.submit_result("task-123", result, success=True)
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return False

        # Mark task complete
        status = TaskStatus.COMPLETED.value if success else TaskStatus.FAILED.value
        submitted = await self._coordination_manager.complete_task(
            self._current_session_id,
            task_id,
            result,
            status
        )

        if submitted:
            # Update local tracking
            if task_id in self._assigned_tasks:
                self._completed_tasks.append(task_id)
                del self._assigned_tasks[task_id]

            print(f"[{self.agent_id}] Submitted result for {task_id} ({status})")

        return submitted

    async def get_coordination_state(self) -> Dict[str, Any]:
        """
        Get agent's coordination state.

        Returns:
            Dictionary with coordination info:
            - in_session: Whether agent is in a session
            - session_id: Current session ID (if any)
            - role: Agent's role in session
            - assigned_tasks: Number of assigned tasks
            - completed_tasks: Number of completed tasks
            - coordination_enabled: Whether ACP is available
        """
        return {
            "agent_id": self.agent_id,
            "in_session": self._current_session_id is not None,
            "session_id": self._current_session_id,
            "role": self._current_role,
            "assigned_tasks": len(self._assigned_tasks),
            "completed_tasks": len(self._completed_tasks),
            "coordination_enabled": self._coordination_enabled,
        }

    async def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about current coordination session.

        Returns:
            Session info dictionary or None
        """
        if self._current_session_id is None or self._coordination_manager is None:
            return None

        session = self._coordination_manager.sessions.get(self._current_session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "coordination_type": session.coordination_type,
            "status": session.status,
            "total_tasks": len(session.tasks),
            "completed_tasks": sum(
                1 for t in session.tasks.values()
                if t.status == TaskStatus.COMPLETED.value
            ),
            "total_participants": len(session.participants),
            "my_role": self._current_role,
        }

    def is_coordinating(self) -> bool:
        """
        Check if agent is currently in a coordination session.

        Returns:
            True if in coordination session
        """
        return self._current_session_id is not None

    def get_assigned_tasks(self) -> List[str]:
        """
        Get list of currently assigned task IDs.

        Returns:
            List of task IDs
        """
        return list(self._assigned_tasks.keys())


# Convenience decorator
def coordination_capable(agent_class):
    """
    Decorator to add coordination capabilities to an agent class.

    Usage:
        @coordination_capable
        class MyAgent(BaseAgent):
            # Agent automatically has coordination methods
            pass

    Args:
        agent_class: The agent class to enhance

    Returns:
        Enhanced class with coordination capabilities
    """
    class CoordinatedAgent(CoordinationMixin, agent_class):
        pass

    CoordinatedAgent.__name__ = agent_class.__name__
    CoordinatedAgent.__module__ = agent_class.__module__

    return CoordinatedAgent


__all__ = [
    "CoordinationMixin",
    "CoordinationError",
    "coordination_capable",
]
