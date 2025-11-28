"""
Configuration Management for Agent Platform API
================================================

Centralized configuration using environment variables with sensible defaults.

Usage:
    from api_server.config import settings

    # Access settings
    db_url = settings.DATABASE_URL
    debug = settings.DEBUG
    log_level = settings.LOG_LEVEL

Environment Variables:
    DATABASE_URL: Database connection string (default: sqlite:///./agents.db)
    DEBUG: Enable debug mode (default: false)
    LOG_LEVEL: Logging level (default: INFO)
    API_HOST: API server host (default: 0.0.0.0)
    API_PORT: API server port (default: 8000)
    CORS_ORIGINS: Comma-separated CORS origins (default: *)
    API_KEY_ENABLED: Enable API key authentication (default: false)
    MAX_WORKFLOW_TIMEOUT: Max workflow execution time in seconds (default: 300)
"""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from functools import lru_cache


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_list(key: str, default: str = "") -> List[str]:
    """Get list from comma-separated environment variable"""
    value = os.getenv(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    """Application settings loaded from environment variables"""

    # ==========================================================================
    # Paths
    # ==========================================================================
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    AGENT_CARDS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "agent_cards")
    BPMN_L2_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "generated_composite_agents" / "level2_bpmn")
    BPMN_L3_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "generated_composite_agents" / "level3_bpmn")
    APQC_HIERARCHY_PATH: Path = field(default_factory=lambda: Path(__file__).parent.parent / "apqc_pcf_hierarchy.json")
    SRC_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "src")

    # ==========================================================================
    # Database
    # ==========================================================================
    DATABASE_URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./agents.db"))
    DATABASE_ECHO: bool = field(default_factory=lambda: get_env_bool("DATABASE_ECHO", False))
    DATABASE_POOL_SIZE: int = field(default_factory=lambda: get_env_int("DATABASE_POOL_SIZE", 5))

    # ==========================================================================
    # Server
    # ==========================================================================
    API_HOST: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    API_PORT: int = field(default_factory=lambda: get_env_int("API_PORT", 8000))
    DEBUG: bool = field(default_factory=lambda: get_env_bool("DEBUG", False))
    RELOAD: bool = field(default_factory=lambda: get_env_bool("RELOAD", False))
    WORKERS: int = field(default_factory=lambda: get_env_int("WORKERS", 1))

    # ==========================================================================
    # Security
    # ==========================================================================
    API_KEY_ENABLED: bool = field(default_factory=lambda: get_env_bool("API_KEY_ENABLED", False))
    API_KEY_HEADER: str = field(default_factory=lambda: os.getenv("API_KEY_HEADER", "X-API-Key"))
    CORS_ORIGINS: List[str] = field(default_factory=lambda: get_env_list("CORS_ORIGINS", "*"))
    CORS_ALLOW_CREDENTIALS: bool = field(default_factory=lambda: get_env_bool("CORS_ALLOW_CREDENTIALS", True))

    # ==========================================================================
    # Logging
    # ==========================================================================
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    LOG_FORMAT: str = field(default_factory=lambda: os.getenv(
        "LOG_FORMAT",
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    ))
    LOG_JSON: bool = field(default_factory=lambda: get_env_bool("LOG_JSON", False))

    # ==========================================================================
    # Workflow Execution
    # ==========================================================================
    MAX_WORKFLOW_TIMEOUT: int = field(default_factory=lambda: get_env_int("MAX_WORKFLOW_TIMEOUT", 300))
    MAX_STEP_RETRIES: int = field(default_factory=lambda: get_env_int("MAX_STEP_RETRIES", 3))
    STEP_RETRY_DELAY: int = field(default_factory=lambda: get_env_int("STEP_RETRY_DELAY", 5))
    WORKFLOW_CONCURRENT_LIMIT: int = field(default_factory=lambda: get_env_int("WORKFLOW_CONCURRENT_LIMIT", 10))

    # ==========================================================================
    # Agent Execution
    # ==========================================================================
    AGENT_TIMEOUT: int = field(default_factory=lambda: get_env_int("AGENT_TIMEOUT", 60))
    AGENT_MAX_MEMORY_MB: int = field(default_factory=lambda: get_env_int("AGENT_MAX_MEMORY_MB", 512))

    # ==========================================================================
    # Integration
    # ==========================================================================
    INTEGRATION_TIMEOUT: int = field(default_factory=lambda: get_env_int("INTEGRATION_TIMEOUT", 30))
    INTEGRATION_MAX_RETRIES: int = field(default_factory=lambda: get_env_int("INTEGRATION_MAX_RETRIES", 3))

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    ENABLE_METRICS: bool = field(default_factory=lambda: get_env_bool("ENABLE_METRICS", True))
    ENABLE_TRACING: bool = field(default_factory=lambda: get_env_bool("ENABLE_TRACING", False))
    ENABLE_ADMIN_ENDPOINTS: bool = field(default_factory=lambda: get_env_bool("ENABLE_ADMIN_ENDPOINTS", True))

    def __post_init__(self):
        """Validate settings after initialization"""
        # Ensure directories exist (create if needed for data dirs)
        self.AGENT_CARDS_DIR.mkdir(parents=True, exist_ok=True)

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_levels:
            self.LOG_LEVEL = "INFO"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database"""
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def database_connect_args(self) -> dict:
        """Get database connection arguments"""
        if self.is_sqlite:
            return {"check_same_thread": False}
        return {}

    def to_dict(self) -> dict:
        """Convert settings to dictionary (for logging/debugging)"""
        return {
            "DATABASE_URL": self.DATABASE_URL.split("@")[-1] if "@" in self.DATABASE_URL else self.DATABASE_URL,
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
            "API_HOST": self.API_HOST,
            "API_PORT": self.API_PORT,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            "MAX_WORKFLOW_TIMEOUT": self.MAX_WORKFLOW_TIMEOUT,
            "ENABLE_METRICS": self.ENABLE_METRICS,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()


# =============================================================================
# Environment file loading (optional)
# =============================================================================

def load_env_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from .env file if it exists.

    Args:
        env_path: Path to .env file. If None, looks for .env in BASE_DIR.

    Returns:
        True if file was loaded, False otherwise.
    """
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        return False

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value
        return True
    except Exception:
        return False


# Try to load .env file on module import
load_env_file()
