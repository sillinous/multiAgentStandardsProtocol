"""
Real-Time Monitoring Dashboard
Visualize autonomous agent operations in real-time with WebSocket streaming
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import uuid


class EventType(Enum):
    """Types of dashboard events"""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    METRIC_UPDATE = "metric_update"
    DISCOVERY_EVENT = "discovery_event"
    REPUTATION_UPDATE = "reputation_update"
    CONTRACT_EVENT = "contract_event"
    SYSTEM_ALERT = "system_alert"


@dataclass
class DashboardEvent:
    """Dashboard event for real-time streaming"""
    event_id: str
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "severity": self.severity
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @staticmethod
    def agent_started(agent_id: str, agent_name: str, task: str) -> 'DashboardEvent':
        """Create agent started event"""
        return DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_STARTED,
            timestamp=datetime.now().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task": task
            },
            severity="info"
        )

    @staticmethod
    def agent_completed(agent_id: str, agent_name: str, task: str,
                       duration_ms: float, success: bool) -> 'DashboardEvent':
        """Create agent completed event"""
        return DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_COMPLETED,
            timestamp=datetime.now().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task": task,
                "duration_ms": duration_ms,
                "success": success
            },
            severity="info" if success else "error"
        )

    @staticmethod
    def workflow_started(workflow_id: str, workflow_name: str,
                        total_tasks: int) -> 'DashboardEvent':
        """Create workflow started event"""
        return DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_STARTED,
            timestamp=datetime.now().isoformat(),
            data={
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "total_tasks": total_tasks
            },
            severity="info"
        )

    @staticmethod
    def workflow_completed(workflow_id: str, workflow_name: str,
                          duration_seconds: float, tasks_completed: int,
                          tasks_failed: int, total_cost: float) -> 'DashboardEvent':
        """Create workflow completed event"""
        success = tasks_failed == 0
        return DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_COMPLETED,
            timestamp=datetime.now().isoformat(),
            data={
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "duration_seconds": duration_seconds,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "total_cost": total_cost,
                "success": success
            },
            severity="info" if success else "warning"
        )

    @staticmethod
    def metric_update(metric_name: str, value: float, unit: str = "") -> 'DashboardEvent':
        """Create metric update event"""
        return DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.METRIC_UPDATE,
            timestamp=datetime.now().isoformat(),
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit
            },
            severity="info"
        )


@dataclass
class DashboardMetrics:
    """Aggregate metrics for dashboard"""
    total_agents: int = 0
    active_agents: int = 0
    total_workflows: int = 0
    active_workflows: int = 0
    workflows_completed: int = 0
    workflows_failed: int = 0
    total_tasks_executed: int = 0
    total_tasks_succeeded: int = 0
    total_tasks_failed: int = 0
    total_cost: float = 0.0
    avg_task_duration_ms: float = 0.0
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class DashboardEventBus:
    """Event bus for broadcasting dashboard events"""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()
        self.event_history: List[DashboardEvent] = []
        self.max_history = 1000
        self.metrics = DashboardMetrics()
        self.start_time = datetime.now()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to dashboard events"""
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from dashboard events"""
        self.subscribers.discard(queue)

    async def publish(self, event: DashboardEvent):
        """Publish event to all subscribers"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Update metrics based on event type
        self._update_metrics(event)

        # Broadcast to all subscribers
        dead_queues = set()
        for queue in self.subscribers:
            try:
                await asyncio.wait_for(queue.put(event), timeout=0.1)
            except asyncio.TimeoutError:
                # Queue is full or slow, mark for removal
                dead_queues.add(queue)
            except Exception:
                dead_queues.add(queue)

        # Remove dead queues
        for queue in dead_queues:
            self.subscribers.discard(queue)

    def _update_metrics(self, event: DashboardEvent):
        """Update metrics based on event"""
        if event.event_type == EventType.AGENT_STARTED:
            self.metrics.active_agents += 1

        elif event.event_type == EventType.AGENT_COMPLETED:
            self.metrics.active_agents = max(0, self.metrics.active_agents - 1)
            self.metrics.total_tasks_executed += 1
            if event.data.get("success", False):
                self.metrics.total_tasks_succeeded += 1
            else:
                self.metrics.total_tasks_failed += 1

        elif event.event_type == EventType.WORKFLOW_STARTED:
            self.metrics.total_workflows += 1
            self.metrics.active_workflows += 1

        elif event.event_type == EventType.WORKFLOW_COMPLETED:
            self.metrics.active_workflows = max(0, self.metrics.active_workflows - 1)
            if event.data.get("success", False):
                self.metrics.workflows_completed += 1
            else:
                self.metrics.workflows_failed += 1
            self.metrics.total_cost += event.data.get("total_cost", 0.0)

        # Update uptime
        self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent events"""
        return [event.to_dict() for event in self.event_history[-count:]]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.to_dict()


# Global event bus instance
_event_bus: Optional[DashboardEventBus] = None


def get_event_bus() -> DashboardEventBus:
    """Get global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = DashboardEventBus()
    return _event_bus


class RealtimeDashboard:
    """Real-time monitoring dashboard coordinator"""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.active_connections: Set[Any] = set()

    async def broadcast_agent_execution(self, agent_id: str, agent_name: str,
                                       task: str, duration_ms: float, success: bool):
        """Broadcast agent execution event"""
        # Started event
        await self.event_bus.publish(
            DashboardEvent.agent_started(agent_id, agent_name, task)
        )

        # Simulate execution (in real usage, this would be actual execution)
        await asyncio.sleep(duration_ms / 1000.0)

        # Completed event
        await self.event_bus.publish(
            DashboardEvent.agent_completed(agent_id, agent_name, task, duration_ms, success)
        )

    async def broadcast_workflow_execution(self, workflow_id: str, workflow_name: str,
                                          total_tasks: int, duration_seconds: float,
                                          tasks_completed: int, tasks_failed: int,
                                          total_cost: float):
        """Broadcast workflow execution events"""
        # Started event
        await self.event_bus.publish(
            DashboardEvent.workflow_started(workflow_id, workflow_name, total_tasks)
        )

        # Simulate execution
        await asyncio.sleep(duration_seconds)

        # Completed event
        await self.event_bus.publish(
            DashboardEvent.workflow_completed(
                workflow_id, workflow_name, duration_seconds,
                tasks_completed, tasks_failed, total_cost
            )
        )

    async def stream_events(self):
        """Stream events to WebSocket (generator for async iteration)"""
        queue = self.event_bus.subscribe()
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self.event_bus.unsubscribe(queue)

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Get current dashboard state"""
        return {
            "metrics": self.event_bus.get_metrics(),
            "recent_events": self.event_bus.get_recent_events(50),
            "timestamp": datetime.now().isoformat()
        }


# Global dashboard instance
_dashboard: Optional[RealtimeDashboard] = None


def get_dashboard() -> RealtimeDashboard:
    """Get global dashboard instance"""
    global _dashboard
    if _dashboard is None:
        _dashboard = RealtimeDashboard()
    return _dashboard
