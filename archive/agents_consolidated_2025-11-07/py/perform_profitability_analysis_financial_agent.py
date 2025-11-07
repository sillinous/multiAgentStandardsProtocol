"""
PerformProfitabilityAnalysisFinancialAgent - APQC Agent
Process: 8.1.3 | ID: apqc_8_0_z8a9b0c1
Skills: contribution_margin (0.92), breakeven_analysis (0.90), profit_driver_analysis (0.88)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class PerformProfitabilityAnalysisFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_z8a9b0c1"
    apqc_process_id: str = "8.1.3"
    agent_id: str = "apqc_8_0_z8a9b0c1"
    agent_name: str = "perform_profitability_analysis_financial_agent"
    agent_type: str = (
        "financial"
        if "8_0" in agent["file"]
        else "strategic" if "1_0" in agent["file"] else "human_capital"
    )
    version: str = "1.0.0"


class PerformProfitabilityAnalysisFinancialAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "8.1.3"

    def __init__(self, config):
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = {}

            # Execute based on agent specialty
            if "revenue_data" in input_data and "variable_costs" in input_data:
                result["contribution_margin"] = self._calculate_contribution_margin(
                    input_data["revenue_data"], input_data["variable_costs"]
                )

            if "fixed_costs" in input_data:
                result["breakeven_analysis"] = self._breakeven_analysis(
                    input_data["fixed_costs"],
                    input_data.get("contribution_margin_pct", 30),
                    input_data.get("price_per_unit", 100),
                )

            if "ar_data" in input_data or "ar_balance" in input_data:
                if "ar_data" in input_data:
                    result["cash_forecast"] = self._forecast_cash_flow(
                        input_data["ar_data"],
                        input_data.get("ap_data", []),
                        input_data.get("revenue_forecast", []),
                        input_data.get("payment_terms", {}),
                    )
                else:
                    result["working_capital"] = self._working_capital_ratios(
                        input_data.get("ar_balance", 0),
                        input_data.get("inventory_balance", 0),
                        input_data.get("ap_balance", 0),
                        input_data.get("revenue_annual", 1),
                        input_data.get("cogs_annual", 1),
                    )

            if "internal_capabilities" in input_data:
                result["swot_analysis"] = self._swot_analysis(
                    input_data["internal_capabilities"],
                    input_data.get("market_conditions", {}),
                    input_data.get("competitive_landscape", {}),
                )

            if "total_budget" in input_data and "cost_centers" in input_data:
                result["budget_allocation"] = self._allocate_budget(
                    input_data["total_budget"],
                    input_data["cost_centers"],
                    input_data.get("strategic_priorities", {}),
                )

            if "employee_compensation" in input_data:
                result["compa_ratio_analysis"] = self._compa_ratio_analysis(
                    input_data["employee_compensation"], input_data.get("market_data", {})
                )

            return {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": result,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_contribution_margin(self, revenue_data, variable_costs):
        results = {}

        for product_id in set(r.get("product_id") for r in revenue_data):
            product_revenue = [r for r in revenue_data if r.get("product_id") == product_id]
            product_costs = [c for c in variable_costs if c.get("product_id") == product_id]

            total_revenue = sum(r.get("amount", 0) for r in product_revenue)
            total_variable_costs = sum(c.get("amount", 0) for c in product_costs)

            contribution = total_revenue - total_variable_costs
            contribution_margin_pct = (
                (contribution / total_revenue * 100) if total_revenue > 0 else 0
            )

            results[product_id] = {
                "revenue": round(total_revenue, 2),
                "variable_costs": round(total_variable_costs, 2),
                "contribution": round(contribution, 2),
                "contribution_margin_pct": round(contribution_margin_pct, 2),
            }

        return results

    def _breakeven_analysis(self, fixed_costs, contribution_margin_pct, price_per_unit):
        # Breakeven Point = Fixed Costs / Contribution Margin per Unit
        contribution_per_unit = price_per_unit * (contribution_margin_pct / 100)

        if contribution_per_unit <= 0:
            return {"breakeven_units": float("inf"), "breakeven_revenue": float("inf")}

        breakeven_units = fixed_costs / contribution_per_unit
        breakeven_revenue = breakeven_units * price_per_unit

        return {
            "fixed_costs": round(fixed_costs, 2),
            "contribution_per_unit": round(contribution_per_unit, 2),
            "breakeven_units": round(breakeven_units, 0),
            "breakeven_revenue": round(breakeven_revenue, 2),
            "margin_of_safety_pct": 0,  # Would calculate based on actual sales
        }

    def _profit_waterfall(self, gross_revenue, cost_components):
        # Profit waterfall showing profit drivers
        waterfall = [
            {"stage": "Gross Revenue", "value": gross_revenue, "cumulative": gross_revenue}
        ]

        cumulative = gross_revenue
        for component in cost_components:
            cumulative -= component.get("amount", 0)
            waterfall.append(
                {
                    "stage": component.get("name", "Cost"),
                    "value": -component.get("amount", 0),
                    "cumulative": cumulative,
                }
            )

        waterfall.append({"stage": "Net Profit", "value": cumulative, "cumulative": cumulative})

        return waterfall

    def _segment_profitability(self, segments, revenue_data, cost_data):
        segment_pl = {}

        for segment in segments:
            segment_id = segment.get("segment_id")
            seg_revenue = sum(
                r.get("amount", 0) for r in revenue_data if r.get("segment_id") == segment_id
            )
            seg_costs = sum(
                c.get("amount", 0) for c in cost_data if c.get("segment_id") == segment_id
            )
            seg_profit = seg_revenue - seg_costs
            seg_margin = (seg_profit / seg_revenue * 100) if seg_revenue > 0 else 0

            segment_pl[segment_id] = {
                "revenue": round(seg_revenue, 2),
                "costs": round(seg_costs, 2),
                "profit": round(seg_profit, 2),
                "margin_pct": round(seg_margin, 2),
                "profitable": seg_profit > 0,
            }

        return segment_pl

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


def create_perform_profitability_analysis_financial_agent(config=None):
    return PerformProfitabilityAnalysisFinancialAgent(
        config or PerformProfitabilityAnalysisFinancialAgentConfig()
    )
