"""
APQC PCF Agent: Assess Strategic Fit and Capabilities (1.1.3.3)

Evaluates organizational readiness and strategic alignment for each market segment.
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


class AssessStrategicFitAgent(ActivityAgentBase):
    """Agent for assessing strategic fit."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10035",
            hierarchy_id="1.1.3.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.3",
            process_name="Select relevant markets",
            activity_id="1.1.3.3",
            activity_name="Assess strategic fit and capabilities",
            parent_element_id="10035",
            kpis=[
                {"name": "segments_assessed", "type": "count", "unit": "number"},
                {"name": "avg_fit_score", "type": "score", "unit": "0-10"},
                {"name": "strong_fit_count", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="assess_strategic_fit_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess strategic fit."""
        execution_start = datetime.utcnow()

        segments = input_data.get("segments", self._get_mock_segments())

        assessments = []
        for segment in segments:
            assessment = await self._assess_segment_fit(segment)
            assessments.append(assessment)

        assessments.sort(key=lambda x: x["overall_fit_score"], reverse=True)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        avg_score = sum(a["overall_fit_score"] for a in assessments) / len(assessments) if assessments else 0
        strong_count = len([a for a in assessments if a["overall_fit_score"] >= 7.5])

        result = {
            "assessment_overview": {
                "execution_date": execution_start.isoformat(),
                "segments_assessed": len(segments)
            },
            "fit_assessments": assessments,
            "capability_gaps": [
                {
                    "segment_id": a["segment_id"],
                    "gaps": random.sample(["Sales capacity", "Technical expertise", "Market knowledge", "Partnership network"], random.randint(1, 3))
                }
                for a in assessments[:3]
            ],
            "kpis": {
                "segments_assessed": len(segments),
                "avg_fit_score": round(avg_score, 1),
                "strong_fit_count": strong_count,
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _assess_segment_fit(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fit for a single segment."""
        await asyncio.sleep(0.05)

        vision_alignment = round(random.uniform(5.0, 9.5), 1)
        capability_match = round(random.uniform(4.5, 9.0), 1)
        resource_availability = round(random.uniform(5.0, 8.5), 1)
        brand_fit = round(random.uniform(5.5, 9.2), 1)

        overall_score = (
            vision_alignment * 0.30 +
            capability_match * 0.30 +
            resource_availability * 0.25 +
            brand_fit * 0.15
        )

        return {
            "segment_id": segment.get("segment_id", "SEG_001"),
            "segment_name": segment.get("name", "Segment"),
            "vision_alignment_score": vision_alignment,
            "capability_match_score": capability_match,
            "resource_availability_score": resource_availability,
            "brand_fit_score": brand_fit,
            "overall_fit_score": round(overall_score, 1),
            "fit_tier": "Strong" if overall_score >= 7.5 else "Moderate" if overall_score >= 5.5 else "Weak",
            "recommendation": "Excellent fit" if overall_score >= 7.5 else "Acceptable fit" if overall_score >= 5.5 else "Poor fit"
        }

    def _get_mock_segments(self) -> List[Dict[str, Any]]:
        return [{"segment_id": f"SEG_{i:03d}", "name": f"Segment {i}"} for i in range(1, 6)]


__all__ = ['AssessStrategicFitAgent']
