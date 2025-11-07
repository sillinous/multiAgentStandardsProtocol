"""
SuperStandard API Server - Production-Ready Multi-Agent Platform

This is the COMPLETE API server that powers the entire SuperStandard platform,
providing REST and WebSocket endpoints for all protocols (ANP, ACP, AConsP).

Features:
- REST API for all protocol operations
- WebSocket streaming for real-time dashboard updates
- Automatic agent registration and discovery
- Coordination session management
- Collective consciousness monitoring
- CORS support for browser access
- Production-ready error handling

Usage:
    python -m uvicorn src.superstandard.api.server:app --reload --port 8080

    Access dashboards at:
    - http://localhost:8080/dashboard/user
    - http://localhost:8080/dashboard/admin
    - http://localhost:8080/dashboard/network
    - http://localhost:8080/dashboard/coordination
    - http://localhost:8080/dashboard/consciousness

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

# Import all protocols
from superstandard.protocols.anp_implementation import (
    AgentNetworkRegistry,
    ANPRegistration,
    DiscoveryQuery,
    AgentStatus,
)
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    CoordinationType,
    TaskStatus,
)
from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ThoughtType,
    ConsciousnessState,
)

# ============================================================================
# Pydantic Models for API
# ============================================================================


class AgentRegistrationRequest(BaseModel):
    """Request to register an agent on the network."""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent (analyst, processor, etc.)")
    capabilities: List[str] = Field(default=[], description="Agent capabilities")
    endpoints: Dict[str, str] = Field(default={}, description="Agent endpoints")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class AgentDiscoveryRequest(BaseModel):
    """Request to discover agents by criteria."""

    capabilities: Optional[List[str]] = None
    agent_type: Optional[str] = None
    health_status: Optional[str] = None
    tags: Optional[List[str]] = None
    region: Optional[str] = None
    max_load: Optional[float] = None
    limit: int = 100


class SessionCreationRequest(BaseModel):
    """Request to create coordination session."""

    name: str = Field(..., description="Session name")
    coordination_type: str = Field(
        ..., description="Type: pipeline, swarm, supervisor, negotiation"
    )
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default={}, description="Session metadata")


class TaskCreationRequest(BaseModel):
    """Request to add task to session."""

    task_type: str = Field(..., description="Type of task")
    description: str = Field(..., description="Task description")
    priority: int = Field(default=5, description="Priority (1-10)")
    input_data: Dict[str, Any] = Field(default={}, description="Task input data")
    dependencies: List[str] = Field(default=[], description="Task dependencies")


class ThoughtSubmissionRequest(BaseModel):
    """Request to submit thought to collective."""

    agent_id: str
    thought_type: str  # observation, inference, intuition, insight, intention, question
    content: str
    confidence: float = 0.5
    emotional_valence: Optional[float] = None
    context: Dict[str, Any] = Field(default={})


class CollectiveQueryRequest(BaseModel):
    """Request to query collective consciousness."""

    query: str
    min_coherence: float = 0.5
    max_patterns: int = 10


# ============================================================================
# Global State - Protocol Instances
# ============================================================================


class ServerState:
    """Global server state managing all protocol instances."""

    def __init__(self):
        # Protocol instances
        self.network_registry = AgentNetworkRegistry()
        self.coordination_manager = CoordinationManager()
        self.collectives: Dict[str, CollectiveConsciousness] = {}

        # WebSocket connections
        self.ws_connections: Dict[str, List[WebSocket]] = {
            "admin": [],
            "network": [],
            "coordination": [],
            "consciousness": [],
        }

        # Stats tracking
        self.stats = {
            "total_agents_registered": 0,
            "total_sessions_created": 0,
            "total_thoughts_submitted": 0,
            "total_patterns_discovered": 0,
            "server_start_time": datetime.utcnow(),
        }

    def get_default_collective(self) -> CollectiveConsciousness:
        """Get or create default collective."""
        if "main" not in self.collectives:
            self.collectives["main"] = CollectiveConsciousness("main")
        return self.collectives["main"]

    async def broadcast_event(self, channel: str, event: Dict[str, Any]):
        """Broadcast event to all WebSocket connections on channel."""
        if channel not in self.ws_connections:
            return

        disconnected = []
        for ws in self.ws_connections[channel]:
            try:
                await ws.send_json(event)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.ws_connections[channel].remove(ws)


# Initialize global state
state = ServerState()

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="SuperStandard Multi-Agent Platform API",
    description="Production-ready API for ANP, ACP, and AConsP protocols",
    version="1.0.0",
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Static File Serving - Dashboards
# ============================================================================


@app.get("/")
async def root():
    """Redirect to user control panel."""
    return HTMLResponse(
        content="""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/dashboard/user" />
        </head>
        <body>
            <p>Redirecting to <a href="/dashboard/user">User Control Panel</a>...</p>
        </body>
    </html>
    """
    )


@app.get("/dashboard/user")
async def user_dashboard():
    """Serve user control panel."""
    dashboard_path = Path(__file__).parent / "user_control_panel.html"
    return FileResponse(dashboard_path)


@app.get("/dashboard/admin")
async def admin_dashboard():
    """Serve admin dashboard."""
    dashboard_path = Path(__file__).parent / "admin_dashboard.html"
    return FileResponse(dashboard_path)


@app.get("/dashboard/network")
async def network_dashboard():
    """Serve ANP network topology dashboard."""
    dashboard_path = Path(__file__).parent / "network_dashboard.html"
    return FileResponse(dashboard_path)


@app.get("/dashboard/coordination")
async def coordination_dashboard():
    """Serve ACP coordination dashboard."""
    dashboard_path = Path(__file__).parent / "coordination_dashboard.html"
    return FileResponse(dashboard_path)


@app.get("/dashboard/consciousness")
async def consciousness_dashboard():
    """Serve AConsP consciousness dashboard."""
    dashboard_path = Path(__file__).parent / "consciousness_dashboard.html"
    return FileResponse(dashboard_path)


# ============================================================================
# ANP (Agent Network Protocol) Endpoints
# ============================================================================


@app.post("/api/anp/agents/register")
async def register_agent(request: AgentRegistrationRequest, background_tasks: BackgroundTasks):
    """Register an agent on the network."""
    try:
        registration = ANPRegistration(
            action="register",
            agent_id=request.agent_id,
            agent_type=request.agent_type,
            capabilities=request.capabilities,
            endpoints=request.endpoints,
            health_status=AgentStatus.HEALTHY.value,
            metadata=request.metadata,
        )

        success = await state.network_registry.register_agent(registration)

        if success:
            state.stats["total_agents_registered"] += 1

            # Broadcast to WebSocket clients
            background_tasks.add_task(
                state.broadcast_event,
                "network",
                {
                    "type": "agent_registered",
                    "agent_id": request.agent_id,
                    "agent_type": request.agent_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "agent",
                    "message": f"Agent {request.agent_id} registered ({request.agent_type})",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        return {
            "success": success,
            "agent_id": request.agent_id,
            "message": "Agent registered successfully" if success else "Registration failed",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anp/agents/discover")
async def discover_agents(request: AgentDiscoveryRequest):
    """Discover agents by criteria."""
    try:
        query = DiscoveryQuery(
            capabilities=request.capabilities,
            agent_type=request.agent_type,
            health_status=request.health_status,
            tags=request.tags,
            region=request.region,
            max_load=request.max_load,
            limit=request.limit,
        )

        result = await state.network_registry.discover_agents(query)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anp/agents")
async def list_agents():
    """List all registered agents."""
    try:
        agents = []
        for agent_id, agent_info in state.network_registry.agents.items():
            # Handle last_heartbeat - it might be datetime, string, or None
            last_hb = agent_info.last_heartbeat
            if last_hb:
                if hasattr(last_hb, 'isoformat'):
                    last_hb_str = last_hb.isoformat()
                else:
                    last_hb_str = str(last_hb)
            else:
                last_hb_str = None

            agents.append(
                {
                    "agent_id": agent_info.agent_id,
                    "agent_type": agent_info.agent_type,
                    "capabilities": agent_info.capabilities,
                    "health_status": agent_info.health_status,
                    "load_score": agent_info.load_score,
                    "region": agent_info.region,
                    "tags": agent_info.tags,
                    "endpoints": agent_info.endpoints,
                    "last_heartbeat": last_hb_str,
                }
            )

        return {"success": True, "count": len(agents), "agents": agents}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anp/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str, health_status: str = "healthy", load_score: float = 0.0):
    """Send heartbeat for an agent."""
    try:
        success = await state.network_registry.heartbeat(agent_id, health_status, load_score)

        return {
            "success": success,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anp/stats")
async def anp_stats():
    """Get ANP network statistics."""
    try:
        total_agents = len(state.network_registry.agents)
        healthy_agents = sum(
            1
            for a in state.network_registry.agents.values()
            if a.health_status == AgentStatus.HEALTHY.value
        )

        all_capabilities = set()
        for agent in state.network_registry.agents.values():
            all_capabilities.update(agent.capabilities)

        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "total_capabilities": len(all_capabilities),
            "discoveries_24h": state.stats["total_agents_registered"],  # Simplified
            "heartbeat_rate": 0,  # TODO: Track actual heartbeat rate
            "network_uptime": 99.9,  # TODO: Calculate actual uptime
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACP (Agent Coordination Protocol) Endpoints
# ============================================================================


@app.post("/api/acp/sessions")
async def create_session(request: SessionCreationRequest, background_tasks: BackgroundTasks):
    """Create a new coordination session."""
    try:
        # Map string to enum
        coord_type_map = {
            "pipeline": CoordinationType.PIPELINE,
            "swarm": CoordinationType.SWARM,
            "supervisor": CoordinationType.SUPERVISOR,
            "negotiation": CoordinationType.NEGOTIATION,
        }

        coord_type = coord_type_map.get(request.coordination_type.lower())
        if not coord_type:
            raise HTTPException(status_code=400, detail="Invalid coordination type")

        session_id = await state.coordination_manager.create_coordination(
            request.name, coord_type, request.metadata
        )

        if session_id:
            state.stats["total_sessions_created"] += 1

            # Broadcast event
            background_tasks.add_task(
                state.broadcast_event,
                "coordination",
                {
                    "type": "session_created",
                    "session_id": session_id,
                    "name": request.name,
                    "coordination_type": request.coordination_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "session",
                    "message": f"New {request.coordination_type} session: {request.name}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        return {
            "success": session_id is not None,
            "session_id": session_id,
            "name": request.name,
            "coordination_type": request.coordination_type,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/acp/sessions")
async def list_sessions():
    """List all coordination sessions."""
    try:
        sessions = []
        for session_id, session in state.coordination_manager.sessions.items():
            completed_tasks = sum(
                1 for t in session.tasks.values() if t.status == TaskStatus.COMPLETED.value
            )

            sessions.append(
                {
                    "session_id": session.session_id,
                    "name": session.coordination_type,  # TODO: Add name field to session
                    "coordination_type": session.coordination_type,
                    "status": session.status,
                    "total_tasks": len(session.tasks),
                    "completed_tasks": completed_tasks,
                    "participant_count": len(session.participants),
                    "created_at": session.created_at.isoformat(),
                }
            )

        return {"success": True, "count": len(sessions), "sessions": sessions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/acp/sessions/{session_id}/tasks")
async def add_task(
    session_id: str, request: TaskCreationRequest, background_tasks: BackgroundTasks
):
    """Add a task to a coordination session."""
    try:
        task_id = await state.coordination_manager.add_task(
            session_id,
            request.task_type,
            request.description,
            request.priority,
            request.dependencies,
            request.input_data,
        )

        if task_id:
            # Broadcast event
            background_tasks.add_task(
                state.broadcast_event,
                "coordination",
                {
                    "type": "task_added",
                    "session_id": session_id,
                    "task_id": task_id,
                    "task_type": request.task_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        return {"success": task_id is not None, "task_id": task_id, "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/acp/sessions/{session_id}/tasks")
async def list_tasks(session_id: str):
    """List tasks in a session."""
    try:
        session = state.coordination_manager.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        tasks = []
        for task_id, task in session.tasks.items():
            tasks.append(
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "assigned_to": task.assigned_to,
                    "progress": task.progress,
                    "dependencies": task.dependencies,
                }
            )

        return {"success": True, "session_id": session_id, "count": len(tasks), "tasks": tasks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/acp/stats")
async def acp_stats():
    """Get ACP coordination statistics."""
    try:
        active_sessions = sum(
            1 for s in state.coordination_manager.sessions.values() if s.status == "active"
        )

        total_tasks = sum(len(s.tasks) for s in state.coordination_manager.sessions.values())

        completed_tasks = sum(
            sum(1 for t in s.tasks.values() if t.status == TaskStatus.COMPLETED.value)
            for s in state.coordination_manager.sessions.values()
        )

        total_participants = sum(
            len(s.participants) for s in state.coordination_manager.sessions.values()
        )

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "active_sessions": active_sessions,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 1),
            "total_participants": total_participants,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AConsP (Agent Consciousness Protocol) Endpoints
# ============================================================================


@app.post("/api/aconsp/collectives/{collective_id}/thoughts")
async def submit_thought(
    collective_id: str, request: ThoughtSubmissionRequest, background_tasks: BackgroundTasks
):
    """Submit a thought to collective consciousness."""
    try:
        # Get or create collective
        if collective_id not in state.collectives:
            state.collectives[collective_id] = CollectiveConsciousness(collective_id)

        collective = state.collectives[collective_id]

        # Map string to enum
        thought_type_map = {
            "observation": ThoughtType.OBSERVATION,
            "inference": ThoughtType.INFERENCE,
            "intuition": ThoughtType.INTUITION,
            "insight": ThoughtType.INSIGHT,
            "intention": ThoughtType.INTENTION,
            "question": ThoughtType.QUESTION,
        }

        thought_type = thought_type_map.get(request.thought_type.lower())
        if not thought_type:
            raise HTTPException(status_code=400, detail="Invalid thought type")

        # Submit thought
        thought = await collective.contribute_thought(
            request.agent_id,
            thought_type,
            request.content,
            request.confidence,
            request.emotional_valence,
            request.context,
        )

        if thought:
            state.stats["total_thoughts_submitted"] += 1

            # Broadcast event
            background_tasks.add_task(
                state.broadcast_event,
                "consciousness",
                {
                    "type": "thought_contributed",
                    "collective_id": collective_id,
                    "agent_id": request.agent_id,
                    "thought_type": request.thought_type,
                    "content": request.content,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "thought",
                    "message": f"{request.agent_id} shared {request.thought_type}: {request.content[:50]}...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        return {
            "success": thought is not None,
            "thought_id": thought.thought_id if thought else None,
            "collective_id": collective_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/aconsp/collectives/{collective_id}/query")
async def query_collective(collective_id: str, request: CollectiveQueryRequest):
    """Query collective consciousness for emergent patterns."""
    try:
        collective = state.collectives.get(collective_id)
        if not collective:
            raise HTTPException(status_code=404, detail="Collective not found")

        patterns = await collective.collapse_consciousness(
            request.query, request.min_coherence, request.max_patterns
        )

        if patterns:
            state.stats["total_patterns_discovered"] += len(patterns)

        return {
            "success": True,
            "collective_id": collective_id,
            "query": request.query,
            "pattern_count": len(patterns),
            "patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "coherence_score": p.coherence_score,
                    "novelty_score": p.novelty_score,
                    "impact_potential": p.impact_potential,
                    "contributing_agents": p.contributing_agents,
                    "synthesis": p.synthesis,
                }
                for p in patterns
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/aconsp/collectives/{collective_id}/state")
async def get_collective_state(collective_id: str):
    """Get state of collective consciousness."""
    try:
        collective = state.collectives.get(collective_id)
        if not collective:
            raise HTTPException(status_code=404, detail="Collective not found")

        collective_state = await collective.get_collective_state()

        return {"success": True, "collective_id": collective_id, "state": collective_state}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/aconsp/stats")
async def aconsp_stats():
    """Get AConsP consciousness statistics."""
    try:
        total_collectives = len(state.collectives)

        total_thoughts = sum(len(c.thought_superposition) for c in state.collectives.values())

        total_patterns = state.stats["total_patterns_discovered"]

        # Calculate average awareness
        if state.collectives:
            avg_awareness = sum(c.collective_awareness for c in state.collectives.values()) / len(
                state.collectives
            )
        else:
            avg_awareness = 0

        return {
            "total_collectives": total_collectives,
            "total_thoughts": total_thoughts,
            "total_patterns": total_patterns,
            "average_awareness": round(avg_awareness, 1),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Admin / System Endpoints
# ============================================================================


@app.get("/api/admin/stats")
async def admin_stats():
    """Get comprehensive system statistics."""
    try:
        anp_stats_data = await anp_stats()
        acp_stats_data = await acp_stats()
        aconsp_stats_data = await aconsp_stats()

        uptime_seconds = (datetime.utcnow() - state.stats["server_start_time"]).total_seconds()

        return {
            "success": True,
            "system": {
                "uptime_seconds": uptime_seconds,
                "total_agents_registered": state.stats["total_agents_registered"],
                "total_sessions_created": state.stats["total_sessions_created"],
                "total_thoughts_submitted": state.stats["total_thoughts_submitted"],
                "total_patterns_discovered": state.stats["total_patterns_discovered"],
            },
            "anp": anp_stats_data,
            "acp": acp_stats_data,
            "aconsp": aconsp_stats_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "protocols": {"anp": "operational", "acp": "operational", "aconsp": "operational"},
    }


# ============================================================================
# WebSocket Endpoints for Real-Time Updates
# ============================================================================


@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """WebSocket for admin dashboard real-time updates."""
    await websocket.accept()
    state.ws_connections["admin"].append(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.ws_connections["admin"].remove(websocket)


@app.websocket("/ws/network")
async def websocket_network(websocket: WebSocket):
    """WebSocket for network dashboard real-time updates."""
    await websocket.accept()
    state.ws_connections["network"].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.ws_connections["network"].remove(websocket)


@app.websocket("/ws/coordination")
async def websocket_coordination(websocket: WebSocket):
    """WebSocket for coordination dashboard real-time updates."""
    await websocket.accept()
    state.ws_connections["coordination"].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.ws_connections["coordination"].remove(websocket)


@app.websocket("/ws/consciousness")
async def websocket_consciousness(websocket: WebSocket):
    """WebSocket for consciousness dashboard real-time updates."""
    await websocket.accept()
    state.ws_connections["consciousness"].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.ws_connections["consciousness"].remove(websocket)


# ============================================================================
# Startup / Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize server state on startup."""
    print("=" * 80)
    print("SuperStandard Multi-Agent Platform API Server")
    print("=" * 80)
    print()
    print("🚀 Server starting...")
    print(f"   Start time: {state.stats['server_start_time'].isoformat()}")
    print()
    print("📡 Protocols initialized:")
    print("   ✅ ANP (Agent Network Protocol)")
    print("   ✅ ACP (Agent Coordination Protocol)")
    print("   ✅ AConsP (Agent Consciousness Protocol)")
    print()
    print("🌐 Dashboards available at:")
    print("   - http://localhost:8080/dashboard/user")
    print("   - http://localhost:8080/dashboard/admin")
    print("   - http://localhost:8080/dashboard/network")
    print("   - http://localhost:8080/dashboard/coordination")
    print("   - http://localhost:8080/dashboard/consciousness")
    print()
    print("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    print()
    print("=" * 80)
    print("🛑 Server shutting down...")
    print(f"   Total agents registered: {state.stats['total_agents_registered']}")
    print(f"   Total sessions created: {state.stats['total_sessions_created']}")
    print(f"   Total thoughts submitted: {state.stats['total_thoughts_submitted']}")
    print(f"   Total patterns discovered: {state.stats['total_patterns_discovered']}")
    print("=" * 80)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
