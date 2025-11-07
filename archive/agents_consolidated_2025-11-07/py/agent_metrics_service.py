"""
Real-Time Agent Metrics Service

Connects to live agent ecosystem and provides real-time metrics
for dashboard visualization and investor demonstrations.

Features:
- Live agent activity tracking
- Protocol usage monitoring (A2A, A2P, ACP, ANP, MCP)
- Performance metrics aggregation
- Business impact calculations
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import random


@dataclass
class AgentMetric:
    """Real-time agent performance metric"""

    agent_id: str
    agent_type: str
    status: str  # active, idle, communicating, learning
    messages_sent: int
    messages_received: int
    tasks_completed: int
    tasks_failed: int
    avg_response_time_ms: float
    protocols_used: List[str]
    current_task: Optional[str]
    uptime_seconds: float
    earnings: float  # A2P earnings
    reputation_score: float
    last_activity: str


@dataclass
class ProtocolMetric:
    """Protocol usage statistics"""

    protocol: str  # A2A, A2P, ACP, ANP, MCP
    messages_count: int
    success_rate: float
    avg_latency_ms: float
    total_value: float  # For A2P
    active_agents: int


@dataclass
class SwarmMetric:
    """Swarm-level performance metrics"""

    swarm_id: str
    swarm_type: str
    agent_count: int
    total_messages: int
    consensus_reached: int
    coordination_events: int
    business_value: float
    efficiency_score: float


@dataclass
class BusinessImpact:
    """Business impact calculations"""

    total_tasks_automated: int
    cost_savings: float
    time_savings_hours: float
    revenue_generated: float
    roi_percentage: float
    customer_satisfaction: float


class AgentMetricsService:
    """
    Aggregates and serves real-time metrics from the agent ecosystem
    """

    def __init__(self):
        # In-memory storage for real-time metrics
        self.agent_metrics: Dict[str, AgentMetric] = {}
        self.protocol_metrics: Dict[str, ProtocolMetric] = {}
        self.swarm_metrics: Dict[str, SwarmMetric] = {}
        self.business_impact = BusinessImpact(
            total_tasks_automated=0,
            cost_savings=0.0,
            time_savings_hours=0.0,
            revenue_generated=0.0,
            roi_percentage=0.0,
            customer_satisfaction=95.0,
        )

        # Message history for activity feed
        self.message_history: List[Dict] = []
        self.max_history = 100

        # Performance tracking
        self.start_time = datetime.now()
        self.total_agent_spawns = 0
        self.total_protocol_messages = 0

    def register_agent(self, agent_id: str, agent_type: str):
        """Register a new agent in the metrics system"""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetric(
                agent_id=agent_id,
                agent_type=agent_type,
                status="idle",
                messages_sent=0,
                messages_received=0,
                tasks_completed=0,
                tasks_failed=0,
                avg_response_time_ms=0.0,
                protocols_used=[],
                current_task=None,
                uptime_seconds=0.0,
                earnings=0.0,
                reputation_score=100.0,
                last_activity=datetime.now().isoformat(),
            )
            self.total_agent_spawns += 1

    def update_agent_status(self, agent_id: str, status: str, current_task: Optional[str] = None):
        """Update agent status"""
        if agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].status = status
            self.agent_metrics[agent_id].current_task = current_task
            self.agent_metrics[agent_id].last_activity = datetime.now().isoformat()

    def record_message(
        self,
        from_agent: str,
        to_agent: str,
        protocol: str,
        message_type: str,
        success: bool = True,
        latency_ms: float = 0.0,
        value: float = 0.0,
    ):
        """Record a protocol message between agents"""

        # Update agent metrics
        if from_agent in self.agent_metrics:
            self.agent_metrics[from_agent].messages_sent += 1
            if protocol not in self.agent_metrics[from_agent].protocols_used:
                self.agent_metrics[from_agent].protocols_used.append(protocol)

        if to_agent in self.agent_metrics:
            self.agent_metrics[to_agent].messages_received += 1

        # Update protocol metrics
        if protocol not in self.protocol_metrics:
            self.protocol_metrics[protocol] = ProtocolMetric(
                protocol=protocol,
                messages_count=0,
                success_rate=100.0,
                avg_latency_ms=0.0,
                total_value=0.0,
                active_agents=0,
            )

        pm = self.protocol_metrics[protocol]
        pm.messages_count += 1
        pm.avg_latency_ms = (
            pm.avg_latency_ms * (pm.messages_count - 1) + latency_ms
        ) / pm.messages_count
        pm.total_value += value

        # Add to message history
        self.message_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "from": from_agent,
                "to": to_agent,
                "protocol": protocol,
                "type": message_type,
                "success": success,
                "latency_ms": latency_ms,
                "value": value,
            }
        )

        # Trim history
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history :]

        self.total_protocol_messages += 1

    def record_task_completion(self, agent_id: str, success: bool, response_time_ms: float):
        """Record task completion"""
        if agent_id in self.agent_metrics:
            metric = self.agent_metrics[agent_id]
            if success:
                metric.tasks_completed += 1
                self.business_impact.total_tasks_automated += 1
            else:
                metric.tasks_failed += 1

            # Update average response time
            total_tasks = metric.tasks_completed + metric.tasks_failed
            metric.avg_response_time_ms = (
                metric.avg_response_time_ms * (total_tasks - 1) + response_time_ms
            ) / total_tasks

    def record_agent_earnings(self, agent_id: str, amount: float):
        """Record A2P earnings for an agent"""
        if agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].earnings += amount
            self.business_impact.revenue_generated += amount

    def get_live_metrics(self) -> Dict[str, Any]:
        """Get comprehensive live metrics snapshot"""

        # Calculate active agents
        active_agents = [
            a
            for a in self.agent_metrics.values()
            if a.status in ["active", "working", "communicating"]
        ]

        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        # Calculate business metrics
        total_earnings = sum(a.earnings for a in self.agent_metrics.values())
        avg_reputation = (
            sum(a.reputation_score for a in self.agent_metrics.values()) / len(self.agent_metrics)
            if self.agent_metrics
            else 0
        )

        # Calculate estimated cost savings (based on manual labor cost)
        manual_cost_per_task = 15.0  # Average $15 per manual task
        self.business_impact.cost_savings = (
            self.business_impact.total_tasks_automated * manual_cost_per_task
        )

        # Calculate time savings (assume each task saves 30 minutes)
        self.business_impact.time_savings_hours = self.business_impact.total_tasks_automated * 0.5

        # Calculate ROI
        if total_earnings > 0:
            self.business_impact.roi_percentage = (
                self.business_impact.cost_savings / total_earnings
            ) * 100

        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "uptime_seconds": uptime_seconds,
                "total_agents": len(self.agent_metrics),
                "active_agents": len(active_agents),
                "total_messages": self.total_protocol_messages,
                "agents_spawned": self.total_agent_spawns,
            },
            "agents": [
                asdict(a) for a in list(self.agent_metrics.values())[:50]
            ],  # Limit for performance
            "protocols": [asdict(p) for p in self.protocol_metrics.values()],
            "business_impact": asdict(self.business_impact),
            "recent_activity": self.message_history[-20:],  # Last 20 messages
            "performance": {
                "total_tasks": self.business_impact.total_tasks_automated,
                "success_rate": self._calculate_success_rate(),
                "avg_response_time": self._calculate_avg_response_time(),
                "total_earnings": total_earnings,
                "avg_reputation": avg_reputation,
            },
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_completed = sum(a.tasks_completed for a in self.agent_metrics.values())
        total_failed = sum(a.tasks_failed for a in self.agent_metrics.values())
        total = total_completed + total_failed
        return (total_completed / total) * 100 if total > 0 else 100.0

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time across all agents"""
        if not self.agent_metrics:
            return 0.0

        total_time = sum(a.avg_response_time_ms for a in self.agent_metrics.values())
        return total_time / len(self.agent_metrics)

    def get_protocol_usage(self) -> Dict[str, Any]:
        """Get protocol-specific usage statistics"""
        return {
            "protocols": {
                protocol: {
                    "messages": metric.messages_count,
                    "success_rate": metric.success_rate,
                    "avg_latency_ms": metric.avg_latency_ms,
                    "total_value": metric.total_value,
                    "active_agents": metric.active_agents,
                }
                for protocol, metric in self.protocol_metrics.items()
            },
            "total_messages": self.total_protocol_messages,
        }

    def simulate_activity(self):
        """
        Generate simulated agent activity for demonstration purposes

        This creates realistic-looking agent interactions when
        no real agents are running.
        """

        # Simulate some agents if none exist
        if len(self.agent_metrics) < 10:
            agent_types = [
                "traffic_prediction",
                "matching_optimization",
                "route_discovery",
                "consensus",
                "task_assignment",
                "activity_tracker",
                "dashboard_orchestrator",
                "testing",
                "design",
                "qa",
            ]

            for i, agent_type in enumerate(agent_types):
                agent_id = f"{agent_type}_sim_{i:03d}"
                self.register_agent(agent_id, agent_type)

        # Simulate random activity
        agent_ids = list(self.agent_metrics.keys())
        if len(agent_ids) < 2:
            return

        # Random message exchange
        from_agent = random.choice(agent_ids)
        to_agent = random.choice([a for a in agent_ids if a != from_agent])
        protocol = random.choice(["A2A", "A2P", "ACP", "ANP", "MCP"])
        message_type = random.choice(["request", "response", "notification", "query"])

        self.record_message(
            from_agent=from_agent,
            to_agent=to_agent,
            protocol=protocol,
            message_type=message_type,
            success=random.random() > 0.05,  # 95% success rate
            latency_ms=random.uniform(10, 100),
            value=random.uniform(0, 10) if protocol == "A2P" else 0.0,
        )

        # Random status updates
        for agent_id in random.sample(agent_ids, min(3, len(agent_ids))):
            status = random.choice(["active", "working", "communicating", "idle"])
            task = random.choice(
                [
                    "Optimizing routes",
                    "Analyzing traffic",
                    "Matching riders",
                    "Coordinating handoff",
                    "Running consensus",
                    "Tracking activity",
                    None,
                ]
            )
            self.update_agent_status(agent_id, status, task)

        # Random task completions
        if random.random() > 0.7:
            agent_id = random.choice(agent_ids)
            self.record_task_completion(
                agent_id=agent_id,
                success=random.random() > 0.1,  # 90% success
                response_time_ms=random.uniform(50, 500),
            )

        # Random earnings (A2P)
        if random.random() > 0.8:
            agent_id = random.choice(agent_ids)
            self.record_agent_earnings(agent_id, random.uniform(0.1, 5.0))


# Global service instance
_metrics_service: Optional[AgentMetricsService] = None


def get_metrics_service() -> AgentMetricsService:
    """Get or create the global metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = AgentMetricsService()
    return _metrics_service


async def metrics_simulation_loop():
    """
    Background task that generates simulated metrics
    for demonstration purposes
    """
    service = get_metrics_service()

    while True:
        try:
            service.simulate_activity()
            await asyncio.sleep(2)  # Update every 2 seconds
        except Exception as e:
            print(f"Error in metrics simulation: {e}")
            await asyncio.sleep(5)
