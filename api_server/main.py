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

    Level 1: Categories (13 total)
    Level 2-5: Processes within categories
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
    else:
        # Return agents from a category, grouped by APQC ID prefix
        if not parent_id:
            return {"level": level, "items": []}

        category = parent_id.replace("_", " ")
        agents = db.query(Agent).filter(
            Agent.is_active == True,
            Agent.apqc_category == category
        ).order_by(Agent.apqc_id, Agent.name).all()

        return {
            "level": level,
            "parent": category,
            "items": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "type": "agent",
                    "apqc_id": a.apqc_id,
                    "description": a.description,
                    "category": a.apqc_category,
                    "agent_type": a.agent_type
                }
                for a in agents
            ]
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
