"""
Agent Discovery Protocol (ADP)

This protocol enables dynamic agent discovery in multi-agent ecosystems.
Instead of hardcoded agent references, agents can discover each other by:
- Capabilities (what they can do)
- Metadata (cost, latency, quality scores)
- Availability status
- Reputation scores

Key Features:
- Dynamic agent registration and unregistration
- Capability-based search
- Advanced filtering (cost, latency, reputation)
- Health status tracking
- Metadata-rich agent profiles
- Integration with A2A message bus

Usage:
    from src.superstandard.protocols.discovery import get_discovery_service

    discovery = get_discovery_service()

    # Register agent
    await discovery.register_agent(agent_info, capabilities=["data_analysis"])

    # Find agents by capability
    agents = await discovery.find_agents(
        required_capabilities=["data_analysis"],
        filters={"cost_per_request": {"max": 0.20}}
    )

    # Update agent status
    await discovery.update_status(agent_id, status="busy")
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


@dataclass
class AgentCapability:
    """Represents a capability an agent can perform"""
    name: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentMetadata:
    """Rich metadata about an agent"""
    # Performance characteristics
    avg_latency_ms: Optional[float] = None
    avg_quality_score: Optional[float] = None
    success_rate: Optional[float] = None

    # Cost information
    cost_per_request: Optional[float] = None
    cost_currency: str = "USD"
    cost_model: str = "per_request"  # per_request, per_minute, per_hour

    # Capacity
    max_concurrent_tasks: int = 10
    current_load: int = 0

    # Reputation
    reputation_score: Optional[float] = None
    total_tasks_completed: int = 0

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegisteredAgent:
    """Complete agent profile in discovery registry"""
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[AgentCapability]
    metadata: AgentMetadata
    status: AgentStatus = AgentStatus.AVAILABLE
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    endpoint: Optional[str] = None  # For remote agents
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    def matches_capabilities(self, required: List[str]) -> bool:
        """Check if agent has all required capabilities"""
        agent_caps = {cap.name for cap in self.capabilities}
        return all(req in agent_caps for req in required)

    def matches_filters(self, filters: Dict[str, Any]) -> bool:
        """Check if agent matches filter criteria"""
        for key, value in filters.items():
            if key == "cost_per_request":
                if self.metadata.cost_per_request is None:
                    return False
                if isinstance(value, dict):
                    if "max" in value and self.metadata.cost_per_request > value["max"]:
                        return False
                    if "min" in value and self.metadata.cost_per_request < value["min"]:
                        return False
                else:
                    if self.metadata.cost_per_request != value:
                        return False

            elif key == "avg_latency_ms":
                if self.metadata.avg_latency_ms is None:
                    return False
                if isinstance(value, dict):
                    if "max" in value and self.metadata.avg_latency_ms > value["max"]:
                        return False
                    if "min" in value and self.metadata.avg_latency_ms < value["min"]:
                        return False

            elif key == "min_reputation":
                if self.metadata.reputation_score is None:
                    return False
                if self.metadata.reputation_score < value:
                    return False

            elif key == "min_success_rate":
                if self.metadata.success_rate is None:
                    return False
                if self.metadata.success_rate < value:
                    return False

            elif key == "status":
                if isinstance(value, list):
                    if self.status.value not in value:
                        return False
                else:
                    if self.status.value != value:
                        return False

            elif key == "tags":
                required_tags = value if isinstance(value, list) else [value]
                if not all(tag in self.metadata.tags for tag in required_tags):
                    return False

            elif key == "agent_type":
                if self.agent_type != value:
                    return False

        return True

    def is_available(self) -> bool:
        """Check if agent is available for work"""
        if self.status != AgentStatus.AVAILABLE:
            return False
        if self.metadata.current_load >= self.metadata.max_concurrent_tasks:
            return False
        return True


class AgentDiscoveryService:
    """
    Central agent discovery service

    Maintains a registry of all agents in the ecosystem and enables
    dynamic discovery based on capabilities and metadata.

    Features:
    - Agent registration/unregistration
    - Capability-based search
    - Advanced filtering
    - Health monitoring (heartbeats)
    - Status tracking
    - Load balancing support
    """

    def __init__(self, heartbeat_timeout_seconds: int = 60):
        """
        Initialize discovery service

        Args:
            heartbeat_timeout_seconds: Time before agent is considered offline
        """
        self.registry: Dict[str, RegisteredAgent] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
        self.type_index: Dict[str, Set[str]] = {}  # agent_type -> agent_ids
        self.heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)

        self.stats = {
            "total_registrations": 0,
            "total_discoveries": 0,
            "active_agents": 0,
            "total_capabilities": 0
        }

        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info("✅ Agent Discovery Service initialized")

    async def start(self):
        """Start discovery service (cleanup task, etc.)"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("🚀 Agent Discovery Service started")

    async def stop(self):
        """Stop discovery service"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Agent Discovery Service stopped")

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        metadata: Optional[AgentMetadata] = None,
        endpoint: Optional[str] = None,
        version: str = "1.0.0"
    ) -> RegisteredAgent:
        """
        Register an agent in the discovery service

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            agent_type: Type of agent (e.g., "data_analyst", "market_researcher")
            capabilities: List of capabilities agent can perform
            metadata: Rich metadata about agent (cost, latency, etc.)
            endpoint: Network endpoint for remote agents
            version: Agent version

        Returns:
            RegisteredAgent profile
        """
        if metadata is None:
            metadata = AgentMetadata()

        registered = RegisteredAgent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            metadata=metadata,
            endpoint=endpoint,
            version=version
        )

        # Add to registry
        self.registry[agent_id] = registered

        # Update capability index
        for cap in capabilities:
            if cap.name not in self.capability_index:
                self.capability_index[cap.name] = set()
            self.capability_index[cap.name].add(agent_id)

        # Update type index
        if agent_type not in self.type_index:
            self.type_index[agent_type] = set()
        self.type_index[agent_type].add(agent_id)

        # Update stats
        self.stats["total_registrations"] += 1
        self.stats["active_agents"] = len([a for a in self.registry.values() if a.status != AgentStatus.OFFLINE])
        self.stats["total_capabilities"] = len(self.capability_index)

        logger.info(f"📝 Agent registered: {name} ({agent_id})")
        logger.info(f"   Type: {agent_type}")
        logger.info(f"   Capabilities: {[c.name for c in capabilities]}")

        return registered

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from discovery"""
        if agent_id not in self.registry:
            logger.warning(f"⚠️  Cannot unregister unknown agent: {agent_id}")
            return

        agent = self.registry[agent_id]

        # Remove from capability index
        for cap in agent.capabilities:
            if cap.name in self.capability_index:
                self.capability_index[cap.name].discard(agent_id)
                if not self.capability_index[cap.name]:
                    del self.capability_index[cap.name]

        # Remove from type index
        if agent.agent_type in self.type_index:
            self.type_index[agent.agent_type].discard(agent_id)
            if not self.type_index[agent.agent_type]:
                del self.type_index[agent.agent_type]

        # Remove from registry
        del self.registry[agent_id]

        # Update stats
        self.stats["active_agents"] = len([a for a in self.registry.values() if a.status != AgentStatus.OFFLINE])

        logger.info(f"🗑️  Agent unregistered: {agent.name} ({agent_id})")

    async def find_agents(
        self,
        required_capabilities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        only_available: bool = True
    ) -> List[RegisteredAgent]:
        """
        Find agents matching criteria

        Args:
            required_capabilities: List of required capability names
            filters: Additional filters (cost, latency, reputation, etc.)
            limit: Maximum number of results
            sort_by: Sort results by field (e.g., "reputation_score", "cost_per_request")
            only_available: Only return available agents

        Returns:
            List of matching agents
        """
        self.stats["total_discoveries"] += 1

        # Start with all agents
        candidates = list(self.registry.values())

        # Filter by availability
        if only_available:
            candidates = [a for a in candidates if a.is_available()]

        # Filter by required capabilities
        if required_capabilities:
            candidates = [
                a for a in candidates
                if a.matches_capabilities(required_capabilities)
            ]

        # Apply additional filters
        if filters:
            candidates = [a for a in candidates if a.matches_filters(filters)]

        # Sort results
        if sort_by:
            reverse = False
            if sort_by.startswith("-"):
                sort_by = sort_by[1:]
                reverse = True

            if sort_by == "reputation_score":
                candidates.sort(
                    key=lambda a: a.metadata.reputation_score or 0,
                    reverse=not reverse
                )
            elif sort_by == "cost_per_request":
                candidates.sort(
                    key=lambda a: a.metadata.cost_per_request or float('inf'),
                    reverse=reverse
                )
            elif sort_by == "avg_latency_ms":
                candidates.sort(
                    key=lambda a: a.metadata.avg_latency_ms or float('inf'),
                    reverse=reverse
                )
            elif sort_by == "success_rate":
                candidates.sort(
                    key=lambda a: a.metadata.success_rate or 0,
                    reverse=not reverse
                )

        # Limit results
        if limit:
            candidates = candidates[:limit]

        logger.debug(f"🔍 Discovery query: found {len(candidates)} matching agents")

        return candidates

    async def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID"""
        return self.registry.get(agent_id)

    async def update_status(self, agent_id: str, status: AgentStatus):
        """Update agent status"""
        if agent_id in self.registry:
            self.registry[agent_id].status = status
            logger.debug(f"📊 Agent {agent_id} status updated: {status.value}")

    async def update_metadata(self, agent_id: str, metadata: Dict[str, Any]):
        """Update agent metadata"""
        if agent_id in self.registry:
            agent = self.registry[agent_id]
            for key, value in metadata.items():
                if hasattr(agent.metadata, key):
                    setattr(agent.metadata, key, value)
            logger.debug(f"📊 Agent {agent_id} metadata updated")

    async def heartbeat(self, agent_id: str):
        """Record agent heartbeat"""
        if agent_id in self.registry:
            self.registry[agent_id].last_heartbeat = datetime.utcnow().isoformat()

    async def list_capabilities(self) -> List[str]:
        """Get list of all capabilities in the system"""
        return list(self.capability_index.keys())

    async def list_agent_types(self) -> List[str]:
        """Get list of all agent types in the system"""
        return list(self.type_index.keys())

    async def get_stats(self) -> Dict[str, Any]:
        """Get discovery service statistics"""
        return {
            **self.stats,
            "registered_agents": len(self.registry),
            "active_agents": len([a for a in self.registry.values() if a.status == AgentStatus.AVAILABLE]),
            "busy_agents": len([a for a in self.registry.values() if a.status == AgentStatus.BUSY]),
            "offline_agents": len([a for a in self.registry.values() if a.status == AgentStatus.OFFLINE]),
        }

    async def _cleanup_loop(self):
        """Periodically cleanup stale agents (missed heartbeats)"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                now = datetime.utcnow()
                stale_agents = []

                for agent_id, agent in self.registry.items():
                    last_heartbeat = datetime.fromisoformat(agent.last_heartbeat)
                    if now - last_heartbeat > self.heartbeat_timeout:
                        stale_agents.append(agent_id)

                # Mark stale agents as offline
                for agent_id in stale_agents:
                    await self.update_status(agent_id, AgentStatus.OFFLINE)
                    logger.warning(f"⚠️  Agent {agent_id} marked offline (missed heartbeat)")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# Global discovery service instance
_discovery_service: Optional[AgentDiscoveryService] = None


def get_discovery_service() -> AgentDiscoveryService:
    """Get or create global discovery service"""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = AgentDiscoveryService()
    return _discovery_service


__all__ = [
    'AgentStatus',
    'AgentCapability',
    'AgentMetadata',
    'RegisteredAgent',
    'AgentDiscoveryService',
    'get_discovery_service'
]
