"""
Protocol Support for BaseAgent - Minimal Implementation

This module provides the protocol classes needed by BaseAgent.
Imports from main protocol implementations where available, provides
minimal implementations where needed.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import from main protocols where available
try:
    from superstandard.protocols.anp_implementation import (
        AgentStatus,
        ANPRegistration,
    )
except ImportError:
    # Fallback if protocols not available
    class AgentStatus(Enum):
        """Agent health status"""

        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
        OFFLINE = "offline"
        UNKNOWN = "unknown"

    @dataclass
    class ANPRegistration:
        """Agent Network Protocol registration"""

        protocol: str = "ANP"
        version: str = "1.0.0"
        action: str = "register"
        timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        agent_id: str = ""
        agent_type: str = ""
        capabilities: List[str] = field(default_factory=list)
        endpoints: Dict[str, str] = field(default_factory=dict)
        health_status: str = "healthy"
        metadata: Dict[str, Any] = field(default_factory=dict)


# Minimal A2A Message implementation
@dataclass
class A2AMessage:
    """Agent-to-Agent message"""

    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")


# Protocol message types
class MessageType(Enum):
    """Protocol message types"""

    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"


# Minimal ProtocolMixin implementation
class ProtocolMixin:
    """
    Mixin providing protocol support to agents.

    This is a minimal implementation that provides basic protocol
    functionality. Agents can override these methods for full protocol support.
    """

    def __init__(self):
        """Initialize protocol support."""
        self._protocol_version = "1.0.0"
        self._registered = False
        self._message_handlers: Dict[str, Any] = {}

    def register_protocol_handler(self, message_type: str, handler: Any) -> None:
        """Register a handler for a specific message type."""
        self._message_handlers[message_type] = handler

    async def send_protocol_message(
        self, recipient: str, message_type: str, content: Dict[str, Any]
    ) -> A2AMessage:
        """
        Send a protocol-compliant message.

        Args:
            recipient: Agent ID of recipient
            message_type: Type of message
            content: Message content

        Returns:
            The sent message
        """
        message = A2AMessage(
            from_agent=getattr(self, "agent_id", "unknown"),
            to_agent=recipient,
            message_type=message_type,
            content=content,
        )
        # TODO: Integrate with actual message bus
        return message

    async def handle_protocol_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming protocol message.

        Args:
            message: The message to handle

        Returns:
            Optional response
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            return await handler(message)
        return None

    def get_protocol_info(self) -> Dict[str, Any]:
        """Get protocol information for this agent."""
        return {
            "protocol_version": self._protocol_version,
            "supported_protocols": ["A2A", "ANP", "ACP"],
            "registered": self._registered,
        }


# Export all needed classes
__all__ = [
    "ProtocolMixin",
    "A2AMessage",
    "ANPRegistration",
    "AgentStatus",
    "MessageType",
]
