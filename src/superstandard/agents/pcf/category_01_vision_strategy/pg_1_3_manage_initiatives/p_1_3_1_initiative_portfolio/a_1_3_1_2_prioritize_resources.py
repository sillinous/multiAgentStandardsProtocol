"""
APQC PCF Agent: Prioritize and Allocate Resources (1.3.1.2)

Prioritizes initiatives and allocates resources across the strategic portfolio.
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


class PrioritizeResourcesAgent(ActivityAgentBase):
    """Agent for prioritizing initiatives and allocating resources."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10068",
            hierarchy_id="1.3.1.2",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.3",
            process_group_name="Manage strategic initiatives",
            process_id="1.3.1",
            process_name="Manage strategic initiative portfolio",
            activity_id="1.3.1.2",
            activity_name="Prioritize and allocate resources",
            parent_element_id="10050",
            kpis=[
                {"name": "initiatives_prioritized", "type": "count", "unit": "number"},
                {"name": "resource_utilization", "type": "percentage", "unit": "%"},
                {"name": "allocation_efficiency", "type": "score", "unit": "0-10"}
            ]
        )

        return PCFAgentConfig(
            agent_id="prioritize_resources_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize initiatives and allocate resources."""
        execution_start = datetime.utcnow()

        initiatives = await self._assess_initiative_portfolio()
        prioritization = await self._prioritize_initiatives(initiatives)
        resource_allocation = await self._allocate_resources(prioritization)
        capacity_plan = await self._develop_capacity_plan(resource_allocation)

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "prioritization_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Strategic initiative prioritization and resource allocation"
            },
            "initiative_portfolio": initiatives,
            "prioritization_results": prioritization,
            "resource_allocation": resource_allocation,
            "capacity_plan": capacity_plan,
            "kpis": {
                "initiatives_prioritized": len(initiatives["active_initiatives"]),
                "resource_utilization": round(random.uniform(82, 95), 1),
                "allocation_efficiency": round(random.uniform(7.0, 9.0), 1),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _assess_initiative_portfolio(self) -> Dict[str, Any]:
        """Assess current initiative portfolio."""
        await asyncio.sleep(0.05)

        active_initiatives = []
        for i in range(random.randint(8, 12)):
            initiative = {
                "id": f"INIT-{i+1:03d}",
                "name": f"Strategic Initiative {i+1}",
                "status": random.choice(["Planning", "In Progress", "At Risk", "On Track"]),
                "strategic_pillar": random.choice([
                    "Product Innovation",
                    "Market Expansion",
                    "Operational Excellence",
                    "Customer Experience"
                ]),
                "budget": f"${random.randint(5, 50)}M",
                "current_spend": f"${random.randint(2, 30)}M",
                "timeline": f"{random.randint(12, 36)} months",
                "completion": f"{random.randint(10, 80)}%",
                "health_score": round(random.uniform(6.0, 9.5), 1)
            }
            active_initiatives.append(initiative)

        return {
            "active_initiatives": active_initiatives,
            "portfolio_summary": {
                "total_initiatives": len(active_initiatives),
                "total_budget": f"${sum(int(i['budget'][1:-1]) for i in active_initiatives)}M",
                "average_health_score": round(sum(i['health_score'] for i in active_initiatives) / len(active_initiatives), 1)
            }
        }

    async def _prioritize_initiatives(self, initiatives: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize initiatives using multi-criteria framework."""
        await asyncio.sleep(0.05)

        prioritization_criteria = {
            "strategic_alignment": {
                "weight": 0.30,
                "description": "Alignment with strategic objectives and vision",
                "scoring": "1-10 scale based on strategic fit analysis"
            },
            "financial_return": {
                "weight": 0.25,
                "description": "Expected ROI and financial impact",
                "scoring": "Based on NPV and ROI calculations"
            },
            "urgency": {
                "weight": 0.20,
                "description": "Time sensitivity and market window",
                "scoring": "Critical/High/Medium/Low urgency assessment"
            },
            "feasibility": {
                "weight": 0.15,
                "description": "Technical and organizational capability to deliver",
                "scoring": "Assessment of resources, skills, and complexity"
            },
            "risk_level": {
                "weight": 0.10,
                "description": "Risk-adjusted priority (lower risk = higher priority)",
                "scoring": "Inverse of risk assessment score"
            }
        }

        # Score initiatives
        scored_initiatives = []
        for init in initiatives["active_initiatives"]:
            scores = {
                "strategic_alignment": round(random.uniform(6.0, 9.5), 1),
                "financial_return": round(random.uniform(5.5, 9.0), 1),
                "urgency": round(random.uniform(6.0, 9.0), 1),
                "feasibility": round(random.uniform(6.5, 9.0), 1),
                "risk_level": round(random.uniform(5.0, 8.5), 1)
            }

            weighted_score = sum(
                scores[criterion] * prioritization_criteria[criterion]["weight"]
                for criterion in prioritization_criteria
            )

            scored_initiatives.append({
                "initiative_id": init["id"],
                "initiative_name": init["name"],
                "scores": scores,
                "weighted_priority_score": round(weighted_score, 2),
                "priority_tier": self._calculate_tier(weighted_score)
            })

        # Sort by priority score
        scored_initiatives.sort(key=lambda x: x["weighted_priority_score"], reverse=True)

        return {
            "prioritization_framework": prioritization_criteria,
            "scored_initiatives": scored_initiatives,
            "priority_tiers": {
                "tier_1_critical": [i for i in scored_initiatives if i["priority_tier"] == "Tier 1 - Critical"],
                "tier_2_high": [i for i in scored_initiatives if i["priority_tier"] == "Tier 2 - High"],
                "tier_3_medium": [i for i in scored_initiatives if i["priority_tier"] == "Tier 3 - Medium"]
            }
        }

    def _calculate_tier(self, score: float) -> str:
        """Calculate priority tier based on weighted score."""
        if score >= 8.0:
            return "Tier 1 - Critical"
        elif score >= 6.5:
            return "Tier 2 - High"
        else:
            return "Tier 3 - Medium"

    async def _allocate_resources(self, prioritization: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate resources based on prioritization."""
        await asyncio.sleep(0.05)

        total_budget = random.randint(200, 400) * 1000000
        total_headcount = random.randint(400, 800)

        allocations = []
        remaining_budget = total_budget
        remaining_headcount = total_headcount

        for initiative in prioritization["scored_initiatives"]:
            # Allocate proportionally to priority
            budget_percent = random.uniform(0.08, 0.20)
            headcount_percent = random.uniform(0.08, 0.18)

            allocated_budget = min(int(total_budget * budget_percent), remaining_budget)
            allocated_headcount = min(int(total_headcount * headcount_percent), remaining_headcount)

            remaining_budget -= allocated_budget
            remaining_headcount -= allocated_headcount

            allocations.append({
                "initiative_id": initiative["initiative_id"],
                "initiative_name": initiative["initiative_name"],
                "priority_tier": initiative["priority_tier"],
                "allocated_budget": f"${allocated_budget / 1000000:.1f}M",
                "allocated_headcount": allocated_headcount,
                "resource_breakdown": {
                    "engineering": f"{int(allocated_headcount * 0.40)} FTEs",
                    "product": f"{int(allocated_headcount * 0.15)} FTEs",
                    "design": f"{int(allocated_headcount * 0.10)} FTEs",
                    "sales_marketing": f"{int(allocated_headcount * 0.20)} FTEs",
                    "operations": f"{int(allocated_headcount * 0.15)} FTEs"
                }
            })

        return {
            "total_available_budget": f"${total_budget / 1000000:.0f}M",
            "total_available_headcount": total_headcount,
            "allocations": allocations,
            "utilization": {
                "budget_allocated": f"${(total_budget - remaining_budget) / 1000000:.0f}M",
                "budget_utilization": f"{((total_budget - remaining_budget) / total_budget * 100):.1f}%",
                "headcount_allocated": total_headcount - remaining_headcount,
                "headcount_utilization": f"{((total_headcount - remaining_headcount) / total_headcount * 100):.1f}%"
            }
        }

    async def _develop_capacity_plan(self, allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Develop capacity plan and identify gaps."""
        await asyncio.sleep(0.05)

        return {
            "capacity_analysis": {
                "current_capacity": {
                    "total_fte": allocation["total_available_headcount"],
                    "utilization_rate": allocation["utilization"]["headcount_utilization"],
                    "available_capacity": random.randint(50, 150)
                },
                "capacity_constraints": [
                    {
                        "resource_type": "Senior Engineers",
                        "required": random.randint(80, 120),
                        "available": random.randint(60, 90),
                        "gap": random.randint(10, 30),
                        "mitigation": "External hiring, contractor augmentation, training program"
                    },
                    {
                        "resource_type": "Product Managers",
                        "required": random.randint(25, 40),
                        "available": random.randint(20, 35),
                        "gap": random.randint(5, 10),
                        "mitigation": "Hire 5-10 PMs, promote from within"
                    },
                    {
                        "resource_type": "Data Scientists",
                        "required": random.randint(30, 50),
                        "available": random.randint(25, 45),
                        "gap": random.randint(5, 15),
                        "mitigation": "University partnerships, contractor model"
                    }
                ]
            },
            "hiring_plan": {
                "q1": f"{random.randint(30, 60)} hires",
                "q2": f"{random.randint(40, 80)} hires",
                "q3": f"{random.randint(35, 70)} hires",
                "q4": f"{random.randint(25, 50)} hires",
                "total_year": f"{random.randint(130, 260)} hires",
                "focus_areas": ["Engineering", "Product", "Data Science", "Sales"]
            },
            "contingency_plans": [
                {
                    "scenario": "Hiring falls short by 30%",
                    "mitigation": "Increase contractor usage, de-scope lower priority initiatives, extend timelines"
                },
                {
                    "scenario": "Key skill shortages in market",
                    "mitigation": "Build vs. buy analysis, training programs, offshore partnerships"
                },
                {
                    "scenario": "Budget constraints tighten",
                    "mitigation": "Re-prioritize Tier 3 initiatives, optimize resource allocation, negotiate vendor costs"
                }
            ]
        }


__all__ = ['PrioritizeResourcesAgent']
