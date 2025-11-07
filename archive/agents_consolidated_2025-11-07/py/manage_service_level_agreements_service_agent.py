"""
ManageServiceLevelAgreementsServiceAgent - APQC 5.3.2
Manage Service Level Agreements and Performance Compliance
APQC ID: apqc_5_3_s1l2a3m4

This agent monitors SLA compliance for ride-sharing services, predicts potential breaches,
tracks performance metrics, and generates remediation plans for service recovery.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class ManageServiceLevelAgreementsServiceAgentConfig:
    apqc_agent_id: str = "apqc_5_3_s1l2a3m4"
    apqc_process_id: str = "5.3.2"
    agent_name: str = "manage_service_level_agreements_service_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageServiceLevelAgreementsServiceAgent(BaseAgent, ProtocolMixin):
    """
    APQC 5.3.2 - Manage Service Level Agreements

    Skills:
    - sla_monitoring: 0.92 (real-time SLA compliance tracking)
    - breach_prediction: 0.89 (predictive breach detection)
    - remediation_planning: 0.87 (automated recovery plans)
    - compliance_tracking: 0.85 (historical compliance analysis)

    Use Cases:
    - Monitor pickup time SLAs
    - Track customer satisfaction commitments
    - Predict and prevent SLA breaches
    - Generate compliance reports
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "5.3.2"

    def __init__(self, config: ManageServiceLevelAgreementsServiceAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "sla_monitoring": 0.92,
            "breach_prediction": 0.89,
            "remediation_planning": 0.87,
            "compliance_tracking": 0.85,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor and manage SLA compliance

        Input:
        {
            "sla_definitions": {
                "pickup_time_minutes": {"target": 5, "threshold": 7, "weight": 0.40},
                "completion_rate": {"target": 0.98, "threshold": 0.95, "weight": 0.30},
                "customer_rating": {"target": 4.5, "threshold": 4.0, "weight": 0.30}
            },
            "current_metrics": {
                "average_pickup_time": 6.2,
                "completion_rate": 0.96,
                "average_customer_rating": 4.3,
                "total_rides": 1500,
                "period_hours": 24
            },
            "historical_data": [
                {"hour": 0, "pickup_time": 4.5, "completion_rate": 0.98, "rating": 4.6},
                {"hour": 1, "pickup_time": 5.2, "completion_rate": 0.97, "rating": 4.5}
            ]
        }
        """
        sla_definitions = input_data.get("sla_definitions", {})
        current_metrics = input_data.get("current_metrics", {})
        historical_data = input_data.get("historical_data", [])

        # Monitor SLA compliance
        compliance_status = self._monitor_sla_compliance(sla_definitions, current_metrics)

        # Predict potential breaches
        breach_predictions = self._predict_sla_breaches(
            sla_definitions, historical_data, current_metrics
        )

        # Generate remediation plans for issues
        remediation_plans = self._generate_remediation_plans(compliance_status, breach_predictions)

        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(compliance_status, sla_definitions)

        # Generate escalations
        escalations = self._generate_escalations(compliance_status, breach_predictions)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "compliance_status": compliance_status,
                "breach_predictions": breach_predictions,
                "remediation_plans": remediation_plans,
                "compliance_score": compliance_score,
                "escalations": escalations,
                "summary": {
                    "overall_status": compliance_score["status"],
                    "compliance_percentage": compliance_score["overall_percentage"],
                    "slas_at_risk": len(
                        [b for b in breach_predictions if b["risk_level"] in ["high", "critical"]]
                    ),
                    "remediation_actions_required": len(remediation_plans),
                },
            },
        }

    def _monitor_sla_compliance(
        self, sla_definitions: Dict[str, Dict], current_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Monitor current SLA compliance status
        """
        compliance_results = []

        for sla_name, sla_config in sla_definitions.items():
            target = sla_config.get("target")
            threshold = sla_config.get("threshold")
            weight = sla_config.get("weight", 1.0)

            # Get current metric value
            metric_key = sla_name
            if sla_name == "pickup_time_minutes":
                current_value = current_metrics.get("average_pickup_time", 0)
                is_inverse = True  # Lower is better
            elif sla_name == "completion_rate":
                current_value = current_metrics.get("completion_rate", 0)
                is_inverse = False  # Higher is better
            elif sla_name == "customer_rating":
                current_value = current_metrics.get("average_customer_rating", 0)
                is_inverse = False  # Higher is better
            else:
                current_value = current_metrics.get(sla_name, 0)
                is_inverse = False

            # Determine compliance status
            if is_inverse:
                # For metrics where lower is better (e.g., pickup time)
                if current_value <= target:
                    status = "compliant"
                    health = "healthy"
                elif current_value <= threshold:
                    status = "warning"
                    health = "at_risk"
                else:
                    status = "breach"
                    health = "critical"

                performance_percentage = (
                    (target / current_value * 100) if current_value > 0 else 100
                )
            else:
                # For metrics where higher is better (e.g., rating, completion rate)
                if current_value >= target:
                    status = "compliant"
                    health = "healthy"
                elif current_value >= threshold:
                    status = "warning"
                    health = "at_risk"
                else:
                    status = "breach"
                    health = "critical"

                performance_percentage = (current_value / target * 100) if target > 0 else 0

            # Calculate deviation
            deviation = abs(current_value - target)
            deviation_percentage = (deviation / target * 100) if target > 0 else 0

            compliance_results.append(
                {
                    "sla_name": sla_name,
                    "target": target,
                    "threshold": threshold,
                    "current_value": round(current_value, 2),
                    "status": status,
                    "health": health,
                    "weight": weight,
                    "performance_percentage": round(performance_percentage, 1),
                    "deviation": round(deviation, 2),
                    "deviation_percentage": round(deviation_percentage, 1),
                    "is_inverse_metric": is_inverse,
                }
            )

        return compliance_results

    def _predict_sla_breaches(
        self, sla_definitions: Dict[str, Dict], historical_data: List[Dict], current_metrics: Dict
    ) -> List[Dict[str, Any]]:
        """
        Predict potential SLA breaches using trend analysis
        """
        predictions = []

        if not historical_data or len(historical_data) < 3:
            # Not enough data for prediction
            for sla_name in sla_definitions.keys():
                predictions.append(
                    {
                        "sla_name": sla_name,
                        "risk_level": "unknown",
                        "prediction": "insufficient_data",
                        "confidence": 0.0,
                    }
                )
            return predictions

        # Analyze trends for each SLA metric
        for sla_name, sla_config in sla_definitions.items():
            target = sla_config.get("target")
            threshold = sla_config.get("threshold")

            # Extract metric values from historical data
            metric_key_map = {
                "pickup_time_minutes": "pickup_time",
                "completion_rate": "completion_rate",
                "customer_rating": "rating",
            }

            metric_key = metric_key_map.get(sla_name, sla_name)
            values = [h.get(metric_key, 0) for h in historical_data if metric_key in h]

            if not values or len(values) < 3:
                predictions.append(
                    {
                        "sla_name": sla_name,
                        "risk_level": "unknown",
                        "prediction": "insufficient_data",
                        "confidence": 0.0,
                    }
                )
                continue

            # Calculate trend (simple linear regression)
            x = np.arange(len(values))
            y = np.array(values)

            if len(x) > 1:
                slope, intercept = np.polyfit(x, y, 1)

                # Predict next period value
                next_value = slope * len(values) + intercept

                # Calculate trend strength
                correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
                trend_strength = abs(correlation)

                # Determine risk level
                is_inverse = sla_name == "pickup_time_minutes"

                if is_inverse:
                    # Lower is better - increasing trend is bad
                    if slope > 0:  # Worsening trend
                        if next_value > threshold:
                            risk_level = "critical"
                        elif next_value > target:
                            risk_level = "high"
                        else:
                            risk_level = "medium"
                    else:
                        risk_level = "low"
                else:
                    # Higher is better - decreasing trend is bad
                    if slope < 0:  # Worsening trend
                        if next_value < threshold:
                            risk_level = "critical"
                        elif next_value < target:
                            risk_level = "high"
                        else:
                            risk_level = "medium"
                    else:
                        risk_level = "low"

                # Calculate time to breach
                if is_inverse:
                    periods_to_breach = (
                        ((threshold - values[-1]) / slope) if slope > 0 else float("inf")
                    )
                else:
                    periods_to_breach = (
                        ((values[-1] - threshold) / abs(slope)) if slope < 0 else float("inf")
                    )

                periods_to_breach = max(0, periods_to_breach)

                predictions.append(
                    {
                        "sla_name": sla_name,
                        "current_value": round(values[-1], 2),
                        "predicted_next_value": round(next_value, 2),
                        "trend_slope": round(slope, 4),
                        "risk_level": risk_level,
                        "trend_strength": round(trend_strength, 2),
                        "periods_to_breach": (
                            round(periods_to_breach, 1)
                            if periods_to_breach != float("inf")
                            else None
                        ),
                        "confidence": round(
                            trend_strength * 0.8, 2
                        ),  # Confidence based on trend strength
                    }
                )

        return predictions

    def _generate_remediation_plans(
        self, compliance_status: List[Dict], breach_predictions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate remediation plans for SLA issues
        """
        remediation_plans = []

        # Create plans for current breaches
        for sla in compliance_status:
            if sla["status"] in ["breach", "warning"]:
                plan = self._create_remediation_plan(sla, "current_issue")
                remediation_plans.append(plan)

        # Create preventive plans for predicted breaches
        for prediction in breach_predictions:
            if prediction.get("risk_level") in ["high", "critical"]:
                # Find corresponding SLA
                sla = next(
                    (s for s in compliance_status if s["sla_name"] == prediction["sla_name"]), None
                )
                if sla:
                    plan = self._create_remediation_plan(sla, "predicted_breach", prediction)
                    remediation_plans.append(plan)

        return remediation_plans

    def _create_remediation_plan(
        self, sla: Dict, issue_type: str, prediction: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create specific remediation plan for an SLA issue
        """
        sla_name = sla["sla_name"]

        # Define remediation actions based on SLA type
        action_templates = {
            "pickup_time_minutes": [
                {
                    "action": "Increase driver incentives in high-demand zones",
                    "priority": "high",
                    "estimated_impact": "15-20% improvement",
                    "implementation_time": "1 hour",
                },
                {
                    "action": "Activate surge pricing to reduce demand",
                    "priority": "high",
                    "estimated_impact": "10-15% improvement",
                    "implementation_time": "15 minutes",
                },
                {
                    "action": "Optimize driver positioning algorithms",
                    "priority": "medium",
                    "estimated_impact": "5-10% improvement",
                    "implementation_time": "2 hours",
                },
            ],
            "completion_rate": [
                {
                    "action": "Review and address driver cancellation patterns",
                    "priority": "high",
                    "estimated_impact": "2-3% improvement",
                    "implementation_time": "4 hours",
                },
                {
                    "action": "Implement rider verification improvements",
                    "priority": "medium",
                    "estimated_impact": "1-2% improvement",
                    "implementation_time": "1 day",
                },
                {
                    "action": "Adjust matching algorithm to improve acceptance rates",
                    "priority": "medium",
                    "estimated_impact": "1-2% improvement",
                    "implementation_time": "6 hours",
                },
            ],
            "customer_rating": [
                {
                    "action": "Launch driver quality training program",
                    "priority": "high",
                    "estimated_impact": "0.2-0.3 point improvement",
                    "implementation_time": "1 week",
                },
                {
                    "action": "Implement real-time driver coaching alerts",
                    "priority": "medium",
                    "estimated_impact": "0.1-0.2 point improvement",
                    "implementation_time": "2 days",
                },
                {
                    "action": "Review and improve vehicle quality standards",
                    "priority": "medium",
                    "estimated_impact": "0.1 point improvement",
                    "implementation_time": "1 week",
                },
            ],
        }

        actions = action_templates.get(
            sla_name,
            [
                {
                    "action": "Investigate root cause and implement corrective measures",
                    "priority": "high",
                    "estimated_impact": "TBD",
                    "implementation_time": "TBD",
                }
            ],
        )

        plan = {
            "sla_name": sla_name,
            "issue_type": issue_type,
            "severity": sla.get("health", "unknown"),
            "current_performance": sla.get("current_value"),
            "target": sla.get("target"),
            "gap": sla.get("deviation"),
            "actions": actions,
            "total_actions": len(actions),
            "estimated_resolution_time": self._estimate_resolution_time(actions),
        }

        if prediction:
            plan["predicted_breach_in"] = prediction.get("periods_to_breach")
            plan["prediction_confidence"] = prediction.get("confidence")

        return plan

    def _estimate_resolution_time(self, actions: List[Dict]) -> str:
        """
        Estimate total resolution time based on actions
        """
        time_map = {
            "15 minutes": 0.25,
            "1 hour": 1,
            "2 hours": 2,
            "4 hours": 4,
            "6 hours": 6,
            "1 day": 24,
            "2 days": 48,
            "1 week": 168,
        }

        total_hours = sum(time_map.get(a.get("implementation_time", "1 hour"), 1) for a in actions)

        if total_hours < 1:
            return f"{int(total_hours * 60)} minutes"
        elif total_hours < 24:
            return f"{int(total_hours)} hours"
        else:
            return f"{int(total_hours / 24)} days"

    def _calculate_compliance_score(
        self, compliance_status: List[Dict], sla_definitions: Dict
    ) -> Dict[str, Any]:
        """
        Calculate overall SLA compliance score
        """
        if not compliance_status:
            return {
                "overall_percentage": 0,
                "weighted_score": 0,
                "status": "unknown",
                "slas_met": 0,
                "slas_total": 0,
            }

        total_weight = sum(
            sla_definitions[s["sla_name"]].get("weight", 1.0) for s in compliance_status
        )
        weighted_sum = 0

        slas_met = 0
        slas_at_risk = 0
        slas_breached = 0

        for sla in compliance_status:
            weight = sla.get("weight", 1.0)

            # Score based on status
            if sla["status"] == "compliant":
                score = 100
                slas_met += 1
            elif sla["status"] == "warning":
                score = 70
                slas_at_risk += 1
            else:  # breach
                score = 30
                slas_breached += 1

            weighted_sum += score * weight

        overall_percentage = (weighted_sum / (total_weight * 100) * 100) if total_weight > 0 else 0

        # Determine overall status
        if overall_percentage >= 95:
            status = "excellent"
        elif overall_percentage >= 85:
            status = "good"
        elif overall_percentage >= 70:
            status = "fair"
        else:
            status = "poor"

        return {
            "overall_percentage": round(overall_percentage, 1),
            "weighted_score": round(weighted_sum / total_weight, 1) if total_weight > 0 else 0,
            "status": status,
            "slas_met": slas_met,
            "slas_at_risk": slas_at_risk,
            "slas_breached": slas_breached,
            "slas_total": len(compliance_status),
        }

    def _generate_escalations(
        self, compliance_status: List[Dict], breach_predictions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate escalations for critical issues
        """
        escalations = []

        # Escalate current breaches
        for sla in compliance_status:
            if sla["status"] == "breach":
                escalations.append(
                    {
                        "type": "sla_breach",
                        "sla_name": sla["sla_name"],
                        "severity": "critical",
                        "current_value": sla["current_value"],
                        "target": sla["target"],
                        "deviation_percentage": sla["deviation_percentage"],
                        "escalation_level": "immediate",
                        "notify": [
                            "operations_manager",
                            "service_quality_team",
                            "executive_dashboard",
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Escalate high-risk predictions
        for prediction in breach_predictions:
            if prediction.get("risk_level") == "critical":
                escalations.append(
                    {
                        "type": "breach_prediction",
                        "sla_name": prediction["sla_name"],
                        "severity": "high",
                        "predicted_breach_in": prediction.get("periods_to_breach"),
                        "confidence": prediction.get("confidence"),
                        "escalation_level": "proactive",
                        "notify": ["operations_manager", "service_quality_team"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return escalations

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for SLA management"""
        return {
            "type": "object",
            "required": ["sla_definitions", "current_metrics"],
            "properties": {
                "sla_definitions": {"type": "object", "description": "SLA targets and thresholds"},
                "current_metrics": {"type": "object", "description": "Current performance metrics"},
                "historical_data": {
                    "type": "array",
                    "description": "Historical performance data for trend analysis",
                },
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "compliance_status": {"type": "array"},
                "breach_predictions": {"type": "array"},
                "remediation_plans": {"type": "array"},
                "compliance_score": {"type": "object"},
                "escalations": {"type": "array"},
            },
        }


def create_manage_service_level_agreements_service_agent() -> (
    ManageServiceLevelAgreementsServiceAgent
):
    """Factory function to create ManageServiceLevelAgreementsServiceAgent"""
    config = ManageServiceLevelAgreementsServiceAgentConfig()
    return ManageServiceLevelAgreementsServiceAgent(config)
