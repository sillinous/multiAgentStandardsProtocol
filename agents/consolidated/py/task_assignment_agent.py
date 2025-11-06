"""
Task Assignment Agent - Meta-Agent for Intelligent Work Distribution

This agent intelligently assigns tasks to other agents based on:
- Agent capabilities and specializations
- Current workload and performance
- Task requirements and priorities
- Agent availability and health

Category: Meta-Agent (Task Distribution & Load Balancing)
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import heapq

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task status"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task definition"""
    task_id: str
    task_type: str
    description: str
    requirements: Dict[str, Any]
    priority: TaskPriority
    created_at: datetime
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class AgentWorkload:
    """Agent workload tracking"""
    agent_id: str
    agent_type: str
    current_tasks: int = 0
    max_concurrent_tasks: int = 3
    total_completed: int = 0
    total_failed: int = 0
    avg_completion_time_ms: float = 0.0
    success_rate: float = 1.0
    is_available: bool = True
    last_assigned: Optional[datetime] = None


class TaskAssignmentAgent(BaseAgent):
    """
    Meta-agent that intelligently assigns tasks to other agents

    Capabilities:
    - Task queue management
    - Intelligent agent selection
    - Load balancing
    - Priority scheduling
    - Task tracking and monitoring
    """

    def __init__(
        self,
        agent_id: str = "task_assignment_001",
        workspace_path: str = "./autonomous-ecosystem/workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="task_assignment",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Task queue (priority queue)
        self.task_queue: List = []  # heapq priority queue
        self.tasks: Dict[str, Task] = {}  # task_id -> Task

        # Agent registry
        self.agents: Dict[str, AgentWorkload] = {}  # agent_id -> AgentWorkload

        # Assignment history
        self.assignment_history: List[Dict] = []

        # Dependencies (injected)
        self.activity_tracker = None
        self.agent_factory = None

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task assignment operations"""
        task_type = task.get("type")

        if task_type == "submit_task":
            return await self._submit_task(task)
        elif task_type == "assign_tasks":
            return await self._assign_pending_tasks()
        elif task_type == "get_task_status":
            return await self._get_task_status(task)
        elif task_type == "cancel_task":
            return await self._cancel_task(task)
        elif task_type == "get_queue_status":
            return await self._get_queue_status()
        elif task_type == "register_agent":
            return await self._register_agent(task)
        elif task_type == "update_agent_status":
            return await self._update_agent_status(task)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task distribution patterns and efficiency"""
        analysis_type = input_data.get("analysis_type", "overview")

        if analysis_type == "overview":
            return self._analyze_overview()
        elif analysis_type == "load_balance":
            return self._analyze_load_balance()
        elif analysis_type == "bottlenecks":
            return self._analyze_bottlenecks()
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    # =====================================================================
    # Task Submission & Management
    # =====================================================================

    async def _submit_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new task to the queue"""
        try:
            task_id = f"task_{datetime.now().timestamp()}"

            task = Task(
                task_id=task_id,
                task_type=task_data["task_type"],
                description=task_data.get("description", ""),
                requirements=task_data.get("requirements", {}),
                priority=TaskPriority(task_data.get("priority", TaskPriority.MEDIUM.value)),
                created_at=datetime.now()
            )

            # Add to queue (priority queue, higher priority first)
            heapq.heappush(self.task_queue, (-task.priority.value, task.created_at, task_id))
            self.tasks[task_id] = task

            # Try immediate assignment
            await self._assign_pending_tasks()

            return {
                "success": True,
                "task_id": task_id,
                "status": task.status.value,
                "message": "Task submitted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _assign_pending_tasks(self) -> Dict[str, Any]:
        """Assign pending tasks to available agents"""
        assigned_count = 0
        failed_count = 0

        while self.task_queue:
            # Peek at highest priority task
            priority, created_at, task_id = heapq.heappop(self.task_queue)
            task = self.tasks.get(task_id)

            if not task or task.status != TaskStatus.QUEUED:
                continue

            # Find best agent for this task
            agent_id = await self._select_best_agent(task)

            if agent_id:
                # Assign task
                success = await self._assign_task_to_agent(task, agent_id)
                if success:
                    assigned_count += 1
                else:
                    # Put back in queue
                    heapq.heappush(self.task_queue, (priority, created_at, task_id))
                    failed_count += 1
                    break  # Stop trying if assignment failed
            else:
                # No available agent, put back in queue
                heapq.heappush(self.task_queue, (priority, created_at, task_id))
                break

        return {
            "success": True,
            "assigned": assigned_count,
            "failed": failed_count,
            "remaining_in_queue": len(self.task_queue)
        }

    async def _select_best_agent(self, task: Task) -> Optional[str]:
        """Select the best agent for a task using intelligent scoring"""
        if not self.agents:
            return None

        # Filter available agents
        available_agents = [
            (agent_id, workload)
            for agent_id, workload in self.agents.items()
            if workload.is_available and workload.current_tasks < workload.max_concurrent_tasks
        ]

        if not available_agents:
            return None

        # Score each agent
        scored_agents = []
        for agent_id, workload in available_agents:
            score = self._calculate_agent_score(workload, task)
            scored_agents.append((score, agent_id))

        if not scored_agents:
            return None

        # Select highest scoring agent
        scored_agents.sort(reverse=True)
        return scored_agents[0][1]

    def _calculate_agent_score(self, workload: AgentWorkload, task: Task) -> float:
        """Calculate fitness score for agent-task pair"""
        score = 0.0

        # Factor 1: Specialization match (if agent type matches task type)
        if workload.agent_type == task.task_type:
            score += 50.0

        # Factor 2: Success rate (0-100 scale)
        score += workload.success_rate * 30.0

        # Factor 3: Current load (inverse, more available = higher score)
        load_factor = 1.0 - (workload.current_tasks / workload.max_concurrent_tasks)
        score += load_factor * 15.0

        # Factor 4: Performance (faster = better)
        if workload.avg_completion_time_ms > 0:
            # Normalize to 0-5 scale (5000ms = baseline)
            perf_factor = max(0, 5.0 - (workload.avg_completion_time_ms / 1000))
            score += perf_factor

        return score

    async def _assign_task_to_agent(self, task: Task, agent_id: str) -> bool:
        """Assign a specific task to an agent"""
        try:
            # Update task
            task.assigned_to = agent_id
            task.assigned_at = datetime.now()
            task.status = TaskStatus.ASSIGNED

            # Update agent workload
            workload = self.agents[agent_id]
            workload.current_tasks += 1
            workload.last_assigned = datetime.now()

            # Record assignment
            self.assignment_history.append({
                "task_id": task.task_id,
                "agent_id": agent_id,
                "assigned_at": task.assigned_at.isoformat(),
                "priority": task.priority.value
            })

            # Log activity
            if self.activity_tracker:
                await self.activity_tracker._log_activity({
                    "agent_id": agent_id,
                    "agent_type": workload.agent_type,
                    "activity_type": "task_assigned",
                    "description": f"Assigned task: {task.description}",
                    "details": {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "priority": task.priority.value
                    }
                })

            return True

        except Exception as e:
            print(f"Error assigning task: {e}")
            return False

    async def _get_task_status(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific task"""
        task_id = task_data.get("task_id")
        if not task_id:
            return {"success": False, "error": "task_id required"}

        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        return {
            "success": True,
            "task": {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result,
                "error": task.error
            }
        }

    async def _cancel_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a task"""
        task_id = task_data.get("task_id")
        if not task_id:
            return {"success": False, "error": "task_id required"}

        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return {"success": False, "error": f"Task already {task.status.value}"}

        # Update task status
        task.status = TaskStatus.CANCELLED

        # If assigned, free up agent
        if task.assigned_to and task.assigned_to in self.agents:
            self.agents[task.assigned_to].current_tasks -= 1

        return {
            "success": True,
            "message": f"Task {task_id} cancelled"
        }

    async def _get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        status_counts = {
            "queued": 0,
            "assigned": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }

        for task in self.tasks.values():
            status_counts[task.status.value] += 1

        return {
            "success": True,
            "queue_length": len(self.task_queue),
            "total_tasks": len(self.tasks),
            "status_breakdown": status_counts,
            "available_agents": sum(
                1 for a in self.agents.values()
                if a.is_available and a.current_tasks < a.max_concurrent_tasks
            ),
            "total_agents": len(self.agents)
        }

    # =====================================================================
    # Agent Registry Management
    # =====================================================================

    async def _register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent with the task assignment system"""
        agent_id = agent_data.get("agent_id")
        if not agent_id:
            return {"success": False, "error": "agent_id required"}

        workload = AgentWorkload(
            agent_id=agent_id,
            agent_type=agent_data.get("agent_type", "unknown"),
            max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 3)
        )

        self.agents[agent_id] = workload

        return {
            "success": True,
            "message": f"Agent {agent_id} registered"
        }

    async def _update_agent_status(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent availability or workload"""
        agent_id = agent_data.get("agent_id")
        if not agent_id or agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        workload = self.agents[agent_id]

        # Update fields
        if "is_available" in agent_data:
            workload.is_available = agent_data["is_available"]

        if "current_tasks" in agent_data:
            workload.current_tasks = agent_data["current_tasks"]

        if "task_completed" in agent_data:
            workload.total_completed += 1
            workload.current_tasks = max(0, workload.current_tasks - 1)

            # Update success rate
            total = workload.total_completed + workload.total_failed
            workload.success_rate = workload.total_completed / total if total > 0 else 1.0

        if "task_failed" in agent_data:
            workload.total_failed += 1
            workload.current_tasks = max(0, workload.current_tasks - 1)

            # Update success rate
            total = workload.total_completed + workload.total_failed
            workload.success_rate = workload.total_completed / total if total > 0 else 1.0

        return {
            "success": True,
            "agent": asdict(workload)
        }

    # =====================================================================
    # Analysis
    # =====================================================================

    def _analyze_overview(self) -> Dict[str, Any]:
        """Overview of task distribution"""
        return {
            "total_tasks": len(self.tasks),
            "queued_tasks": len(self.task_queue),
            "total_agents": len(self.agents),
            "available_agents": sum(
                1 for a in self.agents.values()
                if a.is_available and a.current_tasks < a.max_concurrent_tasks
            ),
            "total_assignments": len(self.assignment_history),
            "avg_queue_time_seconds": self._calculate_avg_queue_time()
        }

    def _analyze_load_balance(self) -> Dict[str, Any]:
        """Analyze load distribution across agents"""
        if not self.agents:
            return {"balanced": True, "agents": []}

        agent_loads = [
            {
                "agent_id": agent_id,
                "current_load": workload.current_tasks,
                "max_capacity": workload.max_concurrent_tasks,
                "utilization": (workload.current_tasks / workload.max_concurrent_tasks) * 100
            }
            for agent_id, workload in self.agents.items()
        ]

        # Calculate variance in utilization
        utilizations = [a["utilization"] for a in agent_loads]
        avg_util = sum(utilizations) / len(utilizations)
        variance = sum((u - avg_util) ** 2 for u in utilizations) / len(utilizations)

        return {
            "balanced": variance < 20,  # Variance threshold
            "avg_utilization": round(avg_util, 2),
            "variance": round(variance, 2),
            "agents": agent_loads
        }

    def _analyze_bottlenecks(self) -> Dict[str, Any]:
        """Identify bottlenecks in task processing"""
        bottlenecks = []

        # Check for overloaded agents
        for agent_id, workload in self.agents.items():
            if workload.current_tasks >= workload.max_concurrent_tasks:
                bottlenecks.append({
                    "type": "overloaded_agent",
                    "agent_id": agent_id,
                    "current_tasks": workload.current_tasks
                })

        # Check for long queue
        if len(self.task_queue) > 10:
            bottlenecks.append({
                "type": "long_queue",
                "queue_length": len(self.task_queue)
            })

        # Check for low availability
        available = sum(
            1 for a in self.agents.values()
            if a.is_available and a.current_tasks < a.max_concurrent_tasks
        )
        if available == 0 and len(self.task_queue) > 0:
            bottlenecks.append({
                "type": "no_available_agents",
                "queued_tasks": len(self.task_queue)
            })

        return {
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": bottlenecks
        }

    def _calculate_avg_queue_time(self) -> float:
        """Calculate average time tasks spend in queue"""
        completed_tasks = [
            t for t in self.tasks.values()
            if t.assigned_at and t.created_at
        ]

        if not completed_tasks:
            return 0.0

        total_queue_time = sum(
            (t.assigned_at - t.created_at).total_seconds()
            for t in completed_tasks
        )

        return total_queue_time / len(completed_tasks)

    # =====================================================================
    # Dependency Injection
    # =====================================================================

    def set_activity_tracker(self, tracker):
        """Inject activity tracker"""
        self.activity_tracker = tracker

    def set_agent_factory(self, factory):
        """Inject agent factory"""
        self.agent_factory = factory


# Singleton instance
_task_assignment_agent = None

def get_task_assignment_agent() -> TaskAssignmentAgent:
    """Get or create task assignment agent instance"""
    global _task_assignment_agent
    if _task_assignment_agent is None:
        _task_assignment_agent = TaskAssignmentAgent()
    return _task_assignment_agent


if __name__ == "__main__":
    # Demo the task assignment agent
    import asyncio

    async def demo():
        assigner = get_task_assignment_agent()

        # Register some agents
        await assigner._register_agent({
            "agent_id": "agent_001",
            "agent_type": "demand_predictor",
            "max_concurrent_tasks": 3
        })

        await assigner._register_agent({
            "agent_id": "agent_002",
            "agent_type": "traffic_analyzer",
            "max_concurrent_tasks": 2
        })

        # Submit tasks
        task1 = await assigner._submit_task({
            "task_type": "demand_predictor",
            "description": "Predict demand hotspots",
            "priority": TaskPriority.HIGH.value
        })
        print("\n[Task Submitted]")
        print(json.dumps(task1, indent=2))

        # Get queue status
        status = await assigner._get_queue_status()
        print("\n[Queue Status]")
        print(json.dumps(status, indent=2))

        # Analyze load balance
        balance = assigner._analyze_load_balance()
        print("\n[Load Balance Analysis]")
        print(json.dumps(balance, indent=2))

    asyncio.run(demo())
