"""
Dashboard Orchestrator Agent v1.0 - Architecturally Compliant
==============================================================

Meta-Agent for UI Coordination and Data Aggregation

This agent coordinates data flow between the agent ecosystem and dashboards,
aggregating metrics, formatting data for visualization, and managing real-time
updates.

**Architectural Compliance:**
- Follows 8 architectural principles
- Supports 5 protocols (A2A, A2P, ACP, ANP, MCP)
- Environment-based configuration (12-factor)
- Standardized lifecycle management
- Resource monitoring and metrics

**Version:** 1.0
**Category:** Meta-Agent (UI Coordination & Presentation)
**Protocols:** A2A, A2P, ACP, ANP, MCP
"""

import asyncio
import json
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


# =========================================================================
# Constants
# =========================================================================

AGENT_TYPE = "dashboard_orchestrator"
VERSION = "1.0"

DEFAULT_CACHE_TTL_SECONDS = 5
DEFAULT_ACTIVITY_FEED_LIMIT = 50
DEFAULT_COST_PER_AGENT_HOUR = 150.0
DEFAULT_TIME_PER_TASK_HOURS = 0.5
DEFAULT_EFFICIENCY_BASE = 25.0
DEFAULT_CO2_PER_AGENT_KG = 2.5


# =========================================================================
# Domain Models
# =========================================================================


@dataclass
class DashboardState:
    """Current dashboard state snapshot"""

    active_agents: List[Dict]
    recent_activities: List[Dict]
    system_metrics: Dict
    agent_network: Dict
    business_impact: Dict
    alerts: List[Dict]
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "active_agents": self.active_agents,
            "recent_activities": self.recent_activities,
            "system_metrics": self.system_metrics,
            "agent_network": self.agent_network,
            "business_impact": self.business_impact,
            "alerts": self.alerts,
            "last_updated": self.last_updated.isoformat(),
        }


# =========================================================================
# Configuration
# =========================================================================


@dataclass
class DashboardOrchestratorAgentConfig:
    """
    Configuration for Dashboard Orchestrator Agent

    All values can be overridden via environment variables following
    12-factor app methodology.
    """

    # Cache settings
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    activity_feed_limit: int = DEFAULT_ACTIVITY_FEED_LIMIT

    # Business impact calculations
    cost_per_agent_hour: float = DEFAULT_COST_PER_AGENT_HOUR
    time_per_task_hours: float = DEFAULT_TIME_PER_TASK_HOURS
    efficiency_base: float = DEFAULT_EFFICIENCY_BASE
    co2_per_agent_kg: float = DEFAULT_CO2_PER_AGENT_KG

    # Resource limits
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 80.0

    @classmethod
    def from_environment(cls) -> "DashboardOrchestratorAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            cache_ttl_seconds=int(os.getenv("DASHBOARD_CACHE_TTL", str(DEFAULT_CACHE_TTL_SECONDS))),
            activity_feed_limit=int(
                os.getenv("DASHBOARD_FEED_LIMIT", str(DEFAULT_ACTIVITY_FEED_LIMIT))
            ),
            cost_per_agent_hour=float(
                os.getenv("DASHBOARD_COST_PER_AGENT_HOUR", str(DEFAULT_COST_PER_AGENT_HOUR))
            ),
            time_per_task_hours=float(
                os.getenv("DASHBOARD_TIME_PER_TASK", str(DEFAULT_TIME_PER_TASK_HOURS))
            ),
            efficiency_base=float(
                os.getenv("DASHBOARD_EFFICIENCY_BASE", str(DEFAULT_EFFICIENCY_BASE))
            ),
            co2_per_agent_kg=float(
                os.getenv("DASHBOARD_CO2_PER_AGENT", str(DEFAULT_CO2_PER_AGENT_KG))
            ),
            memory_limit_mb=int(os.getenv("DASHBOARD_MEMORY_LIMIT_MB", "512")),
            cpu_limit_percent=float(os.getenv("DASHBOARD_CPU_LIMIT_PERCENT", "80.0")),
        )


# =========================================================================
# Dashboard Orchestrator Agent
# =========================================================================


class DashboardOrchestratorAgent(BaseAgent, ProtocolMixin):
    """
    Meta-agent for UI coordination and data aggregation

    **Capabilities:**
    - Aggregate agent metrics for visualization
    - Format data for different dashboard views
    - Generate business impact calculations
    - Coordinate between multiple data sources
    - Cache expensive computations
    - WebSocket broadcast management

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
        config: DashboardOrchestratorAgentConfig,
        activity_tracker=None,
        agent_factory=None,
    ):
        """Initialize Dashboard Orchestrator Agent"""
        # Initialize both parent classes
        super(BaseAgent, self).__init__()
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = VERSION
        ProtocolMixin.__init__(self)

        # Store typed config
        self.typed_config = config

        # Dashboard state
        self.current_state: Optional[DashboardState] = None

        # WebSocket clients (would be populated by server)
        self.websocket_clients: Set = set()

        # Dependencies (injected)
        self.activity_tracker = activity_tracker
        self.agent_factory = agent_factory

        # Cache management
        self.cached_network_graph: Optional[Dict] = None
        self.cache_timestamp: Optional[datetime] = None

        # State tracking
        self.state = {"initialized": False, "last_update": None, "websocket_clients_count": 0}

        # Metrics
        self.metrics = {
            "updates_generated": 0,
            "broadcasts_sent": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Resource tracking
        self.process = psutil.Process()

    # =====================================================================
    # Abstract Method Implementations (Required by BaseAgent)
    # =====================================================================

    async def _configure_data_sources(self):
        """Configure data sources - dependencies injected"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - dashboard orchestrator aggregates from injected sources"""
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
            self.state["last_update"] = datetime.now().isoformat()

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
        Execute dashboard orchestration operations

        Supported operations:
        - get_dashboard_state: Get complete dashboard state
        - get_agent_network: Get agent network graph (cached)
        - get_business_impact: Calculate business impact metrics
        - get_agent_details: Get detailed information about specific agent
        - format_activity_feed: Format activity feed for specific view
        - analyze: Analyze dashboard requirements
        """
        if not self.state["initialized"]:
            return {"success": False, "error": "Agent not initialized. Call initialize() first."}

        start_time = time.time()

        try:
            operation = input_data.get("operation") or input_data.get("type")

            if not operation:
                return {"success": False, "error": "No operation specified"}

            # Route to appropriate handler
            if operation == "get_dashboard_state":
                result = await self._get_dashboard_state()
            elif operation == "get_agent_network":
                result = await self._get_agent_network()
            elif operation == "get_business_impact":
                result = await self._get_business_impact()
            elif operation == "get_agent_details":
                result = await self._get_agent_details(input_data)
            elif operation == "format_activity_feed":
                result = await self._format_activity_feed(input_data)
            elif operation == "analyze":
                result = await self.analyze(input_data)
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}

            # Track execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result["execution_time_ms"] = round(execution_time_ms, 2)

            # Update metrics
            if result.get("success"):
                self.metrics["updates_generated"] += 1

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
            # Clear state
            self.current_state = None
            self.cached_network_graph = None
            self.cache_timestamp = None
            self.websocket_clients.clear()

            self.state["initialized"] = False

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": {
                    "updates_generated": self.metrics["updates_generated"],
                    "broadcasts_sent": self.metrics["broadcasts_sent"],
                    "cache_hits": self.metrics["cache_hits"],
                    "cache_misses": self.metrics["cache_misses"],
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

            # Check dependencies
            dependencies_ok = True
            dependencies_status = {
                "activity_tracker": "connected" if self.activity_tracker else "missing",
                "agent_factory": "connected" if self.agent_factory else "missing",
            }

            if not self.activity_tracker or not self.agent_factory:
                dependencies_ok = False

            status = "ready" if (memory_ok and cpu_ok and dependencies_ok) else "degraded"

            return {
                "status": status,
                "agent_id": self.agent_id,
                "initialized": self.state["initialized"],
                "resources": {
                    "memory_mb": round(memory_mb, 2),
                    "memory_limit_mb": self.typed_config.memory_limit_mb,
                    "memory_percent": round(
                        (memory_mb / self.typed_config.memory_limit_mb) * 100, 1
                    ),
                    "cpu_percent": round(cpu_percent, 1),
                    "cpu_limit_percent": self.typed_config.cpu_limit_percent,
                },
                "dependencies": dependencies_status,
                "websocket_clients": len(self.websocket_clients),
                "state": self.state.copy(),
                "metrics": self.metrics.copy(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =====================================================================
    # Dashboard State Management
    # =====================================================================

    async def _get_dashboard_state(self) -> Dict[str, Any]:
        """Get complete dashboard state"""
        try:
            # Aggregate data from various sources
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
                last_updated=datetime.now(),
            )

            self.current_state = state
            self.state["last_update"] = datetime.now().isoformat()

            return {"success": True, "state": state.to_dict()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_active_agents(self) -> List[Dict]:
        """Get list of active agents with summaries"""
        active_agents = []

        # Get metrics from activity tracker if available
        if self.activity_tracker:
            metrics_result = await self.activity_tracker.execute({"operation": "get_agent_metrics"})

            if metrics_result.get("success"):
                metrics_by_id = metrics_result.get("metrics", {})

                for agent_id, metrics in metrics_by_id.items():
                    active_agents.append(
                        {
                            "agent_id": agent_id,
                            "agent_type": metrics.get("agent_type", "unknown"),
                            "status": metrics.get("current_state", "idle"),
                            "tasks_completed": metrics.get("tasks_completed", 0),
                            "success_rate": round(metrics.get("success_rate", 0) * 100, 2),
                            "last_activity": metrics.get("last_activity"),
                        }
                    )

        return active_agents

    async def _get_recent_activities(self, limit: Optional[int] = None) -> List[Dict]:
        """Get recent activity feed"""
        if not self.activity_tracker:
            return []

        limit = limit or self.typed_config.activity_feed_limit

        feed_result = await self.activity_tracker.execute(
            {"operation": "get_activity_feed", "limit": limit}
        )

        if not feed_result.get("success"):
            return []

        return feed_result.get("activities", [])

    async def _get_system_metrics(self) -> Dict:
        """Get system-wide metrics"""
        if not self.activity_tracker:
            return {
                "total_agents": 0,
                "active_agents": 0,
                "idle_agents": 0,
                "total_tasks": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "overall_success_rate": 0,
                "total_messages": 0,
                "total_errors": 0,
                "uptime_seconds": 0,
            }

        health_result = await self.activity_tracker.execute({"operation": "get_system_health"})

        if health_result.get("success"):
            return health_result.get("health", {})

        return {}

    async def _get_agent_network(self) -> Dict:
        """Get agent network graph (cached)"""
        # Check cache
        if self.cached_network_graph and self.cache_timestamp:
            time_since_cache = (datetime.now() - self.cache_timestamp).seconds
            if time_since_cache < self.typed_config.cache_ttl_seconds:
                self.metrics["cache_hits"] += 1
                return self.cached_network_graph

        self.metrics["cache_misses"] += 1

        # Build network graph
        if not self.activity_tracker:
            return {"nodes": [], "edges": []}

        # Get coordination patterns
        coord_result = await self.activity_tracker.execute(
            {"operation": "get_coordination_patterns"}
        )

        if not coord_result.get("success"):
            return {"nodes": [], "edges": []}

        # Build nodes from active agents
        metrics_result = await self.activity_tracker.execute({"operation": "get_agent_metrics"})

        nodes = []
        if metrics_result.get("success"):
            for agent_id, metrics in metrics_result.get("metrics", {}).items():
                nodes.append(
                    {
                        "id": agent_id,
                        "label": metrics.get("agent_type", "unknown"),
                        "type": metrics.get("agent_type", "unknown"),
                        "status": metrics.get("current_state", "idle"),
                        "category": self._get_agent_category(metrics.get("agent_type", "")),
                    }
                )

        # Build edges from collaborations
        edges = []
        for collab in coord_result.get("top_collaborations", [])[:50]:
            edges.append(
                {
                    "source": collab["from"],
                    "target": collab["to"],
                    "weight": collab["message_count"],
                }
            )

        network = {"nodes": nodes, "edges": edges}

        # Cache it
        self.cached_network_graph = network
        self.cache_timestamp = datetime.now()

        return network

    async def _get_business_impact(self) -> Dict:
        """Calculate business impact metrics"""
        metrics = await self._get_system_metrics()

        active_agents = metrics.get("active_agents", 0)
        tasks_completed = metrics.get("tasks_completed", 0)
        success_rate = metrics.get("overall_success_rate", 0)
        uptime_hours = metrics.get("uptime_seconds", 0) / 3600

        # Business impact calculations using config
        cost_savings = active_agents * self.typed_config.cost_per_agent_hour * uptime_hours
        time_saved = tasks_completed * self.typed_config.time_per_task_hours
        efficiency_gain = min(80, self.typed_config.efficiency_base + (success_rate * 0.5))
        co2_reduction = active_agents * self.typed_config.co2_per_agent_kg * uptime_hours

        return {
            "cost_savings": round(cost_savings, 2),
            "time_saved_hours": round(time_saved, 2),
            "efficiency_gain_percent": round(efficiency_gain, 2),
            "co2_reduction_kg": round(co2_reduction, 2),
            "tasks_automated": tasks_completed,
            "human_equivalent_hours": round(time_saved, 2),
        }

    async def _get_alerts(self) -> List[Dict]:
        """Get system alerts and warnings"""
        if not self.activity_tracker:
            return []

        alerts = []

        # Analyze for bottlenecks
        analysis_result = await self.activity_tracker.execute(
            {"operation": "analyze", "analysis_type": "bottlenecks"}
        )

        for bottleneck in analysis_result.get("bottlenecks", []):
            alerts.append(
                {
                    "severity": bottleneck.get("severity", "medium"),
                    "type": "bottleneck",
                    "message": f"Agent {bottleneck['agent_id']}: {bottleneck['issue']}",
                    "details": bottleneck,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check for isolated agents
        coord_result = await self.activity_tracker.execute(
            {"operation": "analyze", "analysis_type": "coordination"}
        )

        if coord_result.get("isolated_agents", 0) > 0:
            alerts.append(
                {
                    "severity": "low",
                    "type": "coordination",
                    "message": f"{coord_result['isolated_agents']} agents are not coordinating",
                    "details": {"isolated_ids": coord_result.get("isolated_agent_ids", [])},
                    "timestamp": datetime.now().isoformat(),
                }
            )

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
        metrics_result = await self.activity_tracker.execute(
            {"operation": "get_agent_metrics", "agent_id": agent_id}
        )

        if not metrics_result.get("success"):
            return {"success": False, "error": f"Agent {agent_id} not found"}

        # Get recent activities for this agent
        activities_result = await self.activity_tracker.execute(
            {"operation": "get_activity_feed", "agent_id": agent_id, "limit": 20}
        )

        activities = (
            activities_result.get("activities", []) if activities_result.get("success") else []
        )

        return {
            "success": True,
            "agent": {**metrics_result.get("metrics", {}), "recent_activities": activities},
        }

    async def _format_activity_feed(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format activity feed for specific dashboard view"""
        view_type = task.get("view_type", "timeline")
        limit = task.get("limit", self.typed_config.activity_feed_limit)

        activities = await self._get_recent_activities(limit)

        if view_type == "timeline":
            return {
                "success": True,
                "format": "timeline",
                "activities": self._format_timeline(activities),
            }
        elif view_type == "grouped":
            return {
                "success": True,
                "format": "grouped",
                "groups": self._group_activities(activities),
            }
        elif view_type == "agent_centric":
            return {
                "success": True,
                "format": "agent_centric",
                "by_agent": self._group_by_agent(activities),
            }
        else:
            return {"success": False, "error": f"Unknown view type: {view_type}"}

    def _format_timeline(self, activities: List[Dict]) -> List[Dict]:
        """Format activities as timeline"""
        return [
            {
                "id": act.get("activity_id"),
                "timestamp": act.get("timestamp"),
                "title": f"{act.get('agent_type', 'Unknown')}: {act.get('activity_type', 'activity')}",
                "description": act.get("description", ""),
                "icon": self._get_activity_icon(act.get("activity_type", "")),
                "color": self._get_activity_color(act.get("activity_type", "")),
                "success": act.get("success"),
            }
            for act in activities
        ]

    def _group_activities(self, activities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group activities by type"""
        grouped = defaultdict(list)
        for act in activities:
            grouped[act.get("activity_type", "unknown")].append(act)
        return dict(grouped)

    def _group_by_agent(self, activities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group activities by agent"""
        grouped = defaultdict(list)
        for act in activities:
            grouped[act.get("agent_id", "unknown")].append(act)
        return dict(grouped)

    # =====================================================================
    # Analysis Methods
    # =====================================================================

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dashboard requirements and optimize data flow"""
        return {
            "success": True,
            "data_flow_optimizations": [
                f"Cache network graph for {self.typed_config.cache_ttl_seconds} seconds",
                "Batch activity updates every 2 seconds",
                "Pre-compute business impact metrics",
            ],
            "recommendations": [
                "Use WebSocket for real-time activity feed",
                "Poll agent metrics every 3 seconds",
                "Lazy-load agent detail modals",
            ],
        }

    # =====================================================================
    # Helper Methods
    # =====================================================================

    def _get_agent_category(self, agent_type: str) -> str:
        """Map agent type to category for visualization"""
        category_map = {
            "traffic_prediction": "mobility",
            "matching_optimization": "mobility",
            "route_discovery": "mobility",
            "handoff_coordination": "mobility",
            "consensus": "decision",
            "task_assignment": "orchestration",
            "activity_tracker": "monitoring",
            "dashboard_orchestrator": "ui",
        }
        return category_map.get(agent_type, "other")

    def _get_activity_icon(self, activity_type: str) -> str:
        """Get icon for activity type (as text for terminal compatibility)"""
        icon_map = {
            "spawned": "[SPAWN]",
            "task_started": "[START]",
            "task_completed": "[DONE]",
            "task_failed": "[FAIL]",
            "decision_made": "[DECIDE]",
            "communication_sent": "[SEND]",
            "communication_received": "[RECV]",
            "state_changed": "[STATE]",
            "error_occurred": "[ERROR]",
        }
        return icon_map.get(activity_type, "[INFO]")

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
            "error_occurred": "#ef4444",
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
        message = {"type": update_type, "data": data, "timestamp": datetime.now().isoformat()}

        # Send to all connected WebSocket clients
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
                self.metrics["broadcasts_sent"] += 1
            except:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.discard(client)

        self.state["websocket_clients_count"] = len(self.websocket_clients)

    def add_websocket_client(self, websocket):
        """Add WebSocket client"""
        self.websocket_clients.add(websocket)
        self.state["websocket_clients_count"] = len(self.websocket_clients)

    def remove_websocket_client(self, websocket):
        """Remove WebSocket client"""
        self.websocket_clients.discard(websocket)
        self.state["websocket_clients_count"] = len(self.websocket_clients)


# =========================================================================
# Factory Function
# =========================================================================


async def create_dashboard_orchestrator_agent(
    agent_id: str = "dashboard_orchestrator_001",
    config: Optional[DashboardOrchestratorAgentConfig] = None,
    activity_tracker=None,
    agent_factory=None,
) -> DashboardOrchestratorAgent:
    """
    Factory function to create and initialize a Dashboard Orchestrator Agent

    Args:
        agent_id: Unique identifier for the agent
        config: Configuration object (uses environment if not provided)
        activity_tracker: Optional activity tracker dependency
        agent_factory: Optional agent factory dependency

    Returns:
        Initialized DashboardOrchestratorAgent instance
    """
    if config is None:
        config = DashboardOrchestratorAgentConfig.from_environment()

    agent = DashboardOrchestratorAgent(
        agent_id=agent_id,
        config=config,
        activity_tracker=activity_tracker,
        agent_factory=agent_factory,
    )

    await agent.initialize()

    return agent


# =========================================================================
# Main (for testing)
# =========================================================================

if __name__ == "__main__":

    async def demo():
        """Demonstrate Dashboard Orchestrator Agent capabilities"""
        print("\n" + "=" * 80)
        print("DASHBOARD ORCHESTRATOR AGENT v1.0 - DEMO")
        print("=" * 80)

        # Create agent (without dependencies for basic test)
        print("\n[1] Creating agent...")
        agent = await create_dashboard_orchestrator_agent(agent_id="dashboard_orch_demo")
        print(f"    Agent created: {agent.agent_id}")
        print(f"    Initialized: {agent.state['initialized']}")

        # Get dashboard state (will be empty without dependencies)
        print("\n[2] Getting dashboard state (no dependencies)...")
        state_result = await agent.execute({"operation": "get_dashboard_state"})
        if state_result.get("success"):
            state = state_result["state"]
            print(f"    Active agents: {len(state.get('active_agents', []))}")
            print(f"    Recent activities: {len(state.get('recent_activities', []))}")
            print(f"    System metrics: {json.dumps(state.get('system_metrics', {}), indent=6)}")

        # Get business impact
        print("\n[3] Calculating business impact...")
        impact_result = await agent.execute({"operation": "get_business_impact"})
        if impact_result.get("success"):
            impact = impact_result
            print(f"    Cost savings: ${impact.get('cost_savings', 0):.2f}")
            print(f"    Time saved: {impact.get('time_saved_hours', 0):.2f} hours")
            print(f"    Efficiency gain: {impact.get('efficiency_gain_percent', 0):.1f}%")

        # Format activity feed
        print("\n[4] Formatting activity feed (timeline view)...")
        feed_result = await agent.execute(
            {"operation": "format_activity_feed", "view_type": "timeline", "limit": 10}
        )
        if feed_result.get("success"):
            print(f"    Format: {feed_result.get('format')}")
            print(f"    Activities: {len(feed_result.get('activities', []))}")

        # Analyze dashboard
        print("\n[5] Analyzing dashboard requirements...")
        analysis_result = await agent.execute({"operation": "analyze"})
        if analysis_result.get("success"):
            print("    Optimizations:")
            for opt in analysis_result.get("data_flow_optimizations", []):
                print(f"      - {opt}")

        # Health check
        print("\n[6] Health check:")
        health = await agent.health_check()
        print(f"    Status: {health['status']}")
        print(f"    Memory: {health['resources']['memory_mb']:.2f} MB")
        print(f"    Dependencies: {json.dumps(health['dependencies'], indent=6)}")
        print(f"    Cache hits: {health['metrics']['cache_hits']}")
        print(f"    Cache misses: {health['metrics']['cache_misses']}")

        # Shutdown
        print("\n[7] Shutting down...")
        shutdown_result = await agent.shutdown()
        print(f"    Status: {shutdown_result['status']}")
        print(f"    Final metrics: {json.dumps(shutdown_result['final_metrics'], indent=6)}")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80 + "\n")

    asyncio.run(demo())
