"""
Agent Registry Sync API

Provides endpoints for the AgentRegistrySyncAgent to automatically
discover and register agents.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.agents.meta.agent_registry_sync_agent import agent_registry_sync_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/sync")
async def trigger_sync() -> Dict[str, Any]:
    """
    Trigger an agent registry synchronization.

    Scans all configured agent directories and discovers new agents.
    """
    try:
        result = await agent_registry_sync_agent.sync()
        return result
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """
    Get the current synchronization status.

    Returns information about the last sync and statistics.
    """
    return agent_registry_sync_agent.get_sync_status()


@router.get("/discover/{directory}")
async def discover_in_directory(directory: str) -> Dict[str, Any]:
    """
    Discover agents in a specific directory.

    Args:
        directory: Directory path to scan (e.g., "app/agents/hybrid_ai")
    """
    try:
        discovered = agent_registry_sync_agent.discover_agents(directory)
        return {"directory": directory, "agents_found": len(discovered), "agents": discovered}
    except Exception as e:
        logger.error(f"Discovery failed for {directory}: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/register")
async def register_agent(agent_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a single agent.

    Args:
        agent_metadata: Agent metadata dictionary
    """
    try:
        success = await agent_registry_sync_agent.register_agent(agent_metadata)
        if success:
            return {"status": "success", "agent_id": agent_metadata.get("id")}
        else:
            raise HTTPException(status_code=400, detail="Agent registration failed")
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/unregister/{agent_id}")
async def unregister_agent(agent_id: str) -> Dict[str, Any]:
    """
    Unregister an agent.

    Args:
        agent_id: ID of the agent to unregister
    """
    try:
        success = await agent_registry_sync_agent.unregister_agent(agent_id)
        if success:
            return {"status": "success", "agent_id": agent_id}
        else:
            raise HTTPException(status_code=400, detail="Agent unregistration failed")
    except Exception as e:
        logger.error(f"Unregistration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")
