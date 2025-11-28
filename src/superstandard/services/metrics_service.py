"""
Real-time Metrics Service
=========================

Collects and exposes metrics for the agent platform:
- Agent execution metrics
- AI processing statistics
- Workflow orchestration tracking
- System health indicators
- Performance trends

Provides real-time observability into platform operations.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import logging


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels
        }


@dataclass
class MetricSeries:
    """Time series of metric points"""
    name: str
    points: List[MetricPoint] = field(default_factory=list)
    max_points: int = 1000

    def add(self, value: float, labels: Optional[Dict[str, str]] = None):
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
        # Keep only recent points
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points:]

    def get_recent(self, minutes: int = 60) -> List[MetricPoint]:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [p for p in self.points if p.timestamp > cutoff]

    def get_stats(self, minutes: int = 60) -> Dict[str, Any]:
        recent = self.get_recent(minutes)
        if not recent:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "sum": 0}

        values = [p.value for p in recent]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values)
        }


class MetricsService:
    """
    Real-time Metrics Collection Service

    Collects and provides metrics for:
    - Agent executions (count, duration, success rate)
    - AI processing (calls, latency, domains)
    - Orchestration (workflows, steps, duration)
    - System health (errors, memory, throughput)
    """

    def __init__(self):
        self.logger = logging.getLogger("MetricsService")
        self._lock = threading.Lock()

        # Counters
        self.counters: Dict[str, int] = defaultdict(int)

        # Gauges (current values)
        self.gauges: Dict[str, float] = {}

        # Time series
        self.series: Dict[str, MetricSeries] = {}

        # Event log
        self.events: List[Dict[str, Any]] = []
        self.max_events = 500

        # Initialize default metrics
        self._init_default_metrics()

        self.logger.info("MetricsService initialized")

    def _init_default_metrics(self):
        """Initialize default metric series"""
        default_series = [
            "agent_executions",
            "agent_duration_ms",
            "ai_processing_calls",
            "ai_processing_duration_ms",
            "orchestration_executions",
            "orchestration_steps",
            "errors",
            "api_requests",
            "api_latency_ms"
        ]
        for name in default_series:
            self.series[name] = MetricSeries(name=name)

    # =========================================================================
    # Counter Methods
    # =========================================================================

    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value

            # Also record in time series
            if name in self.series:
                self.series[name].add(value, labels)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0)

    # =========================================================================
    # Gauge Methods
    # =========================================================================

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)

    # =========================================================================
    # Time Series Methods
    # =========================================================================

    def record(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a value in a time series"""
        with self._lock:
            if name not in self.series:
                self.series[name] = MetricSeries(name=name)
            self.series[name].add(value, labels)

    def get_series(self, name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get time series data"""
        if name not in self.series:
            return []
        return [p.to_dict() for p in self.series[name].get_recent(minutes)]

    def get_series_stats(self, name: str, minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a time series"""
        if name not in self.series:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "sum": 0}
        return self.series[name].get_stats(minutes)

    # =========================================================================
    # Event Logging
    # =========================================================================

    def log_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """Log an event"""
        with self._lock:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "message": message,
                "severity": severity,
                "data": data or {}
            }
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

    def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent events"""
        events = self.events
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return events[-limit:]

    # =========================================================================
    # High-Level Tracking Methods
    # =========================================================================

    def track_agent_execution(
        self,
        agent_id: str,
        duration_ms: float,
        success: bool,
        domain: str = "unknown"
    ):
        """Track an agent execution"""
        self.increment("agent_executions", labels={"agent_id": agent_id, "domain": domain})
        self.record("agent_duration_ms", duration_ms, {"agent_id": agent_id})

        if success:
            self.increment("agent_executions_success", labels={"domain": domain})
        else:
            self.increment("agent_executions_failed", labels={"domain": domain})
            self.increment("errors", labels={"type": "agent_execution"})

        self.log_event(
            "agent_execution",
            f"Agent {agent_id} executed in {duration_ms:.0f}ms",
            "info" if success else "warning",
            {"agent_id": agent_id, "duration_ms": duration_ms, "success": success, "domain": domain}
        )

    def track_ai_processing(
        self,
        domain: str,
        task_type: str,
        duration_ms: float,
        success: bool
    ):
        """Track AI processing call"""
        self.increment("ai_processing_calls", labels={"domain": domain, "task_type": task_type})
        self.record("ai_processing_duration_ms", duration_ms, {"domain": domain})

        if not success:
            self.increment("errors", labels={"type": "ai_processing"})

        self.log_event(
            "ai_processing",
            f"AI {domain}/{task_type} completed in {duration_ms:.0f}ms",
            "info" if success else "warning",
            {"domain": domain, "task_type": task_type, "duration_ms": duration_ms}
        )

    def track_orchestration(
        self,
        workflow_id: str,
        workflow_name: str,
        steps_total: int,
        steps_completed: int,
        duration_ms: float,
        status: str
    ):
        """Track workflow orchestration"""
        self.increment("orchestration_executions", labels={"status": status})
        self.record("orchestration_steps", steps_completed)
        self.record("orchestration_duration_ms", duration_ms)

        if status == "failed":
            self.increment("errors", labels={"type": "orchestration"})

        self.log_event(
            "orchestration",
            f"Workflow '{workflow_name}' {status}: {steps_completed}/{steps_total} steps in {duration_ms:.0f}ms",
            "info" if status == "completed" else "warning",
            {"workflow_id": workflow_id, "steps": steps_completed, "total": steps_total}
        )

    def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float
    ):
        """Track API request"""
        self.increment("api_requests", labels={"endpoint": endpoint, "method": method})
        self.record("api_latency_ms", duration_ms, {"endpoint": endpoint})

        if status_code >= 400:
            self.increment("errors", labels={"type": "api", "status": str(status_code)})

    # =========================================================================
    # Summary Methods
    # =========================================================================

    def get_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "period_minutes": minutes,
            "counters": {
                "agent_executions": self.get_counter("agent_executions"),
                "agent_executions_success": self.get_counter("agent_executions_success"),
                "agent_executions_failed": self.get_counter("agent_executions_failed"),
                "ai_processing_calls": self.get_counter("ai_processing_calls"),
                "orchestration_executions": self.get_counter("orchestration_executions"),
                "api_requests": self.get_counter("api_requests"),
                "errors": self.get_counter("errors")
            },
            "statistics": {
                "agent_duration": self.get_series_stats("agent_duration_ms", minutes),
                "ai_processing_duration": self.get_series_stats("ai_processing_duration_ms", minutes),
                "orchestration_duration": self.get_series_stats("orchestration_duration_ms", minutes),
                "api_latency": self.get_series_stats("api_latency_ms", minutes)
            },
            "health": self._calculate_health(),
            "recent_events": self.get_events(limit=10)
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data formatted for dashboard display"""
        summary = self.get_summary(60)

        # Calculate rates
        total_executions = summary["counters"]["agent_executions"]
        successful = summary["counters"]["agent_executions_success"]
        success_rate = (successful / total_executions * 100) if total_executions > 0 else 100

        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_agent_executions": total_executions,
                "success_rate_percent": round(success_rate, 1),
                "ai_processing_calls": summary["counters"]["ai_processing_calls"],
                "orchestrations": summary["counters"]["orchestration_executions"],
                "total_errors": summary["counters"]["errors"]
            },
            "performance": {
                "avg_agent_duration_ms": round(summary["statistics"]["agent_duration"]["avg"], 1),
                "avg_ai_duration_ms": round(summary["statistics"]["ai_processing_duration"]["avg"], 1),
                "avg_api_latency_ms": round(summary["statistics"]["api_latency"]["avg"], 1)
            },
            "health": summary["health"],
            "recent_events": summary["recent_events"],
            "time_series": {
                "agent_executions": self.get_series("agent_executions", 60),
                "errors": self.get_series("errors", 60)
            }
        }

    def _calculate_health(self) -> Dict[str, Any]:
        """Calculate system health indicators"""
        total = self.get_counter("agent_executions")
        errors = self.get_counter("errors")

        error_rate = (errors / total * 100) if total > 0 else 0

        if error_rate < 1:
            status = "healthy"
            score = 100
        elif error_rate < 5:
            status = "degraded"
            score = 80
        elif error_rate < 10:
            status = "warning"
            score = 60
        else:
            status = "critical"
            score = max(0, 100 - error_rate * 5)

        return {
            "status": status,
            "score": round(score, 1),
            "error_rate_percent": round(error_rate, 2),
            "indicators": {
                "agent_processing": "ok" if self.get_counter("agent_executions_failed") == 0 else "warning",
                "ai_services": "ok",
                "orchestration": "ok" if self.get_counter("orchestration_executions") >= 0 else "unknown"
            }
        }

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key from name and labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def reset(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            for series in self.series.values():
                series.points.clear()
            self.events.clear()
            self._init_default_metrics()


# Global instance
metrics_service = MetricsService()


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance"""
    return metrics_service


# Convenience functions
def track_agent(agent_id: str, duration_ms: float, success: bool, domain: str = "unknown"):
    """Track agent execution"""
    metrics_service.track_agent_execution(agent_id, duration_ms, success, domain)


def track_ai(domain: str, task_type: str, duration_ms: float, success: bool = True):
    """Track AI processing"""
    metrics_service.track_ai_processing(domain, task_type, duration_ms, success)


def track_workflow(workflow_id: str, name: str, steps: int, completed: int, duration_ms: float, status: str):
    """Track workflow orchestration"""
    metrics_service.track_orchestration(workflow_id, name, steps, completed, duration_ms, status)
