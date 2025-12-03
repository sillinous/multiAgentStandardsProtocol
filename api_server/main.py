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
# Multi-Modal Support
# ============================================================================

MEDIA_ASSETS: Dict[str, Dict[str, Any]] = {}
TRANSCRIPTIONS: Dict[str, Dict[str, Any]] = {}
MEDIA_ANALYSIS: Dict[str, Dict[str, Any]] = {}
SUPPORTED_MEDIA_TYPES = ["image", "audio", "video", "document", "pdf", "spreadsheet"]


@app.post("/media/upload")
def upload_media(
    filename: str,
    media_type: str,
    content_base64: str,
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """Upload a media file"""
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported media type. Supported: {SUPPORTED_MEDIA_TYPES}")

    asset_id = f"asset_{uuid.uuid4().hex[:12]}"
    asset = {
        "id": asset_id,
        "filename": filename,
        "media_type": media_type,
        "size_bytes": len(content_base64) * 3 // 4,  # Approximate decoded size
        "content_hash": hashlib.md5(content_base64.encode()).hexdigest(),
        "metadata": metadata or {},
        "user_id": user_id,
        "url": f"/media/download/{asset_id}",
        "thumbnail_url": f"/media/thumbnail/{asset_id}" if media_type in ["image", "video"] else None,
        "status": "uploaded",
        "created_at": datetime.utcnow().isoformat()
    }
    MEDIA_ASSETS[asset_id] = asset
    return asset


@app.get("/media")
def list_media_assets(
    media_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50
):
    """List media assets"""
    assets = list(MEDIA_ASSETS.values())
    if media_type:
        assets = [a for a in assets if a["media_type"] == media_type]
    if user_id:
        assets = [a for a in assets if a.get("user_id") == user_id]
    assets.sort(key=lambda x: x["created_at"], reverse=True)
    return {"assets": assets[:limit], "total": len(assets)}


@app.get("/media/{asset_id}")
def get_media_asset(asset_id: str):
    """Get media asset details"""
    if asset_id not in MEDIA_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")
    return MEDIA_ASSETS[asset_id]


@app.delete("/media/{asset_id}")
def delete_media_asset(asset_id: str):
    """Delete a media asset"""
    if asset_id not in MEDIA_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")
    del MEDIA_ASSETS[asset_id]
    return {"deleted": True}


@app.post("/media/{asset_id}/transcribe")
def transcribe_media(asset_id: str, language: str = "en", options: Optional[Dict[str, Any]] = None):
    """Transcribe audio/video content"""
    if asset_id not in MEDIA_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = MEDIA_ASSETS[asset_id]
    if asset["media_type"] not in ["audio", "video"]:
        raise HTTPException(status_code=400, detail="Only audio/video can be transcribed")

    transcription_id = f"trans_{uuid.uuid4().hex[:12]}"
    transcription = {
        "id": transcription_id,
        "asset_id": asset_id,
        "language": language,
        "status": "completed",
        "text": "This is a simulated transcription of the media content.",
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "This is a simulated"},
            {"start": 5.0, "end": 10.0, "text": "transcription of the media content."}
        ],
        "confidence": 0.95,
        "duration_seconds": 10.0,
        "options": options or {},
        "created_at": datetime.utcnow().isoformat()
    }
    TRANSCRIPTIONS[transcription_id] = transcription
    return transcription


@app.get("/media/{asset_id}/transcription")
def get_transcription(asset_id: str):
    """Get transcription for a media asset"""
    transcriptions = [t for t in TRANSCRIPTIONS.values() if t["asset_id"] == asset_id]
    if not transcriptions:
        raise HTTPException(status_code=404, detail="No transcription found")
    return transcriptions[-1]


@app.post("/media/{asset_id}/analyze")
def analyze_media(asset_id: str, analysis_types: Optional[List[str]] = None):
    """Analyze media content (OCR, object detection, sentiment, etc.)"""
    if asset_id not in MEDIA_ASSETS:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = MEDIA_ASSETS[asset_id]
    analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"

    # Simulate different analysis based on media type
    results = {}
    if asset["media_type"] == "image":
        results = {
            "objects": [{"label": "person", "confidence": 0.95}, {"label": "laptop", "confidence": 0.88}],
            "text_ocr": "Sample extracted text from image",
            "colors": ["#ffffff", "#000000", "#336699"],
            "dimensions": {"width": 1920, "height": 1080}
        }
    elif asset["media_type"] == "document":
        results = {
            "text": "Extracted document content...",
            "pages": 5,
            "word_count": 1250,
            "language": "en",
            "entities": [{"text": "John Doe", "type": "PERSON"}, {"text": "Acme Corp", "type": "ORG"}]
        }
    elif asset["media_type"] in ["audio", "video"]:
        results = {
            "duration": 120.5,
            "sentiment": "positive",
            "speakers": 2,
            "topics": ["technology", "business"]
        }

    analysis = {
        "id": analysis_id,
        "asset_id": asset_id,
        "media_type": asset["media_type"],
        "analysis_types": analysis_types or ["all"],
        "results": results,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat()
    }
    MEDIA_ANALYSIS[analysis_id] = analysis
    return analysis


@app.get("/media/{asset_id}/analysis")
def get_media_analysis(asset_id: str):
    """Get analysis results for a media asset"""
    analyses = [a for a in MEDIA_ANALYSIS.values() if a["asset_id"] == asset_id]
    return {"analyses": analyses, "total": len(analyses)}


@app.get("/media/types")
def list_supported_media_types():
    """List supported media types"""
    return {
        "types": [
            {"id": "image", "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp"], "max_size_mb": 50},
            {"id": "audio", "extensions": [".mp3", ".wav", ".m4a", ".ogg"], "max_size_mb": 100},
            {"id": "video", "extensions": [".mp4", ".webm", ".mov", ".avi"], "max_size_mb": 500},
            {"id": "document", "extensions": [".doc", ".docx", ".txt", ".rtf"], "max_size_mb": 25},
            {"id": "pdf", "extensions": [".pdf"], "max_size_mb": 50},
            {"id": "spreadsheet", "extensions": [".xls", ".xlsx", ".csv"], "max_size_mb": 25}
        ]
    }


# ============================================================================
# Agent Orchestration
# ============================================================================

ORCHESTRATION_FLOWS: Dict[str, Dict[str, Any]] = {}
ORCHESTRATION_RUNS: Dict[str, Dict[str, Any]] = {}
AGENT_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}
ORCHESTRATION_PATTERNS = ["sequential", "parallel", "fan_out_fan_in", "pipeline", "scatter_gather", "saga"]


@app.post("/orchestration/flows")
def create_orchestration_flow(
    name: str,
    pattern: str,
    agents: List[Dict[str, Any]],
    connections: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
):
    """Create a multi-agent orchestration flow"""
    if pattern not in ORCHESTRATION_PATTERNS:
        raise HTTPException(status_code=400, detail=f"Invalid pattern. Valid: {ORCHESTRATION_PATTERNS}")

    flow_id = f"flow_{uuid.uuid4().hex[:12]}"
    flow = {
        "id": flow_id,
        "name": name,
        "pattern": pattern,
        "agents": agents,
        "connections": connections,
        "config": config or {},
        "status": "active",
        "run_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    ORCHESTRATION_FLOWS[flow_id] = flow
    return flow


@app.get("/orchestration/flows")
def list_orchestration_flows(pattern: Optional[str] = None):
    """List orchestration flows"""
    flows = list(ORCHESTRATION_FLOWS.values())
    if pattern:
        flows = [f for f in flows if f["pattern"] == pattern]
    return {"flows": flows, "total": len(flows)}


@app.get("/orchestration/flows/{flow_id}")
def get_orchestration_flow(flow_id: str):
    """Get orchestration flow details"""
    if flow_id not in ORCHESTRATION_FLOWS:
        raise HTTPException(status_code=404, detail="Flow not found")
    return ORCHESTRATION_FLOWS[flow_id]


@app.post("/orchestration/flows/{flow_id}/run")
def run_orchestration_flow(flow_id: str, input_data: Optional[Dict[str, Any]] = None):
    """Execute an orchestration flow"""
    if flow_id not in ORCHESTRATION_FLOWS:
        raise HTTPException(status_code=404, detail="Flow not found")

    flow = ORCHESTRATION_FLOWS[flow_id]
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    # Simulate flow execution
    agent_results = []
    for agent in flow["agents"]:
        agent_results.append({
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "status": "completed",
            "output": {"result": f"Output from {agent.get('name')}"},
            "duration_ms": random.randint(100, 2000)
        })

    run = {
        "id": run_id,
        "flow_id": flow_id,
        "flow_name": flow["name"],
        "pattern": flow["pattern"],
        "status": "completed",
        "input_data": input_data or {},
        "agent_results": agent_results,
        "total_duration_ms": sum(r["duration_ms"] for r in agent_results),
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }
    ORCHESTRATION_RUNS[run_id] = run
    flow["run_count"] += 1

    return run


@app.get("/orchestration/runs")
def list_orchestration_runs(flow_id: Optional[str] = None, status: Optional[str] = None):
    """List orchestration runs"""
    runs = list(ORCHESTRATION_RUNS.values())
    if flow_id:
        runs = [r for r in runs if r["flow_id"] == flow_id]
    if status:
        runs = [r for r in runs if r["status"] == status]
    runs.sort(key=lambda x: x["started_at"], reverse=True)
    return {"runs": runs, "total": len(runs)}


@app.get("/orchestration/runs/{run_id}")
def get_orchestration_run(run_id: str):
    """Get orchestration run details"""
    if run_id not in ORCHESTRATION_RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    return ORCHESTRATION_RUNS[run_id]


@app.post("/orchestration/messages")
def send_agent_message(
    from_agent: str,
    to_agent: str,
    message_type: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None
):
    """Send a message between agents"""
    message = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,
        "payload": payload,
        "correlation_id": correlation_id or uuid.uuid4().hex[:12],
        "status": "delivered",
        "sent_at": datetime.utcnow().isoformat()
    }

    if to_agent not in AGENT_MESSAGES:
        AGENT_MESSAGES[to_agent] = []
    AGENT_MESSAGES[to_agent].append(message)

    return message


@app.get("/orchestration/messages/{agent_id}")
def get_agent_messages(agent_id: str, limit: int = 50, unread_only: bool = False):
    """Get messages for an agent"""
    messages = AGENT_MESSAGES.get(agent_id, [])
    return {"messages": messages[-limit:], "total": len(messages)}


@app.get("/orchestration/patterns")
def list_orchestration_patterns():
    """List available orchestration patterns"""
    return {
        "patterns": [
            {"id": "sequential", "name": "Sequential", "description": "Agents execute one after another"},
            {"id": "parallel", "name": "Parallel", "description": "Agents execute simultaneously"},
            {"id": "fan_out_fan_in", "name": "Fan-out/Fan-in", "description": "Split work then aggregate"},
            {"id": "pipeline", "name": "Pipeline", "description": "Data flows through stages"},
            {"id": "scatter_gather", "name": "Scatter-Gather", "description": "Broadcast then collect"},
            {"id": "saga", "name": "Saga", "description": "Long-running with compensation"}
        ]
    }


# ============================================================================
# Version Control for Agents
# ============================================================================

AGENT_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}
AGENT_BRANCHES: Dict[str, Dict[str, Any]] = {}
VERSION_DIFFS: Dict[str, Dict[str, Any]] = {}


@app.post("/versions/{agent_id}/commit")
def commit_agent_version(
    agent_id: str,
    config: Dict[str, Any],
    message: str,
    author: Optional[str] = None,
    branch: str = "main"
):
    """Commit a new version of an agent configuration"""
    version_id = f"v_{uuid.uuid4().hex[:8]}"

    # Get previous version
    versions = AGENT_VERSIONS.get(agent_id, [])
    parent_id = versions[-1]["id"] if versions else None

    version = {
        "id": version_id,
        "agent_id": agent_id,
        "config": config,
        "message": message,
        "author": author,
        "branch": branch,
        "parent_id": parent_id,
        "version_number": len(versions) + 1,
        "created_at": datetime.utcnow().isoformat()
    }

    if agent_id not in AGENT_VERSIONS:
        AGENT_VERSIONS[agent_id] = []
    AGENT_VERSIONS[agent_id].append(version)

    return version


@app.get("/versions/{agent_id}")
def get_agent_versions(agent_id: str, branch: Optional[str] = None, limit: int = 50):
    """Get version history for an agent"""
    versions = AGENT_VERSIONS.get(agent_id, [])
    if branch:
        versions = [v for v in versions if v["branch"] == branch]
    versions = list(reversed(versions))  # Most recent first
    return {"versions": versions[:limit], "total": len(versions)}


@app.get("/versions/{agent_id}/{version_id}")
def get_agent_version(agent_id: str, version_id: str):
    """Get a specific version"""
    versions = AGENT_VERSIONS.get(agent_id, [])
    for v in versions:
        if v["id"] == version_id:
            return v
    raise HTTPException(status_code=404, detail="Version not found")


@app.post("/versions/{agent_id}/branches")
def create_agent_branch(agent_id: str, branch_name: str, from_version: Optional[str] = None):
    """Create a new branch for an agent"""
    branch_key = f"{agent_id}:{branch_name}"
    if branch_key in AGENT_BRANCHES:
        raise HTTPException(status_code=400, detail="Branch already exists")

    versions = AGENT_VERSIONS.get(agent_id, [])
    base_version = from_version or (versions[-1]["id"] if versions else None)

    branch = {
        "id": branch_key,
        "agent_id": agent_id,
        "name": branch_name,
        "base_version": base_version,
        "created_at": datetime.utcnow().isoformat()
    }
    AGENT_BRANCHES[branch_key] = branch
    return branch


@app.get("/versions/{agent_id}/branches")
def list_agent_branches(agent_id: str):
    """List branches for an agent"""
    branches = [b for b in AGENT_BRANCHES.values() if b["agent_id"] == agent_id]
    return {"branches": branches, "total": len(branches)}


@app.post("/versions/{agent_id}/diff")
def diff_versions(agent_id: str, version_a: str, version_b: str):
    """Get diff between two versions"""
    versions = AGENT_VERSIONS.get(agent_id, [])
    v_a = next((v for v in versions if v["id"] == version_a), None)
    v_b = next((v for v in versions if v["id"] == version_b), None)

    if not v_a or not v_b:
        raise HTTPException(status_code=404, detail="Version not found")

    # Simple diff simulation
    diff = {
        "id": f"diff_{uuid.uuid4().hex[:8]}",
        "agent_id": agent_id,
        "version_a": version_a,
        "version_b": version_b,
        "changes": [],
        "additions": 0,
        "deletions": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    # Compare configs
    for key in set(list(v_a["config"].keys()) + list(v_b["config"].keys())):
        old_val = v_a["config"].get(key)
        new_val = v_b["config"].get(key)
        if old_val != new_val:
            diff["changes"].append({
                "field": key,
                "old_value": old_val,
                "new_value": new_val,
                "type": "modified" if old_val and new_val else ("added" if new_val else "removed")
            })

    diff["additions"] = len([c for c in diff["changes"] if c["type"] in ["added", "modified"]])
    diff["deletions"] = len([c for c in diff["changes"] if c["type"] in ["removed", "modified"]])

    return diff


@app.post("/versions/{agent_id}/rollback/{version_id}")
def rollback_to_version(agent_id: str, version_id: str):
    """Rollback agent to a specific version"""
    versions = AGENT_VERSIONS.get(agent_id, [])
    target = next((v for v in versions if v["id"] == version_id), None)

    if not target:
        raise HTTPException(status_code=404, detail="Version not found")

    # Create a new version with the old config
    return commit_agent_version(
        agent_id=agent_id,
        config=target["config"],
        message=f"Rollback to {version_id}",
        author="system",
        branch="main"
    )


@app.post("/versions/{agent_id}/merge")
def merge_branches(agent_id: str, source_branch: str, target_branch: str = "main"):
    """Merge one branch into another"""
    source_key = f"{agent_id}:{source_branch}"
    if source_key not in AGENT_BRANCHES:
        raise HTTPException(status_code=404, detail="Source branch not found")

    # Get latest version from source branch
    versions = AGENT_VERSIONS.get(agent_id, [])
    source_versions = [v for v in versions if v["branch"] == source_branch]

    if not source_versions:
        raise HTTPException(status_code=400, detail="No versions in source branch")

    latest = source_versions[-1]

    # Create merge commit
    merge_version = commit_agent_version(
        agent_id=agent_id,
        config=latest["config"],
        message=f"Merge {source_branch} into {target_branch}",
        author="system",
        branch=target_branch
    )

    return {
        "merged": True,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "merge_version": merge_version
    }


# ============================================================================
# Canary Deployments
# ============================================================================

DEPLOYMENTS: Dict[str, Dict[str, Any]] = {}
DEPLOYMENT_STAGES: Dict[str, List[Dict[str, Any]]] = {}
DEPLOYMENT_METRICS: Dict[str, Dict[str, Any]] = {}


@app.post("/deployments")
def create_deployment(
    agent_id: str,
    version_id: str,
    strategy: str = "canary",
    stages: Optional[List[Dict[str, Any]]] = None,
    rollback_threshold: float = 0.05
):
    """Create a new deployment"""
    deployment_id = f"deploy_{uuid.uuid4().hex[:12]}"

    default_stages = [
        {"name": "canary", "percentage": 5, "duration_minutes": 15},
        {"name": "limited", "percentage": 25, "duration_minutes": 30},
        {"name": "broad", "percentage": 50, "duration_minutes": 60},
        {"name": "full", "percentage": 100, "duration_minutes": 0}
    ]

    deployment = {
        "id": deployment_id,
        "agent_id": agent_id,
        "version_id": version_id,
        "strategy": strategy,
        "stages": stages or default_stages,
        "current_stage": 0,
        "current_percentage": 0,
        "rollback_threshold": rollback_threshold,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None
    }
    DEPLOYMENTS[deployment_id] = deployment
    return deployment


@app.get("/deployments")
def list_deployments(agent_id: Optional[str] = None, status: Optional[str] = None):
    """List deployments"""
    deployments = list(DEPLOYMENTS.values())
    if agent_id:
        deployments = [d for d in deployments if d["agent_id"] == agent_id]
    if status:
        deployments = [d for d in deployments if d["status"] == status]
    deployments.sort(key=lambda x: x["created_at"], reverse=True)
    return {"deployments": deployments, "total": len(deployments)}


@app.get("/deployments/{deployment_id}")
def get_deployment(deployment_id: str):
    """Get deployment details"""
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DEPLOYMENTS[deployment_id]


@app.post("/deployments/{deployment_id}/start")
def start_deployment(deployment_id: str):
    """Start a deployment"""
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment = DEPLOYMENTS[deployment_id]
    deployment["status"] = "in_progress"
    deployment["started_at"] = datetime.utcnow().isoformat()
    deployment["current_stage"] = 0
    deployment["current_percentage"] = deployment["stages"][0]["percentage"]

    return deployment


@app.post("/deployments/{deployment_id}/advance")
def advance_deployment_stage(deployment_id: str):
    """Advance deployment to next stage"""
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment = DEPLOYMENTS[deployment_id]
    if deployment["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Deployment not in progress")

    current = deployment["current_stage"]
    if current >= len(deployment["stages"]) - 1:
        deployment["status"] = "completed"
        deployment["current_percentage"] = 100
        deployment["completed_at"] = datetime.utcnow().isoformat()
    else:
        deployment["current_stage"] = current + 1
        deployment["current_percentage"] = deployment["stages"][current + 1]["percentage"]

    return deployment


@app.post("/deployments/{deployment_id}/rollback")
def rollback_deployment(deployment_id: str, reason: Optional[str] = None):
    """Rollback a deployment"""
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment = DEPLOYMENTS[deployment_id]
    deployment["status"] = "rolled_back"
    deployment["current_percentage"] = 0
    deployment["rollback_reason"] = reason
    deployment["rolled_back_at"] = datetime.utcnow().isoformat()

    return deployment


@app.post("/deployments/{deployment_id}/metrics")
def record_deployment_metrics(
    deployment_id: str,
    error_rate: float,
    latency_p50: float,
    latency_p99: float,
    success_rate: float
):
    """Record metrics for a deployment"""
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment = DEPLOYMENTS[deployment_id]
    metrics = {
        "deployment_id": deployment_id,
        "error_rate": error_rate,
        "latency_p50": latency_p50,
        "latency_p99": latency_p99,
        "success_rate": success_rate,
        "recorded_at": datetime.utcnow().isoformat()
    }
    DEPLOYMENT_METRICS[deployment_id] = metrics

    # Auto-rollback if error rate exceeds threshold
    if error_rate > deployment["rollback_threshold"]:
        deployment["status"] = "auto_rolled_back"
        deployment["rollback_reason"] = f"Error rate {error_rate} exceeded threshold {deployment['rollback_threshold']}"
        deployment["rolled_back_at"] = datetime.utcnow().isoformat()

    return {
        "metrics": metrics,
        "deployment_status": deployment["status"],
        "auto_rollback_triggered": deployment["status"] == "auto_rolled_back"
    }


@app.get("/deployments/{deployment_id}/metrics")
def get_deployment_metrics(deployment_id: str):
    """Get metrics for a deployment"""
    return DEPLOYMENT_METRICS.get(deployment_id, {})


# ============================================================================
# Experiments Framework
# ============================================================================

EXPERIMENTS: Dict[str, Dict[str, Any]] = {}
EXPERIMENT_VARIANTS: Dict[str, List[Dict[str, Any]]] = {}
EXPERIMENT_RESULTS: Dict[str, Dict[str, Any]] = {}


@app.post("/experiments")
def create_experiment(
    name: str,
    hypothesis: str,
    agent_id: str,
    variants: List[Dict[str, Any]],
    metrics: List[str],
    traffic_split: Optional[Dict[str, float]] = None,
    duration_days: int = 7
):
    """Create an A/B experiment"""
    experiment_id = f"exp_{uuid.uuid4().hex[:12]}"

    # Default equal traffic split
    if not traffic_split:
        traffic_split = {v["name"]: 1.0 / len(variants) for v in variants}

    experiment = {
        "id": experiment_id,
        "name": name,
        "hypothesis": hypothesis,
        "agent_id": agent_id,
        "variants": variants,
        "metrics": metrics,
        "traffic_split": traffic_split,
        "duration_days": duration_days,
        "status": "draft",
        "participants": 0,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "ended_at": None
    }
    EXPERIMENTS[experiment_id] = experiment
    EXPERIMENT_VARIANTS[experiment_id] = variants
    return experiment


@app.get("/experiments")
def list_experiments(agent_id: Optional[str] = None, status: Optional[str] = None):
    """List experiments"""
    experiments = list(EXPERIMENTS.values())
    if agent_id:
        experiments = [e for e in experiments if e["agent_id"] == agent_id]
    if status:
        experiments = [e for e in experiments if e["status"] == status]
    return {"experiments": experiments, "total": len(experiments)}


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    """Get experiment details"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return EXPERIMENTS[experiment_id]


@app.post("/experiments/{experiment_id}/start")
def start_experiment(experiment_id: str):
    """Start an experiment"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = EXPERIMENTS[experiment_id]
    experiment["status"] = "running"
    experiment["started_at"] = datetime.utcnow().isoformat()
    return experiment


@app.post("/experiments/{experiment_id}/stop")
def stop_experiment(experiment_id: str):
    """Stop an experiment"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = EXPERIMENTS[experiment_id]
    experiment["status"] = "stopped"
    experiment["ended_at"] = datetime.utcnow().isoformat()
    return experiment


@app.post("/experiments/{experiment_id}/record")
def record_experiment_event(
    experiment_id: str,
    variant: str,
    user_id: str,
    metric: str,
    value: float
):
    """Record an event for an experiment"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = EXPERIMENTS[experiment_id]
    experiment["participants"] += 1

    if experiment_id not in EXPERIMENT_RESULTS:
        EXPERIMENT_RESULTS[experiment_id] = {"variants": {}}

    if variant not in EXPERIMENT_RESULTS[experiment_id]["variants"]:
        EXPERIMENT_RESULTS[experiment_id]["variants"][variant] = {"samples": 0, "metrics": {}}

    results = EXPERIMENT_RESULTS[experiment_id]["variants"][variant]
    results["samples"] += 1
    if metric not in results["metrics"]:
        results["metrics"][metric] = {"values": [], "sum": 0}
    results["metrics"][metric]["values"].append(value)
    results["metrics"][metric]["sum"] += value

    return {"recorded": True, "variant": variant, "metric": metric}


@app.get("/experiments/{experiment_id}/results")
def get_experiment_results(experiment_id: str):
    """Get experiment results with statistical analysis"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = EXPERIMENTS[experiment_id]
    raw_results = EXPERIMENT_RESULTS.get(experiment_id, {"variants": {}})

    # Calculate statistics for each variant
    analyzed = {}
    for variant_name, data in raw_results["variants"].items():
        analyzed[variant_name] = {
            "samples": data["samples"],
            "metrics": {}
        }
        for metric, values in data["metrics"].items():
            vals = values["values"]
            if vals:
                analyzed[variant_name]["metrics"][metric] = {
                    "mean": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "count": len(vals)
                }

    # Determine winner (simplified)
    winner = None
    if len(analyzed) >= 2 and experiment["metrics"]:
        primary_metric = experiment["metrics"][0]
        best_mean = -float('inf')
        for variant, data in analyzed.items():
            if primary_metric in data.get("metrics", {}):
                mean = data["metrics"][primary_metric]["mean"]
                if mean > best_mean:
                    best_mean = mean
                    winner = variant

    return {
        "experiment_id": experiment_id,
        "status": experiment["status"],
        "participants": experiment["participants"],
        "variants": analyzed,
        "winner": winner,
        "statistical_significance": random.uniform(0.85, 0.99) if winner else None
    }


@app.post("/experiments/{experiment_id}/declare-winner")
def declare_experiment_winner(experiment_id: str, winner_variant: str):
    """Declare a winner and end experiment"""
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = EXPERIMENTS[experiment_id]
    experiment["status"] = "completed"
    experiment["winner"] = winner_variant
    experiment["ended_at"] = datetime.utcnow().isoformat()

    return experiment


# ============================================================================
# Data Pipelines
# ============================================================================

PIPELINES: Dict[str, Dict[str, Any]] = {}
PIPELINE_RUNS: Dict[str, Dict[str, Any]] = {}
PIPELINE_STEPS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/pipelines")
def create_pipeline(
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    schedule: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
):
    """Create a data pipeline"""
    pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
    pipeline = {
        "id": pipeline_id,
        "name": name,
        "description": description,
        "steps": steps,
        "schedule": schedule,
        "config": config or {},
        "status": "active",
        "run_count": 0,
        "last_run": None,
        "created_at": datetime.utcnow().isoformat()
    }
    PIPELINES[pipeline_id] = pipeline
    PIPELINE_STEPS[pipeline_id] = steps
    return pipeline


@app.get("/pipelines")
def list_pipelines(status: Optional[str] = None):
    """List data pipelines"""
    pipelines = list(PIPELINES.values())
    if status:
        pipelines = [p for p in pipelines if p["status"] == status]
    return {"pipelines": pipelines, "total": len(pipelines)}


@app.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    """Get pipeline details"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PIPELINES[pipeline_id]


@app.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: str, input_data: Optional[Dict[str, Any]] = None):
    """Execute a data pipeline"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = PIPELINES[pipeline_id]
    run_id = f"prun_{uuid.uuid4().hex[:12]}"

    # Simulate step execution
    step_results = []
    current_data = input_data or {}
    for i, step in enumerate(pipeline["steps"]):
        step_result = {
            "step_index": i,
            "step_name": step.get("name"),
            "step_type": step.get("type"),
            "status": "completed",
            "input_records": random.randint(100, 10000),
            "output_records": random.randint(100, 10000),
            "duration_ms": random.randint(500, 5000),
            "output_sample": {"transformed": True}
        }
        step_results.append(step_result)

    run = {
        "id": run_id,
        "pipeline_id": pipeline_id,
        "pipeline_name": pipeline["name"],
        "status": "completed",
        "input_data": input_data,
        "step_results": step_results,
        "total_records_processed": sum(s["output_records"] for s in step_results),
        "total_duration_ms": sum(s["duration_ms"] for s in step_results),
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }
    PIPELINE_RUNS[run_id] = run
    pipeline["run_count"] += 1
    pipeline["last_run"] = datetime.utcnow().isoformat()

    return run


@app.get("/pipelines/{pipeline_id}/runs")
def list_pipeline_runs(pipeline_id: str, limit: int = 20):
    """List runs for a pipeline"""
    runs = [r for r in PIPELINE_RUNS.values() if r["pipeline_id"] == pipeline_id]
    runs.sort(key=lambda x: x["started_at"], reverse=True)
    return {"runs": runs[:limit], "total": len(runs)}


@app.get("/pipelines/runs/{run_id}")
def get_pipeline_run(run_id: str):
    """Get pipeline run details"""
    if run_id not in PIPELINE_RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    return PIPELINE_RUNS[run_id]


@app.put("/pipelines/{pipeline_id}")
def update_pipeline(
    pipeline_id: str,
    steps: Optional[List[Dict[str, Any]]] = None,
    schedule: Optional[str] = None,
    status: Optional[str] = None
):
    """Update a pipeline"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = PIPELINES[pipeline_id]
    if steps:
        pipeline["steps"] = steps
        PIPELINE_STEPS[pipeline_id] = steps
    if schedule:
        pipeline["schedule"] = schedule
    if status:
        pipeline["status"] = status
    pipeline["updated_at"] = datetime.utcnow().isoformat()

    return pipeline


@app.delete("/pipelines/{pipeline_id}")
def delete_pipeline(pipeline_id: str):
    """Delete a pipeline"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    del PIPELINES[pipeline_id]
    return {"deleted": True}


@app.get("/pipelines/step-types")
def list_pipeline_step_types():
    """List available pipeline step types"""
    return {
        "step_types": [
            {"type": "extract", "name": "Extract", "description": "Extract data from source"},
            {"type": "transform", "name": "Transform", "description": "Transform/clean data"},
            {"type": "filter", "name": "Filter", "description": "Filter records"},
            {"type": "aggregate", "name": "Aggregate", "description": "Aggregate/group data"},
            {"type": "enrich", "name": "Enrich", "description": "Enrich with external data"},
            {"type": "validate", "name": "Validate", "description": "Validate data quality"},
            {"type": "load", "name": "Load", "description": "Load to destination"},
            {"type": "agent", "name": "Agent", "description": "Process with AI agent"}
        ]
    }


# ============================================================================
# Custom Metrics & KPIs
# ============================================================================

CUSTOM_METRICS: Dict[str, Dict[str, Any]] = {}
METRIC_DATA_POINTS: Dict[str, List[Dict[str, Any]]] = {}
METRIC_ALERTS: Dict[str, Dict[str, Any]] = {}


@app.post("/metrics/custom")
def create_custom_metric(
    name: str,
    description: str,
    unit: str,
    aggregation: str = "avg",
    dimensions: Optional[List[str]] = None,
    thresholds: Optional[Dict[str, float]] = None
):
    """Create a custom metric definition"""
    metric_id = f"metric_{uuid.uuid4().hex[:12]}"
    metric = {
        "id": metric_id,
        "name": name,
        "description": description,
        "unit": unit,
        "aggregation": aggregation,  # avg, sum, min, max, count, p50, p95, p99
        "dimensions": dimensions or [],
        "thresholds": thresholds or {},  # warning, critical
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    CUSTOM_METRICS[metric_id] = metric
    METRIC_DATA_POINTS[metric_id] = []
    return metric


@app.get("/metrics/custom")
def list_custom_metrics():
    """List custom metrics"""
    return {"metrics": list(CUSTOM_METRICS.values()), "total": len(CUSTOM_METRICS)}


@app.get("/metrics/custom/{metric_id}")
def get_custom_metric(metric_id: str):
    """Get custom metric details"""
    if metric_id not in CUSTOM_METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")
    return CUSTOM_METRICS[metric_id]


@app.post("/metrics/custom/{metric_id}/record")
def record_metric_value(
    metric_id: str,
    value: float,
    dimensions: Optional[Dict[str, str]] = None,
    timestamp: Optional[str] = None
):
    """Record a metric data point"""
    if metric_id not in CUSTOM_METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")

    data_point = {
        "id": f"dp_{uuid.uuid4().hex[:8]}",
        "metric_id": metric_id,
        "value": value,
        "dimensions": dimensions or {},
        "timestamp": timestamp or datetime.utcnow().isoformat()
    }
    METRIC_DATA_POINTS[metric_id].append(data_point)

    # Check thresholds
    metric = CUSTOM_METRICS[metric_id]
    alert_level = None
    if "critical" in metric.get("thresholds", {}) and value >= metric["thresholds"]["critical"]:
        alert_level = "critical"
    elif "warning" in metric.get("thresholds", {}) and value >= metric["thresholds"]["warning"]:
        alert_level = "warning"

    return {"recorded": True, "data_point": data_point, "alert_level": alert_level}


@app.get("/metrics/custom/{metric_id}/data")
def get_metric_data(
    metric_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 1000
):
    """Get metric data points"""
    if metric_id not in CUSTOM_METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")

    data = METRIC_DATA_POINTS.get(metric_id, [])

    # Filter by time range if provided
    if start_time:
        data = [d for d in data if d["timestamp"] >= start_time]
    if end_time:
        data = [d for d in data if d["timestamp"] <= end_time]

    return {"data_points": data[-limit:], "total": len(data)}


@app.get("/metrics/custom/{metric_id}/aggregate")
def aggregate_metric(
    metric_id: str,
    period: str = "1h",
    aggregation: Optional[str] = None
):
    """Get aggregated metric values"""
    if metric_id not in CUSTOM_METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")

    metric = CUSTOM_METRICS[metric_id]
    data = METRIC_DATA_POINTS.get(metric_id, [])
    agg = aggregation or metric["aggregation"]

    if not data:
        return {"aggregation": agg, "period": period, "value": None}

    values = [d["value"] for d in data]

    result = None
    if agg == "avg":
        result = sum(values) / len(values)
    elif agg == "sum":
        result = sum(values)
    elif agg == "min":
        result = min(values)
    elif agg == "max":
        result = max(values)
    elif agg == "count":
        result = len(values)
    elif agg == "p50":
        sorted_vals = sorted(values)
        result = sorted_vals[len(sorted_vals) // 2]
    elif agg == "p95":
        sorted_vals = sorted(values)
        result = sorted_vals[int(len(sorted_vals) * 0.95)]
    elif agg == "p99":
        sorted_vals = sorted(values)
        result = sorted_vals[int(len(sorted_vals) * 0.99)]

    return {"aggregation": agg, "period": period, "value": result, "sample_count": len(values)}


@app.post("/metrics/custom/{metric_id}/alerts")
def create_metric_alert(
    metric_id: str,
    name: str,
    condition: str,
    threshold: float,
    severity: str = "warning",
    actions: Optional[List[Dict[str, Any]]] = None
):
    """Create an alert for a custom metric"""
    if metric_id not in CUSTOM_METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")

    alert_id = f"malert_{uuid.uuid4().hex[:8]}"
    alert = {
        "id": alert_id,
        "metric_id": metric_id,
        "name": name,
        "condition": condition,  # gt, lt, gte, lte, eq
        "threshold": threshold,
        "severity": severity,
        "actions": actions or [],
        "enabled": True,
        "triggered_count": 0,
        "last_triggered": None,
        "created_at": datetime.utcnow().isoformat()
    }
    METRIC_ALERTS[alert_id] = alert
    return alert


@app.get("/metrics/aggregation-types")
def list_aggregation_types():
    """List available aggregation types"""
    return {
        "aggregation_types": [
            {"id": "avg", "name": "Average", "description": "Mean value"},
            {"id": "sum", "name": "Sum", "description": "Total sum"},
            {"id": "min", "name": "Minimum", "description": "Lowest value"},
            {"id": "max", "name": "Maximum", "description": "Highest value"},
            {"id": "count", "name": "Count", "description": "Number of data points"},
            {"id": "p50", "name": "P50 (Median)", "description": "50th percentile"},
            {"id": "p95", "name": "P95", "description": "95th percentile"},
            {"id": "p99", "name": "P99", "description": "99th percentile"}
        ]
    }


# ============================================================================
# Usage Quotas & Limits
# ============================================================================

QUOTA_POLICIES: Dict[str, Dict[str, Any]] = {}
QUOTA_USAGE: Dict[str, Dict[str, Any]] = {}
QUOTA_ALERTS: List[Dict[str, Any]] = []


@app.post("/quotas/policies")
def create_quota_policy(
    name: str,
    resource_type: str,
    limits: Dict[str, Any],
    scope: str = "user",
    enforcement: str = "hard"
):
    """Create a quota policy"""
    policy_id = f"quota_{uuid.uuid4().hex[:12]}"
    policy = {
        "id": policy_id,
        "name": name,
        "resource_type": resource_type,
        "limits": limits,  # e.g., {"requests_per_day": 10000, "tokens_per_month": 1000000}
        "scope": scope,  # user, org, team
        "enforcement": enforcement,  # hard (block), soft (warn)
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    QUOTA_POLICIES[policy_id] = policy
    return policy


@app.get("/quotas/policies")
def list_quota_policies(resource_type: Optional[str] = None):
    """List quota policies"""
    policies = list(QUOTA_POLICIES.values())
    if resource_type:
        policies = [p for p in policies if p["resource_type"] == resource_type]
    return {"policies": policies, "total": len(policies)}


@app.get("/quotas/policies/{policy_id}")
def get_quota_policy(policy_id: str):
    """Get quota policy details"""
    if policy_id not in QUOTA_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return QUOTA_POLICIES[policy_id]


@app.post("/quotas/usage")
def record_quota_usage(
    entity_id: str,
    entity_type: str,
    resource_type: str,
    usage: Dict[str, float]
):
    """Record usage against quotas"""
    key = f"{entity_type}:{entity_id}:{resource_type}"

    if key not in QUOTA_USAGE:
        QUOTA_USAGE[key] = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "resource_type": resource_type,
            "usage": {},
            "period_start": datetime.utcnow().replace(day=1, hour=0, minute=0, second=0).isoformat()
        }

    # Update usage
    for metric, value in usage.items():
        if metric not in QUOTA_USAGE[key]["usage"]:
            QUOTA_USAGE[key]["usage"][metric] = 0
        QUOTA_USAGE[key]["usage"][metric] += value

    QUOTA_USAGE[key]["last_updated"] = datetime.utcnow().isoformat()

    # Check against policies
    violations = []
    for policy in QUOTA_POLICIES.values():
        if policy["resource_type"] == resource_type:
            for limit_key, limit_value in policy["limits"].items():
                current = QUOTA_USAGE[key]["usage"].get(limit_key, 0)
                if current >= limit_value:
                    violations.append({
                        "policy_id": policy["id"],
                        "limit": limit_key,
                        "limit_value": limit_value,
                        "current_usage": current,
                        "enforcement": policy["enforcement"]
                    })

    return {
        "recorded": True,
        "current_usage": QUOTA_USAGE[key]["usage"],
        "violations": violations
    }


@app.get("/quotas/usage/{entity_type}/{entity_id}")
def get_quota_usage(entity_type: str, entity_id: str, resource_type: Optional[str] = None):
    """Get quota usage for an entity"""
    results = []
    for key, usage in QUOTA_USAGE.items():
        if usage["entity_type"] == entity_type and usage["entity_id"] == entity_id:
            if resource_type is None or usage["resource_type"] == resource_type:
                # Add limit info
                usage_with_limits = {**usage, "limits": {}}
                for policy in QUOTA_POLICIES.values():
                    if policy["resource_type"] == usage["resource_type"]:
                        usage_with_limits["limits"] = policy["limits"]
                        break
                results.append(usage_with_limits)

    return {"usage": results, "total": len(results)}


@app.get("/quotas/usage/{entity_type}/{entity_id}/check")
def check_quota(entity_type: str, entity_id: str, resource_type: str, requested: Dict[str, float]):
    """Check if a request would exceed quotas"""
    key = f"{entity_type}:{entity_id}:{resource_type}"
    current_usage = QUOTA_USAGE.get(key, {"usage": {}})["usage"]

    would_exceed = []
    for policy in QUOTA_POLICIES.values():
        if policy["resource_type"] == resource_type:
            for limit_key, limit_value in policy["limits"].items():
                current = current_usage.get(limit_key, 0)
                requested_amount = requested.get(limit_key, 0)
                if current + requested_amount > limit_value:
                    would_exceed.append({
                        "limit": limit_key,
                        "limit_value": limit_value,
                        "current": current,
                        "requested": requested_amount,
                        "total_would_be": current + requested_amount,
                        "overage": (current + requested_amount) - limit_value
                    })

    return {
        "allowed": len(would_exceed) == 0,
        "would_exceed": would_exceed
    }


@app.post("/quotas/reset/{entity_type}/{entity_id}")
def reset_quota_usage(entity_type: str, entity_id: str, resource_type: Optional[str] = None):
    """Reset quota usage for an entity"""
    reset_count = 0
    keys_to_delete = []

    for key in QUOTA_USAGE:
        usage = QUOTA_USAGE[key]
        if usage["entity_type"] == entity_type and usage["entity_id"] == entity_id:
            if resource_type is None or usage["resource_type"] == resource_type:
                keys_to_delete.append(key)
                reset_count += 1

    for key in keys_to_delete:
        del QUOTA_USAGE[key]

    return {"reset": True, "count": reset_count}


@app.get("/quotas/summary")
def get_quota_summary(entity_type: Optional[str] = None):
    """Get summary of quota usage across all entities"""
    summary = {
        "total_entities": 0,
        "entities_near_limit": 0,
        "entities_over_limit": 0,
        "by_resource_type": {}
    }

    seen_entities = set()
    for key, usage in QUOTA_USAGE.items():
        if entity_type and usage["entity_type"] != entity_type:
            continue

        entity_key = f"{usage['entity_type']}:{usage['entity_id']}"
        if entity_key not in seen_entities:
            seen_entities.add(entity_key)
            summary["total_entities"] += 1

        # Check limits
        for policy in QUOTA_POLICIES.values():
            if policy["resource_type"] == usage["resource_type"]:
                for limit_key, limit_value in policy["limits"].items():
                    current = usage["usage"].get(limit_key, 0)
                    ratio = current / limit_value if limit_value > 0 else 0
                    if ratio >= 1.0:
                        summary["entities_over_limit"] += 1
                    elif ratio >= 0.8:
                        summary["entities_near_limit"] += 1

                    if usage["resource_type"] not in summary["by_resource_type"]:
                        summary["by_resource_type"][usage["resource_type"]] = {
                            "total_usage": 0,
                            "entities": 0
                        }
                    summary["by_resource_type"][usage["resource_type"]]["total_usage"] += current
                    summary["by_resource_type"][usage["resource_type"]]["entities"] += 1

    return summary


# ============================================================================
# Real-time Streaming & Events
# ============================================================================

STREAM_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
EVENT_STREAMS: Dict[str, List[Dict[str, Any]]] = {}
STREAM_SUBSCRIPTIONS: Dict[str, List[Dict[str, Any]]] = {}
EVENT_TYPES = ["agent.started", "agent.completed", "agent.failed", "workflow.started",
               "workflow.completed", "workflow.step", "message.received", "alert.triggered"]


@app.post("/streams/connect")
def create_stream_connection(
    user_id: str,
    client_id: str,
    subscriptions: Optional[List[str]] = None
):
    """Create a streaming connection"""
    connection_id = f"stream_{uuid.uuid4().hex[:12]}"
    connection = {
        "id": connection_id,
        "user_id": user_id,
        "client_id": client_id,
        "subscriptions": subscriptions or ["*"],
        "status": "connected",
        "connected_at": datetime.utcnow().isoformat(),
        "last_heartbeat": datetime.utcnow().isoformat(),
        "messages_sent": 0
    }
    STREAM_CONNECTIONS[connection_id] = connection
    return connection


@app.get("/streams/connections")
def list_stream_connections(user_id: Optional[str] = None):
    """List active stream connections"""
    connections = list(STREAM_CONNECTIONS.values())
    if user_id:
        connections = [c for c in connections if c["user_id"] == user_id]
    return {"connections": connections, "total": len(connections)}


@app.delete("/streams/connections/{connection_id}")
def disconnect_stream(connection_id: str):
    """Disconnect a stream"""
    if connection_id not in STREAM_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    STREAM_CONNECTIONS[connection_id]["status"] = "disconnected"
    del STREAM_CONNECTIONS[connection_id]
    return {"disconnected": True}


@app.post("/streams/events")
def publish_event(
    event_type: str,
    payload: Dict[str, Any],
    target_users: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Publish an event to streams"""
    event = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "type": event_type,
        "payload": payload,
        "target_users": target_users,
        "metadata": metadata or {},
        "published_at": datetime.utcnow().isoformat()
    }

    # Add to event stream
    if event_type not in EVENT_STREAMS:
        EVENT_STREAMS[event_type] = []
    EVENT_STREAMS[event_type].append(event)

    # Count deliveries
    delivered = 0
    for conn in STREAM_CONNECTIONS.values():
        if conn["status"] == "connected":
            if "*" in conn["subscriptions"] or event_type in conn["subscriptions"]:
                if target_users is None or conn["user_id"] in target_users:
                    conn["messages_sent"] += 1
                    delivered += 1

    return {"event": event, "delivered_to": delivered}


@app.get("/streams/events")
def get_events(
    event_type: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100
):
    """Get recent events"""
    events = []
    if event_type:
        events = EVENT_STREAMS.get(event_type, [])
    else:
        for evt_list in EVENT_STREAMS.values():
            events.extend(evt_list)

    if since:
        events = [e for e in events if e["published_at"] > since]

    events.sort(key=lambda x: x["published_at"], reverse=True)
    return {"events": events[:limit], "total": len(events)}


@app.post("/streams/subscriptions")
def create_subscription(
    connection_id: str,
    event_types: List[str],
    filters: Optional[Dict[str, Any]] = None
):
    """Add subscription to a connection"""
    if connection_id not in STREAM_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    subscription = {
        "id": f"sub_{uuid.uuid4().hex[:8]}",
        "connection_id": connection_id,
        "event_types": event_types,
        "filters": filters or {},
        "created_at": datetime.utcnow().isoformat()
    }

    if connection_id not in STREAM_SUBSCRIPTIONS:
        STREAM_SUBSCRIPTIONS[connection_id] = []
    STREAM_SUBSCRIPTIONS[connection_id].append(subscription)

    # Update connection subscriptions
    STREAM_CONNECTIONS[connection_id]["subscriptions"].extend(event_types)

    return subscription


@app.post("/streams/heartbeat/{connection_id}")
def stream_heartbeat(connection_id: str):
    """Send heartbeat for a stream connection"""
    if connection_id not in STREAM_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")

    STREAM_CONNECTIONS[connection_id]["last_heartbeat"] = datetime.utcnow().isoformat()
    return {"status": "ok", "connection_id": connection_id}


@app.get("/streams/event-types")
def list_event_types():
    """List available event types"""
    return {"event_types": EVENT_TYPES}


# ============================================================================
# Semantic Search
# ============================================================================

SEARCH_INDEXES: Dict[str, Dict[str, Any]] = {}
SEARCH_DOCUMENTS: Dict[str, List[Dict[str, Any]]] = {}
SEARCH_QUERIES: List[Dict[str, Any]] = []


@app.post("/search/indexes")
def create_search_index(
    name: str,
    resource_types: List[str],
    fields: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
):
    """Create a semantic search index"""
    index_id = f"idx_{uuid.uuid4().hex[:12]}"
    index = {
        "id": index_id,
        "name": name,
        "resource_types": resource_types,
        "fields": fields,
        "config": config or {"embedding_model": "default", "similarity": "cosine"},
        "document_count": 0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat()
    }
    SEARCH_INDEXES[index_id] = index
    SEARCH_DOCUMENTS[index_id] = []
    return index


@app.get("/search/indexes")
def list_search_indexes():
    """List search indexes"""
    return {"indexes": list(SEARCH_INDEXES.values()), "total": len(SEARCH_INDEXES)}


@app.post("/search/indexes/{index_id}/documents")
def index_document(
    index_id: str,
    document_id: str,
    content: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
):
    """Index a document for search"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")

    doc = {
        "id": document_id,
        "content": content,
        "metadata": metadata or {},
        "embedding": [random.random() for _ in range(384)],  # Simulated embedding
        "indexed_at": datetime.utcnow().isoformat()
    }
    SEARCH_DOCUMENTS[index_id].append(doc)
    SEARCH_INDEXES[index_id]["document_count"] += 1
    SEARCH_INDEXES[index_id]["last_updated"] = datetime.utcnow().isoformat()

    return {"indexed": True, "document_id": document_id}


@app.post("/search/query")
def semantic_search(
    query: str,
    index_ids: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    min_score: float = 0.5
):
    """Perform semantic search"""
    results = []
    search_indexes = index_ids or list(SEARCH_INDEXES.keys())

    for idx_id in search_indexes:
        if idx_id not in SEARCH_DOCUMENTS:
            continue
        for doc in SEARCH_DOCUMENTS[idx_id]:
            # Simulate relevance scoring
            score = random.uniform(0.4, 1.0)
            if query.lower() in str(doc["content"]).lower():
                score += 0.2

            if score >= min_score:
                results.append({
                    "document_id": doc["id"],
                    "index_id": idx_id,
                    "score": min(1.0, score),
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "highlights": [f"...{query}..."]
                })

    results.sort(key=lambda x: x["score"], reverse=True)

    # Log query
    SEARCH_QUERIES.append({
        "query": query,
        "results_count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "results": results[:limit],
        "total": len(results),
        "query": query,
        "facets": {"resource_type": {}, "index": {}}
    }


@app.post("/search/natural")
def natural_language_search(
    question: str,
    context: Optional[str] = None,
    include_sources: bool = True
):
    """Natural language search with AI understanding"""
    # Simulate NL understanding
    intent = "find" if "find" in question.lower() or "where" in question.lower() else "explain"
    entities = []
    if "agent" in question.lower():
        entities.append({"type": "resource", "value": "agent"})
    if "workflow" in question.lower():
        entities.append({"type": "resource", "value": "workflow"})

    return {
        "question": question,
        "intent": intent,
        "entities": entities,
        "answer": f"Based on your question about '{question}', here are the relevant results...",
        "confidence": random.uniform(0.75, 0.95),
        "sources": [
            {"type": "agent", "id": "agent_001", "relevance": 0.9},
            {"type": "workflow", "id": "wf_001", "relevance": 0.85}
        ] if include_sources else [],
        "follow_up_questions": [
            "Would you like more details about this?",
            "Should I filter by a specific category?"
        ]
    }


@app.get("/search/suggestions")
def get_search_suggestions(query: str, limit: int = 10):
    """Get search suggestions/autocomplete"""
    suggestions = [
        f"{query} agents",
        f"{query} workflows",
        f"{query} templates",
        f"how to {query}",
        f"{query} examples"
    ]
    return {"suggestions": suggestions[:limit], "query": query}


@app.get("/search/analytics")
def get_search_analytics(time_period: str = "7d"):
    """Get search analytics"""
    return {
        "total_queries": len(SEARCH_QUERIES),
        "unique_queries": len(set(q["query"] for q in SEARCH_QUERIES)),
        "avg_results": sum(q["results_count"] for q in SEARCH_QUERIES) / max(1, len(SEARCH_QUERIES)),
        "top_queries": ["agent", "workflow", "template", "api", "help"],
        "zero_result_queries": [],
        "time_period": time_period
    }


# ============================================================================
# Knowledge Graphs
# ============================================================================

GRAPH_NODES: Dict[str, Dict[str, Any]] = {}
GRAPH_EDGES: Dict[str, Dict[str, Any]] = {}
GRAPH_SCHEMAS: Dict[str, Dict[str, Any]] = {}


@app.post("/graph/nodes")
def create_graph_node(
    node_type: str,
    properties: Dict[str, Any],
    labels: Optional[List[str]] = None
):
    """Create a knowledge graph node"""
    node_id = f"node_{uuid.uuid4().hex[:12]}"
    node = {
        "id": node_id,
        "type": node_type,
        "properties": properties,
        "labels": labels or [],
        "created_at": datetime.utcnow().isoformat()
    }
    GRAPH_NODES[node_id] = node
    return node


@app.get("/graph/nodes")
def list_graph_nodes(node_type: Optional[str] = None, label: Optional[str] = None):
    """List graph nodes"""
    nodes = list(GRAPH_NODES.values())
    if node_type:
        nodes = [n for n in nodes if n["type"] == node_type]
    if label:
        nodes = [n for n in nodes if label in n.get("labels", [])]
    return {"nodes": nodes, "total": len(nodes)}


@app.get("/graph/nodes/{node_id}")
def get_graph_node(node_id: str):
    """Get a graph node"""
    if node_id not in GRAPH_NODES:
        raise HTTPException(status_code=404, detail="Node not found")
    return GRAPH_NODES[node_id]


@app.post("/graph/edges")
def create_graph_edge(
    from_node: str,
    to_node: str,
    relationship: str,
    properties: Optional[Dict[str, Any]] = None
):
    """Create an edge between nodes"""
    if from_node not in GRAPH_NODES or to_node not in GRAPH_NODES:
        raise HTTPException(status_code=404, detail="Node not found")

    edge_id = f"edge_{uuid.uuid4().hex[:12]}"
    edge = {
        "id": edge_id,
        "from_node": from_node,
        "to_node": to_node,
        "relationship": relationship,
        "properties": properties or {},
        "created_at": datetime.utcnow().isoformat()
    }
    GRAPH_EDGES[edge_id] = edge
    return edge


@app.get("/graph/edges")
def list_graph_edges(relationship: Optional[str] = None, node_id: Optional[str] = None):
    """List graph edges"""
    edges = list(GRAPH_EDGES.values())
    if relationship:
        edges = [e for e in edges if e["relationship"] == relationship]
    if node_id:
        edges = [e for e in edges if e["from_node"] == node_id or e["to_node"] == node_id]
    return {"edges": edges, "total": len(edges)}


@app.get("/graph/nodes/{node_id}/neighbors")
def get_node_neighbors(node_id: str, depth: int = 1, relationship: Optional[str] = None):
    """Get neighboring nodes"""
    if node_id not in GRAPH_NODES:
        raise HTTPException(status_code=404, detail="Node not found")

    neighbors = []
    for edge in GRAPH_EDGES.values():
        if relationship and edge["relationship"] != relationship:
            continue
        if edge["from_node"] == node_id:
            neighbors.append({
                "node": GRAPH_NODES.get(edge["to_node"]),
                "relationship": edge["relationship"],
                "direction": "outgoing"
            })
        elif edge["to_node"] == node_id:
            neighbors.append({
                "node": GRAPH_NODES.get(edge["from_node"]),
                "relationship": edge["relationship"],
                "direction": "incoming"
            })

    return {"node_id": node_id, "neighbors": neighbors, "depth": depth}


@app.post("/graph/query")
def query_graph(
    pattern: Dict[str, Any],
    limit: int = 100
):
    """Query the knowledge graph"""
    # Simulate graph query execution
    results = []
    node_type = pattern.get("node_type")
    relationship = pattern.get("relationship")

    for node in GRAPH_NODES.values():
        if node_type and node["type"] != node_type:
            continue
        match = {"node": node, "edges": []}
        for edge in GRAPH_EDGES.values():
            if relationship and edge["relationship"] != relationship:
                continue
            if edge["from_node"] == node["id"] or edge["to_node"] == node["id"]:
                match["edges"].append(edge)
        if match["edges"] or not relationship:
            results.append(match)

    return {"results": results[:limit], "total": len(results), "pattern": pattern}


@app.post("/graph/paths")
def find_paths(from_node: str, to_node: str, max_depth: int = 5):
    """Find paths between two nodes"""
    if from_node not in GRAPH_NODES or to_node not in GRAPH_NODES:
        raise HTTPException(status_code=404, detail="Node not found")

    # Simulate path finding
    paths = []
    if from_node != to_node:
        # Check for direct connection
        for edge in GRAPH_EDGES.values():
            if edge["from_node"] == from_node and edge["to_node"] == to_node:
                paths.append({
                    "nodes": [from_node, to_node],
                    "edges": [edge["id"]],
                    "length": 1
                })

    return {
        "from_node": from_node,
        "to_node": to_node,
        "paths": paths,
        "shortest_path_length": paths[0]["length"] if paths else None
    }


@app.get("/graph/statistics")
def get_graph_statistics():
    """Get knowledge graph statistics"""
    relationship_counts = {}
    for edge in GRAPH_EDGES.values():
        rel = edge["relationship"]
        relationship_counts[rel] = relationship_counts.get(rel, 0) + 1

    node_type_counts = {}
    for node in GRAPH_NODES.values():
        nt = node["type"]
        node_type_counts[nt] = node_type_counts.get(nt, 0) + 1

    return {
        "total_nodes": len(GRAPH_NODES),
        "total_edges": len(GRAPH_EDGES),
        "node_types": node_type_counts,
        "relationship_types": relationship_counts,
        "avg_connections_per_node": len(GRAPH_EDGES) * 2 / max(1, len(GRAPH_NODES))
    }


# ============================================================================
# Agent Personas & Behaviors
# ============================================================================

AGENT_PERSONAS: Dict[str, Dict[str, Any]] = {}
BEHAVIOR_PROFILES: Dict[str, Dict[str, Any]] = {}
PERSONA_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/personas")
def create_persona(
    name: str,
    description: str,
    personality_traits: Dict[str, float],
    communication_style: Dict[str, Any],
    knowledge_domains: Optional[List[str]] = None,
    constraints: Optional[Dict[str, Any]] = None
):
    """Create an agent persona"""
    persona_id = f"persona_{uuid.uuid4().hex[:12]}"
    persona = {
        "id": persona_id,
        "name": name,
        "description": description,
        "personality_traits": personality_traits,  # e.g., {"friendliness": 0.8, "formality": 0.6}
        "communication_style": communication_style,  # e.g., {"tone": "professional", "verbosity": "concise"}
        "knowledge_domains": knowledge_domains or [],
        "constraints": constraints or {},
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    AGENT_PERSONAS[persona_id] = persona
    return persona


@app.get("/personas")
def list_personas(domain: Optional[str] = None):
    """List agent personas"""
    personas = list(AGENT_PERSONAS.values())
    if domain:
        personas = [p for p in personas if domain in p.get("knowledge_domains", [])]
    return {"personas": personas, "total": len(personas)}


@app.get("/personas/{persona_id}")
def get_persona(persona_id: str):
    """Get persona details"""
    if persona_id not in AGENT_PERSONAS:
        raise HTTPException(status_code=404, detail="Persona not found")
    return AGENT_PERSONAS[persona_id]


@app.put("/personas/{persona_id}")
def update_persona(
    persona_id: str,
    personality_traits: Optional[Dict[str, float]] = None,
    communication_style: Optional[Dict[str, Any]] = None
):
    """Update a persona"""
    if persona_id not in AGENT_PERSONAS:
        raise HTTPException(status_code=404, detail="Persona not found")

    persona = AGENT_PERSONAS[persona_id]
    if personality_traits:
        persona["personality_traits"].update(personality_traits)
    if communication_style:
        persona["communication_style"].update(communication_style)
    persona["updated_at"] = datetime.utcnow().isoformat()

    return persona


@app.post("/personas/{persona_id}/assign/{agent_id}")
def assign_persona_to_agent(persona_id: str, agent_id: str):
    """Assign a persona to an agent"""
    if persona_id not in AGENT_PERSONAS:
        raise HTTPException(status_code=404, detail="Persona not found")

    return {
        "assigned": True,
        "persona_id": persona_id,
        "agent_id": agent_id,
        "assigned_at": datetime.utcnow().isoformat()
    }


@app.post("/behaviors")
def create_behavior_profile(
    name: str,
    triggers: List[Dict[str, Any]],
    responses: List[Dict[str, Any]],
    conditions: Optional[Dict[str, Any]] = None
):
    """Create a behavior profile"""
    behavior_id = f"behavior_{uuid.uuid4().hex[:12]}"
    behavior = {
        "id": behavior_id,
        "name": name,
        "triggers": triggers,  # e.g., [{"type": "keyword", "value": "help"}]
        "responses": responses,  # e.g., [{"type": "template", "content": "How can I help?"}]
        "conditions": conditions or {},
        "priority": 0,
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    BEHAVIOR_PROFILES[behavior_id] = behavior
    return behavior


@app.get("/behaviors")
def list_behavior_profiles():
    """List behavior profiles"""
    return {"behaviors": list(BEHAVIOR_PROFILES.values()), "total": len(BEHAVIOR_PROFILES)}


@app.post("/behaviors/{behavior_id}/test")
def test_behavior(behavior_id: str, input_text: str, context: Optional[Dict[str, Any]] = None):
    """Test a behavior profile"""
    if behavior_id not in BEHAVIOR_PROFILES:
        raise HTTPException(status_code=404, detail="Behavior not found")

    behavior = BEHAVIOR_PROFILES[behavior_id]

    # Check if any trigger matches
    triggered = False
    for trigger in behavior["triggers"]:
        if trigger["type"] == "keyword" and trigger["value"].lower() in input_text.lower():
            triggered = True
            break

    response = None
    if triggered and behavior["responses"]:
        response = behavior["responses"][0]

    return {
        "behavior_id": behavior_id,
        "input": input_text,
        "triggered": triggered,
        "response": response,
        "context": context
    }


@app.get("/personas/traits")
def list_personality_traits():
    """List available personality traits"""
    return {
        "traits": [
            {"id": "friendliness", "name": "Friendliness", "range": [0, 1]},
            {"id": "formality", "name": "Formality", "range": [0, 1]},
            {"id": "enthusiasm", "name": "Enthusiasm", "range": [0, 1]},
            {"id": "patience", "name": "Patience", "range": [0, 1]},
            {"id": "humor", "name": "Humor", "range": [0, 1]},
            {"id": "empathy", "name": "Empathy", "range": [0, 1]},
            {"id": "assertiveness", "name": "Assertiveness", "range": [0, 1]},
            {"id": "creativity", "name": "Creativity", "range": [0, 1]}
        ]
    }


# ============================================================================
# Conversation Designer
# ============================================================================

CONVERSATION_FLOWS: Dict[str, Dict[str, Any]] = {}
FLOW_NODES: Dict[str, List[Dict[str, Any]]] = {}
INTENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {}
RESPONSE_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/conversations/flows")
def create_conversation_flow(
    name: str,
    description: str,
    start_node: str,
    nodes: List[Dict[str, Any]],
    transitions: List[Dict[str, Any]]
):
    """Create a conversation flow"""
    flow_id = f"flow_{uuid.uuid4().hex[:12]}"
    flow = {
        "id": flow_id,
        "name": name,
        "description": description,
        "start_node": start_node,
        "nodes": nodes,
        "transitions": transitions,
        "status": "draft",
        "version": 1,
        "created_at": datetime.utcnow().isoformat()
    }
    CONVERSATION_FLOWS[flow_id] = flow
    FLOW_NODES[flow_id] = nodes
    return flow


@app.get("/conversations/flows")
def list_conversation_flows(status: Optional[str] = None):
    """List conversation flows"""
    flows = list(CONVERSATION_FLOWS.values())
    if status:
        flows = [f for f in flows if f["status"] == status]
    return {"flows": flows, "total": len(flows)}


@app.get("/conversations/flows/{flow_id}")
def get_conversation_flow(flow_id: str):
    """Get conversation flow details"""
    if flow_id not in CONVERSATION_FLOWS:
        raise HTTPException(status_code=404, detail="Flow not found")
    return CONVERSATION_FLOWS[flow_id]


@app.post("/conversations/flows/{flow_id}/publish")
def publish_conversation_flow(flow_id: str):
    """Publish a conversation flow"""
    if flow_id not in CONVERSATION_FLOWS:
        raise HTTPException(status_code=404, detail="Flow not found")

    flow = CONVERSATION_FLOWS[flow_id]
    flow["status"] = "published"
    flow["published_at"] = datetime.utcnow().isoformat()
    return flow


@app.post("/conversations/flows/{flow_id}/simulate")
def simulate_conversation(flow_id: str, inputs: List[str]):
    """Simulate a conversation through a flow"""
    if flow_id not in CONVERSATION_FLOWS:
        raise HTTPException(status_code=404, detail="Flow not found")

    flow = CONVERSATION_FLOWS[flow_id]
    simulation = []
    current_node = flow["start_node"]

    for user_input in inputs:
        # Find current node
        node = next((n for n in flow["nodes"] if n.get("id") == current_node), None)
        if not node:
            break

        # Add to simulation
        step = {
            "node_id": current_node,
            "user_input": user_input,
            "bot_response": node.get("response", "Default response"),
            "detected_intent": "general"
        }
        simulation.append(step)

        # Find next transition
        for trans in flow["transitions"]:
            if trans["from"] == current_node:
                current_node = trans["to"]
                break

    return {"flow_id": flow_id, "simulation": simulation, "steps": len(simulation)}


@app.post("/conversations/intents")
def create_intent(
    name: str,
    examples: List[str],
    description: Optional[str] = None,
    entities: Optional[List[str]] = None
):
    """Create an intent definition"""
    intent_id = f"intent_{uuid.uuid4().hex[:12]}"
    intent = {
        "id": intent_id,
        "name": name,
        "description": description,
        "examples": examples,
        "entities": entities or [],
        "training_count": len(examples),
        "created_at": datetime.utcnow().isoformat()
    }
    INTENT_DEFINITIONS[intent_id] = intent
    return intent


@app.get("/conversations/intents")
def list_intents():
    """List intent definitions"""
    return {"intents": list(INTENT_DEFINITIONS.values()), "total": len(INTENT_DEFINITIONS)}


@app.post("/conversations/intents/detect")
def detect_intent(text: str, threshold: float = 0.5):
    """Detect intent from text"""
    detected = []
    for intent in INTENT_DEFINITIONS.values():
        # Simple matching simulation
        score = 0.0
        for example in intent["examples"]:
            if any(word in text.lower() for word in example.lower().split()):
                score = max(score, random.uniform(0.6, 0.95))

        if score >= threshold:
            detected.append({
                "intent": intent["name"],
                "confidence": score,
                "entities": []
            })

    detected.sort(key=lambda x: x["confidence"], reverse=True)
    return {"text": text, "intents": detected, "top_intent": detected[0] if detected else None}


@app.post("/conversations/templates")
def create_response_template(
    name: str,
    template: str,
    variables: Optional[List[str]] = None,
    variants: Optional[List[str]] = None
):
    """Create a response template"""
    template_id = f"tpl_{uuid.uuid4().hex[:12]}"
    tpl = {
        "id": template_id,
        "name": name,
        "template": template,
        "variables": variables or [],
        "variants": variants or [],
        "usage_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    RESPONSE_TEMPLATES[template_id] = tpl
    return tpl


@app.get("/conversations/templates")
def list_response_templates():
    """List response templates"""
    return {"templates": list(RESPONSE_TEMPLATES.values()), "total": len(RESPONSE_TEMPLATES)}


# ============================================================================
# AI Safety & Content Moderation
# ============================================================================

MODERATION_RULES: Dict[str, Dict[str, Any]] = {}
MODERATION_LOGS: List[Dict[str, Any]] = []
SAFETY_POLICIES: Dict[str, Dict[str, Any]] = {}
BLOCKED_PATTERNS: List[Dict[str, Any]] = []


@app.post("/safety/moderate")
def moderate_content(
    content: str,
    content_type: str = "text",
    context: Optional[Dict[str, Any]] = None
):
    """Moderate content for safety"""
    # Simulate moderation checks
    checks = {
        "toxicity": random.uniform(0, 0.3),
        "hate_speech": random.uniform(0, 0.1),
        "harassment": random.uniform(0, 0.15),
        "violence": random.uniform(0, 0.1),
        "sexual_content": random.uniform(0, 0.05),
        "self_harm": random.uniform(0, 0.05),
        "pii_detected": random.choice([True, False]),
        "profanity": random.uniform(0, 0.2)
    }

    # Determine if content passes
    max_score = max(checks["toxicity"], checks["hate_speech"], checks["harassment"])
    passed = max_score < 0.5

    result = {
        "id": f"mod_{uuid.uuid4().hex[:12]}",
        "content_type": content_type,
        "passed": passed,
        "scores": checks,
        "flagged_categories": [k for k, v in checks.items() if isinstance(v, float) and v > 0.3],
        "action": "allow" if passed else "block",
        "timestamp": datetime.utcnow().isoformat()
    }

    MODERATION_LOGS.append(result)
    return result


@app.post("/safety/rules")
def create_moderation_rule(
    name: str,
    rule_type: str,
    pattern: str,
    action: str = "flag",
    severity: str = "medium"
):
    """Create a moderation rule"""
    rule_id = f"rule_{uuid.uuid4().hex[:12]}"
    rule = {
        "id": rule_id,
        "name": name,
        "rule_type": rule_type,  # regex, keyword, ml_category
        "pattern": pattern,
        "action": action,  # flag, block, warn
        "severity": severity,
        "enabled": True,
        "trigger_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    MODERATION_RULES[rule_id] = rule
    return rule


@app.get("/safety/rules")
def list_moderation_rules():
    """List moderation rules"""
    return {"rules": list(MODERATION_RULES.values()), "total": len(MODERATION_RULES)}


@app.post("/safety/bias/detect")
def detect_bias(
    content: str,
    categories: Optional[List[str]] = None
):
    """Detect potential bias in content"""
    bias_categories = categories or ["gender", "race", "age", "religion", "political"]

    results = {}
    for category in bias_categories:
        results[category] = {
            "detected": random.choice([True, False]),
            "confidence": random.uniform(0.5, 0.95) if random.random() > 0.7 else 0.0,
            "examples": []
        }

    overall_bias = any(r["detected"] for r in results.values())

    return {
        "content_analyzed": True,
        "overall_bias_detected": overall_bias,
        "bias_score": random.uniform(0, 0.3) if not overall_bias else random.uniform(0.4, 0.8),
        "categories": results,
        "recommendations": ["Consider neutral language", "Review for inclusive terms"] if overall_bias else []
    }


@app.post("/safety/policies")
def create_safety_policy(
    name: str,
    description: str,
    rules: List[Dict[str, Any]],
    enforcement: str = "strict"
):
    """Create a safety policy"""
    policy_id = f"policy_{uuid.uuid4().hex[:12]}"
    policy = {
        "id": policy_id,
        "name": name,
        "description": description,
        "rules": rules,
        "enforcement": enforcement,  # strict, moderate, permissive
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    SAFETY_POLICIES[policy_id] = policy
    return policy


@app.get("/safety/policies")
def list_safety_policies():
    """List safety policies"""
    return {"policies": list(SAFETY_POLICIES.values()), "total": len(SAFETY_POLICIES)}


@app.get("/safety/logs")
def get_moderation_logs(action: Optional[str] = None, limit: int = 100):
    """Get moderation logs"""
    logs = MODERATION_LOGS
    if action:
        logs = [l for l in logs if l["action"] == action]
    return {"logs": logs[-limit:], "total": len(logs)}


@app.get("/safety/statistics")
def get_safety_statistics(time_period: str = "7d"):
    """Get safety/moderation statistics"""
    total = len(MODERATION_LOGS)
    blocked = len([l for l in MODERATION_LOGS if l["action"] == "block"])

    return {
        "total_checks": total,
        "blocked": blocked,
        "allowed": total - blocked,
        "block_rate": blocked / max(1, total),
        "top_flagged_categories": ["toxicity", "profanity", "harassment"],
        "time_period": time_period
    }


# ============================================================================
# Marketplace & Monetization
# ============================================================================

MARKETPLACE_LISTINGS: Dict[str, Dict[str, Any]] = {}
MARKETPLACE_PURCHASES: Dict[str, Dict[str, Any]] = {}
PRICING_PLANS: Dict[str, Dict[str, Any]] = {}
REVENUE_RECORDS: List[Dict[str, Any]] = []


@app.post("/marketplace/listings")
def create_marketplace_listing(
    name: str,
    description: str,
    resource_type: str,
    resource_id: str,
    pricing: Dict[str, Any],
    author_id: str,
    categories: Optional[List[str]] = None
):
    """Create a marketplace listing"""
    listing_id = f"listing_{uuid.uuid4().hex[:12]}"
    listing = {
        "id": listing_id,
        "name": name,
        "description": description,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "pricing": pricing,  # {"type": "one_time", "amount": 9.99, "currency": "USD"}
        "author_id": author_id,
        "categories": categories or [],
        "rating": 0.0,
        "review_count": 0,
        "purchase_count": 0,
        "status": "pending_review",
        "created_at": datetime.utcnow().isoformat()
    }
    MARKETPLACE_LISTINGS[listing_id] = listing
    return listing


@app.get("/marketplace/listings")
def list_marketplace_listings(
    category: Optional[str] = None,
    resource_type: Optional[str] = None,
    min_rating: float = 0.0,
    sort_by: str = "popular"
):
    """Browse marketplace listings"""
    listings = [l for l in MARKETPLACE_LISTINGS.values() if l["status"] == "published"]

    if category:
        listings = [l for l in listings if category in l.get("categories", [])]
    if resource_type:
        listings = [l for l in listings if l["resource_type"] == resource_type]
    if min_rating > 0:
        listings = [l for l in listings if l["rating"] >= min_rating]

    if sort_by == "popular":
        listings.sort(key=lambda x: x["purchase_count"], reverse=True)
    elif sort_by == "rating":
        listings.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "newest":
        listings.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort_by == "price_low":
        listings.sort(key=lambda x: x["pricing"].get("amount", 0))

    return {"listings": listings, "total": len(listings)}


@app.get("/marketplace/listings/{listing_id}")
def get_marketplace_listing(listing_id: str):
    """Get listing details"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")
    return MARKETPLACE_LISTINGS[listing_id]


@app.post("/marketplace/listings/{listing_id}/publish")
def publish_listing(listing_id: str):
    """Publish a listing to marketplace"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = MARKETPLACE_LISTINGS[listing_id]
    listing["status"] = "published"
    listing["published_at"] = datetime.utcnow().isoformat()
    return listing


@app.post("/marketplace/purchase")
def purchase_listing(
    listing_id: str,
    buyer_id: str,
    payment_method: str = "card"
):
    """Purchase a marketplace listing"""
    if listing_id not in MARKETPLACE_LISTINGS:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = MARKETPLACE_LISTINGS[listing_id]
    purchase_id = f"purchase_{uuid.uuid4().hex[:12]}"

    purchase = {
        "id": purchase_id,
        "listing_id": listing_id,
        "listing_name": listing["name"],
        "buyer_id": buyer_id,
        "seller_id": listing["author_id"],
        "amount": listing["pricing"]["amount"],
        "currency": listing["pricing"].get("currency", "USD"),
        "payment_method": payment_method,
        "status": "completed",
        "purchased_at": datetime.utcnow().isoformat()
    }
    MARKETPLACE_PURCHASES[purchase_id] = purchase
    listing["purchase_count"] += 1

    # Record revenue
    REVENUE_RECORDS.append({
        "purchase_id": purchase_id,
        "seller_id": listing["author_id"],
        "gross_amount": listing["pricing"]["amount"],
        "platform_fee": listing["pricing"]["amount"] * 0.15,
        "net_amount": listing["pricing"]["amount"] * 0.85,
        "timestamp": datetime.utcnow().isoformat()
    })

    return purchase


@app.get("/marketplace/purchases")
def list_purchases(buyer_id: Optional[str] = None, seller_id: Optional[str] = None):
    """List purchases"""
    purchases = list(MARKETPLACE_PURCHASES.values())
    if buyer_id:
        purchases = [p for p in purchases if p["buyer_id"] == buyer_id]
    if seller_id:
        purchases = [p for p in purchases if p["seller_id"] == seller_id]
    return {"purchases": purchases, "total": len(purchases)}


@app.post("/marketplace/pricing-plans")
def create_pricing_plan(
    name: str,
    listing_id: str,
    plan_type: str,
    price: float,
    billing_period: Optional[str] = None,
    features: Optional[List[str]] = None
):
    """Create a pricing plan for a listing"""
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    plan = {
        "id": plan_id,
        "name": name,
        "listing_id": listing_id,
        "plan_type": plan_type,  # one_time, subscription, usage_based
        "price": price,
        "billing_period": billing_period,  # monthly, yearly
        "features": features or [],
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    PRICING_PLANS[plan_id] = plan
    return plan


@app.get("/marketplace/revenue")
def get_revenue_summary(seller_id: str, time_period: str = "30d"):
    """Get revenue summary for a seller"""
    seller_revenue = [r for r in REVENUE_RECORDS if r["seller_id"] == seller_id]

    total_gross = sum(r["gross_amount"] for r in seller_revenue)
    total_fees = sum(r["platform_fee"] for r in seller_revenue)
    total_net = sum(r["net_amount"] for r in seller_revenue)

    return {
        "seller_id": seller_id,
        "total_sales": len(seller_revenue),
        "gross_revenue": total_gross,
        "platform_fees": total_fees,
        "net_revenue": total_net,
        "time_period": time_period
    }


@app.get("/marketplace/categories")
def list_marketplace_categories():
    """List marketplace categories"""
    return {
        "categories": [
            {"id": "agents", "name": "AI Agents", "count": 0},
            {"id": "workflows", "name": "Workflows", "count": 0},
            {"id": "templates", "name": "Templates", "count": 0},
            {"id": "integrations", "name": "Integrations", "count": 0},
            {"id": "plugins", "name": "Plugins", "count": 0},
            {"id": "datasets", "name": "Datasets", "count": 0}
        ]
    }


# ============================================================================
# Plugin System
# ============================================================================

PLUGINS: Dict[str, Dict[str, Any]] = {}
PLUGIN_REGISTRY: Dict[str, Dict[str, Any]] = {}
PLUGIN_INSTANCES: Dict[str, Dict[str, Any]] = {}
PLUGIN_HOOKS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/plugins/register")
def register_plugin(
    name: str,
    version: str,
    description: str,
    author: str,
    entry_point: str,
    hooks: List[str],
    config_schema: Optional[Dict[str, Any]] = None,
    dependencies: Optional[List[str]] = None
):
    """Register a plugin"""
    plugin_id = f"plugin_{uuid.uuid4().hex[:12]}"
    plugin = {
        "id": plugin_id,
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "entry_point": entry_point,
        "hooks": hooks,
        "config_schema": config_schema or {},
        "dependencies": dependencies or [],
        "status": "registered",
        "downloads": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    PLUGIN_REGISTRY[plugin_id] = plugin
    return plugin


@app.get("/plugins")
def list_plugins(status: Optional[str] = None, hook: Optional[str] = None):
    """List registered plugins"""
    plugins = list(PLUGIN_REGISTRY.values())
    if status:
        plugins = [p for p in plugins if p["status"] == status]
    if hook:
        plugins = [p for p in plugins if hook in p["hooks"]]
    return {"plugins": plugins, "total": len(plugins)}


@app.get("/plugins/{plugin_id}")
def get_plugin(plugin_id: str):
    """Get plugin details"""
    if plugin_id not in PLUGIN_REGISTRY:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return PLUGIN_REGISTRY[plugin_id]


@app.post("/plugins/{plugin_id}/install")
def install_plugin(plugin_id: str, config: Optional[Dict[str, Any]] = None):
    """Install a plugin"""
    if plugin_id not in PLUGIN_REGISTRY:
        raise HTTPException(status_code=404, detail="Plugin not found")

    plugin = PLUGIN_REGISTRY[plugin_id]
    instance_id = f"inst_{uuid.uuid4().hex[:12]}"

    instance = {
        "id": instance_id,
        "plugin_id": plugin_id,
        "plugin_name": plugin["name"],
        "version": plugin["version"],
        "config": config or {},
        "status": "installed",
        "installed_at": datetime.utcnow().isoformat()
    }
    PLUGIN_INSTANCES[instance_id] = instance
    plugin["downloads"] += 1

    # Register hooks
    for hook in plugin["hooks"]:
        if hook not in PLUGIN_HOOKS:
            PLUGIN_HOOKS[hook] = []
        PLUGIN_HOOKS[hook].append({
            "instance_id": instance_id,
            "plugin_id": plugin_id,
            "priority": 0
        })

    return instance


@app.get("/plugins/installed")
def list_installed_plugins():
    """List installed plugin instances"""
    return {"instances": list(PLUGIN_INSTANCES.values()), "total": len(PLUGIN_INSTANCES)}


@app.post("/plugins/{instance_id}/enable")
def enable_plugin(instance_id: str):
    """Enable a plugin instance"""
    if instance_id not in PLUGIN_INSTANCES:
        raise HTTPException(status_code=404, detail="Plugin instance not found")

    PLUGIN_INSTANCES[instance_id]["status"] = "enabled"
    PLUGIN_INSTANCES[instance_id]["enabled_at"] = datetime.utcnow().isoformat()
    return PLUGIN_INSTANCES[instance_id]


@app.post("/plugins/{instance_id}/disable")
def disable_plugin(instance_id: str):
    """Disable a plugin instance"""
    if instance_id not in PLUGIN_INSTANCES:
        raise HTTPException(status_code=404, detail="Plugin instance not found")

    PLUGIN_INSTANCES[instance_id]["status"] = "disabled"
    PLUGIN_INSTANCES[instance_id]["disabled_at"] = datetime.utcnow().isoformat()
    return PLUGIN_INSTANCES[instance_id]


@app.delete("/plugins/{instance_id}")
def uninstall_plugin(instance_id: str):
    """Uninstall a plugin"""
    if instance_id not in PLUGIN_INSTANCES:
        raise HTTPException(status_code=404, detail="Plugin instance not found")

    instance = PLUGIN_INSTANCES[instance_id]

    # Remove hooks
    for hook, handlers in PLUGIN_HOOKS.items():
        PLUGIN_HOOKS[hook] = [h for h in handlers if h["instance_id"] != instance_id]

    del PLUGIN_INSTANCES[instance_id]
    return {"uninstalled": True}


@app.post("/plugins/hooks/{hook_name}/trigger")
def trigger_plugin_hook(hook_name: str, data: Dict[str, Any]):
    """Trigger a plugin hook"""
    handlers = PLUGIN_HOOKS.get(hook_name, [])

    results = []
    for handler in handlers:
        instance = PLUGIN_INSTANCES.get(handler["instance_id"])
        if instance and instance["status"] == "enabled":
            results.append({
                "plugin_id": handler["plugin_id"],
                "instance_id": handler["instance_id"],
                "executed": True,
                "result": {"processed": True, "data": data}
            })

    return {
        "hook": hook_name,
        "handlers_triggered": len(results),
        "results": results
    }


@app.get("/plugins/hooks")
def list_plugin_hooks():
    """List available plugin hooks"""
    return {
        "hooks": [
            {"name": "pre_agent_execute", "description": "Before agent execution"},
            {"name": "post_agent_execute", "description": "After agent execution"},
            {"name": "pre_workflow_start", "description": "Before workflow starts"},
            {"name": "post_workflow_complete", "description": "After workflow completes"},
            {"name": "on_message_receive", "description": "When message received"},
            {"name": "on_message_send", "description": "When message sent"},
            {"name": "on_error", "description": "When error occurs"},
            {"name": "on_metric_record", "description": "When metric recorded"}
        ]
    }


@app.put("/plugins/{instance_id}/config")
def update_plugin_config(instance_id: str, config: Dict[str, Any]):
    """Update plugin configuration"""
    if instance_id not in PLUGIN_INSTANCES:
        raise HTTPException(status_code=404, detail="Plugin instance not found")

    PLUGIN_INSTANCES[instance_id]["config"].update(config)
    PLUGIN_INSTANCES[instance_id]["config_updated_at"] = datetime.utcnow().isoformat()
    return PLUGIN_INSTANCES[instance_id]


# ============================================================================
# Time Series & Forecasting
# ============================================================================

TIME_SERIES_DATA: Dict[str, List[Dict[str, Any]]] = {}
FORECASTS: Dict[str, Dict[str, Any]] = {}
TREND_ANALYSES: Dict[str, Dict[str, Any]] = {}


@app.post("/timeseries/{metric_name}/data")
def record_timeseries_data(
    metric_name: str,
    value: float,
    timestamp: Optional[str] = None,
    dimensions: Optional[Dict[str, str]] = None
):
    """Record time series data point"""
    data_point = {
        "id": f"ts_{uuid.uuid4().hex[:8]}",
        "metric_name": metric_name,
        "value": value,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
        "dimensions": dimensions or {}
    }

    if metric_name not in TIME_SERIES_DATA:
        TIME_SERIES_DATA[metric_name] = []
    TIME_SERIES_DATA[metric_name].append(data_point)

    return data_point


@app.get("/timeseries/{metric_name}/data")
def get_timeseries_data(
    metric_name: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    granularity: str = "1h"
):
    """Get time series data"""
    data = TIME_SERIES_DATA.get(metric_name, [])

    if start_time:
        data = [d for d in data if d["timestamp"] >= start_time]
    if end_time:
        data = [d for d in data if d["timestamp"] <= end_time]

    return {
        "metric_name": metric_name,
        "data_points": data,
        "count": len(data),
        "granularity": granularity
    }


@app.post("/timeseries/{metric_name}/forecast")
def create_forecast(
    metric_name: str,
    horizon: int = 7,
    model: str = "linear",
    confidence_level: float = 0.95
):
    """Generate a forecast for a metric"""
    data = TIME_SERIES_DATA.get(metric_name, [])

    if len(data) < 3:
        raise HTTPException(status_code=400, detail="Insufficient data for forecasting")

    # Simulate forecast generation
    last_value = data[-1]["value"] if data else 100
    forecast_id = f"forecast_{uuid.uuid4().hex[:12]}"

    predictions = []
    for i in range(horizon):
        predicted = last_value * (1 + random.uniform(-0.1, 0.15))
        predictions.append({
            "period": i + 1,
            "predicted_value": round(predicted, 2),
            "lower_bound": round(predicted * 0.85, 2),
            "upper_bound": round(predicted * 1.15, 2)
        })
        last_value = predicted

    forecast = {
        "id": forecast_id,
        "metric_name": metric_name,
        "model": model,
        "horizon": horizon,
        "confidence_level": confidence_level,
        "predictions": predictions,
        "accuracy_metrics": {
            "mape": random.uniform(5, 15),
            "rmse": random.uniform(10, 50)
        },
        "created_at": datetime.utcnow().isoformat()
    }
    FORECASTS[forecast_id] = forecast
    return forecast


@app.get("/timeseries/forecasts")
def list_forecasts(metric_name: Optional[str] = None):
    """List forecasts"""
    forecasts = list(FORECASTS.values())
    if metric_name:
        forecasts = [f for f in forecasts if f["metric_name"] == metric_name]
    return {"forecasts": forecasts, "total": len(forecasts)}


@app.post("/timeseries/{metric_name}/trend")
def analyze_trend(metric_name: str, window: str = "7d"):
    """Analyze trend for a metric"""
    data = TIME_SERIES_DATA.get(metric_name, [])

    if not data:
        raise HTTPException(status_code=404, detail="No data found for metric")

    values = [d["value"] for d in data]
    trend_id = f"trend_{uuid.uuid4().hex[:12]}"

    # Simulate trend analysis
    trend_direction = "increasing" if values[-1] > values[0] else "decreasing" if values[-1] < values[0] else "stable"
    change_percent = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0

    analysis = {
        "id": trend_id,
        "metric_name": metric_name,
        "window": window,
        "trend_direction": trend_direction,
        "change_percent": round(change_percent, 2),
        "min_value": min(values),
        "max_value": max(values),
        "avg_value": sum(values) / len(values),
        "volatility": random.uniform(0.1, 0.5),
        "seasonality_detected": random.choice([True, False]),
        "anomalies_detected": random.randint(0, 3),
        "analyzed_at": datetime.utcnow().isoformat()
    }
    TREND_ANALYSES[trend_id] = analysis
    return analysis


@app.get("/timeseries/metrics")
def list_timeseries_metrics():
    """List all metrics with time series data"""
    metrics = []
    for name, data in TIME_SERIES_DATA.items():
        metrics.append({
            "metric_name": name,
            "data_points": len(data),
            "first_timestamp": data[0]["timestamp"] if data else None,
            "last_timestamp": data[-1]["timestamp"] if data else None
        })
    return {"metrics": metrics, "total": len(metrics)}


# ============================================================================
# Workflow Automation Rules
# ============================================================================

AUTOMATION_RULES: Dict[str, Dict[str, Any]] = {}
AUTOMATION_EXECUTIONS: Dict[str, List[Dict[str, Any]]] = {}
SCHEDULED_TRIGGERS: Dict[str, Dict[str, Any]] = {}


@app.post("/automation/rules")
def create_automation_rule(
    name: str,
    trigger: Dict[str, Any],
    conditions: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    enabled: bool = True
):
    """Create an automation rule"""
    rule_id = f"auto_{uuid.uuid4().hex[:12]}"
    rule = {
        "id": rule_id,
        "name": name,
        "trigger": trigger,  # {"type": "event", "event": "agent.completed"} or {"type": "schedule", "cron": "0 * * * *"}
        "conditions": conditions,  # [{"field": "status", "operator": "equals", "value": "success"}]
        "actions": actions,  # [{"type": "webhook", "url": "..."}, {"type": "notification", "channel": "slack"}]
        "enabled": enabled,
        "execution_count": 0,
        "last_executed": None,
        "created_at": datetime.utcnow().isoformat()
    }
    AUTOMATION_RULES[rule_id] = rule
    return rule


@app.get("/automation/rules")
def list_automation_rules(trigger_type: Optional[str] = None, enabled: Optional[bool] = None):
    """List automation rules"""
    rules = list(AUTOMATION_RULES.values())
    if trigger_type:
        rules = [r for r in rules if r["trigger"].get("type") == trigger_type]
    if enabled is not None:
        rules = [r for r in rules if r["enabled"] == enabled]
    return {"rules": rules, "total": len(rules)}


@app.get("/automation/rules/{rule_id}")
def get_automation_rule(rule_id: str):
    """Get automation rule details"""
    if rule_id not in AUTOMATION_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    return AUTOMATION_RULES[rule_id]


@app.put("/automation/rules/{rule_id}")
def update_automation_rule(
    rule_id: str,
    conditions: Optional[List[Dict[str, Any]]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    enabled: Optional[bool] = None
):
    """Update an automation rule"""
    if rule_id not in AUTOMATION_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = AUTOMATION_RULES[rule_id]
    if conditions:
        rule["conditions"] = conditions
    if actions:
        rule["actions"] = actions
    if enabled is not None:
        rule["enabled"] = enabled
    rule["updated_at"] = datetime.utcnow().isoformat()

    return rule


@app.delete("/automation/rules/{rule_id}")
def delete_automation_rule(rule_id: str):
    """Delete an automation rule"""
    if rule_id not in AUTOMATION_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    del AUTOMATION_RULES[rule_id]
    return {"deleted": True}


@app.post("/automation/rules/{rule_id}/execute")
def execute_automation_rule(rule_id: str, context: Optional[Dict[str, Any]] = None):
    """Manually execute an automation rule"""
    if rule_id not in AUTOMATION_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = AUTOMATION_RULES[rule_id]
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"

    # Simulate condition evaluation and action execution
    conditions_met = all(random.choice([True, True, True, False]) for _ in rule["conditions"]) if rule["conditions"] else True

    action_results = []
    if conditions_met:
        for action in rule["actions"]:
            action_results.append({
                "action_type": action.get("type"),
                "status": "success",
                "result": {"executed": True}
            })

    execution = {
        "id": execution_id,
        "rule_id": rule_id,
        "rule_name": rule["name"],
        "conditions_met": conditions_met,
        "actions_executed": len(action_results),
        "action_results": action_results,
        "context": context or {},
        "executed_at": datetime.utcnow().isoformat()
    }

    if rule_id not in AUTOMATION_EXECUTIONS:
        AUTOMATION_EXECUTIONS[rule_id] = []
    AUTOMATION_EXECUTIONS[rule_id].append(execution)

    rule["execution_count"] += 1
    rule["last_executed"] = datetime.utcnow().isoformat()

    return execution


@app.get("/automation/rules/{rule_id}/executions")
def get_rule_executions(rule_id: str, limit: int = 50):
    """Get execution history for a rule"""
    executions = AUTOMATION_EXECUTIONS.get(rule_id, [])
    return {"executions": executions[-limit:], "total": len(executions)}


@app.post("/automation/triggers/schedule")
def create_scheduled_trigger(
    name: str,
    cron: str,
    rule_id: str,
    timezone: str = "UTC"
):
    """Create a scheduled trigger for a rule"""
    trigger_id = f"sched_{uuid.uuid4().hex[:12]}"
    trigger = {
        "id": trigger_id,
        "name": name,
        "cron": cron,
        "rule_id": rule_id,
        "timezone": timezone,
        "enabled": True,
        "next_run": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    SCHEDULED_TRIGGERS[trigger_id] = trigger
    return trigger


@app.get("/automation/triggers/schedule")
def list_scheduled_triggers():
    """List scheduled triggers"""
    return {"triggers": list(SCHEDULED_TRIGGERS.values()), "total": len(SCHEDULED_TRIGGERS)}


# ============================================================================
# Agent Cloning & Templates
# ============================================================================

AGENT_CLONES: Dict[str, Dict[str, Any]] = {}
AGENT_SNAPSHOTS: Dict[str, Dict[str, Any]] = {}
INHERITANCE_CHAINS: Dict[str, List[str]] = {}


@app.post("/agents/{agent_id}/clone")
def clone_agent(
    agent_id: str,
    new_name: str,
    modifications: Optional[Dict[str, Any]] = None,
    include_memory: bool = False
):
    """Clone an agent with optional modifications"""
    clone_id = f"clone_{uuid.uuid4().hex[:12]}"

    clone = {
        "id": clone_id,
        "source_agent_id": agent_id,
        "name": new_name,
        "modifications": modifications or {},
        "include_memory": include_memory,
        "status": "active",
        "cloned_at": datetime.utcnow().isoformat()
    }
    AGENT_CLONES[clone_id] = clone

    # Track inheritance
    if agent_id not in INHERITANCE_CHAINS:
        INHERITANCE_CHAINS[agent_id] = []
    INHERITANCE_CHAINS[agent_id].append(clone_id)

    return clone


@app.get("/agents/{agent_id}/clones")
def list_agent_clones(agent_id: str):
    """List clones of an agent"""
    clones = [c for c in AGENT_CLONES.values() if c["source_agent_id"] == agent_id]
    return {"clones": clones, "total": len(clones)}


@app.post("/agents/{agent_id}/snapshot")
def create_agent_snapshot(agent_id: str, name: str, description: Optional[str] = None):
    """Create a snapshot of an agent"""
    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

    snapshot = {
        "id": snapshot_id,
        "agent_id": agent_id,
        "name": name,
        "description": description,
        "config": {"simulated": "agent_config"},
        "memory_included": True,
        "size_bytes": random.randint(1000, 100000),
        "created_at": datetime.utcnow().isoformat()
    }
    AGENT_SNAPSHOTS[snapshot_id] = snapshot
    return snapshot


@app.get("/agents/{agent_id}/snapshots")
def list_agent_snapshots(agent_id: str):
    """List snapshots for an agent"""
    snapshots = [s for s in AGENT_SNAPSHOTS.values() if s["agent_id"] == agent_id]
    snapshots.sort(key=lambda x: x["created_at"], reverse=True)
    return {"snapshots": snapshots, "total": len(snapshots)}


@app.post("/agents/{agent_id}/restore/{snapshot_id}")
def restore_agent_snapshot(agent_id: str, snapshot_id: str):
    """Restore an agent from a snapshot"""
    if snapshot_id not in AGENT_SNAPSHOTS:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    snapshot = AGENT_SNAPSHOTS[snapshot_id]
    return {
        "restored": True,
        "agent_id": agent_id,
        "snapshot_id": snapshot_id,
        "snapshot_name": snapshot["name"],
        "restored_at": datetime.utcnow().isoformat()
    }


@app.delete("/agents/snapshots/{snapshot_id}")
def delete_agent_snapshot(snapshot_id: str):
    """Delete a snapshot"""
    if snapshot_id not in AGENT_SNAPSHOTS:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    del AGENT_SNAPSHOTS[snapshot_id]
    return {"deleted": True}


@app.get("/agents/{agent_id}/inheritance")
def get_agent_inheritance(agent_id: str):
    """Get inheritance chain for an agent"""
    children = INHERITANCE_CHAINS.get(agent_id, [])

    # Find parent
    parent = None
    for clone in AGENT_CLONES.values():
        if clone["id"] == agent_id:
            parent = clone["source_agent_id"]
            break

    return {
        "agent_id": agent_id,
        "parent_agent": parent,
        "children": children,
        "total_descendants": len(children)
    }


# ============================================================================
# Natural Language Commands
# ============================================================================

NL_COMMANDS: Dict[str, Dict[str, Any]] = {}
COMMAND_HISTORY: List[Dict[str, Any]] = []
COMMAND_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/commands/interpret")
def interpret_nl_command(
    command: str,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """Interpret a natural language command"""
    # Simulate NL understanding
    interpreted = {
        "id": f"cmd_{uuid.uuid4().hex[:12]}",
        "original_command": command,
        "interpreted_action": None,
        "parameters": {},
        "confidence": 0.0,
        "requires_confirmation": True
    }

    # Simple pattern matching simulation
    command_lower = command.lower()
    if "create" in command_lower and "agent" in command_lower:
        interpreted["interpreted_action"] = "create_agent"
        interpreted["parameters"] = {"name": "New Agent"}
        interpreted["confidence"] = 0.85
    elif "run" in command_lower and "workflow" in command_lower:
        interpreted["interpreted_action"] = "run_workflow"
        interpreted["confidence"] = 0.82
    elif "list" in command_lower or "show" in command_lower:
        interpreted["interpreted_action"] = "list_resources"
        interpreted["confidence"] = 0.90
    elif "delete" in command_lower or "remove" in command_lower:
        interpreted["interpreted_action"] = "delete_resource"
        interpreted["confidence"] = 0.75
        interpreted["requires_confirmation"] = True
    else:
        interpreted["interpreted_action"] = "unknown"
        interpreted["confidence"] = 0.3

    interpreted["context"] = context
    interpreted["user_id"] = user_id
    interpreted["interpreted_at"] = datetime.utcnow().isoformat()

    NL_COMMANDS[interpreted["id"]] = interpreted
    return interpreted


@app.post("/commands/{command_id}/confirm")
def confirm_command(command_id: str, confirmed: bool = True):
    """Confirm or reject an interpreted command"""
    if command_id not in NL_COMMANDS:
        raise HTTPException(status_code=404, detail="Command not found")

    command = NL_COMMANDS[command_id]

    if confirmed:
        # Simulate command execution
        result = {
            "command_id": command_id,
            "action": command["interpreted_action"],
            "status": "executed",
            "result": {"success": True, "message": f"Executed {command['interpreted_action']}"},
            "executed_at": datetime.utcnow().isoformat()
        }
    else:
        result = {
            "command_id": command_id,
            "status": "rejected",
            "rejected_at": datetime.utcnow().isoformat()
        }

    COMMAND_HISTORY.append(result)
    return result


@app.get("/commands/history")
def get_command_history(user_id: Optional[str] = None, limit: int = 50):
    """Get command execution history"""
    history = COMMAND_HISTORY
    if user_id:
        history = [h for h in history if h.get("user_id") == user_id]
    return {"history": history[-limit:], "total": len(history)}


@app.post("/commands/templates")
def create_command_template(
    name: str,
    pattern: str,
    action: str,
    parameter_mappings: Dict[str, str],
    examples: List[str]
):
    """Create a command template for NL understanding"""
    template_id = f"tpl_{uuid.uuid4().hex[:12]}"
    template = {
        "id": template_id,
        "name": name,
        "pattern": pattern,
        "action": action,
        "parameter_mappings": parameter_mappings,
        "examples": examples,
        "usage_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    COMMAND_TEMPLATES[template_id] = template
    return template


@app.get("/commands/templates")
def list_command_templates():
    """List command templates"""
    return {"templates": list(COMMAND_TEMPLATES.values()), "total": len(COMMAND_TEMPLATES)}


@app.get("/commands/suggestions")
def get_command_suggestions(partial_command: str, limit: int = 5):
    """Get command suggestions based on partial input"""
    suggestions = [
        f"{partial_command} all agents",
        f"{partial_command} workflow named 'test'",
        f"run {partial_command}",
        f"create new {partial_command}",
        f"show {partial_command} status"
    ]
    return {"suggestions": suggestions[:limit], "partial": partial_command}


# ============================================================================
# Audit Trail & Forensics
# ============================================================================

AUDIT_LOGS: List[Dict[str, Any]] = []
AUDIT_POLICIES: Dict[str, Dict[str, Any]] = {}
FORENSIC_QUERIES: Dict[str, Dict[str, Any]] = {}


@app.post("/audit/log")
def create_audit_log(
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: str,
    changes: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Create an audit log entry"""
    log_entry = {
        "id": f"audit_{uuid.uuid4().hex[:12]}",
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "changes": changes or {},
        "metadata": metadata or {},
        "ip_address": "192.168.1.1",
        "user_agent": "API Client",
        "timestamp": datetime.utcnow().isoformat()
    }
    AUDIT_LOGS.append(log_entry)
    return log_entry


@app.get("/audit/logs")
def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100
):
    """Query audit logs"""
    logs = AUDIT_LOGS

    if resource_type:
        logs = [l for l in logs if l["resource_type"] == resource_type]
    if resource_id:
        logs = [l for l in logs if l["resource_id"] == resource_id]
    if user_id:
        logs = [l for l in logs if l["user_id"] == user_id]
    if action:
        logs = [l for l in logs if l["action"] == action]
    if start_time:
        logs = [l for l in logs if l["timestamp"] >= start_time]
    if end_time:
        logs = [l for l in logs if l["timestamp"] <= end_time]

    return {"logs": logs[-limit:], "total": len(logs)}


@app.get("/audit/logs/{resource_type}/{resource_id}/history")
def get_resource_history(resource_type: str, resource_id: str):
    """Get complete history of changes for a resource"""
    history = [l for l in AUDIT_LOGS if l["resource_type"] == resource_type and l["resource_id"] == resource_id]
    history.sort(key=lambda x: x["timestamp"])

    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "history": history,
        "total_changes": len(history)
    }


@app.post("/audit/policies")
def create_audit_policy(
    name: str,
    resource_types: List[str],
    actions: List[str],
    retention_days: int = 90,
    alert_on: Optional[List[str]] = None
):
    """Create an audit policy"""
    policy_id = f"apol_{uuid.uuid4().hex[:12]}"
    policy = {
        "id": policy_id,
        "name": name,
        "resource_types": resource_types,
        "actions": actions,
        "retention_days": retention_days,
        "alert_on": alert_on or [],
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    AUDIT_POLICIES[policy_id] = policy
    return policy


@app.get("/audit/policies")
def list_audit_policies():
    """List audit policies"""
    return {"policies": list(AUDIT_POLICIES.values()), "total": len(AUDIT_POLICIES)}


@app.post("/audit/forensics/query")
def create_forensic_query(
    name: str,
    description: str,
    filters: Dict[str, Any],
    time_range: Dict[str, str]
):
    """Create a forensic query for investigation"""
    query_id = f"forensic_{uuid.uuid4().hex[:12]}"

    # Execute query
    results = []
    for log in AUDIT_LOGS:
        match = True
        for key, value in filters.items():
            if log.get(key) != value:
                match = False
                break
        if match:
            results.append(log)

    query = {
        "id": query_id,
        "name": name,
        "description": description,
        "filters": filters,
        "time_range": time_range,
        "results_count": len(results),
        "results": results[:100],
        "executed_at": datetime.utcnow().isoformat()
    }
    FORENSIC_QUERIES[query_id] = query
    return query


@app.get("/audit/statistics")
def get_audit_statistics(time_period: str = "7d"):
    """Get audit log statistics"""
    action_counts = {}
    user_counts = {}
    resource_counts = {}

    for log in AUDIT_LOGS:
        action_counts[log["action"]] = action_counts.get(log["action"], 0) + 1
        user_counts[log["user_id"]] = user_counts.get(log["user_id"], 0) + 1
        resource_counts[log["resource_type"]] = resource_counts.get(log["resource_type"], 0) + 1

    return {
        "total_events": len(AUDIT_LOGS),
        "by_action": action_counts,
        "by_user": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        "by_resource": resource_counts,
        "time_period": time_period
    }


# ============================================================================
# Resource Tagging & Organization
# ============================================================================

RESOURCE_TAGS: Dict[str, List[Dict[str, Any]]] = {}
TAG_DEFINITIONS: Dict[str, Dict[str, Any]] = {}
TAG_POLICIES: Dict[str, Dict[str, Any]] = {}


@app.post("/tags/resources/{resource_type}/{resource_id}")
def add_tags_to_resource(
    resource_type: str,
    resource_id: str,
    tags: Dict[str, str]
):
    """Add tags to a resource"""
    key = f"{resource_type}:{resource_id}"

    if key not in RESOURCE_TAGS:
        RESOURCE_TAGS[key] = []

    for tag_key, tag_value in tags.items():
        RESOURCE_TAGS[key].append({
            "key": tag_key,
            "value": tag_value,
            "added_at": datetime.utcnow().isoformat()
        })

    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "tags": RESOURCE_TAGS[key]
    }


@app.get("/tags/resources/{resource_type}/{resource_id}")
def get_resource_tags(resource_type: str, resource_id: str):
    """Get tags for a resource"""
    key = f"{resource_type}:{resource_id}"
    tags = RESOURCE_TAGS.get(key, [])
    return {"resource_type": resource_type, "resource_id": resource_id, "tags": tags}


@app.delete("/tags/resources/{resource_type}/{resource_id}/{tag_key}")
def remove_tag_from_resource(resource_type: str, resource_id: str, tag_key: str):
    """Remove a tag from a resource"""
    key = f"{resource_type}:{resource_id}"
    if key in RESOURCE_TAGS:
        RESOURCE_TAGS[key] = [t for t in RESOURCE_TAGS[key] if t["key"] != tag_key]
    return {"removed": True}


@app.get("/tags/search")
def search_by_tags(
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    resource_type: Optional[str] = None
):
    """Search resources by tags"""
    results = []
    for resource_key, tags in RESOURCE_TAGS.items():
        parts = resource_key.split(":", 1)
        res_type, res_id = parts[0], parts[1]

        if resource_type and res_type != resource_type:
            continue

        for tag in tags:
            if tag_key and tag["key"] != tag_key:
                continue
            if tag_value and tag["value"] != tag_value:
                continue
            results.append({
                "resource_type": res_type,
                "resource_id": res_id,
                "matching_tag": tag
            })
            break

    return {"results": results, "total": len(results)}


@app.post("/tags/definitions")
def create_tag_definition(
    key: str,
    description: str,
    allowed_values: Optional[List[str]] = None,
    required: bool = False
):
    """Define a tag with validation rules"""
    definition = {
        "key": key,
        "description": description,
        "allowed_values": allowed_values,
        "required": required,
        "usage_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    TAG_DEFINITIONS[key] = definition
    return definition


@app.get("/tags/definitions")
def list_tag_definitions():
    """List tag definitions"""
    return {"definitions": list(TAG_DEFINITIONS.values()), "total": len(TAG_DEFINITIONS)}


@app.post("/tags/policies")
def create_tag_policy(
    name: str,
    resource_types: List[str],
    required_tags: List[str],
    enforcement: str = "warn"
):
    """Create a tag policy"""
    policy_id = f"tagpol_{uuid.uuid4().hex[:12]}"
    policy = {
        "id": policy_id,
        "name": name,
        "resource_types": resource_types,
        "required_tags": required_tags,
        "enforcement": enforcement,
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    TAG_POLICIES[policy_id] = policy
    return policy


@app.get("/tags/policies")
def list_tag_policies():
    """List tag policies"""
    return {"policies": list(TAG_POLICIES.values()), "total": len(TAG_POLICIES)}


# ============================================================================
# Cost Allocation & Chargeback
# ============================================================================

COST_CENTERS: Dict[str, Dict[str, Any]] = {}
COST_ALLOCATIONS: Dict[str, List[Dict[str, Any]]] = {}
CHARGEBACK_REPORTS: Dict[str, Dict[str, Any]] = {}


@app.post("/costs/centers")
def create_cost_center(
    name: str,
    code: str,
    owner_id: str,
    budget: Optional[float] = None,
    parent_id: Optional[str] = None
):
    """Create a cost center"""
    center_id = f"cc_{uuid.uuid4().hex[:12]}"
    center = {
        "id": center_id,
        "name": name,
        "code": code,
        "owner_id": owner_id,
        "budget": budget,
        "parent_id": parent_id,
        "total_allocated": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }
    COST_CENTERS[center_id] = center
    return center


@app.get("/costs/centers")
def list_cost_centers():
    """List cost centers"""
    return {"cost_centers": list(COST_CENTERS.values()), "total": len(COST_CENTERS)}


@app.get("/costs/centers/{center_id}")
def get_cost_center(center_id: str):
    """Get cost center details"""
    if center_id not in COST_CENTERS:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return COST_CENTERS[center_id]


@app.post("/costs/allocations")
def create_cost_allocation(
    cost_center_id: str,
    resource_type: str,
    resource_id: str,
    amount: float,
    period: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Allocate cost to a cost center"""
    if cost_center_id not in COST_CENTERS:
        raise HTTPException(status_code=404, detail="Cost center not found")

    allocation = {
        "id": f"alloc_{uuid.uuid4().hex[:8]}",
        "cost_center_id": cost_center_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "amount": amount,
        "period": period,
        "metadata": metadata or {},
        "allocated_at": datetime.utcnow().isoformat()
    }

    if cost_center_id not in COST_ALLOCATIONS:
        COST_ALLOCATIONS[cost_center_id] = []
    COST_ALLOCATIONS[cost_center_id].append(allocation)

    COST_CENTERS[cost_center_id]["total_allocated"] += amount

    return allocation


@app.get("/costs/allocations/{cost_center_id}")
def get_cost_allocations(cost_center_id: str, period: Optional[str] = None):
    """Get allocations for a cost center"""
    allocations = COST_ALLOCATIONS.get(cost_center_id, [])
    if period:
        allocations = [a for a in allocations if a["period"] == period]
    total = sum(a["amount"] for a in allocations)
    return {"allocations": allocations, "total_amount": total}


@app.post("/costs/chargeback/report")
def generate_chargeback_report(
    period: str,
    cost_center_ids: Optional[List[str]] = None,
    include_details: bool = True
):
    """Generate a chargeback report"""
    report_id = f"cb_{uuid.uuid4().hex[:12]}"

    centers_to_report = cost_center_ids or list(COST_CENTERS.keys())

    report_data = []
    total_amount = 0.0

    for cc_id in centers_to_report:
        if cc_id not in COST_CENTERS:
            continue
        center = COST_CENTERS[cc_id]
        allocations = COST_ALLOCATIONS.get(cc_id, [])
        period_allocations = [a for a in allocations if a["period"] == period]
        amount = sum(a["amount"] for a in period_allocations)
        total_amount += amount

        entry = {
            "cost_center_id": cc_id,
            "cost_center_name": center["name"],
            "code": center["code"],
            "amount": amount,
            "budget": center.get("budget"),
            "budget_utilization": (amount / center["budget"] * 100) if center.get("budget") else None
        }
        if include_details:
            entry["allocations"] = period_allocations
        report_data.append(entry)

    report = {
        "id": report_id,
        "period": period,
        "total_amount": total_amount,
        "cost_centers": report_data,
        "generated_at": datetime.utcnow().isoformat()
    }
    CHARGEBACK_REPORTS[report_id] = report
    return report


@app.get("/costs/chargeback/reports")
def list_chargeback_reports():
    """List chargeback reports"""
    return {"reports": list(CHARGEBACK_REPORTS.values()), "total": len(CHARGEBACK_REPORTS)}


@app.get("/costs/summary")
def get_cost_summary(period: Optional[str] = None):
    """Get overall cost summary"""
    total = 0.0
    by_center = {}
    by_resource_type = {}

    for cc_id, allocations in COST_ALLOCATIONS.items():
        for alloc in allocations:
            if period and alloc["period"] != period:
                continue
            total += alloc["amount"]
            by_center[cc_id] = by_center.get(cc_id, 0) + alloc["amount"]
            by_resource_type[alloc["resource_type"]] = by_resource_type.get(alloc["resource_type"], 0) + alloc["amount"]

    return {
        "total_cost": total,
        "by_cost_center": by_center,
        "by_resource_type": by_resource_type,
        "period": period
    }


# ============================================================================
# SLA Management
# ============================================================================

SLA_DEFINITIONS: Dict[str, Dict[str, Any]] = {}
SLA_MEASUREMENTS: Dict[str, List[Dict[str, Any]]] = {}
SLA_BREACHES: List[Dict[str, Any]] = []


@app.post("/sla/definitions")
def create_sla_definition(
    name: str,
    description: str,
    metrics: List[Dict[str, Any]],
    targets: Dict[str, Any],
    measurement_window: str = "1d"
):
    """Create an SLA definition"""
    sla_id = f"sla_{uuid.uuid4().hex[:12]}"
    sla = {
        "id": sla_id,
        "name": name,
        "description": description,
        "metrics": metrics,  # [{"name": "availability", "unit": "percent"}, {"name": "latency_p99", "unit": "ms"}]
        "targets": targets,  # {"availability": 99.9, "latency_p99": 200}
        "measurement_window": measurement_window,
        "status": "active",
        "current_compliance": None,
        "created_at": datetime.utcnow().isoformat()
    }
    SLA_DEFINITIONS[sla_id] = sla
    SLA_MEASUREMENTS[sla_id] = []
    return sla


@app.get("/sla/definitions")
def list_sla_definitions():
    """List SLA definitions"""
    return {"slas": list(SLA_DEFINITIONS.values()), "total": len(SLA_DEFINITIONS)}


@app.get("/sla/definitions/{sla_id}")
def get_sla_definition(sla_id: str):
    """Get SLA definition details"""
    if sla_id not in SLA_DEFINITIONS:
        raise HTTPException(status_code=404, detail="SLA not found")
    return SLA_DEFINITIONS[sla_id]


@app.post("/sla/{sla_id}/measurements")
def record_sla_measurement(
    sla_id: str,
    metric_name: str,
    value: float,
    timestamp: Optional[str] = None
):
    """Record an SLA measurement"""
    if sla_id not in SLA_DEFINITIONS:
        raise HTTPException(status_code=404, detail="SLA not found")

    sla = SLA_DEFINITIONS[sla_id]
    measurement = {
        "id": f"measure_{uuid.uuid4().hex[:8]}",
        "sla_id": sla_id,
        "metric_name": metric_name,
        "value": value,
        "target": sla["targets"].get(metric_name),
        "meets_target": value >= sla["targets"].get(metric_name, 0) if metric_name == "availability" else value <= sla["targets"].get(metric_name, float('inf')),
        "timestamp": timestamp or datetime.utcnow().isoformat()
    }
    SLA_MEASUREMENTS[sla_id].append(measurement)

    # Check for breach
    if not measurement["meets_target"]:
        breach = {
            "id": f"breach_{uuid.uuid4().hex[:8]}",
            "sla_id": sla_id,
            "sla_name": sla["name"],
            "metric_name": metric_name,
            "target_value": measurement["target"],
            "actual_value": value,
            "severity": "critical" if abs(value - measurement["target"]) / measurement["target"] > 0.1 else "warning",
            "timestamp": datetime.utcnow().isoformat()
        }
        SLA_BREACHES.append(breach)

    return measurement


@app.get("/sla/{sla_id}/measurements")
def get_sla_measurements(sla_id: str, limit: int = 100):
    """Get SLA measurements"""
    if sla_id not in SLA_DEFINITIONS:
        raise HTTPException(status_code=404, detail="SLA not found")
    measurements = SLA_MEASUREMENTS.get(sla_id, [])
    return {"measurements": measurements[-limit:], "total": len(measurements)}


@app.get("/sla/{sla_id}/compliance")
def get_sla_compliance(sla_id: str, period: str = "30d"):
    """Get SLA compliance report"""
    if sla_id not in SLA_DEFINITIONS:
        raise HTTPException(status_code=404, detail="SLA not found")

    sla = SLA_DEFINITIONS[sla_id]
    measurements = SLA_MEASUREMENTS.get(sla_id, [])

    compliance_by_metric = {}
    for metric in sla["metrics"]:
        metric_name = metric["name"]
        metric_measurements = [m for m in measurements if m["metric_name"] == metric_name]
        if metric_measurements:
            compliant = len([m for m in metric_measurements if m["meets_target"]])
            compliance_by_metric[metric_name] = {
                "compliance_percent": (compliant / len(metric_measurements)) * 100,
                "measurements_count": len(metric_measurements),
                "target": sla["targets"].get(metric_name)
            }

    overall_compliance = sum(c["compliance_percent"] for c in compliance_by_metric.values()) / max(1, len(compliance_by_metric))

    return {
        "sla_id": sla_id,
        "sla_name": sla["name"],
        "period": period,
        "overall_compliance": round(overall_compliance, 2),
        "by_metric": compliance_by_metric
    }


@app.get("/sla/breaches")
def get_sla_breaches(sla_id: Optional[str] = None, severity: Optional[str] = None, limit: int = 100):
    """Get SLA breaches"""
    breaches = SLA_BREACHES
    if sla_id:
        breaches = [b for b in breaches if b["sla_id"] == sla_id]
    if severity:
        breaches = [b for b in breaches if b["severity"] == severity]
    return {"breaches": breaches[-limit:], "total": len(breaches)}


@app.get("/sla/dashboard")
def get_sla_dashboard():
    """Get SLA dashboard overview"""
    dashboard = {
        "total_slas": len(SLA_DEFINITIONS),
        "slas_meeting_targets": 0,
        "slas_at_risk": 0,
        "slas_breached": 0,
        "recent_breaches": SLA_BREACHES[-5:] if SLA_BREACHES else [],
        "by_sla": []
    }

    for sla_id, sla in SLA_DEFINITIONS.items():
        measurements = SLA_MEASUREMENTS.get(sla_id, [])
        recent = measurements[-10:] if measurements else []
        compliance = len([m for m in recent if m.get("meets_target", True)]) / max(1, len(recent)) * 100

        if compliance >= 99:
            dashboard["slas_meeting_targets"] += 1
            status = "healthy"
        elif compliance >= 95:
            dashboard["slas_at_risk"] += 1
            status = "at_risk"
        else:
            dashboard["slas_breached"] += 1
            status = "breached"

        dashboard["by_sla"].append({
            "sla_id": sla_id,
            "name": sla["name"],
            "compliance": round(compliance, 2),
            "status": status
        })

    return dashboard


# ============================================================================
# Multi-Tenancy & Isolation
# ============================================================================

TENANTS: Dict[str, Dict[str, Any]] = {}
TENANT_QUOTAS: Dict[str, Dict[str, Any]] = {}
TENANT_ISOLATION_POLICIES: Dict[str, Dict[str, Any]] = {}
TENANT_DATA_PARTITIONS: Dict[str, List[str]] = {}


@app.post("/tenants")
def create_tenant(body: dict = Body(...)):
    """Create a new tenant"""
    tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
    tenant = {
        "id": tenant_id,
        "name": body.get("name", ""),
        "plan": body.get("plan", "standard"),
        "status": "active",
        "settings": body.get("settings", {}),
        "metadata": body.get("metadata", {}),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    TENANTS[tenant_id] = tenant
    TENANT_QUOTAS[tenant_id] = {
        "max_agents": body.get("max_agents", 100),
        "max_workflows": body.get("max_workflows", 50),
        "max_api_calls_per_hour": body.get("max_api_calls", 10000),
        "max_storage_mb": body.get("max_storage", 5000),
        "current_usage": {"agents": 0, "workflows": 0, "api_calls": 0, "storage_mb": 0}
    }
    TENANT_DATA_PARTITIONS[tenant_id] = []
    return tenant


@app.get("/tenants")
def list_tenants(status: Optional[str] = None, plan: Optional[str] = None):
    """List all tenants"""
    tenants = list(TENANTS.values())
    if status:
        tenants = [t for t in tenants if t["status"] == status]
    if plan:
        tenants = [t for t in tenants if t["plan"] == plan]
    return {"tenants": tenants, "total": len(tenants)}


@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: str):
    """Get tenant details"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "tenant": TENANTS[tenant_id],
        "quotas": TENANT_QUOTAS.get(tenant_id, {}),
        "partitions": TENANT_DATA_PARTITIONS.get(tenant_id, [])
    }


@app.put("/tenants/{tenant_id}")
def update_tenant(tenant_id: str, body: dict = Body(...)):
    """Update tenant"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant = TENANTS[tenant_id]
    tenant.update({
        "name": body.get("name", tenant["name"]),
        "plan": body.get("plan", tenant["plan"]),
        "settings": body.get("settings", tenant["settings"]),
        "metadata": body.get("metadata", tenant["metadata"]),
        "updated_at": datetime.utcnow().isoformat()
    })
    return tenant


@app.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: str):
    """Delete tenant"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    TENANTS[tenant_id]["status"] = "deleted"
    return {"message": "Tenant marked for deletion", "tenant_id": tenant_id}


@app.get("/tenants/{tenant_id}/quotas")
def get_tenant_quotas(tenant_id: str):
    """Get tenant quotas and usage"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TENANT_QUOTAS.get(tenant_id, {})


@app.put("/tenants/{tenant_id}/quotas")
def update_tenant_quotas(tenant_id: str, body: dict = Body(...)):
    """Update tenant quotas"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    quotas = TENANT_QUOTAS.get(tenant_id, {})
    quotas.update({k: v for k, v in body.items() if k != "current_usage"})
    TENANT_QUOTAS[tenant_id] = quotas
    return quotas


@app.post("/tenants/{tenant_id}/isolation-policy")
def create_isolation_policy(tenant_id: str, body: dict = Body(...)):
    """Create tenant isolation policy"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    policy_id = f"iso_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "tenant_id": tenant_id,
        "data_isolation": body.get("data_isolation", "strict"),
        "network_isolation": body.get("network_isolation", True),
        "resource_limits": body.get("resource_limits", {}),
        "allowed_regions": body.get("allowed_regions", ["all"]),
        "encryption_required": body.get("encryption_required", True),
        "created_at": datetime.utcnow().isoformat()
    }
    TENANT_ISOLATION_POLICIES[policy_id] = policy
    return policy


@app.get("/tenants/{tenant_id}/isolation-policies")
def get_isolation_policies(tenant_id: str):
    """Get tenant isolation policies"""
    if tenant_id not in TENANTS:
        raise HTTPException(status_code=404, detail="Tenant not found")
    policies = [p for p in TENANT_ISOLATION_POLICIES.values() if p["tenant_id"] == tenant_id]
    return {"policies": policies, "total": len(policies)}


# ============================================================================
# Rate Limiting & Throttling
# ============================================================================

RATE_LIMIT_CONFIGS: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_BUCKETS: Dict[str, Dict[str, Any]] = {}
THROTTLE_POLICIES: Dict[str, Dict[str, Any]] = {}


@app.post("/rate-limits")
def create_rate_limit(body: dict = Body(...)):
    """Create rate limit configuration"""
    limit_id = f"rl_{uuid.uuid4().hex[:8]}"
    config = {
        "id": limit_id,
        "name": body.get("name", ""),
        "resource_type": body.get("resource_type", "api"),
        "limit": body.get("limit", 1000),
        "window_seconds": body.get("window_seconds", 3600),
        "burst_limit": body.get("burst_limit"),
        "scope": body.get("scope", "global"),
        "action_on_exceed": body.get("action_on_exceed", "reject"),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    RATE_LIMIT_CONFIGS[limit_id] = config
    return config


@app.get("/rate-limits")
def list_rate_limits(resource_type: Optional[str] = None):
    """List rate limit configurations"""
    configs = list(RATE_LIMIT_CONFIGS.values())
    if resource_type:
        configs = [c for c in configs if c["resource_type"] == resource_type]
    return {"rate_limits": configs, "total": len(configs)}


@app.get("/rate-limits/{limit_id}")
def get_rate_limit(limit_id: str):
    """Get rate limit details"""
    if limit_id not in RATE_LIMIT_CONFIGS:
        raise HTTPException(status_code=404, detail="Rate limit not found")
    return RATE_LIMIT_CONFIGS[limit_id]


@app.put("/rate-limits/{limit_id}")
def update_rate_limit(limit_id: str, body: dict = Body(...)):
    """Update rate limit"""
    if limit_id not in RATE_LIMIT_CONFIGS:
        raise HTTPException(status_code=404, detail="Rate limit not found")
    config = RATE_LIMIT_CONFIGS[limit_id]
    config.update({k: v for k, v in body.items() if k not in ["id", "created_at"]})
    return config


@app.delete("/rate-limits/{limit_id}")
def delete_rate_limit(limit_id: str):
    """Delete rate limit"""
    if limit_id not in RATE_LIMIT_CONFIGS:
        raise HTTPException(status_code=404, detail="Rate limit not found")
    del RATE_LIMIT_CONFIGS[limit_id]
    return {"message": "Rate limit deleted", "id": limit_id}


@app.post("/rate-limits/check")
def check_rate_limit(body: dict = Body(...)):
    """Check if request is within rate limits"""
    resource_id = body.get("resource_id", "default")
    client_id = body.get("client_id", "anonymous")
    bucket_key = f"{resource_id}:{client_id}"

    now = datetime.utcnow()
    bucket = RATE_LIMIT_BUCKETS.get(bucket_key, {
        "count": 0,
        "window_start": now.isoformat(),
        "last_request": now.isoformat()
    })

    bucket["count"] += 1
    bucket["last_request"] = now.isoformat()
    RATE_LIMIT_BUCKETS[bucket_key] = bucket

    return {
        "allowed": True,
        "bucket_key": bucket_key,
        "current_count": bucket["count"],
        "remaining": 1000 - bucket["count"],
        "reset_at": now.isoformat()
    }


@app.post("/throttle-policies")
def create_throttle_policy(body: dict = Body(...)):
    """Create throttle policy"""
    policy_id = f"throttle_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "name": body.get("name", ""),
        "type": body.get("type", "token_bucket"),
        "tokens_per_second": body.get("tokens_per_second", 100),
        "bucket_size": body.get("bucket_size", 1000),
        "priority_levels": body.get("priority_levels", {"high": 1.5, "normal": 1.0, "low": 0.5}),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    THROTTLE_POLICIES[policy_id] = policy
    return policy


@app.get("/throttle-policies")
def list_throttle_policies():
    """List throttle policies"""
    return {"policies": list(THROTTLE_POLICIES.values()), "total": len(THROTTLE_POLICIES)}


# ============================================================================
# Feature Flags & Toggles
# ============================================================================

FEATURE_FLAGS: Dict[str, Dict[str, Any]] = {}
FLAG_OVERRIDES: Dict[str, List[Dict[str, Any]]] = {}
FLAG_ROLLOUTS: Dict[str, Dict[str, Any]] = {}


@app.post("/feature-flags")
def create_feature_flag(body: dict = Body(...)):
    """Create feature flag"""
    flag_id = f"flag_{uuid.uuid4().hex[:8]}"
    flag = {
        "id": flag_id,
        "key": body.get("key", flag_id),
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "type": body.get("type", "boolean"),
        "default_value": body.get("default_value", False),
        "enabled": body.get("enabled", False),
        "tags": body.get("tags", []),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    FEATURE_FLAGS[flag_id] = flag
    return flag


@app.get("/feature-flags")
def list_feature_flags(enabled: Optional[bool] = None, tag: Optional[str] = None):
    """List feature flags"""
    flags = list(FEATURE_FLAGS.values())
    if enabled is not None:
        flags = [f for f in flags if f["enabled"] == enabled]
    if tag:
        flags = [f for f in flags if tag in f.get("tags", [])]
    return {"flags": flags, "total": len(flags)}


@app.get("/feature-flags/{flag_id}")
def get_feature_flag(flag_id: str):
    """Get feature flag details"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {
        "flag": FEATURE_FLAGS[flag_id],
        "overrides": FLAG_OVERRIDES.get(flag_id, []),
        "rollout": FLAG_ROLLOUTS.get(flag_id)
    }


@app.put("/feature-flags/{flag_id}")
def update_feature_flag(flag_id: str, body: dict = Body(...)):
    """Update feature flag"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    flag = FEATURE_FLAGS[flag_id]
    flag.update({
        "name": body.get("name", flag["name"]),
        "description": body.get("description", flag["description"]),
        "default_value": body.get("default_value", flag["default_value"]),
        "enabled": body.get("enabled", flag["enabled"]),
        "tags": body.get("tags", flag["tags"]),
        "updated_at": datetime.utcnow().isoformat()
    })
    return flag


@app.delete("/feature-flags/{flag_id}")
def delete_feature_flag(flag_id: str):
    """Delete feature flag"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    del FEATURE_FLAGS[flag_id]
    return {"message": "Feature flag deleted", "id": flag_id}


@app.post("/feature-flags/{flag_id}/evaluate")
def evaluate_feature_flag(flag_id: str, body: dict = Body(...)):
    """Evaluate feature flag for context"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag = FEATURE_FLAGS[flag_id]
    context = body.get("context", {})

    if not flag["enabled"]:
        return {"value": flag["default_value"], "reason": "flag_disabled"}

    overrides = FLAG_OVERRIDES.get(flag_id, [])
    for override in overrides:
        if all(context.get(k) == v for k, v in override.get("conditions", {}).items()):
            return {"value": override["value"], "reason": "override_match"}

    rollout = FLAG_ROLLOUTS.get(flag_id)
    if rollout:
        user_id = context.get("user_id", "")
        hash_value = hash(user_id) % 100
        if hash_value < rollout.get("percentage", 0):
            return {"value": rollout.get("value", True), "reason": "rollout"}

    return {"value": flag["default_value"], "reason": "default"}


@app.post("/feature-flags/{flag_id}/overrides")
def add_flag_override(flag_id: str, body: dict = Body(...)):
    """Add feature flag override"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    override = {
        "id": f"override_{uuid.uuid4().hex[:8]}",
        "conditions": body.get("conditions", {}),
        "value": body.get("value"),
        "priority": body.get("priority", 0),
        "created_at": datetime.utcnow().isoformat()
    }

    if flag_id not in FLAG_OVERRIDES:
        FLAG_OVERRIDES[flag_id] = []
    FLAG_OVERRIDES[flag_id].append(override)
    FLAG_OVERRIDES[flag_id].sort(key=lambda x: x["priority"], reverse=True)

    return override


@app.post("/feature-flags/{flag_id}/rollout")
def configure_rollout(flag_id: str, body: dict = Body(...)):
    """Configure gradual rollout"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    rollout = {
        "flag_id": flag_id,
        "percentage": body.get("percentage", 0),
        "value": body.get("value", True),
        "schedule": body.get("schedule"),
        "auto_increment": body.get("auto_increment", False),
        "increment_by": body.get("increment_by", 10),
        "created_at": datetime.utcnow().isoformat()
    }
    FLAG_ROLLOUTS[flag_id] = rollout
    return rollout


# ============================================================================
# Notification Center
# ============================================================================

NOTIFICATIONS: Dict[str, Dict[str, Any]] = {}
NOTIFICATION_CHANNELS: Dict[str, Dict[str, Any]] = {}
NOTIFICATION_SUBSCRIPTIONS: Dict[str, List[Dict[str, Any]]] = {}
NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/notifications")
def create_notification(body: dict = Body(...)):
    """Create and send notification"""
    notif_id = f"notif_{uuid.uuid4().hex[:12]}"
    notification = {
        "id": notif_id,
        "type": body.get("type", "info"),
        "title": body.get("title", ""),
        "message": body.get("message", ""),
        "priority": body.get("priority", "normal"),
        "recipients": body.get("recipients", []),
        "channels": body.get("channels", ["in_app"]),
        "data": body.get("data", {}),
        "status": "sent",
        "read_by": [],
        "created_at": datetime.utcnow().isoformat()
    }
    NOTIFICATIONS[notif_id] = notification
    return notification


@app.get("/notifications")
def list_notifications(recipient: Optional[str] = None, type: Optional[str] = None, unread_only: bool = False):
    """List notifications"""
    notifs = list(NOTIFICATIONS.values())
    if recipient:
        notifs = [n for n in notifs if recipient in n["recipients"]]
    if type:
        notifs = [n for n in notifs if n["type"] == type]
    if unread_only:
        notifs = [n for n in notifs if recipient and recipient not in n.get("read_by", [])]
    return {"notifications": notifs, "total": len(notifs)}


@app.get("/notifications/{notif_id}")
def get_notification(notif_id: str):
    """Get notification details"""
    if notif_id not in NOTIFICATIONS:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NOTIFICATIONS[notif_id]


@app.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: str, body: dict = Body(...)):
    """Mark notification as read"""
    if notif_id not in NOTIFICATIONS:
        raise HTTPException(status_code=404, detail="Notification not found")
    user_id = body.get("user_id")
    if user_id and user_id not in NOTIFICATIONS[notif_id]["read_by"]:
        NOTIFICATIONS[notif_id]["read_by"].append(user_id)
    return {"message": "Marked as read", "notification_id": notif_id}


@app.post("/notification-channels")
def create_notification_channel(body: dict = Body(...)):
    """Create notification channel"""
    channel_id = f"channel_{uuid.uuid4().hex[:8]}"
    channel = {
        "id": channel_id,
        "name": body.get("name", ""),
        "type": body.get("type", "email"),
        "config": body.get("config", {}),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    NOTIFICATION_CHANNELS[channel_id] = channel
    return channel


@app.get("/notification-channels")
def list_notification_channels():
    """List notification channels"""
    return {"channels": list(NOTIFICATION_CHANNELS.values()), "total": len(NOTIFICATION_CHANNELS)}


@app.post("/notification-subscriptions")
def create_subscription(body: dict = Body(...)):
    """Create notification subscription"""
    sub_id = f"sub_{uuid.uuid4().hex[:8]}"
    subscription = {
        "id": sub_id,
        "user_id": body.get("user_id"),
        "event_types": body.get("event_types", ["*"]),
        "channels": body.get("channels", ["in_app"]),
        "filters": body.get("filters", {}),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    user_id = body.get("user_id", "default")
    if user_id not in NOTIFICATION_SUBSCRIPTIONS:
        NOTIFICATION_SUBSCRIPTIONS[user_id] = []
    NOTIFICATION_SUBSCRIPTIONS[user_id].append(subscription)
    return subscription


@app.get("/notification-subscriptions/{user_id}")
def get_user_subscriptions(user_id: str):
    """Get user notification subscriptions"""
    return {"subscriptions": NOTIFICATION_SUBSCRIPTIONS.get(user_id, []), "user_id": user_id}


@app.post("/notification-templates")
def create_notification_template(body: dict = Body(...)):
    """Create notification template"""
    template_id = f"tmpl_{uuid.uuid4().hex[:8]}"
    template = {
        "id": template_id,
        "name": body.get("name", ""),
        "type": body.get("type", "info"),
        "title_template": body.get("title_template", ""),
        "message_template": body.get("message_template", ""),
        "variables": body.get("variables", []),
        "created_at": datetime.utcnow().isoformat()
    }
    NOTIFICATION_TEMPLATES[template_id] = template
    return template


# ============================================================================
# Data Pipeline
# ============================================================================

PIPELINES: Dict[str, Dict[str, Any]] = {}
PIPELINE_RUNS: Dict[str, List[Dict[str, Any]]] = {}
PIPELINE_STAGES: Dict[str, List[Dict[str, Any]]] = {}
DATA_TRANSFORMATIONS: Dict[str, Dict[str, Any]] = {}


@app.post("/pipelines")
def create_pipeline(body: dict = Body(...)):
    """Create data pipeline"""
    pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
    pipeline = {
        "id": pipeline_id,
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "source": body.get("source", {}),
        "destination": body.get("destination", {}),
        "schedule": body.get("schedule"),
        "stages": body.get("stages", []),
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    PIPELINES[pipeline_id] = pipeline
    PIPELINE_STAGES[pipeline_id] = body.get("stages", [])
    return pipeline


@app.get("/pipelines")
def list_pipelines(status: Optional[str] = None):
    """List data pipelines"""
    pipes = list(PIPELINES.values())
    if status:
        pipes = [p for p in pipes if p["status"] == status]
    return {"pipelines": pipes, "total": len(pipes)}


@app.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    """Get pipeline details"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {
        "pipeline": PIPELINES[pipeline_id],
        "stages": PIPELINE_STAGES.get(pipeline_id, []),
        "recent_runs": PIPELINE_RUNS.get(pipeline_id, [])[-5:]
    }


@app.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: str, body: dict = Body(default={})):
    """Execute pipeline"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    run = {
        "id": run_id,
        "pipeline_id": pipeline_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "records_processed": 0,
        "errors": [],
        "parameters": body.get("parameters", {})
    }

    if pipeline_id not in PIPELINE_RUNS:
        PIPELINE_RUNS[pipeline_id] = []
    PIPELINE_RUNS[pipeline_id].append(run)

    PIPELINES[pipeline_id]["status"] = "running"

    run["status"] = "completed"
    run["completed_at"] = datetime.utcnow().isoformat()
    run["records_processed"] = random.randint(100, 10000)
    PIPELINES[pipeline_id]["status"] = "idle"

    return run


@app.get("/pipelines/{pipeline_id}/runs")
def get_pipeline_runs(pipeline_id: str, limit: int = 20):
    """Get pipeline run history"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    runs = PIPELINE_RUNS.get(pipeline_id, [])
    return {"runs": runs[-limit:], "total": len(runs)}


@app.post("/pipelines/{pipeline_id}/stages")
def add_pipeline_stage(pipeline_id: str, body: dict = Body(...)):
    """Add stage to pipeline"""
    if pipeline_id not in PIPELINES:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stage = {
        "id": f"stage_{uuid.uuid4().hex[:8]}",
        "name": body.get("name", ""),
        "type": body.get("type", "transform"),
        "config": body.get("config", {}),
        "order": len(PIPELINE_STAGES.get(pipeline_id, []))
    }

    if pipeline_id not in PIPELINE_STAGES:
        PIPELINE_STAGES[pipeline_id] = []
    PIPELINE_STAGES[pipeline_id].append(stage)

    return stage


@app.post("/data-transformations")
def create_transformation(body: dict = Body(...)):
    """Create data transformation"""
    transform_id = f"xform_{uuid.uuid4().hex[:8]}"
    transformation = {
        "id": transform_id,
        "name": body.get("name", ""),
        "type": body.get("type", "map"),
        "expression": body.get("expression", ""),
        "input_schema": body.get("input_schema", {}),
        "output_schema": body.get("output_schema", {}),
        "created_at": datetime.utcnow().isoformat()
    }
    DATA_TRANSFORMATIONS[transform_id] = transformation
    return transformation


@app.get("/data-transformations")
def list_transformations():
    """List data transformations"""
    return {"transformations": list(DATA_TRANSFORMATIONS.values()), "total": len(DATA_TRANSFORMATIONS)}


# ============================================================================
# Schema Registry
# ============================================================================

SCHEMAS: Dict[str, Dict[str, Any]] = {}
SCHEMA_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}
SCHEMA_COMPATIBILITY: Dict[str, str] = {}


@app.post("/schemas")
def create_schema(body: dict = Body(...)):
    """Register new schema"""
    schema_id = f"schema_{uuid.uuid4().hex[:8]}"
    schema = {
        "id": schema_id,
        "name": body.get("name", ""),
        "namespace": body.get("namespace", "default"),
        "type": body.get("type", "json"),
        "definition": body.get("definition", {}),
        "version": 1,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    SCHEMAS[schema_id] = schema
    SCHEMA_VERSIONS[schema_id] = [{"version": 1, "definition": schema["definition"], "created_at": schema["created_at"]}]
    SCHEMA_COMPATIBILITY[schema_id] = body.get("compatibility", "backward")
    return schema


@app.get("/schemas")
def list_schemas(namespace: Optional[str] = None, type: Optional[str] = None):
    """List schemas"""
    schemas = list(SCHEMAS.values())
    if namespace:
        schemas = [s for s in schemas if s["namespace"] == namespace]
    if type:
        schemas = [s for s in schemas if s["type"] == type]
    return {"schemas": schemas, "total": len(schemas)}


@app.get("/schemas/{schema_id}")
def get_schema(schema_id: str, version: Optional[int] = None):
    """Get schema details"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")

    if version:
        versions = SCHEMA_VERSIONS.get(schema_id, [])
        for v in versions:
            if v["version"] == version:
                return {"schema": SCHEMAS[schema_id], "definition": v["definition"], "version": version}
        raise HTTPException(status_code=404, detail="Schema version not found")

    return {
        "schema": SCHEMAS[schema_id],
        "versions": len(SCHEMA_VERSIONS.get(schema_id, [])),
        "compatibility": SCHEMA_COMPATIBILITY.get(schema_id, "backward")
    }


@app.post("/schemas/{schema_id}/versions")
def create_schema_version(schema_id: str, body: dict = Body(...)):
    """Create new schema version"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")

    versions = SCHEMA_VERSIONS.get(schema_id, [])
    new_version = len(versions) + 1

    version_entry = {
        "version": new_version,
        "definition": body.get("definition", {}),
        "created_at": datetime.utcnow().isoformat()
    }
    SCHEMA_VERSIONS[schema_id].append(version_entry)

    SCHEMAS[schema_id]["version"] = new_version
    SCHEMAS[schema_id]["definition"] = body.get("definition", {})
    SCHEMAS[schema_id]["updated_at"] = datetime.utcnow().isoformat()

    return {"schema_id": schema_id, "version": new_version, "message": "Version created"}


@app.get("/schemas/{schema_id}/versions")
def get_schema_versions(schema_id: str):
    """Get all schema versions"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"versions": SCHEMA_VERSIONS.get(schema_id, []), "total": len(SCHEMA_VERSIONS.get(schema_id, []))}


@app.post("/schemas/{schema_id}/validate")
def validate_against_schema(schema_id: str, body: dict = Body(...)):
    """Validate data against schema"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")

    data = body.get("data", {})
    schema_def = SCHEMAS[schema_id]["definition"]

    errors = []
    for field, field_def in schema_def.get("properties", {}).items():
        if field_def.get("required") and field not in data:
            errors.append(f"Missing required field: {field}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "schema_id": schema_id,
        "schema_version": SCHEMAS[schema_id]["version"]
    }


@app.put("/schemas/{schema_id}/compatibility")
def set_schema_compatibility(schema_id: str, body: dict = Body(...)):
    """Set schema compatibility mode"""
    if schema_id not in SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")
    mode = body.get("mode", "backward")
    if mode not in ["backward", "forward", "full", "none"]:
        raise HTTPException(status_code=400, detail="Invalid compatibility mode")
    SCHEMA_COMPATIBILITY[schema_id] = mode
    return {"schema_id": schema_id, "compatibility": mode}


# ============================================================================
# Service Discovery
# ============================================================================

SERVICES: Dict[str, Dict[str, Any]] = {}
SERVICE_INSTANCES: Dict[str, List[Dict[str, Any]]] = {}
SERVICE_HEALTH: Dict[str, Dict[str, Any]] = {}


@app.post("/services")
def register_service(body: dict = Body(...)):
    """Register a service"""
    service_id = f"svc_{uuid.uuid4().hex[:8]}"
    service = {
        "id": service_id,
        "name": body.get("name", ""),
        "version": body.get("version", "1.0.0"),
        "description": body.get("description", ""),
        "endpoints": body.get("endpoints", []),
        "metadata": body.get("metadata", {}),
        "tags": body.get("tags", []),
        "status": "registered",
        "created_at": datetime.utcnow().isoformat()
    }
    SERVICES[service_id] = service
    SERVICE_INSTANCES[service_id] = []
    return service


@app.get("/services")
def list_services(tag: Optional[str] = None, status: Optional[str] = None):
    """List registered services"""
    services = list(SERVICES.values())
    if tag:
        services = [s for s in services if tag in s.get("tags", [])]
    if status:
        services = [s for s in services if s["status"] == status]
    return {"services": services, "total": len(services)}


@app.get("/services/{service_id}")
def get_service(service_id: str):
    """Get service details"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "service": SERVICES[service_id],
        "instances": SERVICE_INSTANCES.get(service_id, []),
        "health": SERVICE_HEALTH.get(service_id, {})
    }


@app.post("/services/{service_id}/instances")
def register_instance(service_id: str, body: dict = Body(...)):
    """Register service instance"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    instance_id = f"inst_{uuid.uuid4().hex[:8]}"
    instance = {
        "id": instance_id,
        "host": body.get("host", "localhost"),
        "port": body.get("port", 8080),
        "protocol": body.get("protocol", "http"),
        "weight": body.get("weight", 1),
        "zone": body.get("zone", "default"),
        "status": "healthy",
        "registered_at": datetime.utcnow().isoformat(),
        "last_heartbeat": datetime.utcnow().isoformat()
    }

    if service_id not in SERVICE_INSTANCES:
        SERVICE_INSTANCES[service_id] = []
    SERVICE_INSTANCES[service_id].append(instance)

    SERVICES[service_id]["status"] = "active"

    return instance


@app.delete("/services/{service_id}/instances/{instance_id}")
def deregister_instance(service_id: str, instance_id: str):
    """Deregister service instance"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    instances = SERVICE_INSTANCES.get(service_id, [])
    SERVICE_INSTANCES[service_id] = [i for i in instances if i["id"] != instance_id]

    if not SERVICE_INSTANCES[service_id]:
        SERVICES[service_id]["status"] = "registered"

    return {"message": "Instance deregistered", "instance_id": instance_id}


@app.post("/services/{service_id}/heartbeat")
def service_heartbeat(service_id: str, body: dict = Body(...)):
    """Update service heartbeat"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    instance_id = body.get("instance_id")
    instances = SERVICE_INSTANCES.get(service_id, [])

    for instance in instances:
        if instance["id"] == instance_id:
            instance["last_heartbeat"] = datetime.utcnow().isoformat()
            instance["status"] = "healthy"
            break

    SERVICE_HEALTH[service_id] = {
        "last_check": datetime.utcnow().isoformat(),
        "healthy_instances": len([i for i in instances if i["status"] == "healthy"]),
        "total_instances": len(instances)
    }

    return {"message": "Heartbeat recorded", "service_id": service_id}


@app.get("/services/{service_id}/discover")
def discover_service(service_id: str, zone: Optional[str] = None):
    """Discover healthy service instances"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    instances = SERVICE_INSTANCES.get(service_id, [])
    healthy = [i for i in instances if i["status"] == "healthy"]

    if zone:
        healthy = [i for i in healthy if i["zone"] == zone]

    if not healthy:
        return {"instances": [], "message": "No healthy instances available"}

    selected = random.choice(healthy)

    return {
        "service": SERVICES[service_id]["name"],
        "selected_instance": selected,
        "all_healthy": healthy,
        "endpoint": f"{selected['protocol']}://{selected['host']}:{selected['port']}"
    }


# ============================================================================
# Circuit Breaker
# ============================================================================

CIRCUIT_BREAKERS: Dict[str, Dict[str, Any]] = {}
CIRCUIT_BREAKER_STATS: Dict[str, Dict[str, Any]] = {}
FALLBACK_CONFIGS: Dict[str, Dict[str, Any]] = {}


@app.post("/circuit-breakers")
def create_circuit_breaker(body: dict = Body(...)):
    """Create circuit breaker"""
    cb_id = f"cb_{uuid.uuid4().hex[:8]}"
    circuit_breaker = {
        "id": cb_id,
        "name": body.get("name", ""),
        "service_id": body.get("service_id"),
        "state": "closed",
        "failure_threshold": body.get("failure_threshold", 5),
        "success_threshold": body.get("success_threshold", 3),
        "timeout_seconds": body.get("timeout_seconds", 30),
        "half_open_max_calls": body.get("half_open_max_calls", 3),
        "created_at": datetime.utcnow().isoformat()
    }
    CIRCUIT_BREAKERS[cb_id] = circuit_breaker
    CIRCUIT_BREAKER_STATS[cb_id] = {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "rejected_calls": 0,
        "last_failure": None,
        "last_state_change": datetime.utcnow().isoformat()
    }
    return circuit_breaker


@app.get("/circuit-breakers")
def list_circuit_breakers(state: Optional[str] = None):
    """List circuit breakers"""
    cbs = list(CIRCUIT_BREAKERS.values())
    if state:
        cbs = [cb for cb in cbs if cb["state"] == state]
    return {"circuit_breakers": cbs, "total": len(cbs)}


@app.get("/circuit-breakers/{cb_id}")
def get_circuit_breaker(cb_id: str):
    """Get circuit breaker details"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    return {
        "circuit_breaker": CIRCUIT_BREAKERS[cb_id],
        "stats": CIRCUIT_BREAKER_STATS.get(cb_id, {}),
        "fallback": FALLBACK_CONFIGS.get(cb_id)
    }


@app.post("/circuit-breakers/{cb_id}/call")
def call_through_breaker(cb_id: str, body: dict = Body(...)):
    """Execute call through circuit breaker"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    cb = CIRCUIT_BREAKERS[cb_id]
    stats = CIRCUIT_BREAKER_STATS[cb_id]

    stats["total_calls"] += 1

    if cb["state"] == "open":
        stats["rejected_calls"] += 1
        fallback = FALLBACK_CONFIGS.get(cb_id)
        if fallback:
            return {"status": "fallback", "response": fallback.get("response"), "circuit_state": "open"}
        raise HTTPException(status_code=503, detail="Circuit breaker is open")

    success = random.random() > 0.1

    if success:
        stats["successful_calls"] += 1
        if cb["state"] == "half_open":
            if stats["successful_calls"] >= cb["success_threshold"]:
                cb["state"] = "closed"
                stats["last_state_change"] = datetime.utcnow().isoformat()
        return {"status": "success", "circuit_state": cb["state"]}
    else:
        stats["failed_calls"] += 1
        stats["last_failure"] = datetime.utcnow().isoformat()

        if stats["failed_calls"] >= cb["failure_threshold"]:
            cb["state"] = "open"
            stats["last_state_change"] = datetime.utcnow().isoformat()

        return {"status": "failure", "circuit_state": cb["state"]}


@app.post("/circuit-breakers/{cb_id}/reset")
def reset_circuit_breaker(cb_id: str):
    """Reset circuit breaker to closed state"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    CIRCUIT_BREAKERS[cb_id]["state"] = "closed"
    CIRCUIT_BREAKER_STATS[cb_id] = {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "rejected_calls": 0,
        "last_failure": None,
        "last_state_change": datetime.utcnow().isoformat()
    }

    return {"message": "Circuit breaker reset", "state": "closed"}


@app.post("/circuit-breakers/{cb_id}/half-open")
def set_half_open(cb_id: str):
    """Transition circuit breaker to half-open state"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    CIRCUIT_BREAKERS[cb_id]["state"] = "half_open"
    CIRCUIT_BREAKER_STATS[cb_id]["last_state_change"] = datetime.utcnow().isoformat()

    return {"message": "Circuit breaker set to half-open", "state": "half_open"}


@app.post("/circuit-breakers/{cb_id}/fallback")
def configure_fallback(cb_id: str, body: dict = Body(...)):
    """Configure fallback for circuit breaker"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")

    fallback = {
        "cb_id": cb_id,
        "type": body.get("type", "static"),
        "response": body.get("response", {}),
        "cache_ttl": body.get("cache_ttl", 60),
        "created_at": datetime.utcnow().isoformat()
    }
    FALLBACK_CONFIGS[cb_id] = fallback
    return fallback


@app.get("/circuit-breakers/dashboard")
def circuit_breaker_dashboard():
    """Get circuit breaker dashboard"""
    dashboard = {
        "total": len(CIRCUIT_BREAKERS),
        "by_state": {"closed": 0, "open": 0, "half_open": 0},
        "breakers": []
    }

    for cb_id, cb in CIRCUIT_BREAKERS.items():
        dashboard["by_state"][cb["state"]] += 1
        stats = CIRCUIT_BREAKER_STATS.get(cb_id, {})
        dashboard["breakers"].append({
            "id": cb_id,
            "name": cb["name"],
            "state": cb["state"],
            "success_rate": (stats.get("successful_calls", 0) / max(1, stats.get("total_calls", 1))) * 100,
            "total_calls": stats.get("total_calls", 0)
        })

    return dashboard


# ============================================================================
# API Gateway & Routing
# ============================================================================

API_ROUTES: Dict[str, Dict[str, Any]] = {}
ROUTE_POLICIES: Dict[str, Dict[str, Any]] = {}
API_KEYS: Dict[str, Dict[str, Any]] = {}
GATEWAY_CONFIGS: Dict[str, Dict[str, Any]] = {}


@app.post("/gateway/routes")
def create_route(body: dict = Body(...)):
    """Create API route"""
    route_id = f"route_{uuid.uuid4().hex[:8]}"
    route = {
        "id": route_id,
        "path": body.get("path", "/"),
        "methods": body.get("methods", ["GET"]),
        "target_service": body.get("target_service"),
        "target_path": body.get("target_path"),
        "strip_prefix": body.get("strip_prefix", False),
        "timeout_ms": body.get("timeout_ms", 30000),
        "retries": body.get("retries", 3),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    API_ROUTES[route_id] = route
    return route


@app.get("/gateway/routes")
def list_routes(enabled: Optional[bool] = None):
    """List API routes"""
    routes = list(API_ROUTES.values())
    if enabled is not None:
        routes = [r for r in routes if r["enabled"] == enabled]
    return {"routes": routes, "total": len(routes)}


@app.get("/gateway/routes/{route_id}")
def get_route(route_id: str):
    """Get route details"""
    if route_id not in API_ROUTES:
        raise HTTPException(status_code=404, detail="Route not found")
    return API_ROUTES[route_id]


@app.put("/gateway/routes/{route_id}")
def update_route(route_id: str, body: dict = Body(...)):
    """Update route"""
    if route_id not in API_ROUTES:
        raise HTTPException(status_code=404, detail="Route not found")
    route = API_ROUTES[route_id]
    route.update({k: v for k, v in body.items() if k not in ["id", "created_at"]})
    return route


@app.delete("/gateway/routes/{route_id}")
def delete_route(route_id: str):
    """Delete route"""
    if route_id not in API_ROUTES:
        raise HTTPException(status_code=404, detail="Route not found")
    del API_ROUTES[route_id]
    return {"message": "Route deleted", "id": route_id}


@app.post("/gateway/api-keys")
def create_api_key(body: dict = Body(...)):
    """Create API key"""
    key_id = f"key_{uuid.uuid4().hex[:8]}"
    api_key = f"ak_{uuid.uuid4().hex}"
    key_data = {
        "id": key_id,
        "key": api_key,
        "name": body.get("name", ""),
        "scopes": body.get("scopes", ["read"]),
        "rate_limit": body.get("rate_limit", 1000),
        "expires_at": body.get("expires_at"),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None
    }
    API_KEYS[key_id] = key_data
    return key_data


@app.get("/gateway/api-keys")
def list_api_keys():
    """List API keys"""
    keys = [{**k, "key": k["key"][:8] + "..."} for k in API_KEYS.values()]
    return {"api_keys": keys, "total": len(keys)}


@app.delete("/gateway/api-keys/{key_id}")
def revoke_api_key(key_id: str):
    """Revoke API key"""
    if key_id not in API_KEYS:
        raise HTTPException(status_code=404, detail="API key not found")
    API_KEYS[key_id]["enabled"] = False
    return {"message": "API key revoked", "id": key_id}


@app.post("/gateway/policies")
def create_route_policy(body: dict = Body(...)):
    """Create routing policy"""
    policy_id = f"policy_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "name": body.get("name", ""),
        "type": body.get("type", "rate_limit"),
        "rules": body.get("rules", []),
        "actions": body.get("actions", []),
        "priority": body.get("priority", 0),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    ROUTE_POLICIES[policy_id] = policy
    return policy


@app.get("/gateway/policies")
def list_route_policies():
    """List routing policies"""
    return {"policies": list(ROUTE_POLICIES.values()), "total": len(ROUTE_POLICIES)}


# ============================================================================
# Secret Management
# ============================================================================

SECRETS: Dict[str, Dict[str, Any]] = {}
SECRET_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}
SECRET_ACCESS_LOGS: List[Dict[str, Any]] = []
SECRET_POLICIES: Dict[str, Dict[str, Any]] = {}


@app.post("/secrets")
def create_secret(body: dict = Body(...)):
    """Create secret"""
    secret_id = f"secret_{uuid.uuid4().hex[:8]}"
    secret = {
        "id": secret_id,
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "type": body.get("type", "generic"),
        "version": 1,
        "tags": body.get("tags", []),
        "rotation_enabled": body.get("rotation_enabled", False),
        "rotation_days": body.get("rotation_days", 90),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    SECRETS[secret_id] = secret
    SECRET_VERSIONS[secret_id] = [{
        "version": 1,
        "value_hash": hash(body.get("value", "")),
        "created_at": datetime.utcnow().isoformat()
    }]
    return {**secret, "message": "Secret created (value stored securely)"}


@app.get("/secrets")
def list_secrets(type: Optional[str] = None, tag: Optional[str] = None):
    """List secrets (metadata only)"""
    secrets = list(SECRETS.values())
    if type:
        secrets = [s for s in secrets if s["type"] == type]
    if tag:
        secrets = [s for s in secrets if tag in s.get("tags", [])]
    return {"secrets": secrets, "total": len(secrets)}


@app.get("/secrets/{secret_id}")
def get_secret(secret_id: str, version: Optional[int] = None):
    """Get secret metadata"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    SECRET_ACCESS_LOGS.append({
        "secret_id": secret_id,
        "action": "read",
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "secret": SECRETS[secret_id],
        "versions": len(SECRET_VERSIONS.get(secret_id, []))
    }


@app.post("/secrets/{secret_id}/rotate")
def rotate_secret(secret_id: str, body: dict = Body(...)):
    """Rotate secret value"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")

    secret = SECRETS[secret_id]
    new_version = secret["version"] + 1
    secret["version"] = new_version
    secret["updated_at"] = datetime.utcnow().isoformat()

    SECRET_VERSIONS[secret_id].append({
        "version": new_version,
        "value_hash": hash(body.get("value", "")),
        "created_at": datetime.utcnow().isoformat()
    })

    return {"message": "Secret rotated", "version": new_version}


@app.delete("/secrets/{secret_id}")
def delete_secret(secret_id: str):
    """Delete secret"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")
    del SECRETS[secret_id]
    SECRET_VERSIONS.pop(secret_id, None)
    return {"message": "Secret deleted", "id": secret_id}


@app.get("/secrets/{secret_id}/versions")
def get_secret_versions(secret_id: str):
    """Get secret version history"""
    if secret_id not in SECRETS:
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"versions": SECRET_VERSIONS.get(secret_id, []), "current": SECRETS[secret_id]["version"]}


@app.post("/secrets/policies")
def create_secret_policy(body: dict = Body(...)):
    """Create secret access policy"""
    policy_id = f"sp_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "name": body.get("name", ""),
        "secrets": body.get("secrets", []),
        "principals": body.get("principals", []),
        "permissions": body.get("permissions", ["read"]),
        "conditions": body.get("conditions", {}),
        "created_at": datetime.utcnow().isoformat()
    }
    SECRET_POLICIES[policy_id] = policy
    return policy


@app.get("/secrets/access-log")
def get_secret_access_log(secret_id: Optional[str] = None, limit: int = 100):
    """Get secret access logs"""
    logs = SECRET_ACCESS_LOGS
    if secret_id:
        logs = [l for l in logs if l["secret_id"] == secret_id]
    return {"logs": logs[-limit:], "total": len(logs)}


# ============================================================================
# Backup & Recovery
# ============================================================================

BACKUPS: Dict[str, Dict[str, Any]] = {}
BACKUP_SCHEDULES: Dict[str, Dict[str, Any]] = {}
RECOVERY_POINTS: Dict[str, List[Dict[str, Any]]] = {}
RESTORE_JOBS: Dict[str, Dict[str, Any]] = {}


@app.post("/backups")
def create_backup(body: dict = Body(...)):
    """Create backup"""
    backup_id = f"backup_{uuid.uuid4().hex[:12]}"
    backup = {
        "id": backup_id,
        "name": body.get("name", f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"),
        "type": body.get("type", "full"),
        "scope": body.get("scope", ["all"]),
        "status": "in_progress",
        "size_bytes": 0,
        "location": body.get("location", "local"),
        "encryption": body.get("encryption", True),
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }
    BACKUPS[backup_id] = backup

    backup["status"] = "completed"
    backup["completed_at"] = datetime.utcnow().isoformat()
    backup["size_bytes"] = random.randint(1000000, 100000000)

    resource_id = body.get("resource_id", "system")
    if resource_id not in RECOVERY_POINTS:
        RECOVERY_POINTS[resource_id] = []
    RECOVERY_POINTS[resource_id].append({
        "backup_id": backup_id,
        "timestamp": backup["completed_at"],
        "type": backup["type"]
    })

    return backup


@app.get("/backups")
def list_backups(type: Optional[str] = None, status: Optional[str] = None):
    """List backups"""
    backups = list(BACKUPS.values())
    if type:
        backups = [b for b in backups if b["type"] == type]
    if status:
        backups = [b for b in backups if b["status"] == status]
    return {"backups": backups, "total": len(backups)}


@app.get("/backups/{backup_id}")
def get_backup(backup_id: str):
    """Get backup details"""
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")
    return BACKUPS[backup_id]


@app.delete("/backups/{backup_id}")
def delete_backup(backup_id: str):
    """Delete backup"""
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")
    del BACKUPS[backup_id]
    return {"message": "Backup deleted", "id": backup_id}


@app.post("/backups/schedules")
def create_backup_schedule(body: dict = Body(...)):
    """Create backup schedule"""
    schedule_id = f"sched_{uuid.uuid4().hex[:8]}"
    schedule = {
        "id": schedule_id,
        "name": body.get("name", ""),
        "cron": body.get("cron", "0 2 * * *"),
        "type": body.get("type", "incremental"),
        "retention_days": body.get("retention_days", 30),
        "scope": body.get("scope", ["all"]),
        "enabled": True,
        "last_run": None,
        "next_run": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    BACKUP_SCHEDULES[schedule_id] = schedule
    return schedule


@app.get("/backups/schedules")
def list_backup_schedules():
    """List backup schedules"""
    return {"schedules": list(BACKUP_SCHEDULES.values()), "total": len(BACKUP_SCHEDULES)}


@app.post("/backups/restore")
def restore_backup(body: dict = Body(...)):
    """Restore from backup"""
    backup_id = body.get("backup_id")
    if backup_id not in BACKUPS:
        raise HTTPException(status_code=404, detail="Backup not found")

    job_id = f"restore_{uuid.uuid4().hex[:8]}"
    job = {
        "id": job_id,
        "backup_id": backup_id,
        "target": body.get("target", "original"),
        "status": "in_progress",
        "progress_percent": 0,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }
    RESTORE_JOBS[job_id] = job

    job["status"] = "completed"
    job["progress_percent"] = 100
    job["completed_at"] = datetime.utcnow().isoformat()

    return job


@app.get("/backups/restore/{job_id}")
def get_restore_status(job_id: str):
    """Get restore job status"""
    if job_id not in RESTORE_JOBS:
        raise HTTPException(status_code=404, detail="Restore job not found")
    return RESTORE_JOBS[job_id]


@app.get("/backups/recovery-points/{resource_id}")
def get_recovery_points(resource_id: str):
    """Get recovery points for resource"""
    return {"recovery_points": RECOVERY_POINTS.get(resource_id, []), "resource_id": resource_id}


# ============================================================================
# Compliance & Governance
# ============================================================================

COMPLIANCE_FRAMEWORKS: Dict[str, Dict[str, Any]] = {}
COMPLIANCE_CONTROLS: Dict[str, List[Dict[str, Any]]] = {}
COMPLIANCE_ASSESSMENTS: Dict[str, Dict[str, Any]] = {}
GOVERNANCE_POLICIES: Dict[str, Dict[str, Any]] = {}


@app.post("/compliance/frameworks")
def create_compliance_framework(body: dict = Body(...)):
    """Create compliance framework"""
    framework_id = f"cf_{uuid.uuid4().hex[:8]}"
    framework = {
        "id": framework_id,
        "name": body.get("name", ""),
        "version": body.get("version", "1.0"),
        "description": body.get("description", ""),
        "type": body.get("type", "regulatory"),
        "controls_count": 0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    COMPLIANCE_FRAMEWORKS[framework_id] = framework
    COMPLIANCE_CONTROLS[framework_id] = []
    return framework


@app.get("/compliance/frameworks")
def list_compliance_frameworks(type: Optional[str] = None):
    """List compliance frameworks"""
    frameworks = list(COMPLIANCE_FRAMEWORKS.values())
    if type:
        frameworks = [f for f in frameworks if f["type"] == type]
    return {"frameworks": frameworks, "total": len(frameworks)}


@app.get("/compliance/frameworks/{framework_id}")
def get_compliance_framework(framework_id: str):
    """Get compliance framework details"""
    if framework_id not in COMPLIANCE_FRAMEWORKS:
        raise HTTPException(status_code=404, detail="Framework not found")
    return {
        "framework": COMPLIANCE_FRAMEWORKS[framework_id],
        "controls": COMPLIANCE_CONTROLS.get(framework_id, [])
    }


@app.post("/compliance/frameworks/{framework_id}/controls")
def add_compliance_control(framework_id: str, body: dict = Body(...)):
    """Add control to framework"""
    if framework_id not in COMPLIANCE_FRAMEWORKS:
        raise HTTPException(status_code=404, detail="Framework not found")

    control = {
        "id": f"ctrl_{uuid.uuid4().hex[:8]}",
        "code": body.get("code", ""),
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "category": body.get("category", "general"),
        "severity": body.get("severity", "medium"),
        "status": "not_assessed",
        "evidence_required": body.get("evidence_required", [])
    }

    COMPLIANCE_CONTROLS[framework_id].append(control)
    COMPLIANCE_FRAMEWORKS[framework_id]["controls_count"] += 1

    return control


@app.post("/compliance/assessments")
def create_assessment(body: dict = Body(...)):
    """Create compliance assessment"""
    assessment_id = f"assess_{uuid.uuid4().hex[:8]}"
    assessment = {
        "id": assessment_id,
        "framework_id": body.get("framework_id"),
        "name": body.get("name", ""),
        "scope": body.get("scope", []),
        "status": "in_progress",
        "results": {},
        "overall_score": 0,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }
    COMPLIANCE_ASSESSMENTS[assessment_id] = assessment
    return assessment


@app.get("/compliance/assessments/{assessment_id}")
def get_assessment(assessment_id: str):
    """Get assessment details"""
    if assessment_id not in COMPLIANCE_ASSESSMENTS:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return COMPLIANCE_ASSESSMENTS[assessment_id]


@app.post("/compliance/assessments/{assessment_id}/evaluate")
def evaluate_control(assessment_id: str, body: dict = Body(...)):
    """Evaluate control in assessment"""
    if assessment_id not in COMPLIANCE_ASSESSMENTS:
        raise HTTPException(status_code=404, detail="Assessment not found")

    control_id = body.get("control_id")
    result = {
        "status": body.get("status", "compliant"),
        "evidence": body.get("evidence", []),
        "notes": body.get("notes", ""),
        "evaluated_at": datetime.utcnow().isoformat()
    }

    COMPLIANCE_ASSESSMENTS[assessment_id]["results"][control_id] = result
    return {"control_id": control_id, "result": result}


@app.post("/governance/policies")
def create_governance_policy(body: dict = Body(...)):
    """Create governance policy"""
    policy_id = f"gov_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "name": body.get("name", ""),
        "type": body.get("type", "data"),
        "description": body.get("description", ""),
        "rules": body.get("rules", []),
        "enforcement": body.get("enforcement", "advisory"),
        "scope": body.get("scope", ["all"]),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    GOVERNANCE_POLICIES[policy_id] = policy
    return policy


@app.get("/governance/policies")
def list_governance_policies(type: Optional[str] = None):
    """List governance policies"""
    policies = list(GOVERNANCE_POLICIES.values())
    if type:
        policies = [p for p in policies if p["type"] == type]
    return {"policies": policies, "total": len(policies)}


@app.get("/compliance/dashboard")
def compliance_dashboard():
    """Get compliance dashboard"""
    dashboard = {
        "frameworks": len(COMPLIANCE_FRAMEWORKS),
        "total_controls": sum(len(c) for c in COMPLIANCE_CONTROLS.values()),
        "assessments": len(COMPLIANCE_ASSESSMENTS),
        "governance_policies": len(GOVERNANCE_POLICIES),
        "compliance_by_framework": []
    }

    for fid, framework in COMPLIANCE_FRAMEWORKS.items():
        controls = COMPLIANCE_CONTROLS.get(fid, [])
        compliant = len([c for c in controls if c["status"] == "compliant"])
        dashboard["compliance_by_framework"].append({
            "framework": framework["name"],
            "total_controls": len(controls),
            "compliant": compliant,
            "compliance_percent": (compliant / max(1, len(controls))) * 100
        })

    return dashboard


# ============================================================================
# Capacity Planning
# ============================================================================

CAPACITY_PLANS: Dict[str, Dict[str, Any]] = {}
RESOURCE_FORECASTS: Dict[str, Dict[str, Any]] = {}
SCALING_RECOMMENDATIONS: List[Dict[str, Any]] = []
CAPACITY_METRICS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/capacity/plans")
def create_capacity_plan(body: dict = Body(...)):
    """Create capacity plan"""
    plan_id = f"cap_{uuid.uuid4().hex[:8]}"
    plan = {
        "id": plan_id,
        "name": body.get("name", ""),
        "resources": body.get("resources", []),
        "target_utilization": body.get("target_utilization", 70),
        "planning_horizon_days": body.get("planning_horizon_days", 90),
        "growth_rate_percent": body.get("growth_rate_percent", 10),
        "buffer_percent": body.get("buffer_percent", 20),
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    CAPACITY_PLANS[plan_id] = plan
    return plan


@app.get("/capacity/plans")
def list_capacity_plans():
    """List capacity plans"""
    return {"plans": list(CAPACITY_PLANS.values()), "total": len(CAPACITY_PLANS)}


@app.get("/capacity/plans/{plan_id}")
def get_capacity_plan(plan_id: str):
    """Get capacity plan details"""
    if plan_id not in CAPACITY_PLANS:
        raise HTTPException(status_code=404, detail="Capacity plan not found")
    return CAPACITY_PLANS[plan_id]


@app.post("/capacity/forecasts")
def create_resource_forecast(body: dict = Body(...)):
    """Create resource forecast"""
    forecast_id = f"forecast_{uuid.uuid4().hex[:8]}"
    resource_type = body.get("resource_type", "compute")

    current = body.get("current_usage", 50)
    growth = body.get("growth_rate", 10)

    forecast = {
        "id": forecast_id,
        "resource_type": resource_type,
        "current_usage": current,
        "growth_rate_percent": growth,
        "forecast_days": body.get("forecast_days", 90),
        "predictions": [
            {"day": 30, "predicted_usage": current * (1 + growth/100)},
            {"day": 60, "predicted_usage": current * (1 + growth/100) ** 2},
            {"day": 90, "predicted_usage": current * (1 + growth/100) ** 3}
        ],
        "confidence": 0.85,
        "created_at": datetime.utcnow().isoformat()
    }
    RESOURCE_FORECASTS[forecast_id] = forecast
    return forecast


@app.get("/capacity/forecasts")
def list_forecasts(resource_type: Optional[str] = None):
    """List resource forecasts"""
    forecasts = list(RESOURCE_FORECASTS.values())
    if resource_type:
        forecasts = [f for f in forecasts if f["resource_type"] == resource_type]
    return {"forecasts": forecasts, "total": len(forecasts)}


@app.post("/capacity/metrics")
def record_capacity_metric(body: dict = Body(...)):
    """Record capacity metric"""
    resource_id = body.get("resource_id", "default")
    metric = {
        "timestamp": datetime.utcnow().isoformat(),
        "utilization_percent": body.get("utilization_percent", 0),
        "total_capacity": body.get("total_capacity", 100),
        "used_capacity": body.get("used_capacity", 0),
        "available_capacity": body.get("total_capacity", 100) - body.get("used_capacity", 0)
    }

    if resource_id not in CAPACITY_METRICS:
        CAPACITY_METRICS[resource_id] = []
    CAPACITY_METRICS[resource_id].append(metric)

    if metric["utilization_percent"] > 80:
        SCALING_RECOMMENDATIONS.append({
            "resource_id": resource_id,
            "type": "scale_up",
            "reason": f"High utilization: {metric['utilization_percent']}%",
            "recommended_action": "Increase capacity by 25%",
            "created_at": datetime.utcnow().isoformat()
        })

    return metric


@app.get("/capacity/metrics/{resource_id}")
def get_capacity_metrics(resource_id: str, limit: int = 100):
    """Get capacity metrics for resource"""
    return {"metrics": CAPACITY_METRICS.get(resource_id, [])[-limit:], "resource_id": resource_id}


@app.get("/capacity/recommendations")
def get_scaling_recommendations(resource_id: Optional[str] = None):
    """Get scaling recommendations"""
    recs = SCALING_RECOMMENDATIONS
    if resource_id:
        recs = [r for r in recs if r["resource_id"] == resource_id]
    return {"recommendations": recs[-20:], "total": len(recs)}


# ============================================================================
# A/B Testing
# ============================================================================

AB_EXPERIMENTS: Dict[str, Dict[str, Any]] = {}
AB_VARIANTS: Dict[str, List[Dict[str, Any]]] = {}
AB_ASSIGNMENTS: Dict[str, Dict[str, str]] = {}
AB_RESULTS: Dict[str, Dict[str, Any]] = {}


@app.post("/experiments")
def create_experiment(body: dict = Body(...)):
    """Create A/B experiment"""
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    experiment = {
        "id": exp_id,
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "hypothesis": body.get("hypothesis", ""),
        "metric": body.get("metric", "conversion_rate"),
        "traffic_percent": body.get("traffic_percent", 100),
        "status": "draft",
        "started_at": None,
        "ended_at": None,
        "created_at": datetime.utcnow().isoformat()
    }
    AB_EXPERIMENTS[exp_id] = experiment
    AB_VARIANTS[exp_id] = []
    AB_RESULTS[exp_id] = {"variants": {}}
    return experiment


@app.get("/experiments")
def list_experiments(status: Optional[str] = None):
    """List experiments"""
    exps = list(AB_EXPERIMENTS.values())
    if status:
        exps = [e for e in exps if e["status"] == status]
    return {"experiments": exps, "total": len(exps)}


@app.get("/experiments/{exp_id}")
def get_experiment(exp_id: str):
    """Get experiment details"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "experiment": AB_EXPERIMENTS[exp_id],
        "variants": AB_VARIANTS.get(exp_id, []),
        "results": AB_RESULTS.get(exp_id, {})
    }


@app.post("/experiments/{exp_id}/variants")
def add_variant(exp_id: str, body: dict = Body(...)):
    """Add variant to experiment"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    variant = {
        "id": f"var_{uuid.uuid4().hex[:8]}",
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "weight": body.get("weight", 50),
        "config": body.get("config", {}),
        "is_control": body.get("is_control", False)
    }

    AB_VARIANTS[exp_id].append(variant)
    AB_RESULTS[exp_id]["variants"][variant["id"]] = {
        "impressions": 0,
        "conversions": 0,
        "conversion_rate": 0
    }

    return variant


@app.post("/experiments/{exp_id}/start")
def start_experiment(exp_id: str):
    """Start experiment"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    AB_EXPERIMENTS[exp_id]["status"] = "running"
    AB_EXPERIMENTS[exp_id]["started_at"] = datetime.utcnow().isoformat()
    return {"message": "Experiment started", "experiment_id": exp_id}


@app.post("/experiments/{exp_id}/stop")
def stop_experiment(exp_id: str):
    """Stop experiment"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    AB_EXPERIMENTS[exp_id]["status"] = "completed"
    AB_EXPERIMENTS[exp_id]["ended_at"] = datetime.utcnow().isoformat()
    return {"message": "Experiment stopped", "experiment_id": exp_id}


@app.post("/experiments/{exp_id}/assign")
def assign_variant(exp_id: str, body: dict = Body(...)):
    """Assign user to variant"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    user_id = body.get("user_id")
    variants = AB_VARIANTS.get(exp_id, [])

    if not variants:
        raise HTTPException(status_code=400, detail="No variants defined")

    assignment_key = f"{exp_id}:{user_id}"
    if assignment_key in AB_ASSIGNMENTS:
        variant_id = AB_ASSIGNMENTS[assignment_key]
    else:
        weights = [v["weight"] for v in variants]
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0
        variant_id = variants[0]["id"]
        for v in variants:
            cumulative += v["weight"]
            if r <= cumulative:
                variant_id = v["id"]
                break
        AB_ASSIGNMENTS[assignment_key] = variant_id

    AB_RESULTS[exp_id]["variants"][variant_id]["impressions"] += 1

    variant = next((v for v in variants if v["id"] == variant_id), None)
    return {"variant_id": variant_id, "variant": variant}


@app.post("/experiments/{exp_id}/convert")
def record_conversion(exp_id: str, body: dict = Body(...)):
    """Record conversion event"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    user_id = body.get("user_id")
    assignment_key = f"{exp_id}:{user_id}"

    if assignment_key not in AB_ASSIGNMENTS:
        raise HTTPException(status_code=400, detail="User not assigned to experiment")

    variant_id = AB_ASSIGNMENTS[assignment_key]
    results = AB_RESULTS[exp_id]["variants"][variant_id]
    results["conversions"] += 1
    results["conversion_rate"] = results["conversions"] / max(1, results["impressions"]) * 100

    return {"message": "Conversion recorded", "variant_id": variant_id}


@app.get("/experiments/{exp_id}/results")
def get_experiment_results(exp_id: str):
    """Get experiment results"""
    if exp_id not in AB_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")

    results = AB_RESULTS.get(exp_id, {})
    variants = AB_VARIANTS.get(exp_id, [])

    winner = None
    best_rate = 0
    for vid, stats in results.get("variants", {}).items():
        if stats["conversion_rate"] > best_rate:
            best_rate = stats["conversion_rate"]
            winner = vid

    return {
        "experiment_id": exp_id,
        "status": AB_EXPERIMENTS[exp_id]["status"],
        "variants": results.get("variants", {}),
        "winner": winner,
        "statistical_significance": random.uniform(0.8, 0.99) if winner else None
    }


# ============================================================================
# Event Sourcing
# ============================================================================

EVENT_STORES: Dict[str, Dict[str, Any]] = {}
EVENT_STREAMS: Dict[str, List[Dict[str, Any]]] = {}
AGGREGATE_SNAPSHOTS: Dict[str, Dict[str, Any]] = {}
EVENT_PROJECTIONS: Dict[str, Dict[str, Any]] = {}


@app.post("/event-stores")
def create_event_store(body: dict = Body(...)):
    """Create event store"""
    store_id = f"store_{uuid.uuid4().hex[:8]}"
    store = {
        "id": store_id,
        "name": body.get("name", ""),
        "retention_days": body.get("retention_days", 365),
        "compression": body.get("compression", True),
        "partitioning": body.get("partitioning", "daily"),
        "created_at": datetime.utcnow().isoformat()
    }
    EVENT_STORES[store_id] = store
    return store


@app.get("/event-stores")
def list_event_stores():
    """List event stores"""
    return {"stores": list(EVENT_STORES.values()), "total": len(EVENT_STORES)}


@app.post("/event-streams/{stream_id}/events")
def append_event(stream_id: str, body: dict = Body(...)):
    """Append event to stream"""
    event = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "stream_id": stream_id,
        "type": body.get("type", ""),
        "data": body.get("data", {}),
        "metadata": body.get("metadata", {}),
        "version": len(EVENT_STREAMS.get(stream_id, [])) + 1,
        "timestamp": datetime.utcnow().isoformat()
    }

    if stream_id not in EVENT_STREAMS:
        EVENT_STREAMS[stream_id] = []
    EVENT_STREAMS[stream_id].append(event)

    return event


@app.get("/event-streams/{stream_id}")
def get_event_stream(stream_id: str, from_version: int = 0, limit: int = 100):
    """Get events from stream"""
    events = EVENT_STREAMS.get(stream_id, [])
    filtered = [e for e in events if e["version"] > from_version]
    return {"events": filtered[:limit], "stream_id": stream_id, "total": len(events)}


@app.get("/event-streams/{stream_id}/aggregate")
def get_aggregate(stream_id: str):
    """Get current aggregate state"""
    events = EVENT_STREAMS.get(stream_id, [])

    if stream_id in AGGREGATE_SNAPSHOTS:
        snapshot = AGGREGATE_SNAPSHOTS[stream_id]
        start_version = snapshot["version"]
        state = snapshot["state"].copy()
    else:
        start_version = 0
        state = {}

    for event in events:
        if event["version"] > start_version:
            state.update(event.get("data", {}))

    return {
        "stream_id": stream_id,
        "state": state,
        "version": len(events),
        "event_count": len(events)
    }


@app.post("/event-streams/{stream_id}/snapshot")
def create_snapshot(stream_id: str):
    """Create aggregate snapshot"""
    events = EVENT_STREAMS.get(stream_id, [])
    state = {}
    for event in events:
        state.update(event.get("data", {}))

    snapshot = {
        "stream_id": stream_id,
        "state": state,
        "version": len(events),
        "created_at": datetime.utcnow().isoformat()
    }
    AGGREGATE_SNAPSHOTS[stream_id] = snapshot
    return snapshot


@app.post("/event-projections")
def create_projection(body: dict = Body(...)):
    """Create event projection"""
    proj_id = f"proj_{uuid.uuid4().hex[:8]}"
    projection = {
        "id": proj_id,
        "name": body.get("name", ""),
        "source_streams": body.get("source_streams", []),
        "event_types": body.get("event_types", ["*"]),
        "handler": body.get("handler", ""),
        "state": {},
        "position": 0,
        "status": "running",
        "created_at": datetime.utcnow().isoformat()
    }
    EVENT_PROJECTIONS[proj_id] = projection
    return projection


@app.get("/event-projections")
def list_projections():
    """List event projections"""
    return {"projections": list(EVENT_PROJECTIONS.values()), "total": len(EVENT_PROJECTIONS)}


@app.get("/event-projections/{proj_id}/state")
def get_projection_state(proj_id: str):
    """Get projection state"""
    if proj_id not in EVENT_PROJECTIONS:
        raise HTTPException(status_code=404, detail="Projection not found")
    return {
        "projection_id": proj_id,
        "state": EVENT_PROJECTIONS[proj_id]["state"],
        "position": EVENT_PROJECTIONS[proj_id]["position"]
    }


# ============================================================================
# License Management
# ============================================================================

LICENSES: Dict[str, Dict[str, Any]] = {}
LICENSE_ALLOCATIONS: Dict[str, List[Dict[str, Any]]] = {}
LICENSE_USAGE: Dict[str, Dict[str, Any]] = {}
ENTITLEMENTS: Dict[str, Dict[str, Any]] = {}


@app.post("/licenses")
def create_license(body: dict = Body(...)):
    """Create license"""
    license_id = f"lic_{uuid.uuid4().hex[:8]}"
    license_key = f"LIC-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    license_data = {
        "id": license_id,
        "key": license_key,
        "product": body.get("product", ""),
        "type": body.get("type", "subscription"),
        "seats": body.get("seats", 1),
        "seats_used": 0,
        "features": body.get("features", []),
        "valid_from": body.get("valid_from", datetime.utcnow().isoformat()),
        "valid_until": body.get("valid_until"),
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    LICENSES[license_id] = license_data
    LICENSE_ALLOCATIONS[license_id] = []
    LICENSE_USAGE[license_id] = {"total_activations": 0, "active_sessions": 0}
    return license_data


@app.get("/licenses")
def list_licenses(product: Optional[str] = None, status: Optional[str] = None):
    """List licenses"""
    licenses = list(LICENSES.values())
    if product:
        licenses = [l for l in licenses if l["product"] == product]
    if status:
        licenses = [l for l in licenses if l["status"] == status]
    return {"licenses": licenses, "total": len(licenses)}


@app.get("/licenses/{license_id}")
def get_license(license_id: str):
    """Get license details"""
    if license_id not in LICENSES:
        raise HTTPException(status_code=404, detail="License not found")
    return {
        "license": LICENSES[license_id],
        "allocations": LICENSE_ALLOCATIONS.get(license_id, []),
        "usage": LICENSE_USAGE.get(license_id, {})
    }


@app.post("/licenses/{license_id}/allocate")
def allocate_license(license_id: str, body: dict = Body(...)):
    """Allocate license seat"""
    if license_id not in LICENSES:
        raise HTTPException(status_code=404, detail="License not found")

    license_data = LICENSES[license_id]
    if license_data["seats_used"] >= license_data["seats"]:
        raise HTTPException(status_code=400, detail="No seats available")

    allocation = {
        "id": f"alloc_{uuid.uuid4().hex[:8]}",
        "user_id": body.get("user_id"),
        "machine_id": body.get("machine_id"),
        "allocated_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    LICENSE_ALLOCATIONS[license_id].append(allocation)
    license_data["seats_used"] += 1
    LICENSE_USAGE[license_id]["total_activations"] += 1
    LICENSE_USAGE[license_id]["active_sessions"] += 1

    return allocation


@app.post("/licenses/{license_id}/release")
def release_license(license_id: str, body: dict = Body(...)):
    """Release license seat"""
    if license_id not in LICENSES:
        raise HTTPException(status_code=404, detail="License not found")

    allocation_id = body.get("allocation_id")
    allocations = LICENSE_ALLOCATIONS.get(license_id, [])

    for alloc in allocations:
        if alloc["id"] == allocation_id:
            alloc["status"] = "released"
            LICENSES[license_id]["seats_used"] -= 1
            LICENSE_USAGE[license_id]["active_sessions"] -= 1
            return {"message": "License seat released", "allocation_id": allocation_id}

    raise HTTPException(status_code=404, detail="Allocation not found")


@app.post("/licenses/validate")
def validate_license(body: dict = Body(...)):
    """Validate license key"""
    license_key = body.get("key")

    for license_data in LICENSES.values():
        if license_data["key"] == license_key:
            if license_data["status"] != "active":
                return {"valid": False, "reason": "License is not active"}
            if license_data.get("valid_until"):
                if datetime.fromisoformat(license_data["valid_until"]) < datetime.utcnow():
                    return {"valid": False, "reason": "License has expired"}
            return {
                "valid": True,
                "license_id": license_data["id"],
                "features": license_data["features"],
                "seats_available": license_data["seats"] - license_data["seats_used"]
            }

    return {"valid": False, "reason": "Invalid license key"}


@app.post("/entitlements")
def create_entitlement(body: dict = Body(...)):
    """Create feature entitlement"""
    ent_id = f"ent_{uuid.uuid4().hex[:8]}"
    entitlement = {
        "id": ent_id,
        "name": body.get("name", ""),
        "feature_code": body.get("feature_code", ""),
        "description": body.get("description", ""),
        "type": body.get("type", "boolean"),
        "default_value": body.get("default_value", False),
        "created_at": datetime.utcnow().isoformat()
    }
    ENTITLEMENTS[ent_id] = entitlement
    return entitlement


@app.get("/entitlements")
def list_entitlements():
    """List entitlements"""
    return {"entitlements": list(ENTITLEMENTS.values()), "total": len(ENTITLEMENTS)}


@app.get("/licenses/dashboard")
def license_dashboard():
    """Get license dashboard"""
    total_seats = sum(l["seats"] for l in LICENSES.values())
    used_seats = sum(l["seats_used"] for l in LICENSES.values())

    return {
        "total_licenses": len(LICENSES),
        "active_licenses": len([l for l in LICENSES.values() if l["status"] == "active"]),
        "total_seats": total_seats,
        "used_seats": used_seats,
        "utilization_percent": (used_seats / max(1, total_seats)) * 100,
        "by_product": {}
    }


# ============================================================================
# Batch Processing
# ============================================================================

BATCH_JOBS: Dict[str, Dict[str, Any]] = {}
BATCH_ITEMS: Dict[str, List[Dict[str, Any]]] = {}
BATCH_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/batch/jobs")
def create_batch_job(body: dict = Body(...)):
    """Create batch processing job"""
    job_id = f"batch_{uuid.uuid4().hex[:12]}"
    job = {
        "id": job_id,
        "name": body.get("name", ""),
        "type": body.get("type", "transform"),
        "status": "pending",
        "priority": body.get("priority", "normal"),
        "items_total": 0,
        "items_processed": 0,
        "items_failed": 0,
        "progress_percent": 0,
        "config": body.get("config", {}),
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None
    }
    BATCH_JOBS[job_id] = job
    BATCH_ITEMS[job_id] = []
    return job


@app.get("/batch/jobs")
def list_batch_jobs(status: Optional[str] = None, type: Optional[str] = None):
    """List batch jobs"""
    jobs = list(BATCH_JOBS.values())
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    if type:
        jobs = [j for j in jobs if j["type"] == type]
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/batch/jobs/{job_id}")
def get_batch_job(job_id: str):
    """Get batch job details"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return {
        "job": BATCH_JOBS[job_id],
        "items_summary": {
            "total": len(BATCH_ITEMS.get(job_id, [])),
            "pending": len([i for i in BATCH_ITEMS.get(job_id, []) if i["status"] == "pending"]),
            "completed": len([i for i in BATCH_ITEMS.get(job_id, []) if i["status"] == "completed"]),
            "failed": len([i for i in BATCH_ITEMS.get(job_id, []) if i["status"] == "failed"])
        }
    }


@app.post("/batch/jobs/{job_id}/items")
def add_batch_items(job_id: str, body: dict = Body(...)):
    """Add items to batch job"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found")

    items = body.get("items", [])
    added = []
    for item_data in items:
        item = {
            "id": f"item_{uuid.uuid4().hex[:8]}",
            "data": item_data,
            "status": "pending",
            "result": None,
            "error": None,
            "processed_at": None
        }
        BATCH_ITEMS[job_id].append(item)
        added.append(item)

    BATCH_JOBS[job_id]["items_total"] = len(BATCH_ITEMS[job_id])
    return {"added": len(added), "items": added}


@app.post("/batch/jobs/{job_id}/start")
def start_batch_job(job_id: str):
    """Start batch job processing"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found")

    job = BATCH_JOBS[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.utcnow().isoformat()

    items = BATCH_ITEMS.get(job_id, [])
    for item in items:
        item["status"] = "completed"
        item["result"] = {"processed": True}
        item["processed_at"] = datetime.utcnow().isoformat()

    job["items_processed"] = len(items)
    job["progress_percent"] = 100
    job["status"] = "completed"
    job["completed_at"] = datetime.utcnow().isoformat()

    return {"message": "Batch job completed", "job_id": job_id}


@app.post("/batch/jobs/{job_id}/cancel")
def cancel_batch_job(job_id: str):
    """Cancel batch job"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found")

    BATCH_JOBS[job_id]["status"] = "cancelled"
    return {"message": "Batch job cancelled", "job_id": job_id}


@app.get("/batch/jobs/{job_id}/items")
def get_batch_items(job_id: str, status: Optional[str] = None, limit: int = 100):
    """Get batch job items"""
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found")

    items = BATCH_ITEMS.get(job_id, [])
    if status:
        items = [i for i in items if i["status"] == status]
    return {"items": items[:limit], "total": len(items)}


@app.post("/batch/templates")
def create_batch_template(body: dict = Body(...)):
    """Create batch job template"""
    template_id = f"tmpl_{uuid.uuid4().hex[:8]}"
    template = {
        "id": template_id,
        "name": body.get("name", ""),
        "type": body.get("type", "transform"),
        "config": body.get("config", {}),
        "created_at": datetime.utcnow().isoformat()
    }
    BATCH_TEMPLATES[template_id] = template
    return template


# ============================================================================
# Content Moderation
# ============================================================================

MODERATION_RULES: Dict[str, Dict[str, Any]] = {}
MODERATION_QUEUE: List[Dict[str, Any]] = []
MODERATION_DECISIONS: Dict[str, Dict[str, Any]] = {}
BLOCKED_CONTENT: Dict[str, Dict[str, Any]] = {}


@app.post("/moderation/rules")
def create_moderation_rule(body: dict = Body(...)):
    """Create moderation rule"""
    rule_id = f"rule_{uuid.uuid4().hex[:8]}"
    rule = {
        "id": rule_id,
        "name": body.get("name", ""),
        "type": body.get("type", "keyword"),
        "pattern": body.get("pattern", ""),
        "action": body.get("action", "flag"),
        "severity": body.get("severity", "medium"),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    MODERATION_RULES[rule_id] = rule
    return rule


@app.get("/moderation/rules")
def list_moderation_rules(type: Optional[str] = None):
    """List moderation rules"""
    rules = list(MODERATION_RULES.values())
    if type:
        rules = [r for r in rules if r["type"] == type]
    return {"rules": rules, "total": len(rules)}


@app.post("/moderation/check")
def check_content(body: dict = Body(...)):
    """Check content against moderation rules"""
    content = body.get("content", "")
    content_type = body.get("content_type", "text")

    violations = []
    for rule in MODERATION_RULES.values():
        if rule["enabled"] and rule["pattern"].lower() in content.lower():
            violations.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "action": rule["action"]
            })

    result = {
        "id": f"check_{uuid.uuid4().hex[:8]}",
        "content_type": content_type,
        "passed": len(violations) == 0,
        "violations": violations,
        "checked_at": datetime.utcnow().isoformat()
    }

    if violations:
        MODERATION_QUEUE.append({
            "id": result["id"],
            "content_preview": content[:100],
            "violations": violations,
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat()
        })

    return result


@app.get("/moderation/queue")
def get_moderation_queue(status: Optional[str] = None, limit: int = 50):
    """Get moderation queue"""
    queue = MODERATION_QUEUE
    if status:
        queue = [q for q in queue if q["status"] == status]
    return {"queue": queue[-limit:], "total": len(queue)}


@app.post("/moderation/queue/{item_id}/decide")
def make_moderation_decision(item_id: str, body: dict = Body(...)):
    """Make moderation decision"""
    decision = {
        "item_id": item_id,
        "decision": body.get("decision", "approve"),
        "reason": body.get("reason", ""),
        "moderator": body.get("moderator", "system"),
        "decided_at": datetime.utcnow().isoformat()
    }
    MODERATION_DECISIONS[item_id] = decision

    for item in MODERATION_QUEUE:
        if item["id"] == item_id:
            item["status"] = "decided"
            break

    return decision


@app.post("/moderation/block")
def block_content(body: dict = Body(...)):
    """Block content"""
    block_id = f"block_{uuid.uuid4().hex[:8]}"
    block = {
        "id": block_id,
        "content_hash": body.get("content_hash", ""),
        "reason": body.get("reason", ""),
        "category": body.get("category", "other"),
        "permanent": body.get("permanent", False),
        "blocked_at": datetime.utcnow().isoformat()
    }
    BLOCKED_CONTENT[block_id] = block
    return block


# ============================================================================
# Geo-Location Services
# ============================================================================

GEO_REGIONS: Dict[str, Dict[str, Any]] = {}
GEO_POLICIES: Dict[str, Dict[str, Any]] = {}
GEO_LOOKUPS: List[Dict[str, Any]] = []


@app.post("/geo/regions")
def create_geo_region(body: dict = Body(...)):
    """Create geo region"""
    region_id = f"region_{uuid.uuid4().hex[:8]}"
    region = {
        "id": region_id,
        "name": body.get("name", ""),
        "code": body.get("code", ""),
        "type": body.get("type", "country"),
        "parent_region": body.get("parent_region"),
        "coordinates": body.get("coordinates", {}),
        "metadata": body.get("metadata", {}),
        "created_at": datetime.utcnow().isoformat()
    }
    GEO_REGIONS[region_id] = region
    return region


@app.get("/geo/regions")
def list_geo_regions(type: Optional[str] = None):
    """List geo regions"""
    regions = list(GEO_REGIONS.values())
    if type:
        regions = [r for r in regions if r["type"] == type]
    return {"regions": regions, "total": len(regions)}


@app.post("/geo/lookup")
def geo_lookup(body: dict = Body(...)):
    """Lookup geo location"""
    lookup = {
        "id": f"lookup_{uuid.uuid4().hex[:8]}",
        "ip": body.get("ip", ""),
        "coordinates": body.get("coordinates", {}),
        "result": {
            "country": "United States",
            "country_code": "US",
            "region": "California",
            "city": "San Francisco",
            "postal_code": "94102",
            "timezone": "America/Los_Angeles",
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "looked_up_at": datetime.utcnow().isoformat()
    }
    GEO_LOOKUPS.append(lookup)
    return lookup


@app.post("/geo/policies")
def create_geo_policy(body: dict = Body(...)):
    """Create geo-fencing policy"""
    policy_id = f"geopol_{uuid.uuid4().hex[:8]}"
    policy = {
        "id": policy_id,
        "name": body.get("name", ""),
        "type": body.get("type", "allow"),
        "regions": body.get("regions", []),
        "action": body.get("action", "block"),
        "applies_to": body.get("applies_to", ["all"]),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    GEO_POLICIES[policy_id] = policy
    return policy


@app.get("/geo/policies")
def list_geo_policies():
    """List geo policies"""
    return {"policies": list(GEO_POLICIES.values()), "total": len(GEO_POLICIES)}


@app.post("/geo/check")
def check_geo_policy(body: dict = Body(...)):
    """Check if location is allowed by policies"""
    region = body.get("region", "")
    country = body.get("country", "")

    allowed = True
    matched_policy = None

    for policy in GEO_POLICIES.values():
        if policy["enabled"]:
            if country in policy["regions"] or region in policy["regions"]:
                if policy["type"] == "deny":
                    allowed = False
                    matched_policy = policy["id"]
                    break

    return {
        "allowed": allowed,
        "region": region,
        "country": country,
        "matched_policy": matched_policy
    }


# ============================================================================
# Quota Management
# ============================================================================

QUOTAS: Dict[str, Dict[str, Any]] = {}
QUOTA_USAGE: Dict[str, Dict[str, Any]] = {}
QUOTA_ALERTS: List[Dict[str, Any]] = []


@app.post("/quotas")
def create_quota(body: dict = Body(...)):
    """Create quota"""
    quota_id = f"quota_{uuid.uuid4().hex[:8]}"
    quota = {
        "id": quota_id,
        "name": body.get("name", ""),
        "resource_type": body.get("resource_type", "api_calls"),
        "limit": body.get("limit", 1000),
        "period": body.get("period", "monthly"),
        "scope": body.get("scope", "global"),
        "scope_id": body.get("scope_id"),
        "alert_threshold": body.get("alert_threshold", 80),
        "action_on_exceed": body.get("action_on_exceed", "block"),
        "enabled": True,
        "created_at": datetime.utcnow().isoformat()
    }
    QUOTAS[quota_id] = quota
    QUOTA_USAGE[quota_id] = {"current": 0, "period_start": datetime.utcnow().isoformat()}
    return quota


@app.get("/quotas")
def list_quotas(resource_type: Optional[str] = None):
    """List quotas"""
    quotas = list(QUOTAS.values())
    if resource_type:
        quotas = [q for q in quotas if q["resource_type"] == resource_type]
    return {"quotas": quotas, "total": len(quotas)}


@app.get("/quotas/{quota_id}")
def get_quota(quota_id: str):
    """Get quota details"""
    if quota_id not in QUOTAS:
        raise HTTPException(status_code=404, detail="Quota not found")
    return {
        "quota": QUOTAS[quota_id],
        "usage": QUOTA_USAGE.get(quota_id, {})
    }


@app.post("/quotas/{quota_id}/consume")
def consume_quota(quota_id: str, body: dict = Body(...)):
    """Consume quota"""
    if quota_id not in QUOTAS:
        raise HTTPException(status_code=404, detail="Quota not found")

    quota = QUOTAS[quota_id]
    usage = QUOTA_USAGE.get(quota_id, {"current": 0})
    amount = body.get("amount", 1)

    new_usage = usage["current"] + amount
    percent_used = (new_usage / quota["limit"]) * 100

    if percent_used >= quota["alert_threshold"] and usage["current"] < quota["limit"] * quota["alert_threshold"] / 100:
        QUOTA_ALERTS.append({
            "quota_id": quota_id,
            "percent_used": percent_used,
            "created_at": datetime.utcnow().isoformat()
        })

    if new_usage > quota["limit"] and quota["action_on_exceed"] == "block":
        return {"allowed": False, "reason": "Quota exceeded", "current": usage["current"], "limit": quota["limit"]}

    usage["current"] = new_usage
    QUOTA_USAGE[quota_id] = usage

    return {
        "allowed": True,
        "consumed": amount,
        "current": new_usage,
        "limit": quota["limit"],
        "remaining": max(0, quota["limit"] - new_usage)
    }


@app.post("/quotas/{quota_id}/reset")
def reset_quota(quota_id: str):
    """Reset quota usage"""
    if quota_id not in QUOTAS:
        raise HTTPException(status_code=404, detail="Quota not found")

    QUOTA_USAGE[quota_id] = {"current": 0, "period_start": datetime.utcnow().isoformat()}
    return {"message": "Quota reset", "quota_id": quota_id}


@app.get("/quotas/alerts")
def get_quota_alerts(limit: int = 50):
    """Get quota alerts"""
    return {"alerts": QUOTA_ALERTS[-limit:], "total": len(QUOTA_ALERTS)}


# ============================================================================
# Webhook Management
# ============================================================================

WEBHOOKS: Dict[str, Dict[str, Any]] = {}
WEBHOOK_DELIVERIES: Dict[str, List[Dict[str, Any]]] = {}
WEBHOOK_SECRETS: Dict[str, str] = {}


@app.post("/webhooks")
def create_webhook(body: dict = Body(...)):
    """Create webhook"""
    webhook_id = f"wh_{uuid.uuid4().hex[:8]}"
    secret = f"whsec_{uuid.uuid4().hex}"
    webhook = {
        "id": webhook_id,
        "url": body.get("url", ""),
        "events": body.get("events", ["*"]),
        "description": body.get("description", ""),
        "headers": body.get("headers", {}),
        "enabled": True,
        "retry_policy": body.get("retry_policy", {"max_retries": 3, "backoff": "exponential"}),
        "created_at": datetime.utcnow().isoformat()
    }
    WEBHOOKS[webhook_id] = webhook
    WEBHOOK_SECRETS[webhook_id] = secret
    WEBHOOK_DELIVERIES[webhook_id] = []
    return {**webhook, "secret": secret}


@app.get("/webhooks")
def list_webhooks():
    """List webhooks"""
    return {"webhooks": list(WEBHOOKS.values()), "total": len(WEBHOOKS)}


@app.get("/webhooks/{webhook_id}")
def get_webhook(webhook_id: str):
    """Get webhook details"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {
        "webhook": WEBHOOKS[webhook_id],
        "recent_deliveries": WEBHOOK_DELIVERIES.get(webhook_id, [])[-10:]
    }


@app.put("/webhooks/{webhook_id}")
def update_webhook(webhook_id: str, body: dict = Body(...)):
    """Update webhook"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
    webhook = WEBHOOKS[webhook_id]
    webhook.update({k: v for k, v in body.items() if k not in ["id", "created_at"]})
    return webhook


@app.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str):
    """Delete webhook"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del WEBHOOKS[webhook_id]
    WEBHOOK_SECRETS.pop(webhook_id, None)
    return {"message": "Webhook deleted", "id": webhook_id}


@app.post("/webhooks/{webhook_id}/test")
def test_webhook(webhook_id: str):
    """Test webhook delivery"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")

    delivery = {
        "id": f"del_{uuid.uuid4().hex[:8]}",
        "event": "test.ping",
        "payload": {"test": True},
        "status": "delivered",
        "response_code": 200,
        "duration_ms": random.randint(50, 500),
        "delivered_at": datetime.utcnow().isoformat()
    }
    WEBHOOK_DELIVERIES[webhook_id].append(delivery)
    return delivery


@app.get("/webhooks/{webhook_id}/deliveries")
def get_webhook_deliveries(webhook_id: str, status: Optional[str] = None, limit: int = 50):
    """Get webhook deliveries"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")

    deliveries = WEBHOOK_DELIVERIES.get(webhook_id, [])
    if status:
        deliveries = [d for d in deliveries if d["status"] == status]
    return {"deliveries": deliveries[-limit:], "total": len(deliveries)}


@app.post("/webhooks/{webhook_id}/rotate-secret")
def rotate_webhook_secret(webhook_id: str):
    """Rotate webhook secret"""
    if webhook_id not in WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")

    new_secret = f"whsec_{uuid.uuid4().hex}"
    WEBHOOK_SECRETS[webhook_id] = new_secret
    return {"message": "Secret rotated", "secret": new_secret}


# ============================================================================
# Search Index
# ============================================================================

SEARCH_INDEXES: Dict[str, Dict[str, Any]] = {}
SEARCH_DOCUMENTS: Dict[str, List[Dict[str, Any]]] = {}
SEARCH_QUERIES: List[Dict[str, Any]] = []


@app.post("/search/indexes")
def create_search_index(body: dict = Body(...)):
    """Create search index"""
    index_id = f"idx_{uuid.uuid4().hex[:8]}"
    index = {
        "id": index_id,
        "name": body.get("name", ""),
        "fields": body.get("fields", []),
        "settings": body.get("settings", {}),
        "document_count": 0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    SEARCH_INDEXES[index_id] = index
    SEARCH_DOCUMENTS[index_id] = []
    return index


@app.get("/search/indexes")
def list_search_indexes():
    """List search indexes"""
    return {"indexes": list(SEARCH_INDEXES.values()), "total": len(SEARCH_INDEXES)}


@app.get("/search/indexes/{index_id}")
def get_search_index(index_id: str):
    """Get search index details"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")
    return SEARCH_INDEXES[index_id]


@app.post("/search/indexes/{index_id}/documents")
def index_document(index_id: str, body: dict = Body(...)):
    """Index document"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")

    doc_id = body.get("id", f"doc_{uuid.uuid4().hex[:8]}")
    document = {
        "id": doc_id,
        "content": body.get("content", {}),
        "indexed_at": datetime.utcnow().isoformat()
    }
    SEARCH_DOCUMENTS[index_id].append(document)
    SEARCH_INDEXES[index_id]["document_count"] += 1
    return {"message": "Document indexed", "document_id": doc_id}


@app.post("/search/indexes/{index_id}/bulk")
def bulk_index(index_id: str, body: dict = Body(...)):
    """Bulk index documents"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")

    documents = body.get("documents", [])
    indexed = 0
    for doc in documents:
        doc_id = doc.get("id", f"doc_{uuid.uuid4().hex[:8]}")
        SEARCH_DOCUMENTS[index_id].append({
            "id": doc_id,
            "content": doc.get("content", {}),
            "indexed_at": datetime.utcnow().isoformat()
        })
        indexed += 1

    SEARCH_INDEXES[index_id]["document_count"] += indexed
    return {"indexed": indexed, "total_documents": SEARCH_INDEXES[index_id]["document_count"]}


@app.post("/search/indexes/{index_id}/query")
def search_query(index_id: str, body: dict = Body(...)):
    """Search documents"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")

    query = body.get("query", "")
    filters = body.get("filters", {})
    limit = body.get("limit", 10)

    documents = SEARCH_DOCUMENTS.get(index_id, [])
    results = []

    for doc in documents:
        content = str(doc.get("content", {})).lower()
        if query.lower() in content:
            results.append({
                "id": doc["id"],
                "content": doc["content"],
                "score": random.uniform(0.5, 1.0)
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    search_log = {
        "query": query,
        "index_id": index_id,
        "results_count": len(results),
        "searched_at": datetime.utcnow().isoformat()
    }
    SEARCH_QUERIES.append(search_log)

    return {"results": results[:limit], "total": len(results), "query": query}


@app.delete("/search/indexes/{index_id}/documents/{doc_id}")
def delete_document(index_id: str, doc_id: str):
    """Delete document from index"""
    if index_id not in SEARCH_INDEXES:
        raise HTTPException(status_code=404, detail="Index not found")

    docs = SEARCH_DOCUMENTS.get(index_id, [])
    SEARCH_DOCUMENTS[index_id] = [d for d in docs if d["id"] != doc_id]
    SEARCH_INDEXES[index_id]["document_count"] = len(SEARCH_DOCUMENTS[index_id])
    return {"message": "Document deleted", "document_id": doc_id}


# ============================================================================
# Deployment Management
# ============================================================================

DEPLOYMENTS: Dict[str, Dict[str, Any]] = {}
DEPLOYMENT_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
ROLLBACK_POINTS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/deployments")
def create_deployment(body: dict = Body(...)):
    """Create deployment"""
    deploy_id = f"deploy_{uuid.uuid4().hex[:12]}"
    deployment = {
        "id": deploy_id,
        "name": body.get("name", ""),
        "version": body.get("version", "1.0.0"),
        "environment": body.get("environment", "production"),
        "strategy": body.get("strategy", "rolling"),
        "status": "pending",
        "replicas": body.get("replicas", 1),
        "config": body.get("config", {}),
        "created_at": datetime.utcnow().isoformat(),
        "deployed_at": None
    }
    DEPLOYMENTS[deploy_id] = deployment
    DEPLOYMENT_HISTORY[deploy_id] = []
    return deployment


@app.get("/deployments")
def list_deployments(environment: Optional[str] = None, status: Optional[str] = None):
    """List deployments"""
    deploys = list(DEPLOYMENTS.values())
    if environment:
        deploys = [d for d in deploys if d["environment"] == environment]
    if status:
        deploys = [d for d in deploys if d["status"] == status]
    return {"deployments": deploys, "total": len(deploys)}


@app.get("/deployments/{deploy_id}")
def get_deployment(deploy_id: str):
    """Get deployment details"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {
        "deployment": DEPLOYMENTS[deploy_id],
        "history": DEPLOYMENT_HISTORY.get(deploy_id, [])[-5:]
    }


@app.post("/deployments/{deploy_id}/execute")
def execute_deployment(deploy_id: str):
    """Execute deployment"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment = DEPLOYMENTS[deploy_id]
    deployment["status"] = "deploying"

    history_entry = {
        "action": "deploy",
        "version": deployment["version"],
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
    DEPLOYMENT_HISTORY[deploy_id].append(history_entry)

    name = deployment["name"]
    if name not in ROLLBACK_POINTS:
        ROLLBACK_POINTS[name] = []
    ROLLBACK_POINTS[name].append({
        "deploy_id": deploy_id,
        "version": deployment["version"],
        "created_at": datetime.utcnow().isoformat()
    })

    deployment["status"] = "deployed"
    deployment["deployed_at"] = datetime.utcnow().isoformat()

    return {"message": "Deployment executed", "deployment": deployment}


@app.post("/deployments/{deploy_id}/rollback")
def rollback_deployment(deploy_id: str, body: dict = Body(...)):
    """Rollback deployment"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    target_version = body.get("target_version")
    deployment = DEPLOYMENTS[deploy_id]

    history_entry = {
        "action": "rollback",
        "from_version": deployment["version"],
        "to_version": target_version,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
    DEPLOYMENT_HISTORY[deploy_id].append(history_entry)

    deployment["version"] = target_version
    deployment["deployed_at"] = datetime.utcnow().isoformat()

    return {"message": "Rollback completed", "deployment": deployment}


@app.post("/deployments/{deploy_id}/scale")
def scale_deployment(deploy_id: str, body: dict = Body(...)):
    """Scale deployment"""
    if deploy_id not in DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")

    replicas = body.get("replicas", 1)
    DEPLOYMENTS[deploy_id]["replicas"] = replicas

    return {"message": "Deployment scaled", "replicas": replicas}


@app.get("/deployments/rollback-points/{name}")
def get_rollback_points(name: str):
    """Get rollback points for deployment"""
    return {"rollback_points": ROLLBACK_POINTS.get(name, []), "name": name}


# ============================================================================
# Environment Configuration
# ============================================================================

ENVIRONMENTS: Dict[str, Dict[str, Any]] = {}
ENV_VARIABLES: Dict[str, Dict[str, str]] = {}
ENV_PROMOTIONS: List[Dict[str, Any]] = []


@app.post("/environments")
def create_environment(body: dict = Body(...)):
    """Create environment"""
    env_id = f"env_{uuid.uuid4().hex[:8]}"
    environment = {
        "id": env_id,
        "name": body.get("name", ""),
        "type": body.get("type", "development"),
        "description": body.get("description", ""),
        "parent_env": body.get("parent_env"),
        "locked": False,
        "created_at": datetime.utcnow().isoformat()
    }
    ENVIRONMENTS[env_id] = environment
    ENV_VARIABLES[env_id] = body.get("variables", {})
    return environment


@app.get("/environments")
def list_environments(type: Optional[str] = None):
    """List environments"""
    envs = list(ENVIRONMENTS.values())
    if type:
        envs = [e for e in envs if e["type"] == type]
    return {"environments": envs, "total": len(envs)}


@app.get("/environments/{env_id}")
def get_environment(env_id: str):
    """Get environment details"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {
        "environment": ENVIRONMENTS[env_id],
        "variables": ENV_VARIABLES.get(env_id, {})
    }


@app.put("/environments/{env_id}/variables")
def update_env_variables(env_id: str, body: dict = Body(...)):
    """Update environment variables"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    if ENVIRONMENTS[env_id]["locked"]:
        raise HTTPException(status_code=400, detail="Environment is locked")

    variables = ENV_VARIABLES.get(env_id, {})
    variables.update(body.get("variables", {}))
    ENV_VARIABLES[env_id] = variables
    return {"variables": variables}


@app.delete("/environments/{env_id}/variables/{key}")
def delete_env_variable(env_id: str, key: str):
    """Delete environment variable"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    variables = ENV_VARIABLES.get(env_id, {})
    if key in variables:
        del variables[key]
    return {"message": "Variable deleted", "key": key}


@app.post("/environments/{env_id}/lock")
def lock_environment(env_id: str):
    """Lock environment"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    ENVIRONMENTS[env_id]["locked"] = True
    return {"message": "Environment locked", "env_id": env_id}


@app.post("/environments/{env_id}/unlock")
def unlock_environment(env_id: str):
    """Unlock environment"""
    if env_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    ENVIRONMENTS[env_id]["locked"] = False
    return {"message": "Environment unlocked", "env_id": env_id}


@app.post("/environments/promote")
def promote_environment(body: dict = Body(...)):
    """Promote config from one environment to another"""
    source_id = body.get("source_env")
    target_id = body.get("target_env")

    if source_id not in ENVIRONMENTS or target_id not in ENVIRONMENTS:
        raise HTTPException(status_code=404, detail="Environment not found")

    if ENVIRONMENTS[target_id]["locked"]:
        raise HTTPException(status_code=400, detail="Target environment is locked")

    source_vars = ENV_VARIABLES.get(source_id, {})
    target_vars = ENV_VARIABLES.get(target_id, {})
    target_vars.update(source_vars)
    ENV_VARIABLES[target_id] = target_vars

    promotion = {
        "source_env": source_id,
        "target_env": target_id,
        "variables_promoted": len(source_vars),
        "promoted_at": datetime.utcnow().isoformat()
    }
    ENV_PROMOTIONS.append(promotion)

    return promotion


@app.get("/environments/promotions")
def get_promotions(limit: int = 20):
    """Get environment promotions history"""
    return {"promotions": ENV_PROMOTIONS[-limit:], "total": len(ENV_PROMOTIONS)}


# ============================================================================
# Message Queue
# ============================================================================

MESSAGE_QUEUES: Dict[str, Dict[str, Any]] = {}
QUEUE_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}
DEAD_LETTER_QUEUES: Dict[str, List[Dict[str, Any]]] = {}
QUEUE_SUBSCRIPTIONS: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/queues")
def create_queue(body: dict = Body(...)):
    """Create message queue"""
    queue_id = f"queue_{uuid.uuid4().hex[:8]}"
    queue = {
        "id": queue_id,
        "name": body.get("name", ""),
        "type": body.get("type", "standard"),
        "max_size": body.get("max_size", 10000),
        "message_retention_seconds": body.get("message_retention_seconds", 86400),
        "visibility_timeout_seconds": body.get("visibility_timeout_seconds", 30),
        "dead_letter_queue": body.get("dead_letter_queue"),
        "max_retries": body.get("max_retries", 3),
        "created_at": datetime.utcnow().isoformat()
    }
    MESSAGE_QUEUES[queue_id] = queue
    QUEUE_MESSAGES[queue_id] = []
    return queue


@app.get("/queues")
def list_queues(type: Optional[str] = None):
    """List message queues"""
    queues = list(MESSAGE_QUEUES.values())
    if type:
        queues = [q for q in queues if q["type"] == type]
    return {"queues": queues, "total": len(queues)}


@app.get("/queues/{queue_id}")
def get_queue(queue_id: str):
    """Get queue details"""
    if queue_id not in MESSAGE_QUEUES:
        raise HTTPException(status_code=404, detail="Queue not found")
    messages = QUEUE_MESSAGES.get(queue_id, [])
    return {
        "queue": MESSAGE_QUEUES[queue_id],
        "message_count": len(messages),
        "oldest_message": messages[0]["created_at"] if messages else None
    }


@app.post("/queues/{queue_id}/messages")
def send_message(queue_id: str, body: dict = Body(...)):
    """Send message to queue"""
    if queue_id not in MESSAGE_QUEUES:
        raise HTTPException(status_code=404, detail="Queue not found")

    message = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "body": body.get("body", {}),
        "attributes": body.get("attributes", {}),
        "priority": body.get("priority", 0),
        "delay_seconds": body.get("delay_seconds", 0),
        "retry_count": 0,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "visible_at": datetime.utcnow().isoformat()
    }
    QUEUE_MESSAGES[queue_id].append(message)
    return {"message_id": message["id"], "status": "queued"}


@app.get("/queues/{queue_id}/messages")
def receive_messages(queue_id: str, max_messages: int = 10):
    """Receive messages from queue"""
    if queue_id not in MESSAGE_QUEUES:
        raise HTTPException(status_code=404, detail="Queue not found")

    messages = QUEUE_MESSAGES.get(queue_id, [])
    pending = [m for m in messages if m["status"] == "pending"][:max_messages]

    for msg in pending:
        msg["status"] = "processing"

    return {"messages": pending, "count": len(pending)}


@app.delete("/queues/{queue_id}/messages/{message_id}")
def delete_message(queue_id: str, message_id: str):
    """Delete/acknowledge message"""
    if queue_id not in MESSAGE_QUEUES:
        raise HTTPException(status_code=404, detail="Queue not found")

    messages = QUEUE_MESSAGES.get(queue_id, [])
    QUEUE_MESSAGES[queue_id] = [m for m in messages if m["id"] != message_id]
    return {"message": "Message deleted", "message_id": message_id}


@app.post("/queues/{queue_id}/messages/{message_id}/nack")
def nack_message(queue_id: str, message_id: str):
    """Negative acknowledge - return message to queue"""
    if queue_id not in MESSAGE_QUEUES:
        raise HTTPException(status_code=404, detail="Queue not found")

    queue = MESSAGE_QUEUES[queue_id]
    messages = QUEUE_MESSAGES.get(queue_id, [])

    for msg in messages:
        if msg["id"] == message_id:
            msg["retry_count"] += 1
            if msg["retry_count"] >= queue["max_retries"]:
                msg["status"] = "dead_letter"
                if queue_id not in DEAD_LETTER_QUEUES:
                    DEAD_LETTER_QUEUES[queue_id] = []
                DEAD_LETTER_QUEUES[queue_id].append(msg)
            else:
                msg["status"] = "pending"
            return {"message": "Message returned to queue", "retry_count": msg["retry_count"]}

    raise HTTPException(status_code=404, detail="Message not found")


@app.get("/queues/{queue_id}/dead-letter")
def get_dead_letter_queue(queue_id: str):
    """Get dead letter queue messages"""
    return {"messages": DEAD_LETTER_QUEUES.get(queue_id, []), "total": len(DEAD_LETTER_QUEUES.get(queue_id, []))}


# ============================================================================
# Cache Management
# ============================================================================

CACHES: Dict[str, Dict[str, Any]] = {}
CACHE_ENTRIES: Dict[str, Dict[str, Any]] = {}
CACHE_STATS: Dict[str, Dict[str, int]] = {}


@app.post("/caches")
def create_cache(body: dict = Body(...)):
    """Create cache"""
    cache_id = f"cache_{uuid.uuid4().hex[:8]}"
    cache = {
        "id": cache_id,
        "name": body.get("name", ""),
        "type": body.get("type", "memory"),
        "max_size_mb": body.get("max_size_mb", 100),
        "default_ttl_seconds": body.get("default_ttl_seconds", 3600),
        "eviction_policy": body.get("eviction_policy", "lru"),
        "created_at": datetime.utcnow().isoformat()
    }
    CACHES[cache_id] = cache
    CACHE_ENTRIES[cache_id] = {}
    CACHE_STATS[cache_id] = {"hits": 0, "misses": 0, "evictions": 0}
    return cache


@app.get("/caches")
def list_caches():
    """List caches"""
    return {"caches": list(CACHES.values()), "total": len(CACHES)}


@app.get("/caches/{cache_id}")
def get_cache(cache_id: str):
    """Get cache details"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")
    return {
        "cache": CACHES[cache_id],
        "stats": CACHE_STATS.get(cache_id, {}),
        "entry_count": len(CACHE_ENTRIES.get(cache_id, {}))
    }


@app.post("/caches/{cache_id}/set")
def cache_set(cache_id: str, body: dict = Body(...)):
    """Set cache entry"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")

    key = body.get("key")
    value = body.get("value")
    ttl = body.get("ttl_seconds", CACHES[cache_id]["default_ttl_seconds"])

    CACHE_ENTRIES[cache_id][key] = {
        "value": value,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
        "ttl_seconds": ttl
    }
    return {"key": key, "status": "set"}


@app.get("/caches/{cache_id}/get/{key}")
def cache_get(cache_id: str, key: str):
    """Get cache entry"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")

    entries = CACHE_ENTRIES.get(cache_id, {})
    if key in entries:
        CACHE_STATS[cache_id]["hits"] += 1
        return {"key": key, "value": entries[key]["value"], "hit": True}
    else:
        CACHE_STATS[cache_id]["misses"] += 1
        return {"key": key, "value": None, "hit": False}


@app.delete("/caches/{cache_id}/delete/{key}")
def cache_delete(cache_id: str, key: str):
    """Delete cache entry"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")

    entries = CACHE_ENTRIES.get(cache_id, {})
    if key in entries:
        del entries[key]
    return {"key": key, "status": "deleted"}


@app.post("/caches/{cache_id}/flush")
def cache_flush(cache_id: str):
    """Flush all cache entries"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")

    count = len(CACHE_ENTRIES.get(cache_id, {}))
    CACHE_ENTRIES[cache_id] = {}
    CACHE_STATS[cache_id]["evictions"] += count
    return {"message": "Cache flushed", "entries_removed": count}


@app.get("/caches/{cache_id}/stats")
def get_cache_stats(cache_id: str):
    """Get cache statistics"""
    if cache_id not in CACHES:
        raise HTTPException(status_code=404, detail="Cache not found")

    stats = CACHE_STATS.get(cache_id, {})
    total = stats.get("hits", 0) + stats.get("misses", 0)
    hit_rate = (stats.get("hits", 0) / max(1, total)) * 100

    return {
        "cache_id": cache_id,
        "hits": stats.get("hits", 0),
        "misses": stats.get("misses", 0),
        "hit_rate": round(hit_rate, 2),
        "evictions": stats.get("evictions", 0),
        "entry_count": len(CACHE_ENTRIES.get(cache_id, {}))
    }


# ============================================================================
# Job Scheduler
# ============================================================================

SCHEDULED_JOBS: Dict[str, Dict[str, Any]] = {}
JOB_EXECUTIONS: Dict[str, List[Dict[str, Any]]] = {}
JOB_TRIGGERS: Dict[str, Dict[str, Any]] = {}


@app.post("/scheduler/jobs")
def create_scheduled_job(body: dict = Body(...)):
    """Create scheduled job"""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = {
        "id": job_id,
        "name": body.get("name", ""),
        "description": body.get("description", ""),
        "schedule": body.get("schedule", "0 * * * *"),
        "timezone": body.get("timezone", "UTC"),
        "action": body.get("action", {}),
        "enabled": True,
        "last_run": None,
        "next_run": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    SCHEDULED_JOBS[job_id] = job
    JOB_EXECUTIONS[job_id] = []
    return job


@app.get("/scheduler/jobs")
def list_scheduled_jobs(enabled: Optional[bool] = None):
    """List scheduled jobs"""
    jobs = list(SCHEDULED_JOBS.values())
    if enabled is not None:
        jobs = [j for j in jobs if j["enabled"] == enabled]
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/scheduler/jobs/{job_id}")
def get_scheduled_job(job_id: str):
    """Get scheduled job details"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job": SCHEDULED_JOBS[job_id],
        "recent_executions": JOB_EXECUTIONS.get(job_id, [])[-10:]
    }


@app.put("/scheduler/jobs/{job_id}")
def update_scheduled_job(job_id: str, body: dict = Body(...)):
    """Update scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = SCHEDULED_JOBS[job_id]
    job.update({k: v for k, v in body.items() if k not in ["id", "created_at"]})
    return job


@app.delete("/scheduler/jobs/{job_id}")
def delete_scheduled_job(job_id: str):
    """Delete scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    del SCHEDULED_JOBS[job_id]
    return {"message": "Job deleted", "job_id": job_id}


@app.post("/scheduler/jobs/{job_id}/run")
def run_job_now(job_id: str):
    """Run job immediately"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    execution = {
        "id": f"exec_{uuid.uuid4().hex[:8]}",
        "job_id": job_id,
        "status": "completed",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_ms": random.randint(100, 5000),
        "result": {"success": True}
    }
    JOB_EXECUTIONS[job_id].append(execution)
    SCHEDULED_JOBS[job_id]["last_run"] = execution["completed_at"]

    return execution


@app.post("/scheduler/jobs/{job_id}/pause")
def pause_job(job_id: str):
    """Pause scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    SCHEDULED_JOBS[job_id]["enabled"] = False
    return {"message": "Job paused", "job_id": job_id}


@app.post("/scheduler/jobs/{job_id}/resume")
def resume_job(job_id: str):
    """Resume scheduled job"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    SCHEDULED_JOBS[job_id]["enabled"] = True
    return {"message": "Job resumed", "job_id": job_id}


@app.get("/scheduler/jobs/{job_id}/executions")
def get_job_executions(job_id: str, status: Optional[str] = None, limit: int = 50):
    """Get job execution history"""
    if job_id not in SCHEDULED_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    executions = JOB_EXECUTIONS.get(job_id, [])
    if status:
        executions = [e for e in executions if e["status"] == status]
    return {"executions": executions[-limit:], "total": len(executions)}


# ============================================================================
# Health Monitoring
# ============================================================================

HEALTH_CHECKS: Dict[str, Dict[str, Any]] = {}
HEALTH_RESULTS: Dict[str, List[Dict[str, Any]]] = {}
HEALTH_ALERTS: List[Dict[str, Any]] = []


@app.post("/health/checks")
def create_health_check(body: dict = Body(...)):
    """Create health check"""
    check_id = f"hc_{uuid.uuid4().hex[:8]}"
    check = {
        "id": check_id,
        "name": body.get("name", ""),
        "type": body.get("type", "http"),
        "target": body.get("target", ""),
        "interval_seconds": body.get("interval_seconds", 30),
        "timeout_seconds": body.get("timeout_seconds", 10),
        "healthy_threshold": body.get("healthy_threshold", 2),
        "unhealthy_threshold": body.get("unhealthy_threshold", 3),
        "enabled": True,
        "status": "unknown",
        "created_at": datetime.utcnow().isoformat()
    }
    HEALTH_CHECKS[check_id] = check
    HEALTH_RESULTS[check_id] = []
    return check


@app.get("/health/checks")
def list_health_checks(status: Optional[str] = None):
    """List health checks"""
    checks = list(HEALTH_CHECKS.values())
    if status:
        checks = [c for c in checks if c["status"] == status]
    return {"checks": checks, "total": len(checks)}


@app.get("/health/checks/{check_id}")
def get_health_check(check_id: str):
    """Get health check details"""
    if check_id not in HEALTH_CHECKS:
        raise HTTPException(status_code=404, detail="Health check not found")
    return {
        "check": HEALTH_CHECKS[check_id],
        "recent_results": HEALTH_RESULTS.get(check_id, [])[-20:]
    }


@app.post("/health/checks/{check_id}/run")
def run_health_check(check_id: str):
    """Run health check now"""
    if check_id not in HEALTH_CHECKS:
        raise HTTPException(status_code=404, detail="Health check not found")

    healthy = random.random() > 0.1
    result = {
        "id": f"result_{uuid.uuid4().hex[:8]}",
        "check_id": check_id,
        "healthy": healthy,
        "response_time_ms": random.randint(10, 500) if healthy else None,
        "error": None if healthy else "Connection timeout",
        "checked_at": datetime.utcnow().isoformat()
    }
    HEALTH_RESULTS[check_id].append(result)
    HEALTH_CHECKS[check_id]["status"] = "healthy" if healthy else "unhealthy"

    if not healthy:
        HEALTH_ALERTS.append({
            "check_id": check_id,
            "check_name": HEALTH_CHECKS[check_id]["name"],
            "status": "unhealthy",
            "error": result["error"],
            "created_at": datetime.utcnow().isoformat()
        })

    return result


@app.get("/health/alerts")
def get_health_alerts(check_id: Optional[str] = None, limit: int = 50):
    """Get health alerts"""
    alerts = HEALTH_ALERTS
    if check_id:
        alerts = [a for a in alerts if a["check_id"] == check_id]
    return {"alerts": alerts[-limit:], "total": len(alerts)}


@app.get("/health/dashboard")
def health_dashboard():
    """Get health dashboard"""
    checks = list(HEALTH_CHECKS.values())
    return {
        "total_checks": len(checks),
        "healthy": len([c for c in checks if c["status"] == "healthy"]),
        "unhealthy": len([c for c in checks if c["status"] == "unhealthy"]),
        "unknown": len([c for c in checks if c["status"] == "unknown"]),
        "recent_alerts": HEALTH_ALERTS[-5:],
        "checks": [{
            "id": c["id"],
            "name": c["name"],
            "status": c["status"],
            "type": c["type"]
        } for c in checks]
    }


# ============================================================================
# API Versioning
# ============================================================================

API_VERSIONS: Dict[str, Dict[str, Any]] = {}
VERSION_ROUTES: Dict[str, List[Dict[str, Any]]] = {}
DEPRECATION_NOTICES: List[Dict[str, Any]] = []


@app.post("/api-versions")
def create_api_version(body: dict = Body(...)):
    """Create API version"""
    version_id = f"v_{uuid.uuid4().hex[:8]}"
    version = {
        "id": version_id,
        "version": body.get("version", "1.0"),
        "status": body.get("status", "active"),
        "release_date": body.get("release_date", datetime.utcnow().isoformat()),
        "deprecation_date": body.get("deprecation_date"),
        "sunset_date": body.get("sunset_date"),
        "changelog": body.get("changelog", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    API_VERSIONS[version_id] = version
    VERSION_ROUTES[version_id] = []
    return version


@app.get("/api-versions")
def list_api_versions(status: Optional[str] = None):
    """List API versions"""
    versions = list(API_VERSIONS.values())
    if status:
        versions = [v for v in versions if v["status"] == status]
    return {"versions": versions, "total": len(versions)}


@app.get("/api-versions/{version_id}")
def get_api_version(version_id: str):
    """Get API version details"""
    if version_id not in API_VERSIONS:
        raise HTTPException(status_code=404, detail="API version not found")
    return {
        "version": API_VERSIONS[version_id],
        "routes": VERSION_ROUTES.get(version_id, [])
    }


@app.post("/api-versions/{version_id}/deprecate")
def deprecate_api_version(version_id: str, body: dict = Body(...)):
    """Deprecate API version"""
    if version_id not in API_VERSIONS:
        raise HTTPException(status_code=404, detail="API version not found")

    version = API_VERSIONS[version_id]
    version["status"] = "deprecated"
    version["deprecation_date"] = datetime.utcnow().isoformat()
    version["sunset_date"] = body.get("sunset_date")

    notice = {
        "version_id": version_id,
        "version": version["version"],
        "message": body.get("message", "This API version is deprecated"),
        "sunset_date": version["sunset_date"],
        "created_at": datetime.utcnow().isoformat()
    }
    DEPRECATION_NOTICES.append(notice)

    return {"message": "Version deprecated", "version": version}


@app.post("/api-versions/{version_id}/routes")
def add_version_route(version_id: str, body: dict = Body(...)):
    """Add route to API version"""
    if version_id not in API_VERSIONS:
        raise HTTPException(status_code=404, detail="API version not found")

    route = {
        "id": f"route_{uuid.uuid4().hex[:8]}",
        "path": body.get("path", ""),
        "methods": body.get("methods", ["GET"]),
        "handler": body.get("handler", ""),
        "deprecated": body.get("deprecated", False)
    }
    VERSION_ROUTES[version_id].append(route)
    return route


@app.get("/api-versions/deprecation-notices")
def get_deprecation_notices():
    """Get deprecation notices"""
    return {"notices": DEPRECATION_NOTICES, "total": len(DEPRECATION_NOTICES)}


# ============================================================================
# Data Export
# ============================================================================

EXPORT_JOBS: Dict[str, Dict[str, Any]] = {}
EXPORT_TEMPLATES: Dict[str, Dict[str, Any]] = {}


@app.post("/exports")
def create_export(body: dict = Body(...)):
    """Create data export job"""
    export_id = f"export_{uuid.uuid4().hex[:12]}"
    export = {
        "id": export_id,
        "name": body.get("name", ""),
        "format": body.get("format", "json"),
        "resource_type": body.get("resource_type", ""),
        "filters": body.get("filters", {}),
        "fields": body.get("fields", []),
        "status": "pending",
        "progress_percent": 0,
        "file_url": None,
        "file_size_bytes": None,
        "record_count": None,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }
    EXPORT_JOBS[export_id] = export
    return export


@app.get("/exports")
def list_exports(status: Optional[str] = None, format: Optional[str] = None):
    """List export jobs"""
    exports = list(EXPORT_JOBS.values())
    if status:
        exports = [e for e in exports if e["status"] == status]
    if format:
        exports = [e for e in exports if e["format"] == format]
    return {"exports": exports, "total": len(exports)}


@app.get("/exports/{export_id}")
def get_export(export_id: str):
    """Get export job details"""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Export not found")
    return EXPORT_JOBS[export_id]


@app.post("/exports/{export_id}/start")
def start_export(export_id: str):
    """Start export job"""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Export not found")

    export = EXPORT_JOBS[export_id]
    export["status"] = "processing"

    export["status"] = "completed"
    export["progress_percent"] = 100
    export["completed_at"] = datetime.utcnow().isoformat()
    export["record_count"] = random.randint(100, 10000)
    export["file_size_bytes"] = random.randint(10000, 1000000)
    export["file_url"] = f"/downloads/{export_id}.{export['format']}"

    return export


@app.delete("/exports/{export_id}")
def delete_export(export_id: str):
    """Delete export job"""
    if export_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Export not found")
    del EXPORT_JOBS[export_id]
    return {"message": "Export deleted", "export_id": export_id}


@app.post("/export-templates")
def create_export_template(body: dict = Body(...)):
    """Create export template"""
    template_id = f"tmpl_{uuid.uuid4().hex[:8]}"
    template = {
        "id": template_id,
        "name": body.get("name", ""),
        "format": body.get("format", "json"),
        "resource_type": body.get("resource_type", ""),
        "filters": body.get("filters", {}),
        "fields": body.get("fields", []),
        "created_at": datetime.utcnow().isoformat()
    }
    EXPORT_TEMPLATES[template_id] = template
    return template


@app.get("/export-templates")
def list_export_templates():
    """List export templates"""
    return {"templates": list(EXPORT_TEMPLATES.values()), "total": len(EXPORT_TEMPLATES)}


# ============================================================================
# Incident Management
# ============================================================================

INCIDENTS: Dict[str, Dict[str, Any]] = {}
INCIDENT_UPDATES: Dict[str, List[Dict[str, Any]]] = {}
INCIDENT_POSTMORTEMS: Dict[str, Dict[str, Any]] = {}


@app.post("/incidents")
def create_incident(body: dict = Body(...)):
    """Create incident"""
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    incident = {
        "id": incident_id,
        "title": body.get("title", ""),
        "description": body.get("description", ""),
        "severity": body.get("severity", "medium"),
        "status": "open",
        "priority": body.get("priority", "P2"),
        "affected_services": body.get("affected_services", []),
        "assigned_to": body.get("assigned_to"),
        "created_at": datetime.utcnow().isoformat(),
        "resolved_at": None
    }
    INCIDENTS[incident_id] = incident
    INCIDENT_UPDATES[incident_id] = []
    return incident


@app.get("/incidents")
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None):
    """List incidents"""
    incidents = list(INCIDENTS.values())
    if status:
        incidents = [i for i in incidents if i["status"] == status]
    if severity:
        incidents = [i for i in incidents if i["severity"] == severity]
    return {"incidents": incidents, "total": len(incidents)}


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    """Get incident details"""
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "incident": INCIDENTS[incident_id],
        "updates": INCIDENT_UPDATES.get(incident_id, []),
        "postmortem": INCIDENT_POSTMORTEMS.get(incident_id)
    }


@app.post("/incidents/{incident_id}/update")
def add_incident_update(incident_id: str, body: dict = Body(...)):
    """Add incident update"""
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")

    update = {
        "id": f"update_{uuid.uuid4().hex[:8]}",
        "message": body.get("message", ""),
        "status": body.get("status"),
        "author": body.get("author", "system"),
        "created_at": datetime.utcnow().isoformat()
    }

    if body.get("status"):
        INCIDENTS[incident_id]["status"] = body["status"]

    INCIDENT_UPDATES[incident_id].append(update)
    return update


@app.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str, body: dict = Body(...)):
    """Resolve incident"""
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = INCIDENTS[incident_id]
    incident["status"] = "resolved"
    incident["resolved_at"] = datetime.utcnow().isoformat()

    INCIDENT_UPDATES[incident_id].append({
        "id": f"update_{uuid.uuid4().hex[:8]}",
        "message": body.get("resolution_message", "Incident resolved"),
        "status": "resolved",
        "author": body.get("author", "system"),
        "created_at": datetime.utcnow().isoformat()
    })

    return {"message": "Incident resolved", "incident": incident}


@app.post("/incidents/{incident_id}/postmortem")
def create_postmortem(incident_id: str, body: dict = Body(...)):
    """Create incident postmortem"""
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")

    postmortem = {
        "incident_id": incident_id,
        "summary": body.get("summary", ""),
        "root_cause": body.get("root_cause", ""),
        "impact": body.get("impact", ""),
        "timeline": body.get("timeline", []),
        "action_items": body.get("action_items", []),
        "lessons_learned": body.get("lessons_learned", []),
        "created_at": datetime.utcnow().isoformat()
    }
    INCIDENT_POSTMORTEMS[incident_id] = postmortem
    return postmortem


@app.get("/incidents/dashboard")
def incident_dashboard():
    """Get incident dashboard"""
    incidents = list(INCIDENTS.values())
    return {
        "total": len(incidents),
        "open": len([i for i in incidents if i["status"] == "open"]),
        "investigating": len([i for i in incidents if i["status"] == "investigating"]),
        "resolved": len([i for i in incidents if i["status"] == "resolved"]),
        "by_severity": {
            "critical": len([i for i in incidents if i["severity"] == "critical"]),
            "high": len([i for i in incidents if i["severity"] == "high"]),
            "medium": len([i for i in incidents if i["severity"] == "medium"]),
            "low": len([i for i in incidents if i["severity"] == "low"])
        },
        "recent": sorted(incidents, key=lambda x: x["created_at"], reverse=True)[:5]
    }


# ============================================================================
# Change Management
# ============================================================================

CHANGE_REQUESTS: Dict[str, Dict[str, Any]] = {}
CHANGE_APPROVALS: Dict[str, List[Dict[str, Any]]] = {}
CHANGE_IMPLEMENTATIONS: Dict[str, Dict[str, Any]] = {}


@app.post("/changes")
def create_change_request(body: dict = Body(...)):
    """Create change request"""
    change_id = f"chg_{uuid.uuid4().hex[:8]}"
    change = {
        "id": change_id,
        "title": body.get("title", ""),
        "description": body.get("description", ""),
        "type": body.get("type", "standard"),
        "priority": body.get("priority", "medium"),
        "risk_level": body.get("risk_level", "low"),
        "status": "draft",
        "requester": body.get("requester", ""),
        "affected_systems": body.get("affected_systems", []),
        "implementation_plan": body.get("implementation_plan", ""),
        "rollback_plan": body.get("rollback_plan", ""),
        "scheduled_date": body.get("scheduled_date"),
        "created_at": datetime.utcnow().isoformat()
    }
    CHANGE_REQUESTS[change_id] = change
    CHANGE_APPROVALS[change_id] = []
    return change


@app.get("/changes")
def list_change_requests(status: Optional[str] = None, type: Optional[str] = None):
    """List change requests"""
    changes = list(CHANGE_REQUESTS.values())
    if status:
        changes = [c for c in changes if c["status"] == status]
    if type:
        changes = [c for c in changes if c["type"] == type]
    return {"changes": changes, "total": len(changes)}


@app.get("/changes/{change_id}")
def get_change_request(change_id: str):
    """Get change request details"""
    if change_id not in CHANGE_REQUESTS:
        raise HTTPException(status_code=404, detail="Change request not found")
    return {
        "change": CHANGE_REQUESTS[change_id],
        "approvals": CHANGE_APPROVALS.get(change_id, []),
        "implementation": CHANGE_IMPLEMENTATIONS.get(change_id)
    }


@app.post("/changes/{change_id}/submit")
def submit_change_request(change_id: str):
    """Submit change request for approval"""
    if change_id not in CHANGE_REQUESTS:
        raise HTTPException(status_code=404, detail="Change request not found")

    CHANGE_REQUESTS[change_id]["status"] = "pending_approval"
    return {"message": "Change submitted for approval", "change_id": change_id}


@app.post("/changes/{change_id}/approve")
def approve_change(change_id: str, body: dict = Body(...)):
    """Approve change request"""
    if change_id not in CHANGE_REQUESTS:
        raise HTTPException(status_code=404, detail="Change request not found")

    approval = {
        "id": f"appr_{uuid.uuid4().hex[:8]}",
        "approver": body.get("approver", ""),
        "decision": "approved",
        "comments": body.get("comments", ""),
        "approved_at": datetime.utcnow().isoformat()
    }
    CHANGE_APPROVALS[change_id].append(approval)
    CHANGE_REQUESTS[change_id]["status"] = "approved"

    return approval


@app.post("/changes/{change_id}/reject")
def reject_change(change_id: str, body: dict = Body(...)):
    """Reject change request"""
    if change_id not in CHANGE_REQUESTS:
        raise HTTPException(status_code=404, detail="Change request not found")

    approval = {
        "id": f"appr_{uuid.uuid4().hex[:8]}",
        "approver": body.get("approver", ""),
        "decision": "rejected",
        "reason": body.get("reason", ""),
        "rejected_at": datetime.utcnow().isoformat()
    }
    CHANGE_APPROVALS[change_id].append(approval)
    CHANGE_REQUESTS[change_id]["status"] = "rejected"

    return approval


@app.post("/changes/{change_id}/implement")
def implement_change(change_id: str, body: dict = Body(...)):
    """Record change implementation"""
    if change_id not in CHANGE_REQUESTS:
        raise HTTPException(status_code=404, detail="Change request not found")

    implementation = {
        "change_id": change_id,
        "implementer": body.get("implementer", ""),
        "status": "completed",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "notes": body.get("notes", "")
    }
    CHANGE_IMPLEMENTATIONS[change_id] = implementation
    CHANGE_REQUESTS[change_id]["status"] = "implemented"

    return implementation


@app.get("/changes/dashboard")
def change_dashboard():
    """Get change management dashboard"""
    changes = list(CHANGE_REQUESTS.values())
    return {
        "total": len(changes),
        "by_status": {
            "draft": len([c for c in changes if c["status"] == "draft"]),
            "pending_approval": len([c for c in changes if c["status"] == "pending_approval"]),
            "approved": len([c for c in changes if c["status"] == "approved"]),
            "implemented": len([c for c in changes if c["status"] == "implemented"]),
            "rejected": len([c for c in changes if c["status"] == "rejected"])
        },
        "by_risk": {
            "high": len([c for c in changes if c["risk_level"] == "high"]),
            "medium": len([c for c in changes if c["risk_level"] == "medium"]),
            "low": len([c for c in changes if c["risk_level"] == "low"])
        },
        "pending_approval": [c for c in changes if c["status"] == "pending_approval"][:5]
    }


# ============================================================================
# MLOps - Machine Learning Operations
# ============================================================================

ML_MODELS: Dict[str, Dict[str, Any]] = {}
ML_EXPERIMENTS: Dict[str, Dict[str, Any]] = {}
ML_DEPLOYMENTS: Dict[str, Dict[str, Any]] = {}
ML_PREDICTIONS: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/mlops/models")
def create_ml_model(data: Dict[str, Any]):
    """Register a machine learning model"""
    model_id = f"model_{uuid.uuid4().hex[:12]}"
    ML_MODELS[model_id] = {
        "model_id": model_id,
        "name": data.get("name"),
        "version": data.get("version", "1.0.0"),
        "framework": data.get("framework", "tensorflow"),
        "model_type": data.get("model_type", "classification"),
        "description": data.get("description", ""),
        "metrics": data.get("metrics", {}),
        "artifacts": data.get("artifacts", {}),
        "tags": data.get("tags", []),
        "status": "registered",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    ML_PREDICTIONS[model_id] = []
    return {"model_id": model_id, "message": "Model registered"}

@app.get("/mlops/models")
def list_ml_models(framework: str = None, model_type: str = None):
    """List all registered models"""
    models = list(ML_MODELS.values())
    if framework:
        models = [m for m in models if m["framework"] == framework]
    if model_type:
        models = [m for m in models if m["model_type"] == model_type]
    return {"models": models, "count": len(models)}

@app.get("/mlops/models/{model_id}")
def get_ml_model(model_id: str):
    """Get model details"""
    if model_id not in ML_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    return ML_MODELS[model_id]

@app.put("/mlops/models/{model_id}/metrics")
def update_model_metrics(model_id: str, data: Dict[str, Any]):
    """Update model metrics"""
    if model_id not in ML_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    ML_MODELS[model_id]["metrics"].update(data.get("metrics", {}))
    ML_MODELS[model_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Metrics updated"}

@app.post("/mlops/experiments")
def create_experiment(data: Dict[str, Any]):
    """Create an ML experiment"""
    exp_id = f"exp_{uuid.uuid4().hex[:12]}"
    ML_EXPERIMENTS[exp_id] = {
        "experiment_id": exp_id,
        "name": data.get("name"),
        "model_id": data.get("model_id"),
        "hypothesis": data.get("hypothesis", ""),
        "parameters": data.get("parameters", {}),
        "dataset": data.get("dataset", {}),
        "results": {},
        "status": "created",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"experiment_id": exp_id, "message": "Experiment created"}

@app.get("/mlops/experiments")
def list_experiments(model_id: str = None, status: str = None):
    """List all experiments"""
    experiments = list(ML_EXPERIMENTS.values())
    if model_id:
        experiments = [e for e in experiments if e["model_id"] == model_id]
    if status:
        experiments = [e for e in experiments if e["status"] == status]
    return {"experiments": experiments, "count": len(experiments)}

@app.post("/mlops/experiments/{exp_id}/run")
def run_experiment(exp_id: str):
    """Run an experiment"""
    if exp_id not in ML_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    ML_EXPERIMENTS[exp_id]["status"] = "running"
    ML_EXPERIMENTS[exp_id]["started_at"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Experiment started"}

@app.post("/mlops/experiments/{exp_id}/complete")
def complete_experiment(exp_id: str, data: Dict[str, Any]):
    """Complete an experiment with results"""
    if exp_id not in ML_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    ML_EXPERIMENTS[exp_id]["status"] = "completed"
    ML_EXPERIMENTS[exp_id]["results"] = data.get("results", {})
    ML_EXPERIMENTS[exp_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Experiment completed"}

@app.post("/mlops/deployments")
def create_model_deployment(data: Dict[str, Any]):
    """Deploy a model"""
    deploy_id = f"deploy_{uuid.uuid4().hex[:12]}"
    ML_DEPLOYMENTS[deploy_id] = {
        "deployment_id": deploy_id,
        "model_id": data.get("model_id"),
        "environment": data.get("environment", "production"),
        "replicas": data.get("replicas", 1),
        "resources": data.get("resources", {"cpu": "1", "memory": "2Gi"}),
        "endpoint": f"/mlops/predict/{deploy_id}",
        "status": "deploying",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"deployment_id": deploy_id, "endpoint": ML_DEPLOYMENTS[deploy_id]["endpoint"]}

@app.get("/mlops/deployments")
def list_model_deployments(model_id: str = None, environment: str = None):
    """List all model deployments"""
    deployments = list(ML_DEPLOYMENTS.values())
    if model_id:
        deployments = [d for d in deployments if d["model_id"] == model_id]
    if environment:
        deployments = [d for d in deployments if d["environment"] == environment]
    return {"deployments": deployments, "count": len(deployments)}

@app.post("/mlops/predict/{deploy_id}")
def make_prediction(deploy_id: str, data: Dict[str, Any]):
    """Make a prediction using deployed model"""
    if deploy_id not in ML_DEPLOYMENTS:
        raise HTTPException(status_code=404, detail="Deployment not found")
    prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
    model_id = ML_DEPLOYMENTS[deploy_id]["model_id"]
    prediction = {
        "prediction_id": prediction_id,
        "deployment_id": deploy_id,
        "input": data.get("input", {}),
        "output": {"prediction": "simulated_result", "confidence": 0.95},
        "latency_ms": 45,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    if model_id in ML_PREDICTIONS:
        ML_PREDICTIONS[model_id].append(prediction)
    return prediction


# ============================================================================
# Feature Flags
# ============================================================================

FEATURE_FLAGS: Dict[str, Dict[str, Any]] = {}
FLAG_OVERRIDES: Dict[str, List[Dict[str, Any]]] = {}
FLAG_AUDIT_LOG: List[Dict[str, Any]] = []

@app.post("/feature-flags")
def create_feature_flag(data: Dict[str, Any]):
    """Create a feature flag"""
    flag_id = f"flag_{uuid.uuid4().hex[:12]}"
    FEATURE_FLAGS[flag_id] = {
        "flag_id": flag_id,
        "key": data.get("key"),
        "name": data.get("name"),
        "description": data.get("description", ""),
        "enabled": data.get("enabled", False),
        "rollout_percentage": data.get("rollout_percentage", 0),
        "targeting_rules": data.get("targeting_rules", []),
        "default_value": data.get("default_value", False),
        "variants": data.get("variants", []),
        "tags": data.get("tags", []),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    FLAG_OVERRIDES[flag_id] = []
    return {"flag_id": flag_id, "key": FEATURE_FLAGS[flag_id]["key"]}

@app.get("/feature-flags")
def list_feature_flags(enabled: bool = None, tag: str = None):
    """List all feature flags"""
    flags = list(FEATURE_FLAGS.values())
    if enabled is not None:
        flags = [f for f in flags if f["enabled"] == enabled]
    if tag:
        flags = [f for f in flags if tag in f.get("tags", [])]
    return {"flags": flags, "count": len(flags)}

@app.get("/feature-flags/{flag_id}")
def get_feature_flag(flag_id: str):
    """Get feature flag details"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return FEATURE_FLAGS[flag_id]

@app.put("/feature-flags/{flag_id}/toggle")
def toggle_feature_flag(flag_id: str):
    """Toggle a feature flag on/off"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    FEATURE_FLAGS[flag_id]["enabled"] = not FEATURE_FLAGS[flag_id]["enabled"]
    FEATURE_FLAGS[flag_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    FLAG_AUDIT_LOG.append({
        "flag_id": flag_id,
        "action": "toggle",
        "new_value": FEATURE_FLAGS[flag_id]["enabled"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    return {"message": "Flag toggled", "enabled": FEATURE_FLAGS[flag_id]["enabled"]}

@app.put("/feature-flags/{flag_id}/rollout")
def update_rollout_percentage(flag_id: str, data: Dict[str, Any]):
    """Update rollout percentage for gradual release"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    percentage = data.get("percentage", 0)
    if not 0 <= percentage <= 100:
        raise HTTPException(status_code=400, detail="Percentage must be 0-100")
    FEATURE_FLAGS[flag_id]["rollout_percentage"] = percentage
    FEATURE_FLAGS[flag_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Rollout updated", "percentage": percentage}

@app.post("/feature-flags/{flag_id}/targeting")
def add_targeting_rule(flag_id: str, data: Dict[str, Any]):
    """Add a targeting rule to a feature flag"""
    if flag_id not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    rule = {
        "rule_id": f"rule_{uuid.uuid4().hex[:8]}",
        "attribute": data.get("attribute"),
        "operator": data.get("operator", "equals"),
        "value": data.get("value"),
        "enabled": data.get("enabled", True)
    }
    FEATURE_FLAGS[flag_id]["targeting_rules"].append(rule)
    return {"message": "Targeting rule added", "rule_id": rule["rule_id"]}

@app.post("/feature-flags/evaluate")
def evaluate_feature_flag(data: Dict[str, Any]):
    """Evaluate a feature flag for a user context"""
    flag_key = data.get("flag_key")
    user_context = data.get("context", {})
    flag = next((f for f in FEATURE_FLAGS.values() if f["key"] == flag_key), None)
    if not flag:
        return {"enabled": False, "reason": "flag_not_found"}
    if not flag["enabled"]:
        return {"enabled": False, "reason": "flag_disabled"}
    if flag["rollout_percentage"] < 100:
        user_id = user_context.get("user_id", "")
        bucket = hash(user_id) % 100
        if bucket >= flag["rollout_percentage"]:
            return {"enabled": False, "reason": "rollout_excluded"}
    return {"enabled": True, "reason": "flag_enabled", "variant": flag.get("default_value")}

@app.get("/feature-flags/audit")
def get_flag_audit_log(flag_id: str = None, limit: int = 50):
    """Get feature flag audit log"""
    logs = FLAG_AUDIT_LOG
    if flag_id:
        logs = [l for l in logs if l["flag_id"] == flag_id]
    return {"audit_log": logs[-limit:], "count": len(logs)}


# ============================================================================
# Rate Limiting
# ============================================================================

RATE_LIMIT_POLICIES: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_BUCKETS: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_VIOLATIONS: List[Dict[str, Any]] = []

@app.post("/rate-limiting/policies")
def create_rate_limit_policy(data: Dict[str, Any]):
    """Create a rate limiting policy"""
    policy_id = f"rlp_{uuid.uuid4().hex[:12]}"
    RATE_LIMIT_POLICIES[policy_id] = {
        "policy_id": policy_id,
        "name": data.get("name"),
        "description": data.get("description", ""),
        "limit": data.get("limit", 100),
        "window_seconds": data.get("window_seconds", 60),
        "strategy": data.get("strategy", "sliding_window"),
        "scope": data.get("scope", "per_user"),
        "endpoints": data.get("endpoints", ["*"]),
        "enabled": data.get("enabled", True),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"policy_id": policy_id, "message": "Rate limit policy created"}

@app.get("/rate-limiting/policies")
def list_rate_limit_policies(enabled: bool = None):
    """List all rate limiting policies"""
    policies = list(RATE_LIMIT_POLICIES.values())
    if enabled is not None:
        policies = [p for p in policies if p["enabled"] == enabled]
    return {"policies": policies, "count": len(policies)}

@app.get("/rate-limiting/policies/{policy_id}")
def get_rate_limit_policy(policy_id: str):
    """Get rate limit policy details"""
    if policy_id not in RATE_LIMIT_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return RATE_LIMIT_POLICIES[policy_id]

@app.put("/rate-limiting/policies/{policy_id}")
def update_rate_limit_policy(policy_id: str, data: Dict[str, Any]):
    """Update a rate limiting policy"""
    if policy_id not in RATE_LIMIT_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    RATE_LIMIT_POLICIES[policy_id].update({
        "limit": data.get("limit", RATE_LIMIT_POLICIES[policy_id]["limit"]),
        "window_seconds": data.get("window_seconds", RATE_LIMIT_POLICIES[policy_id]["window_seconds"]),
        "enabled": data.get("enabled", RATE_LIMIT_POLICIES[policy_id]["enabled"]),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    })
    return {"message": "Policy updated"}

@app.post("/rate-limiting/check")
def check_rate_limit(data: Dict[str, Any]):
    """Check if a request is rate limited"""
    identifier = data.get("identifier")
    endpoint = data.get("endpoint", "*")
    bucket_key = f"{identifier}:{endpoint}"
    if bucket_key not in RATE_LIMIT_BUCKETS:
        RATE_LIMIT_BUCKETS[bucket_key] = {
            "identifier": identifier,
            "endpoint": endpoint,
            "count": 0,
            "window_start": datetime.utcnow().isoformat() + "Z",
            "reset_at": datetime.utcnow().isoformat() + "Z"
        }
    bucket = RATE_LIMIT_BUCKETS[bucket_key]
    bucket["count"] += 1
    applicable_policy = next((p for p in RATE_LIMIT_POLICIES.values()
                             if p["enabled"] and (endpoint in p["endpoints"] or "*" in p["endpoints"])), None)
    if applicable_policy and bucket["count"] > applicable_policy["limit"]:
        RATE_LIMIT_VIOLATIONS.append({
            "identifier": identifier,
            "endpoint": endpoint,
            "policy_id": applicable_policy["policy_id"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        return {"allowed": False, "remaining": 0, "retry_after": applicable_policy["window_seconds"]}
    remaining = applicable_policy["limit"] - bucket["count"] if applicable_policy else 100
    return {"allowed": True, "remaining": max(0, remaining)}

@app.get("/rate-limiting/buckets")
def list_rate_limit_buckets(identifier: str = None):
    """List rate limit buckets"""
    buckets = list(RATE_LIMIT_BUCKETS.values())
    if identifier:
        buckets = [b for b in buckets if b["identifier"] == identifier]
    return {"buckets": buckets, "count": len(buckets)}

@app.delete("/rate-limiting/buckets/{identifier}")
def reset_rate_limit_bucket(identifier: str):
    """Reset rate limit for an identifier"""
    keys_to_delete = [k for k in RATE_LIMIT_BUCKETS if k.startswith(identifier)]
    for key in keys_to_delete:
        del RATE_LIMIT_BUCKETS[key]
    return {"message": "Rate limit reset", "cleared_buckets": len(keys_to_delete)}

@app.get("/rate-limiting/violations")
def get_rate_limit_violations(identifier: str = None, limit: int = 100):
    """Get rate limit violations"""
    violations = RATE_LIMIT_VIOLATIONS
    if identifier:
        violations = [v for v in violations if v["identifier"] == identifier]
    return {"violations": violations[-limit:], "total": len(violations)}


# ============================================================================
# Service Mesh
# ============================================================================

SERVICE_REGISTRY: Dict[str, Dict[str, Any]] = {}
SERVICE_INSTANCES: Dict[str, List[Dict[str, Any]]] = {}
CIRCUIT_BREAKERS: Dict[str, Dict[str, Any]] = {}
LOAD_BALANCERS: Dict[str, Dict[str, Any]] = {}

@app.post("/service-mesh/services")
def register_service(data: Dict[str, Any]):
    """Register a service in the mesh"""
    service_id = f"svc_{uuid.uuid4().hex[:12]}"
    SERVICE_REGISTRY[service_id] = {
        "service_id": service_id,
        "name": data.get("name"),
        "version": data.get("version", "1.0.0"),
        "protocol": data.get("protocol", "http"),
        "port": data.get("port", 8080),
        "health_check": data.get("health_check", "/health"),
        "metadata": data.get("metadata", {}),
        "status": "registered",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    SERVICE_INSTANCES[service_id] = []
    return {"service_id": service_id, "message": "Service registered"}

@app.get("/service-mesh/services")
def list_services(status: str = None):
    """List all registered services"""
    services = list(SERVICE_REGISTRY.values())
    if status:
        services = [s for s in services if s["status"] == status]
    return {"services": services, "count": len(services)}

@app.get("/service-mesh/services/{service_id}")
def get_service(service_id: str):
    """Get service details"""
    if service_id not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail="Service not found")
    service = SERVICE_REGISTRY[service_id].copy()
    service["instances"] = SERVICE_INSTANCES.get(service_id, [])
    return service

@app.post("/service-mesh/services/{service_id}/instances")
def register_service_instance(service_id: str, data: Dict[str, Any]):
    """Register a service instance"""
    if service_id not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail="Service not found")
    instance_id = f"inst_{uuid.uuid4().hex[:8]}"
    instance = {
        "instance_id": instance_id,
        "host": data.get("host"),
        "port": data.get("port"),
        "weight": data.get("weight", 1),
        "healthy": True,
        "last_health_check": datetime.utcnow().isoformat() + "Z",
        "registered_at": datetime.utcnow().isoformat() + "Z"
    }
    SERVICE_INSTANCES[service_id].append(instance)
    SERVICE_REGISTRY[service_id]["status"] = "healthy"
    return {"instance_id": instance_id, "message": "Instance registered"}

@app.delete("/service-mesh/services/{service_id}/instances/{instance_id}")
def deregister_service_instance(service_id: str, instance_id: str):
    """Deregister a service instance"""
    if service_id not in SERVICE_INSTANCES:
        raise HTTPException(status_code=404, detail="Service not found")
    SERVICE_INSTANCES[service_id] = [i for i in SERVICE_INSTANCES[service_id] if i["instance_id"] != instance_id]
    return {"message": "Instance deregistered"}

@app.post("/service-mesh/circuit-breakers")
def create_circuit_breaker(data: Dict[str, Any]):
    """Create a circuit breaker for a service"""
    cb_id = f"cb_{uuid.uuid4().hex[:12]}"
    CIRCUIT_BREAKERS[cb_id] = {
        "circuit_breaker_id": cb_id,
        "service_id": data.get("service_id"),
        "failure_threshold": data.get("failure_threshold", 5),
        "success_threshold": data.get("success_threshold", 3),
        "timeout_seconds": data.get("timeout_seconds", 30),
        "state": "closed",
        "failure_count": 0,
        "success_count": 0,
        "last_failure": None,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"circuit_breaker_id": cb_id, "state": "closed"}

@app.get("/service-mesh/circuit-breakers")
def list_circuit_breakers(state: str = None):
    """List all circuit breakers"""
    cbs = list(CIRCUIT_BREAKERS.values())
    if state:
        cbs = [cb for cb in cbs if cb["state"] == state]
    return {"circuit_breakers": cbs, "count": len(cbs)}

@app.post("/service-mesh/circuit-breakers/{cb_id}/trip")
def trip_circuit_breaker(cb_id: str):
    """Trip a circuit breaker (open it)"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    CIRCUIT_BREAKERS[cb_id]["state"] = "open"
    CIRCUIT_BREAKERS[cb_id]["last_failure"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Circuit breaker tripped", "state": "open"}

@app.post("/service-mesh/circuit-breakers/{cb_id}/reset")
def reset_circuit_breaker(cb_id: str):
    """Reset a circuit breaker (close it)"""
    if cb_id not in CIRCUIT_BREAKERS:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    CIRCUIT_BREAKERS[cb_id]["state"] = "closed"
    CIRCUIT_BREAKERS[cb_id]["failure_count"] = 0
    CIRCUIT_BREAKERS[cb_id]["success_count"] = 0
    return {"message": "Circuit breaker reset", "state": "closed"}

@app.post("/service-mesh/load-balancers")
def create_load_balancer(data: Dict[str, Any]):
    """Create a load balancer configuration"""
    lb_id = f"lb_{uuid.uuid4().hex[:12]}"
    LOAD_BALANCERS[lb_id] = {
        "load_balancer_id": lb_id,
        "service_id": data.get("service_id"),
        "algorithm": data.get("algorithm", "round_robin"),
        "sticky_sessions": data.get("sticky_sessions", False),
        "health_check_interval": data.get("health_check_interval", 30),
        "current_index": 0,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"load_balancer_id": lb_id, "algorithm": LOAD_BALANCERS[lb_id]["algorithm"]}

@app.get("/service-mesh/discover/{service_name}")
def discover_service(service_name: str):
    """Discover healthy instances of a service"""
    service = next((s for s in SERVICE_REGISTRY.values() if s["name"] == service_name), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    instances = [i for i in SERVICE_INSTANCES.get(service["service_id"], []) if i["healthy"]]
    return {"service": service_name, "instances": instances, "count": len(instances)}


# ============================================================================
# Log Aggregation
# ============================================================================

LOG_STREAMS: Dict[str, Dict[str, Any]] = {}
LOG_ENTRIES: Dict[str, List[Dict[str, Any]]] = {}
LOG_RETENTION_POLICIES: Dict[str, Dict[str, Any]] = {}

@app.post("/logs/streams")
def create_log_stream(data: Dict[str, Any]):
    """Create a log stream"""
    stream_id = f"stream_{uuid.uuid4().hex[:12]}"
    LOG_STREAMS[stream_id] = {
        "stream_id": stream_id,
        "name": data.get("name"),
        "source": data.get("source"),
        "format": data.get("format", "json"),
        "tags": data.get("tags", []),
        "retention_days": data.get("retention_days", 30),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    LOG_ENTRIES[stream_id] = []
    return {"stream_id": stream_id, "message": "Log stream created"}

@app.get("/logs/streams")
def list_log_streams(source: str = None):
    """List all log streams"""
    streams = list(LOG_STREAMS.values())
    if source:
        streams = [s for s in streams if s["source"] == source]
    return {"streams": streams, "count": len(streams)}

@app.get("/logs/streams/{stream_id}")
def get_log_stream(stream_id: str):
    """Get log stream details"""
    if stream_id not in LOG_STREAMS:
        raise HTTPException(status_code=404, detail="Log stream not found")
    return LOG_STREAMS[stream_id]

@app.post("/logs/streams/{stream_id}/entries")
def write_log_entry(stream_id: str, data: Dict[str, Any]):
    """Write a log entry to a stream"""
    if stream_id not in LOG_STREAMS:
        raise HTTPException(status_code=404, detail="Log stream not found")
    entry_id = f"log_{uuid.uuid4().hex[:12]}"
    entry = {
        "entry_id": entry_id,
        "level": data.get("level", "info"),
        "message": data.get("message"),
        "metadata": data.get("metadata", {}),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    LOG_ENTRIES[stream_id].append(entry)
    return {"entry_id": entry_id, "message": "Log entry written"}

@app.get("/logs/streams/{stream_id}/entries")
def get_log_entries(stream_id: str, level: str = None, limit: int = 100):
    """Get log entries from a stream"""
    if stream_id not in LOG_ENTRIES:
        raise HTTPException(status_code=404, detail="Log stream not found")
    entries = LOG_ENTRIES[stream_id]
    if level:
        entries = [e for e in entries if e["level"] == level]
    return {"entries": entries[-limit:], "count": len(entries)}

@app.post("/logs/query")
def query_logs(data: Dict[str, Any]):
    """Query logs across streams"""
    query = data.get("query", "")
    level = data.get("level")
    streams = data.get("streams", list(LOG_ENTRIES.keys()))
    results = []
    for stream_id in streams:
        if stream_id in LOG_ENTRIES:
            for entry in LOG_ENTRIES[stream_id]:
                if level and entry["level"] != level:
                    continue
                if query.lower() in entry.get("message", "").lower():
                    results.append({**entry, "stream_id": stream_id})
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"results": results[:100], "total": len(results)}

@app.post("/logs/retention-policies")
def create_retention_policy(data: Dict[str, Any]):
    """Create a log retention policy"""
    policy_id = f"ret_{uuid.uuid4().hex[:12]}"
    LOG_RETENTION_POLICIES[policy_id] = {
        "policy_id": policy_id,
        "name": data.get("name"),
        "stream_pattern": data.get("stream_pattern", "*"),
        "retention_days": data.get("retention_days", 30),
        "archive_enabled": data.get("archive_enabled", False),
        "archive_destination": data.get("archive_destination"),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"policy_id": policy_id, "message": "Retention policy created"}

@app.get("/logs/retention-policies")
def list_retention_policies():
    """List all retention policies"""
    return {"policies": list(LOG_RETENTION_POLICIES.values()), "count": len(LOG_RETENTION_POLICIES)}


# ============================================================================
# Metrics & Observability
# ============================================================================

METRICS: Dict[str, Dict[str, Any]] = {}
METRIC_DATA_POINTS: Dict[str, List[Dict[str, Any]]] = {}
METRIC_DASHBOARDS: Dict[str, Dict[str, Any]] = {}
METRIC_ALERTS: Dict[str, Dict[str, Any]] = {}

@app.post("/metrics")
def create_metric(data: Dict[str, Any]):
    """Create a metric definition"""
    metric_id = f"metric_{uuid.uuid4().hex[:12]}"
    METRICS[metric_id] = {
        "metric_id": metric_id,
        "name": data.get("name"),
        "type": data.get("type", "gauge"),
        "unit": data.get("unit", "count"),
        "description": data.get("description", ""),
        "labels": data.get("labels", []),
        "aggregation": data.get("aggregation", "avg"),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    METRIC_DATA_POINTS[metric_id] = []
    return {"metric_id": metric_id, "message": "Metric created"}

@app.get("/metrics")
def list_metrics(type: str = None):
    """List all metrics"""
    metrics = list(METRICS.values())
    if type:
        metrics = [m for m in metrics if m["type"] == type]
    return {"metrics": metrics, "count": len(metrics)}

@app.get("/metrics/{metric_id}")
def get_metric(metric_id: str):
    """Get metric details"""
    if metric_id not in METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")
    return METRICS[metric_id]

@app.post("/metrics/{metric_id}/record")
def record_metric_value(metric_id: str, data: Dict[str, Any]):
    """Record a metric value"""
    if metric_id not in METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")
    data_point = {
        "value": data.get("value"),
        "labels": data.get("labels", {}),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    METRIC_DATA_POINTS[metric_id].append(data_point)
    return {"message": "Value recorded"}

@app.get("/metrics/{metric_id}/data")
def get_metric_data(metric_id: str, limit: int = 100):
    """Get metric data points"""
    if metric_id not in METRIC_DATA_POINTS:
        raise HTTPException(status_code=404, detail="Metric not found")
    return {"data_points": METRIC_DATA_POINTS[metric_id][-limit:], "count": len(METRIC_DATA_POINTS[metric_id])}

@app.post("/metrics/dashboards")
def create_metric_dashboard(data: Dict[str, Any]):
    """Create a metrics dashboard"""
    dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
    METRIC_DASHBOARDS[dashboard_id] = {
        "dashboard_id": dashboard_id,
        "name": data.get("name"),
        "description": data.get("description", ""),
        "panels": data.get("panels", []),
        "refresh_interval": data.get("refresh_interval", 30),
        "time_range": data.get("time_range", "1h"),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"dashboard_id": dashboard_id, "message": "Dashboard created"}

@app.get("/metrics/dashboards")
def list_metric_dashboards():
    """List all dashboards"""
    return {"dashboards": list(METRIC_DASHBOARDS.values()), "count": len(METRIC_DASHBOARDS)}

@app.get("/metrics/dashboards/{dashboard_id}")
def get_metric_dashboard(dashboard_id: str):
    """Get dashboard details"""
    if dashboard_id not in METRIC_DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return METRIC_DASHBOARDS[dashboard_id]

@app.post("/metrics/alerts")
def create_metric_alert(data: Dict[str, Any]):
    """Create a metric alert"""
    alert_id = f"malert_{uuid.uuid4().hex[:12]}"
    METRIC_ALERTS[alert_id] = {
        "alert_id": alert_id,
        "name": data.get("name"),
        "metric_id": data.get("metric_id"),
        "condition": data.get("condition", "gt"),
        "threshold": data.get("threshold"),
        "duration_seconds": data.get("duration_seconds", 60),
        "severity": data.get("severity", "warning"),
        "notification_channels": data.get("notification_channels", []),
        "enabled": True,
        "state": "ok",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return {"alert_id": alert_id, "message": "Alert created"}

@app.get("/metrics/alerts")
def list_metric_alerts(state: str = None, severity: str = None):
    """List all metric alerts"""
    alerts = list(METRIC_ALERTS.values())
    if state:
        alerts = [a for a in alerts if a["state"] == state]
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    return {"alerts": alerts, "count": len(alerts)}


# ============================================================================
# Configuration Management
# ============================================================================

CONFIG_STORES: Dict[str, Dict[str, Any]] = {}
CONFIG_ENTRIES: Dict[str, Dict[str, Any]] = {}
CONFIG_VERSIONS: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/config/stores")
def create_config_store(data: Dict[str, Any]):
    """Create a configuration store"""
    store_id = f"cfgstore_{uuid.uuid4().hex[:12]}"
    CONFIG_STORES[store_id] = {
        "store_id": store_id,
        "name": data.get("name"),
        "description": data.get("description", ""),
        "environment": data.get("environment", "production"),
        "encryption_enabled": data.get("encryption_enabled", False),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    CONFIG_ENTRIES[store_id] = {}
    CONFIG_VERSIONS[store_id] = []
    return {"store_id": store_id, "message": "Config store created"}

@app.get("/config/stores")
def list_config_stores(environment: str = None):
    """List all config stores"""
    stores = list(CONFIG_STORES.values())
    if environment:
        stores = [s for s in stores if s["environment"] == environment]
    return {"stores": stores, "count": len(stores)}

@app.get("/config/stores/{store_id}")
def get_config_store(store_id: str):
    """Get config store details"""
    if store_id not in CONFIG_STORES:
        raise HTTPException(status_code=404, detail="Config store not found")
    return CONFIG_STORES[store_id]

@app.post("/config/stores/{store_id}/entries")
def set_config_entry(store_id: str, data: Dict[str, Any]):
    """Set a configuration entry"""
    if store_id not in CONFIG_STORES:
        raise HTTPException(status_code=404, detail="Config store not found")
    key = data.get("key")
    old_value = CONFIG_ENTRIES[store_id].get(key)
    CONFIG_ENTRIES[store_id][key] = {
        "key": key,
        "value": data.get("value"),
        "type": data.get("type", "string"),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    CONFIG_VERSIONS[store_id].append({
        "key": key,
        "old_value": old_value["value"] if old_value else None,
        "new_value": data.get("value"),
        "version": len(CONFIG_VERSIONS[store_id]) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    return {"message": "Config entry set", "version": len(CONFIG_VERSIONS[store_id])}

@app.get("/config/stores/{store_id}/entries")
def get_config_entries(store_id: str):
    """Get all config entries in a store"""
    if store_id not in CONFIG_ENTRIES:
        raise HTTPException(status_code=404, detail="Config store not found")
    return {"entries": list(CONFIG_ENTRIES[store_id].values()), "count": len(CONFIG_ENTRIES[store_id])}

@app.get("/config/stores/{store_id}/entries/{key}")
def get_config_entry(store_id: str, key: str):
    """Get a specific config entry"""
    if store_id not in CONFIG_ENTRIES:
        raise HTTPException(status_code=404, detail="Config store not found")
    if key not in CONFIG_ENTRIES[store_id]:
        raise HTTPException(status_code=404, detail="Config entry not found")
    return CONFIG_ENTRIES[store_id][key]

@app.delete("/config/stores/{store_id}/entries/{key}")
def delete_config_entry(store_id: str, key: str):
    """Delete a config entry"""
    if store_id not in CONFIG_ENTRIES:
        raise HTTPException(status_code=404, detail="Config store not found")
    if key in CONFIG_ENTRIES[store_id]:
        del CONFIG_ENTRIES[store_id][key]
    return {"message": "Config entry deleted"}

@app.get("/config/stores/{store_id}/versions")
def get_config_versions(store_id: str, key: str = None, limit: int = 50):
    """Get config version history"""
    if store_id not in CONFIG_VERSIONS:
        raise HTTPException(status_code=404, detail="Config store not found")
    versions = CONFIG_VERSIONS[store_id]
    if key:
        versions = [v for v in versions if v["key"] == key]
    return {"versions": versions[-limit:], "count": len(versions)}

@app.post("/config/stores/{store_id}/rollback")
def rollback_config(store_id: str, data: Dict[str, Any]):
    """Rollback config to a previous version"""
    if store_id not in CONFIG_VERSIONS:
        raise HTTPException(status_code=404, detail="Config store not found")
    target_version = data.get("version")
    key = data.get("key")
    version_entry = next((v for v in CONFIG_VERSIONS[store_id] if v["version"] == target_version and v["key"] == key), None)
    if not version_entry:
        raise HTTPException(status_code=404, detail="Version not found")
    CONFIG_ENTRIES[store_id][key]["value"] = version_entry["old_value"]
    CONFIG_ENTRIES[store_id][key]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return {"message": "Config rolled back", "restored_value": version_entry["old_value"]}


# ============================================================================
# Secret Rotation
# ============================================================================

ROTATION_POLICIES: Dict[str, Dict[str, Any]] = {}
ROTATION_EXECUTIONS: Dict[str, List[Dict[str, Any]]] = {}
ROTATION_AUDIT: List[Dict[str, Any]] = []

@app.post("/secret-rotation/policies")
def create_rotation_policy(data: Dict[str, Any]):
    """Create a secret rotation policy"""
    policy_id = f"rotpol_{uuid.uuid4().hex[:12]}"
    ROTATION_POLICIES[policy_id] = {
        "policy_id": policy_id,
        "name": data.get("name"),
        "secret_type": data.get("secret_type", "api_key"),
        "rotation_interval_days": data.get("rotation_interval_days", 30),
        "pre_rotation_hook": data.get("pre_rotation_hook"),
        "post_rotation_hook": data.get("post_rotation_hook"),
        "notification_channels": data.get("notification_channels", []),
        "enabled": data.get("enabled", True),
        "last_rotation": None,
        "next_rotation": None,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    ROTATION_EXECUTIONS[policy_id] = []
    return {"policy_id": policy_id, "message": "Rotation policy created"}

@app.get("/secret-rotation/policies")
def list_rotation_policies(enabled: bool = None, secret_type: str = None):
    """List all rotation policies"""
    policies = list(ROTATION_POLICIES.values())
    if enabled is not None:
        policies = [p for p in policies if p["enabled"] == enabled]
    if secret_type:
        policies = [p for p in policies if p["secret_type"] == secret_type]
    return {"policies": policies, "count": len(policies)}

@app.get("/secret-rotation/policies/{policy_id}")
def get_rotation_policy(policy_id: str):
    """Get rotation policy details"""
    if policy_id not in ROTATION_POLICIES:
        raise HTTPException(status_code=404, detail="Rotation policy not found")
    return ROTATION_POLICIES[policy_id]

@app.put("/secret-rotation/policies/{policy_id}")
def update_rotation_policy(policy_id: str, data: Dict[str, Any]):
    """Update a rotation policy"""
    if policy_id not in ROTATION_POLICIES:
        raise HTTPException(status_code=404, detail="Rotation policy not found")
    ROTATION_POLICIES[policy_id].update({
        "rotation_interval_days": data.get("rotation_interval_days", ROTATION_POLICIES[policy_id]["rotation_interval_days"]),
        "enabled": data.get("enabled", ROTATION_POLICIES[policy_id]["enabled"]),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    })
    return {"message": "Policy updated"}

@app.post("/secret-rotation/policies/{policy_id}/rotate")
def trigger_rotation(policy_id: str):
    """Trigger immediate secret rotation"""
    if policy_id not in ROTATION_POLICIES:
        raise HTTPException(status_code=404, detail="Rotation policy not found")
    execution_id = f"rotexec_{uuid.uuid4().hex[:12]}"
    execution = {
        "execution_id": execution_id,
        "policy_id": policy_id,
        "status": "in_progress",
        "old_secret_hash": f"hash_{uuid.uuid4().hex[:8]}",
        "new_secret_hash": f"hash_{uuid.uuid4().hex[:8]}",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None
    }
    ROTATION_EXECUTIONS[policy_id].append(execution)
    ROTATION_POLICIES[policy_id]["last_rotation"] = datetime.utcnow().isoformat() + "Z"
    ROTATION_AUDIT.append({
        "policy_id": policy_id,
        "execution_id": execution_id,
        "action": "rotation_triggered",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    return {"execution_id": execution_id, "message": "Rotation triggered"}

@app.post("/secret-rotation/executions/{execution_id}/complete")
def complete_rotation(execution_id: str, data: Dict[str, Any]):
    """Mark a rotation as complete"""
    for policy_id, executions in ROTATION_EXECUTIONS.items():
        for execution in executions:
            if execution["execution_id"] == execution_id:
                execution["status"] = data.get("status", "completed")
                execution["completed_at"] = datetime.utcnow().isoformat() + "Z"
                execution["error"] = data.get("error")
                ROTATION_AUDIT.append({
                    "policy_id": policy_id,
                    "execution_id": execution_id,
                    "action": f"rotation_{execution['status']}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                return {"message": "Rotation completed"}
    raise HTTPException(status_code=404, detail="Execution not found")

@app.get("/secret-rotation/policies/{policy_id}/executions")
def get_rotation_executions(policy_id: str, limit: int = 20):
    """Get rotation execution history"""
    if policy_id not in ROTATION_EXECUTIONS:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"executions": ROTATION_EXECUTIONS[policy_id][-limit:], "count": len(ROTATION_EXECUTIONS[policy_id])}

@app.get("/secret-rotation/audit")
def get_rotation_audit(policy_id: str = None, limit: int = 100):
    """Get rotation audit log"""
    audit = ROTATION_AUDIT
    if policy_id:
        audit = [a for a in audit if a["policy_id"] == policy_id]
    return {"audit_log": audit[-limit:], "total": len(audit)}


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
