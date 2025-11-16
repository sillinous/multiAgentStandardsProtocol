"""
APQC Category 13.0 - Business Capabilities Agent Tests

Comprehensive tests for all Business Capabilities agents from APQC Category 13.0.
(Note: These agents use category_id "12.0" in their code but are referred to as
Category 13.0 in documentation for organizational purposes)

Agents tested:
1. ManageBusinessProcessesCapabilityDevelopmentAgent (12.0.1)
2. InitiateProjectsCapabilityDevelopmentAgent (12.0.2)
3. ExecuteProjectsCapabilityDevelopmentAgent (12.3.3)
4. ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent (12.0.3)
5. ManageEnterpriseQualityCapabilityDevelopmentAgent (12.0.4)
6. ManageChangeCapabilityDevelopmentAgent (12.0.5)
7. DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent (12.0.6)

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Business process management
- Project and program management workflows
- Quality management systems
- Change management processes
- Knowledge management systems
- Multi-agent project execution workflows
- Portfolio optimization tests

Version: 1.0.0
Framework: APQC 7.0.1
Category: 13.0 (code: 12.0) - Develop and Manage Business Capabilities
"""

import pytest
from typing import Dict, Any
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 13.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestManageBusinessProcessesCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for ManageBusinessProcessesCapabilityDevelopmentAgent

    Agent: Manage business processes
    Path: src/superstandard/agents/business/manage_business_processes_capability_development_agent.py
    Domain: process_improvement | Type: capability_development
    APQC: 12.0.1 (13.1 Manage business processes)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.business.manage_business_processes_capability_development_agent import (
            ManageBusinessProcessesCapabilityDevelopmentAgent
        )
        return ManageBusinessProcessesCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.business.manage_business_processes_capability_development_agent import (
            ManageBusinessProcessesCapabilityDevelopmentAgentConfig
        )
        return ManageBusinessProcessesCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.1",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["process_management", "process_improvement", "optimization", "analysis"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for business process management."""
        return {
            "task_type": "manage_business_process",
            "data": {
                "process": {
                    "id": "PROC-001",
                    "name": "Order_to_Cash",
                    "department": "sales_operations",
                    "owner": "VP_Sales_Operations"
                },
                "current_state": {
                    "cycle_time_days": 15,
                    "error_rate": 0.05,
                    "cost_per_transaction": 25,
                    "customer_satisfaction": 3.5
                },
                "improvement_goals": {
                    "cycle_time_reduction": 0.30,
                    "error_rate_target": 0.02,
                    "cost_reduction": 0.20,
                    "satisfaction_target": 4.5
                },
                "process_steps": [
                    {"step": "order_receipt", "duration_hours": 2, "automation": "manual"},
                    {"step": "credit_check", "duration_hours": 24, "automation": "automated"},
                    {"step": "fulfillment", "duration_hours": 120, "automation": "semi_automated"},
                    {"step": "invoicing", "duration_hours": 4, "automation": "automated"},
                    {"step": "payment_collection", "duration_hours": 240, "automation": "manual"}
                ],
                "improvement_initiatives": [
                    "automate_order_receipt",
                    "optimize_fulfillment",
                    "streamline_invoicing"
                ]
            },
            "context": {
                "priority": "high",
                "timeframe": "Q2_2025",
                "budget": 100000
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_process_optimization(self):
        """Test process optimization and improvement recommendations."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "optimize_process"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_process_mapping(self):
        """Test business process mapping and documentation."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "map_process",
            "data": {
                "process_name": "Procure_to_Pay",
                "stakeholders": ["procurement", "finance", "operations"],
                "process_steps": 12
            },
            "priority": "medium"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestInitiateProjectsCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for InitiateProjectsCapabilityDevelopmentAgent

    Agent: Initiate projects
    Path: src/superstandard/agents/infrastructure/initiate_projects_capability_development_agent.py
    Domain: project_management | Type: capability_development
    APQC: 12.0.2 (13.2 Project initiation)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.initiate_projects_capability_development_agent import (
            InitiateProjectsCapabilityDevelopmentAgent
        )
        return InitiateProjectsCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.initiate_projects_capability_development_agent import (
            InitiateProjectsCapabilityDevelopmentAgentConfig
        )
        return InitiateProjectsCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.2",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["project_initiation", "feasibility_analysis", "planning", "stakeholder_management"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for project initiation."""
        return {
            "task_type": "initiate_project",
            "data": {
                "project": {
                    "name": "Digital_Transformation_Initiative",
                    "type": "strategic",
                    "sponsor": "CEO",
                    "proposed_budget": 5000000,
                    "duration_months": 18
                },
                "business_case": {
                    "objectives": [
                        "improve_customer_experience",
                        "increase_operational_efficiency",
                        "enable_data_driven_decisions"
                    ],
                    "benefits": {
                        "revenue_increase": 2000000,
                        "cost_savings": 1000000,
                        "efficiency_gain": 0.25
                    },
                    "risks": [
                        {"risk": "technology_adoption", "probability": 0.6, "impact": "medium"},
                        {"risk": "budget_overrun", "probability": 0.4, "impact": "high"}
                    ]
                },
                "stakeholders": {
                    "sponsor": "CEO",
                    "project_manager": "PMO_Director",
                    "team_members": ["IT", "Operations", "Sales", "Finance"],
                    "beneficiaries": ["customers", "employees", "shareholders"]
                },
                "success_criteria": {
                    "on_time": True,
                    "on_budget": True,
                    "quality_threshold": 0.90,
                    "stakeholder_satisfaction": 4.0
                }
            },
            "context": {
                "priority": "high",
                "strategic_alignment": "high",
                "urgency": "medium"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_project_charter_creation(self):
        """Test project charter creation and approval."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "create_project_charter"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_feasibility_analysis(self):
        """Test project feasibility analysis."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "analyze_feasibility"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestExecuteProjectsCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for ExecuteProjectsCapabilityDevelopmentAgent

    Agent: Execute projects
    Path: src/superstandard/agents/infrastructure/execute_projects_capability_development_agent.py
    Domain: project_execution | Type: operational
    APQC: 12.3.3 (13.2 Project execution)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.execute_projects_capability_development_agent import (
            ExecuteProjectsCapabilityDevelopmentAgent
        )
        return ExecuteProjectsCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.execute_projects_capability_development_agent import (
            ExecuteProjectsCapabilityDevelopmentAgentConfig
        )
        return ExecuteProjectsCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_process_id": "12.3.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for project execution."""
        return {
            "task_type": "execute_project",
            "data": {
                "project_tasks": [
                    {
                        "id": "T1",
                        "name": "Requirements_Gathering",
                        "duration_days": 30,
                        "dependencies": [],
                        "resources": 3
                    },
                    {
                        "id": "T2",
                        "name": "Design",
                        "duration_days": 45,
                        "dependencies": ["T1"],
                        "resources": 5
                    },
                    {
                        "id": "T3",
                        "name": "Development",
                        "duration_days": 90,
                        "dependencies": ["T2"],
                        "resources": 10
                    },
                    {
                        "id": "T4",
                        "name": "Testing",
                        "duration_days": 30,
                        "dependencies": ["T3"],
                        "resources": 4
                    },
                    {
                        "id": "T5",
                        "name": "Deployment",
                        "duration_days": 15,
                        "dependencies": ["T4"],
                        "resources": 6
                    }
                ],
                "resources": [
                    {"id": "R1", "role": "project_manager", "availability": 1.0},
                    {"id": "R2", "role": "developer", "availability": 0.8},
                    {"id": "R3", "role": "qa_engineer", "availability": 0.9}
                ],
                "budget": {
                    "total": 500000,
                    "allocated": 450000,
                    "spent": 200000,
                    "remaining": 250000
                },
                "timeline": {
                    "start_date": "2025-01-01",
                    "planned_end": "2025-07-01",
                    "current_date": "2025-03-01"
                }
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_task_scheduling(self):
        """Test project task scheduling using CPM."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_resource_allocation(self):
        """Test project resource allocation and optimization."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "allocate_resources"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent

    Agent: Manage portfolio of enterprise programs and projects
    Path: src/superstandard/agents/trading/manage_portfolio_of_enterprise_programs_projects_capability_development_agent.py
    Domain: portfolio_management | Type: capability_development
    APQC: 12.0.3 (13.2 Portfolio/program management)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.manage_portfolio_of_enterprise_programs_projects_capability_development_agent import (
            ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent
        )
        return ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.manage_portfolio_of_enterprise_programs_projects_capability_development_agent import (
            ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgentConfig
        )
        return ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.3",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["portfolio_management", "prioritization", "resource_optimization", "strategic_alignment"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for portfolio management."""
        return {
            "task_type": "manage_portfolio",
            "data": {
                "portfolio": {
                    "id": "PORTFOLIO-2025",
                    "name": "Enterprise_Strategic_Portfolio",
                    "total_budget": 20000000,
                    "strategic_themes": [
                        "digital_transformation",
                        "operational_excellence",
                        "customer_experience"
                    ]
                },
                "projects": [
                    {
                        "id": "PROJ-001",
                        "name": "CRM_Upgrade",
                        "budget": 3000000,
                        "strategic_value": 0.85,
                        "roi": 0.45,
                        "risk": "medium",
                        "status": "in_progress",
                        "completion": 0.60
                    },
                    {
                        "id": "PROJ-002",
                        "name": "Supply_Chain_Optimization",
                        "budget": 5000000,
                        "strategic_value": 0.90,
                        "roi": 0.60,
                        "risk": "high",
                        "status": "planning",
                        "completion": 0.10
                    },
                    {
                        "id": "PROJ-003",
                        "name": "Customer_Portal",
                        "budget": 2000000,
                        "strategic_value": 0.75,
                        "roi": 0.35,
                        "risk": "low",
                        "status": "in_progress",
                        "completion": 0.80
                    }
                ],
                "resource_constraints": {
                    "budget": 20000000,
                    "personnel": 150,
                    "timeline": "fiscal_year_2025"
                },
                "optimization_goals": {
                    "maximize_strategic_value": True,
                    "balance_risk": True,
                    "optimize_resource_utilization": True
                }
            },
            "context": {
                "priority": "high",
                "review_cycle": "quarterly"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_portfolio_optimization(self):
        """Test portfolio optimization and prioritization."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "optimize_portfolio"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_portfolio_balancing(self):
        """Test portfolio risk balancing and diversification."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "balance_portfolio"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestManageEnterpriseQualityCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for ManageEnterpriseQualityCapabilityDevelopmentAgent

    Agent: Manage enterprise quality
    Path: src/superstandard/agents/testing/manage_enterprise_quality_capability_development_agent.py
    Domain: quality_management | Type: capability_development
    APQC: 12.0.4 (13.3 Quality management)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.testing.manage_enterprise_quality_capability_development_agent import (
            ManageEnterpriseQualityCapabilityDevelopmentAgent
        )
        return ManageEnterpriseQualityCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.testing.manage_enterprise_quality_capability_development_agent import (
            ManageEnterpriseQualityCapabilityDevelopmentAgentConfig
        )
        return ManageEnterpriseQualityCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.4",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["quality_management", "continuous_improvement", "standards_compliance", "audit"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for enterprise quality management."""
        return {
            "task_type": "manage_quality",
            "data": {
                "quality_program": {
                    "framework": "ISO_9001",
                    "maturity_level": "level_3",
                    "certification_status": "certified",
                    "next_audit": "2025-06-15"
                },
                "quality_metrics": {
                    "defect_rate": 0.02,
                    "customer_satisfaction": 4.2,
                    "process_capability": 1.33,
                    "first_pass_yield": 0.95,
                    "cost_of_quality": 0.05
                },
                "improvement_initiatives": [
                    {
                        "name": "Six_Sigma_Green_Belt_Training",
                        "participants": 50,
                        "expected_benefit": "defect_reduction_30_percent"
                    },
                    {
                        "name": "Process_Automation",
                        "investment": 200000,
                        "expected_benefit": "error_reduction_50_percent"
                    }
                ],
                "quality_standards": [
                    "ISO_9001",
                    "Six_Sigma",
                    "Lean_Manufacturing"
                ],
                "audit_findings": {
                    "critical": 0,
                    "major": 2,
                    "minor": 5,
                    "observations": 8
                }
            },
            "context": {
                "priority": "high",
                "quality_culture": "mature"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_quality_system_management(self):
        """Test quality management system oversight."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_quality_audit(self):
        """Test quality audit planning and execution."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "conduct_audit",
            "data": {
                "audit_type": "internal",
                "scope": "manufacturing_processes",
                "standard": "ISO_9001"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestManageChangeCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for ManageChangeCapabilityDevelopmentAgent

    Agent: Manage change
    Path: src/superstandard/agents/infrastructure/manage_change_capability_development_agent.py
    Domain: change_management | Type: capability_development
    APQC: 12.0.5 (13.4 Change management)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.manage_change_capability_development_agent import (
            ManageChangeCapabilityDevelopmentAgent
        )
        return ManageChangeCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.manage_change_capability_development_agent import (
            ManageChangeCapabilityDevelopmentAgentConfig
        )
        return ManageChangeCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.5",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["change_management", "stakeholder_engagement", "training", "communication"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for change management."""
        return {
            "task_type": "manage_change",
            "data": {
                "change_initiative": {
                    "name": "ERP_System_Replacement",
                    "type": "transformational",
                    "scope": "enterprise_wide",
                    "timeline": "12_months",
                    "budget": 10000000
                },
                "impact_analysis": {
                    "affected_employees": 5000,
                    "affected_processes": 150,
                    "departments": ["finance", "operations", "hr", "sales", "procurement"],
                    "change_magnitude": "high",
                    "readiness_score": 0.65
                },
                "stakeholders": {
                    "sponsors": ["CEO", "CFO"],
                    "champions": ["department_heads"],
                    "resistors": ["legacy_system_users"],
                    "neutrals": ["new_employees"]
                },
                "change_strategy": {
                    "communication_plan": {
                        "frequency": "weekly",
                        "channels": ["email", "town_halls", "intranet"],
                        "key_messages": ["why_change", "benefits", "support_available"]
                    },
                    "training_plan": {
                        "modules": 8,
                        "delivery": "blended",
                        "duration_hours": 40,
                        "target_completion": "90_percent"
                    },
                    "support_plan": {
                        "help_desk": True,
                        "super_users": 100,
                        "documentation": "comprehensive"
                    }
                },
                "success_metrics": {
                    "user_adoption": 0.85,
                    "proficiency": 0.75,
                    "resistance_level": 0.15,
                    "roi_realization": 0.80
                }
            },
            "context": {
                "priority": "critical",
                "change_culture": "moderate"
            },
            "priority": "critical"
        }

    @pytest.mark.asyncio
    async def test_change_readiness_assessment(self):
        """Test organizational change readiness assessment."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "assess_readiness"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_stakeholder_engagement(self):
        """Test stakeholder engagement and communication."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "engage_stakeholders"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestDevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent

    Agent: Develop and manage enterprise-wide knowledge management
    Path: src/superstandard/agents/infrastructure/develop_manage_enterprise_wide_knowledge_management_capability_development_agent.py
    Domain: knowledge_management | Type: capability_development
    APQC: 12.0.6 (13.5 Knowledge management)
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.develop_manage_enterprise_wide_knowledge_management_capability_development_agent import (
            DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent
        )
        return DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.develop_manage_enterprise_wide_knowledge_management_capability_development_agent import (
            DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgentConfig
        )
        return DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "12.0",
            "apqc_process_id": "12.0.6",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self):
        """Return expected capabilities."""
        return ["knowledge_management", "knowledge_capture", "knowledge_sharing", "learning"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for knowledge management."""
        return {
            "task_type": "manage_knowledge",
            "data": {
                "knowledge_program": {
                    "name": "Enterprise_Knowledge_Management",
                    "scope": "global",
                    "maturity": "level_3",
                    "participants": 10000
                },
                "knowledge_repositories": [
                    {
                        "name": "Technical_Documentation",
                        "type": "document_management",
                        "documents": 50000,
                        "usage_rate": 0.75
                    },
                    {
                        "name": "Lessons_Learned",
                        "type": "case_studies",
                        "entries": 2000,
                        "contribution_rate": 0.40
                    },
                    {
                        "name": "Expert_Directory",
                        "type": "people_finder",
                        "experts": 500,
                        "consultation_requests": 1000
                    }
                ],
                "knowledge_processes": {
                    "capture": {
                        "methods": ["documentation", "interviews", "workshops"],
                        "frequency": "continuous"
                    },
                    "storage": {
                        "systems": ["wiki", "sharepoint", "learning_management_system"],
                        "organization": "taxonomy_based"
                    },
                    "sharing": {
                        "channels": ["communities_of_practice", "training", "mentoring"],
                        "effectiveness": 0.70
                    },
                    "application": {
                        "reuse_rate": 0.60,
                        "time_savings": "20_percent",
                        "quality_improvement": "15_percent"
                    }
                },
                "knowledge_metrics": {
                    "knowledge_assets": 55000,
                    "active_contributors": 3000,
                    "monthly_searches": 100000,
                    "knowledge_reuse": 0.65,
                    "satisfaction_score": 4.0
                }
            },
            "context": {
                "priority": "high",
                "knowledge_culture": "developing"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_knowledge_capture(self):
        """Test knowledge capture and documentation processes."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "capture_knowledge"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_knowledge_sharing(self):
        """Test knowledge sharing and collaboration."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "facilitate_sharing",
            "data": {
                "community": "Engineering_Community",
                "topic": "Cloud_Architecture",
                "participants": 200
            },
            "priority": "medium"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_13
@pytest.mark.apqc_integration
class TestCategory13Integration:
    """
    Integration tests for Category 13.0 - Business Capabilities agents.

    Tests complete project lifecycle and capability development workflows.
    """

    @pytest.mark.asyncio
    async def test_complete_project_lifecycle(self):
        """
        Test complete project lifecycle from initiation to execution.

        Workflow:
        1. Initiate project (InitiateProjectsCapabilityDevelopmentAgent)
        2. Add to portfolio (ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent)
        3. Execute project (ExecuteProjectsCapabilityDevelopmentAgent)
        4. Manage change (ManageChangeCapabilityDevelopmentAgent)
        5. Capture knowledge (DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent)
        """
        # Import agents
        from superstandard.agents.infrastructure.initiate_projects_capability_development_agent import (
            InitiateProjectsCapabilityDevelopmentAgent,
            InitiateProjectsCapabilityDevelopmentAgentConfig
        )
        from superstandard.agents.trading.manage_portfolio_of_enterprise_programs_projects_capability_development_agent import (
            ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent,
            ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgentConfig
        )
        from superstandard.agents.infrastructure.execute_projects_capability_development_agent import (
            ExecuteProjectsCapabilityDevelopmentAgent,
            ExecuteProjectsCapabilityDevelopmentAgentConfig
        )
        from superstandard.agents.infrastructure.manage_change_capability_development_agent import (
            ManageChangeCapabilityDevelopmentAgent,
            ManageChangeCapabilityDevelopmentAgentConfig
        )
        from superstandard.agents.infrastructure.develop_manage_enterprise_wide_knowledge_management_capability_development_agent import (
            DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent,
            DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgentConfig
        )

        # Create agent instances
        initiate_agent = InitiateProjectsCapabilityDevelopmentAgent(
            InitiateProjectsCapabilityDevelopmentAgentConfig()
        )
        portfolio_agent = ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgent(
            ManagePortfolioOfEnterpriseProgramsProjectsCapabilityDevelopmentAgentConfig()
        )
        execute_agent = ExecuteProjectsCapabilityDevelopmentAgent(
            ExecuteProjectsCapabilityDevelopmentAgentConfig()
        )
        change_agent = ManageChangeCapabilityDevelopmentAgent(
            ManageChangeCapabilityDevelopmentAgentConfig()
        )
        knowledge_agent = DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent(
            DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgentConfig()
        )

        # Step 1: Initiate project
        initiate_input = {
            "task_type": "initiate_project",
            "data": {
                "project": {
                    "name": "CRM_Modernization",
                    "budget": 2000000,
                    "duration_months": 12
                },
                "business_case": {
                    "objectives": ["improve_customer_satisfaction"],
                    "benefits": {"revenue_increase": 500000}
                }
            },
            "priority": "high"
        }
        initiate_result = await initiate_agent.execute(initiate_input)
        assert initiate_result['status'] in ['completed', 'degraded']

        # Step 2: Add to portfolio
        portfolio_input = {
            "task_type": "add_to_portfolio",
            "data": {
                "project": initiate_result.get('output', {}),
                "portfolio_id": "PORTFOLIO-2025"
            },
            "priority": "high"
        }
        portfolio_result = await portfolio_agent.execute(portfolio_input)
        assert portfolio_result['status'] in ['completed', 'degraded']

        # Step 3: Execute project tasks
        execute_input = {
            "task_type": "execute_project",
            "data": {
                "project_tasks": [
                    {"id": "T1", "name": "Planning", "duration_days": 30},
                    {"id": "T2", "name": "Execution", "duration_days": 180}
                ],
                "resources": [{"id": "R1", "role": "pm", "availability": 1.0}]
            },
            "priority": "high"
        }
        execute_result = await execute_agent.execute(execute_input)
        assert execute_result['status'] in ['completed', 'degraded']

        # Step 4: Manage organizational change
        change_input = {
            "task_type": "manage_change",
            "data": {
                "change_initiative": {
                    "name": "CRM_Adoption",
                    "affected_employees": 500
                },
                "change_strategy": {
                    "communication_plan": {"frequency": "weekly"},
                    "training_plan": {"modules": 5}
                }
            },
            "priority": "high"
        }
        change_result = await change_agent.execute(change_input)
        assert change_result['status'] in ['completed', 'degraded']

        # Step 5: Capture project knowledge
        knowledge_input = {
            "task_type": "capture_knowledge",
            "data": {
                "project_name": "CRM_Modernization",
                "lessons_learned": execute_result.get('output', {}),
                "best_practices": change_result.get('output', {})
            },
            "priority": "medium"
        }
        knowledge_result = await knowledge_agent.execute(knowledge_input)
        assert knowledge_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_process_improvement_workflow(self):
        """Test integrated process improvement workflow."""
        from superstandard.agents.business.manage_business_processes_capability_development_agent import (
            ManageBusinessProcessesCapabilityDevelopmentAgent,
            ManageBusinessProcessesCapabilityDevelopmentAgentConfig
        )
        from superstandard.agents.testing.manage_enterprise_quality_capability_development_agent import (
            ManageEnterpriseQualityCapabilityDevelopmentAgent,
            ManageEnterpriseQualityCapabilityDevelopmentAgentConfig
        )

        process_agent = ManageBusinessProcessesCapabilityDevelopmentAgent(
            ManageBusinessProcessesCapabilityDevelopmentAgentConfig()
        )
        quality_agent = ManageEnterpriseQualityCapabilityDevelopmentAgent(
            ManageEnterpriseQualityCapabilityDevelopmentAgentConfig()
        )

        # Identify process improvement opportunity
        process_input = {
            "task_type": "analyze_process",
            "data": {
                "process": {"name": "Order_Fulfillment"},
                "current_state": {"cycle_time_days": 10, "error_rate": 0.05}
            },
            "priority": "high"
        }
        process_result = await process_agent.execute(process_input)
        assert process_result['status'] in ['completed', 'degraded']

        # Apply quality management
        quality_input = {
            "task_type": "improve_quality",
            "data": {
                "process": "Order_Fulfillment",
                "improvement_target": {"error_rate": 0.02}
            },
            "priority": "high"
        }
        quality_result = await quality_agent.execute(quality_input)
        assert quality_result['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_13
class TestCategory13Capabilities:
    """
    Test category-specific capabilities for Business Capabilities agents.
    """

    @pytest.mark.asyncio
    async def test_capability_development_type(self):
        """Verify agents have capability_development type."""
        from superstandard.agents.business.manage_business_processes_capability_development_agent import (
            ManageBusinessProcessesCapabilityDevelopmentAgent,
            ManageBusinessProcessesCapabilityDevelopmentAgentConfig
        )

        agent = ManageBusinessProcessesCapabilityDevelopmentAgent(
            ManageBusinessProcessesCapabilityDevelopmentAgentConfig()
        )

        # Should have capability_development type
        assert agent.config.agent_type == 'capability_development'

    @pytest.mark.asyncio
    async def test_continuous_improvement_focus(self):
        """Test continuous improvement capabilities."""
        from superstandard.agents.testing.manage_enterprise_quality_capability_development_agent import (
            ManageEnterpriseQualityCapabilityDevelopmentAgent,
            ManageEnterpriseQualityCapabilityDevelopmentAgentConfig
        )

        agent = ManageEnterpriseQualityCapabilityDevelopmentAgent(
            ManageEnterpriseQualityCapabilityDevelopmentAgentConfig()
        )

        improvement_input = {
            "task_type": "continuous_improvement",
            "data": {
                "improvement_area": "process_efficiency",
                "current_performance": 0.75,
                "target_performance": 0.90
            },
            "priority": "medium"
        }

        result = await agent.execute(improvement_input)
        assert result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
