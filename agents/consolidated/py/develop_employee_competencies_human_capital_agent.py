"""
DevelopEmployeeCompetenciesHumanCapitalAgent - APQC 7.0
7.3.1 Develop Employee Competencies
APQC ID: apqc_7_0_f7g8h9i0
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class DevelopEmployeeCompetenciesHumanCapitalAgentConfig:
    apqc_agent_id: str = "apqc_7_0_f7g8h9i0"
    apqc_process_id: str = "7.3.1"
    agent_name: str = "develop_employee_competencies_human_capital_agent"
    agent_type: str = "strategic"
    version: str = "1.0.0"


class DevelopEmployeeCompetenciesHumanCapitalAgent(BaseAgent, ProtocolMixin):
    """
    Skills: skill_gap_analysis: 0.9, learning_path_generation: 0.87, competency_mapping: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "7.3.1"

    def __init__(self, config: DevelopEmployeeCompetenciesHumanCapitalAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {'skill_gap_analysis': 0.9, 'learning_path_generation': 0.87, 'competency_mapping': 0.85}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze skill gaps and generate development plans
        """
        employee_skills = input_data.get('employee_skills', {})
        required_competencies = input_data.get('required_competencies', {})
        role_requirements = input_data.get('role_requirements', {})

        # Skill Gap Analysis
        skill_gaps = self._analyze_skill_gaps(employee_skills, required_competencies)

        # Generate Learning Paths
        learning_paths = self._generate_learning_paths(skill_gaps, role_requirements)

        # Competency Matrix
        competency_matrix = self._build_competency_matrix(employee_skills, required_competencies)

        # Priority Areas
        priority_areas = self._identify_priority_areas(skill_gaps)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "development_plan": {
                    "skill_gaps": skill_gaps,
                    "learning_paths": learning_paths,
                    "competency_matrix": competency_matrix,
                    "priority_areas": priority_areas
                },
                "metrics": {
                    "total_gaps": len(skill_gaps['gaps']),
                    "critical_gaps": len([g for g in skill_gaps['gaps'] if g['severity'] == 'critical']),
                    "average_proficiency": skill_gaps['average_proficiency'],
                    "development_readiness": competency_matrix['readiness_score']
                }
            }
        }

    def _analyze_skill_gaps(self, employee_skills: Dict, required_competencies: Dict) -> Dict[str, Any]:
        """Calculate skill gaps"""
        gaps = []
        total_proficiency = 0
        count = 0

        for skill, required_level in required_competencies.items():
            current_level = employee_skills.get(skill, 0)
            gap = required_level - current_level

            if gap > 0:
                severity = "critical" if gap >= 3 else "high" if gap >= 2 else "medium"
                gaps.append({
                    "skill": skill,
                    "current_level": current_level,
                    "required_level": required_level,
                    "gap": gap,
                    "severity": severity
                })

            total_proficiency += current_level
            count += 1

        average_proficiency = round(total_proficiency / count, 2) if count > 0 else 0

        return {
            "gaps": sorted(gaps, key=lambda x: x['gap'], reverse=True),
            "average_proficiency": average_proficiency,
            "proficiency_target": round(sum(required_competencies.values()) / len(required_competencies), 2) if required_competencies else 0
        }

    def _generate_learning_paths(self, skill_gaps: Dict, role_requirements: Dict) -> List[Dict]:
        """Generate personalized learning paths"""
        learning_paths = []

        for gap in skill_gaps['gaps']:
            skill = gap['skill']
            gap_size = gap['gap']

            # Determine learning activities based on gap size
            if gap_size >= 3:
                activities = ["Formal training program", "Mentorship", "On-the-job training", "Certification"]
                duration = "6-12 months"
            elif gap_size >= 2:
                activities = ["Workshop series", "Online courses", "Practice projects"]
                duration = "3-6 months"
            else:
                activities = ["Self-study", "Micro-learning", "Peer learning"]
                duration = "1-3 months"

            learning_paths.append({
                "skill": skill,
                "gap_size": gap_size,
                "learning_activities": activities,
                "estimated_duration": duration,
                "priority": gap['severity']
            })

        return learning_paths[:5]  # Top 5 priorities

    def _build_competency_matrix(self, employee_skills: Dict, required_competencies: Dict) -> Dict[str, Any]:
        """Build competency assessment matrix"""
        competency_levels = {
            "advanced": [],
            "proficient": [],
            "developing": [],
            "beginner": []
        }

        for skill, required in required_competencies.items():
            current = employee_skills.get(skill, 0)

            if current >= required:
                competency_levels["advanced"].append(skill)
            elif current >= required * 0.75:
                competency_levels["proficient"].append(skill)
            elif current >= required * 0.5:
                competency_levels["developing"].append(skill)
            else:
                competency_levels["beginner"].append(skill)

        total_skills = len(required_competencies)
        readiness_score = ((len(competency_levels["advanced"]) + len(competency_levels["proficient"])) / total_skills * 100) if total_skills > 0 else 0

        return {
            "competency_levels": {k: len(v) for k, v in competency_levels.items()},
            "readiness_score": round(readiness_score, 2),
            "readiness_status": "ready" if readiness_score >= 80 else "nearly_ready" if readiness_score >= 60 else "developing"
        }

    def _identify_priority_areas(self, skill_gaps: Dict) -> List[Dict]:
        """Identify high-priority development areas"""
        critical_gaps = [g for g in skill_gaps['gaps'] if g['severity'] == 'critical']
        high_gaps = [g for g in skill_gaps['gaps'] if g['severity'] == 'high']

        priorities = []

        if critical_gaps:
            priorities.append({
                "area": "Critical Skill Gaps",
                "skills": [g['skill'] for g in critical_gaps],
                "urgency": "immediate",
                "impact": "high"
            })

        if high_gaps:
            priorities.append({
                "area": "High Priority Skills",
                "skills": [g['skill'] for g in high_gaps[:3]],
                "urgency": "near_term",
                "impact": "medium"
            })

        return priorities

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def create_develop_employee_competencies_human_capital_agent(config: Optional[DevelopEmployeeCompetenciesHumanCapitalAgentConfig] = None):
    if config is None:
        config = DevelopEmployeeCompetenciesHumanCapitalAgentConfig()
    return DevelopEmployeeCompetenciesHumanCapitalAgent(config)
