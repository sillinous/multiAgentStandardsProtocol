"""
Agent Activity Tracker - Meta-Agent for Monitoring Agent Ecosystem

This agent monitors, logs, and analyzes the activity of all other agents.
It provides real-time insights into what agents are doing, their performance,
and coordination patterns.

Category: Meta-Agent (Monitoring & Observability)
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentCapability, MessageType


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


class AgentActivityTracker(BaseAgent):
    """
    Meta-agent that tracks and analyzes all agent activity

    Capabilities:
    - Real-time activity monitoring
    - Performance metrics collection
    - Activity feed generation
    - Agent health monitoring
    - Coordination pattern analysis
    """

    def __init__(
        self,
        agent_id: str = "activity_tracker_001",
        workspace_path: str = "./autonomous-ecosystem/workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="activity_tracker",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Activity storage
        self.activities: deque = deque(maxlen=10000)  # Keep last 10k activities
        self.metrics: Dict[str, AgentMetrics] = {}  # agent_id -> metrics

        # Activity indices for fast lookup
        self.activities_by_agent: Dict[str, List[AgentActivity]] = {}
        self.activities_by_type: Dict[ActivityType, List[AgentActivity]] = {}

        # Real-time feed (last 100 activities)
        self.recent_feed: deque = deque(maxlen=100)

        # Monitoring state
        self.monitoring_active = True
        self.start_time = datetime.now()

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tracking task"""
        task_type = task.get("type")

        if task_type == "log_activity":
            return await self._log_activity(task)
        elif task_type == "get_agent_metrics":
            return await self._get_agent_metrics(task)
        elif task_type == "get_activity_feed":
            return await self._get_activity_feed(task)
        elif task_type == "get_system_health":
            return await self._get_system_health(task)
        elif task_type == "get_coordination_patterns":
            return await self._get_coordination_patterns(task)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

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

    # =====================================================================
    # Activity Logging
    # =====================================================================

    async def _log_activity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Log a new agent activity"""
        try:
            activity = AgentActivity(
                activity_id=f"act_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                agent_id=task["agent_id"],
                agent_type=task.get("agent_type", "unknown"),
                activity_type=ActivityType(task["activity_type"]),
                description=task["description"],
                details=task.get("details", {}),
                duration_ms=task.get("duration_ms"),
                success=task.get("success")
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

            return {
                "success": True,
                "activity_id": activity.activity_id,
                "timestamp": activity.timestamp.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _update_metrics(self, activity: AgentActivity):
        """Update agent metrics based on activity"""
        agent_id = activity.agent_id

        # Initialize metrics if needed
        if agent_id not in self.metrics:
            self.metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_type=activity.agent_type
            )

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
        if activity.activity_type == ActivityType.SPAWNED:
            spawn_time = activity.timestamp
        else:
            spawn_time = self.start_time

        metrics.uptime_seconds = (datetime.now() - spawn_time).total_seconds()

    # =====================================================================
    # Query Methods
    # =====================================================================

    async def _get_agent_metrics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics for specific agent or all agents"""
        agent_id = task.get("agent_id")

        if agent_id:
            metrics = self.metrics.get(agent_id)
            if metrics:
                metrics_dict = asdict(metrics)
                # Convert datetime to ISO string
                if metrics_dict.get("last_activity"):
                    metrics_dict["last_activity"] = metrics_dict["last_activity"].isoformat()
                return {
                    "success": True,
                    "metrics": metrics_dict
                }
            else:
                return {
                    "success": False,
                    "error": f"No metrics found for agent: {agent_id}"
                }
        else:
            # Return all metrics
            all_metrics = {}
            for agent_id, metrics in self.metrics.items():
                metrics_dict = asdict(metrics)
                # Convert datetime to ISO string
                if metrics_dict.get("last_activity"):
                    metrics_dict["last_activity"] = metrics_dict["last_activity"].isoformat()
                all_metrics[agent_id] = metrics_dict

            return {
                "success": True,
                "total_agents": len(self.metrics),
                "metrics": all_metrics
            }

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
            "activities": [
                {
                    "activity_id": a.activity_id,
                    "timestamp": a.timestamp.isoformat(),
                    "agent_id": a.agent_id,
                    "agent_type": a.agent_type,
                    "activity_type": a.activity_type.value,
                    "description": a.description,
                    "details": a.details,
                    "duration_ms": a.duration_ms,
                    "success": a.success
                }
                for a in activities
            ]
        }

    async def _get_system_health(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall system health metrics"""
        total_agents = len(self.metrics)
        active_agents = sum(
            1 for m in self.metrics.values()
            if m.last_activity and (datetime.now() - m.last_activity).seconds < 60
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
                "total_messages": sum(m.messages_sent + m.messages_received for m in self.metrics.values()),
                "total_errors": sum(m.errors_count for m in self.metrics.values()),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            }
        }

    async def _get_coordination_patterns(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent coordination patterns"""
        # Find communication activities
        comm_activities = [
            a for a in self.activities
            if a.activity_type in [ActivityType.COMMUNICATION_SENT, ActivityType.COMMUNICATION_RECEIVED]
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
                collaborations.append({
                    "from": sender,
                    "to": receiver,
                    "message_count": count
                })

        collaborations.sort(key=lambda x: x["message_count"], reverse=True)

        return {
            "success": True,
            "total_communications": len(comm_activities),
            "unique_connections": len(collaborations),
            "top_collaborations": collaborations[:20]
        }

    # =====================================================================
    # Analysis Methods
    # =====================================================================

    def _analyze_ecosystem_overview(self) -> Dict[str, Any]:
        """High-level ecosystem overview"""
        return {
            "total_agents": len(self.metrics),
            "total_activities": len(self.activities),
            "activity_types": {
                activity_type.value: len(activities)
                for activity_type, activities in self.activities_by_type.items()
            },
            "top_performers": self._get_top_performers(5),
            "recent_activity": len([
                a for a in self.activities
                if (datetime.now() - a.timestamp).seconds < 300  # Last 5 minutes
            ])
        }

    def _analyze_performance(self) -> Dict[str, Any]:
        """Detailed performance analysis"""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.tasks_completed,
            reverse=True
        )

        return {
            "top_performers": [
                {
                    "agent_id": m.agent_id,
                    "agent_type": m.agent_type,
                    "tasks_completed": m.tasks_completed,
                    "success_rate": round(m.success_rate * 100, 2),
                    "avg_execution_time_ms": round(m.avg_execution_time_ms, 2)
                }
                for m in sorted_metrics[:10]
            ],
            "slowest_agents": sorted(
                [
                    {
                        "agent_id": m.agent_id,
                        "avg_execution_time_ms": round(m.avg_execution_time_ms, 2)
                    }
                    for m in self.metrics.values()
                    if m.avg_execution_time_ms > 0
                ],
                key=lambda x: x["avg_execution_time_ms"],
                reverse=True
            )[:10]
        }

    def _analyze_bottlenecks(self) -> Dict[str, Any]:
        """Identify potential bottlenecks"""
        bottlenecks = []

        for agent_id, metrics in self.metrics.items():
            # High failure rate
            if metrics.tasks_failed > 0 and metrics.success_rate < 0.8:
                bottlenecks.append({
                    "agent_id": agent_id,
                    "issue": "high_failure_rate",
                    "success_rate": round(metrics.success_rate * 100, 2),
                    "severity": "high"
                })

            # Slow execution
            if metrics.avg_execution_time_ms > 5000:  # 5 seconds
                bottlenecks.append({
                    "agent_id": agent_id,
                    "issue": "slow_execution",
                    "avg_time_ms": round(metrics.avg_execution_time_ms, 2),
                    "severity": "medium"
                })

            # High error rate
            if metrics.errors_count > 10:
                bottlenecks.append({
                    "agent_id": agent_id,
                    "issue": "frequent_errors",
                    "error_count": metrics.errors_count,
                    "severity": "high"
                })

        return {
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": bottlenecks
        }

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
            "coordination_health": "good" if len(isolated) == 0 else "needs_improvement"
        }

    def _get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Get top performing agents"""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: (m.success_rate, m.tasks_completed),
            reverse=True
        )

        return [
            {
                "agent_id": m.agent_id,
                "agent_type": m.agent_type,
                "tasks_completed": m.tasks_completed,
                "success_rate": round(m.success_rate * 100, 2)
            }
            for m in sorted_metrics[:limit]
        ]

    # =====================================================================
    # Public API
    # =====================================================================

    def log_agent_spawn(self, agent_id: str, agent_type: str):
        """Log when an agent is spawned"""
        asyncio.create_task(self._log_activity({
            "agent_id": agent_id,
            "agent_type": agent_type,
            "activity_type": "spawned",
            "description": f"Agent {agent_type} spawned",
            "details": {"timestamp": datetime.now().isoformat()}
        }))

    def log_task_start(self, agent_id: str, agent_type: str, task_description: str):
        """Log task start"""
        asyncio.create_task(self._log_activity({
            "agent_id": agent_id,
            "agent_type": agent_type,
            "activity_type": "task_started",
            "description": task_description,
            "details": {"start_time": datetime.now().isoformat()}
        }))

    def log_task_complete(
        self,
        agent_id: str,
        agent_type: str,
        task_description: str,
        duration_ms: float,
        success: bool = True
    ):
        """Log task completion"""
        asyncio.create_task(self._log_activity({
            "agent_id": agent_id,
            "agent_type": agent_type,
            "activity_type": "task_completed" if success else "task_failed",
            "description": task_description,
            "details": {},
            "duration_ms": duration_ms,
            "success": success
        }))

    def get_live_feed(self, limit: int = 50) -> List[Dict]:
        """Get live activity feed for dashboard"""
        activities = sorted(
            list(self.recent_feed),
            key=lambda a: a.timestamp,
            reverse=True
        )[:limit]

        return [
            {
                "timestamp": a.timestamp.isoformat(),
                "agent_id": a.agent_id,
                "agent_type": a.agent_type,
                "activity_type": a.activity_type.value,
                "description": a.description,
                "success": a.success
            }
            for a in activities
        ]

    def get_agent_summary(self, agent_id: str) -> Optional[Dict]:
        """Get summary for specific agent"""
        metrics = self.metrics.get(agent_id)
        if not metrics:
            return None

        return {
            "agent_id": metrics.agent_id,
            "agent_type": metrics.agent_type,
            "status": metrics.current_state,
            "tasks_completed": metrics.tasks_completed,
            "success_rate": round(metrics.success_rate * 100, 2),
            "avg_execution_time_ms": round(metrics.avg_execution_time_ms, 2),
            "uptime_seconds": round(metrics.uptime_seconds, 2),
            "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
        }


# Singleton instance
_activity_tracker = None

def get_activity_tracker() -> AgentActivityTracker:
    """Get or create activity tracker instance"""
    global _activity_tracker
    if _activity_tracker is None:
        _activity_tracker = AgentActivityTracker()
    return _activity_tracker


if __name__ == "__main__":
    # Demo the activity tracker
    import asyncio

    async def demo():
        tracker = get_activity_tracker()

        # Simulate some activities
        await tracker._log_activity({
            "agent_id": "test_agent_001",
            "agent_type": "test_agent",
            "activity_type": "spawned",
            "description": "Test agent spawned",
            "details": {}
        })

        await tracker._log_activity({
            "agent_id": "test_agent_001",
            "agent_type": "test_agent",
            "activity_type": "task_started",
            "description": "Processing test data",
            "details": {"task_id": "task_001"}
        })

        await tracker._log_activity({
            "agent_id": "test_agent_001",
            "agent_type": "test_agent",
            "activity_type": "task_completed",
            "description": "Test data processed",
            "details": {"task_id": "task_001"},
            "duration_ms": 1250.5,
            "success": True
        })

        # Get metrics
        result = await tracker._get_agent_metrics({"agent_id": "test_agent_001"})
        print("\n[Agent Metrics]")
        # Convert datetime to string for JSON serialization
        if result.get("success") and "metrics" in result:
            metrics = result["metrics"]
            if "last_activity" in metrics and metrics["last_activity"]:
                metrics["last_activity"] = metrics["last_activity"].isoformat() if hasattr(metrics["last_activity"], 'isoformat') else str(metrics["last_activity"])
        print(json.dumps(result, indent=2))

        # Get activity feed
        feed = await tracker._get_activity_feed({"limit": 10})
        print("\n[Activity Feed]")
        print(json.dumps(feed, indent=2))

        # Get system health
        health = await tracker._get_system_health({})
        print("\n[System Health]")
        print(json.dumps(health, indent=2))

    asyncio.run(demo())
