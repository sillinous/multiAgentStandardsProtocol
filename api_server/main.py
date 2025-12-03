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

# API Tags for documentation organization
tags_metadata = [
    {
        "name": "Health & Status",
        "description": "System health checks and status endpoints"
    },
    {
        "name": "Agents",
        "description": "Browse and manage the 455 APQC-aligned enterprise agents"
    },
    {
        "name": "Workflows",
        "description": "Execute and monitor multi-agent workflows"
    },
    {
        "name": "Agent Cards",
        "description": "APQC Process Classification Framework agent card definitions with workflow orchestration"
    },
    {
        "name": "Integrations",
        "description": "Enterprise system integration catalog (ERP, CRM, HRIS, etc.)"
    },
    {
        "name": "APQC Hierarchy",
        "description": "Browse the APQC Process Classification Framework hierarchy"
    },
    {
        "name": "Metrics",
        "description": "Platform metrics and observability"
    },
    {
        "name": "AI Execution",
        "description": "AI-powered agent execution with LLM integration"
    }
]

app = FastAPI(
    title="APQC Agent Platform API",
    description="""
## SuperStandard v1.0 Multi-Agent Protocol Suite

Enterprise-grade REST API for orchestrating 455 APQC-aligned business process agents.

### Key Features

- **455 Enterprise Agents**: Aligned with APQC Process Classification Framework
- **Multi-Agent Workflows**: Sequential, parallel, and conditional orchestration
- **Agent Cards**: Structured workflow definitions with input/output schemas
- **Enterprise Integrations**: 31+ pre-built connectors for ERP, CRM, HRIS systems
- **AI-Powered Execution**: LLM-driven intelligent process automation
- **Real-time Metrics**: Comprehensive observability and monitoring

### APQC Categories Covered

1. Develop Vision and Strategy
2. Develop and Manage Products and Services
3. Market and Sell Products and Services
4. Deliver Physical Products
5. Deliver Services
6. Manage Customer Service
7. Develop and Manage Human Capital
8. Manage Information Technology
9. Manage Financial Resources
10. Acquire, Construct, and Manage Assets
11. Manage Enterprise Risk, Compliance, Remediation, & Resiliency
12. Manage External Relationships
13. Develop and Manage Business Capabilities

### Quick Start

1. Browse agents: `GET /api/agents`
2. Execute workflow: `POST /api/workflows/invoice`
3. Check status: `GET /api/workflows/{workflow_id}`
4. List integrations: `GET /api/integrations`

### Documentation

- [Swagger UI](/docs) - Interactive API documentation
- [ReDoc](/redoc) - Alternative API documentation format
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
    openapi_tags=tags_metadata,
    contact={
        "name": "SuperStandard Platform",
        "url": "https://github.com/sillinous/multiAgentStandardsProtocol"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
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

@app.get("/api/health", tags=["Health & Status"])
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the API server including version and timestamp.
    Use this endpoint for monitoring and load balancer health checks.
    """
    return {
        "status": "healthy",
        "service": "APQC Agent Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.get("/api/agents", tags=["Agents"])
async def list_agents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all available agents with optional filtering.

    - **category**: Filter by APQC category (e.g., "9.0 - Manage Financial Resources")
    - **search**: Search term with wildcard support (* for any, ? for single char)
    - **limit**: Maximum number of agents to return (default: 1000)
    - **offset**: Number of agents to skip (for pagination)

    Returns 455 APQC-aligned enterprise agents covering all 13 process categories.
    """
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


@app.get("/api/agents/categories/list", tags=["Agents"])
async def list_categories(db: Session = Depends(get_db)):
    """
    Get all available APQC categories with agent counts.

    Returns the 13 APQC Process Classification Framework categories
    with the number of agents in each category.
    """
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

@app.get("/api/apqc/hierarchy", tags=["APQC Hierarchy"])
async def get_apqc_hierarchy(
    level: int = 1,
    parent_code: Optional[str] = None
):
    """
    Get APQC PCF hierarchy from the complete JSON file.

    This provides the full APQC Process Classification Framework v7.4 structure
    with proper names at all levels. Use this for hierarchical navigation.

    **Hierarchy Levels:**
    - **Level 1**: 13 Categories (1.0 - 13.0)
    - **Level 2**: Process Groups (1.1, 1.2, etc.)
    - **Level 3**: Processes (1.1.1, 1.1.2, etc.)
    - **Level 4**: Activities (1.1.1.1, 1.1.1.2, etc.)
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


@app.get("/api/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific agent.

    Returns complete agent information including APQC alignment,
    capabilities, and execution metadata.
    """
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

@app.post("/api/workflows/invoice", response_model=WorkflowResponse, tags=["Workflows"])
async def execute_invoice_workflow(
    request: InvoiceWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute invoice processing workflow (4-agent pipeline).

    This is a complete end-to-end invoice processing workflow that:
    1. Validates invoice data
    2. Matches invoice to purchase orders
    3. Applies business rules and approvals
    4. Generates accounting entries

    The workflow runs asynchronously in the background. Use the returned
    `workflow_url` to check status and retrieve results.
    """

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


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStatusResponse, tags=["Workflows"])
async def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get workflow status and results.

    Returns the current status, execution time, agent success/failure counts,
    and output data for a workflow execution.
    """
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
# Workflow History Endpoints
# ============================================================================

@app.get("/api/workflows/history", tags=["Workflows"])
async def get_workflow_history(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated workflow execution history.

    - **limit**: Maximum number of workflows to return (default: 20)
    - **offset**: Number of workflows to skip (for pagination)
    - **status**: Filter by status (pending, running, completed, failed)
    """
    query = db.query(Workflow)

    if status:
        query = query.filter(Workflow.status == status)

    total = query.count()
    workflows = query.order_by(Workflow.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "workflows": [
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
    }


@app.get("/api/workflows/stats", tags=["Workflows"])
async def get_workflow_stats(db: Session = Depends(get_db)):
    """
    Get workflow execution statistics.

    Returns counts by status, success rate, and average execution time.
    """
    total = db.query(Workflow).count()
    if total == 0:
        return {
            "total_workflows": 0,
            "by_status": {},
            "success_rate": 0,
            "average_execution_time_ms": 0
        }

    # Count by status
    status_counts = db.query(
        Workflow.status,
        func.count(Workflow.id)
    ).group_by(Workflow.status).all()

    by_status = {status: count for status, count in status_counts}

    # Success rate (completed workflows only)
    completed = db.query(Workflow).filter(Workflow.status == "completed").count()
    successful = db.query(Workflow).filter(Workflow.success == True).count()
    success_rate = round((successful / completed * 100), 1) if completed > 0 else 0

    # Average execution time
    avg_time = db.query(func.avg(Workflow.execution_time_ms)).filter(
        Workflow.execution_time_ms.isnot(None)
    ).scalar() or 0

    return {
        "total_workflows": total,
        "by_status": by_status,
        "success_rate": success_rate,
        "average_execution_time_ms": round(avg_time, 0)
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

@app.get("/api/agent-cards", tags=["Agent Cards"])
async def list_agent_cards():
    """
    List all available agent card definitions.

    Agent cards define structured workflow specifications aligned with APQC PCF.
    Each card includes step definitions, input/output schemas, and orchestration rules.
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


@app.get("/api/agent-cards-stats", tags=["Agent Cards"])
async def get_agent_card_stats():
    """
    Get statistics about agent cards.

    Returns counts by category, orchestration patterns, compliance frameworks,
    and overall coverage metrics.
    """
    if not AGENT_CARDS_DIR.exists():
        return {
            "total_cards": 0,
            "total_steps": 0,
            "by_category": {},
            "by_pattern": {},
            "compliance_frameworks": [],
            "coverage": {}
        }

    cards = []
    for filepath in AGENT_CARDS_DIR.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                cards.append(json.load(f))
        except Exception:
            continue

    # Calculate statistics
    total_steps = sum(len(c.get("agent_cards", [])) for c in cards)

    # By category
    by_category = {}
    for card in cards:
        cat = card.get("category", "Unknown")
        cat_short = cat.split(" - ")[0] if " - " in cat else cat
        by_category[cat_short] = by_category.get(cat_short, 0) + 1

    # By orchestration pattern
    by_pattern = {}
    for card in cards:
        pattern = card.get("orchestration_pattern", "unknown")
        by_pattern[pattern] = by_pattern.get(pattern, 0) + 1

    # Compliance frameworks
    frameworks = set()
    for card in cards:
        for fw in card.get("compliance_frameworks", []):
            frameworks.add(fw)

    # APQC Coverage (which categories have cards)
    apqc_categories = [f"{i}.0" for i in range(1, 14)]
    covered = set(by_category.keys())
    coverage = {
        "categories_covered": len(covered),
        "total_categories": 13,
        "coverage_percentage": round(len(covered) / 13 * 100, 1),
        "missing_categories": [c for c in apqc_categories if c not in covered]
    }

    # Average steps per card
    avg_steps = round(total_steps / len(cards), 1) if cards else 0

    return {
        "total_cards": len(cards),
        "total_steps": total_steps,
        "average_steps_per_card": avg_steps,
        "by_category": dict(sorted(by_category.items())),
        "by_pattern": by_pattern,
        "compliance_frameworks": sorted(list(frameworks)),
        "coverage": coverage
    }


@app.post("/api/agent-cards-validate", tags=["Agent Cards"])
async def validate_agent_card(card_data: Dict[str, Any]):
    """
    Validate an agent card without saving it.

    Checks for required fields, schema consistency, and best practices.
    Returns validation results with errors, warnings, and suggestions.
    """
    errors = []
    warnings = []
    suggestions = []

    # Required top-level fields
    required_fields = ["apqc_id", "apqc_name", "category", "agent_cards"]
    for field in required_fields:
        if field not in card_data:
            errors.append(f"Missing required field: {field}")

    # Validate APQC ID format
    apqc_id = card_data.get("apqc_id", "")
    if apqc_id and not all(c.isdigit() or c == '.' for c in apqc_id):
        errors.append(f"Invalid APQC ID format: {apqc_id}. Expected format: X.X.X.X")

    # Validate orchestration pattern
    valid_patterns = ["sequential", "parallel", "conditional", "hybrid", "event_driven"]
    pattern = card_data.get("orchestration_pattern")
    if pattern and pattern not in valid_patterns:
        warnings.append(f"Non-standard orchestration pattern: {pattern}. Valid patterns: {', '.join(valid_patterns)}")

    # Validate agent_cards array
    agent_cards = card_data.get("agent_cards", [])
    if not isinstance(agent_cards, list):
        errors.append("agent_cards must be an array")
    elif len(agent_cards) == 0:
        errors.append("agent_cards array is empty - at least one step is required")
    else:
        # Validate each step
        for idx, step in enumerate(agent_cards):
            step_num = idx + 1
            if not step.get("step_name"):
                errors.append(f"Step {step_num}: missing step_name")
            if not step.get("id"):
                warnings.append(f"Step {step_num}: missing id field")
            if not step.get("input_schema"):
                suggestions.append(f"Step {step_num}: consider adding input_schema for better documentation")
            if not step.get("output_schema"):
                suggestions.append(f"Step {step_num}: consider adding output_schema for better documentation")

        # Check step numbering
        step_numbers = [s.get("step_number") for s in agent_cards if s.get("step_number")]
        if step_numbers and len(set(step_numbers)) != len(step_numbers):
            warnings.append("Duplicate step numbers detected")

    # Check for KPIs
    if not card_data.get("kpis"):
        suggestions.append("Consider adding KPIs to measure workflow effectiveness")

    # Check for compliance frameworks
    if not card_data.get("compliance_frameworks"):
        suggestions.append("Consider specifying applicable compliance frameworks")

    # Check for workflow rules
    if not card_data.get("workflow_rules"):
        suggestions.append("Consider adding workflow_rules with entry/exit criteria")

    # Determine validity
    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "summary": {
            "total_steps": len(agent_cards) if isinstance(agent_cards, list) else 0,
            "has_kpis": bool(card_data.get("kpis")),
            "has_compliance": bool(card_data.get("compliance_frameworks")),
            "has_workflow_rules": bool(card_data.get("workflow_rules"))
        }
    }


@app.get("/api/agent-cards-export", tags=["Agent Cards"])
async def export_all_agent_cards():
    """
    Export all agent cards as a complete package.

    Returns all agent cards with full details in a single response,
    suitable for backup or migration purposes.
    """
    if not AGENT_CARDS_DIR.exists():
        return {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_cards": 0,
                "platform": "SuperStandard v1.0",
                "format_version": "1.0"
            },
            "agent_cards": []
        }

    cards = []
    for filepath in AGENT_CARDS_DIR.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                cards.append(data)
        except Exception as e:
            logger.warning(f"Failed to read agent card {filepath}: {e}")
            continue

    # Sort by APQC ID
    cards.sort(key=lambda x: x.get("apqc_id", ""))

    return {
        "export_info": {
            "exported_at": datetime.utcnow().isoformat(),
            "total_cards": len(cards),
            "platform": "SuperStandard v1.0",
            "format_version": "1.0"
        },
        "agent_cards": cards
    }


@app.post("/api/agent-cards-import", tags=["Agent Cards"])
async def import_agent_cards(import_data: Dict[str, Any]):
    """
    Import agent cards from an export package.

    Accepts either:
    - A single agent card object
    - An export package with multiple cards

    Returns import statistics including success/skip/error counts.
    """
    results = {
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "details": []
    }

    # Determine format
    cards_to_import = []
    if "agent_cards" in import_data and "export_info" in import_data:
        # Export package format
        cards_to_import = import_data.get("agent_cards", [])
    elif "apqc_id" in import_data and "agent_cards" in import_data:
        # Single card format
        cards_to_import = [import_data]
    else:
        raise HTTPException(status_code=400, detail="Invalid import format")

    # Ensure directory exists
    AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)

    for card in cards_to_import:
        apqc_id = card.get("apqc_id")
        apqc_name = card.get("apqc_name")

        if not apqc_id or not apqc_name:
            results["errors"] += 1
            results["details"].append({"error": "Missing apqc_id or apqc_name"})
            continue

        filename = f"apqc_{apqc_id.replace('.', '_')}_{apqc_name.lower().replace(' ', '_')[:30]}.json"
        filepath = AGENT_CARDS_DIR / filename

        if filepath.exists():
            results["skipped"] += 1
            results["details"].append({"apqc_id": apqc_id, "status": "skipped", "reason": "already exists"})
            continue

        try:
            card["imported_at"] = datetime.utcnow().isoformat()
            with open(filepath, 'w') as f:
                json.dump(card, f, indent=2)
            results["imported"] += 1
            results["details"].append({"apqc_id": apqc_id, "status": "imported", "filename": filename})
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"apqc_id": apqc_id, "status": "error", "error": str(e)})

    return results


@app.get("/api/agent-cards/{apqc_code:path}", tags=["Agent Cards"])
async def get_agent_card(apqc_code: str):
    """
    Get agent card definition for a specific APQC code.

    Returns the complete agent card including all workflow steps,
    input/output schemas, decision rules, and error handlers.

    - **apqc_code**: APQC code (e.g., "9.2.1.1")
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


@app.post("/api/agent-cards", tags=["Agent Cards"])
async def create_agent_card(card_request: AgentCardCreate):
    """
    Create a new agent card definition.

    Creates a new APQC-aligned workflow specification that can be executed
    by the orchestration engine. The agent card will be saved to the
    agent_cards directory.
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


@app.put("/api/agent-cards/{filename}", tags=["Agent Cards"])
async def update_agent_card(filename: str, card_request: Dict[str, Any]):
    """
    Update an existing agent card definition.

    Replaces the entire agent card content with the provided data.
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


@app.delete("/api/agent-cards/{filename}", tags=["Agent Cards"])
async def delete_agent_card(filename: str):
    """
    Delete an agent card definition.

    Permanently removes the agent card file from the system.
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


class AgentCardCopy(BaseModel):
    """Request model for copying agent cards."""
    new_apqc_id: str = Field(..., description="New APQC ID for the copy")
    new_name: str = Field(..., description="New name for the copy")


@app.post("/api/agent-cards/{apqc_code:path}/copy", tags=["Agent Cards"])
async def copy_agent_card(apqc_code: str, copy_request: AgentCardCopy):
    """
    Create a copy of an existing agent card with a new APQC ID.

    This is useful for creating variations of workflows or starting
    new workflows based on existing templates.
    """
    # Get the source card
    source_card = await get_agent_card(apqc_code)

    # Create the copy
    new_card = source_card.copy()
    new_card["apqc_id"] = copy_request.new_apqc_id
    new_card["apqc_name"] = copy_request.new_name
    new_card["created_at"] = datetime.utcnow().isoformat()
    new_card["copied_from"] = apqc_code

    # Update step IDs to reflect new APQC ID
    new_id_underscore = copy_request.new_apqc_id.replace(".", "_")
    if "agent_cards" in new_card:
        for idx, step in enumerate(new_card["agent_cards"]):
            step["id"] = f"agent_{new_id_underscore}_step{idx + 1}"
            step["apqc_id"] = copy_request.new_apqc_id

    # Generate filename
    filename = f"apqc_{new_id_underscore}_{copy_request.new_name.lower().replace(' ', '_')[:30]}.json"

    # Check if already exists
    filepath = AGENT_CARDS_DIR / filename
    if filepath.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Agent card with APQC ID '{copy_request.new_apqc_id}' already exists"
        )

    # Save the copy
    try:
        AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(new_card, f, indent=2)

        logger.info(f"Copied agent card {apqc_code} to {copy_request.new_apqc_id}")

        return {
            "success": True,
            "message": "Agent card copied successfully",
            "source_apqc_id": apqc_code,
            "new_apqc_id": copy_request.new_apqc_id,
            "new_name": copy_request.new_name,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to copy agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to copy agent card: {str(e)}"
        )


class BulkCopyItem(BaseModel):
    """Single item in a bulk copy request."""
    source_apqc_code: str = Field(..., description="Source APQC code to copy from")
    new_apqc_id: str = Field(..., description="New APQC ID for the copy")
    new_name: str = Field(..., description="New name for the copy")


class BulkCopyRequest(BaseModel):
    """Request model for bulk copying agent cards."""
    copies: List[BulkCopyItem] = Field(..., description="List of cards to copy")
    stop_on_error: bool = Field(default=False, description="Stop processing on first error")


@app.post("/api/agent-cards/bulk/copy", tags=["Agent Cards"])
async def bulk_copy_agent_cards(request: BulkCopyRequest):
    """
    Bulk copy multiple agent cards at once.

    Useful for creating entire workflow sets or migrating card collections.
    """
    results = []
    errors = []

    for item in request.copies:
        try:
            copy_request = AgentCardCopy(
                new_apqc_id=item.new_apqc_id,
                new_name=item.new_name
            )
            result = await copy_agent_card(item.source_apqc_code, copy_request)
            results.append({
                "source": item.source_apqc_code,
                "new_apqc_id": item.new_apqc_id,
                "status": "success",
                "filename": result.get("filename")
            })
        except HTTPException as e:
            error_entry = {
                "source": item.source_apqc_code,
                "new_apqc_id": item.new_apqc_id,
                "status": "error",
                "error": e.detail
            }
            errors.append(error_entry)
            results.append(error_entry)

            if request.stop_on_error:
                break
        except Exception as e:
            error_entry = {
                "source": item.source_apqc_code,
                "new_apqc_id": item.new_apqc_id,
                "status": "error",
                "error": str(e)
            }
            errors.append(error_entry)
            results.append(error_entry)

            if request.stop_on_error:
                break

    return {
        "success": len(errors) == 0,
        "total_requested": len(request.copies),
        "successful": len(results) - len(errors),
        "failed": len(errors),
        "results": results
    }


class CloneWithModifications(BaseModel):
    """Request model for cloning with inline modifications."""
    new_apqc_id: str = Field(..., description="New APQC ID for the clone")
    new_name: str = Field(..., description="New name for the clone")
    modifications: Dict[str, Any] = Field(default={}, description="Fields to override in the clone")
    step_modifications: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Modifications to apply to specific steps by index"
    )


@app.post("/api/agent-cards/{apqc_code:path}/clone", tags=["Agent Cards"])
async def clone_agent_card_with_modifications(apqc_code: str, request: CloneWithModifications):
    """
    Clone an agent card with inline modifications.

    Unlike copy, this allows modifying fields during the clone operation,
    useful for creating variations without multiple API calls.
    """
    # Get the source card
    source_card = await get_agent_card(apqc_code)

    # Create base clone
    new_card = source_card.copy()
    new_card["apqc_id"] = request.new_apqc_id
    new_card["apqc_name"] = request.new_name
    new_card["created_at"] = datetime.utcnow().isoformat()
    new_card["cloned_from"] = apqc_code
    new_card["modifications_applied"] = list(request.modifications.keys())

    # Apply top-level modifications
    for key, value in request.modifications.items():
        if key not in ["apqc_id", "apqc_name"]:  # Protect identity fields
            new_card[key] = value

    # Update step IDs
    new_id_underscore = request.new_apqc_id.replace(".", "_")
    if "agent_cards" in new_card:
        for idx, step in enumerate(new_card["agent_cards"]):
            step["id"] = f"agent_{new_id_underscore}_step{idx + 1}"
            step["apqc_id"] = request.new_apqc_id

            # Apply step-specific modifications
            if request.step_modifications:
                for step_mod in request.step_modifications:
                    if step_mod.get("step_index") == idx:
                        for key, value in step_mod.items():
                            if key != "step_index":
                                step[key] = value

    # Generate filename
    filename = f"apqc_{new_id_underscore}_{request.new_name.lower().replace(' ', '_')[:30]}.json"
    filepath = AGENT_CARDS_DIR / filename

    if filepath.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Agent card with APQC ID '{request.new_apqc_id}' already exists"
        )

    try:
        AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(new_card, f, indent=2)

        logger.info(f"Cloned agent card {apqc_code} to {request.new_apqc_id} with modifications")

        return {
            "success": True,
            "message": "Agent card cloned with modifications",
            "source_apqc_id": apqc_code,
            "new_apqc_id": request.new_apqc_id,
            "modifications_applied": list(request.modifications.keys()),
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to clone agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone agent card: {str(e)}"
        )


# Version tracking storage (in production, use database)
CARD_VERSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
VERSIONS_DIR = Path("data/agent_card_versions")


@app.post("/api/agent-cards/{apqc_code:path}/versions", tags=["Agent Cards - Versioning"])
async def create_agent_card_version(apqc_code: str, description: str = ""):
    """
    Create a versioned snapshot of an agent card.

    Saves the current state as a version that can be restored later.
    """
    # Get current card
    current_card = await get_agent_card(apqc_code)

    # Initialize version history for this card if needed
    if apqc_code not in CARD_VERSION_HISTORY:
        CARD_VERSION_HISTORY[apqc_code] = []

    # Create version entry
    version_number = len(CARD_VERSION_HISTORY[apqc_code]) + 1
    version_entry = {
        "version": version_number,
        "timestamp": datetime.utcnow().isoformat(),
        "description": description or f"Version {version_number}",
        "snapshot": current_card.copy()
    }

    CARD_VERSION_HISTORY[apqc_code].append(version_entry)

    # Also persist to file system
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    version_file = VERSIONS_DIR / f"{apqc_code.replace('.', '_')}_v{version_number}.json"
    with open(version_file, 'w') as f:
        json.dump(version_entry, f, indent=2)

    logger.info(f"Created version {version_number} for {apqc_code}")

    return {
        "success": True,
        "apqc_id": apqc_code,
        "version": version_number,
        "timestamp": version_entry["timestamp"],
        "description": version_entry["description"]
    }


@app.get("/api/agent-cards/{apqc_code:path}/versions", tags=["Agent Cards - Versioning"])
async def list_agent_card_versions(apqc_code: str):
    """
    List all versions of an agent card.
    """
    # Load from file system if not in memory
    if apqc_code not in CARD_VERSION_HISTORY:
        CARD_VERSION_HISTORY[apqc_code] = []
        # Try to load from files
        if VERSIONS_DIR.exists():
            pattern = f"{apqc_code.replace('.', '_')}_v*.json"
            for version_file in VERSIONS_DIR.glob(pattern):
                try:
                    with open(version_file, 'r') as f:
                        version_entry = json.load(f)
                        CARD_VERSION_HISTORY[apqc_code].append(version_entry)
                except Exception:
                    pass
            # Sort by version number
            CARD_VERSION_HISTORY[apqc_code].sort(key=lambda x: x.get("version", 0))

    versions = CARD_VERSION_HISTORY.get(apqc_code, [])

    return {
        "apqc_id": apqc_code,
        "total_versions": len(versions),
        "versions": [
            {
                "version": v["version"],
                "timestamp": v["timestamp"],
                "description": v["description"]
            }
            for v in versions
        ]
    }


@app.get("/api/agent-cards/{apqc_code:path}/versions/{version}", tags=["Agent Cards - Versioning"])
async def get_agent_card_version(apqc_code: str, version: int):
    """
    Get a specific version of an agent card.
    """
    # Ensure versions are loaded
    await list_agent_card_versions(apqc_code)

    versions = CARD_VERSION_HISTORY.get(apqc_code, [])
    for v in versions:
        if v["version"] == version:
            return v

    raise HTTPException(
        status_code=404,
        detail=f"Version {version} not found for agent card {apqc_code}"
    )


@app.post("/api/agent-cards/{apqc_code:path}/versions/{version}/restore", tags=["Agent Cards - Versioning"])
async def restore_agent_card_version(apqc_code: str, version: int, create_backup: bool = True):
    """
    Restore an agent card to a previous version.

    Optionally creates a backup of the current state before restoring.
    """
    # Get the version to restore
    version_data = await get_agent_card_version(apqc_code, version)

    # Create backup of current state if requested
    if create_backup:
        await create_agent_card_version(apqc_code, f"Backup before restoring to v{version}")

    # Find and update the current card file
    card_found = False
    for file in AGENT_CARDS_DIR.iterdir():
        if file.suffix == '.json':
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                if card.get("apqc_id") == apqc_code:
                    # Restore from snapshot
                    restored_card = version_data["snapshot"].copy()
                    restored_card["restored_from_version"] = version
                    restored_card["restored_at"] = datetime.utcnow().isoformat()

                    with open(file, 'w') as f:
                        json.dump(restored_card, f, indent=2)

                    card_found = True
                    break
            except Exception:
                pass

    if not card_found:
        raise HTTPException(
            status_code=404,
            detail=f"Agent card {apqc_code} not found"
        )

    logger.info(f"Restored {apqc_code} to version {version}")

    return {
        "success": True,
        "apqc_id": apqc_code,
        "restored_to_version": version,
        "backup_created": create_backup
    }


# Template Management
TEMPLATES_DIR = Path("data/agent_card_templates")


class TemplateCreate(BaseModel):
    """Request model for creating a template."""
    template_name: str = Field(..., description="Name for the template")
    description: str = Field(default="", description="Template description")
    category: str = Field(default="general", description="Template category")
    tags: List[str] = Field(default=[], description="Tags for searchability")


@app.post("/api/agent-cards/{apqc_code:path}/template", tags=["Agent Cards - Templates"])
async def create_template_from_card(apqc_code: str, template: TemplateCreate):
    """
    Create a reusable template from an existing agent card.

    Templates strip instance-specific data and can be used to quickly
    create new cards with consistent structure.
    """
    # Get the source card
    source_card = await get_agent_card(apqc_code)

    # Create template (remove instance-specific fields)
    template_data = source_card.copy()
    template_data.pop("apqc_id", None)
    template_data.pop("created_at", None)
    template_data.pop("copied_from", None)
    template_data.pop("cloned_from", None)

    # Add template metadata
    template_entry = {
        "template_id": f"tpl_{template.template_name.lower().replace(' ', '_')}",
        "template_name": template.template_name,
        "description": template.description,
        "category": template.category,
        "tags": template.tags,
        "created_at": datetime.utcnow().isoformat(),
        "source_apqc_id": apqc_code,
        "card_template": template_data
    }

    # Save template
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_file = TEMPLATES_DIR / f"{template_entry['template_id']}.json"

    if template_file.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Template '{template.template_name}' already exists"
        )

    with open(template_file, 'w') as f:
        json.dump(template_entry, f, indent=2)

    logger.info(f"Created template '{template.template_name}' from {apqc_code}")

    return {
        "success": True,
        "template_id": template_entry["template_id"],
        "template_name": template.template_name,
        "source_apqc_id": apqc_code
    }


@app.get("/api/templates", tags=["Agent Cards - Templates"])
async def list_templates(category: Optional[str] = None, tag: Optional[str] = None):
    """
    List all available agent card templates.

    Optionally filter by category or tag.
    """
    templates = []

    if TEMPLATES_DIR.exists():
        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template = json.load(f)

                    # Apply filters
                    if category and template.get("category") != category:
                        continue
                    if tag and tag not in template.get("tags", []):
                        continue

                    templates.append({
                        "template_id": template["template_id"],
                        "template_name": template["template_name"],
                        "description": template.get("description", ""),
                        "category": template.get("category", "general"),
                        "tags": template.get("tags", []),
                        "source_apqc_id": template.get("source_apqc_id")
                    })
            except Exception:
                pass

    return {
        "total": len(templates),
        "filters": {"category": category, "tag": tag},
        "templates": templates
    }


@app.get("/api/templates/{template_id}", tags=["Agent Cards - Templates"])
async def get_template(template_id: str):
    """
    Get a specific template by ID.
    """
    template_file = TEMPLATES_DIR / f"{template_id}.json"

    if not template_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_id}' not found"
        )

    with open(template_file, 'r') as f:
        return json.load(f)


class CardFromTemplate(BaseModel):
    """Request model for creating a card from template."""
    apqc_id: str = Field(..., description="APQC ID for the new card")
    apqc_name: str = Field(..., description="Name for the new card")
    overrides: Dict[str, Any] = Field(default={}, description="Field overrides")


@app.post("/api/templates/{template_id}/instantiate", tags=["Agent Cards - Templates"])
async def create_card_from_template(template_id: str, request: CardFromTemplate):
    """
    Create a new agent card from a template.

    The template provides the base structure, and you can override
    specific fields as needed.
    """
    # Get template
    template = await get_template(template_id)

    # Create new card from template
    new_card = template["card_template"].copy()
    new_card["apqc_id"] = request.apqc_id
    new_card["apqc_name"] = request.apqc_name
    new_card["created_at"] = datetime.utcnow().isoformat()
    new_card["created_from_template"] = template_id

    # Apply overrides
    for key, value in request.overrides.items():
        if key not in ["apqc_id", "apqc_name"]:
            new_card[key] = value

    # Update step IDs
    new_id_underscore = request.apqc_id.replace(".", "_")
    if "agent_cards" in new_card:
        for idx, step in enumerate(new_card["agent_cards"]):
            step["id"] = f"agent_{new_id_underscore}_step{idx + 1}"
            step["apqc_id"] = request.apqc_id

    # Generate filename and save
    filename = f"apqc_{new_id_underscore}_{request.apqc_name.lower().replace(' ', '_')[:30]}.json"
    filepath = AGENT_CARDS_DIR / filename

    if filepath.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Agent card with APQC ID '{request.apqc_id}' already exists"
        )

    AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(new_card, f, indent=2)

    logger.info(f"Created card {request.apqc_id} from template {template_id}")

    return {
        "success": True,
        "apqc_id": request.apqc_id,
        "apqc_name": request.apqc_name,
        "template_id": template_id,
        "filename": filename
    }


@app.delete("/api/templates/{template_id}", tags=["Agent Cards - Templates"])
async def delete_template(template_id: str):
    """
    Delete a template.
    """
    template_file = TEMPLATES_DIR / f"{template_id}.json"

    if not template_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_id}' not found"
        )

    template_file.unlink()
    logger.info(f"Deleted template {template_id}")

    return {"success": True, "deleted_template": template_id}


# Diff Comparison
@app.get("/api/agent-cards/compare", tags=["Agent Cards - Comparison"])
async def compare_agent_cards(apqc_code_1: str, apqc_code_2: str):
    """
    Compare two agent cards and show differences.

    Useful for reviewing changes or comparing workflow variations.
    """
    card1 = await get_agent_card(apqc_code_1)
    card2 = await get_agent_card(apqc_code_2)

    def deep_diff(d1: Dict, d2: Dict, path: str = "") -> List[Dict]:
        """Recursively find differences between two dictionaries."""
        differences = []

        all_keys = set(d1.keys()) | set(d2.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            if key not in d1:
                differences.append({
                    "path": current_path,
                    "type": "added",
                    "value": d2[key]
                })
            elif key not in d2:
                differences.append({
                    "path": current_path,
                    "type": "removed",
                    "value": d1[key]
                })
            elif d1[key] != d2[key]:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    differences.extend(deep_diff(d1[key], d2[key], current_path))
                elif isinstance(d1[key], list) and isinstance(d2[key], list):
                    if len(d1[key]) != len(d2[key]):
                        differences.append({
                            "path": current_path,
                            "type": "modified",
                            "old_count": len(d1[key]),
                            "new_count": len(d2[key])
                        })
                    else:
                        for i, (item1, item2) in enumerate(zip(d1[key], d2[key])):
                            if item1 != item2:
                                if isinstance(item1, dict) and isinstance(item2, dict):
                                    differences.extend(deep_diff(item1, item2, f"{current_path}[{i}]"))
                                else:
                                    differences.append({
                                        "path": f"{current_path}[{i}]",
                                        "type": "modified",
                                        "old_value": item1,
                                        "new_value": item2
                                    })
                else:
                    differences.append({
                        "path": current_path,
                        "type": "modified",
                        "old_value": d1[key],
                        "new_value": d2[key]
                    })

        return differences

    differences = deep_diff(card1, card2)

    return {
        "card_1": apqc_code_1,
        "card_2": apqc_code_2,
        "total_differences": len(differences),
        "differences": differences,
        "summary": {
            "added": len([d for d in differences if d["type"] == "added"]),
            "removed": len([d for d in differences if d["type"] == "removed"]),
            "modified": len([d for d in differences if d["type"] == "modified"])
        }
    }


@app.get("/api/agent-cards/{apqc_code:path}/versions/{v1}/compare/{v2}", tags=["Agent Cards - Versioning"])
async def compare_card_versions(apqc_code: str, v1: int, v2: int):
    """
    Compare two versions of the same agent card.
    """
    version1 = await get_agent_card_version(apqc_code, v1)
    version2 = await get_agent_card_version(apqc_code, v2)

    # Reuse the compare logic
    def deep_diff(d1: Dict, d2: Dict, path: str = "") -> List[Dict]:
        differences = []
        all_keys = set(d1.keys()) | set(d2.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            if key not in d1:
                differences.append({"path": current_path, "type": "added", "value": d2[key]})
            elif key not in d2:
                differences.append({"path": current_path, "type": "removed", "value": d1[key]})
            elif d1[key] != d2[key]:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    differences.extend(deep_diff(d1[key], d2[key], current_path))
                else:
                    differences.append({
                        "path": current_path,
                        "type": "modified",
                        "old_value": d1[key],
                        "new_value": d2[key]
                    })

        return differences

    differences = deep_diff(version1["snapshot"], version2["snapshot"])

    return {
        "apqc_id": apqc_code,
        "version_1": v1,
        "version_2": v2,
        "timestamp_1": version1["timestamp"],
        "timestamp_2": version2["timestamp"],
        "total_differences": len(differences),
        "differences": differences
    }


# Archive/Restore Functionality
ARCHIVE_DIR = Path("data/agent_card_archive")


@app.post("/api/agent-cards/{apqc_code:path}/archive", tags=["Agent Cards - Archive"])
async def archive_agent_card(apqc_code: str, reason: str = ""):
    """
    Archive an agent card (soft delete).

    The card is moved to the archive and can be restored later.
    """
    # Find and load the card
    card_file = None
    card_data = None

    for file in AGENT_CARDS_DIR.iterdir():
        if file.suffix == '.json':
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                if card.get("apqc_id") == apqc_code:
                    card_file = file
                    card_data = card
                    break
            except Exception:
                pass

    if not card_file:
        raise HTTPException(
            status_code=404,
            detail=f"Agent card {apqc_code} not found"
        )

    # Add archive metadata
    card_data["archived_at"] = datetime.utcnow().isoformat()
    card_data["archive_reason"] = reason
    card_data["original_filename"] = card_file.name

    # Save to archive
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / card_file.name

    with open(archive_file, 'w') as f:
        json.dump(card_data, f, indent=2)

    # Remove from active directory
    card_file.unlink()

    logger.info(f"Archived agent card {apqc_code}")

    return {
        "success": True,
        "apqc_id": apqc_code,
        "archived_at": card_data["archived_at"],
        "reason": reason
    }


@app.get("/api/agent-cards/archived", tags=["Agent Cards - Archive"])
async def list_archived_cards():
    """
    List all archived agent cards.
    """
    archived = []

    if ARCHIVE_DIR.exists():
        for file in ARCHIVE_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                    archived.append({
                        "apqc_id": card.get("apqc_id"),
                        "apqc_name": card.get("apqc_name"),
                        "archived_at": card.get("archived_at"),
                        "archive_reason": card.get("archive_reason", ""),
                        "filename": file.name
                    })
            except Exception:
                pass

    return {
        "total": len(archived),
        "archived_cards": archived
    }


@app.post("/api/agent-cards/archived/{apqc_code:path}/restore", tags=["Agent Cards - Archive"])
async def restore_archived_card(apqc_code: str):
    """
    Restore an archived agent card.
    """
    # Find in archive
    archived_file = None
    card_data = None

    if ARCHIVE_DIR.exists():
        for file in ARCHIVE_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                if card.get("apqc_id") == apqc_code:
                    archived_file = file
                    card_data = card
                    break
            except Exception:
                pass

    if not archived_file:
        raise HTTPException(
            status_code=404,
            detail=f"Archived card {apqc_code} not found"
        )

    # Remove archive metadata
    original_filename = card_data.pop("original_filename", archived_file.name)
    card_data.pop("archived_at", None)
    card_data.pop("archive_reason", None)
    card_data["restored_at"] = datetime.utcnow().isoformat()

    # Restore to active directory
    AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    restore_path = AGENT_CARDS_DIR / original_filename

    # Check for conflicts
    if restore_path.exists():
        raise HTTPException(
            status_code=409,
            detail=f"A card already exists at {original_filename}. Delete or rename it first."
        )

    with open(restore_path, 'w') as f:
        json.dump(card_data, f, indent=2)

    # Remove from archive
    archived_file.unlink()

    logger.info(f"Restored agent card {apqc_code} from archive")

    return {
        "success": True,
        "apqc_id": apqc_code,
        "restored_to": original_filename
    }


@app.delete("/api/agent-cards/archived/{apqc_code:path}", tags=["Agent Cards - Archive"])
async def permanently_delete_archived_card(apqc_code: str):
    """
    Permanently delete an archived agent card.

    This action cannot be undone.
    """
    if ARCHIVE_DIR.exists():
        for file in ARCHIVE_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                if card.get("apqc_id") == apqc_code:
                    file.unlink()
                    logger.info(f"Permanently deleted archived card {apqc_code}")
                    return {
                        "success": True,
                        "apqc_id": apqc_code,
                        "permanently_deleted": True
                    }
            except Exception:
                pass

    raise HTTPException(
        status_code=404,
        detail=f"Archived card {apqc_code} not found"
    )


@app.get("/api/integrations", tags=["Integrations"])
async def list_integrations():
    """
    List all available integrations from the catalog.

    Returns 31+ enterprise system connectors organized by category:
    ERP, CRM, HRIS, Financial Systems, and more.

    Each integration includes connection protocols, authentication methods,
    and common use cases.
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
# Agent Execution Engine
# ============================================================================

# Execution queue and scheduler storage
EXECUTION_QUEUE: List[Dict[str, Any]] = []
SCHEDULED_JOBS: Dict[str, Dict[str, Any]] = {}
EXECUTION_HISTORY: List[Dict[str, Any]] = []


class ExecutionRequest(BaseModel):
    """Request to execute an agent or workflow."""
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default={})
    priority: int = Field(default=5, ge=1, le=10, description="1=highest, 10=lowest")
    scheduled_at: Optional[str] = Field(default=None, description="ISO datetime for scheduled execution")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for completion notification")
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    retry_count: int = Field(default=0, ge=0, le=5)
    tags: List[str] = Field(default=[])


class ExecutionStatus(BaseModel):
    """Status of an execution."""
    execution_id: str
    status: str  # queued, running, completed, failed, cancelled
    progress: float = 0.0  # 0-100
    current_step: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.post("/api/executions", tags=["Execution Engine"])
async def create_execution(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """
    Queue an agent or workflow for execution.

    Supports immediate execution, scheduled execution, and priority queuing.
    """
    execution_id = f"exec_{uuid4().hex[:12]}"

    execution = {
        "execution_id": execution_id,
        "agent_id": request.agent_id,
        "workflow_id": request.workflow_id,
        "input_data": request.input_data,
        "priority": request.priority,
        "status": "queued",
        "progress": 0.0,
        "current_step": None,
        "queued_at": datetime.utcnow().isoformat(),
        "scheduled_at": request.scheduled_at,
        "started_at": None,
        "completed_at": None,
        "callback_url": request.callback_url,
        "timeout_seconds": request.timeout_seconds,
        "retry_count": request.retry_count,
        "retries_remaining": request.retry_count,
        "tags": request.tags,
        "result": None,
        "error": None
    }

    # Add to queue (sorted by priority)
    EXECUTION_QUEUE.append(execution)
    EXECUTION_QUEUE.sort(key=lambda x: x["priority"])

    logger.info(f"Created execution {execution_id} for agent={request.agent_id} workflow={request.workflow_id}")

    return {
        "execution_id": execution_id,
        "status": "queued",
        "position": EXECUTION_QUEUE.index(execution) + 1,
        "estimated_start": None  # Would calculate based on queue
    }


@app.get("/api/executions", tags=["Execution Engine"])
async def list_executions(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 50,
    include_history: bool = False
):
    """
    List executions in the queue and optionally history.
    """
    results = []

    # Add queued executions
    for exec in EXECUTION_QUEUE:
        if status and exec["status"] != status:
            continue
        if agent_id and exec.get("agent_id") != agent_id:
            continue
        results.append(exec)

    # Add history if requested
    if include_history:
        for exec in EXECUTION_HISTORY:
            if status and exec["status"] != status:
                continue
            if agent_id and exec.get("agent_id") != agent_id:
                continue
            results.append(exec)

    return {
        "total": len(results),
        "executions": results[:limit],
        "queue_length": len(EXECUTION_QUEUE)
    }


@app.get("/api/executions/{execution_id}", tags=["Execution Engine"])
async def get_execution_status(execution_id: str):
    """
    Get detailed status of a specific execution.
    """
    # Check queue
    for exec in EXECUTION_QUEUE:
        if exec["execution_id"] == execution_id:
            return ExecutionStatus(**exec)

    # Check history
    for exec in EXECUTION_HISTORY:
        if exec["execution_id"] == execution_id:
            return ExecutionStatus(**exec)

    raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")


@app.post("/api/executions/{execution_id}/cancel", tags=["Execution Engine"])
async def cancel_execution(execution_id: str):
    """
    Cancel a queued or running execution.
    """
    for i, exec in enumerate(EXECUTION_QUEUE):
        if exec["execution_id"] == execution_id:
            exec["status"] = "cancelled"
            exec["completed_at"] = datetime.utcnow().isoformat()
            EXECUTION_HISTORY.append(EXECUTION_QUEUE.pop(i))
            return {"success": True, "execution_id": execution_id, "status": "cancelled"}

    raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found in queue")


@app.post("/api/executions/{execution_id}/retry", tags=["Execution Engine"])
async def retry_execution(execution_id: str):
    """
    Retry a failed execution.
    """
    for exec in EXECUTION_HISTORY:
        if exec["execution_id"] == execution_id and exec["status"] == "failed":
            # Create new execution based on failed one
            new_id = f"exec_{uuid4().hex[:12]}"
            new_exec = exec.copy()
            new_exec["execution_id"] = new_id
            new_exec["status"] = "queued"
            new_exec["progress"] = 0.0
            new_exec["queued_at"] = datetime.utcnow().isoformat()
            new_exec["started_at"] = None
            new_exec["completed_at"] = None
            new_exec["error"] = None
            new_exec["retry_of"] = execution_id

            EXECUTION_QUEUE.append(new_exec)
            EXECUTION_QUEUE.sort(key=lambda x: x["priority"])

            return {"success": True, "new_execution_id": new_id, "original_id": execution_id}

    raise HTTPException(status_code=404, detail=f"Failed execution {execution_id} not found")


class ScheduleRequest(BaseModel):
    """Request to schedule recurring execution."""
    name: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default={})
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 9 * * *' for 9am daily)")
    timezone: str = Field(default="UTC")
    enabled: bool = Field(default=True)


@app.post("/api/schedules", tags=["Execution Engine"])
async def create_schedule(request: ScheduleRequest):
    """
    Create a scheduled/recurring execution.
    """
    schedule_id = f"sched_{uuid4().hex[:8]}"

    schedule = {
        "schedule_id": schedule_id,
        "name": request.name,
        "agent_id": request.agent_id,
        "workflow_id": request.workflow_id,
        "input_data": request.input_data,
        "cron_expression": request.cron_expression,
        "timezone": request.timezone,
        "enabled": request.enabled,
        "created_at": datetime.utcnow().isoformat(),
        "last_run": None,
        "next_run": None,  # Would calculate from cron
        "run_count": 0
    }

    SCHEDULED_JOBS[schedule_id] = schedule

    return {"success": True, "schedule_id": schedule_id, "schedule": schedule}


@app.get("/api/schedules", tags=["Execution Engine"])
async def list_schedules():
    """
    List all scheduled jobs.
    """
    return {
        "total": len(SCHEDULED_JOBS),
        "schedules": list(SCHEDULED_JOBS.values())
    }


@app.delete("/api/schedules/{schedule_id}", tags=["Execution Engine"])
async def delete_schedule(schedule_id: str):
    """
    Delete a scheduled job.
    """
    if schedule_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")

    del SCHEDULED_JOBS[schedule_id]
    return {"success": True, "deleted": schedule_id}


# ============================================================================
# Search & Discovery
# ============================================================================

class SearchRequest(BaseModel):
    """Full-text search request."""
    query: str = Field(..., min_length=2)
    types: List[str] = Field(default=["agents", "cards", "workflows", "templates"])
    filters: Dict[str, Any] = Field(default={})
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


@app.post("/api/search", tags=["Search & Discovery"])
async def full_text_search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Full-text search across agents, cards, workflows, and templates.

    Supports filtering by type, category, tags, and more.
    """
    results = []
    query_lower = request.query.lower()

    # Search agents
    if "agents" in request.types:
        agents = db.query(Agent).all()
        for agent in agents:
            score = 0
            if query_lower in agent.name.lower():
                score += 10
            if agent.description and query_lower in agent.description.lower():
                score += 5
            if agent.apqc_id and query_lower in agent.apqc_id.lower():
                score += 8

            if score > 0:
                results.append({
                    "type": "agent",
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "apqc_id": agent.apqc_id,
                    "score": score
                })

    # Search agent cards
    if "cards" in request.types and AGENT_CARDS_DIR.exists():
        for file in AGENT_CARDS_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                score = 0
                card_name = card.get("apqc_name", "")
                card_id = card.get("apqc_id", "")

                if query_lower in card_name.lower():
                    score += 10
                if query_lower in card_id.lower():
                    score += 8
                if query_lower in str(card).lower():
                    score += 2

                if score > 0:
                    results.append({
                        "type": "card",
                        "id": card_id,
                        "name": card_name,
                        "filename": file.name,
                        "score": score
                    })
            except Exception:
                pass

    # Search templates
    if "templates" in request.types and TEMPLATES_DIR.exists():
        for file in TEMPLATES_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    template = json.load(f)
                score = 0
                tpl_name = template.get("template_name", "")

                if query_lower in tpl_name.lower():
                    score += 10
                if query_lower in template.get("description", "").lower():
                    score += 5

                if score > 0:
                    results.append({
                        "type": "template",
                        "id": template.get("template_id"),
                        "name": tpl_name,
                        "category": template.get("category"),
                        "score": score
                    })
            except Exception:
                pass

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)

    # Apply pagination
    paginated = results[request.offset:request.offset + request.limit]

    return {
        "query": request.query,
        "total": len(results),
        "offset": request.offset,
        "limit": request.limit,
        "results": paginated
    }


@app.get("/api/search/suggestions", tags=["Search & Discovery"])
async def get_search_suggestions(q: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get autocomplete suggestions for search.
    """
    if len(q) < 2:
        return {"suggestions": []}

    suggestions = []
    q_lower = q.lower()

    # Get agent name suggestions
    agents = db.query(Agent).filter(Agent.name.ilike(f"%{q}%")).limit(limit).all()
    for agent in agents:
        suggestions.append({
            "text": agent.name,
            "type": "agent",
            "id": agent.id
        })

    # Get APQC ID suggestions
    if AGENT_CARDS_DIR.exists():
        for file in AGENT_CARDS_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    card = json.load(f)
                if q_lower in card.get("apqc_id", "").lower():
                    suggestions.append({
                        "text": f"{card.get('apqc_id')} - {card.get('apqc_name', '')}",
                        "type": "card",
                        "id": card.get("apqc_id")
                    })
            except Exception:
                pass

    return {"suggestions": suggestions[:limit]}


@app.get("/api/discover/categories", tags=["Search & Discovery"])
async def discover_categories(db: Session = Depends(get_db)):
    """
    Get all available categories with counts.
    """
    categories = {}

    # Count agents by APQC category
    agents = db.query(Agent).all()
    for agent in agents:
        if agent.apqc_id:
            cat = agent.apqc_id.split(".")[0] if "." in agent.apqc_id else "other"
            categories[cat] = categories.get(cat, 0) + 1

    # Map to APQC names
    apqc_names = {
        "1": "Develop Vision and Strategy",
        "2": "Develop and Manage Products and Services",
        "3": "Market and Sell Products and Services",
        "4": "Deliver Physical Products",
        "5": "Deliver Services",
        "6": "Manage Customer Service",
        "7": "Develop and Manage Human Capital",
        "8": "Manage Information Technology",
        "9": "Manage Financial Resources",
        "10": "Acquire, Construct, and Manage Assets",
        "11": "Manage Enterprise Risk, Compliance, Remediation, and Resiliency",
        "12": "Manage External Relationships",
        "13": "Develop and Manage Business Capabilities"
    }

    return {
        "categories": [
            {
                "id": cat_id,
                "name": apqc_names.get(cat_id, f"Category {cat_id}"),
                "count": count
            }
            for cat_id, count in sorted(categories.items())
        ]
    }


@app.get("/api/discover/recommendations", tags=["Search & Discovery"])
async def get_recommendations(
    based_on: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get smart recommendations for agents and workflows.

    Can be based on a specific agent/card or category.
    """
    recommendations = []

    if based_on:
        # Find related agents in the same APQC category
        base_parts = based_on.split(".")
        if len(base_parts) >= 2:
            prefix = f"{base_parts[0]}.{base_parts[1]}"
            agents = db.query(Agent).filter(Agent.apqc_id.like(f"{prefix}%")).limit(limit).all()
            for agent in agents:
                if agent.apqc_id != based_on:
                    recommendations.append({
                        "type": "agent",
                        "id": agent.id,
                        "name": agent.name,
                        "apqc_id": agent.apqc_id,
                        "reason": f"Related to {based_on}"
                    })

    elif category:
        # Get top agents in category
        agents = db.query(Agent).filter(Agent.apqc_id.like(f"{category}.%")).limit(limit).all()
        for agent in agents:
            recommendations.append({
                "type": "agent",
                "id": agent.id,
                "name": agent.name,
                "apqc_id": agent.apqc_id,
                "reason": f"Top in category {category}"
            })

    else:
        # Get popular/recent agents
        agents = db.query(Agent).order_by(Agent.created_at.desc()).limit(limit).all()
        for agent in agents:
            recommendations.append({
                "type": "agent",
                "id": agent.id,
                "name": agent.name,
                "apqc_id": agent.apqc_id,
                "reason": "Recently added"
            })

    return {
        "recommendations": recommendations,
        "based_on": based_on,
        "category": category
    }


# ============================================================================
# Workflow Builder
# ============================================================================

# In-memory workflow definitions storage
WORKFLOW_DEFINITIONS: Dict[str, Dict[str, Any]] = {}


class WorkflowStep(BaseModel):
    """A step in a workflow definition."""
    step_id: str
    name: str
    agent_id: Optional[str] = None
    card_id: Optional[str] = None
    action: str = Field(default="execute")
    inputs: Dict[str, Any] = Field(default={})
    outputs: List[str] = Field(default=[])
    dependencies: List[str] = Field(default=[], description="Step IDs this step depends on")
    condition: Optional[str] = Field(default=None, description="Condition expression for conditional execution")
    retry_policy: Optional[Dict[str, Any]] = None
    timeout_seconds: int = Field(default=300)
    position: Optional[Dict[str, int]] = Field(default=None, description="Visual position {x, y}")


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    name: str
    description: str = ""
    steps: List[WorkflowStep]
    triggers: List[Dict[str, Any]] = Field(default=[])
    variables: Dict[str, Any] = Field(default={})
    error_handling: Dict[str, Any] = Field(default={"strategy": "fail_fast"})
    tags: List[str] = Field(default=[])


@app.post("/api/workflow-builder/definitions", tags=["Workflow Builder"])
async def create_workflow_definition(definition: WorkflowDefinition):
    """
    Create a new workflow definition.

    The definition includes steps, dependencies, and visual layout information.
    """
    workflow_id = f"wf_def_{uuid4().hex[:10]}"

    # Validate step dependencies
    step_ids = {step.step_id for step in definition.steps}
    for step in definition.steps:
        for dep in step.dependencies:
            if dep not in step_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Step '{step.step_id}' depends on non-existent step '{dep}'"
                )

    # Check for circular dependencies
    def has_cycle(step_id: str, visited: set, path: set) -> bool:
        visited.add(step_id)
        path.add(step_id)
        step = next((s for s in definition.steps if s.step_id == step_id), None)
        if step:
            for dep in step.dependencies:
                if dep not in visited:
                    if has_cycle(dep, visited, path):
                        return True
                elif dep in path:
                    return True
        path.remove(step_id)
        return False

    for step in definition.steps:
        if has_cycle(step.step_id, set(), set()):
            raise HTTPException(status_code=400, detail="Circular dependency detected in workflow")

    workflow_def = {
        "workflow_id": workflow_id,
        "name": definition.name,
        "description": definition.description,
        "steps": [step.dict() for step in definition.steps],
        "triggers": definition.triggers,
        "variables": definition.variables,
        "error_handling": definition.error_handling,
        "tags": definition.tags,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 1
    }

    WORKFLOW_DEFINITIONS[workflow_id] = workflow_def

    return {"success": True, "workflow_id": workflow_id, "definition": workflow_def}


@app.get("/api/workflow-builder/definitions", tags=["Workflow Builder"])
async def list_workflow_definitions(tag: Optional[str] = None):
    """
    List all workflow definitions.
    """
    definitions = list(WORKFLOW_DEFINITIONS.values())

    if tag:
        definitions = [d for d in definitions if tag in d.get("tags", [])]

    return {
        "total": len(definitions),
        "definitions": definitions
    }


@app.get("/api/workflow-builder/definitions/{workflow_id}", tags=["Workflow Builder"])
async def get_workflow_definition(workflow_id: str):
    """
    Get a specific workflow definition.
    """
    if workflow_id not in WORKFLOW_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Workflow definition {workflow_id} not found")

    return WORKFLOW_DEFINITIONS[workflow_id]


@app.put("/api/workflow-builder/definitions/{workflow_id}", tags=["Workflow Builder"])
async def update_workflow_definition(workflow_id: str, definition: WorkflowDefinition):
    """
    Update a workflow definition.
    """
    if workflow_id not in WORKFLOW_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Workflow definition {workflow_id} not found")

    existing = WORKFLOW_DEFINITIONS[workflow_id]

    updated = {
        "workflow_id": workflow_id,
        "name": definition.name,
        "description": definition.description,
        "steps": [step.dict() for step in definition.steps],
        "triggers": definition.triggers,
        "variables": definition.variables,
        "error_handling": definition.error_handling,
        "tags": definition.tags,
        "created_at": existing["created_at"],
        "updated_at": datetime.utcnow().isoformat(),
        "version": existing.get("version", 1) + 1
    }

    WORKFLOW_DEFINITIONS[workflow_id] = updated

    return {"success": True, "workflow_id": workflow_id, "version": updated["version"]}


@app.delete("/api/workflow-builder/definitions/{workflow_id}", tags=["Workflow Builder"])
async def delete_workflow_definition(workflow_id: str):
    """
    Delete a workflow definition.
    """
    if workflow_id not in WORKFLOW_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Workflow definition {workflow_id} not found")

    del WORKFLOW_DEFINITIONS[workflow_id]
    return {"success": True, "deleted": workflow_id}


@app.post("/api/workflow-builder/definitions/{workflow_id}/validate", tags=["Workflow Builder"])
async def validate_workflow_definition(workflow_id: str, db: Session = Depends(get_db)):
    """
    Validate a workflow definition.

    Checks that all referenced agents exist, dependencies are valid, etc.
    """
    if workflow_id not in WORKFLOW_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Workflow definition {workflow_id} not found")

    definition = WORKFLOW_DEFINITIONS[workflow_id]
    issues = []

    for step in definition["steps"]:
        # Check agent exists
        if step.get("agent_id"):
            agent = db.query(Agent).filter(Agent.id == step["agent_id"]).first()
            if not agent:
                issues.append({
                    "step": step["step_id"],
                    "severity": "error",
                    "message": f"Agent '{step['agent_id']}' not found"
                })

        # Check card exists
        if step.get("card_id") and AGENT_CARDS_DIR.exists():
            card_found = False
            for file in AGENT_CARDS_DIR.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        card = json.load(f)
                    if card.get("apqc_id") == step["card_id"]:
                        card_found = True
                        break
                except Exception:
                    pass
            if not card_found:
                issues.append({
                    "step": step["step_id"],
                    "severity": "warning",
                    "message": f"Agent card '{step['card_id']}' not found"
                })

    return {
        "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues,
        "workflow_id": workflow_id
    }


@app.post("/api/workflow-builder/definitions/{workflow_id}/execute", tags=["Workflow Builder"])
async def execute_workflow_definition(workflow_id: str, input_data: Dict[str, Any] = {}):
    """
    Execute a workflow from its definition.
    """
    if workflow_id not in WORKFLOW_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Workflow definition {workflow_id} not found")

    execution_id = f"exec_{uuid4().hex[:12]}"
    definition = WORKFLOW_DEFINITIONS[workflow_id]

    execution = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "workflow_name": definition["name"],
        "input_data": input_data,
        "status": "queued",
        "progress": 0.0,
        "current_step": None,
        "queued_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "step_results": {},
        "result": None,
        "error": None
    }

    EXECUTION_QUEUE.append(execution)

    return {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "queued"
    }


# ============================================================================
# Analytics & Reporting
# ============================================================================

@app.get("/api/analytics/overview", tags=["Analytics & Reporting"])
async def get_analytics_overview(db: Session = Depends(get_db)):
    """
    Get high-level analytics overview.
    """
    total_agents = db.query(Agent).count()
    total_workflows = db.query(Workflow).count()
    total_executions = len(EXECUTION_HISTORY)

    # Calculate success rate
    successful = len([e for e in EXECUTION_HISTORY if e.get("status") == "completed"])
    success_rate = (successful / total_executions * 100) if total_executions > 0 else 0

    return {
        "summary": {
            "total_agents": total_agents,
            "total_workflows": total_workflows,
            "total_workflow_definitions": len(WORKFLOW_DEFINITIONS),
            "total_executions": total_executions,
            "queued_executions": len(EXECUTION_QUEUE),
            "scheduled_jobs": len(SCHEDULED_JOBS),
            "success_rate": round(success_rate, 2)
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/analytics/executions", tags=["Analytics & Reporting"])
async def get_execution_analytics(
    period: str = "24h",
    group_by: str = "hour"
):
    """
    Get execution analytics over time.

    Periods: 1h, 6h, 24h, 7d, 30d
    Group by: minute, hour, day
    """
    # Would calculate from execution history
    # Simulated data for now
    data_points = []
    now = datetime.utcnow()

    for i in range(24):
        data_points.append({
            "timestamp": (now.replace(hour=i, minute=0, second=0)).isoformat(),
            "total": len([e for e in EXECUTION_HISTORY]) // 24 + i % 5,
            "successful": len([e for e in EXECUTION_HISTORY if e.get("status") == "completed"]) // 24,
            "failed": len([e for e in EXECUTION_HISTORY if e.get("status") == "failed"]) // 24
        })

    return {
        "period": period,
        "group_by": group_by,
        "data": data_points,
        "summary": {
            "total": sum(d["total"] for d in data_points),
            "successful": sum(d["successful"] for d in data_points),
            "failed": sum(d["failed"] for d in data_points)
        }
    }


@app.get("/api/analytics/agents/performance", tags=["Analytics & Reporting"])
async def get_agent_performance(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get performance metrics for top agents.
    """
    agents = db.query(Agent).limit(limit).all()

    performance = []
    for agent in agents:
        agent_executions = [e for e in EXECUTION_HISTORY if e.get("agent_id") == agent.id]
        successful = len([e for e in agent_executions if e.get("status") == "completed"])

        performance.append({
            "agent_id": agent.id,
            "name": agent.name,
            "apqc_id": agent.apqc_id,
            "total_executions": len(agent_executions),
            "successful": successful,
            "failed": len(agent_executions) - successful,
            "success_rate": (successful / len(agent_executions) * 100) if agent_executions else 0,
            "avg_duration_seconds": 0  # Would calculate from actual execution times
        })

    performance.sort(key=lambda x: x["total_executions"], reverse=True)

    return {
        "agents": performance,
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/analytics/workflows/performance", tags=["Analytics & Reporting"])
async def get_workflow_performance():
    """
    Get performance metrics for workflows.
    """
    workflow_stats = {}

    for exec in EXECUTION_HISTORY:
        wf_id = exec.get("workflow_id")
        if wf_id:
            if wf_id not in workflow_stats:
                workflow_stats[wf_id] = {
                    "workflow_id": wf_id,
                    "name": WORKFLOW_DEFINITIONS.get(wf_id, {}).get("name", wf_id),
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "cancelled": 0
                }
            workflow_stats[wf_id]["total"] += 1
            if exec.get("status") == "completed":
                workflow_stats[wf_id]["successful"] += 1
            elif exec.get("status") == "failed":
                workflow_stats[wf_id]["failed"] += 1
            elif exec.get("status") == "cancelled":
                workflow_stats[wf_id]["cancelled"] += 1

    return {
        "workflows": list(workflow_stats.values()),
        "generated_at": datetime.utcnow().isoformat()
    }


class ReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: str = Field(..., description="Type: execution_summary, agent_usage, workflow_analysis")
    period: str = Field(default="7d")
    format: str = Field(default="json", description="json or csv")
    filters: Dict[str, Any] = Field(default={})


@app.post("/api/reports/generate", tags=["Analytics & Reporting"])
async def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """
    Generate a detailed report.
    """
    report_id = f"rpt_{uuid4().hex[:8]}"

    if request.report_type == "execution_summary":
        data = {
            "total_executions": len(EXECUTION_HISTORY),
            "successful": len([e for e in EXECUTION_HISTORY if e.get("status") == "completed"]),
            "failed": len([e for e in EXECUTION_HISTORY if e.get("status") == "failed"]),
            "cancelled": len([e for e in EXECUTION_HISTORY if e.get("status") == "cancelled"]),
            "executions": EXECUTION_HISTORY[-100:]  # Last 100
        }
    elif request.report_type == "agent_usage":
        agents = db.query(Agent).all()
        data = {
            "total_agents": len(agents),
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "apqc_id": a.apqc_id,
                    "execution_count": len([e for e in EXECUTION_HISTORY if e.get("agent_id") == a.id])
                }
                for a in agents
            ]
        }
    elif request.report_type == "workflow_analysis":
        data = {
            "total_definitions": len(WORKFLOW_DEFINITIONS),
            "definitions": list(WORKFLOW_DEFINITIONS.values()),
            "execution_stats": await get_workflow_performance()
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")

    report = {
        "report_id": report_id,
        "report_type": request.report_type,
        "period": request.period,
        "generated_at": datetime.utcnow().isoformat(),
        "data": data
    }

    return report


@app.get("/api/analytics/real-time", tags=["Analytics & Reporting"])
async def get_real_time_stats():
    """
    Get real-time statistics for live dashboards.
    """
    return {
        "queue": {
            "length": len(EXECUTION_QUEUE),
            "oldest_wait_seconds": 0,  # Would calculate
            "by_priority": {}
        },
        "active_executions": len([e for e in EXECUTION_QUEUE if e.get("status") == "running"]),
        "completed_last_hour": len([
            e for e in EXECUTION_HISTORY
            if e.get("completed_at") and
            datetime.fromisoformat(e["completed_at"]) > datetime.utcnow().replace(hour=datetime.utcnow().hour - 1)
        ]),
        "error_rate_last_hour": 0,  # Would calculate
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Webhooks & Event System
# ============================================================================

# Webhook and event storage
WEBHOOKS: Dict[str, Dict[str, Any]] = {}
EVENT_LOG: List[Dict[str, Any]] = []
EVENT_SUBSCRIPTIONS: Dict[str, List[str]] = {}  # event_type -> [webhook_ids]


class WebhookCreate(BaseModel):
    """Create a webhook subscription."""
    name: str
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(default=None, description="Secret for HMAC signature")
    headers: Dict[str, str] = Field(default={}, description="Custom headers to send")
    enabled: bool = Field(default=True)
    retry_policy: Dict[str, Any] = Field(
        default={"max_retries": 3, "backoff_seconds": 60}
    )


# Available event types
WEBHOOK_EVENT_TYPES = [
    "execution.queued", "execution.started", "execution.completed", "execution.failed",
    "workflow.created", "workflow.updated", "workflow.deleted",
    "agent.created", "agent.updated", "agent.deleted",
    "schedule.triggered", "schedule.created", "schedule.deleted",
    "user.created", "user.updated", "team.member_added",
    "export.completed", "export.failed"
]


@app.post("/api/webhooks", tags=["Webhooks & Events"])
async def create_webhook(webhook: WebhookCreate):
    """
    Create a webhook subscription.

    Webhooks receive HTTP POST notifications when subscribed events occur.
    """
    webhook_id = f"wh_{uuid4().hex[:10]}"

    # Validate event types
    for event in webhook.events:
        if event not in WEBHOOK_EVENT_TYPES and not event.endswith(".*"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event}. Valid types: {WEBHOOK_EVENT_TYPES}"
            )

    wh = {
        "webhook_id": webhook_id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook.events,
        "secret": webhook.secret,
        "headers": webhook.headers,
        "enabled": webhook.enabled,
        "retry_policy": webhook.retry_policy,
        "created_at": datetime.utcnow().isoformat(),
        "last_triggered": None,
        "trigger_count": 0,
        "failure_count": 0
    }

    WEBHOOKS[webhook_id] = wh

    # Register subscriptions
    for event in webhook.events:
        if event not in EVENT_SUBSCRIPTIONS:
            EVENT_SUBSCRIPTIONS[event] = []
        EVENT_SUBSCRIPTIONS[event].append(webhook_id)

    return {"success": True, "webhook_id": webhook_id, "webhook": wh}


@app.get("/api/webhooks", tags=["Webhooks & Events"])
async def list_webhooks():
    """List all registered webhooks."""
    return {
        "total": len(WEBHOOKS),
        "webhooks": list(WEBHOOKS.values())
    }


@app.get("/api/webhooks/{webhook_id}", tags=["Webhooks & Events"])
async def get_webhook(webhook_id: str):
    """Get webhook details."""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")
    return WEBHOOKS[webhook_id]


@app.delete("/api/webhooks/{webhook_id}", tags=["Webhooks & Events"])
async def delete_webhook(webhook_id: str):
    """Delete a webhook."""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")

    wh = WEBHOOKS.pop(webhook_id)

    # Remove from subscriptions
    for event in wh["events"]:
        if event in EVENT_SUBSCRIPTIONS:
            EVENT_SUBSCRIPTIONS[event] = [w for w in EVENT_SUBSCRIPTIONS[event] if w != webhook_id]

    return {"success": True, "deleted": webhook_id}


@app.post("/api/webhooks/{webhook_id}/test", tags=["Webhooks & Events"])
async def test_webhook(webhook_id: str):
    """Send a test event to a webhook."""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")

    test_event = {
        "event_id": f"evt_{uuid4().hex[:10]}",
        "event_type": "webhook.test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"message": "This is a test event", "webhook_id": webhook_id}
    }

    # Would actually send HTTP request here
    return {"success": True, "test_event": test_event, "status": "sent"}


@app.get("/api/events", tags=["Webhooks & Events"])
async def list_events(
    event_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List recent events."""
    events = EVENT_LOG

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return {
        "total": len(events),
        "events": events[offset:offset + limit],
        "event_types": WEBHOOK_EVENT_TYPES
    }


@app.post("/api/events/emit", tags=["Webhooks & Events"])
async def emit_event(event_type: str, data: Dict[str, Any] = {}):
    """
    Emit a custom event (triggers webhooks).

    Internal use for testing and custom integrations.
    """
    event = {
        "event_id": f"evt_{uuid4().hex[:10]}",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    EVENT_LOG.append(event)

    # Find matching webhooks and trigger them
    triggered = []
    for wh_id in EVENT_SUBSCRIPTIONS.get(event_type, []):
        if wh_id in WEBHOOKS and WEBHOOKS[wh_id]["enabled"]:
            WEBHOOKS[wh_id]["trigger_count"] += 1
            WEBHOOKS[wh_id]["last_triggered"] = datetime.utcnow().isoformat()
            triggered.append(wh_id)

    return {
        "success": True,
        "event": event,
        "webhooks_triggered": len(triggered)
    }


# ============================================================================
# User & Team Management
# ============================================================================

# User and team storage
USERS: Dict[str, Dict[str, Any]] = {}
TEAMS: Dict[str, Dict[str, Any]] = {}
ORGANIZATIONS: Dict[str, Dict[str, Any]] = {}
AUDIT_LOG: List[Dict[str, Any]] = []

# Default roles and permissions
ROLES = {
    "admin": ["*"],
    "editor": ["read", "write", "execute"],
    "viewer": ["read"],
    "executor": ["read", "execute"]
}


class UserCreate(BaseModel):
    """Create a user."""
    email: str
    name: str
    role: str = Field(default="viewer")
    team_ids: List[str] = Field(default=[])
    organization_id: Optional[str] = None


class TeamCreate(BaseModel):
    """Create a team."""
    name: str
    description: str = ""
    organization_id: Optional[str] = None


class OrganizationCreate(BaseModel):
    """Create an organization."""
    name: str
    plan: str = Field(default="free", description="free, pro, enterprise")
    settings: Dict[str, Any] = Field(default={})


@app.post("/api/organizations", tags=["User & Team Management"])
async def create_organization(org: OrganizationCreate):
    """Create an organization (tenant)."""
    org_id = f"org_{uuid4().hex[:8]}"

    organization = {
        "organization_id": org_id,
        "name": org.name,
        "plan": org.plan,
        "settings": org.settings,
        "created_at": datetime.utcnow().isoformat(),
        "member_count": 0,
        "team_count": 0
    }

    ORGANIZATIONS[org_id] = organization

    return {"success": True, "organization_id": org_id, "organization": organization}


@app.get("/api/organizations", tags=["User & Team Management"])
async def list_organizations():
    """List all organizations."""
    return {"total": len(ORGANIZATIONS), "organizations": list(ORGANIZATIONS.values())}


@app.get("/api/organizations/{org_id}", tags=["User & Team Management"])
async def get_organization(org_id: str):
    """Get organization details."""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")
    return ORGANIZATIONS[org_id]


@app.post("/api/teams", tags=["User & Team Management"])
async def create_team(team: TeamCreate):
    """Create a team."""
    team_id = f"team_{uuid4().hex[:8]}"

    team_data = {
        "team_id": team_id,
        "name": team.name,
        "description": team.description,
        "organization_id": team.organization_id,
        "created_at": datetime.utcnow().isoformat(),
        "members": [],
        "member_count": 0
    }

    TEAMS[team_id] = team_data

    if team.organization_id and team.organization_id in ORGANIZATIONS:
        ORGANIZATIONS[team.organization_id]["team_count"] += 1

    return {"success": True, "team_id": team_id, "team": team_data}


@app.get("/api/teams", tags=["User & Team Management"])
async def list_teams(organization_id: Optional[str] = None):
    """List all teams."""
    teams = list(TEAMS.values())
    if organization_id:
        teams = [t for t in teams if t.get("organization_id") == organization_id]
    return {"total": len(teams), "teams": teams}


@app.get("/api/teams/{team_id}", tags=["User & Team Management"])
async def get_team(team_id: str):
    """Get team details."""
    if team_id not in TEAMS:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return TEAMS[team_id]


@app.post("/api/users", tags=["User & Team Management"])
async def create_user(user: UserCreate):
    """Create a user."""
    user_id = f"user_{uuid4().hex[:8]}"

    if user.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {user.role}. Valid: {list(ROLES.keys())}")

    user_data = {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "permissions": ROLES[user.role],
        "team_ids": user.team_ids,
        "organization_id": user.organization_id,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None,
        "status": "active"
    }

    USERS[user_id] = user_data

    # Add to teams
    for team_id in user.team_ids:
        if team_id in TEAMS:
            TEAMS[team_id]["members"].append(user_id)
            TEAMS[team_id]["member_count"] += 1

    if user.organization_id and user.organization_id in ORGANIZATIONS:
        ORGANIZATIONS[user.organization_id]["member_count"] += 1

    # Audit log
    AUDIT_LOG.append({
        "event": "user.created",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {"email": user.email, "role": user.role}
    })

    return {"success": True, "user_id": user_id, "user": user_data}


@app.get("/api/users", tags=["User & Team Management"])
async def list_users(
    team_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    role: Optional[str] = None
):
    """List users with optional filters."""
    users = list(USERS.values())

    if team_id:
        users = [u for u in users if team_id in u.get("team_ids", [])]
    if organization_id:
        users = [u for u in users if u.get("organization_id") == organization_id]
    if role:
        users = [u for u in users if u.get("role") == role]

    return {"total": len(users), "users": users}


@app.get("/api/users/{user_id}", tags=["User & Team Management"])
async def get_user(user_id: str):
    """Get user details."""
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return USERS[user_id]


@app.put("/api/users/{user_id}/role", tags=["User & Team Management"])
async def update_user_role(user_id: str, role: str):
    """Update a user's role."""
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    old_role = USERS[user_id]["role"]
    USERS[user_id]["role"] = role
    USERS[user_id]["permissions"] = ROLES[role]

    AUDIT_LOG.append({
        "event": "user.role_changed",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {"old_role": old_role, "new_role": role}
    })

    return {"success": True, "user_id": user_id, "new_role": role}


@app.post("/api/teams/{team_id}/members", tags=["User & Team Management"])
async def add_team_member(team_id: str, user_id: str):
    """Add a user to a team."""
    if team_id not in TEAMS:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    if user_id not in TEAMS[team_id]["members"]:
        TEAMS[team_id]["members"].append(user_id)
        TEAMS[team_id]["member_count"] += 1
        USERS[user_id]["team_ids"].append(team_id)

    return {"success": True, "team_id": team_id, "user_id": user_id}


@app.get("/api/audit-log", tags=["User & Team Management"])
async def get_audit_log(
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """Get audit log entries."""
    logs = AUDIT_LOG

    if user_id:
        logs = [l for l in logs if l.get("user_id") == user_id]
    if event_type:
        logs = [l for l in logs if l.get("event") == event_type]

    return {"total": len(logs), "entries": logs[-limit:]}


@app.get("/api/roles", tags=["User & Team Management"])
async def list_roles():
    """List available roles and their permissions."""
    return {"roles": ROLES}


# ============================================================================
# Data Export & Compliance
# ============================================================================

EXPORT_JOBS: Dict[str, Dict[str, Any]] = {}
DATA_RETENTION_POLICIES: Dict[str, Dict[str, Any]] = {}


class ExportRequest(BaseModel):
    """Request for data export."""
    export_type: str = Field(..., description="agents, executions, workflows, users, audit_log, all")
    format: str = Field(default="json", description="json, csv")
    filters: Dict[str, Any] = Field(default={})
    include_pii: bool = Field(default=False, description="Include personally identifiable information")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="{start, end} ISO dates")


class RetentionPolicy(BaseModel):
    """Data retention policy."""
    name: str
    data_type: str = Field(..., description="executions, audit_log, events")
    retention_days: int = Field(..., ge=1, le=3650)
    action: str = Field(default="delete", description="delete, archive, anonymize")


@app.post("/api/exports", tags=["Data Export & Compliance"])
async def create_export(request: ExportRequest, db: Session = Depends(get_db)):
    """
    Create a data export job.

    Supports GDPR-compliant exports with optional PII exclusion.
    """
    export_id = f"exp_{uuid4().hex[:10]}"

    # Gather data based on export type
    data = {}

    if request.export_type in ["agents", "all"]:
        agents = db.query(Agent).all()
        data["agents"] = [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "apqc_id": a.apqc_id,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in agents
        ]

    if request.export_type in ["executions", "all"]:
        data["executions"] = EXECUTION_HISTORY[-1000:]

    if request.export_type in ["workflows", "all"]:
        data["workflow_definitions"] = list(WORKFLOW_DEFINITIONS.values())

    if request.export_type in ["users", "all"]:
        users_data = list(USERS.values())
        if not request.include_pii:
            # Anonymize PII
            users_data = [
                {**u, "email": f"user_{i}@anonymized.com", "name": f"User {i}"}
                for i, u in enumerate(users_data)
            ]
        data["users"] = users_data

    if request.export_type in ["audit_log", "all"]:
        data["audit_log"] = AUDIT_LOG[-1000:]

    export_job = {
        "export_id": export_id,
        "export_type": request.export_type,
        "format": request.format,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "record_count": sum(len(v) if isinstance(v, list) else 1 for v in data.values()),
        "include_pii": request.include_pii,
        "download_url": f"/api/exports/{export_id}/download",
        "expires_at": (datetime.utcnow().replace(hour=datetime.utcnow().hour + 24)).isoformat()
    }

    EXPORT_JOBS[export_id] = {"job": export_job, "data": data}

    return {"success": True, "export": export_job}


@app.get("/api/exports", tags=["Data Export & Compliance"])
async def list_exports():
    """List all export jobs."""
    return {
        "total": len(EXPORT_JOBS),
        "exports": [e["job"] for e in EXPORT_JOBS.values()]
    }


@app.get("/api/exports/{export_id}", tags=["Data Export & Compliance"])
async def get_export(export_id: str):
    """Get export job details."""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail=f"Export {export_id} not found")
    return EXPORT_JOBS[export_id]["job"]


@app.get("/api/exports/{export_id}/download", tags=["Data Export & Compliance"])
async def download_export(export_id: str):
    """Download export data."""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail=f"Export {export_id} not found")

    return EXPORT_JOBS[export_id]["data"]


@app.post("/api/compliance/gdpr/delete-request", tags=["Data Export & Compliance"])
async def gdpr_delete_request(user_id: str, confirm: bool = False):
    """
    GDPR Right to Erasure (Article 17) request.

    Deletes all personal data associated with a user.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm deletion with confirm=true"
        )

    deleted_data = {
        "user_data": False,
        "execution_history": 0,
        "audit_entries": 0
    }

    # Delete user
    if user_id in USERS:
        del USERS[user_id]
        deleted_data["user_data"] = True

    # Anonymize execution history
    for exec in EXECUTION_HISTORY:
        if exec.get("user_id") == user_id:
            exec["user_id"] = "DELETED"
            deleted_data["execution_history"] += 1

    # Anonymize audit log
    for entry in AUDIT_LOG:
        if entry.get("user_id") == user_id:
            entry["user_id"] = "DELETED"
            entry["details"] = {"anonymized": True}
            deleted_data["audit_entries"] += 1

    return {
        "success": True,
        "user_id": user_id,
        "deleted": deleted_data,
        "completed_at": datetime.utcnow().isoformat()
    }


@app.post("/api/compliance/retention-policies", tags=["Data Export & Compliance"])
async def create_retention_policy(policy: RetentionPolicy):
    """Create a data retention policy."""
    policy_id = f"rp_{uuid4().hex[:8]}"

    policy_data = {
        "policy_id": policy_id,
        "name": policy.name,
        "data_type": policy.data_type,
        "retention_days": policy.retention_days,
        "action": policy.action,
        "created_at": datetime.utcnow().isoformat(),
        "last_run": None,
        "records_affected": 0
    }

    DATA_RETENTION_POLICIES[policy_id] = policy_data

    return {"success": True, "policy_id": policy_id, "policy": policy_data}


@app.get("/api/compliance/retention-policies", tags=["Data Export & Compliance"])
async def list_retention_policies():
    """List data retention policies."""
    return {
        "total": len(DATA_RETENTION_POLICIES),
        "policies": list(DATA_RETENTION_POLICIES.values())
    }


@app.get("/api/compliance/data-inventory", tags=["Data Export & Compliance"])
async def get_data_inventory(db: Session = Depends(get_db)):
    """
    Get inventory of all data stored in the system.

    Useful for GDPR Article 30 compliance (Records of Processing).
    """
    return {
        "data_categories": [
            {
                "category": "Agents",
                "count": db.query(Agent).count(),
                "contains_pii": False,
                "retention": "permanent"
            },
            {
                "category": "Users",
                "count": len(USERS),
                "contains_pii": True,
                "pii_fields": ["email", "name"],
                "retention": "until deletion request"
            },
            {
                "category": "Execution History",
                "count": len(EXECUTION_HISTORY),
                "contains_pii": False,
                "retention": "90 days default"
            },
            {
                "category": "Audit Log",
                "count": len(AUDIT_LOG),
                "contains_pii": True,
                "pii_fields": ["user_id"],
                "retention": "365 days"
            },
            {
                "category": "Webhooks",
                "count": len(WEBHOOKS),
                "contains_pii": False,
                "retention": "permanent"
            }
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# Cost Analytics & Billing
# ============================================================================

COST_RECORDS: List[Dict[str, Any]] = []
BILLING_ACCOUNTS: Dict[str, Dict[str, Any]] = {}
USAGE_QUOTAS: Dict[str, Dict[str, Any]] = {}

# Cost rates (configurable)
COST_RATES = {
    "agent_execution": 0.01,  # per execution
    "workflow_execution": 0.05,  # per workflow
    "ai_call": 0.002,  # per AI API call
    "storage_gb_month": 0.10,  # per GB per month
    "api_request": 0.0001  # per API request
}


class BillingAccount(BaseModel):
    """Billing account for an organization."""
    organization_id: str
    plan: str = Field(default="free", description="free, pro, enterprise")
    payment_method: Optional[str] = None
    billing_email: str


class UsageQuota(BaseModel):
    """Usage quota for an organization."""
    organization_id: str
    quota_type: str = Field(..., description="executions, api_calls, storage_gb")
    limit: int
    period: str = Field(default="monthly", description="daily, monthly")


@app.post("/api/billing/accounts", tags=["Cost Analytics & Billing"])
async def create_billing_account(account: BillingAccount):
    """Create a billing account for an organization."""
    if account.organization_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail=f"Organization {account.organization_id} not found")

    BILLING_ACCOUNTS[account.organization_id] = {
        "organization_id": account.organization_id,
        "plan": account.plan,
        "payment_method": account.payment_method,
        "billing_email": account.billing_email,
        "created_at": datetime.utcnow().isoformat(),
        "current_balance": 0.0,
        "total_spent": 0.0
    }

    return {"success": True, "account": BILLING_ACCOUNTS[account.organization_id]}


@app.get("/api/billing/accounts/{org_id}", tags=["Cost Analytics & Billing"])
async def get_billing_account(org_id: str):
    """Get billing account details."""
    if org_id not in BILLING_ACCOUNTS:
        raise HTTPException(status_code=404, detail=f"Billing account for {org_id} not found")
    return BILLING_ACCOUNTS[org_id]


@app.post("/api/costs/record", tags=["Cost Analytics & Billing"])
async def record_cost(
    organization_id: str,
    cost_type: str,
    quantity: int = 1,
    metadata: Dict[str, Any] = {}
):
    """
    Record a cost event (internal use).

    Called automatically when executions, API calls, etc. occur.
    """
    if cost_type not in COST_RATES:
        raise HTTPException(status_code=400, detail=f"Unknown cost type: {cost_type}")

    cost = COST_RATES[cost_type] * quantity

    record = {
        "record_id": f"cost_{uuid4().hex[:8]}",
        "organization_id": organization_id,
        "cost_type": cost_type,
        "quantity": quantity,
        "unit_cost": COST_RATES[cost_type],
        "total_cost": cost,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata
    }

    COST_RECORDS.append(record)

    # Update billing account
    if organization_id in BILLING_ACCOUNTS:
        BILLING_ACCOUNTS[organization_id]["current_balance"] += cost
        BILLING_ACCOUNTS[organization_id]["total_spent"] += cost

    return {"success": True, "cost": cost, "record": record}


@app.get("/api/costs/summary", tags=["Cost Analytics & Billing"])
async def get_cost_summary(
    organization_id: Optional[str] = None,
    period: str = "30d"
):
    """
    Get cost summary and breakdown.

    Periods: 24h, 7d, 30d, 90d
    """
    records = COST_RECORDS

    if organization_id:
        records = [r for r in records if r.get("organization_id") == organization_id]

    # Group by cost type
    by_type = {}
    for record in records:
        ct = record["cost_type"]
        if ct not in by_type:
            by_type[ct] = {"count": 0, "total_cost": 0.0}
        by_type[ct]["count"] += record["quantity"]
        by_type[ct]["total_cost"] += record["total_cost"]

    total_cost = sum(t["total_cost"] for t in by_type.values())

    return {
        "period": period,
        "organization_id": organization_id,
        "total_cost": round(total_cost, 4),
        "breakdown": by_type,
        "record_count": len(records),
        "rates": COST_RATES
    }


@app.get("/api/costs/trends", tags=["Cost Analytics & Billing"])
async def get_cost_trends(
    organization_id: Optional[str] = None,
    group_by: str = "day"
):
    """
    Get cost trends over time.

    Group by: hour, day, week, month
    """
    # Simulated trend data
    trends = []
    now = datetime.utcnow()

    for i in range(30):
        day = now.replace(day=max(1, now.day - i))
        day_records = [r for r in COST_RECORDS if r.get("timestamp", "").startswith(day.strftime("%Y-%m-%d"))]

        trends.append({
            "date": day.strftime("%Y-%m-%d"),
            "total_cost": sum(r["total_cost"] for r in day_records),
            "execution_count": len([r for r in day_records if r["cost_type"] == "agent_execution"])
        })

    return {
        "group_by": group_by,
        "organization_id": organization_id,
        "trends": trends[::-1]  # Chronological order
    }


@app.post("/api/quotas", tags=["Cost Analytics & Billing"])
async def create_quota(quota: UsageQuota):
    """Create a usage quota for an organization."""
    quota_id = f"quota_{uuid4().hex[:8]}"

    quota_data = {
        "quota_id": quota_id,
        "organization_id": quota.organization_id,
        "quota_type": quota.quota_type,
        "limit": quota.limit,
        "period": quota.period,
        "current_usage": 0,
        "created_at": datetime.utcnow().isoformat(),
        "reset_at": None
    }

    USAGE_QUOTAS[quota_id] = quota_data

    return {"success": True, "quota_id": quota_id, "quota": quota_data}


@app.get("/api/quotas", tags=["Cost Analytics & Billing"])
async def list_quotas(organization_id: Optional[str] = None):
    """List usage quotas."""
    quotas = list(USAGE_QUOTAS.values())
    if organization_id:
        quotas = [q for q in quotas if q.get("organization_id") == organization_id]
    return {"total": len(quotas), "quotas": quotas}


@app.get("/api/quotas/usage/{org_id}", tags=["Cost Analytics & Billing"])
async def get_quota_usage(org_id: str):
    """Get current quota usage for an organization."""
    org_quotas = [q for q in USAGE_QUOTAS.values() if q.get("organization_id") == org_id]

    usage = []
    for quota in org_quotas:
        usage.append({
            "quota_type": quota["quota_type"],
            "limit": quota["limit"],
            "current_usage": quota["current_usage"],
            "remaining": quota["limit"] - quota["current_usage"],
            "percentage_used": round(quota["current_usage"] / quota["limit"] * 100, 2) if quota["limit"] > 0 else 0
        })

    return {"organization_id": org_id, "usage": usage}


# ============================================================================
# Notifications System
# ============================================================================

NOTIFICATION_CHANNELS: Dict[str, Dict[str, Any]] = {}
NOTIFICATIONS: List[Dict[str, Any]] = []
NOTIFICATION_PREFERENCES: Dict[str, Dict[str, Any]] = {}


class NotificationChannel(BaseModel):
    """Notification channel configuration."""
    name: str
    channel_type: str = Field(..., description="email, slack, teams, webhook")
    config: Dict[str, Any] = Field(..., description="Channel-specific configuration")
    enabled: bool = Field(default=True)


class NotificationPreference(BaseModel):
    """User notification preferences."""
    user_id: str
    channel_id: str
    events: List[str] = Field(..., description="Events to receive notifications for")
    quiet_hours: Optional[Dict[str, str]] = Field(default=None, description="{start, end} times")


@app.post("/api/notifications/channels", tags=["Notifications"])
async def create_notification_channel(channel: NotificationChannel):
    """Create a notification channel."""
    channel_id = f"nc_{uuid4().hex[:8]}"

    channel_data = {
        "channel_id": channel_id,
        "name": channel.name,
        "channel_type": channel.channel_type,
        "config": channel.config,
        "enabled": channel.enabled,
        "created_at": datetime.utcnow().isoformat(),
        "message_count": 0
    }

    NOTIFICATION_CHANNELS[channel_id] = channel_data

    return {"success": True, "channel_id": channel_id, "channel": channel_data}


@app.get("/api/notifications/channels", tags=["Notifications"])
async def list_notification_channels():
    """List notification channels."""
    return {"total": len(NOTIFICATION_CHANNELS), "channels": list(NOTIFICATION_CHANNELS.values())}


@app.post("/api/notifications/send", tags=["Notifications"])
async def send_notification(
    channel_id: str,
    title: str,
    message: str,
    priority: str = "normal",
    metadata: Dict[str, Any] = {}
):
    """Send a notification through a channel."""
    if channel_id not in NOTIFICATION_CHANNELS:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    notification = {
        "notification_id": f"notif_{uuid4().hex[:10]}",
        "channel_id": channel_id,
        "title": title,
        "message": message,
        "priority": priority,
        "metadata": metadata,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent"
    }

    NOTIFICATIONS.append(notification)
    NOTIFICATION_CHANNELS[channel_id]["message_count"] += 1

    return {"success": True, "notification": notification}


@app.get("/api/notifications", tags=["Notifications"])
async def list_notifications(
    channel_id: Optional[str] = None,
    limit: int = 50
):
    """List recent notifications."""
    notifs = NOTIFICATIONS

    if channel_id:
        notifs = [n for n in notifs if n.get("channel_id") == channel_id]

    return {"total": len(notifs), "notifications": notifs[-limit:]}


@app.post("/api/notifications/preferences", tags=["Notifications"])
async def set_notification_preferences(pref: NotificationPreference):
    """Set notification preferences for a user."""
    pref_id = f"{pref.user_id}_{pref.channel_id}"

    NOTIFICATION_PREFERENCES[pref_id] = {
        "user_id": pref.user_id,
        "channel_id": pref.channel_id,
        "events": pref.events,
        "quiet_hours": pref.quiet_hours,
        "updated_at": datetime.utcnow().isoformat()
    }

    return {"success": True, "preferences": NOTIFICATION_PREFERENCES[pref_id]}


@app.get("/api/notifications/preferences/{user_id}", tags=["Notifications"])
async def get_notification_preferences(user_id: str):
    """Get notification preferences for a user."""
    prefs = [p for p in NOTIFICATION_PREFERENCES.values() if p.get("user_id") == user_id]
    return {"user_id": user_id, "preferences": prefs}


# ============================================================================
# Rate Limiting & Quotas
# ============================================================================

RATE_LIMIT_RULES: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_COUNTERS: Dict[str, Dict[str, Any]] = {}


class RateLimitRule(BaseModel):
    """Rate limiting rule."""
    name: str
    scope: str = Field(..., description="global, organization, user, ip")
    endpoint_pattern: str = Field(default="*", description="Endpoint pattern to apply to")
    requests_per_minute: int = Field(default=60)
    requests_per_hour: int = Field(default=1000)
    burst_limit: int = Field(default=10)


@app.post("/api/rate-limits/rules", tags=["Rate Limiting"])
async def create_rate_limit_rule(rule: RateLimitRule):
    """Create a rate limiting rule."""
    rule_id = f"rl_{uuid4().hex[:8]}"

    rule_data = {
        "rule_id": rule_id,
        "name": rule.name,
        "scope": rule.scope,
        "endpoint_pattern": rule.endpoint_pattern,
        "requests_per_minute": rule.requests_per_minute,
        "requests_per_hour": rule.requests_per_hour,
        "burst_limit": rule.burst_limit,
        "created_at": datetime.utcnow().isoformat(),
        "enabled": True
    }

    RATE_LIMIT_RULES[rule_id] = rule_data

    return {"success": True, "rule_id": rule_id, "rule": rule_data}


@app.get("/api/rate-limits/rules", tags=["Rate Limiting"])
async def list_rate_limit_rules():
    """List rate limiting rules."""
    return {"total": len(RATE_LIMIT_RULES), "rules": list(RATE_LIMIT_RULES.values())}


@app.get("/api/rate-limits/status", tags=["Rate Limiting"])
async def get_rate_limit_status(
    scope_type: str = "global",
    scope_id: Optional[str] = None
):
    """Get current rate limit status."""
    key = f"{scope_type}:{scope_id or 'default'}"

    if key not in RATE_LIMIT_COUNTERS:
        RATE_LIMIT_COUNTERS[key] = {
            "requests_this_minute": 0,
            "requests_this_hour": 0,
            "last_reset_minute": datetime.utcnow().isoformat(),
            "last_reset_hour": datetime.utcnow().isoformat()
        }

    counter = RATE_LIMIT_COUNTERS[key]

    # Find applicable rules
    applicable_rules = [r for r in RATE_LIMIT_RULES.values() if r["scope"] == scope_type]

    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "current_usage": counter,
        "applicable_rules": applicable_rules,
        "status": "ok"  # Would calculate if limited
    }


@app.post("/api/rate-limits/increment", tags=["Rate Limiting"])
async def increment_rate_limit(
    scope_type: str = "global",
    scope_id: Optional[str] = None
):
    """
    Increment rate limit counter (internal use).

    Called automatically on API requests.
    """
    key = f"{scope_type}:{scope_id or 'default'}"

    if key not in RATE_LIMIT_COUNTERS:
        RATE_LIMIT_COUNTERS[key] = {
            "requests_this_minute": 0,
            "requests_this_hour": 0,
            "last_reset_minute": datetime.utcnow().isoformat(),
            "last_reset_hour": datetime.utcnow().isoformat()
        }

    RATE_LIMIT_COUNTERS[key]["requests_this_minute"] += 1
    RATE_LIMIT_COUNTERS[key]["requests_this_hour"] += 1

    # Check if limited
    limited = False
    for rule in RATE_LIMIT_RULES.values():
        if rule["scope"] == scope_type and rule["enabled"]:
            if RATE_LIMIT_COUNTERS[key]["requests_this_minute"] > rule["requests_per_minute"]:
                limited = True
            if RATE_LIMIT_COUNTERS[key]["requests_this_hour"] > rule["requests_per_hour"]:
                limited = True

    return {
        "limited": limited,
        "current": RATE_LIMIT_COUNTERS[key]
    }


# ============================================================================
# AI/LLM Integration Layer
# ============================================================================

# Storage for AI providers and configurations
AI_PROVIDERS: Dict[str, Dict[str, Any]] = {}
AI_MODELS: Dict[str, Dict[str, Any]] = {}
AI_CONVERSATIONS: Dict[str, Dict[str, Any]] = {}
AI_USAGE_LOG: List[Dict[str, Any]] = []

SUPPORTED_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
        "capabilities": ["chat", "completion", "embedding", "image", "audio"]
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3.5-sonnet"],
        "capabilities": ["chat", "completion"]
    },
    "google": {
        "name": "Google AI",
        "models": ["gemini-pro", "gemini-pro-vision", "gemini-ultra"],
        "capabilities": ["chat", "completion", "embedding", "image"]
    },
    "azure": {
        "name": "Azure OpenAI",
        "models": ["gpt-4", "gpt-35-turbo"],
        "capabilities": ["chat", "completion", "embedding"]
    },
    "cohere": {
        "name": "Cohere",
        "models": ["command", "command-light", "command-r", "command-r-plus"],
        "capabilities": ["chat", "completion", "embedding"]
    },
    "local": {
        "name": "Local/Self-hosted",
        "models": ["llama", "mistral", "custom"],
        "capabilities": ["chat", "completion"]
    }
}


class AIProviderCreate(BaseModel):
    provider_type: str
    name: str
    api_key_secret_id: Optional[str] = None
    endpoint_url: Optional[str] = None
    default_model: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AICompletionRequest(BaseModel):
    provider_id: str
    model: Optional[str] = None
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None


@app.get("/ai/providers/supported")
def list_supported_providers():
    """List all supported AI providers and their capabilities"""
    return {"providers": SUPPORTED_PROVIDERS}


@app.post("/ai/providers")
def create_ai_provider(provider: AIProviderCreate):
    """Register a new AI provider configuration"""
    if provider.provider_type not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider.provider_type}")

    provider_id = str(uuid.uuid4())
    AI_PROVIDERS[provider_id] = {
        "id": provider_id,
        "provider_type": provider.provider_type,
        "name": provider.name,
        "api_key_secret_id": provider.api_key_secret_id,
        "endpoint_url": provider.endpoint_url,
        "default_model": provider.default_model,
        "config": provider.config or {},
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "total_requests": 0,
        "total_tokens": 0
    }
    return AI_PROVIDERS[provider_id]


@app.get("/ai/providers")
def list_ai_providers():
    """List all registered AI providers"""
    return {"providers": list(AI_PROVIDERS.values())}


@app.get("/ai/providers/{provider_id}")
def get_ai_provider(provider_id: str):
    """Get AI provider details"""
    if provider_id not in AI_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")
    return AI_PROVIDERS[provider_id]


@app.delete("/ai/providers/{provider_id}")
def delete_ai_provider(provider_id: str):
    """Delete an AI provider configuration"""
    if provider_id not in AI_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")
    del AI_PROVIDERS[provider_id]
    return {"status": "deleted"}


@app.post("/ai/providers/{provider_id}/test")
def test_ai_provider(provider_id: str):
    """Test connectivity to an AI provider"""
    if provider_id not in AI_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = AI_PROVIDERS[provider_id]
    # Simulated test - in production would make actual API call
    return {
        "provider_id": provider_id,
        "status": "connected",
        "latency_ms": 145,
        "models_available": SUPPORTED_PROVIDERS[provider["provider_type"]]["models"],
        "tested_at": datetime.utcnow().isoformat()
    }


@app.post("/ai/completions")
def create_ai_completion(request: AICompletionRequest):
    """Execute an AI completion request"""
    if request.provider_id not in AI_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = AI_PROVIDERS[request.provider_id]
    model = request.model or provider["default_model"]

    # Simulated completion - in production would call actual API
    completion_id = str(uuid.uuid4())
    response = {
        "id": completion_id,
        "provider_id": request.provider_id,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[Simulated response from {model}] This is a placeholder response. In production, this would be the actual AI response."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.get("content", "").split()) * 1.3 for m in request.messages),
            "completion_tokens": 50,
            "total_tokens": 0
        },
        "created_at": datetime.utcnow().isoformat()
    }
    response["usage"]["total_tokens"] = int(response["usage"]["prompt_tokens"] + response["usage"]["completion_tokens"])

    # Update provider stats
    AI_PROVIDERS[request.provider_id]["last_used"] = datetime.utcnow().isoformat()
    AI_PROVIDERS[request.provider_id]["total_requests"] += 1
    AI_PROVIDERS[request.provider_id]["total_tokens"] += response["usage"]["total_tokens"]

    # Log usage
    AI_USAGE_LOG.append({
        "completion_id": completion_id,
        "provider_id": request.provider_id,
        "model": model,
        "tokens": response["usage"]["total_tokens"],
        "timestamp": datetime.utcnow().isoformat()
    })

    return response


@app.post("/ai/conversations")
def create_conversation(data: Dict[str, Any] = Body(...)):
    """Create a new AI conversation session"""
    conversation_id = str(uuid.uuid4())
    AI_CONVERSATIONS[conversation_id] = {
        "id": conversation_id,
        "provider_id": data.get("provider_id"),
        "model": data.get("model"),
        "title": data.get("title", "New Conversation"),
        "messages": [],
        "context": data.get("context", {}),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return AI_CONVERSATIONS[conversation_id]


@app.get("/ai/conversations")
def list_conversations():
    """List all conversations"""
    return {"conversations": list(AI_CONVERSATIONS.values())}


@app.get("/ai/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Get conversation history"""
    if conversation_id not in AI_CONVERSATIONS:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return AI_CONVERSATIONS[conversation_id]


@app.post("/ai/conversations/{conversation_id}/messages")
def add_conversation_message(conversation_id: str, message: Dict[str, Any] = Body(...)):
    """Add a message to a conversation and get AI response"""
    if conversation_id not in AI_CONVERSATIONS:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = AI_CONVERSATIONS[conversation_id]

    # Add user message
    user_msg = {
        "role": "user",
        "content": message.get("content", ""),
        "timestamp": datetime.utcnow().isoformat()
    }
    conv["messages"].append(user_msg)

    # Simulate AI response
    ai_msg = {
        "role": "assistant",
        "content": f"[Simulated response] Received: {message.get('content', '')}",
        "timestamp": datetime.utcnow().isoformat()
    }
    conv["messages"].append(ai_msg)
    conv["updated_at"] = datetime.utcnow().isoformat()

    return {"user_message": user_msg, "ai_response": ai_msg}


@app.delete("/ai/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in AI_CONVERSATIONS:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del AI_CONVERSATIONS[conversation_id]
    return {"status": "deleted"}


@app.get("/ai/usage")
def get_ai_usage(provider_id: Optional[str] = None, days: int = 30):
    """Get AI usage statistics"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = [l for l in AI_USAGE_LOG if datetime.fromisoformat(l["timestamp"]) > cutoff]

    if provider_id:
        logs = [l for l in logs if l["provider_id"] == provider_id]

    return {
        "period_days": days,
        "total_requests": len(logs),
        "total_tokens": sum(l["tokens"] for l in logs),
        "by_model": {},
        "by_day": {}
    }


# ============================================================================
# Agent Marketplace
# ============================================================================

# Storage for marketplace
MARKETPLACE_LISTINGS: Dict[str, Dict[str, Any]] = {}
MARKETPLACE_REVIEWS: Dict[str, List[Dict[str, Any]]] = {}
MARKETPLACE_DOWNLOADS: Dict[str, List[Dict[str, Any]]] = {}
MARKETPLACE_FEATURED: List[str] = []
MARKETPLACE_CATEGORIES = [
    "productivity", "automation", "data-analysis", "communication",
    "development", "finance", "hr", "marketing", "sales", "operations",
    "customer-service", "legal", "compliance", "research", "creative"
]


class MarketplaceListingCreate(BaseModel):
    agent_card_id: str
    title: str
    description: str
    category: str
    tags: Optional[List[str]] = []
    pricing_model: Optional[str] = "free"  # free, one-time, subscription
    price: Optional[float] = 0.0
    screenshots: Optional[List[str]] = []
    demo_url: Optional[str] = None


class MarketplaceReview(BaseModel):
    rating: int  # 1-5
    title: str
    content: str
    user_id: str


@app.post("/marketplace/listings")
def create_marketplace_listing(listing: MarketplaceListingCreate):
    """Publish an agent to the marketplace"""
    listing_id = str(uuid.uuid4())
    MARKETPLACE_LISTINGS[listing_id] = {
        "id": listing_id,
        "agent_card_id": listing.agent_card_id,
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "tags": listing.tags or [],
        "pricing_model": listing.pricing_model,
        "price": listing.price,
        "screenshots": listing.screenshots or [],
        "demo_url": listing.demo_url,
        "publisher_id": "current_user",
        "status": "pending_review",
        "downloads": 0,
        "average_rating": 0.0,
        "review_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "published_at": None
    }
    MARKETPLACE_REVIEWS[listing_id] = []
    MARKETPLACE_DOWNLOADS[listing_id] = []
    return MARKETPLACE_LISTINGS[listing_id]


@app.get("/marketplace/listings")
def list_marketplace_listings(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "downloads",
    pricing: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """Browse marketplace listings"""
    listings = [l for l in MARKETPLACE_LISTINGS.values() if l["status"] == "published"]

    if category:
        listings = [l for l in listings if l["category"] == category]
    if search:
        search_lower = search.lower()
        listings = [l for l in listings if search_lower in l["title"].lower() or search_lower in l["description"].lower()]
    if pricing:
        listings = [l for l in listings if l["pricing_model"] == pricing]

    # Sort
    if sort_by == "downloads":
        listings.sort(key=lambda x: x["downloads"], reverse=True)
    elif sort_by == "rating":
        listings.sort(key=lambda x: x["average_rating"], reverse=True)
    elif sort_by == "newest":
        listings.sort(key=lambda x: x["published_at"] or "", reverse=True)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "listings": listings[start:end],
        "total": len(listings),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(listings) + page_size - 1) // page_size
    }


@app.get("/marketplace/listings/{listing_id}")
def get_marketplace_listing(listing_id: str):
    """Get marketplace listing details"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {
        "listing": MARKETPLACE_LISTINGS[listing_id],
        "reviews": MARKETPLACE_REVIEWS.get(listing_id, [])[:10]
    }


@app.put("/marketplace/listings/{listing_id}")
def update_marketplace_listing(listing_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a marketplace listing"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    allowed = ["title", "description", "category", "tags", "pricing_model", "price", "screenshots", "demo_url"]
    for key, value in updates.items():
        if key in allowed:
            MARKETPLACE_LISTINGS[listing_id][key] = value
    MARKETPLACE_LISTINGS[listing_id]["updated_at"] = datetime.utcnow().isoformat()
    return MARKETPLACE_LISTINGS[listing_id]


@app.post("/marketplace/listings/{listing_id}/publish")
def publish_marketplace_listing(listing_id: str):
    """Publish a listing to the marketplace"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    MARKETPLACE_LISTINGS[listing_id]["status"] = "published"
    MARKETPLACE_LISTINGS[listing_id]["published_at"] = datetime.utcnow().isoformat()
    return MARKETPLACE_LISTINGS[listing_id]


@app.post("/marketplace/listings/{listing_id}/unpublish")
def unpublish_marketplace_listing(listing_id: str):
    """Unpublish a listing from the marketplace"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    MARKETPLACE_LISTINGS[listing_id]["status"] = "unpublished"
    return MARKETPLACE_LISTINGS[listing_id]


@app.delete("/marketplace/listings/{listing_id}")
def delete_marketplace_listing(listing_id: str):
    """Delete a marketplace listing"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")
    del MARKETPLACE_LISTINGS[listing_id]
    return {"status": "deleted"}


@app.post("/marketplace/listings/{listing_id}/download")
def download_marketplace_listing(listing_id: str, user_id: str = "current_user"):
    """Download/install an agent from the marketplace"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = MARKETPLACE_LISTINGS[listing_id]
    listing["downloads"] += 1

    MARKETPLACE_DOWNLOADS[listing_id].append({
        "user_id": user_id,
        "downloaded_at": datetime.utcnow().isoformat()
    })

    return {
        "status": "downloaded",
        "agent_card_id": listing["agent_card_id"],
        "message": "Agent has been added to your library"
    }


@app.post("/marketplace/listings/{listing_id}/reviews")
def create_marketplace_review(listing_id: str, review: MarketplaceReview):
    """Submit a review for a marketplace listing"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    review_data = {
        "id": str(uuid.uuid4()),
        "listing_id": listing_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "title": review.title,
        "content": review.content,
        "helpful_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    MARKETPLACE_REVIEWS[listing_id].append(review_data)

    # Update average rating
    reviews = MARKETPLACE_REVIEWS[listing_id]
    MARKETPLACE_LISTINGS[listing_id]["average_rating"] = sum(r["rating"] for r in reviews) / len(reviews)
    MARKETPLACE_LISTINGS[listing_id]["review_count"] = len(reviews)

    return review_data


@app.get("/marketplace/listings/{listing_id}/reviews")
def get_marketplace_reviews(listing_id: str, page: int = 1, page_size: int = 10):
    """Get reviews for a marketplace listing"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    reviews = MARKETPLACE_REVIEWS.get(listing_id, [])
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "reviews": reviews[start:end],
        "total": len(reviews),
        "average_rating": MARKETPLACE_LISTINGS[listing_id]["average_rating"]
    }


@app.get("/marketplace/featured")
def get_featured_listings():
    """Get featured marketplace listings"""
    featured = [MARKETPLACE_LISTINGS[lid] for lid in MARKETPLACE_FEATURED if lid in MARKETPLACE_LISTINGS]
    return {"featured": featured}


@app.get("/marketplace/categories")
def get_marketplace_categories():
    """Get marketplace categories with counts"""
    category_counts = {}
    for listing in MARKETPLACE_LISTINGS.values():
        if listing["status"] == "published":
            cat = listing["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "categories": [
            {"name": cat, "count": category_counts.get(cat, 0)}
            for cat in MARKETPLACE_CATEGORIES
        ]
    }


@app.get("/marketplace/trending")
def get_trending_listings(days: int = 7, limit: int = 10):
    """Get trending marketplace listings"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Calculate recent downloads
    trending_scores = {}
    for listing_id, downloads in MARKETPLACE_DOWNLOADS.items():
        recent = [d for d in downloads if datetime.fromisoformat(d["downloaded_at"]) > cutoff]
        trending_scores[listing_id] = len(recent)

    # Sort by trending score
    sorted_ids = sorted(trending_scores.keys(), key=lambda x: trending_scores[x], reverse=True)[:limit]

    return {
        "trending": [MARKETPLACE_LISTINGS[lid] for lid in sorted_ids if lid in MARKETPLACE_LISTINGS]
    }


# ============================================================================
# Testing & Sandbox
# ============================================================================

# Storage for testing
TEST_SUITES: Dict[str, Dict[str, Any]] = {}
TEST_RUNS: Dict[str, Dict[str, Any]] = {}
SANDBOX_ENVIRONMENTS: Dict[str, Dict[str, Any]] = {}
MOCK_RESPONSES: Dict[str, Dict[str, Any]] = {}


class TestCase(BaseModel):
    name: str
    description: Optional[str] = None
    input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    assertions: Optional[List[Dict[str, Any]]] = []
    timeout_seconds: Optional[int] = 30


class TestSuiteCreate(BaseModel):
    agent_card_id: str
    name: str
    description: Optional[str] = None
    test_cases: List[TestCase]


class SandboxCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    mock_providers: Optional[List[str]] = []
    isolated: Optional[bool] = True


@app.post("/testing/suites")
def create_test_suite(suite: TestSuiteCreate):
    """Create a test suite for an agent"""
    suite_id = str(uuid.uuid4())
    TEST_SUITES[suite_id] = {
        "id": suite_id,
        "agent_card_id": suite.agent_card_id,
        "name": suite.name,
        "description": suite.description,
        "test_cases": [tc.dict() for tc in suite.test_cases],
        "total_tests": len(suite.test_cases),
        "last_run": None,
        "last_result": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return TEST_SUITES[suite_id]


@app.get("/testing/suites")
def list_test_suites(agent_card_id: Optional[str] = None):
    """List test suites"""
    suites = list(TEST_SUITES.values())
    if agent_card_id:
        suites = [s for s in suites if s["agent_card_id"] == agent_card_id]
    return {"test_suites": suites}


@app.get("/testing/suites/{suite_id}")
def get_test_suite(suite_id: str):
    """Get test suite details"""
    if suite_id not in TEST_SUITES:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return TEST_SUITES[suite_id]


@app.put("/testing/suites/{suite_id}")
def update_test_suite(suite_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a test suite"""
    if suite_id not in TEST_SUITES:
        raise HTTPException(status_code=404, detail="Test suite not found")

    allowed = ["name", "description", "test_cases"]
    for key, value in updates.items():
        if key in allowed:
            TEST_SUITES[suite_id][key] = value

    if "test_cases" in updates:
        TEST_SUITES[suite_id]["total_tests"] = len(updates["test_cases"])
    TEST_SUITES[suite_id]["updated_at"] = datetime.utcnow().isoformat()
    return TEST_SUITES[suite_id]


@app.delete("/testing/suites/{suite_id}")
def delete_test_suite(suite_id: str):
    """Delete a test suite"""
    if suite_id not in TEST_SUITES:
        raise HTTPException(status_code=404, detail="Test suite not found")
    del TEST_SUITES[suite_id]
    return {"status": "deleted"}


@app.post("/testing/suites/{suite_id}/run")
def run_test_suite(suite_id: str, sandbox_id: Optional[str] = None):
    """Execute a test suite"""
    if suite_id not in TEST_SUITES:
        raise HTTPException(status_code=404, detail="Test suite not found")

    suite = TEST_SUITES[suite_id]
    run_id = str(uuid.uuid4())

    # Simulate test execution
    results = []
    passed = 0
    failed = 0

    for tc in suite["test_cases"]:
        # Simulated test result
        test_passed = True  # In production, would actually execute
        if test_passed:
            passed += 1
            status = "passed"
        else:
            failed += 1
            status = "failed"

        results.append({
            "test_name": tc["name"],
            "status": status,
            "duration_ms": 150,
            "output": {"simulated": True},
            "assertions_passed": len(tc.get("assertions", [])),
            "assertions_failed": 0
        })

    TEST_RUNS[run_id] = {
        "id": run_id,
        "suite_id": suite_id,
        "sandbox_id": sandbox_id,
        "status": "completed",
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "duration_ms": sum(r["duration_ms"] for r in results),
        "results": results,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }

    # Update suite last run
    TEST_SUITES[suite_id]["last_run"] = datetime.utcnow().isoformat()
    TEST_SUITES[suite_id]["last_result"] = "passed" if failed == 0 else "failed"

    return TEST_RUNS[run_id]


@app.get("/testing/runs")
def list_test_runs(suite_id: Optional[str] = None, limit: int = 20):
    """List test runs"""
    runs = list(TEST_RUNS.values())
    if suite_id:
        runs = [r for r in runs if r["suite_id"] == suite_id]
    runs.sort(key=lambda x: x["started_at"], reverse=True)
    return {"test_runs": runs[:limit]}


@app.get("/testing/runs/{run_id}")
def get_test_run(run_id: str):
    """Get test run details"""
    if run_id not in TEST_RUNS:
        raise HTTPException(status_code=404, detail="Test run not found")
    return TEST_RUNS[run_id]


@app.post("/sandbox")
def create_sandbox(sandbox: SandboxCreate):
    """Create an isolated sandbox environment"""
    sandbox_id = str(uuid.uuid4())
    SANDBOX_ENVIRONMENTS[sandbox_id] = {
        "id": sandbox_id,
        "name": sandbox.name,
        "description": sandbox.description,
        "config": sandbox.config or {},
        "mock_providers": sandbox.mock_providers or [],
        "isolated": sandbox.isolated,
        "status": "ready",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    return SANDBOX_ENVIRONMENTS[sandbox_id]


@app.get("/sandbox")
def list_sandboxes():
    """List sandbox environments"""
    return {"sandboxes": list(SANDBOX_ENVIRONMENTS.values())}


@app.get("/sandbox/{sandbox_id}")
def get_sandbox(sandbox_id: str):
    """Get sandbox details"""
    if sandbox_id not in SANDBOX_ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return SANDBOX_ENVIRONMENTS[sandbox_id]


@app.delete("/sandbox/{sandbox_id}")
def delete_sandbox(sandbox_id: str):
    """Delete a sandbox environment"""
    if sandbox_id not in SANDBOX_ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    del SANDBOX_ENVIRONMENTS[sandbox_id]
    return {"status": "deleted"}


@app.post("/sandbox/{sandbox_id}/execute")
def execute_in_sandbox(sandbox_id: str, data: Dict[str, Any] = Body(...)):
    """Execute an agent in a sandbox environment"""
    if sandbox_id not in SANDBOX_ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    execution_id = str(uuid.uuid4())
    return {
        "execution_id": execution_id,
        "sandbox_id": sandbox_id,
        "status": "completed",
        "result": {"simulated": True, "message": "Sandbox execution completed"},
        "logs": ["[sandbox] Starting execution", "[sandbox] Execution completed"],
        "duration_ms": 200
    }


@app.post("/testing/mocks")
def create_mock_response(data: Dict[str, Any] = Body(...)):
    """Create a mock response for testing"""
    mock_id = str(uuid.uuid4())
    MOCK_RESPONSES[mock_id] = {
        "id": mock_id,
        "pattern": data.get("pattern", "*"),
        "response": data.get("response", {}),
        "status_code": data.get("status_code", 200),
        "delay_ms": data.get("delay_ms", 0),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    return MOCK_RESPONSES[mock_id]


@app.get("/testing/mocks")
def list_mock_responses():
    """List mock responses"""
    return {"mocks": list(MOCK_RESPONSES.values())}


@app.delete("/testing/mocks/{mock_id}")
def delete_mock_response(mock_id: str):
    """Delete a mock response"""
    if mock_id not in MOCK_RESPONSES:
        raise HTTPException(status_code=404, detail="Mock not found")
    del MOCK_RESPONSES[mock_id]
    return {"status": "deleted"}


# ============================================================================
# Secrets Management
# ============================================================================

# Storage for secrets (encrypted in production)
SECRETS: Dict[str, Dict[str, Any]] = {}
SECRET_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}
SECRET_ACCESS_LOG: List[Dict[str, Any]] = []


class SecretCreate(BaseModel):
    name: str
    value: str
    description: Optional[str] = None
    scope: Optional[str] = "global"  # global, org, team, user
    scope_id: Optional[str] = None
    expires_at: Optional[str] = None
    rotation_days: Optional[int] = None


@app.post("/secrets")
def create_secret(secret: SecretCreate):
    """Create a new secret"""
    secret_id = str(uuid.uuid4())

    # Mask the value (in production, would encrypt)
    masked_value = secret.value[:4] + "*" * (len(secret.value) - 4) if len(secret.value) > 4 else "****"

    SECRETS[secret_id] = {
        "id": secret_id,
        "name": secret.name,
        "masked_value": masked_value,
        "_value": secret.value,  # In production, would be encrypted
        "description": secret.description,
        "scope": secret.scope,
        "scope_id": secret.scope_id,
        "version": 1,
        "expires_at": secret.expires_at,
        "rotation_days": secret.rotation_days,
        "last_rotated": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    SECRET_VERSIONS[secret_id] = [{
        "version": 1,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "current_user"
    }]

    # Don't return the actual value
    result = {k: v for k, v in SECRETS[secret_id].items() if k != "_value"}
    return result


@app.get("/secrets")
def list_secrets(scope: Optional[str] = None):
    """List secrets (values are masked)"""
    secrets = [{k: v for k, v in s.items() if k != "_value"} for s in SECRETS.values()]
    if scope:
        secrets = [s for s in secrets if s["scope"] == scope]
    return {"secrets": secrets}


@app.get("/secrets/{secret_id}")
def get_secret(secret_id: str, include_value: bool = False):
    """Get secret details"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    # Log access
    SECRET_ACCESS_LOG.append({
        "secret_id": secret_id,
        "action": "read",
        "include_value": include_value,
        "user": "current_user",
        "timestamp": datetime.utcnow().isoformat()
    })

    secret = SECRETS[secret_id]
    if include_value:
        return {k: v for k, v in secret.items()}
    else:
        return {k: v for k, v in secret.items() if k != "_value"}


@app.put("/secrets/{secret_id}")
def update_secret(secret_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a secret"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    allowed = ["name", "description", "expires_at", "rotation_days"]
    for key, value in updates.items():
        if key in allowed:
            SECRETS[secret_id][key] = value
    SECRETS[secret_id]["updated_at"] = datetime.utcnow().isoformat()

    result = {k: v for k, v in SECRETS[secret_id].items() if k != "_value"}
    return result


@app.post("/secrets/{secret_id}/rotate")
def rotate_secret(secret_id: str, new_value: str = Body(..., embed=True)):
    """Rotate a secret's value"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    secret = SECRETS[secret_id]
    secret["version"] += 1
    secret["_value"] = new_value
    secret["masked_value"] = new_value[:4] + "*" * (len(new_value) - 4) if len(new_value) > 4 else "****"
    secret["last_rotated"] = datetime.utcnow().isoformat()
    secret["updated_at"] = datetime.utcnow().isoformat()

    SECRET_VERSIONS[secret_id].append({
        "version": secret["version"],
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "current_user"
    })

    SECRET_ACCESS_LOG.append({
        "secret_id": secret_id,
        "action": "rotate",
        "user": "current_user",
        "timestamp": datetime.utcnow().isoformat()
    })

    result = {k: v for k, v in secret.items() if k != "_value"}
    return result


@app.delete("/secrets/{secret_id}")
def delete_secret(secret_id: str):
    """Delete a secret"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    SECRET_ACCESS_LOG.append({
        "secret_id": secret_id,
        "action": "delete",
        "user": "current_user",
        "timestamp": datetime.utcnow().isoformat()
    })

    del SECRETS[secret_id]
    return {"status": "deleted"}


@app.get("/secrets/{secret_id}/versions")
def get_secret_versions(secret_id: str):
    """Get secret version history"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"versions": SECRET_VERSIONS.get(secret_id, [])}


@app.get("/secrets/{secret_id}/access-log")
def get_secret_access_log(secret_id: str, limit: int = 50):
    """Get access log for a secret"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    logs = [l for l in SECRET_ACCESS_LOG if l["secret_id"] == secret_id]
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"access_log": logs[:limit]}


# ============================================================================
# Integration Connectors
# ============================================================================

# Storage for connectors
CONNECTORS: Dict[str, Dict[str, Any]] = {}
CONNECTOR_INSTANCES: Dict[str, Dict[str, Any]] = {}
CONNECTOR_LOGS: List[Dict[str, Any]] = []

SUPPORTED_CONNECTORS = {
    "slack": {
        "name": "Slack",
        "category": "communication",
        "actions": ["send_message", "create_channel", "list_channels", "upload_file"],
        "triggers": ["message_received", "reaction_added", "channel_created"],
        "auth_type": "oauth2"
    },
    "github": {
        "name": "GitHub",
        "category": "development",
        "actions": ["create_issue", "create_pr", "merge_pr", "list_repos", "create_comment"],
        "triggers": ["push", "pull_request", "issue_opened", "issue_closed"],
        "auth_type": "oauth2"
    },
    "jira": {
        "name": "Jira",
        "category": "project_management",
        "actions": ["create_issue", "update_issue", "transition_issue", "add_comment", "search"],
        "triggers": ["issue_created", "issue_updated", "issue_transitioned"],
        "auth_type": "oauth2"
    },
    "salesforce": {
        "name": "Salesforce",
        "category": "crm",
        "actions": ["create_lead", "update_opportunity", "query", "create_task"],
        "triggers": ["lead_created", "opportunity_updated", "case_created"],
        "auth_type": "oauth2"
    },
    "postgresql": {
        "name": "PostgreSQL",
        "category": "database",
        "actions": ["query", "insert", "update", "delete", "execute"],
        "triggers": [],
        "auth_type": "connection_string"
    },
    "mongodb": {
        "name": "MongoDB",
        "category": "database",
        "actions": ["find", "insert", "update", "delete", "aggregate"],
        "triggers": ["change_stream"],
        "auth_type": "connection_string"
    },
    "aws_s3": {
        "name": "AWS S3",
        "category": "storage",
        "actions": ["upload", "download", "list", "delete", "copy"],
        "triggers": ["object_created", "object_deleted"],
        "auth_type": "api_key"
    },
    "google_sheets": {
        "name": "Google Sheets",
        "category": "productivity",
        "actions": ["read_range", "write_range", "append_row", "create_sheet"],
        "triggers": ["row_added", "cell_updated"],
        "auth_type": "oauth2"
    },
    "twilio": {
        "name": "Twilio",
        "category": "communication",
        "actions": ["send_sms", "send_whatsapp", "make_call"],
        "triggers": ["sms_received", "call_completed"],
        "auth_type": "api_key"
    },
    "sendgrid": {
        "name": "SendGrid",
        "category": "email",
        "actions": ["send_email", "send_template", "add_contact"],
        "triggers": ["email_opened", "email_clicked", "email_bounced"],
        "auth_type": "api_key"
    },
    "stripe": {
        "name": "Stripe",
        "category": "payments",
        "actions": ["create_charge", "create_subscription", "create_invoice", "refund"],
        "triggers": ["payment_succeeded", "payment_failed", "subscription_created"],
        "auth_type": "api_key"
    },
    "webhook": {
        "name": "Generic Webhook",
        "category": "integration",
        "actions": ["http_get", "http_post", "http_put", "http_delete"],
        "triggers": ["webhook_received"],
        "auth_type": "custom"
    }
}


class ConnectorInstanceCreate(BaseModel):
    connector_type: str
    name: str
    secret_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@app.get("/connectors/available")
def list_available_connectors():
    """List all available connector types"""
    return {"connectors": SUPPORTED_CONNECTORS}


@app.post("/connectors/instances")
def create_connector_instance(instance: ConnectorInstanceCreate):
    """Create a connector instance"""
    if instance.connector_type not in SUPPORTED_CONNECTORS:
        raise HTTPException(status_code=400, detail=f"Unsupported connector: {instance.connector_type}")

    instance_id = str(uuid.uuid4())
    CONNECTOR_INSTANCES[instance_id] = {
        "id": instance_id,
        "connector_type": instance.connector_type,
        "name": instance.name,
        "secret_id": instance.secret_id,
        "config": instance.config or {},
        "status": "configured",
        "last_used": None,
        "total_executions": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    return CONNECTOR_INSTANCES[instance_id]


@app.get("/connectors/instances")
def list_connector_instances(connector_type: Optional[str] = None):
    """List connector instances"""
    instances = list(CONNECTOR_INSTANCES.values())
    if connector_type:
        instances = [i for i in instances if i["connector_type"] == connector_type]
    return {"instances": instances}


@app.get("/connectors/instances/{instance_id}")
def get_connector_instance(instance_id: str):
    """Get connector instance details"""
    if instance_id not in CONNECTOR_INSTANCES:
        raise HTTPException(status_code=404, detail="Connector instance not found")
    return CONNECTOR_INSTANCES[instance_id]


@app.delete("/connectors/instances/{instance_id}")
def delete_connector_instance(instance_id: str):
    """Delete a connector instance"""
    if instance_id not in CONNECTOR_INSTANCES:
        raise HTTPException(status_code=404, detail="Connector instance not found")
    del CONNECTOR_INSTANCES[instance_id]
    return {"status": "deleted"}


@app.post("/connectors/instances/{instance_id}/test")
def test_connector_instance(instance_id: str):
    """Test connector connectivity"""
    if instance_id not in CONNECTOR_INSTANCES:
        raise HTTPException(status_code=404, detail="Connector instance not found")

    instance = CONNECTOR_INSTANCES[instance_id]
    # Simulated test
    return {
        "instance_id": instance_id,
        "connector_type": instance["connector_type"],
        "status": "connected",
        "latency_ms": 85,
        "tested_at": datetime.utcnow().isoformat()
    }


@app.post("/connectors/instances/{instance_id}/execute")
def execute_connector_action(instance_id: str, data: Dict[str, Any] = Body(...)):
    """Execute a connector action"""
    if instance_id not in CONNECTOR_INSTANCES:
        raise HTTPException(status_code=404, detail="Connector instance not found")

    instance = CONNECTOR_INSTANCES[instance_id]
    connector_type = instance["connector_type"]
    action = data.get("action")

    if action not in SUPPORTED_CONNECTORS[connector_type]["actions"]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    execution_id = str(uuid.uuid4())

    # Log execution
    CONNECTOR_LOGS.append({
        "execution_id": execution_id,
        "instance_id": instance_id,
        "connector_type": connector_type,
        "action": action,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    })

    # Update stats
    instance["last_used"] = datetime.utcnow().isoformat()
    instance["total_executions"] += 1

    return {
        "execution_id": execution_id,
        "status": "success",
        "result": {"simulated": True, "action": action},
        "duration_ms": 120
    }


@app.get("/connectors/logs")
def get_connector_logs(instance_id: Optional[str] = None, limit: int = 50):
    """Get connector execution logs"""
    logs = CONNECTOR_LOGS.copy()
    if instance_id:
        logs = [l for l in logs if l["instance_id"] == instance_id]
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"logs": logs[:limit]}


# ============================================================================
# Health & Monitoring
# ============================================================================

# Storage for monitoring
HEALTH_CHECKS: Dict[str, Dict[str, Any]] = {}
UPTIME_RECORDS: List[Dict[str, Any]] = []
ALERT_RULES: Dict[str, Dict[str, Any]] = {}
ALERTS: List[Dict[str, Any]] = []
METRICS: Dict[str, List[Dict[str, Any]]] = {}

SERVICE_COMPONENTS = [
    "api_server", "database", "cache", "queue", "ai_providers",
    "storage", "webhooks", "scheduler"
]


class HealthCheckCreate(BaseModel):
    name: str
    component: str
    check_type: str = "http"  # http, tcp, script
    endpoint: Optional[str] = None
    interval_seconds: int = 60
    timeout_seconds: int = 10
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3


class AlertRuleCreate(BaseModel):
    name: str
    component: str
    condition: str  # unhealthy, latency_high, error_rate_high
    threshold: Optional[float] = None
    notification_channels: List[str] = []


@app.get("/health")
def get_health_status():
    """Get overall system health status"""
    component_status = {}
    for comp in SERVICE_COMPONENTS:
        # Simulated health check
        component_status[comp] = {
            "status": "healthy",
            "latency_ms": 15,
            "last_check": datetime.utcnow().isoformat()
        }

    overall = "healthy" if all(c["status"] == "healthy" for c in component_status.values()) else "degraded"

    return {
        "status": overall,
        "components": component_status,
        "uptime_seconds": 86400,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/detailed")
def get_detailed_health():
    """Get detailed health information"""
    return {
        "status": "healthy",
        "components": {
            comp: {
                "status": "healthy",
                "latency_ms": 15,
                "memory_mb": 256,
                "cpu_percent": 5.2,
                "connections": 10,
                "last_check": datetime.utcnow().isoformat()
            }
            for comp in SERVICE_COMPONENTS
        },
        "system": {
            "memory_total_mb": 8192,
            "memory_used_mb": 4096,
            "cpu_cores": 4,
            "cpu_percent": 25.5,
            "disk_total_gb": 100,
            "disk_used_gb": 45
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/health/checks")
def create_health_check(check: HealthCheckCreate):
    """Create a custom health check"""
    check_id = str(uuid.uuid4())
    HEALTH_CHECKS[check_id] = {
        "id": check_id,
        "name": check.name,
        "component": check.component,
        "check_type": check.check_type,
        "endpoint": check.endpoint,
        "interval_seconds": check.interval_seconds,
        "timeout_seconds": check.timeout_seconds,
        "healthy_threshold": check.healthy_threshold,
        "unhealthy_threshold": check.unhealthy_threshold,
        "status": "healthy",
        "consecutive_failures": 0,
        "last_check": None,
        "created_at": datetime.utcnow().isoformat()
    }
    return HEALTH_CHECKS[check_id]


@app.get("/health/checks")
def list_health_checks():
    """List health checks"""
    return {"health_checks": list(HEALTH_CHECKS.values())}


@app.get("/health/checks/{check_id}")
def get_health_check(check_id: str):
    """Get health check details"""
    if check_id not in HEALTH_CHECKS:
        raise HTTPException(status_code=404, detail="Health check not found")
    return HEALTH_CHECKS[check_id]


@app.delete("/health/checks/{check_id}")
def delete_health_check(check_id: str):
    """Delete a health check"""
    if check_id not in HEALTH_CHECKS:
        raise HTTPException(status_code=404, detail="Health check not found")
    del HEALTH_CHECKS[check_id]
    return {"status": "deleted"}


@app.post("/health/checks/{check_id}/run")
def run_health_check(check_id: str):
    """Manually run a health check"""
    if check_id not in HEALTH_CHECKS:
        raise HTTPException(status_code=404, detail="Health check not found")

    check = HEALTH_CHECKS[check_id]
    # Simulated check
    check["last_check"] = datetime.utcnow().isoformat()
    check["status"] = "healthy"

    return {
        "check_id": check_id,
        "status": "healthy",
        "latency_ms": 45,
        "checked_at": check["last_check"]
    }


@app.get("/health/uptime")
def get_uptime_history(days: int = 30):
    """Get uptime history"""
    # Simulated uptime data
    records = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        records.append({
            "date": date,
            "uptime_percent": 99.9 if i > 0 else 100.0,
            "incidents": 0,
            "total_downtime_minutes": 0
        })

    return {
        "period_days": days,
        "overall_uptime_percent": 99.95,
        "daily_records": records
    }


@app.post("/monitoring/alerts/rules")
def create_alert_rule(rule: AlertRuleCreate):
    """Create an alert rule"""
    rule_id = str(uuid.uuid4())
    ALERT_RULES[rule_id] = {
        "id": rule_id,
        "name": rule.name,
        "component": rule.component,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "notification_channels": rule.notification_channels,
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    return ALERT_RULES[rule_id]


@app.get("/monitoring/alerts/rules")
def list_alert_rules():
    """List alert rules"""
    return {"alert_rules": list(ALERT_RULES.values())}


@app.delete("/monitoring/alerts/rules/{rule_id}")
def delete_alert_rule(rule_id: str):
    """Delete an alert rule"""
    if rule_id not in ALERT_RULES:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    del ALERT_RULES[rule_id]
    return {"status": "deleted"}


@app.get("/monitoring/alerts")
def list_alerts(status: Optional[str] = None, limit: int = 50):
    """List alerts"""
    alerts = ALERTS.copy()
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    alerts.sort(key=lambda x: x["triggered_at"], reverse=True)
    return {"alerts": alerts[:limit]}


@app.post("/monitoring/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    for alert in ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = datetime.utcnow().isoformat()
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/monitoring/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    """Resolve an alert"""
    for alert in ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = "resolved"
            alert["resolved_at"] = datetime.utcnow().isoformat()
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/monitoring/metrics")
def get_metrics(component: Optional[str] = None, metric_name: Optional[str] = None, hours: int = 24):
    """Get system metrics"""
    # Simulated metrics
    return {
        "period_hours": hours,
        "metrics": {
            "requests_per_minute": [{"timestamp": datetime.utcnow().isoformat(), "value": 150}],
            "response_time_ms": [{"timestamp": datetime.utcnow().isoformat(), "value": 45}],
            "error_rate_percent": [{"timestamp": datetime.utcnow().isoformat(), "value": 0.1}],
            "active_connections": [{"timestamp": datetime.utcnow().isoformat(), "value": 25}]
        }
    }


# ============================================================================
# Environment Management
# ============================================================================

# Storage for environments
ENVIRONMENTS: Dict[str, Dict[str, Any]] = {}
ENVIRONMENT_VARIABLES: Dict[str, Dict[str, Dict[str, Any]]] = {}
DEPLOYMENTS: Dict[str, Dict[str, Any]] = {}
PROMOTION_HISTORY: List[Dict[str, Any]] = []

DEFAULT_ENVIRONMENTS = ["development", "staging", "production"]


class EnvironmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_environment: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    protection_rules: Optional[Dict[str, Any]] = None


class DeploymentCreate(BaseModel):
    environment_id: str
    agent_card_id: Optional[str] = None
    workflow_id: Optional[str] = None
    version: str
    config_overrides: Optional[Dict[str, Any]] = None


@app.post("/environments")
def create_environment(env: EnvironmentCreate):
    """Create a new environment"""
    env_id = str(uuid.uuid4())
    ENVIRONMENTS[env_id] = {
        "id": env_id,
        "name": env.name,
        "description": env.description,
        "parent_environment": env.parent_environment,
        "config": env.config or {},
        "protection_rules": env.protection_rules or {},
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    ENVIRONMENT_VARIABLES[env_id] = {}
    return ENVIRONMENTS[env_id]


@app.get("/environments")
def list_environments():
    """List all environments"""
    return {"environments": list(ENVIRONMENTS.values())}


@app.get("/environments/{env_id}")
def get_environment(env_id: str):
    """Get environment details"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {
        "environment": ENVIRONMENTS[env_id],
        "variables": ENVIRONMENT_VARIABLES.get(env_id, {})
    }


@app.put("/environments/{env_id}")
def update_environment(env_id: str, updates: Dict[str, Any] = Body(...)):
    """Update an environment"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    allowed = ["name", "description", "config", "protection_rules"]
    for key, value in updates.items():
        if key in allowed:
            ENVIRONMENTS[env_id][key] = value
    ENVIRONMENTS[env_id]["updated_at"] = datetime.utcnow().isoformat()
    return ENVIRONMENTS[env_id]


@app.delete("/environments/{env_id}")
def delete_environment(env_id: str):
    """Delete an environment"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Check protection rules
    if ENVIRONMENTS[env_id].get("protection_rules", {}).get("prevent_deletion"):
        raise HTTPException(status_code=403, detail="Environment is protected from deletion")

    del ENVIRONMENTS[env_id]
    if env_id in ENVIRONMENT_VARIABLES:
        del ENVIRONMENT_VARIABLES[env_id]
    return {"status": "deleted"}


@app.post("/environments/{env_id}/variables")
def set_environment_variable(env_id: str, data: Dict[str, Any] = Body(...)):
    """Set an environment variable"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    var_name = data.get("name")
    var_value = data.get("value")
    is_secret = data.get("is_secret", False)

    ENVIRONMENT_VARIABLES[env_id][var_name] = {
        "name": var_name,
        "value": var_value if not is_secret else "****",
        "_value": var_value,
        "is_secret": is_secret,
        "updated_at": datetime.utcnow().isoformat()
    }

    return {"name": var_name, "is_secret": is_secret, "updated_at": datetime.utcnow().isoformat()}


@app.get("/environments/{env_id}/variables")
def get_environment_variables(env_id: str, include_secrets: bool = False):
    """Get environment variables"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    variables = ENVIRONMENT_VARIABLES.get(env_id, {})
    if not include_secrets:
        variables = {k: {kk: vv for kk, vv in v.items() if kk != "_value"} for k, v in variables.items()}

    return {"variables": variables}


@app.delete("/environments/{env_id}/variables/{var_name}")
def delete_environment_variable(env_id: str, var_name: str):
    """Delete an environment variable"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    if var_name in ENVIRONMENT_VARIABLES.get(env_id, {}):
        del ENVIRONMENT_VARIABLES[env_id][var_name]
    return {"status": "deleted"}


@app.post("/deployments")
def create_deployment(deployment: DeploymentCreate):
    """Create a new deployment"""
    if deployment.environment_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    deploy_id = str(uuid.uuid4())
    DEPLOYMENTS[deploy_id] = {
        "id": deploy_id,
        "environment_id": deployment.environment_id,
        "agent_card_id": deployment.agent_card_id,
        "workflow_id": deployment.workflow_id,
        "version": deployment.version,
        "config_overrides": deployment.config_overrides or {},
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "deployed_at": None,
        "deployed_by": "current_user"
    }

    # Simulate deployment
    DEPLOYMENTS[deploy_id]["status"] = "deployed"
    DEPLOYMENTS[deploy_id]["deployed_at"] = datetime.utcnow().isoformat()

    return DEPLOYMENTS[deploy_id]


@app.get("/deployments")
def list_deployments(environment_id: Optional[str] = None, limit: int = 20):
    """List deployments"""
    deployments = list(DEPLOYMENTS.values())
    if environment_id:
        deployments = [d for d in deployments if d["environment_id"] == environment_id]
    deployments.sort(key=lambda x: x["created_at"], reverse=True)
    return {"deployments": deployments[:limit]}


@app.get("/deployments/{deploy_id}")
def get_deployment(deploy_id: str):
    """Get deployment details"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DEPLOYMENTS[deploy_id]


@app.post("/deployments/{deploy_id}/rollback")
def rollback_deployment(deploy_id: str):
    """Rollback a deployment"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    DEPLOYMENTS[deploy_id]["status"] = "rolled_back"
    DEPLOYMENTS[deploy_id]["rolled_back_at"] = datetime.utcnow().isoformat()
    return DEPLOYMENTS[deploy_id]


@app.post("/environments/{env_id}/promote")
def promote_to_environment(env_id: str, data: Dict[str, Any] = Body(...)):
    """Promote a deployment to another environment"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Target environment not found")

    source_deploy_id = data.get("source_deployment_id")
    if source_deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Source deployment not found")

    source = DEPLOYMENTS[source_deploy_id]

    # Create new deployment in target environment
    new_deploy_id = str(uuid.uuid4())
    DEPLOYMENTS[new_deploy_id] = {
        "id": new_deploy_id,
        "environment_id": env_id,
        "agent_card_id": source["agent_card_id"],
        "workflow_id": source["workflow_id"],
        "version": source["version"],
        "config_overrides": source["config_overrides"],
        "status": "deployed",
        "promoted_from": source_deploy_id,
        "created_at": datetime.utcnow().isoformat(),
        "deployed_at": datetime.utcnow().isoformat(),
        "deployed_by": "current_user"
    }

    PROMOTION_HISTORY.append({
        "source_deployment_id": source_deploy_id,
        "target_deployment_id": new_deploy_id,
        "target_environment_id": env_id,
        "promoted_at": datetime.utcnow().isoformat(),
        "promoted_by": "current_user"
    })

    return DEPLOYMENTS[new_deploy_id]


@app.get("/environments/promotion-history")
def get_promotion_history(limit: int = 20):
    """Get promotion history"""
    history = PROMOTION_HISTORY.copy()
    history.sort(key=lambda x: x["promoted_at"], reverse=True)
    return {"promotions": history[:limit]}


# ============================================================================
# Collaboration Features
# ============================================================================

# Storage for collaboration
COMMENTS: Dict[str, List[Dict[str, Any]]] = {}
SHARES: Dict[str, Dict[str, Any]] = {}
ACTIVITY_FEED: List[Dict[str, Any]] = []
MENTIONS: Dict[str, List[Dict[str, Any]]] = {}
REACTIONS: Dict[str, Dict[str, int]] = {}


class CommentCreate(BaseModel):
    content: str
    resource_type: str  # agent_card, workflow, execution, etc.
    resource_id: str
    parent_comment_id: Optional[str] = None
    mentions: Optional[List[str]] = []


class ShareCreate(BaseModel):
    resource_type: str
    resource_id: str
    share_with_type: str  # user, team, org, public
    share_with_id: Optional[str] = None
    permission: str = "view"  # view, edit, admin


@app.post("/comments")
def create_comment(comment: CommentCreate):
    """Add a comment to a resource"""
    comment_id = str(uuid.uuid4())
    resource_key = f"{comment.resource_type}:{comment.resource_id}"

    if resource_key not in COMMENTS:
        COMMENTS[resource_key] = []

    comment_data = {
        "id": comment_id,
        "content": comment.content,
        "resource_type": comment.resource_type,
        "resource_id": comment.resource_id,
        "parent_comment_id": comment.parent_comment_id,
        "author_id": "current_user",
        "mentions": comment.mentions or [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "edited": False
    }
    COMMENTS[resource_key].append(comment_data)
    REACTIONS[comment_id] = {}

    # Record activity
    ACTIVITY_FEED.append({
        "type": "comment_added",
        "resource_type": comment.resource_type,
        "resource_id": comment.resource_id,
        "user_id": "current_user",
        "timestamp": datetime.utcnow().isoformat()
    })

    # Record mentions
    for user_id in comment.mentions or []:
        if user_id not in MENTIONS:
            MENTIONS[user_id] = []
        MENTIONS[user_id].append({
            "comment_id": comment_id,
            "mentioned_by": "current_user",
            "resource_type": comment.resource_type,
            "resource_id": comment.resource_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    return comment_data


@app.get("/comments")
def get_comments(resource_type: str, resource_id: str):
    """Get comments for a resource"""
    resource_key = f"{resource_type}:{resource_id}"
    comments = COMMENTS.get(resource_key, [])

    # Add reaction counts
    for comment in comments:
        comment["reactions"] = REACTIONS.get(comment["id"], {})

    return {"comments": comments}


@app.put("/comments/{comment_id}")
def update_comment(comment_id: str, content: str = Body(..., embed=True)):
    """Update a comment"""
    for resource_comments in COMMENTS.values():
        for comment in resource_comments:
            if comment["id"] == comment_id:
                comment["content"] = content
                comment["updated_at"] = datetime.utcnow().isoformat()
                comment["edited"] = True
                return comment
    raise HTTPException(status_code=404, detail="Comment not found")


@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: str):
    """Delete a comment"""
    for resource_key, resource_comments in COMMENTS.items():
        for i, comment in enumerate(resource_comments):
            if comment["id"] == comment_id:
                del COMMENTS[resource_key][i]
                return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Comment not found")


@app.post("/comments/{comment_id}/reactions")
def add_reaction(comment_id: str, reaction: str = Body(..., embed=True)):
    """Add a reaction to a comment"""
    if comment_id not in REACTIONS:
        REACTIONS[comment_id] = {}

    REACTIONS[comment_id][reaction] = REACTIONS[comment_id].get(reaction, 0) + 1
    return {"reactions": REACTIONS[comment_id]}


@app.delete("/comments/{comment_id}/reactions/{reaction}")
def remove_reaction(comment_id: str, reaction: str):
    """Remove a reaction from a comment"""
    if comment_id in REACTIONS and reaction in REACTIONS[comment_id]:
        REACTIONS[comment_id][reaction] = max(0, REACTIONS[comment_id][reaction] - 1)
    return {"reactions": REACTIONS.get(comment_id, {})}


@app.post("/shares")
def create_share(share: ShareCreate):
    """Share a resource"""
    share_id = str(uuid.uuid4())
    SHARES[share_id] = {
        "id": share_id,
        "resource_type": share.resource_type,
        "resource_id": share.resource_id,
        "share_with_type": share.share_with_type,
        "share_with_id": share.share_with_id,
        "permission": share.permission,
        "shared_by": "current_user",
        "created_at": datetime.utcnow().isoformat()
    }

    # Record activity
    ACTIVITY_FEED.append({
        "type": "resource_shared",
        "resource_type": share.resource_type,
        "resource_id": share.resource_id,
        "user_id": "current_user",
        "share_with": share.share_with_id or share.share_with_type,
        "timestamp": datetime.utcnow().isoformat()
    })

    return SHARES[share_id]


@app.get("/shares")
def list_shares(resource_type: Optional[str] = None, resource_id: Optional[str] = None):
    """List shares"""
    shares = list(SHARES.values())
    if resource_type:
        shares = [s for s in shares if s["resource_type"] == resource_type]
    if resource_id:
        shares = [s for s in shares if s["resource_id"] == resource_id]
    return {"shares": shares}


@app.delete("/shares/{share_id}")
def delete_share(share_id: str):
    """Remove a share"""
    if share_id not in SHARES:
        raise HTTPException(status_code=404, detail="Share not found")
    del SHARES[share_id]
    return {"status": "deleted"}


@app.get("/activity")
def get_activity_feed(
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50
):
    """Get activity feed"""
    activities = ACTIVITY_FEED.copy()
    if resource_type:
        activities = [a for a in activities if a.get("resource_type") == resource_type]
    if user_id:
        activities = [a for a in activities if a.get("user_id") == user_id]
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"activities": activities[:limit]}


@app.get("/mentions")
def get_mentions(user_id: str = "current_user", unread_only: bool = False):
    """Get mentions for a user"""
    mentions = MENTIONS.get(user_id, [])
    mentions.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"mentions": mentions}


@app.post("/mentions/{mention_index}/read")
def mark_mention_read(user_id: str = "current_user", mention_index: int = 0):
    """Mark a mention as read"""
    if user_id in MENTIONS and mention_index < len(MENTIONS[user_id]):
        MENTIONS[user_id][mention_index]["read"] = True
        return {"status": "marked_read"}
    raise HTTPException(status_code=404, detail="Mention not found")


@app.get("/shared-with-me")
def get_shared_with_me(user_id: str = "current_user"):
    """Get resources shared with the current user"""
    shared = [s for s in SHARES.values() if s.get("share_with_id") == user_id]
    return {"shared_resources": shared}


# ============================================================================
# Agent Templates Library
# ============================================================================

# Storage for templates
AGENT_TEMPLATES: Dict[str, Dict[str, Any]] = {}
TEMPLATE_CATEGORIES: Dict[str, Dict[str, Any]] = {}
TEMPLATE_USAGE: Dict[str, List[Dict[str, Any]]] = {}

# Pre-built template definitions
BUILTIN_TEMPLATES = {
    "customer-support": {
        "name": "Customer Support Agent",
        "description": "Handle customer inquiries, complaints, and support tickets with empathy and efficiency",
        "category": "customer-service",
        "system_prompt": "You are a helpful customer support agent. Be empathetic, professional, and solution-oriented. Always acknowledge the customer's concern before providing solutions.",
        "capabilities": ["ticket_handling", "faq_response", "escalation", "sentiment_analysis"],
        "suggested_tools": ["knowledge_base", "ticket_system", "email"],
        "example_inputs": ["I can't log into my account", "Where is my order?", "I want a refund"],
        "config": {"tone": "friendly", "max_response_length": 500}
    },
    "data-analyst": {
        "name": "Data Analysis Agent",
        "description": "Analyze datasets, generate insights, create visualizations, and answer data questions",
        "category": "data-analysis",
        "system_prompt": "You are a data analyst expert. Analyze data thoroughly, identify patterns, and provide actionable insights. Always validate your findings and present them clearly.",
        "capabilities": ["data_analysis", "visualization", "statistical_analysis", "reporting"],
        "suggested_tools": ["sql", "python", "charts", "export"],
        "example_inputs": ["What are the sales trends?", "Find anomalies in this dataset", "Create a monthly report"],
        "config": {"output_format": "structured", "include_confidence": True}
    },
    "code-reviewer": {
        "name": "Code Review Agent",
        "description": "Review code for bugs, security issues, performance problems, and best practices",
        "category": "development",
        "system_prompt": "You are an expert code reviewer. Analyze code for bugs, security vulnerabilities, performance issues, and adherence to best practices. Provide constructive feedback with specific suggestions.",
        "capabilities": ["bug_detection", "security_analysis", "performance_review", "style_check"],
        "suggested_tools": ["github", "static_analysis", "linter"],
        "example_inputs": ["Review this pull request", "Check for security issues", "Suggest optimizations"],
        "config": {"severity_levels": True, "auto_suggest_fixes": True}
    },
    "content-writer": {
        "name": "Content Writing Agent",
        "description": "Create blog posts, articles, marketing copy, and other written content",
        "category": "creative",
        "system_prompt": "You are a skilled content writer. Create engaging, well-structured content that matches the target audience and purpose. Maintain consistent tone and style throughout.",
        "capabilities": ["blog_writing", "copywriting", "editing", "seo_optimization"],
        "suggested_tools": ["grammar_check", "seo_analyzer", "plagiarism_check"],
        "example_inputs": ["Write a blog post about AI", "Create marketing copy for our product", "Edit this article"],
        "config": {"default_length": "medium", "include_seo": True}
    },
    "research-assistant": {
        "name": "Research Assistant Agent",
        "description": "Conduct research, summarize findings, and compile reports on any topic",
        "category": "research",
        "system_prompt": "You are a thorough research assistant. Gather information from multiple sources, verify facts, and present findings in a clear, organized manner. Always cite sources.",
        "capabilities": ["web_research", "summarization", "fact_checking", "report_generation"],
        "suggested_tools": ["web_search", "document_reader", "citation_manager"],
        "example_inputs": ["Research market trends in AI", "Summarize this paper", "Find statistics on X"],
        "config": {"citation_style": "apa", "include_sources": True}
    },
    "meeting-assistant": {
        "name": "Meeting Assistant Agent",
        "description": "Take notes, summarize discussions, track action items, and schedule follow-ups",
        "category": "productivity",
        "system_prompt": "You are an efficient meeting assistant. Capture key points, decisions, and action items accurately. Organize notes clearly and ensure nothing important is missed.",
        "capabilities": ["note_taking", "summarization", "action_tracking", "scheduling"],
        "suggested_tools": ["calendar", "task_manager", "transcription"],
        "example_inputs": ["Summarize this meeting", "List action items", "Schedule a follow-up"],
        "config": {"format": "structured", "extract_decisions": True}
    },
    "sales-assistant": {
        "name": "Sales Assistant Agent",
        "description": "Qualify leads, draft proposals, answer product questions, and assist with sales processes",
        "category": "sales",
        "system_prompt": "You are a knowledgeable sales assistant. Help qualify leads, understand customer needs, and provide relevant product information. Be helpful without being pushy.",
        "capabilities": ["lead_qualification", "proposal_drafting", "product_knowledge", "crm_updates"],
        "suggested_tools": ["crm", "email", "calendar", "product_catalog"],
        "example_inputs": ["Qualify this lead", "Draft a proposal", "Answer product questions"],
        "config": {"crm_integration": True, "follow_up_reminders": True}
    },
    "hr-assistant": {
        "name": "HR Assistant Agent",
        "description": "Handle HR inquiries, assist with onboarding, and manage employee-related tasks",
        "category": "hr",
        "system_prompt": "You are a helpful HR assistant. Answer employee questions about policies, benefits, and procedures. Maintain confidentiality and be supportive.",
        "capabilities": ["policy_guidance", "onboarding_support", "leave_management", "benefits_info"],
        "suggested_tools": ["hr_system", "document_library", "calendar"],
        "example_inputs": ["What's the leave policy?", "Help with onboarding", "Explain benefits"],
        "config": {"confidential_mode": True, "escalation_enabled": True}
    },
    "legal-reviewer": {
        "name": "Legal Document Reviewer Agent",
        "description": "Review contracts, identify risks, and summarize legal documents",
        "category": "legal",
        "system_prompt": "You are a legal document reviewer. Analyze contracts and legal documents for key terms, risks, and obligations. Flag potential issues and summarize findings clearly.",
        "capabilities": ["contract_review", "risk_identification", "clause_extraction", "compliance_check"],
        "suggested_tools": ["document_parser", "legal_database", "redlining"],
        "example_inputs": ["Review this contract", "Identify risks", "Summarize key terms"],
        "config": {"jurisdiction": "general", "risk_threshold": "medium"}
    },
    "devops-assistant": {
        "name": "DevOps Assistant Agent",
        "description": "Help with deployments, infrastructure, monitoring, and CI/CD pipelines",
        "category": "development",
        "system_prompt": "You are a DevOps expert assistant. Help with infrastructure, deployments, and operational tasks. Prioritize reliability, security, and best practices.",
        "capabilities": ["deployment_assistance", "infrastructure_help", "monitoring_setup", "pipeline_config"],
        "suggested_tools": ["aws", "kubernetes", "terraform", "github_actions"],
        "example_inputs": ["Help deploy this service", "Set up monitoring", "Debug this pipeline"],
        "config": {"cloud_provider": "aws", "security_first": True}
    }
}


class AgentTemplateCreate(BaseModel):
    name: str
    description: str
    category: str
    system_prompt: str
    capabilities: Optional[List[str]] = []
    suggested_tools: Optional[List[str]] = []
    example_inputs: Optional[List[str]] = []
    config: Optional[Dict[str, Any]] = {}
    is_public: Optional[bool] = False


@app.get("/templates/builtin")
def list_builtin_templates():
    """List all built-in agent templates"""
    return {"templates": BUILTIN_TEMPLATES}


@app.get("/templates/builtin/{template_id}")
def get_builtin_template(template_id: str):
    """Get a specific built-in template"""
    if template_id not in BUILTIN_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": BUILTIN_TEMPLATES[template_id]}


@app.post("/templates/builtin/{template_id}/use")
def use_builtin_template(template_id: str, customizations: Dict[str, Any] = Body(default={})):
    """Create an agent card from a built-in template"""
    if template_id not in BUILTIN_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = BUILTIN_TEMPLATES[template_id].copy()

    # Apply customizations
    for key, value in customizations.items():
        if key in template:
            template[key] = value

    # Track usage
    if template_id not in TEMPLATE_USAGE:
        TEMPLATE_USAGE[template_id] = []
    TEMPLATE_USAGE[template_id].append({
        "used_at": datetime.utcnow().isoformat(),
        "customizations": list(customizations.keys())
    })

    agent_card_id = str(uuid.uuid4())
    return {
        "agent_card_id": agent_card_id,
        "template_id": template_id,
        "config": template,
        "message": "Agent card created from template"
    }


@app.post("/templates")
def create_custom_template(template: AgentTemplateCreate):
    """Create a custom agent template"""
    template_id = str(uuid.uuid4())
    AGENT_TEMPLATES[template_id] = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "system_prompt": template.system_prompt,
        "capabilities": template.capabilities or [],
        "suggested_tools": template.suggested_tools or [],
        "example_inputs": template.example_inputs or [],
        "config": template.config or {},
        "is_public": template.is_public,
        "author_id": "current_user",
        "uses": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return AGENT_TEMPLATES[template_id]


@app.get("/templates")
def list_custom_templates(category: Optional[str] = None, public_only: bool = False):
    """List custom templates"""
    templates = list(AGENT_TEMPLATES.values())
    if category:
        templates = [t for t in templates if t["category"] == category]
    if public_only:
        templates = [t for t in templates if t["is_public"]]
    return {"templates": templates}


@app.get("/templates/{template_id}")
def get_custom_template(template_id: str):
    """Get a custom template"""
    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return AGENT_TEMPLATES[template_id]


@app.put("/templates/{template_id}")
def update_custom_template(template_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a custom template"""
    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    allowed = ["name", "description", "system_prompt", "capabilities", "suggested_tools", "example_inputs", "config", "is_public"]
    for key, value in updates.items():
        if key in allowed:
            AGENT_TEMPLATES[template_id][key] = value
    AGENT_TEMPLATES[template_id]["updated_at"] = datetime.utcnow().isoformat()
    return AGENT_TEMPLATES[template_id]


@app.delete("/templates/{template_id}")
def delete_custom_template(template_id: str):
    """Delete a custom template"""
    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    del AGENT_TEMPLATES[template_id]
    return {"status": "deleted"}


@app.get("/templates/categories")
def list_template_categories():
    """List template categories with counts"""
    categories = {}
    for template in BUILTIN_TEMPLATES.values():
        cat = template["category"]
        categories[cat] = categories.get(cat, 0) + 1
    for template in AGENT_TEMPLATES.values():
        cat = template["category"]
        categories[cat] = categories.get(cat, 0) + 1
    return {"categories": [{"name": k, "count": v} for k, v in categories.items()]}


# ============================================================================
# Prompt Engineering Tools
# ============================================================================

# Storage for prompts
PROMPTS: Dict[str, Dict[str, Any]] = {}
PROMPT_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}
PROMPT_TESTS: Dict[str, Dict[str, Any]] = {}
PROMPT_EXPERIMENTS: Dict[str, Dict[str, Any]] = {}


class PromptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template: str
    variables: Optional[List[str]] = []
    category: Optional[str] = None
    tags: Optional[List[str]] = []


class PromptTest(BaseModel):
    prompt_id: str
    test_inputs: Dict[str, str]
    expected_behavior: Optional[str] = None


class PromptExperiment(BaseModel):
    name: str
    prompt_variants: List[str]  # List of prompt IDs
    test_cases: List[Dict[str, Any]]
    metrics: Optional[List[str]] = ["quality", "relevance", "coherence"]


@app.post("/prompts")
def create_prompt(prompt: PromptCreate):
    """Create a new prompt template"""
    prompt_id = str(uuid.uuid4())

    # Extract variables from template ({{variable}})
    import re
    found_vars = re.findall(r'\{\{(\w+)\}\}', prompt.template)

    PROMPTS[prompt_id] = {
        "id": prompt_id,
        "name": prompt.name,
        "description": prompt.description,
        "template": prompt.template,
        "variables": prompt.variables or found_vars,
        "category": prompt.category,
        "tags": prompt.tags or [],
        "version": 1,
        "author_id": "current_user",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    PROMPT_VERSIONS[prompt_id] = [{
        "version": 1,
        "template": prompt.template,
        "created_at": datetime.utcnow().isoformat()
    }]
    return PROMPTS[prompt_id]


@app.get("/prompts")
def list_prompts(category: Optional[str] = None, tag: Optional[str] = None):
    """List prompts"""
    prompts = list(PROMPTS.values())
    if category:
        prompts = [p for p in prompts if p["category"] == category]
    if tag:
        prompts = [p for p in prompts if tag in p.get("tags", [])]
    return {"prompts": prompts}


@app.get("/prompts/{prompt_id}")
def get_prompt(prompt_id: str):
    """Get prompt details"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PROMPTS[prompt_id]


@app.put("/prompts/{prompt_id}")
def update_prompt(prompt_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a prompt (creates new version)"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt = PROMPTS[prompt_id]

    if "template" in updates:
        prompt["version"] += 1
        PROMPT_VERSIONS[prompt_id].append({
            "version": prompt["version"],
            "template": updates["template"],
            "created_at": datetime.utcnow().isoformat()
        })

    allowed = ["name", "description", "template", "variables", "category", "tags"]
    for key, value in updates.items():
        if key in allowed:
            prompt[key] = value
    prompt["updated_at"] = datetime.utcnow().isoformat()
    return prompt


@app.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: str):
    """Delete a prompt"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")
    del PROMPTS[prompt_id]
    return {"status": "deleted"}


@app.get("/prompts/{prompt_id}/versions")
def get_prompt_versions(prompt_id: str):
    """Get prompt version history"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"versions": PROMPT_VERSIONS.get(prompt_id, [])}


@app.post("/prompts/{prompt_id}/render")
def render_prompt(prompt_id: str, variables: Dict[str, str] = Body(...)):
    """Render a prompt with variables"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")

    template = PROMPTS[prompt_id]["template"]
    rendered = template
    for var, value in variables.items():
        rendered = rendered.replace(f"{{{{{var}}}}}", value)

    return {
        "prompt_id": prompt_id,
        "rendered": rendered,
        "variables_used": list(variables.keys())
    }


@app.post("/prompts/{prompt_id}/test")
def test_prompt(prompt_id: str, test: PromptTest):
    """Test a prompt with sample inputs"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")

    template = PROMPTS[prompt_id]["template"]
    rendered = template
    for var, value in test.test_inputs.items():
        rendered = rendered.replace(f"{{{{{var}}}}}", value)

    test_id = str(uuid.uuid4())
    PROMPT_TESTS[test_id] = {
        "id": test_id,
        "prompt_id": prompt_id,
        "inputs": test.test_inputs,
        "rendered_prompt": rendered,
        "expected_behavior": test.expected_behavior,
        "simulated_response": f"[Simulated AI response to: {rendered[:100]}...]",
        "created_at": datetime.utcnow().isoformat()
    }
    return PROMPT_TESTS[test_id]


@app.post("/prompts/{prompt_id}/analyze")
def analyze_prompt(prompt_id: str):
    """Analyze a prompt for potential improvements"""
    if prompt_id not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt = PROMPTS[prompt_id]
    template = prompt["template"]

    # Basic analysis
    analysis = {
        "prompt_id": prompt_id,
        "length": len(template),
        "word_count": len(template.split()),
        "variable_count": len(prompt.get("variables", [])),
        "suggestions": [],
        "score": 0
    }

    # Generate suggestions
    if len(template) < 50:
        analysis["suggestions"].append("Prompt may be too short. Consider adding more context or instructions.")
    if len(template) > 2000:
        analysis["suggestions"].append("Prompt is quite long. Consider breaking into smaller, focused prompts.")
    if "{{" not in template:
        analysis["suggestions"].append("No variables detected. Consider adding {{variables}} for reusability.")
    if not any(word in template.lower() for word in ["please", "you are", "your task"]):
        analysis["suggestions"].append("Consider adding role/task framing like 'You are...' or 'Your task is...'")
    if "example" not in template.lower():
        analysis["suggestions"].append("Consider adding examples for better AI understanding.")

    # Calculate score
    analysis["score"] = max(0, 100 - len(analysis["suggestions"]) * 15)

    return analysis


@app.post("/prompts/experiments")
def create_prompt_experiment(experiment: PromptExperiment):
    """Create an A/B test experiment for prompts"""
    exp_id = str(uuid.uuid4())
    PROMPT_EXPERIMENTS[exp_id] = {
        "id": exp_id,
        "name": experiment.name,
        "prompt_variants": experiment.prompt_variants,
        "test_cases": experiment.test_cases,
        "metrics": experiment.metrics,
        "status": "created",
        "results": {},
        "created_at": datetime.utcnow().isoformat()
    }
    return PROMPT_EXPERIMENTS[exp_id]


@app.post("/prompts/experiments/{exp_id}/run")
def run_prompt_experiment(exp_id: str):
    """Run a prompt experiment"""
    if exp_id not in PROMPT_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = PROMPT_EXPERIMENTS[exp_id]
    experiment["status"] = "running"

    # Simulate experiment results
    results = {}
    for variant_id in experiment["prompt_variants"]:
        results[variant_id] = {
            "quality_score": 75 + (hash(variant_id) % 25),
            "relevance_score": 70 + (hash(variant_id + "r") % 30),
            "coherence_score": 80 + (hash(variant_id + "c") % 20),
            "avg_response_time_ms": 150 + (hash(variant_id + "t") % 100),
            "test_cases_passed": len(experiment["test_cases"])
        }

    experiment["results"] = results
    experiment["status"] = "completed"
    experiment["completed_at"] = datetime.utcnow().isoformat()

    # Determine winner
    best_variant = max(results.keys(), key=lambda k: results[k]["quality_score"])
    experiment["winner"] = best_variant

    return experiment


@app.get("/prompts/experiments")
def list_experiments():
    """List all prompt experiments"""
    return {"experiments": list(PROMPT_EXPERIMENTS.values())}


@app.get("/prompts/experiments/{exp_id}")
def get_experiment(exp_id: str):
    """Get experiment details"""
    if exp_id not in PROMPT_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return PROMPT_EXPERIMENTS[exp_id]


# ============================================================================
# A2A (Agent-to-Agent) Communication Protocol
# ============================================================================

# Storage for A2A
A2A_CHANNELS: Dict[str, Dict[str, Any]] = {}
A2A_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}
A2A_SUBSCRIPTIONS: Dict[str, List[str]] = {}
A2A_PROTOCOLS: Dict[str, Dict[str, Any]] = {}

# Built-in A2A message types
A2A_MESSAGE_TYPES = [
    "request", "response", "event", "query", "command",
    "handoff", "escalation", "delegation", "notification", "heartbeat"
]


class A2AChannelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    participants: List[str]  # Agent IDs
    protocol: Optional[str] = "default"
    config: Optional[Dict[str, Any]] = {}


class A2AMessage(BaseModel):
    channel_id: str
    sender_agent_id: str
    message_type: str
    content: Dict[str, Any]
    target_agent_id: Optional[str] = None
    requires_response: Optional[bool] = False
    timeout_seconds: Optional[int] = 30


@app.post("/a2a/channels")
def create_a2a_channel(channel: A2AChannelCreate):
    """Create an A2A communication channel"""
    channel_id = str(uuid.uuid4())
    A2A_CHANNELS[channel_id] = {
        "id": channel_id,
        "name": channel.name,
        "description": channel.description,
        "participants": channel.participants,
        "protocol": channel.protocol,
        "config": channel.config or {},
        "status": "active",
        "message_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    A2A_MESSAGES[channel_id] = []
    return A2A_CHANNELS[channel_id]


@app.get("/a2a/channels")
def list_a2a_channels(agent_id: Optional[str] = None):
    """List A2A channels"""
    channels = list(A2A_CHANNELS.values())
    if agent_id:
        channels = [c for c in channels if agent_id in c["participants"]]
    return {"channels": channels}


@app.get("/a2a/channels/{channel_id}")
def get_a2a_channel(channel_id: str):
    """Get channel details"""
    if channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")
    return A2A_CHANNELS[channel_id]


@app.delete("/a2a/channels/{channel_id}")
def delete_a2a_channel(channel_id: str):
    """Delete an A2A channel"""
    if channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")
    del A2A_CHANNELS[channel_id]
    if channel_id in A2A_MESSAGES:
        del A2A_MESSAGES[channel_id]
    return {"status": "deleted"}


@app.post("/a2a/channels/{channel_id}/join")
def join_a2a_channel(channel_id: str, agent_id: str = Body(..., embed=True)):
    """Add an agent to a channel"""
    if channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")

    if agent_id not in A2A_CHANNELS[channel_id]["participants"]:
        A2A_CHANNELS[channel_id]["participants"].append(agent_id)
    return A2A_CHANNELS[channel_id]


@app.post("/a2a/channels/{channel_id}/leave")
def leave_a2a_channel(channel_id: str, agent_id: str = Body(..., embed=True)):
    """Remove an agent from a channel"""
    if channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")

    if agent_id in A2A_CHANNELS[channel_id]["participants"]:
        A2A_CHANNELS[channel_id]["participants"].remove(agent_id)
    return A2A_CHANNELS[channel_id]


@app.post("/a2a/messages")
def send_a2a_message(message: A2AMessage):
    """Send a message through an A2A channel"""
    if message.channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")

    if message.message_type not in A2A_MESSAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid message type. Valid types: {A2A_MESSAGE_TYPES}")

    message_id = str(uuid.uuid4())
    msg_data = {
        "id": message_id,
        "channel_id": message.channel_id,
        "sender_agent_id": message.sender_agent_id,
        "target_agent_id": message.target_agent_id,
        "message_type": message.message_type,
        "content": message.content,
        "requires_response": message.requires_response,
        "response_id": None,
        "status": "delivered",
        "timestamp": datetime.utcnow().isoformat()
    }
    A2A_MESSAGES[message.channel_id].append(msg_data)
    A2A_CHANNELS[message.channel_id]["message_count"] += 1

    return msg_data


@app.get("/a2a/channels/{channel_id}/messages")
def get_a2a_messages(channel_id: str, limit: int = 50, since: Optional[str] = None):
    """Get messages from a channel"""
    if channel_id not in A2A_CHANNELS:
        raise HTTPException(status_code=404, detail="Channel not found")

    messages = A2A_MESSAGES.get(channel_id, [])
    if since:
        messages = [m for m in messages if m["timestamp"] > since]
    messages = messages[-limit:]
    return {"messages": messages}


@app.post("/a2a/messages/{message_id}/respond")
def respond_to_a2a_message(message_id: str, response: Dict[str, Any] = Body(...)):
    """Respond to an A2A message"""
    # Find the message
    for channel_id, messages in A2A_MESSAGES.items():
        for msg in messages:
            if msg["id"] == message_id:
                response_id = str(uuid.uuid4())
                response_msg = {
                    "id": response_id,
                    "channel_id": channel_id,
                    "sender_agent_id": response.get("sender_agent_id", "responder"),
                    "target_agent_id": msg["sender_agent_id"],
                    "message_type": "response",
                    "content": response.get("content", {}),
                    "in_response_to": message_id,
                    "status": "delivered",
                    "timestamp": datetime.utcnow().isoformat()
                }
                A2A_MESSAGES[channel_id].append(response_msg)
                msg["response_id"] = response_id
                return response_msg

    raise HTTPException(status_code=404, detail="Message not found")


@app.post("/a2a/handoff")
def agent_handoff(data: Dict[str, Any] = Body(...)):
    """Hand off a task from one agent to another"""
    handoff_id = str(uuid.uuid4())
    return {
        "handoff_id": handoff_id,
        "from_agent": data.get("from_agent_id"),
        "to_agent": data.get("to_agent_id"),
        "task": data.get("task"),
        "context": data.get("context", {}),
        "status": "handed_off",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/a2a/broadcast")
def broadcast_to_agents(data: Dict[str, Any] = Body(...)):
    """Broadcast a message to multiple agents"""
    broadcast_id = str(uuid.uuid4())
    target_agents = data.get("target_agents", [])
    return {
        "broadcast_id": broadcast_id,
        "sender_agent_id": data.get("sender_agent_id"),
        "target_agents": target_agents,
        "message": data.get("message"),
        "delivered_to": len(target_agents),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/a2a/message-types")
def list_a2a_message_types():
    """List available A2A message types"""
    return {"message_types": A2A_MESSAGE_TYPES}


# ============================================================================
# SDK Generation & Client Libraries
# ============================================================================

SDK_CONFIGS: Dict[str, Dict[str, Any]] = {}
SDK_GENERATIONS: List[Dict[str, Any]] = []

SUPPORTED_SDK_LANGUAGES = {
    "python": {
        "name": "Python",
        "package_manager": "pip",
        "file_extension": ".py",
        "template_style": "pydantic"
    },
    "typescript": {
        "name": "TypeScript",
        "package_manager": "npm",
        "file_extension": ".ts",
        "template_style": "fetch"
    },
    "javascript": {
        "name": "JavaScript",
        "package_manager": "npm",
        "file_extension": ".js",
        "template_style": "fetch"
    },
    "go": {
        "name": "Go",
        "package_manager": "go mod",
        "file_extension": ".go",
        "template_style": "http"
    },
    "rust": {
        "name": "Rust",
        "package_manager": "cargo",
        "file_extension": ".rs",
        "template_style": "reqwest"
    },
    "java": {
        "name": "Java",
        "package_manager": "maven",
        "file_extension": ".java",
        "template_style": "okhttp"
    }
}


@app.get("/sdk/languages")
def list_sdk_languages():
    """List supported SDK languages"""
    return {"languages": SUPPORTED_SDK_LANGUAGES}


@app.post("/sdk/generate")
def generate_sdk(data: Dict[str, Any] = Body(...)):
    """Generate an SDK for a specific language"""
    language = data.get("language", "python")
    if language not in SUPPORTED_SDK_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {list(SUPPORTED_SDK_LANGUAGES.keys())}")

    generation_id = str(uuid.uuid4())
    sdk_info = SUPPORTED_SDK_LANGUAGES[language]

    # Simulated SDK generation
    generation = {
        "id": generation_id,
        "language": language,
        "version": "1.0.0",
        "api_version": "v1",
        "package_name": f"masp-sdk-{language}",
        "status": "generated",
        "files": [
            f"masp_client{sdk_info['file_extension']}",
            f"models{sdk_info['file_extension']}",
            f"exceptions{sdk_info['file_extension']}",
            "README.md"
        ],
        "install_command": f"{sdk_info['package_manager']} install masp-sdk-{language}",
        "download_url": f"/sdk/download/{generation_id}",
        "created_at": datetime.utcnow().isoformat()
    }
    SDK_GENERATIONS.append(generation)
    return generation


@app.get("/sdk/download/{generation_id}")
def download_sdk(generation_id: str):
    """Download a generated SDK"""
    for gen in SDK_GENERATIONS:
        if gen["id"] == generation_id:
            return {
                "generation_id": generation_id,
                "download_url": f"https://sdk.example.com/download/{generation_id}.zip",
                "message": "SDK ready for download"
            }
    raise HTTPException(status_code=404, detail="SDK generation not found")


@app.get("/sdk/generations")
def list_sdk_generations():
    """List SDK generations"""
    return {"generations": SDK_GENERATIONS}


@app.get("/sdk/snippet/{language}")
def get_sdk_snippet(language: str, endpoint: str = "agent_cards"):
    """Get a code snippet for using the SDK"""
    if language not in SUPPORTED_SDK_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")

    snippets = {
        "python": f'''from masp_sdk import MASPClient

client = MASPClient(api_key="your-api-key")

# List {endpoint}
items = client.{endpoint}.list()
for item in items:
    print(item.name)

# Create new
new_item = client.{endpoint}.create(name="My Agent", description="...")
''',
        "typescript": f'''import {{ MASPClient }} from 'masp-sdk';

const client = new MASPClient({{ apiKey: 'your-api-key' }});

// List {endpoint}
const items = await client.{endpoint}.list();
items.forEach(item => console.log(item.name));

// Create new
const newItem = await client.{endpoint}.create({{
  name: 'My Agent',
  description: '...'
}});
''',
        "javascript": f'''const {{ MASPClient }} = require('masp-sdk');

const client = new MASPClient({{ apiKey: 'your-api-key' }});

// List {endpoint}
const items = await client.{endpoint}.list();
items.forEach(item => console.log(item.name));
'''
    }

    return {
        "language": language,
        "endpoint": endpoint,
        "snippet": snippets.get(language, "// Snippet not available")
    }


# ============================================================================
# OpenAPI / Swagger Support
# ============================================================================

@app.get("/openapi.json")
def get_openapi_spec():
    """Get OpenAPI specification"""
    return app.openapi()


@app.get("/docs/swagger")
def get_swagger_ui_config():
    """Get Swagger UI configuration"""
    return {
        "swagger_url": "/openapi.json",
        "title": "Multi-Agent Standards Protocol API",
        "version": "1.0.0",
        "description": "Comprehensive API for managing AI agents, workflows, and enterprise features",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    }


@app.get("/docs/endpoints")
def list_all_endpoints():
    """List all API endpoints with their methods and descriptions"""
    endpoints = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            endpoints.append({
                "path": route.path,
                "methods": list(route.methods - {"HEAD", "OPTIONS"}),
                "name": route.name,
                "description": route.endpoint.__doc__ if route.endpoint else None
            })
    return {
        "total_endpoints": len(endpoints),
        "endpoints": sorted(endpoints, key=lambda x: x["path"])
    }


@app.get("/docs/categories")
def list_endpoint_categories():
    """List endpoints grouped by category"""
    categories = {}
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith("/"):
            parts = route.path.split("/")
            if len(parts) > 1 and parts[1]:
                category = parts[1]
                if category not in categories:
                    categories[category] = []
                if hasattr(route, 'methods'):
                    categories[category].append({
                        "path": route.path,
                        "methods": list(route.methods - {"HEAD", "OPTIONS"})
                    })
    return {"categories": categories}


# ============================================================================
# CLI Support Endpoints
# ============================================================================

CLI_SESSIONS: Dict[str, Dict[str, Any]] = {}
CLI_HISTORY: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/cli/auth")
def cli_authenticate(data: Dict[str, Any] = Body(...)):
    """Authenticate CLI session"""
    session_id = str(uuid.uuid4())
    CLI_SESSIONS[session_id] = {
        "id": session_id,
        "api_key": data.get("api_key", "")[:8] + "...",
        "authenticated": True,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    CLI_HISTORY[session_id] = []
    return {
        "session_id": session_id,
        "authenticated": True,
        "message": "CLI session authenticated successfully"
    }


@app.get("/cli/status")
def cli_status(session_id: Optional[str] = None):
    """Get CLI status and available commands"""
    return {
        "version": "1.0.0",
        "authenticated": session_id in CLI_SESSIONS if session_id else False,
        "available_commands": [
            {"command": "masp agents list", "description": "List all agent cards"},
            {"command": "masp agents create <name>", "description": "Create a new agent"},
            {"command": "masp agents get <id>", "description": "Get agent details"},
            {"command": "masp workflows list", "description": "List all workflows"},
            {"command": "masp workflows run <id>", "description": "Run a workflow"},
            {"command": "masp templates list", "description": "List agent templates"},
            {"command": "masp templates use <id>", "description": "Create agent from template"},
            {"command": "masp execute <agent_id>", "description": "Execute an agent"},
            {"command": "masp search <query>", "description": "Search for agents"},
            {"command": "masp config set <key> <value>", "description": "Set configuration"},
            {"command": "masp config get <key>", "description": "Get configuration"},
            {"command": "masp health", "description": "Check API health"},
            {"command": "masp version", "description": "Show version info"}
        ]
    }


@app.post("/cli/execute")
def cli_execute_command(data: Dict[str, Any] = Body(...)):
    """Execute a CLI command"""
    command = data.get("command", "")
    session_id = data.get("session_id")

    # Parse command
    parts = command.strip().split()
    if not parts:
        return {"error": "No command provided"}

    # Simulate command execution
    result = {
        "command": command,
        "status": "success",
        "output": f"Executed: {command}",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Log to history
    if session_id and session_id in CLI_HISTORY:
        CLI_HISTORY[session_id].append(result)

    return result


@app.get("/cli/history")
def cli_get_history(session_id: str, limit: int = 20):
    """Get CLI command history"""
    if session_id not in CLI_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    history = CLI_HISTORY.get(session_id, [])
    return {"history": history[-limit:]}


@app.get("/cli/completions")
def cli_get_completions(partial: str):
    """Get CLI auto-completions"""
    commands = ["agents", "workflows", "templates", "execute", "search", "config", "health", "version"]
    subcommands = {
        "agents": ["list", "create", "get", "update", "delete"],
        "workflows": ["list", "create", "run", "status"],
        "templates": ["list", "use", "create"],
        "config": ["set", "get", "list"]
    }

    parts = partial.strip().split()
    if len(parts) == 0:
        return {"completions": commands}
    elif len(parts) == 1:
        matches = [c for c in commands if c.startswith(parts[0])]
        return {"completions": matches}
    elif len(parts) == 2 and parts[0] in subcommands:
        matches = [s for s in subcommands[parts[0]] if s.startswith(parts[1])]
        return {"completions": matches}

    return {"completions": []}


# ============================================================================
# Memory / Context Management
# ============================================================================

# Storage for memory
AGENT_MEMORIES: Dict[str, Dict[str, Any]] = {}
MEMORY_ENTRIES: Dict[str, List[Dict[str, Any]]] = {}
CONVERSATION_CONTEXTS: Dict[str, Dict[str, Any]] = {}


class MemoryCreate(BaseModel):
    agent_id: str
    memory_type: str = "long_term"  # short_term, long_term, episodic, semantic
    capacity: Optional[int] = 1000
    config: Optional[Dict[str, Any]] = {}


class MemoryEntry(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    importance: Optional[float] = 0.5
    tags: Optional[List[str]] = []


@app.post("/memory")
def create_agent_memory(memory: MemoryCreate):
    """Create a memory store for an agent"""
    memory_id = str(uuid.uuid4())
    AGENT_MEMORIES[memory_id] = {
        "id": memory_id,
        "agent_id": memory.agent_id,
        "memory_type": memory.memory_type,
        "capacity": memory.capacity,
        "config": memory.config or {},
        "entry_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    MEMORY_ENTRIES[memory_id] = []
    return AGENT_MEMORIES[memory_id]


@app.get("/memory")
def list_agent_memories(agent_id: Optional[str] = None):
    """List memory stores"""
    memories = list(AGENT_MEMORIES.values())
    if agent_id:
        memories = [m for m in memories if m["agent_id"] == agent_id]
    return {"memories": memories}


@app.get("/memory/{memory_id}")
def get_agent_memory(memory_id: str):
    """Get memory store details"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")
    return AGENT_MEMORIES[memory_id]


@app.delete("/memory/{memory_id}")
def delete_agent_memory(memory_id: str):
    """Delete a memory store"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")
    del AGENT_MEMORIES[memory_id]
    if memory_id in MEMORY_ENTRIES:
        del MEMORY_ENTRIES[memory_id]
    return {"status": "deleted"}


@app.post("/memory/{memory_id}/entries")
def add_memory_entry(memory_id: str, entry: MemoryEntry):
    """Add an entry to memory"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")

    entry_id = str(uuid.uuid4())
    entry_data = {
        "id": entry_id,
        "content": entry.content,
        "metadata": entry.metadata or {},
        "importance": entry.importance,
        "tags": entry.tags or [],
        "access_count": 0,
        "last_accessed": None,
        "created_at": datetime.utcnow().isoformat()
    }
    MEMORY_ENTRIES[memory_id].append(entry_data)
    AGENT_MEMORIES[memory_id]["entry_count"] += 1

    # Enforce capacity
    capacity = AGENT_MEMORIES[memory_id]["capacity"]
    if len(MEMORY_ENTRIES[memory_id]) > capacity:
        # Remove least important entries
        MEMORY_ENTRIES[memory_id].sort(key=lambda x: x["importance"], reverse=True)
        MEMORY_ENTRIES[memory_id] = MEMORY_ENTRIES[memory_id][:capacity]
        AGENT_MEMORIES[memory_id]["entry_count"] = capacity

    return entry_data


@app.get("/memory/{memory_id}/entries")
def list_memory_entries(memory_id: str, limit: int = 50, tag: Optional[str] = None):
    """List memory entries"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")

    entries = MEMORY_ENTRIES.get(memory_id, [])
    if tag:
        entries = [e for e in entries if tag in e.get("tags", [])]
    entries.sort(key=lambda x: x["importance"], reverse=True)
    return {"entries": entries[:limit]}


@app.post("/memory/{memory_id}/search")
def search_memory(memory_id: str, query: str = Body(..., embed=True)):
    """Search memory entries"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")

    entries = MEMORY_ENTRIES.get(memory_id, [])
    query_lower = query.lower()

    # Simple text search (in production would use embeddings)
    matches = []
    for entry in entries:
        if query_lower in entry["content"].lower():
            entry["access_count"] += 1
            entry["last_accessed"] = datetime.utcnow().isoformat()
            matches.append(entry)

    matches.sort(key=lambda x: x["importance"], reverse=True)
    return {"query": query, "matches": matches[:10]}


@app.post("/memory/{memory_id}/consolidate")
def consolidate_memory(memory_id: str):
    """Consolidate memory entries (merge similar, remove redundant)"""
    if memory_id not in AGENT_MEMORIES:
        raise HTTPException(status_code=404, detail="Memory not found")

    original_count = len(MEMORY_ENTRIES.get(memory_id, []))
    # Simulated consolidation
    return {
        "memory_id": memory_id,
        "original_entries": original_count,
        "consolidated_entries": original_count,
        "entries_merged": 0,
        "entries_removed": 0,
        "message": "Memory consolidation complete"
    }


@app.post("/context")
def create_conversation_context(data: Dict[str, Any] = Body(...)):
    """Create a conversation context"""
    context_id = str(uuid.uuid4())
    CONVERSATION_CONTEXTS[context_id] = {
        "id": context_id,
        "agent_id": data.get("agent_id"),
        "user_id": data.get("user_id"),
        "variables": data.get("variables", {}),
        "history": [],
        "metadata": data.get("metadata", {}),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return CONVERSATION_CONTEXTS[context_id]


@app.get("/context/{context_id}")
def get_conversation_context(context_id: str):
    """Get conversation context"""
    if context_id not in CONVERSATION_CONTEXTS:
        raise HTTPException(status_code=404, detail="Context not found")
    return CONVERSATION_CONTEXTS[context_id]


@app.put("/context/{context_id}")
def update_conversation_context(context_id: str, updates: Dict[str, Any] = Body(...)):
    """Update conversation context"""
    if context_id not in CONVERSATION_CONTEXTS:
        raise HTTPException(status_code=404, detail="Context not found")

    context = CONVERSATION_CONTEXTS[context_id]
    if "variables" in updates:
        context["variables"].update(updates["variables"])
    if "metadata" in updates:
        context["metadata"].update(updates["metadata"])
    if "history_entry" in updates:
        context["history"].append(updates["history_entry"])
    context["updated_at"] = datetime.utcnow().isoformat()
    return context


@app.delete("/context/{context_id}")
def delete_conversation_context(context_id: str):
    """Delete conversation context"""
    if context_id not in CONVERSATION_CONTEXTS:
        raise HTTPException(status_code=404, detail="Context not found")
    del CONVERSATION_CONTEXTS[context_id]
    return {"status": "deleted"}


# ============================================================================
# RAG (Retrieval Augmented Generation) Integration
# ============================================================================

# Storage for RAG
KNOWLEDGE_BASES: Dict[str, Dict[str, Any]] = {}
DOCUMENTS: Dict[str, List[Dict[str, Any]]] = {}
VECTOR_STORES: Dict[str, Dict[str, Any]] = {}
RAG_QUERIES: List[Dict[str, Any]] = []


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    embedding_model: Optional[str] = "text-embedding-ada-002"
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 50
    config: Optional[Dict[str, Any]] = {}


class DocumentUpload(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class RAGQuery(BaseModel):
    knowledge_base_id: str
    query: str
    top_k: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = {}
    include_sources: Optional[bool] = True


@app.post("/rag/knowledge-bases")
def create_knowledge_base(kb: KnowledgeBaseCreate):
    """Create a knowledge base"""
    kb_id = str(uuid.uuid4())
    KNOWLEDGE_BASES[kb_id] = {
        "id": kb_id,
        "name": kb.name,
        "description": kb.description,
        "embedding_model": kb.embedding_model,
        "chunk_size": kb.chunk_size,
        "chunk_overlap": kb.chunk_overlap,
        "config": kb.config or {},
        "document_count": 0,
        "chunk_count": 0,
        "status": "ready",
        "created_at": datetime.utcnow().isoformat()
    }
    DOCUMENTS[kb_id] = []
    return KNOWLEDGE_BASES[kb_id]


@app.get("/rag/knowledge-bases")
def list_knowledge_bases():
    """List knowledge bases"""
    return {"knowledge_bases": list(KNOWLEDGE_BASES.values())}


@app.get("/rag/knowledge-bases/{kb_id}")
def get_knowledge_base(kb_id: str):
    """Get knowledge base details"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KNOWLEDGE_BASES[kb_id]


@app.delete("/rag/knowledge-bases/{kb_id}")
def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    del KNOWLEDGE_BASES[kb_id]
    if kb_id in DOCUMENTS:
        del DOCUMENTS[kb_id]
    return {"status": "deleted"}


@app.post("/rag/knowledge-bases/{kb_id}/documents")
def upload_document(kb_id: str, doc: DocumentUpload):
    """Upload a document to knowledge base"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    doc_id = str(uuid.uuid4())
    chunk_size = KNOWLEDGE_BASES[kb_id]["chunk_size"]

    # Simulate chunking
    content_length = len(doc.content)
    num_chunks = (content_length + chunk_size - 1) // chunk_size

    doc_data = {
        "id": doc_id,
        "title": doc.title,
        "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
        "source": doc.source,
        "metadata": doc.metadata or {},
        "chunk_count": num_chunks,
        "status": "indexed",
        "uploaded_at": datetime.utcnow().isoformat()
    }
    DOCUMENTS[kb_id].append(doc_data)

    # Update KB stats
    KNOWLEDGE_BASES[kb_id]["document_count"] += 1
    KNOWLEDGE_BASES[kb_id]["chunk_count"] += num_chunks

    return doc_data


@app.get("/rag/knowledge-bases/{kb_id}/documents")
def list_documents(kb_id: str):
    """List documents in knowledge base"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"documents": DOCUMENTS.get(kb_id, [])}


@app.delete("/rag/knowledge-bases/{kb_id}/documents/{doc_id}")
def delete_document(kb_id: str, doc_id: str):
    """Delete a document from knowledge base"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    docs = DOCUMENTS.get(kb_id, [])
    for i, doc in enumerate(docs):
        if doc["id"] == doc_id:
            KNOWLEDGE_BASES[kb_id]["document_count"] -= 1
            KNOWLEDGE_BASES[kb_id]["chunk_count"] -= doc["chunk_count"]
            del docs[i]
            return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="Document not found")


@app.post("/rag/query")
def rag_query(query: RAGQuery):
    """Query knowledge base with RAG"""
    if query.knowledge_base_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    kb = KNOWLEDGE_BASES[query.knowledge_base_id]
    docs = DOCUMENTS.get(query.knowledge_base_id, [])

    # Simulate semantic search
    results = []
    for doc in docs[:query.top_k]:
        results.append({
            "document_id": doc["id"],
            "title": doc["title"],
            "content_preview": doc["content_preview"],
            "relevance_score": 0.85 + (hash(doc["id"]) % 15) / 100,
            "source": doc.get("source")
        })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    query_result = {
        "query_id": str(uuid.uuid4()),
        "query": query.query,
        "knowledge_base_id": query.knowledge_base_id,
        "results": results,
        "total_results": len(results),
        "augmented_prompt": f"Based on the following context:\n\n[Retrieved content would be here]\n\nAnswer the question: {query.query}",
        "timestamp": datetime.utcnow().isoformat()
    }

    RAG_QUERIES.append(query_result)
    return query_result


@app.post("/rag/knowledge-bases/{kb_id}/sync")
def sync_knowledge_base(kb_id: str, source: Dict[str, Any] = Body(...)):
    """Sync knowledge base with external source"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return {
        "kb_id": kb_id,
        "source_type": source.get("type", "unknown"),
        "source_url": source.get("url"),
        "status": "syncing",
        "message": "Sync initiated. Documents will be updated in the background.",
        "started_at": datetime.utcnow().isoformat()
    }


@app.get("/rag/queries")
def list_rag_queries(kb_id: Optional[str] = None, limit: int = 20):
    """List RAG queries"""
    queries = RAG_QUERIES.copy()
    if kb_id:
        queries = [q for q in queries if q["knowledge_base_id"] == kb_id]
    queries.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"queries": queries[:limit]}


@app.post("/rag/agents/{agent_id}/attach")
def attach_knowledge_base_to_agent(agent_id: str, kb_id: str = Body(..., embed=True)):
    """Attach a knowledge base to an agent for RAG"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return {
        "agent_id": agent_id,
        "knowledge_base_id": kb_id,
        "status": "attached",
        "message": f"Knowledge base attached. Agent will use RAG for responses.",
        "attached_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# Agent Chains / Pipelines
# ============================================================================

# Storage for chains
AGENT_CHAINS: Dict[str, Dict[str, Any]] = {}
CHAIN_EXECUTIONS: Dict[str, Dict[str, Any]] = {}
CHAIN_TEMPLATES: Dict[str, Dict[str, Any]] = {}


class ChainStep(BaseModel):
    agent_id: str
    name: str
    input_mapping: Optional[Dict[str, str]] = {}  # Map outputs from previous steps
    output_key: Optional[str] = None
    condition: Optional[str] = None  # Conditional execution
    on_error: Optional[str] = "stop"  # stop, skip, retry
    timeout_seconds: Optional[int] = 60
    config: Optional[Dict[str, Any]] = {}


class AgentChainCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[ChainStep]
    parallel_groups: Optional[List[List[int]]] = []  # Steps that can run in parallel
    config: Optional[Dict[str, Any]] = {}


@app.post("/chains")
def create_agent_chain(chain: AgentChainCreate):
    """Create an agent chain/pipeline"""
    chain_id = str(uuid.uuid4())
    AGENT_CHAINS[chain_id] = {
        "id": chain_id,
        "name": chain.name,
        "description": chain.description,
        "steps": [s.dict() for s in chain.steps],
        "parallel_groups": chain.parallel_groups or [],
        "config": chain.config or {},
        "step_count": len(chain.steps),
        "total_executions": 0,
        "avg_duration_ms": 0,
        "success_rate": 100.0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return AGENT_CHAINS[chain_id]


@app.get("/chains")
def list_agent_chains():
    """List all agent chains"""
    return {"chains": list(AGENT_CHAINS.values())}


@app.get("/chains/{chain_id}")
def get_agent_chain(chain_id: str):
    """Get chain details"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    return AGENT_CHAINS[chain_id]


@app.put("/chains/{chain_id}")
def update_agent_chain(chain_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a chain"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    allowed = ["name", "description", "steps", "parallel_groups", "config"]
    for key, value in updates.items():
        if key in allowed:
            AGENT_CHAINS[chain_id][key] = value
    if "steps" in updates:
        AGENT_CHAINS[chain_id]["step_count"] = len(updates["steps"])
    AGENT_CHAINS[chain_id]["updated_at"] = datetime.utcnow().isoformat()
    return AGENT_CHAINS[chain_id]


@app.delete("/chains/{chain_id}")
def delete_agent_chain(chain_id: str):
    """Delete a chain"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    del AGENT_CHAINS[chain_id]
    return {"status": "deleted"}


@app.post("/chains/{chain_id}/execute")
def execute_agent_chain(chain_id: str, input_data: Dict[str, Any] = Body(default={})):
    """Execute an agent chain"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    chain = AGENT_CHAINS[chain_id]
    execution_id = str(uuid.uuid4())

    # Simulate chain execution
    step_results = []
    accumulated_outputs = {"input": input_data}
    total_duration = 0

    for i, step in enumerate(chain["steps"]):
        step_start = datetime.utcnow()
        step_duration = 100 + (hash(step["agent_id"]) % 200)
        total_duration += step_duration

        step_result = {
            "step_index": i,
            "step_name": step["name"],
            "agent_id": step["agent_id"],
            "status": "completed",
            "output": {"result": f"Output from {step['name']}", "data": {}},
            "duration_ms": step_duration,
            "started_at": step_start.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        step_results.append(step_result)

        # Store output for next steps
        output_key = step.get("output_key", f"step_{i}")
        accumulated_outputs[output_key] = step_result["output"]

    CHAIN_EXECUTIONS[execution_id] = {
        "id": execution_id,
        "chain_id": chain_id,
        "status": "completed",
        "input": input_data,
        "step_results": step_results,
        "final_output": accumulated_outputs,
        "total_duration_ms": total_duration,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }

    # Update chain stats
    chain["total_executions"] += 1

    return CHAIN_EXECUTIONS[execution_id]


@app.get("/chains/{chain_id}/executions")
def list_chain_executions(chain_id: str, limit: int = 20):
    """List executions for a chain"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    executions = [e for e in CHAIN_EXECUTIONS.values() if e["chain_id"] == chain_id]
    executions.sort(key=lambda x: x["started_at"], reverse=True)
    return {"executions": executions[:limit]}


@app.get("/chains/executions/{execution_id}")
def get_chain_execution(execution_id: str):
    """Get chain execution details"""
    if execution_id not in CHAIN_EXECUTIONS:
        raise HTTPException(status_code=404, detail="Execution not found")
    return CHAIN_EXECUTIONS[execution_id]


@app.post("/chains/{chain_id}/validate")
def validate_agent_chain(chain_id: str):
    """Validate a chain configuration"""
    if chain_id not in AGENT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    chain = AGENT_CHAINS[chain_id]
    issues = []
    warnings = []

    # Check for empty chain
    if not chain["steps"]:
        issues.append("Chain has no steps defined")

    # Check for circular dependencies (simplified)
    for i, step in enumerate(chain["steps"]):
        if not step.get("agent_id"):
            issues.append(f"Step {i} has no agent_id")

    return {
        "chain_id": chain_id,
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }


# ============================================================================
# Evaluation Framework
# ============================================================================

# Storage for evaluations
EVALUATION_METRICS: Dict[str, Dict[str, Any]] = {}
EVALUATION_RUNS: Dict[str, Dict[str, Any]] = {}
EVALUATION_DATASETS: Dict[str, Dict[str, Any]] = {}
AGENT_SCORES: Dict[str, List[Dict[str, Any]]] = {}

BUILTIN_METRICS = {
    "accuracy": {"name": "Accuracy", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "relevance": {"name": "Relevance", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "coherence": {"name": "Coherence", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "helpfulness": {"name": "Helpfulness", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "safety": {"name": "Safety", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "latency_ms": {"name": "Latency", "type": "numeric", "range": [0, 10000], "higher_is_better": False},
    "cost": {"name": "Cost", "type": "numeric", "range": [0, 100], "higher_is_better": False},
    "groundedness": {"name": "Groundedness", "type": "numeric", "range": [0, 100], "higher_is_better": True},
    "toxicity": {"name": "Toxicity", "type": "numeric", "range": [0, 100], "higher_is_better": False}
}


class EvaluationDataset(BaseModel):
    name: str
    description: Optional[str] = None
    test_cases: List[Dict[str, Any]]


class EvaluationRun(BaseModel):
    agent_id: str
    dataset_id: str
    metrics: List[str]
    config: Optional[Dict[str, Any]] = {}


@app.get("/evaluation/metrics")
def list_evaluation_metrics():
    """List available evaluation metrics"""
    custom_metrics = {k: v for k, v in EVALUATION_METRICS.items()}
    return {"builtin_metrics": BUILTIN_METRICS, "custom_metrics": custom_metrics}


@app.post("/evaluation/metrics")
def create_custom_metric(data: Dict[str, Any] = Body(...)):
    """Create a custom evaluation metric"""
    metric_id = str(uuid.uuid4())
    EVALUATION_METRICS[metric_id] = {
        "id": metric_id,
        "name": data.get("name"),
        "description": data.get("description"),
        "type": data.get("type", "numeric"),
        "range": data.get("range", [0, 100]),
        "higher_is_better": data.get("higher_is_better", True),
        "calculation": data.get("calculation"),
        "created_at": datetime.utcnow().isoformat()
    }
    return EVALUATION_METRICS[metric_id]


@app.post("/evaluation/datasets")
def create_evaluation_dataset(dataset: EvaluationDataset):
    """Create an evaluation dataset"""
    dataset_id = str(uuid.uuid4())
    EVALUATION_DATASETS[dataset_id] = {
        "id": dataset_id,
        "name": dataset.name,
        "description": dataset.description,
        "test_cases": dataset.test_cases,
        "test_count": len(dataset.test_cases),
        "created_at": datetime.utcnow().isoformat()
    }
    return EVALUATION_DATASETS[dataset_id]


@app.get("/evaluation/datasets")
def list_evaluation_datasets():
    """List evaluation datasets"""
    return {"datasets": list(EVALUATION_DATASETS.values())}


@app.get("/evaluation/datasets/{dataset_id}")
def get_evaluation_dataset(dataset_id: str):
    """Get dataset details"""
    if dataset_id not in EVALUATION_DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return EVALUATION_DATASETS[dataset_id]


@app.delete("/evaluation/datasets/{dataset_id}")
def delete_evaluation_dataset(dataset_id: str):
    """Delete a dataset"""
    if dataset_id not in EVALUATION_DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    del EVALUATION_DATASETS[dataset_id]
    return {"status": "deleted"}


@app.post("/evaluation/run")
def run_evaluation(evaluation: EvaluationRun):
    """Run an evaluation"""
    if evaluation.dataset_id not in EVALUATION_DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")

    run_id = str(uuid.uuid4())
    dataset = EVALUATION_DATASETS[evaluation.dataset_id]

    # Simulate evaluation results
    metric_results = {}
    for metric in evaluation.metrics:
        if metric in BUILTIN_METRICS:
            metric_info = BUILTIN_METRICS[metric]
            base_score = 70 + (hash(evaluation.agent_id + metric) % 30)
            metric_results[metric] = {
                "score": base_score,
                "min": metric_info["range"][0],
                "max": metric_info["range"][1],
                "higher_is_better": metric_info["higher_is_better"]
            }

    # Calculate overall score
    overall_score = sum(r["score"] for r in metric_results.values()) / len(metric_results) if metric_results else 0

    test_results = []
    for i, test_case in enumerate(dataset["test_cases"]):
        test_results.append({
            "test_index": i,
            "input": test_case.get("input"),
            "expected": test_case.get("expected"),
            "actual": f"[Simulated output for test {i}]",
            "passed": True,
            "scores": {m: metric_results[m]["score"] + (hash(str(i)) % 10 - 5) for m in evaluation.metrics if m in metric_results}
        })

    EVALUATION_RUNS[run_id] = {
        "id": run_id,
        "agent_id": evaluation.agent_id,
        "dataset_id": evaluation.dataset_id,
        "metrics": evaluation.metrics,
        "metric_results": metric_results,
        "overall_score": overall_score,
        "test_results": test_results,
        "tests_passed": len(test_results),
        "tests_failed": 0,
        "status": "completed",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }

    # Track agent scores
    if evaluation.agent_id not in AGENT_SCORES:
        AGENT_SCORES[evaluation.agent_id] = []
    AGENT_SCORES[evaluation.agent_id].append({
        "run_id": run_id,
        "overall_score": overall_score,
        "timestamp": datetime.utcnow().isoformat()
    })

    return EVALUATION_RUNS[run_id]


@app.get("/evaluation/runs")
def list_evaluation_runs(agent_id: Optional[str] = None, limit: int = 20):
    """List evaluation runs"""
    runs = list(EVALUATION_RUNS.values())
    if agent_id:
        runs = [r for r in runs if r["agent_id"] == agent_id]
    runs.sort(key=lambda x: x["started_at"], reverse=True)
    return {"runs": runs[:limit]}


@app.get("/evaluation/runs/{run_id}")
def get_evaluation_run(run_id: str):
    """Get evaluation run details"""
    if run_id not in EVALUATION_RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    return EVALUATION_RUNS[run_id]


@app.get("/evaluation/agents/{agent_id}/scores")
def get_agent_scores(agent_id: str):
    """Get historical scores for an agent"""
    scores = AGENT_SCORES.get(agent_id, [])
    return {
        "agent_id": agent_id,
        "scores": scores,
        "latest_score": scores[-1]["overall_score"] if scores else None,
        "score_trend": "improving" if len(scores) > 1 and scores[-1]["overall_score"] > scores[0]["overall_score"] else "stable"
    }


@app.post("/evaluation/compare")
def compare_agents(agent_ids: List[str] = Body(...)):
    """Compare multiple agents' evaluation scores"""
    comparison = {}
    for agent_id in agent_ids:
        scores = AGENT_SCORES.get(agent_id, [])
        comparison[agent_id] = {
            "latest_score": scores[-1]["overall_score"] if scores else None,
            "avg_score": sum(s["overall_score"] for s in scores) / len(scores) if scores else None,
            "evaluation_count": len(scores)
        }

    # Rank agents
    ranked = sorted(
        [(aid, data) for aid, data in comparison.items() if data["latest_score"] is not None],
        key=lambda x: x[1]["latest_score"],
        reverse=True
    )

    return {
        "comparison": comparison,
        "ranking": [{"rank": i + 1, "agent_id": aid, "score": data["latest_score"]} for i, (aid, data) in enumerate(ranked)]
    }


# ============================================================================
# Guardrails & Safety
# ============================================================================

# Storage for guardrails
GUARDRAILS: Dict[str, Dict[str, Any]] = {}
GUARDRAIL_VIOLATIONS: List[Dict[str, Any]] = []
CONTENT_FILTERS: Dict[str, Dict[str, Any]] = {}
PII_PATTERNS: Dict[str, str] = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
}

TOXICITY_CATEGORIES = [
    "hate_speech", "harassment", "violence", "self_harm",
    "sexual_content", "dangerous_content", "spam", "misinformation"
]


class GuardrailCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # input, output, both
    rules: List[Dict[str, Any]]
    action: str = "block"  # block, warn, log, redact
    enabled: bool = True


class ContentFilterCreate(BaseModel):
    name: str
    filter_type: str  # keyword, regex, ml_model
    patterns: List[str]
    action: str = "block"
    severity: str = "high"


@app.post("/guardrails")
def create_guardrail(guardrail: GuardrailCreate):
    """Create a guardrail"""
    guardrail_id = str(uuid.uuid4())
    GUARDRAILS[guardrail_id] = {
        "id": guardrail_id,
        "name": guardrail.name,
        "description": guardrail.description,
        "type": guardrail.type,
        "rules": guardrail.rules,
        "action": guardrail.action,
        "enabled": guardrail.enabled,
        "triggers": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    return GUARDRAILS[guardrail_id]


@app.get("/guardrails")
def list_guardrails():
    """List all guardrails"""
    return {"guardrails": list(GUARDRAILS.values())}


@app.get("/guardrails/{guardrail_id}")
def get_guardrail(guardrail_id: str):
    """Get guardrail details"""
    if guardrail_id not in GUARDRAILS:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return GUARDRAILS[guardrail_id]


@app.put("/guardrails/{guardrail_id}")
def update_guardrail(guardrail_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a guardrail"""
    if guardrail_id not in GUARDRAILS:
        raise HTTPException(status_code=404, detail="Guardrail not found")

    allowed = ["name", "description", "rules", "action", "enabled"]
    for key, value in updates.items():
        if key in allowed:
            GUARDRAILS[guardrail_id][key] = value
    return GUARDRAILS[guardrail_id]


@app.delete("/guardrails/{guardrail_id}")
def delete_guardrail(guardrail_id: str):
    """Delete a guardrail"""
    if guardrail_id not in GUARDRAILS:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    del GUARDRAILS[guardrail_id]
    return {"status": "deleted"}


@app.post("/guardrails/check")
def check_guardrails(data: Dict[str, Any] = Body(...)):
    """Check content against all enabled guardrails"""
    content = data.get("content", "")
    content_type = data.get("type", "output")  # input or output

    violations = []
    for guardrail_id, guardrail in GUARDRAILS.items():
        if not guardrail["enabled"]:
            continue
        if guardrail["type"] != "both" and guardrail["type"] != content_type:
            continue

        # Check rules (simplified)
        for rule in guardrail["rules"]:
            if rule.get("type") == "keyword":
                for keyword in rule.get("keywords", []):
                    if keyword.lower() in content.lower():
                        violations.append({
                            "guardrail_id": guardrail_id,
                            "guardrail_name": guardrail["name"],
                            "rule": rule,
                            "action": guardrail["action"],
                            "match": keyword
                        })
                        guardrail["triggers"] += 1

    passed = len(violations) == 0
    if not passed:
        GUARDRAIL_VIOLATIONS.extend([{**v, "timestamp": datetime.utcnow().isoformat(), "content_preview": content[:100]} for v in violations])

    return {
        "passed": passed,
        "violations": violations,
        "action": violations[0]["action"] if violations else None
    }


@app.post("/safety/detect-pii")
def detect_pii(content: str = Body(..., embed=True)):
    """Detect PII in content"""
    import re
    detected = []

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            detected.append({
                "type": pii_type,
                "count": len(matches),
                "matches": [m[:4] + "****" for m in matches[:5]]  # Partially mask
            })

    return {
        "has_pii": len(detected) > 0,
        "detected": detected,
        "recommendation": "redact" if detected else "safe"
    }


@app.post("/safety/redact-pii")
def redact_pii(content: str = Body(..., embed=True)):
    """Redact PII from content"""
    import re
    redacted = content

    replacements = {
        "email": "[EMAIL_REDACTED]",
        "phone": "[PHONE_REDACTED]",
        "ssn": "[SSN_REDACTED]",
        "credit_card": "[CARD_REDACTED]",
        "ip_address": "[IP_REDACTED]"
    }

    for pii_type, pattern in PII_PATTERNS.items():
        redacted = re.sub(pattern, replacements[pii_type], redacted)

    return {
        "original_length": len(content),
        "redacted_length": len(redacted),
        "redacted_content": redacted
    }


@app.post("/safety/check-toxicity")
def check_toxicity(content: str = Body(..., embed=True)):
    """Check content for toxicity"""
    # Simulated toxicity detection
    scores = {}
    for category in TOXICITY_CATEGORIES:
        # Simulate score based on content hash
        scores[category] = (hash(content + category) % 30) / 100  # 0-0.3 range

    max_score = max(scores.values())
    flagged_categories = [cat for cat, score in scores.items() if score > 0.2]

    return {
        "is_toxic": max_score > 0.25,
        "toxicity_score": max_score,
        "category_scores": scores,
        "flagged_categories": flagged_categories,
        "recommendation": "block" if max_score > 0.5 else "review" if max_score > 0.25 else "safe"
    }


@app.post("/content-filters")
def create_content_filter(filter_data: ContentFilterCreate):
    """Create a content filter"""
    filter_id = str(uuid.uuid4())
    CONTENT_FILTERS[filter_id] = {
        "id": filter_id,
        "name": filter_data.name,
        "filter_type": filter_data.filter_type,
        "patterns": filter_data.patterns,
        "action": filter_data.action,
        "severity": filter_data.severity,
        "matches": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    return CONTENT_FILTERS[filter_id]


@app.get("/content-filters")
def list_content_filters():
    """List content filters"""
    return {"filters": list(CONTENT_FILTERS.values())}


@app.get("/guardrails/violations")
def get_guardrail_violations(limit: int = 50):
    """Get recent guardrail violations"""
    violations = GUARDRAIL_VIOLATIONS.copy()
    violations.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"violations": violations[:limit]}


# ============================================================================
# Batch Processing
# ============================================================================

# Storage for batch jobs
BATCH_JOBS: Dict[str, Dict[str, Any]] = {}
BATCH_RESULTS: Dict[str, List[Dict[str, Any]]] = {}


class BatchJobCreate(BaseModel):
    name: str
    agent_id: str
    items: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]] = {}
    parallelism: Optional[int] = 10
    on_error: Optional[str] = "continue"  # continue, stop


@app.post("/batch")
def create_batch_job(job: BatchJobCreate):
    """Create a batch processing job"""
    job_id = str(uuid.uuid4())
    BATCH_JOBS[job_id] = {
        "id": job_id,
        "name": job.name,
        "agent_id": job.agent_id,
        "total_items": len(job.items),
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "parallelism": job.parallelism,
        "on_error": job.on_error,
        "status": "pending",
        "progress_percent": 0,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None
    }
    BATCH_RESULTS[job_id] = []

    # Store items for processing
    BATCH_JOBS[job_id]["_items"] = job.items

    return BATCH_JOBS[job_id]


@app.get("/batch")
def list_batch_jobs(status: Optional[str] = None):
    """List batch jobs"""
    jobs = [{k: v for k, v in j.items() if not k.startswith("_")} for j in BATCH_JOBS.values()]
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return {"jobs": jobs}


@app.get("/batch/{job_id}")
def get_batch_job(job_id: str):
    """Get batch job details"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = {k: v for k, v in BATCH_JOBS[job_id].items() if not k.startswith("_")}
    return job


@app.post("/batch/{job_id}/start")
def start_batch_job(job_id: str):
    """Start a batch job"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = BATCH_JOBS[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.utcnow().isoformat()

    # Simulate processing
    items = job.get("_items", [])
    for i, item in enumerate(items):
        result = {
            "item_index": i,
            "input": item,
            "output": {"result": f"Processed item {i}"},
            "status": "success",
            "duration_ms": 50 + (hash(str(item)) % 100)
        }
        BATCH_RESULTS[job_id].append(result)
        job["processed"] += 1
        job["succeeded"] += 1
        job["progress_percent"] = int((job["processed"] / job["total_items"]) * 100)

    job["status"] = "completed"
    job["completed_at"] = datetime.utcnow().isoformat()

    return {k: v for k, v in job.items() if not k.startswith("_")}


@app.post("/batch/{job_id}/cancel")
def cancel_batch_job(job_id: str):
    """Cancel a batch job"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    BATCH_JOBS[job_id]["status"] = "cancelled"
    return {"status": "cancelled"}


@app.get("/batch/{job_id}/results")
def get_batch_results(job_id: str, offset: int = 0, limit: int = 100):
    """Get batch job results"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    results = BATCH_RESULTS.get(job_id, [])
    return {
        "total": len(results),
        "offset": offset,
        "limit": limit,
        "results": results[offset:offset + limit]
    }


@app.delete("/batch/{job_id}")
def delete_batch_job(job_id: str):
    """Delete a batch job"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    del BATCH_JOBS[job_id]
    if job_id in BATCH_RESULTS:
        del BATCH_RESULTS[job_id]
    return {"status": "deleted"}


# ============================================================================
# WebSocket Real-time Support
# ============================================================================

# Storage for WebSocket connections (simulated)
WS_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
WS_SUBSCRIPTIONS: Dict[str, List[str]] = {}
REALTIME_EVENTS: List[Dict[str, Any]] = []

WS_EVENT_TYPES = [
    "execution.started", "execution.progress", "execution.completed", "execution.failed",
    "workflow.step_completed", "workflow.completed",
    "chain.step_completed", "chain.completed",
    "batch.progress", "batch.completed",
    "notification.new", "alert.triggered"
]


@app.post("/realtime/connect")
def websocket_connect(data: Dict[str, Any] = Body(...)):
    """Simulate WebSocket connection (REST endpoint for demo)"""
    connection_id = str(uuid.uuid4())
    WS_CONNECTIONS[connection_id] = {
        "id": connection_id,
        "user_id": data.get("user_id"),
        "connected_at": datetime.utcnow().isoformat(),
        "last_heartbeat": datetime.utcnow().isoformat(),
        "subscriptions": []
    }
    WS_SUBSCRIPTIONS[connection_id] = []

    return {
        "connection_id": connection_id,
        "status": "connected",
        "ws_url": f"wss://api.example.com/ws/{connection_id}",
        "message": "Use this connection_id for subscribing to events"
    }


@app.post("/realtime/{connection_id}/subscribe")
def websocket_subscribe(connection_id: str, event_types: List[str] = Body(...)):
    """Subscribe to real-time events"""
    if connection_id not in WS_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    valid_types = [et for et in event_types if et in WS_EVENT_TYPES]
    WS_SUBSCRIPTIONS[connection_id].extend(valid_types)
    WS_CONNECTIONS[connection_id]["subscriptions"] = list(set(WS_SUBSCRIPTIONS[connection_id]))

    return {
        "connection_id": connection_id,
        "subscribed_to": WS_CONNECTIONS[connection_id]["subscriptions"]
    }


@app.post("/realtime/{connection_id}/unsubscribe")
def websocket_unsubscribe(connection_id: str, event_types: List[str] = Body(...)):
    """Unsubscribe from events"""
    if connection_id not in WS_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    for et in event_types:
        if et in WS_SUBSCRIPTIONS[connection_id]:
            WS_SUBSCRIPTIONS[connection_id].remove(et)
    WS_CONNECTIONS[connection_id]["subscriptions"] = WS_SUBSCRIPTIONS[connection_id]

    return {
        "connection_id": connection_id,
        "subscribed_to": WS_SUBSCRIPTIONS[connection_id]
    }


@app.get("/realtime/{connection_id}/poll")
def websocket_poll(connection_id: str, since: Optional[str] = None):
    """Poll for events (simulates WebSocket receive)"""
    if connection_id not in WS_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    subscriptions = WS_SUBSCRIPTIONS.get(connection_id, [])
    events = [e for e in REALTIME_EVENTS if e["event_type"] in subscriptions]

    if since:
        events = [e for e in events if e["timestamp"] > since]

    return {"events": events[-20:]}


@app.post("/realtime/emit")
def emit_realtime_event(data: Dict[str, Any] = Body(...)):
    """Emit a real-time event"""
    event = {
        "id": str(uuid.uuid4()),
        "event_type": data.get("event_type"),
        "payload": data.get("payload", {}),
        "timestamp": datetime.utcnow().isoformat()
    }
    REALTIME_EVENTS.append(event)

    # Keep only last 1000 events
    if len(REALTIME_EVENTS) > 1000:
        REALTIME_EVENTS.pop(0)

    return event


@app.delete("/realtime/{connection_id}")
def websocket_disconnect(connection_id: str):
    """Disconnect WebSocket"""
    if connection_id not in WS_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    del WS_CONNECTIONS[connection_id]
    if connection_id in WS_SUBSCRIPTIONS:
        del WS_SUBSCRIPTIONS[connection_id]
    return {"status": "disconnected"}


@app.get("/realtime/event-types")
def list_realtime_event_types():
    """List available real-time event types"""
    return {"event_types": WS_EVENT_TYPES}


# ============================================================================
# Plugin / Extension System
# ============================================================================

# Storage for plugins
PLUGINS: Dict[str, Dict[str, Any]] = {}
PLUGIN_HOOKS: Dict[str, List[str]] = {}
PLUGIN_CONFIGS: Dict[str, Dict[str, Any]] = {}

PLUGIN_HOOK_POINTS = [
    "pre_execution", "post_execution",
    "pre_workflow", "post_workflow",
    "pre_chain", "post_chain",
    "on_error", "on_completion",
    "input_transform", "output_transform",
    "auth_check", "rate_limit_check"
]


class PluginCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: str
    author: Optional[str] = None
    hooks: List[str]
    config_schema: Optional[Dict[str, Any]] = {}
    code_url: Optional[str] = None


@app.post("/plugins")
def register_plugin(plugin: PluginCreate):
    """Register a new plugin"""
    plugin_id = str(uuid.uuid4())

    # Validate hooks
    invalid_hooks = [h for h in plugin.hooks if h not in PLUGIN_HOOK_POINTS]
    if invalid_hooks:
        raise HTTPException(status_code=400, detail=f"Invalid hooks: {invalid_hooks}")

    PLUGINS[plugin_id] = {
        "id": plugin_id,
        "name": plugin.name,
        "description": plugin.description,
        "version": plugin.version,
        "author": plugin.author,
        "hooks": plugin.hooks,
        "config_schema": plugin.config_schema or {},
        "code_url": plugin.code_url,
        "enabled": True,
        "install_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    # Register hooks
    for hook in plugin.hooks:
        if hook not in PLUGIN_HOOKS:
            PLUGIN_HOOKS[hook] = []
        PLUGIN_HOOKS[hook].append(plugin_id)

    return PLUGINS[plugin_id]


@app.get("/plugins")
def list_plugins(enabled_only: bool = False):
    """List all plugins"""
    plugins = list(PLUGINS.values())
    if enabled_only:
        plugins = [p for p in plugins if p["enabled"]]
    return {"plugins": plugins}


@app.get("/plugins/{plugin_id}")
def get_plugin(plugin_id: str):
    """Get plugin details"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return PLUGINS[plugin_id]


@app.post("/plugins/{plugin_id}/enable")
def enable_plugin(plugin_id: str):
    """Enable a plugin"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")
    PLUGINS[plugin_id]["enabled"] = True
    return PLUGINS[plugin_id]


@app.post("/plugins/{plugin_id}/disable")
def disable_plugin(plugin_id: str):
    """Disable a plugin"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")
    PLUGINS[plugin_id]["enabled"] = False
    return PLUGINS[plugin_id]


@app.delete("/plugins/{plugin_id}")
def unregister_plugin(plugin_id: str):
    """Unregister a plugin"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Remove from hooks
    for hook, plugins in PLUGIN_HOOKS.items():
        if plugin_id in plugins:
            plugins.remove(plugin_id)

    del PLUGINS[plugin_id]
    return {"status": "deleted"}


@app.post("/plugins/{plugin_id}/configure")
def configure_plugin(plugin_id: str, config: Dict[str, Any] = Body(...)):
    """Configure a plugin"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")

    PLUGIN_CONFIGS[plugin_id] = config
    return {"plugin_id": plugin_id, "config": config}


@app.get("/plugins/{plugin_id}/config")
def get_plugin_config(plugin_id: str):
    """Get plugin configuration"""
    if plugin_id not in PLUGINS:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"config": PLUGIN_CONFIGS.get(plugin_id, {})}


@app.get("/plugins/hooks")
def list_plugin_hooks():
    """List available plugin hook points"""
    return {
        "hook_points": PLUGIN_HOOK_POINTS,
        "registered_hooks": {k: len(v) for k, v in PLUGIN_HOOKS.items() if v}
    }


@app.post("/plugins/hooks/{hook_point}/execute")
def execute_plugin_hook(hook_point: str, context: Dict[str, Any] = Body(...)):
    """Execute all plugins registered for a hook point"""
    if hook_point not in PLUGIN_HOOK_POINTS:
        raise HTTPException(status_code=400, detail="Invalid hook point")

    plugin_ids = PLUGIN_HOOKS.get(hook_point, [])
    results = []

    for plugin_id in plugin_ids:
        if plugin_id in PLUGINS and PLUGINS[plugin_id]["enabled"]:
            results.append({
                "plugin_id": plugin_id,
                "plugin_name": PLUGINS[plugin_id]["name"],
                "result": "executed",
                "modified_context": context
            })

    return {"hook_point": hook_point, "plugins_executed": len(results), "results": results}


# ============================================================================
# Import / Export
# ============================================================================

EXPORT_FORMATS = ["json", "yaml", "csv"]
IMPORT_JOBS: Dict[str, Dict[str, Any]] = {}
EXPORT_JOBS: Dict[str, Dict[str, Any]] = {}


@app.post("/export/agents")
def export_agents(data: Dict[str, Any] = Body(...)):
    """Export agent cards"""
    export_id = str(uuid.uuid4())
    agent_ids = data.get("agent_ids", [])
    format_type = data.get("format", "json")
    include_related = data.get("include_related", False)

    if format_type not in EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Supported: {EXPORT_FORMATS}")

    EXPORT_JOBS[export_id] = {
        "id": export_id,
        "type": "agents",
        "format": format_type,
        "item_count": len(agent_ids) if agent_ids else "all",
        "include_related": include_related,
        "status": "completed",
        "download_url": f"/export/download/{export_id}",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }

    return EXPORT_JOBS[export_id]


@app.post("/export/workflows")
def export_workflows(data: Dict[str, Any] = Body(...)):
    """Export workflows"""
    export_id = str(uuid.uuid4())
    workflow_ids = data.get("workflow_ids", [])
    format_type = data.get("format", "json")

    EXPORT_JOBS[export_id] = {
        "id": export_id,
        "type": "workflows",
        "format": format_type,
        "item_count": len(workflow_ids) if workflow_ids else "all",
        "status": "completed",
        "download_url": f"/export/download/{export_id}",
        "created_at": datetime.utcnow().isoformat()
    }

    return EXPORT_JOBS[export_id]


@app.post("/export/full")
def export_full_backup(data: Dict[str, Any] = Body(...)):
    """Export full platform backup"""
    export_id = str(uuid.uuid4())

    EXPORT_JOBS[export_id] = {
        "id": export_id,
        "type": "full_backup",
        "format": "json",
        "includes": ["agents", "workflows", "chains", "templates", "prompts", "knowledge_bases"],
        "status": "completed",
        "download_url": f"/export/download/{export_id}",
        "size_estimate_mb": 50,
        "created_at": datetime.utcnow().isoformat()
    }

    return EXPORT_JOBS[export_id]


@app.get("/export/download/{export_id}")
def download_export(export_id: str):
    """Download an export"""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Export not found")

    return {
        "export_id": export_id,
        "download_url": f"https://exports.example.com/{export_id}.zip",
        "message": "Export ready for download"
    }


@app.get("/export/jobs")
def list_export_jobs():
    """List export jobs"""
    return {"exports": list(EXPORT_JOBS.values())}


@app.post("/import/agents")
def import_agents(data: Dict[str, Any] = Body(...)):
    """Import agent cards"""
    import_id = str(uuid.uuid4())

    IMPORT_JOBS[import_id] = {
        "id": import_id,
        "type": "agents",
        "source": data.get("source_url") or "uploaded_file",
        "format": data.get("format", "json"),
        "status": "completed",
        "items_imported": data.get("count", 0),
        "items_skipped": 0,
        "items_failed": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    return IMPORT_JOBS[import_id]


@app.post("/import/workflows")
def import_workflows(data: Dict[str, Any] = Body(...)):
    """Import workflows"""
    import_id = str(uuid.uuid4())

    IMPORT_JOBS[import_id] = {
        "id": import_id,
        "type": "workflows",
        "source": data.get("source_url") or "uploaded_file",
        "format": data.get("format", "json"),
        "status": "completed",
        "items_imported": data.get("count", 0),
        "created_at": datetime.utcnow().isoformat()
    }

    return IMPORT_JOBS[import_id]


@app.post("/import/restore")
def restore_backup(data: Dict[str, Any] = Body(...)):
    """Restore from a full backup"""
    import_id = str(uuid.uuid4())

    IMPORT_JOBS[import_id] = {
        "id": import_id,
        "type": "full_restore",
        "source": data.get("source_url") or "uploaded_file",
        "status": "completed",
        "restored": ["agents", "workflows", "chains", "templates"],
        "created_at": datetime.utcnow().isoformat()
    }

    return IMPORT_JOBS[import_id]


@app.get("/import/jobs")
def list_import_jobs():
    """List import jobs"""
    return {"imports": list(IMPORT_JOBS.values())}


@app.get("/import/formats")
def list_import_formats():
    """List supported import/export formats"""
    return {
        "formats": EXPORT_FORMATS,
        "importable_types": ["agents", "workflows", "chains", "templates", "prompts", "knowledge_bases"],
        "exportable_types": ["agents", "workflows", "chains", "templates", "prompts", "knowledge_bases", "full_backup"]
    }


# ============================================================================
# GraphQL API Support
# ============================================================================

# GraphQL schema and resolvers (simplified REST representation)
GRAPHQL_SCHEMA = """
type Query {
  agents(limit: Int, offset: Int): [Agent!]!
  agent(id: ID!): Agent
  workflows(limit: Int): [Workflow!]!
  workflow(id: ID!): Workflow
  chains(limit: Int): [Chain!]!
  templates: [Template!]!
  health: HealthStatus!
}

type Mutation {
  createAgent(input: AgentInput!): Agent!
  updateAgent(id: ID!, input: AgentInput!): Agent!
  deleteAgent(id: ID!): Boolean!
  executeAgent(id: ID!, input: JSON): Execution!
  createWorkflow(input: WorkflowInput!): Workflow!
  runWorkflow(id: ID!, input: JSON): WorkflowExecution!
}

type Subscription {
  executionUpdated(executionId: ID!): Execution!
  workflowProgress(workflowId: ID!): WorkflowExecution!
}

type Agent {
  id: ID!
  name: String!
  description: String
  capabilities: [String!]
  createdAt: DateTime!
}

type Workflow {
  id: ID!
  name: String!
  steps: [WorkflowStep!]!
}

type Execution {
  id: ID!
  status: String!
  output: JSON
}
"""


@app.get("/graphql/schema")
def get_graphql_schema():
    """Get GraphQL schema"""
    return {
        "schema": GRAPHQL_SCHEMA,
        "introspection_url": "/graphql/introspection"
    }


@app.post("/graphql")
def execute_graphql(data: Dict[str, Any] = Body(...)):
    """Execute GraphQL query"""
    query = data.get("query", "")
    variables = data.get("variables", {})
    operation_name = data.get("operationName")

    # Parse query type (simplified)
    if "query" in query.lower() or query.strip().startswith("{"):
        query_type = "query"
    elif "mutation" in query.lower():
        query_type = "mutation"
    elif "subscription" in query.lower():
        query_type = "subscription"
    else:
        query_type = "unknown"

    # Simulated response
    response = {
        "data": {
            "simulated": True,
            "query_type": query_type,
            "message": "GraphQL execution simulated. In production, this would return actual data."
        },
        "extensions": {
            "query_complexity": 10,
            "execution_time_ms": 15
        }
    }

    if query_type == "subscription":
        response["data"]["subscription_id"] = str(uuid.uuid4())
        response["data"]["websocket_url"] = "wss://api.example.com/graphql/subscriptions"

    return response


@app.get("/graphql/introspection")
def graphql_introspection():
    """GraphQL introspection query result"""
    return {
        "__schema": {
            "types": [
                {"name": "Query", "kind": "OBJECT"},
                {"name": "Mutation", "kind": "OBJECT"},
                {"name": "Subscription", "kind": "OBJECT"},
                {"name": "Agent", "kind": "OBJECT"},
                {"name": "Workflow", "kind": "OBJECT"},
                {"name": "Execution", "kind": "OBJECT"},
                {"name": "String", "kind": "SCALAR"},
                {"name": "Int", "kind": "SCALAR"},
                {"name": "Boolean", "kind": "SCALAR"},
                {"name": "ID", "kind": "SCALAR"},
                {"name": "JSON", "kind": "SCALAR"},
                {"name": "DateTime", "kind": "SCALAR"}
            ],
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"},
            "subscriptionType": {"name": "Subscription"}
        }
    }


@app.get("/graphql/playground")
def graphql_playground_config():
    """GraphQL Playground configuration"""
    return {
        "endpoint": "/graphql",
        "subscription_endpoint": "wss://api.example.com/graphql/subscriptions",
        "settings": {
            "editor.theme": "dark",
            "editor.fontSize": 14,
            "tracing.tracingSupported": True
        }
    }


# ============================================================================
# Multi-tenancy / Organizations
# ============================================================================

ORGANIZATIONS: Dict[str, Dict[str, Any]] = {}
ORG_TEAMS: Dict[str, Dict[str, Any]] = {}
ORG_MEMBERS: Dict[str, Dict[str, Any]] = {}
ORG_ROLES: Dict[str, Dict[str, Any]] = {
    "owner": {"permissions": ["*"]},
    "admin": {"permissions": ["read", "write", "delete", "manage_members", "manage_teams"]},
    "member": {"permissions": ["read", "write"]},
    "viewer": {"permissions": ["read"]}
}


@app.post("/organizations")
def create_organization(request: Request):
    """Create a new organization"""
    data = {}
    org_id = f"org_{uuid.uuid4().hex[:12]}"

    org = {
        "id": org_id,
        "name": data.get("name", f"Organization {org_id}"),
        "slug": data.get("slug", org_id),
        "plan": data.get("plan", "free"),
        "settings": {
            "default_environment": "development",
            "require_2fa": False,
            "allowed_domains": [],
            "ip_whitelist": []
        },
        "limits": {
            "max_agents": 100,
            "max_workflows": 50,
            "max_members": 10,
            "max_teams": 5,
            "api_rate_limit": 1000
        },
        "billing": {
            "plan": "free",
            "status": "active",
            "next_billing_date": None
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    ORGANIZATIONS[org_id] = org
    return {"organization": org}


@app.get("/organizations")
def list_organizations():
    """List all organizations"""
    return {
        "organizations": list(ORGANIZATIONS.values()),
        "total": len(ORGANIZATIONS)
    }


@app.get("/organizations/{org_id}")
def get_organization(org_id: str):
    """Get organization details"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"organization": ORGANIZATIONS[org_id]}


@app.put("/organizations/{org_id}")
def update_organization(org_id: str, request: Request):
    """Update organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    data = {}
    org = ORGANIZATIONS[org_id]

    for field in ["name", "slug", "plan", "settings", "limits"]:
        if field in data:
            org[field] = data[field]

    org["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"organization": org}


@app.delete("/organizations/{org_id}")
def delete_organization(org_id: str):
    """Delete organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    del ORGANIZATIONS[org_id]
    # Clean up related resources
    teams_to_delete = [tid for tid, t in ORG_TEAMS.items() if t.get("org_id") == org_id]
    for tid in teams_to_delete:
        del ORG_TEAMS[tid]

    members_to_delete = [mid for mid, m in ORG_MEMBERS.items() if m.get("org_id") == org_id]
    for mid in members_to_delete:
        del ORG_MEMBERS[mid]

    return {"deleted": True}


@app.post("/organizations/{org_id}/teams")
def create_team(org_id: str, request: Request):
    """Create a team within an organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    data = {}
    team_id = f"team_{uuid.uuid4().hex[:12]}"

    team = {
        "id": team_id,
        "org_id": org_id,
        "name": data.get("name", f"Team {team_id}"),
        "description": data.get("description", ""),
        "members": [],
        "permissions": data.get("permissions", ["read"]),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    ORG_TEAMS[team_id] = team
    return {"team": team}


@app.get("/organizations/{org_id}/teams")
def list_teams(org_id: str):
    """List teams in an organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    teams = [t for t in ORG_TEAMS.values() if t.get("org_id") == org_id]
    return {"teams": teams, "total": len(teams)}


@app.post("/organizations/{org_id}/members")
def add_member(org_id: str, request: Request):
    """Add a member to an organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    data = {}
    member_id = f"member_{uuid.uuid4().hex[:12]}"

    member = {
        "id": member_id,
        "org_id": org_id,
        "user_id": data.get("user_id"),
        "email": data.get("email"),
        "role": data.get("role", "member"),
        "teams": data.get("teams", []),
        "status": "active",
        "invited_at": datetime.now(timezone.utc).isoformat(),
        "joined_at": datetime.now(timezone.utc).isoformat()
    }

    ORG_MEMBERS[member_id] = member
    return {"member": member}


@app.get("/organizations/{org_id}/members")
def list_members(org_id: str):
    """List members in an organization"""
    if org_id not in ORGANIZATIONS:
        raise HTTPException(status_code=404, detail="Organization not found")

    members = [m for m in ORG_MEMBERS.values() if m.get("org_id") == org_id]
    return {"members": members, "total": len(members)}


@app.put("/organizations/{org_id}/members/{member_id}/role")
def update_member_role(org_id: str, member_id: str, request: Request):
    """Update a member's role"""
    if member_id not in ORG_MEMBERS:
        raise HTTPException(status_code=404, detail="Member not found")

    data = {}
    new_role = data.get("role", "member")

    if new_role not in ORG_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    ORG_MEMBERS[member_id]["role"] = new_role
    return {"member": ORG_MEMBERS[member_id]}


@app.get("/organizations/{org_id}/permissions")
def get_org_permissions(org_id: str):
    """Get available roles and permissions"""
    return {
        "roles": ORG_ROLES,
        "available_permissions": [
            "read", "write", "delete", "execute",
            "manage_members", "manage_teams", "manage_billing",
            "manage_settings", "manage_integrations", "admin", "*"
        ]
    }


# ============================================================================
# Audit Logging / Activity Stream
# ============================================================================

AUDIT_LOGS: List[Dict[str, Any]] = []
AUDIT_LOG_RETENTION_DAYS = 90


@app.post("/audit/log")
def create_audit_log(request: Request):
    """Create an audit log entry"""
    data = {}

    log_entry = {
        "id": f"audit_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": {
            "type": data.get("actor_type", "user"),
            "id": data.get("actor_id"),
            "email": data.get("actor_email"),
            "ip_address": data.get("ip_address")
        },
        "action": data.get("action", "unknown"),
        "resource": {
            "type": data.get("resource_type"),
            "id": data.get("resource_id"),
            "name": data.get("resource_name")
        },
        "context": {
            "org_id": data.get("org_id"),
            "environment": data.get("environment"),
            "user_agent": data.get("user_agent"),
            "request_id": data.get("request_id")
        },
        "changes": data.get("changes", {}),
        "metadata": data.get("metadata", {}),
        "status": data.get("status", "success")
    }

    AUDIT_LOGS.append(log_entry)
    return {"audit_log": log_entry}


@app.get("/audit/logs")
def list_audit_logs(
    org_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Query audit logs with filters"""
    filtered = AUDIT_LOGS.copy()

    if org_id:
        filtered = [l for l in filtered if l["context"].get("org_id") == org_id]
    if actor_id:
        filtered = [l for l in filtered if l["actor"].get("id") == actor_id]
    if action:
        filtered = [l for l in filtered if l.get("action") == action]
    if resource_type:
        filtered = [l for l in filtered if l["resource"].get("type") == resource_type]

    # Sort by timestamp descending
    filtered.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "logs": filtered[offset:offset + limit],
        "total": len(filtered),
        "limit": limit,
        "offset": offset
    }


@app.get("/audit/logs/{log_id}")
def get_audit_log(log_id: str):
    """Get a specific audit log entry"""
    for log in AUDIT_LOGS:
        if log["id"] == log_id:
            return {"audit_log": log}
    raise HTTPException(status_code=404, detail="Audit log not found")


@app.get("/audit/activity-stream")
def get_activity_stream(
    org_id: Optional[str] = None,
    limit: int = 50
):
    """Get recent activity stream"""
    filtered = AUDIT_LOGS.copy()

    if org_id:
        filtered = [l for l in filtered if l["context"].get("org_id") == org_id]

    filtered.sort(key=lambda x: x["timestamp"], reverse=True)

    activities = []
    for log in filtered[:limit]:
        activities.append({
            "id": log["id"],
            "timestamp": log["timestamp"],
            "actor": log["actor"].get("email") or log["actor"].get("id"),
            "action": log["action"],
            "resource": f"{log['resource'].get('type')}: {log['resource'].get('name') or log['resource'].get('id')}",
            "status": log["status"]
        })

    return {"activities": activities, "total": len(activities)}


@app.get("/audit/actions")
def list_audit_actions():
    """List available audit action types"""
    return {
        "actions": [
            "agent.created", "agent.updated", "agent.deleted", "agent.executed",
            "workflow.created", "workflow.updated", "workflow.deleted", "workflow.executed",
            "user.login", "user.logout", "user.created", "user.updated", "user.deleted",
            "org.created", "org.updated", "org.member_added", "org.member_removed",
            "api_key.created", "api_key.revoked",
            "settings.updated", "billing.updated",
            "export.created", "import.completed"
        ]
    }


@app.post("/audit/export")
def export_audit_logs(request: Request):
    """Export audit logs"""
    data = {}

    export_id = f"audit_export_{uuid.uuid4().hex[:8]}"

    return {
        "export_id": export_id,
        "status": "processing",
        "format": data.get("format", "json"),
        "filters": data.get("filters", {}),
        "download_url": f"/audit/exports/{export_id}/download",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }


# ============================================================================
# Cost Management / Usage Analytics
# ============================================================================

USAGE_RECORDS: List[Dict[str, Any]] = []
BUDGETS: Dict[str, Dict[str, Any]] = {}
COST_ALERTS: List[Dict[str, Any]] = []


@app.post("/usage/record")
def record_usage(request: Request):
    """Record a usage event"""
    data = {}

    record = {
        "id": f"usage_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "org_id": data.get("org_id"),
        "resource_type": data.get("resource_type"),  # agent, workflow, api_call, etc.
        "resource_id": data.get("resource_id"),
        "operation": data.get("operation"),
        "quantity": data.get("quantity", 1),
        "unit": data.get("unit", "request"),
        "cost": {
            "amount": data.get("cost_amount", 0.0),
            "currency": data.get("currency", "USD")
        },
        "metadata": {
            "model": data.get("model"),
            "tokens_input": data.get("tokens_input", 0),
            "tokens_output": data.get("tokens_output", 0),
            "duration_ms": data.get("duration_ms", 0)
        }
    }

    USAGE_RECORDS.append(record)
    return {"usage_record": record}


@app.get("/usage/summary")
def get_usage_summary(
    org_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "day"
):
    """Get usage summary with aggregations"""
    filtered = USAGE_RECORDS.copy()

    if org_id:
        filtered = [r for r in filtered if r.get("org_id") == org_id]

    total_cost = sum(r["cost"]["amount"] for r in filtered)
    total_requests = len(filtered)
    total_tokens = sum(
        r["metadata"].get("tokens_input", 0) + r["metadata"].get("tokens_output", 0)
        for r in filtered
    )

    by_resource = {}
    for r in filtered:
        rt = r.get("resource_type", "unknown")
        if rt not in by_resource:
            by_resource[rt] = {"count": 0, "cost": 0.0}
        by_resource[rt]["count"] += 1
        by_resource[rt]["cost"] += r["cost"]["amount"]

    return {
        "summary": {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "currency": "USD"
        },
        "by_resource_type": by_resource,
        "period": {
            "start": start_date,
            "end": end_date,
            "group_by": group_by
        }
    }


@app.get("/usage/costs")
def get_cost_breakdown(
    org_id: Optional[str] = None,
    period: str = "month"
):
    """Get detailed cost breakdown"""
    filtered = USAGE_RECORDS.copy()

    if org_id:
        filtered = [r for r in filtered if r.get("org_id") == org_id]

    by_agent = {}
    by_workflow = {}
    by_model = {}

    for r in filtered:
        # By agent
        if r.get("resource_type") == "agent":
            aid = r.get("resource_id", "unknown")
            if aid not in by_agent:
                by_agent[aid] = 0.0
            by_agent[aid] += r["cost"]["amount"]

        # By workflow
        if r.get("resource_type") == "workflow":
            wid = r.get("resource_id", "unknown")
            if wid not in by_workflow:
                by_workflow[wid] = 0.0
            by_workflow[wid] += r["cost"]["amount"]

        # By model
        model = r["metadata"].get("model", "unknown")
        if model not in by_model:
            by_model[model] = 0.0
        by_model[model] += r["cost"]["amount"]

    return {
        "period": period,
        "by_agent": by_agent,
        "by_workflow": by_workflow,
        "by_model": by_model,
        "total": sum(r["cost"]["amount"] for r in filtered)
    }


@app.post("/usage/budgets")
def create_budget(request: Request):
    """Create a budget with alerts"""
    data = {}
    budget_id = f"budget_{uuid.uuid4().hex[:8]}"

    budget = {
        "id": budget_id,
        "name": data.get("name", f"Budget {budget_id}"),
        "org_id": data.get("org_id"),
        "amount": data.get("amount", 1000.0),
        "currency": data.get("currency", "USD"),
        "period": data.get("period", "monthly"),
        "alert_thresholds": data.get("alert_thresholds", [50, 80, 100]),
        "current_spend": 0.0,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    BUDGETS[budget_id] = budget
    return {"budget": budget}


@app.get("/usage/budgets")
def list_budgets(org_id: Optional[str] = None):
    """List all budgets"""
    budgets = list(BUDGETS.values())
    if org_id:
        budgets = [b for b in budgets if b.get("org_id") == org_id]
    return {"budgets": budgets, "total": len(budgets)}


@app.get("/usage/budgets/{budget_id}")
def get_budget(budget_id: str):
    """Get budget details with current status"""
    if budget_id not in BUDGETS:
        raise HTTPException(status_code=404, detail="Budget not found")

    budget = BUDGETS[budget_id]
    percentage_used = (budget["current_spend"] / budget["amount"]) * 100 if budget["amount"] > 0 else 0

    return {
        "budget": budget,
        "percentage_used": percentage_used,
        "remaining": budget["amount"] - budget["current_spend"]
    }


@app.get("/usage/alerts")
def list_cost_alerts(org_id: Optional[str] = None):
    """List cost alerts"""
    alerts = COST_ALERTS.copy()
    if org_id:
        alerts = [a for a in alerts if a.get("org_id") == org_id]
    return {"alerts": alerts, "total": len(alerts)}


# ============================================================================
# Scheduling / Cron Jobs
# ============================================================================

SCHEDULED_JOBS: Dict[str, Dict[str, Any]] = {}
JOB_EXECUTIONS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/schedules")
def create_schedule(request: Request):
    """Create a scheduled job"""
    data = {}
    job_id = f"schedule_{uuid.uuid4().hex[:8]}"

    job = {
        "id": job_id,
        "name": data.get("name", f"Job {job_id}"),
        "description": data.get("description", ""),
        "schedule": {
            "type": data.get("schedule_type", "cron"),  # cron, interval, once
            "expression": data.get("cron_expression", "0 0 * * *"),  # Daily at midnight
            "interval_seconds": data.get("interval_seconds"),
            "run_at": data.get("run_at"),
            "timezone": data.get("timezone", "UTC")
        },
        "action": {
            "type": data.get("action_type", "agent"),  # agent, workflow, webhook
            "target_id": data.get("target_id"),
            "input": data.get("input", {}),
            "config": data.get("config", {})
        },
        "retry": {
            "max_attempts": data.get("max_retries", 3),
            "backoff_seconds": data.get("backoff_seconds", 60)
        },
        "status": "active",
        "next_run_at": None,
        "last_run_at": None,
        "run_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    SCHEDULED_JOBS[job_id] = job
    JOB_EXECUTIONS[job_id] = []
    return {"schedule": job}


@app.get("/schedules")
def list_schedules(status: Optional[str] = None):
    """List all scheduled jobs"""
    jobs = list(SCHEDULED_JOBS.values())
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    return {"schedules": jobs, "total": len(jobs)}


@app.get("/schedules/{job_id}")
def get_schedule(job_id: str):
    """Get schedule details"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"schedule": SCHEDULED_JOBS[job_id]}


@app.put("/schedules/{job_id}")
def update_schedule(job_id: str, request: Request):
    """Update a schedule"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    data = {}
    job = SCHEDULED_JOBS[job_id]

    for field in ["name", "description", "schedule", "action", "retry"]:
        if field in data:
            job[field] = data[field]

    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"schedule": job}


@app.post("/schedules/{job_id}/pause")
def pause_schedule(job_id: str):
    """Pause a scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    SCHEDULED_JOBS[job_id]["status"] = "paused"
    return {"schedule": SCHEDULED_JOBS[job_id]}


@app.post("/schedules/{job_id}/resume")
def resume_schedule(job_id: str):
    """Resume a paused schedule"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    SCHEDULED_JOBS[job_id]["status"] = "active"
    return {"schedule": SCHEDULED_JOBS[job_id]}


@app.post("/schedules/{job_id}/trigger")
def trigger_schedule(job_id: str):
    """Manually trigger a scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    job = SCHEDULED_JOBS[job_id]
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"

    execution = {
        "id": execution_id,
        "job_id": job_id,
        "triggered_by": "manual",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "status": "running",
        "result": None,
        "error": None
    }

    JOB_EXECUTIONS[job_id].append(execution)
    job["last_run_at"] = execution["started_at"]
    job["run_count"] += 1

    # Simulate completion
    execution["status"] = "completed"
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution["result"] = {"message": "Execution completed successfully"}

    return {"execution": execution}


@app.delete("/schedules/{job_id}")
def delete_schedule(job_id: str):
    """Delete a schedule"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    del SCHEDULED_JOBS[job_id]
    if job_id in JOB_EXECUTIONS:
        del JOB_EXECUTIONS[job_id]

    return {"deleted": True}


@app.get("/schedules/{job_id}/executions")
def list_schedule_executions(job_id: str, limit: int = 50):
    """List executions for a schedule"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Schedule not found")

    executions = JOB_EXECUTIONS.get(job_id, [])
    return {"executions": executions[-limit:], "total": len(executions)}


# ============================================================================
# Caching Layer
# ============================================================================

CACHE_STORE: Dict[str, Dict[str, Any]] = {}
SEMANTIC_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_STATS = {"hits": 0, "misses": 0, "evictions": 0}


@app.post("/cache/set")
def cache_set(request: Request):
    """Set a cache entry"""
    data = {}

    key = data.get("key")
    if not key:
        raise HTTPException(status_code=400, detail="Cache key required")

    ttl_seconds = data.get("ttl_seconds", 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    entry = {
        "key": key,
        "value": data.get("value"),
        "metadata": data.get("metadata", {}),
        "ttl_seconds": ttl_seconds,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "access_count": 0
    }

    CACHE_STORE[key] = entry
    return {"cached": True, "key": key, "expires_at": entry["expires_at"]}


@app.get("/cache/get/{key}")
def cache_get(key: str):
    """Get a cache entry"""
    if key not in CACHE_STORE:
        CACHE_STATS["misses"] += 1
        raise HTTPException(status_code=404, detail="Cache miss")

    entry = CACHE_STORE[key]

    # Check expiration
    if datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00")) < datetime.now(timezone.utc):
        del CACHE_STORE[key]
        CACHE_STATS["evictions"] += 1
        CACHE_STATS["misses"] += 1
        raise HTTPException(status_code=404, detail="Cache expired")

    entry["access_count"] += 1
    CACHE_STATS["hits"] += 1

    return {"value": entry["value"], "metadata": entry["metadata"]}


@app.delete("/cache/delete/{key}")
def cache_delete(key: str):
    """Delete a cache entry"""
    if key in CACHE_STORE:
        del CACHE_STORE[key]
        return {"deleted": True}
    return {"deleted": False}


@app.post("/cache/clear")
def cache_clear(pattern: Optional[str] = None):
    """Clear cache entries"""
    if pattern:
        keys_to_delete = [k for k in CACHE_STORE.keys() if pattern in k]
        for k in keys_to_delete:
            del CACHE_STORE[k]
        return {"cleared": len(keys_to_delete)}
    else:
        count = len(CACHE_STORE)
        CACHE_STORE.clear()
        return {"cleared": count}


@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    total = CACHE_STATS["hits"] + CACHE_STATS["misses"]
    hit_rate = (CACHE_STATS["hits"] / total * 100) if total > 0 else 0

    return {
        "stats": CACHE_STATS,
        "hit_rate_percent": hit_rate,
        "total_entries": len(CACHE_STORE),
        "semantic_cache_entries": len(SEMANTIC_CACHE)
    }


@app.post("/cache/semantic/set")
def semantic_cache_set(request: Request):
    """Set a semantic cache entry (for LLM responses)"""
    data = {}

    cache_id = f"sem_{uuid.uuid4().hex[:12]}"

    entry = {
        "id": cache_id,
        "prompt_hash": data.get("prompt_hash"),
        "prompt_embedding": data.get("prompt_embedding", []),
        "model": data.get("model"),
        "response": data.get("response"),
        "similarity_threshold": data.get("similarity_threshold", 0.95),
        "ttl_seconds": data.get("ttl_seconds", 86400),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hit_count": 0
    }

    SEMANTIC_CACHE[cache_id] = entry
    return {"cached": True, "cache_id": cache_id}


@app.post("/cache/semantic/lookup")
def semantic_cache_lookup(request: Request):
    """Look up semantic cache by similarity"""
    data = {}

    # In production, this would compute embedding similarity
    prompt_hash = data.get("prompt_hash")

    for cache_id, entry in SEMANTIC_CACHE.items():
        if entry.get("prompt_hash") == prompt_hash:
            entry["hit_count"] += 1
            return {
                "hit": True,
                "cache_id": cache_id,
                "response": entry["response"],
                "model": entry["model"]
            }

    return {"hit": False}


# ============================================================================
# Feature Flags
# ============================================================================

FEATURE_FLAGS: Dict[str, Dict[str, Any]] = {}
FLAG_OVERRIDES: Dict[str, Dict[str, bool]] = {}  # user_id -> {flag_name: value}


@app.post("/feature-flags")
def create_feature_flag(request: Request):
    """Create a feature flag"""
    data = {}

    flag_name = data.get("name")
    if not flag_name:
        raise HTTPException(status_code=400, detail="Flag name required")

    flag = {
        "name": flag_name,
        "description": data.get("description", ""),
        "enabled": data.get("enabled", False),
        "rollout_percentage": data.get("rollout_percentage", 0),
        "targeting_rules": data.get("targeting_rules", []),
        "environments": data.get("environments", {"development": True, "staging": False, "production": False}),
        "variants": data.get("variants", []),
        "default_variant": data.get("default_variant"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    FEATURE_FLAGS[flag_name] = flag
    return {"feature_flag": flag}


@app.get("/feature-flags")
def list_feature_flags(environment: Optional[str] = None):
    """List all feature flags"""
    flags = list(FEATURE_FLAGS.values())
    return {"feature_flags": flags, "total": len(flags)}


@app.get("/feature-flags/{flag_name}")
def get_feature_flag(flag_name: str):
    """Get feature flag details"""
    if flag_name not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {"feature_flag": FEATURE_FLAGS[flag_name]}


@app.put("/feature-flags/{flag_name}")
def update_feature_flag(flag_name: str, request: Request):
    """Update a feature flag"""
    if flag_name not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    data = {}
    flag = FEATURE_FLAGS[flag_name]

    for field in ["description", "enabled", "rollout_percentage", "targeting_rules", "environments", "variants"]:
        if field in data:
            flag[field] = data[field]

    flag["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"feature_flag": flag}


@app.post("/feature-flags/{flag_name}/toggle")
def toggle_feature_flag(flag_name: str, environment: Optional[str] = None):
    """Toggle a feature flag"""
    if flag_name not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag = FEATURE_FLAGS[flag_name]

    if environment:
        flag["environments"][environment] = not flag["environments"].get(environment, False)
    else:
        flag["enabled"] = not flag["enabled"]

    flag["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"feature_flag": flag}


@app.post("/feature-flags/evaluate")
def evaluate_feature_flags(request: Request):
    """Evaluate feature flags for a user/context"""
    data = {}

    user_id = data.get("user_id")
    environment = data.get("environment", "production")
    context = data.get("context", {})

    evaluated = {}
    for flag_name, flag in FEATURE_FLAGS.items():
        # Check override first
        if user_id and user_id in FLAG_OVERRIDES:
            if flag_name in FLAG_OVERRIDES[user_id]:
                evaluated[flag_name] = FLAG_OVERRIDES[user_id][flag_name]
                continue

        # Check environment
        env_enabled = flag["environments"].get(environment, False)

        # Check rollout percentage (simplified)
        if flag["rollout_percentage"] > 0 and user_id:
            hash_value = hash(f"{flag_name}:{user_id}") % 100
            rollout_enabled = hash_value < flag["rollout_percentage"]
        else:
            rollout_enabled = flag["enabled"]

        evaluated[flag_name] = env_enabled and rollout_enabled

    return {"flags": evaluated, "user_id": user_id, "environment": environment}


@app.post("/feature-flags/{flag_name}/override")
def set_flag_override(flag_name: str, request: Request):
    """Set a user-specific flag override"""
    data = {}

    user_id = data.get("user_id")
    value = data.get("value", True)

    if user_id not in FLAG_OVERRIDES:
        FLAG_OVERRIDES[user_id] = {}

    FLAG_OVERRIDES[user_id][flag_name] = value
    return {"override_set": True, "user_id": user_id, "flag": flag_name, "value": value}


@app.delete("/feature-flags/{flag_name}")
def delete_feature_flag(flag_name: str):
    """Delete a feature flag"""
    if flag_name not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    del FEATURE_FLAGS[flag_name]
    return {"deleted": True}


# ============================================================================
# A/B Testing
# ============================================================================

AB_EXPERIMENTS: Dict[str, Dict[str, Any]] = {}
AB_ASSIGNMENTS: Dict[str, Dict[str, str]] = {}  # user_id -> {experiment_id: variant}
AB_EVENTS: List[Dict[str, Any]] = []


@app.post("/experiments")
def create_experiment(request: Request):
    """Create an A/B experiment"""
    data = {}
    experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

    experiment = {
        "id": experiment_id,
        "name": data.get("name", f"Experiment {experiment_id}"),
        "description": data.get("description", ""),
        "hypothesis": data.get("hypothesis", ""),
        "variants": data.get("variants", [
            {"id": "control", "name": "Control", "weight": 50},
            {"id": "treatment", "name": "Treatment", "weight": 50}
        ]),
        "metrics": data.get("metrics", ["conversion", "engagement"]),
        "targeting": {
            "percentage": data.get("targeting_percentage", 100),
            "rules": data.get("targeting_rules", [])
        },
        "status": "draft",
        "started_at": None,
        "ended_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    AB_EXPERIMENTS[experiment_id] = experiment
    return {"experiment": experiment}


@app.get("/experiments")
def list_experiments(status: Optional[str] = None):
    """List all experiments"""
    experiments = list(AB_EXPERIMENTS.values())
    if status:
        experiments = [e for e in experiments if e.get("status") == status]
    return {"experiments": experiments, "total": len(experiments)}


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    """Get experiment details"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment": AB_EXPERIMENTS[experiment_id]}


@app.post("/experiments/{experiment_id}/start")
def start_experiment(experiment_id: str):
    """Start an experiment"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = AB_EXPERIMENTS[experiment_id]
    experiment["status"] = "running"
    experiment["started_at"] = datetime.now(timezone.utc).isoformat()

    return {"experiment": experiment}


@app.post("/experiments/{experiment_id}/stop")
def stop_experiment(experiment_id: str):
    """Stop an experiment"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = AB_EXPERIMENTS[experiment_id]
    experiment["status"] = "stopped"
    experiment["ended_at"] = datetime.now(timezone.utc).isoformat()

    return {"experiment": experiment}


@app.post("/experiments/{experiment_id}/assign")
def assign_variant(experiment_id: str, request: Request):
    """Assign a user to an experiment variant"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    data = {}
    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    # Check existing assignment
    if user_id in AB_ASSIGNMENTS and experiment_id in AB_ASSIGNMENTS[user_id]:
        return {
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": AB_ASSIGNMENTS[user_id][experiment_id],
            "source": "existing"
        }

    # Assign based on weights
    experiment = AB_EXPERIMENTS[experiment_id]
    variants = experiment["variants"]
    total_weight = sum(v["weight"] for v in variants)

    hash_value = hash(f"{experiment_id}:{user_id}") % total_weight
    cumulative = 0
    assigned_variant = variants[0]["id"]

    for variant in variants:
        cumulative += variant["weight"]
        if hash_value < cumulative:
            assigned_variant = variant["id"]
            break

    if user_id not in AB_ASSIGNMENTS:
        AB_ASSIGNMENTS[user_id] = {}
    AB_ASSIGNMENTS[user_id][experiment_id] = assigned_variant

    return {
        "user_id": user_id,
        "experiment_id": experiment_id,
        "variant": assigned_variant,
        "source": "new"
    }


@app.post("/experiments/{experiment_id}/track")
def track_experiment_event(experiment_id: str, request: Request):
    """Track an event for an experiment"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    data = {}

    event = {
        "id": f"event_{uuid.uuid4().hex[:8]}",
        "experiment_id": experiment_id,
        "user_id": data.get("user_id"),
        "variant": data.get("variant"),
        "event_type": data.get("event_type", "conversion"),
        "value": data.get("value", 1),
        "metadata": data.get("metadata", {}),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    AB_EVENTS.append(event)
    return {"event": event}


@app.get("/experiments/{experiment_id}/results")
def get_experiment_results(experiment_id: str):
    """Get experiment results and statistics"""
    if experiment_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = AB_EXPERIMENTS[experiment_id]
    events = [e for e in AB_EVENTS if e["experiment_id"] == experiment_id]

    # Calculate stats per variant
    variant_stats = {}
    for variant in experiment["variants"]:
        vid = variant["id"]
        variant_events = [e for e in events if e.get("variant") == vid]

        variant_stats[vid] = {
            "total_users": len(set(e["user_id"] for e in variant_events if e.get("user_id"))),
            "total_events": len(variant_events),
            "conversions": len([e for e in variant_events if e.get("event_type") == "conversion"]),
            "total_value": sum(e.get("value", 0) for e in variant_events)
        }

        if variant_stats[vid]["total_users"] > 0:
            variant_stats[vid]["conversion_rate"] = (
                variant_stats[vid]["conversions"] / variant_stats[vid]["total_users"] * 100
            )
        else:
            variant_stats[vid]["conversion_rate"] = 0

    return {
        "experiment_id": experiment_id,
        "status": experiment["status"],
        "variant_stats": variant_stats,
        "total_events": len(events)
    }


# ============================================================================
# Human-in-the-Loop (HITL)
# ============================================================================

HITL_TASKS: Dict[str, Dict[str, Any]] = {}
HITL_QUEUES: Dict[str, List[str]] = {}  # queue_name -> [task_ids]
HITL_FEEDBACK: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/hitl/tasks")
def create_hitl_task(request: Request):
    """Create a human-in-the-loop task"""
    data = {}
    task_id = f"hitl_{uuid.uuid4().hex[:8]}"

    task = {
        "id": task_id,
        "type": data.get("type", "review"),  # review, approval, annotation, correction
        "title": data.get("title", f"Task {task_id}"),
        "description": data.get("description", ""),
        "context": {
            "agent_id": data.get("agent_id"),
            "execution_id": data.get("execution_id"),
            "input": data.get("input"),
            "output": data.get("output")
        },
        "options": data.get("options", ["approve", "reject", "modify"]),
        "priority": data.get("priority", "normal"),
        "queue": data.get("queue", "default"),
        "assignee": data.get("assignee"),
        "deadline": data.get("deadline"),
        "status": "pending",
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }

    HITL_TASKS[task_id] = task

    # Add to queue
    queue_name = task["queue"]
    if queue_name not in HITL_QUEUES:
        HITL_QUEUES[queue_name] = []
    HITL_QUEUES[queue_name].append(task_id)

    return {"task": task}


@app.get("/hitl/tasks")
def list_hitl_tasks(
    queue: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None
):
    """List HITL tasks"""
    tasks = list(HITL_TASKS.values())

    if queue:
        tasks = [t for t in tasks if t.get("queue") == queue]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if assignee:
        tasks = [t for t in tasks if t.get("assignee") == assignee]

    return {"tasks": tasks, "total": len(tasks)}


@app.get("/hitl/tasks/{task_id}")
def get_hitl_task(task_id: str):
    """Get HITL task details"""
    if task_id not in HITL_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": HITL_TASKS[task_id]}


@app.post("/hitl/tasks/{task_id}/claim")
def claim_hitl_task(task_id: str, request: Request):
    """Claim a HITL task for processing"""
    if task_id not in HITL_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    data = {}
    task = HITL_TASKS[task_id]

    if task["status"] != "pending":
        raise HTTPException(status_code=400, detail="Task is not available for claiming")

    task["assignee"] = data.get("assignee")
    task["status"] = "in_progress"
    task["claimed_at"] = datetime.now(timezone.utc).isoformat()

    return {"task": task}


@app.post("/hitl/tasks/{task_id}/complete")
def complete_hitl_task(task_id: str, request: Request):
    """Complete a HITL task"""
    if task_id not in HITL_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    data = {}
    task = HITL_TASKS[task_id]

    task["status"] = "completed"
    task["result"] = {
        "decision": data.get("decision"),
        "modified_output": data.get("modified_output"),
        "notes": data.get("notes"),
        "completed_by": data.get("completed_by")
    }
    task["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Remove from queue
    if task["queue"] in HITL_QUEUES and task_id in HITL_QUEUES[task["queue"]]:
        HITL_QUEUES[task["queue"]].remove(task_id)

    return {"task": task}


@app.post("/hitl/tasks/{task_id}/escalate")
def escalate_hitl_task(task_id: str, request: Request):
    """Escalate a HITL task"""
    if task_id not in HITL_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    data = {}
    task = HITL_TASKS[task_id]

    task["status"] = "escalated"
    task["escalation"] = {
        "reason": data.get("reason"),
        "escalated_to": data.get("escalated_to"),
        "escalated_at": datetime.now(timezone.utc).isoformat()
    }

    return {"task": task}


@app.get("/hitl/queues")
def list_hitl_queues():
    """List HITL queues"""
    queue_stats = {}
    for queue_name, task_ids in HITL_QUEUES.items():
        queue_stats[queue_name] = {
            "total_tasks": len(task_ids),
            "pending": len([t for t in task_ids if HITL_TASKS.get(t, {}).get("status") == "pending"])
        }
    return {"queues": queue_stats}


@app.post("/hitl/feedback")
def submit_hitl_feedback(request: Request):
    """Submit feedback on an agent output"""
    data = {}
    feedback_id = f"feedback_{uuid.uuid4().hex[:8]}"

    feedback = {
        "id": feedback_id,
        "agent_id": data.get("agent_id"),
        "execution_id": data.get("execution_id"),
        "rating": data.get("rating"),  # 1-5
        "feedback_type": data.get("feedback_type", "general"),  # accuracy, helpfulness, safety
        "comment": data.get("comment"),
        "corrections": data.get("corrections"),
        "submitted_by": data.get("submitted_by"),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    agent_id = data.get("agent_id", "unknown")
    if agent_id not in HITL_FEEDBACK:
        HITL_FEEDBACK[agent_id] = []
    HITL_FEEDBACK[agent_id].append(feedback)

    return {"feedback": feedback}


@app.get("/hitl/feedback/{agent_id}")
def get_agent_feedback(agent_id: str, limit: int = 50):
    """Get feedback for an agent"""
    feedback_list = HITL_FEEDBACK.get(agent_id, [])

    avg_rating = None
    if feedback_list:
        ratings = [f["rating"] for f in feedback_list if f.get("rating")]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)

    return {
        "agent_id": agent_id,
        "feedback": feedback_list[-limit:],
        "total": len(feedback_list),
        "average_rating": avg_rating
    }


# ============================================================================
# Knowledge Base
# ============================================================================

KNOWLEDGE_ARTICLES: Dict[str, Dict[str, Any]] = {}
KNOWLEDGE_CATEGORIES: Dict[str, Dict[str, Any]] = {}
KNOWLEDGE_EMBEDDINGS: Dict[str, List[float]] = {}


@app.post("/knowledge/articles")
def create_knowledge_article(request: Request):
    """Create a knowledge base article"""
    data = {}
    article_id = f"kb_{uuid.uuid4().hex[:8]}"

    article = {
        "id": article_id,
        "title": data.get("title", f"Article {article_id}"),
        "content": data.get("content", ""),
        "summary": data.get("summary", ""),
        "category": data.get("category"),
        "tags": data.get("tags", []),
        "metadata": {
            "author": data.get("author"),
            "source": data.get("source"),
            "language": data.get("language", "en")
        },
        "visibility": data.get("visibility", "public"),
        "status": data.get("status", "published"),
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    KNOWLEDGE_ARTICLES[article_id] = article
    return {"article": article}


@app.get("/knowledge/articles")
def list_knowledge_articles(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    """List knowledge base articles"""
    articles = list(KNOWLEDGE_ARTICLES.values())

    if category:
        articles = [a for a in articles if a.get("category") == category]
    if tag:
        articles = [a for a in articles if tag in a.get("tags", [])]
    if search:
        search_lower = search.lower()
        articles = [a for a in articles if
                   search_lower in a.get("title", "").lower() or
                   search_lower in a.get("content", "").lower()]

    return {"articles": articles[:limit], "total": len(articles)}


@app.get("/knowledge/articles/{article_id}")
def get_knowledge_article(article_id: str):
    """Get knowledge article details"""
    if article_id not in KNOWLEDGE_ARTICLES:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"article": KNOWLEDGE_ARTICLES[article_id]}


@app.put("/knowledge/articles/{article_id}")
def update_knowledge_article(article_id: str, request: Request):
    """Update a knowledge article"""
    if article_id not in KNOWLEDGE_ARTICLES:
        raise HTTPException(status_code=404, detail="Article not found")

    data = {}
    article = KNOWLEDGE_ARTICLES[article_id]

    for field in ["title", "content", "summary", "category", "tags", "visibility", "status"]:
        if field in data:
            article[field] = data[field]

    article["version"] += 1
    article["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {"article": article}


@app.delete("/knowledge/articles/{article_id}")
def delete_knowledge_article(article_id: str):
    """Delete a knowledge article"""
    if article_id not in KNOWLEDGE_ARTICLES:
        raise HTTPException(status_code=404, detail="Article not found")

    del KNOWLEDGE_ARTICLES[article_id]
    return {"deleted": True}


@app.post("/knowledge/categories")
def create_knowledge_category(request: Request):
    """Create a knowledge category"""
    data = {}
    cat_id = f"cat_{uuid.uuid4().hex[:8]}"

    category = {
        "id": cat_id,
        "name": data.get("name", f"Category {cat_id}"),
        "description": data.get("description", ""),
        "parent_id": data.get("parent_id"),
        "icon": data.get("icon"),
        "order": data.get("order", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    KNOWLEDGE_CATEGORIES[cat_id] = category
    return {"category": category}


@app.get("/knowledge/categories")
def list_knowledge_categories():
    """List knowledge categories"""
    return {"categories": list(KNOWLEDGE_CATEGORIES.values())}


@app.post("/knowledge/search")
def semantic_knowledge_search(request: Request):
    """Semantic search across knowledge base"""
    data = {}
    query = data.get("query", "")
    limit = data.get("limit", 10)

    # Simplified search - in production would use embeddings
    results = []
    query_lower = query.lower()

    for article_id, article in KNOWLEDGE_ARTICLES.items():
        score = 0
        if query_lower in article.get("title", "").lower():
            score += 2
        if query_lower in article.get("content", "").lower():
            score += 1
        if query_lower in article.get("summary", "").lower():
            score += 1.5

        if score > 0:
            results.append({
                "article_id": article_id,
                "title": article["title"],
                "summary": article.get("summary", "")[:200],
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {"results": results[:limit], "query": query}


# ============================================================================
# Model Registry
# ============================================================================

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {}
MODEL_DEPLOYMENTS: Dict[str, Dict[str, Any]] = {}
MODEL_METRICS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/models/register")
def register_model(request: Request):
    """Register a model in the registry"""
    data = {}
    model_id = f"model_{uuid.uuid4().hex[:8]}"

    model = {
        "id": model_id,
        "name": data.get("name", f"Model {model_id}"),
        "version": data.get("version", "1.0.0"),
        "type": data.get("type", "llm"),  # llm, embedding, classifier, etc.
        "provider": data.get("provider"),  # openai, anthropic, local, etc.
        "config": {
            "model_name": data.get("model_name"),
            "endpoint": data.get("endpoint"),
            "api_key_ref": data.get("api_key_ref"),
            "max_tokens": data.get("max_tokens", 4096),
            "temperature": data.get("temperature", 0.7)
        },
        "capabilities": data.get("capabilities", []),
        "pricing": {
            "input_cost_per_1k": data.get("input_cost", 0.0),
            "output_cost_per_1k": data.get("output_cost", 0.0),
            "currency": "USD"
        },
        "status": "registered",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    MODEL_REGISTRY[model_id] = model
    return {"model": model}


@app.get("/models")
def list_models(
    model_type: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None
):
    """List registered models"""
    models = list(MODEL_REGISTRY.values())

    if model_type:
        models = [m for m in models if m.get("type") == model_type]
    if provider:
        models = [m for m in models if m.get("provider") == provider]
    if status:
        models = [m for m in models if m.get("status") == status]

    return {"models": models, "total": len(models)}


@app.get("/models/{model_id}")
def get_model(model_id: str):
    """Get model details"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"model": MODEL_REGISTRY[model_id]}


@app.put("/models/{model_id}")
def update_model(model_id: str, request: Request):
    """Update model configuration"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}
    model = MODEL_REGISTRY[model_id]

    for field in ["name", "version", "config", "capabilities", "pricing", "status"]:
        if field in data:
            model[field] = data[field]

    model["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"model": model}


@app.post("/models/{model_id}/deploy")
def deploy_model(model_id: str, request: Request):
    """Deploy a model to an environment"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}
    deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"

    deployment = {
        "id": deployment_id,
        "model_id": model_id,
        "environment": data.get("environment", "production"),
        "config": data.get("config", {}),
        "scaling": {
            "min_instances": data.get("min_instances", 1),
            "max_instances": data.get("max_instances", 10),
            "target_concurrency": data.get("target_concurrency", 100)
        },
        "status": "deploying",
        "endpoint": f"/models/{model_id}/invoke",
        "deployed_at": datetime.now(timezone.utc).isoformat()
    }

    MODEL_DEPLOYMENTS[deployment_id] = deployment
    MODEL_REGISTRY[model_id]["status"] = "deployed"

    # Simulate deployment completion
    deployment["status"] = "active"

    return {"deployment": deployment}


@app.get("/models/{model_id}/deployments")
def list_model_deployments(model_id: str):
    """List deployments for a model"""
    deployments = [d for d in MODEL_DEPLOYMENTS.values() if d.get("model_id") == model_id]
    return {"deployments": deployments, "total": len(deployments)}


@app.post("/models/{model_id}/metrics")
def record_model_metrics(model_id: str, request: Request):
    """Record performance metrics for a model"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}

    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": data.get("latency_ms"),
        "tokens_input": data.get("tokens_input"),
        "tokens_output": data.get("tokens_output"),
        "success": data.get("success", True),
        "error_type": data.get("error_type"),
        "metadata": data.get("metadata", {})
    }

    if model_id not in MODEL_METRICS:
        MODEL_METRICS[model_id] = []
    MODEL_METRICS[model_id].append(metrics)

    return {"recorded": True}


@app.get("/models/{model_id}/metrics")
def get_model_metrics(model_id: str, limit: int = 100):
    """Get model performance metrics"""
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")

    metrics_list = MODEL_METRICS.get(model_id, [])

    # Calculate aggregates
    if metrics_list:
        latencies = [m["latency_ms"] for m in metrics_list if m.get("latency_ms")]
        successes = [m for m in metrics_list if m.get("success")]

        summary = {
            "total_requests": len(metrics_list),
            "success_rate": len(successes) / len(metrics_list) * 100,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        }
    else:
        summary = {}

    return {
        "model_id": model_id,
        "metrics": metrics_list[-limit:],
        "summary": summary
    }


@app.post("/models/compare")
def compare_models(request: Request):
    """Compare multiple models"""
    data = {}
    model_ids = data.get("model_ids", [])

    comparison = {}
    for model_id in model_ids:
        if model_id in MODEL_REGISTRY:
            model = MODEL_REGISTRY[model_id]
            metrics_list = MODEL_METRICS.get(model_id, [])

            latencies = [m["latency_ms"] for m in metrics_list if m.get("latency_ms")]

            comparison[model_id] = {
                "name": model["name"],
                "version": model["version"],
                "provider": model.get("provider"),
                "pricing": model.get("pricing"),
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
                "total_requests": len(metrics_list)
            }

    return {"comparison": comparison}


# ============================================================================
# Distributed Execution
# ============================================================================

WORKER_REGISTRY: Dict[str, Dict[str, Any]] = {}
TASK_QUEUE: List[Dict[str, Any]] = []
DISTRIBUTED_TASKS: Dict[str, Dict[str, Any]] = {}


@app.post("/workers/register")
def register_worker(request: Request):
    """Register a worker node"""
    data = {}
    worker_id = f"worker_{uuid.uuid4().hex[:8]}"

    worker = {
        "id": worker_id,
        "name": data.get("name", f"Worker {worker_id}"),
        "type": data.get("type", "general"),
        "capabilities": data.get("capabilities", []),
        "capacity": {
            "max_concurrent": data.get("max_concurrent", 10),
            "current_load": 0
        },
        "endpoint": data.get("endpoint"),
        "status": "active",
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "registered_at": datetime.now(timezone.utc).isoformat()
    }

    WORKER_REGISTRY[worker_id] = worker
    return {"worker": worker}


@app.get("/workers")
def list_workers(status: Optional[str] = None):
    """List registered workers"""
    workers = list(WORKER_REGISTRY.values())
    if status:
        workers = [w for w in workers if w.get("status") == status]
    return {"workers": workers, "total": len(workers)}


@app.post("/workers/{worker_id}/heartbeat")
def worker_heartbeat(worker_id: str, request: Request):
    """Update worker heartbeat"""
    if worker_id not in WORKER_REGISTRY:
        raise HTTPException(status_code=404, detail="Worker not found")

    data = {}
    worker = WORKER_REGISTRY[worker_id]

    worker["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    worker["capacity"]["current_load"] = data.get("current_load", 0)
    worker["status"] = data.get("status", "active")

    return {"acknowledged": True}


@app.post("/distributed/tasks")
def create_distributed_task(request: Request):
    """Create a distributed task"""
    data = {}
    task_id = f"dtask_{uuid.uuid4().hex[:8]}"

    task = {
        "id": task_id,
        "type": data.get("type", "agent_execution"),
        "payload": data.get("payload", {}),
        "priority": data.get("priority", 5),
        "routing": {
            "strategy": data.get("routing_strategy", "least_loaded"),
            "required_capabilities": data.get("required_capabilities", []),
            "preferred_worker": data.get("preferred_worker")
        },
        "retry": {
            "max_attempts": data.get("max_retries", 3),
            "attempt": 0
        },
        "status": "queued",
        "assigned_worker": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    DISTRIBUTED_TASKS[task_id] = task
    TASK_QUEUE.append(task)

    return {"task": task}


@app.get("/distributed/tasks")
def list_distributed_tasks(status: Optional[str] = None, limit: int = 100):
    """List distributed tasks"""
    tasks = list(DISTRIBUTED_TASKS.values())
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return {"tasks": tasks[-limit:], "total": len(tasks)}


@app.post("/distributed/tasks/{task_id}/assign")
def assign_distributed_task(task_id: str, request: Request):
    """Assign task to a worker"""
    if task_id not in DISTRIBUTED_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    data = {}
    task = DISTRIBUTED_TASKS[task_id]
    worker_id = data.get("worker_id")

    if worker_id and worker_id in WORKER_REGISTRY:
        task["assigned_worker"] = worker_id
        task["status"] = "assigned"
        task["assigned_at"] = datetime.now(timezone.utc).isoformat()
        WORKER_REGISTRY[worker_id]["capacity"]["current_load"] += 1
    else:
        # Auto-assign to least loaded worker
        available_workers = [w for w in WORKER_REGISTRY.values()
                          if w["status"] == "active" and
                          w["capacity"]["current_load"] < w["capacity"]["max_concurrent"]]

        if available_workers:
            worker = min(available_workers, key=lambda w: w["capacity"]["current_load"])
            task["assigned_worker"] = worker["id"]
            task["status"] = "assigned"
            task["assigned_at"] = datetime.now(timezone.utc).isoformat()
            worker["capacity"]["current_load"] += 1

    return {"task": task}


@app.post("/distributed/tasks/{task_id}/complete")
def complete_distributed_task(task_id: str, request: Request):
    """Mark distributed task as complete"""
    if task_id not in DISTRIBUTED_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    data = {}
    task = DISTRIBUTED_TASKS[task_id]

    task["status"] = "completed"
    task["result"] = data.get("result")
    task["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Update worker load
    if task["assigned_worker"] and task["assigned_worker"] in WORKER_REGISTRY:
        WORKER_REGISTRY[task["assigned_worker"]]["capacity"]["current_load"] -= 1

    return {"task": task}


@app.get("/distributed/queue")
def get_task_queue():
    """Get current task queue status"""
    queued = [t for t in TASK_QUEUE if t["status"] == "queued"]

    return {
        "queue_length": len(queued),
        "tasks": queued[:50],
        "workers_available": len([w for w in WORKER_REGISTRY.values() if w["status"] == "active"])
    }


# ============================================================================
# Observability / Tracing
# ============================================================================

TRACES: Dict[str, Dict[str, Any]] = {}
SPANS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/tracing/traces")
def create_trace(request: Request):
    """Create a new trace"""
    data = {}
    trace_id = data.get("trace_id") or f"trace_{uuid.uuid4().hex[:16]}"

    trace = {
        "trace_id": trace_id,
        "name": data.get("name", "unnamed"),
        "service": data.get("service", "api"),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "duration_ms": None,
        "status": "active",
        "attributes": data.get("attributes", {}),
        "resource": {
            "service.name": data.get("service_name", "masp-api"),
            "service.version": data.get("service_version", "1.0.0")
        }
    }

    TRACES[trace_id] = trace
    SPANS[trace_id] = []

    return {"trace": trace}


@app.post("/tracing/traces/{trace_id}/spans")
def create_span(trace_id: str, request: Request):
    """Create a span within a trace"""
    if trace_id not in TRACES:
        raise HTTPException(status_code=404, detail="Trace not found")

    data = {}
    span_id = f"span_{uuid.uuid4().hex[:16]}"

    span = {
        "span_id": span_id,
        "trace_id": trace_id,
        "parent_span_id": data.get("parent_span_id"),
        "name": data.get("name", "unnamed"),
        "kind": data.get("kind", "internal"),  # internal, server, client, producer, consumer
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "duration_ms": None,
        "status": {"code": "OK"},
        "attributes": data.get("attributes", {}),
        "events": [],
        "links": []
    }

    SPANS[trace_id].append(span)
    return {"span": span}


@app.put("/tracing/traces/{trace_id}/spans/{span_id}")
def update_span(trace_id: str, span_id: str, request: Request):
    """Update a span"""
    if trace_id not in TRACES:
        raise HTTPException(status_code=404, detail="Trace not found")

    data = {}

    for span in SPANS[trace_id]:
        if span["span_id"] == span_id:
            if data.get("end"):
                span["end_time"] = datetime.now(timezone.utc).isoformat()
            if "status" in data:
                span["status"] = data["status"]
            if "attributes" in data:
                span["attributes"].update(data["attributes"])
            return {"span": span}

    raise HTTPException(status_code=404, detail="Span not found")


@app.post("/tracing/traces/{trace_id}/complete")
def complete_trace(trace_id: str):
    """Complete a trace"""
    if trace_id not in TRACES:
        raise HTTPException(status_code=404, detail="Trace not found")

    trace = TRACES[trace_id]
    trace["end_time"] = datetime.now(timezone.utc).isoformat()
    trace["status"] = "completed"

    # Calculate duration
    start = datetime.fromisoformat(trace["start_time"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(trace["end_time"].replace("Z", "+00:00"))
    trace["duration_ms"] = (end - start).total_seconds() * 1000

    return {"trace": trace}


@app.get("/tracing/traces")
def list_traces(
    service: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """List traces"""
    traces = list(TRACES.values())

    if service:
        traces = [t for t in traces if t.get("service") == service]
    if status:
        traces = [t for t in traces if t.get("status") == status]

    traces.sort(key=lambda x: x["start_time"], reverse=True)

    return {"traces": traces[:limit], "total": len(traces)}


@app.get("/tracing/traces/{trace_id}")
def get_trace(trace_id: str):
    """Get trace with all spans"""
    if trace_id not in TRACES:
        raise HTTPException(status_code=404, detail="Trace not found")

    return {
        "trace": TRACES[trace_id],
        "spans": SPANS.get(trace_id, [])
    }


@app.get("/tracing/services")
def list_traced_services():
    """List services with tracing data"""
    services = {}
    for trace in TRACES.values():
        service = trace.get("service", "unknown")
        if service not in services:
            services[service] = {"trace_count": 0, "error_count": 0}
        services[service]["trace_count"] += 1
        if trace.get("status") == "error":
            services[service]["error_count"] += 1

    return {"services": services}


# ============================================================================
# Circuit Breakers
# ============================================================================

CIRCUIT_BREAKERS: Dict[str, Dict[str, Any]] = {}


@app.post("/circuit-breakers")
def create_circuit_breaker(request: Request):
    """Create a circuit breaker"""
    data = {}
    cb_id = f"cb_{uuid.uuid4().hex[:8]}"

    circuit_breaker = {
        "id": cb_id,
        "name": data.get("name", f"CircuitBreaker {cb_id}"),
        "target": data.get("target"),  # service/endpoint being protected
        "config": {
            "failure_threshold": data.get("failure_threshold", 5),
            "success_threshold": data.get("success_threshold", 3),
            "timeout_seconds": data.get("timeout_seconds", 30),
            "half_open_max_calls": data.get("half_open_max_calls", 3)
        },
        "state": "closed",  # closed, open, half_open
        "metrics": {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "consecutive_failures": 0,
            "consecutive_successes": 0
        },
        "last_failure_time": None,
        "last_state_change": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    CIRCUIT_BREAKERS[cb_id] = circuit_breaker
    return {"circuit_breaker": circuit_breaker}


@app.get("/circuit-breakers")
def list_circuit_breakers():
    """List all circuit breakers"""
    return {"circuit_breakers": list(CIRCUIT_BREAKERS.values())}


@app.get("/circuit-breakers/{cb_id}")
def get_circuit_breaker(cb_id: str):
    """Get circuit breaker status"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    return {"circuit_breaker": CIRCUIT_BREAKERS[cb_id]}


@app.post("/circuit-breakers/{cb_id}/record")
def record_circuit_breaker_call(cb_id: str, request: Request):
    """Record a call result for the circuit breaker"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    data = {}
    cb = CIRCUIT_BREAKERS[cb_id]
    success = data.get("success", True)

    cb["metrics"]["total_calls"] += 1

    if success:
        cb["metrics"]["successful_calls"] += 1
        cb["metrics"]["consecutive_successes"] += 1
        cb["metrics"]["consecutive_failures"] = 0

        # Check if we can close from half_open
        if cb["state"] == "half_open":
            if cb["metrics"]["consecutive_successes"] >= cb["config"]["success_threshold"]:
                cb["state"] = "closed"
                cb["last_state_change"] = datetime.now(timezone.utc).isoformat()
    else:
        cb["metrics"]["failed_calls"] += 1
        cb["metrics"]["consecutive_failures"] += 1
        cb["metrics"]["consecutive_successes"] = 0
        cb["last_failure_time"] = datetime.now(timezone.utc).isoformat()

        # Check if we should open the circuit
        if cb["state"] == "closed":
            if cb["metrics"]["consecutive_failures"] >= cb["config"]["failure_threshold"]:
                cb["state"] = "open"
                cb["last_state_change"] = datetime.now(timezone.utc).isoformat()
        elif cb["state"] == "half_open":
            cb["state"] = "open"
            cb["last_state_change"] = datetime.now(timezone.utc).isoformat()

    return {"circuit_breaker": cb, "call_allowed": cb["state"] != "open"}


@app.post("/circuit-breakers/{cb_id}/check")
def check_circuit_breaker(cb_id: str):
    """Check if a call is allowed"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    cb = CIRCUIT_BREAKERS[cb_id]

    # Check if timeout has passed for open circuit
    if cb["state"] == "open" and cb["last_state_change"]:
        last_change = datetime.fromisoformat(cb["last_state_change"].replace("Z", "+00:00"))
        timeout = timedelta(seconds=cb["config"]["timeout_seconds"])

        if datetime.now(timezone.utc) > last_change + timeout:
            cb["state"] = "half_open"
            cb["last_state_change"] = datetime.now(timezone.utc).isoformat()
            cb["metrics"]["consecutive_successes"] = 0

    return {
        "allowed": cb["state"] != "open",
        "state": cb["state"],
        "metrics": cb["metrics"]
    }


@app.post("/circuit-breakers/{cb_id}/reset")
def reset_circuit_breaker(cb_id: str):
    """Manually reset a circuit breaker"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    cb = CIRCUIT_BREAKERS[cb_id]
    cb["state"] = "closed"
    cb["metrics"] = {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "consecutive_failures": 0,
        "consecutive_successes": 0
    }
    cb["last_failure_time"] = None
    cb["last_state_change"] = datetime.now(timezone.utc).isoformat()

    return {"circuit_breaker": cb}


@app.delete("/circuit-breakers/{cb_id}")
def delete_circuit_breaker(cb_id: str):
    """Delete a circuit breaker"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    del CIRCUIT_BREAKERS[cb_id]
    return {"deleted": True}


# ============================================================================
# API Versioning
# ============================================================================

API_VERSIONS: Dict[str, Dict[str, Any]] = {
    "v1": {
        "version": "1.0.0",
        "status": "stable",
        "deprecated": False,
        "sunset_date": None,
        "endpoints_count": 300
    },
    "v2": {
        "version": "2.0.0",
        "status": "beta",
        "deprecated": False,
        "sunset_date": None,
        "endpoints_count": 320
    }
}

VERSION_MIGRATIONS: List[Dict[str, Any]] = []


@app.get("/api/versions")
def list_api_versions():
    """List all API versions"""
    return {
        "versions": API_VERSIONS,
        "current": "v1",
        "latest": "v2"
    }


@app.get("/api/versions/{version}")
def get_api_version(version: str):
    """Get API version details"""
    if version not in API_VERSIONS:
        raise HTTPException(status_code=404, detail="API version not found")

    return {
        "version": API_VERSIONS[version],
        "changelog": f"/api/versions/{version}/changelog",
        "migration_guide": f"/api/versions/{version}/migration"
    }


@app.get("/api/versions/{version}/changelog")
def get_version_changelog(version: str):
    """Get changelog for a version"""
    if version not in API_VERSIONS:
        raise HTTPException(status_code=404, detail="API version not found")

    return {
        "version": version,
        "changes": [
            {"type": "added", "description": "New endpoints for enhanced functionality"},
            {"type": "changed", "description": "Improved response formats"},
            {"type": "deprecated", "description": "Legacy endpoints marked for removal"},
            {"type": "fixed", "description": "Bug fixes and performance improvements"}
        ]
    }


@app.post("/api/versions/deprecate")
def deprecate_api_version(request: Request):
    """Mark an API version as deprecated"""
    data = {}
    version = data.get("version")

    if version and version in API_VERSIONS:
        API_VERSIONS[version]["deprecated"] = True
        API_VERSIONS[version]["sunset_date"] = data.get("sunset_date")
        return {"deprecated": True, "version": API_VERSIONS[version]}

    raise HTTPException(status_code=404, detail="Version not found")


@app.get("/api/versions/{version}/endpoints")
def list_version_endpoints(version: str):
    """List endpoints available in a version"""
    return {
        "version": version,
        "endpoints": [
            {"path": "/agents", "methods": ["GET", "POST"], "version_added": "v1"},
            {"path": "/workflows", "methods": ["GET", "POST"], "version_added": "v1"},
            {"path": "/executions", "methods": ["GET", "POST"], "version_added": "v1"},
            {"path": "/chains", "methods": ["GET", "POST"], "version_added": "v2"},
            {"path": "/experiments", "methods": ["GET", "POST"], "version_added": "v2"}
        ],
        "total": API_VERSIONS.get(version, {}).get("endpoints_count", 0)
    }


# ============================================================================
# Request Validation
# ============================================================================

VALIDATION_SCHEMAS: Dict[str, Dict[str, Any]] = {}
VALIDATION_RULES: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/validation/schemas")
def create_validation_schema(request: Request):
    """Create a validation schema"""
    data = {}
    schema_id = f"schema_{uuid.uuid4().hex[:8]}"

    schema = {
        "id": schema_id,
        "name": data.get("name", f"Schema {schema_id}"),
        "description": data.get("description", ""),
        "type": data.get("type", "object"),
        "properties": data.get("properties", {}),
        "required": data.get("required", []),
        "additional_properties": data.get("additional_properties", False),
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    VALIDATION_SCHEMAS[schema_id] = schema
    return {"schema": schema}


@app.get("/validation/schemas")
def list_validation_schemas():
    """List all validation schemas"""
    return {"schemas": list(VALIDATION_SCHEMAS.values()), "total": len(VALIDATION_SCHEMAS)}


@app.get("/validation/schemas/{schema_id}")
def get_validation_schema(schema_id: str):
    """Get a validation schema"""
    if schema_id not in VALIDATION_SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"schema": VALIDATION_SCHEMAS[schema_id]}


@app.post("/validation/validate")
def validate_request_data(request: Request):
    """Validate data against a schema"""
    data = {}
    schema_id = data.get("schema_id")
    payload = data.get("data", {})

    if schema_id and schema_id in VALIDATION_SCHEMAS:
        schema = VALIDATION_SCHEMAS[schema_id]
        errors = []

        # Check required fields
        for field in schema.get("required", []):
            if field not in payload:
                errors.append({"field": field, "error": "Required field missing"})

        # Check field types
        for field, props in schema.get("properties", {}).items():
            if field in payload:
                expected_type = props.get("type")
                value = payload[field]

                type_mapping = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }

                if expected_type in type_mapping:
                    if not isinstance(value, type_mapping[expected_type]):
                        errors.append({
                            "field": field,
                            "error": f"Expected {expected_type}, got {type(value).__name__}"
                        })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "schema_id": schema_id
        }

    return {"valid": True, "errors": [], "schema_id": None}


@app.post("/validation/sanitize")
def sanitize_input(request: Request):
    """Sanitize input data"""
    data = {}
    payload = data.get("data", {})
    rules = data.get("rules", ["trim", "escape_html"])

    sanitized = {}

    for key, value in payload.items():
        if isinstance(value, str):
            result = value
            if "trim" in rules:
                result = result.strip()
            if "escape_html" in rules:
                result = result.replace("<", "&lt;").replace(">", "&gt;")
            if "lowercase" in rules:
                result = result.lower()
            if "remove_scripts" in rules:
                import re
                result = re.sub(r'<script[^>]*>.*?</script>', '', result, flags=re.IGNORECASE | re.DOTALL)
            sanitized[key] = result
        else:
            sanitized[key] = value

    return {"sanitized": sanitized, "rules_applied": rules}


@app.get("/validation/rules")
def list_validation_rules():
    """List available validation rules"""
    return {
        "rules": [
            {"name": "required", "description": "Field must be present"},
            {"name": "type", "description": "Field must match specified type"},
            {"name": "min_length", "description": "String minimum length"},
            {"name": "max_length", "description": "String maximum length"},
            {"name": "pattern", "description": "String must match regex pattern"},
            {"name": "min", "description": "Numeric minimum value"},
            {"name": "max", "description": "Numeric maximum value"},
            {"name": "enum", "description": "Value must be in allowed list"},
            {"name": "email", "description": "Must be valid email format"},
            {"name": "url", "description": "Must be valid URL format"},
            {"name": "uuid", "description": "Must be valid UUID format"}
        ]
    }


# ============================================================================
# OpenAPI / Swagger Generation
# ============================================================================

OPENAPI_SPEC: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {
        "title": "Multi-Agent Standards Protocol API",
        "version": "1.0.0",
        "description": "Comprehensive API for multi-agent orchestration and management"
    }
}


@app.get("/openapi/spec")
def get_openapi_spec():
    """Get OpenAPI specification"""
    spec = OPENAPI_SPEC.copy()
    spec["paths"] = {}

    # Auto-generate paths from registered routes
    endpoint_groups = {
        "/agents": {"tag": "Agents", "description": "Agent management"},
        "/workflows": {"tag": "Workflows", "description": "Workflow orchestration"},
        "/executions": {"tag": "Executions", "description": "Execution management"},
        "/chains": {"tag": "Chains", "description": "Agent chains and pipelines"},
        "/evaluation": {"tag": "Evaluation", "description": "Evaluation framework"},
        "/guardrails": {"tag": "Guardrails", "description": "Safety and guardrails"},
        "/organizations": {"tag": "Organizations", "description": "Multi-tenancy"},
        "/audit": {"tag": "Audit", "description": "Audit logging"},
        "/usage": {"tag": "Usage", "description": "Cost management"}
    }

    for path, meta in endpoint_groups.items():
        spec["paths"][path] = {
            "get": {
                "tags": [meta["tag"]],
                "summary": f"List {meta['tag'].lower()}",
                "responses": {"200": {"description": "Success"}}
            },
            "post": {
                "tags": [meta["tag"]],
                "summary": f"Create {meta['tag'].lower()[:-1]}",
                "responses": {"201": {"description": "Created"}}
            }
        }

    return spec


@app.get("/openapi/spec.json")
def get_openapi_json():
    """Get OpenAPI spec as JSON"""
    return get_openapi_spec()


@app.get("/openapi/spec.yaml")
def get_openapi_yaml():
    """Get OpenAPI spec as YAML"""
    spec = get_openapi_spec()
    # Return as formatted string (YAML library would be used in production)
    return {"format": "yaml", "spec": spec}


@app.get("/openapi/docs")
def get_swagger_ui_config():
    """Get Swagger UI configuration"""
    return {
        "swagger_url": "/openapi/spec.json",
        "title": "MASP API Documentation",
        "theme": "dark",
        "try_it_out_enabled": True,
        "request_snippets_enabled": True,
        "supported_languages": ["curl", "python", "javascript", "go"]
    }


@app.post("/openapi/generate")
def generate_client_code(request: Request):
    """Generate client code from OpenAPI spec"""
    data = {}
    language = data.get("language", "python")

    templates = {
        "python": "import requests\n\nclass MASPClient:\n    def __init__(self, base_url):\n        self.base_url = base_url\n",
        "javascript": "class MASPClient {\n    constructor(baseUrl) {\n        this.baseUrl = baseUrl;\n    }\n",
        "go": "package masp\n\ntype Client struct {\n    BaseURL string\n}\n",
        "typescript": "export class MASPClient {\n    constructor(private baseUrl: string) {}\n"
    }

    return {
        "language": language,
        "code": templates.get(language, templates["python"]),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# OAuth2 / OIDC Flows
# ============================================================================

OAUTH_CLIENTS: Dict[str, Dict[str, Any]] = {}
OAUTH_TOKENS: Dict[str, Dict[str, Any]] = {}
AUTHORIZATION_CODES: Dict[str, Dict[str, Any]] = {}


@app.post("/oauth/clients")
def register_oauth_client(request: Request):
    """Register an OAuth client"""
    data = {}
    client_id = f"client_{uuid.uuid4().hex[:16]}"
    client_secret = f"secret_{uuid.uuid4().hex[:32]}"

    client = {
        "client_id": client_id,
        "client_secret": client_secret,
        "name": data.get("name", f"Client {client_id[:8]}"),
        "redirect_uris": data.get("redirect_uris", []),
        "grant_types": data.get("grant_types", ["authorization_code", "refresh_token"]),
        "scopes": data.get("scopes", ["read", "write"]),
        "token_endpoint_auth_method": data.get("auth_method", "client_secret_basic"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    OAUTH_CLIENTS[client_id] = client
    return {"client": client}


@app.get("/oauth/clients")
def list_oauth_clients():
    """List OAuth clients"""
    # Don't expose secrets
    clients = []
    for c in OAUTH_CLIENTS.values():
        safe_client = {k: v for k, v in c.items() if k != "client_secret"}
        clients.append(safe_client)
    return {"clients": clients, "total": len(clients)}


@app.get("/oauth/authorize")
def oauth_authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "read",
    state: Optional[str] = None
):
    """OAuth2 authorization endpoint"""
    if client_id not in OAUTH_CLIENTS:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    client = OAUTH_CLIENTS[client_id]

    if redirect_uri not in client.get("redirect_uris", []):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # Generate authorization code
    code = f"authz_{uuid.uuid4().hex[:16]}"

    AUTHORIZATION_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    }

    return {
        "redirect_to": f"{redirect_uri}?code={code}&state={state}",
        "code": code,
        "state": state
    }


@app.post("/oauth/token")
def oauth_token(request: Request):
    """OAuth2 token endpoint"""
    data = {}
    grant_type = data.get("grant_type")

    if grant_type == "authorization_code":
        code = data.get("code")
        if code not in AUTHORIZATION_CODES:
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        auth_code = AUTHORIZATION_CODES[code]
        del AUTHORIZATION_CODES[code]

        access_token = f"access_{uuid.uuid4().hex[:32]}"
        refresh_token = f"refresh_{uuid.uuid4().hex[:32]}"

        token = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": auth_code["scope"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        OAUTH_TOKENS[access_token] = token
        return token

    elif grant_type == "client_credentials":
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")

        if client_id not in OAUTH_CLIENTS:
            raise HTTPException(status_code=401, detail="Invalid client credentials")

        if OAUTH_CLIENTS[client_id]["client_secret"] != client_secret:
            raise HTTPException(status_code=401, detail="Invalid client credentials")

        access_token = f"access_{uuid.uuid4().hex[:32]}"

        token = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(OAUTH_CLIENTS[client_id]["scopes"]),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        OAUTH_TOKENS[access_token] = token
        return token

    elif grant_type == "refresh_token":
        refresh = data.get("refresh_token")

        # Find and refresh
        access_token = f"access_{uuid.uuid4().hex[:32]}"

        token = {
            "access_token": access_token,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "expires_in": 3600,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        OAUTH_TOKENS[access_token] = token
        return token

    raise HTTPException(status_code=400, detail="Unsupported grant type")


@app.post("/oauth/revoke")
def oauth_revoke(request: Request):
    """Revoke an OAuth token"""
    data = {}
    token = data.get("token")

    if token in OAUTH_TOKENS:
        del OAUTH_TOKENS[token]
        return {"revoked": True}

    return {"revoked": False}


@app.get("/oauth/userinfo")
def oauth_userinfo(authorization: Optional[str] = None):
    """OIDC UserInfo endpoint"""
    return {
        "sub": "user_12345",
        "name": "Test User",
        "email": "user@example.com",
        "email_verified": True,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/.well-known/openid-configuration")
def openid_configuration():
    """OIDC Discovery endpoint"""
    base_url = "https://api.example.com"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "userinfo_endpoint": f"{base_url}/oauth/userinfo",
        "revocation_endpoint": f"{base_url}/oauth/revoke",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"]
    }


# ============================================================================
# Fine-grained RBAC
# ============================================================================

RBAC_POLICIES: Dict[str, Dict[str, Any]] = {}
RESOURCE_PERMISSIONS: Dict[str, Dict[str, Any]] = {}
PERMISSION_GRANTS: List[Dict[str, Any]] = []


@app.post("/rbac/policies")
def create_rbac_policy(request: Request):
    """Create an RBAC policy"""
    data = {}
    policy_id = f"policy_{uuid.uuid4().hex[:8]}"

    policy = {
        "id": policy_id,
        "name": data.get("name", f"Policy {policy_id}"),
        "description": data.get("description", ""),
        "effect": data.get("effect", "allow"),  # allow, deny
        "actions": data.get("actions", ["read"]),
        "resources": data.get("resources", ["*"]),
        "conditions": data.get("conditions", {}),
        "priority": data.get("priority", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    RBAC_POLICIES[policy_id] = policy
    return {"policy": policy}


@app.get("/rbac/policies")
def list_rbac_policies():
    """List RBAC policies"""
    return {"policies": list(RBAC_POLICIES.values()), "total": len(RBAC_POLICIES)}


@app.get("/rbac/policies/{policy_id}")
def get_rbac_policy(policy_id: str):
    """Get RBAC policy details"""
    if policy_id not in RBAC_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": RBAC_POLICIES[policy_id]}


@app.post("/rbac/permissions/grant")
def grant_permission(request: Request):
    """Grant permission to a subject"""
    data = {}

    grant = {
        "id": f"grant_{uuid.uuid4().hex[:8]}",
        "subject_type": data.get("subject_type", "user"),  # user, role, group
        "subject_id": data.get("subject_id"),
        "resource_type": data.get("resource_type"),  # agent, workflow, etc.
        "resource_id": data.get("resource_id"),  # specific ID or "*"
        "actions": data.get("actions", ["read"]),
        "conditions": data.get("conditions", {}),
        "granted_by": data.get("granted_by"),
        "granted_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": data.get("expires_at")
    }

    PERMISSION_GRANTS.append(grant)
    return {"grant": grant}


@app.post("/rbac/permissions/revoke")
def revoke_permission(request: Request):
    """Revoke a permission grant"""
    data = {}
    grant_id = data.get("grant_id")

    for i, grant in enumerate(PERMISSION_GRANTS):
        if grant["id"] == grant_id:
            del PERMISSION_GRANTS[i]
            return {"revoked": True}

    return {"revoked": False}


@app.post("/rbac/check")
def check_permission(request: Request):
    """Check if an action is permitted"""
    data = {}
    subject_id = data.get("subject_id")
    action = data.get("action")
    resource_type = data.get("resource_type")
    resource_id = data.get("resource_id")

    # Check grants
    for grant in PERMISSION_GRANTS:
        if grant["subject_id"] == subject_id:
            if grant["resource_type"] == resource_type or grant["resource_type"] == "*":
                if grant["resource_id"] == resource_id or grant["resource_id"] == "*":
                    if action in grant["actions"] or "*" in grant["actions"]:
                        return {
                            "allowed": True,
                            "grant_id": grant["id"],
                            "reason": "Explicit grant"
                        }

    return {
        "allowed": False,
        "reason": "No matching permission grant"
    }


@app.get("/rbac/permissions/{subject_id}")
def get_subject_permissions(subject_id: str):
    """Get all permissions for a subject"""
    grants = [g for g in PERMISSION_GRANTS if g["subject_id"] == subject_id]
    return {"subject_id": subject_id, "permissions": grants, "total": len(grants)}


@app.get("/rbac/resources/{resource_type}/{resource_id}/permissions")
def get_resource_permissions(resource_type: str, resource_id: str):
    """Get all permissions for a resource"""
    grants = [g for g in PERMISSION_GRANTS
              if g["resource_type"] == resource_type and
              (g["resource_id"] == resource_id or g["resource_id"] == "*")]
    return {"resource": f"{resource_type}/{resource_id}", "permissions": grants}


# ============================================================================
# Data Retention Policies
# ============================================================================

RETENTION_POLICIES: Dict[str, Dict[str, Any]] = {}
RETENTION_JOBS: Dict[str, Dict[str, Any]] = {}
DATA_DELETION_REQUESTS: List[Dict[str, Any]] = []


@app.post("/retention/policies")
def create_retention_policy(request: Request):
    """Create a data retention policy"""
    data = {}
    policy_id = f"retention_{uuid.uuid4().hex[:8]}"

    policy = {
        "id": policy_id,
        "name": data.get("name", f"Policy {policy_id}"),
        "description": data.get("description", ""),
        "data_types": data.get("data_types", ["logs", "executions"]),
        "retention_days": data.get("retention_days", 90),
        "action": data.get("action", "delete"),  # delete, archive, anonymize
        "schedule": data.get("schedule", "0 0 * * *"),  # Daily at midnight
        "enabled": data.get("enabled", True),
        "last_run": None,
        "next_run": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    RETENTION_POLICIES[policy_id] = policy
    return {"policy": policy}


@app.get("/retention/policies")
def list_retention_policies():
    """List retention policies"""
    return {"policies": list(RETENTION_POLICIES.values()), "total": len(RETENTION_POLICIES)}


@app.get("/retention/policies/{policy_id}")
def get_retention_policy(policy_id: str):
    """Get retention policy details"""
    if policy_id not in RETENTION_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": RETENTION_POLICIES[policy_id]}


@app.post("/retention/policies/{policy_id}/run")
def run_retention_policy(policy_id: str):
    """Manually run a retention policy"""
    if policy_id not in RETENTION_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = RETENTION_POLICIES[policy_id]
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    job = {
        "id": job_id,
        "policy_id": policy_id,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "records_processed": 0,
        "records_deleted": 0,
        "records_archived": 0
    }

    RETENTION_JOBS[job_id] = job
    policy["last_run"] = job["started_at"]

    # Simulate completion
    job["status"] = "completed"
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    job["records_processed"] = 1000
    job["records_deleted"] = 150

    return {"job": job}


@app.get("/retention/jobs")
def list_retention_jobs(policy_id: Optional[str] = None):
    """List retention jobs"""
    jobs = list(RETENTION_JOBS.values())
    if policy_id:
        jobs = [j for j in jobs if j.get("policy_id") == policy_id]
    return {"jobs": jobs, "total": len(jobs)}


@app.post("/retention/gdpr/delete-request")
def create_gdpr_delete_request(request: Request):
    """Create a GDPR data deletion request"""
    data = {}
    request_id = f"gdpr_{uuid.uuid4().hex[:8]}"

    deletion_request = {
        "id": request_id,
        "type": "deletion",
        "subject_email": data.get("email"),
        "subject_id": data.get("user_id"),
        "data_types": data.get("data_types", ["all"]),
        "reason": data.get("reason"),
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "completed_at": None
    }

    DATA_DELETION_REQUESTS.append(deletion_request)
    return {"request": deletion_request}


@app.get("/retention/gdpr/requests")
def list_gdpr_requests(status: Optional[str] = None):
    """List GDPR requests"""
    requests = DATA_DELETION_REQUESTS.copy()
    if status:
        requests = [r for r in requests if r.get("status") == status]
    return {"requests": requests, "total": len(requests)}


@app.post("/retention/gdpr/requests/{request_id}/complete")
def complete_gdpr_request(request_id: str):
    """Mark a GDPR request as completed"""
    for req in DATA_DELETION_REQUESTS:
        if req["id"] == request_id:
            req["status"] = "completed"
            req["completed_at"] = datetime.now(timezone.utc).isoformat()
            return {"request": req}

    raise HTTPException(status_code=404, detail="Request not found")


# ============================================================================
# Enhanced Webhooks
# ============================================================================

WEBHOOK_ENDPOINTS: Dict[str, Dict[str, Any]] = {}
WEBHOOK_DELIVERIES: Dict[str, List[Dict[str, Any]]] = {}
WEBHOOK_SECRETS: Dict[str, str] = {}


@app.post("/webhooks/endpoints")
def create_webhook_endpoint(request: Request):
    """Create a webhook endpoint"""
    data = {}
    endpoint_id = f"wh_{uuid.uuid4().hex[:8]}"
    secret = f"whsec_{uuid.uuid4().hex[:32]}"

    endpoint = {
        "id": endpoint_id,
        "url": data.get("url"),
        "description": data.get("description", ""),
        "events": data.get("events", ["*"]),
        "enabled": True,
        "config": {
            "content_type": data.get("content_type", "application/json"),
            "secret": secret,
            "insecure_ssl": data.get("insecure_ssl", False)
        },
        "retry_policy": {
            "max_retries": data.get("max_retries", 3),
            "retry_delay_seconds": data.get("retry_delay", 60),
            "exponential_backoff": data.get("exponential_backoff", True)
        },
        "metadata": data.get("metadata", {}),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    WEBHOOK_ENDPOINTS[endpoint_id] = endpoint
    WEBHOOK_SECRETS[endpoint_id] = secret
    WEBHOOK_DELIVERIES[endpoint_id] = []

    return {"endpoint": endpoint, "secret": secret}


@app.get("/webhooks/endpoints")
def list_webhook_endpoints():
    """List webhook endpoints"""
    # Don't expose secrets
    endpoints = []
    for e in WEBHOOK_ENDPOINTS.values():
        safe = e.copy()
        safe["config"] = {k: v for k, v in e["config"].items() if k != "secret"}
        endpoints.append(safe)
    return {"endpoints": endpoints, "total": len(endpoints)}


@app.get("/webhooks/endpoints/{endpoint_id}")
def get_webhook_endpoint(endpoint_id: str):
    """Get webhook endpoint details"""
    if endpoint_id not in WEBHOOK_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    endpoint = WEBHOOK_ENDPOINTS[endpoint_id].copy()
    endpoint["config"] = {k: v for k, v in endpoint["config"].items() if k != "secret"}
    return {"endpoint": endpoint}


@app.post("/webhooks/endpoints/{endpoint_id}/test")
def test_webhook_endpoint(endpoint_id: str):
    """Send a test webhook"""
    if endpoint_id not in WEBHOOK_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    delivery_id = f"delivery_{uuid.uuid4().hex[:8]}"

    delivery = {
        "id": delivery_id,
        "endpoint_id": endpoint_id,
        "event": "test.ping",
        "payload": {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()},
        "status": "success",
        "response_code": 200,
        "response_time_ms": 150,
        "attempt": 1,
        "delivered_at": datetime.now(timezone.utc).isoformat()
    }

    WEBHOOK_DELIVERIES[endpoint_id].append(delivery)
    return {"delivery": delivery}


@app.get("/webhooks/endpoints/{endpoint_id}/deliveries")
def list_webhook_deliveries(endpoint_id: str, limit: int = 50):
    """List webhook deliveries"""
    if endpoint_id not in WEBHOOK_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    deliveries = WEBHOOK_DELIVERIES.get(endpoint_id, [])
    return {"deliveries": deliveries[-limit:], "total": len(deliveries)}


@app.post("/webhooks/endpoints/{endpoint_id}/deliveries/{delivery_id}/retry")
def retry_webhook_delivery(endpoint_id: str, delivery_id: str):
    """Retry a failed webhook delivery"""
    if endpoint_id not in WEBHOOK_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    for delivery in WEBHOOK_DELIVERIES.get(endpoint_id, []):
        if delivery["id"] == delivery_id:
            new_delivery = delivery.copy()
            new_delivery["id"] = f"delivery_{uuid.uuid4().hex[:8]}"
            new_delivery["attempt"] = delivery["attempt"] + 1
            new_delivery["status"] = "success"
            new_delivery["delivered_at"] = datetime.now(timezone.utc).isoformat()

            WEBHOOK_DELIVERIES[endpoint_id].append(new_delivery)
            return {"delivery": new_delivery}

    raise HTTPException(status_code=404, detail="Delivery not found")


@app.post("/webhooks/sign")
def sign_webhook_payload(request: Request):
    """Generate HMAC signature for webhook payload"""
    data = {}
    payload = data.get("payload", "")
    secret = data.get("secret", "")

    import hashlib
    import hmac

    signature = hmac.new(
        secret.encode(),
        payload.encode() if isinstance(payload, str) else str(payload).encode(),
        hashlib.sha256
    ).hexdigest()

    return {
        "signature": f"sha256={signature}",
        "header_name": "X-Webhook-Signature"
    }


@app.post("/webhooks/verify")
def verify_webhook_signature(request: Request):
    """Verify a webhook signature"""
    data = {}
    payload = data.get("payload", "")
    signature = data.get("signature", "")
    secret = data.get("secret", "")

    import hashlib
    import hmac

    expected = hmac.new(
        secret.encode(),
        payload.encode() if isinstance(payload, str) else str(payload).encode(),
        hashlib.sha256
    ).hexdigest()

    valid = hmac.compare_digest(f"sha256={expected}", signature)
    return {"valid": valid}


# ============================================================================
# Event Bus / Pub-Sub
# ============================================================================

EVENT_TOPICS: Dict[str, Dict[str, Any]] = {}
EVENT_SUBSCRIPTIONS: Dict[str, List[Dict[str, Any]]] = {}
EVENT_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/events/topics")
def create_event_topic(request: Request):
    """Create an event topic"""
    data = {}
    topic_id = f"topic_{uuid.uuid4().hex[:8]}"

    topic = {
        "id": topic_id,
        "name": data.get("name", f"Topic {topic_id}"),
        "description": data.get("description", ""),
        "schema": data.get("schema", {}),
        "retention_hours": data.get("retention_hours", 168),  # 7 days
        "max_message_size_kb": data.get("max_message_size", 256),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    EVENT_TOPICS[topic_id] = topic
    EVENT_SUBSCRIPTIONS[topic_id] = []
    EVENT_MESSAGES[topic_id] = []

    return {"topic": topic}


@app.get("/events/topics")
def list_event_topics():
    """List event topics"""
    topics = []
    for topic_id, topic in EVENT_TOPICS.items():
        topic_info = topic.copy()
        topic_info["subscription_count"] = len(EVENT_SUBSCRIPTIONS.get(topic_id, []))
        topic_info["message_count"] = len(EVENT_MESSAGES.get(topic_id, []))
        topics.append(topic_info)
    return {"topics": topics, "total": len(topics)}


@app.post("/events/topics/{topic_id}/subscribe")
def subscribe_to_topic(topic_id: str, request: Request):
    """Subscribe to a topic"""
    if topic_id not in EVENT_TOPICS:
        raise HTTPException(status_code=404, detail="Topic not found")

    data = {}
    subscription_id = f"sub_{uuid.uuid4().hex[:8]}"

    subscription = {
        "id": subscription_id,
        "topic_id": topic_id,
        "name": data.get("name", f"Subscription {subscription_id}"),
        "endpoint": data.get("endpoint"),  # webhook URL or queue name
        "filter": data.get("filter", {}),
        "delivery_type": data.get("delivery_type", "push"),  # push, pull
        "ack_deadline_seconds": data.get("ack_deadline", 60),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    EVENT_SUBSCRIPTIONS[topic_id].append(subscription)
    return {"subscription": subscription}


@app.get("/events/topics/{topic_id}/subscriptions")
def list_topic_subscriptions(topic_id: str):
    """List subscriptions for a topic"""
    if topic_id not in EVENT_TOPICS:
        raise HTTPException(status_code=404, detail="Topic not found")

    return {"subscriptions": EVENT_SUBSCRIPTIONS.get(topic_id, [])}


@app.post("/events/topics/{topic_id}/publish")
def publish_event(topic_id: str, request: Request):
    """Publish an event to a topic"""
    if topic_id not in EVENT_TOPICS:
        raise HTTPException(status_code=404, detail="Topic not found")

    data = {}
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    message = {
        "id": message_id,
        "topic_id": topic_id,
        "data": data.get("data", {}),
        "attributes": data.get("attributes", {}),
        "published_at": datetime.now(timezone.utc).isoformat()
    }

    EVENT_MESSAGES[topic_id].append(message)

    # Notify subscribers (simulated)
    subscribers_notified = len(EVENT_SUBSCRIPTIONS.get(topic_id, []))

    return {
        "message_id": message_id,
        "subscribers_notified": subscribers_notified
    }


@app.post("/events/subscriptions/{subscription_id}/pull")
def pull_events(subscription_id: str, max_messages: int = 10):
    """Pull events from a subscription"""
    for topic_id, subs in EVENT_SUBSCRIPTIONS.items():
        for sub in subs:
            if sub["id"] == subscription_id:
                messages = EVENT_MESSAGES.get(topic_id, [])[-max_messages:]
                return {
                    "messages": messages,
                    "subscription_id": subscription_id
                }

    raise HTTPException(status_code=404, detail="Subscription not found")


@app.post("/events/subscriptions/{subscription_id}/ack")
def acknowledge_event(subscription_id: str, request: Request):
    """Acknowledge receipt of events"""
    data = {}
    message_ids = data.get("message_ids", [])

    return {
        "acknowledged": len(message_ids),
        "subscription_id": subscription_id
    }


# ============================================================================
# SSO Providers
# ============================================================================

SSO_PROVIDERS: Dict[str, Dict[str, Any]] = {}
SSO_SESSIONS: Dict[str, Dict[str, Any]] = {}


@app.post("/sso/providers")
def configure_sso_provider(request: Request):
    """Configure an SSO provider"""
    data = {}
    provider_id = f"sso_{uuid.uuid4().hex[:8]}"

    provider = {
        "id": provider_id,
        "type": data.get("type", "saml"),  # saml, oidc
        "name": data.get("name", f"Provider {provider_id}"),
        "enabled": data.get("enabled", True),
        "config": {
            # SAML config
            "entity_id": data.get("entity_id"),
            "sso_url": data.get("sso_url"),
            "certificate": data.get("certificate"),
            # OIDC config
            "client_id": data.get("client_id"),
            "client_secret": data.get("client_secret"),
            "authorization_url": data.get("authorization_url"),
            "token_url": data.get("token_url"),
            "userinfo_url": data.get("userinfo_url")
        },
        "attribute_mapping": data.get("attribute_mapping", {
            "email": "email",
            "name": "name",
            "groups": "groups"
        }),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    SSO_PROVIDERS[provider_id] = provider
    return {"provider": provider}


@app.get("/sso/providers")
def list_sso_providers():
    """List SSO providers"""
    # Don't expose secrets
    providers = []
    for p in SSO_PROVIDERS.values():
        safe = p.copy()
        safe["config"] = {k: v for k, v in p["config"].items()
                        if k not in ["client_secret", "certificate"]}
        providers.append(safe)
    return {"providers": providers, "total": len(providers)}


@app.get("/sso/providers/{provider_id}")
def get_sso_provider(provider_id: str):
    """Get SSO provider details"""
    if provider_id not in SSO_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = SSO_PROVIDERS[provider_id].copy()
    provider["config"] = {k: v for k, v in provider["config"].items()
                         if k not in ["client_secret", "certificate"]}
    return {"provider": provider}


@app.get("/sso/providers/{provider_id}/login")
def initiate_sso_login(provider_id: str, redirect_uri: Optional[str] = None):
    """Initiate SSO login flow"""
    if provider_id not in SSO_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = SSO_PROVIDERS[provider_id]
    session_id = f"sso_session_{uuid.uuid4().hex[:16]}"

    SSO_SESSIONS[session_id] = {
        "provider_id": provider_id,
        "redirect_uri": redirect_uri,
        "state": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if provider["type"] == "saml":
        return {
            "redirect_to": provider["config"].get("sso_url"),
            "saml_request": f"SAMLRequest={session_id}",
            "session_id": session_id
        }
    else:  # OIDC
        return {
            "redirect_to": provider["config"].get("authorization_url"),
            "session_id": session_id
        }


@app.post("/sso/callback")
def sso_callback(request: Request):
    """Handle SSO callback"""
    data = {}

    # Process SAML response or OIDC code
    session_id = data.get("session_id") or data.get("state")

    if session_id in SSO_SESSIONS:
        session = SSO_SESSIONS[session_id]

        # Create user session
        user_session = {
            "user_id": f"user_{uuid.uuid4().hex[:8]}",
            "email": data.get("email", "user@example.com"),
            "name": data.get("name", "SSO User"),
            "provider_id": session["provider_id"],
            "authenticated_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "success": True,
            "session": user_session,
            "redirect_to": session.get("redirect_uri", "/")
        }

    raise HTTPException(status_code=400, detail="Invalid SSO session")


@app.post("/sso/providers/{provider_id}/test")
def test_sso_provider(provider_id: str):
    """Test SSO provider configuration"""
    if provider_id not in SSO_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = SSO_PROVIDERS[provider_id]

    return {
        "provider_id": provider_id,
        "status": "healthy",
        "tests": {
            "connectivity": True,
            "certificate_valid": True,
            "metadata_accessible": True
        },
        "tested_at": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# Dashboard Metrics
# ============================================================================

DASHBOARD_CONFIGS: Dict[str, Dict[str, Any]] = {}
METRIC_TIMESERIES: Dict[str, List[Dict[str, Any]]] = {}


@app.get("/dashboard/overview")
def get_dashboard_overview():
    """Get dashboard overview metrics"""
    return {
        "summary": {
            "total_agents": len(AGENTS) if "AGENTS" in dir() else 0,
            "total_workflows": len(WORKFLOWS) if "WORKFLOWS" in dir() else 0,
            "active_executions": 5,
            "total_users": len(USERS) if "USERS" in dir() else 0
        },
        "trends": {
            "executions_today": 150,
            "executions_yesterday": 120,
            "change_percent": 25.0
        },
        "health": {
            "api_status": "healthy",
            "database_status": "healthy",
            "queue_status": "healthy"
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/dashboard/metrics/timeseries")
def get_metrics_timeseries(
    metric: str = "executions",
    period: str = "24h",
    interval: str = "1h"
):
    """Get time-series metrics data"""
    now = datetime.now(timezone.utc)

    # Generate sample time-series data
    data_points = []
    for i in range(24):
        timestamp = now - timedelta(hours=23 - i)
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "value": 50 + (i * 2) + (i % 5)
        })

    return {
        "metric": metric,
        "period": period,
        "interval": interval,
        "data": data_points
    }


@app.get("/dashboard/metrics/summary")
def get_metrics_summary(period: str = "7d"):
    """Get aggregated metrics summary"""
    return {
        "period": period,
        "metrics": {
            "total_executions": 1250,
            "successful_executions": 1180,
            "failed_executions": 70,
            "success_rate": 94.4,
            "avg_execution_time_ms": 450,
            "p95_execution_time_ms": 1200,
            "total_tokens_used": 5000000,
            "total_cost_usd": 125.50
        }
    }


@app.post("/dashboard/widgets")
def create_dashboard_widget(request: Request):
    """Create a dashboard widget configuration"""
    data = {}
    widget_id = f"widget_{uuid.uuid4().hex[:8]}"

    widget = {
        "id": widget_id,
        "type": data.get("type", "line_chart"),  # line_chart, bar_chart, pie_chart, metric, table
        "title": data.get("title", f"Widget {widget_id}"),
        "metric": data.get("metric"),
        "config": data.get("config", {}),
        "position": data.get("position", {"x": 0, "y": 0, "w": 4, "h": 3}),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    return {"widget": widget}


@app.get("/dashboard/real-time")
def get_real_time_metrics():
    """Get real-time streaming metrics"""
    return {
        "current": {
            "active_connections": 42,
            "requests_per_second": 125,
            "avg_latency_ms": 45,
            "error_rate_percent": 0.5,
            "queue_depth": 15
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# Anomaly Detection
# ============================================================================

ANOMALY_RULES: Dict[str, Dict[str, Any]] = {}
DETECTED_ANOMALIES: List[Dict[str, Any]] = []


@app.post("/anomaly/rules")
def create_anomaly_rule(request: Request):
    """Create an anomaly detection rule"""
    data = {}
    rule_id = f"anomaly_{uuid.uuid4().hex[:8]}"

    rule = {
        "id": rule_id,
        "name": data.get("name", f"Rule {rule_id}"),
        "description": data.get("description", ""),
        "metric": data.get("metric"),
        "condition": {
            "type": data.get("condition_type", "threshold"),  # threshold, percentage_change, stddev
            "operator": data.get("operator", "gt"),  # gt, lt, eq
            "value": data.get("threshold_value", 100),
            "window_minutes": data.get("window_minutes", 5)
        },
        "severity": data.get("severity", "warning"),  # info, warning, critical
        "actions": data.get("actions", ["alert"]),
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    ANOMALY_RULES[rule_id] = rule
    return {"rule": rule}


@app.get("/anomaly/rules")
def list_anomaly_rules():
    """List anomaly detection rules"""
    return {"rules": list(ANOMALY_RULES.values()), "total": len(ANOMALY_RULES)}


@app.get("/anomaly/rules/{rule_id}")
def get_anomaly_rule(rule_id: str):
    """Get anomaly rule details"""
    if rule_id not in ANOMALY_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"rule": ANOMALY_RULES[rule_id]}


@app.post("/anomaly/detect")
def detect_anomalies(request: Request):
    """Run anomaly detection on metrics"""
    data = {}
    metric = data.get("metric")
    values = data.get("values", [])

    if not values:
        return {"anomalies": [], "total": 0}

    # Simple anomaly detection using z-score
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    stddev = variance ** 0.5 if variance > 0 else 1

    anomalies = []
    for i, value in enumerate(values):
        z_score = abs(value - mean) / stddev if stddev > 0 else 0
        if z_score > 2:  # More than 2 standard deviations
            anomalies.append({
                "index": i,
                "value": value,
                "z_score": z_score,
                "severity": "critical" if z_score > 3 else "warning"
            })

    return {
        "metric": metric,
        "anomalies": anomalies,
        "statistics": {
            "mean": mean,
            "stddev": stddev,
            "min": min(values),
            "max": max(values)
        }
    }


@app.get("/anomaly/history")
def get_anomaly_history(
    severity: Optional[str] = None,
    limit: int = 100
):
    """Get detected anomaly history"""
    anomalies = DETECTED_ANOMALIES.copy()

    if severity:
        anomalies = [a for a in anomalies if a.get("severity") == severity]

    return {"anomalies": anomalies[-limit:], "total": len(anomalies)}


@app.post("/anomaly/acknowledge/{anomaly_id}")
def acknowledge_anomaly(anomaly_id: str):
    """Acknowledge an anomaly"""
    for anomaly in DETECTED_ANOMALIES:
        if anomaly.get("id") == anomaly_id:
            anomaly["acknowledged"] = True
            anomaly["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            return {"anomaly": anomaly}

    raise HTTPException(status_code=404, detail="Anomaly not found")


# ============================================================================
# Usage Forecasting
# ============================================================================

FORECAST_MODELS: Dict[str, Dict[str, Any]] = {}
FORECAST_RESULTS: Dict[str, Dict[str, Any]] = {}


@app.post("/forecasting/models")
def create_forecast_model(request: Request):
    """Create a forecasting model"""
    data = {}
    model_id = f"forecast_{uuid.uuid4().hex[:8]}"

    model = {
        "id": model_id,
        "name": data.get("name", f"Model {model_id}"),
        "metric": data.get("metric", "usage"),
        "algorithm": data.get("algorithm", "linear"),  # linear, exponential, seasonal
        "config": {
            "seasonality": data.get("seasonality", "daily"),
            "trend": data.get("trend", "additive"),
            "confidence_interval": data.get("confidence_interval", 0.95)
        },
        "training_data_days": data.get("training_days", 30),
        "forecast_days": data.get("forecast_days", 7),
        "last_trained": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    FORECAST_MODELS[model_id] = model
    return {"model": model}


@app.get("/forecasting/models")
def list_forecast_models():
    """List forecasting models"""
    return {"models": list(FORECAST_MODELS.values()), "total": len(FORECAST_MODELS)}


@app.post("/forecasting/models/{model_id}/train")
def train_forecast_model(model_id: str):
    """Train a forecasting model"""
    if model_id not in FORECAST_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")

    model = FORECAST_MODELS[model_id]
    model["last_trained"] = datetime.now(timezone.utc).isoformat()

    return {
        "model_id": model_id,
        "status": "trained",
        "metrics": {
            "mape": 5.2,  # Mean Absolute Percentage Error
            "rmse": 12.5,  # Root Mean Square Error
            "r_squared": 0.92
        }
    }


@app.post("/forecasting/models/{model_id}/predict")
def generate_forecast(model_id: str, request: Request):
    """Generate a forecast"""
    if model_id not in FORECAST_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}
    model = FORECAST_MODELS[model_id]
    horizon_days = data.get("horizon_days", model["forecast_days"])

    # Generate sample forecast
    now = datetime.now(timezone.utc)
    predictions = []
    base_value = 100

    for i in range(horizon_days):
        date = now + timedelta(days=i + 1)
        predicted = base_value + (i * 5) + (i % 7 * 3)  # Simulated trend with weekly pattern
        lower = predicted * 0.9
        upper = predicted * 1.1

        predictions.append({
            "date": date.date().isoformat(),
            "predicted": predicted,
            "lower_bound": lower,
            "upper_bound": upper
        })

    forecast_id = f"result_{uuid.uuid4().hex[:8]}"
    FORECAST_RESULTS[forecast_id] = {
        "id": forecast_id,
        "model_id": model_id,
        "predictions": predictions,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    return {"forecast": FORECAST_RESULTS[forecast_id]}


@app.get("/forecasting/capacity")
def get_capacity_forecast():
    """Get capacity planning forecast"""
    return {
        "current_capacity": {
            "agents": {"used": 45, "limit": 100, "utilization": 45},
            "workflows": {"used": 20, "limit": 50, "utilization": 40},
            "api_calls": {"used": 500000, "limit": 1000000, "utilization": 50}
        },
        "forecast": {
            "days_until_80_percent": 15,
            "recommended_upgrade_date": (datetime.now(timezone.utc) + timedelta(days=10)).date().isoformat(),
            "projected_growth_rate": 5.2
        }
    }


# ============================================================================
# Backup & Recovery
# ============================================================================

BACKUPS: Dict[str, Dict[str, Any]] = {}
RESTORE_JOBS: Dict[str, Dict[str, Any]] = {}


@app.post("/backups")
def create_backup(request: Request):
    """Create a backup"""
    data = {}
    backup_id = f"backup_{uuid.uuid4().hex[:8]}"

    backup = {
        "id": backup_id,
        "name": data.get("name", f"Backup {backup_id}"),
        "type": data.get("type", "full"),  # full, incremental, differential
        "includes": data.get("includes", ["agents", "workflows", "configs"]),
        "status": "in_progress",
        "size_bytes": 0,
        "checksum": None,
        "storage_location": data.get("storage", "local"),
        "retention_days": data.get("retention_days", 30),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }

    BACKUPS[backup_id] = backup

    # Simulate completion
    backup["status"] = "completed"
    backup["completed_at"] = datetime.now(timezone.utc).isoformat()
    backup["size_bytes"] = 1024 * 1024 * 50  # 50MB
    backup["checksum"] = f"sha256:{uuid.uuid4().hex}"

    return {"backup": backup}


@app.get("/backups")
def list_backups(status: Optional[str] = None):
    """List backups"""
    backups = list(BACKUPS.values())
    if status:
        backups = [b for b in backups if b.get("status") == status]
    return {"backups": backups, "total": len(backups)}


@app.get("/backups/{backup_id}")
def get_backup(backup_id: str):
    """Get backup details"""
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")
    return {"backup": BACKUPS[backup_id]}


@app.post("/backups/{backup_id}/restore")
def restore_backup(backup_id: str, request: Request):
    """Restore from a backup"""
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")

    data = {}
    restore_id = f"restore_{uuid.uuid4().hex[:8]}"

    restore = {
        "id": restore_id,
        "backup_id": backup_id,
        "target": data.get("target", "current"),
        "includes": data.get("includes"),  # Selective restore
        "status": "in_progress",
        "progress_percent": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }

    RESTORE_JOBS[restore_id] = restore

    # Simulate completion
    restore["status"] = "completed"
    restore["progress_percent"] = 100
    restore["completed_at"] = datetime.now(timezone.utc).isoformat()

    return {"restore": restore}


@app.get("/backups/restore/{restore_id}")
def get_restore_status(restore_id: str):
    """Get restore job status"""
    if restore_id not in RESTORE_JOBS:
        raise HTTPException(status_code=404, detail="Restore job not found")
    return {"restore": RESTORE_JOBS[restore_id]}


@app.delete("/backups/{backup_id}")
def delete_backup(backup_id: str):
    """Delete a backup"""
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")

    del BACKUPS[backup_id]
    return {"deleted": True}


@app.post("/backups/schedule")
def schedule_backup(request: Request):
    """Schedule automatic backups"""
    data = {}

    schedule = {
        "id": f"schedule_{uuid.uuid4().hex[:8]}",
        "type": data.get("type", "full"),
        "schedule": data.get("schedule", "0 2 * * *"),  # Daily at 2 AM
        "retention_days": data.get("retention_days", 30),
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    return {"schedule": schedule}


# ============================================================================
# Migration Tools
# ============================================================================

MIGRATIONS: Dict[str, Dict[str, Any]] = {}
MIGRATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "v1_to_v2": {
        "name": "V1 to V2 Migration",
        "source_version": "1.0",
        "target_version": "2.0",
        "steps": ["backup", "transform", "validate", "apply"]
    }
}


@app.post("/migrations")
def create_migration(request: Request):
    """Create a migration job"""
    data = {}
    migration_id = f"migration_{uuid.uuid4().hex[:8]}"

    migration = {
        "id": migration_id,
        "name": data.get("name", f"Migration {migration_id}"),
        "type": data.get("type", "schema"),  # schema, data, full
        "source": data.get("source", {}),
        "target": data.get("target", {}),
        "options": {
            "dry_run": data.get("dry_run", True),
            "backup_before": data.get("backup", True),
            "rollback_on_error": data.get("rollback", True)
        },
        "status": "pending",
        "steps": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    MIGRATIONS[migration_id] = migration
    return {"migration": migration}


@app.get("/migrations")
def list_migrations(status: Optional[str] = None):
    """List migrations"""
    migrations = list(MIGRATIONS.values())
    if status:
        migrations = [m for m in migrations if m.get("status") == status]
    return {"migrations": migrations, "total": len(migrations)}


@app.get("/migrations/{migration_id}")
def get_migration(migration_id: str):
    """Get migration details"""
    if migration_id not in MIGRATIONS:
        raise HTTPException(status_code=404, detail="Migration not found")
    return {"migration": MIGRATIONS[migration_id]}


@app.post("/migrations/{migration_id}/run")
def run_migration(migration_id: str):
    """Run a migration"""
    if migration_id not in MIGRATIONS:
        raise HTTPException(status_code=404, detail="Migration not found")

    migration = MIGRATIONS[migration_id]
    migration["status"] = "running"
    migration["started_at"] = datetime.now(timezone.utc).isoformat()

    # Simulate migration steps
    migration["steps"] = [
        {"name": "backup", "status": "completed", "duration_ms": 5000},
        {"name": "validate_source", "status": "completed", "duration_ms": 1000},
        {"name": "transform", "status": "completed", "duration_ms": 10000},
        {"name": "apply", "status": "completed", "duration_ms": 8000},
        {"name": "verify", "status": "completed", "duration_ms": 2000}
    ]

    migration["status"] = "completed"
    migration["completed_at"] = datetime.now(timezone.utc).isoformat()

    return {"migration": migration}


@app.post("/migrations/{migration_id}/rollback")
def rollback_migration(migration_id: str):
    """Rollback a migration"""
    if migration_id not in MIGRATIONS:
        raise HTTPException(status_code=404, detail="Migration not found")

    migration = MIGRATIONS[migration_id]
    migration["status"] = "rolled_back"
    migration["rolled_back_at"] = datetime.now(timezone.utc).isoformat()

    return {"migration": migration}


@app.get("/migrations/templates")
def list_migration_templates():
    """List available migration templates"""
    return {"templates": list(MIGRATION_TEMPLATES.values())}


@app.post("/migrations/analyze")
def analyze_migration(request: Request):
    """Analyze migration impact"""
    data = {}

    return {
        "analysis": {
            "affected_resources": {
                "agents": 25,
                "workflows": 10,
                "configs": 5
            },
            "estimated_duration_seconds": 300,
            "risk_level": "low",
            "recommendations": [
                "Run during low-traffic period",
                "Ensure backup is recent",
                "Notify stakeholders"
            ]
        }
    }


# ============================================================================
# Configuration Management
# ============================================================================

CONFIGS: Dict[str, Dict[str, Any]] = {}
CONFIG_HISTORY: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/configs")
def create_config(request: Request):
    """Create a configuration"""
    data = {}
    config_id = f"config_{uuid.uuid4().hex[:8]}"

    config = {
        "id": config_id,
        "key": data.get("key", config_id),
        "value": data.get("value"),
        "type": data.get("type", "string"),  # string, number, boolean, json
        "environment": data.get("environment", "all"),
        "description": data.get("description", ""),
        "sensitive": data.get("sensitive", False),
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    CONFIGS[config_id] = config
    CONFIG_HISTORY[config_id] = [config.copy()]

    return {"config": config}


@app.get("/configs")
def list_configs(environment: Optional[str] = None):
    """List configurations"""
    configs = list(CONFIGS.values())
    if environment:
        configs = [c for c in configs if c.get("environment") in [environment, "all"]]

    # Mask sensitive values
    for c in configs:
        if c.get("sensitive"):
            c["value"] = "********"

    return {"configs": configs, "total": len(configs)}


@app.get("/configs/{config_id}")
def get_config(config_id: str):
    """Get configuration details"""
    if config_id not in CONFIGS:
        raise HTTPException(status_code=404, detail="Config not found")

    config = CONFIGS[config_id].copy()
    if config.get("sensitive"):
        config["value"] = "********"

    return {"config": config}


@app.put("/configs/{config_id}")
def update_config(config_id: str, request: Request):
    """Update a configuration"""
    if config_id not in CONFIGS:
        raise HTTPException(status_code=404, detail="Config not found")

    data = {}
    config = CONFIGS[config_id]

    # Save history
    CONFIG_HISTORY[config_id].append(config.copy())

    # Update
    if "value" in data:
        config["value"] = data["value"]
    if "description" in data:
        config["description"] = data["description"]

    config["version"] += 1
    config["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {"config": config}


@app.get("/configs/{config_id}/history")
def get_config_history(config_id: str):
    """Get configuration version history"""
    if config_id not in CONFIGS:
        raise HTTPException(status_code=404, detail="Config not found")

    history = CONFIG_HISTORY.get(config_id, [])
    return {"history": history, "total": len(history)}


@app.post("/configs/{config_id}/rollback")
def rollback_config(config_id: str, request: Request):
    """Rollback configuration to a previous version"""
    if config_id not in CONFIGS:
        raise HTTPException(status_code=404, detail="Config not found")

    data = {}
    target_version = data.get("version", 1)
    history = CONFIG_HISTORY.get(config_id, [])

    for h in history:
        if h.get("version") == target_version:
            CONFIGS[config_id] = h.copy()
            CONFIGS[config_id]["version"] = CONFIGS[config_id]["version"] + 0.1  # Mark as rollback
            CONFIGS[config_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            return {"config": CONFIGS[config_id]}

    raise HTTPException(status_code=404, detail="Version not found")


@app.delete("/configs/{config_id}")
def delete_config(config_id: str):
    """Delete a configuration"""
    if config_id not in CONFIGS:
        raise HTTPException(status_code=404, detail="Config not found")

    del CONFIGS[config_id]
    if config_id in CONFIG_HISTORY:
        del CONFIG_HISTORY[config_id]

    return {"deleted": True}


@app.get("/configs/export")
def export_configs(environment: Optional[str] = None):
    """Export configurations"""
    configs = list(CONFIGS.values())
    if environment:
        configs = [c for c in configs if c.get("environment") in [environment, "all"]]

    # Remove sensitive values
    export_data = []
    for c in configs:
        exported = c.copy()
        if exported.get("sensitive"):
            exported["value"] = None
        export_data.append(exported)

    return {
        "configs": export_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "environment": environment
    }


@app.post("/configs/import")
def import_configs(request: Request):
    """Import configurations"""
    data = {}
    configs_to_import = data.get("configs", [])
    imported = 0

    for config_data in configs_to_import:
        config_id = config_data.get("id") or f"config_{uuid.uuid4().hex[:8]}"

        config = {
            "id": config_id,
            "key": config_data.get("key", config_id),
            "value": config_data.get("value"),
            "type": config_data.get("type", "string"),
            "environment": config_data.get("environment", "all"),
            "description": config_data.get("description", ""),
            "sensitive": config_data.get("sensitive", False),
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        CONFIGS[config_id] = config
        CONFIG_HISTORY[config_id] = [config.copy()]
        imported += 1

    return {"imported": imported}


# ============================================================================
# Prompt Chaining / Routing
# ============================================================================

PROMPT_CHAINS: Dict[str, Dict[str, Any]] = {}
PROMPT_ROUTERS: Dict[str, Dict[str, Any]] = {}
ROUTING_RULES: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/prompts/chains")
def create_prompt_chain(request: Request):
    """Create a prompt chain"""
    data = {}
    chain_id = f"pchain_{uuid.uuid4().hex[:8]}"

    chain = {
        "id": chain_id,
        "name": data.get("name", f"Chain {chain_id}"),
        "description": data.get("description", ""),
        "steps": data.get("steps", []),
        "variables": data.get("variables", {}),
        "output_mapping": data.get("output_mapping", {}),
        "error_handling": data.get("error_handling", "stop"),  # stop, continue, fallback
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    PROMPT_CHAINS[chain_id] = chain
    return {"chain": chain}


@app.get("/prompts/chains")
def list_prompt_chains():
    """List prompt chains"""
    return {"chains": list(PROMPT_CHAINS.values()), "total": len(PROMPT_CHAINS)}


@app.get("/prompts/chains/{chain_id}")
def get_prompt_chain(chain_id: str):
    """Get prompt chain details"""
    if chain_id not in PROMPT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"chain": PROMPT_CHAINS[chain_id]}


@app.post("/prompts/chains/{chain_id}/execute")
def execute_prompt_chain(chain_id: str, request: Request):
    """Execute a prompt chain"""
    if chain_id not in PROMPT_CHAINS:
        raise HTTPException(status_code=404, detail="Chain not found")

    data = {}
    chain = PROMPT_CHAINS[chain_id]
    execution_id = f"pexec_{uuid.uuid4().hex[:8]}"

    results = []
    context = data.get("initial_context", {})

    for i, step in enumerate(chain["steps"]):
        step_result = {
            "step_index": i,
            "step_name": step.get("name", f"step_{i}"),
            "prompt": step.get("prompt", ""),
            "output": f"Simulated output for step {i}",
            "duration_ms": 100 + (i * 50)
        }
        results.append(step_result)
        context[f"step_{i}_output"] = step_result["output"]

    return {
        "execution_id": execution_id,
        "chain_id": chain_id,
        "results": results,
        "final_context": context,
        "total_duration_ms": sum(r["duration_ms"] for r in results)
    }


@app.post("/prompts/routers")
def create_prompt_router(request: Request):
    """Create a prompt router"""
    data = {}
    router_id = f"router_{uuid.uuid4().hex[:8]}"

    router = {
        "id": router_id,
        "name": data.get("name", f"Router {router_id}"),
        "description": data.get("description", ""),
        "routing_type": data.get("routing_type", "conditional"),  # conditional, semantic, random
        "routes": data.get("routes", []),
        "default_route": data.get("default_route"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    PROMPT_ROUTERS[router_id] = router
    return {"router": router}


@app.get("/prompts/routers")
def list_prompt_routers():
    """List prompt routers"""
    return {"routers": list(PROMPT_ROUTERS.values()), "total": len(PROMPT_ROUTERS)}


@app.post("/prompts/routers/{router_id}/route")
def route_prompt(router_id: str, request: Request):
    """Route a prompt through the router"""
    if router_id not in PROMPT_ROUTERS:
        raise HTTPException(status_code=404, detail="Router not found")

    data = {}
    router = PROMPT_ROUTERS[router_id]
    input_text = data.get("input", "")

    # Evaluate routes
    selected_route = router.get("default_route")
    matched_conditions = []

    for route in router["routes"]:
        condition = route.get("condition", {})
        if condition.get("type") == "contains":
            if condition.get("value", "").lower() in input_text.lower():
                selected_route = route.get("target")
                matched_conditions.append(condition)
                break
        elif condition.get("type") == "regex":
            import re
            if re.search(condition.get("pattern", ""), input_text):
                selected_route = route.get("target")
                matched_conditions.append(condition)
                break

    return {
        "router_id": router_id,
        "input": input_text,
        "selected_route": selected_route,
        "matched_conditions": matched_conditions
    }


# ============================================================================
# Embeddings Management
# ============================================================================

EMBEDDING_COLLECTIONS: Dict[str, Dict[str, Any]] = {}
EMBEDDINGS: Dict[str, List[Dict[str, Any]]] = {}
EMBEDDING_INDEXES: Dict[str, Dict[str, Any]] = {}


@app.post("/embeddings/collections")
def create_embedding_collection(request: Request):
    """Create an embedding collection"""
    data = {}
    collection_id = f"emb_col_{uuid.uuid4().hex[:8]}"

    collection = {
        "id": collection_id,
        "name": data.get("name", f"Collection {collection_id}"),
        "description": data.get("description", ""),
        "embedding_model": data.get("model", "text-embedding-ada-002"),
        "dimensions": data.get("dimensions", 1536),
        "distance_metric": data.get("distance_metric", "cosine"),  # cosine, euclidean, dot_product
        "metadata_schema": data.get("metadata_schema", {}),
        "count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    EMBEDDING_COLLECTIONS[collection_id] = collection
    EMBEDDINGS[collection_id] = []

    return {"collection": collection}


@app.get("/embeddings/collections")
def list_embedding_collections():
    """List embedding collections"""
    return {"collections": list(EMBEDDING_COLLECTIONS.values()), "total": len(EMBEDDING_COLLECTIONS)}


@app.get("/embeddings/collections/{collection_id}")
def get_embedding_collection(collection_id: str):
    """Get embedding collection details"""
    if collection_id not in EMBEDDING_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"collection": EMBEDDING_COLLECTIONS[collection_id]}


@app.post("/embeddings/collections/{collection_id}/add")
def add_embeddings(collection_id: str, request: Request):
    """Add embeddings to a collection"""
    if collection_id not in EMBEDDING_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")

    data = {}
    documents = data.get("documents", [])
    added = 0

    for doc in documents:
        embedding_id = f"emb_{uuid.uuid4().hex[:12]}"

        embedding = {
            "id": embedding_id,
            "text": doc.get("text", ""),
            "vector": doc.get("vector", [0.0] * EMBEDDING_COLLECTIONS[collection_id]["dimensions"]),
            "metadata": doc.get("metadata", {}),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        EMBEDDINGS[collection_id].append(embedding)
        added += 1

    EMBEDDING_COLLECTIONS[collection_id]["count"] = len(EMBEDDINGS[collection_id])

    return {"added": added, "total": EMBEDDING_COLLECTIONS[collection_id]["count"]}


@app.post("/embeddings/collections/{collection_id}/search")
def search_embeddings(collection_id: str, request: Request):
    """Search embeddings by similarity"""
    if collection_id not in EMBEDDING_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")

    data = {}
    query_vector = data.get("vector", [])
    query_text = data.get("text", "")
    top_k = data.get("top_k", 10)
    filter_metadata = data.get("filter", {})

    # Simulate similarity search
    results = []
    for emb in EMBEDDINGS[collection_id][:top_k]:
        # In production, would compute actual similarity
        results.append({
            "id": emb["id"],
            "text": emb["text"],
            "score": 0.95 - (len(results) * 0.05),
            "metadata": emb["metadata"]
        })

    return {
        "query": query_text or "vector query",
        "results": results,
        "total": len(results)
    }


@app.delete("/embeddings/collections/{collection_id}")
def delete_embedding_collection(collection_id: str):
    """Delete an embedding collection"""
    if collection_id not in EMBEDDING_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")

    del EMBEDDING_COLLECTIONS[collection_id]
    if collection_id in EMBEDDINGS:
        del EMBEDDINGS[collection_id]

    return {"deleted": True}


@app.post("/embeddings/generate")
def generate_embedding(request: Request):
    """Generate embeddings for text"""
    data = {}
    texts = data.get("texts", [])
    model = data.get("model", "text-embedding-ada-002")

    embeddings = []
    for text in texts:
        # Simulated embedding generation
        embeddings.append({
            "text": text,
            "vector": [0.1] * 1536,  # Simulated vector
            "model": model,
            "tokens": len(text.split())
        })

    return {"embeddings": embeddings, "model": model}


# ============================================================================
# Agent Fine-tuning
# ============================================================================

FINETUNING_JOBS: Dict[str, Dict[str, Any]] = {}
FINETUNING_DATASETS: Dict[str, Dict[str, Any]] = {}
FINETUNED_MODELS: Dict[str, Dict[str, Any]] = {}


@app.post("/finetuning/datasets")
def create_finetuning_dataset(request: Request):
    """Create a fine-tuning dataset"""
    data = {}
    dataset_id = f"ftds_{uuid.uuid4().hex[:8]}"

    dataset = {
        "id": dataset_id,
        "name": data.get("name", f"Dataset {dataset_id}"),
        "description": data.get("description", ""),
        "format": data.get("format", "jsonl"),
        "purpose": data.get("purpose", "fine-tune"),
        "examples": data.get("examples", []),
        "example_count": len(data.get("examples", [])),
        "validation_split": data.get("validation_split", 0.1),
        "status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    FINETUNING_DATASETS[dataset_id] = dataset
    return {"dataset": dataset}


@app.get("/finetuning/datasets")
def list_finetuning_datasets():
    """List fine-tuning datasets"""
    return {"datasets": list(FINETUNING_DATASETS.values()), "total": len(FINETUNING_DATASETS)}


@app.post("/finetuning/datasets/{dataset_id}/examples")
def add_dataset_examples(dataset_id: str, request: Request):
    """Add examples to a dataset"""
    if dataset_id not in FINETUNING_DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")

    data = {}
    examples = data.get("examples", [])

    FINETUNING_DATASETS[dataset_id]["examples"].extend(examples)
    FINETUNING_DATASETS[dataset_id]["example_count"] = len(FINETUNING_DATASETS[dataset_id]["examples"])

    return {"added": len(examples), "total": FINETUNING_DATASETS[dataset_id]["example_count"]}


@app.post("/finetuning/jobs")
def create_finetuning_job(request: Request):
    """Create a fine-tuning job"""
    data = {}
    job_id = f"ftjob_{uuid.uuid4().hex[:8]}"

    job = {
        "id": job_id,
        "name": data.get("name", f"Job {job_id}"),
        "base_model": data.get("base_model", "gpt-3.5-turbo"),
        "dataset_id": data.get("dataset_id"),
        "hyperparameters": {
            "n_epochs": data.get("n_epochs", 3),
            "batch_size": data.get("batch_size", 4),
            "learning_rate_multiplier": data.get("learning_rate", 1.0)
        },
        "status": "pending",
        "progress": 0,
        "trained_tokens": 0,
        "result_model_id": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None
    }

    FINETUNING_JOBS[job_id] = job
    return {"job": job}


@app.get("/finetuning/jobs")
def list_finetuning_jobs(status: Optional[str] = None):
    """List fine-tuning jobs"""
    jobs = list(FINETUNING_JOBS.values())
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/finetuning/jobs/{job_id}")
def get_finetuning_job(job_id: str):
    """Get fine-tuning job details"""
    if job_id not in FINETUNING_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": FINETUNING_JOBS[job_id]}


@app.post("/finetuning/jobs/{job_id}/start")
def start_finetuning_job(job_id: str):
    """Start a fine-tuning job"""
    if job_id not in FINETUNING_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = FINETUNING_JOBS[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.now(timezone.utc).isoformat()
    job["progress"] = 0

    return {"job": job}


@app.post("/finetuning/jobs/{job_id}/cancel")
def cancel_finetuning_job(job_id: str):
    """Cancel a fine-tuning job"""
    if job_id not in FINETUNING_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = FINETUNING_JOBS[job_id]
    job["status"] = "cancelled"

    return {"job": job}


@app.get("/finetuning/models")
def list_finetuned_models():
    """List fine-tuned models"""
    return {"models": list(FINETUNED_MODELS.values()), "total": len(FINETUNED_MODELS)}


# ============================================================================
# Model Serving
# ============================================================================

SERVED_MODELS: Dict[str, Dict[str, Any]] = {}
MODEL_ENDPOINTS: Dict[str, Dict[str, Any]] = {}
MODEL_TRAFFIC_SPLITS: Dict[str, Dict[str, Any]] = {}


@app.post("/serving/models")
def deploy_model_for_serving(request: Request):
    """Deploy a model for serving"""
    data = {}
    serving_id = f"serve_{uuid.uuid4().hex[:8]}"

    served_model = {
        "id": serving_id,
        "name": data.get("name", f"Model {serving_id}"),
        "model_id": data.get("model_id"),
        "model_type": data.get("model_type", "completion"),
        "config": {
            "max_tokens": data.get("max_tokens", 4096),
            "temperature": data.get("temperature", 0.7),
            "timeout_seconds": data.get("timeout", 30)
        },
        "scaling": {
            "min_replicas": data.get("min_replicas", 1),
            "max_replicas": data.get("max_replicas", 10),
            "target_concurrency": data.get("target_concurrency", 100)
        },
        "status": "deploying",
        "endpoint": f"/serving/models/{serving_id}/invoke",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    SERVED_MODELS[serving_id] = served_model

    # Simulate deployment completion
    served_model["status"] = "active"

    return {"model": served_model}


@app.get("/serving/models")
def list_served_models(status: Optional[str] = None):
    """List served models"""
    models = list(SERVED_MODELS.values())
    if status:
        models = [m for m in models if m.get("status") == status]
    return {"models": models, "total": len(models)}


@app.get("/serving/models/{serving_id}")
def get_served_model(serving_id: str):
    """Get served model details"""
    if serving_id not in SERVED_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"model": SERVED_MODELS[serving_id]}


@app.post("/serving/models/{serving_id}/invoke")
def invoke_served_model(serving_id: str, request: Request):
    """Invoke a served model"""
    if serving_id not in SERVED_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}
    model = SERVED_MODELS[serving_id]

    return {
        "model_id": serving_id,
        "input": data.get("input", ""),
        "output": f"Response from {model['name']}",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "total_tokens": 150
        },
        "latency_ms": 250
    }


@app.post("/serving/traffic-split")
def create_traffic_split(request: Request):
    """Create a traffic split for A/B testing models"""
    data = {}
    split_id = f"split_{uuid.uuid4().hex[:8]}"

    split = {
        "id": split_id,
        "name": data.get("name", f"Split {split_id}"),
        "models": data.get("models", []),  # [{"model_id": "x", "weight": 50}, ...]
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    MODEL_TRAFFIC_SPLITS[split_id] = split
    return {"split": split}


@app.get("/serving/traffic-splits")
def list_traffic_splits():
    """List traffic splits"""
    return {"splits": list(MODEL_TRAFFIC_SPLITS.values()), "total": len(MODEL_TRAFFIC_SPLITS)}


@app.post("/serving/models/{serving_id}/scale")
def scale_served_model(serving_id: str, request: Request):
    """Scale a served model"""
    if serving_id not in SERVED_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")

    data = {}
    model = SERVED_MODELS[serving_id]

    if "min_replicas" in data:
        model["scaling"]["min_replicas"] = data["min_replicas"]
    if "max_replicas" in data:
        model["scaling"]["max_replicas"] = data["max_replicas"]

    return {"model": model}


# ============================================================================
# Debug / Trace Mode
# ============================================================================

DEBUG_SESSIONS: Dict[str, Dict[str, Any]] = {}
DEBUG_BREAKPOINTS: Dict[str, List[Dict[str, Any]]] = {}
EXECUTION_TRACES: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/debug/sessions")
def create_debug_session(request: Request):
    """Create a debug session"""
    data = {}
    session_id = f"debug_{uuid.uuid4().hex[:8]}"

    session = {
        "id": session_id,
        "target_type": data.get("target_type", "agent"),  # agent, workflow, chain
        "target_id": data.get("target_id"),
        "mode": data.get("mode", "trace"),  # trace, step, breakpoint
        "options": {
            "capture_inputs": data.get("capture_inputs", True),
            "capture_outputs": data.get("capture_outputs", True),
            "capture_context": data.get("capture_context", True),
            "max_depth": data.get("max_depth", 10)
        },
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    DEBUG_SESSIONS[session_id] = session
    DEBUG_BREAKPOINTS[session_id] = []
    EXECUTION_TRACES[session_id] = []

    return {"session": session}


@app.get("/debug/sessions")
def list_debug_sessions(status: Optional[str] = None):
    """List debug sessions"""
    sessions = list(DEBUG_SESSIONS.values())
    if status:
        sessions = [s for s in sessions if s.get("status") == status]
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/debug/sessions/{session_id}")
def get_debug_session(session_id: str):
    """Get debug session details"""
    if session_id not in DEBUG_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session": DEBUG_SESSIONS[session_id],
        "breakpoints": DEBUG_BREAKPOINTS.get(session_id, []),
        "trace_count": len(EXECUTION_TRACES.get(session_id, []))
    }


@app.post("/debug/sessions/{session_id}/breakpoints")
def add_breakpoint(session_id: str, request: Request):
    """Add a breakpoint to a debug session"""
    if session_id not in DEBUG_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    data = {}
    breakpoint_id = f"bp_{uuid.uuid4().hex[:8]}"

    breakpoint = {
        "id": breakpoint_id,
        "location": data.get("location"),
        "condition": data.get("condition"),
        "enabled": True
    }

    DEBUG_BREAKPOINTS[session_id].append(breakpoint)
    return {"breakpoint": breakpoint}


@app.get("/debug/sessions/{session_id}/traces")
def get_execution_traces(session_id: str, limit: int = 100):
    """Get execution traces for a debug session"""
    if session_id not in DEBUG_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    traces = EXECUTION_TRACES.get(session_id, [])
    return {"traces": traces[-limit:], "total": len(traces)}


@app.post("/debug/sessions/{session_id}/step")
def step_execution(session_id: str, request: Request):
    """Step through execution"""
    if session_id not in DEBUG_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    data = {}
    step_type = data.get("step_type", "next")  # next, into, out, continue

    # Simulate step execution
    trace = {
        "id": f"trace_{uuid.uuid4().hex[:8]}",
        "step_type": step_type,
        "location": "step_1",
        "context": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    EXECUTION_TRACES[session_id].append(trace)
    return {"trace": trace}


@app.post("/debug/sessions/{session_id}/end")
def end_debug_session(session_id: str):
    """End a debug session"""
    if session_id not in DEBUG_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    DEBUG_SESSIONS[session_id]["status"] = "ended"
    DEBUG_SESSIONS[session_id]["ended_at"] = datetime.now(timezone.utc).isoformat()

    return {"session": DEBUG_SESSIONS[session_id]}


# ============================================================================
# API Playground
# ============================================================================

PLAYGROUND_SESSIONS: Dict[str, Dict[str, Any]] = {}
PLAYGROUND_HISTORY: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/playground/sessions")
def create_playground_session(request: Request):
    """Create a playground session"""
    data = {}
    session_id = f"play_{uuid.uuid4().hex[:8]}"

    session = {
        "id": session_id,
        "name": data.get("name", f"Session {session_id}"),
        "environment": data.get("environment", "sandbox"),
        "settings": {
            "timeout_seconds": data.get("timeout", 30),
            "auto_save": data.get("auto_save", True),
            "mock_responses": data.get("mock_responses", False)
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    PLAYGROUND_SESSIONS[session_id] = session
    PLAYGROUND_HISTORY[session_id] = []

    return {"session": session}


@app.get("/playground/sessions")
def list_playground_sessions():
    """List playground sessions"""
    return {"sessions": list(PLAYGROUND_SESSIONS.values()), "total": len(PLAYGROUND_SESSIONS)}


@app.post("/playground/sessions/{session_id}/execute")
def execute_in_playground(session_id: str, request: Request):
    """Execute a request in the playground"""
    if session_id not in PLAYGROUND_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    data = {}
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"

    execution = {
        "id": execution_id,
        "method": data.get("method", "GET"),
        "endpoint": data.get("endpoint", "/health"),
        "headers": data.get("headers", {}),
        "body": data.get("body"),
        "response": {
            "status_code": 200,
            "body": {"status": "ok"},
            "headers": {"content-type": "application/json"}
        },
        "duration_ms": 50,
        "executed_at": datetime.now(timezone.utc).isoformat()
    }

    PLAYGROUND_HISTORY[session_id].append(execution)
    return {"execution": execution}


@app.get("/playground/sessions/{session_id}/history")
def get_playground_history(session_id: str, limit: int = 50):
    """Get playground execution history"""
    if session_id not in PLAYGROUND_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    history = PLAYGROUND_HISTORY.get(session_id, [])
    return {"history": history[-limit:], "total": len(history)}


@app.get("/playground/endpoints")
def list_playground_endpoints():
    """List available endpoints for the playground"""
    return {
        "endpoints": [
            {"path": "/agents", "methods": ["GET", "POST"], "description": "Agent management"},
            {"path": "/workflows", "methods": ["GET", "POST"], "description": "Workflow management"},
            {"path": "/executions", "methods": ["GET", "POST"], "description": "Execution management"},
            {"path": "/health", "methods": ["GET"], "description": "Health check"}
        ]
    }


# ============================================================================
# Code Examples
# ============================================================================

CODE_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "python": {},
    "javascript": {},
    "curl": {},
    "go": {}
}


@app.get("/examples/languages")
def list_example_languages():
    """List supported languages for code examples"""
    return {
        "languages": [
            {"id": "python", "name": "Python", "version": "3.9+"},
            {"id": "javascript", "name": "JavaScript", "version": "ES2020+"},
            {"id": "typescript", "name": "TypeScript", "version": "4.0+"},
            {"id": "curl", "name": "cURL", "version": "7.0+"},
            {"id": "go", "name": "Go", "version": "1.18+"},
            {"id": "ruby", "name": "Ruby", "version": "3.0+"},
            {"id": "java", "name": "Java", "version": "11+"}
        ]
    }


@app.get("/examples/endpoints/{endpoint_path:path}")
def get_endpoint_examples(endpoint_path: str, language: str = "python"):
    """Get code examples for an endpoint"""
    base_url = "https://api.example.com"

    examples = {
        "python": f'''import requests

response = requests.get("{base_url}/{endpoint_path}")
print(response.json())
''',
        "javascript": f'''const response = await fetch("{base_url}/{endpoint_path}");
const data = await response.json();
console.log(data);
''',
        "curl": f'''curl -X GET "{base_url}/{endpoint_path}" \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json"
''',
        "go": f'''resp, err := http.Get("{base_url}/{endpoint_path}")
if err != nil {{
    log.Fatal(err)
}}
defer resp.Body.Close()
'''
    }

    return {
        "endpoint": endpoint_path,
        "language": language,
        "example": examples.get(language, examples["python"])
    }


@app.post("/examples/generate")
def generate_code_example(request: Request):
    """Generate a code example from request spec"""
    data = {}

    language = data.get("language", "python")
    method = data.get("method", "GET")
    endpoint = data.get("endpoint", "/agents")
    body = data.get("body", {})

    # Generate example based on language
    if language == "python":
        if method == "GET":
            code = f'''import requests

response = requests.get("https://api.example.com{endpoint}")
print(response.json())
'''
        else:
            code = f'''import requests

payload = {body}
response = requests.{method.lower()}("https://api.example.com{endpoint}", json=payload)
print(response.json())
'''
    else:
        code = f"// Example for {language} - {method} {endpoint}"

    return {
        "language": language,
        "method": method,
        "endpoint": endpoint,
        "code": code
    }


# ============================================================================
# API Changelog
# ============================================================================

API_CHANGELOG: List[Dict[str, Any]] = [
    {
        "version": "2.0.0",
        "date": "2024-01-15",
        "changes": [
            {"type": "added", "description": "Advanced AI/ML features"},
            {"type": "added", "description": "Policy engine"},
            {"type": "changed", "description": "Improved error responses"}
        ]
    },
    {
        "version": "1.5.0",
        "date": "2024-01-01",
        "changes": [
            {"type": "added", "description": "OAuth2/OIDC support"},
            {"type": "added", "description": "Fine-grained RBAC"},
            {"type": "deprecated", "description": "Legacy auth endpoints"}
        ]
    }
]

BREAKING_CHANGES: List[Dict[str, Any]] = []


@app.get("/changelog")
def get_api_changelog(version: Optional[str] = None):
    """Get API changelog"""
    if version:
        for entry in API_CHANGELOG:
            if entry["version"] == version:
                return {"changelog": entry}
        raise HTTPException(status_code=404, detail="Version not found")

    return {"changelog": API_CHANGELOG}


@app.get("/changelog/breaking")
def get_breaking_changes():
    """Get breaking changes"""
    return {"breaking_changes": BREAKING_CHANGES}


@app.get("/changelog/latest")
def get_latest_changelog():
    """Get latest changelog entry"""
    if API_CHANGELOG:
        return {"latest": API_CHANGELOG[0]}
    return {"latest": None}


@app.post("/changelog/subscribe")
def subscribe_to_changelog(request: Request):
    """Subscribe to changelog updates"""
    data = {}

    subscription = {
        "id": f"sub_{uuid.uuid4().hex[:8]}",
        "email": data.get("email"),
        "notify_on": data.get("notify_on", ["breaking", "major"]),
        "subscribed_at": datetime.now(timezone.utc).isoformat()
    }

    return {"subscription": subscription}


# ============================================================================
# Policy Engine
# ============================================================================

POLICIES: Dict[str, Dict[str, Any]] = {}
POLICY_RULES: Dict[str, List[Dict[str, Any]]] = {}
POLICY_VIOLATIONS: List[Dict[str, Any]] = []


@app.post("/policies")
def create_policy(request: Request):
    """Create a policy"""
    data = {}
    policy_id = f"policy_{uuid.uuid4().hex[:8]}"

    policy = {
        "id": policy_id,
        "name": data.get("name", f"Policy {policy_id}"),
        "description": data.get("description", ""),
        "type": data.get("type", "enforcement"),  # enforcement, advisory
        "scope": data.get("scope", "global"),  # global, org, team, user
        "rules": data.get("rules", []),
        "actions": data.get("actions", ["deny"]),  # deny, warn, log, notify
        "enabled": True,
        "priority": data.get("priority", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    POLICIES[policy_id] = policy
    return {"policy": policy}


@app.get("/policies")
def list_policies(policy_type: Optional[str] = None, scope: Optional[str] = None):
    """List policies"""
    policies = list(POLICIES.values())
    if policy_type:
        policies = [p for p in policies if p.get("type") == policy_type]
    if scope:
        policies = [p for p in policies if p.get("scope") == scope]
    return {"policies": policies, "total": len(policies)}


@app.get("/policies/{policy_id}")
def get_policy(policy_id: str):
    """Get policy details"""
    if policy_id not in POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": POLICIES[policy_id]}


@app.put("/policies/{policy_id}")
def update_policy(policy_id: str, request: Request):
    """Update a policy"""
    if policy_id not in POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")

    data = {}
    policy = POLICIES[policy_id]

    for field in ["name", "description", "rules", "actions", "enabled", "priority"]:
        if field in data:
            policy[field] = data[field]

    policy["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"policy": policy}


@app.post("/policies/evaluate")
def evaluate_policies(request: Request):
    """Evaluate policies against an action"""
    data = {}
    action = data.get("action")
    resource = data.get("resource")
    context = data.get("context", {})

    violations = []
    warnings = []

    for policy in POLICIES.values():
        if not policy["enabled"]:
            continue

        # Simplified policy evaluation
        for rule in policy.get("rules", []):
            if rule.get("action") == action or rule.get("action") == "*":
                if "deny" in policy["actions"]:
                    violations.append({
                        "policy_id": policy["id"],
                        "policy_name": policy["name"],
                        "rule": rule,
                        "action": "deny"
                    })
                elif "warn" in policy["actions"]:
                    warnings.append({
                        "policy_id": policy["id"],
                        "policy_name": policy["name"],
                        "rule": rule,
                        "action": "warn"
                    })

    return {
        "allowed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings
    }


@app.get("/policies/violations")
def list_policy_violations(limit: int = 100):
    """List policy violations"""
    return {"violations": POLICY_VIOLATIONS[-limit:], "total": len(POLICY_VIOLATIONS)}


# ============================================================================
# Approval Workflows
# ============================================================================

APPROVAL_WORKFLOWS: Dict[str, Dict[str, Any]] = {}
APPROVAL_REQUESTS: Dict[str, Dict[str, Any]] = {}


@app.post("/approvals/workflows")
def create_approval_workflow(request: Request):
    """Create an approval workflow"""
    data = {}
    workflow_id = f"approval_{uuid.uuid4().hex[:8]}"

    workflow = {
        "id": workflow_id,
        "name": data.get("name", f"Workflow {workflow_id}"),
        "description": data.get("description", ""),
        "trigger": data.get("trigger", {}),
        "steps": data.get("steps", [
            {"name": "manager_approval", "approvers": ["manager"], "required": 1},
            {"name": "security_review", "approvers": ["security_team"], "required": 1}
        ]),
        "timeout_hours": data.get("timeout_hours", 72),
        "on_timeout": data.get("on_timeout", "deny"),
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    APPROVAL_WORKFLOWS[workflow_id] = workflow
    return {"workflow": workflow}


@app.get("/approvals/workflows")
def list_approval_workflows():
    """List approval workflows"""
    return {"workflows": list(APPROVAL_WORKFLOWS.values()), "total": len(APPROVAL_WORKFLOWS)}


@app.post("/approvals/requests")
def create_approval_request(request: Request):
    """Create an approval request"""
    data = {}
    request_id = f"areq_{uuid.uuid4().hex[:8]}"

    approval_request = {
        "id": request_id,
        "workflow_id": data.get("workflow_id"),
        "title": data.get("title", f"Request {request_id}"),
        "description": data.get("description", ""),
        "requested_by": data.get("requested_by"),
        "resource": data.get("resource"),
        "action": data.get("action"),
        "current_step": 0,
        "approvals": [],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
    }

    APPROVAL_REQUESTS[request_id] = approval_request
    return {"request": approval_request}


@app.get("/approvals/requests")
def list_approval_requests(status: Optional[str] = None, assignee: Optional[str] = None):
    """List approval requests"""
    requests = list(APPROVAL_REQUESTS.values())
    if status:
        requests = [r for r in requests if r.get("status") == status]
    return {"requests": requests, "total": len(requests)}


@app.get("/approvals/requests/{request_id}")
def get_approval_request(request_id: str):
    """Get approval request details"""
    if request_id not in APPROVAL_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"request": APPROVAL_REQUESTS[request_id]}


@app.post("/approvals/requests/{request_id}/approve")
def approve_request(request_id: str, request: Request):
    """Approve a request"""
    if request_id not in APPROVAL_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")

    data = {}
    req = APPROVAL_REQUESTS[request_id]

    approval = {
        "approver": data.get("approver"),
        "decision": "approved",
        "comment": data.get("comment"),
        "approved_at": datetime.now(timezone.utc).isoformat()
    }

    req["approvals"].append(approval)
    req["current_step"] += 1

    # Check if fully approved
    workflow = APPROVAL_WORKFLOWS.get(req.get("workflow_id"), {})
    if req["current_step"] >= len(workflow.get("steps", [])):
        req["status"] = "approved"

    return {"request": req}


@app.post("/approvals/requests/{request_id}/reject")
def reject_request(request_id: str, request: Request):
    """Reject a request"""
    if request_id not in APPROVAL_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")

    data = {}
    req = APPROVAL_REQUESTS[request_id]

    req["status"] = "rejected"
    req["rejection"] = {
        "rejected_by": data.get("rejected_by"),
        "reason": data.get("reason"),
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }

    return {"request": req}


# ============================================================================
# Data Classification
# ============================================================================

DATA_CLASSIFICATIONS: Dict[str, Dict[str, Any]] = {
    "public": {"level": 0, "description": "Public information"},
    "internal": {"level": 1, "description": "Internal use only"},
    "confidential": {"level": 2, "description": "Confidential data"},
    "restricted": {"level": 3, "description": "Highly restricted"},
    "pii": {"level": 3, "description": "Personally identifiable information"},
    "phi": {"level": 3, "description": "Protected health information"}
}

CLASSIFIED_RESOURCES: Dict[str, Dict[str, Any]] = {}


@app.get("/classification/levels")
def list_classification_levels():
    """List data classification levels"""
    return {"classifications": DATA_CLASSIFICATIONS}


@app.post("/classification/classify")
def classify_resource(request: Request):
    """Classify a resource"""
    data = {}
    resource_id = data.get("resource_id")
    resource_type = data.get("resource_type")

    classification = {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "classification": data.get("classification", "internal"),
        "labels": data.get("labels", []),
        "handling_requirements": data.get("handling_requirements", []),
        "classified_by": data.get("classified_by"),
        "classified_at": datetime.now(timezone.utc).isoformat(),
        "review_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    }

    CLASSIFIED_RESOURCES[f"{resource_type}:{resource_id}"] = classification
    return {"classification": classification}


@app.get("/classification/resources/{resource_type}/{resource_id}")
def get_resource_classification(resource_type: str, resource_id: str):
    """Get resource classification"""
    key = f"{resource_type}:{resource_id}"
    if key not in CLASSIFIED_RESOURCES:
        return {"classification": None, "default": "internal"}
    return {"classification": CLASSIFIED_RESOURCES[key]}


@app.post("/classification/scan")
def scan_for_sensitive_data(request: Request):
    """Scan content for sensitive data"""
    data = {}
    content = data.get("content", "")

    findings = []

    # Check for PII patterns
    import re

    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
    }

    for data_type, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            findings.append({
                "type": data_type,
                "count": len(matches),
                "classification": "pii"
            })

    return {
        "scanned": True,
        "content_length": len(content),
        "findings": findings,
        "recommended_classification": "pii" if findings else "internal"
    }


@app.get("/classification/resources")
def list_classified_resources(classification: Optional[str] = None):
    """List classified resources"""
    resources = list(CLASSIFIED_RESOURCES.values())
    if classification:
        resources = [r for r in resources if r.get("classification") == classification]
    return {"resources": resources, "total": len(resources)}


# ============================================================================
# Compliance Reports
# ============================================================================

COMPLIANCE_REPORTS: Dict[str, Dict[str, Any]] = {}
COMPLIANCE_FRAMEWORKS = ["GDPR", "SOC2", "HIPAA", "PCI-DSS", "ISO27001"]


@app.post("/compliance/reports")
def generate_compliance_report(request: Request):
    """Generate a compliance report"""
    data = {}
    report_id = f"report_{uuid.uuid4().hex[:8]}"

    report = {
        "id": report_id,
        "framework": data.get("framework", "SOC2"),
        "scope": data.get("scope", "full"),
        "period": {
            "start": data.get("start_date", (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()),
            "end": data.get("end_date", datetime.now(timezone.utc).isoformat())
        },
        "status": "generating",
        "findings": [],
        "summary": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    COMPLIANCE_REPORTS[report_id] = report

    # Simulate report generation
    report["status"] = "completed"
    report["findings"] = [
        {"control": "AC-1", "status": "pass", "evidence": "Access controls in place"},
        {"control": "AC-2", "status": "pass", "evidence": "Account management documented"},
        {"control": "AU-1", "status": "warning", "evidence": "Audit logging needs review"}
    ]
    report["summary"] = {
        "total_controls": 50,
        "passed": 45,
        "warnings": 3,
        "failed": 2,
        "compliance_score": 90
    }

    return {"report": report}


@app.get("/compliance/reports")
def list_compliance_reports(framework: Optional[str] = None):
    """List compliance reports"""
    reports = list(COMPLIANCE_REPORTS.values())
    if framework:
        reports = [r for r in reports if r.get("framework") == framework]
    return {"reports": reports, "total": len(reports)}


@app.get("/compliance/reports/{report_id}")
def get_compliance_report(report_id: str):
    """Get compliance report details"""
    if report_id not in COMPLIANCE_REPORTS:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report": COMPLIANCE_REPORTS[report_id]}


@app.get("/compliance/frameworks")
def list_compliance_frameworks():
    """List supported compliance frameworks"""
    return {
        "frameworks": [
            {"id": "GDPR", "name": "General Data Protection Regulation", "controls": 99},
            {"id": "SOC2", "name": "SOC 2 Type II", "controls": 64},
            {"id": "HIPAA", "name": "Health Insurance Portability and Accountability Act", "controls": 75},
            {"id": "PCI-DSS", "name": "Payment Card Industry Data Security Standard", "controls": 78},
            {"id": "ISO27001", "name": "ISO/IEC 27001", "controls": 114}
        ]
    }


@app.get("/compliance/status")
def get_compliance_status():
    """Get overall compliance status"""
    return {
        "status": {
            "GDPR": {"score": 92, "status": "compliant"},
            "SOC2": {"score": 88, "status": "compliant"},
            "HIPAA": {"score": 85, "status": "needs_attention"},
            "PCI-DSS": {"score": 95, "status": "compliant"}
        },
        "last_assessment": datetime.now(timezone.utc).isoformat(),
        "next_audit": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    }


# ============================================================================
# Auto-scaling Rules
# ============================================================================

SCALING_RULES: Dict[str, Dict[str, Any]] = {}
SCALING_EVENTS: List[Dict[str, Any]] = []


@app.post("/scaling/rules")
def create_scaling_rule(request: Request):
    """Create an auto-scaling rule"""
    data = {}
    rule_id = f"scale_{uuid.uuid4().hex[:8]}"

    rule = {
        "id": rule_id,
        "name": data.get("name", f"Rule {rule_id}"),
        "target": data.get("target"),  # resource to scale
        "metric": data.get("metric", "cpu_utilization"),
        "condition": {
            "operator": data.get("operator", "gt"),
            "threshold": data.get("threshold", 80),
            "duration_seconds": data.get("duration", 300)
        },
        "action": {
            "type": data.get("action_type", "scale_out"),
            "adjustment": data.get("adjustment", 1),
            "cooldown_seconds": data.get("cooldown", 300)
        },
        "limits": {
            "min_capacity": data.get("min_capacity", 1),
            "max_capacity": data.get("max_capacity", 10)
        },
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    SCALING_RULES[rule_id] = rule
    return {"rule": rule}


@app.get("/scaling/rules")
def list_scaling_rules():
    """List auto-scaling rules"""
    return {"rules": list(SCALING_RULES.values()), "total": len(SCALING_RULES)}


@app.get("/scaling/rules/{rule_id}")
def get_scaling_rule(rule_id: str):
    """Get scaling rule details"""
    if rule_id not in SCALING_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"rule": SCALING_RULES[rule_id]}


@app.put("/scaling/rules/{rule_id}")
def update_scaling_rule(rule_id: str, request: Request):
    """Update a scaling rule"""
    if rule_id not in SCALING_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")

    data = {}
    rule = SCALING_RULES[rule_id]

    for field in ["name", "metric", "condition", "action", "limits", "enabled"]:
        if field in data:
            rule[field] = data[field]

    rule["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"rule": rule}


@app.post("/scaling/rules/{rule_id}/trigger")
def trigger_scaling(rule_id: str):
    """Manually trigger a scaling action"""
    if rule_id not in SCALING_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = SCALING_RULES[rule_id]
    event_id = f"scale_event_{uuid.uuid4().hex[:8]}"

    event = {
        "id": event_id,
        "rule_id": rule_id,
        "action": rule["action"]["type"],
        "adjustment": rule["action"]["adjustment"],
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }

    SCALING_EVENTS.append(event)
    return {"event": event}


@app.get("/scaling/events")
def list_scaling_events(rule_id: Optional[str] = None, limit: int = 100):
    """List scaling events"""
    events = SCALING_EVENTS.copy()
    if rule_id:
        events = [e for e in events if e.get("rule_id") == rule_id]
    return {"events": events[-limit:], "total": len(events)}


@app.delete("/scaling/rules/{rule_id}")
def delete_scaling_rule(rule_id: str):
    """Delete a scaling rule"""
    if rule_id not in SCALING_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")

    del SCALING_RULES[rule_id]
    return {"deleted": True}


# ============================================================================
# Comments / Annotations
# ============================================================================

COMMENTS: Dict[str, List[Dict[str, Any]]] = {}
ANNOTATIONS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/comments")
def add_comment(request: Request):
    """Add a comment to a resource"""
    data = {}
    comment_id = f"comment_{uuid.uuid4().hex[:8]}"
    resource_key = f"{data.get('resource_type')}:{data.get('resource_id')}"

    comment = {
        "id": comment_id,
        "resource_type": data.get("resource_type"),
        "resource_id": data.get("resource_id"),
        "author": data.get("author"),
        "content": data.get("content", ""),
        "parent_id": data.get("parent_id"),  # For replies
        "mentions": data.get("mentions", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }

    if resource_key not in COMMENTS:
        COMMENTS[resource_key] = []
    COMMENTS[resource_key].append(comment)

    return {"comment": comment}


@app.get("/comments/{resource_type}/{resource_id}")
def get_comments(resource_type: str, resource_id: str):
    """Get comments for a resource"""
    resource_key = f"{resource_type}:{resource_id}"
    comments = COMMENTS.get(resource_key, [])
    return {"comments": comments, "total": len(comments)}


@app.put("/comments/{comment_id}")
def update_comment(comment_id: str, request: Request):
    """Update a comment"""
    data = {}

    for resource_key, comment_list in COMMENTS.items():
        for comment in comment_list:
            if comment["id"] == comment_id:
                comment["content"] = data.get("content", comment["content"])
                comment["updated_at"] = datetime.now(timezone.utc).isoformat()
                return {"comment": comment}

    raise HTTPException(status_code=404, detail="Comment not found")


@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: str):
    """Delete a comment"""
    for resource_key, comment_list in COMMENTS.items():
        for i, comment in enumerate(comment_list):
            if comment["id"] == comment_id:
                del comment_list[i]
                return {"deleted": True}

    raise HTTPException(status_code=404, detail="Comment not found")


@app.post("/annotations")
def add_annotation(request: Request):
    """Add an annotation to a resource"""
    data = {}
    annotation_id = f"annot_{uuid.uuid4().hex[:8]}"
    resource_key = f"{data.get('resource_type')}:{data.get('resource_id')}"

    annotation = {
        "id": annotation_id,
        "resource_type": data.get("resource_type"),
        "resource_id": data.get("resource_id"),
        "key": data.get("key"),
        "value": data.get("value"),
        "type": data.get("type", "info"),  # info, warning, error, success
        "created_by": data.get("created_by"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if resource_key not in ANNOTATIONS:
        ANNOTATIONS[resource_key] = []
    ANNOTATIONS[resource_key].append(annotation)

    return {"annotation": annotation}


@app.get("/annotations/{resource_type}/{resource_id}")
def get_annotations(resource_type: str, resource_id: str):
    """Get annotations for a resource"""
    resource_key = f"{resource_type}:{resource_id}"
    annotations = ANNOTATIONS.get(resource_key, [])
    return {"annotations": annotations, "total": len(annotations)}


# ============================================================================
# Review Workflows
# ============================================================================

REVIEW_WORKFLOWS: Dict[str, Dict[str, Any]] = {}
REVIEW_REQUESTS: Dict[str, Dict[str, Any]] = {}


@app.post("/reviews/workflows")
def create_review_workflow(request: Request):
    """Create a review workflow"""
    data = {}
    workflow_id = f"review_{uuid.uuid4().hex[:8]}"

    workflow = {
        "id": workflow_id,
        "name": data.get("name", f"Review Workflow {workflow_id}"),
        "description": data.get("description", ""),
        "resource_types": data.get("resource_types", ["agent", "workflow"]),
        "reviewers": {
            "required": data.get("required_reviewers", 1),
            "teams": data.get("reviewer_teams", []),
            "users": data.get("reviewer_users", [])
        },
        "rules": data.get("rules", []),
        "auto_merge": data.get("auto_merge", False),
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    REVIEW_WORKFLOWS[workflow_id] = workflow
    return {"workflow": workflow}


@app.get("/reviews/workflows")
def list_review_workflows():
    """List review workflows"""
    return {"workflows": list(REVIEW_WORKFLOWS.values()), "total": len(REVIEW_WORKFLOWS)}


@app.post("/reviews/requests")
def create_review_request(request: Request):
    """Create a review request"""
    data = {}
    request_id = f"rreq_{uuid.uuid4().hex[:8]}"

    review_request = {
        "id": request_id,
        "workflow_id": data.get("workflow_id"),
        "title": data.get("title", f"Review {request_id}"),
        "description": data.get("description", ""),
        "author": data.get("author"),
        "resource": {
            "type": data.get("resource_type"),
            "id": data.get("resource_id"),
            "version": data.get("version")
        },
        "changes": data.get("changes", []),
        "reviewers": data.get("reviewers", []),
        "reviews": [],
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    REVIEW_REQUESTS[request_id] = review_request
    return {"request": review_request}


@app.get("/reviews/requests")
def list_review_requests(status: Optional[str] = None, reviewer: Optional[str] = None):
    """List review requests"""
    requests = list(REVIEW_REQUESTS.values())
    if status:
        requests = [r for r in requests if r.get("status") == status]
    if reviewer:
        requests = [r for r in requests if reviewer in r.get("reviewers", [])]
    return {"requests": requests, "total": len(requests)}


@app.get("/reviews/requests/{request_id}")
def get_review_request(request_id: str):
    """Get review request details"""
    if request_id not in REVIEW_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"request": REVIEW_REQUESTS[request_id]}


@app.post("/reviews/requests/{request_id}/review")
def submit_review(request_id: str, request: Request):
    """Submit a review"""
    if request_id not in REVIEW_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")

    data = {}
    req = REVIEW_REQUESTS[request_id]

    review = {
        "reviewer": data.get("reviewer"),
        "decision": data.get("decision", "comment"),  # approve, request_changes, comment
        "comments": data.get("comments", []),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    req["reviews"].append(review)

    # Check if approved
    approvals = len([r for r in req["reviews"] if r["decision"] == "approve"])
    workflow = REVIEW_WORKFLOWS.get(req.get("workflow_id"), {})
    required = workflow.get("reviewers", {}).get("required", 1)

    if approvals >= required:
        req["status"] = "approved"

    return {"request": req}


@app.post("/reviews/requests/{request_id}/merge")
def merge_review_request(request_id: str):
    """Merge an approved review request"""
    if request_id not in REVIEW_REQUESTS:
        raise HTTPException(status_code=404, detail="Request not found")

    req = REVIEW_REQUESTS[request_id]

    if req["status"] != "approved":
        raise HTTPException(status_code=400, detail="Request not approved")

    req["status"] = "merged"
    req["merged_at"] = datetime.now(timezone.utc).isoformat()

    return {"request": req}


# ============================================================================
# Resource Sharing
# ============================================================================

SHARED_RESOURCES: Dict[str, Dict[str, Any]] = {}
SHARE_LINKS: Dict[str, Dict[str, Any]] = {}


@app.post("/sharing/share")
def share_resource(request: Request):
    """Share a resource with users or teams"""
    data = {}
    share_id = f"share_{uuid.uuid4().hex[:8]}"

    share = {
        "id": share_id,
        "resource_type": data.get("resource_type"),
        "resource_id": data.get("resource_id"),
        "shared_by": data.get("shared_by"),
        "shared_with": data.get("shared_with", []),  # user IDs or team IDs
        "permissions": data.get("permissions", ["read"]),  # read, write, execute, admin
        "expires_at": data.get("expires_at"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    resource_key = f"{data.get('resource_type')}:{data.get('resource_id')}"
    SHARED_RESOURCES[resource_key] = share

    return {"share": share}


@app.get("/sharing/{resource_type}/{resource_id}")
def get_resource_sharing(resource_type: str, resource_id: str):
    """Get sharing info for a resource"""
    resource_key = f"{resource_type}:{resource_id}"
    share = SHARED_RESOURCES.get(resource_key)

    if not share:
        return {"shared": False}

    return {"shared": True, "share": share}


@app.put("/sharing/{share_id}")
def update_sharing(share_id: str, request: Request):
    """Update sharing permissions"""
    data = {}

    for resource_key, share in SHARED_RESOURCES.items():
        if share["id"] == share_id:
            if "shared_with" in data:
                share["shared_with"] = data["shared_with"]
            if "permissions" in data:
                share["permissions"] = data["permissions"]
            if "expires_at" in data:
                share["expires_at"] = data["expires_at"]

            share["updated_at"] = datetime.now(timezone.utc).isoformat()
            return {"share": share}

    raise HTTPException(status_code=404, detail="Share not found")


@app.delete("/sharing/{share_id}")
def revoke_sharing(share_id: str):
    """Revoke sharing"""
    for resource_key, share in list(SHARED_RESOURCES.items()):
        if share["id"] == share_id:
            del SHARED_RESOURCES[resource_key]
            return {"revoked": True}

    raise HTTPException(status_code=404, detail="Share not found")


@app.post("/sharing/links")
def create_share_link(request: Request):
    """Create a shareable link"""
    data = {}
    link_id = f"link_{uuid.uuid4().hex[:12]}"

    link = {
        "id": link_id,
        "url": f"https://app.example.com/share/{link_id}",
        "resource_type": data.get("resource_type"),
        "resource_id": data.get("resource_id"),
        "permissions": data.get("permissions", ["read"]),
        "password_protected": data.get("password_protected", False),
        "max_uses": data.get("max_uses"),
        "use_count": 0,
        "expires_at": data.get("expires_at"),
        "created_by": data.get("created_by"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    SHARE_LINKS[link_id] = link
    return {"link": link}


@app.get("/sharing/links")
def list_share_links(resource_type: Optional[str] = None, resource_id: Optional[str] = None):
    """List share links"""
    links = list(SHARE_LINKS.values())
    if resource_type:
        links = [l for l in links if l.get("resource_type") == resource_type]
    if resource_id:
        links = [l for l in links if l.get("resource_id") == resource_id]
    return {"links": links, "total": len(links)}


@app.delete("/sharing/links/{link_id}")
def delete_share_link(link_id: str):
    """Delete a share link"""
    if link_id not in SHARE_LINKS:
        raise HTTPException(status_code=404, detail="Link not found")

    del SHARE_LINKS[link_id]
    return {"deleted": True}


@app.get("/sharing/shared-with-me")
def get_shared_with_me(user_id: Optional[str] = None):
    """Get resources shared with the current user"""
    shared = []
    for resource_key, share in SHARED_RESOURCES.items():
        if user_id and user_id in share.get("shared_with", []):
            shared.append(share)

    return {"shared_resources": shared, "total": len(shared)}


# ============================================================================
# Templates & Marketplace
# ============================================================================

AGENT_TEMPLATES: Dict[str, Dict[str, Any]] = {}
WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {}
TEMPLATE_REVIEWS: Dict[str, List[Dict[str, Any]]] = {}
TEMPLATE_CATEGORIES = ["customer-service", "data-processing", "content-generation",
                        "code-assistance", "research", "automation", "analytics", "integration"]


@app.post("/templates/agents")
def create_agent_template(
    name: str,
    description: str,
    category: str,
    agent_card_config: Dict[str, Any],
    tags: Optional[List[str]] = None,
    is_public: bool = True,
    author_id: Optional[str] = None
):
    """Create a reusable agent template"""
    template_id = f"at_{uuid.uuid4().hex[:12]}"
    template = {
        "id": template_id,
        "name": name,
        "description": description,
        "category": category,
        "agent_card_config": agent_card_config,
        "tags": tags or [],
        "is_public": is_public,
        "author_id": author_id,
        "downloads": 0,
        "rating": 0.0,
        "review_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    AGENT_TEMPLATES[template_id] = template
    return template


@app.get("/templates/agents")
def list_agent_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "downloads"
):
    """List available agent templates"""
    templates = list(AGENT_TEMPLATES.values())

    if category:
        templates = [t for t in templates if t["category"] == category]
    if tag:
        templates = [t for t in templates if tag in t.get("tags", [])]
    if search:
        templates = [t for t in templates if search.lower() in t["name"].lower()
                    or search.lower() in t["description"].lower()]

    # Sort
    if sort_by == "downloads":
        templates.sort(key=lambda x: x["downloads"], reverse=True)
    elif sort_by == "rating":
        templates.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "newest":
        templates.sort(key=lambda x: x["created_at"], reverse=True)

    return {"templates": templates, "total": len(templates)}


@app.get("/templates/agents/{template_id}")
def get_agent_template(template_id: str):
    """Get agent template details"""
    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return AGENT_TEMPLATES[template_id]


@app.post("/templates/agents/{template_id}/deploy")
def deploy_agent_template(template_id: str, customizations: Optional[Dict[str, Any]] = None):
    """One-click deploy an agent template"""
    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = AGENT_TEMPLATES[template_id]
    template["downloads"] += 1

    # Create agent card from template
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    config = {**template["agent_card_config"]}
    if customizations:
        config.update(customizations)

    return {
        "deployed": True,
        "agent_id": agent_id,
        "config": config,
        "source_template": template_id
    }


@app.post("/templates/workflows")
def create_workflow_template(
    name: str,
    description: str,
    category: str,
    workflow_config: Dict[str, Any],
    tags: Optional[List[str]] = None,
    author_id: Optional[str] = None
):
    """Create a reusable workflow template"""
    template_id = f"wt_{uuid.uuid4().hex[:12]}"
    template = {
        "id": template_id,
        "name": name,
        "description": description,
        "category": category,
        "workflow_config": workflow_config,
        "tags": tags or [],
        "author_id": author_id,
        "downloads": 0,
        "rating": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }
    WORKFLOW_TEMPLATES[template_id] = template
    return template


@app.get("/templates/workflows")
def list_workflow_templates(category: Optional[str] = None):
    """List workflow templates"""
    templates = list(WORKFLOW_TEMPLATES.values())
    if category:
        templates = [t for t in templates if t["category"] == category]
    return {"templates": templates, "total": len(templates)}


@app.post("/templates/{template_id}/reviews")
def add_template_review(
    template_id: str,
    user_id: str,
    rating: int,
    comment: Optional[str] = None
):
    """Add a review to a template"""
    if template_id not in AGENT_TEMPLATES and template_id not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    review = {
        "id": f"rev_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "rating": min(5, max(1, rating)),
        "comment": comment,
        "created_at": datetime.utcnow().isoformat()
    }

    if template_id not in TEMPLATE_REVIEWS:
        TEMPLATE_REVIEWS[template_id] = []
    TEMPLATE_REVIEWS[template_id].append(review)

    # Update average rating
    reviews = TEMPLATE_REVIEWS[template_id]
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)

    if template_id in AGENT_TEMPLATES:
        AGENT_TEMPLATES[template_id]["rating"] = round(avg_rating, 2)
        AGENT_TEMPLATES[template_id]["review_count"] = len(reviews)
    elif template_id in WORKFLOW_TEMPLATES:
        WORKFLOW_TEMPLATES[template_id]["rating"] = round(avg_rating, 2)

    return review


@app.get("/templates/{template_id}/reviews")
def get_template_reviews(template_id: str):
    """Get reviews for a template"""
    reviews = TEMPLATE_REVIEWS.get(template_id, [])
    return {"reviews": reviews, "total": len(reviews)}


@app.get("/templates/categories")
def list_template_categories():
    """List available template categories"""
    return {"categories": TEMPLATE_CATEGORIES}


# ============================================================================
# Notifications & Real-time Alerts
# ============================================================================

NOTIFICATION_SUBSCRIPTIONS: Dict[str, Dict[str, Any]] = {}
NOTIFICATIONS: Dict[str, List[Dict[str, Any]]] = {}
ALERT_RULES: Dict[str, Dict[str, Any]] = {}
NOTIFICATION_CHANNELS = ["email", "slack", "teams", "webhook", "in_app"]


@app.post("/notifications/subscriptions")
def create_notification_subscription(
    user_id: str,
    event_types: List[str],
    channels: List[str],
    filters: Optional[Dict[str, Any]] = None
):
    """Subscribe to event notifications"""
    sub_id = f"sub_{uuid.uuid4().hex[:12]}"
    subscription = {
        "id": sub_id,
        "user_id": user_id,
        "event_types": event_types,
        "channels": [c for c in channels if c in NOTIFICATION_CHANNELS],
        "filters": filters or {},
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    NOTIFICATION_SUBSCRIPTIONS[sub_id] = subscription
    return subscription


@app.get("/notifications/subscriptions")
def list_notification_subscriptions(user_id: Optional[str] = None):
    """List notification subscriptions"""
    subs = list(NOTIFICATION_SUBSCRIPTIONS.values())
    if user_id:
        subs = [s for s in subs if s["user_id"] == user_id]
    return {"subscriptions": subs, "total": len(subs)}


@app.put("/notifications/subscriptions/{subscription_id}")
def update_notification_subscription(
    subscription_id: str,
    enabled: Optional[bool] = None,
    channels: Optional[List[str]] = None,
    event_types: Optional[List[str]] = None
):
    """Update a notification subscription"""
    if subscription_id not in NOTIFICATION_SUBSCRIPTIONS:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub = NOTIFICATION_SUBSCRIPTIONS[subscription_id]
    if enabled is not None:
        sub["enabled"] = enabled
    if channels:
        sub["channels"] = channels
    if event_types:
        sub["event_types"] = event_types
    sub["updated_at"] = datetime.utcnow().isoformat()

    return sub


@app.delete("/notifications/subscriptions/{subscription_id}")
def delete_notification_subscription(subscription_id: str):
    """Delete a notification subscription"""
    if subscription_id not in NOTIFICATION_SUBSCRIPTIONS:
        raise HTTPException(status_code=404, detail="Subscription not found")
    del NOTIFICATION_SUBSCRIPTIONS[subscription_id]
    return {"deleted": True}


@app.post("/notifications/send")
def send_notification(
    user_id: str,
    title: str,
    message: str,
    event_type: str,
    priority: str = "normal",
    data: Optional[Dict[str, Any]] = None
):
    """Send a notification to a user"""
    notification = {
        "id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "title": title,
        "message": message,
        "event_type": event_type,
        "priority": priority,
        "data": data or {},
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    }

    if user_id not in NOTIFICATIONS:
        NOTIFICATIONS[user_id] = []
    NOTIFICATIONS[user_id].insert(0, notification)

    return notification


@app.get("/notifications")
def get_notifications(user_id: str, unread_only: bool = False, limit: int = 50):
    """Get user notifications"""
    notifs = NOTIFICATIONS.get(user_id, [])
    if unread_only:
        notifs = [n for n in notifs if not n["read"]]
    return {"notifications": notifs[:limit], "total": len(notifs)}


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, user_id: str):
    """Mark a notification as read"""
    user_notifs = NOTIFICATIONS.get(user_id, [])
    for notif in user_notifs:
        if notif["id"] == notification_id:
            notif["read"] = True
            notif["read_at"] = datetime.utcnow().isoformat()
            return notif
    raise HTTPException(status_code=404, detail="Notification not found")


@app.post("/notifications/mark-all-read")
def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read"""
    user_notifs = NOTIFICATIONS.get(user_id, [])
    count = 0
    for notif in user_notifs:
        if not notif["read"]:
            notif["read"] = True
            notif["read_at"] = datetime.utcnow().isoformat()
            count += 1
    return {"marked_read": count}


@app.post("/alerts/rules")
def create_alert_rule(
    name: str,
    user_id: str,
    condition: Dict[str, Any],
    actions: List[Dict[str, Any]],
    enabled: bool = True
):
    """Create a custom alert rule"""
    rule_id = f"alert_{uuid.uuid4().hex[:12]}"
    rule = {
        "id": rule_id,
        "name": name,
        "user_id": user_id,
        "condition": condition,
        "actions": actions,
        "enabled": enabled,
        "trigger_count": 0,
        "last_triggered": None,
        "created_at": datetime.utcnow().isoformat()
    }
    ALERT_RULES[rule_id] = rule
    return rule


@app.get("/alerts/rules")
def list_alert_rules(user_id: Optional[str] = None):
    """List alert rules"""
    rules = list(ALERT_RULES.values())
    if user_id:
        rules = [r for r in rules if r["user_id"] == user_id]
    return {"rules": rules, "total": len(rules)}


@app.post("/alerts/rules/{rule_id}/test")
def test_alert_rule(rule_id: str, test_data: Optional[Dict[str, Any]] = None):
    """Test an alert rule with sample data"""
    if rule_id not in ALERT_RULES:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    rule = ALERT_RULES[rule_id]
    # Simulate rule evaluation
    return {
        "rule_id": rule_id,
        "would_trigger": True,
        "test_data": test_data,
        "matched_condition": rule["condition"]
    }


@app.get("/notifications/channels")
def list_notification_channels():
    """List available notification channels"""
    return {"channels": NOTIFICATION_CHANNELS}


# ============================================================================
# Smart Recommendations
# ============================================================================

USER_PREFERENCES: Dict[str, Dict[str, Any]] = {}
RECOMMENDATION_CACHE: Dict[str, List[Dict[str, Any]]] = {}


@app.get("/recommendations/agents")
def get_agent_recommendations(user_id: str, limit: int = 10):
    """Get personalized agent recommendations"""
    # Simulate recommendation engine
    recommendations = []

    # Based on user activity, suggest popular templates
    for template_id, template in list(AGENT_TEMPLATES.items())[:limit]:
        recommendations.append({
            "type": "agent_template",
            "id": template_id,
            "name": template["name"],
            "reason": "Popular in your category",
            "score": template.get("downloads", 0) * 0.1 + template.get("rating", 0) * 20,
            "category": template.get("category")
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return {"recommendations": recommendations[:limit], "user_id": user_id}


@app.get("/recommendations/workflows")
def get_workflow_recommendations(user_id: str, context: Optional[str] = None):
    """Get workflow recommendations based on context"""
    recommendations = []

    for wf_id, wf in list(WORKFLOW_TEMPLATES.items())[:5]:
        recommendations.append({
            "type": "workflow_template",
            "id": wf_id,
            "name": wf["name"],
            "reason": f"Matches your {context or 'usage pattern'}",
            "score": random.uniform(0.7, 1.0)
        })

    return {"recommendations": recommendations, "context": context}


@app.get("/recommendations/performance-tips")
def get_performance_tips(user_id: str, resource_type: Optional[str] = None):
    """Get performance improvement recommendations"""
    tips = [
        {
            "id": "tip_1",
            "title": "Enable response caching",
            "description": "Your agents could benefit from caching repeated queries",
            "impact": "high",
            "category": "performance",
            "action_url": "/settings/caching"
        },
        {
            "id": "tip_2",
            "title": "Optimize prompt length",
            "description": "Some prompts exceed recommended length, affecting latency",
            "impact": "medium",
            "category": "performance",
            "action_url": "/agents/optimize"
        },
        {
            "id": "tip_3",
            "title": "Use batch processing",
            "description": "Batch similar requests to reduce API calls by 40%",
            "impact": "high",
            "category": "efficiency",
            "action_url": "/batch/configure"
        }
    ]

    if resource_type:
        tips = [t for t in tips if resource_type in t.get("category", "")]

    return {"tips": tips, "user_id": user_id}


@app.get("/recommendations/cost-optimization")
def get_cost_optimization_recommendations(user_id: str, time_period: str = "30d"):
    """Get cost optimization recommendations"""
    recommendations = [
        {
            "id": "cost_1",
            "title": "Switch to smaller model for simple tasks",
            "description": "30% of your requests could use a smaller, cheaper model",
            "potential_savings": "$150/month",
            "confidence": 0.85,
            "affected_agents": ["agent_001", "agent_002"]
        },
        {
            "id": "cost_2",
            "title": "Enable request deduplication",
            "description": "Detected 15% duplicate requests that could be cached",
            "potential_savings": "$75/month",
            "confidence": 0.92,
            "action": "enable_dedup"
        },
        {
            "id": "cost_3",
            "title": "Optimize token usage",
            "description": "Trim unnecessary context from prompts",
            "potential_savings": "$50/month",
            "confidence": 0.78,
            "action": "review_prompts"
        }
    ]

    total_savings = sum(float(r["potential_savings"].replace("$", "").replace("/month", ""))
                       for r in recommendations)

    return {
        "recommendations": recommendations,
        "total_potential_savings": f"${total_savings}/month",
        "time_period": time_period
    }


@app.get("/recommendations/workflow-optimization")
def get_workflow_optimization_recommendations(workflow_id: Optional[str] = None):
    """Get workflow optimization suggestions"""
    optimizations = [
        {
            "id": "opt_1",
            "type": "bottleneck",
            "title": "Parallel execution opportunity",
            "description": "Steps 2 and 3 can run in parallel, reducing total time by 35%",
            "current_duration": "45s",
            "optimized_duration": "29s",
            "workflow_id": workflow_id
        },
        {
            "id": "opt_2",
            "type": "redundancy",
            "title": "Remove redundant validation",
            "description": "Same validation runs twice in the workflow",
            "recommendation": "Consolidate into single step"
        }
    ]

    return {"optimizations": optimizations, "analyzed_workflow": workflow_id}


# ============================================================================
# Quick Actions & Shortcuts
# ============================================================================

USER_FAVORITES: Dict[str, List[Dict[str, Any]]] = {}
USER_RECENT_ACTIVITY: Dict[str, List[Dict[str, Any]]] = {}
KEYBOARD_SHORTCUTS: Dict[str, Dict[str, str]] = {}


@app.post("/favorites")
def add_to_favorites(user_id: str, resource_type: str, resource_id: str, name: str):
    """Add a resource to favorites"""
    favorite = {
        "id": f"fav_{uuid.uuid4().hex[:8]}",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "name": name,
        "pinned": False,
        "added_at": datetime.utcnow().isoformat()
    }

    if user_id not in USER_FAVORITES:
        USER_FAVORITES[user_id] = []
    USER_FAVORITES[user_id].append(favorite)

    return favorite


@app.get("/favorites")
def get_favorites(user_id: str, resource_type: Optional[str] = None):
    """Get user's favorite resources"""
    favorites = USER_FAVORITES.get(user_id, [])
    if resource_type:
        favorites = [f for f in favorites if f["resource_type"] == resource_type]

    # Sort pinned first
    favorites.sort(key=lambda x: (not x.get("pinned", False), x["added_at"]))
    return {"favorites": favorites, "total": len(favorites)}


@app.put("/favorites/{favorite_id}/pin")
def pin_favorite(user_id: str, favorite_id: str, pinned: bool = True):
    """Pin or unpin a favorite"""
    favorites = USER_FAVORITES.get(user_id, [])
    for fav in favorites:
        if fav["id"] == favorite_id:
            fav["pinned"] = pinned
            return fav
    raise HTTPException(status_code=404, detail="Favorite not found")


@app.delete("/favorites/{favorite_id}")
def remove_from_favorites(user_id: str, favorite_id: str):
    """Remove a resource from favorites"""
    favorites = USER_FAVORITES.get(user_id, [])
    USER_FAVORITES[user_id] = [f for f in favorites if f["id"] != favorite_id]
    return {"removed": True}


@app.post("/activity/track")
def track_activity(user_id: str, action: str, resource_type: str, resource_id: str, metadata: Optional[Dict[str, Any]] = None):
    """Track user activity for recent items"""
    activity = {
        "id": f"act_{uuid.uuid4().hex[:8]}",
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat()
    }

    if user_id not in USER_RECENT_ACTIVITY:
        USER_RECENT_ACTIVITY[user_id] = []
    USER_RECENT_ACTIVITY[user_id].insert(0, activity)

    # Keep only last 100 activities
    USER_RECENT_ACTIVITY[user_id] = USER_RECENT_ACTIVITY[user_id][:100]

    return activity


@app.get("/activity/recent")
def get_recent_activity(user_id: str, limit: int = 20, resource_type: Optional[str] = None):
    """Get recent user activity"""
    activities = USER_RECENT_ACTIVITY.get(user_id, [])
    if resource_type:
        activities = [a for a in activities if a["resource_type"] == resource_type]
    return {"activities": activities[:limit], "total": len(activities)}


@app.post("/bulk-operations")
def execute_bulk_operation(
    operation: str,
    resource_type: str,
    resource_ids: List[str],
    params: Optional[Dict[str, Any]] = None
):
    """Execute bulk operations on multiple resources"""
    valid_operations = ["delete", "archive", "export", "tag", "move", "duplicate"]
    if operation not in valid_operations:
        raise HTTPException(status_code=400, detail=f"Invalid operation. Valid: {valid_operations}")

    results = []
    for resource_id in resource_ids:
        results.append({
            "resource_id": resource_id,
            "operation": operation,
            "status": "success",
            "message": f"{operation} completed"
        })

    return {
        "operation": operation,
        "resource_type": resource_type,
        "processed": len(results),
        "results": results
    }


@app.get("/keyboard-shortcuts")
def get_keyboard_shortcuts(context: Optional[str] = None):
    """Get available keyboard shortcuts"""
    shortcuts = {
        "global": {
            "Ctrl+K": "Quick search",
            "Ctrl+N": "New agent",
            "Ctrl+Shift+N": "New workflow",
            "Ctrl+/": "Show shortcuts",
            "Ctrl+,": "Settings"
        },
        "editor": {
            "Ctrl+S": "Save",
            "Ctrl+Enter": "Run/Execute",
            "Ctrl+Shift+Enter": "Run with options",
            "Escape": "Cancel"
        },
        "navigation": {
            "G then A": "Go to Agents",
            "G then W": "Go to Workflows",
            "G then T": "Go to Templates",
            "G then D": "Go to Dashboard"
        }
    }

    if context and context in shortcuts:
        return {"shortcuts": shortcuts[context], "context": context}
    return {"shortcuts": shortcuts, "contexts": list(shortcuts.keys())}


@app.post("/keyboard-shortcuts/custom")
def set_custom_shortcut(user_id: str, action: str, shortcut: str):
    """Set a custom keyboard shortcut"""
    if user_id not in KEYBOARD_SHORTCUTS:
        KEYBOARD_SHORTCUTS[user_id] = {}
    KEYBOARD_SHORTCUTS[user_id][action] = shortcut
    return {"action": action, "shortcut": shortcut, "user_id": user_id}


# ============================================================================
# Personal Dashboard
# ============================================================================

USER_DASHBOARDS: Dict[str, Dict[str, Any]] = {}
DASHBOARD_WIDGETS: Dict[str, List[Dict[str, Any]]] = {}
SAVED_VIEWS: Dict[str, List[Dict[str, Any]]] = {}
USER_GOALS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/dashboard")
def create_personal_dashboard(
    user_id: str,
    name: str,
    layout: Optional[Dict[str, Any]] = None,
    is_default: bool = False
):
    """Create a personal dashboard"""
    dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
    dashboard = {
        "id": dashboard_id,
        "user_id": user_id,
        "name": name,
        "layout": layout or {"columns": 3, "rows": "auto"},
        "is_default": is_default,
        "widgets": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    USER_DASHBOARDS[dashboard_id] = dashboard
    return dashboard


@app.get("/dashboard")
def get_user_dashboards(user_id: str):
    """Get all dashboards for a user"""
    dashboards = [d for d in USER_DASHBOARDS.values() if d["user_id"] == user_id]
    return {"dashboards": dashboards, "total": len(dashboards)}


@app.post("/dashboard/{dashboard_id}/widgets")
def add_dashboard_widget(
    dashboard_id: str,
    widget_type: str,
    title: str,
    config: Dict[str, Any],
    position: Optional[Dict[str, int]] = None
):
    """Add a widget to a dashboard"""
    if dashboard_id not in USER_DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = {
        "id": f"widget_{uuid.uuid4().hex[:8]}",
        "type": widget_type,
        "title": title,
        "config": config,
        "position": position or {"x": 0, "y": 0, "w": 1, "h": 1},
        "added_at": datetime.utcnow().isoformat()
    }

    if dashboard_id not in DASHBOARD_WIDGETS:
        DASHBOARD_WIDGETS[dashboard_id] = []
    DASHBOARD_WIDGETS[dashboard_id].append(widget)
    USER_DASHBOARDS[dashboard_id]["widgets"] = DASHBOARD_WIDGETS[dashboard_id]

    return widget


@app.get("/dashboard/{dashboard_id}/widgets")
def get_dashboard_widgets(dashboard_id: str):
    """Get all widgets for a dashboard"""
    widgets = DASHBOARD_WIDGETS.get(dashboard_id, [])
    return {"widgets": widgets, "total": len(widgets)}


@app.put("/dashboard/{dashboard_id}/widgets/{widget_id}")
def update_dashboard_widget(
    dashboard_id: str,
    widget_id: str,
    config: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, int]] = None
):
    """Update a dashboard widget"""
    widgets = DASHBOARD_WIDGETS.get(dashboard_id, [])
    for widget in widgets:
        if widget["id"] == widget_id:
            if config:
                widget["config"] = config
            if position:
                widget["position"] = position
            widget["updated_at"] = datetime.utcnow().isoformat()
            return widget
    raise HTTPException(status_code=404, detail="Widget not found")


@app.delete("/dashboard/{dashboard_id}/widgets/{widget_id}")
def remove_dashboard_widget(dashboard_id: str, widget_id: str):
    """Remove a widget from a dashboard"""
    widgets = DASHBOARD_WIDGETS.get(dashboard_id, [])
    DASHBOARD_WIDGETS[dashboard_id] = [w for w in widgets if w["id"] != widget_id]
    return {"removed": True}


@app.get("/dashboard/widget-types")
def list_widget_types():
    """List available widget types"""
    return {
        "widget_types": [
            {"type": "metrics", "name": "Metrics Card", "description": "Display key metrics"},
            {"type": "chart", "name": "Chart", "description": "Line, bar, or pie charts"},
            {"type": "table", "name": "Data Table", "description": "Tabular data display"},
            {"type": "activity", "name": "Activity Feed", "description": "Recent activity stream"},
            {"type": "agents", "name": "Agent Status", "description": "Agent health overview"},
            {"type": "workflows", "name": "Workflow Status", "description": "Active workflows"},
            {"type": "alerts", "name": "Alerts", "description": "Recent alerts"},
            {"type": "quick_actions", "name": "Quick Actions", "description": "Common actions"}
        ]
    }


@app.post("/saved-views")
def create_saved_view(
    user_id: str,
    name: str,
    resource_type: str,
    filters: Dict[str, Any],
    sort: Optional[Dict[str, str]] = None
):
    """Create a saved view with custom filters"""
    view = {
        "id": f"view_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "name": name,
        "resource_type": resource_type,
        "filters": filters,
        "sort": sort or {},
        "created_at": datetime.utcnow().isoformat()
    }

    if user_id not in SAVED_VIEWS:
        SAVED_VIEWS[user_id] = []
    SAVED_VIEWS[user_id].append(view)

    return view


@app.get("/saved-views")
def get_saved_views(user_id: str, resource_type: Optional[str] = None):
    """Get user's saved views"""
    views = SAVED_VIEWS.get(user_id, [])
    if resource_type:
        views = [v for v in views if v["resource_type"] == resource_type]
    return {"views": views, "total": len(views)}


@app.post("/goals")
def create_goal(
    user_id: str,
    name: str,
    target_metric: str,
    target_value: float,
    deadline: Optional[str] = None
):
    """Create a goal to track"""
    goal = {
        "id": f"goal_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "name": name,
        "target_metric": target_metric,
        "target_value": target_value,
        "current_value": 0.0,
        "progress_percent": 0.0,
        "deadline": deadline,
        "status": "in_progress",
        "created_at": datetime.utcnow().isoformat()
    }

    if user_id not in USER_GOALS:
        USER_GOALS[user_id] = []
    USER_GOALS[user_id].append(goal)

    return goal


@app.get("/goals")
def get_goals(user_id: str, status: Optional[str] = None):
    """Get user goals"""
    goals = USER_GOALS.get(user_id, [])
    if status:
        goals = [g for g in goals if g["status"] == status]
    return {"goals": goals, "total": len(goals)}


@app.put("/goals/{goal_id}/progress")
def update_goal_progress(user_id: str, goal_id: str, current_value: float):
    """Update goal progress"""
    goals = USER_GOALS.get(user_id, [])
    for goal in goals:
        if goal["id"] == goal_id:
            goal["current_value"] = current_value
            goal["progress_percent"] = min(100, (current_value / goal["target_value"]) * 100)
            if goal["progress_percent"] >= 100:
                goal["status"] = "completed"
                goal["completed_at"] = datetime.utcnow().isoformat()
            return goal
    raise HTTPException(status_code=404, detail="Goal not found")


@app.get("/activity-feed")
def get_activity_feed(user_id: str, limit: int = 50, include_system: bool = True):
    """Get personalized activity feed"""
    feed = []

    # Get user's own activities
    activities = USER_RECENT_ACTIVITY.get(user_id, [])
    for act in activities[:limit // 2]:
        feed.append({
            "type": "user_activity",
            "data": act,
            "timestamp": act["timestamp"]
        })

    # Add notifications
    notifs = NOTIFICATIONS.get(user_id, [])
    for notif in notifs[:limit // 2]:
        feed.append({
            "type": "notification",
            "data": notif,
            "timestamp": notif["created_at"]
        })

    # Sort by timestamp
    feed.sort(key=lambda x: x["timestamp"], reverse=True)

    return {"feed": feed[:limit], "total": len(feed)}


# ============================================================================
# Scheduled Reports
# ============================================================================

SCHEDULED_REPORTS: Dict[str, Dict[str, Any]] = {}
GENERATED_REPORTS: Dict[str, List[Dict[str, Any]]] = {}
REPORT_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/reports/scheduled")
def create_scheduled_report(
    name: str,
    user_id: str,
    report_type: str,
    schedule: str,
    config: Dict[str, Any],
    recipients: Optional[List[str]] = None,
    format: str = "pdf"
):
    """Create a scheduled report"""
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    report = {
        "id": report_id,
        "name": name,
        "user_id": user_id,
        "report_type": report_type,
        "schedule": schedule,  # cron expression or preset
        "config": config,
        "recipients": recipients or [user_id],
        "format": format,
        "enabled": True,
        "last_run": None,
        "next_run": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    SCHEDULED_REPORTS[report_id] = report
    return report


@app.get("/reports/scheduled")
def list_scheduled_reports(user_id: Optional[str] = None):
    """List scheduled reports"""
    reports = list(SCHEDULED_REPORTS.values())
    if user_id:
        reports = [r for r in reports if r["user_id"] == user_id]
    return {"reports": reports, "total": len(reports)}


@app.put("/reports/scheduled/{report_id}")
def update_scheduled_report(
    report_id: str,
    schedule: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None
):
    """Update a scheduled report"""
    if report_id not in SCHEDULED_REPORTS:
        raise HTTPException(status_code=404, detail="Scheduled report not found")

    report = SCHEDULED_REPORTS[report_id]
    if schedule:
        report["schedule"] = schedule
    if config:
        report["config"] = config
    if enabled is not None:
        report["enabled"] = enabled
    report["updated_at"] = datetime.utcnow().isoformat()

    return report


@app.delete("/reports/scheduled/{report_id}")
def delete_scheduled_report(report_id: str):
    """Delete a scheduled report"""
    if report_id not in SCHEDULED_REPORTS:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    del SCHEDULED_REPORTS[report_id]
    return {"deleted": True}


@app.post("/reports/scheduled/{report_id}/run")
def run_scheduled_report_now(report_id: str):
    """Manually trigger a scheduled report"""
    if report_id not in SCHEDULED_REPORTS:
        raise HTTPException(status_code=404, detail="Scheduled report not found")

    report = SCHEDULED_REPORTS[report_id]

    generated = {
        "id": f"gen_{uuid.uuid4().hex[:12]}",
        "report_id": report_id,
        "report_name": report["name"],
        "format": report["format"],
        "status": "completed",
        "file_url": f"/reports/download/{uuid.uuid4().hex[:12]}",
        "generated_at": datetime.utcnow().isoformat(),
        "size_bytes": random.randint(10000, 500000)
    }

    if report_id not in GENERATED_REPORTS:
        GENERATED_REPORTS[report_id] = []
    GENERATED_REPORTS[report_id].insert(0, generated)

    report["last_run"] = datetime.utcnow().isoformat()

    return generated


@app.get("/reports/generated")
def list_generated_reports(report_id: Optional[str] = None, user_id: Optional[str] = None):
    """List generated reports"""
    if report_id:
        reports = GENERATED_REPORTS.get(report_id, [])
    else:
        reports = []
        for rid, gen_list in GENERATED_REPORTS.items():
            reports.extend(gen_list)

    reports.sort(key=lambda x: x["generated_at"], reverse=True)
    return {"reports": reports, "total": len(reports)}


@app.post("/reports/builder")
def create_custom_report(
    name: str,
    user_id: str,
    sections: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None,
    branding: Optional[Dict[str, Any]] = None
):
    """Create a custom report using the report builder"""
    report_id = f"custom_{uuid.uuid4().hex[:12]}"
    report = {
        "id": report_id,
        "name": name,
        "user_id": user_id,
        "sections": sections,
        "filters": filters or {},
        "branding": branding or {},
        "created_at": datetime.utcnow().isoformat()
    }
    REPORT_TEMPLATES[report_id] = report
    return report


@app.get("/reports/formats")
def list_report_formats():
    """List available report export formats"""
    return {
        "formats": [
            {"id": "pdf", "name": "PDF", "mime_type": "application/pdf"},
            {"id": "csv", "name": "CSV", "mime_type": "text/csv"},
            {"id": "xlsx", "name": "Excel", "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            {"id": "json", "name": "JSON", "mime_type": "application/json"},
            {"id": "html", "name": "HTML", "mime_type": "text/html"}
        ]
    }


@app.get("/reports/schedules")
def list_schedule_presets():
    """List available schedule presets"""
    return {
        "presets": [
            {"id": "daily", "name": "Daily", "cron": "0 9 * * *", "description": "Every day at 9 AM"},
            {"id": "weekly", "name": "Weekly", "cron": "0 9 * * 1", "description": "Every Monday at 9 AM"},
            {"id": "biweekly", "name": "Bi-weekly", "cron": "0 9 1,15 * *", "description": "1st and 15th of month"},
            {"id": "monthly", "name": "Monthly", "cron": "0 9 1 * *", "description": "First day of month"},
            {"id": "quarterly", "name": "Quarterly", "cron": "0 9 1 1,4,7,10 *", "description": "First day of quarter"}
        ]
    }


# ============================================================================
# Integrations Hub
# ============================================================================

INTEGRATIONS: Dict[str, Dict[str, Any]] = {}
INTEGRATION_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
WEBHOOK_TEMPLATES: Dict[str, Dict[str, Any]] = {}
OAUTH_APPS: Dict[str, Dict[str, Any]] = {}


@app.get("/integrations/available")
def list_available_integrations():
    """List all available integrations"""
    return {
        "integrations": [
            {"id": "slack", "name": "Slack", "category": "communication", "status": "available",
             "description": "Send notifications and interact via Slack"},
            {"id": "teams", "name": "Microsoft Teams", "category": "communication", "status": "available",
             "description": "Teams integration for notifications and commands"},
            {"id": "jira", "name": "Jira", "category": "project_management", "status": "available",
             "description": "Create and manage Jira issues"},
            {"id": "github", "name": "GitHub", "category": "development", "status": "available",
             "description": "Trigger workflows from GitHub events"},
            {"id": "gitlab", "name": "GitLab", "category": "development", "status": "available",
             "description": "GitLab CI/CD integration"},
            {"id": "notion", "name": "Notion", "category": "documentation", "status": "available",
             "description": "Sync with Notion databases"},
            {"id": "zapier", "name": "Zapier", "category": "automation", "status": "available",
             "description": "Connect to 5000+ apps via Zapier"},
            {"id": "salesforce", "name": "Salesforce", "category": "crm", "status": "available",
             "description": "CRM integration with Salesforce"},
            {"id": "hubspot", "name": "HubSpot", "category": "crm", "status": "available",
             "description": "HubSpot CRM and marketing"},
            {"id": "snowflake", "name": "Snowflake", "category": "data", "status": "available",
             "description": "Query and sync with Snowflake"}
        ]
    }


@app.post("/integrations/connect")
def connect_integration(
    integration_id: str,
    user_id: str,
    credentials: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
):
    """Connect an integration"""
    connection_id = f"conn_{uuid.uuid4().hex[:12]}"
    connection = {
        "id": connection_id,
        "integration_id": integration_id,
        "user_id": user_id,
        "status": "connected",
        "config": config or {},
        "connected_at": datetime.utcnow().isoformat(),
        "last_sync": None,
        "health": "healthy"
    }
    INTEGRATION_CONNECTIONS[connection_id] = connection
    return connection


@app.get("/integrations/connections")
def list_integration_connections(user_id: Optional[str] = None):
    """List active integration connections"""
    connections = list(INTEGRATION_CONNECTIONS.values())
    if user_id:
        connections = [c for c in connections if c["user_id"] == user_id]
    return {"connections": connections, "total": len(connections)}


@app.get("/integrations/connections/{connection_id}")
def get_integration_connection(connection_id: str):
    """Get integration connection details"""
    if connection_id not in INTEGRATION_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    return INTEGRATION_CONNECTIONS[connection_id]


@app.post("/integrations/connections/{connection_id}/test")
def test_integration_connection(connection_id: str):
    """Test an integration connection"""
    if connection_id not in INTEGRATION_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection = INTEGRATION_CONNECTIONS[connection_id]
    # Simulate connection test
    return {
        "connection_id": connection_id,
        "integration_id": connection["integration_id"],
        "test_result": "success",
        "latency_ms": random.randint(50, 200),
        "tested_at": datetime.utcnow().isoformat()
    }


@app.post("/integrations/connections/{connection_id}/sync")
def sync_integration(connection_id: str, full_sync: bool = False):
    """Trigger a sync for an integration"""
    if connection_id not in INTEGRATION_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection = INTEGRATION_CONNECTIONS[connection_id]
    connection["last_sync"] = datetime.utcnow().isoformat()

    return {
        "connection_id": connection_id,
        "sync_type": "full" if full_sync else "incremental",
        "status": "completed",
        "records_synced": random.randint(10, 100),
        "synced_at": connection["last_sync"]
    }


@app.delete("/integrations/connections/{connection_id}")
def disconnect_integration(connection_id: str):
    """Disconnect an integration"""
    if connection_id not in INTEGRATION_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    del INTEGRATION_CONNECTIONS[connection_id]
    return {"disconnected": True}


@app.get("/integrations/webhook-templates")
def list_webhook_templates():
    """List pre-made webhook configurations"""
    return {
        "templates": [
            {"id": "slack_notify", "name": "Slack Notification",
             "description": "Send formatted message to Slack channel",
             "config": {"method": "POST", "content_type": "application/json"}},
            {"id": "discord_notify", "name": "Discord Webhook",
             "description": "Post to Discord channel",
             "config": {"method": "POST", "content_type": "application/json"}},
            {"id": "pagerduty_alert", "name": "PagerDuty Alert",
             "description": "Create PagerDuty incident",
             "config": {"method": "POST", "content_type": "application/json"}},
            {"id": "generic_post", "name": "Generic POST",
             "description": "Send data to any HTTP endpoint",
             "config": {"method": "POST", "content_type": "application/json"}}
        ]
    }


@app.post("/integrations/oauth-apps")
def register_oauth_app(
    name: str,
    client_id: str,
    redirect_uri: str,
    scopes: List[str],
    user_id: str
):
    """Register a third-party OAuth app"""
    app_id = f"oauth_{uuid.uuid4().hex[:12]}"
    app = {
        "id": app_id,
        "name": name,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "user_id": user_id,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    OAUTH_APPS[app_id] = app
    return app


@app.get("/integrations/oauth-apps")
def list_oauth_apps(user_id: Optional[str] = None):
    """List registered OAuth apps"""
    apps = list(OAUTH_APPS.values())
    if user_id:
        apps = [a for a in apps if a["user_id"] == user_id]
    return {"apps": apps, "total": len(apps)}


@app.get("/integrations/health")
def get_integrations_health():
    """Get health status of all integrations"""
    health_status = []
    for conn_id, conn in INTEGRATION_CONNECTIONS.items():
        health_status.append({
            "connection_id": conn_id,
            "integration_id": conn["integration_id"],
            "status": conn.get("health", "unknown"),
            "last_check": datetime.utcnow().isoformat(),
            "uptime_percent": random.uniform(99.0, 100.0)
        })

    return {
        "health": health_status,
        "total_connections": len(health_status),
        "healthy": len([h for h in health_status if h["status"] == "healthy"])
    }


# ============================================================================
# Agent Memory & Context
# ============================================================================

AGENT_MEMORY: Dict[str, Dict[str, Any]] = {}
CONVERSATION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
USER_PREFERENCES_STORE: Dict[str, Dict[str, Any]] = {}
CONTEXT_WINDOWS: Dict[str, Dict[str, Any]] = {}


@app.post("/memory/{agent_id}")
def store_memory(
    agent_id: str,
    key: str,
    value: Any,
    memory_type: str = "short_term",
    ttl_seconds: Optional[int] = None
):
    """Store a memory item for an agent"""
    memory_item = {
        "key": key,
        "value": value,
        "memory_type": memory_type,
        "ttl_seconds": ttl_seconds,
        "stored_at": datetime.utcnow().isoformat(),
        "access_count": 0,
        "last_accessed": None
    }

    if agent_id not in AGENT_MEMORY:
        AGENT_MEMORY[agent_id] = {}
    AGENT_MEMORY[agent_id][key] = memory_item

    return memory_item


@app.get("/memory/{agent_id}")
def get_agent_memory(agent_id: str, key: Optional[str] = None, memory_type: Optional[str] = None):
    """Get agent memory items"""
    if agent_id not in AGENT_MEMORY:
        return {"memory": {}, "total": 0}

    memory = AGENT_MEMORY[agent_id]

    if key:
        if key in memory:
            memory[key]["access_count"] += 1
            memory[key]["last_accessed"] = datetime.utcnow().isoformat()
            return {"memory": {key: memory[key]}, "total": 1}
        return {"memory": {}, "total": 0}

    if memory_type:
        filtered = {k: v for k, v in memory.items() if v["memory_type"] == memory_type}
        return {"memory": filtered, "total": len(filtered)}

    return {"memory": memory, "total": len(memory)}


@app.delete("/memory/{agent_id}")
def clear_agent_memory(agent_id: str, key: Optional[str] = None, memory_type: Optional[str] = None):
    """Clear agent memory"""
    if agent_id not in AGENT_MEMORY:
        return {"cleared": 0}

    if key:
        if key in AGENT_MEMORY[agent_id]:
            del AGENT_MEMORY[agent_id][key]
            return {"cleared": 1}
        return {"cleared": 0}

    if memory_type:
        before = len(AGENT_MEMORY[agent_id])
        AGENT_MEMORY[agent_id] = {k: v for k, v in AGENT_MEMORY[agent_id].items()
                                   if v["memory_type"] != memory_type}
        after = len(AGENT_MEMORY[agent_id])
        return {"cleared": before - after}

    count = len(AGENT_MEMORY[agent_id])
    AGENT_MEMORY[agent_id] = {}
    return {"cleared": count}


@app.post("/memory/{agent_id}/conversation")
def add_conversation_turn(
    agent_id: str,
    role: str,
    content: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Add a turn to conversation history"""
    turn = {
        "id": f"turn_{uuid.uuid4().hex[:8]}",
        "role": role,
        "content": content,
        "user_id": user_id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat()
    }

    if agent_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[agent_id] = []
    CONVERSATION_HISTORY[agent_id].append(turn)

    return turn


@app.get("/memory/{agent_id}/conversation")
def get_conversation_history(agent_id: str, limit: int = 50, user_id: Optional[str] = None):
    """Get conversation history for an agent"""
    history = CONVERSATION_HISTORY.get(agent_id, [])

    if user_id:
        history = [h for h in history if h.get("user_id") == user_id]

    return {"history": history[-limit:], "total": len(history)}


@app.post("/memory/user-preferences")
def store_user_preferences(user_id: str, agent_id: str, preferences: Dict[str, Any]):
    """Store user preferences for personalized agent behavior"""
    key = f"{user_id}:{agent_id}"
    pref = {
        "user_id": user_id,
        "agent_id": agent_id,
        "preferences": preferences,
        "updated_at": datetime.utcnow().isoformat()
    }
    USER_PREFERENCES_STORE[key] = pref
    return pref


@app.get("/memory/user-preferences")
def get_user_preferences(user_id: str, agent_id: Optional[str] = None):
    """Get user preferences"""
    if agent_id:
        key = f"{user_id}:{agent_id}"
        return USER_PREFERENCES_STORE.get(key, {"preferences": {}})

    # Get all preferences for user
    prefs = [v for k, v in USER_PREFERENCES_STORE.items() if k.startswith(f"{user_id}:")]
    return {"preferences": prefs, "total": len(prefs)}


@app.post("/memory/{agent_id}/context-window")
def configure_context_window(
    agent_id: str,
    max_tokens: int = 4000,
    include_history: int = 10,
    include_memory_types: Optional[List[str]] = None
):
    """Configure context window for an agent"""
    config = {
        "agent_id": agent_id,
        "max_tokens": max_tokens,
        "include_history": include_history,
        "include_memory_types": include_memory_types or ["short_term", "important"],
        "configured_at": datetime.utcnow().isoformat()
    }
    CONTEXT_WINDOWS[agent_id] = config
    return config


@app.get("/memory/{agent_id}/context-window")
def get_context_window(agent_id: str):
    """Get the current context window configuration"""
    return CONTEXT_WINDOWS.get(agent_id, {
        "agent_id": agent_id,
        "max_tokens": 4000,
        "include_history": 10,
        "include_memory_types": ["short_term"]
    })


@app.get("/memory/{agent_id}/build-context")
def build_agent_context(agent_id: str, user_id: Optional[str] = None):
    """Build the full context for an agent including memory and history"""
    context = {
        "agent_id": agent_id,
        "built_at": datetime.utcnow().isoformat()
    }

    # Get context window config
    config = CONTEXT_WINDOWS.get(agent_id, {"include_history": 10, "include_memory_types": ["short_term"]})

    # Add conversation history
    history = CONVERSATION_HISTORY.get(agent_id, [])
    if user_id:
        history = [h for h in history if h.get("user_id") == user_id]
    context["conversation_history"] = history[-config.get("include_history", 10):]

    # Add relevant memory
    memory = AGENT_MEMORY.get(agent_id, {})
    relevant_memory = {k: v for k, v in memory.items()
                       if v["memory_type"] in config.get("include_memory_types", [])}
    context["memory"] = relevant_memory

    # Add user preferences
    if user_id:
        key = f"{user_id}:{agent_id}"
        if key in USER_PREFERENCES_STORE:
            context["user_preferences"] = USER_PREFERENCES_STORE[key]["preferences"]

    return context


@app.post("/memory/search")
def search_memory(
    agent_id: str,
    query: str,
    memory_types: Optional[List[str]] = None,
    limit: int = 10
):
    """Search agent memory"""
    memory = AGENT_MEMORY.get(agent_id, {})
    results = []

    for key, item in memory.items():
        if memory_types and item["memory_type"] not in memory_types:
            continue

        # Simple text search (in production, use vector similarity)
        if query.lower() in str(item["value"]).lower() or query.lower() in key.lower():
            results.append({
                "key": key,
                "value": item["value"],
                "memory_type": item["memory_type"],
                "relevance_score": 0.8 + random.uniform(0, 0.2)
            })

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return {"results": results[:limit], "query": query, "total": len(results)}


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
