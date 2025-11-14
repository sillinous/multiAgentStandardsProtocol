"""
Protocols Module - Standard protocols for multi-agent ecosystems

This module provides standardized protocols for agent coordination,
discovery, and interaction in the Agentic Standards Protocol platform.

Available Protocols:
- Agent Discovery Protocol (ADP): Dynamic agent discovery by capability
- More protocols coming soon...

Usage:
    from src.superstandard.protocols.discovery import get_discovery_service

    discovery = get_discovery_service()
    await discovery.start()
"""

from .discovery import (
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    RegisteredAgent,
    AgentDiscoveryService,
    get_discovery_service
)

__all__ = [
    'AgentStatus',
    'AgentCapability',
    'AgentMetadata',
    'RegisteredAgent',
    'AgentDiscoveryService',
    'get_discovery_service'
]
