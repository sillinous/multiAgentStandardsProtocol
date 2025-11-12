"""
APQC PCF Agent: Capture Customer Needs and Wants (1.1.2.2)

This agent systematically identifies, documents, and categorizes customer needs
and wants across different segments, creating a comprehensive understanding of
customer requirements for product and service development.

Hierarchy:
- Category: 1.0 - Develop Vision and Strategy
- Process Group: 1.1 - Define the business concept and long-term vision
- Process: 1.1.2 - Survey market and determine customer needs and wants
- Activity: 1.1.2.2 - Capture customer needs and wants

Element ID: 19946
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


class CaptureNeedsAgent(ActivityAgentBase):
    """
    Agent for capturing and documenting customer needs and wants.

    This agent synthesizes research data, customer feedback, and market intelligence
    to create a structured catalog of customer needs across different dimensions:
    - Functional needs (what customers need the product/service to do)
    - Emotional needs (how customers want to feel)
    - Social needs (how customers want to be perceived)
    - Aspirational wants (what customers desire for the future)

    Capabilities:
    - Need identification from multiple sources
    - Need categorization (Kano model, Jobs-to-be-Done)
    - Priority ranking (must-have, performance, delighter)
    - Segment-specific need mapping
    - Voice-of-customer synthesis
    - Unmet need identification
    - Need-to-feature mapping
    - Gap analysis

    Outputs:
    - Comprehensive need catalog
    - Segment-specific needs
    - Priority rankings
    - Need categories and types
    - Unmet needs list
    - Feature mapping suggestions
    - KPI tracking (needs identified, segment coverage, priority needs)
    """

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        """Create the default configuration for this agent."""
        metadata = PCFMetadata(
            pcf_element_id="19946",
            hierarchy_id="1.1.2.2",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.2",
            process_name="Survey market and determine customer needs and wants",
            activity_id="1.1.2.2",
            activity_name="Capture customer needs and wants",
            parent_element_id="10030",
            kpis=[
                {"name": "needs_identified", "type": "count", "unit": "number"},
                {"name": "segment_coverage", "type": "percentage", "unit": "%"},
                {"name": "priority_needs_count", "type": "count", "unit": "number"},
                {"name": "unmet_needs_count", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="capture_needs_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture and categorize customer needs and wants.

        Args:
            input_data: Need capture parameters including:
                - research_data: Research findings (optional, from agent 1.1.2.1)
                - customer_segments: Target segments to analyze
                - data_sources: List of data sources (surveys, interviews, feedback, etc.)
                - categorization_framework: Framework to use (Kano, JTBD, etc.)
                - include_wants: Whether to capture aspirational wants (default: True)

        Returns:
            Comprehensive catalog of customer needs and wants with priorities
        """
        execution_start = datetime.utcnow()

        # Extract input parameters
        segments = input_data.get("customer_segments", ["Enterprise", "Mid-Market", "SMB"])
        data_sources = input_data.get("data_sources", [
            "Customer interviews",
            "Survey responses",
            "Support tickets",
            "Sales feedback",
            "User analytics"
        ])
        framework = input_data.get("categorization_framework", "Kano")
        include_wants = input_data.get("include_wants", True)

        # Identify needs from data sources
        identified_needs = await self._identify_needs_from_sources(
            data_sources, segments
        )

        # Categorize needs by type
        categorized_needs = await self._categorize_needs(
            identified_needs, framework
        )

        # Prioritize needs
        prioritized_needs = await self._prioritize_needs(
            categorized_needs, segments
        )

        # Identify unmet needs
        unmet_needs = await self._identify_unmet_needs(
            prioritized_needs, segments
        )

        # Capture aspirational wants
        wants = {}
        if include_wants:
            wants = await self._capture_aspirational_wants(segments)

        # Map needs to potential features
        feature_mapping = await self._map_needs_to_features(
            prioritized_needs
        )

        # Perform segment analysis
        segment_analysis = await self._analyze_segment_needs(
            prioritized_needs, segments
        )

        # Calculate execution metrics
        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        # Calculate KPIs
        total_needs = sum(len(cat["needs"]) for cat in categorized_needs.values())
        priority_needs = sum(
            1 for need in prioritized_needs if need["priority_level"] in ["Critical", "High"]
        )
        unmet_count = len(unmet_needs)

        # Prepare results
        result = {
            "capture_overview": {
                "execution_date": execution_start.isoformat(),
                "segments_analyzed": segments,
                "data_sources_used": data_sources,
                "categorization_framework": framework,
                "includes_aspirational_wants": include_wants
            },
            "identified_needs": identified_needs,
            "categorized_needs": categorized_needs,
            "prioritized_needs": prioritized_needs,
            "unmet_needs": unmet_needs,
            "aspirational_wants": wants,
            "feature_mapping": feature_mapping,
            "segment_analysis": segment_analysis,
            "summary": {
                "total_needs_identified": total_needs,
                "critical_needs": priority_needs,
                "unmet_needs": unmet_count,
                "segments_covered": len(segments),
                "data_source_count": len(data_sources)
            },
            "kpis": {
                "needs_identified": total_needs,
                "segment_coverage": 100.0,  # All segments analyzed
                "priority_needs_count": priority_needs,
                "unmet_needs_count": unmet_count,
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _identify_needs_from_sources(
        self,
        sources: List[str],
        segments: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify raw needs from various data sources."""
        await asyncio.sleep(0.1)  # Simulate need extraction

        # Generate mock needs identified from different sources
        needs = [
            {
                "need_id": "N001",
                "statement": "Reduce time spent on manual data entry",
                "source": "Customer interviews",
                "frequency": "Very High",
                "affected_segments": segments,
                "evidence": "Mentioned by 87% of interview participants"
            },
            {
                "need_id": "N002",
                "statement": "Access system from mobile devices",
                "source": "Survey responses",
                "frequency": "High",
                "affected_segments": segments[1:] if len(segments) > 1 else segments,
                "evidence": "72% of survey respondents rated mobile access as important"
            },
            {
                "need_id": "N003",
                "statement": "Integrate seamlessly with existing tools",
                "source": "Customer interviews",
                "frequency": "Critical",
                "affected_segments": segments,
                "evidence": "Top pain point in qualitative research"
            },
            {
                "need_id": "N004",
                "statement": "Understand performance through analytics",
                "source": "Sales feedback",
                "frequency": "High",
                "affected_segments": [segments[0]] if segments else ["Enterprise"],
                "evidence": "Requested in 65% of enterprise sales calls"
            },
            {
                "need_id": "N005",
                "statement": "Onboard new users quickly without extensive training",
                "source": "Support tickets",
                "frequency": "Very High",
                "affected_segments": segments,
                "evidence": "34% of support tickets related to onboarding confusion"
            },
            {
                "need_id": "N006",
                "statement": "Customize workflows to match business processes",
                "source": "Customer interviews",
                "frequency": "High",
                "affected_segments": [segments[0]] if segments else ["Enterprise"],
                "evidence": "Critical requirement for 78% of enterprise customers"
            },
            {
                "need_id": "N007",
                "statement": "Ensure data security and compliance",
                "source": "Sales feedback",
                "frequency": "Critical",
                "affected_segments": segments,
                "evidence": "Required for all enterprise deals, increasing in SMB"
            },
            {
                "need_id": "N008",
                "statement": "Collaborate in real-time with team members",
                "source": "User analytics",
                "frequency": "High",
                "affected_segments": segments,
                "evidence": "Multi-user sessions represent 68% of usage time"
            },
            {
                "need_id": "N009",
                "statement": "Automate repetitive tasks and workflows",
                "source": "Customer interviews",
                "frequency": "Very High",
                "affected_segments": segments,
                "evidence": "Most frequently mentioned improvement (91% of participants)"
            },
            {
                "need_id": "N010",
                "statement": "Get responsive customer support when issues arise",
                "source": "Survey responses",
                "frequency": "High",
                "affected_segments": segments,
                "evidence": "Support quality rated as 2nd most important factor"
            },
            {
                "need_id": "N011",
                "statement": "Scale solution as business grows",
                "source": "Sales feedback",
                "frequency": "Medium",
                "affected_segments": segments[1:] if len(segments) > 1 else segments,
                "evidence": "Mentioned in 45% of mid-market evaluations"
            },
            {
                "need_id": "N012",
                "statement": "Pay fair price for value received",
                "source": "Survey responses",
                "frequency": "Very High",
                "affected_segments": segments,
                "evidence": "Price/value ratio is #1 selection criterion"
            }
        ]

        return needs

    async def _categorize_needs(
        self,
        needs: List[Dict[str, Any]],
        framework: str
    ) -> Dict[str, Any]:
        """Categorize needs using specified framework (Kano, JTBD, etc.)."""
        await asyncio.sleep(0.1)  # Simulate categorization

        if framework == "Kano":
            categories = {
                "Must-Be (Basic)": {
                    "description": "Expected features that cause dissatisfaction if missing",
                    "needs": [n for n in needs if n["need_id"] in ["N003", "N007", "N012"]]
                },
                "Performance (Satisfiers)": {
                    "description": "Features where more is better, linear satisfaction",
                    "needs": [n for n in needs if n["need_id"] in ["N001", "N004", "N008", "N010", "N011"]]
                },
                "Excitement (Delighters)": {
                    "description": "Unexpected features that delight customers",
                    "needs": [n for n in needs if n["need_id"] in ["N009", "N002"]]
                },
                "Indifferent": {
                    "description": "Features that don't significantly impact satisfaction",
                    "needs": []
                },
                "Reverse": {
                    "description": "Features that some customers dislike",
                    "needs": []
                }
            }
        else:  # Jobs-to-be-Done framework
            categories = {
                "Functional Jobs": {
                    "description": "Tasks customers are trying to accomplish",
                    "needs": [n for n in needs if n["need_id"] in ["N001", "N003", "N004", "N008", "N009", "N011"]]
                },
                "Emotional Jobs": {
                    "description": "How customers want to feel",
                    "needs": [n for n in needs if n["need_id"] in ["N005", "N010"]]
                },
                "Social Jobs": {
                    "description": "How customers want to be perceived",
                    "needs": [n for n in needs if n["need_id"] in ["N006", "N007"]]
                },
                "Supporting Jobs": {
                    "description": "Auxiliary jobs in the purchase/use process",
                    "needs": [n for n in needs if n["need_id"] in ["N002", "N012"]]
                }
            }

        # Add usage dimension
        for category in categories:
            if categories[category]["needs"]:
                categories[category]["count"] = len(categories[category]["needs"])
                categories[category]["percentage"] = round(
                    (len(categories[category]["needs"]) / len(needs)) * 100, 1
                )

        return categories

    async def _prioritize_needs(
        self,
        categorized_needs: Dict[str, Any],
        segments: List[str]
    ) -> List[Dict[str, Any]]:
        """Prioritize needs based on multiple factors."""
        await asyncio.sleep(0.1)  # Simulate prioritization

        # Flatten categorized needs and add priority scoring
        all_needs = []
        for category, data in categorized_needs.items():
            for need in data.get("needs", []):
                # Calculate priority score based on multiple factors
                frequency_score = {
                    "Critical": 10,
                    "Very High": 9,
                    "High": 7,
                    "Medium": 5,
                    "Low": 3
                }.get(need["frequency"], 5)

                segment_coverage = len(need["affected_segments"]) / len(segments)
                segment_score = segment_coverage * 10

                # Category importance
                category_score = {
                    "Must-Be (Basic)": 10,
                    "Excitement (Delighters)": 9,
                    "Performance (Satisfiers)": 8,
                    "Functional Jobs": 9,
                    "Emotional Jobs": 7,
                    "Social Jobs": 6,
                    "Supporting Jobs": 5
                }.get(category, 7)

                total_score = (frequency_score * 0.4 + segment_score * 0.3 + category_score * 0.3)

                # Determine priority level
                if total_score >= 8.5:
                    priority = "Critical"
                elif total_score >= 7.0:
                    priority = "High"
                elif total_score >= 5.0:
                    priority = "Medium"
                else:
                    priority = "Low"

                prioritized_need = {
                    **need,
                    "category": category,
                    "priority_score": round(total_score, 1),
                    "priority_level": priority,
                    "implementation_complexity": random.choice(["Low", "Medium", "High"]),
                    "estimated_effort_weeks": random.randint(2, 16)
                }
                all_needs.append(prioritized_need)

        # Sort by priority score
        all_needs.sort(key=lambda x: x["priority_score"], reverse=True)

        return all_needs

    async def _identify_unmet_needs(
        self,
        prioritized_needs: List[Dict[str, Any]],
        segments: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify needs that are currently unmet in the market."""
        await asyncio.sleep(0.1)  # Simulate unmet need identification

        # Mock analysis of which needs are unmet by current solutions
        unmet_needs = [
            {
                "need_id": "N009",
                "need_statement": "Automate repetitive tasks and workflows",
                "why_unmet": "Current solutions require manual configuration or coding",
                "competitive_gap": "High - No solution offers true no-code automation",
                "market_opportunity": "Very High",
                "potential_revenue_impact": "$45M-$120M ARR",
                "time_to_address": "9-12 months",
                "strategic_priority": "Critical"
            },
            {
                "need_id": "N003",
                "need_statement": "Integrate seamlessly with existing tools",
                "why_unmet": "Limited pre-built integrations, complex API documentation",
                "competitive_gap": "Medium - Some competitors have more integrations",
                "market_opportunity": "High",
                "potential_revenue_impact": "$30M-$75M ARR",
                "time_to_address": "6-9 months",
                "strategic_priority": "Critical"
            },
            {
                "need_id": "N005",
                "need_statement": "Onboard new users quickly without extensive training",
                "why_unmet": "Industry standard is 2-3 weeks onboarding time",
                "competitive_gap": "Medium - Most solutions have similar onboarding friction",
                "market_opportunity": "High",
                "potential_revenue_impact": "$20M-$50M ARR via higher conversion",
                "time_to_address": "4-6 months",
                "strategic_priority": "High"
            },
            {
                "need_id": "N004",
                "need_statement": "Understand performance through analytics",
                "why_unmet": "Basic reporting only, no predictive insights",
                "competitive_gap": "High - Advanced analytics is competitive differentiator",
                "market_opportunity": "Medium-High",
                "potential_revenue_impact": "$15M-$40M ARR",
                "time_to_address": "12-18 months",
                "strategic_priority": "High"
            }
        ]

        return unmet_needs

    async def _capture_aspirational_wants(
        self,
        segments: List[str]
    ) -> Dict[str, Any]:
        """Capture aspirational wants beyond current needs."""
        await asyncio.sleep(0.1)  # Simulate wants capture

        wants = {
            "future_vision": [
                {
                    "want": "AI assistant that anticipates needs and proactively suggests actions",
                    "segment": "All",
                    "horizon": "2-3 years",
                    "feasibility": "Medium",
                    "strategic_value": "Very High"
                },
                {
                    "want": "Unified workspace that eliminates tool switching",
                    "segment": "All",
                    "horizon": "1-2 years",
                    "feasibility": "High",
                    "strategic_value": "High"
                },
                {
                    "want": "Voice and natural language interface for all operations",
                    "segment": segments[1:] if len(segments) > 1 else segments,
                    "horizon": "2-4 years",
                    "feasibility": "Medium",
                    "strategic_value": "Medium"
                },
                {
                    "want": "Self-optimizing system that improves automatically",
                    "segment": [segments[0]] if segments else ["Enterprise"],
                    "horizon": "3-5 years",
                    "feasibility": "Low-Medium",
                    "strategic_value": "High"
                }
            ],
            "experience_aspirations": [
                "Feel confident making decisions with data",
                "Experience seamless flow without interruptions",
                "Feel empowered and productive, not frustrated",
                "Trust the system to handle critical operations"
            ],
            "outcome_desires": [
                "Reduce operational costs by 30-50%",
                "Increase team productivity by 40%+",
                "Make better decisions faster",
                "Scale business without adding headcount proportionally"
            ]
        }

        return wants

    async def _map_needs_to_features(
        self,
        prioritized_needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Map customer needs to potential product features."""
        await asyncio.sleep(0.1)  # Simulate feature mapping

        mappings = []
        for need in prioritized_needs[:8]:  # Top 8 needs
            feature_suggestions = {
                "N009": ["Visual workflow builder", "Automation rules engine", "Template library"],
                "N003": ["Pre-built integration marketplace", "Universal API connector", "Webhook system"],
                "N007": ["SOC 2 Type II compliance", "Role-based access control", "Audit logging"],
                "N001": ["Smart form auto-fill", "Bulk import tools", "OCR data extraction"],
                "N012": ["Tiered pricing model", "Usage-based billing option", "ROI calculator"],
                "N005": ["Interactive product tours", "Contextual help system", "Quick-start templates"],
                "N008": ["Real-time co-editing", "@mentions and notifications", "Activity feed"],
                "N004": ["Customizable dashboards", "Predictive analytics", "Automated insights"]
            }.get(need["need_id"], ["Feature mapping TBD"])

            mappings.append({
                "need_id": need["need_id"],
                "need_statement": need["statement"],
                "priority_level": need["priority_level"],
                "suggested_features": feature_suggestions,
                "feature_category": random.choice(["Core", "Advanced", "Premium", "Enterprise"]),
                "development_approach": random.choice(["Build", "Buy", "Partner", "Build + Partner"])
            })

        return mappings

    async def _analyze_segment_needs(
        self,
        prioritized_needs: List[Dict[str, Any]],
        segments: List[str]
    ) -> Dict[str, Any]:
        """Analyze how needs vary across customer segments."""
        await asyncio.sleep(0.1)  # Simulate segment analysis

        segment_profiles = {}
        for segment in segments:
            # Find needs affecting this segment
            segment_needs = [n for n in prioritized_needs if segment in n["affected_segments"]]

            # Analyze priorities for this segment
            critical_needs = [n for n in segment_needs if n["priority_level"] == "Critical"]
            high_needs = [n for n in segment_needs if n["priority_level"] == "High"]

            # Determine segment characteristics
            if segment in ["Enterprise", "Large Enterprise"]:
                focus_areas = ["Security & Compliance", "Customization", "Advanced Analytics", "Integration"]
                buying_journey = "Long (6-12 months), committee-based, ROI-driven"
                price_sensitivity = "Low"
            elif segment in ["Mid-Market", "Medium Business"]:
                focus_areas = ["Scalability", "Value for money", "Integration", "Support quality"]
                buying_journey = "Medium (3-6 months), team-based, value-focused"
                price_sensitivity = "Medium"
            else:  # SMB
                focus_areas = ["Ease of use", "Quick setup", "Price", "Essential features"]
                buying_journey = "Short (1-3 months), individual/small team, price-sensitive"
                price_sensitivity = "High"

            segment_profiles[segment] = {
                "total_needs": len(segment_needs),
                "critical_needs": len(critical_needs),
                "high_priority_needs": len(high_needs),
                "top_3_needs": [n["statement"] for n in segment_needs[:3]],
                "focus_areas": focus_areas,
                "buying_journey": buying_journey,
                "price_sensitivity": price_sensitivity,
                "unique_needs": [n["statement"] for n in segment_needs if len(n["affected_segments"]) == 1][:2]
            }

        return segment_profiles


# Module export
__all__ = ['CaptureNeedsAgent']
