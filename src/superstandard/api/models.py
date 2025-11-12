"""
API Models for PCF Agent Execution

Pydantic models for request/response validation and OpenAPI documentation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PCFAgentExecuteRequest(BaseModel):
    """
    Request model for PCF agent execution.

    Used by BPM systems to invoke agents with process variables.
    """
    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data for agent execution (process variables from BPM)",
        example={
            "market_segment": "Cloud Infrastructure",
            "geographic_scope": "North America",
            "industry_focus": ["Technology", "SaaS"]
        }
    )

    delegate_to_children: bool = Field(
        default=True,
        description="Whether to delegate execution to child agents (hierarchical execution)"
    )

    track_kpis: bool = Field(
        default=True,
        description="Whether to track and return KPI metrics"
    )

    timeout_seconds: Optional[int] = Field(
        default=300,
        description="Execution timeout in seconds (default: 5 minutes)",
        ge=1,
        le=3600
    )

    async_execution: bool = Field(
        default=False,
        description="Execute asynchronously and return execution ID for later retrieval"
    )

    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID from BPM process instance for tracking"
    )


class PCFAgentMetadata(BaseModel):
    """PCF agent metadata"""
    pcf_element_id: str = Field(..., description="5-digit PCF element ID")
    hierarchy_id: str = Field(..., description="Hierarchical ID (e.g., '1.1.1.1')")
    level: int = Field(..., description="PCF level (1-5)", ge=1, le=5)
    level_name: str = Field(..., description="Level name (Category, Process Group, etc.)")
    name: str = Field(..., description="Agent/process name")
    description: Optional[str] = Field(None, description="Agent description")

    category_id: Optional[str] = None
    category_name: Optional[str] = None
    process_group_id: Optional[str] = None
    process_group_name: Optional[str] = None
    process_id: Optional[str] = None
    process_name: Optional[str] = None
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None

    inputs: List[Dict[str, Any]] = Field(default_factory=list, description="Expected input parameters")
    outputs: List[Dict[str, Any]] = Field(default_factory=list, description="Output parameters")
    kpis: List[Dict[str, Any]] = Field(default_factory=list, description="KPI definitions")

    bpmn_model_available: bool = Field(default=False, description="Whether BPMN model exists")
    bpmn_model_path: Optional[str] = None


class KPIResult(BaseModel):
    """KPI measurement result"""
    name: str = Field(..., description="KPI name")
    value: Any = Field(..., description="KPI value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    target: Optional[Any] = Field(None, description="Target value")
    threshold_met: Optional[bool] = Field(None, description="Whether threshold was met")


class PCFAgentExecuteResponse(BaseModel):
    """
    Response model for PCF agent execution.

    Returned to BPM systems after agent execution completes.
    """
    execution_id: str = Field(..., description="Unique execution ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Whether execution succeeded")

    hierarchy_id: str = Field(..., description="PCF hierarchy ID that was executed")
    pcf_element_id: str = Field(..., description="PCF element ID")
    agent_name: str = Field(..., description="Agent name")

    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Agent execution result (domain-specific output)"
    )

    kpis: List[KPIResult] = Field(
        default_factory=list,
        description="KPI measurements from execution"
    )

    execution_time_ms: int = Field(..., description="Execution time in milliseconds")

    started_at: datetime = Field(..., description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")

    error: Optional[str] = Field(None, description="Error message if execution failed")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")

    correlation_id: Optional[str] = Field(None, description="Correlation ID from request")

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (agent version, runtime info, etc.)"
    )


class PCFAgentExecuteAsyncResponse(BaseModel):
    """Response for async execution request"""
    execution_id: str = Field(..., description="Unique execution ID for status checking")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Initial status")
    hierarchy_id: str = Field(..., description="PCF hierarchy ID")

    status_url: str = Field(..., description="URL to check execution status")
    estimated_completion_seconds: Optional[int] = Field(
        None,
        description="Estimated time to completion"
    )

    correlation_id: Optional[str] = Field(None, description="Correlation ID from request")


class PCFAgentStatusResponse(BaseModel):
    """Response for execution status check"""
    execution_id: str
    status: ExecutionStatus
    hierarchy_id: str

    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None

    result: Optional[PCFAgentExecuteResponse] = Field(
        None,
        description="Full result if execution completed"
    )

    started_at: datetime
    updated_at: datetime


class PCFAgentSearchRequest(BaseModel):
    """Request model for searching PCF agents"""
    query: Optional[str] = Field(None, description="Text search query")

    level: Optional[int] = Field(None, description="Filter by PCF level", ge=1, le=5)
    category_id: Optional[str] = Field(None, description="Filter by category")

    has_bpmn: Optional[bool] = Field(None, description="Filter by BPMN model availability")

    limit: int = Field(default=50, description="Max results to return", ge=1, le=1000)
    offset: int = Field(default=0, description="Offset for pagination", ge=0)


class PCFAgentSearchResult(BaseModel):
    """Single search result"""
    hierarchy_id: str
    pcf_element_id: str
    name: str
    level: int
    level_name: str
    category_name: str
    description: Optional[str] = None
    has_bpmn: bool
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class PCFAgentSearchResponse(BaseModel):
    """Response model for agent search"""
    total: int = Field(..., description="Total results matching query")
    count: int = Field(..., description="Number of results in this response")
    offset: int = Field(..., description="Current offset")

    results: List[PCFAgentSearchResult] = Field(
        default_factory=list,
        description="Search results"
    )


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)

    agents_available: int = Field(..., description="Number of available agents")

    uptime_seconds: int = Field(..., description="Service uptime in seconds")

    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependencies (database, cache, etc.)"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    detail: Optional[str] = Field(None, description="Detailed error information")

    hierarchy_id: Optional[str] = Field(None, description="Relevant hierarchy ID if applicable")

    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
