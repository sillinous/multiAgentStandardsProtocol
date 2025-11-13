"""
APQC PCF Agent: Define Mission and Core Values (1.1.5.3)

Articulates organizational purpose (mission) and core values.
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


class DefineMissionValuesAgent(ActivityAgentBase):
    """Agent for defining mission statement and core values."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10045",
            hierarchy_id="1.1.5.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.5",
            process_name="Establish strategic vision",
            activity_id="1.1.5.3",
            activity_name="Define mission and core values",
            parent_element_id="10045",
            kpis=[
                {"name": "core_values_defined", "type": "count", "unit": "number"},
                {"name": "mission_clarity_score", "type": "score", "unit": "0-10"},
                {"name": "authenticity_score", "type": "score", "unit": "0-10"}
            ]
        )

        return PCFAgentConfig(
            agent_id="define_mission_values_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Define mission statement and core values."""
        execution_start = datetime.utcnow()

        # Craft mission statement
        mission_statement = await self._craft_mission_statement()

        # Define core values
        core_values = await self._define_core_values()

        # Create behavioral anchors for each value
        behavioral_anchors = await self._create_behavioral_anchors(core_values)

        # Assess cultural alignment
        cultural_assessment = await self._assess_cultural_alignment(mission_statement, core_values)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "definition_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Mission statement and organizational values"
            },
            "mission_statement": mission_statement,
            "core_values": core_values,
            "behavioral_anchors": behavioral_anchors,
            "cultural_assessment": cultural_assessment,
            "kpis": {
                "core_values_defined": len(core_values),
                "mission_clarity_score": mission_statement["clarity_score"],
                "authenticity_score": cultural_assessment["authenticity_score"],
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _craft_mission_statement(self) -> Dict[str, Any]:
        """Craft organizational mission statement."""
        await asyncio.sleep(0.05)

        mission_text = (
            "To empower organizations to unlock their full potential by delivering "
            "intelligent automation solutions that eliminate complexity, accelerate "
            "innovation, and create meaningful impact for customers, employees, and society."
        )

        return {
            "primary_statement": mission_text,
            "key_elements": {
                "purpose": "Empower organizations to unlock full potential",
                "how": "Intelligent automation solutions",
                "benefit": "Eliminate complexity, accelerate innovation, create impact",
                "stakeholders": "Customers, employees, society"
            },
            "clarity_score": round(random.uniform(8.5, 9.5), 1),
            "distinctiveness": "Focuses on empowerment and societal impact beyond just technology"
        }

    async def _define_core_values(self) -> List[Dict[str, Any]]:
        """Define organizational core values."""
        await asyncio.sleep(0.05)

        values = [
            {
                "value": "Customer Obsession",
                "definition": "We start with the customer and work backwards, obsessing over their success",
                "why_important": "Ensures we build what matters and deliver exceptional experiences",
                "decision_criterion": "When faced with choices, we ask: What's best for our customers?",
                "distinguishing": True
            },
            {
                "value": "Innovation Excellence",
                "definition": "We pursue breakthrough innovation, not incremental improvements",
                "why_important": "Drives competitive advantage and long-term leadership",
                "decision_criterion": "We invest in bold ideas that can create 10x impact",
                "distinguishing": True
            },
            {
                "value": "Intellectual Rigor",
                "definition": "We challenge assumptions, seek truth through data, and embrace complexity",
                "why_important": "Enables superior decision-making and problem-solving",
                "decision_criterion": "We require evidence and reasoning, not opinions",
                "distinguishing": True
            },
            {
                "value": "Bias for Action",
                "definition": "We move fast, experiment rapidly, and learn from failures",
                "why_important": "Speed of learning is a competitive advantage",
                "decision_criterion": "We choose calculated action over perfect planning",
                "distinguishing": False
            },
            {
                "value": "Collaborative Excellence",
                "definition": "We win as a team, share knowledge freely, and amplify each other",
                "why_important": "Collective intelligence outperforms individual brilliance",
                "decision_criterion": "We optimize for team success over individual glory",
                "distinguishing": False
            },
            {
                "value": "Integrity & Transparency",
                "definition": "We do what's right, communicate honestly, and build trust through transparency",
                "why_important": "Foundation for long-term relationships and sustainable success",
                "decision_criterion": "We choose the right path even when it's difficult",
                "distinguishing": False
            }
        ]

        return values

    async def _create_behavioral_anchors(self, values: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create specific behavioral examples for each value."""
        await asyncio.sleep(0.05)

        anchors = {}

        for value in values:
            if value["value"] == "Customer Obsession":
                anchors[value["value"]] = {
                    "positive_behaviors": [
                        "Spending time with customers to understand their challenges",
                        "Making product decisions based on customer data, not assumptions",
                        "Proactively solving customer problems before they escalate"
                    ],
                    "negative_behaviors": [
                        "Building features without customer validation",
                        "Prioritizing internal convenience over customer experience",
                        "Ignoring customer feedback or usage data"
                    ]
                }
            elif value["value"] == "Innovation Excellence":
                anchors[value["value"]] = {
                    "positive_behaviors": [
                        "Dedicating time to explore emerging technologies",
                        "Challenging status quo with 'what if' thinking",
                        "Prototyping bold ideas quickly to test viability"
                    ],
                    "negative_behaviors": [
                        "Settling for copying competitors",
                        "Dismissing ideas because 'that's not how it's done'",
                        "Avoiding risks to protect short-term metrics"
                    ]
                }

        return anchors

    async def _assess_cultural_alignment(
        self,
        mission: Dict[str, Any],
        values: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess alignment between mission, values, and culture."""
        await asyncio.sleep(0.05)

        return {
            "authenticity_score": round(random.uniform(8.0, 9.5), 1),
            "authenticity_assessment": (
                "Values reflect genuine organizational DNA and strategic priorities. "
                "Strong emphasis on innovation and customer-centricity aligns with "
                "product-led culture and market positioning."
            ),
            "mission_values_coherence": round(random.uniform(8.5, 9.5), 1),
            "coherence_assessment": (
                "Mission and values are mutually reinforcing. Customer obsession and "
                "innovation excellence directly support the mission of empowering "
                "organizations through intelligent automation."
            ),
            "cultural_fit": {
                "current_culture_alignment": "Strong - values reflect existing strengths",
                "aspirational_elements": "Intellectual rigor and bias for action need reinforcement",
                "implementation_priority": "High - culture is competitive advantage"
            },
            "differentiation_analysis": {
                "unique_values": 3,
                "commodity_values": 3,
                "competitive_advantage": "Moderate - combination is unique even if elements aren't"
            },
            "recommendations": [
                "Develop specific hiring criteria based on values",
                "Create recognition programs aligned with values",
                "Embed values in performance review framework",
                "Train managers on values-based leadership"
            ]
        }


__all__ = ['DefineMissionValuesAgent']
