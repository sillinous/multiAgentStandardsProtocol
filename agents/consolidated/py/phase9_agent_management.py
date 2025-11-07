"""
Phase 9 Agent Management System

Holistic agent management backend that:
1. CONTROLS agents - Start, stop, pause, resume, allocate resources
2. MANAGES agent lifecycle - Registration, versioning, configuration
3. MAPS agents - Library inventory, capabilities, relationships
4. MONITORS agents - Real-time metrics, health, performance
5. MAINTAINS agents - Updates, patches, state synchronization
6. MANIPULATES agent behavior - Dynamic parameter adjustment, strategy changes
7. GAINS INSIGHTS - Agent logs, decisions, environmental memory, pattern analysis
8. VISUALIZES agents - Dashboard representation, activity feeds, collaboration networks

This is the backend for a complete Agent Operations Center.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import json
from collections import defaultdict


# ============================================================================
# Enums and Data Classes
# ============================================================================


class AgentStatus(str, Enum):
    """Agent operational status"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class AgentHealthLevel(str, Enum):
    """Agent health assessment"""

    CRITICAL = "critical"  # Immediate intervention needed
    WARNING = "warning"  # Monitor closely
    HEALTHY = "healthy"  # Operating normally
    OPTIMAL = "optimal"  # Peak performance


@dataclass
class AgentCapability:
    """Represents a single agent capability"""

    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
    category: str  # "trading", "analysis", "risk", "research", etc.
    reliability_score: float = 0.95  # 0-1
    avg_execution_time_seconds: float = 1.0


@dataclass
class AgentMetrics:
    """Real-time agent metrics"""

    agent_id: str
    status: AgentStatus
    health_level: AgentHealthLevel
    uptime_seconds: float
    executions_total: int
    executions_successful: int
    executions_failed: int
    avg_execution_time_ms: float
    error_rate: float  # 0-1
    cpu_usage_percent: float
    memory_usage_mb: float
    last_execution: Optional[str]  # ISO timestamp
    last_error: Optional[str]
    timestamp: str  # ISO timestamp


@dataclass
class AgentLogEntry:
    """Single agent log entry"""

    agent_id: str
    timestamp: str
    level: str  # "DEBUG", "INFO", "WARN", "ERROR"
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    """Agent decision recorded for analysis"""

    agent_id: str
    decision_type: str  # "trade", "research_strategy", "risk_assessment", etc.
    decision: str
    confidence: float  # 0-1
    reasoning: str
    inputs_considered: Dict[str, Any]
    outcome: Optional[str] = None  # Result after decision was executed
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentInfo:
    """Complete agent information"""

    agent_id: str
    agent_type: str  # "trading_agent", "research_agent", etc.
    name: str
    description: str
    version: str
    status: AgentStatus
    health_level: AgentHealthLevel
    capabilities: List[AgentCapability]
    metrics: AgentMetrics
    current_task: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    team_memberships: List[str] = field(default_factory=list)  # Team IDs
    recent_logs: List[AgentLogEntry] = field(default_factory=list)
    recent_decisions: List[AgentDecision] = field(default_factory=list)
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentTeam:
    """Team of agents working together"""

    team_id: str
    name: str
    objective: str
    agent_ids: List[str]
    lead_agent: Optional[str]  # Agent coordinating the team
    status: str  # "forming", "active", "paused", "completed"
    voting_mechanism: str  # "majority", "consensus", "weighted", "ranked_choice"
    created_at: str
    decisions_log: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EnvironmentalMemory:
    """Shared environmental memory"""

    memory_id: str
    memory_type: str  # "market_state", "strategy_history", "team_context", etc.
    data: Dict[str, Any]
    timestamp: str
    ttl_seconds: Optional[int] = None  # Time to live
    accessed_by: List[str] = field(default_factory=list)  # Agent IDs


# ============================================================================
# Agent Management System
# ============================================================================


class AgentManagementSystem:
    """Holistic agent management backend"""

    def __init__(self):
        """Initialize agent management system"""
        self.agents: Dict[str, AgentInfo] = {}
        self.teams: Dict[str, AgentTeam] = {}
        self.agent_logs: Dict[str, List[AgentLogEntry]] = defaultdict(list)
        self.agent_decisions: Dict[str, List[AgentDecision]] = defaultdict(list)
        self.environmental_memory: Dict[str, EnvironmentalMemory] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # workflow_id -> agent_ids

    async def initialize(self) -> None:
        """Initialize agent management system"""
        # Load agents from AgentRegistry
        try:
            from src.backend.agent_registry import get_agent_registry

            registry = get_agent_registry()  # Not async
            agents_data = registry.get_all_agents()  # Not async

            for agent_data in agents_data:
                # Reconstruct AgentInfo from dictionary
                agent_id = agent_data["agent_id"]

                # Reconstruct nested objects
                metrics_data = agent_data.get("metrics", {})
                metrics = AgentMetrics(
                    agent_id=metrics_data.get("agent_id", agent_id),
                    status=AgentStatus(metrics_data.get("status", "idle")),
                    health_level=AgentHealthLevel(metrics_data.get("health_level", "healthy")),
                    uptime_seconds=metrics_data.get("uptime_seconds", 0),
                    executions_total=metrics_data.get("executions_total", 0),
                    executions_successful=metrics_data.get("executions_successful", 0),
                    executions_failed=metrics_data.get("executions_failed", 0),
                    avg_execution_time_ms=metrics_data.get("avg_execution_time_ms", 0),
                    error_rate=metrics_data.get("error_rate", 0),
                    cpu_usage_percent=metrics_data.get("cpu_usage_percent", 0),
                    memory_usage_mb=metrics_data.get("memory_usage_mb", 0),
                    last_execution=metrics_data.get("last_execution"),
                    last_error=metrics_data.get("last_error"),
                    timestamp=metrics_data.get("timestamp", datetime.now().isoformat()),
                )

                capabilities = [
                    AgentCapability(
                        name=cap["name"],
                        description=cap.get("description", ""),
                        inputs=cap.get("inputs", []),
                        outputs=cap.get("outputs", []),
                        category=cap.get("category", "general"),
                        reliability_score=cap.get("reliability_score", 0.95),
                        avg_execution_time_seconds=cap.get("avg_execution_time_seconds", 1.0),
                    )
                    for cap in agent_data.get("capabilities", [])
                ]

                agent = AgentInfo(
                    agent_id=agent_data["agent_id"],
                    agent_type=agent_data.get("agent_type", "general"),
                    name=agent_data.get("name", agent_id),
                    description=agent_data.get("description", ""),
                    version=agent_data.get("version", "1.0.0"),
                    status=AgentStatus(agent_data.get("status", "idle")),
                    health_level=AgentHealthLevel(agent_data.get("health_level", "healthy")),
                    capabilities=capabilities,
                    metrics=metrics,
                    current_task=agent_data.get("current_task"),
                    parameters=agent_data.get("parameters", {}),
                    environment=agent_data.get("environment", {}),
                    team_memberships=agent_data.get("team_memberships", []),
                    recent_logs=agent_data.get("recent_logs", []),
                    recent_decisions=agent_data.get("recent_decisions", []),
                    registered_at=agent_data.get("registered_at", datetime.now().isoformat()),
                    last_heartbeat=agent_data.get("last_heartbeat", datetime.now().isoformat()),
                )

                self.agents[agent_id] = agent

            print(
                f"Agent Management System initialized with {len(self.agents)} agents from registry"
            )
        except Exception as e:
            print(f"Warning: Could not load agents from registry: {e}")
            print("Agent Management System initialized (no agents loaded)")

    # ========================================================================
    # CONTROL: Start, Stop, Pause, Resume, Allocate
    # ========================================================================

    async def start_agent(
        self, agent_id: str, parameters: Dict[str, Any] = None, environment: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Start an agent with optional parameters and environment variables.
        """
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        agent.status = AgentStatus.INITIALIZING

        if parameters:
            agent.parameters.update(parameters)
        if environment:
            agent.environment.update(environment)

        # TODO: Actually start the agent process
        agent.status = AgentStatus.RUNNING
        agent.last_heartbeat = datetime.now().isoformat()

        return {
            "agent_id": agent_id,
            "status": agent.status.value,
            "parameters": agent.parameters,
            "environment": agent.environment,
        }

    async def stop_agent(self, agent_id: str) -> Dict[str, Any]:
        """Stop an agent gracefully"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        agent.status = AgentStatus.IDLE
        # TODO: Gracefully shutdown agent

        return {"agent_id": agent_id, "status": "stopped"}

    async def pause_agent(self, agent_id: str) -> Dict[str, Any]:
        """Pause agent execution (can be resumed)"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        agent.status = AgentStatus.PAUSED

        return {"agent_id": agent_id, "status": "paused"}

    async def resume_agent(self, agent_id: str) -> Dict[str, Any]:
        """Resume paused agent"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        agent.status = AgentStatus.RUNNING

        return {"agent_id": agent_id, "status": "running"}

    async def update_agent_parameters(
        self, agent_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically update agent parameters while running.
        Useful for fine-tuning behavior.
        """
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        agent.parameters.update(parameters)

        # TODO: Notify agent of parameter changes via MessageBus

        return {
            "agent_id": agent_id,
            "updated_parameters": parameters,
            "all_parameters": agent.parameters,
        }

    # ========================================================================
    # MANAGE: Registration, Versioning, Configuration
    # ========================================================================

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        name: str,
        description: str,
        version: str,
        capabilities: List[Dict[str, Any]],
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Register a new agent in the management system.
        """
        if agent_id in self.agents:
            return {"error": f"Agent {agent_id} already registered"}

        # Create capability objects
        caps = [
            AgentCapability(
                name=cap["name"],
                description=cap.get("description", ""),
                inputs=cap.get("inputs", []),
                outputs=cap.get("outputs", []),
                category=cap.get("category", "general"),
                reliability_score=cap.get("reliability_score", 0.95),
            )
            for cap in capabilities
        ]

        # Create metrics
        metrics = AgentMetrics(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            health_level=AgentHealthLevel.HEALTHY,
            uptime_seconds=0,
            executions_total=0,
            executions_successful=0,
            executions_failed=0,
            avg_execution_time_ms=0,
            error_rate=0,
            cpu_usage_percent=0,
            memory_usage_mb=0,
            last_execution=None,
            last_error=None,
            timestamp=datetime.now().isoformat(),
        )

        # Create agent
        agent = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            name=name,
            description=description,
            version=version,
            status=AgentStatus.IDLE,
            health_level=AgentHealthLevel.HEALTHY,
            capabilities=caps,
            metrics=metrics,
            parameters=parameters or {},
        )

        self.agents[agent_id] = agent
        self.agent_logs[agent_id] = []
        self.agent_decisions[agent_id] = []

        return {"agent_id": agent_id, "status": "registered", "agent": asdict(agent)}

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get complete agent information"""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        return asdict(agent)

    # ========================================================================
    # MAP: Library Inventory, Capabilities, Relationships
    # ========================================================================

    async def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [asdict(agent) for agent in self.agents.values()]

    async def find_agents_by_capability(self, capability_name: str) -> List[Dict[str, Any]]:
        """Find agents with a specific capability"""
        matching_agents = []
        for agent in self.agents.values():
            if any(cap.name == capability_name for cap in agent.capabilities):
                matching_agents.append(asdict(agent))
        return matching_agents

    async def find_agents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Find agents in a specific category (trading, research, etc.)"""
        matching_agents = []
        for agent in self.agents.values():
            if any(cap.category == category for cap in agent.capabilities):
                matching_agents.append(asdict(agent))
        return matching_agents

    async def get_agent_relationships(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's team memberships and collaborations"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        teams = [self.teams[team_id] for team_id in agent.team_memberships if team_id in self.teams]

        return {
            "agent_id": agent_id,
            "team_memberships": agent.team_memberships,
            "teams": [asdict(t) for t in teams],
            "recent_collaborators": self._get_collaborators(agent_id),
        }

    async def get_agent_library(self) -> Dict[str, Any]:
        """Get complete agent library organized by category"""
        library = {}
        for agent in self.agents.values():
            for cap in agent.capabilities:
                if cap.category not in library:
                    library[cap.category] = []
                library[cap.category].append(
                    {
                        "agent_id": agent.agent_id,
                        "agent_name": agent.name,
                        "capability": cap.name,
                        "version": agent.version,
                        "status": agent.status.value,
                        "health": agent.health_level.value,
                    }
                )
        return library

    # ========================================================================
    # MONITOR: Metrics, Health, Performance, Real-Time Activity
    # ========================================================================

    async def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]) -> None:
        """Update agent metrics from heartbeat"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        old_metrics = agent.metrics

        # Update metrics
        agent.metrics.uptime_seconds = metrics.get("uptime_seconds", old_metrics.uptime_seconds)
        agent.metrics.executions_total = metrics.get(
            "executions_total", old_metrics.executions_total
        )
        agent.metrics.executions_successful = metrics.get(
            "executions_successful", old_metrics.executions_successful
        )
        agent.metrics.executions_failed = metrics.get(
            "executions_failed", old_metrics.executions_failed
        )
        agent.metrics.avg_execution_time_ms = metrics.get(
            "avg_execution_time_ms", old_metrics.avg_execution_time_ms
        )
        agent.metrics.cpu_usage_percent = metrics.get(
            "cpu_usage_percent", old_metrics.cpu_usage_percent
        )
        agent.metrics.memory_usage_mb = metrics.get("memory_usage_mb", old_metrics.memory_usage_mb)
        agent.metrics.last_execution = metrics.get("last_execution", old_metrics.last_execution)
        agent.metrics.last_error = metrics.get("last_error", old_metrics.last_error)
        agent.metrics.timestamp = datetime.now().isoformat()

        # Calculate error rate
        if agent.metrics.executions_total > 0:
            agent.metrics.error_rate = (
                agent.metrics.executions_failed / agent.metrics.executions_total
            )
        else:
            agent.metrics.error_rate = 0

        # Assess health
        agent.health_level = self._assess_health(agent.metrics)
        agent.last_heartbeat = datetime.now().isoformat()

    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent metrics"""
        if agent_id not in self.agents:
            return None
        return asdict(self.agents[agent_id].metrics)

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get high-level dashboard summary"""
        agents = list(self.agents.values())

        # Aggregate stats
        total_agents = len(agents)
        agents_running = sum(1 for a in agents if a.status == AgentStatus.RUNNING)
        agents_healthy = sum(1 for a in agents if a.health_level == AgentHealthLevel.HEALTHY)
        agents_warning = sum(1 for a in agents if a.health_level == AgentHealthLevel.WARNING)
        agents_critical = sum(1 for a in agents if a.health_level == AgentHealthLevel.CRITICAL)

        # Calculate avg error rate
        avg_error_rate = 0
        if agents:
            total_error_rate = sum(a.metrics.error_rate for a in agents)
            avg_error_rate = total_error_rate / len(agents)

        # Top performing agents
        top_agents = sorted(agents, key=lambda a: a.metrics.executions_successful, reverse=True)[:5]

        # Agents needing attention
        critical_agents = [
            a
            for a in agents
            if a.health_level in [AgentHealthLevel.CRITICAL, AgentHealthLevel.WARNING]
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_agents": total_agents,
                "agents_running": agents_running,
                "agents_healthy": agents_healthy,
                "agents_warning": agents_warning,
                "agents_critical": agents_critical,
                "avg_error_rate": avg_error_rate,
            },
            "top_performers": [asdict(a) for a in top_agents],
            "agents_needing_attention": [asdict(a) for a in critical_agents],
            "teams": len(self.teams),
            "environmental_memory_entries": len(self.environmental_memory),
        }

    async def get_agent_activity_feed(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity for an agent (logs + decisions)"""
        if agent_id not in self.agents:
            return []

        # Combine logs and decisions
        activity = []

        # Add recent logs
        for log in self.agent_logs[agent_id][-limit:]:
            activity.append(
                {
                    "type": "log",
                    "timestamp": log.timestamp,
                    "level": log.level,
                    "message": log.message,
                    "context": log.context,
                }
            )

        # Add recent decisions
        for decision in self.agent_decisions[agent_id][-limit:]:
            activity.append(
                {
                    "type": "decision",
                    "timestamp": decision.timestamp,
                    "decision_type": decision.decision_type,
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                    "outcome": decision.outcome,
                }
            )

        # Sort by timestamp (newest first)
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:limit]

    # ========================================================================
    # MAINTAIN: Updates, Patches, State Synchronization
    # ========================================================================

    async def update_agent_version(self, agent_id: str, new_version: str) -> Dict[str, Any]:
        """Update agent to new version"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        old_version = agent.version
        agent.version = new_version

        # Log the update
        await self.log_agent_event(
            agent_id, "INFO", f"Agent updated from v{old_version} to v{new_version}"
        )

        return {
            "agent_id": agent_id,
            "old_version": old_version,
            "new_version": new_version,
            "status": "updated",
        }

    async def sync_agent_state(self, agent_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize agent state from actual agent to management system"""
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        agent.parameters.update(state.get("parameters", {}))
        agent.environment.update(state.get("environment", {}))

        if "status" in state:
            agent.status = AgentStatus(state["status"])

        if "current_task" in state:
            agent.current_task = state["current_task"]

        return {"agent_id": agent_id, "status": "synced", "agent": asdict(agent)}

    # ========================================================================
    # MANIPULATE: Dynamic Behavior Adjustment
    # ========================================================================

    async def adjust_agent_behavior(
        self, agent_id: str, adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically adjust agent behavior:
        - Risk tolerance
        - Decision thresholds
        - Execution speed
        - Strategy parameters
        """
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        agent.parameters.update(adjustments)

        # TODO: Notify agent of adjustments via MessageBus

        await self.log_agent_event(
            agent_id, "INFO", f"Behavior adjusted: {json.dumps(adjustments)}"
        )

        return {"agent_id": agent_id, "adjustments": adjustments, "status": "adjusted"}

    # ========================================================================
    # GAIN INSIGHTS: Logs, Decisions, Memory, Pattern Analysis
    # ========================================================================

    async def log_agent_event(
        self, agent_id: str, level: str, message: str, context: Dict[str, Any] = None
    ) -> None:
        """Log agent event"""
        if agent_id not in self.agents:
            return

        log_entry = AgentLogEntry(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            context=context or {},
        )

        self.agent_logs[agent_id].append(log_entry)

    async def record_agent_decision(
        self,
        agent_id: str,
        decision_type: str,
        decision: str,
        confidence: float,
        reasoning: str,
        inputs_considered: Dict[str, Any],
    ) -> None:
        """Record agent decision for analysis"""
        if agent_id not in self.agents:
            return

        decision = AgentDecision(
            agent_id=agent_id,
            decision_type=decision_type,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            inputs_considered=inputs_considered,
        )

        self.agent_decisions[agent_id].append(decision)

    async def get_agent_logs(
        self, agent_id: str, level: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get agent logs with optional filtering"""
        if agent_id not in self.agents:
            return []

        logs = self.agent_logs[agent_id]

        if level:
            logs = [l for l in logs if l.level == level]

        return [asdict(l) for l in logs[-limit:]]

    async def get_agent_decisions(
        self, agent_id: str, decision_type: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get agent decision history"""
        if agent_id not in self.agents:
            return []

        decisions = self.agent_decisions[agent_id]

        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]

        return [asdict(d) for d in decisions[-limit:]]

    async def analyze_agent_patterns(self, agent_id: str, window_size: int = 100) -> Dict[str, Any]:
        """
        Analyze agent patterns:
        - Decision distribution
        - Error patterns
        - Performance trends
        - Anomalies
        """
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        decisions = self.agent_decisions[agent_id][-window_size:]
        logs = self.agent_logs[agent_id][-window_size:]

        # Analyze decisions
        decision_types = defaultdict(int)
        avg_confidence = 0
        for d in decisions:
            decision_types[d.decision_type] += 1
            avg_confidence += d.confidence
        if decisions:
            avg_confidence /= len(decisions)

        # Analyze logs
        error_count = sum(1 for l in logs if l.level in ["ERROR", "CRITICAL"])
        warning_count = sum(1 for l in logs if l.level == "WARN")

        return {
            "agent_id": agent_id,
            "analysis_window": window_size,
            "decision_analysis": {
                "types": dict(decision_types),
                "avg_confidence": avg_confidence,
                "total_decisions": len(decisions),
            },
            "log_analysis": {
                "errors": error_count,
                "warnings": warning_count,
                "total_logs": len(logs),
            },
            "error_rate": error_count / (len(logs) if logs else 1),
        }

    # ========================================================================
    # Environmental Memory
    # ========================================================================

    async def write_environmental_memory(
        self, memory_type: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> str:
        """Write shared memory entry"""
        memory_id = f"mem_{datetime.now().timestamp()}"
        memory = EnvironmentalMemory(
            memory_id=memory_id,
            memory_type=memory_type,
            data=data,
            timestamp=datetime.now().isoformat(),
            ttl_seconds=ttl_seconds,
        )
        self.environmental_memory[memory_id] = memory
        return memory_id

    async def read_environmental_memory(
        self, agent_id: str, memory_type: str = None
    ) -> List[Dict[str, Any]]:
        """Read shared memory entries"""
        entries = []
        for memory in self.environmental_memory.values():
            # Check TTL
            if memory.ttl_seconds:
                created = datetime.fromisoformat(memory.timestamp)
                if datetime.now() - created > timedelta(seconds=memory.ttl_seconds):
                    continue

            # Filter by type if specified
            if memory_type and memory.memory_type != memory_type:
                continue

            # Track access
            if agent_id not in memory.accessed_by:
                memory.accessed_by.append(agent_id)

            entries.append(asdict(memory))

        return entries

    # ========================================================================
    # Team Management
    # ========================================================================

    async def create_team(
        self,
        team_id: str,
        name: str,
        objective: str,
        agent_ids: List[str],
        lead_agent: Optional[str] = None,
        voting_mechanism: str = "majority",
    ) -> Dict[str, Any]:
        """Create a team of agents"""
        # Validate agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                return {"error": f"Agent {agent_id} not found"}

        team = AgentTeam(
            team_id=team_id,
            name=name,
            objective=objective,
            agent_ids=agent_ids,
            lead_agent=lead_agent,
            status="active",
            voting_mechanism=voting_mechanism,
            created_at=datetime.now().isoformat(),
        )

        self.teams[team_id] = team

        # Register team membership
        for agent_id in agent_ids:
            self.agents[agent_id].team_memberships.append(team_id)

        return {"team_id": team_id, "status": "created", "team": asdict(team)}

    async def get_team_info(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team information"""
        if team_id not in self.teams:
            return None
        return asdict(self.teams[team_id])

    # ========================================================================
    # Private Helpers
    # ========================================================================

    def _assess_health(self, metrics: AgentMetrics) -> AgentHealthLevel:
        """Assess agent health based on metrics"""
        if metrics.error_rate > 0.25:  # >25% error rate
            return AgentHealthLevel.CRITICAL
        elif metrics.error_rate > 0.1:  # >10% error rate
            return AgentHealthLevel.WARNING
        elif metrics.cpu_usage_percent > 90:
            return AgentHealthLevel.WARNING
        elif metrics.memory_usage_mb > 2000:
            return AgentHealthLevel.WARNING
        else:
            return AgentHealthLevel.HEALTHY

    def _get_collaborators(self, agent_id: str) -> List[str]:
        """Get agents this agent has collaborated with"""
        collaborators = set()
        for team in self.teams.values():
            if agent_id in team.agent_ids:
                for other_id in team.agent_ids:
                    if other_id != agent_id:
                        collaborators.add(other_id)
        return list(collaborators)
