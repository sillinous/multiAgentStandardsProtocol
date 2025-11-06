#!/usr/bin/env python3
"""
🌙 Health Check Agent

Autonomous agent that monitors the health of other agents.
Performs comprehensive health checks and creates alerts for issues.

Can run independently or as part of the orchestration system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from src.db import SessionLocal
from src.orchestration import AgentOrchestrator
from src.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class HealthCheckAgent(BaseAgent):
    """Agent that monitors health of other agents"""

    name = "health_check_agent"
    description = "Monitors agent health and creates alerts"
    category = "monitoring"
    exchange = "general"

    def __init__(self):
        """Initialize health check agent"""
        super().__init__()
        self.db = SessionLocal()
        self.orchestrator = AgentOrchestrator(self.db)

    async def execute(self) -> Dict[str, Any]:
        """
        Execute health checks on all running agents

        Returns:
            Dictionary with health check results
        """
        try:
            logger.info("Starting health check on all agents")

            # Check health of all running agents
            health_summaries = self.orchestrator.check_all_agents_health()

            # Analyze results and create alerts
            critical_alerts = []
            warning_alerts = []

            for summary in health_summaries:
                if summary["overall_status"] == "critical":
                    critical_alerts.append(summary["agent_name"])
                    # Create alert for critical status
                    self.orchestrator.create_alert(
                        agent_name=summary["agent_name"],
                        alert_type="critical",
                        message=f"Agent {summary['agent_name']} is in critical health status",
                        metadata={"health_summary": summary},
                    )
                elif summary["overall_status"] == "warning":
                    warning_alerts.append(summary["agent_name"])
                    # Create alert for warning status
                    self.orchestrator.create_alert(
                        agent_name=summary["agent_name"],
                        alert_type="warning",
                        message=f"Agent {summary['agent_name']} has health warnings",
                        metadata={"health_summary": summary},
                    )

            # Attempt auto-remediation for critical issues
            remediation_results = self.orchestrator.auto_remediate_failures()

            result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "agents_checked": len(health_summaries),
                "critical_alerts": len(critical_alerts),
                "warning_alerts": len(warning_alerts),
                "critical_agents": critical_alerts,
                "warning_agents": warning_alerts,
                "remediation": remediation_results,
                "health_summaries": health_summaries,
            }

            logger.info(f"Health check complete: {len(health_summaries)} agents checked")
            return result

        except Exception as e:
            logger.error(f"Error during health check: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            self.db.close()

    def get_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Get health status for a specific agent"""
        return self.orchestrator.check_agent_health(agent_name)

    def get_health_statistics(self) -> Dict[str, Any]:
        """Get overall health statistics"""
        return self.orchestrator.get_health_stats()


async def main():
    """Run health check agent standalone"""
    agent = HealthCheckAgent()
    result = await agent.execute()

    print("\n" + "=" * 60)
    print("🏥 HEALTH CHECK RESULTS")
    print("=" * 60)
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"Agents Checked: {result.get('agents_checked')}")
    print(f"Critical: {result.get('critical_alerts')}")
    print(f"Warnings: {result.get('warning_alerts')}")
    print(f"Remediated: {result.get('remediation', {}).get('remediated', 0)}")

    if result.get("critical_agents"):
        print(f"\n⚠️  CRITICAL: {result['critical_agents']}")

    if result.get("warning_agents"):
        print(f"\n⚠️  WARNING: {result['warning_agents']}")

    print("\n" + "=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(main())
