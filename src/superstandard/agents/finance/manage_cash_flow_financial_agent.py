"""
ManageCashFlowFinancialAgent - APQC Agent
Process: 8.4.1 | ID: apqc_8_0_a9b0c1d2
Skills: cash_forecasting (0.93), working_capital_optimization (0.90), liquidity_analysis (0.89)
Compliance: All 8 principles | Protocols: A2A, A2P, ACP, ANP, MCP
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
class ManageCashFlowFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_a9b0c1d2"
    apqc_process_id: str = "8.4.1"
    agent_id: str = "apqc_8_0_a9b0c1d2"
    agent_name: str = "manage_cash_flow_financial_agent"
    agent_type: str = (
        "financial"
        if "8_0" in agent["file"]
        else "strategic" if "1_0" in agent["file"] else "human_capital"
    )
    version: str = "1.0.0"


class ManageCashFlowFinancialAgent(BaseAgent, ProtocolMixin):
    VERSION = "1.0.0"
    APQC_PROCESS_ID = "8.4.1"

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

    def _forecast_cash_flow(self, ar_data, ap_data, revenue_forecast, payment_terms):
        # Direct method cash flow forecast
        cash_forecast = []

        for period in revenue_forecast:
            period_id = period.get("period")
            forecasted_revenue = period.get("revenue", 0)

            # Calculate cash collections (considering payment terms)
            avg_collection_days = payment_terms.get("ar_days", 30)
            cash_collections = forecasted_revenue * 0.7  # Simplified: 70% collected in period

            # Calculate cash payments
            avg_payment_days = payment_terms.get("ap_days", 45)
            cash_payments = period.get("expenses", 0) * 0.8  # 80% paid in period

            net_cash_flow = cash_collections - cash_payments

            cash_forecast.append(
                {
                    "period": period_id,
                    "cash_collections": round(cash_collections, 2),
                    "cash_payments": round(cash_payments, 2),
                    "net_cash_flow": round(net_cash_flow, 2),
                }
            )

        return cash_forecast

    def _working_capital_ratios(
        self, ar_balance, inventory_balance, ap_balance, revenue_annual, cogs_annual
    ):
        # Days Sales Outstanding (DSO)
        dso = (ar_balance / revenue_annual * 365) if revenue_annual > 0 else 0

        # Days Inventory Outstanding (DIO)
        dio = (inventory_balance / cogs_annual * 365) if cogs_annual > 0 else 0

        # Days Payable Outstanding (DPO)
        dpo = (ap_balance / cogs_annual * 365) if cogs_annual > 0 else 0

        # Cash Conversion Cycle
        ccc = dso + dio - dpo

        return {
            "dso": round(dso, 1),
            "dio": round(dio, 1),
            "dpo": round(dpo, 1),
            "cash_conversion_cycle": round(ccc, 1),
            "working_capital": round(ar_balance + inventory_balance - ap_balance, 2),
            "efficiency": "Excellent" if ccc < 30 else "Good" if ccc < 60 else "Needs Improvement",
        }

    def _liquidity_scoring(self, current_assets, current_liabilities, quick_assets):
        # Current Ratio
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0

        # Quick Ratio (Acid Test)
        quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else 0

        # Liquidity Score (0-100)
        current_score = min((current_ratio / 2.0) * 50, 50)  # Target: 2.0
        quick_score = min((quick_ratio / 1.0) * 50, 50)  # Target: 1.0
        liquidity_score = current_score + quick_score

        return {
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2),
            "liquidity_score": round(liquidity_score, 2),
            "liquidity_status": (
                "Strong"
                if liquidity_score >= 80
                else "Adequate" if liquidity_score >= 60 else "Weak"
            ),
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


def create_manage_cash_flow_financial_agent(config=None):
    return ManageCashFlowFinancialAgent(config or ManageCashFlowFinancialAgentConfig())
