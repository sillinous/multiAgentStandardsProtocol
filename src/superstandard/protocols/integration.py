"""
Protocol Integration Layer

Automatically integrates multiple protocols to create self-improving behaviors.

Key Integration:
- Reputation → Discovery: Auto-update discovery reputation scores
- Contracts → Reputation: Breaches affect reputation automatically
- Contracts → Resources: Use pricing terms for resource allocation
- Reputation → Resources: High-rep agents get priority and larger quotas
- Reputation → Dashboard: Broadcast reputation change events

This is the magic that makes the system self-improving!
"""

import logging
from typing import Optional

from .discovery import get_discovery_service, AgentDiscoveryService
from .reputation import get_reputation_service, ReputationService
from .contracts import get_contract_service, ContractService
from .resources import (
    get_resource_service,
    ResourceAllocationService,
    ResourceType,
    ResourceQuota
)


logger = logging.getLogger(__name__)


class ProtocolIntegration:
    """
    Integrates multiple protocols to create self-improving behaviors

    Key Features:
    - Auto-update discovery reputation from reputation service
    - Contract breaches automatically affect reputation
    - Contract pricing auto-configures resource allocations
    - High-reputation agents get priority resource allocation
    - Broadcast reputation events to dashboard
    - Seamless cross-protocol communication
    """

    def __init__(
        self,
        discovery: Optional[AgentDiscoveryService] = None,
        reputation: Optional[ReputationService] = None,
        contracts: Optional[ContractService] = None,
        resources: Optional[ResourceAllocationService] = None
    ):
        """
        Initialize protocol integration

        Args:
            discovery: Discovery service (uses global if not provided)
            reputation: Reputation service (uses global if not provided)
            contracts: Contract service (uses global if not provided)
            resources: Resource service (uses global if not provided)
        """
        self.discovery = discovery or get_discovery_service()
        self.reputation = reputation or get_reputation_service()
        self.contracts = contracts or get_contract_service()
        self.resources = resources or get_resource_service()

        # Wrap reputation's record_outcome to also update discovery
        self._wrap_reputation_updates()

        # Wrap contracts' record_request to also affect reputation
        self._wrap_contract_breaches()

        # Wrap contract creation to auto-setup resource allocation
        self._wrap_contract_creation()

        # Wrap resource requests to use reputation for priority
        self._wrap_resource_requests()

        logger.info("✅ Protocol Integration initialized")
        logger.info("   Reputation → Discovery: Auto-updates enabled")
        logger.info("   Contracts → Reputation: Breach penalties enabled")
        logger.info("   Contracts → Resources: Auto-allocation enabled")
        logger.info("   Reputation → Resources: Priority allocation enabled")

    def _wrap_reputation_updates(self):
        """Wrap reputation service to auto-update discovery"""
        original_record = self.reputation.record_outcome

        async def wrapped_record(*args, **kwargs):
            # Call original method
            outcome = await original_record(*args, **kwargs)

            # Get agent_id from outcome
            agent_id = outcome.agent_id

            # Update discovery with new reputation
            await self._sync_reputation_to_discovery(agent_id)

            return outcome

        # Replace method
        self.reputation.record_outcome = wrapped_record

    async def _sync_reputation_to_discovery(self, agent_id: str):
        """Sync reputation scores to discovery metadata"""
        try:
            # Get latest reputation
            reputation = await self.reputation.get_reputation(agent_id)
            if not reputation:
                return

            # Update discovery metadata
            await self.discovery.update_metadata(
                agent_id,
                {
                    "reputation_score": reputation.overall_score,
                    "avg_quality_score": reputation.avg_quality,
                    "success_rate": (
                        reputation.successful_tasks / reputation.total_tasks
                        if reputation.total_tasks > 0 else 0.0
                    ),
                    "total_tasks_completed": reputation.total_tasks,
                    "avg_latency_ms": reputation.avg_duration_ms,
                    "cost_per_request": reputation.avg_cost
                }
            )

            logger.debug(
                f"🔄 Synced reputation to discovery: {agent_id} "
                f"({reputation.overall_score:.3f})"
            )

        except Exception as e:
            logger.error(f"Failed to sync reputation to discovery: {e}")

    def _wrap_contract_breaches(self):
        """Wrap contract service to automatically penalize reputation for breaches"""
        original_record = self.contracts.record_request

        async def wrapped_record(*args, **kwargs):
            # Call original method
            breaches = await original_record(*args, **kwargs)

            # If there were breaches, record negative reputation impact
            if breaches and len(args) > 0:
                contract_id = args[0]  # First arg is contract_id
                contract = await self.contracts.get_contract(contract_id)

                if contract:
                    # Record failed outcome for provider (they breached the SLA)
                    for breach in breaches:
                        await self.reputation.record_outcome(
                            agent_id=contract.provider_id,
                            task_id=f"contract-{contract_id}-{breach.breach_id}",
                            success=False,  # Breach = failure
                            quality_score=breach.actual_value if breach.breach_type == "quality" else None,
                            duration_ms=breach.actual_value if breach.breach_type == "latency" else None,
                            error_type=f"contract_breach_{breach.breach_type}",
                            metadata={
                                "breach_severity": breach.severity.value,
                                "contract_id": contract_id
                            }
                        )

                        logger.info(
                            f"⚠️  Reputation penalty applied for {contract.provider_id} "
                            f"(breach: {breach.breach_type})"
                        )

            return breaches

        # Replace method
        self.contracts.record_request = wrapped_record

    def _wrap_contract_creation(self):
        """Wrap contract creation to auto-setup resource allocation"""
        original_create = self.contracts.create_contract

        async def wrapped_create(*args, **kwargs):
            # Call original method
            contract = await original_create(*args, **kwargs)

            # Auto-create resource allocation based on contract pricing
            try:
                # Calculate budget from pricing terms
                budget_usd = contract.pricing.monthly_cap if contract.pricing.monthly_cap else 100.0
                api_calls_limit = int(budget_usd / contract.pricing.per_request) if contract.pricing.per_request > 0 else 1000

                # Create quotas based on contract
                quotas = {
                    ResourceType.API_CALLS.value: ResourceQuota(
                        ResourceType.API_CALLS,
                        api_calls_limit,
                        description=f"Contract {contract.contract_id} API quota"
                    ),
                    ResourceType.BUDGET_USD.value: ResourceQuota(
                        ResourceType.BUDGET_USD,
                        budget_usd,
                        description=f"Contract {contract.contract_id} budget"
                    )
                }

                # Request allocation for consumer
                allocation = await self.resources.request_allocation(
                    agent_id=contract.consumer_id,
                    quotas=quotas,
                    priority=5,  # Default priority
                    duration_hours=720,  # 30 days (matches contract)
                    auto_approve=True
                )

                logger.info(
                    f"💰 Auto-created resource allocation for contract {contract.contract_id}: "
                    f"{contract.consumer_id} (budget: ${budget_usd}, calls: {api_calls_limit})"
                )

            except Exception as e:
                logger.error(f"Failed to auto-create resource allocation: {e}")

            return contract

        # Replace method
        self.contracts.create_contract = wrapped_create

    def _wrap_resource_requests(self):
        """Wrap resource requests to use reputation for priority"""
        original_request = self.resources.request_allocation

        async def wrapped_request(*args, **kwargs):
            # Get agent_id from args or kwargs
            agent_id = args[0] if args else kwargs.get('agent_id')

            if agent_id:
                try:
                    # Get agent reputation
                    reputation = await self.reputation.get_reputation(agent_id)

                    if reputation:
                        # Calculate priority based on reputation (1-10 scale)
                        # High reputation (>0.9) = priority 9-10
                        # Good reputation (0.7-0.9) = priority 6-8
                        # Medium reputation (0.5-0.7) = priority 4-5
                        # Low reputation (<0.5) = priority 1-3
                        if reputation.overall_score >= 0.9:
                            priority = 9
                        elif reputation.overall_score >= 0.8:
                            priority = 8
                        elif reputation.overall_score >= 0.7:
                            priority = 7
                        elif reputation.overall_score >= 0.6:
                            priority = 6
                        elif reputation.overall_score >= 0.5:
                            priority = 5
                        else:
                            priority = max(1, int(reputation.overall_score * 10))

                        # Also boost quotas for high-reputation agents
                        quota_multiplier = 1.0 + (reputation.overall_score - 0.5)  # 0.5-1.5x multiplier

                        # Update priority in kwargs
                        if 'priority' not in kwargs:
                            kwargs['priority'] = priority

                        # Boost quotas for high-rep agents
                        if 'quotas' in kwargs and kwargs['quotas']:
                            for quota in kwargs['quotas'].values():
                                quota.limit *= quota_multiplier

                        logger.info(
                            f"🎯 Reputation-based resource allocation: {agent_id} "
                            f"(rep: {reputation.overall_score:.2f}, priority: {priority}, "
                            f"boost: {quota_multiplier:.2f}x)"
                        )

                except Exception as e:
                    logger.debug(f"Could not apply reputation to resource request: {e}")

            # Call original method
            if args:
                return await original_request(*args, **kwargs)
            else:
                return await original_request(**kwargs)

        # Replace method
        self.resources.request_allocation = wrapped_request


# Global integration instance
_integration: Optional[ProtocolIntegration] = None


def get_protocol_integration() -> ProtocolIntegration:
    """Get or create global protocol integration"""
    global _integration
    if _integration is None:
        _integration = ProtocolIntegration()
    return _integration


def enable_auto_sync():
    """Enable automatic synchronization between protocols"""
    integration = get_protocol_integration()
    logger.info("🔄 Protocol auto-sync enabled: Reputation → Discovery")
    return integration


__all__ = [
    'ProtocolIntegration',
    'get_protocol_integration',
    'enable_auto_sync'
]
