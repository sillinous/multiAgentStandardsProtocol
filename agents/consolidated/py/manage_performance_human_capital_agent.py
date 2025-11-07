"""
ManagePerformanceHumanCapitalAgent - APQC 7.0
7.4.2 Manage Performance
APQC ID: apqc_7_0_m4n5o6p7
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManagePerformanceHumanCapitalAgentConfig:
    apqc_agent_id: str = "apqc_7_0_m4n5o6p7"
    apqc_process_id: str = "7.4.2"
    agent_name: str = "manage_performance_human_capital_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManagePerformanceHumanCapitalAgent(BaseAgent, ProtocolMixin):
    """
    Skills: kpi_tracking: 0.9, performance_scoring: 0.88, feedback_analysis: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "7.4.2"

    def __init__(self, config: ManagePerformanceHumanCapitalAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {"kpi_tracking": 0.9, "performance_scoring": 0.88, "feedback_analysis": 0.85}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage performance with KPI tracking, scoring, and feedback analysis
        """
        employee_metrics = input_data.get("employee_metrics", {})
        kpi_targets = input_data.get("kpi_targets", {})
        feedback_data = input_data.get("feedback_data", [])
        performance_period = input_data.get("performance_period", "Q4 2025")

        # Performance Scoring
        performance_scores = self._calculate_performance_scores(employee_metrics, kpi_targets)

        # KPI Achievement Analysis
        kpi_analysis = self._analyze_kpi_achievement(employee_metrics, kpi_targets)

        # Trend Analysis
        trends = self._analyze_performance_trends(employee_metrics)

        # Feedback Analysis
        feedback_summary = self._analyze_feedback(feedback_data)

        # Improvement Areas
        improvement_areas = self._identify_improvement_areas(
            performance_scores, kpi_analysis, feedback_summary
        )

        # Recognition Recommendations
        recognition = self._generate_recognition_recommendations(performance_scores, kpi_analysis)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "performance_report": {
                    "scores": performance_scores,
                    "kpi_achievement": kpi_analysis,
                    "trends": trends,
                    "feedback_summary": feedback_summary,
                    "improvement_areas": improvement_areas,
                    "recognition_recommendations": recognition,
                },
                "metrics": {
                    "overall_performance_score": performance_scores["overall_score"],
                    "kpi_achievement_rate": kpi_analysis["achievement_rate"],
                    "top_performers_count": len(recognition["high_performers"]),
                    "improvement_needed_count": len(improvement_areas["critical"]),
                },
            },
        }

    def _calculate_performance_scores(self, metrics: Dict, targets: Dict) -> Dict[str, Any]:
        """
        Calculate weighted performance scores
        """
        kpi_scores = []
        weights_total = 0

        for kpi_name, target_value in targets.items():
            actual_value = metrics.get(kpi_name, 0)
            weight = targets.get(f"{kpi_name}_weight", 1.0)

            # Calculate achievement percentage
            if target_value > 0:
                achievement_pct = (actual_value / target_value) * 100
            else:
                achievement_pct = 100 if actual_value == target_value else 0

            # Score on 0-100 scale (capped at 150% for overachievement)
            score = min(achievement_pct, 150)

            kpi_scores.append(
                {
                    "kpi": kpi_name,
                    "target": target_value,
                    "actual": actual_value,
                    "achievement_pct": round(achievement_pct, 1),
                    "score": round(score, 1),
                    "weight": weight,
                    "weighted_score": round(score * weight, 1),
                }
            )

            weights_total += weight

        # Calculate overall weighted score
        if weights_total > 0:
            overall_score = sum(kpi["weighted_score"] for kpi in kpi_scores) / weights_total
        else:
            overall_score = 0

        # Determine rating
        if overall_score >= 110:
            rating = "exceptional"
        elif overall_score >= 90:
            rating = "exceeds_expectations"
        elif overall_score >= 70:
            rating = "meets_expectations"
        elif overall_score >= 50:
            rating = "needs_improvement"
        else:
            rating = "unsatisfactory"

        return {
            "overall_score": round(overall_score, 1),
            "rating": rating,
            "kpi_scores": kpi_scores,
            "top_performing_kpis": sorted(
                kpi_scores, key=lambda x: x["achievement_pct"], reverse=True
            )[:3],
            "underperforming_kpis": sorted(kpi_scores, key=lambda x: x["achievement_pct"])[:3],
        }

    def _analyze_kpi_achievement(self, metrics: Dict, targets: Dict) -> Dict[str, Any]:
        """
        Analyze KPI achievement rates
        """
        total_kpis = len(targets)
        achieved_kpis = 0
        exceeded_kpis = 0

        for kpi_name, target_value in targets.items():
            actual_value = metrics.get(kpi_name, 0)

            if actual_value >= target_value:
                achieved_kpis += 1

            if target_value > 0 and actual_value >= target_value * 1.1:  # 110% or more
                exceeded_kpis += 1

        achievement_rate = (achieved_kpis / total_kpis * 100) if total_kpis > 0 else 0
        exceed_rate = (exceeded_kpis / total_kpis * 100) if total_kpis > 0 else 0

        return {
            "total_kpis": total_kpis,
            "achieved_kpis": achieved_kpis,
            "exceeded_kpis": exceeded_kpis,
            "achievement_rate": round(achievement_rate, 1),
            "exceed_rate": round(exceed_rate, 1),
            "status": (
                "excellent"
                if achievement_rate >= 90
                else "good" if achievement_rate >= 70 else "needs_improvement"
            ),
        }

    def _analyze_performance_trends(self, metrics: Dict) -> Dict[str, Any]:
        """
        Analyze performance trends over time
        """
        # Simulate historical data for trend analysis
        current_period = metrics
        previous_period = {k: v * 0.9 for k, v in metrics.items()}  # Simplified: 90% of current

        trends = []

        for metric_name, current_value in current_period.items():
            previous_value = previous_period.get(metric_name, current_value)

            if previous_value > 0:
                change_pct = ((current_value - previous_value) / previous_value) * 100
            else:
                change_pct = 0

            if change_pct > 5:
                trend = "improving"
            elif change_pct < -5:
                trend = "declining"
            else:
                trend = "stable"

            trends.append(
                {
                    "metric": metric_name,
                    "current_value": round(current_value, 2),
                    "previous_value": round(previous_value, 2),
                    "change_pct": round(change_pct, 1),
                    "trend": trend,
                }
            )

        improving_count = len([t for t in trends if t["trend"] == "improving"])
        declining_count = len([t for t in trends if t["trend"] == "declining"])

        return {
            "trends_by_metric": trends,
            "improving_metrics": improving_count,
            "declining_metrics": declining_count,
            "overall_trend": (
                "improving"
                if improving_count > declining_count
                else "declining" if declining_count > improving_count else "stable"
            ),
        }

    def _analyze_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze feedback data
        """
        if not feedback_data:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "sentiment": "neutral",
                "key_themes": [],
            }

        ratings = [fb.get("rating", 3) for fb in feedback_data]
        average_rating = np.mean(ratings)

        # Sentiment analysis (simplified)
        if average_rating >= 4:
            sentiment = "positive"
        elif average_rating >= 3:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        # Extract themes from comments (simplified keyword extraction)
        comments = [fb.get("comment", "") for fb in feedback_data]
        all_text = " ".join(comments).lower()

        positive_keywords = ["excellent", "great", "outstanding", "good", "strong"]
        improvement_keywords = ["improve", "better", "develop", "enhance", "work on"]

        key_themes = []
        if any(kw in all_text for kw in positive_keywords):
            key_themes.append("Strong performance noted")
        if any(kw in all_text for kw in improvement_keywords):
            key_themes.append("Areas for development identified")

        return {
            "total_feedback": len(feedback_data),
            "average_rating": round(average_rating, 2),
            "rating_distribution": {
                "5_star": len([r for r in ratings if r == 5]),
                "4_star": len([r for r in ratings if r == 4]),
                "3_star": len([r for r in ratings if r == 3]),
                "2_star": len([r for r in ratings if r == 2]),
                "1_star": len([r for r in ratings if r == 1]),
            },
            "sentiment": sentiment,
            "key_themes": key_themes,
        }

    def _identify_improvement_areas(
        self, scores: Dict, kpi_analysis: Dict, feedback: Dict
    ) -> Dict[str, Any]:
        """
        Identify areas needing improvement
        """
        critical = []
        moderate = []

        # Check underperforming KPIs
        for kpi in scores["underperforming_kpis"]:
            if kpi["achievement_pct"] < 70:
                critical.append(
                    {
                        "area": kpi["kpi"],
                        "current_performance": kpi["achievement_pct"],
                        "gap": round(100 - kpi["achievement_pct"], 1),
                        "priority": "high",
                    }
                )
            elif kpi["achievement_pct"] < 90:
                moderate.append(
                    {
                        "area": kpi["kpi"],
                        "current_performance": kpi["achievement_pct"],
                        "gap": round(100 - kpi["achievement_pct"], 1),
                        "priority": "medium",
                    }
                )

        # Check feedback sentiment
        if feedback["sentiment"] == "negative":
            critical.append(
                {
                    "area": "Stakeholder satisfaction",
                    "current_performance": feedback["average_rating"] * 20,  # Convert to percentage
                    "gap": round(100 - (feedback["average_rating"] * 20), 1),
                    "priority": "high",
                }
            )

        return {
            "critical": critical,
            "moderate": moderate,
            "action_required": len(critical) > 0,
            "development_plan_needed": len(critical) + len(moderate) > 0,
        }

    def _generate_recognition_recommendations(
        self, scores: Dict, kpi_analysis: Dict
    ) -> Dict[str, Any]:
        """
        Generate recognition recommendations
        """
        high_performers = []
        recognition_actions = []

        # Check for exceptional performance
        if scores["rating"] in ["exceptional", "exceeds_expectations"]:
            high_performers.append(
                {
                    "reason": "Overall exceptional performance",
                    "score": scores["overall_score"],
                    "rating": scores["rating"],
                }
            )

        # Check for exceeded KPIs
        if kpi_analysis["exceeded_kpis"] >= 3:
            recognition_actions.append(
                {
                    "type": "achievement_award",
                    "reason": f"Exceeded {kpi_analysis['exceeded_kpis']} KPI targets",
                    "recommendation": "Formal recognition and bonus consideration",
                }
            )

        # Check top performing KPIs
        for kpi in scores["top_performing_kpis"]:
            if kpi["achievement_pct"] >= 120:
                recognition_actions.append(
                    {
                        "type": "kpi_excellence",
                        "reason": f"Outstanding achievement in {kpi['kpi']}",
                        "recommendation": "Public recognition in team meeting",
                    }
                )

        return {
            "high_performers": high_performers,
            "recognition_actions": recognition_actions[:3],  # Top 3
            "recognition_warranted": len(recognition_actions) > 0,
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_manage_performance_human_capital_agent(
    config: Optional[ManagePerformanceHumanCapitalAgentConfig] = None,
):
    if config is None:
        config = ManagePerformanceHumanCapitalAgentConfig()
    return ManagePerformanceHumanCapitalAgent(config)
