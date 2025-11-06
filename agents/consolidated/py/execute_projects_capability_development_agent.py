"""
ExecuteProjectsCapabilityDevelopmentAgent - APQC 12.0
12.3.3 Execute Projects
APQC ID: apqc_12_0_j1k2l3m4
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ExecuteProjectsCapabilityDevelopmentAgentConfig:
    apqc_agent_id: str = "apqc_12_0_j1k2l3m4"
    apqc_process_id: str = "12.3.3"
    agent_name: str = "execute_projects_capability_development_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ExecuteProjectsCapabilityDevelopmentAgent(BaseAgent, ProtocolMixin):
    """
    Skills: task_scheduling: 0.9, resource_allocation: 0.88, progress_tracking: 0.86
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "12.3.3"

    def __init__(self, config: ExecuteProjectsCapabilityDevelopmentAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'task_scheduling': 0.9, 'resource_allocation': 0.88, 'progress_tracking': 0.86}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute projects using Critical Path Method (CPM), resource leveling, and EVM
        """
        project_tasks = input_data.get('project_tasks', [])
        resources = input_data.get('resources', [])
        dependencies = input_data.get('dependencies', [])
        budget = input_data.get('budget', 0)

        # Critical Path Method
        critical_path = self._calculate_critical_path(project_tasks, dependencies)

        # Resource Allocation
        resource_plan = self._allocate_resources(project_tasks, resources, critical_path)

        # Earned Value Management
        evm = self._calculate_earned_value(project_tasks, budget)

        # Risk Identification
        risks = self._identify_project_risks(critical_path, resource_plan, evm)

        # Milestones
        milestones = self._define_milestones(project_tasks, critical_path)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "execution_plan": {
                    "schedule": {
                        "critical_path": critical_path,
                        "total_duration": critical_path['total_duration'],
                        "milestones": milestones
                    },
                    "resource_assignments": resource_plan,
                    "earned_value_metrics": evm,
                    "risks": risks
                },
                "metrics": {
                    "project_duration_days": critical_path['total_duration'],
                    "critical_tasks_count": len(critical_path['critical_tasks']),
                    "schedule_performance_index": evm['spi'],
                    "cost_performance_index": evm['cpi']
                }
            }
        }

    def _calculate_critical_path(self, tasks: List[Dict], dependencies: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Critical Path Method (CPM)
        """
        if not tasks:
            return {"critical_path": [], "total_duration": 0, "critical_tasks": []}

        # Build dependency map
        dep_map = {}
        for dep in dependencies:
            predecessor = dep.get('predecessor')
            successor = dep.get('successor')
            if successor not in dep_map:
                dep_map[successor] = []
            dep_map[successor].append(predecessor)

        # Calculate early start/finish
        task_map = {task.get('task_id'): task for task in tasks}
        early_start = {}
        early_finish = {}

        for task in tasks:
            task_id = task.get('task_id')
            duration = task.get('duration_days', 0)

            # Get dependencies
            predecessors = dep_map.get(task_id, [])

            if not predecessors:
                early_start[task_id] = 0
            else:
                early_start[task_id] = max(early_finish.get(pred, 0) for pred in predecessors)

            early_finish[task_id] = early_start[task_id] + duration

        # Project duration
        project_duration = max(early_finish.values()) if early_finish else 0

        # Calculate late start/finish (backward pass)
        late_finish = {}
        late_start = {}

        # Start from end
        for task in reversed(tasks):
            task_id = task.get('task_id')
            duration = task.get('duration_days', 0)

            # Find successors
            successors = [dep['successor'] for dep in dependencies if dep.get('predecessor') == task_id]

            if not successors:
                late_finish[task_id] = project_duration
            else:
                late_finish[task_id] = min(late_start.get(succ, project_duration) for succ in successors)

            late_start[task_id] = late_finish[task_id] - duration

        # Calculate slack and identify critical path
        critical_tasks = []
        for task in tasks:
            task_id = task.get('task_id')
            slack = late_start.get(task_id, 0) - early_start.get(task_id, 0)

            if slack == 0:  # Zero slack = critical
                critical_tasks.append({
                    "task_id": task_id,
                    "name": task.get('name', 'Unknown'),
                    "duration": task.get('duration_days', 0),
                    "early_start": early_start.get(task_id, 0),
                    "early_finish": early_finish.get(task_id, 0)
                })

        return {
            "critical_path": [t['name'] for t in critical_tasks],
            "critical_tasks": critical_tasks,
            "total_duration": project_duration,
            "total_slack_buffer": sum(late_start.get(t.get('task_id'), 0) - early_start.get(t.get('task_id'), 0) for t in tasks)
        }

    def _allocate_resources(self, tasks: List[Dict], resources: List[Dict], critical_path: Dict) -> Dict[str, Any]:
        """
        Allocate resources using resource leveling
        """
        resource_assignments = []
        resource_utilization = {r.get('name'): 0 for r in resources}

        critical_task_ids = [t['task_id'] for t in critical_path['critical_tasks']]

        # Priority to critical path tasks
        sorted_tasks = sorted(tasks, key=lambda t: 0 if t.get('task_id') in critical_task_ids else 1)

        for task in sorted_tasks:
            required_skills = task.get('required_skills', [])
            task_duration = task.get('duration_days', 0)

            # Find best resource match
            best_resource = None
            best_match_score = 0

            for resource in resources:
                resource_skills = resource.get('skills', [])
                match_score = len(set(required_skills) & set(resource_skills)) / len(required_skills) if required_skills else 1

                if match_score > best_match_score:
                    best_match_score = match_score
                    best_resource = resource

            if best_resource:
                resource_assignments.append({
                    "task_id": task.get('task_id'),
                    "task_name": task.get('name'),
                    "resource": best_resource.get('name'),
                    "allocation_percentage": 100,
                    "duration_days": task_duration,
                    "skill_match": round(best_match_score * 100, 1)
                })

                resource_utilization[best_resource.get('name')] += task_duration

        # Calculate utilization percentages
        project_duration = critical_path['total_duration']
        resource_util_pct = {
            name: round((util / project_duration * 100), 1) if project_duration > 0 else 0
            for name, util in resource_utilization.items()
        }

        return {
            "assignments": resource_assignments,
            "resource_utilization": resource_util_pct,
            "over_allocated": [name for name, util in resource_util_pct.items() if util > 100],
            "under_utilized": [name for name, util in resource_util_pct.items() if util < 50]
        }

    def _calculate_earned_value(self, tasks: List[Dict], budget: float) -> Dict[str, Any]:
        """
        Calculate Earned Value Management (EVM) metrics
        """
        if not tasks or budget == 0:
            return {"pv": 0, "ev": 0, "ac": 0, "spi": 1.0, "cpi": 1.0}

        # Planned Value (PV) - budgeted cost of work scheduled
        total_duration = sum(task.get('duration_days', 0) for task in tasks)
        pv_per_day = budget / total_duration if total_duration > 0 else 0

        # Assume we're at 50% point of project
        elapsed_duration = total_duration * 0.5
        pv = pv_per_day * elapsed_duration

        # Earned Value (EV) - budgeted cost of work performed
        completed_tasks = [t for t in tasks if t.get('completion_percentage', 0) >= 100]
        in_progress = [t for t in tasks if 0 < t.get('completion_percentage', 0) < 100]

        ev = 0
        for task in completed_tasks:
            task_budget = (task.get('duration_days', 0) / total_duration) * budget
            ev += task_budget

        for task in in_progress:
            task_budget = (task.get('duration_days', 0) / total_duration) * budget
            ev += task_budget * (task.get('completion_percentage', 0) / 100)

        # Actual Cost (AC) - actual cost of work performed (assume 95% of EV for demo)
        ac = ev * 0.95

        # Schedule Performance Index (SPI)
        spi = ev / pv if pv > 0 else 1.0

        # Cost Performance Index (CPI)
        cpi = ev / ac if ac > 0 else 1.0

        # Estimate at Completion (EAC)
        eac = budget / cpi if cpi > 0 else budget

        # Variance
        schedule_variance = ev - pv
        cost_variance = ev - ac

        return {
            "pv": round(pv, 2),
            "ev": round(ev, 2),
            "ac": round(ac, 2),
            "spi": round(spi, 2),
            "cpi": round(cpi, 2),
            "schedule_variance": round(schedule_variance, 2),
            "cost_variance": round(cost_variance, 2),
            "eac": round(eac, 2),
            "status": "ahead" if spi > 1.0 and cpi > 1.0 else "on_track" if spi >= 0.9 and cpi >= 0.9 else "at_risk"
        }

    def _identify_project_risks(self, critical_path: Dict, resource_plan: Dict, evm: Dict) -> List[Dict]:
        """
        Identify project risks
        """
        risks = []

        # Critical path risk
        if len(critical_path['critical_tasks']) > 0:
            risks.append({
                "risk": "Critical path delay",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Monitor critical tasks closely, have contingency plans"
            })

        # Resource over-allocation risk
        if resource_plan.get('over_allocated'):
            risks.append({
                "risk": "Resource over-allocation",
                "probability": "high",
                "impact": "medium",
                "mitigation": "Resource leveling, hire additional resources"
            })

        # Schedule risk
        if evm.get('spi', 1.0) < 0.9:
            risks.append({
                "risk": "Schedule slippage",
                "probability": "high",
                "impact": "high",
                "mitigation": "Fast-track critical activities, add resources"
            })

        # Cost risk
        if evm.get('cpi', 1.0) < 0.9:
            risks.append({
                "risk": "Budget overrun",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Cost control measures, scope adjustment"
            })

        return risks

    def _define_milestones(self, tasks: List[Dict], critical_path: Dict) -> List[Dict]:
        """
        Define project milestones
        """
        milestones = []

        # Project start
        milestones.append({
            "name": "Project Kickoff",
            "date_offset": 0,
            "type": "start"
        })

        # Critical path milestones
        cumulative_duration = 0
        for task in critical_path['critical_tasks']:
            cumulative_duration += task['duration']
            if cumulative_duration % 30 == 0 or task == critical_path['critical_tasks'][-1]:  # Every 30 days or last task
                milestones.append({
                    "name": f"Milestone: {task['name']} Complete",
                    "date_offset": cumulative_duration,
                    "type": "checkpoint"
                })

        # Project end
        milestones.append({
            "name": "Project Completion",
            "date_offset": critical_path['total_duration'],
            "type": "end"
        })

        return milestones

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_execute_projects_capability_development_agent(config: Optional[ExecuteProjectsCapabilityDevelopmentAgentConfig] = None):
    if config is None:
        config = ExecuteProjectsCapabilityDevelopmentAgentConfig()
    return ExecuteProjectsCapabilityDevelopmentAgent(config)
