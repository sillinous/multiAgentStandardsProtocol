"""
Security Module for SuperStandard API

Provides authentication, authorization, rate limiting, and security middleware.

Features:
- API Key authentication
- Rate limiting per endpoint
- CORS configuration
- Input sanitization
- Security headers
"""

import os
import hashlib
import time
from typing import Optional, Dict, List, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import Security, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Constants
# ============================================================================

# Load from environment or use secure defaults
API_KEY_HEADER_NAME = "X-API-Key"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")  # Must be set in production
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY", "")  # Must be set in production

# Rate limiting defaults
DEFAULT_RATE_LIMIT = 100  # requests per window
DEFAULT_RATE_WINDOW = 60  # seconds
RATE_LIMIT_EXCEEDED_MESSAGE = "Rate limit exceeded. Please try again later."

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

# ============================================================================
# API Key Authentication
# ============================================================================

api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


class AuthLevel:
    """Authentication levels"""
    PUBLIC = "public"  # No auth required
    CLIENT = "client"  # Requires client API key
    ADMIN = "admin"  # Requires admin API key


def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
    required_level: str = AuthLevel.CLIENT
) -> str:
    """
    Verify API key and return the authentication level.

    Args:
        api_key: API key from header
        required_level: Minimum required authentication level

    Returns:
        Authentication level (client or admin)

    Raises:
        HTTPException: If authentication fails
    """
    # Public endpoints don't require authentication
    if required_level == AuthLevel.PUBLIC:
        return AuthLevel.PUBLIC

    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide it in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Verify admin key
    if api_key == ADMIN_API_KEY and ADMIN_API_KEY:
        return AuthLevel.ADMIN

    # Verify client key
    if api_key == CLIENT_API_KEY and CLIENT_API_KEY:
        if required_level == AuthLevel.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this operation"
            )
        return AuthLevel.CLIENT

    # Invalid key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"}
    )


def require_auth(level: str = AuthLevel.CLIENT):
    """
    Decorator to require authentication for endpoints.

    Usage:
        @app.get("/protected")
        @require_auth(level=AuthLevel.CLIENT)
        async def protected_endpoint():
            return {"message": "Access granted"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from kwargs (injected by FastAPI)
            api_key = kwargs.get('api_key') or kwargs.get('auth_level')
            verify_api_key(api_key, level)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter.

    Tracks requests per client (by IP or API key) and enforces limits.
    """

    def __init__(self):
        # Storage: {client_id: {"tokens": int, "last_update": float}}
        self.clients: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": DEFAULT_RATE_LIMIT,
            "last_update": time.time()
        })
        self.limits: Dict[str, int] = {}  # Custom limits per endpoint

    def set_limit(self, endpoint: str, limit: int, window: int = DEFAULT_RATE_WINDOW):
        """Set custom rate limit for an endpoint."""
        self.limits[endpoint] = {"limit": limit, "window": window}

    def _get_client_id(self, request: Request, api_key: Optional[str] = None) -> str:
        """Generate client identifier from request."""
        if api_key:
            return f"key_{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        return f"ip_{request.client.host}" if request.client else "unknown"

    def _refill_tokens(self, client_data: Dict, limit: int, window: int):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - client_data["last_update"]

        # Refill rate: limit tokens per window
        refill_rate = limit / window
        tokens_to_add = elapsed * refill_rate

        client_data["tokens"] = min(limit, client_data["tokens"] + tokens_to_add)
        client_data["last_update"] = now

    def check_rate_limit(
        self,
        request: Request,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> bool:
        """
        Check if request should be rate limited.

        Returns:
            True if request is allowed, False if rate limited
        """
        client_id = self._get_client_id(request, api_key)

        # Get limit for this endpoint
        if endpoint and endpoint in self.limits:
            limit_config = self.limits[endpoint]
            limit = limit_config["limit"]
            window = limit_config["window"]
        else:
            limit = DEFAULT_RATE_LIMIT
            window = DEFAULT_RATE_WINDOW

        client_data = self.clients[client_id]
        self._refill_tokens(client_data, limit, window)

        # Check if client has tokens available
        if client_data["tokens"] >= 1:
            client_data["tokens"] -= 1
            return True

        return False

    async def __call__(self, request: Request, api_key: Optional[str] = None):
        """Middleware function to check rate limits."""
        endpoint = request.url.path

        if not self.check_rate_limit(request, api_key, endpoint):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=RATE_LIMIT_EXCEEDED_MESSAGE,
                headers={
                    "Retry-After": str(DEFAULT_RATE_WINDOW),
                    "X-RateLimit-Limit": str(DEFAULT_RATE_LIMIT),
                    "X-RateLimit-Remaining": "0"
                }
            )


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# CORS Configuration
# ============================================================================

def configure_cors(app):
    """
    Configure CORS middleware with secure defaults.

    In production, ALLOWED_ORIGINS should be set via environment variable.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]
    )
    logger.info(f"CORS configured with allowed origins: {ALLOWED_ORIGINS}")


# ============================================================================
# Security Headers Middleware
# ============================================================================

async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


# ============================================================================
# WebSocket Authentication
# ============================================================================

def verify_websocket_token(token: Optional[str]) -> bool:
    """
    Verify WebSocket connection token.

    Args:
        token: Authentication token from query parameter

    Returns:
        True if token is valid, False otherwise
    """
    if not token:
        return False

    # Check against valid API keys
    return token == ADMIN_API_KEY or token == CLIENT_API_KEY


# ============================================================================
# Input Sanitization
# ============================================================================

def sanitize_string_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Trim to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip leading/trailing whitespace
    value = value.strip()

    return value


def validate_agent_id(agent_id: str) -> str:
    """
    Validate agent ID format.

    Agent IDs must be alphanumeric with underscores, dashes, max 128 chars.
    """
    if not agent_id or len(agent_id) > 128:
        raise ValueError("Agent ID must be 1-128 characters")

    if not all(c.isalnum() or c in '-_' for c in agent_id):
        raise ValueError("Agent ID must be alphanumeric with dashes/underscores only")

    return agent_id


# ============================================================================
# Security Utilities
# ============================================================================

def generate_api_key() -> str:
    """Generate a secure random API key."""
    import secrets
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# ============================================================================
# Setup Function
# ============================================================================

def setup_security(app):
    """
    Setup all security features for the FastAPI app.

    Call this during app initialization:
        setup_security(app)
    """
    # Check if API keys are configured
    if not ADMIN_API_KEY or not CLIENT_API_KEY:
        logger.warning(
            "⚠️  API keys not configured! Set ADMIN_API_KEY and CLIENT_API_KEY "
            "environment variables for production."
        )
        logger.warning(f"    Example: export ADMIN_API_KEY={generate_api_key()}")
        logger.warning(f"    Example: export CLIENT_API_KEY={generate_api_key()}")

    # Configure CORS
    configure_cors(app)

    # Add security headers middleware
    app.middleware("http")(add_security_headers)

    logger.info("✓ Security configured successfully")


# ============================================================================
# Export Public API
# ============================================================================

__all__ = [
    "AuthLevel",
    "verify_api_key",
    "require_auth",
    "rate_limiter",
    "RateLimiter",
    "setup_security",
    "verify_websocket_token",
    "sanitize_string_input",
    "validate_agent_id",
    "generate_api_key",
]
