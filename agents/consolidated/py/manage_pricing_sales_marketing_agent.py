"""
ManagePricingSalesMarketingAgent - APQC 3.0
3.3.2 Manage Pricing
APQC ID: apqc_3_0_k2l3m4n5
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManagePricingSalesMarketingAgentConfig:
    apqc_agent_id: str = "apqc_3_0_k2l3m4n5"
    apqc_process_id: str = "3.3.2"
    agent_name: str = "manage_pricing_sales_marketing_agent"
    agent_type: str = "strategic"
    version: str = "1.0.0"


class ManagePricingSalesMarketingAgent(BaseAgent, ProtocolMixin):
    """
    Skills: dynamic_pricing: 0.92, elasticity_analysis: 0.88, optimization: 0.86
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "3.3.2"

    def __init__(self, config: ManagePricingSalesMarketingAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'dynamic_pricing': 0.92, 'elasticity_analysis': 0.88, 'optimization': 0.86}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage pricing with elasticity analysis and margin optimization
        """
        costs = input_data.get('costs', {})
        competitor_prices = input_data.get('competitor_prices', {})
        demand_elasticity = input_data.get('demand_elasticity', -1.5)  # Default elastic
        market_conditions = input_data.get('market_conditions', {})

        # Price Elasticity Analysis
        elasticity_analysis = self._analyze_price_elasticity(demand_elasticity, market_conditions)

        # Competitive Pricing Analysis
        competitive_analysis = self._analyze_competitive_pricing(costs, competitor_prices)

        # Margin Optimization
        optimal_pricing = self._optimize_pricing(costs, elasticity_analysis, competitive_analysis)

        # Volume Impact Analysis
        volume_impact = self._calculate_volume_impact(optimal_pricing, elasticity_analysis)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "pricing_strategy": {
                    "recommended_prices": optimal_pricing['recommendations'],
                    "expected_volume": volume_impact,
                    "margin_impact": optimal_pricing['margin_analysis'],
                    "competitive_position": competitive_analysis
                },
                "metrics": {
                    "optimal_price": optimal_pricing['optimal_price'],
                    "expected_margin": optimal_pricing['expected_margin'],
                    "revenue_projection": optimal_pricing['revenue_projection']
                }
            }
        }

    def _analyze_price_elasticity(self, elasticity: float, market_conditions: Dict) -> Dict[str, Any]:
        """
        Analyze price elasticity of demand
        Price Elasticity = % Change in Quantity / % Change in Price
        """
        # Classify elasticity
        if elasticity < -1:
            elasticity_type = "elastic"
            sensitivity = "high"
            pricing_recommendation = "Lower prices increase revenue"
        elif elasticity > -1 and elasticity < 0:
            elasticity_type = "inelastic"
            sensitivity = "low"
            pricing_recommendation = "Higher prices increase revenue"
        else:
            elasticity_type = "unit_elastic"
            sensitivity = "moderate"
            pricing_recommendation = "Price changes have neutral effect"

        # Calculate price change impact
        price_changes = [-10, -5, 0, 5, 10]  # Percentage changes
        demand_impacts = []

        for price_change in price_changes:
            demand_change = elasticity * price_change
            demand_impacts.append({
                "price_change_pct": price_change,
                "demand_change_pct": round(demand_change, 2),
                "net_effect": "positive" if (price_change * (1 + demand_change / 100)) > 0 else "negative"
            })

        return {
            "elasticity_coefficient": elasticity,
            "elasticity_type": elasticity_type,
            "sensitivity": sensitivity,
            "recommendation": pricing_recommendation,
            "price_impact_scenarios": demand_impacts
        }

    def _analyze_competitive_pricing(self, costs: Dict, competitor_prices: Dict) -> Dict[str, Any]:
        """
        Analyze competitive pricing landscape
        """
        unit_cost = costs.get('unit_cost', 100)
        competitor_price_list = list(competitor_prices.values())

        if not competitor_price_list:
            return {
                "market_position": "no_competitors",
                "price_gap": 0,
                "competitive_index": 100
            }

        avg_competitor_price = np.mean(competitor_price_list)
        min_competitor_price = np.min(competitor_price_list)
        max_competitor_price = np.max(competitor_price_list)

        # Calculate competitive pricing ranges
        pricing_bands = {
            "premium": max_competitor_price * 1.1,
            "market_rate": avg_competitor_price,
            "competitive": avg_competitor_price * 0.95,
            "aggressive": min_competitor_price * 0.9
        }

        return {
            "competitor_average": round(avg_competitor_price, 2),
            "competitor_range": {
                "min": round(min_competitor_price, 2),
                "max": round(max_competitor_price, 2)
            },
            "pricing_bands": {k: round(v, 2) for k, v in pricing_bands.items()},
            "cost_to_market_ratio": round((unit_cost / avg_competitor_price * 100), 2) if avg_competitor_price > 0 else 0
        }

    def _optimize_pricing(self, costs: Dict, elasticity: Dict, competitive: Dict) -> Dict[str, Any]:
        """
        Optimize pricing for maximum margin while considering market factors
        """
        unit_cost = costs.get('unit_cost', 100)
        target_margin_pct = costs.get('target_margin_percentage', 30)

        # Cost-plus pricing baseline
        cost_plus_price = unit_cost * (1 + target_margin_pct / 100)

        # Market-based pricing
        market_price = competitive.get('competitor_average', cost_plus_price)

        # Calculate optimal price based on elasticity
        elasticity_coef = elasticity['elasticity_coefficient']

        if elasticity_coef < -1:  # Elastic
            # Lower price for volume
            optimal_price = min(cost_plus_price, market_price * 0.95)
            strategy = "volume_based"
        elif elasticity_coef > -1 and elasticity_coef < 0:  # Inelastic
            # Higher price for margin
            optimal_price = max(cost_plus_price, market_price * 1.05)
            strategy = "margin_based"
        else:
            # Market rate
            optimal_price = market_price
            strategy = "market_following"

        # Ensure minimum margin
        min_price = unit_cost * 1.15  # At least 15% margin
        optimal_price = max(optimal_price, min_price)

        # Calculate expected margin
        expected_margin = ((optimal_price - unit_cost) / optimal_price * 100)

        # Revenue projection (simplified)
        base_volume = costs.get('expected_volume', 1000)
        price_change_pct = ((optimal_price - market_price) / market_price * 100) if market_price > 0 else 0
        volume_change_pct = elasticity_coef * price_change_pct
        expected_volume = base_volume * (1 + volume_change_pct / 100)
        revenue_projection = optimal_price * expected_volume

        # Pricing recommendations by scenario
        recommendations = [
            {
                "scenario": "Aggressive Growth",
                "price": round(optimal_price * 0.95, 2),
                "strategy": "Maximize market share",
                "margin": round(((optimal_price * 0.95 - unit_cost) / (optimal_price * 0.95) * 100), 2)
            },
            {
                "scenario": "Balanced",
                "price": round(optimal_price, 2),
                "strategy": strategy,
                "margin": round(expected_margin, 2)
            },
            {
                "scenario": "Premium Positioning",
                "price": round(optimal_price * 1.1, 2),
                "strategy": "Maximize margin",
                "margin": round(((optimal_price * 1.1 - unit_cost) / (optimal_price * 1.1) * 100), 2)
            }
        ]

        return {
            "optimal_price": round(optimal_price, 2),
            "expected_margin": round(expected_margin, 2),
            "pricing_strategy": strategy,
            "recommendations": recommendations,
            "margin_analysis": {
                "unit_cost": unit_cost,
                "optimal_price": round(optimal_price, 2),
                "margin_dollars": round(optimal_price - unit_cost, 2),
                "margin_percentage": round(expected_margin, 2)
            },
            "revenue_projection": round(revenue_projection, 2)
        }

    def _calculate_volume_impact(self, pricing: Dict, elasticity: Dict) -> Dict[str, Any]:
        """
        Calculate volume impact of pricing decisions
        """
        scenarios = []

        for rec in pricing['recommendations']:
            price = rec['price']
            base_price = pricing['optimal_price']

            price_change = ((price - base_price) / base_price * 100) if base_price > 0 else 0
            volume_change = elasticity['elasticity_coefficient'] * price_change

            scenarios.append({
                "scenario": rec['scenario'],
                "price": price,
                "volume_change_pct": round(volume_change, 2),
                "expected_volume_multiplier": round(1 + volume_change / 100, 2)
            })

        return {
            "volume_scenarios": scenarios,
            "elasticity_factor": elasticity['elasticity_coefficient']
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_manage_pricing_sales_marketing_agent(config: Optional[ManagePricingSalesMarketingAgentConfig] = None):
    if config is None:
        config = ManagePricingSalesMarketingAgentConfig()
    return ManagePricingSalesMarketingAgent(config)
