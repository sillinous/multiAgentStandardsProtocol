"""
A2A (Agent-to-Agent) Protocol Implementation

Standards-compliant protocol for agent-to-agent communication enabling:
- Agent discovery and registration
- Message routing and delivery
- Request-response patterns
- Event broadcasting
- Capability negotiation
"""

from .protocol import (
    A2AMessage,
    A2AEnvelope,
    MessageType,
    AgentInfo,
    Capability
)
from .bus import A2AMessageBus

__all__ = [
    'A2AMessage',
    'A2AEnvelope',
    'MessageType',
    'AgentInfo',
    'Capability',
    'A2AMessageBus'
]
