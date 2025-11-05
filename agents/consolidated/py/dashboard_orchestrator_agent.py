"""
Dashboard Orchestrator Agent - Meta-Agent for UI Coordination

This agent coordinates data flow between the agent ecosystem and dashboards.
It aggregates metrics, formats data for visualization, and manages real-time updates.

Category: Meta-Agent (UI Coordination & Presentation)
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentCapability


@dataclass
class DashboardState:
    """Current dashboard state"""
    active_agents: List[Dict]
    recent_activities: List[Dict]
    system_metrics: Dict
    agent_network: Dict
    business_impact: Dict
    alerts: List[Dict]
    last_updated: datetime


class DashboardOrchestratorAgent(BaseAgent):
    """
    Meta-agent that orchestrates dashboard data flow

    Responsibilities:
    - Aggregate agent metrics for visualization
    - Format data for different dashboard views
    - Manage WebSocket broadcasts
    - Generate business impact calculations
    - Coordinate between multiple data sources
    """

    def __init__(
        self,
        agent_id: str = "dashboard_orchestrator_001",
        workspace_path: str = "./autonomous-ecosystem/workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="dashboard_orchestrator",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Dashboard state
        self.current_state: Optional[DashboardState] = None
        self.websocket_clients: Set = set()

        # Data sources (injected)
        self.activity_tracker = None
        self.agent_factory = None

        # Cached data
        self.cached_network_graph = None
        self.cache_timestamp = None
        self.cache_ttl = 5  # seconds

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dashboard coordination task"""
        task_type = task.get("type")

        if task_type == "get_dashboard_state":
            return await self._get_dashboard_state()
        elif task_type == "get_agent_network":
            return await self._get_agent_network()
        elif task_type == "get_business_impact":
            return await self._get_business_impact()
        elif task_type == "get_agent_details":
            return await self._get_agent_details(task)
        elif task_type == "format_activity_feed":
            return await self._format_activity_feed(task)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dashboard requirements and optimize data flow"""
        return {
            "data_flow_optimizations": [
                "Cache network graph for 5 seconds",
                "Batch activity updates every 2 seconds",
                "Pre-compute business impact metrics"
            ],
            "recommendations": [
                "Use WebSocket for real-time activity feed",
                "Poll agent metrics every 3 seconds",
                "Lazy-load agent detail modals"
            ]
        }

    # =====================================================================
    # Dashboard State Management
    # =====================================================================

    async def _get_dashboard_state(self) -> Dict[str, Any]:
        """Get complete dashboard state"""
        try:
            # Get data from various sources
            active_agents = await self._get_active_agents()
            recent_activities = await self._get_recent_activities()
            system_metrics = await self._get_system_metrics()
            agent_network = await self._get_agent_network()
            business_impact = await self._get_business_impact()
            alerts = await self._get_alerts()

            state = DashboardState(
                active_agents=active_agents,
                recent_activities=recent_activities,
                system_metrics=system_metrics,
                agent_network=agent_network,
                business_impact=business_impact,
                alerts=alerts,
                last_updated=datetime.now()
            )

            self.current_state = state

            return {
                "success": True,
                "state": {
                    "active_agents": state.active_agents,
                    "recent_activities": state.recent_activities,
                    "system_metrics": state.system_metrics,
                    "agent_network": state.agent_network,
                    "business_impact": state.business_impact,
                    "alerts": state.alerts,
                    "last_updated": state.last_updated.isoformat()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_active_agents(self) -> List[Dict]:
        """Get list of active agents with summaries"""
        active_agents = []

        # Primary source: Get spawned agents from factory (shows all spawned agents)
        if self.agent_factory:
            factory_agents = self.agent_factory.list_active_agents()
            for agent in factory_agents:
                active_agents.append({
                    "agent_id": agent.get("agent_id"),
                    "agent_type": agent.get("agent_type", "unknown"),
                    "status": agent.get("status", "idle"),
                    "category": agent.get("category", "other"),
                    "name": agent.get("name", "Unknown Agent")
                })

        # Secondary source: Enrich with activity metrics if available
        if self.activity_tracker:
            metrics_result = await self.activity_tracker._get_agent_metrics({})
            if metrics_result.get("success"):
                metrics_by_id = metrics_result.get("metrics", {})

                # Update existing agents with activity metrics
                for agent in active_agents:
                    agent_id = agent["agent_id"]
                    if agent_id in metrics_by_id:
                        metrics = metrics_by_id[agent_id]
                        agent.update({
                            "tasks_completed": metrics.get("tasks_completed", 0),
                            "success_rate": metrics.get("success_rate", 0),
                            "last_activity": metrics.get("last_activity")
                        })

        return active_agents

    async def _get_recent_activities(self, limit: int = 50) -> List[Dict]:
        """Get recent activity feed"""
        if not self.activity_tracker:
            return []

        feed_result = await self.activity_tracker._get_activity_feed({"limit": limit})
        if not feed_result.get("success"):
            return []

        return feed_result.get("activities", [])

    async def _get_system_metrics(self) -> Dict:
        """Get system-wide metrics"""
        # Get count of spawned agents from factory
        total_agents = 0
        active_agents_count = 0
        if self.agent_factory:
            active_list = self.agent_factory.list_active_agents()
            total_agents = len(active_list)
            active_agents_count = total_agents  # All spawned agents are considered active

        # Enrich with activity metrics if available
        if self.activity_tracker:
            health_result = await self.activity_tracker._get_system_health({})
            if health_result.get("success"):
                health_data = health_result.get("health", {})
                # Override with factory counts (more accurate)
                health_data["total_agents"] = total_agents
                health_data["active_agents"] = active_agents_count
                return health_data

        # Fallback if no activity tracker
        return {
            "total_agents": total_agents,
            "active_agents": active_agents_count,
            "idle_agents": 0,
            "total_tasks": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "overall_success_rate": 0,
            "total_messages": 0,
            "total_errors": 0,
            "uptime_seconds": 0
        }

    async def _get_agent_network(self) -> Dict:
        """Get agent network graph (cached)"""
        # Check cache
        if self.cached_network_graph and self.cache_timestamp:
            if (datetime.now() - self.cache_timestamp).seconds < self.cache_ttl:
                return self.cached_network_graph

        # Build network graph
        if not self.activity_tracker:
            return {"nodes": [], "edges": []}

        # Get coordination patterns
        coord_result = await self.activity_tracker._get_coordination_patterns({})
        if not coord_result.get("success"):
            return {"nodes": [], "edges": []}

        # Build nodes from active agents
        metrics_result = await self.activity_tracker._get_agent_metrics({})
        nodes = []
        if metrics_result.get("success"):
            for agent_id, metrics in metrics_result.get("metrics", {}).items():
                nodes.append({
                    "id": agent_id,
                    "label": metrics.get("agent_type", "unknown"),
                    "type": metrics.get("agent_type", "unknown"),
                    "status": metrics.get("current_state", "idle"),
                    "category": self._get_agent_category(metrics.get("agent_type", ""))
                })

        # Build edges from collaborations
        edges = []
        for collab in coord_result.get("top_collaborations", [])[:50]:
            edges.append({
                "source": collab["from"],
                "target": collab["to"],
                "weight": collab["message_count"]
            })

        network = {"nodes": nodes, "edges": edges}

        # Cache it
        self.cached_network_graph = network
        self.cache_timestamp = datetime.now()

        return network

    async def _get_business_impact(self) -> Dict:
        """Calculate business impact metrics"""
        if not self.activity_tracker:
            return {
                "cost_savings": 0,
                "time_saved_hours": 0,
                "efficiency_gain_percent": 0,
                "co2_reduction_kg": 0
            }

        metrics = await self._get_system_metrics()

        # Business impact calculations
        active_agents = metrics.get("active_agents", 0)
        tasks_completed = metrics.get("tasks_completed", 0)
        success_rate = metrics.get("overall_success_rate", 0)

        # Estimates (would be customized per use case)
        cost_per_agent_hour = 150  # $150/hour saved per agent
        time_per_task_hours = 0.5  # 0.5 hours saved per task
        efficiency_base = 25  # 25% base efficiency gain
        co2_per_agent_kg = 2.5  # 2.5 kg CO2 saved per agent per hour

        uptime_hours = metrics.get("uptime_seconds", 0) / 3600

        return {
            "cost_savings": round(active_agents * cost_per_agent_hour * uptime_hours, 2),
            "time_saved_hours": round(tasks_completed * time_per_task_hours, 2),
            "efficiency_gain_percent": min(80, efficiency_base + (success_rate * 0.5)),
            "co2_reduction_kg": round(active_agents * co2_per_agent_kg * uptime_hours, 2),
            "tasks_automated": tasks_completed,
            "human_equivalent_hours": round(tasks_completed * time_per_task_hours, 2)
        }

    async def _get_alerts(self) -> List[Dict]:
        """Get system alerts and warnings"""
        if not self.activity_tracker:
            return []

        alerts = []

        # Analyze for bottlenecks
        analysis = self.activity_tracker._analyze_bottlenecks()
        for bottleneck in analysis.get("bottlenecks", []):
            alerts.append({
                "severity": bottleneck.get("severity", "medium"),
                "type": "bottleneck",
                "message": f"Agent {bottleneck['agent_id']}: {bottleneck['issue']}",
                "details": bottleneck,
                "timestamp": datetime.now().isoformat()
            })

        # Check for isolated agents
        coord_analysis = self.activity_tracker._analyze_coordination()
        if coord_analysis.get("isolated_agents", 0) > 0:
            alerts.append({
                "severity": "low",
                "type": "coordination",
                "message": f"{coord_analysis['isolated_agents']} agents are not coordinating",
                "details": {"isolated_ids": coord_analysis.get("isolated_agent_ids", [])},
                "timestamp": datetime.now().isoformat()
            })

        return alerts

    # =====================================================================
    # Detailed Views
    # =====================================================================

    async def _get_agent_details(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about specific agent"""
        agent_id = task.get("agent_id")
        if not agent_id:
            return {"success": False, "error": "agent_id required"}

        if not self.activity_tracker:
            return {"success": False, "error": "Activity tracker not available"}

        # Get metrics
        summary = self.activity_tracker.get_agent_summary(agent_id)
        if not summary:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        # Get recent activities for this agent
        activities_result = await self.activity_tracker._get_activity_feed({
            "agent_id": agent_id,
            "limit": 20
        })

        activities = activities_result.get("activities", []) if activities_result.get("success") else []

        # Get agent template info if available
        agent_info = {}
        if self.agent_factory:
            agent_type = summary.get("agent_type")
            details = self.agent_factory.get_agent_details(agent_type)
            if details:
                agent_info = details

        return {
            "success": True,
            "agent": {
                **summary,
                "recent_activities": activities,
                "template_info": agent_info
            }
        }

    async def _format_activity_feed(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format activity feed for specific dashboard view"""
        view_type = task.get("view_type", "timeline")
        limit = task.get("limit", 50)

        activities = await self._get_recent_activities(limit)

        if view_type == "timeline":
            return {
                "success": True,
                "format": "timeline",
                "activities": self._format_timeline(activities)
            }
        elif view_type == "grouped":
            return {
                "success": True,
                "format": "grouped",
                "groups": self._group_activities(activities)
            }
        elif view_type == "agent_centric":
            return {
                "success": True,
                "format": "agent_centric",
                "by_agent": self._group_by_agent(activities)
            }
        else:
            return {"success": False, "error": f"Unknown view type: {view_type}"}

    def _format_timeline(self, activities: List[Dict]) -> List[Dict]:
        """Format activities as timeline"""
        return [
            {
                "id": act["activity_id"],
                "timestamp": act["timestamp"],
                "title": f"{act['agent_type']}: {act['activity_type']}",
                "description": act["description"],
                "icon": self._get_activity_icon(act["activity_type"]),
                "color": self._get_activity_color(act["activity_type"]),
                "success": act.get("success")
            }
            for act in activities
        ]

    def _group_activities(self, activities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group activities by type"""
        grouped = defaultdict(list)
        for act in activities:
            grouped[act["activity_type"]].append(act)
        return dict(grouped)

    def _group_by_agent(self, activities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group activities by agent"""
        grouped = defaultdict(list)
        for act in activities:
            grouped[act["agent_id"]].append(act)
        return dict(grouped)

    # =====================================================================
    # Helper Methods
    # =====================================================================

    def _get_agent_category(self, agent_type: str) -> str:
        """Map agent type to category for visualization"""
        category_map = {
            "demand_predictor": "mobility",
            "traffic_analyzer": "mobility",
            "route_optimizer": "mobility",
            "matching_engine": "mobility",
            "fleet_coordinator": "mobility",
            "pricing_optimizer": "operations",
            "driver_incentive": "operations",
            "customer_support": "operations",
            "safety_monitor": "safety",
            "fraud_detection": "safety",
            "marketing_optimizer": "marketing",
            "analytics_reporter": "analytics",
            "activity_tracker": "meta",
            "dashboard_orchestrator": "meta"
        }
        return category_map.get(agent_type, "other")

    def _get_activity_icon(self, activity_type: str) -> str:
        """Get icon for activity type"""
        icon_map = {
            "spawned": "🚀",
            "task_started": "▶️",
            "task_completed": "✅",
            "task_failed": "❌",
            "decision_made": "🤔",
            "communication_sent": "📤",
            "communication_received": "📥",
            "state_changed": "🔄",
            "error_occurred": "⚠️"
        }
        return icon_map.get(activity_type, "📌")

    def _get_activity_color(self, activity_type: str) -> str:
        """Get color for activity type"""
        color_map = {
            "spawned": "#10b981",
            "task_started": "#3b82f6",
            "task_completed": "#10b981",
            "task_failed": "#ef4444",
            "decision_made": "#8b5cf6",
            "communication_sent": "#06b6d4",
            "communication_received": "#06b6d4",
            "state_changed": "#f59e0b",
            "error_occurred": "#ef4444"
        }
        return color_map.get(activity_type, "#64748b")

    # =====================================================================
    # Dependency Injection
    # =====================================================================

    def set_activity_tracker(self, tracker):
        """Inject activity tracker dependency"""
        self.activity_tracker = tracker

    def set_agent_factory(self, factory):
        """Inject agent factory dependency"""
        self.agent_factory = factory

    # =====================================================================
    # WebSocket Management
    # =====================================================================

    async def broadcast_update(self, update_type: str, data: Dict):
        """Broadcast update to all connected dashboards"""
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Send to all connected WebSocket clients
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except:
                # Remove disconnected clients
                self.websocket_clients.discard(client)

    def add_websocket_client(self, websocket):
        """Add WebSocket client"""
        self.websocket_clients.add(websocket)

    def remove_websocket_client(self, websocket):
        """Remove WebSocket client"""
        self.websocket_clients.discard(websocket)


# Singleton instance
_dashboard_orchestrator = None

def get_dashboard_orchestrator() -> DashboardOrchestratorAgent:
    """Get or create dashboard orchestrator instance"""
    global _dashboard_orchestrator
    if _dashboard_orchestrator is None:
        _dashboard_orchestrator = DashboardOrchestratorAgent()
    return _dashboard_orchestrator


if __name__ == "__main__":
    # Demo the dashboard orchestrator
    import asyncio

    async def demo():
        orchestrator = get_dashboard_orchestrator()

        # Get dashboard state (will be empty without dependencies)
        state = await orchestrator._get_dashboard_state()
        print("\n[Dashboard State]")
        print(json.dumps(state, indent=2))

        # Analyze dashboard requirements
        analysis = await orchestrator.analyze({})
        print("\n[Dashboard Analysis]")
        print(json.dumps(analysis, indent=2))

    asyncio.run(demo())
