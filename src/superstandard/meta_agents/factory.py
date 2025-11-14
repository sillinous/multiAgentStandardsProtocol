"""
Factory Meta-Agent with Discovery Integration

Creates specialized agents on-demand based on requirements.
Enables dynamic agent generation for autonomous workflows.

Enhanced with Agent Discovery Protocol (ADP):
- Checks for existing agents before creating new ones
- Registers new agents with discovery service
- Enables capability-based agent reuse
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass

from ..a2a.protocol import AgentInfo, Capability
from ..a2a.bus import A2AMessageBus, get_message_bus
from ..protocols.discovery import (
    get_discovery_service,
    AgentDiscoveryService,
    AgentCapability,
    AgentMetadata,
    AgentStatus
)


@dataclass
class AgentSpec:
    """Specification for creating an agent"""
    agent_type: str
    name: str
    capabilities: List[str]
    configuration: Dict[str, Any]
    description: str = ""


class FactoryMetaAgent:
    """
    Factory Meta-Agent - Creates Specialized Agents On-Demand

    This meta-agent can dynamically create specialized agents based on
    requirements, enabling truly autonomous system extension.

    Enhanced with Discovery Protocol:
    - Checks for existing agents before creating new ones
    - Registers new agents with discovery service
    - Enables agent reuse and resource optimization

    Capabilities:
    - Create agents from specifications
    - Register agents with A2A bus and discovery
    - Configure agent capabilities
    - Track created agents
    - Find or create agents (smart reuse)
    """

    def __init__(
        self,
        bus: Optional[A2AMessageBus] = None,
        discovery: Optional[AgentDiscoveryService] = None
    ):
        """
        Initialize factory meta-agent

        Args:
            bus: A2A message bus (uses global if not provided)
            discovery: Discovery service (uses global if not provided)
        """
        self.logger = logging.getLogger(__name__)
        self.bus = bus or get_message_bus()
        self.discovery = discovery or get_discovery_service()

        # Factory's own agent info
        self.agent_info = AgentInfo(
            agent_id=f"factory-meta-{uuid.uuid4().hex[:8]}",
            agent_type="meta-agent",
            name="FactoryMetaAgent",
            capabilities=[
                Capability(
                    name="agent_creation",
                    version="1.0.0",
                    description="Creates specialized agents on-demand"
                ),
                Capability(
                    name="agent_discovery",
                    version="1.0.0",
                    description="Discovers existing agents by capability"
                )
            ],
            metadata={
                "role": "factory",
                "meta_level": 1
            }
        )

        # Track created agents
        self.created_agents: Dict[str, AgentInfo] = {}

        # Agent registry (type -> creation function)
        self.agent_registry: Dict[str, callable] = {}

        # Register self with bus
        self.bus.register_agent(self.agent_info)

        self.logger.info(f"✅ FactoryMetaAgent initialized: {self.agent_info.agent_id}")
        self.logger.info(f"   Discovery integration: Enabled")

    def register_agent_type(
        self,
        agent_type: str,
        creation_func: callable
    ):
        """
        Register an agent type that can be created

        Args:
            agent_type: Type identifier for the agent
            creation_func: Function that creates the agent
        """
        self.agent_registry[agent_type] = creation_func
        self.logger.info(f"📝 Registered agent type: {agent_type}")

    async def create_agent(
        self,
        spec: AgentSpec,
        register_with_discovery: bool = True
    ) -> Optional[AgentInfo]:
        """
        Create a specialized agent from specification

        Args:
            spec: Agent specification
            register_with_discovery: Register with discovery service

        Returns:
            AgentInfo for created agent, or None if creation failed
        """
        self.logger.info(f"🏭 Creating agent: {spec.name} (type: {spec.agent_type})")

        try:
            # Check if agent type is registered
            if spec.agent_type not in self.agent_registry:
                # Use generic agent creation
                agent_info = self._create_generic_agent(spec)
            else:
                # Use registered creation function
                creation_func = self.agent_registry[spec.agent_type]
                agent_info = await creation_func(spec)

            if agent_info:
                # Register with bus
                self.bus.register_agent(agent_info)

                # Track created agent
                self.created_agents[agent_info.agent_id] = agent_info

                # Register with discovery service
                if register_with_discovery:
                    await self._register_with_discovery(agent_info, spec)

                self.logger.info(
                    f"✅ Created agent: {agent_info.name} ({agent_info.agent_id})"
                )

                return agent_info
            else:
                self.logger.error(f"❌ Failed to create agent: {spec.name}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error creating agent {spec.name}: {e}", exc_info=True)
            return None

    async def find_or_create_agent(
        self,
        spec: AgentSpec,
        reuse_existing: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentInfo]:
        """
        Find existing agent or create new one

        This is the smart method that checks discovery first!

        Args:
            spec: Agent specification
            reuse_existing: If True, reuse existing agent if found
            filters: Additional filters for discovery search

        Returns:
            AgentInfo for found or created agent
        """
        if reuse_existing:
            # Try to find existing agent with required capabilities
            self.logger.info(
                f"🔍 Searching for existing agent with capabilities: {spec.capabilities}"
            )

            discovered = await self.discovery.find_agents(
                required_capabilities=spec.capabilities,
                filters=filters or {},
                limit=1
            )

            if discovered:
                agent = discovered[0]
                self.logger.info(
                    f"♻️  Found existing agent: {agent.name} ({agent.agent_id})"
                )
                self.logger.info(f"   Reusing instead of creating new agent!")

                # Convert RegisteredAgent to AgentInfo for compatibility
                # (In production, you'd have proper type conversion)
                return self._registered_to_agent_info(agent)

        # No existing agent found, create new one
        self.logger.info(f"📦 No existing agent found, creating new agent...")
        return await self.create_agent(spec)

    def _registered_to_agent_info(self, registered_agent) -> AgentInfo:
        """Convert RegisteredAgent to AgentInfo"""
        # Convert capabilities
        capabilities = [
            Capability(
                name=cap.name,
                version=cap.version,
                description=cap.description
            )
            for cap in registered_agent.capabilities
        ]

        return AgentInfo(
            agent_id=registered_agent.agent_id,
            agent_type=registered_agent.agent_type,
            name=registered_agent.name,
            capabilities=capabilities,
            metadata=registered_agent.metadata.to_dict()
        )

    async def _register_with_discovery(self, agent_info: AgentInfo, spec: AgentSpec):
        """Register newly created agent with discovery service"""
        try:
            capabilities = [
                AgentCapability(
                    name=cap.name,
                    version=cap.version,
                    description=cap.description
                )
                for cap in agent_info.capabilities
            ]

            metadata = AgentMetadata(
                tags=[spec.agent_type, "factory_created"],
                custom={
                    "created_by": self.agent_info.agent_id,
                    "spec_description": spec.description
                }
            )

            await self.discovery.register_agent(
                agent_id=agent_info.agent_id,
                name=agent_info.name,
                agent_type=agent_info.agent_type,
                capabilities=capabilities,
                metadata=metadata
            )

            self.logger.info(f"📝 Registered with discovery: {agent_info.name}")

        except Exception as e:
            self.logger.error(f"⚠️  Failed to register with discovery: {e}")

    def _create_generic_agent(self, spec: AgentSpec) -> AgentInfo:
        """Create a generic agent from specification"""
        agent_id = f"{spec.agent_type}-{uuid.uuid4().hex[:8]}"

        capabilities = [
            Capability(
                name=cap,
                version="1.0.0",
                description=f"{cap} capability"
            )
            for cap in spec.capabilities
        ]

        agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type=spec.agent_type,
            name=spec.name,
            capabilities=capabilities,
            metadata={
                **spec.configuration,
                "created_by": self.agent_info.agent_id,
                "description": spec.description
            }
        )

        return agent_info

    async def create_agent_team(
        self,
        team_specs: List[AgentSpec]
    ) -> List[AgentInfo]:
        """
        Create a team of agents

        Args:
            team_specs: List of agent specifications

        Returns:
            List of created agent infos
        """
        self.logger.info(f"🏗️  Creating agent team: {len(team_specs)} agents")

        created = []
        for spec in team_specs:
            agent_info = await self.create_agent(spec)
            if agent_info:
                created.append(agent_info)

        self.logger.info(f"✅ Created {len(created)}/{len(team_specs)} agents")
        return created

    def get_created_agents(self) -> List[AgentInfo]:
        """Get list of all created agents"""
        return list(self.created_agents.values())

    def get_agent_count(self) -> int:
        """Get count of created agents"""
        return len(self.created_agents)

    def destroy_agent(self, agent_id: str):
        """
        Destroy a created agent

        Args:
            agent_id: ID of agent to destroy
        """
        if agent_id in self.created_agents:
            agent_info = self.created_agents[agent_id]
            self.bus.unregister_agent(agent_id)
            del self.created_agents[agent_id]
            self.logger.info(f"🗑️  Destroyed agent: {agent_info.name} ({agent_id})")
        else:
            self.logger.warning(f"⚠️  Agent {agent_id} not found")

    def get_stats(self) -> Dict[str, Any]:
        """Get factory statistics"""
        return {
            "factory_id": self.agent_info.agent_id,
            "total_agents_created": len(self.created_agents),
            "registered_types": list(self.agent_registry.keys()),
            "active_agents": [
                {
                    "id": agent.agent_id,
                    "type": agent.agent_type,
                    "name": agent.name
                }
                for agent in self.created_agents.values()
            ]
        }
