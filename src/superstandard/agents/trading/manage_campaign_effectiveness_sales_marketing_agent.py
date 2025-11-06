"""
ManageCampaignEffectivenessSalesMarketingAgent - APQC Agent
APQC Process: 3.4.1
APQC Blueprint ID: apqc_3_0_t2u3v4w5
Skills: roi_calculation (0.93), attribution_modeling (0.89), ab_testing (0.87)
Full compliance: All 8 architectural principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageCampaignEffectivenessSalesMarketingAgentConfig:
    apqc_agent_id: str = "apqc_3_0_t2u3v4w5"
    apqc_process_id: str = "3.4.1"
    agent_id: str = "apqc_3_0_t2u3v4w5"
    agent_name: str = "manage_campaign_effectiveness_sales_marketing_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class ManageCampaignEffectivenessSalesMarketingAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "3.4.1"

    def __init__(self, config):
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract inputs
            channel_sales = input_data.get("channel_sales", [])
            channel_costs = input_data.get("channel_costs", [])
            campaigns = input_data.get("campaign_data", [])
            conversions = input_data.get("conversions", [])
            touchpoints = input_data.get("touchpoints", [])

            # Execute business logic
            profitability = (
                self._calculate_channel_profitability(channel_sales, channel_costs)
                if channel_sales
                else {}
            )
            contribution = self._analyze_contribution(profitability) if profitability else {}
            campaign_roi = self._calculate_campaign_roi(campaigns, conversions) if campaigns else {}
            attribution = (
                self._multi_touch_attribution(touchpoints, conversions) if touchpoints else {}
            )

            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": {
                    "channel_analysis": profitability,
                    "contribution_analysis": contribution,
                    "campaign_roi": campaign_roi,
                    "attribution": attribution,
                    "recommendations": (
                        self._optimize_channels(contribution) if contribution else []
                    ),
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_campaign_roi(self, campaigns, conversions):
        roi_results = {}
        for campaign in campaigns:
            campaign_id = campaign.get("campaign_id")
            cost = campaign.get("cost", 0)
            campaign_conversions = [c for c in conversions if c.get("campaign_id") == campaign_id]
            revenue = sum(c.get("revenue", 0) for c in campaign_conversions)
            roi = ((revenue - cost) / cost * 100) if cost > 0 else 0

            roi_results[campaign_id] = {
                "cost": cost,
                "revenue": revenue,
                "roi_pct": round(roi, 2),
                "conversions": len(campaign_conversions),
                "cpa": round(cost / len(campaign_conversions), 2) if campaign_conversions else 0,
            }
        return roi_results

    def _multi_touch_attribution(self, touchpoints, conversions):
        # Linear attribution model
        attribution = {}
        for conversion in conversions:
            customer_touchpoints = [
                t for t in touchpoints if t.get("customer_id") == conversion.get("customer_id")
            ]
            if customer_touchpoints:
                credit_per_touch = conversion.get("revenue", 0) / len(customer_touchpoints)
                for touch in customer_touchpoints:
                    channel = touch.get("channel")
                    attribution[channel] = attribution.get(channel, 0) + credit_per_touch
        return attribution

    def _ab_test_significance(self, variant_a, variant_b):
        # Statistical significance using z-test approximation
        conversion_a = variant_a.get("conversions", 0) / variant_a.get("visitors", 1)
        conversion_b = variant_b.get("conversions", 0) / variant_b.get("visitors", 1)

        pooled_conversion = (variant_a.get("conversions", 0) + variant_b.get("conversions", 0)) / (
            variant_a.get("visitors", 1) + variant_b.get("visitors", 1)
        )

        se = (
            pooled_conversion
            * (1 - pooled_conversion)
            * (1 / variant_a.get("visitors", 1) + 1 / variant_b.get("visitors", 1))
        ) ** 0.5

        z_score = abs(conversion_b - conversion_a) / se if se > 0 else 0
        significant = z_score > 1.96  # 95% confidence

        return {
            "conversion_rate_a": round(conversion_a * 100, 2),
            "conversion_rate_b": round(conversion_b * 100, 2),
            "lift_pct": (
                round((conversion_b - conversion_a) / conversion_a * 100, 2)
                if conversion_a > 0
                else 0
            ),
            "statistically_significant": significant,
            "z_score": round(z_score, 3),
        }

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


def create_manage_campaign_effectiveness_sales_marketing_agent(config=None):
    return ManageCampaignEffectivenessSalesMarketingAgent(
        config or ManageCampaignEffectivenessSalesMarketingAgentConfig()
    )
