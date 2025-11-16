"""
APQC Category 7.0 - Develop and Manage Human Capital Agent Tests

Comprehensive tests for all 11 Human Capital agents from APQC Category 7.0.

Agents tested:
1. DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent (7.1)
2. RecruitSourceSelectEmployeesHumanCapitalAgent (7.2)
3. SourceCandidatesHumanCapitalAgent
4. OnboardDriversHumanCapitalAgent
5. DevelopCounselEmployeesHumanCapitalAgent (7.3)
6. DevelopEmployeeCompetenciesHumanCapitalAgent
7. ManagePerformanceHumanCapitalAgent
8. ManageCompensationHumanCapitalAgent (7.4)
9. RewardRetainEmployeesHumanCapitalAgent (7.4)
10. RedeployRetireEmployeesHumanCapitalAgent (7.5)
11. ManageEmployeeInformationHumanCapitalAgent

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Employee lifecycle integration tests
- Talent management workflows
- Performance and compensation management

Version: 1.0.0
Framework: APQC 7.0.1
Category: 7.0 - Develop and Manage Human Capital
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 7.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestDevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent (APQC 7.1)

    Agent: Develop and manage HR planning, policies, and strategies
    Path: src/superstandard/agents/api/develop_manage_hr_planning_policies_strategies_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.develop_manage_hr_planning_policies_strategies_human_capital_agent import (
            DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent
        )
        return DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.develop_manage_hr_planning_policies_strategies_human_capital_agent import (
            DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgentConfig
        )
        return DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.1",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return ["hr_strategy", "workforce_planning", "policy_development", "compliance"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for HR strategy development."""
        return {
            "task_type": "develop_hr_strategy",
            "data": {
                "business_strategy": {
                    "growth_targets": {"headcount": 500, "revenue": 50000000, "markets": ["north_america", "europe"]},
                    "strategic_priorities": ["digital_transformation", "market_expansion", "innovation"],
                    "timeframe": "3_years"
                },
                "current_workforce": {
                    "total_headcount": 300,
                    "departments": {
                        "engineering": 150,
                        "sales": 50,
                        "operations": 60,
                        "support": 40
                    },
                    "demographics": {
                        "average_tenure": "3.5_years",
                        "turnover_rate": 0.12,
                        "diversity_metrics": {"gender_balance": 0.45, "underrepresented_groups": 0.30}
                    },
                    "skills_inventory": ["python", "javascript", "project_management", "sales", "customer_service"]
                },
                "workforce_requirements": {
                    "critical_roles": ["senior_engineers", "sales_managers", "product_managers"],
                    "skills_gaps": ["machine_learning", "cloud_architecture", "data_science"],
                    "succession_planning_needs": ["leadership", "specialized_technical"],
                    "geographic_expansion": ["europe", "asia"]
                },
                "hr_policies": {
                    "remote_work": "hybrid",
                    "diversity_equity_inclusion": True,
                    "learning_development_budget": 2000,
                    "performance_management_cycle": "quarterly",
                    "compensation_philosophy": "market_competitive"
                },
                "compliance_requirements": {
                    "regulations": ["gdpr", "eeoc", "labor_laws"],
                    "certifications": ["iso_hr", "diversity_certified"],
                    "audit_frequency": "annual"
                }
            },
            "context": {
                "planning_cycle": "annual",
                "industry": "technology",
                "company_size": "mid_market",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_workforce_planning_scenario(self):
        """Test workforce planning for growth scenario."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["scenario"] = "aggressive_growth"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result
        assert result['apqc_process_id'] == "7.1"

    @pytest.mark.asyncio
    async def test_policy_development(self):
        """Test HR policy development."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "develop_hr_policies"
        input_data["data"]["policy_areas"] = ["remote_work", "dei", "compensation", "benefits"]

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestRecruitSourceSelectEmployeesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for RecruitSourceSelectEmployeesHumanCapitalAgent (APQC 7.2)

    Agent: Recruit, source, and select employees
    Path: src/superstandard/agents/api/recruit_source_select_employees_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.recruit_source_select_employees_human_capital_agent import (
            RecruitSourceSelectEmployeesHumanCapitalAgent
        )
        return RecruitSourceSelectEmployeesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.recruit_source_select_employees_human_capital_agent import (
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig
        )
        return RecruitSourceSelectEmployeesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.2",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for recruitment."""
        return {
            "task_type": "recruit_employees",
            "data": {
                "job_requisition": {
                    "requisition_id": "REQ-2025-001",
                    "position_title": "Senior Software Engineer",
                    "department": "engineering",
                    "level": "senior",
                    "headcount": 3,
                    "location": ["remote", "san_francisco", "new_york"],
                    "urgency": "high"
                },
                "job_requirements": {
                    "required_skills": ["python", "kubernetes", "microservices", "aws"],
                    "preferred_skills": ["machine_learning", "terraform", "golang"],
                    "experience_years": {"min": 5, "max": 10},
                    "education": ["bachelors_cs", "equivalent_experience"],
                    "certifications": ["aws_certified", "kubernetes_certified"]
                },
                "sourcing_strategy": {
                    "channels": ["job_boards", "linkedin", "employee_referrals", "recruiters", "university_partnerships"],
                    "target_candidates": 100,
                    "diversity_goals": {"underrepresented_groups": 0.40},
                    "budget": 15000,
                    "timeline": "60_days"
                },
                "selection_process": {
                    "stages": ["resume_screen", "phone_screen", "technical_interview", "behavioral_interview", "final_interview"],
                    "assessments": ["coding_challenge", "system_design", "behavioral_assessment"],
                    "interview_panel": ["hiring_manager", "tech_lead", "peer_engineer", "hr"],
                    "decision_criteria": ["technical_skills", "culture_fit", "communication", "problem_solving"]
                },
                "compensation_range": {
                    "base_salary": {"min": 120000, "max": 180000},
                    "equity": True,
                    "bonus_target": 0.15,
                    "benefits": ["health", "401k", "pto", "learning_budget"]
                }
            },
            "context": {
                "hiring_urgency": "high",
                "market_conditions": "competitive",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_full_recruitment_cycle(self):
        """Test complete recruitment cycle."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_diversity_recruitment(self):
        """Test diversity-focused recruitment."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["sourcing_strategy"]["diversity_goals"] = {
            "underrepresented_groups": 0.50,
            "gender_balance": 0.50,
            "veterans": 0.10
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestSourceCandidatesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for SourceCandidatesHumanCapitalAgent

    Agent: Source candidates
    Path: src/superstandard/agents/api/source_candidates_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.source_candidates_human_capital_agent import (
            SourceCandidatesHumanCapitalAgent
        )
        return SourceCandidatesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.source_candidates_human_capital_agent import (
            SourceCandidatesHumanCapitalAgentConfig
        )
        return SourceCandidatesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for candidate sourcing."""
        return {
            "task_type": "source_candidates",
            "data": {
                "search_parameters": {
                    "job_title": "Senior Data Scientist",
                    "required_skills": ["python", "machine_learning", "tensorflow", "sql"],
                    "experience_level": "senior",
                    "locations": ["remote", "bay_area", "boston"],
                    "industries": ["technology", "finance", "healthcare"]
                },
                "sourcing_channels": {
                    "linkedin": {"searches": 10, "inmails": 50},
                    "github": {"target_contributors": True, "min_stars": 100},
                    "stackoverflow": {"reputation_min": 5000},
                    "referrals": {"employee_network": True, "bonus": 2000},
                    "job_boards": ["indeed", "glassdoor", "dice"]
                },
                "target_metrics": {
                    "candidates_sourced": 200,
                    "qualified_candidates": 50,
                    "response_rate_target": 0.30,
                    "diversity_target": 0.40
                },
                "engagement_strategy": {
                    "personalized_outreach": True,
                    "employer_branding": ["tech_blog", "open_source", "conferences"],
                    "value_proposition": ["remote_work", "cutting_edge_tech", "learning_culture"],
                    "response_time_sla": "24_hours"
                }
            },
            "context": {
                "urgency": "high",
                "budget": 5000,
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_multi_channel_sourcing(self):
        """Test multi-channel candidate sourcing."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_passive_candidate_sourcing(self):
        """Test sourcing passive candidates."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["candidate_type"] = "passive"
        input_data["data"]["engagement_strategy"]["approach"] = "relationship_building"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestOnboardDriversHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for OnboardDriversHumanCapitalAgent

    Agent: Onboard employees/drivers
    Path: src/superstandard/agents/api/onboard_drivers_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.onboard_drivers_human_capital_agent import (
            OnboardDriversHumanCapitalAgent
        )
        return OnboardDriversHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.onboard_drivers_human_capital_agent import (
            OnboardDriversHumanCapitalAgentConfig
        )
        return OnboardDriversHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for onboarding."""
        return {
            "task_type": "onboard_employee",
            "data": {
                "new_hire": {
                    "employee_id": "EMP-2025-001",
                    "name": "Jane Smith",
                    "position": "Senior Software Engineer",
                    "department": "engineering",
                    "manager": "MGR-123",
                    "start_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "location": "remote",
                    "employment_type": "full_time"
                },
                "pre_boarding": {
                    "tasks": ["send_welcome_email", "send_paperwork", "setup_accounts", "ship_equipment"],
                    "paperwork": ["i9", "w4", "direct_deposit", "benefits_enrollment", "nda", "policy_acknowledgments"],
                    "equipment": ["laptop", "monitor", "keyboard", "mouse", "headset"],
                    "account_setup": ["email", "slack", "github", "jira", "confluence"]
                },
                "onboarding_plan": {
                    "week_1": {
                        "orientation": ["company_overview", "culture_values", "org_structure"],
                        "admin": ["hr_systems", "expense_reporting", "time_tracking"],
                        "dept_intro": ["team_meetings", "1on1_with_manager", "buddy_assignment"],
                        "training": ["security_training", "compliance_training", "tools_training"]
                    },
                    "week_2_4": {
                        "role_training": ["codebase_review", "architecture_overview", "first_task"],
                        "relationship_building": ["stakeholder_meetings", "cross_functional_intros"],
                        "goals": ["30_day_objectives", "learning_plan"]
                    },
                    "day_30_90": {
                        "milestones": ["first_project", "peer_review", "30_day_feedback", "90_day_review"],
                        "integration": ["team_contribution", "knowledge_sharing", "process_improvement"]
                    }
                },
                "success_metrics": {
                    "completion_rate": 1.0,
                    "time_to_productivity": "30_days",
                    "satisfaction_score_target": 0.85,
                    "retention_target": 0.90
                }
            },
            "context": {
                "onboarding_type": "technical_role",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_complete_onboarding_workflow(self):
        """Test complete onboarding workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_remote_onboarding(self):
        """Test remote employee onboarding."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["new_hire"]["location"] = "remote"
        input_data["data"]["onboarding_plan"]["remote_considerations"] = {
            "virtual_meetups": True,
            "shipping_logistics": True,
            "timezone_coordination": True
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestDevelopCounselEmployeesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for DevelopCounselEmployeesHumanCapitalAgent (APQC 7.3)

    Agent: Develop and counsel employees
    Path: src/superstandard/agents/api/develop_counsel_employees_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.develop_counsel_employees_human_capital_agent import (
            DevelopCounselEmployeesHumanCapitalAgent
        )
        return DevelopCounselEmployeesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.develop_counsel_employees_human_capital_agent import (
            DevelopCounselEmployeesHumanCapitalAgentConfig
        )
        return DevelopCounselEmployeesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for employee development."""
        return {
            "task_type": "develop_employee",
            "data": {
                "employee": {
                    "employee_id": "EMP-456",
                    "name": "John Doe",
                    "position": "Software Engineer",
                    "tenure": "2_years",
                    "performance_rating": "exceeds_expectations",
                    "career_aspirations": ["tech_lead", "architect", "management"]
                },
                "development_needs": {
                    "skill_gaps": ["system_design", "leadership", "public_speaking"],
                    "technical_areas": ["distributed_systems", "cloud_architecture"],
                    "soft_skills": ["communication", "mentoring", "project_management"],
                    "certifications_desired": ["aws_solutions_architect", "pmp"]
                },
                "development_plan": {
                    "learning_objectives": [
                        "master_distributed_systems",
                        "develop_leadership_skills",
                        "mentor_junior_engineers"
                    ],
                    "activities": {
                        "courses": ["distributed_systems_course", "leadership_training"],
                        "projects": ["lead_microservices_migration", "mentor_2_juniors"],
                        "conferences": ["aws_reinvent", "kubecon"],
                        "certifications": ["aws_solutions_architect"]
                    },
                    "timeline": "12_months",
                    "budget": 5000,
                    "milestones": ["Q1_course_completion", "Q2_project_delivery", "Q3_certification", "Q4_leadership_role"]
                },
                "counseling_needs": {
                    "career_guidance": True,
                    "performance_coaching": False,
                    "work_life_balance": False,
                    "conflict_resolution": False
                },
                "manager_support": {
                    "1on1_frequency": "weekly",
                    "feedback_cadence": "continuous",
                    "stretch_assignments": True,
                    "visibility_opportunities": ["tech_talks", "architecture_reviews"]
                }
            },
            "context": {
                "development_cycle": "annual",
                "retention_risk": "low",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_career_development_planning(self):
        """Test career development planning."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_performance_counseling(self):
        """Test performance counseling."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["counseling_needs"]["performance_coaching"] = True
        input_data["data"]["employee"]["performance_rating"] = "needs_improvement"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestDevelopEmployeeCompetenciesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for DevelopEmployeeCompetenciesHumanCapitalAgent

    Agent: Develop employee competencies
    Path: src/superstandard/agents/api/develop_employee_competencies_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.develop_employee_competencies_human_capital_agent import (
            DevelopEmployeeCompetenciesHumanCapitalAgent
        )
        return DevelopEmployeeCompetenciesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.develop_employee_competencies_human_capital_agent import (
            DevelopEmployeeCompetenciesHumanCapitalAgentConfig
        )
        return DevelopEmployeeCompetenciesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for competency development."""
        return {
            "task_type": "develop_competencies",
            "data": {
                "competency_framework": {
                    "technical_competencies": [
                        {"name": "programming", "levels": ["basic", "intermediate", "advanced", "expert"]},
                        {"name": "system_design", "levels": ["basic", "intermediate", "advanced", "expert"]},
                        {"name": "cloud_platforms", "levels": ["basic", "intermediate", "advanced", "expert"]}
                    ],
                    "leadership_competencies": [
                        {"name": "team_management", "levels": ["basic", "intermediate", "advanced", "expert"]},
                        {"name": "strategic_thinking", "levels": ["basic", "intermediate", "advanced", "expert"]},
                        {"name": "change_management", "levels": ["basic", "intermediate", "advanced", "expert"]}
                    ],
                    "business_competencies": [
                        {"name": "project_management", "levels": ["basic", "intermediate", "advanced", "expert"]},
                        {"name": "stakeholder_management", "levels": ["basic", "intermediate", "advanced", "expert"]}
                    ]
                },
                "employee_cohort": {
                    "cohort_id": "ENG-2025-Q1",
                    "employees": 20,
                    "departments": ["engineering"],
                    "levels": ["mid_level", "senior"],
                    "average_tenure": "3_years"
                },
                "current_competencies": {
                    "technical_average": "intermediate",
                    "leadership_average": "basic",
                    "business_average": "intermediate"
                },
                "target_competencies": {
                    "technical_target": "advanced",
                    "leadership_target": "intermediate",
                    "business_target": "advanced",
                    "timeline": "12_months"
                },
                "development_programs": {
                    "training_courses": ["advanced_python", "system_design", "leadership_fundamentals"],
                    "certifications": ["aws_certified", "pmp"],
                    "mentoring": {"pairs": 10, "duration": "6_months"},
                    "job_rotation": {"opportunities": 5, "duration": "3_months"},
                    "stretch_assignments": {"count": 15, "difficulty": "challenging"}
                }
            },
            "context": {
                "program_type": "competency_development",
                "budget": 50000,
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_competency_assessment(self):
        """Test competency assessment."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "assess_competencies"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_competency_gap_analysis(self):
        """Test competency gap analysis."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestManagePerformanceHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for ManagePerformanceHumanCapitalAgent

    Agent: Manage employee performance
    Path: src/superstandard/agents/api/manage_performance_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgent
        )
        return ManagePerformanceHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgentConfig
        )
        return ManagePerformanceHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for performance management."""
        return {
            "task_type": "manage_performance",
            "data": {
                "employee": {
                    "employee_id": "EMP-789",
                    "name": "Alice Johnson",
                    "position": "Product Manager",
                    "manager_id": "MGR-456",
                    "review_period": "2025-Q1"
                },
                "performance_goals": {
                    "objectives": [
                        {"id": "OBJ-1", "description": "Launch product V2", "weight": 0.40, "status": "achieved"},
                        {"id": "OBJ-2", "description": "Improve user engagement 20%", "weight": 0.30, "status": "exceeded"},
                        {"id": "OBJ-3", "description": "Mentor 2 associate PMs", "weight": 0.20, "status": "achieved"},
                        {"id": "OBJ-4", "description": "Complete product management cert", "weight": 0.10, "status": "in_progress"}
                    ],
                    "okrs": [
                        {"objective": "Grow user base", "key_results": ["10k new users", "20% engagement", "NPS 50"]},
                        {"objective": "Improve product quality", "key_results": ["Reduce bugs 30%", "Increase uptime 99.9%"]}
                    ]
                },
                "performance_data": {
                    "achievements": [
                        "Successfully launched product V2 on schedule",
                        "User engagement increased 25% (exceeded target)",
                        "Mentored 2 associate PMs with positive feedback"
                    ],
                    "competencies": {
                        "product_strategy": 4.5,
                        "stakeholder_management": 4.0,
                        "data_driven_decision_making": 4.5,
                        "team_collaboration": 5.0,
                        "innovation": 4.0
                    },
                    "peer_feedback": {
                        "strengths": ["strategic_thinking", "collaboration", "customer_focus"],
                        "development_areas": ["technical_depth", "delegation"]
                    },
                    "manager_feedback": {
                        "rating": "exceeds_expectations",
                        "comments": "Outstanding performance, ready for next level"
                    }
                },
                "performance_metrics": {
                    "goal_achievement_rate": 0.90,
                    "competency_average": 4.4,
                    "360_feedback_score": 4.3,
                    "customer_satisfaction": 0.88
                }
            },
            "context": {
                "review_cycle": "quarterly",
                "calibration_session": "completed",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_performance_review(self):
        """Test performance review process."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_goal_setting(self):
        """Test goal setting process."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "set_goals"
        input_data["data"]["next_period"] = "2025-Q2"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestManageCompensationHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for ManageCompensationHumanCapitalAgent (APQC 7.4)

    Agent: Manage compensation
    Path: src/superstandard/agents/api/manage_compensation_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_compensation_human_capital_agent import (
            ManageCompensationHumanCapitalAgent
        )
        return ManageCompensationHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_compensation_human_capital_agent import (
            ManageCompensationHumanCapitalAgentConfig
        )
        return ManageCompensationHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.4",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for compensation management."""
        return {
            "task_type": "manage_compensation",
            "data": {
                "compensation_philosophy": {
                    "market_positioning": "60th_percentile",
                    "pay_for_performance": True,
                    "internal_equity": True,
                    "transparency_level": "ranges_published"
                },
                "salary_structure": {
                    "grade_levels": 10,
                    "progression_criteria": ["performance", "tenure", "market"],
                    "band_width": 0.40,
                    "midpoint_progression": 0.15
                },
                "employee_population": {
                    "total_employees": 500,
                    "departments": ["engineering", "sales", "operations", "support"],
                    "geographic_distribution": ["us", "europe", "asia"],
                    "compensation_review_eligible": 450
                },
                "market_data": {
                    "sources": ["radford", "payscale", "glassdoor"],
                    "peer_companies": 20,
                    "market_movement": 0.05,
                    "cost_of_living_adjustments": {"sf": 1.3, "nyc": 1.25, "austin": 1.0}
                },
                "compensation_review": {
                    "review_type": "annual",
                    "budget": 5000000,
                    "merit_pool": 0.04,
                    "promotion_pool": 0.02,
                    "equity_refresh": 0.015,
                    "guidelines": {
                        "exceeds_expectations": {"min": 0.05, "max": 0.08},
                        "meets_expectations": {"min": 0.03, "max": 0.05},
                        "needs_improvement": {"min": 0.0, "max": 0.02}
                    }
                },
                "equity_program": {
                    "type": "rsu",
                    "vesting_schedule": "4_year_monthly",
                    "cliff": "1_year",
                    "refresh_grants": True
                }
            },
            "context": {
                "review_cycle": "annual",
                "effective_date": "2025-04-01",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_compensation_planning(self):
        """Test compensation planning."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_market_benchmarking(self):
        """Test market benchmarking."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "benchmark_compensation"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestRewardRetainEmployeesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for RewardRetainEmployeesHumanCapitalAgent (APQC 7.4)

    Agent: Reward and retain employees
    Path: src/superstandard/agents/api/reward_retain_employees_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.reward_retain_employees_human_capital_agent import (
            RewardRetainEmployeesHumanCapitalAgent
        )
        return RewardRetainEmployeesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.reward_retain_employees_human_capital_agent import (
            RewardRetainEmployeesHumanCapitalAgentConfig
        )
        return RewardRetainEmployeesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.4",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for reward and retention."""
        return {
            "task_type": "reward_retain",
            "data": {
                "retention_strategy": {
                    "target_retention_rate": 0.92,
                    "critical_talent_retention": 0.95,
                    "focus_areas": ["top_performers", "high_potential", "critical_skills"],
                    "risk_factors": ["market_competition", "compensation_gap", "career_stagnation"]
                },
                "reward_programs": {
                    "recognition": {
                        "peer_recognition": True,
                        "spot_awards": {"budget": 50000, "avg_amount": 500},
                        "quarterly_awards": {"categories": ["innovation", "teamwork", "customer_focus"]},
                        "annual_awards": {"budget": 100000, "top_awards": 10}
                    },
                    "monetary_incentives": {
                        "performance_bonus": {"pool": 1000000, "payout_range": [0.05, 0.20]},
                        "retention_bonus": {"high_risk_employees": 50, "avg_bonus": 10000},
                        "referral_bonus": {"amount": 2000, "eligible_roles": "all"},
                        "project_completion_bonus": True
                    },
                    "non_monetary_rewards": {
                        "flexible_work": ["remote", "flexible_hours", "compressed_week"],
                        "learning_development": {"budget_per_employee": 2000, "conference_attendance": True},
                        "career_advancement": ["promotions", "lateral_moves", "stretch_assignments"],
                        "work_life_balance": ["additional_pto", "sabbatical", "wellness_programs"]
                    },
                    "equity_compensation": {
                        "refresh_grants": True,
                        "performance_accelerators": True,
                        "retention_grants": {"high_risk": True, "amount_multiplier": 1.5}
                    }
                },
                "retention_interventions": {
                    "at_risk_employees": {
                        "count": 25,
                        "risk_level": "high",
                        "retention_actions": ["compensation_adjustment", "role_change", "special_project"]
                    },
                    "stay_interviews": {
                        "frequency": "annual",
                        "target_population": "all_employees",
                        "key_questions": ["satisfaction", "career_goals", "improvement_areas"]
                    },
                    "counter_offers": {
                        "policy": "case_by_case",
                        "approval_level": "vp",
                        "max_adjustment": 0.20
                    }
                }
            },
            "context": {
                "retention_cycle": "ongoing",
                "market_conditions": "competitive",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_retention_risk_assessment(self):
        """Test retention risk assessment."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "assess_retention_risk"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_recognition_program(self):
        """Test recognition program management."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestRedeployRetireEmployeesHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for RedeployRetireEmployeesHumanCapitalAgent (APQC 7.5)

    Agent: Redeploy and retire employees
    Path: src/superstandard/agents/api/redeploy_retire_employees_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.redeploy_retire_employees_human_capital_agent import (
            RedeployRetireEmployeesHumanCapitalAgent
        )
        return RedeployRetireEmployeesHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.redeploy_retire_employees_human_capital_agent import (
            RedeployRetireEmployeesHumanCapitalAgentConfig
        )
        return RedeployRetireEmployeesHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_process_id": "7.5",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for redeployment/retirement."""
        return {
            "task_type": "manage_transition",
            "data": {
                "transition_type": "redeployment",
                "employee": {
                    "employee_id": "EMP-999",
                    "name": "Robert Chen",
                    "current_position": "Senior Engineer - Legacy Systems",
                    "tenure": "15_years",
                    "age": 58,
                    "skills": ["cobol", "mainframe", "sql", "project_management"]
                },
                "redeployment_scenario": {
                    "reason": "role_elimination",
                    "target_roles": ["technical_consultant", "architect", "trainer"],
                    "skill_transferability": 0.70,
                    "reskilling_required": ["cloud_platforms", "modern_architecture"],
                    "timeline": "90_days"
                },
                "redeployment_support": {
                    "internal_job_matching": True,
                    "skills_assessment": True,
                    "training_programs": ["cloud_certification", "modern_dev_practices"],
                    "career_counseling": True,
                    "transition_coach": True
                },
                "retirement_scenario": {
                    "retirement_eligibility": True,
                    "planned_retirement_date": "2026-12-31",
                    "succession_planning": {
                        "critical_knowledge": ["legacy_systems", "business_processes"],
                        "knowledge_transfer_plan": True,
                        "successor_identified": False,
                        "transition_period": "12_months"
                    }
                },
                "benefits_transition": {
                    "retirement_benefits": {
                        "pension": {"vested": True, "monthly_amount": 3500},
                        "401k": {"balance": 500000, "rollover_options": True},
                        "health_insurance": {"cobra": True, "retiree_coverage": True}
                    },
                    "severance_package": {
                        "eligible": True,
                        "weeks_of_pay": 52,
                        "continuation_benefits": "6_months"
                    }
                },
                "offboarding_process": {
                    "knowledge_transfer": {"duration": "3_months", "documentation": True},
                    "asset_return": ["laptop", "phone", "badge", "keys"],
                    "access_revocation": {"scheduled": True, "effective_date": "last_day"},
                    "exit_interview": {"scheduled": True, "feedback_collection": True}
                }
            },
            "context": {
                "organizational_change": "restructuring",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_redeployment_planning(self):
        """Test employee redeployment planning."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["transition_type"] = "redeployment"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_retirement_planning(self):
        """Test retirement planning."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["transition_type"] = "retirement"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestManageEmployeeInformationHumanCapitalAgent(APQCAgentTestCase):
    """
    Tests for ManageEmployeeInformationHumanCapitalAgent

    Agent: Manage employee information
    Path: src/superstandard/agents/api/manage_employee_information_human_capital_agent.py
    Domain: human_capital | Type: human_capital
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_employee_information_human_capital_agent import (
            ManageEmployeeInformationHumanCapitalAgent
        )
        return ManageEmployeeInformationHumanCapitalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_employee_information_human_capital_agent import (
            ManageEmployeeInformationHumanCapitalAgentConfig
        )
        return ManageEmployeeInformationHumanCapitalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "7.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for employee information management."""
        return {
            "task_type": "manage_employee_data",
            "data": {
                "employee_record": {
                    "employee_id": "EMP-12345",
                    "personal_info": {
                        "name": "Sarah Williams",
                        "date_of_birth": "1990-05-15",
                        "contact": {"email": "sarah.w@company.com", "phone": "555-0123"},
                        "address": {"street": "123 Main St", "city": "San Francisco", "state": "CA", "zip": "94105"}
                    },
                    "employment_info": {
                        "hire_date": "2020-03-01",
                        "position": "Senior Data Analyst",
                        "department": "analytics",
                        "manager_id": "MGR-789",
                        "employment_type": "full_time",
                        "status": "active"
                    },
                    "compensation_info": {
                        "base_salary": 125000,
                        "bonus_target": 0.15,
                        "equity_grants": ["RSU-2020-001", "RSU-2022-001"],
                        "pay_grade": "L5"
                    },
                    "benefits_enrollment": {
                        "health_insurance": "premium_plan",
                        "dental": "standard",
                        "vision": "standard",
                        "401k": {"contribution": 0.06, "match": 0.04},
                        "pto_balance": 15
                    }
                },
                "data_management_operation": {
                    "operation_type": "update",
                    "fields_to_update": ["address", "emergency_contact"],
                    "data_quality_check": True,
                    "audit_trail": True,
                    "notification_required": True
                },
                "compliance_requirements": {
                    "data_privacy": ["gdpr", "ccpa"],
                    "data_retention": "7_years_post_employment",
                    "access_controls": {"role_based": True, "need_to_know": True},
                    "encryption": {"at_rest": True, "in_transit": True}
                },
                "reporting_requirements": {
                    "regulatory": ["eeo1", "vets4212", "hipaa"],
                    "internal": ["headcount", "demographics", "compensation"],
                    "audit": ["changes", "access_logs", "data_exports"]
                }
            },
            "context": {
                "system": "hris",
                "requestor": "HR-Admin",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @pytest.mark.asyncio
    async def test_employee_data_update(self):
        """Test employee data update."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_data_privacy_compliance(self):
        """Test data privacy compliance."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "compliance_audit"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_7
@pytest.mark.apqc_integration
class TestCategory7Integration:
    """
    Integration tests for Category 7.0 - Human Capital agents.

    Tests complete employee lifecycle workflows from recruitment to retirement.
    """

    @pytest.mark.asyncio
    async def test_complete_employee_lifecycle(self):
        """
        Test complete employee lifecycle workflow.

        Workflow:
        1. Recruit and select (RecruitSourceSelectEmployeesHumanCapitalAgent)
        2. Onboard (OnboardDriversHumanCapitalAgent)
        3. Develop (DevelopCounselEmployeesHumanCapitalAgent)
        4. Manage performance (ManagePerformanceHumanCapitalAgent)
        5. Manage compensation (ManageCompensationHumanCapitalAgent)
        """
        # Import agents
        from superstandard.agents.api.recruit_source_select_employees_human_capital_agent import (
            RecruitSourceSelectEmployeesHumanCapitalAgent,
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig
        )
        from superstandard.agents.api.onboard_drivers_human_capital_agent import (
            OnboardDriversHumanCapitalAgent,
            OnboardDriversHumanCapitalAgentConfig
        )
        from superstandard.agents.api.develop_counsel_employees_human_capital_agent import (
            DevelopCounselEmployeesHumanCapitalAgent,
            DevelopCounselEmployeesHumanCapitalAgentConfig
        )
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgent,
            ManagePerformanceHumanCapitalAgentConfig
        )
        from superstandard.agents.api.manage_compensation_human_capital_agent import (
            ManageCompensationHumanCapitalAgent,
            ManageCompensationHumanCapitalAgentConfig
        )

        # Create agent instances
        recruit_agent = RecruitSourceSelectEmployeesHumanCapitalAgent(
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig()
        )
        onboard_agent = OnboardDriversHumanCapitalAgent(
            OnboardDriversHumanCapitalAgentConfig()
        )
        develop_agent = DevelopCounselEmployeesHumanCapitalAgent(
            DevelopCounselEmployeesHumanCapitalAgentConfig()
        )
        performance_agent = ManagePerformanceHumanCapitalAgent(
            ManagePerformanceHumanCapitalAgentConfig()
        )
        compensation_agent = ManageCompensationHumanCapitalAgent(
            ManageCompensationHumanCapitalAgentConfig()
        )

        # Step 1: Recruit
        recruit_input = {
            "task_type": "recruit_employees",
            "data": {
                "job_requisition": {
                    "position_title": "Software Engineer",
                    "headcount": 1
                },
                "job_requirements": {"required_skills": ["python"]}
            },
            "priority": "high"
        }
        recruit_result = await recruit_agent.execute(recruit_input)
        assert recruit_result['status'] in ['completed', 'degraded']

        # Step 2: Onboard
        onboard_input = {
            "task_type": "onboard_employee",
            "data": {
                "new_hire": {
                    "employee_id": "EMP-NEW-001",
                    "position": "Software Engineer",
                    "start_date": (datetime.now() + timedelta(days=14)).isoformat()
                },
                "onboarding_plan": {"week_1": {}}
            },
            "priority": "high"
        }
        onboard_result = await onboard_agent.execute(onboard_input)
        assert onboard_result['status'] in ['completed', 'degraded']

        # Step 3: Develop
        develop_input = {
            "task_type": "develop_employee",
            "data": {
                "employee": {"employee_id": "EMP-NEW-001"},
                "development_needs": {"skill_gaps": ["leadership"]},
                "development_plan": {"timeline": "12_months"}
            },
            "priority": "medium"
        }
        develop_result = await develop_agent.execute(develop_input)
        assert develop_result['status'] in ['completed', 'degraded']

        # Step 4: Manage performance
        performance_input = {
            "task_type": "manage_performance",
            "data": {
                "employee": {"employee_id": "EMP-NEW-001", "review_period": "2025-Q1"},
                "performance_goals": {"objectives": []}
            },
            "priority": "high"
        }
        performance_result = await performance_agent.execute(performance_input)
        assert performance_result['status'] in ['completed', 'degraded']

        # Step 5: Manage compensation
        compensation_input = {
            "task_type": "manage_compensation",
            "data": {
                "compensation_philosophy": {"market_positioning": "50th_percentile"},
                "compensation_review": {"review_type": "annual"}
            },
            "priority": "high"
        }
        compensation_result = await compensation_agent.execute(compensation_input)
        assert compensation_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_talent_acquisition_workflow(self):
        """Test end-to-end talent acquisition workflow."""
        from superstandard.agents.api.source_candidates_human_capital_agent import (
            SourceCandidatesHumanCapitalAgent,
            SourceCandidatesHumanCapitalAgentConfig
        )
        from superstandard.agents.api.recruit_source_select_employees_human_capital_agent import (
            RecruitSourceSelectEmployeesHumanCapitalAgent,
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig
        )

        source_agent = SourceCandidatesHumanCapitalAgent(
            SourceCandidatesHumanCapitalAgentConfig()
        )
        recruit_agent = RecruitSourceSelectEmployeesHumanCapitalAgent(
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig()
        )

        # Source candidates
        source_input = {
            "task_type": "source_candidates",
            "data": {
                "search_parameters": {"job_title": "Data Scientist"},
                "sourcing_channels": {"linkedin": {"searches": 10}}
            },
            "priority": "high"
        }
        source_result = await source_agent.execute(source_input)
        assert source_result['status'] in ['completed', 'degraded']

        # Recruit from sourced candidates
        recruit_input = {
            "task_type": "recruit_employees",
            "data": {
                "job_requisition": {"position_title": "Data Scientist"},
                "candidate_pool": source_result.get('output', {})
            },
            "priority": "high"
        }
        recruit_result = await recruit_agent.execute(recruit_input)
        assert recruit_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_performance_compensation_integration(self):
        """Test integration between performance and compensation management."""
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgent,
            ManagePerformanceHumanCapitalAgentConfig
        )
        from superstandard.agents.api.reward_retain_employees_human_capital_agent import (
            RewardRetainEmployeesHumanCapitalAgent,
            RewardRetainEmployeesHumanCapitalAgentConfig
        )

        performance_agent = ManagePerformanceHumanCapitalAgent(
            ManagePerformanceHumanCapitalAgentConfig()
        )
        reward_agent = RewardRetainEmployeesHumanCapitalAgent(
            RewardRetainEmployeesHumanCapitalAgentConfig()
        )

        # Evaluate performance
        performance_input = {
            "task_type": "manage_performance",
            "data": {
                "employee": {"employee_id": "EMP-001"},
                "performance_goals": {"objectives": []},
                "performance_data": {"manager_feedback": {"rating": "exceeds_expectations"}}
            },
            "priority": "high"
        }
        performance_result = await performance_agent.execute(performance_input)
        assert performance_result['status'] in ['completed', 'degraded']

        # Reward based on performance
        reward_input = {
            "task_type": "reward_retain",
            "data": {
                "retention_strategy": {"target_retention_rate": 0.90},
                "reward_programs": {"recognition": {"peer_recognition": True}},
                "performance_data": performance_result.get('output', {})
            },
            "priority": "high"
        }
        reward_result = await reward_agent.execute(reward_input)
        assert reward_result['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_7
class TestCategory7Capabilities:
    """
    Test category-specific capabilities for Human Capital agents.
    """

    @pytest.mark.asyncio
    async def test_competency_based_hiring(self):
        """Test competency-based hiring approach."""
        from superstandard.agents.api.recruit_source_select_employees_human_capital_agent import (
            RecruitSourceSelectEmployeesHumanCapitalAgent,
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig
        )

        agent = RecruitSourceSelectEmployeesHumanCapitalAgent(
            RecruitSourceSelectEmployeesHumanCapitalAgentConfig()
        )

        input_data = {
            "task_type": "recruit_employees",
            "data": {
                "job_requisition": {"position_title": "Product Manager"},
                "job_requirements": {
                    "competencies": ["strategic_thinking", "stakeholder_management", "data_driven"]
                },
                "selection_process": {"assessments": ["competency_assessment"]}
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_continuous_performance_management(self):
        """Test continuous performance management."""
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgent,
            ManagePerformanceHumanCapitalAgentConfig
        )

        agent = ManagePerformanceHumanCapitalAgent(
            ManagePerformanceHumanCapitalAgentConfig()
        )

        input_data = {
            "task_type": "manage_performance",
            "data": {
                "employee": {"employee_id": "EMP-001"},
                "performance_goals": {"objectives": []},
                "feedback_model": "continuous"
            },
            "context": {"review_cycle": "continuous"},
            "priority": "medium"
        }

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Performance Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_7
@pytest.mark.slow
class TestCategory7Performance:
    """
    Performance tests for Category 7 agents.
    """

    @pytest.mark.asyncio
    async def test_bulk_employee_data_processing(self):
        """Test processing bulk employee data updates."""
        import asyncio
        from superstandard.agents.api.manage_employee_information_human_capital_agent import (
            ManageEmployeeInformationHumanCapitalAgent,
            ManageEmployeeInformationHumanCapitalAgentConfig
        )

        agent = ManageEmployeeInformationHumanCapitalAgent(
            ManageEmployeeInformationHumanCapitalAgentConfig()
        )

        tasks = []
        for i in range(10):
            input_data = {
                "task_type": "manage_employee_data",
                "data": {
                    "employee_record": {
                        "employee_id": f"EMP-{i:05d}",
                        "personal_info": {"name": f"Employee {i}"}
                    },
                    "data_management_operation": {"operation_type": "update"}
                },
                "priority": "medium"
            }
            tasks.append(agent.execute(input_data))

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_concurrent_performance_reviews(self):
        """Test concurrent performance review processing."""
        import asyncio
        from superstandard.agents.api.manage_performance_human_capital_agent import (
            ManagePerformanceHumanCapitalAgent,
            ManagePerformanceHumanCapitalAgentConfig
        )

        agents = [
            ManagePerformanceHumanCapitalAgent(
                ManagePerformanceHumanCapitalAgentConfig()
            )
            for _ in range(5)
        ]

        input_data = {
            "task_type": "manage_performance",
            "data": {
                "employee": {"employee_id": "EMP-001"},
                "performance_goals": {"objectives": []}
            },
            "priority": "high"
        }

        tasks = [agent.execute(input_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
