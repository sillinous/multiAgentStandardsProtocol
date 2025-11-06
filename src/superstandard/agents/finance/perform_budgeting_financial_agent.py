"""
PerformBudgetingFinancialAgent - APQC Agent
Process: 8.1.4 | ID: apqc_8_0_c1d2e3f4
Skills: budget_allocation (0.91), variance_tracking (0.90), rolling_forecasts (0.88)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
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
class PerformBudgetingFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_c1d2e3f4"
    apqc_process_id: str = "8.1.4"
    agent_id: str = "apqc_8_0_c1d2e3f4"
    agent_name: str = "perform_budgeting_financial_agent"
    agent_type: str = (
        "financial"
        if "8_0" in agent["file"]
        else "strategic" if "1_0" in agent["file"] else "human_capital"
    )
    version: str = "1.0.0"


class PerformBudgetingFinancialAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "8.1.4"

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

    def _allocate_budget(self, total_budget, cost_centers, strategic_priorities):
        # Budget allocation algorithm
        allocations = {}

        # Calculate priority-weighted allocation
        total_weight = sum(cc.get("priority_weight", 1.0) for cc in cost_centers)

        for cost_center in cost_centers:
            cc_id = cost_center.get("cost_center_id")
            base_allocation = (
                cost_center.get("priority_weight", 1.0) / total_weight
            ) * total_budget

            # Adjust for strategic alignment
            strategic_multiplier = 1.0
            if cc_id in strategic_priorities:
                strategic_multiplier = strategic_priorities[cc_id].get("multiplier", 1.0)

            final_allocation = base_allocation * strategic_multiplier

            allocations[cc_id] = {
                "base_allocation": round(base_allocation, 2),
                "strategic_multiplier": strategic_multiplier,
                "final_allocation": round(final_allocation, 2),
                "pct_of_total": round((final_allocation / total_budget * 100), 2),
            }

        return allocations

    def _variance_analysis(self, actual_spend, budgeted_spend):
        variance_report = {}

        for category, budget in budgeted_spend.items():
            actual = actual_spend.get(category, 0)
            variance = actual - budget
            variance_pct = (variance / budget * 100) if budget > 0 else 0

            # Determine significance
            if abs(variance_pct) > 10:
                significance = "material"
            elif abs(variance_pct) > 5:
                significance = "moderate"
            else:
                significance = "minor"

            variance_report[category] = {
                "budget": round(budget, 2),
                "actual": round(actual, 2),
                "variance": round(variance, 2),
                "variance_pct": round(variance_pct, 2),
                "status": "unfavorable" if variance > 0 else "favorable",
                "significance": significance,
            }

        return variance_report

    def _rolling_forecast_update(self, current_forecast, actual_ytd, months_remaining):
        # Update rolling forecast based on YTD actuals
        updated_forecast = {}

        for category, forecast_annual in current_forecast.items():
            actual = actual_ytd.get(category, 0)
            months_elapsed = 12 - months_remaining

            # Calculate run rate
            monthly_actual = actual / months_elapsed if months_elapsed > 0 else 0

            # Projected full year = Actual YTD + (Monthly Run Rate × Months Remaining)
            projected_annual = actual + (monthly_actual * months_remaining)

            variance_to_budget = projected_annual - forecast_annual

            updated_forecast[category] = {
                "original_forecast": round(forecast_annual, 2),
                "actual_ytd": round(actual, 2),
                "projected_annual": round(projected_annual, 2),
                "variance_to_budget": round(variance_to_budget, 2),
                "confidence": (
                    "high" if months_elapsed >= 6 else "medium" if months_elapsed >= 3 else "low"
                ),
            }

        return updated_forecast

    def _zero_based_budgeting_scoring(self, budget_requests):
        # Zero-Based Budgeting: Justify each expense from zero
        scored_requests = []

        for request in budget_requests:
            # Scoring criteria
            business_impact = request.get("business_impact_score", 0)  # 0-10
            strategic_alignment = request.get("strategic_alignment_score", 0)  # 0-10
            roi = request.get("expected_roi", 0)  # percentage

            # Composite score
            composite_score = (
                (business_impact * 0.4) + (strategic_alignment * 0.4) + (min(roi / 10, 10) * 0.2)
            )

            scored_requests.append(
                {
                    "request_id": request.get("request_id"),
                    "amount": request.get("amount", 0),
                    "composite_score": round(composite_score, 2),
                    "recommendation": (
                        "Approve"
                        if composite_score >= 7
                        else "Review" if composite_score >= 5 else "Reject"
                    ),
                }
            )

        # Sort by score descending
        scored_requests.sort(key=lambda x: x["composite_score"], reverse=True)

        return scored_requests

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


def create_perform_budgeting_financial_agent(config=None):
    return PerformBudgetingFinancialAgent(config or PerformBudgetingFinancialAgentConfig())
