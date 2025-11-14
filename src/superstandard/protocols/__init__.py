"""
Protocols Module - Standard protocols for multi-agent ecosystems

This module provides standardized protocols for agent coordination,
discovery, and interaction in the Agentic Standards Protocol platform.

Available Protocols:
- Agent Discovery Protocol (ADP): Dynamic agent discovery by capability
- Agent Reputation Protocol (ARP): Performance tracking and reputation scoring

Usage:
    from src.superstandard.protocols.discovery import get_discovery_service
    from src.superstandard.protocols.reputation import get_reputation_service

    discovery = get_discovery_service()
    reputation = get_reputation_service()

    await discovery.start()
    await reputation.start()
"""

from .discovery import (
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    RegisteredAgent,
    AgentDiscoveryService,
    get_discovery_service
)

from .reputation import (
    ReputationDimension,
    TaskOutcome,
    DimensionScore,
    AgentReputation,
    ReputationService,
    get_reputation_service
)

__all__ = [
    # Discovery
    'AgentStatus',
    'AgentCapability',
    'AgentMetadata',
    'RegisteredAgent',
    'AgentDiscoveryService',
    'get_discovery_service',
    # Reputation
    'ReputationDimension',
    'TaskOutcome',
    'DimensionScore',
    'AgentReputation',
    'ReputationService',
    'get_reputation_service'
]
