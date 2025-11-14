"""
Real-Time Dashboard State and Event Broadcasting

This module provides the core infrastructure for real-time monitoring and
visualization of the autonomous agent system.

Features:
- Event broadcasting to connected clients
- Dashboard state management
- Event history buffering
- Metrics aggregation
- WebSocket support (when integrated with web framework)

Events Broadcast:
- agent_execution_started
- agent_execution_completed
- opportunity_discovered
- synthesis_started
- quality_score_updated
- error_occurred
- system_health_updated
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class EventType(Enum):
    """Types of events broadcast by the dashboard."""

    AGENT_EXECUTION_STARTED = "agent_execution_started"
    AGENT_EXECUTION_COMPLETED = "agent_execution_completed"
    OPPORTUNITY_DISCOVERED = "opportunity_discovered"
    SYNTHESIS_STARTED = "synthesis_started"
    SYNTHESIS_COMPLETED = "synthesis_completed"
    QUALITY_SCORE_UPDATED = "quality_score_updated"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_HEALTH_UPDATED = "system_health_updated"
    AGENT_REGISTERED = "agent_registered"
    METRICS_UPDATED = "metrics_updated"
    REPUTATION_UPDATED = "reputation_updated"  # NEW: Reputation change event
    TASK_OUTCOME_RECORDED = "task_outcome_recorded"  # NEW: Task execution outcome


@dataclass
class DashboardEvent:
    """Represents a real-time dashboard event."""

    event_id: str
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    severity: str = "info"  # info, warning, error, success

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "severity": self.severity
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class DashboardState:
    """
    Manages real-time dashboard state and event broadcasting.

    This is the central hub for all real-time monitoring. Agents and
    orchestrators emit events here, which are then broadcast to all
    connected dashboard clients.
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize dashboard state.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self.max_history = max_history
        self.event_history: List[DashboardEvent] = []
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.opportunities: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "total_agents_executed": 0,
            "total_opportunities_discovered": 0,
            "total_events": 0,
            "avg_quality_score": 0.0,
            "system_uptime_seconds": 0
        }

        # WebSocket connections (in real implementation, would use actual WebSocket library)
        self.subscribers: Set[Any] = set()

        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.utcnow()

    async def broadcast_event(self, event: DashboardEvent):
        """
        Broadcast event to all connected clients and add to history.

        Args:
            event: Dashboard event to broadcast
        """
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Update metrics
        self.metrics["total_events"] += 1

        # Log event
        log_method = {
            "info": self.logger.info,
            "warning": self.logger.warning,
            "error": self.logger.error,
            "success": self.logger.info
        }.get(event.severity, self.logger.info)

        log_method(f"📡 Dashboard Event: {event.event_type.value} - {event.data.get('description', '')}")

        # Broadcast to all subscribers (in real implementation)
        # For now, just store for retrieval
        for subscriber in self.subscribers:
            try:
                # await subscriber.send(event.to_json())
                pass  # Placeholder for actual WebSocket send
            except Exception as e:
                self.logger.error(f"Failed to send event to subscriber: {e}")

    async def agent_started(
        self,
        agent_id: str,
        agent_name: str,
        task_description: str,
        **kwargs
    ):
        """Broadcast agent execution started event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_EXECUTION_STARTED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task_description": task_description,
                "description": f"Agent {agent_name} started: {task_description}",
                **kwargs
            },
            severity="info"
        )

        # Track active agent
        self.active_agents[agent_id] = {
            "agent_name": agent_name,
            "status": "running",
            "started_at": event.timestamp
        }

        await self.broadcast_event(event)

    async def agent_completed(
        self,
        agent_id: str,
        agent_name: str,
        task_description: str,
        duration_ms: float,
        success: bool,
        data_source: Optional[str] = None,
        quality_score: Optional[float] = None,
        **kwargs
    ):
        """Broadcast agent execution completed event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_EXECUTION_COMPLETED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task_description": task_description,
                "duration_ms": duration_ms,
                "success": success,
                "data_source": data_source,
                "quality_score": quality_score,
                "description": f"Agent {agent_name} {'completed' if success else 'failed'} in {duration_ms:.0f}ms",
                **kwargs
            },
            severity="success" if success else "error"
        )

        # Update active agent
        if agent_id in self.active_agents:
            self.active_agents[agent_id]["status"] = "completed" if success else "failed"
            self.active_agents[agent_id]["completed_at"] = event.timestamp
            self.active_agents[agent_id]["duration_ms"] = duration_ms

        # Update metrics
        self.metrics["total_agents_executed"] += 1
        if quality_score:
            current_avg = self.metrics["avg_quality_score"]
            total = self.metrics["total_agents_executed"]
            self.metrics["avg_quality_score"] = (current_avg * (total - 1) + quality_score) / total

        await self.broadcast_event(event)

    async def opportunity_discovered(
        self,
        opportunity_id: str,
        title: str,
        description: str,
        confidence_score: float,
        revenue_potential: str,
        category: str,
        **kwargs
    ):
        """Broadcast opportunity discovered event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.OPPORTUNITY_DISCOVERED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "opportunity_id": opportunity_id,
                "title": title,
                "description": description,
                "confidence_score": confidence_score,
                "revenue_potential": revenue_potential,
                "category": category,
                **kwargs
            },
            severity="success"
        )

        # Store opportunity
        self.opportunities.append(event.data)
        self.metrics["total_opportunities_discovered"] += 1

        await self.broadcast_event(event)

    async def synthesis_started(self, phase: str, description: str, **kwargs):
        """Broadcast synthesis phase started event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYNTHESIS_STARTED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "phase": phase,
                "description": description,
                **kwargs
            },
            severity="info"
        )

        await self.broadcast_event(event)

    async def synthesis_completed(
        self,
        phase: str,
        duration_ms: float,
        patterns_found: int,
        **kwargs
    ):
        """Broadcast synthesis phase completed event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYNTHESIS_COMPLETED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "phase": phase,
                "duration_ms": duration_ms,
                "patterns_found": patterns_found,
                "description": f"Synthesis completed: {patterns_found} patterns found",
                **kwargs
            },
            severity="success"
        )

        await self.broadcast_event(event)

    async def quality_score_updated(
        self,
        source: str,
        overall_score: float,
        dimension_scores: Dict[str, float],
        **kwargs
    ):
        """Broadcast quality score update event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.QUALITY_SCORE_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "source": source,
                "overall_score": overall_score,
                "dimension_scores": dimension_scores,
                "description": f"Quality score: {overall_score:.1f}%",
                **kwargs
            },
            severity="success" if overall_score >= 95 else "warning" if overall_score >= 90 else "error"
        )

        await self.broadcast_event(event)

    async def error_occurred(
        self,
        source: str,
        error_message: str,
        error_type: str,
        **kwargs
    ):
        """Broadcast error event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ERROR_OCCURRED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "source": source,
                "error_message": error_message,
                "error_type": error_type,
                "description": f"Error in {source}: {error_message}",
                **kwargs
            },
            severity="error"
        )

        await self.broadcast_event(event)

    async def system_health_updated(
        self,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        active_agents: int = 0,
        **kwargs
    ):
        """Broadcast system health update event."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        self.metrics["system_uptime_seconds"] = uptime

        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_HEALTH_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "active_agents": active_agents,
                "uptime_seconds": uptime,
                "description": f"System health: {active_agents} active agents, {uptime:.0f}s uptime",
                **kwargs
            },
            severity="info"
        )

        await self.broadcast_event(event)

    async def reputation_updated(
        self,
        agent_id: str,
        agent_name: str,
        old_score: float,
        new_score: float,
        total_tasks: int,
        trend: str,
        **kwargs
    ):
        """Broadcast reputation update event."""
        change = new_score - old_score
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.REPUTATION_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "old_score": old_score,
                "new_score": new_score,
                "change": change,
                "total_tasks": total_tasks,
                "trend": trend,
                "description": f"{agent_name} reputation: {new_score:.1%} ({'+' if change >= 0 else ''}{change:.1%} change, {trend})",
                **kwargs
            },
            severity="success" if change >= 0 else "warning"
        )

        await self.broadcast_event(event)

    async def task_outcome_recorded(
        self,
        agent_id: str,
        agent_name: str,
        task_id: str,
        success: bool,
        quality_score: Optional[float] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """Broadcast task outcome recorded event."""
        event = DashboardEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.TASK_OUTCOME_RECORDED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "task_id": task_id,
                "success": success,
                "quality_score": quality_score,
                "duration_ms": duration_ms,
                "description": f"{agent_name} {'✅ completed' if success else '❌ failed'} task {task_id}",
                **kwargs
            },
            severity="success" if success else "error"
        )

        await self.broadcast_event(event)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get current dashboard statistics."""
        return {
            "metrics": self.metrics,
            "active_agents": len([a for a in self.active_agents.values() if a["status"] == "running"]),
            "total_opportunities": len(self.opportunities),
            "recent_events": len(self.event_history),
            "system_uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events."""
        events = self.event_history[-limit:]
        return [e.to_dict() for e in reversed(events)]

    def get_opportunities(self) -> List[Dict[str, Any]]:
        """Get all discovered opportunities."""
        return self.opportunities


# Global dashboard instance
_dashboard_instance: Optional[DashboardState] = None


def get_dashboard() -> DashboardState:
    """Get or create the global dashboard instance."""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = DashboardState()
    return _dashboard_instance


__all__ = ['DashboardState', 'DashboardEvent', 'EventType', 'get_dashboard']
