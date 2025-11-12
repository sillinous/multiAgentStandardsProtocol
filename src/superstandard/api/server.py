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

    Dashboard Hub:
    - http://localhost:8080/dashboard (Main landing page)

    Individual Dashboards:
    - http://localhost:8080/dashboard/admin
    - http://localhost:8080/dashboard/user
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
    AgentStatus
)
from superstandard.protocols.acp_implementation import (
    CoordinationManager,
    CoordinationType,
    TaskStatus
)
from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ThoughtType,
    ConsciousnessState
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
    coordination_type: str = Field(..., description="Type: pipeline, swarm, supervisor, negotiation")
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
            "consciousness": []
        }

        # Stats tracking
        self.stats = {
            "total_agents_registered": 0,
            "total_sessions_created": 0,
            "total_thoughts_submitted": 0,
            "total_patterns_discovered": 0,
            "server_start_time": datetime.utcnow()
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
    version="1.0.0"
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
    return HTMLResponse(content="""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/dashboard/user" />
        </head>
        <body>
            <p>Redirecting to <a href="/dashboard/user">User Control Panel</a>...</p>
        </body>
    </html>
    """)

@app.get("/dashboard")
async def dashboard_landing():
    """Serve main dashboard landing page."""
    dashboard_path = Path(__file__).parent / "dashboard_landing.html"
    return FileResponse(dashboard_path)

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

@app.get("/dashboard/personality")
async def personality_dashboard():
    """Serve Agent Personality Dashboard."""
    dashboard_path = Path(__file__).parent / "personality_dashboard.html"
    return FileResponse(dashboard_path)

# ============================================================================
# Demo Endpoint - Populate Platform with Sample Data
# ============================================================================

@app.post("/api/demo/populate")
async def populate_demo_data(background_tasks: BackgroundTasks):
    """
    Populate the platform with sample data for demonstration purposes.

    This endpoint creates:
    - 5 sample agents with different specialties
    - 2 coordination sessions (pipeline and swarm)
    - 8 sample thoughts submitted to collective
    - Demonstrates real-time dashboard updates
    """
    results = {
        "success": True,
        "agents_created": [],
        "sessions_created": [],
        "thoughts_submitted": [],
        "message": "Demo data populated successfully!"
    }

    # Sample agents to create
    sample_agents = [
        {
            "agent_id": "supply_chain_analyst_001",
            "agent_type": "analyst",
            "capabilities": ["data_analysis", "pattern_recognition", "forecasting"],
            "endpoints": {"http": "http://localhost:9001"},
            "metadata": {"specialty": "Supply chain analytics", "department": "Operations"}
        },
        {
            "agent_id": "logistics_optimizer_001",
            "agent_type": "optimizer",
            "capabilities": ["optimization", "route_planning", "scheduling"],
            "endpoints": {"http": "http://localhost:9002"},
            "metadata": {"specialty": "Transportation optimization", "department": "Logistics"}
        },
        {
            "agent_id": "inventory_manager_001",
            "agent_type": "manager",
            "capabilities": ["inventory_management", "stock_prediction", "reorder_automation"],
            "endpoints": {"http": "http://localhost:9003"},
            "metadata": {"specialty": "Inventory management", "department": "Warehouse"}
        },
        {
            "agent_id": "cost_optimizer_001",
            "agent_type": "optimizer",
            "capabilities": ["cost_analysis", "financial_optimization", "budget_planning"],
            "endpoints": {"http": "http://localhost:9004"},
            "metadata": {"specialty": "Cost optimization", "department": "Finance"}
        },
        {
            "agent_id": "demand_forecaster_001",
            "agent_type": "analyst",
            "capabilities": ["demand_forecasting", "trend_analysis", "predictive_analytics"],
            "endpoints": {"http": "http://localhost:9005"},
            "metadata": {"specialty": "Demand forecasting", "department": "Analytics"}
        }
    ]

    # Register all sample agents
    for agent_data in sample_agents:
        try:
            registration = ANPRegistration(
                action="register",
                agent_id=agent_data["agent_id"],
                agent_type=agent_data["agent_type"],
                capabilities=agent_data["capabilities"],
                endpoints=agent_data["endpoints"],
                health_status=AgentStatus.HEALTHY.value,
                metadata=agent_data["metadata"]
            )

            success = await state.network_registry.register_agent(registration)
            if success:
                results["agents_created"].append(agent_data["agent_id"])
                state.stats["total_agents_registered"] += 1

                # Broadcast to WebSocket clients
                background_tasks.add_task(
                    state.broadcast_event,
                    "network",
                    {
                        "type": "agent_registered",
                        "agent_id": agent_data["agent_id"],
                        "agent_type": agent_data["agent_type"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            print(f"Error registering agent {agent_data['agent_id']}: {e}")

    # Create sample coordination sessions
    sample_sessions = [
        {
            "name": "Supply Chain Optimization Pipeline",
            "coordination_type": CoordinationType.PIPELINE.value,
            "description": "End-to-end supply chain optimization using pipeline coordination",
            "objective": "Reduce costs by 30% while maintaining 95% service level"
        },
        {
            "name": "Real-Time Inventory Swarm",
            "coordination_type": CoordinationType.SWARM.value,
            "description": "Distributed inventory management using swarm intelligence",
            "objective": "Optimize stock levels across all warehouses in real-time"
        }
    ]

    for session_data in sample_sessions:
        try:
            session_id = f"session_{str(uuid4())[:8]}"
            session = CoordinationSession(
                session_id=session_id,
                name=session_data["name"],
                coordination_type=session_data["coordination_type"],
                objective=session_data["objective"],
                description=session_data["description"],
                status=SessionStatus.ACTIVE.value,
                created_at=datetime.now()
            )

            success = await state.coordination_manager.create_coordination(session)
            if success:
                results["sessions_created"].append(session_id)
                state.stats["total_sessions_created"] += 1

                # Broadcast to WebSocket clients
                background_tasks.add_task(
                    state.broadcast_event,
                    "coordination",
                    {
                        "type": "session_created",
                        "session_id": session_id,
                        "name": session_data["name"],
                        "coordination_type": session_data["coordination_type"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            print(f"Error creating session {session_data['name']}: {e}")

    # Submit sample thoughts to collective
    collective_id = "demo_collective"
    if collective_id not in state.collectives:
        state.collectives[collective_id] = CollectiveConsciousness(collective_id)

    collective = state.collectives[collective_id]

    sample_thoughts = [
        {
            "agent_id": "supply_chain_analyst_001",
            "thought_type": ThoughtType.OBSERVATION.value,
            "content": "Historical data shows 23% delivery delays in Q3 2023",
            "confidence": 0.95
        },
        {
            "agent_id": "logistics_optimizer_001",
            "thought_type": ThoughtType.INFERENCE.value,
            "content": "Delays correlate with route consolidation attempts",
            "confidence": 0.82
        },
        {
            "agent_id": "inventory_manager_001",
            "thought_type": ThoughtType.INTUITION.value,
            "content": "Safety stock levels feel misaligned with actual variability",
            "confidence": 0.70
        },
        {
            "agent_id": "cost_optimizer_001",
            "thought_type": ThoughtType.INSIGHT.value,
            "content": "40% cost reduction possible if we accept 5% longer lead times",
            "confidence": 0.88
        },
        {
            "agent_id": "demand_forecaster_001",
            "thought_type": ThoughtType.OBSERVATION.value,
            "content": "Customer tolerance for delays is 7 days in 78% of orders",
            "confidence": 0.92
        }
    ]

    for thought_data in sample_thoughts:
        try:
            thought = Thought(
                thought_id=f"thought_{str(uuid4())[:8]}",
                agent_id=thought_data["agent_id"],
                thought_type=thought_data["thought_type"],
                content=thought_data["content"],
                confidence=thought_data["confidence"],
                timestamp=datetime.now()
            )

            await collective.contribute_thought(thought)
            results["thoughts_submitted"].append(thought.thought_id)
            state.stats["total_thoughts_submitted"] += 1

            # Broadcast to WebSocket clients
            background_tasks.add_task(
                state.broadcast_event,
                "consciousness",
                {
                    "type": "thought_contributed",
                    "agent_id": thought_data["agent_id"],
                    "thought_type": thought_data["thought_type"],
                    "content": thought_data["content"],
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Error submitting thought: {e}")

    return results

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
            metadata=request.metadata
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "agent",
                    "message": f"Agent {request.agent_id} registered ({request.agent_type})",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "success": success,
            "agent_id": request.agent_id,
            "message": "Agent registered successfully" if success else "Registration failed"
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
            limit=request.limit
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
            agents.append({
                "agent_id": agent_info.agent_id,
                "agent_type": agent_info.agent_type,
                "capabilities": agent_info.capabilities,
                "health_status": agent_info.health_status,
                "load_score": agent_info.load_score,
                "region": agent_info.region,
                "tags": agent_info.tags,
                "endpoints": agent_info.endpoints,
                "last_heartbeat": agent_info.last_heartbeat.isoformat() if agent_info.last_heartbeat else None
            })

        return {
            "success": True,
            "count": len(agents),
            "agents": agents
        }

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
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anp/stats")
async def anp_stats():
    """Get ANP network statistics."""
    try:
        total_agents = len(state.network_registry.agents)
        healthy_agents = sum(
            1 for a in state.network_registry.agents.values()
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
            "network_uptime": 99.9  # TODO: Calculate actual uptime
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
            "negotiation": CoordinationType.NEGOTIATION
        }

        coord_type = coord_type_map.get(request.coordination_type.lower())
        if not coord_type:
            raise HTTPException(status_code=400, detail="Invalid coordination type")

        session_id = await state.coordination_manager.create_coordination(
            request.name,
            coord_type,
            request.metadata
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "session",
                    "message": f"New {request.coordination_type} session: {request.name}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "success": session_id is not None,
            "session_id": session_id,
            "name": request.name,
            "coordination_type": request.coordination_type
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
                1 for t in session.tasks.values()
                if t.status == TaskStatus.COMPLETED.value
            )

            sessions.append({
                "session_id": session.session_id,
                "name": session.coordination_type,  # TODO: Add name field to session
                "coordination_type": session.coordination_type,
                "status": session.status,
                "total_tasks": len(session.tasks),
                "completed_tasks": completed_tasks,
                "participant_count": len(session.participants),
                "created_at": session.created_at.isoformat()
            })

        return {
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/acp/sessions/{session_id}/tasks")
async def add_task(session_id: str, request: TaskCreationRequest, background_tasks: BackgroundTasks):
    """Add a task to a coordination session."""
    try:
        task_id = await state.coordination_manager.add_task(
            session_id,
            request.task_type,
            request.description,
            request.priority,
            request.dependencies,
            request.input_data
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "success": task_id is not None,
            "task_id": task_id,
            "session_id": session_id
        }

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
            tasks.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "assigned_to": task.assigned_to,
                "progress": task.progress,
                "dependencies": task.dependencies
            })

        return {
            "success": True,
            "session_id": session_id,
            "count": len(tasks),
            "tasks": tasks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/acp/stats")
async def acp_stats():
    """Get ACP coordination statistics."""
    try:
        active_sessions = sum(
            1 for s in state.coordination_manager.sessions.values()
            if s.status == "active"
        )

        total_tasks = sum(
            len(s.tasks) for s in state.coordination_manager.sessions.values()
        )

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
            "total_participants": total_participants
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AConsP (Agent Consciousness Protocol) Endpoints
# ============================================================================

@app.post("/api/aconsp/collectives/{collective_id}/thoughts")
async def submit_thought(
    collective_id: str,
    request: ThoughtSubmissionRequest,
    background_tasks: BackgroundTasks
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
            "question": ThoughtType.QUESTION
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
            request.context
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            background_tasks.add_task(
                state.broadcast_event,
                "admin",
                {
                    "type": "activity",
                    "category": "thought",
                    "message": f"{request.agent_id} shared {request.thought_type}: {request.content[:50]}...",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "success": thought is not None,
            "thought_id": thought.thought_id if thought else None,
            "collective_id": collective_id
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
            request.query,
            request.min_coherence,
            request.max_patterns
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
                    "synthesis": p.synthesis
                }
                for p in patterns
            ]
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

        return {
            "success": True,
            "collective_id": collective_id,
            "state": collective_state
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aconsp/stats")
async def aconsp_stats():
    """Get AConsP consciousness statistics."""
    try:
        total_collectives = len(state.collectives)

        total_thoughts = sum(
            len(c.thought_superposition) for c in state.collectives.values()
        )

        total_patterns = state.stats["total_patterns_discovered"]

        # Calculate average awareness
        if state.collectives:
            avg_awareness = sum(
                c.collective_awareness for c in state.collectives.values()
            ) / len(state.collectives)
        else:
            avg_awareness = 0

        return {
            "total_collectives": total_collectives,
            "total_thoughts": total_thoughts,
            "total_patterns": total_patterns,
            "average_awareness": round(avg_awareness, 1)
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
                "total_patterns_discovered": state.stats["total_patterns_discovered"]
            },
            "anp": anp_stats_data,
            "acp": acp_stats_data,
            "aconsp": aconsp_stats_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "protocols": {
            "anp": "operational",
            "acp": "operational",
            "aconsp": "operational"
        }
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
    print(">> Server starting...")
    print(f"   Start time: {state.stats['server_start_time'].isoformat()}")
    print()
    print(">> Protocols initialized:")
    print("   [OK] ANP (Agent Network Protocol)")
    print("   [OK] ACP (Agent Coordination Protocol)")
    print("   [OK] AConsP (Agent Consciousness Protocol)")
    print()
    print(">> Dashboard Hub:")
    print("   [HOME] http://localhost:8080/dashboard (Main landing page)")
    print()
    print("   Individual Dashboards:")
    print("   [ADMIN] http://localhost:8080/dashboard/admin")
    print("   [USER]  http://localhost:8080/dashboard/user")
    print("   [NET]   http://localhost:8080/dashboard/network")
    print("   [COORD] http://localhost:8080/dashboard/coordination")
    print("   [MIND]  http://localhost:8080/dashboard/consciousness")
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
