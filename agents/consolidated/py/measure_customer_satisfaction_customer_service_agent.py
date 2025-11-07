"""
MeasureCustomerSatisfactionCustomerServiceAgent - APQC 6.0 Agent
6.2.3 Measure Customer Satisfaction

APQC Blueprint ID: apqc_6_0_r0s1t2u3
Skills: nps_calculation (0.92), csat_scoring (0.90), sentiment_analysis (0.88), trend_tracking (0.86)

Business Logic: NPS, CSAT, sentiment aggregation, satisfaction trending
Full compliance with all 8 architectural principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class MeasureCustomerSatisfactionCustomerServiceAgentConfig:
    apqc_agent_id: str = "apqc_6_0_r0s1t2u3"
    apqc_process_id: str = "6.2.3"
    apqc_process_name: str = "6.2.3 Measure Customer Satisfaction"
    agent_id: str = "apqc_6_0_r0s1t2u3"
    agent_name: str = "measure_customer_satisfaction_customer_service_agent"
    agent_type: str = "analytical"
    domain: str = "customer_service"
    version: str = "1.0.0"
    autonomous_level: float = 0.92
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class MeasureCustomerSatisfactionCustomerServiceAgent(BaseAgent, ProtocolMixin):
    """
    Customer Satisfaction Measurement with NPS, CSAT, sentiment analysis.

    NPS Formula: % Promoters (9-10) - % Detractors (0-6)
    CSAT Formula: (Satisfied Responses / Total Responses) * 100
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "6.2.3"

    def __init__(self, config: MeasureCustomerSatisfactionCustomerServiceAgentConfig):
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "nps_calculation": 0.92,
            "csat_scoring": 0.90,
            "sentiment_analysis": 0.88,
            "trend_tracking": 0.86,
        }
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute customer satisfaction measurement"""
        try:
            survey_responses = input_data.get("survey_responses", [])
            feedback_data = input_data.get("feedback_data", [])

            nps_result = self._calculate_nps(survey_responses)
            csat_result = self._calculate_csat(survey_responses)
            sentiment_result = self._analyze_sentiment(feedback_data)
            trends = self._track_satisfaction_trends(survey_responses)
            alerts = self._generate_alerts(nps_result, csat_result, sentiment_result)

            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": {
                    "satisfaction_metrics": {
                        "nps": nps_result,
                        "csat": csat_result,
                        "sentiment_score": sentiment_result,
                        "trends": trends,
                        "alerts": alerts,
                    }
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_nps(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate Net Promoter Score: % Promoters (9-10) - % Detractors (0-6)"""
        nps_responses = [r for r in responses if "nps_score" in r]
        if not nps_responses:
            return {"score": 0, "category": "N/A", "sample_size": 0}

        promoters = sum(1 for r in nps_responses if r["nps_score"] >= 9)
        detractors = sum(1 for r in nps_responses if r["nps_score"] <= 6)
        total = len(nps_responses)
        nps_score = ((promoters - detractors) / total * 100) if total > 0 else 0

        category = (
            "Excellent"
            if nps_score >= 70
            else (
                "Great"
                if nps_score >= 50
                else (
                    "Good"
                    if nps_score >= 30
                    else "Needs Improvement" if nps_score >= 0 else "Critical"
                )
            )
        )

        return {
            "score": round(nps_score, 2),
            "category": category,
            "promoters": promoters,
            "detractors": detractors,
            "sample_size": total,
        }

    def _calculate_csat(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate CSAT: (Satisfied Responses / Total) * 100"""
        csat_responses = [r for r in responses if "satisfaction_rating" in r]
        if not csat_responses:
            return {"score": 0, "category": "N/A"}

        satisfied = sum(1 for r in csat_responses if r["satisfaction_rating"] >= 4)
        total = len(csat_responses)
        csat_score = (satisfied / total * 100) if total > 0 else 0

        return {
            "score": round(csat_score, 2),
            "category": (
                "Excellent"
                if csat_score >= 90
                else "Good" if csat_score >= 75 else "Fair" if csat_score >= 60 else "Poor"
            ),
            "satisfied_count": satisfied,
            "sample_size": total,
        }

    def _analyze_sentiment(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Sentiment analysis using keyword matching"""
        if not feedback_data:
            return {"score": 50, "category": "Neutral"}

        positive_keywords = ["great", "excellent", "good", "love", "best", "amazing"]
        negative_keywords = ["bad", "poor", "worst", "terrible", "hate", "disappointing"]

        scores = []
        for feedback in feedback_data:
            text = feedback.get("text", "").lower()
            pos = sum(1 for word in positive_keywords if word in text)
            neg = sum(1 for word in negative_keywords if word in text)
            scores.append((pos - neg) / (pos + neg) if pos + neg > 0 else 0)

        avg_sentiment = sum(scores) / len(scores) if scores else 0
        sentiment_score = (avg_sentiment + 1) * 50

        return {
            "score": round(sentiment_score, 2),
            "category": (
                "Positive"
                if sentiment_score >= 70
                else "Neutral" if sentiment_score >= 40 else "Negative"
            ),
        }

    def _track_satisfaction_trends(self, responses: List[Dict]) -> Dict[str, Any]:
        """Track trends"""
        if len(responses) < 4:
            return {"trend": "insufficient_data", "change_rate": 0}

        mid = len(responses) // 2
        avg_first = np.mean([r.get("satisfaction_rating", 3) for r in responses[:mid]])
        avg_second = np.mean([r.get("satisfaction_rating", 3) for r in responses[mid:]])
        change_rate = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0

        return {
            "trend": (
                "improving" if change_rate > 5 else "declining" if change_rate < -5 else "stable"
            ),
            "change_rate": round(change_rate, 2),
        }

    def _generate_alerts(self, nps: Dict, csat: Dict, sentiment: Dict) -> List[Dict]:
        """Generate alerts"""
        alerts = []
        if nps["score"] < 0:
            alerts.append({"severity": "critical", "metric": "NPS", "message": "NPS is negative"})
        if csat["score"] < 60:
            alerts.append({"severity": "high", "metric": "CSAT", "message": "CSAT is low"})
        return alerts

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "status": self.state["status"],
            "version": self.VERSION,
        }

    def log(self, level: str, message: str):
        print(
            f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}"
        )


def create_measure_customer_satisfaction_customer_service_agent(
    config: Optional[MeasureCustomerSatisfactionCustomerServiceAgentConfig] = None,
):
    return MeasureCustomerSatisfactionCustomerServiceAgent(
        config or MeasureCustomerSatisfactionCustomerServiceAgentConfig()
    )
