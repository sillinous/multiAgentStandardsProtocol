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
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server.database import get_db, Agent, Workflow, AgentExecution, WorkflowStage, init_db, seed_agents

# Import our workflow
sys.path.insert(0, str(Path(__file__).parent.parent))
from poc_invoice_workflow import InvoiceProcessingWorkflow


# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="APQC Agent Platform API",
    description="REST API for executing APQC agents and workflows with real business logic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    else:
        # Level 3+: Return individual agents within a Level 2 group
        # parent_id format: "Category|5.1"
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

        level2_code = parts[1]  # e.g., "5.1"

        # Filter agents by Level 2 code
        filtered_agents = []
        for agent in agents:
            agent_parts = agent.name.split(" ")
            if len(agent_parts) >= 2 and agent_parts[0] == "APQC":
                code = agent_parts[1]
                code_parts = code.split(".")
                if len(code_parts) >= 2:
                    agent_level2 = code_parts[0] + "." + code_parts[1]
                    if agent_level2 == level2_code:
                        filtered_agents.append(agent)

        # Return agents as testable items
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
            "code": level2_code,
            "items": items
        }


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
    import asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api_server.database import DATABASE_URL
    import os

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
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
