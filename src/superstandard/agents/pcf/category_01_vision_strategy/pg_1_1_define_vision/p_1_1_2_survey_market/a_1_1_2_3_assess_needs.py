"""
APQC PCF Agent: Assess Customer Needs and Wants (1.1.2.3)

This agent evaluates the feasibility, strategic fit, and market opportunity of
identified customer needs, providing recommendations on which needs to target
and how to prioritize product/service development efforts.

Hierarchy:
- Category: 1.0 - Develop Vision and Strategy
- Process Group: 1.1 - Define the business concept and long-term vision
- Process: 1.1.2 - Survey market and determine customer needs and wants
- Activity: 1.1.2.3 - Assess customer needs and wants

Element ID: 19947
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


class AssessNeedsAgent(ActivityAgentBase):
    """
    Agent for assessing and evaluating customer needs.

    This agent performs comprehensive assessment of captured needs to determine:
    - Technical feasibility of addressing each need
    - Strategic fit with organizational vision and capabilities
    - Market opportunity size and revenue potential
    - Competitive positioning and differentiation
    - Resource requirements and investment needed
    - Risk factors and mitigation strategies
    - ROI projections and business case
    - Implementation priorities and roadmap

    Capabilities:
    - Feasibility analysis (technical, operational, financial)
    - Strategic fit evaluation
    - Market opportunity sizing (TAM, SAM, SOM)
    - Competitive gap analysis
    - Resource requirements estimation
    - Risk assessment and scoring
    - ROI modeling
    - Prioritization recommendations
    - Roadmap generation

    Outputs:
    - Feasibility scores for each need
    - Strategic fit ratings
    - Market opportunity estimates
    - Competitive analysis
    - Resource requirements
    - Risk assessments
    - Strategic recommendations
    - Implementation roadmap
    - KPI tracking (needs assessed, opportunity value, recommendation confidence)
    """

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        """Create the default configuration for this agent."""
        metadata = PCFMetadata(
            pcf_element_id="19947",
            hierarchy_id="1.1.2.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.2",
            process_name="Survey market and determine customer needs and wants",
            activity_id="1.1.2.3",
            activity_name="Assess customer needs and wants",
            parent_element_id="10030",
            kpis=[
                {"name": "needs_assessed", "type": "count", "unit": "number"},
                {"name": "opportunity_value_usd", "type": "currency", "unit": "USD"},
                {"name": "recommendation_confidence", "type": "percentage", "unit": "%"},
                {"name": "strategic_fit_score", "type": "score", "unit": "0-10"}
            ]
        )

        return PCFAgentConfig(
            agent_id="assess_needs_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess customer needs for feasibility and strategic value.

        Args:
            input_data: Assessment parameters including:
                - captured_needs: List of needs from agent 1.1.2.2 (optional)
                - organizational_capabilities: Current capabilities (optional)
                - strategic_objectives: Strategic goals (optional)
                - budget_available: Available investment budget (optional)
                - time_horizon: Planning horizon in months (optional)
                - risk_tolerance: Risk tolerance level (low/medium/high)

        Returns:
            Comprehensive assessment with recommendations and roadmap
        """
        execution_start = datetime.utcnow()

        # Extract input parameters (use mock data if not provided)
        needs = input_data.get("captured_needs", self._get_mock_needs())
        capabilities = input_data.get("organizational_capabilities", {
            "engineering_capacity": "Medium",
            "existing_platform": "Moderate",
            "data_infrastructure": "Strong",
            "design_resources": "Limited",
            "partnership_network": "Growing"
        })
        budget = input_data.get("budget_available", 5000000)
        time_horizon = input_data.get("time_horizon", 18)
        risk_tolerance = input_data.get("risk_tolerance", "medium")

        # Perform feasibility analysis
        feasibility_results = await self._assess_feasibility(
            needs, capabilities
        )

        # Evaluate strategic fit
        strategic_fit = await self._evaluate_strategic_fit(
            needs
        )

        # Size market opportunity
        market_opportunity = await self._size_market_opportunity(
            needs
        )

        # Analyze competitive positioning
        competitive_analysis = await self._analyze_competitive_positioning(
            needs
        )

        # Estimate resource requirements
        resource_requirements = await self._estimate_resource_requirements(
            needs
        )

        # Assess risks
        risk_assessment = await self._assess_risks(
            needs, risk_tolerance
        )

        # Calculate ROI projections
        roi_projections = await self._calculate_roi_projections(
            needs, resource_requirements, market_opportunity
        )

        # Generate recommendations
        recommendations = await self._generate_strategic_recommendations(
            feasibility_results,
            strategic_fit,
            market_opportunity,
            competitive_analysis,
            resource_requirements,
            risk_assessment,
            roi_projections,
            budget,
            time_horizon
        )

        # Create implementation roadmap
        roadmap = await self._create_implementation_roadmap(
            recommendations, time_horizon
        )

        # Calculate execution metrics
        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        # Calculate KPIs
        total_opportunity_value = sum(
            opp["revenue_potential_max"] for opp in market_opportunity
        )
        avg_strategic_fit = sum(
            fit["strategic_fit_score"] for fit in strategic_fit
        ) / len(strategic_fit) if strategic_fit else 0

        # Prepare results
        result = {
            "assessment_overview": {
                "execution_date": execution_start.isoformat(),
                "needs_evaluated": len(needs),
                "budget_available": budget,
                "time_horizon_months": time_horizon,
                "risk_tolerance": risk_tolerance
            },
            "feasibility_analysis": feasibility_results,
            "strategic_fit_evaluation": strategic_fit,
            "market_opportunity_sizing": market_opportunity,
            "competitive_analysis": competitive_analysis,
            "resource_requirements": resource_requirements,
            "risk_assessment": risk_assessment,
            "roi_projections": roi_projections,
            "recommendations": recommendations,
            "implementation_roadmap": roadmap,
            "executive_summary": self._create_executive_summary(
                recommendations, market_opportunity, roi_projections
            ),
            "kpis": {
                "needs_assessed": len(needs),
                "opportunity_value_usd": total_opportunity_value,
                "recommendation_confidence": round(random.uniform(82.0, 94.0), 1),
                "strategic_fit_score": round(avg_strategic_fit, 1),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    def _get_mock_needs(self) -> List[Dict[str, Any]]:
        """Generate mock needs data if not provided."""
        return [
            {"need_id": "N009", "statement": "Automate repetitive tasks", "priority_level": "Critical"},
            {"need_id": "N003", "statement": "Integrate with existing tools", "priority_level": "Critical"},
            {"need_id": "N007", "statement": "Ensure data security", "priority_level": "Critical"},
            {"need_id": "N001", "statement": "Reduce manual data entry", "priority_level": "High"},
            {"need_id": "N004", "statement": "Advanced analytics", "priority_level": "High"},
            {"need_id": "N005", "statement": "Quick onboarding", "priority_level": "High"},
            {"need_id": "N008", "statement": "Real-time collaboration", "priority_level": "High"},
            {"need_id": "N002", "statement": "Mobile access", "priority_level": "Medium"}
        ]

    async def _assess_feasibility(
        self,
        needs: List[Dict[str, Any]],
        capabilities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess technical, operational, and financial feasibility."""
        await asyncio.sleep(0.1)  # Simulate analysis

        feasibility_assessments = []
        for need in needs:
            # Generate feasibility scores
            technical_feasibility = round(random.uniform(6.0, 9.5), 1)
            operational_feasibility = round(random.uniform(6.5, 9.2), 1)
            financial_feasibility = round(random.uniform(5.5, 9.0), 1)

            overall_feasibility = (
                technical_feasibility * 0.4 +
                operational_feasibility * 0.3 +
                financial_feasibility * 0.3
            )

            # Determine complexity and barriers
            if overall_feasibility >= 8.0:
                complexity = "Low"
                barriers = ["None significant"]
            elif overall_feasibility >= 6.5:
                complexity = "Medium"
                barriers = ["Resource constraints", "Integration complexity"]
            else:
                complexity = "High"
                barriers = ["Technical challenges", "High investment required", "Long development timeline"]

            assessment = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "technical_feasibility": technical_feasibility,
                "operational_feasibility": operational_feasibility,
                "financial_feasibility": financial_feasibility,
                "overall_feasibility_score": round(overall_feasibility, 1),
                "complexity": complexity,
                "primary_barriers": barriers,
                "build_vs_buy_recommendation": random.choice(["Build", "Buy", "Partner", "Build + Partner"]),
                "estimated_development_time_months": random.randint(3, 18),
                "feasibility_confidence": round(random.uniform(75.0, 95.0), 1)
            }
            feasibility_assessments.append(assessment)

        # Sort by overall feasibility
        feasibility_assessments.sort(key=lambda x: x["overall_feasibility_score"], reverse=True)

        return feasibility_assessments

    async def _evaluate_strategic_fit(
        self,
        needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate how well each need aligns with strategic objectives."""
        await asyncio.sleep(0.1)  # Simulate evaluation

        strategic_evaluations = []
        for need in needs:
            # Score different strategic dimensions
            vision_alignment = round(random.uniform(6.5, 9.8), 1)
            capability_fit = round(random.uniform(6.0, 9.2), 1)
            market_positioning = round(random.uniform(7.0, 9.5), 1)
            differentiation_potential = round(random.uniform(6.5, 9.3), 1)

            strategic_fit_score = (
                vision_alignment * 0.3 +
                capability_fit * 0.25 +
                market_positioning * 0.25 +
                differentiation_potential * 0.2
            )

            # Determine strategic value tier
            if strategic_fit_score >= 8.5:
                tier = "Strategic Imperative"
            elif strategic_fit_score >= 7.5:
                tier = "High Strategic Value"
            elif strategic_fit_score >= 6.5:
                tier = "Moderate Strategic Value"
            else:
                tier = "Low Strategic Value"

            evaluation = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "vision_alignment_score": vision_alignment,
                "capability_fit_score": capability_fit,
                "market_positioning_score": market_positioning,
                "differentiation_potential_score": differentiation_potential,
                "strategic_fit_score": round(strategic_fit_score, 1),
                "strategic_value_tier": tier,
                "competitive_advantage": random.choice([
                    "Strong differentiator",
                    "Moderate differentiation",
                    "Table stakes requirement",
                    "Parity with competition"
                ])
            }
            strategic_evaluations.append(evaluation)

        # Sort by strategic fit score
        strategic_evaluations.sort(key=lambda x: x["strategic_fit_score"], reverse=True)

        return strategic_evaluations

    async def _size_market_opportunity(
        self,
        needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Size the market opportunity for addressing each need."""
        await asyncio.sleep(0.1)  # Simulate market sizing

        opportunities = []
        for need in needs:
            # Generate market sizing estimates
            tam = random.randint(500000000, 5000000000)
            sam = int(tam * random.uniform(0.15, 0.35))
            som = int(sam * random.uniform(0.08, 0.25))

            # Revenue projections
            year1_revenue = random.randint(2000000, 15000000)
            year3_revenue = int(year1_revenue * random.uniform(2.5, 5.0))

            opportunity = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "total_addressable_market_usd": tam,
                "serviceable_addressable_market_usd": sam,
                "serviceable_obtainable_market_usd": som,
                "revenue_potential_year1": year1_revenue,
                "revenue_potential_year3": year3_revenue,
                "revenue_potential_max": som,
                "market_growth_rate_cagr": round(random.uniform(12.0, 35.0), 1),
                "customer_acquisition_potential": random.randint(500, 5000),
                "average_deal_size": random.randint(15000, 85000),
                "market_maturity": random.choice(["Emerging", "Growth", "Mature"]),
                "opportunity_window": random.choice(["Immediate", "Near-term (6-12mo)", "Long-term (12-24mo)"])
            }
            opportunities.append(opportunity)

        # Sort by SOM
        opportunities.sort(key=lambda x: x["serviceable_obtainable_market_usd"], reverse=True)

        return opportunities

    async def _analyze_competitive_positioning(
        self,
        needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze competitive landscape for each need."""
        await asyncio.sleep(0.1)  # Simulate competitive analysis

        competitive_insights = []
        for need in needs:
            # Generate competitive metrics
            num_competitors = random.randint(3, 15)
            market_leader_share = round(random.uniform(18.0, 42.0), 1)

            positioning = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "number_of_competitors": num_competitors,
                "market_leader_share_pct": market_leader_share,
                "competitive_intensity": random.choice(["Low", "Moderate", "High", "Very High"]),
                "current_satisfaction_level": round(random.uniform(4.5, 7.2), 1) / 10,
                "unmet_need_gap": round(random.uniform(25.0, 75.0), 1),
                "our_current_capability": random.choice(["None", "Weak", "Moderate", "Strong"]),
                "differentiation_opportunity": random.choice(["Low", "Medium", "High", "Very High"]),
                "competitive_response_time": random.choice(["Fast (3-6mo)", "Moderate (6-12mo)", "Slow (12-18mo)"]),
                "barrier_to_entry": random.choice(["Low", "Medium", "High"])
            }
            competitive_insights.append(positioning)

        return competitive_insights

    async def _estimate_resource_requirements(
        self,
        needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Estimate resources needed to address each need."""
        await asyncio.sleep(0.1)  # Simulate resource estimation

        resource_estimates = []
        for need in needs:
            development_cost = random.randint(200000, 3000000)

            estimate = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "total_investment_required": development_cost,
                "development_cost": development_cost,
                "ongoing_operational_cost_annual": int(development_cost * random.uniform(0.15, 0.30)),
                "engineering_resources": {
                    "frontend_engineers": random.randint(1, 4),
                    "backend_engineers": random.randint(1, 5),
                    "designers": random.randint(1, 2),
                    "qa_engineers": random.randint(1, 3)
                },
                "timeline_months": random.randint(4, 18),
                "dependencies": random.sample([
                    "Platform infrastructure upgrade",
                    "Third-party API integration",
                    "Data pipeline enhancement",
                    "Security audit and certification",
                    "None - standalone feature"
                ], random.randint(0, 3)),
                "risk_contingency_pct": round(random.uniform(15.0, 35.0), 1)
            }
            resource_estimates.append(estimate)

        return resource_estimates

    async def _assess_risks(
        self,
        needs: List[Dict[str, Any]],
        risk_tolerance: str
    ) -> List[Dict[str, Any]]:
        """Assess risks associated with addressing each need."""
        await asyncio.sleep(0.1)  # Simulate risk assessment

        risk_assessments = []
        for need in needs:
            # Generate risk scores
            technical_risk = round(random.uniform(2.0, 8.0), 1)
            market_risk = round(random.uniform(2.5, 7.5), 1)
            execution_risk = round(random.uniform(3.0, 8.5), 1)
            financial_risk = round(random.uniform(2.0, 7.0), 1)

            overall_risk_score = (
                technical_risk * 0.3 +
                market_risk * 0.25 +
                execution_risk * 0.25 +
                financial_risk * 0.2
            )

            if overall_risk_score >= 7.0:
                risk_level = "High"
            elif overall_risk_score >= 5.0:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            assessment = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "technical_risk_score": technical_risk,
                "market_risk_score": market_risk,
                "execution_risk_score": execution_risk,
                "financial_risk_score": financial_risk,
                "overall_risk_score": round(overall_risk_score, 1),
                "risk_level": risk_level,
                "key_risks": random.sample([
                    "Technical complexity higher than estimated",
                    "Market adoption slower than projected",
                    "Resource availability constraints",
                    "Competitive response faster than expected",
                    "Integration challenges with existing systems",
                    "Regulatory compliance requirements"
                ], random.randint(2, 4)),
                "mitigation_strategies": random.sample([
                    "Phased rollout approach",
                    "Early customer validation program",
                    "Partner with specialized vendor",
                    "Invest in additional technical expertise",
                    "Build MVP to test market",
                    "Secure executive sponsorship"
                ], random.randint(2, 3))
            }
            risk_assessments.append(assessment)

        return risk_assessments

    async def _calculate_roi_projections(
        self,
        needs: List[Dict[str, Any]],
        resource_reqs: List[Dict[str, Any]],
        market_opps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate ROI projections for addressing each need."""
        await asyncio.sleep(0.1)  # Simulate ROI calculation

        roi_projections = []
        for i, need in enumerate(needs):
            investment = resource_reqs[i]["total_investment_required"] if i < len(resource_reqs) else 1000000
            revenue_y1 = market_opps[i]["revenue_potential_year1"] if i < len(market_opps) else 5000000
            revenue_y3 = market_opps[i]["revenue_potential_year3"] if i < len(market_opps) else 15000000

            # Calculate payback period
            monthly_revenue = revenue_y1 / 12
            payback_months = investment / monthly_revenue if monthly_revenue > 0 else 999

            # Calculate NPV (simple version)
            discount_rate = 0.12
            npv = -investment
            for year in range(1, 4):
                year_revenue = revenue_y1 * (1.5 ** (year - 1))
                npv += year_revenue / ((1 + discount_rate) ** year)

            projection = {
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "total_investment": investment,
                "projected_revenue_year1": revenue_y1,
                "projected_revenue_year3": revenue_y3,
                "payback_period_months": round(payback_months, 1),
                "roi_year1_pct": round(((revenue_y1 - investment) / investment) * 100, 1),
                "roi_year3_pct": round(((revenue_y3 - investment) / investment) * 100, 1),
                "npv_3year": int(npv),
                "irr_pct": round(random.uniform(25.0, 85.0), 1),
                "ltv_cac_ratio": round(random.uniform(2.5, 6.5), 1),
                "financial_viability": "Strong" if npv > investment else "Moderate" if npv > 0 else "Weak"
            }
            roi_projections.append(projection)

        return roi_projections

    async def _generate_strategic_recommendations(
        self,
        feasibility: List[Dict[str, Any]],
        strategic_fit: List[Dict[str, Any]],
        market_opp: List[Dict[str, Any]],
        competitive: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        roi: List[Dict[str, Any]],
        budget: float,
        time_horizon: int
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on all assessments."""
        await asyncio.sleep(0.1)  # Simulate recommendation generation

        # Score each need across all dimensions
        need_scores = []
        for i in range(len(feasibility)):
            total_score = (
                feasibility[i]["overall_feasibility_score"] * 0.25 +
                strategic_fit[i]["strategic_fit_score"] * 0.25 +
                (roi[i]["roi_year3_pct"] / 100) * 0.20 +  # Normalize ROI
                (10 - risks[i]["overall_risk_score"]) * 0.15 +  # Invert risk
                (market_opp[i]["market_growth_rate_cagr"] / 10) * 0.15  # Normalize growth rate
            )

            need_scores.append({
                "need_id": feasibility[i]["need_id"],
                "need_statement": feasibility[i]["need_statement"],
                "total_score": round(total_score, 2),
                "feasibility_score": feasibility[i]["overall_feasibility_score"],
                "strategic_fit_score": strategic_fit[i]["strategic_fit_score"],
                "market_opportunity_score": round(market_opp[i]["market_growth_rate_cagr"] / 10, 1),
                "risk_adjusted_score": round(10 - risks[i]["overall_risk_score"], 1),
                "roi_score": round(roi[i]["roi_year3_pct"] / 100, 1)
            })

        # Sort by total score
        need_scores.sort(key=lambda x: x["total_score"], reverse=True)

        # Generate recommendations
        recommendations = []
        cumulative_investment = 0

        for i, scored_need in enumerate(need_scores):
            need_idx = next(idx for idx, f in enumerate(feasibility) if f["need_id"] == scored_need["need_id"])
            investment_needed = resources[need_idx]["total_investment_required"]

            # Determine recommendation tier
            if i < 3 and cumulative_investment + investment_needed <= budget * 0.7:
                tier = "Must Have - Immediate Priority"
                timeline = "Q1-Q2"
                cumulative_investment += investment_needed
            elif i < 6 and cumulative_investment + investment_needed <= budget:
                tier = "Should Have - High Priority"
                timeline = "Q2-Q3"
                cumulative_investment += investment_needed
            elif i < 10:
                tier = "Could Have - Medium Priority"
                timeline = "Q3-Q4"
            else:
                tier = "Won't Have - Future Consideration"
                timeline = "Beyond current planning horizon"

            recommendation = {
                "rank": i + 1,
                "need_id": scored_need["need_id"],
                "need_statement": scored_need["need_statement"],
                "recommendation_tier": tier,
                "suggested_timeline": timeline,
                "overall_score": scored_need["total_score"],
                "key_rationale": self._generate_rationale(scored_need, feasibility[need_idx], strategic_fit[need_idx]),
                "investment_required": investment_needed,
                "expected_return": roi[need_idx]["projected_revenue_year3"],
                "confidence_level": round(random.uniform(78.0, 95.0), 1),
                "critical_success_factors": random.sample([
                    "Executive sponsorship and commitment",
                    "Cross-functional team alignment",
                    "Early customer validation",
                    "Agile development approach",
                    "Clear success metrics and milestones"
                ], 3)
            }
            recommendations.append(recommendation)

        return recommendations

    def _generate_rationale(
        self,
        scored_need: Dict[str, Any],
        feasibility: Dict[str, Any],
        strategic: Dict[str, Any]
    ) -> str:
        """Generate rationale for recommendation."""
        rationale_parts = []

        if feasibility["overall_feasibility_score"] >= 8.0:
            rationale_parts.append(f"High feasibility ({feasibility['overall_feasibility_score']}/10)")

        if strategic["strategic_fit_score"] >= 8.0:
            rationale_parts.append(f"Strong strategic alignment ({strategic['strategic_value_tier']})")

        if scored_need["roi_score"] >= 2.0:
            rationale_parts.append("Excellent ROI potential")

        if not rationale_parts:
            rationale_parts.append("Balanced opportunity across all dimensions")

        return "; ".join(rationale_parts)

    async def _create_implementation_roadmap(
        self,
        recommendations: List[Dict[str, Any]],
        time_horizon: int
    ) -> Dict[str, Any]:
        """Create implementation roadmap based on recommendations."""
        await asyncio.sleep(0.1)  # Simulate roadmap creation

        # Group by quarter
        roadmap = {
            "Q1": {"theme": "Foundation & Quick Wins", "initiatives": []},
            "Q2": {"theme": "Core Capabilities", "initiatives": []},
            "Q3": {"theme": "Advanced Features", "initiatives": []},
            "Q4": {"theme": "Optimization & Scale", "initiatives": []}
        }

        for rec in recommendations:
            if "Q1" in rec["suggested_timeline"]:
                roadmap["Q1"]["initiatives"].append({
                    "need": rec["need_statement"],
                    "priority": rec["recommendation_tier"],
                    "investment": rec["investment_required"]
                })
            elif "Q2" in rec["suggested_timeline"]:
                roadmap["Q2"]["initiatives"].append({
                    "need": rec["need_statement"],
                    "priority": rec["recommendation_tier"],
                    "investment": rec["investment_required"]
                })
            elif "Q3" in rec["suggested_timeline"]:
                roadmap["Q3"]["initiatives"].append({
                    "need": rec["need_statement"],
                    "priority": rec["recommendation_tier"],
                    "investment": rec["investment_required"]
                })
            elif "Q4" in rec["suggested_timeline"]:
                roadmap["Q4"]["initiatives"].append({
                    "need": rec["need_statement"],
                    "priority": rec["recommendation_tier"],
                    "investment": rec["investment_required"]
                })

        # Add summary metrics
        roadmap["summary"] = {
            "total_initiatives": len([r for r in recommendations if "Won't Have" not in r["recommendation_tier"]]),
            "high_priority_count": len([r for r in recommendations if "Must Have" in r["recommendation_tier"]]),
            "total_investment_planned": sum(r["investment_required"] for r in recommendations if "Won't Have" not in r["recommendation_tier"]),
            "expected_revenue_year3": sum(r["expected_return"] for r in recommendations[:6])
        }

        return roadmap

    def _create_executive_summary(
        self,
        recommendations: List[Dict[str, Any]],
        market_opps: List[Dict[str, Any]],
        roi_projections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create executive summary of assessment."""
        must_have_recs = [r for r in recommendations if "Must Have" in r["recommendation_tier"]]

        return {
            "key_findings": [
                f"Identified {len(recommendations)} customer needs with strategic value",
                f"{len(must_have_recs)} needs recommended for immediate investment",
                f"Total market opportunity exceeds ${sum(m['serviceable_obtainable_market_usd'] for m in market_opps[:5])/1e6:.0f}M",
                f"Average ROI for top recommendations: {sum(r['roi_year3_pct'] for r in roi_projections[:5])/5:.0f}%"
            ],
            "top_3_recommendations": [
                {
                    "need": rec["need_statement"],
                    "rationale": rec["key_rationale"],
                    "expected_return": f"${rec['expected_return']/1e6:.1f}M by Year 3"
                }
                for rec in recommendations[:3]
            ],
            "total_investment_recommended": sum(r["investment_required"] for r in must_have_recs),
            "expected_3year_revenue": sum(r["expected_return"] for r in must_have_recs),
            "strategic_impact": "High - Addresses critical customer needs with strong market opportunity",
            "risk_level": "Medium - Manageable risks with appropriate mitigation strategies"
        }


# Module export
__all__ = ['AssessNeedsAgent']
