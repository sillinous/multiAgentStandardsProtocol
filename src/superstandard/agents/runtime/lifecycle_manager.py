"""
⚙️ LifecycleManager - Simplified Agent Lifecycle Control
========================================================

Lightweight manager for agent lifecycle operations.
Most logic is in RuntimeAgent; this provides high-level coordination.
"""

import logging
from typing import Dict, Any, List
from .agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages agent lifecycle at a high level.

    Provides simple interface for:
    - Bulk operations
    - Health checking
    - Statistics aggregation
    """

    def __init__(self, factory: AgentFactory):
        """
        Initialize lifecycle manager.

        Args:
            factory: AgentFactory instance
        """
        self.factory = factory
        logger.info("⚙️ LifecycleManager initialized")

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all running agents.

        Returns:
            Health status summary
        """
        agents = self.factory.get_running_agents()

        healthy = sum(1 for a in agents if a["state"] in ["idle", "working"])
        unhealthy = sum(1 for a in agents if a["state"] == "error")
        paused = sum(1 for a in agents if a["state"] == "paused")

        return {
            "total_agents": len(agents),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "paused": paused,
            "agents": agents
        }

    async def stop_all_agents(self):
        """Stop all running agents"""
        await self.factory.stop_all_agents()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated statistics across all agents.

        Returns:
            Statistics summary
        """
        agents = self.factory.get_running_agents()

        total_tasks = sum(a["stats"]["tasks_completed"] for a in agents)
        total_failed = sum(a["stats"]["tasks_failed"] for a in agents)
        total_exec_time = sum(a["stats"]["total_execution_time"] for a in agents)

        return {
            "total_agents": len(agents),
            "total_tasks_completed": total_tasks,
            "total_tasks_failed": total_failed,
            "total_execution_time": total_exec_time,
            "average_task_time": total_exec_time / total_tasks if total_tasks > 0 else 0,
            "success_rate": (total_tasks / (total_tasks + total_failed) * 100) if (total_tasks + total_failed) > 0 else 100
        }
