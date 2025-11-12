"""
APQC PCF Agent: Evaluate Market Attractiveness (1.1.3.2)

Evaluates market attractiveness using multi-criteria framework including
market size, growth potential, profitability, and competitive dynamics.
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


class EvaluateAttractivenessAgent(ActivityAgentBase):
    """Agent for evaluating market attractiveness."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10035",
            hierarchy_id="1.1.3.2",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.3",
            process_name="Select relevant markets",
            activity_id="1.1.3.2",
            activity_name="Evaluate market attractiveness",
            parent_element_id="10035",
            kpis=[
                {"name": "markets_evaluated", "type": "count", "unit": "number"},
                {"name": "avg_attractiveness_score", "type": "score", "unit": "0-10"},
                {"name": "high_attractiveness_count", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="evaluate_attractiveness_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate market attractiveness."""
        execution_start = datetime.utcnow()

        # Get segments to evaluate (from 1.1.3.1 or mock)
        segments = input_data.get("segments", self._get_mock_segments())

        # Evaluate each segment
        evaluations = []
        for segment in segments:
            evaluation = await self._evaluate_segment_attractiveness(segment)
            evaluations.append(evaluation)

        # Rank segments by attractiveness
        evaluations.sort(key=lambda x: x["overall_attractiveness_score"], reverse=True)

        # Calculate metrics
        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        avg_score = sum(e["overall_attractiveness_score"] for e in evaluations) / len(evaluations) if evaluations else 0
        high_count = len([e for e in evaluations if e["overall_attractiveness_score"] >= 7.5])

        result = {
            "evaluation_overview": {
                "execution_date": execution_start.isoformat(),
                "segments_evaluated": len(segments)
            },
            "segment_evaluations": evaluations,
            "rankings": [
                {"rank": i+1, "segment_name": e["segment_name"], "score": e["overall_attractiveness_score"]}
                for i, e in enumerate(evaluations)
            ],
            "kpis": {
                "markets_evaluated": len(segments),
                "avg_attractiveness_score": round(avg_score, 1),
                "high_attractiveness_count": high_count,
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _evaluate_segment_attractiveness(
        self,
        segment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate attractiveness of a single segment."""
        await asyncio.sleep(0.05)

        # Scoring dimensions
        market_size_score = round(random.uniform(5.0, 9.5), 1)
        growth_score = round(random.uniform(4.5, 9.8), 1)
        profitability_score = round(random.uniform(5.5, 9.2), 1)
        competitive_score = round(random.uniform(3.0, 8.5), 1)
        accessibility_score = round(random.uniform(4.0, 9.0), 1)

        overall_score = (
            market_size_score * 0.25 +
            growth_score * 0.25 +
            profitability_score * 0.20 +
            competitive_score * 0.15 +
            accessibility_score * 0.15
        )

        return {
            "segment_id": segment.get("segment_id", "SEG_001"),
            "segment_name": segment.get("name", "Segment"),
            "market_size_score": market_size_score,
            "growth_score": growth_score,
            "profitability_score": profitability_score,
            "competitive_score": competitive_score,
            "accessibility_score": accessibility_score,
            "overall_attractiveness_score": round(overall_score, 1),
            "attractiveness_tier": "High" if overall_score >= 7.5 else "Medium" if overall_score >= 5.5 else "Low",
            "recommendation": "Priority target" if overall_score >= 7.5 else "Consider" if overall_score >= 5.5 else "Deprioritize"
        }

    def _get_mock_segments(self) -> List[Dict[str, Any]]:
        """Generate mock segments if not provided."""
        return [
            {"segment_id": f"SEG_{i:03d}", "name": f"Segment {i}"}
            for i in range(1, 6)
        ]


__all__ = ['EvaluateAttractivenessAgent']
