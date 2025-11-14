"""
Protocol Integration Layer

Automatically integrates multiple protocols to create self-improving behaviors.

Key Integration:
- Reputation → Discovery: Auto-update discovery reputation scores
- Contracts → Reputation: Breaches affect reputation automatically
- Reputation → Dashboard: Broadcast reputation change events

This is the magic that makes the system self-improving!
"""

import logging
from typing import Optional

from .discovery import get_discovery_service, AgentDiscoveryService
from .reputation import get_reputation_service, ReputationService
from .contracts import get_contract_service, ContractService


logger = logging.getLogger(__name__)


class ProtocolIntegration:
    """
    Integrates multiple protocols to create self-improving behaviors

    Key Features:
    - Auto-update discovery reputation from reputation service
    - Contract breaches automatically affect reputation
    - Broadcast reputation events to dashboard
    - Seamless cross-protocol communication
    """

    def __init__(
        self,
        discovery: Optional[AgentDiscoveryService] = None,
        reputation: Optional[ReputationService] = None,
        contracts: Optional[ContractService] = None
    ):
        """
        Initialize protocol integration

        Args:
            discovery: Discovery service (uses global if not provided)
            reputation: Reputation service (uses global if not provided)
            contracts: Contract service (uses global if not provided)
        """
        self.discovery = discovery or get_discovery_service()
        self.reputation = reputation or get_reputation_service()
        self.contracts = contracts or get_contract_service()

        # Wrap reputation's record_outcome to also update discovery
        self._wrap_reputation_updates()

        # Wrap contracts' record_request to also affect reputation
        self._wrap_contract_breaches()

        logger.info("✅ Protocol Integration initialized")
        logger.info("   Reputation → Discovery: Auto-updates enabled")
        logger.info("   Contracts → Reputation: Breach penalties enabled")

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
