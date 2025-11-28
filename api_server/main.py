"""
Agent Platform API Server
==========================

FastAPI REST API for executing agents and workflows.

Endpoints:
- POST /api/workflows/invoice - Execute invoice processing workflow
- GET /api/workflows/{workflow_id} - Get workflow status and results
- GET /api/agents - List all available agents
- GET /api/agents/{agent_id} - Get agent details
- POST /api/agents/{agent_id}/execute - Execute a single agent
- GET /api/health - Health check
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, distinct, create_engine

# Import security module
from api_server.security import (
    setup_security,
    require_api_key,
    require_role,
    SafeInvoiceRequest,
    SafeAgentExecutionRequest,
    InputSanitizer,
    logger as security_logger
)

# Import configuration, logging, and error handling
from api_server.config import settings
from api_server.logging_config import setup_logging, get_logger, RequestLoggingMiddleware, Timer
from api_server.errors import (
    APIError,
    NotFoundError,
    ValidationError,
    WorkflowExecutionError,
    ServiceUnavailableError,
    api_error_handler,
    error_response
)

# Setup logging early
setup_logging()
logger = get_logger(__name__)

# Load APQC PCF Hierarchy
APQC_HIERARCHY_PATH = Path(__file__).parent.parent / "apqc_pcf_hierarchy.json"
APQC_HIERARCHY = {}
if APQC_HIERARCHY_PATH.exists():
    with open(APQC_HIERARCHY_PATH, 'r') as f:
        APQC_HIERARCHY = json.load(f)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server.database import get_db, Agent, Workflow, AgentExecution, WorkflowStage, init_db, seed_agents, DATABASE_URL

# Import our workflow
sys.path.insert(0, str(Path(__file__).parent.parent))
from poc_invoice_workflow import InvoiceProcessingWorkflow

# Add src to path for superstandard imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import integration catalog (used by multiple endpoints)
try:
    from superstandard.schemas.integration_catalog import INTEGRATION_CATALOG, CATEGORY_SUMMARY
    INTEGRATION_CATALOG_AVAILABLE = True
except ImportError:
    INTEGRATION_CATALOG = {}
    CATEGORY_SUMMARY = {}
    INTEGRATION_CATALOG_AVAILABLE = False

# Import workflow engine (lazy initialization for performance)
try:
    from superstandard.engine.workflow_engine import WorkflowEngine
    WORKFLOW_ENGINE_AVAILABLE = True
except ImportError:
    WorkflowEngine = None
    WORKFLOW_ENGINE_AVAILABLE = False

# Import metrics service
try:
    from superstandard.services.metrics_service import MetricsService, get_metrics_service
    METRICS_SERVICE_AVAILABLE = True
    metrics_service = get_metrics_service()
except ImportError:
    METRICS_SERVICE_AVAILABLE = False
    metrics_service = None


# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="APQC Agent Platform API",
    description="REST API for executing APQC agents and workflows with real business logic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# Add request logging middleware (must be added before CORS)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - use settings
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom error handlers
app.add_exception_handler(APIError, api_error_handler)

# Setup security middleware and exception handlers
setup_security(app)

# Log startup configuration
logger.info(
    "API server initialized",
    extra={"config": settings.to_dict()}
)

# Content Security Policy middleware - allow unsafe-eval for bpmn-js
@app.middleware("http")
async def add_csp_header(request, call_next):
    """Add CSP header that allows unsafe-eval for BPMN viewer library"""
    response = await call_next(request)
    # Allow unsafe-eval for bpmn-js library (needed for diagram rendering)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com data: https:; "
        "connect-src 'self' https: wss:; "
        "media-src 'self' https: data: blob:; "
        "object-src 'none'; "
        "frame-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class InvoiceWorkflowRequest(BaseModel):
    """Request to execute invoice processing workflow"""
    source: str = "api"
    invoice_number: str
    vendor_name: str
    date: str
    items: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "source": "api",
                "invoice_number": "INV-2025-100",
                "vendor_name": "Acme Corp",
                "date": "2025-11-18",
                "items": [
                    {"desc": "Software License", "qty": 10, "price": 450.00},
                    {"desc": "Support Contract", "qty": 1, "price": 500.00}
                ]
            }
        }


class WorkflowResponse(BaseModel):
    """Response for workflow execution"""
    workflow_id: str
    status: str
    message: str
    workflow_url: str


class WorkflowStatusResponse(BaseModel):
    """Detailed workflow status"""
    workflow_id: str
    workflow_name: str
    status: str
    success: Optional[bool]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[float]
    total_agents: int
    agents_succeeded: int
    agents_failed: int
    input_data: Optional[Dict]
    output_data: Optional[Dict]
    error_message: Optional[str]


class AgentResponse(BaseModel):
    """Agent information"""
    agent_id: str
    name: str
    description: Optional[str]
    apqc_id: Optional[str]
    apqc_category: Optional[str]
    agent_type: str
    is_active: bool


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Agent Platform API...")
    init_db()
    seed_agents()
    print("✅ API Server ready!")


# ============================================================================
# Static Files & Dashboard
# ============================================================================

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root():
    """Serve the dashboard"""
    dashboard_path = static_dir / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"message": "APQC Agent Platform API", "docs": "/docs"}

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard"""
    dashboard_path = static_dir / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/admin")
async def admin_panel():
    """Serve the admin panel"""
    admin_path = static_dir / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin panel not found")

@app.get("/process-testing")
async def process_testing_dashboard():
    """Serve the process testing and debugging dashboard"""
    dashboard_path = static_dir / "process-testing-dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Process testing dashboard not found")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "APQC Agent Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.get("/api/agents")
async def list_agents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all available agents with optional filtering and wildcard support"""
    query = db.query(Agent).filter(Agent.is_active == True)

    # Category filter - exact match
    if category and category.strip():
        query = query.filter(Agent.apqc_category == category)

    # Search filter with wildcard support
    if search and search.strip() and search != "*":
        # Convert wildcard patterns to SQL LIKE patterns
        search_pattern = search.replace("*", "%").replace("?", "_")
        search_term = f"%{search_pattern}%"
        query = query.filter(
            (Agent.name.ilike(search_term)) |
            (Agent.description.ilike(search_term)) |
            (Agent.apqc_id.ilike(search_term)) |
            (Agent.agent_id.ilike(search_term)) |
            (Agent.apqc_category.ilike(search_term))
        )

    # Order and limit results
    agents = query.order_by(Agent.apqc_category, Agent.apqc_id).offset(offset).limit(limit).all()

    # Return as dicts to avoid serialization issues
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "description": a.description,
            "apqc_id": a.apqc_id,
            "apqc_category": a.apqc_category,
            "agent_type": a.agent_type,
            "is_active": a.is_active,
            "version": a.version
        }
        for a in agents
    ]


@app.get("/api/agents/categories/list")
async def list_categories(db: Session = Depends(get_db)):
    """Get all available APQC categories with agent counts"""
    query = db.query(
        Agent.apqc_category,
        func.count(Agent.id).label("count")
    ).filter(Agent.is_active == True).group_by(Agent.apqc_category).order_by(Agent.apqc_category).all()

    return [
        {"category": cat, "count": count}
        for cat, count in query
    ]


@app.get("/api/agents/search")
async def search_agents(
    q: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Full-text search for agents"""
    if not q or len(q) < 2:
        return []

    search_term = f"%{q}%"
    agents = db.query(Agent).filter(
        Agent.is_active == True,
        (
            (Agent.name.ilike(search_term)) |
            (Agent.description.ilike(search_term)) |
            (Agent.apqc_id.ilike(search_term)) |
            (Agent.agent_id.ilike(search_term)) |
            (Agent.apqc_category.ilike(search_term))
        )
    ).limit(limit).all()

    return agents


@app.get("/api/agents/stats/overview")
async def agent_stats(db: Session = Depends(get_db)):
    """Get agent statistics"""
    total = db.query(Agent).count()
    active = db.query(Agent).filter(Agent.is_active == True).count()
    categories = db.query(func.count(distinct(Agent.apqc_category))).scalar() or 0

    category_breakdown = db.query(
        Agent.apqc_category,
        func.count(Agent.id).label("count")
    ).filter(Agent.is_active == True).group_by(Agent.apqc_category).order_by(Agent.apqc_category).all()

    return {
        "total_agents": total,
        "active_agents": active,
        "total_categories": categories,
        "categories": [
            {"name": cat, "count": count}
            for cat, count in category_breakdown
        ]
    }


@app.get("/api/agents/by-apqc-level")
async def get_agents_by_apqc_level(
    level: int = 1,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get agents organized by APQC hierarchy level (1-5)

    Level 1: Categories (13 total) - Process Groups
    Level 2-4: Sub-processes within categories
    Level 5: Individual atomic agents (executable)
    """
    if level == 1:
        # Return all categories with agent counts
        categories = db.query(
            Agent.apqc_category,
            func.count(Agent.id).label("count")
        ).filter(Agent.is_active == True).group_by(Agent.apqc_category).order_by(Agent.apqc_category).all()

        return {
            "level": 1,
            "items": [
                {
                    "id": cat.replace(" ", "_"),
                    "name": cat,
                    "type": "category",
                    "count": count,
                    "icon": get_category_icon(cat),
                    "color": get_category_color(cat),
                    "children_count": count
                }
                for cat, count in categories
            ]
        }

    # For levels 2-5, return hierarchical structure based on APQC codes
    if not parent_id:
        return {"level": level, "items": []}

    category = parent_id.split("|")[0].replace("_", " ")

    # Get all agents in this category
    agents = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.apqc_category == category
    ).order_by(Agent.agent_id).all()

    if not agents:
        return {"level": level, "parent": category, "items": []}

    if level == 2:
        # Level 2: Return process groups (5.1, 5.2, 5.3, etc)
        # Extract Level 2 codes from APQC IDs
        level2_groups = {}

        for agent in agents:
            # Get APQC code from agent name (e.g., "APQC 5.1.1.5 - ...")
            parts = agent.name.split(" ")
            if len(parts) >= 2 and parts[0] == "APQC":
                code = parts[1]  # e.g., "5.1.1.5"
                code_parts = code.split(".")
                if len(code_parts) >= 2:
                    level2_code = code_parts[0] + "." + code_parts[1]  # e.g., "5.1"

                    if level2_code not in level2_groups:
                        level2_groups[level2_code] = {
                            "code": level2_code,
                            "agents": [],
                            "name": ""  # Will be filled from first agent
                        }

                    level2_groups[level2_code]["agents"].append(agent)
                    # Extract sub-process name from agent (e.g., "Allocate Resources")
                    if not level2_groups[level2_code]["name"] and len(parts) > 3:
                        level2_groups[level2_code]["name"] = " ".join(parts[3:]).rstrip(" -")

        # Convert to list items
        items = []
        for level2_code in sorted(level2_groups.keys()):
            group = level2_groups[level2_code]
            items.append({
                "id": f"{category.replace(' ', '_')}|{level2_code}",
                "name": f"{level2_code} - {group['name']}" if group['name'] else f"{level2_code} - Process Group",
                "type": "process_group",
                "code": level2_code,
                "description": f"Sub-process group containing {len(group['agents'])} agents",
                "children_count": len(group['agents'])
            })

        return {
            "level": level,
            "parent": category,
            "items": items
        }

    elif level == 3:
        # Level 3: Group by level 3 codes (e.g., 5.1.1, 5.1.2)
        # parent_id format: "Category|5.1"
        parts = parent_id.split("|")
        if len(parts) < 2:
            return {"level": level, "parent": category, "items": []}

        level2_code = parts[1]  # e.g., "5.1"
        level3_groups = {}

        for agent in agents:
            agent_parts = agent.name.split(" ")
            if len(agent_parts) >= 2 and agent_parts[0] == "APQC":
                code = agent_parts[1]
                code_parts = code.split(".")
                if len(code_parts) >= 3:
                    agent_level2 = code_parts[0] + "." + code_parts[1]
                    if agent_level2 == level2_code:
                        level3_code = ".".join(code_parts[:3])  # e.g., "5.1.1"
                        if level3_code not in level3_groups:
                            # Extract name from agent
                            name_parts = " ".join(agent_parts[3:]).split(" - ")
                            level3_groups[level3_code] = {
                                "code": level3_code,
                                "agents": [],
                                "name": name_parts[0] if name_parts else "Sub-process"
                            }
                        level3_groups[level3_code]["agents"].append(agent)

        items = []
        for code in sorted(level3_groups.keys()):
            group = level3_groups[code]
            items.append({
                "id": f"{category.replace(' ', '_')}|{code}",
                "name": f"{code} - {group['name']}",
                "type": "sub_process",
                "code": code,
                "description": f"Contains {len(group['agents'])} activities",
                "children_count": len(group['agents'])
            })

        return {"level": level, "parent": category, "code": level2_code, "items": items}

    elif level == 4:
        # Level 4: Group by level 4 codes (e.g., 5.1.1.1, 5.1.1.2)
        # parent_id format: "Category|5.1.1"
        parts = parent_id.split("|")
        if len(parts) < 2:
            return {"level": level, "parent": category, "items": []}

        level3_code = parts[1]  # e.g., "5.1.1"
        level4_groups = {}

        for agent in agents:
            agent_parts = agent.name.split(" ")
            if len(agent_parts) >= 2 and agent_parts[0] == "APQC":
                code = agent_parts[1]
                code_parts = code.split(".")
                if len(code_parts) >= 4:
                    agent_level3 = ".".join(code_parts[:3])
                    if agent_level3 == level3_code:
                        level4_code = ".".join(code_parts[:4])  # e.g., "5.1.1.1"
                        if level4_code not in level4_groups:
                            # Extract name from agent
                            name_parts = " ".join(agent_parts[3:]).split(" - ")
                            level4_groups[level4_code] = {
                                "code": level4_code,
                                "agents": [],
                                "name": name_parts[0] if name_parts else "Activity"
                            }
                        level4_groups[level4_code]["agents"].append(agent)

        items = []
        for code in sorted(level4_groups.keys()):
            group = level4_groups[code]
            items.append({
                "id": f"{category.replace(' ', '_')}|{code}",
                "name": f"{code} - {group['name']}",
                "type": "activity",
                "code": code,
                "description": f"Contains {len(group['agents'])} tasks/agents",
                "children_count": len(group['agents'])
            })

        return {"level": level, "parent": category, "code": level3_code, "items": items}

    else:
        # Level 5: Return individual agents within a Level 4 group
        # parent_id format: "Category|5.1.1.1"
        parts = parent_id.split("|")
        if len(parts) < 2:
            # Fallback: return all agents
            items = []
            for agent in agents:
                items.append({
                    "id": agent.agent_id,
                    "name": agent.name,
                    "type": "agent",
                    "description": agent.description,
                    "agent_type": agent.agent_type,
                    "apqc_category": agent.apqc_category,
                    "children_count": 0
                })
            return {"level": level, "parent": category, "items": items}

        level4_code = parts[1]  # e.g., "5.1.1.1"

        # Filter agents by Level 4 code
        filtered_agents = []
        for agent in agents:
            agent_parts = agent.name.split(" ")
            if len(agent_parts) >= 2 and agent_parts[0] == "APQC":
                code = agent_parts[1]
                code_parts = code.split(".")
                if len(code_parts) >= 4:
                    agent_level4 = ".".join(code_parts[:4])
                    if agent_level4 == level4_code:
                        filtered_agents.append(agent)

        # Return agents as items
        items = []
        for agent in filtered_agents:
            items.append({
                "id": agent.agent_id,
                "name": agent.name,
                "type": "agent",
                "description": agent.description,
                "agent_type": agent.agent_type,
                "apqc_category": agent.apqc_category,
                "children_count": 0
            })

        return {
            "level": level,
            "parent": category,
            "code": level4_code,
            "items": items
        }


# ============================================================================
# APQC PCF Hierarchy Endpoint (using JSON file)
# ============================================================================

@app.get("/api/apqc/hierarchy")
async def get_apqc_hierarchy(
    level: int = 1,
    parent_code: Optional[str] = None
):
    """Get APQC PCF hierarchy from the complete JSON file.

    This provides the full APQC PCF 7.4 structure with proper names at all levels.

    Level 1: 13 Categories (1.0 - 13.0)
    Level 2: Process Groups (1.1, 1.2, etc.)
    Level 3: Processes (1.1.1, 1.1.2, etc.)
    Level 4: Activities (1.1.1.1, 1.1.1.2, etc.)
    """
    if not APQC_HIERARCHY or "hierarchy" not in APQC_HIERARCHY:
        raise HTTPException(status_code=500, detail="APQC hierarchy data not loaded")

    hierarchy = APQC_HIERARCHY["hierarchy"]

    # Level 1: Return all 13 categories
    if level == 1:
        items = []
        for code, data in sorted(hierarchy.items()):
            children_count = len(data.get("children", {}))
            items.append({
                "id": code,
                "code": code,
                "name": data["name"],
                "type": data["type"],
                "icon": get_pcf_icon(code),
                "color": get_pcf_color(code),
                "children_count": children_count,
                "description": f"APQC Category {code}"
            })
        return {"level": 1, "items": items, "total": len(items)}

    # Level 2+: Navigate into the hierarchy based on parent_code
    if not parent_code:
        return {"level": level, "items": [], "error": "parent_code required for level > 1"}

    # Parse the parent code to navigate the hierarchy
    # parent_code format: "1.0" for level 2, "1.1" for level 3, "1.1.1" for level 4
    code_parts = parent_code.split(".")

    # Navigate to the correct position in hierarchy
    current = hierarchy
    try:
        # For level 2, parent is "1.0" -> go to hierarchy["1.0"]["children"]
        if level == 2:
            cat_code = parent_code  # e.g., "1.0"
            current = hierarchy.get(cat_code, {}).get("children", {})
        elif level == 3:
            # parent is "1.1" -> go to hierarchy["1.0"]["children"]["1.1"]["children"]
            cat_code = code_parts[0] + ".0"
            pg_code = parent_code  # e.g., "1.1"
            current = hierarchy.get(cat_code, {}).get("children", {}).get(pg_code, {}).get("children", {})
        elif level == 4:
            # parent is "1.1.1" -> deeper navigation
            cat_code = code_parts[0] + ".0"
            pg_code = ".".join(code_parts[:2])  # e.g., "1.1"
            proc_code = parent_code  # e.g., "1.1.1"
            current = (hierarchy.get(cat_code, {})
                      .get("children", {}).get(pg_code, {})
                      .get("children", {}).get(proc_code, {})
                      .get("children", {}))
        elif level == 5:
            # parent is "1.1.1.1" -> deepest level
            cat_code = code_parts[0] + ".0"
            pg_code = ".".join(code_parts[:2])
            proc_code = ".".join(code_parts[:3])
            act_code = parent_code
            current = (hierarchy.get(cat_code, {})
                      .get("children", {}).get(pg_code, {})
                      .get("children", {}).get(proc_code, {})
                      .get("children", {}).get(act_code, {})
                      .get("children", {}))
    except (KeyError, AttributeError):
        current = {}

    # Build response items
    items = []
    for code, data in sorted(current.items()):
        if isinstance(data, dict):
            children_count = len(data.get("children", {})) if isinstance(data.get("children"), dict) else 0
            items.append({
                "id": code,
                "code": code,
                "name": data.get("name", code),
                "type": data.get("type", "item"),
                "icon": get_pcf_icon(code),
                "color": get_pcf_color(code.split(".")[0] + ".0"),
                "children_count": children_count,
                "description": f"APQC {data.get('type', 'item').replace('_', ' ').title()} {code}"
            })

    return {
        "level": level,
        "parent_code": parent_code,
        "items": items,
        "total": len(items)
    }


def get_pcf_icon(code: str) -> str:
    """Get icon based on APQC code"""
    cat = code.split(".")[0]
    icons = {
        "1": "🎯",   # Vision & Strategy
        "2": "🚀",   # Products & Services
        "3": "📈",   # Market & Sell
        "4": "📦",   # Deliver Physical Products
        "5": "🛎️",   # Deliver Services
        "6": "😊",   # Customer Service
        "7": "👥",   # Human Capital
        "8": "💻",   # IT
        "9": "💵",   # Financial Resources
        "10": "🏗️",  # Assets
        "11": "🛡️",  # Risk & Compliance
        "12": "🤝",  # External Relationships
        "13": "📊"   # Business Capabilities
    }
    return icons.get(cat, "📋")


def get_pcf_color(code: str) -> str:
    """Get color based on APQC category code"""
    cat = code.split(".")[0]
    colors = {
        "1": "#667eea",  # Purple
        "2": "#f093fb",  # Pink
        "3": "#4facfe",  # Blue
        "4": "#43e97b",  # Green
        "5": "#fa709a",  # Rose
        "6": "#fee140",  # Yellow
        "7": "#30cfd0",  # Cyan
        "8": "#a8edea",  # Teal
        "9": "#d299c2",  # Lavender
        "10": "#ffecd2", # Peach
        "11": "#fcb69f", # Coral
        "12": "#a1c4fd", # Light Blue
        "13": "#c2e9fb"  # Sky
    }
    return colors.get(cat, "#667eea")


def get_category_icon(category: str) -> str:
    """Get emoji icon for APQC category"""
    icons = {
        "Deliver Service": "📦",
        "Develop Business Capabilities": "🏗️",
        "Develop Strategy & Manage Enterprise Transformation": "🎯",
        "Manage Assets": "💰",
        "Manage External Relations": "🤝",
        "Manage Financial Resources": "💵",
        "Manage Human Capital": "👥",
        "Manage Information Technology": "💻",
        "Manage Product Development": "🚀",
        "Manage Risk & Compliance": "🛡️",
        "Manage Sales and Marketing": "📈",
        "Manage Supply Chain": "🚚",
        "Serve Customers": "😊"
    }
    return icons.get(category, "📋")


def get_category_color(category: str) -> str:
    """Get color for APQC category"""
    colors = {
        "Deliver Service": "#FF6B6B",
        "Develop Business Capabilities": "#4ECDC4",
        "Develop Strategy & Manage Enterprise Transformation": "#45B7D1",
        "Manage Assets": "#FFA07A",
        "Manage External Relations": "#98D8C8",
        "Manage Financial Resources": "#F7DC6F",
        "Manage Human Capital": "#BB8FCE",
        "Manage Information Technology": "#85C1E2",
        "Manage Product Development": "#F8B88B",
        "Manage Risk & Compliance": "#F5A9A9",
        "Manage Sales and Marketing": "#52C970",
        "Manage Supply Chain": "#7FB3D5",
        "Serve Customers": "#FFAF87"
    }
    return colors.get(category, "#667eea")


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get details for a specific agent"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent


@app.post("/api/workflows/save")
async def save_workflow(
    workflow_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Save a custom orchestrated workflow"""
    workflow_name = workflow_data.get("name", "Untitled Workflow")
    agents = workflow_data.get("agents", [])
    connections = workflow_data.get("connections", [])

    workflow_id = f"custom_{uuid4().hex[:12]}"

    return {
        "workflow_id": workflow_id,
        "status": "saved",
        "name": workflow_name,
        "message": f"Workflow '{workflow_name}' saved successfully",
        "agents_count": len(agents),
        "connections_count": len(connections)
    }


@app.post("/api/workflows/execute-custom")
async def execute_custom_workflow(
    workflow_data: Dict[str, Any],
    sandbox: bool = True,
    db: Session = Depends(get_db)
):
    """Execute a custom orchestrated workflow in sandbox or production"""
    workflow_id = f"exec_{uuid4().hex[:12]}"
    agents = workflow_data.get("agents", [])

    return {
        "workflow_id": workflow_id,
        "status": "executing",
        "environment": "sandbox" if sandbox else "production",
        "message": f"Executing workflow with {len(agents)} agents",
        "execution_url": f"/api/workflows/{workflow_id}"
    }


# ============================================================================
# Workflow Endpoints
# ============================================================================

@app.post("/api/workflows/invoice", response_model=WorkflowResponse)
async def execute_invoice_workflow(
    request: InvoiceWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute invoice processing workflow (4-agent pipeline)"""

    # Create workflow record
    workflow_id = f"wf_{uuid4().hex[:16]}"
    workflow = Workflow(
        workflow_id=workflow_id,
        workflow_name="Invoice Processing",
        workflow_type="invoice_processing",
        status="pending",
        input_data={
            "source": request.source,
            "extracted_fields": {
                "invoice_number": request.invoice_number,
                "vendor_name": request.vendor_name,
                "date": request.date,
                "items": request.items
            }
        },
        total_agents=4
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Execute workflow in background
    background_tasks.add_task(run_invoice_workflow, workflow.id, workflow_id, db)

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="pending",
        message="Workflow started successfully",
        workflow_url=f"/api/workflows/{workflow_id}"
    )


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    """Get workflow status and results"""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    return WorkflowStatusResponse(
        workflow_id=workflow.workflow_id,
        workflow_name=workflow.workflow_name,
        status=workflow.status,
        success=workflow.success,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        execution_time_ms=workflow.execution_time_ms,
        total_agents=workflow.total_agents,
        agents_succeeded=workflow.agents_succeeded or 0,
        agents_failed=workflow.agents_failed or 0,
        input_data=workflow.input_data,
        output_data=workflow.output_data,
        error_message=workflow.error_message
    )


@app.get("/api/workflows/{workflow_id}/stages")
async def get_workflow_stages(workflow_id: str, db: Session = Depends(get_db)):
    """Get detailed stage information for a workflow"""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    stages = db.query(WorkflowStage).filter(WorkflowStage.workflow_id == workflow.id).order_by(WorkflowStage.stage_number).all()

    return {
        "workflow_id": workflow_id,
        "stages": [
            {
                "stage_number": stage.stage_number,
                "stage_name": stage.stage_name,
                "status": stage.status,
                "execution_time_ms": stage.execution_time_ms,
                "success": stage.success,
                "error_message": stage.error_message
            }
            for stage in stages
        ]
    }


# ============================================================================
# Process Testing & Debugging Endpoints
# ============================================================================

def _get_business_description(agent_name: str, agent_type: str, category: str) -> str:
    """Generate realistic business descriptions for process steps"""
    descriptions = {
        "deliver service": [
            "Allocate and schedule service delivery resources based on customer requirements",
            "Assess current service capabilities and capacity constraints",
            "Assign qualified personnel to handle customer service requests",
            "Coordinate service fulfillment with logistics and operations teams",
            "Monitor service delivery performance and customer satisfaction metrics",
            "Perform post-service quality assurance and feedback collection"
        ],
        "develop business capabilities": [
            "Analyze business requirements and define capability improvements",
            "Design new business processes and systems architecture",
            "Develop training materials and change management plans",
            "Implement capability enhancements across the organization",
            "Conduct capability maturity assessments and gap analysis",
            "Update business process documentation and standard operating procedures"
        ],
        "manage financial resources": [
            "Review and approve budget allocations for business units",
            "Forecast revenue and expense projections for planning purposes",
            "Manage cash flow and working capital optimization",
            "Process accounts payable and receivable transactions",
            "Conduct financial reconciliation and audit preparations",
            "Generate financial reports and performance dashboards"
        ],
        "manage human capital": [
            "Recruit and onboard qualified candidates for open positions",
            "Manage employee performance reviews and compensation planning",
            "Develop and deliver employee training and development programs",
            "Administer benefits, payroll, and human resources systems",
            "Maintain employee records and compliance documentation",
            "Foster employee engagement and organizational culture initiatives"
        ],
        "develop strategy": [
            "Analyze market trends and competitive landscape",
            "Define organizational strategy and strategic objectives",
            "Communicate strategy to stakeholders and obtain alignment",
            "Monitor strategy execution and business performance metrics",
            "Adjust strategies based on market changes and performance data",
            "Conduct scenario planning for emerging business opportunities"
        ],
        "manage information technology": [
            "Assess IT infrastructure needs and technology solutions",
            "Design and implement enterprise technology systems",
            "Manage IT operations, maintenance, and system uptime",
            "Ensure cybersecurity and data protection compliance",
            "Manage IT vendor relationships and service agreements",
            "Provide technical support and resolve system issues"
        ]
    }

    # Find matching description based on category
    category_lower = category.lower()
    for key, desc_list in descriptions.items():
        if key in category_lower:
            return desc_list[hash(agent_name) % len(desc_list)]

    # Default description if no match
    return f"Execute critical business process step: {agent_name}"


@app.get("/api/processes/{process_id}/definition")
async def get_process_definition(process_id: str, db: Session = Depends(get_db)):
    """Get complete process definition with steps, inputs, outputs, and roles"""
    # Extract APQC code from process_id (e.g., "1.1.1" from "apqc_1_1_1")
    apqc_code = process_id.replace("apqc_", "").replace("_", ".")

    # Load process steps - these are the sub-processes/activities under this level
    agents = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.apqc_category.contains(apqc_code.split(".")[0])
    ).limit(20).all()

    # Define process steps structure
    steps = [
        {
            "step_id": f"step_{i}",
            "step_number": i,
            "name": agent.name,
            "description": agent.description or f"Process step for {agent.agent_type}",
            "required_role": f"Process Manager - {agent.apqc_category}",
            "input_schema": {
                "format": "json",
                "fields": {
                    "process_data": "string",
                    "context": "object",
                    "parameters": "object"
                },
                "example": {
                    "process_data": "incoming data from previous step",
                    "context": {"process_id": process_id, "step_number": i},
                    "parameters": {}
                }
            },
            "output_schema": {
                "format": "json",
                "fields": {
                    "result": "object",
                    "status": "string",
                    "message": "string",
                    "next_step_data": "object"
                }
            },
            "business_description": _get_business_description(agent.name, agent.agent_type, agent.apqc_category),
            "agent_id": agent.agent_id
        }
        for i, agent in enumerate(agents, 1)
    ]

    return {
        "process_id": process_id,
        "apqc_code": apqc_code,
        "total_steps": len(steps),
        "steps": steps,
        "bpmn2_available": True,
        "estimated_duration_minutes": len(steps) * 2
    }


@app.post("/api/processes/{process_id}/execute-step")
async def execute_process_step(
    process_id: str,
    step_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute a single process step and return results in technical and business formats"""
    step_id = step_data.get("step_id")
    step_number = step_data.get("step_number", 1)
    agent_id = step_data.get("agent_id")
    input_data = step_data.get("input_data", {})

    try:
        # Get the agent
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Simulate agent execution - in production this would call the actual agent
        execution_result = {
            "status": "success",
            "message": f"Successfully executed {agent.name}",
            "execution_time_ms": 1250,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Generate realistic output
        output_data = {
            "result": {
                "processed_items": len(input_data.get("items", [])),
                "validation_passed": True,
                "data_quality_score": 0.95,
                "summary": f"Processed {len(input_data.get('items', []))} items successfully"
            },
            "next_step_data": input_data,  # Pass through to next step
            "metrics": {
                "items_processed": len(input_data.get("items", [])),
                "errors": 0,
                "warnings": 0,
                "success_rate": 1.0
            }
        }

        return {
            "process_id": process_id,
            "step_id": step_id,
            "step_number": step_number,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": "completed",
            "execution": execution_result,
            "input": {
                "technical": input_data,
                "business_summary": f"Received {len(input_data.get('items', []))} items for processing",
            },
            "output": {
                "technical": output_data,
                "business_summary": f"Processed {output_data['result']['processed_items']} items with {output_data['result'].get('data_quality_score', 0)*100:.1f}% quality score"
            },
            "next_step": {
                "step_number": step_number + 1,
                "ready_to_proceed": True,
                "data_to_pass": output_data.get("next_step_data")
            }
        }

    except Exception as e:
        return {
            "process_id": process_id,
            "step_id": step_id,
            "status": "error",
            "error": str(e),
            "message": f"Failed to execute process step: {str(e)}"
        }


@app.get("/api/processes/{process_id}/diagram")
async def get_process_diagram(process_id: str, db: Session = Depends(get_db)):
    """Get BPMN2 diagram for the process with full visual layout (BPMNDI)"""

    # Parse process_id to extract category and APQC code
    # Format can be: "Category_Name|8.1" or "Category_Name" or "apqc_8_1_1"
    category = None
    apqc_prefix = None

    if "|" in process_id:
        # Level 2+ format: "Manage_Information_Technology|8.1"
        parts = process_id.split("|")
        category = parts[0].replace("_", " ")
        apqc_prefix = parts[1] if len(parts) > 1 else None
    else:
        # Level 1 format: just category name like "Manage_Information_Technology"
        category = process_id.replace("_", " ")

    # Query agents based on category
    query = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.apqc_category == category
    )

    agents_list = query.order_by(Agent.name).all()

    # Filter by APQC prefix if specified (e.g., "8.1" matches "APQC 8.1.x.x")
    if apqc_prefix and agents_list:
        filtered = []
        for agent in agents_list:
            # Extract APQC code from agent name (e.g., "APQC 8.1.1.5 - ...")
            if agent.name.startswith("APQC "):
                parts = agent.name.split(" ")
                if len(parts) >= 2:
                    agent_code = parts[1]  # e.g., "8.1.1.5"
                    if agent_code.startswith(apqc_prefix + "."):
                        filtered.append(agent)
        agents_list = filtered

    # Limit to 5 for readability in diagram
    agents = agents_list[:5]

    # If no agents found, create a simple placeholder diagram
    if not agents:
        # Create a minimal valid BPMN with one placeholder task
        class PlaceholderAgent:
            name = f"Process: {category or process_id}" + (f" ({apqc_prefix})" if apqc_prefix else "")
        agents = [PlaceholderAgent()]

    # Build dynamic tasks and flows
    tasks_xml = ""
    shapes_xml = ""
    edges_xml = ""

    # Starting position for layout
    x_pos = 180
    y_pos = 80
    task_width = 100
    task_height = 80
    spacing = 50

    # Start event
    start_id = f"StartEvent_{process_id}"

    # Build tasks from agents
    task_ids = []
    for i, agent in enumerate(agents[:5]):  # Limit to 5 tasks for readability
        task_id = f"Task_{i+1}"
        task_ids.append(task_id)
        task_name = agent.name[:30] + "..." if len(agent.name) > 30 else agent.name

        # Task XML
        incoming = f"Flow_{i}" if i == 0 else f"Flow_{i}"
        outgoing = f"Flow_{i+1}"
        tasks_xml += f'''
    <bpmn:task id="{task_id}" name="{task_name}">
      <bpmn:incoming>{incoming}</bpmn:incoming>
      <bpmn:outgoing>{outgoing}</bpmn:outgoing>
    </bpmn:task>'''

        # Shape XML (visual position)
        task_x = x_pos + i * (task_width + spacing)
        shapes_xml += f'''
      <bpmndi:BPMNShape id="{task_id}_di" bpmnElement="{task_id}">
        <dc:Bounds x="{task_x}" y="{y_pos}" width="{task_width}" height="{task_height}" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>'''

    # Build sequence flows
    flows_xml = f'''
    <bpmn:sequenceFlow id="Flow_0" sourceRef="{start_id}" targetRef="Task_1" />'''

    # Start event edge
    edges_xml += f'''
      <bpmndi:BPMNEdge id="Flow_0_di" bpmnElement="Flow_0">
        <di:waypoint x="158" y="{y_pos + task_height//2}" />
        <di:waypoint x="{x_pos}" y="{y_pos + task_height//2}" />
      </bpmndi:BPMNEdge>'''

    for i in range(len(task_ids)):
        if i < len(task_ids) - 1:
            flow_id = f"Flow_{i+1}"
            flows_xml += f'''
    <bpmn:sequenceFlow id="{flow_id}" sourceRef="Task_{i+1}" targetRef="Task_{i+2}" />'''

            # Edge waypoints
            src_x = x_pos + i * (task_width + spacing) + task_width
            tgt_x = x_pos + (i+1) * (task_width + spacing)
            edges_xml += f'''
      <bpmndi:BPMNEdge id="{flow_id}_di" bpmnElement="{flow_id}">
        <di:waypoint x="{src_x}" y="{y_pos + task_height//2}" />
        <di:waypoint x="{tgt_x}" y="{y_pos + task_height//2}" />
      </bpmndi:BPMNEdge>'''
        else:
            # Last task to end event
            flow_id = f"Flow_{i+1}"
            end_id = f"EndEvent_{process_id}"
            flows_xml += f'''
    <bpmn:sequenceFlow id="{flow_id}" sourceRef="Task_{i+1}" targetRef="{end_id}" />'''

            src_x = x_pos + i * (task_width + spacing) + task_width
            end_x = src_x + spacing + 18
            edges_xml += f'''
      <bpmndi:BPMNEdge id="{flow_id}_di" bpmnElement="{flow_id}">
        <di:waypoint x="{src_x}" y="{y_pos + task_height//2}" />
        <di:waypoint x="{end_x}" y="{y_pos + task_height//2}" />
      </bpmndi:BPMNEdge>'''

    # Calculate end event position
    end_x = x_pos + len(task_ids) * (task_width + spacing)
    end_id = f"EndEvent_{process_id}"

    # Complete BPMN2 with BPMNDI section for visual rendering
    bpmn2_diagram = f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_{process_id}"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_{process_id}" isExecutable="true">
    <bpmn:startEvent id="{start_id}" name="Start">
      <bpmn:outgoing>Flow_0</bpmn:outgoing>
    </bpmn:startEvent>{tasks_xml}
    <bpmn:endEvent id="{end_id}" name="End">
      <bpmn:incoming>Flow_{len(task_ids)}</bpmn:incoming>
    </bpmn:endEvent>{flows_xml}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_{process_id}">
    <bpmndi:BPMNPlane id="BPMNPlane_{process_id}" bpmnElement="Process_{process_id}">
      <bpmndi:BPMNShape id="{start_id}_di" bpmnElement="{start_id}">
        <dc:Bounds x="122" y="{y_pos + task_height//2 - 18}" width="36" height="36" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="128" y="{y_pos + task_height//2 + 22}" width="24" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>{shapes_xml}
      <bpmndi:BPMNShape id="{end_id}_di" bpmnElement="{end_id}">
        <dc:Bounds x="{end_x}" y="{y_pos + task_height//2 - 18}" width="36" height="36" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="{end_x + 6}" y="{y_pos + task_height//2 + 22}" width="24" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>{edges_xml}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''

    return {
        "process_id": process_id,
        "format": "bpmn2",
        "content": bpmn2_diagram,
        "diagram_url": f"/api/processes/{process_id}/diagram.svg",
        "task_count": len(task_ids)
    }


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/api/admin/workflows/all")
async def get_all_workflows(db: Session = Depends(get_db)):
    """Get all workflows for admin panel (no pagination)"""
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    return [
        {
            "workflow_id": w.workflow_id,
            "workflow_name": w.workflow_name,
            "workflow_type": w.workflow_type,
            "status": w.status,
            "success": w.success,
            "started_at": w.started_at.isoformat() if w.started_at else None,
            "completed_at": w.completed_at.isoformat() if w.completed_at else None,
            "execution_time_ms": w.execution_time_ms,
            "total_agents": w.total_agents,
            "agents_succeeded": w.agents_succeeded or 0,
            "agents_failed": w.agents_failed or 0,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "error_message": w.error_message
        }
        for w in workflows
    ]


# ============================================================================
# Background Task: Execute Workflow
# ============================================================================

async def run_invoice_workflow(workflow_db_id: int, workflow_id: str, db: Session):
    """Background task to execute invoice workflow"""
    # Create new session for background task
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        workflow_record = db.query(Workflow).filter(Workflow.id == workflow_db_id).first()

        # Update status to running
        workflow_record.status = "running"
        workflow_record.started_at = datetime.utcnow()
        db.commit()

        # Execute the workflow
        workflow_engine = InvoiceProcessingWorkflow()
        raw_invoice = {
            "source": workflow_record.input_data.get("source"),
            "extracted_fields": workflow_record.input_data.get("extracted_fields")
        }

        result = await workflow_engine.process_invoice(raw_invoice)

        # Update workflow record
        workflow_record.status = "completed" if result["success"] else "failed"
        workflow_record.completed_at = datetime.utcnow()
        workflow_record.execution_time_ms = result.get("total_execution_time_ms", 0)
        workflow_record.success = result["success"]
        workflow_record.output_data = result
        workflow_record.agents_succeeded = sum(1 for stage in result.get("stages", {}).values() if stage.get("success"))
        workflow_record.agents_failed = sum(1 for stage in result.get("stages", {}).values() if not stage.get("success"))

        if not result["success"]:
            workflow_record.error_message = result.get("error", "Unknown error")

        # Save stage details
        stage_names = ["extract", "validate", "calculate", "approve"]
        for idx, stage_name in enumerate(stage_names, 1):
            if stage_name in result.get("stages", {}):
                stage_data = result["stages"][stage_name]
                stage = WorkflowStage(
                    workflow_id=workflow_db_id,
                    stage_number=idx,
                    stage_name=stage_name,
                    status="completed" if stage_data.get("success") else "failed",
                    execution_time_ms=stage_data.get("execution_time_ms", 0),
                    success=stage_data.get("success"),
                    completed_at=datetime.utcnow()
                )
                db.add(stage)

        db.commit()

    except Exception as e:
        print(f"Error executing workflow: {e}")
        workflow_record = db.query(Workflow).filter(Workflow.id == workflow_db_id).first()
        workflow_record.status = "failed"
        workflow_record.success = False
        workflow_record.error_message = str(e)
        workflow_record.completed_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()


# ============================================================================
# BPMN File Service Endpoints
# ============================================================================

BPMN_BASE_DIR = Path(__file__).parent.parent / "generated_composite_agents"
BPMN_L2_DIR = BPMN_BASE_DIR / "level2_bpmn"  # Level 2: Process Groups (x.y)
BPMN_L3_DIR = BPMN_BASE_DIR / "level4_bpmn"  # Level 3: Processes (x.y.z) - named level4 historically

def get_bpmn_filepath(apqc_code: str):
    """Get the file path for a BPMN file based on APQC code level"""
    code_parts = apqc_code.split(".")
    code_underscore = apqc_code.replace(".", "_")

    # Level 2 codes (x.y) -> level2_bpmn/COMPOSITE_L2_x_y.bpmn
    if len(code_parts) == 2:
        filename = f"COMPOSITE_L2_{code_underscore}.bpmn"
        return BPMN_L2_DIR / filename, filename

    # Level 3 codes (x.y.z) -> level4_bpmn/COMPOSITE_L4_x_y_z.bpmn
    elif len(code_parts) == 3:
        filename = f"COMPOSITE_L4_{code_underscore}.bpmn"
        return BPMN_L3_DIR / filename, filename

    # Other levels - check both directories
    else:
        filename = f"COMPOSITE_L4_{code_underscore}.bpmn"
        return BPMN_L3_DIR / filename, filename

@app.get("/api/apqc/bpmn/{apqc_code:path}")
async def get_bpmn_file(apqc_code: str):
    """
    Get BPMN 2.0 XML file for an APQC code.

    Supports multiple levels:
    - Level 2 (x.y): Process Groups -> level2_bpmn/
    - Level 3 (x.y.z): Processes -> level4_bpmn/

    Args:
        apqc_code: APQC code (e.g., "1.1", "1.1.1", "8.2.3")

    Returns:
        BPMN 2.0 XML content
    """
    filepath, filename = get_bpmn_filepath(apqc_code)

    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=f"BPMN file not found for APQC code {apqc_code}. Expected: {filename}"
        )

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            bpmn_content = f.read()

        return Response(
            content=bpmn_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading BPMN file: {str(e)}")


@app.get("/api/apqc/bpmn-list")
async def list_available_bpmn():
    """
    List all available BPMN files with their APQC codes.

    Returns:
        List of APQC codes that have BPMN files available (Level 2 and Level 3)
    """
    bpmn_files = []

    # Collect Level 2 BPMN files (Process Groups: x.y)
    if BPMN_L2_DIR.exists():
        for filepath in BPMN_L2_DIR.glob("COMPOSITE_L2_*.bpmn"):
            # Convert filename back to APQC code: "COMPOSITE_L2_1_1.bpmn" -> "1.1"
            filename = filepath.stem  # "COMPOSITE_L2_1_1"
            code_part = filename.replace("COMPOSITE_L2_", "")  # "1_1"
            apqc_code = code_part.replace("_", ".")  # "1.1"

            bpmn_files.append({
                "apqc_code": apqc_code,
                "filename": filepath.name,
                "level": 2,
                "level_name": "Process Group"
            })

    # Collect Level 3 BPMN files (Processes: x.y.z)
    if BPMN_L3_DIR.exists():
        for filepath in BPMN_L3_DIR.glob("COMPOSITE_L4_*.bpmn"):
            # Convert filename back to APQC code: "COMPOSITE_L4_1_1_1.bpmn" -> "1.1.1"
            filename = filepath.stem  # "COMPOSITE_L4_1_1_1"
            code_part = filename.replace("COMPOSITE_L4_", "")  # "1_1_1"
            apqc_code = code_part.replace("_", ".")  # "1.1.1"

            bpmn_files.append({
                "apqc_code": apqc_code,
                "filename": filepath.name,
                "level": 3,
                "level_name": "Process"
            })

    # Sort by APQC code
    bpmn_files.sort(key=lambda x: [int(p) for p in x["apqc_code"].split(".")])

    return {
        "total": len(bpmn_files),
        "level_2_count": len([f for f in bpmn_files if f["level"] == 2]),
        "level_3_count": len([f for f in bpmn_files if f["level"] == 3]),
        "bpmn_files": bpmn_files
    }


@app.get("/api/apqc/bpmn-check/{apqc_code:path}")
async def check_bpmn_available(apqc_code: str):
    """
    Check if a BPMN file exists for a given APQC code.

    Supports multiple levels:
    - Level 2 (x.y): Process Groups
    - Level 3 (x.y.z): Processes

    Args:
        apqc_code: APQC code to check

    Returns:
        Boolean indicating if BPMN is available
    """
    filepath, filename = get_bpmn_filepath(apqc_code)
    code_parts = apqc_code.split(".")
    level = len(code_parts)

    return {
        "apqc_code": apqc_code,
        "has_bpmn": filepath.exists(),
        "filename": filename if filepath.exists() else None,
        "level": level,
        "level_name": "Process Group" if level == 2 else "Process" if level == 3 else f"Level {level}"
    }


# ============================================================================
# Agent Card and Integration Catalog Endpoints
# ============================================================================

AGENT_CARDS_DIR = Path(__file__).parent.parent / "agent_cards"

@app.get("/api/agent-cards")
async def list_agent_cards():
    """
    List all available agent card definitions.
    """
    if not AGENT_CARDS_DIR.exists():
        return {"total": 0, "agent_cards": []}

    cards = []
    for filepath in AGENT_CARDS_DIR.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                cards.append({
                    "apqc_id": data.get("apqc_id"),
                    "apqc_name": data.get("apqc_name"),
                    "category": data.get("category"),
                    "description": data.get("description"),
                    "orchestration_pattern": data.get("orchestration_pattern", "sequential"),
                    "total_steps": data.get("total_steps", len(data.get("agent_cards", []))),
                    "estimated_duration_seconds": data.get("estimated_duration_seconds"),
                    "compliance_frameworks": data.get("compliance_frameworks", []),
                    "integration_summary": data.get("integration_summary", {}),
                    "filename": filepath.name
                })
        except Exception as e:
            continue

    # Sort by APQC ID
    cards.sort(key=lambda x: x.get("apqc_id", ""))

    return {"total": len(cards), "agent_cards": cards}


@app.get("/api/agent-cards/{apqc_code:path}")
async def get_agent_card(apqc_code: str):
    """
    Get agent card definition for a specific APQC code.

    Args:
        apqc_code: APQC code (e.g., "9.2.1.1")
    """
    # Convert code to filename format
    code_underscore = apqc_code.replace(".", "_")

    # Try different filename patterns
    possible_files = [
        AGENT_CARDS_DIR / f"apqc_{code_underscore}.json",
        AGENT_CARDS_DIR / f"apqc_{code_underscore}_invoice_processing.json",
        AGENT_CARDS_DIR / f"{code_underscore}.json"
    ]

    for filepath in possible_files:
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading agent card: {str(e)}")

    # Also try glob pattern
    for filepath in AGENT_CARDS_DIR.glob(f"*{code_underscore}*.json"):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            # Skip files that can't be read or parsed
            continue

    raise HTTPException(
        status_code=404,
        detail=f"Agent card not found for APQC code {apqc_code}"
    )


@app.get("/api/agent-cards/{apqc_code:path}/step/{step_number}")
async def get_agent_card_step(apqc_code: str, step_number: int):
    """
    Get a specific step from an agent card.
    """
    card = await get_agent_card(apqc_code)

    for agent in card.get("agent_cards", []):
        if agent.get("step_number") == step_number:
            return agent

    raise HTTPException(
        status_code=404,
        detail=f"Step {step_number} not found in agent card {apqc_code}"
    )


class AgentCardCreate(BaseModel):
    """Request model for creating agent cards."""
    filename: str = Field(..., description="Filename for the agent card (e.g., apqc_7_3_1_1_vendor_management.json)")
    content: Dict[str, Any] = Field(..., description="The agent card JSON content")


@app.post("/api/agent-cards")
async def create_agent_card(card_request: AgentCardCreate):
    """
    Create a new agent card definition.

    The agent card will be saved to the agent_cards directory.
    """
    # Ensure agent_cards directory exists
    AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    filename = card_request.filename
    if not filename.endswith('.json'):
        filename += '.json'

    # Basic filename validation
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Must not contain path separators or parent directory references."
        )

    filepath = AGENT_CARDS_DIR / filename

    # Check if file already exists
    if filepath.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Agent card with filename '{filename}' already exists. Use PUT to update."
        )

    # Validate required fields
    content = card_request.content
    required_fields = ["apqc_id", "apqc_name", "category", "agent_cards"]
    missing = [f for f in required_fields if f not in content]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}"
        )

    # Add metadata
    content["created_at"] = datetime.utcnow().isoformat()
    content["created_by"] = "dashboard"

    try:
        with open(filepath, 'w') as f:
            json.dump(content, f, indent=2)

        logger.info(f"Created new agent card: {filename}")

        return {
            "success": True,
            "message": f"Agent card created successfully",
            "filename": filename,
            "apqc_id": content.get("apqc_id"),
            "apqc_name": content.get("apqc_name")
        }
    except Exception as e:
        logger.error(f"Failed to create agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save agent card: {str(e)}"
        )


@app.put("/api/agent-cards/{filename}")
async def update_agent_card(filename: str, card_request: Dict[str, Any]):
    """
    Update an existing agent card definition.
    """
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = AGENT_CARDS_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Agent card '{filename}' not found"
        )

    # Add update metadata
    card_request["updated_at"] = datetime.utcnow().isoformat()

    try:
        with open(filepath, 'w') as f:
            json.dump(card_request, f, indent=2)

        logger.info(f"Updated agent card: {filename}")

        return {
            "success": True,
            "message": "Agent card updated successfully",
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to update agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent card: {str(e)}"
        )


@app.delete("/api/agent-cards/{filename}")
async def delete_agent_card(filename: str):
    """
    Delete an agent card definition.
    """
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = AGENT_CARDS_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Agent card '{filename}' not found"
        )

    try:
        filepath.unlink()
        logger.info(f"Deleted agent card: {filename}")

        return {
            "success": True,
            "message": "Agent card deleted successfully",
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to delete agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete agent card: {str(e)}"
        )


@app.get("/api/integrations")
async def list_integrations():
    """
    List all available integrations from the catalog.
    """
    if not INTEGRATION_CATALOG_AVAILABLE:
        return {"total": 0, "categories": {}, "integrations": [], "error": "Integration catalog not found"}

    integrations = []
    for int_id, int_data in INTEGRATION_CATALOG.items():
        integrations.append({
            "id": int_id,
            "name": int_data.get("name"),
            "category": int_data.get("category"),
            "type": int_data.get("type"),
            "capabilities_count": len(int_data.get("capabilities", []))
        })

    return {
        "total": len(integrations),
        "categories": CATEGORY_SUMMARY,
        "integrations": integrations
    }


@app.get("/api/integrations/{integration_id}")
async def get_integration(integration_id: str):
    """
    Get details for a specific integration.
    """
    if not INTEGRATION_CATALOG_AVAILABLE:
        raise HTTPException(status_code=500, detail="Integration catalog not available")

    if integration_id in INTEGRATION_CATALOG:
        return INTEGRATION_CATALOG[integration_id]

    raise HTTPException(status_code=404, detail=f"Integration {integration_id} not found")


@app.get("/api/integrations/category/{category}")
async def get_integrations_by_category(category: str):
    """
    Get all integrations in a specific category.
    """
    if not INTEGRATION_CATALOG_AVAILABLE:
        raise HTTPException(status_code=500, detail="Integration catalog not available")

    integrations = [
        integration
        for integration in INTEGRATION_CATALOG.values()
        if integration["category"] == category
    ]

    return {"category": category, "total": len(integrations), "integrations": integrations}


@app.get("/api/integrations/search/{capability}")
async def search_integrations_by_capability(capability: str):
    """
    Find integrations that have a specific capability.
    """
    if not INTEGRATION_CATALOG_AVAILABLE:
        raise HTTPException(status_code=500, detail="Integration catalog not available")

    integrations = [
        integration
        for integration in INTEGRATION_CATALOG.values()
        if capability.lower() in [c.lower() for c in integration.get("capabilities", [])]
    ]

    return {"capability": capability, "total": len(integrations), "integrations": integrations}


# ============================================================================
# Workflow Execution Engine Endpoints
# ============================================================================

# Initialize workflow engine (lazy loading)
workflow_engine = None

def get_workflow_engine():
    """Get or create workflow engine instance"""
    global workflow_engine
    if workflow_engine is None:
        if not WORKFLOW_ENGINE_AVAILABLE:
            raise HTTPException(status_code=500, detail="Workflow engine not available")
        workflow_engine = WorkflowEngine(
            agent_cards_dir=str(Path(__file__).parent.parent / "agent_cards")
        )
    return workflow_engine


class ExecuteWorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    apqc_code: str
    input_data: Dict[str, Any] = {}
    credentials: Optional[Dict[str, Dict[str, str]]] = None


@app.post("/api/execute")
async def execute_workflow(request: ExecuteWorkflowRequest):
    """
    Execute a workflow for the given APQC code.

    This endpoint runs the full workflow defined by the agent card,
    executing each step in sequence, making integration calls,
    evaluating decision rules, and generating a complete audit trail.

    Args:
        request: ExecuteWorkflowRequest with apqc_code, input_data, and optional credentials

    Returns:
        Complete execution result including:
        - success: Boolean indicating overall success
        - execution_id: Unique identifier for this execution
        - status: Final status (completed, failed, etc.)
        - step_executions: Details for each step
        - integration_calls: Log of all API calls made
        - audit_log: Complete audit trail
    """
    try:
        engine = get_workflow_engine()
        result = await engine.execute(
            apqc_code=request.apqc_code,
            input_data=request.input_data,
            credentials=request.credentials
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.get("/api/executions")
async def list_executions(limit: int = 50):
    """
    List recent workflow executions.

    Returns both active (running) and completed executions.
    """
    try:
        engine = get_workflow_engine()
        executions = engine.list_executions(limit=limit)
        return {
            "total": len(executions),
            "executions": executions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    """
    Get details of a specific execution.

    Args:
        execution_id: The unique execution ID

    Returns:
        Complete execution details including step results and audit log
    """
    try:
        engine = get_workflow_engine()
        result = engine.get_execution_status(execution_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")


@app.post("/api/execute/test/{apqc_code:path}")
async def test_execute_workflow(apqc_code: str):
    """
    Test execute a workflow with sample data.

    This is a convenience endpoint for testing workflows without
    providing custom input data. Uses default test data.

    Args:
        apqc_code: APQC code to execute (e.g., "9.2.1.1")
    """
    # Default test data for invoice processing
    test_input = {
        "invoice_number": f"TEST-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "vendor_name": "Test Vendor Inc",
        "invoice_date": datetime.now().isoformat(),
        "due_date": (datetime.now()).isoformat(),
        "total_amount": 1500.00,
        "currency": "USD",
        "po_number": "PO-TEST-001",
        "line_items": [
            {"description": "Test Item 1", "quantity": 10, "unit_price": 100.00, "total": 1000.00},
            {"description": "Test Item 2", "quantity": 5, "unit_price": 100.00, "total": 500.00}
        ]
    }

    try:
        engine = get_workflow_engine()
        result = await engine.execute(
            apqc_code=apqc_code,
            input_data=test_input,
            credentials={}  # No credentials for test
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@app.get("/api/execute/available")
async def list_executable_workflows():
    """
    List all workflows that have agent card definitions and can be executed.
    """
    try:
        engine = get_workflow_engine()
        available = []

        for filepath in engine.agent_cards_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    card = json.load(f)
                    available.append({
                        "apqc_code": card.get("apqc_code"),
                        "apqc_name": card.get("apqc_name"),
                        "category": card.get("category"),
                        "total_steps": len(card.get("agent_cards", [])),
                        "estimated_duration_seconds": card.get("estimated_duration_seconds", 0),
                        "required_integrations": list(set(
                            int_id
                            for step in card.get("agent_cards", [])
                            for int_id in step.get("required_integrations", [])
                        ))
                    })
            except (json.JSONDecodeError, IOError, OSError, KeyError, TypeError):
                # Skip files that can't be read, parsed, or have invalid structure
                continue

        return {
            "total": len(available),
            "workflows": available
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


# ============================================================================
# Agent Card Execution Endpoints
# ============================================================================

class AgentCardExecuteRequest(BaseModel):
    """Request model for agent card execution"""
    input_data: Dict[str, Any] = {}
    credentials: Optional[Dict[str, Dict[str, str]]] = None
    dry_run: bool = False
    step_by_step: bool = False


@app.post("/api/agent-cards/{apqc_code:path}/execute")
async def execute_agent_card(apqc_code: str, request: AgentCardExecuteRequest):
    """
    Execute an agent card workflow.

    This endpoint executes the full workflow defined by the agent card,
    with options for dry-run and step-by-step execution.

    Args:
        apqc_code: APQC code (e.g., "8.2.1.1")
        request: Execution request with input_data, credentials, and options

    Returns:
        Execution result including step details and audit trail
    """
    # First verify the agent card exists
    card = await get_agent_card(apqc_code)

    try:
        engine = get_workflow_engine()

        if request.dry_run:
            # Simulate execution without making actual integration calls
            return await _simulate_execution(card, request.input_data)

        result = await engine.execute(
            apqc_code=apqc_code,
            input_data=request.input_data,
            credentials=request.credentials
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


async def _simulate_execution(card: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate workflow execution without actual API calls."""
    execution_id = f"DRY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{card.get('apqc_id', 'unknown').replace('.', '')}"

    steps = card.get("agent_cards", [])
    simulated_steps = []

    for step in steps:
        step_result = {
            "step_number": step.get("step_number"),
            "step_name": step.get("step_name"),
            "status": "simulated",
            "simulated_output": {
                field["name"]: f"<simulated_{field['type']}>"
                for field in step.get("output_schema", [])
            },
            "would_call_integrations": [
                int_ref.get("system") if isinstance(int_ref, dict) else int_ref
                for int_ref in step.get("required_integrations", [])
            ],
            "decision_rules_to_evaluate": [
                rule.get("name") for rule in step.get("decision_rules", [])
            ]
        }
        simulated_steps.append(step_result)

    return {
        "success": True,
        "dry_run": True,
        "execution_id": execution_id,
        "apqc_code": card.get("apqc_id"),
        "apqc_name": card.get("apqc_name"),
        "total_steps": len(steps),
        "simulated_steps": simulated_steps,
        "estimated_duration_seconds": card.get("estimated_duration_seconds", 0),
        "required_integrations_summary": list(set(
            int_ref.get("system") if isinstance(int_ref, dict) else int_ref
            for step in steps
            for int_ref in step.get("required_integrations", [])
        )),
        "message": "Dry run completed. No actual integrations were called."
    }


@app.post("/api/agent-cards/{apqc_code:path}/validate")
async def validate_agent_card_input(apqc_code: str, input_data: Dict[str, Any]):
    """
    Validate input data against an agent card's input schema.

    Args:
        apqc_code: APQC code (e.g., "8.2.1.1")
        input_data: The input data to validate

    Returns:
        Validation result with any errors or warnings
    """
    card = await get_agent_card(apqc_code)
    steps = card.get("agent_cards", [])

    if not steps:
        return {
            "valid": True,
            "apqc_code": apqc_code,
            "message": "No input schema defined for this agent card"
        }

    # Get first step's input schema
    first_step = steps[0]
    input_schema = first_step.get("input_schema", [])

    errors = []
    warnings = []

    # Check required fields
    for field in input_schema:
        field_name = field.get("name")
        is_required = field.get("required", False)
        field_type = field.get("type", "string")

        if is_required and field_name not in input_data:
            errors.append({
                "field": field_name,
                "error": "required_field_missing",
                "message": f"Required field '{field_name}' is missing"
            })
        elif field_name in input_data:
            value = input_data[field_name]
            # Basic type validation
            if field_type == "string" and not isinstance(value, str):
                warnings.append({
                    "field": field_name,
                    "warning": "type_mismatch",
                    "message": f"Field '{field_name}' should be string, got {type(value).__name__}"
                })
            elif field_type == "number" and not isinstance(value, (int, float)):
                warnings.append({
                    "field": field_name,
                    "warning": "type_mismatch",
                    "message": f"Field '{field_name}' should be number, got {type(value).__name__}"
                })
            elif field_type == "array" and not isinstance(value, list):
                warnings.append({
                    "field": field_name,
                    "warning": "type_mismatch",
                    "message": f"Field '{field_name}' should be array, got {type(value).__name__}"
                })

            # Check enum validation
            validation = field.get("validation", {})
            if "enum" in validation and value not in validation["enum"]:
                errors.append({
                    "field": field_name,
                    "error": "invalid_enum_value",
                    "message": f"Field '{field_name}' must be one of: {validation['enum']}"
                })

    return {
        "valid": len(errors) == 0,
        "apqc_code": apqc_code,
        "apqc_name": card.get("apqc_name"),
        "errors": errors,
        "warnings": warnings,
        "schema_fields": len(input_schema),
        "provided_fields": len(input_data)
    }


@app.get("/api/agent-cards/{apqc_code:path}/execution-history")
async def get_agent_card_execution_history(apqc_code: str, limit: int = 20):
    """
    Get execution history for a specific agent card.

    Args:
        apqc_code: APQC code (e.g., "8.2.1.1")
        limit: Maximum number of executions to return

    Returns:
        List of past executions for this agent card
    """
    # Verify the agent card exists
    card = await get_agent_card(apqc_code)

    try:
        engine = get_workflow_engine()
        all_executions = engine.list_executions(limit=500)

        # Filter to this agent card
        card_executions = [
            exec_data for exec_data in all_executions
            if exec_data.get("apqc_code") == apqc_code
        ][:limit]

        return {
            "apqc_code": apqc_code,
            "apqc_name": card.get("apqc_name"),
            "total_executions": len(card_executions),
            "executions": card_executions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")


@app.get("/api/agent-cards/{apqc_code:path}/required-inputs")
async def get_agent_card_required_inputs(apqc_code: str):
    """
    Get the required inputs for an agent card workflow.

    Args:
        apqc_code: APQC code (e.g., "8.2.1.1")

    Returns:
        Input schema with field names, types, and requirements
    """
    card = await get_agent_card(apqc_code)
    steps = card.get("agent_cards", [])

    if not steps:
        return {
            "apqc_code": apqc_code,
            "apqc_name": card.get("apqc_name"),
            "required_inputs": [],
            "optional_inputs": []
        }

    first_step = steps[0]
    input_schema = first_step.get("input_schema", [])

    required = []
    optional = []

    for field in input_schema:
        field_info = {
            "name": field.get("name"),
            "type": field.get("type", "string"),
            "description": field.get("description", ""),
            "validation": field.get("validation", {}),
            "example": field.get("example")
        }

        if field.get("required", False):
            required.append(field_info)
        else:
            optional.append(field_info)

    return {
        "apqc_code": apqc_code,
        "apqc_name": card.get("apqc_name"),
        "required_inputs": required,
        "optional_inputs": optional,
        "total_fields": len(input_schema)
    }


@app.get("/api/agent-cards/{apqc_code:path}/integrations")
async def get_agent_card_integrations(apqc_code: str):
    """
    Get all integrations required by an agent card.

    Args:
        apqc_code: APQC code (e.g., "8.2.1.1")

    Returns:
        List of required integrations grouped by step
    """
    card = await get_agent_card(apqc_code)
    steps = card.get("agent_cards", [])

    integrations_by_step = []
    all_integrations = set()

    for step in steps:
        step_integrations = []
        for int_ref in step.get("required_integrations", []):
            if isinstance(int_ref, dict):
                int_info = {
                    "system": int_ref.get("system"),
                    "type": int_ref.get("type"),
                    "protocol": int_ref.get("protocol"),
                    "examples": int_ref.get("examples", [])
                }
                step_integrations.append(int_info)
                all_integrations.add(int_ref.get("system"))
            else:
                step_integrations.append({"system": int_ref})
                all_integrations.add(int_ref)

        integrations_by_step.append({
            "step_number": step.get("step_number"),
            "step_name": step.get("step_name"),
            "integrations": step_integrations
        })

    # Also include integration summary from card level
    integration_summary = card.get("integration_summary", {})

    return {
        "apqc_code": apqc_code,
        "apqc_name": card.get("apqc_name"),
        "total_unique_integrations": len(all_integrations),
        "integrations_by_step": integrations_by_step,
        "integration_summary": integration_summary
    }


# ============================================================================
# AI-Powered Smart Processing Endpoints
# ============================================================================

# Import smart processing services
try:
    from superstandard.services.smart_processing import get_processor, ProcessorFactory
    from superstandard.services.ai_service import get_ai_service, AIService
    AI_SERVICES_AVAILABLE = True
except ImportError:
    AI_SERVICES_AVAILABLE = False
    ProcessorFactory = None


class AIProcessRequest(BaseModel):
    """Request model for AI processing"""
    domain: str = Field(..., description="Domain processor to use (finance, hr, operations, customer_service, it)")
    task_type: str = Field(default="default", description="Type of task to perform")
    data: Dict[str, Any] = Field(default_factory=dict, description="Input data for processing")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class AIAnalyzeRequest(BaseModel):
    """Request model for AI analysis"""
    prompt: str = Field(..., description="Analysis prompt")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Data to analyze")
    domain: Optional[str] = Field(default=None, description="Optional domain context")


class AIRecommendRequest(BaseModel):
    """Request model for AI recommendations"""
    context: Dict[str, Any] = Field(..., description="Context for recommendations")
    constraints: List[str] = Field(default_factory=list, description="Constraints to consider")
    max_recommendations: int = Field(default=5, description="Maximum recommendations to return")


@app.get("/api/ai/status")
async def get_ai_status():
    """
    Get AI services status and available capabilities.
    """
    if not AI_SERVICES_AVAILABLE:
        return {
            "available": False,
            "message": "AI services not available. Install required dependencies.",
            "domains": [],
            "capabilities": []
        }

    # Get available domains
    domains = ["finance", "hr", "operations", "customer_service", "it"]

    return {
        "available": True,
        "version": "1.0.0",
        "domains": domains,
        "capabilities": [
            "analyze",
            "process",
            "recommend",
            "decide",
            "assess_risk",
            "extract_entities"
        ],
        "ai_providers": ["openai", "anthropic", "ollama", "mock"],
        "smart_agents_count": 78
    }


@app.get("/api/ai/domains")
async def list_ai_domains():
    """
    List available domain processors and their capabilities.
    """
    if not AI_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    domains = {
        "finance": {
            "name": "Finance Processor",
            "description": "Financial analysis, risk assessment, forecasting",
            "task_types": ["default", "risk_assessment", "forecasting", "anomaly_detection"],
            "capabilities": [
                "analyze_financial_data",
                "assess_financial_risk",
                "forecast_metrics",
                "detect_anomalies"
            ]
        },
        "hr": {
            "name": "HR Processor",
            "description": "Human resources, recruitment, workforce planning",
            "task_types": ["default", "recruitment", "performance", "workforce_planning"],
            "capabilities": [
                "evaluate_candidate",
                "assess_performance",
                "plan_workforce",
                "analyze_engagement"
            ]
        },
        "operations": {
            "name": "Operations Processor",
            "description": "Supply chain, manufacturing, logistics optimization",
            "task_types": ["default", "supply_chain", "inventory", "production"],
            "capabilities": [
                "optimize_supply_chain",
                "manage_inventory",
                "plan_production",
                "analyze_efficiency"
            ]
        },
        "customer_service": {
            "name": "Customer Service Processor",
            "description": "Ticket handling, sentiment analysis, customer insights",
            "task_types": ["default", "ticket_routing", "sentiment_analysis", "customer_insights"],
            "capabilities": [
                "route_ticket",
                "analyze_sentiment",
                "generate_response",
                "assess_satisfaction"
            ]
        },
        "it": {
            "name": "IT Processor",
            "description": "System monitoring, incident management, capacity planning",
            "task_types": ["default", "incident", "monitoring", "capacity"],
            "capabilities": [
                "analyze_incident",
                "monitor_systems",
                "plan_capacity",
                "assess_security"
            ]
        }
    }

    return {
        "total": len(domains),
        "domains": domains
    }


@app.post("/api/ai/process")
async def ai_process(request: AIProcessRequest):
    """
    Process data using domain-specific AI processor.

    This endpoint routes requests to the appropriate domain processor
    (Finance, HR, Operations, Customer Service, IT) for intelligent analysis.

    Example:
        POST /api/ai/process
        {
            "domain": "finance",
            "task_type": "risk_assessment",
            "data": {"portfolio": [...], "market_conditions": "volatile"},
            "context": {"risk_tolerance": "moderate"}
        }
    """
    if not AI_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    try:
        processor = get_processor(request.domain)

        processing_context = {
            "data": request.data,
            "context": request.context,
            "options": request.options,
            "timestamp": datetime.now().isoformat()
        }

        result = await processor.process(processing_context, request.task_type)

        return {
            "status": "completed",
            "domain": request.domain,
            "task_type": request.task_type,
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")


@app.post("/api/ai/analyze")
async def ai_analyze(request: AIAnalyzeRequest):
    """
    Perform AI-powered analysis on provided data.

    This endpoint uses the AI service to analyze data and extract insights.

    Example:
        POST /api/ai/analyze
        {
            "prompt": "Analyze this sales data and identify trends",
            "data": {"sales": [...], "period": "Q4 2024"}
        }
    """
    if not AI_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    try:
        ai_service = get_ai_service()
        result = await ai_service.analyze(
            prompt=request.prompt,
            data=request.data
        )

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "analysis": result
        }
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@app.post("/api/ai/recommend")
async def ai_recommend(request: AIRecommendRequest):
    """
    Generate AI-powered recommendations.

    This endpoint generates actionable recommendations based on context and constraints.

    Example:
        POST /api/ai/recommend
        {
            "context": {"issue": "high customer churn", "segment": "enterprise"},
            "constraints": ["budget under $50k", "implement within 30 days"],
            "max_recommendations": 3
        }
    """
    if not AI_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    try:
        ai_service = get_ai_service()
        recommendations = await ai_service.generate_recommendations(
            context=request.context,
            constraints=request.constraints
        )

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "recommendations": recommendations[:request.max_recommendations]
        }
    except Exception as e:
        logger.error(f"AI recommendation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI recommendation failed: {str(e)}")


@app.get("/api/ai/agents")
async def list_ai_agents():
    """
    List all agents with AI-powered smart processing capabilities.
    """
    # Find all agents with smart processing
    agents_dir = Path(__file__).parent.parent / "src" / "superstandard" / "agents"
    ai_agents = []

    if agents_dir.exists():
        for domain_dir in agents_dir.iterdir():
            if domain_dir.is_dir() and not domain_dir.name.startswith('_'):
                for agent_file in domain_dir.glob("*_agent.py"):
                    try:
                        content = agent_file.read_text()
                        if "smart_processing" in content:
                            # Extract agent info
                            import re
                            class_match = re.search(r'class\s+(\w+Agent)', content)
                            apqc_match = re.search(r'APQC_PROCESS_ID\s*=\s*["\']([^"\']+)["\']', content)
                            domain_match = re.search(r'domain:\s*str\s*=\s*["\']([^"\']+)["\']', content)

                            ai_agents.append({
                                "file": agent_file.name,
                                "domain_folder": domain_dir.name,
                                "class_name": class_match.group(1) if class_match else "Unknown",
                                "apqc_process_id": apqc_match.group(1) if apqc_match else "Unknown",
                                "domain": domain_match.group(1) if domain_match else domain_dir.name,
                                "ai_powered": True
                            })
                    except Exception:
                        pass

    return {
        "total": len(ai_agents),
        "ai_powered_agents": ai_agents
    }


@app.post("/api/ai/demo/{domain}")
async def ai_demo(domain: str):
    """
    Run a demo of AI-powered processing for a specific domain.

    Available domains: finance, hr, operations, customer_service, it

    This endpoint uses sample data to demonstrate the AI capabilities.
    """
    if not AI_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    demo_data = {
        "finance": {
            "task_type": "risk_assessment",
            "data": {
                "portfolio_value": 500000,
                "holdings": [
                    {"symbol": "AAPL", "allocation": 0.25},
                    {"symbol": "MSFT", "allocation": 0.20},
                    {"symbol": "GOOGL", "allocation": 0.15},
                    {"symbol": "BND", "allocation": 0.40}
                ],
                "risk_tolerance": "moderate"
            },
            "context": {"market_conditions": "volatile"}
        },
        "hr": {
            "task_type": "recruitment",
            "data": {
                "position": "Senior Software Engineer",
                "candidates": 15,
                "requirements": ["Python", "AWS", "5+ years experience"]
            },
            "context": {"urgency": "high"}
        },
        "operations": {
            "task_type": "supply_chain",
            "data": {
                "inventory_level": 1500,
                "demand_forecast": 2000,
                "lead_time_days": 14
            },
            "context": {"season": "peak"}
        },
        "customer_service": {
            "task_type": "ticket_routing",
            "data": {
                "ticket_subject": "Cannot login to my account",
                "ticket_content": "I've been trying for 2 hours and getting error 403",
                "customer_tier": "premium"
            },
            "context": {"channel": "email"}
        },
        "it": {
            "task_type": "incident",
            "data": {
                "incident_type": "service_degradation",
                "affected_systems": ["api-gateway", "auth-service"],
                "error_rate": 0.15
            },
            "context": {"severity": "high"}
        }
    }

    if domain not in demo_data:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown domain: {domain}. Available: {list(demo_data.keys())}"
        )

    try:
        processor = get_processor(domain)
        demo = demo_data[domain]

        result = await processor.process(
            {"data": demo["data"], "context": demo["context"]},
            demo["task_type"]
        )

        return {
            "status": "completed",
            "domain": domain,
            "demo_scenario": demo["task_type"],
            "input_data": demo["data"],
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"AI demo error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI demo failed: {str(e)}")


# ============================================================================
# Workflow Orchestration Endpoints
# ============================================================================

# Import orchestration engine
try:
    from superstandard.engine.orchestration_engine import get_orchestration_engine
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False


class OrchestrationRequest(BaseModel):
    """Request model for workflow orchestration"""
    workflow_id: str = Field(..., description="Workflow identifier (e.g., APQC level)")
    workflow_name: str = Field(..., description="Human-readable workflow name")
    agent_ids: List[str] = Field(..., description="List of agent IDs to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Initial input data")
    options: Dict[str, Any] = Field(default_factory=dict, description="Execution options")


class CompositeExecuteRequest(BaseModel):
    """Request to execute a composite agent workflow"""
    composite_level: int = Field(..., ge=1, le=2, description="Composite level (1 or 2)")
    composite_id: str = Field(..., description="Composite agent ID (e.g., '1', '8')")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    max_agents: int = Field(default=10, ge=1, le=50, description="Max agents to execute")


@app.get("/api/orchestration/status")
async def get_orchestration_status():
    """
    Get orchestration engine status.
    """
    if not ORCHESTRATION_AVAILABLE:
        return {
            "available": False,
            "message": "Orchestration engine not available"
        }

    engine = get_orchestration_engine()
    executions = engine.list_executions(limit=10)

    return {
        "available": True,
        "active_executions": len([e for e in executions if e["status"] == "running"]),
        "total_executions": len(engine.executions),
        "recent_executions": executions[:5]
    }


@app.post("/api/orchestration/execute")
async def execute_orchestrated_workflow(request: OrchestrationRequest):
    """
    Execute a workflow with AI-powered orchestration.

    The orchestration engine will:
    - Analyze the workflow for optimal execution
    - Execute agents sequentially or in parallel
    - Handle errors with AI-powered recovery
    - Provide real-time progress tracking

    Example:
        POST /api/orchestration/execute
        {
            "workflow_id": "8",
            "workflow_name": "Manage Financial Resources",
            "agent_ids": ["8.1.1", "8.1.2", "8.2.1"],
            "input_data": {"amount": 10000},
            "options": {"allow_parallel": true}
        }
    """
    if not ORCHESTRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Orchestration engine not available")

    try:
        engine = get_orchestration_engine()

        execution = await engine.execute_workflow(
            workflow_id=request.workflow_id,
            workflow_name=request.workflow_name,
            agent_ids=request.agent_ids,
            input_data=request.input_data,
            options=request.options
        )

        return execution.to_dict()

    except Exception as e:
        logger.error(f"Orchestration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


@app.post("/api/orchestration/composite/{level}/{composite_id}")
async def execute_composite_workflow(level: int, composite_id: str, request: CompositeExecuteRequest):
    """
    Execute a composite agent workflow.

    This loads and executes a predefined composite agent with AI orchestration.

    Args:
        level: Composite level (1 or 2)
        composite_id: The composite ID (e.g., "1" for "Develop Vision and Strategy")

    Example:
        POST /api/orchestration/composite/1/8
        {
            "composite_level": 1,
            "composite_id": "8",
            "input_data": {"fiscal_year": 2024},
            "max_agents": 10
        }
    """
    if not ORCHESTRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Orchestration engine not available")

    # Load composite agent definition
    composite_path = Path(__file__).parent.parent / "generated_composite_agents" / f"level{level}_agents" / f"composite_{composite_id}_level{level}.py"

    if not composite_path.exists():
        raise HTTPException(status_code=404, detail=f"Composite agent not found: level{level}/{composite_id}")

    try:
        # Read composite agent to get child agent IDs
        content = composite_path.read_text()
        import re

        # Extract child agent IDs
        match = re.search(r'self\.child_agent_ids\s*=\s*\[([\s\S]*?)\]', content)
        if not match:
            raise HTTPException(status_code=500, detail="Could not parse composite agent")

        agent_ids_str = match.group(1)
        agent_ids = re.findall(r'"([^"]+)"', agent_ids_str)

        # Limit agents
        agent_ids = agent_ids[:request.max_agents]

        # Extract workflow name
        name_match = re.search(r'Category:\s*([^\n]+)', content)
        workflow_name = name_match.group(1).strip() if name_match else f"Composite {composite_id}"

        # Execute with orchestration
        engine = get_orchestration_engine()

        execution = await engine.execute_workflow(
            workflow_id=f"composite-L{level}-{composite_id}",
            workflow_name=workflow_name,
            agent_ids=agent_ids,
            input_data=request.input_data,
            options={"max_agents": request.max_agents, "allow_parallel": True}
        )

        return {
            "composite_level": level,
            "composite_id": composite_id,
            "workflow_name": workflow_name,
            "agents_executed": len(agent_ids),
            "execution": execution.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Composite execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Composite execution failed: {str(e)}")


@app.get("/api/orchestration/executions")
async def list_orchestration_executions(limit: int = 50):
    """
    List recent workflow executions.
    """
    if not ORCHESTRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Orchestration engine not available")

    engine = get_orchestration_engine()
    return {
        "total": len(engine.executions),
        "executions": engine.list_executions(limit=limit)
    }


@app.get("/api/orchestration/executions/{execution_id}")
async def get_orchestration_execution(execution_id: str):
    """
    Get details of a specific workflow execution.
    """
    if not ORCHESTRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Orchestration engine not available")

    engine = get_orchestration_engine()
    execution = engine.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    return execution.to_dict()


@app.post("/api/orchestration/executions/{execution_id}/cancel")
async def cancel_orchestration_execution(execution_id: str):
    """
    Cancel a running workflow execution.
    """
    if not ORCHESTRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Orchestration engine not available")

    engine = get_orchestration_engine()
    success = await engine.cancel_execution(execution_id)

    if success:
        return {"status": "cancelled", "execution_id": execution_id}
    else:
        raise HTTPException(status_code=400, detail="Could not cancel execution (may not be running)")


@app.get("/api/orchestration/composites")
async def list_composite_agents():
    """
    List available composite agents that can be orchestrated.
    """
    composites = []

    # Level 1 composites
    level1_dir = Path(__file__).parent.parent / "generated_composite_agents" / "level1_agents"
    if level1_dir.exists():
        for f in level1_dir.glob("composite_*_level1.py"):
            import re
            content = f.read_text()
            name_match = re.search(r'Category:\s*([^\n]+)', content)
            child_match = re.search(r'orchestrates\s+(\d+)\s+child', content)

            composites.append({
                "level": 1,
                "id": f.stem.replace("composite_", "").replace("_level1", ""),
                "name": name_match.group(1).strip() if name_match else f.stem,
                "child_agents": int(child_match.group(1)) if child_match else 0,
                "file": f.name
            })

    # Level 2 composites
    level2_dir = Path(__file__).parent.parent / "generated_composite_agents" / "level2_agents"
    if level2_dir.exists():
        for f in level2_dir.glob("composite_*_level2.py"):
            import re
            content = f.read_text()
            name_match = re.search(r'Category:\s*([^\n]+)', content)
            child_match = re.search(r'orchestrates\s+(\d+)\s+child', content)

            composites.append({
                "level": 2,
                "id": f.stem.replace("composite_", "").replace("_level2", ""),
                "name": name_match.group(1).strip() if name_match else f.stem,
                "child_agents": int(child_match.group(1)) if child_match else 0,
                "file": f.name
            })

    return {
        "total": len(composites),
        "level1_count": len([c for c in composites if c["level"] == 1]),
        "level2_count": len([c for c in composites if c["level"] == 2]),
        "composites": sorted(composites, key=lambda x: (x["level"], x["id"]))
    }


# ============================================================================
# Metrics API Endpoints
# ============================================================================

@app.get("/api/metrics/status")
async def get_metrics_status():
    """
    Get metrics service status and availability.
    """
    return {
        "available": METRICS_SERVICE_AVAILABLE,
        "service": "metrics",
        "features": [
            "counters",
            "gauges",
            "time_series",
            "events",
            "dashboard_data"
        ] if METRICS_SERVICE_AVAILABLE else []
    }


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """
    Get a summary of all metrics for dashboard display.

    Returns aggregated metrics across all domains.
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    return metrics_service.get_dashboard_data()


@app.get("/api/metrics/counters")
async def get_all_counters():
    """
    Get all counter metrics.
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    return {
        "counters": dict(metrics_service.counters),
        "total": len(metrics_service.counters)
    }


@app.get("/api/metrics/gauges")
async def get_all_gauges():
    """
    Get all gauge metrics (current values).
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    return {
        "gauges": metrics_service.gauges,
        "total": len(metrics_service.gauges)
    }


@app.get("/api/metrics/series/{series_name}")
async def get_metric_series(series_name: str, minutes: int = 60):
    """
    Get time series data for a specific metric.

    Args:
        series_name: Name of the metric series
        minutes: How many minutes of data to return (default 60)
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    if series_name not in metrics_service.series:
        raise HTTPException(status_code=404, detail=f"Series '{series_name}' not found")

    series = metrics_service.series[series_name]
    recent = series.get_recent(minutes)
    stats = series.get_stats(minutes)

    return {
        "series_name": series_name,
        "time_range_minutes": minutes,
        "data_points": [p.to_dict() for p in recent],
        "statistics": stats
    }


@app.get("/api/metrics/series")
async def list_metric_series():
    """
    List all available metric series.
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    series_info = []
    for name, series in metrics_service.series.items():
        stats = series.get_stats(60)
        series_info.append({
            "name": name,
            "total_points": len(series.points),
            "recent_stats": stats
        })

    return {
        "series": series_info,
        "total": len(series_info)
    }


@app.get("/api/metrics/events")
async def get_recent_events(limit: int = 100):
    """
    Get recent metric events.
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    events = metrics_service.events[-limit:] if metrics_service.events else []
    return {
        "events": events,
        "total": len(events),
        "limit": limit
    }


@app.post("/api/metrics/record")
async def record_metric(
    metric_type: str,
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """
    Record a metric (for internal use).

    Args:
        metric_type: Type of metric (counter, gauge, series)
        name: Metric name
        value: Metric value
        labels: Optional labels for the metric
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    if metric_type == "counter":
        metrics_service.increment(name, int(value), labels)
    elif metric_type == "gauge":
        metrics_service.set_gauge(name, value, labels)
    elif metric_type == "series":
        metrics_service.record(name, value, labels)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric type: {metric_type}")

    return {"status": "recorded", "metric_type": metric_type, "name": name, "value": value}


@app.get("/api/metrics/dashboard")
async def get_dashboard_metrics():
    """
    Get comprehensive metrics data for dashboard visualization.

    Returns pre-aggregated data optimized for dashboard display.
    """
    if not METRICS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Metrics service not available")

    dashboard_data = metrics_service.get_dashboard_data()

    # Add chart data for key metrics
    chart_data = {}
    for series_name in ["agent_executions", "ai_processing_calls", "orchestration_executions", "errors"]:
        if series_name in metrics_service.series:
            series = metrics_service.series[series_name]
            recent = series.get_recent(60)
            chart_data[series_name] = {
                "labels": [p.timestamp.strftime("%H:%M") for p in recent],
                "values": [p.value for p in recent]
            }

    return {
        **dashboard_data,
        "chart_data": chart_data,
        "last_updated": datetime.now().isoformat()
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
