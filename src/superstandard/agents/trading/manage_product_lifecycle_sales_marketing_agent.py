"""
ManageProductLifecycleSalesMarketingAgent - APQC 3.0 Agent
3.2.4 Manage Product Lifecycle

APQC Blueprint ID: apqc_3_0_q9r0s1t2
Domain: sales_marketing | Type: analytical

Full compliance with all 8 architectural principles
Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageProductLifecycleSalesMarketingAgentConfig:
    apqc_agent_id: str = "apqc_3_0_q9r0s1t2"
    apqc_category_id: str = "3.0"
    apqc_process_id: str = "3.2.4"
    apqc_process_name: str = "3.2.4 Manage Product Lifecycle"
    agent_id: str = "apqc_3_0_q9r0s1t2"
    agent_name: str = "manage_product_lifecycle_sales_marketing_agent"
    agent_type: str = "analytical"
    domain: str = "sales_marketing"
    version: str = "1.0.0"
    autonomous_level: float = 0.90
    collaboration_mode: str = "orchestrated"
    learning_enabled: bool = True
    self_improvement: bool = True
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class ManageProductLifecycleSalesMarketingAgent(BaseAgent, ProtocolMixin):
    """
    Product Lifecycle Management with S-curve analysis, lifecycle stage detection,
    maturity scoring, and cannibalization analysis.

    Skills: lifecycle_analysis (0.90), s_curve_modeling (0.87), maturity_scoring (0.86), sunset_planning (0.84)

    Business Logic:
    - S-curve growth modeling (Introduction, Growth, Maturity, Decline)
    - Product maturity scoring using sales velocity and market penetration
    - Cannibalization impact analysis for product portfolio
    - Lifecycle stage transition detection
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "3.2.4"

    def __init__(self, config: ManageProductLifecycleSalesMarketingAgentConfig):
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "lifecycle_analysis": 0.90,
            "s_curve_modeling": 0.87,
            "maturity_scoring": 0.86,
            "sunset_planning": 0.84,
        }
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute product lifecycle analysis"""
        try:
            product_sales = input_data.get("product_sales_history", [])
            market_data = input_data.get("market_data", {})
            competitive_landscape = input_data.get("competitive_landscape", {})

            # Perform S-curve analysis
            s_curve_results = self._analyze_s_curve(product_sales)

            # Detect lifecycle stage
            lifecycle_stages = self._detect_lifecycle_stage(product_sales, s_curve_results)

            # Calculate maturity scores
            maturity_scores = self._calculate_maturity_scores(product_sales, market_data)

            # Analyze cannibalization
            cannibalization = self._analyze_cannibalization(product_sales)

            # Generate sunset candidates
            sunset_candidates = self._identify_sunset_candidates(lifecycle_stages, maturity_scores)

            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": {
                    "lifecycle_assessment": lifecycle_stages,
                    "s_curve_analysis": s_curve_results,
                    "maturity_scores": maturity_scores,
                    "cannibalization_analysis": cannibalization,
                    "sunset_candidates": sunset_candidates,
                    "recommendations": self._generate_lifecycle_recommendations(
                        lifecycle_stages, maturity_scores
                    ),
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _analyze_s_curve(self, product_sales: List[Dict]) -> Dict[str, Any]:
        """
        S-curve analysis for product adoption lifecycle.

        S-curve model: y = L / (1 + e^(-k(x - x0)))
        Where: L = max market potential, k = steepness, x0 = midpoint
        """
        product_curves = {}

        for product_id in set(sale.get("product_id") for sale in product_sales):
            sales_data = [s for s in product_sales if s.get("product_id") == product_id]
            sorted_sales = sorted(sales_data, key=lambda x: x.get("date", ""))

            if len(sorted_sales) < 3:
                continue

            cumulative_sales = []
            total = 0
            for sale in sorted_sales:
                total += sale.get("quantity", 0)
                cumulative_sales.append(total)

            # Calculate growth rate
            if len(cumulative_sales) > 1:
                growth_rate = (
                    (cumulative_sales[-1] - cumulative_sales[0]) / cumulative_sales[0]
                    if cumulative_sales[0] > 0
                    else 0
                )

                # Detect inflection point (where growth accelerates/decelerates)
                growth_deltas = [
                    cumulative_sales[i] - cumulative_sales[i - 1]
                    for i in range(1, len(cumulative_sales))
                ]
                max_growth_idx = growth_deltas.index(max(growth_deltas)) if growth_deltas else 0

                product_curves[product_id] = {
                    "cumulative_sales": cumulative_sales,
                    "growth_rate": round(growth_rate, 4),
                    "inflection_point": max_growth_idx,
                    "current_position": (
                        "pre_inflection"
                        if len(cumulative_sales) - 1 < max_growth_idx
                        else "post_inflection"
                    ),
                }

        return product_curves

    def _detect_lifecycle_stage(
        self, product_sales: List[Dict], s_curve_results: Dict
    ) -> Dict[str, Dict]:
        """
        Detect product lifecycle stage based on sales patterns.

        Stages: Introduction, Growth, Maturity, Decline
        """
        lifecycle_stages = {}

        for product_id in set(sale.get("product_id") for sale in product_sales):
            sales_data = [s for s in product_sales if s.get("product_id") == product_id]
            sorted_sales = sorted(sales_data, key=lambda x: x.get("date", ""))

            if len(sorted_sales) < 4:
                lifecycle_stages[product_id] = {"stage": "Introduction", "confidence": 0.9}
                continue

            # Calculate recent growth trend
            recent_sales = sorted_sales[-6:] if len(sorted_sales) >= 6 else sorted_sales
            recent_quantities = [s.get("quantity", 0) for s in recent_sales]

            # Calculate moving average
            avg_recent = sum(recent_quantities) / len(recent_quantities)
            avg_overall = sum(s.get("quantity", 0) for s in sorted_sales) / len(sorted_sales)

            # Growth rate calculation
            if len(recent_quantities) >= 2:
                recent_growth = (
                    (recent_quantities[-1] - recent_quantities[0]) / recent_quantities[0]
                    if recent_quantities[0] > 0
                    else 0
                )
            else:
                recent_growth = 0

            # Stage determination logic
            if recent_growth > 0.3 and avg_recent > avg_overall:
                stage = "Growth"
                confidence = 0.85
            elif abs(recent_growth) < 0.1 and avg_recent >= avg_overall * 0.9:
                stage = "Maturity"
                confidence = 0.8
            elif recent_growth < -0.2:
                stage = "Decline"
                confidence = 0.9
            else:
                stage = "Introduction"
                confidence = 0.75

            lifecycle_stages[product_id] = {
                "stage": stage,
                "confidence": confidence,
                "recent_growth_rate": round(recent_growth, 4),
                "avg_sales_recent": round(avg_recent, 2),
                "avg_sales_overall": round(avg_overall, 2),
            }

        return lifecycle_stages

    def _calculate_maturity_scores(
        self, product_sales: List[Dict], market_data: Dict
    ) -> Dict[str, float]:
        """
        Calculate product maturity scores using sales velocity and market penetration.

        Maturity Score = (Sales Velocity Score * 0.4) + (Market Penetration * 0.3) +
                        (Product Age * 0.3)
        Score range: 0-100 (higher = more mature)
        """
        maturity_scores = {}

        for product_id in set(sale.get("product_id") for sale in product_sales):
            sales_data = [s for s in product_sales if s.get("product_id") == product_id]

            # Sales velocity score (recent vs historical)
            if len(sales_data) >= 4:
                recent_velocity = sum(s.get("quantity", 0) for s in sales_data[-3:]) / 3
                historical_velocity = sum(s.get("quantity", 0) for s in sales_data[:-3]) / max(
                    len(sales_data) - 3, 1
                )
                velocity_ratio = (
                    min(historical_velocity / recent_velocity, 2.0) if recent_velocity > 0 else 2.0
                )
                velocity_score = velocity_ratio * 50  # 0-100 scale
            else:
                velocity_score = 25  # Low maturity for new products

            # Market penetration score
            total_market_size = market_data.get("total_addressable_market", 1000000)
            product_sales_total = sum(s.get("quantity", 0) for s in sales_data)
            penetration = (
                (product_sales_total / total_market_size) * 100 if total_market_size > 0 else 0
            )
            penetration_score = min(penetration * 10, 100)  # Cap at 100

            # Product age score (older = more mature)
            if sales_data:
                first_sale_date = min(s.get("date", datetime.now().isoformat()) for s in sales_data)
                if isinstance(first_sale_date, str):
                    first_sale_date = datetime.fromisoformat(first_sale_date)
                product_age_months = max((datetime.now() - first_sale_date).days / 30, 0)
                age_score = min(product_age_months * 2, 100)  # Cap at 100 after 50 months
            else:
                age_score = 0

            # Calculate composite maturity score
            maturity_score = (velocity_score * 0.4) + (penetration_score * 0.3) + (age_score * 0.3)
            maturity_scores[product_id] = round(maturity_score, 2)

        return maturity_scores

    def _analyze_cannibalization(self, product_sales: List[Dict]) -> Dict[str, Any]:
        """
        Analyze cannibalization effects between products in portfolio.

        Cannibalization occurs when new product sales correlate negatively with
        existing product sales decline.
        """
        cannibalization_analysis = {}
        product_ids = list(set(sale.get("product_id") for sale in product_sales))

        for i, product_a in enumerate(product_ids):
            for product_b in product_ids[i + 1 :]:
                sales_a = sorted(
                    [s for s in product_sales if s.get("product_id") == product_a],
                    key=lambda x: x.get("date", ""),
                )
                sales_b = sorted(
                    [s for s in product_sales if s.get("product_id") == product_b],
                    key=lambda x: x.get("date", ""),
                )

                if len(sales_a) < 3 or len(sales_b) < 3:
                    continue

                # Calculate correlation between product sales
                quantities_a = [s.get("quantity", 0) for s in sales_a[-6:]]
                quantities_b = [s.get("quantity", 0) for s in sales_b[-6:]]

                min_len = min(len(quantities_a), len(quantities_b))
                if min_len < 2:
                    continue

                quantities_a = quantities_a[-min_len:]
                quantities_b = quantities_b[-min_len:]

                # Simple correlation coefficient
                correlation = np.corrcoef(quantities_a, quantities_b)[0, 1] if min_len > 1 else 0

                # Negative correlation suggests cannibalization
                if correlation < -0.3:
                    pair_key = f"{product_a}_vs_{product_b}"
                    cannibalization_analysis[pair_key] = {
                        "product_a": product_a,
                        "product_b": product_b,
                        "correlation": round(correlation, 3),
                        "cannibalization_risk": "high" if correlation < -0.6 else "medium",
                        "recommendation": "Consider product differentiation or phased discontinuation",
                    }

        return cannibalization_analysis

    def _identify_sunset_candidates(
        self, lifecycle_stages: Dict, maturity_scores: Dict
    ) -> List[Dict]:
        """Identify products that are candidates for sunset/discontinuation"""
        sunset_candidates = []

        for product_id, stage_info in lifecycle_stages.items():
            maturity = maturity_scores.get(product_id, 0)

            # Criteria for sunset: Decline stage + high maturity + low growth
            if (
                stage_info["stage"] == "Decline"
                and maturity > 70
                and stage_info["recent_growth_rate"] < -0.15
            ):

                sunset_candidates.append(
                    {
                        "product_id": product_id,
                        "lifecycle_stage": stage_info["stage"],
                        "maturity_score": maturity,
                        "growth_rate": stage_info["recent_growth_rate"],
                        "sunset_priority": "high" if maturity > 85 else "medium",
                        "recommended_action": "Plan phased discontinuation with customer migration strategy",
                    }
                )

        return sunset_candidates

    def _generate_lifecycle_recommendations(
        self, lifecycle_stages: Dict, maturity_scores: Dict
    ) -> List[Dict]:
        """Generate strategic recommendations based on lifecycle analysis"""
        recommendations = []

        for product_id, stage_info in lifecycle_stages.items():
            stage = stage_info["stage"]
            maturity = maturity_scores.get(product_id, 0)

            if stage == "Introduction":
                recommendations.append(
                    {
                        "product_id": product_id,
                        "priority": "high",
                        "actions": [
                            "Invest in market education and awareness campaigns",
                            "Focus on early adopter acquisition",
                            "Gather customer feedback for product refinement",
                        ],
                    }
                )
            elif stage == "Growth":
                recommendations.append(
                    {
                        "product_id": product_id,
                        "priority": "high",
                        "actions": [
                            "Scale production and distribution capacity",
                            "Expand market reach and channel partnerships",
                            "Build brand loyalty programs",
                        ],
                    }
                )
            elif stage == "Maturity":
                recommendations.append(
                    {
                        "product_id": product_id,
                        "priority": "medium",
                        "actions": [
                            "Optimize pricing for market share retention",
                            "Introduce product variations and upgrades",
                            "Focus on operational efficiency and cost reduction",
                        ],
                    }
                )
            elif stage == "Decline":
                recommendations.append(
                    {
                        "product_id": product_id,
                        "priority": "high",
                        "actions": [
                            "Evaluate sunset timeline and replacement products",
                            "Develop customer migration strategy",
                            "Maximize profitability through cost controls",
                        ],
                    }
                )

        return recommendations

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "status": self.state["status"],
            "version": self.VERSION,
            "compliance": {
                "standardized": True,
                "interoperable": True,
                "redeployable": True,
                "reusable": True,
                "atomic": True,
                "composable": True,
                "orchestratable": True,
                "vendor_agnostic": True,
            },
        }

    def log(self, level: str, message: str):
        print(
            f"[{datetime.now().isoformat()}] [{level.upper()}] [{self.config.agent_name}] {message}"
        )


def create_manage_product_lifecycle_sales_marketing_agent(
    config: Optional[ManageProductLifecycleSalesMarketingAgentConfig] = None,
):
    if config is None:
        config = ManageProductLifecycleSalesMarketingAgentConfig()
    return ManageProductLifecycleSalesMarketingAgent(config)
