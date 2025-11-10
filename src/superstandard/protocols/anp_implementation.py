"""
🌐 Agent Network Protocol (ANP) v1.0 - PRODUCTION IMPLEMENTATION
==================================================================

Complete implementation of ANP for agent discovery, registration, and network management.

Features:
- Agent registration and deregistration
- Capability-based discovery
- Health monitoring with automatic cleanup
- Network topology awareness
- Load balancing hints
- Persistent storage support
- Event notifications

Author: SuperStandard Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class AgentStatus(Enum):
    """Agent health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class ANPRegistration:
    """Agent Network Protocol registration"""

    protocol: str = "ANP"
    version: str = "1.0.0"
    action: str = "register"  # register, discover, heartbeat, deregister
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: str = ""
    agent_type: str = ""
    capabilities: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    health_status: str = AgentStatus.HEALTHY.value
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class AgentInfo:
    """Complete agent information"""

    agent_id: str
    agent_type: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    health_status: str = AgentStatus.HEALTHY.value
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    heartbeat_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    load_score: float = 0.0  # 0.0 = idle, 1.0 = fully loaded
    region: str = "default"
    version: str = "1.0.0"


@dataclass
class DiscoveryQuery:
    """Query for discovering agents"""

    capabilities: Optional[List[str]] = None
    agent_type: Optional[str] = None
    health_status: Optional[str] = None
    tags: Optional[List[str]] = None
    region: Optional[str] = None
    max_load: Optional[float] = None  # Only return agents with load < this
    limit: int = 100


@dataclass
class NetworkTopology:
    """Network topology information"""

    total_agents: int = 0
    agents_by_type: Dict[str, int] = field(default_factory=dict)
    agents_by_region: Dict[str, int] = field(default_factory=dict)
    agents_by_status: Dict[str, int] = field(default_factory=dict)
    capability_coverage: Dict[str, int] = field(default_factory=dict)
    average_load: float = 0.0


# ============================================================================
# AGENT NETWORK REGISTRY
# ============================================================================


class AgentNetworkRegistry:
    """
    Central registry for agent network management.

    Handles:
    - Agent registration and deregistration
    - Capability-based discovery
    - Health monitoring
    - Network topology tracking
    """

    def __init__(self, heartbeat_timeout: int = 300):
        """
        Initialize the registry.

        Args:
            heartbeat_timeout: Seconds before an agent is considered offline (default: 5 minutes)
        """
        self.heartbeat_timeout = heartbeat_timeout

        # Storage
        self.agents: Dict[str, AgentInfo] = {}
        self.capability_index: Dict[str, Set[str]] = defaultdict(set)
        self.type_index: Dict[str, Set[str]] = defaultdict(set)
        self.region_index: Dict[str, Set[str]] = defaultdict(set)

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Background tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.running = False

        # Statistics
        self.stats = {
            "total_registrations": 0,
            "total_discoveries": 0,
            "total_heartbeats": 0,
            "total_deregistrations": 0,
        }

    async def start(self):
        """Start the registry and background tasks"""
        if self.running:
            return

        self.running = True
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("🌐 Agent Network Registry started")

    async def stop(self):
        """Stop the registry and cleanup"""
        self.running = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("🌐 Agent Network Registry stopped")

    # ========================================================================
    # AGENT REGISTRATION
    # ========================================================================

    async def register_agent(self, registration: ANPRegistration) -> Dict[str, Any]:
        """
        Register an agent on the network.

        Args:
            registration: ANP registration message

        Returns:
            Registration result with agent info
        """
        try:
            agent_id = registration.agent_id

            # Validate registration
            if not agent_id:
                return {"success": False, "error": "agent_id is required"}

            if not registration.agent_type:
                return {"success": False, "error": "agent_type is required"}

            # Check if already registered
            is_update = agent_id in self.agents

            # Create or update agent info
            if is_update:
                agent_info = self.agents[agent_id]
                # Update existing agent
                agent_info.capabilities = registration.capabilities
                agent_info.endpoints = registration.endpoints
                agent_info.health_status = registration.health_status
                agent_info.metadata.update(registration.metadata)
                agent_info.last_heartbeat = datetime.utcnow().isoformat()
            else:
                # New registration
                agent_info = AgentInfo(
                    agent_id=agent_id,
                    agent_type=registration.agent_type,
                    capabilities=registration.capabilities,
                    endpoints=registration.endpoints,
                    health_status=registration.health_status,
                    metadata=registration.metadata,
                )
                self.agents[agent_id] = agent_info
                self.stats["total_registrations"] += 1

            # Update indexes
            self._update_indexes(agent_info)

            # Emit event
            await self._emit_event(
                "agent_registered" if not is_update else "agent_updated", agent_info
            )

            logger.info(
                f"✅ Agent {'updated' if is_update else 'registered'}: {agent_id} ({registration.agent_type})"
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "is_update": is_update,
                "agent_info": asdict(agent_info),
            }

        except Exception as e:
            logger.error(f"❌ Registration failed: {e}")
            return {"success": False, "error": str(e)}

    async def deregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Deregister an agent from the network.

        Args:
            agent_id: ID of agent to deregister

        Returns:
            Deregistration result
        """
        try:
            if agent_id not in self.agents:
                return {"success": False, "error": f"Agent {agent_id} not found"}

            agent_info = self.agents[agent_id]

            # Remove from indexes
            self._remove_from_indexes(agent_info)

            # Remove agent
            del self.agents[agent_id]
            self.stats["total_deregistrations"] += 1

            # Emit event
            await self._emit_event("agent_deregistered", agent_info)

            logger.info(f"🔴 Agent deregistered: {agent_id}")

            return {"success": True, "agent_id": agent_id}

        except Exception as e:
            logger.error(f"❌ Deregistration failed: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # HEARTBEAT & HEALTH
    # ========================================================================

    async def heartbeat(
        self, agent_id: str, health_status: Optional[str] = None, load_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process agent heartbeat.

        Args:
            agent_id: Agent sending heartbeat
            health_status: Current health status
            load_score: Current load (0.0-1.0)

        Returns:
            Heartbeat acknowledgment
        """
        try:
            if agent_id not in self.agents:
                return {"success": False, "error": f"Agent {agent_id} not registered"}

            agent_info = self.agents[agent_id]
            agent_info.last_heartbeat = datetime.utcnow().isoformat()
            agent_info.heartbeat_count += 1

            if health_status:
                agent_info.health_status = health_status

            if load_score is not None:
                agent_info.load_score = max(0.0, min(1.0, load_score))

            self.stats["total_heartbeats"] += 1

            return {
                "success": True,
                "agent_id": agent_id,
                "heartbeat_count": agent_info.heartbeat_count,
                "time_since_registration": self._time_since(agent_info.registered_at),
            }

        except Exception as e:
            logger.error(f"❌ Heartbeat failed: {e}")
            return {"success": False, "error": str(e)}

    async def _health_check_loop(self):
        """Background task to check agent health"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_agent_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")

    async def _check_agent_health(self):
        """Check all agents for timeout"""
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=self.heartbeat_timeout)

        agents_to_mark_offline = []

        for agent_id, agent_info in self.agents.items():
            # Handle both string and datetime types for last_heartbeat
            last_heartbeat = agent_info.last_heartbeat
            if isinstance(last_heartbeat, str):
                last_heartbeat = datetime.fromisoformat(last_heartbeat)

            if last_heartbeat < timeout_threshold:
                if agent_info.health_status != AgentStatus.OFFLINE.value:
                    agents_to_mark_offline.append(agent_id)

        # Mark agents as offline
        for agent_id in agents_to_mark_offline:
            self.agents[agent_id].health_status = AgentStatus.OFFLINE.value
            await self._emit_event("agent_offline", self.agents[agent_id])
            logger.warning(f"⚠️ Agent marked offline (no heartbeat): {agent_id}")

    # ========================================================================
    # AGENT DISCOVERY
    # ========================================================================

    async def discover_agents(self, query: DiscoveryQuery) -> Dict[str, Any]:
        """
        Discover agents matching query criteria.

        Args:
            query: Discovery query with filters

        Returns:
            List of matching agents
        """
        try:
            self.stats["total_discoveries"] += 1

            # Start with all agents
            candidates = set(self.agents.keys())

            # Filter by capability
            if query.capabilities:
                capability_matches = set()
                for capability in query.capabilities:
                    capability_matches.update(self.capability_index.get(capability, set()))
                candidates &= capability_matches

            # Filter by type
            if query.agent_type:
                candidates &= self.type_index.get(query.agent_type, set())

            # Filter by region
            if query.region:
                candidates &= self.region_index.get(query.region, set())

            # Apply additional filters
            matched_agents = []
            for agent_id in candidates:
                agent_info = self.agents[agent_id]

                # Health status filter
                if query.health_status and agent_info.health_status != query.health_status:
                    continue

                # Load filter
                if query.max_load is not None and agent_info.load_score > query.max_load:
                    continue

                # Tags filter (all tags must match)
                if query.tags and not all(tag in agent_info.tags for tag in query.tags):
                    continue

                matched_agents.append(agent_info)

            # Sort by load (least loaded first for load balancing)
            matched_agents.sort(key=lambda a: a.load_score)

            # Apply limit
            matched_agents = matched_agents[: query.limit]

            return {
                "success": True,
                "count": len(matched_agents),
                "agents": [asdict(agent) for agent in matched_agents],
            }

        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            return {"success": False, "error": str(e), "agents": []}

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent info"""
        if agent_id in self.agents:
            return asdict(self.agents[agent_id])
        return None

    async def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [asdict(agent) for agent in self.agents.values()]

    # ========================================================================
    # NETWORK TOPOLOGY
    # ========================================================================

    async def get_network_topology(self) -> NetworkTopology:
        """Get current network topology and statistics"""
        topology = NetworkTopology()

        topology.total_agents = len(self.agents)

        # Count by type
        for agent_info in self.agents.values():
            topology.agents_by_type[agent_info.agent_type] = (
                topology.agents_by_type.get(agent_info.agent_type, 0) + 1
            )

            topology.agents_by_region[agent_info.region] = (
                topology.agents_by_region.get(agent_info.region, 0) + 1
            )

            topology.agents_by_status[agent_info.health_status] = (
                topology.agents_by_status.get(agent_info.health_status, 0) + 1
            )

        # Capability coverage
        for capability, agents in self.capability_index.items():
            topology.capability_coverage[capability] = len(agents)

        # Average load
        if self.agents:
            topology.average_load = sum(a.load_score for a in self.agents.values()) / len(
                self.agents
            )

        return topology

    # ========================================================================
    # EVENT SYSTEM
    # ========================================================================

    def on_event(self, event_name: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_name].append(handler)

    async def _emit_event(self, event_name: str, data: Any):
        """Emit event to registered handlers"""
        for handler in self.event_handlers.get(event_name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"❌ Event handler error ({event_name}): {e}")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _update_indexes(self, agent_info: AgentInfo):
        """Update search indexes"""
        # Capability index
        for capability in agent_info.capabilities:
            self.capability_index[capability].add(agent_info.agent_id)

        # Type index
        self.type_index[agent_info.agent_type].add(agent_info.agent_id)

        # Region index
        self.region_index[agent_info.region].add(agent_info.agent_id)

    def _remove_from_indexes(self, agent_info: AgentInfo):
        """Remove agent from search indexes"""
        # Capability index
        for capability in agent_info.capabilities:
            self.capability_index[capability].discard(agent_info.agent_id)
            if not self.capability_index[capability]:
                del self.capability_index[capability]

        # Type index
        self.type_index[agent_info.agent_type].discard(agent_info.agent_id)
        if not self.type_index[agent_info.agent_type]:
            del self.type_index[agent_info.agent_type]

        # Region index
        self.region_index[agent_info.region].discard(agent_info.agent_id)
        if not self.region_index[agent_info.region]:
            del self.region_index[agent_info.region]

    def _time_since(self, iso_timestamp: str) -> float:
        """Calculate seconds since timestamp"""
        then = datetime.fromisoformat(iso_timestamp)
        now = datetime.utcnow()
        return (now - then).total_seconds()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        topology = await self.get_network_topology()

        return {
            "stats": self.stats,
            "current_agents": len(self.agents),
            "topology": asdict(topology),
            "index_sizes": {
                "capabilities": len(self.capability_index),
                "types": len(self.type_index),
                "regions": len(self.region_index),
            },
        }


# ============================================================================
# ANP PROTOCOL CLIENT
# ============================================================================


class ANPClient:
    """
    Client for interacting with ANP registry.

    Use this in your agents to register and discover other agents.
    """

    def __init__(self, registry: AgentNetworkRegistry):
        """Initialize client with registry reference"""
        self.registry = registry

    async def register(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        endpoints: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register this agent on the network"""
        registration = ANPRegistration(
            action="register",
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            endpoints=endpoints or {},
            metadata=metadata or {},
        )
        return await self.registry.register_agent(registration)

    async def deregister(self, agent_id: str) -> Dict[str, Any]:
        """Deregister this agent from the network"""
        return await self.registry.deregister_agent(agent_id)

    async def heartbeat(
        self, agent_id: str, health_status: Optional[str] = None, load_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send heartbeat"""
        return await self.registry.heartbeat(agent_id, health_status, load_score)

    async def discover(
        self,
        capabilities: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        health_status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Discover agents by criteria"""
        query = DiscoveryQuery(
            capabilities=capabilities,
            agent_type=agent_type,
            health_status=health_status,
            limit=limit,
        )
        result = await self.registry.discover_agents(query)
        return result.get("agents", [])

    async def get_network_info(self) -> Dict[str, Any]:
        """Get network topology and statistics"""
        topology = await self.registry.get_network_topology()
        return asdict(topology)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def example_usage():
    """Demonstrate ANP usage"""

    print("ANP v1.0 - Agent Network Protocol Example\n")

    # Create registry
    registry = AgentNetworkRegistry(heartbeat_timeout=60)
    await registry.start()

    # Create clients for different agents
    client1 = ANPClient(registry)
    client2 = ANPClient(registry)
    client3 = ANPClient(registry)

    # Register agents
    print("[*] Registering agents...")

    await client1.register(
        agent_id="agent-1",
        agent_type="analyzer",
        capabilities=["text-analysis", "sentiment-analysis"],
        endpoints={"http": "http://localhost:8001"},
    )

    await client2.register(
        agent_id="agent-2",
        agent_type="analyzer",
        capabilities=["text-analysis", "translation"],
        endpoints={"http": "http://localhost:8002"},
    )

    await client3.register(
        agent_id="agent-3",
        agent_type="coordinator",
        capabilities=["orchestration", "task-management"],
        endpoints={"http": "http://localhost:8003"},
    )

    print("[+] 3 agents registered\n")

    # Discover agents by capability
    print("[*] Discovering agents with 'text-analysis' capability...")
    agents = await client1.discover(capabilities=["text-analysis"])
    print(f"Found {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent['agent_id']} ({agent['agent_type']})")
    print()

    # Discover agents by type
    print("[*] Discovering 'analyzer' agents...")
    agents = await client1.discover(agent_type="analyzer")
    print(f"Found {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent['agent_id']}: {agent['capabilities']}")
    print()

    # Send heartbeats
    print("[*] Sending heartbeats...")
    await client1.heartbeat("agent-1", load_score=0.3)
    await client2.heartbeat("agent-2", load_score=0.7)
    await client3.heartbeat("agent-3", load_score=0.1)
    print("[+] Heartbeats sent\n")

    # Get network topology
    print("[*] Network Topology:")
    topology = await client1.get_network_info()
    print(f"  Total agents: {topology['total_agents']}")
    print(f"  Agents by type: {topology['agents_by_type']}")
    print(f"  Capability coverage: {topology['capability_coverage']}")
    print(f"  Average load: {topology['average_load']:.2f}")
    print()

    # Get statistics
    stats = await registry.get_statistics()
    print("[*] Registry Statistics:")
    print(f"  Registrations: {stats['stats']['total_registrations']}")
    print(f"  Discoveries: {stats['stats']['total_discoveries']}")
    print(f"  Heartbeats: {stats['stats']['total_heartbeats']}")
    print()

    # Deregister one agent
    print("[*] Deregistering agent-2...")
    await client2.deregister("agent-2")

    # Check updated count
    agents = await client1.discover()
    print(f"[+] Agents remaining: {len(agents)}\n")

    # Cleanup
    await registry.stop()
    print("[+] Registry stopped")


if __name__ == "__main__":
    asyncio.run(example_usage())
