"""
🤝 Agent Coordination Protocol (ACP) v1.0 - PRODUCTION IMPLEMENTATION
======================================================================

Complete implementation of ACP for multi-agent task coordination and orchestration.

Features:
- Coordination session management
- Multiple coordination patterns (swarm, pipeline, hierarchical, consensus)
- Task assignment and tracking
- Progress monitoring
- State synchronization
- Participant lifecycle
- Event notifications

Author: SuperStandard Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class CoordinationType(Enum):
    """Types of coordination patterns"""

    SWARM = "swarm"  # All agents work independently on same goal
    PIPELINE = "pipeline"  # Sequential processing through agents
    HIERARCHICAL = "hierarchical"  # Coordinator delegates to subordinates
    CONSENSUS = "consensus"  # Agents vote/agree on actions
    AUCTION = "auction"  # Agents bid for tasks
    COLLABORATIVE = "collaborative"  # Agents work together closely


class CoordinationStatus(Enum):
    """Status of coordination session"""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Status of individual tasks"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Individual task in coordination"""

    task_id: str
    task_type: str
    description: str
    assigned_to: Optional[str] = None
    status: str = TaskStatus.PENDING.value
    priority: int = 5  # 1-10, higher = more important
    dependencies: List[str] = field(default_factory=list)  # Other task IDs
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Participant:
    """Agent participating in coordination"""

    agent_id: str
    agent_type: str
    capabilities: List[str]
    role: str = "participant"  # coordinator, participant, observer
    status: str = "active"  # active, idle, busy, offline
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    assigned_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ACPCoordination:
    """Agent Coordination Protocol session"""

    protocol: str = "ACP"
    version: str = "1.0.0"
    coordination_id: str = field(default_factory=lambda: f"coord_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    coordinator_id: str = ""
    coordination_type: str = CoordinationType.SWARM.value
    status: str = CoordinationStatus.INITIALIZING.value
    goal: str = ""
    participants: Dict[str, Participant] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    coordination_plan: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class CoordinationMessage:
    """Message within coordination session"""

    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    coordination_id: str = ""
    from_agent: str = ""
    message_type: str = ""  # join, leave, task_update, state_sync, query, response
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# COORDINATION MANAGER
# ============================================================================


class CoordinationManager:
    """
    Manager for agent coordination sessions.

    Handles:
    - Coordination lifecycle (create, start, pause, complete)
    - Participant management (join, leave, assign)
    - Task management (create, assign, track, complete)
    - State synchronization across agents
    - Progress monitoring
    """

    def __init__(self):
        """Initialize the coordination manager"""
        # Storage
        self.coordinations: Dict[str, ACPCoordination] = {}
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Statistics
        self.stats = {
            "total_coordinations": 0,
            "active_coordinations": 0,
            "total_participants": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
        }

    # ========================================================================
    # COORDINATION LIFECYCLE
    # ========================================================================

    async def create_coordination(
        self,
        coordinator_id: str,
        coordination_type: str,
        goal: str,
        coordination_plan: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new coordination session.

        Args:
            coordinator_id: Agent creating the coordination
            coordination_type: Type of coordination pattern
            goal: What this coordination aims to achieve
            coordination_plan: Optional plan/strategy
            metadata: Additional metadata

        Returns:
            Coordination creation result
        """
        try:
            coordination = ACPCoordination(
                coordinator_id=coordinator_id,
                coordination_type=coordination_type,
                goal=goal,
                coordination_plan=coordination_plan or {},
                metadata=metadata or {},
            )

            # Add coordinator as first participant
            coordinator = Participant(
                agent_id=coordinator_id,
                agent_type="coordinator",
                capabilities=[],
                role="coordinator",
            )
            coordination.participants[coordinator_id] = coordinator

            # Store coordination
            self.coordinations[coordination.coordination_id] = coordination
            self.stats["total_coordinations"] += 1
            self.stats["active_coordinations"] += 1

            # Emit event
            await self._emit_event("coordination_created", coordination)

            logger.info(
                f"[+] Coordination created: {coordination.coordination_id} ({coordination_type})"
            )

            return {
                "success": True,
                "coordination_id": coordination.coordination_id,
                "coordination": asdict(coordination),
            }

        except Exception as e:
            logger.error(f"[!] Failed to create coordination: {e}")
            return {"success": False, "error": str(e)}

    async def start_coordination(self, coordination_id: str) -> Dict[str, Any]:
        """Start/activate a coordination session"""
        if coordination_id not in self.coordinations:
            return {"success": False, "error": "Coordination not found"}

        coordination = self.coordinations[coordination_id]
        coordination.status = CoordinationStatus.ACTIVE.value

        await self._emit_event("coordination_started", coordination)
        logger.info(f"[*] Coordination started: {coordination_id}")

        return {"success": True, "coordination_id": coordination_id}

    async def pause_coordination(self, coordination_id: str) -> Dict[str, Any]:
        """Pause a coordination session"""
        if coordination_id not in self.coordinations:
            return {"success": False, "error": "Coordination not found"}

        coordination = self.coordinations[coordination_id]
        coordination.status = CoordinationStatus.PAUSED.value

        await self._emit_event("coordination_paused", coordination)
        logger.info(f"[*] Coordination paused: {coordination_id}")

        return {"success": True, "coordination_id": coordination_id}

    async def complete_coordination(self, coordination_id: str) -> Dict[str, Any]:
        """Complete a coordination session"""
        if coordination_id not in self.coordinations:
            return {"success": False, "error": "Coordination not found"}

        coordination = self.coordinations[coordination_id]
        coordination.status = CoordinationStatus.COMPLETED.value
        coordination.completed_at = datetime.utcnow().isoformat()

        self.stats["active_coordinations"] = max(0, self.stats["active_coordinations"] - 1)

        await self._emit_event("coordination_completed", coordination)
        logger.info(f"[+] Coordination completed: {coordination_id}")

        return {
            "success": True,
            "coordination_id": coordination_id,
            "summary": await self._get_coordination_summary(coordination),
        }

    # ========================================================================
    # PARTICIPANT MANAGEMENT
    # ========================================================================

    async def join_coordination(
        self,
        coordination_id: str,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        role: str = "participant",
    ) -> Dict[str, Any]:
        """Agent joins a coordination session"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]

            # Check if already joined
            if agent_id in coordination.participants:
                return {"success": False, "error": "Agent already in coordination"}

            # Create participant
            participant = Participant(
                agent_id=agent_id, agent_type=agent_type, capabilities=capabilities, role=role
            )

            coordination.participants[agent_id] = participant
            self.stats["total_participants"] += 1

            await self._emit_event(
                "participant_joined",
                {"coordination_id": coordination_id, "participant": participant},
            )

            logger.info(f"[+] Agent {agent_id} joined coordination {coordination_id}")

            return {
                "success": True,
                "coordination_id": coordination_id,
                "participant": asdict(participant),
            }

        except Exception as e:
            logger.error(f"[!] Failed to join coordination: {e}")
            return {"success": False, "error": str(e)}

    async def leave_coordination(self, coordination_id: str, agent_id: str) -> Dict[str, Any]:
        """Agent leaves a coordination session"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]

            if agent_id not in coordination.participants:
                return {"success": False, "error": "Agent not in coordination"}

            # Remove participant
            participant = coordination.participants.pop(agent_id)

            # Reassign their tasks
            for task_id in participant.assigned_tasks:
                if task_id in coordination.tasks:
                    coordination.tasks[task_id].assigned_to = None
                    coordination.tasks[task_id].status = TaskStatus.PENDING.value

            await self._emit_event(
                "participant_left", {"coordination_id": coordination_id, "agent_id": agent_id}
            )

            logger.info(f"[-] Agent {agent_id} left coordination {coordination_id}")

            return {"success": True, "coordination_id": coordination_id}

        except Exception as e:
            logger.error(f"[!] Failed to leave coordination: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # TASK MANAGEMENT
    # ========================================================================

    async def create_task(
        self,
        coordination_id: str,
        task_type: str,
        description: str,
        priority: int = 5,
        dependencies: Optional[List[str]] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a task in coordination"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]

            task = Task(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                task_type=task_type,
                description=description,
                priority=priority,
                dependencies=dependencies or [],
                input_data=input_data or {},
            )

            coordination.tasks[task.task_id] = task
            self.stats["total_tasks"] += 1

            await self._emit_event(
                "task_created", {"coordination_id": coordination_id, "task": task}
            )

            logger.info(f"[+] Task created: {task.task_id} in {coordination_id}")

            return {"success": True, "task_id": task.task_id, "task": asdict(task)}

        except Exception as e:
            logger.error(f"[!] Failed to create task: {e}")
            return {"success": False, "error": str(e)}

    async def assign_task(
        self, coordination_id: str, task_id: str, agent_id: str
    ) -> Dict[str, Any]:
        """Assign task to an agent"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]

            if task_id not in coordination.tasks:
                return {"success": False, "error": "Task not found"}

            if agent_id not in coordination.participants:
                return {"success": False, "error": "Agent not in coordination"}

            task = coordination.tasks[task_id]
            participant = coordination.participants[agent_id]

            # Assign task
            task.assigned_to = agent_id
            task.status = TaskStatus.ASSIGNED.value
            participant.assigned_tasks.append(task_id)

            await self._emit_event(
                "task_assigned",
                {"coordination_id": coordination_id, "task_id": task_id, "agent_id": agent_id},
            )

            logger.info(f"[*] Task {task_id} assigned to {agent_id}")

            return {"success": True, "task_id": task_id, "agent_id": agent_id}

        except Exception as e:
            logger.error(f"[!] Failed to assign task: {e}")
            return {"success": False, "error": str(e)}

    async def update_task_status(
        self,
        coordination_id: str,
        task_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update task status and optionally add output"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]

            if task_id not in coordination.tasks:
                return {"success": False, "error": "Task not found"}

            task = coordination.tasks[task_id]
            old_status = task.status
            task.status = status

            if status == TaskStatus.IN_PROGRESS.value and not task.started_at:
                task.started_at = datetime.utcnow().isoformat()

            if status == TaskStatus.COMPLETED.value:
                task.completed_at = datetime.utcnow().isoformat()
                if output_data:
                    task.output_data.update(output_data)

                # Update participant stats
                if task.assigned_to and task.assigned_to in coordination.participants:
                    participant = coordination.participants[task.assigned_to]
                    if task_id in participant.assigned_tasks:
                        participant.assigned_tasks.remove(task_id)
                    participant.completed_tasks.append(task_id)

                self.stats["completed_tasks"] += 1

            await self._emit_event(
                "task_status_changed",
                {
                    "coordination_id": coordination_id,
                    "task_id": task_id,
                    "old_status": old_status,
                    "new_status": status,
                },
            )

            logger.info(f"[*] Task {task_id} status: {old_status} -> {status}")

            return {"success": True, "task_id": task_id, "status": status}

        except Exception as e:
            logger.error(f"[!] Failed to update task: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # STATE SYNCHRONIZATION
    # ========================================================================

    async def update_shared_state(
        self, coordination_id: str, agent_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update shared state across coordination"""
        try:
            if coordination_id not in self.coordinations:
                return {"success": False, "error": "Coordination not found"}

            coordination = self.coordinations[coordination_id]
            coordination.shared_state.update(updates)

            await self._emit_event(
                "state_updated",
                {"coordination_id": coordination_id, "agent_id": agent_id, "updates": updates},
            )

            return {"success": True, "shared_state": coordination.shared_state}

        except Exception as e:
            logger.error(f"[!] Failed to update state: {e}")
            return {"success": False, "error": str(e)}

    async def get_shared_state(self, coordination_id: str) -> Dict[str, Any]:
        """Get current shared state"""
        if coordination_id not in self.coordinations:
            return {}
        return self.coordinations[coordination_id].shared_state.copy()

    # ========================================================================
    # QUERIES & MONITORING
    # ========================================================================

    async def get_coordination(self, coordination_id: str) -> Optional[Dict[str, Any]]:
        """Get coordination details"""
        if coordination_id in self.coordinations:
            return asdict(self.coordinations[coordination_id])
        return None

    async def list_coordinations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all coordinations, optionally filtered by status"""
        coordinations = []
        for coord in self.coordinations.values():
            if status is None or coord.status == status:
                coordinations.append(asdict(coord))
        return coordinations

    async def get_available_tasks(self, coordination_id: str) -> List[Dict[str, Any]]:
        """Get tasks that are pending/available"""
        if coordination_id not in self.coordinations:
            return []

        coordination = self.coordinations[coordination_id]
        available_tasks = []

        for task in coordination.tasks.values():
            if task.status == TaskStatus.PENDING.value:
                # Check if dependencies are met
                dependencies_met = True
                for dep_id in task.dependencies:
                    if dep_id in coordination.tasks:
                        dep_task = coordination.tasks[dep_id]
                        if dep_task.status != TaskStatus.COMPLETED.value:
                            dependencies_met = False
                            break

                if dependencies_met:
                    available_tasks.append(asdict(task))

        # Sort by priority (higher first)
        available_tasks.sort(key=lambda t: t["priority"], reverse=True)
        return available_tasks

    async def get_progress(self, coordination_id: str) -> Dict[str, Any]:
        """Get coordination progress"""
        if coordination_id not in self.coordinations:
            return {}

        coordination = self.coordinations[coordination_id]

        total_tasks = len(coordination.tasks)
        if total_tasks == 0:
            return {"total_tasks": 0, "completed_tasks": 0, "progress_percentage": 0.0}

        completed = sum(
            1 for task in coordination.tasks.values() if task.status == TaskStatus.COMPLETED.value
        )
        in_progress = sum(
            1 for task in coordination.tasks.values() if task.status == TaskStatus.IN_PROGRESS.value
        )
        pending = sum(
            1 for task in coordination.tasks.values() if task.status == TaskStatus.PENDING.value
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "progress_percentage": (completed / total_tasks) * 100 if total_tasks > 0 else 0,
            "participants": len(coordination.participants),
        }

    # ========================================================================
    # EVENT SYSTEM
    # ========================================================================

    def on_event(self, event_name: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_name].append(handler)

    async def _emit_event(self, event_name: str, data: Any):
        """Emit event to registered handlers"""
        for handler in self.event_handlers.get(event_name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"[!] Event handler error ({event_name}): {e}")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def _get_coordination_summary(self, coordination: ACPCoordination) -> Dict[str, Any]:
        """Generate coordination summary"""
        total_tasks = len(coordination.tasks)
        completed_tasks = sum(
            1 for t in coordination.tasks.values() if t.status == TaskStatus.COMPLETED.value
        )

        return {
            "coordination_id": coordination.coordination_id,
            "goal": coordination.goal,
            "type": coordination.coordination_type,
            "participants": len(coordination.participants),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "duration": self._calculate_duration(
                coordination.created_at, coordination.completed_at
            ),
        }

    def _calculate_duration(self, start: str, end: Optional[str]) -> float:
        """Calculate duration in seconds"""
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end) if end else datetime.utcnow()
        return (end_time - start_time).total_seconds()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            "stats": self.stats,
            "active_coordinations": [
                coord.coordination_id
                for coord in self.coordinations.values()
                if coord.status == CoordinationStatus.ACTIVE.value
            ],
        }


# ============================================================================
# ACP CLIENT
# ============================================================================


class ACPClient:
    """
    Client for interacting with ACP coordination manager.

    Use this in your agents to participate in coordinations.
    """

    def __init__(self, manager: CoordinationManager, agent_id: str):
        """Initialize client"""
        self.manager = manager
        self.agent_id = agent_id

    async def create_coordination(
        self, coordination_type: str, goal: str, plan: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new coordination (as coordinator)"""
        result = await self.manager.create_coordination(
            self.agent_id, coordination_type, goal, plan
        )
        return result.get("coordination_id", "")

    async def join(self, coordination_id: str, agent_type: str, capabilities: List[str]) -> bool:
        """Join existing coordination"""
        result = await self.manager.join_coordination(
            coordination_id, self.agent_id, agent_type, capabilities
        )
        return result.get("success", False)

    async def leave(self, coordination_id: str) -> bool:
        """Leave coordination"""
        result = await self.manager.leave_coordination(coordination_id, self.agent_id)
        return result.get("success", False)

    async def create_task(
        self, coordination_id: str, task_type: str, description: str, priority: int = 5
    ) -> str:
        """Create task in coordination"""
        result = await self.manager.create_task(coordination_id, task_type, description, priority)
        return result.get("task_id", "")

    async def get_available_tasks(self, coordination_id: str) -> List[Dict[str, Any]]:
        """Get available tasks"""
        return await self.manager.get_available_tasks(coordination_id)

    async def claim_task(self, coordination_id: str, task_id: str) -> bool:
        """Claim/assign task to self"""
        result = await self.manager.assign_task(coordination_id, task_id, self.agent_id)
        return result.get("success", False)

    async def update_task(
        self,
        coordination_id: str,
        task_id: str,
        status: str,
        output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update task status"""
        result = await self.manager.update_task_status(coordination_id, task_id, status, output)
        return result.get("success", False)

    async def update_state(self, coordination_id: str, updates: Dict[str, Any]) -> bool:
        """Update shared state"""
        result = await self.manager.update_shared_state(coordination_id, self.agent_id, updates)
        return result.get("success", False)

    async def get_progress(self, coordination_id: str) -> Dict[str, Any]:
        """Get coordination progress"""
        return await self.manager.get_progress(coordination_id)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def example_usage():
    """Demonstrate ACP usage"""

    print("ACP v1.0 - Agent Coordination Protocol Example\n")

    # Create manager
    manager = CoordinationManager()

    # Create clients for different agents
    coordinator_client = ACPClient(manager, "agent-coordinator")
    worker1_client = ACPClient(manager, "agent-worker-1")
    worker2_client = ACPClient(manager, "agent-worker-2")

    # Create coordination
    print("[*] Creating coordination session...")
    coord_id = await coordinator_client.create_coordination(
        coordination_type=CoordinationType.SWARM.value,
        goal="Process and analyze dataset",
        plan={"strategy": "divide_and_conquer"},
    )
    print(f"[+] Coordination created: {coord_id}\n")

    # Start coordination
    await manager.start_coordination(coord_id)

    # Workers join
    print("[*] Workers joining...")
    await worker1_client.join(coord_id, "analyzer", ["data-processing", "analysis"])
    await worker2_client.join(coord_id, "analyzer", ["data-processing", "validation"])
    print("[+] 2 workers joined\n")

    # Create tasks
    print("[*] Creating tasks...")
    task1_id = await coordinator_client.create_task(
        coord_id, "data_processing", "Process dataset chunk 1", priority=8
    )
    task2_id = await coordinator_client.create_task(
        coord_id, "data_processing", "Process dataset chunk 2", priority=7
    )
    task3_id = await coordinator_client.create_task(
        coord_id, "analysis", "Analyze results", priority=6
    )
    print(f"[+] 3 tasks created\n")

    # Workers claim tasks
    print("[*] Workers claiming tasks...")
    await worker1_client.claim_task(coord_id, task1_id)
    await worker2_client.claim_task(coord_id, task2_id)
    print("[+] Tasks assigned\n")

    # Simulate work
    print("[*] Workers processing tasks...")
    await worker1_client.update_task(coord_id, task1_id, TaskStatus.IN_PROGRESS.value)
    await asyncio.sleep(0.1)
    await worker1_client.update_task(
        coord_id, task1_id, TaskStatus.COMPLETED.value, output={"result": "chunk1_processed"}
    )

    await worker2_client.update_task(coord_id, task2_id, TaskStatus.IN_PROGRESS.value)
    await asyncio.sleep(0.1)
    await worker2_client.update_task(
        coord_id, task2_id, TaskStatus.COMPLETED.value, output={"result": "chunk2_processed"}
    )
    print("[+] Tasks completed\n")

    # Check progress
    print("[*] Progress Report:")
    progress = await coordinator_client.get_progress(coord_id)
    print(f"  Total tasks: {progress['total_tasks']}")
    print(f"  Completed: {progress['completed_tasks']}")
    print(f"  In progress: {progress['in_progress_tasks']}")
    print(f"  Pending: {progress['pending_tasks']}")
    print(f"  Progress: {progress['progress_percentage']:.1f}%")
    print(f"  Participants: {progress['participants']}\n")

    # Update shared state
    print("[*] Updating shared state...")
    await worker1_client.update_state(coord_id, {"chunks_processed": 2})
    state = await manager.get_shared_state(coord_id)
    print(f"  Shared state: {state}\n")

    # Complete coordination
    print("[*] Completing coordination...")
    result = await manager.complete_coordination(coord_id)
    print(f"[+] Coordination completed!")
    print(f"  Summary: {result['summary']}\n")

    # Statistics
    stats = await manager.get_statistics()
    print("[*] Manager Statistics:")
    print(f"  Total coordinations: {stats['stats']['total_coordinations']}")
    print(f"  Total tasks: {stats['stats']['total_tasks']}")
    print(f"  Completed tasks: {stats['stats']['completed_tasks']}")


if __name__ == "__main__":
    asyncio.run(example_usage())
