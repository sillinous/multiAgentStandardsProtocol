"""
Protocols Module - Standard protocols for multi-agent ecosystems

This module provides standardized protocols for agent coordination,
discovery, and interaction in the Agentic Standards Protocol platform.

Available Protocols:
- Agent Discovery Protocol (ADP): Dynamic agent discovery by capability
- Agent Reputation Protocol (ARP): Performance tracking and reputation scoring
- Agent Contract Protocol (ACP): Formal agreements and SLA enforcement
- Resource Allocation Protocol (RAP): Budget and quota management

Usage:
    from src.superstandard.protocols.discovery import get_discovery_service
    from src.superstandard.protocols.reputation import get_reputation_service
    from src.superstandard.protocols.contracts import get_contract_service
    from src.superstandard.protocols.resources import get_resource_service

    discovery = get_discovery_service()
    reputation = get_reputation_service()
    contracts = get_contract_service()
    resources = get_resource_service()

    await discovery.start()
    await reputation.start()
    await contracts.start()
    await resources.start()
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

from .contracts import (
    ContractStatus,
    BreachSeverity,
    SLATerms,
    PricingTerms,
    ContractBreach,
    ContractCompliance,
    AgentContract,
    ContractService,
    get_contract_service
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
    'get_reputation_service',
    # Contracts
    'ContractStatus',
    'BreachSeverity',
    'SLATerms',
    'PricingTerms',
    'ContractBreach',
    'ContractCompliance',
    'AgentContract',
    'ContractService',
    'get_contract_service'
]
