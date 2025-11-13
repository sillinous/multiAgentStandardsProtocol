"""
APQC PCF Agent: Define Resource Requirements (1.2.3.3)

Determines headcount, capital, and capability requirements.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
import random

from superstandard.agents.pcf.base import (
    ActivityAgentBase,
    PCFMetadata,
    PCFAgentConfig,
)


class ResourceRequirementsAgent(ActivityAgentBase):
    """Agent for defining resource requirements."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10061",
            hierarchy_id="1.2.3.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.2",
            process_group_name="Develop business strategy",
            process_id="1.2.3",
            process_name="Develop business plans",
            activity_id="1.2.3.3",
            activity_name="Define resource requirements",
            parent_element_id="10050",
            kpis=[
                {"name": "headcount_plan", "type": "count", "unit": "number"},
                {"name": "capex_requirements", "type": "currency", "unit": "USD"},
                {"name": "capability_gaps", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="resource_requirements_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Define resource requirements."""
        execution_start = datetime.utcnow()

        headcount = await self._plan_headcount()
        capital = await self._plan_capital_investments()
        capabilities = await self._assess_capability_gaps()

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "requirements_overview": {
                "execution_date": execution_start.isoformat(),
                "planning_horizon": "3 years"
            },
            "headcount_plan": headcount,
            "capital_investments": capital,
            "capability_gaps": capabilities,
            "kpis": {
                "headcount_plan": headcount["year_3_headcount"],
                "capex_requirements": capital["total_capex"],
                "capability_gaps": len(capabilities["critical_gaps"]),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _plan_headcount(self) -> Dict[str, Any]:
        """Plan headcount requirements."""
        await asyncio.sleep(0.05)

        return {
            "current_headcount": random.randint(200, 400),
            "year_3_headcount": random.randint(600, 1000),
            "by_function": {
                "Engineering": f"{random.randint(30, 40)}%",
                "Sales": f"{random.randint(20, 30)}%",
                "Operations": f"{random.randint(15, 25)}%"
            }
        }

    async def _plan_capital_investments(self) -> Dict[str, Any]:
        """Plan capital investments."""
        await asyncio.sleep(0.05)

        return {
            "total_capex": f"${random.randint(50, 150)}M",
            "by_category": {
                "Technology": f"${random.randint(20, 60)}M",
                "Facilities": f"${random.randint(10, 30)}M",
                "Equipment": f"${random.randint(5, 20)}M"
            }
        }

    async def _assess_capability_gaps(self) -> Dict[str, Any]:
        """Assess capability gaps."""
        await asyncio.sleep(0.05)

        return {
            "critical_gaps": [
                {"gap": "AI/ML Engineering", "severity": "High"},
                {"gap": "Enterprise Sales", "severity": "High"},
                {"gap": "Vertical Expertise", "severity": "Medium"}
            ],
            "development_plan": "12-18 month ramp with mix of hiring and partnerships"
        }


__all__ = ['ResourceRequirementsAgent']
