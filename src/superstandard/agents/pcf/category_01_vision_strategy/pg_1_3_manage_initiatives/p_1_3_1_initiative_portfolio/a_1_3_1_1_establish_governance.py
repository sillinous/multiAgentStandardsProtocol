"""
APQC PCF Agent: Establish Strategic Initiative Governance (1.3.1.1)

Defines governance structure, decision rights, and accountability for strategic initiatives.
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


class EstablishGovernanceAgent(ActivityAgentBase):
    """Agent for establishing strategic initiative governance."""

    def __init__(self, config: PCFAgentConfig = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        metadata = PCFMetadata(
            pcf_element_id="10067",
            hierarchy_id="1.3.1.1",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.3",
            process_group_name="Manage strategic initiatives",
            process_id="1.3.1",
            process_name="Manage strategic initiative portfolio",
            activity_id="1.3.1.1",
            activity_name="Establish strategic initiative governance",
            parent_element_id="10050",
            kpis=[
                {"name": "governance_bodies_established", "type": "count", "unit": "number"},
                {"name": "decision_clarity_score", "type": "score", "unit": "0-10"},
                {"name": "stakeholder_alignment", "type": "percentage", "unit": "%"}
            ]
        )

        return PCFAgentConfig(
            agent_id="establish_governance_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Establish strategic initiative governance."""
        execution_start = datetime.utcnow()

        governance_structure = await self._define_governance_structure()
        decision_rights = await self._establish_decision_rights()
        meeting_cadence = await self._define_meeting_cadence()
        escalation_paths = await self._define_escalation_paths()

        execution_end = datetime.utcnow()
        execution_duration = (execution_end - execution_start).total_seconds()

        result = {
            "governance_overview": {
                "execution_date": execution_start.isoformat(),
                "scope": "Strategic initiative governance framework"
            },
            "governance_structure": governance_structure,
            "decision_rights": decision_rights,
            "meeting_cadence": meeting_cadence,
            "escalation_paths": escalation_paths,
            "kpis": {
                "governance_bodies_established": len(governance_structure["governance_bodies"]),
                "decision_clarity_score": round(random.uniform(7.5, 9.5), 1),
                "stakeholder_alignment": round(random.uniform(80, 95), 1),
                "execution_time_seconds": round(execution_duration, 2)
            }
        }

        return result

    async def _define_governance_structure(self) -> Dict[str, Any]:
        """Define governance structure and bodies."""
        await asyncio.sleep(0.05)

        return {
            "governance_bodies": [
                {
                    "name": "Strategic Steering Committee",
                    "purpose": "Overall strategic direction and portfolio decisions",
                    "members": ["CEO", "CFO", "COO", "CTO", "Chief Strategy Officer"],
                    "chair": "CEO",
                    "meeting_frequency": "Monthly",
                    "decision_authority": "Portfolio approval, resource allocation >$5M, strategic pivots"
                },
                {
                    "name": "Initiative Review Board",
                    "purpose": "Initiative oversight and operational decisions",
                    "members": ["Chief Strategy Officer", "Portfolio Manager", "Initiative Owners", "Finance Rep"],
                    "chair": "Chief Strategy Officer",
                    "meeting_frequency": "Bi-weekly",
                    "decision_authority": "Initiative scope changes, resource reallocation <$5M, risk mitigation"
                },
                {
                    "name": "Initiative Working Teams",
                    "purpose": "Initiative execution and day-to-day management",
                    "members": ["Initiative Owner", "Project Manager", "Workstream Leads", "Subject Matter Experts"],
                    "chair": "Initiative Owner",
                    "meeting_frequency": "Weekly",
                    "decision_authority": "Tactical execution, issue resolution, milestone delivery"
                }
            ],
            "governance_principles": [
                "Clear accountability - every initiative has a single owner",
                "Transparent decision-making - all decisions documented and communicated",
                "Data-driven reviews - decisions based on metrics and evidence",
                "Rapid escalation - issues elevated quickly when thresholds exceeded",
                "Continuous improvement - lessons learned incorporated into governance"
            ]
        }

    async def _establish_decision_rights(self) -> Dict[str, Any]:
        """Establish clear decision rights and authorities."""
        await asyncio.sleep(0.05)

        return {
            "decision_matrix": [
                {
                    "decision_type": "New Initiative Approval",
                    "threshold": "Any strategic initiative",
                    "decision_maker": "Strategic Steering Committee",
                    "input_required": ["Business case", "Resource requirements", "Strategic fit assessment"],
                    "approval_criteria": "Strategic alignment, ROI >20%, resource availability"
                },
                {
                    "decision_type": "Initiative Prioritization",
                    "threshold": "Portfolio-level resource conflicts",
                    "decision_maker": "Strategic Steering Committee",
                    "input_required": ["Initiative status", "Resource demands", "Strategic impact analysis"],
                    "approval_criteria": "Strategic value, urgency, dependencies, resource constraints"
                },
                {
                    "decision_type": "Scope Change (Major)",
                    "threshold": ">20% budget increase or 3-month timeline extension",
                    "decision_maker": "Strategic Steering Committee",
                    "input_required": ["Change justification", "Impact analysis", "Updated business case"],
                    "approval_criteria": "Continued strategic value, revised ROI acceptable"
                },
                {
                    "decision_type": "Scope Change (Minor)",
                    "threshold": "<20% budget increase or <3-month timeline extension",
                    "decision_maker": "Initiative Review Board",
                    "input_required": ["Change request", "Impact assessment"],
                    "approval_criteria": "Reasonable justification, no strategic impact"
                },
                {
                    "decision_type": "Resource Reallocation",
                    "threshold": "Between initiatives",
                    "decision_maker": "Initiative Review Board",
                    "input_required": ["Current utilization", "Initiative priorities", "Impact on both initiatives"],
                    "approval_criteria": "Portfolio optimization, minimal disruption"
                },
                {
                    "decision_type": "Initiative Termination",
                    "threshold": "Any initiative",
                    "decision_maker": "Strategic Steering Committee",
                    "input_required": ["Performance data", "Termination rationale", "Wind-down plan"],
                    "approval_criteria": "Failed to meet objectives, strategic relevance lost, unacceptable risk"
                }
            ],
            "delegation_principles": {
                "push_down": "Decisions made at lowest appropriate level",
                "escalation_only": "Only escalate when required by threshold or complexity",
                "time_bound": "All decisions made within 5 business days of escalation",
                "documented": "All major decisions logged in initiative management system"
            }
        }

    async def _define_meeting_cadence(self) -> Dict[str, Any]:
        """Define meeting cadence and agendas."""
        await asyncio.sleep(0.05)

        return {
            "meeting_schedule": [
                {
                    "meeting": "Strategic Steering Committee",
                    "frequency": "Monthly (1st Monday)",
                    "duration": "3 hours",
                    "standard_agenda": [
                        "Portfolio performance dashboard review (30 min)",
                        "Initiative deep-dive (1 initiative per month) (60 min)",
                        "New initiative approvals and prioritization decisions (45 min)",
                        "Strategic risks and escalations (30 min)",
                        "Actions and decisions recap (15 min)"
                    ],
                    "required_artifacts": [
                        "Portfolio dashboard",
                        "Initiative status reports",
                        "Financial performance vs. plan",
                        "Risk register"
                    ]
                },
                {
                    "meeting": "Initiative Review Board",
                    "frequency": "Bi-weekly (Tuesdays)",
                    "duration": "2 hours",
                    "standard_agenda": [
                        "Initiative status updates (all active initiatives) (60 min)",
                        "Issue resolution and decision-making (30 min)",
                        "Resource allocation and conflicts (20 min)",
                        "Upcoming milestones and risks (10 min)"
                    ],
                    "required_artifacts": [
                        "Initiative status reports",
                        "Issue log",
                        "Resource utilization report"
                    ]
                },
                {
                    "meeting": "Initiative Working Team Stand-ups",
                    "frequency": "Weekly (Wednesdays)",
                    "duration": "1 hour",
                    "standard_agenda": [
                        "Previous week accomplishments (15 min)",
                        "Current week priorities (15 min)",
                        "Blockers and issues (20 min)",
                        "Action items (10 min)"
                    ],
                    "required_artifacts": [
                        "Sprint/iteration progress",
                        "Issue log updates"
                    ]
                }
            ],
            "special_meetings": {
                "quarterly_strategy_review": "Comprehensive portfolio review and strategic alignment check",
                "initiative_kickoffs": "Dedicated session for new initiative launch",
                "post_implementation_reviews": "Lessons learned and success assessment",
                "emergency_sessions": "Called as needed for urgent escalations"
            }
        }

    async def _define_escalation_paths(self) -> Dict[str, Any]:
        """Define escalation paths and triggers."""
        await asyncio.sleep(0.05)

        return {
            "escalation_triggers": [
                {
                    "trigger": "Initiative >20% over budget",
                    "severity": "High",
                    "escalate_to": "Initiative Review Board immediately, Steering Committee within 1 week",
                    "required_info": ["Budget variance analysis", "Corrective action plan", "Revised forecast"]
                },
                {
                    "trigger": "Milestone missed by >2 weeks",
                    "severity": "Medium",
                    "escalate_to": "Initiative Review Board at next meeting",
                    "required_info": ["Root cause analysis", "Recovery plan", "Impact on downstream milestones"]
                },
                {
                    "trigger": "Key risk materialized (High/Critical severity)",
                    "severity": "High",
                    "escalate_to": "Steering Committee immediately",
                    "required_info": ["Risk description", "Impact assessment", "Mitigation plan"]
                },
                {
                    "trigger": "Initiative team turnover >30%",
                    "severity": "Medium",
                    "escalate_to": "Initiative Review Board and CHRO",
                    "required_info": ["Turnover analysis", "Staffing plan", "Knowledge transfer status"]
                },
                {
                    "trigger": "Scope creep >20% of original scope",
                    "severity": "Medium",
                    "escalate_to": "Initiative Review Board for decision",
                    "required_info": ["Scope change request", "Impact on timeline/budget", "Business justification"]
                },
                {
                    "trigger": "Strategic assumptions invalidated",
                    "severity": "Critical",
                    "escalate_to": "Steering Committee immediately",
                    "required_info": ["Assumption analysis", "Impact on strategic value", "Recommendation (pivot/continue/stop)"]
                }
            ],
            "escalation_process": {
                "step_1": "Initiative Owner identifies trigger and prepares required information",
                "step_2": "Initiative Owner escalates to appropriate governance body per matrix",
                "step_3": "Governance body reviews within defined timeframe",
                "step_4": "Decision made and communicated to all stakeholders",
                "step_5": "Action plan implemented and progress monitored"
            },
            "communication_protocol": {
                "urgent": "Email + Slack + Phone call within 4 hours",
                "high": "Email + Slack within 24 hours",
                "medium": "Email within 48 hours",
                "low": "Included in next regular meeting"
            }
        }


__all__ = ['EstablishGovernanceAgent']
