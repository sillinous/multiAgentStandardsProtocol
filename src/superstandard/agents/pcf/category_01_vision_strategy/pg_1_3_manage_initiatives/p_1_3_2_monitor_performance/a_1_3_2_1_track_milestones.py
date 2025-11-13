"""
APQC PCF Agent: Track Initiative Milestones (1.3.2.1)

Monitors progress against initiative milestones and identifies variances.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
import random

from superstandard.agents.pcf.base import (
    ActivityAgentBase,
    PCFMetadata,
    PCFAgentConfig,
)


class TrackMilestonesAgent(ActivityAgentBase):
    """Agent for tracking initiative milestones."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10071",
            hierarchy_id="1.3.2.1",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.3",
            process_group_name="Manage strategic initiatives",
            process_id="1.3.2",
            process_name="Monitor strategic initiative performance",
            activity_id="1.3.2.1",
            activity_name="Track initiative milestones",
            parent_element_id="10050",
            kpis=[
                {"name": "milestones_tracked", "type": "count", "unit": "number"},
                {"name": "on_time_completion", "type": "percentage", "unit": "%"},
                {"name": "average_variance", "type": "duration", "unit": "days"}
            ]
        )

        return PCFAgentConfig(
            agent_id="track_milestones_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track initiative milestones."""
        execution_start = datetime.utcnow()

        milestones = await self._collect_milestone_data()
        status_analysis = await self._analyze_milestone_status(milestones)
        variance_analysis = await self._analyze_variances(milestones)
        alerts = await self._generate_alerts(milestones, status_analysis)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "milestone_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Initiative milestone tracking and variance analysis"
            },
            "milestones": milestones,
            "status_analysis": status_analysis,
            "variance_analysis": variance_analysis,
            "alerts": alerts,
            "kpis": {
                "milestones_tracked": milestones["total_milestones"],
                "on_time_completion": status_analysis["on_time_percentage"],
                "average_variance": variance_analysis["average_variance_days"],
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _collect_milestone_data(self) -> Dict[str, Any]:
        """Collect milestone data across initiatives."""
        await asyncio.sleep(0.05)

        milestones = []
        for i in range(random.randint(15, 25)):
            planned_date = datetime.utcnow() + timedelta(days=random.randint(-60, 120))
            actual_or_forecast = planned_date + timedelta(days=random.randint(-15, 30))

            status = random.choice(["Completed", "On Track", "At Risk", "Delayed"])

            milestone = {
                "id": f"MS-{i+1:03d}",
                "initiative_id": f"INIT-{random.randint(1, 10):03d}",
                "name": f"Milestone {i+1}",
                "type": random.choice(["Phase Gate", "Deliverable", "Decision Point", "Go-Live"]),
                "planned_date": planned_date.strftime("%Y-%m-%d"),
                "actual_or_forecast_date": actual_or_forecast.strftime("%Y-%m-%d"),
                "status": status,
                "completion": random.randint(0, 100) if status != "Completed" else 100,
                "variance_days": (actual_or_forecast - planned_date).days
            }
            milestones.append(milestone)

        return {
            "milestones": milestones,
            "total_milestones": len(milestones)
        }

    async def _analyze_milestone_status(self, milestones: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze milestone status distribution."""
        await asyncio.sleep(0.05)

        milestone_list = milestones["milestones"]

        completed = len([m for m in milestone_list if m["status"] == "Completed"])
        on_track = len([m for m in milestone_list if m["status"] == "On Track"])
        at_risk = len([m for m in milestone_list if m["status"] == "At Risk"])
        delayed = len([m for m in milestone_list if m["status"] == "Delayed"])

        on_time = len([m for m in milestone_list if m["status"] == "Completed" and m["variance_days"] <= 7])

        return {
            "status_distribution": {
                "completed": completed,
                "on_track": on_track,
                "at_risk": at_risk,
                "delayed": delayed
            },
            "on_time_completion": on_time,
            "on_time_percentage": round(on_time / completed * 100, 1) if completed > 0 else 0,
            "health_assessment": random.choice(["Healthy", "Needs Attention", "Good Progress"])
        }

    async def _analyze_variances(self, milestones: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze milestone variances."""
        await asyncio.sleep(0.05)

        milestone_list = milestones["milestones"]
        variances = [m["variance_days"] for m in milestone_list]

        avg_variance = sum(variances) / len(variances) if variances else 0

        return {
            "average_variance_days": round(avg_variance, 1),
            "max_positive_variance": max(variances) if variances else 0,
            "max_negative_variance": min(variances) if variances else 0,
            "variance_trends": {
                "last_30_days": f"{random.randint(-5, 5)} days avg",
                "last_90_days": f"{random.randint(-3, 8)} days avg",
                "trend": random.choice(["Improving", "Stable", "Deteriorating"])
            }
        }

    async def _generate_alerts(self, milestones: Dict[str, Any], status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for milestone issues."""
        await asyncio.sleep(0.05)

        milestone_list = milestones["milestones"]

        alerts = []
        for m in milestone_list:
            if m["status"] == "Delayed" and m["variance_days"] > 14:
                alerts.append({
                    "severity": "High",
                    "milestone": m["name"],
                    "issue": f"Delayed by {m['variance_days']} days",
                    "action_required": "Escalate to Initiative Review Board"
                })
            elif m["status"] == "At Risk":
                alerts.append({
                    "severity": "Medium",
                    "milestone": m["name"],
                    "issue": "At risk of delay",
                    "action_required": "Develop recovery plan"
                })

        return alerts[:10]  # Return top 10 alerts


__all__ = ['TrackMilestonesAgent']
