"""
APQC PCF Agent: Segment and Analyze Potential Markets (1.1.3.1)

This agent identifies and segments potential market opportunities, creating
a comprehensive framework for market analysis and selection decisions.

Hierarchy:
- Category: 1.0 - Develop Vision and Strategy
- Process Group: 1.1 - Define the business concept and long-term vision
- Process: 1.1.3 - Select relevant markets
- Activity: 1.1.3.1 - Segment and analyze potential markets

Element ID: 10035 (process level, activity level TBD)
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


class SegmentMarketsAgent(ActivityAgentBase):
    """
    Agent for market segmentation and analysis.

    This agent identifies and analyzes potential market segments using multiple
    segmentation approaches:
    - Geographic segmentation (regions, countries, urban/rural)
    - Demographic segmentation (age, income, company size)
    - Psychographic segmentation (values, lifestyle, attitudes)
    - Behavioral segmentation (usage patterns, benefits sought)
    - Firmographic segmentation (B2B - industry, company size, revenue)

    Capabilities:
    - Multi-dimensional market segmentation
    - Segment profiling and characterization
    - Market size estimation per segment
    - Segment accessibility and reach analysis
    - Segment differentiation assessment
    - Actionability evaluation
    - Segment growth trend analysis

    Outputs:
    - Complete segment taxonomy
    - Detailed segment profiles
    - Size and growth metrics
    - Accessibility ratings
    - Differentiation scores
    - Actionability assessments
    - KPI tracking (segments identified, coverage, differentiation)
    """

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        """Create the default configuration for this agent."""
        metadata = PCFMetadata(
            pcf_element_id="10035",  # Process level (no specific activity ID yet)
            hierarchy_id="1.1.3.1",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.3",
            process_name="Select relevant markets",
            activity_id="1.1.3.1",
            activity_name="Segment and analyze potential markets",
            parent_element_id="10035",
            kpis=[
                {"name": "segments_identified", "type": "count", "unit": "number"},
                {"name": "market_coverage_pct", "type": "percentage", "unit": "%"},
                {"name": "avg_differentiation_score", "type": "score", "unit": "0-10"},
                {"name": "actionable_segments", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="segment_markets_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Segment and analyze potential markets.

        Args:
            input_data: Segmentation parameters including:
                - market_scope: Geographic scope for analysis
                - segmentation_approach: B2B, B2C, or Both
                - segmentation_bases: Specific bases to use (geographic, demographic, etc.)
                - minimum_segment_size: Minimum size to be considered viable
                - product_category: Product/service category context

        Returns:
            Comprehensive market segmentation with segment profiles and analysis
        """
        execution_start = datetime.utcnow()

        # Extract input parameters
        market_scope = input_data.get("market_scope", "North America")
        approach = input_data.get("segmentation_approach", "B2B")
        bases = input_data.get("segmentation_bases", [
            "firmographic", "behavioral", "geographic"
        ])
        min_size = input_data.get("minimum_segment_size", 100000000)  # $100M minimum
        product_category = input_data.get("product_category", "Enterprise Software")

        # Perform segmentation
        if approach in ["B2B", "Both"]:
            b2b_segments = await self._segment_b2b_markets(
                market_scope, bases, min_size
            )
        else:
            b2b_segments = []

        if approach in ["B2C", "Both"]:
            b2c_segments = await self._segment_b2c_markets(
                market_scope, bases, min_size
            )
        else:
            b2c_segments = []

        all_segments = b2b_segments + b2c_segments

        # Analyze each segment
        segment_profiles = await self._profile_segments(
            all_segments, product_category
        )

        # Assess segment viability
        viability_assessment = await self._assess_segment_viability(
            segment_profiles
        )

        # Create segment comparison matrix
        comparison_matrix = await self._create_comparison_matrix(
            segment_profiles
        )

        # Identify high-potential segments
        high_potential = await self._identify_high_potential_segments(
            segment_profiles, viability_assessment
        )

        # Calculate execution metrics
        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        # Calculate KPIs
        total_segments = len(all_segments)
        actionable_count = len([s for s in viability_assessment if s["is_actionable"]])
        avg_differentiation = sum(s["differentiation_score"] for s in segment_profiles) / len(segment_profiles) if segment_profiles else 0
        total_market_size = sum(s["market_size_usd"] for s in segment_profiles)
        covered_market = sum(s["market_size_usd"] for s in segment_profiles if s.get("is_viable", True))
        coverage_pct = (covered_market / total_market_size * 100) if total_market_size > 0 else 0

        # Prepare results
        result = {
            "segmentation_overview": {
                "execution_date": execution_start.isoformat(),
                "market_scope": market_scope,
                "segmentation_approach": approach,
                "bases_used": bases,
                "total_segments_identified": total_segments,
                "actionable_segments": actionable_count
            },
            "segment_taxonomy": {
                "b2b_segments": len(b2b_segments),
                "b2c_segments": len(b2c_segments),
                "total": total_segments
            },
            "segment_profiles": segment_profiles,
            "viability_assessment": viability_assessment,
            "comparison_matrix": comparison_matrix,
            "high_potential_segments": high_potential,
            "market_insights": {
                "total_addressable_market": total_market_size,
                "viable_market_coverage": round(coverage_pct, 1),
                "average_segment_growth_rate": round(
                    sum(s["growth_rate_cagr"] for s in segment_profiles) / len(segment_profiles), 1
                ) if segment_profiles else 0,
                "competitive_intensity_distribution": self._analyze_competitive_distribution(segment_profiles)
            },
            "kpis": {
                "segments_identified": total_segments,
                "market_coverage_pct": round(coverage_pct, 1),
                "avg_differentiation_score": round(avg_differentiation, 1),
                "actionable_segments": actionable_count,
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _segment_b2b_markets(
        self,
        scope: str,
        bases: List[str],
        min_size: float
    ) -> List[Dict[str, Any]]:
        """Segment B2B markets based on firmographics and behavior."""
        await asyncio.sleep(0.1)  # Simulate segmentation

        segments = []

        # Segment by company size (firmographic)
        if "firmographic" in bases:
            segments.extend([
                {
                    "segment_id": "B2B_ENT_001",
                    "name": "Large Enterprise",
                    "type": "B2B",
                    "basis": "Firmographic - Company Size",
                    "criteria": "10,000+ employees, $1B+ revenue",
                    "description": "Fortune 1000 and global enterprises"
                },
                {
                    "segment_id": "B2B_MID_001",
                    "name": "Mid-Market",
                    "type": "B2B",
                    "basis": "Firmographic - Company Size",
                    "criteria": "500-10,000 employees, $50M-$1B revenue",
                    "description": "Growing mid-sized businesses"
                },
                {
                    "segment_id": "B2B_SMB_001",
                    "name": "Small Business",
                    "type": "B2B",
                    "basis": "Firmographic - Company Size",
                    "criteria": "10-500 employees, $1M-$50M revenue",
                    "description": "Small and medium businesses"
                }
            ])

        # Segment by industry vertical (firmographic)
        if "firmographic" in bases or "behavioral" in bases:
            segments.extend([
                {
                    "segment_id": "B2B_IND_001",
                    "name": "Financial Services",
                    "type": "B2B",
                    "basis": "Firmographic - Industry",
                    "criteria": "Banks, insurance, fintech",
                    "description": "Highly regulated, security-focused"
                },
                {
                    "segment_id": "B2B_IND_002",
                    "name": "Healthcare & Life Sciences",
                    "type": "B2B",
                    "basis": "Firmographic - Industry",
                    "criteria": "Hospitals, pharma, biotech, medical devices",
                    "description": "Compliance-heavy, patient data sensitive"
                },
                {
                    "segment_id": "B2B_IND_003",
                    "name": "Technology & SaaS",
                    "type": "B2B",
                    "basis": "Firmographic - Industry",
                    "criteria": "Software, IT services, tech companies",
                    "description": "Innovation-focused, fast-paced"
                },
                {
                    "segment_id": "B2B_IND_004",
                    "name": "Manufacturing & Supply Chain",
                    "type": "B2B",
                    "basis": "Firmographic - Industry",
                    "criteria": "Manufacturing, logistics, distribution",
                    "description": "Process-oriented, efficiency-driven"
                }
            ])

        # Segment by digital maturity (behavioral)
        if "behavioral" in bases:
            segments.extend([
                {
                    "segment_id": "B2B_MAT_001",
                    "name": "Digital Leaders",
                    "type": "B2B",
                    "basis": "Behavioral - Digital Maturity",
                    "criteria": "Advanced digital adoption, cloud-first",
                    "description": "Early adopters, innovation-driven"
                },
                {
                    "segment_id": "B2B_MAT_002",
                    "name": "Digital Followers",
                    "type": "B2B",
                    "basis": "Behavioral - Digital Maturity",
                    "criteria": "Moderate digital adoption, in transition",
                    "description": "Actively modernizing, pragmatic"
                }
            ])

        return segments

    async def _segment_b2c_markets(
        self,
        scope: str,
        bases: List[str],
        min_size: float
    ) -> List[Dict[str, Any]]:
        """Segment B2C markets based on demographics and psychographics."""
        await asyncio.sleep(0.1)  # Simulate segmentation

        segments = []

        # Demographic segmentation
        if "demographic" in bases:
            segments.extend([
                {
                    "segment_id": "B2C_DEM_001",
                    "name": "Gen Z (18-26)",
                    "type": "B2C",
                    "basis": "Demographic - Age",
                    "criteria": "Born 1997-2006, digital natives",
                    "description": "Mobile-first, value authenticity and experiences"
                },
                {
                    "segment_id": "B2C_DEM_002",
                    "name": "Millennials (27-42)",
                    "type": "B2C",
                    "basis": "Demographic - Age",
                    "criteria": "Born 1981-1996, tech-savvy",
                    "description": "Career-focused, value work-life balance"
                },
                {
                    "segment_id": "B2C_DEM_003",
                    "name": "Gen X (43-58)",
                    "type": "B2C",
                    "basis": "Demographic - Age",
                    "criteria": "Born 1965-1980, pragmatic",
                    "description": "Independent, value quality and reliability"
                }
            ])

        return segments

    async def _profile_segments(
        self,
        segments: List[Dict[str, Any]],
        product_category: str
    ) -> List[Dict[str, Any]]:
        """Create detailed profiles for each segment."""
        await asyncio.sleep(0.1)  # Simulate profiling

        profiles = []
        for segment in segments:
            # Generate market size
            if segment["type"] == "B2B":
                base_size = random.randint(200000000, 3000000000)
            else:
                base_size = random.randint(500000000, 5000000000)

            profile = {
                **segment,
                "market_size_usd": base_size,
                "growth_rate_cagr": round(random.uniform(5.0, 28.0), 1),
                "customer_count_estimate": random.randint(5000, 250000),
                "average_customer_value": base_size // random.randint(5000, 250000),
                "geographic_concentration": random.choice([
                    "Highly concentrated (Top 3 metros: 65%+)",
                    "Moderately concentrated (Top 10 metros: 55%)",
                    "Distributed nationally",
                    "Global with regional hubs"
                ]),
                "accessibility": {
                    "reach_difficulty": random.choice(["Easy", "Moderate", "Difficult"]),
                    "channel_options": random.sample([
                        "Direct sales", "Channel partners", "Online/digital",
                        "Inside sales", "Marketplaces", "Referrals"
                    ], random.randint(2, 4)),
                    "marketing_channels": random.sample([
                        "Search/SEO", "Social media", "Events/conferences",
                        "Content marketing", "Account-based marketing", "PR"
                    ], random.randint(2, 5))
                },
                "differentiation_score": round(random.uniform(4.5, 9.2), 1),
                "competitive_intensity": random.choice(["Low", "Moderate", "High", "Very High"]),
                "key_buying_criteria": random.sample([
                    "Price/value", "Features/functionality", "Brand reputation",
                    "Customer service", "Integration capabilities",
                    "Scalability", "Security", "Ease of use"
                ], random.randint(3, 5)),
                "purchase_cycle": {
                    "typical_length_days": random.randint(30, 365),
                    "decision_complexity": random.choice(["Low", "Medium", "High"]),
                    "stakeholder_count": random.randint(1, 12)
                }
            }
            profiles.append(profile)

        return profiles

    async def _assess_segment_viability(
        self,
        profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assess viability of each segment."""
        await asyncio.sleep(0.1)  # Simulate assessment

        assessments = []
        for profile in profiles:
            # Viability scoring
            size_score = min(10, (profile["market_size_usd"] / 500000000) * 10)
            growth_score = min(10, (profile["growth_rate_cagr"] / 20) * 10)
            access_score = {"Easy": 9.0, "Moderate": 6.5, "Difficult": 4.0}[
                profile["accessibility"]["reach_difficulty"]
            ]
            comp_score = {"Low": 9.0, "Moderate": 7.0, "High": 5.0, "Very High": 3.0}[
                profile["competitive_intensity"]
            ]

            viability_score = (
                size_score * 0.3 +
                growth_score * 0.25 +
                access_score * 0.25 +
                comp_score * 0.20
            )

            # Determine if actionable
            is_actionable = (
                viability_score >= 6.0 and
                profile["market_size_usd"] >= 100000000 and
                profile["accessibility"]["reach_difficulty"] != "Difficult"
            )

            assessment = {
                "segment_id": profile["segment_id"],
                "segment_name": profile["name"],
                "viability_score": round(viability_score, 1),
                "is_actionable": is_actionable,
                "strengths": [],
                "challenges": [],
                "entry_barriers": []
            }

            # Add strengths
            if profile["market_size_usd"] > 1000000000:
                assessment["strengths"].append("Large market size ($1B+)")
            if profile["growth_rate_cagr"] > 15:
                assessment["strengths"].append(f"High growth ({profile['growth_rate_cagr']}% CAGR)")
            if profile["differentiation_score"] > 7.5:
                assessment["strengths"].append("Strong differentiation potential")

            # Add challenges
            if profile["competitive_intensity"] in ["High", "Very High"]:
                assessment["challenges"].append("Intense competition")
            if profile["accessibility"]["reach_difficulty"] == "Difficult":
                assessment["challenges"].append("Difficult to reach")
            if profile["purchase_cycle"]["decision_complexity"] == "High":
                assessment["challenges"].append("Complex buying process")

            # Add barriers
            if profile["competitive_intensity"] == "Very High":
                assessment["entry_barriers"].append("Entrenched competitors")
            if len(profile["accessibility"]["channel_options"]) < 3:
                assessment["entry_barriers"].append("Limited distribution channels")

            assessments.append(assessment)

        return assessments

    async def _create_comparison_matrix(
        self,
        profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create comparison matrix for segments."""
        await asyncio.sleep(0.05)  # Simulate matrix creation

        matrix = {
            "dimensions": [
                "Market Size",
                "Growth Rate",
                "Accessibility",
                "Competition",
                "Differentiation"
            ],
            "segments": []
        }

        for profile in profiles:
            matrix["segments"].append({
                "segment_id": profile["segment_id"],
                "segment_name": profile["name"],
                "scores": {
                    "Market Size": round((profile["market_size_usd"] / 5000000000) * 10, 1),
                    "Growth Rate": round((profile["growth_rate_cagr"] / 30) * 10, 1),
                    "Accessibility": {"Easy": 9, "Moderate": 6, "Difficult": 3}[
                        profile["accessibility"]["reach_difficulty"]
                    ],
                    "Competition": {"Low": 9, "Moderate": 6, "High": 4, "Very High": 2}[
                        profile["competitive_intensity"]
                    ],
                    "Differentiation": profile["differentiation_score"]
                }
            })

        return matrix

    async def _identify_high_potential_segments(
        self,
        profiles: List[Dict[str, Any]],
        assessments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify high-potential segments for targeting."""
        await asyncio.sleep(0.05)  # Simulate identification

        # Sort by viability score
        sorted_assessments = sorted(assessments, key=lambda x: x["viability_score"], reverse=True)

        high_potential = []
        for assessment in sorted_assessments[:5]:  # Top 5
            profile = next(p for p in profiles if p["segment_id"] == assessment["segment_id"])

            high_potential.append({
                "rank": len(high_potential) + 1,
                "segment_id": assessment["segment_id"],
                "segment_name": assessment["segment_name"],
                "viability_score": assessment["viability_score"],
                "market_size_usd": profile["market_size_usd"],
                "growth_rate_cagr": profile["growth_rate_cagr"],
                "key_rationale": self._generate_segment_rationale(profile, assessment),
                "recommended_action": "Deep dive analysis" if assessment["is_actionable"] else "Monitor only"
            })

        return high_potential

    def _generate_segment_rationale(
        self,
        profile: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> str:
        """Generate rationale for high-potential segment."""
        reasons = []

        if profile["market_size_usd"] > 1000000000:
            reasons.append(f"Large market (${profile['market_size_usd']/1e9:.1f}B)")

        if profile["growth_rate_cagr"] > 15:
            reasons.append(f"Fast growth ({profile['growth_rate_cagr']}% CAGR)")

        if profile["competitive_intensity"] in ["Low", "Moderate"]:
            reasons.append(f"{profile['competitive_intensity']} competition")

        if profile["differentiation_score"] > 7.5:
            reasons.append("Strong differentiation opportunity")

        return "; ".join(reasons) if reasons else "Balanced opportunity"

    def _analyze_competitive_distribution(
        self,
        profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze competitive intensity distribution."""
        distribution = {"Low": 0, "Moderate": 0, "High": 0, "Very High": 0}

        for profile in profiles:
            distribution[profile["competitive_intensity"]] += 1

        total = len(profiles)
        return {
            level: {"count": count, "percentage": round((count / total) * 100, 1) if total > 0 else 0}
            for level, count in distribution.items()
        }


# Module export
__all__ = ['SegmentMarketsAgent']
