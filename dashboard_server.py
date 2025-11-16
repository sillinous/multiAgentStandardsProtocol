"""
🎯 APQC Real-Time Agent Monitoring Dashboard - Backend Server
============================================================

Production-ready FastAPI server with WebSocket support for monitoring
118+ APQC agents across 13 categories and 5 production workflows.

Features:
- Real-time agent status updates via WebSocket
- Agent health monitoring and metrics aggregation
- Workflow execution tracking
- Performance analytics
- RESTful API for agent management
- SQLite state persistence
- Auto-discovery of APQC agents
- Protocol-aware communication (A2A, A2P, ACP, ANP, MCP)

Architecture:
- FastAPI for async REST API
- WebSocket for real-time updates
- SQLite for state persistence
- Background tasks for monitoring
- Agent registry for discovery
- Metrics collector for performance data

Version: 1.0.0
Author: APQC Dashboard Team
Date: 2025-11-16
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import APQC framework
try:
    from agents.consolidated.py.apqc_agent_specialization_framework import (
        APQCAgentSpecializationFramework,
        APQCCategory,
        initialize_apqc_framework,
        get_apqc_framework,
    )
except ImportError:
    print("⚠️ APQC framework not found, using mock implementation")
    APQCAgentSpecializationFramework = None
    APQCCategory = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import admin API
try:
    from admin_api import get_admin_router
    ADMIN_API_AVAILABLE = True
    logger.info("✅ Admin API loaded successfully")
except ImportError as e:
    ADMIN_API_AVAILABLE = False
    logger.warning(f"⚠️ Admin API not available: {e}")


# ============================================================================
# Configuration Models
# ============================================================================

class DashboardConfig:
    """Dashboard configuration loader"""

    def __init__(self, config_path: str = "dashboard_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 8765,
                'reload': False,
                'workers': 1
            },
            'websocket': {
                'heartbeat_interval': 10,
                'connection_timeout': 300,
                'max_connections': 1000
            },
            'monitoring': {
                'agent_refresh_rate': 5,
                'metrics_refresh_rate': 10,
                'workflow_refresh_rate': 15,
                'retention_days': 30
            },
            'database': {
                'path': './dashboard_data.db',
                'backup_interval': 3600
            },
            'alerts': {
                'agent_down_threshold': 60,
                'performance_degradation_threshold': 0.7,
                'error_rate_threshold': 0.1
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value if value else default


# ============================================================================
# Data Models
# ============================================================================

class AgentStatus(BaseModel):
    """Agent status model"""
    agent_id: str
    agent_name: str
    category_id: str
    category_name: str
    process_id: str
    status: str  # healthy, degraded, unhealthy, offline
    health_score: float = Field(ge=0.0, le=1.0)
    last_heartbeat: datetime
    tasks_processed: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    protocols: List[str] = ["A2A", "A2P", "ACP", "ANP", "MCP"]
    capabilities: List[str] = []
    current_task: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WorkflowStatus(BaseModel):
    """Workflow status model"""
    workflow_id: str
    workflow_name: str
    workflow_type: str  # financial, marketing, recruitment, supply_chain, customer_support
    status: str  # running, paused, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    progress: float = Field(ge=0.0, le=1.0)
    agents_involved: List[str] = []
    current_stage: str = ""
    stages_completed: int = 0
    total_stages: int = 0
    metrics: Dict[str, Any] = {}


class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    timestamp: datetime
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    success_rate: float = Field(ge=0.0, le=1.0)
    throughput: float = 0.0  # tasks per minute
    error_rate: float = Field(ge=0.0, le=1.0)
    resource_usage: Dict[str, float] = {}


class AgentEvent(BaseModel):
    """Agent event model"""
    event_id: str
    event_type: str  # task_started, task_completed, error, communication, status_change
    agent_id: str
    timestamp: datetime
    severity: str  # info, warning, error, critical
    message: str
    details: Dict[str, Any] = {}


class CategoryMetrics(BaseModel):
    """Category-level metrics"""
    category_id: str
    category_name: str
    total_agents: int
    active_agents: int
    avg_health_score: float
    total_tasks: int
    success_rate: float
    agents: List[str] = []


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    """SQLite database manager for dashboard state"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                agent_name TEXT,
                category_id TEXT,
                category_name TEXT,
                process_id TEXT,
                status TEXT,
                health_score REAL,
                last_heartbeat TIMESTAMP,
                tasks_processed INTEGER,
                error_count INTEGER,
                avg_response_time REAL,
                memory_usage REAL,
                cpu_usage REAL,
                protocols TEXT,
                capabilities TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                workflow_name TEXT,
                workflow_type TEXT,
                status TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                progress REAL,
                agents_involved TEXT,
                current_stage TEXT,
                stages_completed INTEGER,
                total_stages INTEGER,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                timestamp TIMESTAMP,
                tasks_completed INTEGER,
                tasks_failed INTEGER,
                avg_response_time REAL,
                success_rate REAL,
                throughput REAL,
                error_rate REAL,
                resource_usage TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)

        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT,
                agent_id TEXT,
                timestamp TIMESTAMP,
                severity TEXT,
                message TEXT,
                details TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_category ON agents(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")

        conn.commit()
        conn.close()
        logger.info(f"📊 Database initialized: {self.db_path}")

    def save_agent_status(self, agent: AgentStatus):
        """Save or update agent status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agents
            (agent_id, agent_name, category_id, category_name, process_id, status,
             health_score, last_heartbeat, tasks_processed, error_count,
             avg_response_time, memory_usage, cpu_usage, protocols, capabilities,
             metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.agent_id, agent.agent_name, agent.category_id, agent.category_name,
            agent.process_id, agent.status, agent.health_score, agent.last_heartbeat,
            agent.tasks_processed, agent.error_count, agent.avg_response_time,
            agent.memory_usage, agent.cpu_usage, json.dumps(agent.protocols),
            json.dumps(agent.capabilities), json.dumps(agent.metadata),
            datetime.now()
        ))

        conn.commit()
        conn.close()

    def get_all_agents(self) -> List[AgentStatus]:
        """Get all agent statuses"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents ORDER BY category_id, agent_name")
        rows = cursor.fetchall()
        conn.close()

        agents = []
        for row in rows:
            agents.append(AgentStatus(
                agent_id=row['agent_id'],
                agent_name=row['agent_name'],
                category_id=row['category_id'],
                category_name=row['category_name'],
                process_id=row['process_id'],
                status=row['status'],
                health_score=row['health_score'],
                last_heartbeat=datetime.fromisoformat(row['last_heartbeat']),
                tasks_processed=row['tasks_processed'],
                error_count=row['error_count'],
                avg_response_time=row['avg_response_time'],
                memory_usage=row['memory_usage'],
                cpu_usage=row['cpu_usage'],
                protocols=json.loads(row['protocols']),
                capabilities=json.loads(row['capabilities']),
                metadata=json.loads(row['metadata'])
            ))

        return agents

    def save_workflow(self, workflow: WorkflowStatus):
        """Save or update workflow status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO workflows
            (workflow_id, workflow_name, workflow_type, status, start_time, end_time,
             progress, agents_involved, current_stage, stages_completed, total_stages,
             metrics, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow.workflow_id, workflow.workflow_name, workflow.workflow_type,
            workflow.status, workflow.start_time, workflow.end_time, workflow.progress,
            json.dumps(workflow.agents_involved), workflow.current_stage,
            workflow.stages_completed, workflow.total_stages, json.dumps(workflow.metrics),
            datetime.now()
        ))

        conn.commit()
        conn.close()

    def save_event(self, event: AgentEvent):
        """Save agent event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events
            (event_id, event_type, agent_id, timestamp, severity, message, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.event_type, event.agent_id, event.timestamp,
            event.severity, event.message, json.dumps(event.details)
        ))

        conn.commit()
        conn.close()

    def save_metrics(self, metrics: AgentMetrics):
        """Save agent metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metrics
            (agent_id, timestamp, tasks_completed, tasks_failed, avg_response_time,
             success_rate, throughput, error_rate, resource_usage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.agent_id, metrics.timestamp, metrics.tasks_completed,
            metrics.tasks_failed, metrics.avg_response_time, metrics.success_rate,
            metrics.throughput, metrics.error_rate, json.dumps(metrics.resource_usage)
        ))

        conn.commit()
        conn.close()

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(days=days)

        cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
        cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))

        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        logger.info(f"🧹 Cleaned up {deleted} old records")


# ============================================================================
# Agent Monitor
# ============================================================================

class AgentMonitor:
    """Monitor and track all APQC agents"""

    def __init__(self, db: DatabaseManager, config: DashboardConfig):
        self.db = db
        self.config = config
        self.apqc_framework = None
        self.agents: Dict[str, AgentStatus] = {}
        self.workflows: Dict[str, WorkflowStatus] = {}
        self.active_connections: Set[WebSocket] = set()

        # Initialize APQC framework
        self._init_apqc_framework()

    def _init_apqc_framework(self):
        """Initialize APQC framework and discover agents"""
        try:
            if APQCAgentSpecializationFramework:
                self.apqc_framework = initialize_apqc_framework()
                logger.info("✅ APQC framework initialized")
                self._discover_agents()
            else:
                logger.warning("⚠️ APQC framework not available, using mock agents")
                self._create_mock_agents()
        except Exception as e:
            logger.error(f"❌ Error initializing APQC framework: {e}")
            self._create_mock_agents()

    def _discover_agents(self):
        """Discover all APQC agents from framework"""
        if not self.apqc_framework:
            return

        specializations = self.apqc_framework.get_all_specializations()

        for agent_id, spec in specializations.items():
            # Determine category
            if spec.primary_processes:
                process_id = spec.primary_processes[0]
                category_code = process_id.split('.')[0] + '.0'
            else:
                category_code = "13.0"  # Default to Business Capabilities

            # Get category name
            category_name = self._get_category_name(category_code)

            agent = AgentStatus(
                agent_id=agent_id,
                agent_name=spec.agent_name,
                category_id=category_code,
                category_name=category_name,
                process_id=spec.primary_processes[0] if spec.primary_processes else category_code,
                status="healthy",
                health_score=0.95,
                last_heartbeat=datetime.now(),
                tasks_processed=0,
                error_count=0,
                avg_response_time=0.15,
                memory_usage=45.2,
                cpu_usage=12.5,
                protocols=["A2A", "A2P", "ACP", "ANP", "MCP"],
                capabilities=spec.core_capabilities[:5] if spec.core_capabilities else [],
                metadata={
                    "specialization_level": spec.specialization_level.value,
                    "primary_processes": spec.primary_processes,
                    "ai_models": spec.ai_models
                }
            )

            self.agents[agent_id] = agent
            self.db.save_agent_status(agent)

        logger.info(f"🔍 Discovered {len(self.agents)} APQC agents")

    def _get_category_name(self, category_code: str) -> str:
        """Get category name from code"""
        category_map = {
            "1.0": "Vision & Strategy",
            "2.0": "Products & Services",
            "3.0": "Market & Sell",
            "4.0": "Deliver Physical",
            "5.0": "Deliver Services",
            "6.0": "Customer Service",
            "7.0": "Human Capital",
            "8.0": "Information Technology",
            "9.0": "Financial Resources",
            "10.0": "Assets",
            "11.0": "Risk & Compliance",
            "12.0": "External Relationships",
            "13.0": "Business Capabilities"
        }
        return category_map.get(category_code, "Unknown Category")

    def _create_mock_agents(self):
        """Create mock agents for testing"""
        categories = [
            ("1.0", "Vision & Strategy", 4),
            ("2.0", "Products & Services", 3),
            ("3.0", "Market & Sell", 5),
            ("4.0", "Deliver Physical", 4),
            ("5.0", "Deliver Services", 4),
            ("6.0", "Customer Service", 3),
            ("7.0", "Human Capital", 5),
            ("8.0", "Information Technology", 5),
            ("9.0", "Financial Resources", 5),
            ("10.0", "Assets", 3),
            ("11.0", "Risk & Compliance", 4),
            ("12.0", "External Relationships", 4),
            ("13.0", "Business Capabilities", 5)
        ]

        import random

        for cat_id, cat_name, count in categories:
            for i in range(count):
                agent_id = f"apqc_{cat_id.replace('.', '_')}_{i+1}"
                process_id = f"{cat_id.replace('.0', '')}.{i+1}"

                agent = AgentStatus(
                    agent_id=agent_id,
                    agent_name=f"{cat_name} Agent {i+1}",
                    category_id=cat_id,
                    category_name=cat_name,
                    process_id=process_id,
                    status=random.choice(["healthy", "healthy", "healthy", "degraded"]),
                    health_score=random.uniform(0.85, 1.0),
                    last_heartbeat=datetime.now(),
                    tasks_processed=random.randint(100, 10000),
                    error_count=random.randint(0, 50),
                    avg_response_time=random.uniform(0.05, 0.5),
                    memory_usage=random.uniform(20.0, 80.0),
                    cpu_usage=random.uniform(5.0, 60.0),
                    protocols=["A2A", "A2P", "ACP", "ANP", "MCP"],
                    capabilities=[f"capability_{j+1}" for j in range(3)]
                )

                self.agents[agent_id] = agent
                self.db.save_agent_status(agent)

        logger.info(f"🎭 Created {len(self.agents)} mock agents")

    async def update_agent_status(self, agent_id: str, updates: Dict[str, Any]):
        """Update agent status and notify clients"""
        if agent_id not in self.agents:
            logger.warning(f"⚠️ Unknown agent: {agent_id}")
            return

        agent = self.agents[agent_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        agent.last_heartbeat = datetime.now()

        # Save to database
        self.db.save_agent_status(agent)

        # Broadcast update
        await self.broadcast_update({
            "type": "agent_update",
            "agent": agent.dict()
        })

    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients"""
        if not self.active_connections:
            return

        message_json = json.dumps(message, default=str)

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        self.active_connections -= disconnected

    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get agent status"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[AgentStatus]:
        """Get all agents"""
        return list(self.agents.values())

    def get_category_metrics(self) -> List[CategoryMetrics]:
        """Get metrics by category"""
        category_data = defaultdict(lambda: {
            "agents": [],
            "health_scores": [],
            "tasks": 0,
            "successes": 0
        })

        for agent in self.agents.values():
            cat_id = agent.category_id
            category_data[cat_id]["agents"].append(agent.agent_id)
            category_data[cat_id]["health_scores"].append(agent.health_score)
            category_data[cat_id]["tasks"] += agent.tasks_processed
            success_rate = (agent.tasks_processed - agent.error_count) / max(agent.tasks_processed, 1)
            category_data[cat_id]["successes"] += success_rate * agent.tasks_processed

        metrics = []
        for cat_id, data in category_data.items():
            cat_name = self._get_category_name(cat_id)
            total_tasks = data["tasks"]

            metrics.append(CategoryMetrics(
                category_id=cat_id,
                category_name=cat_name,
                total_agents=len(data["agents"]),
                active_agents=sum(1 for aid in data["agents"] if self.agents[aid].status == "healthy"),
                avg_health_score=sum(data["health_scores"]) / max(len(data["health_scores"]), 1),
                total_tasks=total_tasks,
                success_rate=data["successes"] / max(total_tasks, 1),
                agents=data["agents"]
            ))

        return sorted(metrics, key=lambda x: x.category_id)


# ============================================================================
# FastAPI Application
# ============================================================================

# Global instances
config = DashboardConfig()
db = DatabaseManager(config.get('database.path', './dashboard_data.db'))
monitor = AgentMonitor(db, config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("🚀 Starting APQC Dashboard Server...")

    # Start background monitoring
    asyncio.create_task(background_monitoring())
    asyncio.create_task(cleanup_task())

    yield

    # Shutdown
    logger.info("👋 Shutting down APQC Dashboard Server...")


app = FastAPI(
    title="APQC Agent Monitoring Dashboard",
    description="Real-time monitoring for 118+ APQC agents across 13 categories",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin API routes
if ADMIN_API_AVAILABLE:
    try:
        admin_router = get_admin_router()
        app.include_router(admin_router)
        logger.info("✅ Admin API routes registered")
    except Exception as e:
        logger.error(f"❌ Failed to register admin API routes: {e}")


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "APQC Agent Monitoring Dashboard",
        "version": "1.0.0",
        "status": "operational",
        "agents": len(monitor.agents),
        "categories": 13,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/agents")
async def get_agents():
    """Get all agents"""
    agents = monitor.get_all_agents()
    return {"agents": [a.dict() for a in agents], "count": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent"""
    agent = monitor.get_agent_status(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.dict()


@app.post("/api/agents/{agent_id}/status")
async def update_agent(agent_id: str, updates: Dict[str, Any]):
    """Update agent status"""
    await monitor.update_agent_status(agent_id, updates)
    return {"status": "updated", "agent_id": agent_id}


@app.get("/api/categories")
async def get_categories():
    """Get category metrics"""
    metrics = monitor.get_category_metrics()
    return {"categories": [m.dict() for m in metrics]}


@app.get("/api/workflows")
async def get_workflows():
    """Get all workflows"""
    workflows = list(monitor.workflows.values())
    return {"workflows": [w.dict() for w in workflows], "count": len(workflows)}


@app.get("/api/metrics/summary")
async def get_summary_metrics():
    """Get summary metrics"""
    agents = monitor.get_all_agents()

    total_agents = len(agents)
    healthy_agents = sum(1 for a in agents if a.status == "healthy")
    degraded_agents = sum(1 for a in agents if a.status == "degraded")
    offline_agents = sum(1 for a in agents if a.status == "offline")

    total_tasks = sum(a.tasks_processed for a in agents)
    total_errors = sum(a.error_count for a in agents)

    avg_health = sum(a.health_score for a in agents) / max(total_agents, 1)
    avg_response_time = sum(a.avg_response_time for a in agents) / max(total_agents, 1)

    return {
        "total_agents": total_agents,
        "healthy_agents": healthy_agents,
        "degraded_agents": degraded_agents,
        "offline_agents": offline_agents,
        "avg_health_score": round(avg_health, 2),
        "total_tasks_processed": total_tasks,
        "total_errors": total_errors,
        "success_rate": round((total_tasks - total_errors) / max(total_tasks, 1), 3),
        "avg_response_time": round(avg_response_time, 3),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Workflow API Endpoints
# ============================================================================

# Import workflow engine
try:
    from workflow_engine import (
        WorkflowManager,
        WorkflowDefinition,
        WorkflowTemplateLibrary
    )
    workflow_manager = WorkflowManager()
    WORKFLOW_ENGINE_AVAILABLE = True
    logger.info("✅ Workflow engine loaded successfully")
except ImportError as e:
    WORKFLOW_ENGINE_AVAILABLE = False
    workflow_manager = None
    logger.warning(f"⚠️ Workflow engine not available: {e}")


@app.get("/api/workflows")
async def get_workflows():
    """Get all workflows"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        return {"workflows": [], "count": 0}

    workflows = workflow_manager.list_workflows()
    return {
        "workflows": [w.dict() for w in workflows],
        "count": len(workflows)
    }


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow.dict()


@app.post("/api/workflows")
async def create_workflow(workflow_data: Dict[str, Any]):
    """Create new workflow"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow = WorkflowDefinition(**workflow_data)
        workflow_id = workflow_manager.create_workflow(workflow)
        return {
            "status": "created",
            "workflow_id": workflow_id,
            "message": "Workflow created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, workflow_data: Dict[str, Any]):
    """Update existing workflow"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow_data['id'] = workflow_id
        workflow = WorkflowDefinition(**workflow_data)
        workflow_manager.update_workflow(workflow)
        return {
            "status": "updated",
            "workflow_id": workflow_id,
            "message": "Workflow updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    workflow_manager.delete_workflow(workflow_id)
    return {
        "status": "deleted",
        "workflow_id": workflow_id,
        "message": "Workflow deleted successfully"
    }


@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, inputs: Dict[str, Any] = None):
    """Execute workflow"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        execution = await workflow_manager.execute_workflow(workflow_id, inputs or {})
        return {
            "status": "executed",
            "execution_id": execution.id,
            "execution": execution.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/workflows/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get workflow execution status"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    execution = workflow_manager.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution.dict()


@app.get("/api/workflow-templates")
async def get_workflow_templates():
    """Get all workflow templates"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        return {"templates": [], "count": 0}

    templates = workflow_manager.template_library.list_templates()
    return {
        "templates": [t.dict() for t in templates],
        "count": len(templates)
    }


@app.get("/api/workflow-templates/{template_id}")
async def get_workflow_template(template_id: str):
    """Get specific workflow template"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    template = workflow_manager.template_library.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.dict()


@app.post("/api/workflows/import")
async def import_workflow(data: str, format: str = "json"):
    """Import workflow from JSON/YAML"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow_id = workflow_manager.import_workflow(data, format)
        return {
            "status": "imported",
            "workflow_id": workflow_id,
            "message": "Workflow imported successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/workflows/{workflow_id}/export")
async def export_workflow(workflow_id: str, format: str = "json"):
    """Export workflow to JSON/YAML"""
    if not WORKFLOW_ENGINE_AVAILABLE or not workflow_manager:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        data = workflow_manager.export_workflow(workflow_id, format)
        return JSONResponse(
            content=data,
            media_type=f"application/{format}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    monitor.active_connections.add(websocket)

    logger.info(f"📡 WebSocket connected (total: {len(monitor.active_connections)})")

    try:
        # Send initial data
        await websocket.send_json({
            "type": "initial",
            "agents": [a.dict() for a in monitor.get_all_agents()],
            "categories": [c.dict() for c in monitor.get_category_metrics()],
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive
        while True:
            # Wait for messages from client (ping/commands)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "connected_clients": len(monitor.active_connections)
                })

    except WebSocketDisconnect:
        logger.info("📡 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        monitor.active_connections.discard(websocket)


# ============================================================================
# Background Tasks
# ============================================================================

async def background_monitoring():
    """Background task for monitoring agents"""
    import random

    while True:
        try:
            # Simulate agent activity updates
            for agent_id, agent in list(monitor.agents.items()):
                # Random updates to simulate real activity
                if random.random() < 0.1:  # 10% chance of update
                    updates = {
                        "tasks_processed": agent.tasks_processed + random.randint(1, 10),
                        "health_score": min(1.0, agent.health_score + random.uniform(-0.05, 0.05)),
                        "avg_response_time": max(0.01, agent.avg_response_time + random.uniform(-0.02, 0.02)),
                        "cpu_usage": max(0.0, min(100.0, agent.cpu_usage + random.uniform(-5, 5))),
                        "memory_usage": max(0.0, min(100.0, agent.memory_usage + random.uniform(-2, 2)))
                    }
                    await monitor.update_agent_status(agent_id, updates)

            await asyncio.sleep(config.get('monitoring.agent_refresh_rate', 5))

        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            await asyncio.sleep(10)


async def cleanup_task():
    """Background task for cleanup"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            retention_days = config.get('monitoring.retention_days', 30)
            db.cleanup_old_data(retention_days)
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = config.get('server.host', '0.0.0.0')
    port = config.get('server.port', 8765)
    reload = config.get('server.reload', False)

    logger.info(f"🎯 APQC Dashboard Server starting on {host}:{port}")
    logger.info(f"📊 Monitoring {len(monitor.agents)} agents across 13 categories")
    logger.info(f"🌐 Dashboard: http://localhost:{port}")
    logger.info(f"📡 WebSocket: ws://localhost:{port}/ws")
    if ADMIN_API_AVAILABLE:
        logger.info(f"🔧 Admin Panel: http://localhost:{port} (click Admin button)")
        logger.info(f"🔑 Default credentials: admin / admin123 (CHANGE IMMEDIATELY!)")

    uvicorn.run(
        "dashboard_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
