"""
A2A Protocol Specification

Standards-compliant Agent-to-Agent communication protocol.
Based on emerging A2A standards for autonomous agent systems.
"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum


class MessageType(Enum):
    """A2A Message Types"""

    # Task management
    TASK_ASSIGNMENT = "task_assignment"
    TASK_ACCEPTED = "task_accepted"
    TASK_REJECTED = "task_rejected"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Information exchange
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"

    # Coordination
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    NEGOTIATION = "negotiation"
    AGREEMENT = "agreement"

    # Status
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"

    # Discovery
    AGENT_REGISTER = "agent_register"
    AGENT_DEREGISTER = "agent_deregister"
    AGENT_QUERY = "agent_query"


class Priority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Capability:
    """Represents an agent capability"""

    name: str
    version: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class AgentInfo:
    """Agent information for discovery and routing"""

    agent_id: str
    agent_type: str
    name: str
    capabilities: List[Capability] = field(default_factory=list)
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "endpoint": self.endpoint,
            "metadata": self.metadata
        }


@dataclass
class A2AMessage:
    """
    A2A Protocol Message Payload

    The core message content conforming to A2A standards.
    """

    message_type: MessageType
    sender: AgentInfo
    content: Dict[str, Any] = field(default_factory=dict)

    # Optional fields
    receiver: Optional[AgentInfo] = None
    reply_to: Optional[str] = None  # Message ID this is replying to

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_type": self.message_type.value,
            "sender": self.sender.to_dict(),
            "receiver": self.receiver.to_dict() if self.receiver else None,
            "content": self.content,
            "reply_to": self.reply_to
        }


@dataclass
class A2AEnvelope:
    """
    A2A Protocol Envelope

    Wraps the message with routing and metadata information.
    Standards-compliant envelope for A2A messages.
    """

    # Required fields
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    protocol_version: str = "1.0"

    # Message payload
    message: Optional[A2AMessage] = None

    # Routing
    from_agent: Optional[str] = None
    to_agent: Optional[str] = None

    # Priority and TTL
    priority: Priority = Priority.NORMAL
    ttl_seconds: int = 300  # 5 minutes default

    # Metadata
    correlation_id: Optional[str] = None  # For request-response tracking
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "protocol_version": self.protocol_version,
            "message": self.message.to_dict() if self.message else None,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "priority": self.priority.value,
            "ttl_seconds": self.ttl_seconds,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AEnvelope':
        """Create from dictionary"""
        envelope = cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            protocol_version=data.get("protocol_version", "1.0"),
            from_agent=data.get("from_agent"),
            to_agent=data.get("to_agent"),
            priority=Priority(data.get("priority", Priority.NORMAL.value)),
            ttl_seconds=data.get("ttl_seconds", 300),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )

        # Parse message if present
        if "message" in data and data["message"]:
            msg_data = data["message"]

            # Parse sender
            sender_data = msg_data["sender"]
            sender = AgentInfo(
                agent_id=sender_data["agent_id"],
                agent_type=sender_data["agent_type"],
                name=sender_data["name"],
                capabilities=[
                    Capability(**c) for c in sender_data.get("capabilities", [])
                ],
                endpoint=sender_data.get("endpoint"),
                metadata=sender_data.get("metadata", {})
            )

            # Parse receiver if present
            receiver = None
            if msg_data.get("receiver"):
                recv_data = msg_data["receiver"]
                receiver = AgentInfo(
                    agent_id=recv_data["agent_id"],
                    agent_type=recv_data["agent_type"],
                    name=recv_data["name"],
                    capabilities=[
                        Capability(**c) for c in recv_data.get("capabilities", [])
                    ],
                    endpoint=recv_data.get("endpoint"),
                    metadata=recv_data.get("metadata", {})
                )

            envelope.message = A2AMessage(
                message_type=MessageType(msg_data["message_type"]),
                sender=sender,
                receiver=receiver,
                content=msg_data.get("content", {}),
                reply_to=msg_data.get("reply_to")
            )

        return envelope

    def is_expired(self) -> bool:
        """Check if message has exceeded TTL"""
        msg_time = datetime.fromisoformat(self.timestamp)
        expiry = msg_time + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry

    def create_reply(
        self,
        message_type: MessageType,
        sender: AgentInfo,
        content: Dict[str, Any]
    ) -> 'A2AEnvelope':
        """Create a reply envelope to this message"""
        reply = A2AEnvelope(
            from_agent=sender.agent_id,
            to_agent=self.from_agent,
            correlation_id=self.correlation_id or self.message_id,
            priority=self.priority
        )

        reply.message = A2AMessage(
            message_type=message_type,
            sender=sender,
            receiver=self.message.sender if self.message else None,
            content=content,
            reply_to=self.message_id
        )

        return reply


# Helper functions for creating common message types

def create_task_assignment(
    sender: AgentInfo,
    receiver: AgentInfo,
    task_id: str,
    task_type: str,
    parameters: Dict[str, Any],
    priority: Priority = Priority.NORMAL
) -> A2AEnvelope:
    """Create a task assignment message"""
    envelope = A2AEnvelope(
        from_agent=sender.agent_id,
        to_agent=receiver.agent_id,
        priority=priority
    )

    envelope.message = A2AMessage(
        message_type=MessageType.TASK_ASSIGNMENT,
        sender=sender,
        receiver=receiver,
        content={
            "task_id": task_id,
            "task_type": task_type,
            "parameters": parameters
        }
    )

    return envelope


def create_task_completed(
    sender: AgentInfo,
    task_id: str,
    result: Dict[str, Any],
    reply_to: Optional[str] = None
) -> A2AEnvelope:
    """Create a task completed message"""
    envelope = A2AEnvelope(
        from_agent=sender.agent_id
    )

    envelope.message = A2AMessage(
        message_type=MessageType.TASK_COMPLETED,
        sender=sender,
        content={
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        },
        reply_to=reply_to
    )

    return envelope


def create_capability_query(sender: AgentInfo) -> A2AEnvelope:
    """Create a capability query message (broadcast)"""
    envelope = A2AEnvelope(
        from_agent=sender.agent_id,
        to_agent="*"  # Broadcast
    )

    envelope.message = A2AMessage(
        message_type=MessageType.CAPABILITY_QUERY,
        sender=sender,
        content={}
    )

    return envelope


def create_status_update(
    sender: AgentInfo,
    status: str,
    details: Dict[str, Any]
) -> A2AEnvelope:
    """Create a status update message"""
    envelope = A2AEnvelope(
        from_agent=sender.agent_id
    )

    envelope.message = A2AMessage(
        message_type=MessageType.STATUS_UPDATE,
        sender=sender,
        content={
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    return envelope
