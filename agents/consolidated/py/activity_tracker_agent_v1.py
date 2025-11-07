"""
Activity Tracker Agent v1.0 - Architecturally Compliant
========================================================

Meta-Agent for Monitoring Agent Ecosystem Activity

This agent monitors, logs, and analyzes the activity of all other agents,
providing real-time insights into agent performance, coordination patterns,
and ecosystem health.

**Architectural Compliance:**
- Follows 8 architectural principles
- Supports 5 protocols (A2A, A2P, ACP, ANP, MCP)
- Environment-based configuration (12-factor)
- Standardized lifecycle management
- Resource monitoring and metrics

**Version:** 1.0
**Category:** Meta-Agent (Monitoring & Observability)
**Protocols:** A2A, A2P, ACP, ANP, MCP
"""

import asyncio
import json
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


# =========================================================================
# Constants
# =========================================================================

AGENT_TYPE = "activity_tracker"
VERSION = "1.0"

DEFAULT_MAX_ACTIVITIES = 10000
DEFAULT_FEED_SIZE = 100
DEFAULT_ACTIVE_THRESHOLD_SECONDS = 60


# =========================================================================
# Domain Models
# =========================================================================


class ActivityType(Enum):
    """Types of agent activities"""

    SPAWNED = "spawned"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    DECISION_MADE = "decision_made"
    COMMUNICATION_SENT = "communication_sent"
    COMMUNICATION_RECEIVED = "communication_received"
    STATE_CHANGED = "state_changed"
    ERROR_OCCURRED = "error_occurred"
    IDLE = "idle"


@dataclass
class AgentActivity:
    """Record of a single agent activity"""

    activity_id: str
    timestamp: datetime
    agent_id: str
    agent_type: str
    activity_type: ActivityType
    description: str
    details: Dict[str, Any]
    duration_ms: Optional[float] = None
    success: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "activity_id": self.activity_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "activity_type": self.activity_type.value,
            "description": self.description,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""

    agent_id: str
    agent_type: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    decisions_made: int = 0
    errors_count: int = 0
    uptime_seconds: float = 0.0
    current_state: str = "idle"
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_execution_time_ms": self.total_execution_time_ms,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "success_rate": self.success_rate,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "decisions_made": self.decisions_made,
            "errors_count": self.errors_count,
            "uptime_seconds": self.uptime_seconds,
            "current_state": self.current_state,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


# =========================================================================
# Configuration
# =========================================================================


@dataclass
class ActivityTrackerAgentConfig:
    """
    Configuration for Activity Tracker Agent

    All values can be overridden via environment variables following
    12-factor app methodology.
    """

    # Storage limits
    max_activities: int = DEFAULT_MAX_ACTIVITIES
    feed_size: int = DEFAULT_FEED_SIZE

    # Activity thresholds
    active_threshold_seconds: int = DEFAULT_ACTIVE_THRESHOLD_SECONDS
    slow_execution_threshold_ms: float = 5000.0
    high_failure_threshold: float = 0.8
    high_error_threshold: int = 10

    # Resource limits
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 80.0

    @classmethod
    def from_environment(cls) -> "ActivityTrackerAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            max_activities=int(
                os.getenv("ACTIVITY_TRACKER_MAX_ACTIVITIES", str(DEFAULT_MAX_ACTIVITIES))
            ),
            feed_size=int(os.getenv("ACTIVITY_TRACKER_FEED_SIZE", str(DEFAULT_FEED_SIZE))),
            active_threshold_seconds=int(
                os.getenv(
                    "ACTIVITY_TRACKER_ACTIVE_THRESHOLD", str(DEFAULT_ACTIVE_THRESHOLD_SECONDS)
                )
            ),
            slow_execution_threshold_ms=float(
                os.getenv("ACTIVITY_TRACKER_SLOW_THRESHOLD", "5000.0")
            ),
            high_failure_threshold=float(os.getenv("ACTIVITY_TRACKER_FAILURE_THRESHOLD", "0.8")),
            high_error_threshold=int(os.getenv("ACTIVITY_TRACKER_ERROR_THRESHOLD", "10")),
            memory_limit_mb=int(os.getenv("ACTIVITY_TRACKER_MEMORY_LIMIT_MB", "512")),
            cpu_limit_percent=float(os.getenv("ACTIVITY_TRACKER_CPU_LIMIT_PERCENT", "80.0")),
        )


# =========================================================================
# Activity Tracker Agent
# =========================================================================


class ActivityTrackerAgent(BaseAgent, ProtocolMixin):
    """
    Meta-agent for ecosystem-wide activity monitoring and analysis

    **Capabilities:**
    - Real-time activity monitoring
    - Performance metrics collection
    - Activity feed generation
    - Agent health monitoring
    - Coordination pattern analysis
    - Bottleneck detection

    **Architectural Standards:**
    - Inherits from BaseAgent + ProtocolMixin
    - Environment-based configuration
    - Resource monitoring
    - Full lifecycle management
    - Protocol support (A2A, A2P, ACP, ANP, MCP)
    """

    def __init__(self, agent_id: str, config: ActivityTrackerAgentConfig):
        """Initialize Activity Tracker Agent"""
        # Initialize both parent classes
        super(BaseAgent, self).__init__()
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = VERSION
        ProtocolMixin.__init__(self)

        # Store typed config
        self.typed_config = config

        # Activity storage with size limits
        self.activities: deque = deque(maxlen=config.max_activities)
        self.recent_feed: deque = deque(maxlen=config.feed_size)

        # Agent metrics
        self.metrics: Dict[str, AgentMetrics] = {}

        # Activity indices for fast lookup
        self.activities_by_agent: Dict[str, List[AgentActivity]] = {}
        self.activities_by_type: Dict[ActivityType, List[AgentActivity]] = {}

        # State tracking
        self.state = {"initialized": False, "monitoring_active": True, "total_activities_logged": 0}

        # Monitoring metrics
        self.tracker_metrics = {"activities_logged": 0, "agents_tracked": 0, "queries_processed": 0}

        # Resource tracking
        self.process = psutil.Process()
        self.start_time = datetime.now()

    # =====================================================================
    # Abstract Method Implementations (Required by BaseAgent)
    # =====================================================================

    async def _configure_data_sources(self):
        """Configure data sources - not required for activity tracker"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - activity tracker uses internal state only"""
        return {}

    async def _execute_logic(
        self, input_data: Dict[str, Any], fetched_data: Dict[str, Any]
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
            self.state["monitoring_active"] = True

            init_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "version": self.version,
                "initialization_time_ms": round(init_time_ms, 2),
            }

        except Exception as e:
            return {"success": False, "error": f"Initialization failed: {str(e)}"}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute activity tracking operations

        Supported operations:
        - log_activity: Log a new agent activity
        - get_agent_metrics: Get metrics for specific agent or all agents
        - get_activity_feed: Get recent activity feed
        - get_system_health: Get overall system health metrics
        - get_coordination_patterns: Analyze agent coordination patterns
        - analyze: Perform various analyses
        """
        if not self.state["initialized"]:
            return {"success": False, "error": "Agent not initialized. Call initialize() first."}

        start_time = time.time()

        try:
            operation = input_data.get("operation") or input_data.get("type")

            if not operation:
                return {"success": False, "error": "No operation specified"}

            # Route to appropriate handler
            if operation == "log_activity":
                result = await self._log_activity(input_data)
            elif operation == "get_agent_metrics":
                result = await self._get_agent_metrics(input_data)
            elif operation == "get_activity_feed":
                result = await self._get_activity_feed(input_data)
            elif operation == "get_system_health":
                result = await self._get_system_health()
            elif operation == "get_coordination_patterns":
                result = await self._get_coordination_patterns()
            elif operation == "analyze":
                result = await self.analyze(input_data)
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}

            # Track execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result["execution_time_ms"] = round(execution_time_ms, 2)

            # Update tracker metrics
            self.tracker_metrics["queries_processed"] += 1

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": round(execution_time_ms, 2),
            }

    async def shutdown(self) -> Dict[str, Any]:
        """Shutdown the agent and clean up resources"""
        try:
            self.state["monitoring_active"] = False
            self.state["initialized"] = False

            # Clear all data structures
            self.activities.clear()
            self.recent_feed.clear()
            self.metrics.clear()
            self.activities_by_agent.clear()
            self.activities_by_type.clear()

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": {
                    "activities_logged": self.tracker_metrics["activities_logged"],
                    "agents_tracked": self.tracker_metrics["agents_tracked"],
                    "queries_processed": self.tracker_metrics["queries_processed"],
                },
            }
        except Exception as e:
            return {"status": "error", "reason": f"Shutdown failed: {str(e)}"}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Get resource usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            # Check resource limits
            memory_ok = memory_mb < self.typed_config.memory_limit_mb
            cpu_ok = cpu_percent < self.typed_config.cpu_limit_percent

            # Check storage health
            storage_ok = len(self.activities) < self.typed_config.max_activities * 0.9

            status = "ready" if (memory_ok and cpu_ok and storage_ok) else "degraded"

            return {
                "status": status,
                "agent_id": self.agent_id,
                "initialized": self.state["initialized"],
                "monitoring_active": self.state["monitoring_active"],
                "resources": {
                    "memory_mb": round(memory_mb, 2),
                    "memory_limit_mb": self.typed_config.memory_limit_mb,
                    "memory_percent": round(
                        (memory_mb / self.typed_config.memory_limit_mb) * 100, 1
                    ),
                    "cpu_percent": round(cpu_percent, 1),
                    "cpu_limit_percent": self.typed_config.cpu_limit_percent,
                },
                "storage": {
                    "activities_stored": len(self.activities),
                    "max_activities": self.typed_config.max_activities,
                    "utilization_percent": round(
                        (len(self.activities) / self.typed_config.max_activities) * 100, 1
                    ),
                    "healthy": storage_ok,
                },
                "state": self.state.copy(),
                "metrics": self.tracker_metrics.copy(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =====================================================================
    # Activity Logging
    # =====================================================================

    async def _log_activity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Log a new agent activity"""
        try:
            # Parse activity type
            activity_type_value = task.get("activity_type")
            if isinstance(activity_type_value, str):
                activity_type = ActivityType(activity_type_value)
            else:
                activity_type = activity_type_value

            activity = AgentActivity(
                activity_id=f"act_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                agent_id=task["agent_id"],
                agent_type=task.get("agent_type", "unknown"),
                activity_type=activity_type,
                description=task["description"],
                details=task.get("details", {}),
                duration_ms=task.get("duration_ms"),
                success=task.get("success"),
            )

            # Store activity
            self.activities.append(activity)
            self.recent_feed.append(activity)

            # Index by agent
            if activity.agent_id not in self.activities_by_agent:
                self.activities_by_agent[activity.agent_id] = []
            self.activities_by_agent[activity.agent_id].append(activity)

            # Index by type
            if activity.activity_type not in self.activities_by_type:
                self.activities_by_type[activity.activity_type] = []
            self.activities_by_type[activity.activity_type].append(activity)

            # Update metrics
            self._update_metrics(activity)

            # Update tracker metrics
            self.tracker_metrics["activities_logged"] += 1
            self.tracker_metrics["agents_tracked"] = len(self.metrics)
            self.state["total_activities_logged"] += 1

            return {
                "success": True,
                "activity_id": activity.activity_id,
                "timestamp": activity.timestamp.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_metrics(self, activity: AgentActivity):
        """Update agent metrics based on activity"""
        agent_id = activity.agent_id

        # Initialize metrics if needed
        if agent_id not in self.metrics:
            self.metrics[agent_id] = AgentMetrics(agent_id=agent_id, agent_type=activity.agent_type)

        metrics = self.metrics[agent_id]
        metrics.last_activity = activity.timestamp

        # Update based on activity type
        if activity.activity_type == ActivityType.TASK_COMPLETED:
            metrics.tasks_completed += 1
            if activity.duration_ms:
                metrics.total_execution_time_ms += activity.duration_ms
                metrics.avg_execution_time_ms = (
                    metrics.total_execution_time_ms / metrics.tasks_completed
                )

        elif activity.activity_type == ActivityType.TASK_FAILED:
            metrics.tasks_failed += 1

        elif activity.activity_type == ActivityType.COMMUNICATION_SENT:
            metrics.messages_sent += 1

        elif activity.activity_type == ActivityType.COMMUNICATION_RECEIVED:
            metrics.messages_received += 1

        elif activity.activity_type == ActivityType.DECISION_MADE:
            metrics.decisions_made += 1

        elif activity.activity_type == ActivityType.ERROR_OCCURRED:
            metrics.errors_count += 1

        elif activity.activity_type == ActivityType.STATE_CHANGED:
            metrics.current_state = activity.details.get("new_state", "unknown")

        # Calculate success rate
        total_tasks = metrics.tasks_completed + metrics.tasks_failed
        if total_tasks > 0:
            metrics.success_rate = metrics.tasks_completed / total_tasks

        # Calculate uptime
        metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

    # =====================================================================
    # Query Methods
    # =====================================================================

    async def _get_agent_metrics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics for specific agent or all agents"""
        agent_id = task.get("agent_id")

        if agent_id:
            metrics = self.metrics.get(agent_id)
            if metrics:
                return {"success": True, "metrics": metrics.to_dict()}
            else:
                return {"success": False, "error": f"No metrics found for agent: {agent_id}"}
        else:
            # Return all metrics
            all_metrics = {
                agent_id: metrics.to_dict() for agent_id, metrics in self.metrics.items()
            }

            return {"success": True, "total_agents": len(self.metrics), "metrics": all_metrics}

    async def _get_activity_feed(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent activity feed"""
        limit = task.get("limit", 50)
        agent_id = task.get("agent_id")
        activity_type = task.get("activity_type")

        # Filter activities
        activities = list(self.recent_feed)

        if agent_id:
            activities = [a for a in activities if a.agent_id == agent_id]

        if activity_type:
            activities = [a for a in activities if a.activity_type.value == activity_type]

        # Limit and sort
        activities = sorted(activities, key=lambda a: a.timestamp, reverse=True)[:limit]

        return {
            "success": True,
            "count": len(activities),
            "activities": [a.to_dict() for a in activities],
        }

    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        total_agents = len(self.metrics)
        active_agents = sum(
            1
            for m in self.metrics.values()
            if m.last_activity
            and (datetime.now() - m.last_activity).seconds
            < self.typed_config.active_threshold_seconds
        )

        total_tasks = sum(m.tasks_completed + m.tasks_failed for m in self.metrics.values())
        total_completed = sum(m.tasks_completed for m in self.metrics.values())
        total_failed = sum(m.tasks_failed for m in self.metrics.values())

        overall_success_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "success": True,
            "health": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "idle_agents": total_agents - active_agents,
                "total_tasks": total_tasks,
                "tasks_completed": total_completed,
                "tasks_failed": total_failed,
                "overall_success_rate": round(overall_success_rate, 2),
                "total_messages": sum(
                    m.messages_sent + m.messages_received for m in self.metrics.values()
                ),
                "total_errors": sum(m.errors_count for m in self.metrics.values()),
                "uptime_seconds": round((datetime.now() - self.start_time).total_seconds(), 2),
            },
        }

    async def _get_coordination_patterns(self) -> Dict[str, Any]:
        """Analyze agent coordination patterns"""
        # Find communication activities
        comm_activities = [
            a
            for a in self.activities
            if a.activity_type
            in [ActivityType.COMMUNICATION_SENT, ActivityType.COMMUNICATION_RECEIVED]
        ]

        # Build communication graph
        comm_graph = {}
        for activity in comm_activities:
            if activity.activity_type == ActivityType.COMMUNICATION_SENT:
                sender = activity.agent_id
                receiver = activity.details.get("recipient", "unknown")

                if sender not in comm_graph:
                    comm_graph[sender] = {}

                comm_graph[sender][receiver] = comm_graph[sender].get(receiver, 0) + 1

        # Find most active collaborations
        collaborations = []
        for sender, receivers in comm_graph.items():
            for receiver, count in receivers.items():
                collaborations.append({"from": sender, "to": receiver, "message_count": count})

        collaborations.sort(key=lambda x: x["message_count"], reverse=True)

        return {
            "success": True,
            "total_communications": len(comm_activities),
            "unique_connections": len(collaborations),
            "top_collaborations": collaborations[:20],
        }

    # =====================================================================
    # Analysis Methods
    # =====================================================================

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent ecosystem health and patterns"""
        analysis_type = input_data.get("analysis_type", "overview")

        if analysis_type == "overview":
            return self._analyze_ecosystem_overview()
        elif analysis_type == "performance":
            return self._analyze_performance()
        elif analysis_type == "bottlenecks":
            return self._analyze_bottlenecks()
        elif analysis_type == "coordination":
            return self._analyze_coordination()
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    def _analyze_ecosystem_overview(self) -> Dict[str, Any]:
        """High-level ecosystem overview"""
        recent_threshold = datetime.now() - timedelta(minutes=5)
        recent_activity_count = len([a for a in self.activities if a.timestamp >= recent_threshold])

        return {
            "total_agents": len(self.metrics),
            "total_activities": len(self.activities),
            "activity_types": {
                activity_type.value: len(activities)
                for activity_type, activities in self.activities_by_type.items()
            },
            "top_performers": self._get_top_performers(5),
            "recent_activity_count": recent_activity_count,
        }

    def _analyze_performance(self) -> Dict[str, Any]:
        """Detailed performance analysis"""
        sorted_metrics = sorted(
            self.metrics.values(), key=lambda m: m.tasks_completed, reverse=True
        )

        return {
            "top_performers": [
                {
                    "agent_id": m.agent_id,
                    "agent_type": m.agent_type,
                    "tasks_completed": m.tasks_completed,
                    "success_rate": round(m.success_rate * 100, 2),
                    "avg_execution_time_ms": round(m.avg_execution_time_ms, 2),
                }
                for m in sorted_metrics[:10]
            ],
            "slowest_agents": sorted(
                [
                    {
                        "agent_id": m.agent_id,
                        "avg_execution_time_ms": round(m.avg_execution_time_ms, 2),
                    }
                    for m in self.metrics.values()
                    if m.avg_execution_time_ms > 0
                ],
                key=lambda x: x["avg_execution_time_ms"],
                reverse=True,
            )[:10],
        }

    def _analyze_bottlenecks(self) -> Dict[str, Any]:
        """Identify potential bottlenecks"""
        bottlenecks = []

        for agent_id, metrics in self.metrics.items():
            # High failure rate
            if (
                metrics.tasks_failed > 0
                and metrics.success_rate < self.typed_config.high_failure_threshold
            ):
                bottlenecks.append(
                    {
                        "agent_id": agent_id,
                        "issue": "high_failure_rate",
                        "success_rate": round(metrics.success_rate * 100, 2),
                        "severity": "high",
                    }
                )

            # Slow execution
            if metrics.avg_execution_time_ms > self.typed_config.slow_execution_threshold_ms:
                bottlenecks.append(
                    {
                        "agent_id": agent_id,
                        "issue": "slow_execution",
                        "avg_time_ms": round(metrics.avg_execution_time_ms, 2),
                        "severity": "medium",
                    }
                )

            # High error rate
            if metrics.errors_count > self.typed_config.high_error_threshold:
                bottlenecks.append(
                    {
                        "agent_id": agent_id,
                        "issue": "frequent_errors",
                        "error_count": metrics.errors_count,
                        "severity": "high",
                    }
                )

        return {"bottlenecks_found": len(bottlenecks), "bottlenecks": bottlenecks}

    def _analyze_coordination(self) -> Dict[str, Any]:
        """Analyze coordination effectiveness"""
        # Count message exchanges
        sent = sum(m.messages_sent for m in self.metrics.values())
        received = sum(m.messages_received for m in self.metrics.values())

        # Find isolated agents (no communication)
        isolated = [
            m.agent_id
            for m in self.metrics.values()
            if m.messages_sent == 0 and m.messages_received == 0
        ]

        return {
            "total_messages": sent + received,
            "messages_sent": sent,
            "messages_received": received,
            "isolated_agents": len(isolated),
            "isolated_agent_ids": isolated,
            "coordination_health": "good" if len(isolated) == 0 else "needs_improvement",
        }

    def _get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Get top performing agents"""
        sorted_metrics = sorted(
            self.metrics.values(), key=lambda m: (m.success_rate, m.tasks_completed), reverse=True
        )

        return [
            {
                "agent_id": m.agent_id,
                "agent_type": m.agent_type,
                "tasks_completed": m.tasks_completed,
                "success_rate": round(m.success_rate * 100, 2),
            }
            for m in sorted_metrics[:limit]
        ]


# =========================================================================
# Factory Function
# =========================================================================


async def create_activity_tracker_agent(
    agent_id: str = "activity_tracker_001", config: Optional[ActivityTrackerAgentConfig] = None
) -> ActivityTrackerAgent:
    """
    Factory function to create and initialize an Activity Tracker Agent

    Args:
        agent_id: Unique identifier for the agent
        config: Configuration object (uses environment if not provided)

    Returns:
        Initialized ActivityTrackerAgent instance
    """
    if config is None:
        config = ActivityTrackerAgentConfig.from_environment()

    agent = ActivityTrackerAgent(agent_id=agent_id, config=config)

    await agent.initialize()

    return agent


# =========================================================================
# Main (for testing)
# =========================================================================

if __name__ == "__main__":

    async def demo():
        """Demonstrate Activity Tracker Agent capabilities"""
        print("\n" + "=" * 80)
        print("ACTIVITY TRACKER AGENT v1.0 - DEMO")
        print("=" * 80)

        # Create agent
        print("\n[1] Creating agent...")
        agent = await create_activity_tracker_agent(agent_id="activity_tracker_demo")
        print(f"    Agent created: {agent.agent_id}")
        print(f"    Initialized: {agent.state['initialized']}")

        # Simulate activities from multiple agents
        print("\n[2] Logging activities...")
        test_activities = [
            {
                "operation": "log_activity",
                "agent_id": "test_agent_001",
                "agent_type": "data_processor",
                "activity_type": "spawned",
                "description": "Data processor spawned",
                "details": {},
            },
            {
                "operation": "log_activity",
                "agent_id": "test_agent_001",
                "agent_type": "data_processor",
                "activity_type": "task_started",
                "description": "Processing dataset alpha",
                "details": {"dataset": "alpha"},
            },
            {
                "operation": "log_activity",
                "agent_id": "test_agent_001",
                "agent_type": "data_processor",
                "activity_type": "task_completed",
                "description": "Dataset alpha processed",
                "details": {"dataset": "alpha", "records": 1000},
                "duration_ms": 1250.5,
                "success": True,
            },
            {
                "operation": "log_activity",
                "agent_id": "test_agent_002",
                "agent_type": "analyzer",
                "activity_type": "spawned",
                "description": "Analyzer spawned",
                "details": {},
            },
            {
                "operation": "log_activity",
                "agent_id": "test_agent_002",
                "agent_type": "analyzer",
                "activity_type": "task_completed",
                "description": "Analysis complete",
                "details": {"insights": 5},
                "duration_ms": 850.2,
                "success": True,
            },
        ]

        for activity in test_activities:
            result = await agent.execute(activity)
            if result.get("success"):
                print(f"    Logged: {activity['description']}")

        # Get agent metrics
        print("\n[3] Agent metrics:")
        metrics_result = await agent.execute(
            {"operation": "get_agent_metrics", "agent_id": "test_agent_001"}
        )
        if metrics_result.get("success"):
            metrics = metrics_result["metrics"]
            print(f"    Agent: {metrics['agent_id']}")
            print(f"    Tasks completed: {metrics['tasks_completed']}")
            print(f"    Success rate: {metrics['success_rate'] * 100:.1f}%")
            print(f"    Avg execution time: {metrics['avg_execution_time_ms']:.2f} ms")

        # Get activity feed
        print("\n[4] Activity feed:")
        feed_result = await agent.execute({"operation": "get_activity_feed", "limit": 5})
        if feed_result.get("success"):
            print(f"    Recent activities: {feed_result['count']}")
            for activity in feed_result["activities"][:3]:
                print(f"      - {activity['description']} ({activity['agent_id']})")

        # Get system health
        print("\n[5] System health:")
        health_result = await agent.execute({"operation": "get_system_health"})
        if health_result.get("success"):
            health = health_result["health"]
            print(f"    Total agents: {health['total_agents']}")
            print(f"    Active agents: {health['active_agents']}")
            print(f"    Tasks completed: {health['tasks_completed']}")
            print(f"    Overall success rate: {health['overall_success_rate']}%")

        # Analyze ecosystem
        print("\n[6] Ecosystem analysis:")
        analysis_result = await agent.execute({"operation": "analyze", "analysis_type": "overview"})
        print(f"    Total activities: {analysis_result.get('total_activities', 0)}")
        print(f"    Recent activity: {analysis_result.get('recent_activity_count', 0)}")

        # Health check
        print("\n[7] Health check:")
        health = await agent.health_check()
        print(f"    Status: {health['status']}")
        print(f"    Memory: {health['resources']['memory_mb']:.2f} MB")
        print(f"    Activities stored: {health['storage']['activities_stored']}")

        # Shutdown
        print("\n[8] Shutting down...")
        shutdown_result = await agent.shutdown()
        print(f"    Status: {shutdown_result['status']}")
        print(f"    Final metrics: {json.dumps(shutdown_result['final_metrics'], indent=6)}")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80 + "\n")

    asyncio.run(demo())
