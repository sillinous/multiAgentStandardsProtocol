"""
Agent Library Service Routes

Provides REST API endpoints for the Agent Library Service, enabling:
- Agent discovery and search
- Agent execution and monitoring
- Health status tracking
- Agent registration and management
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.services.agent_library_service import (
    get_agent_library_service,
    AgentLibraryService,
    AgentMetadataModel,
    AgentExecutionRequest,
    AgentExecutionResponse,
    ExecutionStatus,
    AgentStatus,
)

logger = logging.getLogger(__name__)

# Create router for Agent Library endpoints
router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agent Library"],
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    },
)


# ============================================================================
# Request/Response Models
# ============================================================================

class AgentDiscoveryRequest(BaseModel):
    """Request for agent discovery"""
    apqc_process: Optional[str] = Field(
        None, description="Filter by APQC process (e.g., '3.0', '4.0')"
    )
    apqc_level: Optional[str] = Field(
        None, description="Filter by APQC level (e.g., 'strategy', 'process')"
    )
    capability: Optional[str] = Field(
        None, description="Filter by capability name"
    )
    keyword: Optional[str] = Field(
        None, description="Search by keyword in agent name/description"
    )
    status: Optional[str] = Field(
        None, description="Filter by agent status (draft, staging, production, deprecated)"
    )
    min_proficiency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum proficiency level (0.0-1.0)"
    )
    skip: int = Field(0, ge=0, description="Pagination: number of items to skip")
    limit: int = Field(10, ge=1, le=100, description="Pagination: max items to return")


class AgentDiscoveryResponse(BaseModel):
    """Response from agent discovery"""
    total: int = Field(..., description="Total number of matching agents")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Requested limit")
    agents: List[AgentMetadataModel] = Field(..., description="List of matching agents")


class AgentExecutionRequestModel(BaseModel):
    """Request to execute an agent"""
    agent_id: str = Field(..., description="Unique identifier of the agent")
    input_data: Dict[str, Any] = Field(..., description="Input data for the agent")
    timeout_ms: int = Field(30000, ge=1000, le=300000, description="Execution timeout in milliseconds")
    priority: int = Field(5, ge=1, le=10, description="Execution priority (1=low, 10=high)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentExecutionResponseModel(BaseModel):
    """Response from agent execution"""
    execution_id: str = Field(..., description="Unique execution identifier")
    agent_id: str = Field(..., description="Agent that was executed")
    status: str = Field(..., description="Execution status")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Agent output")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: int = Field(..., description="Time spent executing")
    created_at: datetime = Field(..., description="Timestamp when execution started")


class AgentHealthModel(BaseModel):
    """Health status of an agent"""
    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    last_execution: Optional[datetime] = Field(None, description="Last execution time")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate (0.0-1.0)")
    average_execution_time_ms: int = Field(..., description="Average execution time")
    error_count: int = Field(0, ge=0, description="Number of recent errors")


class SystemHealthModel(BaseModel):
    """Overall system health status"""
    status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)")
    total_agents: int = Field(..., description="Total number of agents")
    healthy_agents: int = Field(..., description="Number of healthy agents")
    degraded_agents: int = Field(..., description="Number of degraded agents")
    unhealthy_agents: int = Field(..., description="Number of unhealthy agents")
    total_executions: int = Field(..., description="Total number of executions")
    average_success_rate: float = Field(..., ge=0.0, le=1.0, description="Average success rate")
    timestamp: datetime = Field(..., description="Timestamp of health check")


class AgentRegistryStatsModel(BaseModel):
    """Statistics about the agent registry"""
    total_agents: int = Field(..., description="Total number of agents in registry")
    agents_by_status: Dict[str, int] = Field(..., description="Count by status")
    agents_by_apqc_process: Dict[str, int] = Field(..., description="Count by APQC process")
    total_capabilities: int = Field(..., description="Total unique capabilities")
    last_updated: datetime = Field(..., description="Last registry update time")


class ExecutionHistoryItemModel(BaseModel):
    """Single execution history item"""
    execution_id: str
    agent_id: str
    status: str
    execution_time_ms: int
    created_at: datetime
    error_message: Optional[str] = None


class ExecutionHistoryModel(BaseModel):
    """Execution history response"""
    agent_id: str
    total: int
    items: List[ExecutionHistoryItemModel]


# ============================================================================
# Discovery Endpoints
# ============================================================================

@router.post(
    "/discover",
    response_model=AgentDiscoveryResponse,
    summary="Discover agents with filtering",
    description="Search for agents using various filters (APQC, capability, keyword, status)"
)
async def discover_agents(
    request: AgentDiscoveryRequest,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """
    Discover agents using flexible filtering criteria.

    Query parameters support:
    - APQC process filtering
    - Capability-based search
    - Keyword search
    - Status filtering
    - Proficiency level filtering
    - Pagination
    """
    try:
        logger.info(f"Discovering agents with filters: {request.dict(exclude_none=True)}")

        agents = await service.discovery.discover_agents(
            apqc_process=request.apqc_process,
            apqc_level=request.apqc_level,
            capability=request.capability,
            keyword=request.keyword,
            status=request.status,
            min_proficiency=request.min_proficiency,
            skip=request.skip,
            limit=request.limit,
        )

        total = await service.discovery.get_agent_count(
            apqc_process=request.apqc_process,
            apqc_level=request.apqc_level,
            capability=request.capability,
            keyword=request.keyword,
            status=request.status,
            min_proficiency=request.min_proficiency,
        )

        return AgentDiscoveryResponse(
            total=total,
            skip=request.skip,
            limit=request.limit,
            agents=agents,
        )
    except Exception as e:
        logger.error(f"Error discovering agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/search",
    response_model=AgentDiscoveryResponse,
    summary="Quick search for agents",
    description="Quick search by keyword, APQC process, or capability"
)
async def search_agents(
    q: Optional[str] = Query(None, min_length=1, description="Search query"),
    apqc: Optional[str] = Query(None, description="APQC process filter"),
    capability: Optional[str] = Query(None, description="Capability filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Quick search endpoint for agents."""
    try:
        logger.info(f"Searching agents with query: {q}, apqc: {apqc}, capability: {capability}")

        agents = await service.discovery.discover_agents(
            keyword=q,
            apqc_process=apqc,
            capability=capability,
            skip=skip,
            limit=limit,
        )

        total = await service.discovery.get_agent_count(
            keyword=q,
            apqc_process=apqc,
            capability=capability,
        )

        return AgentDiscoveryResponse(
            total=total,
            skip=skip,
            limit=limit,
            agents=agents,
        )
    except Exception as e:
        logger.error(f"Error searching agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{agent_id}",
    response_model=AgentMetadataModel,
    summary="Get agent details",
    description="Retrieve detailed metadata for a specific agent"
)
async def get_agent(
    agent_id: str,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get detailed information about a specific agent."""
    try:
        logger.info(f"Fetching agent: {agent_id}")

        agent = await service.discovery.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Execution Endpoints
# ============================================================================

@router.post(
    "/execute",
    response_model=AgentExecutionResponseModel,
    summary="Execute an agent",
    description="Execute an agent with provided input data"
)
async def execute_agent(
    request: AgentExecutionRequestModel,
    background_tasks: BackgroundTasks,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """
    Execute an agent with the provided input data.

    Returns execution ID and initial status immediately (async execution).
    Use the /executions/{execution_id} endpoint to poll for results.
    """
    try:
        logger.info(f"Executing agent: {request.agent_id}")

        # Create execution request object
        exec_request = AgentExecutionRequest(
            agent_id=request.agent_id,
            input_data=request.input_data,
            request_id=str(uuid.uuid4()),
            timeout_ms=request.timeout_ms,
            priority=request.priority,
            metadata=request.metadata,
        )

        # Execute agent
        response = await service.execution.execute_agent(exec_request)

        logger.info(f"Agent execution started: {response.execution_id}")
        return AgentExecutionResponseModel(
            execution_id=response.execution_id,
            agent_id=response.agent_id,
            status=response.status,
            output_data=response.output_data,
            error_message=response.error_message,
            execution_time_ms=response.execution_time_ms,
            created_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent {request.agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/executions/{execution_id}",
    response_model=AgentExecutionResponseModel,
    summary="Get execution status",
    description="Check the status of an agent execution"
)
async def get_execution_status(
    execution_id: str,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get status of a specific agent execution."""
    try:
        logger.info(f"Fetching execution status: {execution_id}")

        response = await service.execution.get_execution_status(execution_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )

        return AgentExecutionResponseModel(
            execution_id=response.execution_id,
            agent_id=response.agent_id,
            status=response.status,
            output_data=response.output_data,
            error_message=response.error_message,
            execution_time_ms=response.execution_time_ms,
            created_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution status {execution_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/executions/{execution_id}",
    summary="Cancel agent execution",
    description="Cancel a running agent execution"
)
async def cancel_execution(
    execution_id: str,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Cancel a running agent execution."""
    try:
        logger.info(f"Cancelling execution: {execution_id}")

        success = await service.execution.cancel_execution(execution_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found or already completed"
            )

        return {"status": "cancelled", "execution_id": execution_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution {execution_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{agent_id}/history",
    response_model=ExecutionHistoryModel,
    summary="Get agent execution history",
    description="Retrieve execution history for a specific agent"
)
async def get_agent_execution_history(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get execution history for a specific agent."""
    try:
        logger.info(f"Fetching execution history for agent: {agent_id}")

        history_items = await service.execution.get_execution_history(agent_id, limit)

        return ExecutionHistoryModel(
            agent_id=agent_id,
            total=len(history_items),
            items=[
                ExecutionHistoryItemModel(
                    execution_id=item.get("execution_id"),
                    agent_id=item.get("agent_id"),
                    status=item.get("status"),
                    execution_time_ms=item.get("execution_time_ms", 0),
                    created_at=item.get("created_at", datetime.utcnow()),
                    error_message=item.get("error_message"),
                )
                for item in history_items
            ],
        )
    except Exception as e:
        logger.error(f"Error fetching execution history for {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Health & Monitoring Endpoints
# ============================================================================

@router.get(
    "/health/system",
    response_model=SystemHealthModel,
    summary="Get system health status",
    description="Get overall health status of the agent library system"
)
async def get_system_health(
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get overall system health status."""
    try:
        logger.info("Checking system health")

        health = await service.health.get_system_health()

        return SystemHealthModel(
            status=health.get("status", "unknown"),
            total_agents=health.get("total_agents", 0),
            healthy_agents=health.get("healthy_agents", 0),
            degraded_agents=health.get("degraded_agents", 0),
            unhealthy_agents=health.get("unhealthy_agents", 0),
            total_executions=health.get("total_executions", 0),
            average_success_rate=health.get("average_success_rate", 0.0),
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{agent_id}/health",
    response_model=AgentHealthModel,
    summary="Get agent health status",
    description="Get health and performance metrics for a specific agent"
)
async def get_agent_health(
    agent_id: str,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get health status of a specific agent."""
    try:
        logger.info(f"Checking health for agent: {agent_id}")

        health = await service.health.get_agent_health(agent_id)
        if not health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        return AgentHealthModel(
            agent_id=agent_id,
            status=health.get("status", "unknown"),
            last_execution=health.get("last_execution"),
            success_rate=health.get("success_rate", 0.0),
            average_execution_time_ms=health.get("average_execution_time_ms", 0),
            error_count=health.get("error_count", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health for {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Registry Management Endpoints
# ============================================================================

@router.post(
    "/registry/register",
    response_model=AgentMetadataModel,
    summary="Register a new agent",
    description="Register a new agent in the library"
)
async def register_agent(
    metadata: AgentMetadataModel,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Register a new agent in the library."""
    try:
        logger.info(f"Registering agent: {metadata.agent_id}")

        result = await service.registry.register_agent(metadata)

        logger.info(f"Agent registered successfully: {metadata.agent_id}")
        return result
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{agent_id}/registry",
    summary="Unregister an agent",
    description="Remove an agent from the registry"
)
async def unregister_agent(
    agent_id: str,
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Unregister an agent from the library."""
    try:
        logger.info(f"Unregistering agent: {agent_id}")

        success = await service.registry.unregister_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        return {"status": "unregistered", "agent_id": agent_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/registry/stats",
    response_model=AgentRegistryStatsModel,
    summary="Get registry statistics",
    description="Get statistics and insights about the agent registry"
)
async def get_registry_stats(
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Get registry statistics."""
    try:
        logger.info("Fetching registry statistics")

        stats = await service.registry.get_registry_stats()

        return AgentRegistryStatsModel(
            total_agents=stats.get("total_agents", 0),
            agents_by_status=stats.get("agents_by_status", {}),
            agents_by_apqc_process=stats.get("agents_by_apqc_process", {}),
            total_capabilities=stats.get("total_capabilities", 0),
            last_updated=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error fetching registry stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get(
    "/health",
    summary="Agent library service health check",
    description="Check if the agent library service is running"
)
async def health_check(
    service: AgentLibraryService = Depends(get_agent_library_service)
):
    """Health check endpoint for the agent library service."""
    return {
        "status": "ok",
        "service": "agent_library",
        "timestamp": datetime.utcnow().isoformat(),
    }
