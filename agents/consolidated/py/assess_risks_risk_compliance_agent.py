"""
AssessRisksRiskComplianceAgent - APQC 10.0
10.2.1 Assess Risks
APQC ID: apqc_10_0_n5o6p7q8
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class AssessRisksRiskComplianceAgentConfig:
    apqc_agent_id: str = "apqc_10_0_n5o6p7q8"
    apqc_process_id: str = "10.2.1"
    agent_name: str = "assess_risks_risk_compliance_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"


class AssessRisksRiskComplianceAgent(BaseAgent, ProtocolMixin):
    """
    Skills: risk_scoring: 0.92, probability_analysis: 0.88, impact_assessment: 0.87
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "10.2.1"

    def __init__(self, config: AssessRisksRiskComplianceAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "risk_scoring": 0.92,
            "probability_analysis": 0.88,
            "impact_assessment": 0.87,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risks using probability × impact matrix and prioritization
        """
        risk_events = input_data.get("risk_events", [])
        probability_estimates = input_data.get("probability_estimates", {})
        impact_estimates = input_data.get("impact_estimates", {})
        risk_tolerance = input_data.get("risk_tolerance", "medium")

        # Risk Matrix Calculation
        risk_matrix = self._calculate_risk_matrix(
            risk_events, probability_estimates, impact_estimates
        )

        # Risk Scoring
        risk_scores = self._calculate_risk_scores(risk_matrix)

        # Risk Heat Map
        heat_map = self._generate_risk_heat_map(risk_scores)

        # Priority Classification
        priorities = self._prioritize_risks(risk_scores, risk_tolerance)

        # Mitigation Recommendations
        mitigation_recs = self._generate_mitigation_recommendations(priorities)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "risk_assessment": {
                    "risk_scores": risk_scores,
                    "heat_map": heat_map,
                    "priorities": priorities,
                    "mitigation_recommendations": mitigation_recs,
                },
                "metrics": {
                    "total_risks_identified": len(risk_events),
                    "critical_risks": len(
                        [r for r in risk_scores["risks"] if r["risk_level"] == "critical"]
                    ),
                    "high_risks": len(
                        [r for r in risk_scores["risks"] if r["risk_level"] == "high"]
                    ),
                    "average_risk_score": risk_scores["average_risk_score"],
                },
            },
        }

    def _calculate_risk_matrix(
        self, risk_events: List[Dict], probabilities: Dict, impacts: Dict
    ) -> List[Dict]:
        """
        Calculate risk matrix with probability and impact
        """
        risk_matrix = []

        for risk in risk_events:
            risk_id = risk.get("risk_id")
            risk_name = risk.get("name", "Unknown Risk")
            risk_category = risk.get("category", "General")

            # Get probability (scale 1-5)
            probability = probabilities.get(risk_id, 3)  # Default to medium

            # Get impact (scale 1-5)
            impact = impacts.get(risk_id, 3)  # Default to medium

            risk_matrix.append(
                {
                    "risk_id": risk_id,
                    "name": risk_name,
                    "category": risk_category,
                    "probability": probability,
                    "impact": impact,
                    "probability_label": self._get_probability_label(probability),
                    "impact_label": self._get_impact_label(impact),
                }
            )

        return risk_matrix

    def _get_probability_label(self, score: int) -> str:
        """Convert probability score to label"""
        labels = {1: "rare", 2: "unlikely", 3: "possible", 4: "likely", 5: "almost_certain"}
        return labels.get(score, "possible")

    def _get_impact_label(self, score: int) -> str:
        """Convert impact score to label"""
        labels = {1: "negligible", 2: "minor", 3: "moderate", 4: "major", 5: "catastrophic"}
        return labels.get(score, "moderate")

    def _calculate_risk_scores(self, risk_matrix: List[Dict]) -> Dict[str, Any]:
        """
        Calculate risk scores (Probability × Impact)
        """
        scored_risks = []

        for risk in risk_matrix:
            # Risk Score = Probability × Impact
            risk_score = risk["probability"] * risk["impact"]

            # Determine risk level based on score
            if risk_score >= 20:  # 4×5 or 5×4 or 5×5
                risk_level = "critical"
            elif risk_score >= 12:  # 3×4, 4×3, 4×4, etc.
                risk_level = "high"
            elif risk_score >= 6:  # 2×3, 3×2, 3×3, etc.
                risk_level = "medium"
            else:
                risk_level = "low"

            scored_risks.append({**risk, "risk_score": risk_score, "risk_level": risk_level})

        # Sort by risk score
        scored_risks.sort(key=lambda x: x["risk_score"], reverse=True)

        average_risk_score = np.mean([r["risk_score"] for r in scored_risks]) if scored_risks else 0

        return {
            "risks": scored_risks,
            "average_risk_score": round(average_risk_score, 2),
            "total_risk_exposure": sum(r["risk_score"] for r in scored_risks),
        }

    def _generate_risk_heat_map(self, risk_scores: Dict) -> Dict[str, Any]:
        """
        Generate risk heat map data
        """
        # Create 5x5 matrix
        heat_map_matrix = [[[] for _ in range(5)] for _ in range(5)]

        for risk in risk_scores["risks"]:
            prob_idx = risk["probability"] - 1  # 0-indexed
            impact_idx = risk["impact"] - 1
            heat_map_matrix[prob_idx][impact_idx].append(
                {"risk_id": risk["risk_id"], "name": risk["name"], "risk_score": risk["risk_score"]}
            )

        # Count risks in each quadrant
        quadrants = {
            "critical": 0,  # High probability, high impact
            "high": 0,  # Either high probability or high impact
            "medium": 0,  # Moderate on both
            "low": 0,  # Low on both
        }

        for risk in risk_scores["risks"]:
            quadrants[risk["risk_level"]] += 1

        return {
            "matrix": heat_map_matrix,
            "quadrant_distribution": quadrants,
            "visualization_data": {
                "x_axis": "Impact (1=Negligible to 5=Catastrophic)",
                "y_axis": "Probability (1=Rare to 5=Almost Certain)",
                "color_coding": {
                    "green": "Low risk (1-5)",
                    "yellow": "Medium risk (6-11)",
                    "orange": "High risk (12-19)",
                    "red": "Critical risk (20-25)",
                },
            },
        }

    def _prioritize_risks(self, risk_scores: Dict, risk_tolerance: str) -> Dict[str, Any]:
        """
        Prioritize risks based on scores and tolerance
        """
        critical_risks = []
        high_priority = []
        medium_priority = []
        low_priority = []

        for risk in risk_scores["risks"]:
            risk_level = risk["risk_level"]

            if risk_level == "critical":
                critical_risks.append(risk)
            elif risk_level == "high":
                high_priority.append(risk)
            elif risk_level == "medium":
                medium_priority.append(risk)
            else:
                low_priority.append(risk)

        # Adjust priorities based on risk tolerance
        tolerance_thresholds = {
            "low": {"critical": 15, "high": 10, "medium": 5},
            "medium": {"critical": 20, "high": 12, "medium": 6},
            "high": {"critical": 25, "high": 15, "medium": 8},
        }

        thresholds = tolerance_thresholds.get(risk_tolerance, tolerance_thresholds["medium"])

        return {
            "critical_risks": critical_risks,
            "high_priority_risks": high_priority,
            "medium_priority_risks": medium_priority,
            "low_priority_risks": low_priority,
            "immediate_action_required": len(critical_risks) > 0,
            "risk_tolerance": risk_tolerance,
            "thresholds": thresholds,
            "priority_summary": {
                "critical": len(critical_risks),
                "high": len(high_priority),
                "medium": len(medium_priority),
                "low": len(low_priority),
            },
        }

    def _generate_mitigation_recommendations(self, priorities: Dict) -> List[Dict]:
        """
        Generate risk mitigation recommendations
        """
        recommendations = []

        # Critical risks - immediate action
        for risk in priorities["critical_risks"]:
            recommendations.append(
                {
                    "risk_id": risk["risk_id"],
                    "risk_name": risk["name"],
                    "priority": "critical",
                    "strategy": "mitigate",
                    "actions": [
                        "Develop immediate response plan",
                        "Assign dedicated risk owner",
                        "Implement preventive controls",
                        "Establish monitoring mechanisms",
                        "Escalate to senior management",
                    ],
                    "timeline": "immediate (0-7 days)",
                    "estimated_cost": "high",
                    "expected_reduction": "50-75%",
                }
            )

        # High priority risks
        for risk in priorities["high_priority_risks"][:5]:  # Top 5
            recommendations.append(
                {
                    "risk_id": risk["risk_id"],
                    "risk_name": risk["name"],
                    "priority": "high",
                    "strategy": "mitigate",
                    "actions": [
                        "Develop mitigation plan",
                        "Implement risk controls",
                        "Regular monitoring",
                        "Contingency planning",
                    ],
                    "timeline": "short-term (1-4 weeks)",
                    "estimated_cost": "medium",
                    "expected_reduction": "30-50%",
                }
            )

        # Medium priority risks - accept or mitigate
        for risk in priorities["medium_priority_risks"][:3]:  # Top 3
            recommendations.append(
                {
                    "risk_id": risk["risk_id"],
                    "risk_name": risk["name"],
                    "priority": "medium",
                    "strategy": "monitor_and_review",
                    "actions": ["Regular monitoring", "Periodic review", "Basic controls"],
                    "timeline": "medium-term (1-3 months)",
                    "estimated_cost": "low",
                    "expected_reduction": "10-30%",
                }
            )

        # Low priority risks - accept
        if priorities["low_priority_risks"]:
            recommendations.append(
                {
                    "risk_id": "low_priority_group",
                    "risk_name": f"Group of {len(priorities['low_priority_risks'])} low priority risks",
                    "priority": "low",
                    "strategy": "accept",
                    "actions": ["Routine monitoring", "Annual review"],
                    "timeline": "long-term (ongoing)",
                    "estimated_cost": "minimal",
                    "expected_reduction": "0-10%",
                }
            )

        return recommendations

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_assess_risks_risk_compliance_agent(
    config: Optional[AssessRisksRiskComplianceAgentConfig] = None,
):
    if config is None:
        config = AssessRisksRiskComplianceAgentConfig()
    return AssessRisksRiskComplianceAgent(config)
