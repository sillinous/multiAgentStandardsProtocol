"""
Network Mixin for BaseAgent - Seamless ANP Integration

This module provides a mixin that adds network awareness capabilities to any BaseAgent,
enabling agents to participate in agent networks for discovery, registration, and
health monitoring.

Usage:
    from superstandard.agents.base.base_agent import BaseAgent
    from superstandard.agents.base.network_mixin import NetworkAwareMixin
    from superstandard.protocols.anp_implementation import AgentStatus

    class MyAgent(NetworkAwareMixin, BaseAgent):
        async def execute_task(self, task):
            # Agent can now use network features
            peers = await self.discover_agents(capabilities=["analysis"])
            await self.send_heartbeat()
            return result

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# Import ANP protocol
try:
    from superstandard.protocols.anp_implementation import (
        AgentNetworkRegistry,
        ANPRegistration,
        AgentStatus,
        DiscoveryQuery,
    )

    ANP_AVAILABLE = True
except ImportError:
    ANP_AVAILABLE = False

    class AgentStatus:
        HEALTHY = "healthy"


class NetworkError(Exception):
    """Raised when network operations fail"""

    pass


class NetworkAwareMixin:
    """
    Mixin that adds network awareness capabilities to BaseAgent.

    This mixin provides:
    - Agent registration with network registry
    - Capability-based agent discovery
    - Automatic heartbeat management
    - Health status reporting
    - Network topology awareness

    Methods added to agent:
    - register_on_network(registry) - Register with network
    - deregister_from_network() - Leave network
    - discover_agents(query) - Find other agents
    - send_heartbeat() - Report health status
    - update_status(status) - Update health status
    - get_network_info() - Get network membership info
    """

    def __init__(self, *args, **kwargs):
        """Initialize network awareness capabilities."""
        super().__init__(*args, **kwargs)

        # Network state
        self._network_registry: Optional["AgentNetworkRegistry"] = None
        self._network_enabled = ANP_AVAILABLE
        self._network_registered = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds
        self._last_heartbeat_time: Optional[datetime] = None

    async def register_on_network(
        self,
        registry: "AgentNetworkRegistry",
        endpoints: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_heartbeat: bool = True,
    ) -> bool:
        """
        Register agent with network registry.

        This makes the agent discoverable by other agents in the network.

        Args:
            registry: The AgentNetworkRegistry to join
            endpoints: Agent endpoints (e.g., {"http": "http://localhost:8000"})
            metadata: Additional metadata about the agent
            auto_heartbeat: Whether to automatically send heartbeats

        Returns:
            True if successfully registered

        Raises:
            NetworkError: If ANP protocol not available

        Example:
            registry = AgentNetworkRegistry()
            await agent.register_on_network(
                registry,
                endpoints={"http": "http://localhost:8001"},
                metadata={"version": "1.0.0"}
            )
        """
        if not self._network_enabled:
            raise NetworkError("ANP protocol not available. Install anp_implementation module.")

        if self._network_registered and self._network_registry is not None:
            # Already registered - deregister first
            await self.deregister_from_network()

        # Build registration
        registration = ANPRegistration(
            action="register",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            capabilities=self.capabilities_list if hasattr(self, "capabilities_list") else [],
            endpoints=endpoints or {},
            health_status=AgentStatus.HEALTHY.value,
            metadata=metadata or {},
        )

        # Register with registry
        success = await registry.register_agent(registration)

        if success:
            self._network_registry = registry
            self._network_registered = True

            # Start auto-heartbeat if enabled
            if auto_heartbeat:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            print(f"[{self.agent_id}] Registered on network")
            print(f"  Registry: {id(registry)}")
            print(f"  Capabilities: {', '.join(registration.capabilities)}")
            print(f"  Auto-heartbeat: {auto_heartbeat}")

        return success

    async def deregister_from_network(self) -> bool:
        """
        Deregister agent from network.

        Returns:
            True if successfully deregistered
        """
        if not self._network_registered or self._network_registry is None:
            return False

        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Deregister
        registration = ANPRegistration(
            action="deregister", agent_id=self.agent_id, agent_type=self.agent_type
        )

        success = await self._network_registry.deregister_agent(self.agent_id)

        if success:
            self._network_registry = None
            self._network_registered = False

            print(f"[{self.agent_id}] Deregistered from network")

        return success

    async def discover_agents(
        self,
        capabilities: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        health_status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        region: Optional[str] = None,
        max_load: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Discover other agents in the network.

        Args:
            capabilities: Required capabilities
            agent_type: Specific agent type
            health_status: Required health status (e.g., "healthy")
            tags: Required tags
            region: Specific region
            max_load: Maximum load score
            limit: Maximum number of results

        Returns:
            List of agent information dictionaries

        Raises:
            NetworkError: If not registered on network

        Example:
            # Find all healthy analysis agents
            analysts = await agent.discover_agents(
                capabilities=["analysis"],
                health_status="healthy"
            )

            for analyst in analysts:
                print(f"Found: {analyst['agent_id']}")
        """
        if not self._network_registered or self._network_registry is None:
            raise NetworkError("Agent must be registered on network to discover agents")

        # Build query
        query = DiscoveryQuery(
            capabilities=capabilities,
            agent_type=agent_type,
            health_status=health_status,
            tags=tags,
            region=region,
            max_load=max_load,
            limit=limit,
        )

        # Execute discovery
        result = await self._network_registry.discover_agents(query)

        if not result.get("success"):
            return []

        # Return list of agent info dicts (already in dict format from asdict())
        return result.get("agents", [])

    async def send_heartbeat(
        self, health_status: Optional[str] = None, load_score: Optional[float] = None
    ) -> bool:
        """
        Send heartbeat to network registry.

        Args:
            health_status: Current health status
            load_score: Current load (0.0 = idle, 1.0 = fully loaded)

        Returns:
            True if heartbeat successful

        Example:
            # Report healthy with 30% load
            await agent.send_heartbeat(
                health_status="healthy",
                load_score=0.3
            )
        """
        if not self._network_registered or self._network_registry is None:
            return False

        # Build heartbeat
        registration = ANPRegistration(
            action="heartbeat",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            health_status=health_status or AgentStatus.HEALTHY.value,
            metadata={"load_score": load_score} if load_score is not None else {},
        )

        success = await self._network_registry.heartbeat(
            self.agent_id, health_status or AgentStatus.HEALTHY.value, load_score or 0.0
        )

        if success:
            self._last_heartbeat_time = datetime.utcnow()

        return success

    async def update_status(self, health_status: str, load_score: Optional[float] = None) -> bool:
        """
        Update agent health status.

        Args:
            health_status: New health status
            load_score: Current load score

        Returns:
            True if update successful
        """
        return await self.send_heartbeat(health_status, load_score)

    async def get_network_info(self) -> Dict[str, Any]:
        """
        Get agent's network membership information.

        Returns:
            Dictionary with network info:
            - registered: Whether agent is registered
            - registry_id: ID of registry (if registered)
            - last_heartbeat: Last heartbeat timestamp
            - auto_heartbeat: Whether auto-heartbeat is enabled
            - network_enabled: Whether ANP is available
        """
        return {
            "agent_id": self.agent_id,
            "registered": self._network_registered,
            "registry_id": id(self._network_registry) if self._network_registry else None,
            "last_heartbeat": (
                self._last_heartbeat_time.isoformat() if self._last_heartbeat_time else None
            ),
            "auto_heartbeat": self._heartbeat_task is not None,
            "heartbeat_interval": self._heartbeat_interval,
            "network_enabled": self._network_enabled,
        }

    async def _heartbeat_loop(self):
        """Internal heartbeat loop for auto-heartbeat."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Heartbeat error: {e}")

    def is_on_network(self) -> bool:
        """
        Check if agent is registered on a network.

        Returns:
            True if registered on network
        """
        return self._network_registered

    def get_network_registry(self) -> Optional["AgentNetworkRegistry"]:
        """
        Get the network registry this agent is registered with.

        Returns:
            AgentNetworkRegistry or None
        """
        return self._network_registry


# Convenience decorator
def network_aware(agent_class):
    """
    Decorator to add network awareness to an agent class.

    Usage:
        @network_aware
        class MyAgent(BaseAgent):
            # Agent automatically has network methods
            pass

    Args:
        agent_class: The agent class to enhance

    Returns:
        Enhanced class with network capabilities
    """

    class NetworkAwareAgent(NetworkAwareMixin, agent_class):
        pass

    NetworkAwareAgent.__name__ = agent_class.__name__
    NetworkAwareAgent.__module__ = agent_class.__module__

    return NetworkAwareAgent


__all__ = [
    "NetworkAwareMixin",
    "NetworkError",
    "network_aware",
]
