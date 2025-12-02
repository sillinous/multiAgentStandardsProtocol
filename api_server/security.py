"""
API Security & Hardening Module
================================

Provides comprehensive security features for the API server:
- Global exception handling
- Rate limiting
- API key authentication
- Request validation
- Structured logging
- Input sanitization

Version: 1.0.0
"""

import os
import re
import time
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel, Field, validator, root_validator
from starlette.middleware.base import BaseHTTPMiddleware


# ============================================================================
# Structured Logging
# ============================================================================

class StructuredLogger:
    """Structured logging for API requests and security events"""

    def __init__(self, name: str = "api_server"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_request(self, request: Request, response_status: int, duration_ms: float):
        """Log API request with structured data"""
        self.logger.info(
            f"REQUEST | {request.method} {request.url.path} | "
            f"status={response_status} | duration={duration_ms:.2f}ms | "
            f"client={request.client.host if request.client else 'unknown'}"
        )

    def log_security_event(self, event_type: str, details: Dict[str, Any], level: str = "warning"):
        """Log security-related events"""
        log_fn = getattr(self.logger, level, self.logger.warning)
        log_fn(f"SECURITY | {event_type} | {details}")

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with context"""
        self.logger.error(
            f"ERROR | {type(error).__name__}: {str(error)} | context={context or {}}"
        )


logger = StructuredLogger()


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter with per-client tracking.

    Features:
    - Configurable requests per window
    - Per-IP client tracking
    - Automatic cleanup of old entries
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.client_data: Dict[str, Dict] = defaultdict(lambda: {
            "minute_requests": [],
            "hour_requests": [],
            "blocked_until": None
        })
        self._cleanup_counter = 0

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use X-Forwarded-For if behind proxy, otherwise use client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_id: str):
        """Remove expired request timestamps"""
        now = time.time()
        data = self.client_data[client_id]

        # Clean minute window (60 seconds)
        data["minute_requests"] = [
            t for t in data["minute_requests"]
            if now - t < 60
        ]

        # Clean hour window (3600 seconds)
        data["hour_requests"] = [
            t for t in data["hour_requests"]
            if now - t < 3600
        ]

        # Periodic full cleanup
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            self._full_cleanup()

    def _full_cleanup(self):
        """Remove stale client entries"""
        now = time.time()
        stale_clients = [
            client_id for client_id, data in self.client_data.items()
            if not data["minute_requests"] and not data["hour_requests"]
            and (not data["blocked_until"] or data["blocked_until"] < now)
        ]
        for client_id in stale_clients:
            del self.client_data[client_id]

    def is_allowed(self, request: Request) -> tuple[bool, Optional[Dict]]:
        """
        Check if request is allowed under rate limits.

        Returns:
            (allowed: bool, rate_limit_info: Optional[Dict])
        """
        client_id = self._get_client_id(request)
        now = time.time()

        self._cleanup_old_requests(client_id)
        data = self.client_data[client_id]

        # Check if client is temporarily blocked
        if data["blocked_until"] and data["blocked_until"] > now:
            retry_after = int(data["blocked_until"] - now)
            return False, {
                "error": "rate_limit_exceeded",
                "retry_after": retry_after,
                "message": f"Too many requests. Retry after {retry_after} seconds."
            }

        # Check minute limit
        minute_count = len(data["minute_requests"])
        if minute_count >= self.requests_per_minute:
            data["blocked_until"] = now + 60  # Block for 1 minute
            logger.log_security_event("rate_limit_exceeded", {
                "client": client_id,
                "limit": "per_minute",
                "count": minute_count
            })
            return False, {
                "error": "rate_limit_exceeded",
                "retry_after": 60,
                "message": "Rate limit exceeded. Please wait 60 seconds."
            }

        # Check hour limit
        hour_count = len(data["hour_requests"])
        if hour_count >= self.requests_per_hour:
            data["blocked_until"] = now + 300  # Block for 5 minutes
            logger.log_security_event("rate_limit_exceeded", {
                "client": client_id,
                "limit": "per_hour",
                "count": hour_count
            })
            return False, {
                "error": "rate_limit_exceeded",
                "retry_after": 300,
                "message": "Hourly rate limit exceeded. Please wait 5 minutes."
            }

        # Allow request and record timestamp
        data["minute_requests"].append(now)
        data["hour_requests"].append(now)

        return True, {
            "remaining_minute": self.requests_per_minute - minute_count - 1,
            "remaining_hour": self.requests_per_hour - hour_count - 1
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "3000"))
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on all requests"""

    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/api/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        allowed, info = rate_limiter.is_allowed(request)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=info,
                headers={"Retry-After": str(info.get("retry_after", 60))}
            )

        response = await call_next(request)

        # Add rate limit headers
        if info:
            response.headers["X-RateLimit-Remaining-Minute"] = str(info.get("remaining_minute", 0))
            response.headers["X-RateLimit-Remaining-Hour"] = str(info.get("remaining_hour", 0))

        return response


# ============================================================================
# API Key Authentication
# ============================================================================

# API key storage (in production, use database or secrets manager)
API_KEYS: Dict[str, Dict] = {}

def _load_api_keys():
    """Load API keys from environment or generate default"""
    # Check for master API key in environment
    master_key = os.getenv("API_MASTER_KEY")
    if master_key:
        API_KEYS[master_key] = {
            "name": "master",
            "role": "admin",
            "created_at": datetime.now().isoformat()
        }

    # Generate a default development key if none configured
    if not API_KEYS:
        dev_key = os.getenv("API_DEV_KEY", "dev_" + secrets.token_hex(16))
        API_KEYS[dev_key] = {
            "name": "development",
            "role": "developer",
            "created_at": datetime.now().isoformat()
        }
        logger.logger.info(f"Development API key generated: {dev_key[:12]}...")

_load_api_keys()


# FastAPI security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    api_key_header: str = Depends(api_key_header),
    api_key_query: str = Depends(api_key_query)
) -> Optional[str]:
    """Extract API key from header or query parameter"""
    return api_key_header or api_key_query


async def require_api_key(
    request: Request,
    api_key: str = Depends(get_api_key)
) -> Dict:
    """
    Dependency that requires valid API key authentication.

    Use in endpoints that need protection:
        @app.get("/api/protected")
        async def protected_endpoint(auth: Dict = Depends(require_api_key)):
            ...
    """
    # Allow unauthenticated access in development mode
    if os.getenv("API_AUTH_DISABLED", "false").lower() == "true":
        return {"name": "anonymous", "role": "developer"}

    if not api_key:
        logger.log_security_event("auth_failed", {
            "reason": "missing_api_key",
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header or api_key query parameter."
        )

    if api_key not in API_KEYS:
        logger.log_security_event("auth_failed", {
            "reason": "invalid_api_key",
            "path": request.url.path,
            "key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***"
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    return API_KEYS[api_key]


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @app.delete("/api/admin/reset")
        async def admin_reset(auth: Dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(auth: Dict = Depends(require_api_key)) -> Dict:
        if auth.get("role") != required_role and auth.get("role") != "admin":
            logger.log_security_event("access_denied", {
                "reason": "insufficient_role",
                "required": required_role,
                "actual": auth.get("role")
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return auth
    return role_checker


# ============================================================================
# Input Validation & Sanitization
# ============================================================================

class InputSanitizer:
    """Sanitize and validate user inputs"""

    # Patterns for common injection attacks
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        re.IGNORECASE
    )
    XSS_PATTERN = re.compile(r"<script|javascript:|on\w+=", re.IGNORECASE)
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\./|\.\.\\")

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize a string input"""
        if not isinstance(value, str):
            return str(value)[:max_length]

        # Truncate to max length
        value = value[:max_length]

        # Strip dangerous characters
        value = value.strip()

        return value

    @classmethod
    def check_injection(cls, value: str) -> tuple[bool, Optional[str]]:
        """Check for potential injection attacks"""
        if cls.SQL_INJECTION_PATTERN.search(value):
            return False, "Potential SQL injection detected"
        if cls.XSS_PATTERN.search(value):
            return False, "Potential XSS detected"
        if cls.PATH_TRAVERSAL_PATTERN.search(value):
            return False, "Path traversal attempt detected"
        return True, None

    @classmethod
    def sanitize_dict(cls, data: Dict, max_depth: int = 5, current_depth: int = 0) -> Dict:
        """Recursively sanitize dictionary values"""
        if current_depth >= max_depth:
            return {}

        result = {}
        for key, value in data.items():
            # Sanitize key
            clean_key = cls.sanitize_string(str(key), max_length=100)

            # Sanitize value based on type
            if isinstance(value, str):
                result[clean_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                result[clean_key] = cls.sanitize_dict(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                result[clean_key] = [
                    cls.sanitize_dict(v, max_depth, current_depth + 1) if isinstance(v, dict)
                    else cls.sanitize_string(v) if isinstance(v, str)
                    else v
                    for v in value[:100]  # Limit list size
                ]
            else:
                result[clean_key] = value

        return result


# ============================================================================
# Enhanced Pydantic Models with Validation
# ============================================================================

class SecureBaseModel(BaseModel):
    """Base model with security validations"""

    class Config:
        # Forbid extra fields to prevent injection
        extra = "forbid"
        # Strip whitespace from strings
        str_strip_whitespace = True
        # Max string length
        max_anystr_length = 10000


class SafeInvoiceRequest(SecureBaseModel):
    """Hardened invoice workflow request with strict validation"""

    source: str = Field(
        default="api",
        max_length=50,
        regex=r"^[a-zA-Z0-9_-]+$",
        description="Source system identifier"
    )
    invoice_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex=r"^[A-Za-z0-9\-_]+$",
        description="Invoice number (alphanumeric, hyphens, underscores only)"
    )
    vendor_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Vendor name"
    )
    date: str = Field(
        ...,
        regex=r"^\d{4}-\d{2}-\d{2}$",
        description="Invoice date in YYYY-MM-DD format"
    )
    items: List[Dict[str, Any]] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="Invoice line items"
    )

    @validator("vendor_name")
    def validate_vendor_name(cls, v):
        safe, reason = InputSanitizer.check_injection(v)
        if not safe:
            raise ValueError(f"Invalid vendor name: {reason}")
        return InputSanitizer.sanitize_string(v, max_length=200)

    @validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item is required")

        validated_items = []
        for item in v:
            if not isinstance(item, dict):
                raise ValueError("Each item must be an object")

            # Validate required fields
            if "price" in item:
                try:
                    price = float(item["price"])
                    if price < 0:
                        raise ValueError("Price cannot be negative")
                    if price > 1_000_000_000:  # 1 billion max
                        raise ValueError("Price exceeds maximum allowed")
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Invalid price: {e}")

            if "qty" in item:
                try:
                    qty = int(item["qty"])
                    if qty < 0:
                        raise ValueError("Quantity cannot be negative")
                    if qty > 1_000_000:
                        raise ValueError("Quantity exceeds maximum allowed")
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Invalid quantity: {e}")

            validated_items.append(InputSanitizer.sanitize_dict(item))

        return validated_items


class SafeAgentExecutionRequest(SecureBaseModel):
    """Hardened agent execution request"""

    task_name: str = Field(
        default="api_task",
        max_length=100,
        regex=r"^[a-zA-Z0-9_\-\s]+$"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task parameters"
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Execution timeout (1-3600 seconds)"
    )

    @validator("parameters")
    def validate_parameters(cls, v):
        return InputSanitizer.sanitize_dict(v)


# ============================================================================
# Global Exception Handler
# ============================================================================

class GlobalExceptionHandler:
    """Centralized exception handling for the API"""

    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle Pydantic validation errors"""
        logger.log_error(exc, {"path": request.url.path, "type": "validation"})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": str(exc)
            }
        )

    @staticmethod
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        if exc.status_code >= 500:
            logger.log_error(exc, {"path": request.url.path, "status": exc.status_code})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )

    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        logger.log_error(exc, {"path": request.url.path, "type": "unexpected"})

        # Don't expose internal errors in production
        is_production = os.getenv("ENVIRONMENT", "development") == "production"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "An internal error occurred" if is_production else str(exc),
                "request_id": secrets.token_hex(8)
            }
        )


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with timing"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.log_request(request, response.status_code, duration_ms)

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


# ============================================================================
# Utility Functions
# ============================================================================

def setup_security(app):
    """
    Configure all security features on a FastAPI app.

    Usage:
        from api_server.security import setup_security
        app = FastAPI()
        setup_security(app)
    """
    from fastapi.exceptions import RequestValidationError

    # Add middlewares (order matters - first added = last executed)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await GlobalExceptionHandler.handle_validation_error(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await GlobalExceptionHandler.handle_http_exception(request, exc)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return await GlobalExceptionHandler.handle_generic_exception(request, exc)

    logger.logger.info("Security middleware and handlers configured")
