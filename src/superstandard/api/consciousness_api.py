"""
Consciousness API - REST + WebSocket Endpoints

This module provides a complete FastAPI-based REST and WebSocket API for
consciousness protocol integration, enabling:

- REST endpoints for consciousness management
- WebSocket streams for real-time consciousness events
- Metrics and health monitoring
- Multi-collective management
- Pattern discovery queries

Usage:
    # Run standalone
    python -m uvicorn superstandard.api.consciousness_api:app --reload --port 8000

    # Or programmatically
    import uvicorn
    from superstandard.api.consciousness_api import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

Endpoints:
    GET  /api/consciousness/                        - List all collectives
    POST /api/consciousness/                        - Create new collective
    GET  /api/consciousness/{id}                    - Get collective state
    DELETE /api/consciousness/{id}                  - Delete collective
    POST /api/consciousness/{id}/agents             - Register agent
    DELETE /api/consciousness/{id}/agents/{agent_id} - Remove agent
    POST /api/consciousness/{id}/thoughts           - Contribute thought
    POST /api/consciousness/{id}/collapse           - Trigger collapse
    GET  /api/consciousness/{id}/patterns           - Get patterns
    GET  /api/consciousness/{id}/metrics            - Get metrics
    GET  /api/consciousness/{id}/health             - Health check
    WS   /api/consciousness/{id}/stream             - Real-time event stream

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ConsciousnessState,
    ThoughtType,
    EmergentPattern,
)
from superstandard.protocols.consciousness_persistence import (
    PersistentCollectiveConsciousness,
    JSONStorageBackend,
)


# ============================================================================
# Pydantic Models for API
# ============================================================================


class CreateCollectiveRequest(BaseModel):
    """Request to create new collective consciousness."""

    consciousness_id: str = Field(..., description="Unique ID for collective")
    persistent: bool = Field(default=False, description="Enable persistence")
    auto_save: bool = Field(default=True, description="Enable auto-save")
    save_interval: int = Field(default=60, description="Auto-save interval (seconds)")


class RegisterAgentRequest(BaseModel):
    """Request to register agent with collective."""

    agent_id: str = Field(..., description="Unique agent ID")
    initial_state: str = Field(default="awakening", description="Initial consciousness state")


class ContributeThoughtRequest(BaseModel):
    """Request to contribute thought to collective."""

    agent_id: str = Field(..., description="Agent contributing thought")
    thought_type: str = Field(..., description="Type of thought")
    content: Any = Field(..., description="Thought content")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level")
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0, description="Emotional tone")


class CollapseConsciousnessRequest(BaseModel):
    """Request to collapse consciousness."""

    query: str = Field(..., description="Query to pose to collective")
    min_coherence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum coherence threshold"
    )


class ConsciousnessEvent(BaseModel):
    """Real-time consciousness event for WebSocket stream."""

    event_type: str = Field(..., description="Event type")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    consciousness_id: str = Field(..., description="Collective ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")


# ============================================================================
# Consciousness Manager
# ============================================================================


class ConsciousnessManager:
    """
    Manages multiple collective consciousness instances.

    Handles creation, lifecycle, and event broadcasting for all collectives.
    """

    def __init__(self, storage_path: str = "./consciousness_storage"):
        self.collectives: Dict[str, CollectiveConsciousness] = {}
        self.storage_path = storage_path
        self.websocket_connections: Dict[str, List[WebSocket]] = (
            {}
        )  # consciousness_id -> [websockets]
        self.event_queues: Dict[str, asyncio.Queue] = {}

    async def create_collective(
        self,
        consciousness_id: str,
        persistent: bool = False,
        auto_save: bool = True,
        save_interval: int = 60,
    ) -> CollectiveConsciousness:
        """Create new collective consciousness."""
        if consciousness_id in self.collectives:
            raise ValueError(f"Collective {consciousness_id} already exists")

        if persistent:
            storage = JSONStorageBackend(self.storage_path)
            collective = PersistentCollectiveConsciousness(
                consciousness_id, storage, auto_save=auto_save, save_interval=save_interval
            )
            await collective.initialize()
        else:
            collective = CollectiveConsciousness(consciousness_id)

        self.collectives[consciousness_id] = collective
        self.websocket_connections[consciousness_id] = []
        self.event_queues[consciousness_id] = asyncio.Queue()

        # Broadcast creation event
        await self._broadcast_event(
            consciousness_id,
            "collective_created",
            {"consciousness_id": consciousness_id, "persistent": persistent},
        )

        return collective

    async def get_collective(self, consciousness_id: str) -> CollectiveConsciousness:
        """Get existing collective."""
        if consciousness_id not in self.collectives:
            raise ValueError(f"Collective {consciousness_id} not found")
        return self.collectives[consciousness_id]

    async def delete_collective(self, consciousness_id: str) -> bool:
        """Delete collective."""
        if consciousness_id not in self.collectives:
            return False

        collective = self.collectives[consciousness_id]

        # Shutdown if persistent
        if isinstance(collective, PersistentCollectiveConsciousness):
            await collective.shutdown()

        # Close all websockets
        for ws in self.websocket_connections.get(consciousness_id, []):
            await ws.close()

        # Remove
        del self.collectives[consciousness_id]
        if consciousness_id in self.websocket_connections:
            del self.websocket_connections[consciousness_id]
        if consciousness_id in self.event_queues:
            del self.event_queues[consciousness_id]

        return True

    def list_collectives(self) -> List[str]:
        """List all collective IDs."""
        return list(self.collectives.keys())

    async def register_websocket(self, consciousness_id: str, websocket: WebSocket):
        """Register WebSocket for event stream."""
        if consciousness_id not in self.websocket_connections:
            self.websocket_connections[consciousness_id] = []
        self.websocket_connections[consciousness_id].append(websocket)

    async def unregister_websocket(self, consciousness_id: str, websocket: WebSocket):
        """Unregister WebSocket."""
        if consciousness_id in self.websocket_connections:
            self.websocket_connections[consciousness_id].remove(websocket)

    async def _broadcast_event(self, consciousness_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all WebSocket connections."""
        event = ConsciousnessEvent(
            event_type=event_type, consciousness_id=consciousness_id, data=data
        )

        # Add to queue
        if consciousness_id in self.event_queues:
            await self.event_queues[consciousness_id].put(event)

        # Broadcast to websockets
        if consciousness_id in self.websocket_connections:
            disconnected = []
            for ws in self.websocket_connections[consciousness_id]:
                try:
                    await ws.send_json(event.dict())
                except Exception:
                    disconnected.append(ws)

            # Remove disconnected
            for ws in disconnected:
                await self.unregister_websocket(consciousness_id, ws)

    async def broadcast_agent_registered(self, consciousness_id: str, agent_id: str, state: str):
        """Broadcast agent registration."""
        await self._broadcast_event(
            consciousness_id, "agent_registered", {"agent_id": agent_id, "state": state}
        )

    async def broadcast_thought_contributed(
        self, consciousness_id: str, agent_id: str, thought_type: str
    ):
        """Broadcast thought contribution."""
        await self._broadcast_event(
            consciousness_id,
            "thought_contributed",
            {"agent_id": agent_id, "thought_type": thought_type},
        )

    async def broadcast_consciousness_collapsed(self, consciousness_id: str, patterns_count: int):
        """Broadcast consciousness collapse."""
        await self._broadcast_event(
            consciousness_id, "consciousness_collapsed", {"patterns_discovered": patterns_count}
        )

    async def broadcast_pattern_discovered(self, consciousness_id: str, pattern: EmergentPattern):
        """Broadcast pattern discovery."""
        await self._broadcast_event(
            consciousness_id,
            "pattern_discovered",
            {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "coherence": pattern.coherence_score,
                "novelty": pattern.novelty_score,
                "impact": pattern.impact_potential,
                "agents": list(pattern.contributing_agents),
            },
        )


# ============================================================================
# FastAPI Application
# ============================================================================

# Create FastAPI app
app = FastAPI(
    title="Consciousness API",
    description="REST and WebSocket API for Agent Consciousness Protocol",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global manager
manager = ConsciousnessManager()


# ============================================================================
# REST Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Consciousness API",
        "version": "1.0.0",
        "status": "operational",
        "collectives": len(manager.list_collectives()),
        "documentation": "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the consciousness dashboard."""
    dashboard_path = Path(__file__).parent / "consciousness_dashboard.html"
    if dashboard_path.exists():
        return dashboard_path.read_text()
    return "<h1>Dashboard not found</h1>"


@app.get("/api/consciousness/")
async def list_collectives():
    """List all collective consciousness instances."""
    collectives = []
    for cid in manager.list_collectives():
        collective = await manager.get_collective(cid)
        state = collective.get_consciousness_state()
        collectives.append(
            {
                "consciousness_id": cid,
                "total_agents": state["total_agents"],
                "total_thoughts": state["total_thoughts"],
                "emergent_patterns": state["emergent_patterns_discovered"],
                "collective_awareness": state["collective_awareness"],
            }
        )
    return {"collectives": collectives}


@app.post("/api/consciousness/")
async def create_collective(request: CreateCollectiveRequest):
    """Create new collective consciousness."""
    try:
        collective = await manager.create_collective(
            request.consciousness_id,
            persistent=request.persistent,
            auto_save=request.auto_save,
            save_interval=request.save_interval,
        )

        return {
            "consciousness_id": collective.consciousness_id,
            "persistent": request.persistent,
            "status": "created",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/consciousness/{consciousness_id}")
async def get_collective_state(consciousness_id: str):
    """Get complete state of collective consciousness."""
    try:
        collective = await manager.get_collective(consciousness_id)
        return collective.get_consciousness_state()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/consciousness/{consciousness_id}")
async def delete_collective(consciousness_id: str):
    """Delete collective consciousness."""
    success = await manager.delete_collective(consciousness_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collective not found")
    return {"status": "deleted", "consciousness_id": consciousness_id}


@app.post("/api/consciousness/{consciousness_id}/agents")
async def register_agent(consciousness_id: str, request: RegisterAgentRequest):
    """Register agent with collective."""
    try:
        collective = await manager.get_collective(consciousness_id)

        # Parse state
        try:
            state = ConsciousnessState(request.initial_state)
        except ValueError:
            state = ConsciousnessState.AWAKENING

        success = await collective.register_agent(request.agent_id, state)

        if success:
            await manager.broadcast_agent_registered(
                consciousness_id, request.agent_id, state.value
            )

        return {
            "agent_id": request.agent_id,
            "consciousness_id": consciousness_id,
            "state": state.value,
            "registered": success,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/consciousness/{consciousness_id}/thoughts")
async def contribute_thought(consciousness_id: str, request: ContributeThoughtRequest):
    """Contribute thought to collective."""
    try:
        collective = await manager.get_collective(consciousness_id)

        # Parse thought type
        try:
            thought_type = ThoughtType(request.thought_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid thought type: {request.thought_type}"
            )

        thought = await collective.contribute_thought(
            request.agent_id,
            thought_type,
            request.content,
            request.confidence,
            request.emotional_valence,
        )

        await manager.broadcast_thought_contributed(
            consciousness_id, request.agent_id, thought_type.value
        )

        return {
            "agent_id": thought.agent_id,
            "thought_type": thought.thought_type.value,
            "timestamp": thought.timestamp.isoformat(),
            "quantum_state": thought.quantum_state,
            "entangled_with": len(thought.entangled_with),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/consciousness/{consciousness_id}/collapse")
async def collapse_consciousness(consciousness_id: str, request: CollapseConsciousnessRequest):
    """Trigger consciousness collapse to discover emergent patterns."""
    try:
        collective = await manager.get_collective(consciousness_id)

        patterns = await collective.collapse_consciousness(request.query, request.min_coherence)

        await manager.broadcast_consciousness_collapsed(consciousness_id, len(patterns))

        # Broadcast each pattern
        for pattern in patterns:
            await manager.broadcast_pattern_discovered(consciousness_id, pattern)

        return {
            "query": request.query,
            "patterns_discovered": len(patterns),
            "patterns": [pattern.to_dict() for pattern in patterns],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/consciousness/{consciousness_id}/patterns")
async def get_patterns(consciousness_id: str):
    """Get all emergent patterns."""
    try:
        collective = await manager.get_collective(consciousness_id)
        return {"patterns": [p.to_dict() for p in collective.emergent_patterns]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/consciousness/{consciousness_id}/metrics")
async def get_metrics(consciousness_id: str):
    """Get consciousness metrics."""
    try:
        collective = await manager.get_collective(consciousness_id)
        state = collective.get_consciousness_state()

        return {
            "consciousness_id": consciousness_id,
            "metrics": {
                "total_agents": state["total_agents"],
                "active_agents": state["active_agents"],
                "superconscious_agents": state["superconscious_agents"],
                "total_thoughts": state["total_thoughts"],
                "thoughts_in_superposition": state["thoughts_in_superposition"],
                "emergent_patterns": state["emergent_patterns_discovered"],
                "collective_awareness": state["collective_awareness"],
                "average_integration": state["average_integration_score"],
                "entanglement_density": state["entanglement_density"],
                "total_collapses": state["total_collapses"],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/consciousness/{consciousness_id}/health")
async def check_health(consciousness_id: str):
    """Health check for collective consciousness."""
    try:
        collective = await manager.get_collective(consciousness_id)
        state = collective.get_consciousness_state()

        # Determine health status
        health = "healthy"
        issues = []

        if state["collective_awareness"] < 0.1:
            health = "degraded"
            issues.append("Low collective awareness")

        if state["entanglement_density"] > 10.0:
            health = "warning"
            issues.append("High entanglement density - consider pruning")

        if state["active_agents"] == 0:
            health = "warning"
            issues.append("No active agents")

        return {
            "consciousness_id": consciousness_id,
            "health": health,
            "issues": issues,
            "metrics": {
                "collective_awareness": state["collective_awareness"],
                "active_agents": state["active_agents"],
                "entanglement_density": state["entanglement_density"],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@app.websocket("/api/consciousness/{consciousness_id}/stream")
async def consciousness_stream(websocket: WebSocket, consciousness_id: str):
    """
    Real-time consciousness event stream.

    Events:
    - agent_registered: Agent joins collective
    - thought_contributed: Thought added
    - consciousness_collapsed: Collapse triggered
    - pattern_discovered: Emergent pattern found
    """
    await websocket.accept()

    # Check if collective exists
    if consciousness_id not in manager.collectives:
        await websocket.send_json({"error": f"Collective {consciousness_id} not found"})
        await websocket.close()
        return

    # Register websocket
    await manager.register_websocket(consciousness_id, websocket)

    try:
        # Send initial state
        collective = await manager.get_collective(consciousness_id)
        await websocket.send_json(
            {"event_type": "connected", "data": collective.get_consciousness_state()}
        )

        # Keep connection alive and listen for disconnect
        while True:
            # Just keep alive - events sent via broadcast
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        await manager.unregister_websocket(consciousness_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.unregister_websocket(consciousness_id, websocket)


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("Consciousness API starting...")
    print(f"Storage path: {manager.storage_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Consciousness API shutting down...")

    # Shutdown all persistent collectives
    for consciousness_id, collective in manager.collectives.items():
        if isinstance(collective, PersistentCollectiveConsciousness):
            await collective.shutdown()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
