"""
ManageSupplierRelationshipsOperationalAgent - APQC 4.0
4.2.2 Manage Supplier Relationships
APQC ID: apqc_4_0_h9i0j1k2
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageSupplierRelationshipsOperationalAgentConfig:
    apqc_agent_id: str = "apqc_4_0_h9i0j1k2"
    apqc_process_id: str = "4.2.2"
    agent_name: str = "manage_supplier_relationships_operational_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageSupplierRelationshipsOperationalAgent(BaseAgent, ProtocolMixin):
    """
    Skills: supplier_scoring: 0.9, performance_tracking: 0.88, relationship_analytics: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.2.2"

    def __init__(self, config: ManageSupplierRelationshipsOperationalAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'supplier_scoring': 0.9, 'performance_tracking': 0.88, 'relationship_analytics': 0.85}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage supplier relationships with scorecard and performance tracking
        """
        supplier_data = input_data.get('supplier_data', [])
        delivery_performance = input_data.get('delivery_performance', {})
        quality_metrics = input_data.get('quality_metrics', {})

        # Supplier Scorecard
        scorecard = self._create_supplier_scorecard(supplier_data, delivery_performance, quality_metrics)

        # Performance Tracking
        performance = self._track_supplier_performance(supplier_data, delivery_performance, quality_metrics)

        # Risk Assessment
        risk_assessment = self._assess_supplier_risk(scorecard, performance)

        # Improvement Recommendations
        improvements = self._generate_improvement_recommendations(scorecard, risk_assessment)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "supplier_evaluation": {
                    "scorecard": scorecard,
                    "performance_summary": performance,
                    "risk_assessment": risk_assessment,
                    "improvement_areas": improvements
                },
                "metrics": {
                    "average_supplier_score": scorecard['average_score'],
                    "top_performers_count": len(scorecard['top_performers']),
                    "at_risk_suppliers": len(risk_assessment['high_risk_suppliers'])
                }
            }
        }

    def _create_supplier_scorecard(self, suppliers: List[Dict], delivery: Dict, quality: Dict) -> Dict[str, Any]:
        """Create supplier scorecard with weighted scoring"""
        scored_suppliers = []

        for supplier in suppliers:
            supplier_id = supplier.get('supplier_id')
            supplier_name = supplier.get('name', 'Unknown')

            # Scoring criteria (weights sum to 100)
            delivery_score = delivery.get(supplier_id, {}).get('on_time_rate', 80) # 40% weight
            quality_score = quality.get(supplier_id, {}).get('quality_rate', 90)  # 30% weight
            cost_competitiveness = supplier.get('cost_score', 75)  # 20% weight
            responsiveness = supplier.get('responsiveness_score', 80)  # 10% weight

            # Calculate weighted total score
            total_score = (
                delivery_score * 0.40 +
                quality_score * 0.30 +
                cost_competitiveness * 0.20 +
                responsiveness * 0.10
            )

            # Determine tier
            if total_score >= 90:
                tier = "strategic"
            elif total_score >= 75:
                tier = "preferred"
            elif total_score >= 60:
                tier = "approved"
            else:
                tier = "conditional"

            scored_suppliers.append({
                "supplier_id": supplier_id,
                "name": supplier_name,
                "scores": {
                    "delivery": round(delivery_score, 1),
                    "quality": round(quality_score, 1),
                    "cost": round(cost_competitiveness, 1),
                    "responsiveness": round(responsiveness, 1)
                },
                "total_score": round(total_score, 1),
                "tier": tier,
                "ranking": 0  # Will be set after sorting
            })

        # Sort by score and assign rankings
        scored_suppliers.sort(key=lambda x: x['total_score'], reverse=True)
        for idx, supplier in enumerate(scored_suppliers):
            supplier['ranking'] = idx + 1

        average_score = np.mean([s['total_score'] for s in scored_suppliers]) if scored_suppliers else 0

        return {
            "suppliers": scored_suppliers,
            "average_score": round(average_score, 1),
            "top_performers": [s for s in scored_suppliers if s['tier'] in ['strategic', 'preferred']],
            "underperformers": [s for s in scored_suppliers if s['tier'] == 'conditional'],
            "tier_distribution": {
                "strategic": len([s for s in scored_suppliers if s['tier'] == 'strategic']),
                "preferred": len([s for s in scored_suppliers if s['tier'] == 'preferred']),
                "approved": len([s for s in scored_suppliers if s['tier'] == 'approved']),
                "conditional": len([s for s in scored_suppliers if s['tier'] == 'conditional'])
            }
        }

    def _track_supplier_performance(self, suppliers: List[Dict], delivery: Dict, quality: Dict) -> Dict[str, Any]:
        """Track supplier performance metrics"""
        performance_summary = {
            "overall_on_time_delivery": 0,
            "overall_quality_rate": 0,
            "total_suppliers": len(suppliers),
            "performance_trends": []
        }

        if not suppliers:
            return performance_summary

        on_time_rates = []
        quality_rates = []

        for supplier in suppliers:
            supplier_id = supplier.get('supplier_id')
            on_time = delivery.get(supplier_id, {}).get('on_time_rate', 0)
            quality_rate = quality.get(supplier_id, {}).get('quality_rate', 0)

            on_time_rates.append(on_time)
            quality_rates.append(quality_rate)

        performance_summary['overall_on_time_delivery'] = round(np.mean(on_time_rates), 1) if on_time_rates else 0
        performance_summary['overall_quality_rate'] = round(np.mean(quality_rates), 1) if quality_rates else 0

        # Identify trends (simplified)
        performance_summary['performance_trends'] = [
            {
                "metric": "On-Time Delivery",
                "value": performance_summary['overall_on_time_delivery'],
                "trend": "improving" if performance_summary['overall_on_time_delivery'] > 85 else "declining",
                "target": 95
            },
            {
                "metric": "Quality Rate",
                "value": performance_summary['overall_quality_rate'],
                "trend": "stable",
                "target": 98
            }
        ]

        return performance_summary

    def _assess_supplier_risk(self, scorecard: Dict, performance: Dict) -> Dict[str, Any]:
        """Assess supplier risk levels"""
        high_risk = []
        medium_risk = []
        low_risk = []

        for supplier in scorecard['suppliers']:
            score = supplier['total_score']
            tier = supplier['tier']

            # Risk factors
            risk_score = 0

            if score < 60:
                risk_score += 40
            elif score < 75:
                risk_score += 20

            if supplier['scores']['delivery'] < 85:
                risk_score += 20

            if supplier['scores']['quality'] < 90:
                risk_score += 15

            if tier == 'conditional':
                risk_score += 25

            # Classify risk
            if risk_score >= 60:
                high_risk.append(supplier['name'])
            elif risk_score >= 30:
                medium_risk.append(supplier['name'])
            else:
                low_risk.append(supplier['name'])

        return {
            "high_risk_suppliers": high_risk,
            "medium_risk_suppliers": medium_risk,
            "low_risk_suppliers": low_risk,
            "risk_summary": {
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "low_risk_count": len(low_risk)
            }
        }

    def _generate_improvement_recommendations(self, scorecard: Dict, risk: Dict) -> List[Dict]:
        """Generate supplier improvement recommendations"""
        recommendations = []

        # For underperformers
        for supplier in scorecard['underperformers']:
            recommendations.append({
                "supplier": supplier['name'],
                "priority": "high",
                "action": "Performance improvement plan required",
                "focus_areas": [
                    area for area, score in supplier['scores'].items()
                    if score < 70
                ],
                "timeline": "90 days"
            })

        # For high-risk suppliers
        for supplier_name in risk['high_risk_suppliers']:
            if supplier_name not in [r['supplier'] for r in recommendations]:
                recommendations.append({
                    "supplier": supplier_name,
                    "priority": "critical",
                    "action": "Risk mitigation and contingency planning",
                    "focus_areas": ["Risk assessment", "Alternative sourcing"],
                    "timeline": "immediate"
                })

        # General recommendations
        if scorecard['average_score'] < 80:
            recommendations.append({
                "supplier": "All Suppliers",
                "priority": "medium",
                "action": "Overall supplier base improvement initiative",
                "focus_areas": ["Performance monitoring", "Communication", "Collaboration"],
                "timeline": "6 months"
            })

        return recommendations

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_manage_supplier_relationships_operational_agent(config: Optional[ManageSupplierRelationshipsOperationalAgentConfig] = None):
    if config is None:
        config = ManageSupplierRelationshipsOperationalAgentConfig()
    return ManageSupplierRelationshipsOperationalAgent(config)
