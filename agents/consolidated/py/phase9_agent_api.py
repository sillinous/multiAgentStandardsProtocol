"""
Phase 9 Agent Management API

REST endpoints for complete agent management:
- /api/v4/agents - Agent discovery, listing, searching
- /api/v4/agents/{agent_id} - Agent control, monitoring, inspection
- /api/v4/teams - Team creation and management
- /api/v4/dashboard - Real-time agent dashboard
- /api/v4/memory - Environmental memory access
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from datetime import datetime

from src.backend.phase9_agent_management import (
    AgentManagementSystem,
    AgentStatus,
    AgentHealthLevel,
)


# ============================================================================
# Initialize Agent Management System (Singleton)
# ============================================================================

_agent_management: Optional[AgentManagementSystem] = None


async def get_agent_management() -> AgentManagementSystem:
    """Get or create singleton agent management system"""
    global _agent_management
    if _agent_management is None:
        _agent_management = AgentManagementSystem()
        await _agent_management.initialize()
    return _agent_management


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentCapabilityModel(BaseModel):
    """Agent capability model"""
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
    category: str
    reliability_score: float = 0.95


class RegisterAgentRequest(BaseModel):
    """Request to register new agent"""
    agent_id: str
    agent_type: str
    name: str
    description: str
    version: str
    capabilities: List[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None


class UpdateAgentParametersRequest(BaseModel):
    """Request to update agent parameters"""
    parameters: Dict[str, Any]


class AdjustAgentBehaviorRequest(BaseModel):
    """Request to adjust agent behavior"""
    adjustments: Dict[str, Any] = Field(
        ...,
        example={
            "risk_tolerance": "high",
            "decision_threshold": 0.8,
            "execution_speed": "fast"
        }
    )


class CreateTeamRequest(BaseModel):
    """Request to create agent team"""
    team_id: str
    name: str
    objective: str
    agent_ids: List[str]
    lead_agent: Optional[str] = None
    voting_mechanism: str = "majority"


# ============================================================================
# API Router
# ============================================================================

def create_agent_management_router() -> APIRouter:
    """Create agent management API router"""
    router = APIRouter(prefix="/api/v4/agents", tags=["Phase 9 Agent Management"])

    # ====================================================================
    # DISCOVERY & LISTING
    # ====================================================================

    @router.get(
        "",
        summary="List All Agents",
        description="Get complete list of all registered agents"
    )
    async def list_agents() -> Dict[str, Any]:
        """List all registered agents"""
        try:
            mgmt = await get_agent_management()
            agents = await mgmt.list_all_agents()
            return {
                "count": len(agents),
                "agents": agents,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/library",
        summary="Get Agent Library",
        description="Get agent library organized by category"
    )
    async def get_agent_library() -> Dict[str, Any]:
        """Get agent library organized by capability categories"""
        try:
            mgmt = await get_agent_management()
            library = await mgmt.get_agent_library()
            return {
                "library": library,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/search",
        summary="Search Agents",
        description="Search agents by capability or category"
    )
    async def search_agents(
        capability: Optional[str] = Query(None, description="Search by capability name"),
        category: Optional[str] = Query(None, description="Search by category (trading, research, etc.)")
    ) -> Dict[str, Any]:
        """Search agents by capability or category"""
        try:
            mgmt = await get_agent_management()

            if capability:
                agents = await mgmt.find_agents_by_capability(capability)
                return {
                    "search_type": "capability",
                    "query": capability,
                    "count": len(agents),
                    "agents": agents
                }
            elif category:
                agents = await mgmt.find_agents_by_category(category)
                return {
                    "search_type": "category",
                    "query": category,
                    "count": len(agents),
                    "agents": agents
                }
            else:
                raise HTTPException(status_code=400, detail="Must specify 'capability' or 'category'")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ====================================================================
    # AGENT REGISTRATION & INFO
    # ====================================================================

    @router.post(
        "/register",
        summary="Register New Agent",
        description="Register a new agent in the management system"
    )
    async def register_agent(request: RegisterAgentRequest) -> Dict[str, Any]:
        """Register a new agent"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.register_agent(
                agent_id=request.agent_id,
                agent_type=request.agent_type,
                name=request.name,
                description=request.description,
                version=request.version,
                capabilities=request.capabilities,
                parameters=request.parameters
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}",
        summary="Get Agent Info",
        description="Get complete information for specific agent"
    )
    async def get_agent_info(agent_id: str) -> Dict[str, Any]:
        """Get agent information"""
        try:
            mgmt = await get_agent_management()
            agent = await mgmt.get_agent_info(agent_id)

            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            return agent
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ====================================================================
    # CONTROL: Start, Stop, Pause, Resume
    # ====================================================================

    @router.post(
        "/{agent_id}/start",
        summary="Start Agent",
        description="Start an agent with optional parameters"
    )
    async def start_agent(
        agent_id: str,
        request: Optional[Dict[str, Any]] = Body(None)
    ) -> Dict[str, Any]:
        """Start an agent"""
        try:
            mgmt = await get_agent_management()
            parameters = request.get("parameters") if request else None
            environment = request.get("environment") if request else None

            result = await mgmt.start_agent(
                agent_id=agent_id,
                parameters=parameters,
                environment=environment
            )

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post(
        "/{agent_id}/stop",
        summary="Stop Agent",
        description="Stop an agent gracefully"
    )
    async def stop_agent(agent_id: str) -> Dict[str, Any]:
        """Stop an agent"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.stop_agent(agent_id)

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post(
        "/{agent_id}/pause",
        summary="Pause Agent",
        description="Pause agent execution (can be resumed)"
    )
    async def pause_agent(agent_id: str) -> Dict[str, Any]:
        """Pause an agent"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.pause_agent(agent_id)

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post(
        "/{agent_id}/resume",
        summary="Resume Agent",
        description="Resume paused agent"
    )
    async def resume_agent(agent_id: str) -> Dict[str, Any]:
        """Resume an agent"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.resume_agent(agent_id)

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ====================================================================
    # PARAMETERS & CONFIGURATION
    # ====================================================================

    @router.put(
        "/{agent_id}/parameters",
        summary="Update Agent Parameters",
        description="Dynamically update agent parameters"
    )
    async def update_agent_parameters(
        agent_id: str,
        request: UpdateAgentParametersRequest
    ) -> Dict[str, Any]:
        """Update agent parameters"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.update_agent_parameters(agent_id, request.parameters)

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post(
        "/{agent_id}/adjust",
        summary="Adjust Agent Behavior",
        description="Dynamically adjust agent behavior (risk, thresholds, speed, etc.)"
    )
    async def adjust_agent_behavior(
        agent_id: str,
        request: AdjustAgentBehaviorRequest
    ) -> Dict[str, Any]:
        """Adjust agent behavior"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.adjust_agent_behavior(agent_id, request.adjustments)

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ====================================================================
    # MONITORING & METRICS
    # ====================================================================

    @router.get(
        "/{agent_id}/metrics",
        summary="Get Agent Metrics",
        description="Get real-time agent metrics and performance"
    )
    async def get_agent_metrics(agent_id: str) -> Dict[str, Any]:
        """Get agent metrics"""
        try:
            mgmt = await get_agent_management()
            metrics = await mgmt.get_agent_metrics(agent_id)

            if not metrics:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            return metrics
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}/activity",
        summary="Get Agent Activity Feed",
        description="Get recent logs and decisions for agent"
    )
    async def get_agent_activity(
        agent_id: str,
        limit: int = Query(50, le=200)
    ) -> Dict[str, Any]:
        """Get agent activity feed"""
        try:
            mgmt = await get_agent_management()
            activity = await mgmt.get_agent_activity_feed(agent_id, limit)

            if not activity and not (await mgmt.get_agent_info(agent_id)):
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            return {
                "agent_id": agent_id,
                "activity_count": len(activity),
                "activity": activity
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}/logs",
        summary="Get Agent Logs",
        description="Get agent event logs with optional filtering"
    )
    async def get_agent_logs(
        agent_id: str,
        level: Optional[str] = Query(None, description="Filter by log level: DEBUG, INFO, WARN, ERROR"),
        limit: int = Query(100, le=1000)
    ) -> Dict[str, Any]:
        """Get agent logs"""
        try:
            mgmt = await get_agent_management()
            logs = await mgmt.get_agent_logs(agent_id, level, limit)

            if not logs and not (await mgmt.get_agent_info(agent_id)):
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            return {
                "agent_id": agent_id,
                "log_count": len(logs),
                "level_filter": level,
                "logs": logs
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}/decisions",
        summary="Get Agent Decisions",
        description="Get agent decision history with confidence scores"
    )
    async def get_agent_decisions(
        agent_id: str,
        decision_type: Optional[str] = Query(None),
        limit: int = Query(100, le=1000)
    ) -> Dict[str, Any]:
        """Get agent decisions"""
        try:
            mgmt = await get_agent_management()
            decisions = await mgmt.get_agent_decisions(agent_id, decision_type, limit)

            if not decisions and not (await mgmt.get_agent_info(agent_id)):
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            return {
                "agent_id": agent_id,
                "decision_count": len(decisions),
                "type_filter": decision_type,
                "decisions": decisions
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}/relationships",
        summary="Get Agent Relationships",
        description="Get agent's teams and collaborators"
    )
    async def get_agent_relationships(agent_id: str) -> Dict[str, Any]:
        """Get agent relationships"""
        try:
            mgmt = await get_agent_management()
            relationships = await mgmt.get_agent_relationships(agent_id)

            if "error" in relationships:
                raise HTTPException(status_code=404, detail=relationships["error"])

            return relationships
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{agent_id}/patterns",
        summary="Analyze Agent Patterns",
        description="Analyze decision and error patterns for agent"
    )
    async def analyze_agent_patterns(
        agent_id: str,
        window_size: int = Query(100, ge=10, le=1000)
    ) -> Dict[str, Any]:
        """Analyze agent patterns"""
        try:
            mgmt = await get_agent_management()
            patterns = await mgmt.analyze_agent_patterns(agent_id, window_size)

            if "error" in patterns:
                raise HTTPException(status_code=404, detail=patterns["error"])

            return patterns
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router


# ============================================================================
# Dashboard Router
# ============================================================================

def create_dashboard_router() -> APIRouter:
    """Create dashboard API router"""
    router = APIRouter(prefix="/api/v4/dashboard", tags=["Phase 9 Dashboard"])

    @router.get(
        "/summary",
        summary="Dashboard Summary",
        description="Get high-level dashboard summary"
    )
    async def get_dashboard_summary() -> Dict[str, Any]:
        """Get dashboard summary"""
        try:
            mgmt = await get_agent_management()
            summary = await mgmt.get_dashboard_summary()
            return summary
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router


# ============================================================================
# Teams Router
# ============================================================================

def create_teams_router() -> APIRouter:
    """Create teams API router"""
    router = APIRouter(prefix="/api/v4/teams", tags=["Phase 9 Teams"])

    @router.post(
        "",
        summary="Create Team",
        description="Create a team of agents"
    )
    async def create_team(request: CreateTeamRequest) -> Dict[str, Any]:
        """Create agent team"""
        try:
            mgmt = await get_agent_management()
            result = await mgmt.create_team(
                team_id=request.team_id,
                name=request.name,
                objective=request.objective,
                agent_ids=request.agent_ids,
                lead_agent=request.lead_agent,
                voting_mechanism=request.voting_mechanism
            )

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get(
        "/{team_id}",
        summary="Get Team Info",
        description="Get team information"
    )
    async def get_team_info(team_id: str) -> Dict[str, Any]:
        """Get team information"""
        try:
            mgmt = await get_agent_management()
            team = await mgmt.get_team_info(team_id)

            if not team:
                raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

            return team
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router


# ============================================================================
# Memory Router
# ============================================================================

def create_memory_router() -> APIRouter:
    """Create environmental memory router"""
    router = APIRouter(prefix="/api/v4/memory", tags=["Phase 9 Environmental Memory"])

    @router.post(
        "/write",
        summary="Write to Memory",
        description="Write data to environmental memory"
    )
    async def write_memory(
        request: Dict[str, Any] = Body(...)
    ) -> Dict[str, Any]:
        """Write to environmental memory"""
        try:
            mgmt = await get_agent_management()
            memory_type = request.get("type", "general")
            data = request.get("data", {})
            ttl_seconds = request.get("ttl_seconds")

            memory_id = await mgmt.write_environmental_memory(
                memory_type=memory_type,
                data=data,
                ttl_seconds=ttl_seconds
            )

            return {
                "memory_id": memory_id,
                "type": memory_type,
                "status": "written"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post(
        "/read",
        summary="Read from Memory",
        description="Read data from environmental memory"
    )
    async def read_memory(
        agent_id: str = Query(..., description="Agent reading the memory"),
        memory_type: Optional[str] = Query(None, description="Filter by memory type")
    ) -> Dict[str, Any]:
        """Read from environmental memory"""
        try:
            mgmt = await get_agent_management()
            entries = await mgmt.read_environmental_memory(agent_id, memory_type)

            return {
                "agent_id": agent_id,
                "memory_type_filter": memory_type,
                "entry_count": len(entries),
                "entries": entries
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router


# ============================================================================
# Integration Helper
# ============================================================================

def register_agent_management_routes(app) -> None:
    """Register all agent management routes with FastAPI app"""
    # Include routers
    app.include_router(create_agent_management_router())
    app.include_router(create_dashboard_router())
    app.include_router(create_teams_router())
    app.include_router(create_memory_router())
