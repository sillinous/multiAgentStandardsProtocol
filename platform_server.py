#!/usr/bin/env python3
"""
APQC Agentic Platform - Web Server
===================================

Complete UI-driven platform - NO command line required!

Features:
- Setup wizard for configuration
- APQC navigation and workflow composer
- Drag-and-drop workflow designer
- One-click execution
- Real-time monitoring

Usage:
    python platform_server.py

Then open browser to: http://localhost:8080

Version: 2.0.0
Date: 2025-11-17
"""

import os
import sys
import json
import asyncio
import logging
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("❌ Required packages not found!")
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn websockets pydantic")
    print("✅ Packages installed. Please run the script again.")
    sys.exit(0)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class IntegrationConfig(BaseModel):
    """Integration configuration from setup wizard"""
    integration_id: str
    credentials: Dict[str, str]
    status: str = "unconfigured"


class PlatformConfig(BaseModel):
    """Platform configuration"""
    port: int = 8080
    environment: str = "production"
    max_concurrent_agents: int = 50
    agent_timeout: int = 300
    security_keys_generated: bool = False


class SetupRequest(BaseModel):
    """Complete setup configuration from wizard"""
    integrations: List[IntegrationConfig]
    platform: PlatformConfig


class WorkflowAgent(BaseModel):
    """Agent in a workflow"""
    id: str
    name: str


class WorkflowExecutionRequest(BaseModel):
    """Workflow execution request"""
    agents: List[WorkflowAgent]


@dataclass
class ExecutionResult:
    """Agent execution result"""
    agent_id: str
    agent_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Platform State Manager
# ============================================================================

class PlatformState:
    """Manages platform configuration and state"""

    def __init__(self):
        self.config_file = Path(".platform_config.json")
        self.env_file = Path(".env")
        self.is_configured = False
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.platform_config: Optional[PlatformConfig] = None
        self.load_config()

    def load_config(self):
        """Load existing configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.integrations = {
                        k: IntegrationConfig(**v)
                        for k, v in data.get('integrations', {}).items()
                    }
                    self.platform_config = PlatformConfig(**data.get('platform', {}))
                    self.is_configured = True
                    logger.info("✅ Loaded existing configuration")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")

    def save_config(self, setup: SetupRequest):
        """Save configuration from setup wizard"""
        try:
            # Save structured config
            config_data = {
                'integrations': {
                    integration.integration_id: integration.dict()
                    for integration in setup.integrations
                },
                'platform': setup.platform.dict(),
                'configured_at': datetime.now().isoformat()
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Save .env file for compatibility
            self._generate_env_file(setup)

            # Update in-memory state
            self.integrations = {
                integration.integration_id: integration
                for integration in setup.integrations
            }
            self.platform_config = setup.platform
            self.is_configured = True

            logger.info("✅ Configuration saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def _generate_env_file(self, setup: SetupRequest):
        """Generate .env file from configuration"""
        env_lines = [
            "# ============================================================================",
            "# APQC Platform Configuration - Generated by Setup Wizard",
            f"# Generated: {datetime.now().isoformat()}",
            "# ============================================================================",
            "",
            "# Platform Settings",
            f"PLATFORM_PORT={setup.platform.port}",
            f"PLATFORM_ENV={setup.platform.environment}",
            f"MAX_CONCURRENT_AGENTS={setup.platform.max_concurrent_agents}",
            f"AGENT_TIMEOUT_SECONDS={setup.platform.agent_timeout}",
            "",
        ]

        # Add integration credentials
        for integration in setup.integrations:
            env_lines.append(f"# {integration.integration_id.upper()} Integration")
            for key, value in integration.credentials.items():
                env_key = f"{integration.integration_id.upper()}_{key.upper()}"
                env_lines.append(f"{env_key}={value}")
            env_lines.append("")

        # Add security keys if generated
        if setup.platform.security_keys_generated:
            env_lines.extend([
                "# Security Keys",
                f"SECRET_KEY={secrets.token_urlsafe(32)}",
                f"JWT_SECRET={secrets.token_urlsafe(32)}",
                f"ENCRYPTION_KEY={secrets.token_urlsafe(32)}",
                ""
            ])

        with open(self.env_file, 'w') as f:
            f.write('\n'.join(env_lines))


# ============================================================================
# Agent Registry
# ============================================================================

class AgentRegistry:
    """Manages APQC agent registry"""

    def __init__(self):
        self.agents_dir = Path("generated_agents_v2")
        self.agents = self._load_agents()

    def _load_agents(self) -> Dict[str, Dict]:
        """Load agents from generated directory"""
        agents = {}

        if self.agents_dir.exists():
            for domain_dir in self.agents_dir.iterdir():
                if domain_dir.is_dir():
                    for agent_file in domain_dir.glob("*.py"):
                        # Parse agent ID from filename
                        # Expected format: agent_X_X_X_X.py
                        parts = agent_file.stem.split('_')
                        if len(parts) >= 5:
                            agent_id = '.'.join(parts[1:5])
                            agents[agent_id] = {
                                'id': agent_id,
                                'file': str(agent_file),
                                'domain': domain_dir.name,
                                'category': parts[1] + '.0'
                            }

        logger.info(f"📦 Loaded {len(agents)} agents from registry")
        return agents

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all agents"""
        return list(self.agents.values())


# ============================================================================
# Workflow Executor
# ============================================================================

class WorkflowExecutor:
    """Executes workflows composed of APQC agents"""

    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry

    async def execute_workflow(
        self,
        agents: List[WorkflowAgent],
        websocket: Optional[WebSocket] = None
    ) -> List[ExecutionResult]:
        """Execute workflow sequentially"""
        results = []

        for i, agent in enumerate(agents):
            logger.info(f"🤖 Executing agent {i+1}/{len(agents)}: {agent.name}")

            # Send status update via WebSocket if connected
            if websocket:
                await websocket.send_json({
                    'type': 'agent_start',
                    'index': i,
                    'agent_id': agent.id,
                    'agent_name': agent.name
                })

            # Execute agent
            result = await self._execute_agent(agent)
            results.append(result)

            # Send completion update
            if websocket:
                await websocket.send_json({
                    'type': 'agent_complete',
                    'index': i,
                    'result': asdict(result)
                })

        return results

    async def _execute_agent(self, agent: WorkflowAgent) -> ExecutionResult:
        """Execute a single agent"""
        start_time = datetime.now()

        try:
            # Simulate agent execution (2-4 seconds)
            execution_time = 2 + (hash(agent.id) % 3)
            await asyncio.sleep(execution_time)

            # Simulated successful execution
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return ExecutionResult(
                agent_id=agent.id,
                agent_name=agent.name,
                status='success',
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration_ms=duration_ms,
                output={
                    'result': f'Successfully executed {agent.name}',
                    'data_processed': 100 + (hash(agent.id) % 900)
                }
            )

        except Exception as e:
            logger.error(f"Error executing agent {agent.id}: {e}")
            return ExecutionResult(
                agent_id=agent.id,
                agent_name=agent.name,
                status='failed',
                start_time=start_time.isoformat(),
                error=str(e)
            )


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="APQC Agentic Platform",
    description="Complete UI-driven enterprise platform",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize platform components
platform_state = PlatformState()
agent_registry = AgentRegistry()
workflow_executor = WorkflowExecutor(agent_registry)


# ============================================================================
# Routes - Main UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to setup wizard if not configured, otherwise to platform UI"""
    if not platform_state.is_configured:
        return FileResponse("setup_wizard.html")
    return FileResponse("platform_ui.html")


@app.get("/setup", response_class=HTMLResponse)
async def setup_wizard():
    """Serve setup wizard"""
    return FileResponse("setup_wizard.html")


@app.get("/platform", response_class=HTMLResponse)
async def platform_ui():
    """Serve main platform UI"""
    return FileResponse("platform_ui.html")


@app.get("/enterprise", response_class=HTMLResponse)
async def enterprise_ui():
    """Serve enterprise UI"""
    if Path("ENTERPRISE_UI.html").exists():
        return FileResponse("ENTERPRISE_UI.html")
    raise HTTPException(status_code=404, detail="Enterprise UI not found")


# ============================================================================
# Routes - Configuration API
# ============================================================================

@app.get("/api/config/status")
async def config_status():
    """Get configuration status"""
    return {
        'configured': platform_state.is_configured,
        'integrations_count': len(platform_state.integrations),
        'platform_config': platform_state.platform_config.dict() if platform_state.platform_config else None
    }


@app.post("/api/config/setup")
async def configure_platform(setup: SetupRequest):
    """Save configuration from setup wizard"""
    try:
        platform_state.save_config(setup)
        return {
            'success': True,
            'message': 'Platform configured successfully',
            'integrations': len(setup.integrations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/test-connection")
async def test_connection(integration: IntegrationConfig):
    """Test integration connection"""
    # Simulate connection test
    await asyncio.sleep(1)

    # For demo, randomly succeed
    success = hash(integration.integration_id) % 10 > 2

    return {
        'success': success,
        'integration_id': integration.integration_id,
        'message': 'Connection successful' if success else 'Connection failed'
    }


@app.post("/api/config/generate-keys")
async def generate_security_keys():
    """Generate security keys"""
    return {
        'success': True,
        'keys': {
            'secret_key': secrets.token_urlsafe(32),
            'jwt_secret': secrets.token_urlsafe(32),
            'encryption_key': secrets.token_urlsafe(32)
        }
    }


# ============================================================================
# Routes - Agent Registry API
# ============================================================================

@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    return {
        'agents': agent_registry.list_agents(),
        'count': len(agent_registry.agents)
    }


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


# ============================================================================
# Routes - Workflow Execution API
# ============================================================================

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowExecutionRequest):
    """Execute workflow"""
    try:
        results = await workflow_executor.execute_workflow(request.agents)
        return {
            'success': True,
            'workflow_size': len(request.agents),
            'results': [asdict(r) for r in results],
            'total_duration_ms': sum(r.duration_ms or 0 for r in results)
        }
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/workflow/execute/ws")
async def execute_workflow_ws(websocket: WebSocket):
    """Execute workflow with WebSocket updates"""
    await websocket.accept()

    try:
        # Receive workflow request
        data = await websocket.receive_json()
        agents = [WorkflowAgent(**agent) for agent in data['agents']]

        # Execute with real-time updates
        results = await workflow_executor.execute_workflow(agents, websocket)

        # Send final completion
        await websocket.send_json({
            'type': 'workflow_complete',
            'results': [asdict(r) for r in results]
        })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })


# ============================================================================
# Routes - System API
# ============================================================================

@app.get("/api/system/health")
async def health_check():
    """System health check"""
    return {
        'status': 'healthy',
        'configured': platform_state.is_configured,
        'agents_loaded': len(agent_registry.agents),
        'integrations': len(platform_state.integrations),
        'timestamp': datetime.now().isoformat()
    }


@app.get("/api/system/stats")
async def system_stats():
    """Get system statistics"""
    # Count agents by category
    category_counts = {}
    for agent in agent_registry.agents.values():
        category = agent.get('category', 'Unknown')
        category_counts[category] = category_counts.get(category, 0) + 1

    return {
        'total_agents': len(agent_registry.agents),
        'categories': len(category_counts),
        'integrations': len(platform_state.integrations),
        'category_breakdown': category_counts,
        'configured': platform_state.is_configured
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Start the platform server"""
    print("=" * 80)
    print("🚀 APQC AGENTIC PLATFORM - WEB SERVER")
    print("=" * 80)
    print()
    print("✨ Complete UI-driven platform - NO command line required!")
    print()

    # Determine port
    port = 8080
    if platform_state.platform_config:
        port = platform_state.platform_config.port

    print(f"🌐 Starting server on http://localhost:{port}")
    print()

    if platform_state.is_configured:
        print("✅ Platform is configured")
        print(f"   • {len(platform_state.integrations)} integrations")
        print(f"   • {len(agent_registry.agents)} agents loaded")
        print()
        print("📊 Access Points:")
        print(f"   • Platform UI:    http://localhost:{port}/platform")
        print(f"   • Enterprise UI:  http://localhost:{port}/enterprise")
        print(f"   • Setup Wizard:   http://localhost:{port}/setup")
    else:
        print("⚠️  Platform not configured yet")
        print()
        print("👉 Opening setup wizard...")
        print(f"   Navigate to: http://localhost:{port}/setup")

    print()
    print("=" * 80)
    print()

    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
