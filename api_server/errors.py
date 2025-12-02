"""
Standardized Error Handling for Agent Platform API
===================================================

Provides consistent error responses across all API endpoints.

Usage:
    from api_server.errors import (
        APIError,
        NotFoundError,
        ValidationError,
        WorkflowExecutionError,
        IntegrationError,
        error_response
    )

    # Raise custom errors
    raise NotFoundError("Agent", agent_id)
    raise ValidationError("Invalid APQC code format")
    raise WorkflowExecutionError(workflow_id, "Step 3 failed", details={...})

    # Or use the error_response helper
    return error_response(404, "NOT_FOUND", "Agent not found")
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
import logging

# Configure module logger
logger = logging.getLogger("api_server.errors")


# =============================================================================
# Standard Error Response Format
# =============================================================================

def error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        error_code: Machine-readable error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable error message
        details: Optional additional error details
        request_id: Optional request tracking ID

    Returns:
        JSONResponse with standardized error format
    """
    content = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }

    if details:
        content["error"]["details"] = details

    if request_id:
        content["error"]["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=content)


# =============================================================================
# Custom Exception Classes
# =============================================================================

class APIError(Exception):
    """Base class for all API errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def to_response(self, request_id: Optional[str] = None) -> JSONResponse:
        """Convert exception to standardized JSON response"""
        return error_response(
            status_code=self.status_code,
            error_code=self.error_code,
            message=self.message,
            details=self.details if self.details else None,
            request_id=request_id
        )


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})}
        )


class ValidationError(APIError):
    """Input validation error"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=error_details if error_details else None
        )


class WorkflowExecutionError(APIError):
    """Workflow execution failed"""

    def __init__(
        self,
        workflow_id: str,
        message: str,
        step: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        error_details = {"workflow_id": workflow_id, **(details or {})}
        if step:
            error_details["failed_step"] = step
        super().__init__(
            message=f"Workflow execution failed: {message}",
            status_code=500,
            error_code="WORKFLOW_EXECUTION_ERROR",
            details=error_details
        )


class AgentExecutionError(APIError):
    """Agent execution failed"""

    def __init__(
        self,
        agent_id: str,
        message: str,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"Agent execution failed: {message}",
            status_code=500,
            error_code="AGENT_EXECUTION_ERROR",
            details={"agent_id": agent_id, **(details or {})}
        )


class IntegrationError(APIError):
    """External integration error"""

    def __init__(
        self,
        integration_id: str,
        message: str,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=f"Integration error ({integration_id}): {message}",
            status_code=502,
            error_code="INTEGRATION_ERROR",
            details={"integration_id": integration_id, **(details or {})}
        )


class ConfigurationError(APIError):
    """Configuration or setup error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class ServiceUnavailableError(APIError):
    """Service temporarily unavailable"""

    def __init__(self, service: str, message: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message or f"Service '{service}' is temporarily unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service, **(details or {})}
        )


class RateLimitError(APIError):
    """Rate limit exceeded"""

    def __init__(self, limit: int, window_seconds: int, details: Optional[Dict] = None):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds} seconds",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window_seconds": window_seconds, **(details or {})}
        )


# =============================================================================
# Exception Handler for FastAPI
# =============================================================================

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    FastAPI exception handler for APIError and subclasses.

    Register with:
        app.add_exception_handler(APIError, api_error_handler)
    """
    request_id = getattr(request.state, "request_id", None)

    # Log the error
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )

    return exc.to_response(request_id=request_id)


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Register with:
        app.add_exception_handler(Exception, generic_error_handler)
    """
    request_id = getattr(request.state, "request_id", None)

    # Log the full traceback for debugging
    logger.exception(
        f"Unexpected error: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__} if logger.level <= logging.DEBUG else None,
        request_id=request_id
    )


# =============================================================================
# Helper Functions
# =============================================================================

def raise_not_found(resource_type: str, resource_id: str):
    """Convenience function to raise NotFoundError"""
    raise NotFoundError(resource_type, resource_id)


def raise_validation_error(message: str, field: Optional[str] = None):
    """Convenience function to raise ValidationError"""
    raise ValidationError(message, field)


def safe_execute(func, error_message: str = "Operation failed", **error_kwargs):
    """
    Decorator to wrap functions with standardized error handling.

    Usage:
        @safe_execute
        def my_function():
            ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.exception(f"{error_message}: {str(e)}")
            raise APIError(
                message=error_message,
                details={"original_error": str(e), **error_kwargs}
            )
    return wrapper
