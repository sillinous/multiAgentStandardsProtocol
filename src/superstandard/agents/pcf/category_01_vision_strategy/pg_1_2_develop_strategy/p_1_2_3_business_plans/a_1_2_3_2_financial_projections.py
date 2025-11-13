"""
APQC PCF Agent: Develop Financial Projections (1.2.3.2)

Creates 3-5 year financial forecasts with P&L, balance sheet, and cash flow.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
import random

from superstandard.agents.pcf.base import (
    ActivityAgentBase,
    PCFMetadata,
    PCFAgentConfig,
)


class FinancialProjectionsAgent(ActivityAgentBase):
    """Agent for developing financial projections."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10060",
            hierarchy_id="1.2.3.2",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.2",
            process_group_name="Develop business strategy",
            process_id="1.2.3",
            process_name="Develop business plans",
            activity_id="1.2.3.2",
            activity_name="Develop financial projections",
            parent_element_id="10050",
            kpis=[
                {"name": "projected_revenue", "type": "currency", "unit": "USD"},
                {"name": "projected_ebitda", "type": "currency", "unit": "USD"},
                {"name": "cash_requirements", "type": "currency", "unit": "USD"}
            ]
        )

        return PCFAgentConfig(
            agent_id="financial_projections_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Develop financial projections."""
        execution_start = datetime.utcnow()

        pl_projections = await self._create_pl_projections()
        balance_sheet = await self._create_balance_sheet_projections()
        cash_flow = await self._create_cash_flow_projections()
        sensitivity = await self._conduct_sensitivity_analysis()

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        year_5 = pl_projections["yearly_projections"][-1]

        result = {
            "projections_overview": {
                "execution_date": execution_start.isoformat(),
                "projection_period": "5 years"
            },
            "income_statement": pl_projections,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "sensitivity_analysis": sensitivity,
            "kpis": {
                "projected_revenue": year_5["revenue"],
                "projected_ebitda": year_5["ebitda"],
                "cash_requirements": cash_flow["cumulative_cash_burn"],
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _create_pl_projections(self) -> Dict[str, Any]:
        """Create P&L projections."""
        await asyncio.sleep(0.05)

        base_revenue = random.randint(50, 100) * 1000000
        projections = []

        for year in range(1, 6):
            revenue = int(base_revenue * (1.5 ** (year - 1)))
            cogs = int(revenue * random.uniform(0.20, 0.30))
            gross_profit = revenue - cogs
            opex = int(revenue * random.uniform(0.50, 0.70))
            ebitda = gross_profit - opex

            projections.append({
                "year": year,
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "gross_margin_pct": round((gross_profit / revenue) * 100, 1),
                "opex": opex,
                "ebitda": ebitda,
                "ebitda_margin_pct": round((ebitda / revenue) * 100, 1) if ebitda > 0 else round((ebitda / revenue) * 100, 1)
            })

        return {
            "yearly_projections": projections,
            "cagr": f"{round(((projections[-1]['revenue'] / projections[0]['revenue']) ** (1/4) - 1) * 100, 1)}%"
        }

    async def _create_balance_sheet_projections(self) -> Dict[str, Any]:
        """Create balance sheet projections."""
        await asyncio.sleep(0.05)

        return {
            "year_5_snapshot": {
                "cash": f"${random.randint(50, 150)}M",
                "ar": f"${random.randint(30, 80)}M",
                "total_assets": f"${random.randint(200, 400)}M",
                "total_liabilities": f"${random.randint(50, 150)}M",
                "shareholders_equity": f"${random.randint(100, 300)}M"
            }
        }

    async def _create_cash_flow_projections(self) -> Dict[str, Any]:
        """Create cash flow projections."""
        await asyncio.sleep(0.05)

        return {
            "cumulative_cash_burn": f"${random.randint(100, 250)}M",
            "breakeven_quarter": f"Q{random.randint(8, 16)}",
            "peak_funding_need": f"${random.randint(150, 300)}M"
        }

    async def _conduct_sensitivity_analysis(self) -> Dict[str, Any]:
        """Conduct sensitivity analysis."""
        await asyncio.sleep(0.05)

        return {
            "scenarios": {
                "optimistic": {"revenue_impact": "+25%", "ebitda_impact": "+40%"},
                "baseline": {"revenue_impact": "0%", "ebitda_impact": "0%"},
                "pessimistic": {"revenue_impact": "-20%", "ebitda_impact": "-35%"}
            }
        }


__all__ = ['FinancialProjectionsAgent']
