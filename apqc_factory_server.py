"""
APQC Agent Factory API Server
==============================

FastAPI server providing REST API for the APQC Agent Factory.
Enables UI-driven agent configuration and generation.

Features:
- GET /api/apqc/tasks - List all task configurations
- GET /api/apqc/tasks/{agent_id} - Get specific task config
- PUT /api/apqc/tasks/{agent_id} - Update task configuration
- POST /api/apqc/generate/{agent_id} - Generate single agent
- POST /api/apqc/generate-all - Generate all enabled agents
- POST /api/apqc/generate-category/{category_id} - Generate category agents
- GET /api/apqc/stats - Get hierarchy statistics
- POST /api/apqc/initialize - Initialize from hierarchy file

Port: 8765
Frontend: Serves static files from dashboard_frontend/

Version: 1.0.0
Date: 2025-11-17
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from apqc_agent_factory import (
    APQCAgentFactory,
    AgentConfigurationDB,
    APQCAgentGenerator
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="APQC Agent Factory API",
    description="UI-driven agent generation for APQC PCF framework",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize factory
factory = APQCAgentFactory()
db = AgentConfigurationDB()
generator = APQCAgentGenerator()


# ============================================================================
# Pydantic Models
# ============================================================================

class TaskUpdateModel(BaseModel):
    description: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[str] = None
    autonomous_level: Optional[float] = None
    collaboration_mode: Optional[str] = None
    learning_enabled: Optional[bool] = None
    compute_mode: Optional[str] = None
    memory_mode: Optional[str] = None
    api_budget_mode: Optional[str] = None
    requires_api_keys: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    custom_config: Optional[Dict[str, Any]] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/apqc/tasks")
async def get_all_tasks():
    """Get all task configurations"""
    try:
        configs = db.get_all_configs()
        return configs
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/apqc/tasks/{agent_id}")
async def get_task(agent_id: str):
    """Get specific task configuration"""
    try:
        config = db.get_config_by_id(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Task {agent_id} not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/apqc/tasks/{agent_id}")
async def update_task(agent_id: str, updates: TaskUpdateModel):
    """Update task configuration"""
    try:
        # Verify task exists
        config = db.get_config_by_id(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Task {agent_id} not found")

        # Update configuration
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        db.update_config(agent_id, update_dict)

        # Return updated config
        updated_config = db.get_config_by_id(agent_id)
        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apqc/generate/{agent_id}")
async def generate_agent(agent_id: str):
    """Generate single agent"""
    try:
        success, path_or_error = generator.generate_agent(agent_id)
        if success:
            return {"success": True, "path": path_or_error, "agent_id": agent_id}
        else:
            return {"success": False, "error": path_or_error, "agent_id": agent_id}
    except Exception as e:
        logger.error(f"Failed to generate agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apqc/generate-all")
async def generate_all_agents():
    """Generate all enabled agents"""
    try:
        results = generator.generate_all()
        return results
    except Exception as e:
        logger.error(f"Failed to generate all agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apqc/generate-category/{category_id}")
async def generate_category_agents(category_id: str):
    """Generate all agents for a specific category"""
    try:
        results = generator.generate_all(category_id=category_id)
        return results
    except Exception as e:
        logger.error(f"Failed to generate category {category_id} agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/apqc/stats")
async def get_stats():
    """Get hierarchy statistics"""
    try:
        stats = factory.get_hierarchy_summary()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apqc/initialize")
async def initialize_hierarchy():
    """Initialize configurations from hierarchy file"""
    try:
        result = factory.initialize_from_hierarchy()
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Hierarchy file not found: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "APQC Agent Factory",
        "version": "1.0.0"
    }


# ============================================================================
# Static Files (Frontend)
# ============================================================================

# Serve APQC hierarchy explorer
@app.get("/apqc")
async def serve_apqc_explorer():
    """Serve APQC hierarchy explorer page"""
    frontend_dir = Path(__file__).parent / "dashboard_frontend"
    html_file = frontend_dir / "apqc_explorer.html"

    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Create minimal HTML page that loads the explorer
        return """
<!DOCTYPE html>
<html>
<head>
    <title>APQC Hierarchy Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <link rel="stylesheet" href="/dashboard_frontend/styles.css">
    <style>
        :root {
            --bg-primary: #0f1419;
            --bg-secondary: #1a1f27;
            --card-bg: #151a21;
            --border-color: #2d3748;
            --text-primary: #e0e0e0;
            --text-secondary: #a0aec0;
            --text-muted: #718096;
            --accent-primary: #3b82f6;
            --status-healthy: #48bb78;
            --status-warning: #ed8936;
            --status-offline: #718096;
            --text-warning: #ed8936;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        .spinner {
            border: 3px solid var(--border-color);
            border-top: 3px solid var(--accent-primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel" src="/dashboard_frontend/apqc_hierarchy_explorer.tsx"></script>
    <script type="text/babel">
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<window.APQCHierarchyExplorer onClose={() => window.location.href = '/'} />);
    </script>
</body>
</html>
"""


# Serve static frontend files
frontend_dir = Path(__file__).parent / "dashboard_frontend"
if frontend_dir.exists():
    app.mount("/dashboard_frontend", StaticFiles(directory=str(frontend_dir)), name="dashboard_frontend")


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("=" * 60)
    logger.info("🏭 APQC Agent Factory API Server")
    logger.info("=" * 60)
    logger.info(f"📊 Version: 1.0.0")
    logger.info(f"🌐 API Docs: http://localhost:8765/docs")
    logger.info(f"🎯 APQC Explorer: http://localhost:8765/apqc")
    logger.info(f"💡 Configure all ~840 APQC agents through the UI!")
    logger.info("=" * 60)

    # Check if database is initialized
    configs = db.get_all_configs()
    if len(configs) == 0:
        logger.warning("⚠️ No tasks configured - run initialization:")
        logger.warning("   POST /api/apqc/initialize")
        logger.warning("   OR")
        logger.warning("   python apqc_agent_factory.py --init")
    else:
        logger.info(f"✅ Database ready: {len(configs)} tasks configured")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )
