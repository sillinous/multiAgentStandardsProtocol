"""
APQC PCF Agent: Evaluate Risk and Return Profile (1.2.2.3)

Quantifies strategic risks and returns with risk-adjusted analysis.
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


class EvaluateRiskReturnAgent(ActivityAgentBase):
    """Agent for evaluating risk and return profiles of strategies."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10057",
            hierarchy_id="1.2.2.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.2",
            process_group_name="Develop business strategy",
            process_id="1.2.2",
            process_name="Evaluate and select strategies",
            activity_id="1.2.2.3",
            activity_name="Evaluate risk and return profile",
            parent_element_id="10050",
            kpis=[
                {"name": "expected_roi", "type": "percentage", "unit": "%"},
                {"name": "risk_adjusted_return", "type": "score", "unit": "0-10"},
                {"name": "payback_period", "type": "duration", "unit": "months"}
            ]
        )

        return PCFAgentConfig(
            agent_id="evaluate_risk_return_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate risk and return profiles."""
        execution_start = datetime.utcnow()

        # Quantify strategic risks
        risk_analysis = await self._quantify_risks()

        # Project returns
        return_projections = await self._project_returns()

        # Calculate risk-adjusted returns
        risk_adjusted = await self._calculate_risk_adjusted_returns(
            risk_analysis, return_projections
        )

        # Portfolio risk assessment
        portfolio_risk = await self._assess_portfolio_risk(risk_analysis)

        # Generate risk-return matrix
        risk_return_matrix = await self._create_risk_return_matrix(
            risk_analysis, return_projections
        )

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        # Calculate summary KPIs
        best_strategy = max(risk_adjusted, key=lambda x: x["risk_adjusted_score"])

        result = {
            "risk_return_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Comprehensive risk-return analysis"
            },
            "risk_analysis": risk_analysis,
            "return_projections": return_projections,
            "risk_adjusted_returns": risk_adjusted,
            "portfolio_risk": portfolio_risk,
            "risk_return_matrix": risk_return_matrix,
            "kpis": {
                "expected_roi": best_strategy["expected_roi"],
                "risk_adjusted_return": best_strategy["risk_adjusted_score"],
                "payback_period": best_strategy["payback_months"],
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _quantify_risks(self) -> List[Dict[str, Any]]:
        """Quantify strategic risks for each strategy."""
        await asyncio.sleep(0.05)

        strategies = [
            {"name": "Aggressive Market Penetration", "base_risk": "Medium"},
            {"name": "Product Innovation Platform", "base_risk": "Medium-High"},
            {"name": "Geographic Expansion (EMEA)", "base_risk": "High"},
            {"name": "Vertical Market Specialization", "base_risk": "Low-Medium"},
            {"name": "Strategic Acquisition", "base_risk": "High"}
        ]

        risk_categories = ["market_risk", "execution_risk", "financial_risk", "competitive_risk"]
        risk_analysis = []

        for strategy in strategies:
            risks = {}
            total_risk_score = 0

            for category in risk_categories:
                if strategy["base_risk"] == "High":
                    probability = round(random.uniform(0.30, 0.50), 2)
                    impact = round(random.uniform(7.0, 9.0), 1)
                elif strategy["base_risk"] == "Medium-High":
                    probability = round(random.uniform(0.25, 0.40), 2)
                    impact = round(random.uniform(6.0, 8.0), 1)
                elif strategy["base_risk"] == "Medium":
                    probability = round(random.uniform(0.15, 0.30), 2)
                    impact = round(random.uniform(5.0, 7.0), 1)
                else:  # Low-Medium
                    probability = round(random.uniform(0.10, 0.20), 2)
                    impact = round(random.uniform(4.0, 6.0), 1)

                risk_score = probability * impact
                risks[category] = {
                    "probability": probability,
                    "impact": impact,
                    "risk_score": round(risk_score, 2),
                    "mitigation": f"Mitigation strategy for {category}"
                }
                total_risk_score += risk_score

            risk_analysis.append({
                "strategy": strategy["name"],
                "risk_breakdown": risks,
                "total_risk_score": round(total_risk_score, 2),
                "risk_rating": strategy["base_risk"],
                "top_risks": sorted(
                    [{"category": k, **v} for k, v in risks.items()],
                    key=lambda x: x["risk_score"],
                    reverse=True
                )[:2]
            })

        return risk_analysis

    async def _project_returns(self) -> List[Dict[str, Any]]:
        """Project financial returns for each strategy."""
        await asyncio.sleep(0.05)

        strategies = [
            "Aggressive Market Penetration",
            "Product Innovation Platform",
            "Geographic Expansion (EMEA)",
            "Vertical Market Specialization",
            "Strategic Acquisition"
        ]

        projections = []

        for strategy in strategies:
            investment = random.randint(20, 150) * 1000000  # $20M - $150M
            year1_revenue = investment * random.uniform(0.3, 0.8)
            growth_rate = random.uniform(1.3, 2.0)  # 30%-100% growth

            year_revenues = [year1_revenue * (growth_rate ** i) for i in range(5)]
            cumulative_revenue = sum(year_revenues)
            npv = cumulative_revenue * random.uniform(0.6, 0.8) - investment  # Simplified NPV

            projections.append({
                "strategy": strategy,
                "investment_required": investment,
                "5_year_projections": {
                    "year_1_revenue": round(year_revenues[0]),
                    "year_5_revenue": round(year_revenues[4]),
                    "cumulative_revenue": round(cumulative_revenue),
                    "cagr": f"{round((year_revenues[4] / year_revenues[0]) ** (1/4) - 1, 2) * 100}%"
                },
                "financial_metrics": {
                    "npv": round(npv),
                    "roi": f"{round((cumulative_revenue / investment - 1) * 100, 1)}%",
                    "payback_period_months": random.randint(18, 48),
                    "irr": f"{round(random.uniform(15, 45), 1)}%"
                },
                "profitability": {
                    "gross_margin": f"{round(random.uniform(60, 80), 1)}%",
                    "ebitda_margin_year_5": f"{round(random.uniform(15, 35), 1)}%",
                    "breakeven_month": random.randint(12, 36)
                }
            })

        return projections

    async def _calculate_risk_adjusted_returns(
        self,
        risks: List[Dict[str, Any]],
        returns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate risk-adjusted returns (Sharpe ratio inspired)."""
        await asyncio.sleep(0.05)

        risk_adjusted = []

        for i, risk_data in enumerate(risks):
            return_data = returns[i]

            # Extract metrics
            roi_str = return_data["financial_metrics"]["roi"].rstrip("%")
            expected_roi = float(roi_str)
            risk_score = risk_data["total_risk_score"]
            payback_months = return_data["financial_metrics"]["payback_period_months"]

            # Risk-adjusted return score (0-10 scale)
            # Higher ROI is better, lower risk is better, shorter payback is better
            roi_normalized = min(expected_roi / 300 * 10, 10)  # Normalize ROI to 0-10
            risk_normalized = 10 - (risk_score / 10 * 10)  # Invert risk to 0-10
            payback_normalized = 10 - (payback_months / 48 * 10)  # Shorter is better

            risk_adjusted_score = (
                roi_normalized * 0.40 +
                risk_normalized * 0.40 +
                payback_normalized * 0.20
            )

            risk_adjusted.append({
                "strategy": risk_data["strategy"],
                "expected_roi": expected_roi,
                "risk_score": risk_score,
                "payback_months": payback_months,
                "risk_adjusted_score": round(risk_adjusted_score, 1),
                "sharpe_ratio_equivalent": round(risk_adjusted_score / 10 * 3, 2),  # Scale to ~0-3
                "recommendation": (
                    "Highly attractive" if risk_adjusted_score >= 7.5 else
                    "Attractive" if risk_adjusted_score >= 6.5 else
                    "Moderate" if risk_adjusted_score >= 5.5 else
                    "Marginal"
                )
            })

        return sorted(risk_adjusted, key=lambda x: x["risk_adjusted_score"], reverse=True)

    async def _assess_portfolio_risk(
        self,
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess portfolio-level risk if multiple strategies pursued."""
        await asyncio.sleep(0.05)

        return {
            "portfolio_diversification": {
                "risk_correlation": "Moderate - some strategies share common risk factors",
                "diversification_benefit": "Portfolio risk 20-30% lower than sum of individual risks",
                "concentration_risk": "Acceptable - no single strategy dominates portfolio"
            },
            "aggregate_risk_metrics": {
                "portfolio_var_95": f"${random.randint(15, 40)}M at 95% confidence",
                "stress_test_loss": f"${random.randint(30, 80)}M in severe downturn",
                "expected_shortfall": f"${random.randint(20, 50)}M"
            },
            "risk_mitigation_strategy": [
                "Sequence high-risk strategies to avoid concentration",
                "Build contingency reserves equal to 20% of portfolio investment",
                "Establish risk monitoring dashboard with trigger-based interventions",
                "Consider risk transfer mechanisms (insurance, hedging) for tail risks"
            ],
            "recommendations": [
                "Limit any single strategy to <40% of total portfolio investment",
                "Ensure at least one low-risk strategy in portfolio for stability",
                "Build option value into strategies (ability to scale or exit)",
                "Monitor portfolio risk quarterly and rebalance as needed"
            ]
        }

    async def _create_risk_return_matrix(
        self,
        risks: List[Dict[str, Any]],
        returns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create risk-return positioning matrix."""
        await asyncio.sleep(0.05)

        matrix_positions = []

        for i, risk_data in enumerate(risks):
            return_data = returns[i]

            roi_str = return_data["financial_metrics"]["roi"].rstrip("%")
            expected_return = float(roi_str)
            risk_level = risk_data["total_risk_score"]

            # Categorize position
            if expected_return > 150 and risk_level < 5:
                quadrant = "High Return, Low Risk (Ideal)"
            elif expected_return > 150 and risk_level >= 5:
                quadrant = "High Return, High Risk (Aggressive)"
            elif expected_return <= 150 and risk_level < 5:
                quadrant = "Moderate Return, Low Risk (Conservative)"
            else:
                quadrant = "Moderate Return, High Risk (Avoid)"

            matrix_positions.append({
                "strategy": risk_data["strategy"],
                "return": expected_return,
                "risk": risk_level,
                "quadrant": quadrant,
                "position": {
                    "x": round(risk_level, 1),  # Risk on X-axis
                    "y": round(expected_return / 10, 1)  # Return on Y-axis (scaled)
                }
            })

        return {
            "matrix_positions": matrix_positions,
            "efficient_frontier": [
                "Product Innovation Platform and Vertical Specialization offer best risk-return tradeoff",
                "Aggressive Market Penetration provides good return but moderate risk",
                "Geographic Expansion is high risk - only pursue if risk tolerance is high"
            ],
            "recommended_portfolio": {
                "core_strategies": [
                    "Vertical Market Specialization (low risk, good return)",
                    "Product Innovation Platform (moderate risk, high return)"
                ],
                "opportunistic": [
                    "Aggressive Market Penetration (if market conditions favorable)",
                    "Strategic Acquisition (if compelling target emerges)"
                ],
                "avoid": [
                    "Strategies in 'Moderate Return, High Risk' quadrant unless strategic imperative"
                ]
            }
        }


__all__ = ['EvaluateRiskReturnAgent']
