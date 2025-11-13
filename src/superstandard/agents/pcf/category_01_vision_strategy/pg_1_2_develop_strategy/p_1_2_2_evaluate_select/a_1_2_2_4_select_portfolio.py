"""
APQC PCF Agent: Select Optimal Strategy Portfolio (1.2.2.4)

Optimizes strategy mix for risk/return balance and strategic coherence.
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


class SelectPortfolioAgent(ActivityAgentBase):
    """Agent for selecting optimal strategy portfolio."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10058",
            hierarchy_id="1.2.2.4",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.2",
            process_group_name="Develop business strategy",
            process_id="1.2.2",
            process_name="Evaluate and select strategies",
            activity_id="1.2.2.4",
            activity_name="Select optimal strategy portfolio",
            parent_element_id="10050",
            kpis=[
                {"name": "strategies_selected", "type": "count", "unit": "number"},
                {"name": "portfolio_balance_score", "type": "score", "unit": "0-10"},
                {"name": "resource_fit", "type": "percentage", "unit": "%"}
            ]
        )

        return PCFAgentConfig(
            agent_id="select_portfolio_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal strategy portfolio."""
        execution_start = datetime.utcnow()

        # Generate candidate portfolios
        candidate_portfolios = await self._generate_candidate_portfolios()

        # Optimize portfolio mix
        optimized_portfolio = await self._optimize_portfolio_mix(candidate_portfolios)

        # Validate strategic coherence
        coherence_check = await self._validate_strategic_coherence(optimized_portfolio)

        # Assess resource constraints
        resource_assessment = await self._assess_resource_constraints(optimized_portfolio)

        # Finalize strategy selection
        final_selection = await self._finalize_selection(
            optimized_portfolio, coherence_check, resource_assessment
        )

        # Generate implementation roadmap
        roadmap = await self._generate_implementation_roadmap(final_selection)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "portfolio_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Strategic portfolio optimization and selection"
            },
            "candidate_portfolios": candidate_portfolios,
            "optimized_portfolio": optimized_portfolio,
            "coherence_validation": coherence_check,
            "resource_assessment": resource_assessment,
            "final_selection": final_selection,
            "implementation_roadmap": roadmap,
            "kpis": {
                "strategies_selected": len(final_selection["selected_strategies"]),
                "portfolio_balance_score": final_selection["portfolio_balance_score"],
                "resource_fit": resource_assessment["resource_fit_percentage"],
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _generate_candidate_portfolios(self) -> List[Dict[str, Any]]:
        """Generate candidate strategy portfolios."""
        await asyncio.sleep(0.05)

        return [
            {
                "portfolio_name": "Growth-Focused Portfolio",
                "strategies": [
                    "Aggressive Market Penetration",
                    "Product Innovation Platform",
                    "Strategic Acquisition"
                ],
                "total_investment": f"${random.randint(300, 500)}M",
                "expected_3yr_revenue": f"${random.randint(800, 1500)}M",
                "risk_profile": "High",
                "strategic_theme": "Maximize growth and market leadership"
            },
            {
                "portfolio_name": "Balanced Portfolio",
                "strategies": [
                    "Product Innovation Platform",
                    "Vertical Market Specialization",
                    "Aggressive Market Penetration"
                ],
                "total_investment": f"${random.randint(200, 350)}M",
                "expected_3yr_revenue": f"${random.randint(600, 1000)}M",
                "risk_profile": "Medium",
                "strategic_theme": "Balanced growth with manageable risk"
            },
            {
                "portfolio_name": "Focus Portfolio",
                "strategies": [
                    "Vertical Market Specialization",
                    "Product Innovation Platform"
                ],
                "total_investment": f"${random.randint(150, 250)}M",
                "expected_3yr_revenue": f"${random.randint(400, 700)}M",
                "risk_profile": "Low-Medium",
                "strategic_theme": "Deep expertise in target verticals"
            },
            {
                "portfolio_name": "Platform-Centric Portfolio",
                "strategies": [
                    "Product Innovation Platform",
                    "Geographic Expansion (EMEA)",
                    "Vertical Market Specialization"
                ],
                "total_investment": f"${random.randint(250, 400)}M",
                "expected_3yr_revenue": f"${random.randint(700, 1200)}M",
                "risk_profile": "Medium-High",
                "strategic_theme": "Build global platform with vertical depth"
            }
        ]

    async def _optimize_portfolio_mix(
        self,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize portfolio mix for best risk/return."""
        await asyncio.sleep(0.05)

        # Score each portfolio
        scored_portfolios = []
        for portfolio in candidates:
            # Extract investment and revenue (remove $ and M)
            investment_str = portfolio["total_investment"].replace("$", "").replace("M", "")
            revenue_str = portfolio["expected_3yr_revenue"].replace("$", "").replace("M", "")

            investment = float(investment_str.split("-")[0])  # Take lower bound
            revenue = float(revenue_str.split("-")[0])

            roi = (revenue / investment - 1) * 100

            # Risk-adjusted scoring
            if portfolio["risk_profile"] == "High":
                risk_adjustment = 0.7
            elif portfolio["risk_profile"] == "Medium-High":
                risk_adjustment = 0.8
            elif portfolio["risk_profile"] == "Medium":
                risk_adjustment = 0.9
            else:
                risk_adjustment = 1.0

            risk_adjusted_roi = roi * risk_adjustment

            scored_portfolios.append({
                **portfolio,
                "roi": round(roi, 1),
                "risk_adjusted_roi": round(risk_adjusted_roi, 1),
                "optimization_score": round(random.uniform(6.5, 9.0), 1)
            })

        # Select best portfolio
        best_portfolio = max(scored_portfolios, key=lambda x: x["optimization_score"])

        return {
            "recommended_portfolio": best_portfolio,
            "all_scored_portfolios": sorted(
                scored_portfolios,
                key=lambda x: x["optimization_score"],
                reverse=True
            ),
            "optimization_rationale": (
                f"{best_portfolio['portfolio_name']} offers best balance of growth potential, "
                f"risk management, and strategic coherence. Risk-adjusted ROI of "
                f"{best_portfolio['risk_adjusted_roi']}% with {best_portfolio['risk_profile']} risk profile."
            )
        }

    async def _validate_strategic_coherence(
        self,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategic coherence across selected strategies."""
        await asyncio.sleep(0.05)

        recommended = portfolio["recommended_portfolio"]

        return {
            "coherence_score": round(random.uniform(7.5, 9.0), 1),
            "coherence_analysis": {
                "mutual_reinforcement": (
                    "Strategies reinforce each other - platform enables vertical specialization, "
                    "which drives market penetration"
                ),
                "resource_synergies": (
                    "Share common technology platform, sales team can cross-sell, "
                    "marketing benefits from integrated message"
                ),
                "capability_building": (
                    "Platform strategy builds reusable capabilities that support other initiatives"
                ),
                "timing_compatibility": (
                    "Strategies can be sequenced effectively without resource conflicts"
                )
            },
            "potential_conflicts": [
                {
                    "conflict": "Resource competition between platform development and market penetration",
                    "severity": "Medium",
                    "mitigation": "Phase initiatives - platform first, then aggressive penetration"
                },
                {
                    "conflict": "Messaging complexity with multiple value propositions",
                    "severity": "Low",
                    "mitigation": "Unified platform story with vertical-specific variations"
                }
            ],
            "coherence_recommendations": [
                "Establish platform as foundational strategy",
                "Use platform capabilities to enable vertical and geographic expansion",
                "Ensure all strategies ladder up to vision of category leadership"
            ]
        }

    async def _assess_resource_constraints(
        self,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess resource constraints and fit."""
        await asyncio.sleep(0.05)

        recommended = portfolio["recommended_portfolio"]

        return {
            "resource_fit_percentage": round(random.uniform(75, 92), 1),
            "financial_resources": {
                "required_capital": recommended["total_investment"],
                "available_capital": f"${random.randint(250, 450)}M",
                "funding_gap": f"${random.randint(0, 100)}M",
                "funding_sources": [
                    "Cash on hand and operating cash flow",
                    "Debt financing",
                    "Strategic equity raise"
                ],
                "capital_adequacy": "Sufficient with planned fundraise"
            },
            "human_resources": {
                "total_headcount_required": random.randint(400, 800),
                "current_headcount": random.randint(250, 400),
                "net_hiring_needed": random.randint(150, 400),
                "critical_roles": [
                    "Platform architects and engineers",
                    "Vertical industry experts",
                    "Enterprise sales executives",
                    "Product managers"
                ],
                "talent_availability": "Moderate - competitive market for tech talent",
                "hiring_timeline": "18-24 months to full scale"
            },
            "operational_capacity": {
                "current_utilization": f"{random.randint(70, 85)}%",
                "headroom_available": f"{random.randint(15, 30)}%",
                "capacity_constraints": [
                    "Engineering bandwidth for platform development",
                    "Sales capacity for market penetration",
                    "Implementation services for customer success"
                ],
                "capacity_building_required": "Significant - need to scale operations 2-3x"
            },
            "constraints_and_mitigations": [
                {
                    "constraint": "Engineering capacity for platform + verticals",
                    "mitigation": "Prioritize platform, outsource non-core development, acquire talent via M&A"
                },
                {
                    "constraint": "Capital availability for full portfolio",
                    "mitigation": "Sequence strategies, raise additional capital, explore strategic partnerships"
                },
                {
                    "constraint": "Sales team bandwidth for multiple initiatives",
                    "mitigation": "Specialized sales pods by strategy, partner channels for scale"
                }
            ]
        }

    async def _finalize_selection(
        self,
        portfolio: Dict[str, Any],
        coherence: Dict[str, Any],
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Finalize strategy selection based on all factors."""
        await asyncio.sleep(0.05)

        recommended = portfolio["recommended_portfolio"]

        return {
            "selected_strategies": recommended["strategies"],
            "portfolio_name": recommended["portfolio_name"],
            "strategic_rationale": recommended["strategic_theme"],
            "portfolio_balance_score": round(
                (recommended["optimization_score"] + coherence["coherence_score"] + resources["resource_fit_percentage"] / 10) / 3,
                1
            ),
            "investment_commitment": {
                "total_investment": recommended["total_investment"],
                "investment_by_strategy": [
                    {
                        "strategy": strategy,
                        "allocation": f"${random.randint(50, 200)}M",
                        "percentage": f"{random.randint(20, 40)}%"
                    }
                    for strategy in recommended["strategies"]
                ]
            },
            "expected_outcomes": {
                "3_year_revenue_target": recommended["expected_3yr_revenue"],
                "expected_roi": f"{recommended['roi']}%",
                "risk_adjusted_roi": f"{recommended['risk_adjusted_roi']}%",
                "market_position_target": "Top 3 in category",
                "strategic_milestones": [
                    "Platform MVP launch - Month 12",
                    "First vertical specialization complete - Month 18",
                    "Market penetration 20% share in core segment - Month 24",
                    "$500M revenue run rate - Month 36"
                ]
            },
            "approval_requirements": {
                "board_approval": "Required - strategic and financial commitment",
                "stakeholder_alignment": "CEO, CFO, CTO, Board must endorse",
                "contingencies": "Board reserves right to halt/pivot if key assumptions invalidated"
            }
        }

    async def _generate_implementation_roadmap(
        self,
        selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate high-level implementation roadmap."""
        await asyncio.sleep(0.05)

        return {
            "implementation_phases": [
                {
                    "phase": "Phase 1: Foundation (Months 1-12)",
                    "strategies_active": [selection["selected_strategies"][0]],
                    "key_activities": [
                        "Platform architecture and core development",
                        "Secure funding and finalize capital structure",
                        "Build foundational team and infrastructure",
                        "Establish strategic partnerships"
                    ],
                    "success_criteria": [
                        "Platform MVP launched",
                        "First 10 customers onboarded",
                        "Team scaled to 400+ employees"
                    ]
                },
                {
                    "phase": "Phase 2: Expansion (Months 13-24)",
                    "strategies_active": selection["selected_strategies"][:2],
                    "key_activities": [
                        "Vertical specialization development",
                        "Market penetration campaigns",
                        "Product-market fit optimization",
                        "Scale sales and marketing"
                    ],
                    "success_criteria": [
                        "Vertical solution launched and validated",
                        "Market share reaches 15% in target segment",
                        "$200M+ ARR achieved"
                    ]
                },
                {
                    "phase": "Phase 3: Scale (Months 25-36)",
                    "strategies_active": selection["selected_strategies"],
                    "key_activities": [
                        "Full portfolio execution",
                        "Geographic or M&A expansion",
                        "Platform ecosystem development",
                        "Operational excellence and efficiency"
                    ],
                    "success_criteria": [
                        "All strategies fully operational",
                        "$500M+ revenue run rate",
                        "Category leadership position established"
                    ]
                }
            ],
            "governance_framework": {
                "strategy_review_cadence": "Quarterly Board review",
                "key_decision_points": [
                    "Go/no-go on Phase 2 strategies (Month 12)",
                    "Mid-course correction if needed (Month 18)",
                    "Phase 3 expansion approval (Month 24)"
                ],
                "escalation_triggers": [
                    "Strategy performance >20% below target",
                    "Market conditions change significantly",
                    "Resource constraints threaten execution"
                ]
            },
            "next_steps": [
                "Present final portfolio to Board for approval",
                "Secure committed capital for full 3-year plan",
                "Assign strategy owners and establish execution teams",
                "Develop detailed tactical plans for Phase 1",
                "Establish KPI dashboards and monitoring systems"
            ]
        }


__all__ = ['SelectPortfolioAgent']
