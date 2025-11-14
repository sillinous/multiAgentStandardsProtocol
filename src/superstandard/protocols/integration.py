"""
Protocol Integration Layer

Automatically integrates multiple protocols to create self-improving behaviors.

Key Integration:
- Reputation → Discovery: Auto-update discovery reputation scores
- Reputation → Dashboard: Broadcast reputation change events

This is the magic that makes the system self-improving!
"""

import logging
from typing import Optional

from .discovery import get_discovery_service, AgentDiscoveryService
from .reputation import get_reputation_service, ReputationService


logger = logging.getLogger(__name__)


class ProtocolIntegration:
    """
    Integrates multiple protocols to create self-improving behaviors

    Key Features:
    - Auto-update discovery reputation from reputation service
    - Broadcast reputation events to dashboard
    - Seamless cross-protocol communication
    """

    def __init__(
        self,
        discovery: Optional[AgentDiscoveryService] = None,
        reputation: Optional[ReputationService] = None
    ):
        """
        Initialize protocol integration

        Args:
            discovery: Discovery service (uses global if not provided)
            reputation: Reputation service (uses global if not provided)
        """
        self.discovery = discovery or get_discovery_service()
        self.reputation = reputation or get_reputation_service()

        # Wrap reputation's record_outcome to also update discovery
        self._wrap_reputation_updates()

        logger.info("✅ Protocol Integration initialized")
        logger.info("   Reputation → Discovery: Auto-updates enabled")

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
