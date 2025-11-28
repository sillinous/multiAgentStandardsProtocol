"""
Authentication Routes for AOH (Agent Operations Hub)

Provides simple authentication for the Agent Operations Hub interface.
This is a basic implementation for demonstration purposes.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import hashlib

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Simple in-memory session store (use Redis/database in production)
active_sessions: Dict[str, Dict[str, Any]] = {}

# Demo credentials (use secure credential storage in production)
DEMO_CREDENTIALS = {
    "test-principal": {
        "secret_hash": hashlib.sha256(b"test-secret").hexdigest(),
        "name": "Demo User",
        "role": "admin"
    }
}


class LoginRequest(BaseModel):
    """Login request model"""
    principal_id: str
    secret: str

    class Config:
        json_schema_extra = {
            "example": {
                "principal_id": "test-principal",
                "secret": "test-secret"
            }
        }


class LoginResponse(BaseModel):
    """Login response model"""
    success: bool
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    expires_at: Optional[str] = None


def hash_secret(secret: str) -> str:
    """Hash a secret for storage"""
    return hashlib.sha256(secret.encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """Validate a session token"""
    if token in active_sessions:
        session = active_sessions[token]

        # Check if expired
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() < expires_at:
            return session
        else:
            # Remove expired session
            del active_sessions[token]

    return None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate a user with principal ID and secret

    Returns a session token on success.
    """
    principal_id = request.principal_id.strip()
    secret = request.secret

    # Validate credentials
    if principal_id not in DEMO_CREDENTIALS:
        raise HTTPException(
            status_code=401,
            detail="Invalid principal ID or secret"
        )

    stored_creds = DEMO_CREDENTIALS[principal_id]
    secret_hash = hash_secret(secret)

    if secret_hash != stored_creds["secret_hash"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid principal ID or secret"
        )

    # Generate session token
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Store session
    active_sessions[token] = {
        "principal_id": principal_id,
        "name": stored_creds["name"],
        "role": stored_creds["role"],
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat()
    }

    return LoginResponse(
        success=True,
        token=token,
        user={
            "principal_id": principal_id,
            "name": stored_creds["name"],
            "role": stored_creds["role"]
        },
        message="Login successful",
        expires_at=expires_at.isoformat()
    )


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout and invalidate session token
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    # Extract token from "Bearer <token>" format
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # Remove session if it exists
    if token in active_sessions:
        del active_sessions[token]
        return {"success": True, "message": "Logged out successfully"}

    return {"success": False, "message": "Session not found"}


@router.get("/validate")
async def validate_token(authorization: Optional[str] = Header(None)):
    """
    Validate a session token
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    # Extract token
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # Validate session
    session = validate_session(token)

    if session:
        return {
            "success": True,
            "valid": True,
            "user": {
                "principal_id": session["principal_id"],
                "name": session["name"],
                "role": session["role"]
            },
            "expires_at": session["expires_at"]
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/sessions")
async def get_active_sessions():
    """
    Get list of active sessions (admin only in production)
    """
    return {
        "success": True,
        "count": len(active_sessions),
        "sessions": [
            {
                "principal_id": session["principal_id"],
                "name": session["name"],
                "role": session["role"],
                "created_at": session["created_at"],
                "expires_at": session["expires_at"]
            }
            for session in active_sessions.values()
        ]
    }


@router.get("/health")
async def auth_health():
    """
    Health check for authentication service
    """
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }
