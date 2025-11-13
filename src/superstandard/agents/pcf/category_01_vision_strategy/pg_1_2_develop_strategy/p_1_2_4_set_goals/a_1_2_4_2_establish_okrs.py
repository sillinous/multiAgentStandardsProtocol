"""
APQC PCF Agent: Establish Key Results (OKRs) (1.2.4.2)

Defines measurable key results for each objective.
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


class EstablishOKRsAgent(ActivityAgentBase):
    """Agent for establishing OKRs."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10064",
            hierarchy_id="1.2.4.2",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.2",
            process_group_name="Develop business strategy",
            process_id="1.2.4",
            process_name="Develop and set organizational goals",
            activity_id="1.2.4.2",
            activity_name="Establish key results (OKRs)",
            parent_element_id="10050",
            kpis=[
                {"name": "key_results_count", "type": "count", "unit": "number"},
                {"name": "measurability_score", "type": "score", "unit": "0-10"},
                {"name": "target_ambition", "type": "score", "unit": "0-10"}
            ]
        )

        return PCFAgentConfig(
            agent_id="establish_okrs_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Establish OKRs."""
        execution_start = datetime.utcnow()

        okrs = await self._define_okrs()
        indicators = await self._define_leading_lagging_indicators()
        targets = await self._set_ambitious_targets()

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        total_krs = sum(len(okr["key_results"]) for okr in okrs)

        result = {
            "okr_overview": {
                "execution_date": execution_start.isoformat(),
                "framework": "OKRs with leading and lagging indicators"
            },
            "okrs": okrs,
            "indicators": indicators,
            "targets": targets,
            "kpis": {
                "key_results_count": total_krs,
                "measurability_score": round(random.uniform(8.5, 9.5), 1),
                "target_ambition": round(random.uniform(8.0, 9.0), 1),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _define_okrs(self) -> List[Dict[str, Any]]:
        """Define OKRs."""
        await asyncio.sleep(0.05)

        return [
            {
                "objective": "Achieve $500M ARR by end of Year 3",
                "key_results": [
                    {"kr": "Reach $150M ARR by end of Year 1", "current": 0, "target": 150, "unit": "$M"},
                    {"kr": "Reach $300M ARR by end of Year 2", "current": 0, "target": 300, "unit": "$M"},
                    {"kr": "Reach $500M ARR by end of Year 3", "current": 0, "target": 500, "unit": "$M"}
                ]
            },
            {
                "objective": "Launch platform MVP and achieve 100 customers",
                "key_results": [
                    {"kr": "Complete core platform features", "current": "0%", "target": "100%", "unit": "%"},
                    {"kr": "Onboard 100 paying customers", "current": 0, "target": 100, "unit": "customers"},
                    {"kr": "Achieve NPS >50", "current": 0, "target": 50, "unit": "score"}
                ]
            }
        ]

    async def _define_leading_lagging_indicators(self) -> Dict[str, Any]:
        """Define leading and lagging indicators."""
        await asyncio.sleep(0.05)

        return {
            "indicators": [
                {
                    "objective": "Revenue Growth",
                    "lagging": ["Monthly ARR", "Quarterly bookings"],
                    "leading": ["Sales pipeline", "Demo requests", "Trial conversions"]
                },
                {
                    "objective": "Platform Success",
                    "lagging": ["Customer count", "NPS"],
                    "leading": ["Feature adoption rate", "Daily active users", "Time to value"]
                }
            ]
        }

    async def _set_ambitious_targets(self) -> Dict[str, Any]:
        """Set ambitious targets."""
        await asyncio.sleep(0.05)

        return {
            "target_philosophy": "Set targets at 70-80% probability of achievement",
            "stretch_targets": "Additional 20-30% beyond base targets",
            "threshold_targets": "Minimum acceptable performance (50% of target)"
        }


__all__ = ['EstablishOKRsAgent']
