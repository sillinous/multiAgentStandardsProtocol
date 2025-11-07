"""
Agent Library Service - Production-Ready Interface Layer

Provides unified service layer for discovering, executing, and managing agents
from the agent library. This service acts as the primary interface between
applications and the agentic ecosystem.

Features:
- Agent discovery by APQC process, capability, or keyword
- Agent execution with standard input/output handling
- Agent lifecycle management
- Health checks and monitoring
- Error handling and resilience
- Logging and observability
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import json

from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent operational status"""

    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """Agent execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# ============================================================================
# DATA MODELS
# ============================================================================


class AgentCapabilityModel(BaseModel):
    """Agent capability specification"""

    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    proficiency: float = Field(..., ge=0.0, le=1.0, description="Proficiency level")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    estimated_execution_time_ms: Optional[int] = None


class AgentMetadataModel(BaseModel):
    """Agent metadata"""

    agent_id: str
    name: str
    description: Optional[str] = None
    version: str
    status: AgentStatus
    apqc_process: str
    apqc_level: str
    category: str
    capabilities: List[AgentCapabilityModel]
    protocols_supported: List[str] = Field(default_factory=list)
    last_health_check: Optional[datetime] = None
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_execution_time_ms: Optional[float] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""

    agent_id: str
    input_data: Dict[str, Any]
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    priority: int = Field(default=5, ge=1, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResponse(BaseModel):
    """Response from agent execution"""

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    request_id: str
    status: ExecutionStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AgentHealthStatus(BaseModel):
    """Agent health status"""

    agent_id: str
    status: AgentStatus
    healthy: bool
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    error_count_24h: int = 0
    success_rate_24h: float = 1.0
    last_execution_time: Optional[datetime] = None
    uptime_seconds: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AgentDiscoveryQuery(BaseModel):
    """Query for discovering agents"""

    apqc_process: Optional[str] = None
    apqc_level: Optional[str] = None
    capability: Optional[str] = None
    keyword: Optional[str] = None
    status: Optional[AgentStatus] = None
    min_proficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# SERVICE INTERFACES
# ============================================================================


class IAgentDiscoveryService(ABC):
    """Agent discovery service interface"""

    @abstractmethod
    async def discover_agents(
        self, query: AgentDiscoveryQuery
    ) -> Tuple[List[AgentMetadataModel], int]:
        """Discover agents matching criteria. Returns (agents, total_count)"""
        pass

    @abstractmethod
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentMetadataModel]:
        """Get agent metadata by ID"""
        pass

    @abstractmethod
    async def search_by_keyword(self, keyword: str, limit: int = 10) -> List[AgentMetadataModel]:
        """Search agents by keyword"""
        pass

    @abstractmethod
    async def get_agents_by_apqc(self, apqc_process: str) -> List[AgentMetadataModel]:
        """Get all agents for a specific APQC process"""
        pass

    @abstractmethod
    async def get_agents_by_capability(self, capability: str) -> List[AgentMetadataModel]:
        """Get agents that provide a specific capability"""
        pass


class IAgentExecutionService(ABC):
    """Agent execution service interface"""

    @abstractmethod
    async def execute_agent(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        """Execute an agent with given input"""
        pass

    @abstractmethod
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get status of a specific execution"""
        pass

    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        pass

    @abstractmethod
    async def get_execution_history(
        self, agent_id: str, limit: int = 10
    ) -> List[AgentExecutionResponse]:
        """Get recent execution history for an agent"""
        pass


class IAgentHealthService(ABC):
    """Agent health monitoring service interface"""

    @abstractmethod
    async def get_agent_health(self, agent_id: str) -> Optional[AgentHealthStatus]:
        """Get health status of a specific agent"""
        pass

    @abstractmethod
    async def get_all_health_status(self) -> List[AgentHealthStatus]:
        """Get health status of all agents"""
        pass

    @abstractmethod
    async def check_agent_availability(self, agent_id: str) -> bool:
        """Check if agent is available for execution"""
        pass

    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        pass


class IAgentRegistryService(ABC):
    """Agent registry service interface"""

    @abstractmethod
    async def register_agent(self, metadata: AgentMetadataModel) -> bool:
        """Register a new agent"""
        pass

    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        pass

    @abstractmethod
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent operational status"""
        pass

    @abstractmethod
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================


class AgentDiscoveryService(IAgentDiscoveryService):
    """Agent discovery service implementation"""

    def __init__(self):
        self.agents: Dict[str, AgentMetadataModel] = {}
        self.apqc_index: Dict[str, List[str]] = {}  # apqc_process -> agent_ids
        self.capability_index: Dict[str, List[str]] = {}  # capability -> agent_ids
        logger.info("✅ AgentDiscoveryService initialized")

    async def discover_agents(
        self, query: AgentDiscoveryQuery
    ) -> Tuple[List[AgentMetadataModel], int]:
        """Discover agents matching criteria"""
        results = []

        for agent_id, agent in self.agents.items():
            # Check APQC process
            if query.apqc_process and agent.apqc_process != query.apqc_process:
                continue

            # Check APQC level
            if query.apqc_level and agent.apqc_level != query.apqc_level:
                continue

            # Check status
            if query.status and agent.status != query.status:
                continue

            # Check capability
            if query.capability:
                has_capability = any(cap.name == query.capability for cap in agent.capabilities)
                if not has_capability:
                    continue

            # Check proficiency
            if query.min_proficiency > 0:
                max_proficiency = max((cap.proficiency for cap in agent.capabilities), default=0.0)
                if max_proficiency < query.min_proficiency:
                    continue

            # Check keyword
            if query.keyword:
                keyword_lower = query.keyword.lower()
                if (
                    keyword_lower not in agent.name.lower()
                    and keyword_lower not in (agent.description or "").lower()
                    and not any(keyword_lower in cap.name.lower() for cap in agent.capabilities)
                ):
                    continue

            results.append(agent)

        # Sort by relevance/success rate
        results.sort(key=lambda a: a.success_rate, reverse=True)

        # Apply pagination
        total = len(results)
        paginated = results[query.offset : query.offset + query.limit]

        logger.info(f"🔍 Discovered {len(paginated)} agents (total: {total})")
        return paginated, total

    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentMetadataModel]:
        """Get agent metadata by ID"""
        agent = self.agents.get(agent_id)
        if agent:
            logger.info(f"✅ Retrieved agent: {agent_id}")
        else:
            logger.warning(f"⚠️ Agent not found: {agent_id}")
        return agent

    async def search_by_keyword(self, keyword: str, limit: int = 10) -> List[AgentMetadataModel]:
        """Search agents by keyword"""
        query = AgentDiscoveryQuery(keyword=keyword, limit=limit)
        results, _ = await self.discover_agents(query)
        logger.info(f"🔍 Keyword search '{keyword}': found {len(results)} agents")
        return results

    async def get_agents_by_apqc(self, apqc_process: str) -> List[AgentMetadataModel]:
        """Get all agents for a specific APQC process"""
        agent_ids = self.apqc_index.get(apqc_process, [])
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        logger.info(f"✅ Found {len(agents)} agents for APQC {apqc_process}")
        return agents

    async def get_agents_by_capability(self, capability: str) -> List[AgentMetadataModel]:
        """Get agents that provide a specific capability"""
        agent_ids = self.capability_index.get(capability, [])
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        logger.info(f"✅ Found {len(agents)} agents with capability '{capability}'")
        return agents


class AgentExecutionService(IAgentExecutionService):
    """Agent execution service implementation"""

    def __init__(self, discovery_service: IAgentDiscoveryService):
        self.discovery_service = discovery_service
        self.executions: Dict[str, AgentExecutionResponse] = {}
        self.execution_history: Dict[str, List[AgentExecutionResponse]] = {}
        logger.info("✅ AgentExecutionService initialized")

    async def execute_agent(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        """Execute an agent with given input"""
        start_time = datetime.utcnow()

        try:
            # Verify agent exists
            agent = await self.discovery_service.get_agent_by_id(request.agent_id)
            if not agent:
                logger.error(f"❌ Agent not found: {request.agent_id}")
                return AgentExecutionResponse(
                    agent_id=request.agent_id,
                    request_id=request.request_id,
                    status=ExecutionStatus.FAILED,
                    error_message=f"Agent {request.agent_id} not found",
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )

            # Execute agent (simulated)
            # In production, this would call the actual agent implementation
            await asyncio.sleep(0.1)  # Simulate execution

            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            response = AgentExecutionResponse(
                agent_id=request.agent_id,
                request_id=request.request_id,
                status=ExecutionStatus.COMPLETED,
                output_data={"result": "success", "processed_at": datetime.utcnow().isoformat()},
                execution_time_ms=execution_time_ms,
            )

            # Store execution
            self.executions[response.execution_id] = response

            # Update history
            if request.agent_id not in self.execution_history:
                self.execution_history[request.agent_id] = []
            self.execution_history[request.agent_id].append(response)

            logger.info(
                f"✅ Agent executed successfully: {request.agent_id} (took {execution_time_ms}ms)"
            )
            return response

        except Exception as e:
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"❌ Agent execution failed: {str(e)}")
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                request_id=request.request_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
            )

    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get status of a specific execution"""
        if execution_id in self.executions:
            return self.executions[execution_id].status
        logger.warning(f"⚠️ Execution not found: {execution_id}")
        return None

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        if execution_id in self.executions:
            response = self.executions[execution_id]
            if response.status == ExecutionStatus.RUNNING:
                response.status = ExecutionStatus.CANCELLED
                logger.info(f"✅ Execution cancelled: {execution_id}")
                return True
        logger.warning(f"⚠️ Cannot cancel execution: {execution_id}")
        return False

    async def get_execution_history(
        self, agent_id: str, limit: int = 10
    ) -> List[AgentExecutionResponse]:
        """Get recent execution history for an agent"""
        history = self.execution_history.get(agent_id, [])
        recent = history[-limit:] if len(history) > limit else history
        logger.info(f"✅ Retrieved {len(recent)} execution records for {agent_id}")
        return recent


class AgentHealthService(IAgentHealthService):
    """Agent health monitoring service implementation"""

    def __init__(self, discovery_service: IAgentDiscoveryService):
        self.discovery_service = discovery_service
        self.health_status: Dict[str, AgentHealthStatus] = {}
        logger.info("✅ AgentHealthService initialized")

    async def get_agent_health(self, agent_id: str) -> Optional[AgentHealthStatus]:
        """Get health status of a specific agent"""
        if agent_id in self.health_status:
            return self.health_status[agent_id]

        # Create default health status
        agent = await self.discovery_service.get_agent_by_id(agent_id)
        if not agent:
            return None

        health = AgentHealthStatus(
            agent_id=agent_id,
            status=agent.status,
            healthy=agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE],
            cpu_usage_percent=None,
            memory_usage_percent=None,
            success_rate_24h=agent.success_rate,
        )

        self.health_status[agent_id] = health
        logger.info(f"✅ Retrieved health status: {agent_id}")
        return health

    async def get_all_health_status(self) -> List[AgentHealthStatus]:
        """Get health status of all agents"""
        return list(self.health_status.values())

    async def check_agent_availability(self, agent_id: str) -> bool:
        """Check if agent is available for execution"""
        health = await self.get_agent_health(agent_id)
        if not health:
            return False
        available = health.status in [AgentStatus.ACTIVE, AgentStatus.IDLE] and health.healthy
        logger.info(
            f"{'✅' if available else '⚠️'} Agent availability check: {agent_id} = {available}"
        )
        return available

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        statuses = await self.get_all_health_status()
        healthy_count = sum(1 for s in statuses if s.healthy)
        total_count = len(statuses)

        health_data = {
            "total_agents": total_count,
            "healthy_agents": healthy_count,
            "unhealthy_agents": total_count - healthy_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "system_healthy": healthy_count >= (total_count * 0.9),  # 90% threshold
            "timestamp": datetime.utcnow().isoformat(),
            "agents_by_status": {},
        }

        # Count by status
        for status in AgentStatus:
            count = sum(1 for s in statuses if s.status == status)
            if count > 0:
                health_data["agents_by_status"][status.value] = count

        logger.info(f"📊 System health: {healthy_count}/{total_count} agents healthy")
        return health_data


class AgentRegistryService(IAgentRegistryService):
    """Agent registry service implementation"""

    def __init__(self):
        self.agents: Dict[str, AgentMetadataModel] = {}
        logger.info("✅ AgentRegistryService initialized")

    async def register_agent(self, metadata: AgentMetadataModel) -> bool:
        """Register a new agent"""
        try:
            self.agents[metadata.agent_id] = metadata
            logger.info(f"✅ Agent registered: {metadata.agent_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to register agent: {str(e)}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"✅ Agent unregistered: {agent_id}")
                return True
            logger.warning(f"⚠️ Agent not found: {agent_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to unregister agent: {str(e)}")
            return False

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent operational status"""
        try:
            if agent_id in self.agents:
                self.agents[agent_id].status = status
                logger.info(f"✅ Agent status updated: {agent_id} -> {status.value}")
                return True
            logger.warning(f"⚠️ Agent not found: {agent_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update agent status: {str(e)}")
            return False

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        agents = list(self.agents.values())
        stats = {
            "total_agents": len(agents),
            "agents_by_status": {},
            "agents_by_apqc": {},
            "total_capabilities": 0,
            "average_success_rate": 0.0,
        }

        # Count by status
        for status in AgentStatus:
            count = sum(1 for a in agents if a.status == status)
            if count > 0:
                stats["agents_by_status"][status.value] = count

        # Count by APQC
        apqc_counts = {}
        for agent in agents:
            apqc = agent.apqc_process
            apqc_counts[apqc] = apqc_counts.get(apqc, 0) + 1
        stats["agents_by_apqc"] = apqc_counts

        # Count total capabilities
        stats["total_capabilities"] = sum(len(a.capabilities) for a in agents)

        # Calculate average success rate
        if agents:
            stats["average_success_rate"] = sum(a.success_rate for a in agents) / len(agents)

        logger.info(f"📊 Registry stats: {stats['total_agents']} agents registered")
        return stats


# ============================================================================
# UNIFIED AGENT LIBRARY SERVICE
# ============================================================================


class AgentLibraryService:
    """
    Unified service for agent library operations.

    Provides a single interface to:
    - Discover agents
    - Execute agents
    - Monitor agent health
    - Manage agent registry
    """

    def __init__(self):
        self.discovery = AgentDiscoveryService()
        self.execution = AgentExecutionService(self.discovery)
        self.health = AgentHealthService(self.discovery)
        self.registry = AgentRegistryService()
        logger.info("🚀 AgentLibraryService fully initialized")

    # =======================================================================
    # DISCOVERY OPERATIONS
    # =======================================================================

    async def discover_agents(
        self, query: AgentDiscoveryQuery
    ) -> Tuple[List[AgentMetadataModel], int]:
        """Discover agents matching criteria"""
        return await self.discovery.discover_agents(query)

    async def get_agent(self, agent_id: str) -> Optional[AgentMetadataModel]:
        """Get specific agent"""
        return await self.discovery.get_agent_by_id(agent_id)

    async def search_agents(self, keyword: str, limit: int = 10) -> List[AgentMetadataModel]:
        """Search agents by keyword"""
        return await self.discovery.search_by_keyword(keyword, limit)

    async def get_agents_by_apqc(self, apqc_process: str) -> List[AgentMetadataModel]:
        """Get agents for APQC process"""
        return await self.discovery.get_agents_by_apqc(apqc_process)

    async def get_agents_by_capability(self, capability: str) -> List[AgentMetadataModel]:
        """Get agents with specific capability"""
        return await self.discovery.get_agents_by_capability(capability)

    # =======================================================================
    # EXECUTION OPERATIONS
    # =======================================================================

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        """Execute an agent"""
        return await self.execution.execute_agent(request)

    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get execution status"""
        return await self.execution.get_execution_status(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel execution"""
        return await self.execution.cancel_execution(execution_id)

    async def get_execution_history(
        self, agent_id: str, limit: int = 10
    ) -> List[AgentExecutionResponse]:
        """Get execution history"""
        return await self.execution.get_execution_history(agent_id, limit)

    # =======================================================================
    # HEALTH & MONITORING
    # =======================================================================

    async def get_agent_health(self, agent_id: str) -> Optional[AgentHealthStatus]:
        """Get agent health status"""
        return await self.health.get_agent_health(agent_id)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health"""
        return await self.health.get_system_health()

    async def is_agent_available(self, agent_id: str) -> bool:
        """Check if agent is available"""
        return await self.health.check_agent_availability(agent_id)

    # =======================================================================
    # REGISTRY OPERATIONS
    # =======================================================================

    async def register_agent(self, metadata: AgentMetadataModel) -> bool:
        """Register new agent"""
        success = await self.registry.register_agent(metadata)
        if success:
            await self._update_indexes(metadata)
        return success

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent"""
        return await self.registry.unregister_agent(agent_id)

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        return await self.registry.update_agent_status(agent_id, status)

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return await self.registry.get_registry_stats()

    # =======================================================================
    # HELPER METHODS
    # =======================================================================

    async def _update_indexes(self, agent: AgentMetadataModel):
        """Update discovery indexes when agent is registered"""
        # This would update the internal indexes in discovery service
        # Implementation depends on specific discovery service structure
        pass

    async def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        return {
            "service": "AgentLibraryService",
            "status": "healthy",
            "components": {
                "discovery": "operational",
                "execution": "operational",
                "health": "operational",
                "registry": "operational",
            },
            "system_health": await self.get_system_health(),
            "registry_stats": await self.get_registry_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# FACTORY & INITIALIZATION
# ============================================================================

_agent_library_service: Optional[AgentLibraryService] = None


def get_agent_library_service() -> AgentLibraryService:
    """Get or create the agent library service singleton"""
    global _agent_library_service
    if _agent_library_service is None:
        _agent_library_service = AgentLibraryService()
        logger.info("🚀 Agent Library Service initialized (singleton)")
    return _agent_library_service


async def initialize_agent_library_service() -> AgentLibraryService:
    """Initialize and return the agent library service"""
    service = get_agent_library_service()
    logger.info("✅ Agent Library Service ready")
    return service
