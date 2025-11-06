"""
ResolveCustomerIssuesCustomerServiceAgent - APQC 6.0
6.2.2 Resolve Customer Issues
APQC ID: apqc_6_0_g8h9i0j1
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ResolveCustomerIssuesCustomerServiceAgentConfig:
    apqc_agent_id: str = "apqc_6_0_g8h9i0j1"
    apqc_process_id: str = "6.2.2"
    agent_name: str = "resolve_customer_issues_customer_service_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ResolveCustomerIssuesCustomerServiceAgent(BaseAgent, ProtocolMixin):
    """
    Skills: issue_categorization: 0.9, root_cause_analysis: 0.88, resolution_tracking: 0.86
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "6.2.2"

    def __init__(self, config: ResolveCustomerIssuesCustomerServiceAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'issue_categorization': 0.9, 'root_cause_analysis': 0.88, 'resolution_tracking': 0.86}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve customer issues using categorization and RCA (5 Whys)
        """
        customer_issue = input_data.get('customer_issue', {})
        history = input_data.get('history', [])
        knowledge_base = input_data.get('knowledge_base', [])

        # Categorize Issue
        category = self._categorize_issue(customer_issue)

        # Root Cause Analysis
        root_cause = self._perform_root_cause_analysis(customer_issue, history)

        # Generate Resolution Plan
        resolution_plan = self._generate_resolution_plan(category, root_cause, knowledge_base)

        # Follow-up Plan
        follow_up = self._create_follow_up_plan(resolution_plan, customer_issue)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "resolution_plan": {
                    "category": category,
                    "root_cause": root_cause,
                    "solution_steps": resolution_plan['steps'],
                    "estimated_resolution_time": resolution_plan['estimated_time'],
                    "follow_up": follow_up
                },
                "metrics": {
                    "issue_severity": category['severity'],
                    "estimated_resolution_hours": resolution_plan['estimated_time'],
                    "confidence_score": resolution_plan['confidence']
                }
            }
        }

    def _categorize_issue(self, issue: Dict) -> Dict[str, Any]:
        """Categorize customer issue"""
        issue_type = issue.get('type', 'general')
        description = issue.get('description', '').lower()

        # Simple keyword-based categorization
        categories = {
            "product_defect": ["broken", "defect", "not working", "malfunction"],
            "billing": ["charge", "invoice", "payment", "bill"],
            "delivery": ["shipping", "delivery", "received", "package"],
            "service": ["support", "help", "assistance", "service"],
            "account": ["login", "password", "access", "account"]
        }

        detected_category = "general"
        for cat, keywords in categories.items():
            if any(kw in description for kw in keywords):
                detected_category = cat
                break

        # Determine severity based on keywords
        severity_high = ["urgent", "critical", "major", "severe", "emergency"]
        severity_medium = ["important", "significant", "moderate"]

        if any(kw in description for kw in severity_high):
            severity = "high"
            priority = 1
        elif any(kw in description for kw in severity_medium):
            severity = "medium"
            priority = 2
        else:
            severity = "low"
            priority = 3

        return {
            "category": detected_category,
            "severity": severity,
            "priority": priority,
            "requires_escalation": severity == "high"
        }

    def _perform_root_cause_analysis(self, issue: Dict, history: List[Dict]) -> Dict[str, Any]:
        """
        Perform Root Cause Analysis using 5 Whys methodology
        """
        problem = issue.get('description', 'Unknown issue')

        # Simulate 5 Whys analysis
        whys = [
            {"why": 1, "question": "Why did this issue occur?", "answer": "Customer experienced service interruption"},
            {"why": 2, "question": "Why was there a service interruption?", "answer": "System component failed"},
            {"why": 3, "question": "Why did the component fail?", "answer": "Maintenance schedule not followed"},
            {"why": 4, "question": "Why wasn't maintenance followed?", "answer": "Resource constraints"},
            {"why": 5, "question": "Why were there resource constraints?", "answer": "Inadequate planning"}
        ]

        # Check history for patterns
        similar_issues = [h for h in history if h.get('category') == issue.get('type')]
        is_recurring = len(similar_issues) > 2

        root_cause = whys[-1]['answer'] if whys else "Unknown"

        return {
            "root_cause": root_cause,
            "analysis_method": "5_whys",
            "whys_chain": whys[:3],  # First 3 whys
            "is_recurring_issue": is_recurring,
            "similar_issue_count": len(similar_issues),
            "contributing_factors": ["Resource constraints", "Process gaps"] if is_recurring else ["Isolated incident"]
        }

    def _generate_resolution_plan(self, category: Dict, root_cause: Dict, knowledge_base: List[Dict]) -> Dict[str, Any]:
        """Generate resolution plan"""
        severity = category['severity']

        # Search knowledge base for similar solutions
        relevant_solutions = [
            kb for kb in knowledge_base
            if kb.get('category') == category['category']
        ]

        if relevant_solutions:
            solution_steps = relevant_solutions[0].get('steps', [])
            confidence = 0.9
        else:
            # Generate generic resolution steps
            solution_steps = [
                "Acknowledge and document the issue",
                "Gather detailed information from customer",
                "Apply immediate workaround if available",
                "Escalate to technical team if needed",
                "Implement permanent fix",
                "Verify resolution with customer"
            ]
            confidence = 0.6

        # Estimate resolution time based on severity
        time_estimates = {
            "high": 4,  # hours
            "medium": 8,
            "low": 24
        }
        estimated_time = time_estimates.get(severity, 24)

        return {
            "steps": solution_steps,
            "estimated_time": estimated_time,
            "confidence": confidence,
            "requires_approval": severity == "high"
        }

    def _create_follow_up_plan(self, resolution_plan: Dict, issue: Dict) -> Dict[str, Any]:
        """Create follow-up plan"""
        return {
            "follow_up_required": True,
            "follow_up_timeline": "24 hours after resolution",
            "follow_up_actions": [
                "Confirm issue is fully resolved",
                "Check customer satisfaction",
                "Document lessons learned",
                "Update knowledge base if new solution"
            ],
            "escalation_path": "Supervisor" if resolution_plan.get('requires_approval') else "None"
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_resolve_customer_issues_customer_service_agent(config: Optional[ResolveCustomerIssuesCustomerServiceAgentConfig] = None):
    if config is None:
        config = ResolveCustomerIssuesCustomerServiceAgentConfig()
    return ResolveCustomerIssuesCustomerServiceAgent(config)
