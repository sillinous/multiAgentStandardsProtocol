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
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
