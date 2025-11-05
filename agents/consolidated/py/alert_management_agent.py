#!/usr/bin/env python3
"""
🌙 Alert Management Agent

Autonomous agent that manages alerts across the system.
Handles alert acknowledgment, resolution, and notification dispatch.

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


class AlertManagementAgent(BaseAgent):
    """Agent that manages system alerts"""

    name = "alert_management_agent"
    description = "Manages alerts and notifications"
    category = "monitoring"
    exchange = "general"

    def __init__(self):
        """Initialize alert management agent"""
        super().__init__()
        self.db = SessionLocal()
        self.orchestrator = AgentOrchestrator(self.db)

    async def execute(self) -> Dict[str, Any]:
        """
        Execute alert management tasks

        Returns:
            Dictionary with alert management results
        """
        try:
            logger.info("Starting alert management cycle")

            # Get current alert statistics
            alert_stats = self.orchestrator.get_alert_stats()

            # Get all active alerts
            active_alerts = self.orchestrator.get_active_alerts()

            # Analyze alerts
            critical_alerts = [a for a in active_alerts if a["alert_type"] == "critical"]
            warning_alerts = [a for a in active_alerts if a["alert_type"] == "warning"]
            info_alerts = [a for a in active_alerts if a["alert_type"] == "info"]

            # Log alert summary
            logger.info(
                f"Alert summary: {len(critical_alerts)} critical, "
                f"{len(warning_alerts)} warnings, {len(info_alerts)} info"
            )

            result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_statistics": alert_stats,
                "active_alerts": {
                    "critical": len(critical_alerts),
                    "warning": len(warning_alerts),
                    "info": len(info_alerts),
                    "total": len(active_alerts),
                },
                "alerts": active_alerts,
            }

            return result

        except Exception as e:
            logger.error(f"Error during alert management: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            self.db.close()

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert

        Args:
            alert_id: ID of alert to acknowledge

        Returns:
            Updated alert data
        """
        alert = self.orchestrator.acknowledge_alert(alert_id)
        return alert if alert else {"error": "Alert not found"}

    def resolve_alert(
        self,
        alert_id: str,
        resolution_message: str = "Issue resolved",
    ) -> Dict[str, Any]:
        """
        Resolve an alert

        Args:
            alert_id: ID of alert to resolve
            resolution_message: Message about resolution

        Returns:
            Updated alert data
        """
        alert = self.orchestrator.resolve_alert(alert_id, resolution_message)
        return alert if alert else {"error": "Alert not found"}

    def get_active_alerts_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get active alerts for a specific agent"""
        return self.orchestrator.get_active_alerts(agent_name)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get overall alert statistics"""
        return self.orchestrator.get_alert_stats()

    def create_alert(
        self,
        agent_name: str,
        alert_type: str,
        message: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new alert"""
        return self.orchestrator.create_alert(agent_name, alert_type, message, metadata)


async def main():
    """Run alert management agent standalone"""
    agent = AlertManagementAgent()
    result = await agent.execute()

    print("\n" + "=" * 60)
    print("🚨 ALERT MANAGEMENT REPORT")
    print("=" * 60)
    print(f"Timestamp: {result.get('timestamp')}")

    stats = result.get("alert_statistics", {})
    print(f"\nOverall Statistics:")
    print(f"  Total Alerts: {stats.get('total_alerts', 0)}")
    print(f"  Active: {stats.get('by_status', {}).get('active', 0)}")
    print(f"  Acknowledged: {stats.get('by_status', {}).get('acknowledged', 0)}")
    print(f"  Resolved: {stats.get('by_status', {}).get('resolved', 0)}")

    active = result.get("active_alerts", {})
    print(f"\nActive Alerts:")
    print(f"  Critical: {active.get('critical', 0)}")
    print(f"  Warning: {active.get('warning', 0)}")
    print(f"  Info: {active.get('info', 0)}")
    print(f"  Total: {active.get('total', 0)}")

    # Show sample alerts
    alerts = result.get("alerts", [])
    if alerts:
        print(f"\nRecent Alerts (showing first 5):")
        for alert in alerts[:5]:
            print(f"  [{alert.get('alert_type').upper()}] {alert.get('agent_name')}: {alert.get('message')}")

    print("\n" + "=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(main())
