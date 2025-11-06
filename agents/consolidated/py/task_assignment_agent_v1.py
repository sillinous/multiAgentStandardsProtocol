"""
Task Assignment Agent v1.0 - Architecturally Compliant
=========================================================

Meta-Agent for Intelligent Work Distribution

This agent intelligently assigns tasks to other agents based on:
- Agent capabilities and specializations
- Current workload and performance
- Task requirements and priorities
- Agent availability and health

**Architectural Compliance:**
- Follows 8 architectural principles
- Supports 5 protocols (A2A, A2P, ACP, ANP, MCP)
- Environment-based configuration (12-factor)
- Standardized lifecycle management
- Resource monitoring and metrics

**Version:** 1.0
**Category:** Meta-Agent (Orchestration & Load Balancing)
**Protocols:** A2A, A2P, ACP, ANP, MCP
"""

import asyncio
import json
import os
import time
import heapq
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


# =========================================================================
# Constants
# =========================================================================

AGENT_TYPE = "task_assignment"
VERSION = "1.0"

DEFAULT_MAX_CONCURRENT_TASKS = 3
DEFAULT_QUEUE_SIZE_WARNING = 10
DEFAULT_SPECIALIZATION_BONUS = 50.0
DEFAULT_SUCCESS_RATE_WEIGHT = 30.0
DEFAULT_LOAD_WEIGHT = 15.0
DEFAULT_PERFORMANCE_WEIGHT = 5.0


# =========================================================================
# Domain Models
# =========================================================================

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
    """Task definition with full lifecycle tracking"""
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "requirements": self.requirements,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


@dataclass
class AgentWorkload:
    """Agent workload tracking and performance metrics"""
    agent_id: str
    agent_type: str
    current_tasks: int = 0
    max_concurrent_tasks: int = DEFAULT_MAX_CONCURRENT_TASKS
    total_completed: int = 0
    total_failed: int = 0
    avg_completion_time_ms: float = 0.0
    success_rate: float = 1.0
    is_available: bool = True
    last_assigned: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "current_tasks": self.current_tasks,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "avg_completion_time_ms": self.avg_completion_time_ms,
            "success_rate": self.success_rate,
            "is_available": self.is_available,
            "last_assigned": self.last_assigned.isoformat() if self.last_assigned else None
        }


# =========================================================================
# Configuration
# =========================================================================

@dataclass
class TaskAssignmentAgentConfig:
    """
    Configuration for Task Assignment Agent

    All values can be overridden via environment variables following
    12-factor app methodology.
    """
    # Queue management
    max_concurrent_tasks_per_agent: int = DEFAULT_MAX_CONCURRENT_TASKS
    queue_size_warning_threshold: int = DEFAULT_QUEUE_SIZE_WARNING

    # Scoring weights
    specialization_bonus: float = DEFAULT_SPECIALIZATION_BONUS
    success_rate_weight: float = DEFAULT_SUCCESS_RATE_WEIGHT
    load_weight: float = DEFAULT_LOAD_WEIGHT
    performance_weight: float = DEFAULT_PERFORMANCE_WEIGHT

    # Load balancing
    variance_threshold: float = 20.0

    # Resource limits
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 80.0

    @classmethod
    def from_environment(cls) -> "TaskAssignmentAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            max_concurrent_tasks_per_agent=int(os.getenv(
                "TASK_ASSIGN_MAX_CONCURRENT",
                str(DEFAULT_MAX_CONCURRENT_TASKS)
            )),
            queue_size_warning_threshold=int(os.getenv(
                "TASK_ASSIGN_QUEUE_WARNING",
                str(DEFAULT_QUEUE_SIZE_WARNING)
            )),
            specialization_bonus=float(os.getenv(
                "TASK_ASSIGN_SPECIALIZATION_BONUS",
                str(DEFAULT_SPECIALIZATION_BONUS)
            )),
            success_rate_weight=float(os.getenv(
                "TASK_ASSIGN_SUCCESS_WEIGHT",
                str(DEFAULT_SUCCESS_RATE_WEIGHT)
            )),
            load_weight=float(os.getenv(
                "TASK_ASSIGN_LOAD_WEIGHT",
                str(DEFAULT_LOAD_WEIGHT)
            )),
            performance_weight=float(os.getenv(
                "TASK_ASSIGN_PERF_WEIGHT",
                str(DEFAULT_PERFORMANCE_WEIGHT)
            )),
            variance_threshold=float(os.getenv(
                "TASK_ASSIGN_VARIANCE_THRESHOLD",
                "20.0"
            )),
            memory_limit_mb=int(os.getenv("TASK_ASSIGN_MEMORY_LIMIT_MB", "512")),
            cpu_limit_percent=float(os.getenv("TASK_ASSIGN_CPU_LIMIT_PERCENT", "80.0"))
        )


# =========================================================================
# Task Assignment Agent
# =========================================================================

class TaskAssignmentAgent(BaseAgent, ProtocolMixin):
    """
    Meta-agent for intelligent task distribution and load balancing

    **Capabilities:**
    - Priority-based task queue management
    - Intelligent agent selection using multi-factor scoring
    - Load balancing across agent pool
    - Performance tracking and analysis
    - Bottleneck detection

    **Architectural Standards:**
    - Inherits from BaseAgent + ProtocolMixin
    - Environment-based configuration
    - Resource monitoring
    - Full lifecycle management
    - Protocol support (A2A, A2P, ACP, ANP, MCP)
    """

    def __init__(
        self,
        agent_id: str,
        config: TaskAssignmentAgentConfig,
        activity_tracker=None,
        agent_factory=None
    ):
        """Initialize Task Assignment Agent"""
        # Initialize both parent classes
        super(BaseAgent, self).__init__()
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = VERSION
        ProtocolMixin.__init__(self)

        # Store typed config
        self.typed_config = config

        # Task queue (priority queue: [-priority, timestamp, task_id])
        self.task_queue: List[Tuple[int, datetime, str]] = []

        # Task storage
        self.tasks: Dict[str, Task] = {}

        # Agent registry
        self.agents: Dict[str, AgentWorkload] = {}

        # Assignment history
        self.assignment_history: List[Dict[str, Any]] = []

        # Dependencies (injected)
        self.activity_tracker = activity_tracker
        self.agent_factory = agent_factory

        # State tracking
        self.state = {
            "initialized": False,
            "total_tasks_processed": 0,
            "total_assignments_made": 0
        }

        # Metrics
        self.metrics = {
            "tasks_submitted": 0,
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "agents_registered": 0,
            "avg_queue_time_ms": 0.0,
            "avg_assignment_time_ms": 0.0
        }

        # Resource tracking
        self.process = psutil.Process()

    # =====================================================================
    # Abstract Method Implementations (Required by BaseAgent)
    # =====================================================================

    async def _configure_data_sources(self):
        """Configure data sources - not required for task assignment"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - task assignment uses internal state only"""
        return {}

    async def _execute_logic(
        self,
        input_data: Dict[str, Any],
        fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core execution logic - delegates to execute() method"""
        return await self.execute(input_data)

    # =====================================================================
    # Lifecycle Methods
    # =====================================================================

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the agent"""
        try:
            start_time = time.time()

            # Protocol support is provided by ProtocolMixin base class
            # No manual protocol enabling needed

            self.state["initialized"] = True

            init_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "version": self.version,
                "initialization_time_ms": round(init_time_ms, 2)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Initialization failed: {str(e)}"
            }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task assignment operations

        Supported operations:
        - submit_task: Submit a new task to the queue
        - assign_tasks: Assign pending tasks to agents
        - get_task_status: Get status of a specific task
        - cancel_task: Cancel a task
        - get_queue_status: Get current queue status
        - register_agent: Register an agent with the system
        - update_agent_status: Update agent workload/availability
        - analyze: Perform analysis (overview, load_balance, bottlenecks)
        """
        if not self.state["initialized"]:
            return {
                "success": False,
                "error": "Agent not initialized. Call initialize() first."
            }

        start_time = time.time()

        try:
            operation = input_data.get("operation") or input_data.get("type")

            if not operation:
                return {
                    "success": False,
                    "error": "No operation specified"
                }

            # Route to appropriate handler
            if operation == "submit_task":
                result = await self._submit_task(input_data)
            elif operation == "assign_tasks":
                result = await self._assign_pending_tasks()
            elif operation == "get_task_status":
                result = await self._get_task_status(input_data)
            elif operation == "cancel_task":
                result = await self._cancel_task(input_data)
            elif operation == "get_queue_status":
                result = await self._get_queue_status()
            elif operation == "register_agent":
                result = await self._register_agent(input_data)
            elif operation == "update_agent_status":
                result = await self._update_agent_status(input_data)
            elif operation == "analyze":
                result = await self.analyze(input_data)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }

            # Track execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result["execution_time_ms"] = round(execution_time_ms, 2)

            # Update state
            self.state["total_tasks_processed"] += 1

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": round(execution_time_ms, 2)
            }

    async def shutdown(self) -> Dict[str, Any]:
        """Shutdown the agent and clean up resources"""
        try:
            # Clear queues and caches
            self.task_queue.clear()
            self.tasks.clear()
            self.agents.clear()
            self.assignment_history.clear()

            self.state["initialized"] = False

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": {
                    "tasks_submitted": self.metrics["tasks_submitted"],
                    "tasks_assigned": self.metrics["tasks_assigned"],
                    "tasks_completed": self.metrics["tasks_completed"],
                    "tasks_failed": self.metrics["tasks_failed"],
                    "agents_registered": self.metrics["agents_registered"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "reason": f"Shutdown failed: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Get resource usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            # Check resource limits
            memory_ok = memory_mb < self.typed_config.memory_limit_mb
            cpu_ok = cpu_percent < self.typed_config.cpu_limit_percent

            # Check queue health
            queue_ok = len(self.task_queue) < self.typed_config.queue_size_warning_threshold

            status = "ready" if (memory_ok and cpu_ok and queue_ok) else "degraded"

            return {
                "status": status,
                "agent_id": self.agent_id,
                "initialized": self.state["initialized"],
                "resources": {
                    "memory_mb": round(memory_mb, 2),
                    "memory_limit_mb": self.typed_config.memory_limit_mb,
                    "memory_percent": round((memory_mb / self.typed_config.memory_limit_mb) * 100, 1),
                    "cpu_percent": round(cpu_percent, 1),
                    "cpu_limit_percent": self.typed_config.cpu_limit_percent
                },
                "queue": {
                    "length": len(self.task_queue),
                    "threshold": self.typed_config.queue_size_warning_threshold,
                    "healthy": queue_ok
                },
                "state": self.state.copy(),
                "metrics": self.metrics.copy()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    # =====================================================================
    # Task Submission & Management
    # =====================================================================

    async def _submit_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new task to the queue"""
        try:
            task_id = f"task_{datetime.now().timestamp()}"

            # Parse priority
            priority_value = task_data.get("priority", TaskPriority.MEDIUM.value)
            if isinstance(priority_value, int):
                priority = TaskPriority(priority_value)
            else:
                priority = TaskPriority[priority_value.upper()]

            # Create task
            task = Task(
                task_id=task_id,
                task_type=task_data["task_type"],
                description=task_data.get("description", ""),
                requirements=task_data.get("requirements", {}),
                priority=priority,
                created_at=datetime.now()
            )

            # Add to priority queue (negative priority for max-heap behavior)
            heapq.heappush(
                self.task_queue,
                (-task.priority.value, task.created_at, task_id)
            )
            self.tasks[task_id] = task

            # Update metrics
            self.metrics["tasks_submitted"] += 1

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
        start_time = time.time()

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
                    self.metrics["tasks_assigned"] += 1
                    self.state["total_assignments_made"] += 1
                else:
                    # Put back in queue
                    heapq.heappush(self.task_queue, (priority, created_at, task_id))
                    failed_count += 1
                    break
            else:
                # No available agent, put back in queue
                heapq.heappush(self.task_queue, (priority, created_at, task_id))
                break

        # Update avg assignment time
        if assigned_count > 0:
            assignment_time_ms = (time.time() - start_time) * 1000
            self.metrics["avg_assignment_time_ms"] = assignment_time_ms / assigned_count

        return {
            "success": True,
            "assigned": assigned_count,
            "failed": failed_count,
            "remaining_in_queue": len(self.task_queue)
        }

    async def _select_best_agent(self, task: Task) -> Optional[str]:
        """Select the best agent for a task using multi-factor scoring"""
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
        """
        Calculate fitness score for agent-task pair

        Scoring factors:
        1. Specialization match (if agent type matches task type)
        2. Success rate (historical performance)
        3. Current load (prefer less busy agents)
        4. Performance (prefer faster agents)
        """
        score = 0.0

        # Factor 1: Specialization match
        if workload.agent_type == task.task_type:
            score += self.typed_config.specialization_bonus

        # Factor 2: Success rate (0-1 scale)
        score += workload.success_rate * self.typed_config.success_rate_weight

        # Factor 3: Current load (inverse, more available = higher score)
        load_factor = 1.0 - (workload.current_tasks / workload.max_concurrent_tasks)
        score += load_factor * self.typed_config.load_weight

        # Factor 4: Performance (faster = better)
        if workload.avg_completion_time_ms > 0:
            # Normalize to 0-1 scale (5000ms = baseline)
            perf_factor = max(0, 1.0 - (workload.avg_completion_time_ms / 5000))
            score += perf_factor * self.typed_config.performance_weight

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
            "task": task.to_dict()
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
        self.metrics["tasks_cancelled"] += 1

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
            "failed": 0,
            "cancelled": 0
        }

        for task in self.tasks.values():
            status_counts[task.status.value] += 1

        available_agents = sum(
            1 for a in self.agents.values()
            if a.is_available and a.current_tasks < a.max_concurrent_tasks
        )

        return {
            "success": True,
            "queue_length": len(self.task_queue),
            "total_tasks": len(self.tasks),
            "status_breakdown": status_counts,
            "available_agents": available_agents,
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
            max_concurrent_tasks=agent_data.get(
                "max_concurrent_tasks",
                self.typed_config.max_concurrent_tasks_per_agent
            )
        )

        self.agents[agent_id] = workload
        self.metrics["agents_registered"] += 1

        return {
            "success": True,
            "message": f"Agent {agent_id} registered",
            "workload": workload.to_dict()
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
            self.metrics["tasks_completed"] += 1

            # Update success rate
            total = workload.total_completed + workload.total_failed
            workload.success_rate = workload.total_completed / total if total > 0 else 1.0

        if "task_failed" in agent_data:
            workload.total_failed += 1
            workload.current_tasks = max(0, workload.current_tasks - 1)
            self.metrics["tasks_failed"] += 1

            # Update success rate
            total = workload.total_completed + workload.total_failed
            workload.success_rate = workload.total_completed / total if total > 0 else 1.0

        return {
            "success": True,
            "agent": workload.to_dict()
        }

    # =====================================================================
    # Analysis
    # =====================================================================

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

    def _analyze_overview(self) -> Dict[str, Any]:
        """Overview of task distribution"""
        available_agents = sum(
            1 for a in self.agents.values()
            if a.is_available and a.current_tasks < a.max_concurrent_tasks
        )

        return {
            "total_tasks": len(self.tasks),
            "queued_tasks": len(self.task_queue),
            "total_agents": len(self.agents),
            "available_agents": available_agents,
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
        avg_util = sum(utilizations) / len(utilizations) if utilizations else 0
        variance = (
            sum((u - avg_util) ** 2 for u in utilizations) / len(utilizations)
            if utilizations else 0
        )

        return {
            "balanced": variance < self.typed_config.variance_threshold,
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
        if len(self.task_queue) > self.typed_config.queue_size_warning_threshold:
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
        """Inject activity tracker dependency"""
        self.activity_tracker = tracker

    def set_agent_factory(self, factory):
        """Inject agent factory dependency"""
        self.agent_factory = factory


# =========================================================================
# Factory Function
# =========================================================================

async def create_task_assignment_agent(
    agent_id: str = "task_assign_001",
    config: Optional[TaskAssignmentAgentConfig] = None,
    activity_tracker=None,
    agent_factory=None
) -> TaskAssignmentAgent:
    """
    Factory function to create and initialize a Task Assignment Agent

    Args:
        agent_id: Unique identifier for the agent
        config: Configuration object (uses environment if not provided)
        activity_tracker: Optional activity tracker dependency
        agent_factory: Optional agent factory dependency

    Returns:
        Initialized TaskAssignmentAgent instance
    """
    if config is None:
        config = TaskAssignmentAgentConfig.from_environment()

    agent = TaskAssignmentAgent(
        agent_id=agent_id,
        config=config,
        activity_tracker=activity_tracker,
        agent_factory=agent_factory
    )

    await agent.initialize()

    return agent


# =========================================================================
# Main (for testing)
# =========================================================================

if __name__ == "__main__":
    async def demo():
        """Demonstrate Task Assignment Agent capabilities"""
        print("\n" + "=" * 80)
        print("TASK ASSIGNMENT AGENT v1.0 - DEMO")
        print("=" * 80)

        # Create agent
        print("\n[1] Creating agent...")
        agent = await create_task_assignment_agent(agent_id="task_assign_demo")
        print(f"    Agent created: {agent.agent_id}")
        print(f"    Initialized: {agent.state['initialized']}")

        # Register agents
        print("\n[2] Registering worker agents...")
        for i in range(3):
            result = await agent.execute({
                "operation": "register_agent",
                "agent_id": f"worker_{i+1}",
                "agent_type": "data_processor",
                "max_concurrent_tasks": 2
            })
            if not result.get('success'):
                print(f"    Worker {i+1}: FAILED - {result.get('error', 'Unknown error')}")
            else:
                print(f"    Worker {i+1}: {result.get('message', 'Registered')}")

        # Submit tasks
        print("\n[3] Submitting tasks...")
        for i in range(5):
            result = await agent.execute({
                "operation": "submit_task",
                "task_type": "data_processor",
                "description": f"Process dataset {i+1}",
                "priority": 2 if i < 3 else 3
            })
            print(f"    Task {i+1}: {result.get('message', 'Submitted')} (ID: {result.get('task_id', 'N/A')})")

        # Get queue status
        print("\n[4] Queue status:")
        status = await agent.execute({"operation": "get_queue_status"})
        print(f"    Success: {status.get('success', False)}")
        if status.get('success'):
            print(f"    Total tasks: {status.get('total_tasks', 0)}")
            print(f"    Queue length: {status.get('queue_length', 0)}")
            print(f"    Available agents: {status.get('available_agents', 0)}/{status.get('total_agents', 0)}")
            print(f"    Status breakdown: {json.dumps(status.get('status_breakdown', {}), indent=6)}")

        # Analyze load balance
        print("\n[5] Load balance analysis:")
        analysis = await agent.execute({
            "operation": "analyze",
            "analysis_type": "load_balance"
        })
        print(f"    Balanced: {analysis.get('balanced', False)}")
        print(f"    Average utilization: {analysis.get('avg_utilization', 0)}%")

        # Health check
        print("\n[6] Health check:")
        health = await agent.health_check()
        print(f"    Status: {health['status']}")
        print(f"    Memory: {health['resources']['memory_mb']:.2f} MB")
        print(f"    Queue health: {'OK' if health['queue']['healthy'] else 'WARNING'}")

        # Shutdown
        print("\n[7] Shutting down...")
        shutdown_result = await agent.shutdown()
        print(f"    Status: {shutdown_result['status']}")
        print(f"    Final metrics: {json.dumps(shutdown_result['final_metrics'], indent=6)}")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80 + "\n")

    asyncio.run(demo())
