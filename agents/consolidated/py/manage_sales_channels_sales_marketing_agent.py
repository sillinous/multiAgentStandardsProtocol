"""
ManageSalesChannelsSalesMarketingAgent - APQC Agent
APQC Process: 3.3.3
APQC Blueprint ID: apqc_3_0_s1t2u3v4
Skills: channel_profitability (0.91), contribution_analysis (0.88), channel_optimization (0.86)
Full compliance: All 8 architectural principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageSalesChannelsSalesMarketingAgentConfig:
    apqc_agent_id: str = "apqc_3_0_s1t2u3v4"
    apqc_process_id: str = "3.3.3"
    agent_id: str = "apqc_3_0_s1t2u3v4"
    agent_name: str = "manage_sales_channels_sales_marketing_agent"
    agent_type: str = "analytical"
    version: str = "1.0.0"
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class ManageSalesChannelsSalesMarketingAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "3.3.3"

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

    def _calculate_channel_profitability(self, channel_sales, channel_costs):
        results = {}
        for channel_id in set(s.get("channel_id") for s in channel_sales):
            sales = [s for s in channel_sales if s.get("channel_id") == channel_id]
            costs = [c for c in channel_costs if c.get("channel_id") == channel_id]

            total_revenue = sum(s.get("amount", 0) for s in sales)
            total_costs = sum(c.get("cost", 0) for c in costs)
            profit = total_revenue - total_costs
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

            results[channel_id] = {
                "revenue": round(total_revenue, 2),
                "costs": round(total_costs, 2),
                "profit": round(profit, 2),
                "margin_pct": round(margin, 2),
                "roi": round((profit / total_costs * 100), 2) if total_costs > 0 else 0,
            }
        return results

    def _analyze_contribution(self, profitability):
        total_profit = sum(v["profit"] for v in profitability.values())
        for channel_id, metrics in profitability.items():
            metrics["contribution_pct"] = (
                round((metrics["profit"] / total_profit * 100), 2) if total_profit > 0 else 0
            )
        return profitability

    def _optimize_channels(self, analysis):
        recommendations = []
        for channel_id, metrics in analysis.items():
            if metrics["margin_pct"] < 10:
                recommendations.append(
                    {
                        "channel_id": channel_id,
                        "action": "Review pricing or reduce costs",
                        "priority": "high",
                    }
                )
            elif metrics["roi"] > 200:
                recommendations.append(
                    {
                        "channel_id": channel_id,
                        "action": "Increase investment - high ROI channel",
                        "priority": "high",
                    }
                )
        return recommendations

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


def create_manage_sales_channels_sales_marketing_agent(config=None):
    return ManageSalesChannelsSalesMarketingAgent(
        config or ManageSalesChannelsSalesMarketingAgentConfig()
    )
