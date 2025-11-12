"""
SuperStandard PCF Agent API

FastAPI application providing REST endpoints for PCF agent execution.
Enables BPM systems (Camunda, Activiti, etc.) to invoke agents as services.

Endpoints:
- POST /api/pcf/{hierarchy_id}/execute - Execute an agent
- GET /api/pcf/{hierarchy_id}/status/{execution_id} - Check execution status
- GET /api/pcf/{hierarchy_id} - Get agent metadata
- POST /api/pcf/search - Search for agents
- GET /api/health - Health check
- GET /docs - OpenAPI documentation (Swagger UI)
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .models import (
    PCFAgentExecuteRequest,
    PCFAgentExecuteResponse,
    PCFAgentExecuteAsyncResponse,
    PCFAgentStatusResponse,
    PCFAgentMetadata,
    PCFAgentSearchRequest,
    PCFAgentSearchResponse,
    PCFAgentSearchResult,
    HealthCheckResponse,
    ErrorResponse,
    ExecutionStatus,
    KPIResult
)
from .agent_loader import get_registry, AgentLoadError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Execution tracking
execution_store: Dict[str, Dict[str, Any]] = {}

# Service start time
START_TIME = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting SuperStandard PCF Agent API")
    registry = get_registry()
    stats = registry.get_statistics()
    logger.info(f"Loaded {stats['total_elements']} PCF elements")
    logger.info(f"Available agents: {stats['available_agents']}")

    yield

    # Shutdown
    logger.info("Shutting down SuperStandard PCF Agent API")


# Create FastAPI app
app = FastAPI(
    title="SuperStandard PCF Agent API",
    description=(
        "REST API for APQC PCF (Process Classification Framework) agent execution. "
        "Enables Business Process Management systems to invoke standardized business process agents."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AgentLoadError)
async def agent_load_error_handler(request: Request, exc: AgentLoadError):
    """Handle agent loading errors"""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error=str(exc),
            error_code="AGENT_NOT_FOUND",
            detail="The requested agent is not implemented yet."
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            detail=str(exc)
        ).model_dump()
    )


@app.post(
    "/api/pcf/{hierarchy_id}/execute",
    response_model=PCFAgentExecuteResponse,
    summary="Execute PCF Agent",
    description=(
        "Execute a PCF agent with the provided input data. "
        "This is the primary endpoint used by BPM systems to invoke agents from BPMN service tasks."
    ),
    responses={
        200: {"description": "Agent executed successfully"},
        202: {"description": "Async execution started", "model": PCFAgentExecuteAsyncResponse},
        404: {"description": "Agent not found", "model": ErrorResponse},
        500: {"description": "Execution error", "model": ErrorResponse}
    }
)
async def execute_agent(
    hierarchy_id: str = Path(
        ...,
        description="PCF hierarchy ID (e.g., '1.1.1.1')",
        example="1.1.1.1"
    ),
    request: PCFAgentExecuteRequest = ...
):
    """
    Execute a PCF agent.

    BPM Integration Example (Camunda):
    ```java
    // In PCFAgentDelegate.java
    HttpResponse response = httpClient.post(
        "http://api.superstandard.ai/api/pcf/1.1.1.1/execute",
        jsonBody(processVariables)
    );
    ```

    Process Variables Mapping:
    - Input data from request maps to agent inputs
    - Output data maps back to process variables
    - KPIs can be stored for monitoring
    """
    execution_id = str(uuid.uuid4())
    started_at = datetime.now()

    logger.info(
        f"Execution {execution_id}: Starting {hierarchy_id} "
        f"(correlation_id={request.correlation_id})"
    )

    # Get registry
    registry = get_registry()

    # Get metadata
    metadata = registry.get_metadata(hierarchy_id)
    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail=f"PCF element {hierarchy_id} not found in registry"
        )

    # Check if async execution requested
    if request.async_execution:
        # Store execution request for background processing
        execution_store[execution_id] = {
            'status': ExecutionStatus.PENDING,
            'hierarchy_id': hierarchy_id,
            'request': request,
            'started_at': started_at,
            'updated_at': started_at
        }

        # TODO: Start background task
        # asyncio.create_task(execute_agent_background(execution_id))

        return PCFAgentExecuteAsyncResponse(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            hierarchy_id=hierarchy_id,
            status_url=f"/api/pcf/{hierarchy_id}/status/{execution_id}",
            estimated_completion_seconds=60,
            correlation_id=request.correlation_id
        )

    # Synchronous execution
    try:
        # Get agent
        agent = registry.get_agent(hierarchy_id, use_cache=True)

        # Execute agent
        logger.info(f"Execution {execution_id}: Executing agent {agent.__class__.__name__}")

        result = await agent.execute_with_hierarchy(
            input_data=request.input_data,
            delegate_to_children=request.delegate_to_children
        )

        completed_at = datetime.now()
        execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.info(
            f"Execution {execution_id}: Completed successfully in {execution_time_ms}ms"
        )

        # Extract KPIs from result
        kpis = []
        if request.track_kpis and isinstance(result, dict):
            result_metadata = result.get('metadata', {})
            kpi_values = result_metadata.get('kpis', {})
            for kpi_name, kpi_value in kpi_values.items():
                kpis.append(KPIResult(
                    name=kpi_name,
                    value=kpi_value
                ))

        # Build response
        response = PCFAgentExecuteResponse(
            execution_id=execution_id,
            status=ExecutionStatus.COMPLETED,
            success=result.get('success', True) if isinstance(result, dict) else True,
            hierarchy_id=hierarchy_id,
            pcf_element_id=metadata.get('element_id', ''),
            agent_name=metadata.get('name', ''),
            result=result,
            kpis=kpis,
            execution_time_ms=execution_time_ms,
            started_at=started_at,
            completed_at=completed_at,
            correlation_id=request.correlation_id,
            metadata={
                'agent_class': agent.__class__.__name__,
                'delegated_to_children': request.delegate_to_children
            }
        )

        return response

    except AgentLoadError as e:
        logger.error(f"Execution {execution_id}: Agent load error: {e}")
        raise

    except Exception as e:
        completed_at = datetime.now()
        execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.error(f"Execution {execution_id}: Failed: {e}", exc_info=True)

        return PCFAgentExecuteResponse(
            execution_id=execution_id,
            status=ExecutionStatus.FAILED,
            success=False,
            hierarchy_id=hierarchy_id,
            pcf_element_id=metadata.get('element_id', ''),
            agent_name=metadata.get('name', ''),
            result=None,
            kpis=[],
            execution_time_ms=execution_time_ms,
            started_at=started_at,
            completed_at=completed_at,
            error=str(e),
            error_code="EXECUTION_ERROR",
            correlation_id=request.correlation_id
        )


@app.get(
    "/api/pcf/{hierarchy_id}/status/{execution_id}",
    response_model=PCFAgentStatusResponse,
    summary="Get Execution Status",
    description="Check the status of an async agent execution"
)
async def get_execution_status(
    hierarchy_id: str = Path(..., description="PCF hierarchy ID"),
    execution_id: str = Path(..., description="Execution ID")
):
    """Get status of async execution"""
    execution = execution_store.get(execution_id)

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found"
        )

    if execution['hierarchy_id'] != hierarchy_id:
        raise HTTPException(
            status_code=400,
            detail=f"Execution {execution_id} is for {execution['hierarchy_id']}, not {hierarchy_id}"
        )

    return PCFAgentStatusResponse(
        execution_id=execution_id,
        status=execution['status'],
        hierarchy_id=hierarchy_id,
        result=execution.get('result'),
        started_at=execution['started_at'],
        updated_at=execution['updated_at']
    )


@app.get(
    "/api/pcf/{hierarchy_id}",
    response_model=PCFAgentMetadata,
    summary="Get Agent Metadata",
    description="Retrieve metadata for a PCF agent including inputs, outputs, and KPIs"
)
async def get_agent_metadata(
    hierarchy_id: str = Path(
        ...,
        description="PCF hierarchy ID",
        example="1.1.1.1"
    )
):
    """Get agent metadata"""
    registry = get_registry()
    metadata = registry.get_metadata(hierarchy_id)

    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail=f"PCF element {hierarchy_id} not found"
        )

    # Check if BPMN model exists
    bpmn_model_path = None
    bpmn_available = False

    # Check if this is a process (level 3)
    if metadata.get('level') == 3:
        from pathlib import Path
        bpmn_dir = Path(__file__).parent.parent / 'agents/pcf/bpmn_models'
        process_id_clean = hierarchy_id.replace('.', '_')

        # Try to find BPMN file
        for bpmn_file in bpmn_dir.glob(f"process_{process_id_clean}_*.bpmn"):
            bpmn_model_path = str(bpmn_file)
            bpmn_available = True
            break

    return PCFAgentMetadata(
        pcf_element_id=metadata.get('element_id', ''),
        hierarchy_id=hierarchy_id,
        level=metadata.get('level', 0),
        level_name=metadata.get('level_name', ''),
        name=metadata.get('name', ''),
        description=metadata.get('description'),
        category_id=metadata.get('category_id'),
        category_name=metadata.get('category_name'),
        process_group_id=metadata.get('process_group_id'),
        process_group_name=metadata.get('process_group_name'),
        process_id=metadata.get('process_id'),
        process_name=metadata.get('process_name'),
        activity_id=metadata.get('activity_id'),
        activity_name=metadata.get('activity_name'),
        inputs=metadata.get('inputs', []),
        outputs=metadata.get('outputs', []),
        kpis=metadata.get('kpis', []),
        bpmn_model_available=bpmn_available,
        bpmn_model_path=bpmn_model_path
    )


@app.post(
    "/api/pcf/search",
    response_model=PCFAgentSearchResponse,
    summary="Search PCF Agents",
    description="Search for PCF agents by text query, level, category, or implementation status"
)
async def search_agents(request: PCFAgentSearchRequest):
    """Search for agents"""
    registry = get_registry()

    results = registry.search(
        query=request.query,
        level=request.level,
        category_id=request.category_id,
        has_implementation=None,  # Search all for now
        limit=request.limit,
        offset=request.offset
    )

    # Convert to response format
    search_results = []
    for item in results:
        search_results.append(PCFAgentSearchResult(
            hierarchy_id=item['hierarchy_id'],
            pcf_element_id=item.get('element_id', ''),
            name=item.get('name', ''),
            level=item.get('level', 0),
            level_name=item.get('level_name', ''),
            category_name=item.get('category_name', ''),
            description=item.get('description'),
            has_bpmn=(item.get('level') == 3),  # Simplified check
            relevance_score=item.get('relevance_score', 1.0)
        ))

    return PCFAgentSearchResponse(
        total=len(results),  # TODO: Get actual total before limit
        count=len(search_results),
        offset=request.offset,
        results=search_results
    )


@app.get(
    "/api/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check API health and service status"
)
async def health_check():
    """Health check endpoint"""
    registry = get_registry()
    stats = registry.get_statistics()

    uptime = (datetime.now() - START_TIME).total_seconds()

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        agents_available=stats['implemented_agents'],
        uptime_seconds=int(uptime),
        dependencies={
            'pcf_registry': 'ok',
            'agent_loader': 'ok'
        }
    )


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect to docs"""
    return {
        "message": "SuperStandard PCF Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "superstandard.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)
