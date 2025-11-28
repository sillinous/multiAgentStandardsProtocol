"""
Logging Configuration for Agent Platform API
=============================================

Provides structured logging with optional JSON output for production environments.

Usage:
    from api_server.logging_config import setup_logging, get_logger

    # Setup logging (call once at startup)
    setup_logging()

    # Get a logger for your module
    logger = get_logger(__name__)

    # Log with context
    logger.info("Processing workflow", extra={"workflow_id": "123", "step": 1})
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from functools import lru_cache

from api_server.config import settings


# =============================================================================
# Custom Formatters
# =============================================================================

class StandardFormatter(logging.Formatter):
    """Standard text formatter with colors for console output"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        # Add timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Get level with optional color
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level:8}{self.RESET}"
        else:
            level = f"{level:8}"

        # Format the message
        message = record.getMessage()

        # Build the log line
        log_line = f"{timestamp} | {level} | {record.name} | {message}"

        # Add extra context if present
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and k not in ('message', 'asctime')
        }

        if extra_fields:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra_fields.items())
            log_line += f" | {extra_str}"

        # Add exception info if present
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (production/log aggregation)"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra context fields
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and k not in ('message', 'asctime')
        }

        if extra_fields:
            log_data["context"] = extra_fields

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_data)


# =============================================================================
# Logger Setup
# =============================================================================

def setup_logging(
    level: Optional[str] = None,
    json_output: Optional[bool] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, use JSON formatting
        log_format: Custom log format string (ignored if json_output=True)
    """
    # Use settings defaults if not specified
    level = level or settings.LOG_LEVEL
    json_output = json_output if json_output is not None else settings.LOG_JSON

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Set formatter based on output type
    if json_output:
        formatter = JSONFormatter()
    else:
        # Use colors if outputting to a terminal
        use_colors = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        formatter = StandardFormatter(use_colors=use_colors)

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )

    # Log startup message
    root_logger.info(
        f"Logging configured",
        extra={"level": level, "json_output": json_output}
    )


@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# =============================================================================
# Context-Aware Logger
# =============================================================================

class ContextLogger:
    """
    Logger wrapper that maintains context across log calls.

    Usage:
        logger = ContextLogger(__name__, workflow_id="abc123")
        logger.info("Starting step 1")  # Includes workflow_id automatically
        logger.info("Step complete", extra={"duration_ms": 150})
    """

    def __init__(self, name: str, **context):
        self._logger = logging.getLogger(name)
        self._context = context

    def _log(self, level: int, message: str, extra: Optional[Dict] = None, **kwargs):
        """Log with merged context"""
        merged_extra = {**self._context, **(extra or {})}
        self._logger.log(level, message, extra=merged_extra, **kwargs)

    def debug(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.DEBUG, message, extra, **kwargs)

    def info(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.INFO, message, extra, **kwargs)

    def warning(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.WARNING, message, extra, **kwargs)

    def error(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.ERROR, message, extra, **kwargs)

    def critical(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.CRITICAL, message, extra, **kwargs)

    def exception(self, message: str, extra: Optional[Dict] = None, **kwargs):
        self._log(logging.ERROR, message, extra, exc_info=True, **kwargs)

    def with_context(self, **additional_context) -> "ContextLogger":
        """Create a new logger with additional context"""
        return ContextLogger(
            self._logger.name,
            **{**self._context, **additional_context}
        )


# =============================================================================
# Request Logging Middleware
# =============================================================================

class RequestLoggingMiddleware:
    """
    FastAPI middleware for logging requests and responses.

    Usage:
        from api_server.logging_config import RequestLoggingMiddleware

        app.add_middleware(RequestLoggingMiddleware)
    """

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api_server.requests")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time
        from uuid import uuid4

        # Generate request ID
        request_id = str(uuid4())[:8]
        start_time = time.time()

        # Extract request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"").decode()

        # Log request start
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query_string[:100] if query_string else None,
            }
        )

        # Track response status
        response_status = [0]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message.get("status", 0)
            await send(message)

        try:
            # Add request_id to scope for access in handlers
            scope["state"] = scope.get("state", {})
            scope["state"]["request_id"] = request_id

            await self.app(scope, receive, send_wrapper)
        finally:
            # Log request completion
            duration_ms = (time.time() - start_time) * 1000
            status = response_status[0]

            log_level = logging.INFO
            if status >= 500:
                log_level = logging.ERROR
            elif status >= 400:
                log_level = logging.WARNING

            self.logger.log(
                log_level,
                f"Request completed: {method} {path} -> {status}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status": status,
                    "duration_ms": round(duration_ms, 2),
                }
            )


# =============================================================================
# Performance Logging Helpers
# =============================================================================

class Timer:
    """
    Context manager for timing code blocks.

    Usage:
        with Timer("database_query", logger) as timer:
            result = db.query(...)
        # Logs: "database_query completed in 15.2ms"
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.start_time = None
        self.duration_ms = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            self.logger.error(
                f"{self.name} failed after {self.duration_ms:.2f}ms",
                extra={"operation": self.name, "duration_ms": self.duration_ms}
            )
        else:
            self.logger.log(
                self.level,
                f"{self.name} completed in {self.duration_ms:.2f}ms",
                extra={"operation": self.name, "duration_ms": self.duration_ms}
            )

        return False  # Don't suppress exceptions
