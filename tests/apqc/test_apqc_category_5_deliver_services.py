"""
APQC Category 5.0 - Deliver Services Agent Tests

Comprehensive tests for all 6 Deliver Services agents from APQC Category 5.0.

Agents tested:
1. PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent (5.1)
2. DevelopManageServiceDeliveryServiceDeliveryAgent (5.2)
3. DesignServiceDeliveryProcessServiceAgent
4. ManageServiceLevelAgreementsServiceAgent (5.3)
5. DeliverServiceToCustomerOperationalAgent (5.4)
6. DeliverServiceToCustomerServiceDeliveryAgent (5.4)

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Service delivery workflow integration tests
- SLA management and compliance workflows
- Customer service delivery workflows
- Cross-agent collaboration within category

Version: 1.0.0
Framework: APQC 7.0.1
Category: 5.0 - Deliver Services
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 5.0 Agent Tests - Service Delivery Planning (5.1)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestPlanForAlignServiceDeliveryResourcesServiceDeliveryAgent(APQCAgentTestCase):
    """
    Tests for PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent (APQC 5.1)

    Agent: Plan for and align service delivery resources
    Path: src/superstandard/agents/api/plan_for_align_service_delivery_resources_service_delivery_agent.py
    Domain: service_delivery | Type: service_delivery
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.plan_for_align_service_delivery_resources_service_delivery_agent import (
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent
        )
        return PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.plan_for_align_service_delivery_resources_service_delivery_agent import (
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig
        )
        return PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_process_id": "5.1",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "analysis",
            "planning",
            "resource_management",
            "service_delivery"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for service delivery resource planning."""
        return {
            "task_type": "plan_service_resources",
            "data": {
                "service_catalog": [
                    {
                        "service_id": "SVC-001",
                        "service_name": "Technical Support",
                        "estimated_volume": 1000,  # requests per month
                        "avg_resolution_time": 2.5  # hours
                    },
                    {
                        "service_id": "SVC-002",
                        "service_name": "Implementation",
                        "estimated_volume": 50,  # projects per quarter
                        "avg_duration": 160  # hours
                    }
                ],
                "current_resources": {
                    "support_staff": 20,
                    "consultants": 10,
                    "tools": ["ticketing_system", "knowledge_base", "remote_access"]
                },
                "capacity_target": 0.80,  # 80% utilization
                "service_level_targets": {
                    "response_time": "2_hours",
                    "resolution_time": "24_hours",
                    "customer_satisfaction": 0.90
                },
                "constraints": ["budget", "hiring_time", "training_time"]
            },
            "context": {
                "planning_horizon": "6_months",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_service_resource_planning(self):
        """Test service delivery resource planning workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "capacity_planning",
            "data": {
                "demand_forecast": {
                    "Q1": 2000,
                    "Q2": 2500,
                    "Q3": 2800,
                    "Q4": 3000
                },
                "current_capacity": 2200,
                "growth_strategy": "organic",
                "investment_budget": 500000
            },
            "context": {
                "service_type": "professional_services",
                "priority": "high"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result
        assert result['apqc_process_id'] == '5.1'

    @pytest.mark.asyncio
    async def test_resource_alignment(self):
        """Test alignment of service resources with business objectives."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "align_resources",
            "data": {
                "business_objectives": [
                    "improve_customer_satisfaction",
                    "reduce_service_costs",
                    "increase_service_capacity"
                ],
                "current_allocation": {
                    "tier_1_support": 0.40,
                    "tier_2_support": 0.30,
                    "professional_services": 0.30
                },
                "optimization_criteria": ["cost_effectiveness", "quality", "scalability"]
            },
            "priority": "medium"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category 5.0 Agent Tests - Service Development (5.2)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestDevelopManageServiceDeliveryServiceDeliveryAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageServiceDeliveryServiceDeliveryAgent (APQC 5.2)

    Agent: Develop and manage service delivery
    Path: src/superstandard/agents/api/develop_manage_service_delivery_service_delivery_agent.py
    Domain: service_delivery | Type: service_delivery
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.develop_manage_service_delivery_service_delivery_agent import (
            DevelopManageServiceDeliveryServiceDeliveryAgent
        )
        return DevelopManageServiceDeliveryServiceDeliveryAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.develop_manage_service_delivery_service_delivery_agent import (
            DevelopManageServiceDeliveryServiceDeliveryAgentConfig
        )
        return DevelopManageServiceDeliveryServiceDeliveryAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_process_id": "5.2",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "service_design",
            "process_management",
            "quality_management",
            "continuous_improvement"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for service delivery development."""
        return {
            "task_type": "develop_service_delivery",
            "data": {
                "service_definition": {
                    "service_name": "Cloud Migration Service",
                    "service_type": "professional_services",
                    "target_customers": ["enterprise", "mid_market"],
                    "delivery_model": "project_based"
                },
                "service_components": [
                    "assessment",
                    "planning",
                    "migration",
                    "validation",
                    "optimization"
                ],
                "delivery_standards": {
                    "methodology": "agile",
                    "quality_gates": ["design_review", "testing", "acceptance"],
                    "documentation_required": True
                },
                "pricing_model": "time_and_materials",
                "expected_margins": 0.30
            },
            "context": {
                "market_segment": "technology_services",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_service_delivery_development(self):
        """Test service delivery development workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "design_service",
            "data": {
                "service_concept": {
                    "name": "Managed Security Service",
                    "value_proposition": "24/7 security monitoring and response"
                },
                "customer_requirements": [
                    "continuous_monitoring",
                    "incident_response",
                    "compliance_reporting"
                ],
                "resource_requirements": {
                    "technology": ["SIEM", "IDS/IPS", "SOAR"],
                    "personnel": ["security_analysts", "incident_responders"],
                    "certifications": ["ISO27001", "SOC2"]
                }
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestDesignServiceDeliveryProcessServiceAgent(APQCAgentTestCase):
    """
    Tests for DesignServiceDeliveryProcessServiceAgent

    Agent: Design service delivery process
    Path: src/superstandard/agents/api/design_service_delivery_process_service_agent.py
    Domain: service | Type: service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.design_service_delivery_process_service_agent import (
            DesignServiceDeliveryProcessServiceAgent
        )
        return DesignServiceDeliveryProcessServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.design_service_delivery_process_service_agent import (
            DesignServiceDeliveryProcessServiceAgentConfig
        )
        return DesignServiceDeliveryProcessServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "process_design",
            "workflow_optimization",
            "service_design",
            "quality_assurance"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for service process design."""
        return {
            "task_type": "design_service_process",
            "data": {
                "service_type": "customer_onboarding",
                "process_steps": [
                    {
                        "step": "initial_contact",
                        "owner": "sales",
                        "duration": 1,  # hours
                        "inputs": ["customer_inquiry"],
                        "outputs": ["qualified_lead"]
                    },
                    {
                        "step": "needs_assessment",
                        "owner": "solutions_architect",
                        "duration": 4,
                        "inputs": ["qualified_lead"],
                        "outputs": ["requirements_document"]
                    },
                    {
                        "step": "solution_design",
                        "owner": "technical_team",
                        "duration": 16,
                        "inputs": ["requirements_document"],
                        "outputs": ["solution_blueprint"]
                    }
                ],
                "quality_criteria": {
                    "customer_satisfaction": 0.90,
                    "time_to_value": "30_days",
                    "defect_rate": 0.05
                },
                "automation_opportunities": ["data_entry", "document_generation", "status_updates"]
            },
            "context": {
                "improvement_goal": "reduce_cycle_time",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @pytest.mark.asyncio
    async def test_process_design_optimization(self):
        """Test service process design and optimization."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "optimize_process",
            "data": {
                "current_process": {
                    "steps": 10,
                    "avg_cycle_time": 120,  # hours
                    "automation_level": 0.20
                },
                "improvement_targets": {
                    "cycle_time_reduction": 0.30,
                    "cost_reduction": 0.20,
                    "quality_improvement": 0.10
                },
                "constraints": ["technology_budget", "change_management"]
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category 5.0 Agent Tests - SLA Management (5.3)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestManageServiceLevelAgreementsServiceAgent(APQCAgentTestCase):
    """
    Tests for ManageServiceLevelAgreementsServiceAgent (APQC 5.3)

    Agent: Manage service level agreements
    Path: src/superstandard/agents/api/manage_service_level_agreements_service_agent.py
    Domain: service | Type: service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgent
        )
        return ManageServiceLevelAgreementsServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgentConfig
        )
        return ManageServiceLevelAgreementsServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_process_id": "5.3",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "sla_management",
            "performance_monitoring",
            "compliance_tracking",
            "reporting"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for SLA management."""
        return {
            "task_type": "manage_sla",
            "data": {
                "sla": {
                    "id": "SLA-2025-001",
                    "customer_id": "CUST-12345",
                    "service_type": "managed_services",
                    "effective_date": datetime.now().isoformat(),
                    "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
                    "metrics": [
                        {
                            "metric": "availability",
                            "target": 0.999,
                            "measurement": "uptime_percentage",
                            "penalty": "credit_5_percent"
                        },
                        {
                            "metric": "response_time",
                            "target": 15,  # minutes
                            "measurement": "p95_latency",
                            "penalty": "credit_2_percent"
                        },
                        {
                            "metric": "resolution_time",
                            "target": 4,  # hours
                            "measurement": "average",
                            "penalty": "credit_3_percent"
                        }
                    ]
                },
                "performance_data": {
                    "period": "2025-01",
                    "availability": 0.9995,
                    "avg_response_time": 12,
                    "avg_resolution_time": 3.5
                },
                "action": "compliance_check"
            },
            "context": {
                "review_period": "monthly",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_sla_compliance_monitoring(self):
        """Test SLA compliance monitoring and reporting."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "monitor_compliance",
            "data": {
                "sla_id": "SLA-001",
                "metrics": [
                    {"name": "uptime", "target": 0.99, "actual": 0.995},
                    {"name": "response_time", "target": 30, "actual": 25},
                    {"name": "customer_satisfaction", "target": 0.90, "actual": 0.92}
                ],
                "reporting_period": "Q1_2025"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_sla_violation_handling(self):
        """Test SLA violation detection and handling."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "handle_violation",
            "data": {
                "sla_id": "SLA-001",
                "violation": {
                    "metric": "availability",
                    "target": 0.999,
                    "actual": 0.985,
                    "timestamp": datetime.now().isoformat()
                },
                "impact_assessment": {
                    "customers_affected": 150,
                    "downtime_minutes": 720,
                    "financial_impact": 50000
                },
                "remediation_plan": "required"
            },
            "priority": "critical"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category 5.0 Agent Tests - Service Delivery (5.4)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestDeliverServiceToCustomerOperationalAgent(APQCAgentTestCase):
    """
    Tests for DeliverServiceToCustomerOperationalAgent (APQC 5.4)

    Agent: Deliver service to customer (operational)
    Path: src/superstandard/agents/api/deliver_service_to_customer_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.deliver_service_to_customer_operational_agent import (
            DeliverServiceToCustomerOperationalAgent
        )
        return DeliverServiceToCustomerOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.deliver_service_to_customer_operational_agent import (
            DeliverServiceToCustomerOperationalAgentConfig
        )
        return DeliverServiceToCustomerOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_process_id": "5.4",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "service_delivery",
            "customer_engagement",
            "quality_assurance",
            "issue_resolution"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for service delivery."""
        return MockDataGenerator.generate_service_input()

    @pytest.mark.asyncio
    async def test_service_delivery_execution(self):
        """Test service delivery execution workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "deliver_service",
            "data": {
                "service_request": {
                    "id": "SR-2025-001",
                    "customer_id": "CUST-12345",
                    "service_type": "technical_support",
                    "priority": "high",
                    "description": "System integration issue"
                },
                "assigned_resources": {
                    "engineer": "ENG-001",
                    "tools": ["remote_access", "diagnostic_tools"]
                },
                "sla_requirements": {
                    "response_time": "2_hours",
                    "resolution_time": "24_hours"
                },
                "customer_expectations": {
                    "communication_frequency": "hourly_updates",
                    "resolution_quality": "high"
                }
            },
            "context": {
                "channel": "phone",
                "priority": "high"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestDeliverServiceToCustomerServiceDeliveryAgent(APQCAgentTestCase):
    """
    Tests for DeliverServiceToCustomerServiceDeliveryAgent (APQC 5.4)

    Agent: Deliver service to customer (service delivery)
    Path: src/superstandard/agents/api/deliver_service_to_customer_service_delivery_agent.py
    Domain: service_delivery | Type: service_delivery
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgent
        )
        return DeliverServiceToCustomerServiceDeliveryAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgentConfig
        )
        return DeliverServiceToCustomerServiceDeliveryAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "5.0",
            "apqc_process_id": "5.4",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "service_delivery",
            "project_management",
            "quality_control",
            "customer_satisfaction"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for service delivery."""
        return {
            "task_type": "deliver_professional_service",
            "data": {
                "project": {
                    "id": "PROJ-2025-001",
                    "customer_id": "CUST-12345",
                    "service_type": "implementation",
                    "scope": "ERP system implementation",
                    "timeline": {
                        "start": datetime.now().isoformat(),
                        "end": (datetime.now() + timedelta(days=180)).isoformat()
                    },
                    "budget": 500000
                },
                "deliverables": [
                    "requirements_document",
                    "system_design",
                    "implementation",
                    "testing",
                    "training",
                    "go_live_support"
                ],
                "team": {
                    "project_manager": "PM-001",
                    "consultants": ["CONS-001", "CONS-002", "CONS-003"],
                    "technical_specialists": ["TECH-001", "TECH-002"]
                },
                "quality_gates": ["design_review", "UAT", "production_readiness"],
                "success_criteria": {
                    "on_time": True,
                    "within_budget": True,
                    "quality_standards_met": True,
                    "customer_satisfaction": 0.90
                }
            },
            "context": {
                "delivery_model": "agile",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_professional_services_delivery(self):
        """Test professional services delivery workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "execute_project",
            "data": {
                "project_phase": "implementation",
                "activities": [
                    "configure_system",
                    "migrate_data",
                    "integrate_systems",
                    "test_functionality"
                ],
                "resources_allocated": True,
                "risks": ["timeline_pressure", "resource_availability"]
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category 5.0 Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
@pytest.mark.apqc_integration
class TestCategory5Integration:
    """
    Integration tests for Category 5.0 - Deliver Services agents.

    Tests end-to-end service delivery workflows and cross-agent collaboration.
    """

    @pytest.mark.asyncio
    async def test_end_to_end_service_delivery_workflow(self):
        """
        Test complete service delivery workflow from planning to execution.

        Workflow:
        1. Plan service delivery resources (PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent)
        2. Design service process (DesignServiceDeliveryProcessServiceAgent)
        3. Establish SLA (ManageServiceLevelAgreementsServiceAgent)
        4. Deliver service (DeliverServiceToCustomerServiceDeliveryAgent)
        """
        # Import agents
        from superstandard.agents.api.plan_for_align_service_delivery_resources_service_delivery_agent import (
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent,
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig
        )
        from superstandard.agents.api.design_service_delivery_process_service_agent import (
            DesignServiceDeliveryProcessServiceAgent,
            DesignServiceDeliveryProcessServiceAgentConfig
        )
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgent,
            ManageServiceLevelAgreementsServiceAgentConfig
        )
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgent,
            DeliverServiceToCustomerServiceDeliveryAgentConfig
        )

        # Create agent instances
        planning_agent = PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent(
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig()
        )
        design_agent = DesignServiceDeliveryProcessServiceAgent(
            DesignServiceDeliveryProcessServiceAgentConfig()
        )
        sla_agent = ManageServiceLevelAgreementsServiceAgent(
            ManageServiceLevelAgreementsServiceAgentConfig()
        )
        delivery_agent = DeliverServiceToCustomerServiceDeliveryAgent(
            DeliverServiceToCustomerServiceDeliveryAgentConfig()
        )

        # Step 1: Plan service delivery resources
        planning_input = {
            "task_type": "plan_service_resources",
            "data": {
                "service_catalog": [
                    {"service_id": "SVC-001", "estimated_volume": 100}
                ],
                "capacity_target": 0.80
            },
            "priority": "high"
        }
        planning_result = await planning_agent.execute(planning_input)
        assert planning_result['status'] in ['completed', 'degraded']

        # Step 2: Design service delivery process
        design_input = {
            "task_type": "design_service_process",
            "data": {
                "service_type": "consulting",
                "process_steps": [
                    {"step": "discovery", "duration": 8},
                    {"step": "design", "duration": 40},
                    {"step": "implementation", "duration": 80}
                ]
            },
            "priority": "high"
        }
        design_result = await design_agent.execute(design_input)
        assert design_result['status'] in ['completed', 'degraded']

        # Step 3: Establish SLA
        sla_input = {
            "task_type": "create_sla",
            "data": {
                "customer_id": "CUST-001",
                "service_type": "consulting",
                "metrics": [
                    {"metric": "response_time", "target": 24}
                ]
            },
            "priority": "high"
        }
        sla_result = await sla_agent.execute(sla_input)
        assert sla_result['status'] in ['completed', 'degraded']

        # Step 4: Deliver service
        delivery_input = {
            "task_type": "deliver_professional_service",
            "data": {
                "project": {
                    "id": "PROJ-001",
                    "customer_id": "CUST-001",
                    "service_type": "consulting"
                },
                "sla": sla_result.get('output', {})
            },
            "priority": "high"
        }
        delivery_result = await delivery_agent.execute(delivery_input)
        assert delivery_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_sla_driven_service_delivery(self):
        """
        Test SLA-driven service delivery workflow.
        """
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgent,
            ManageServiceLevelAgreementsServiceAgentConfig
        )
        from superstandard.agents.api.deliver_service_to_customer_operational_agent import (
            DeliverServiceToCustomerOperationalAgent,
            DeliverServiceToCustomerOperationalAgentConfig
        )

        sla_agent = ManageServiceLevelAgreementsServiceAgent(
            ManageServiceLevelAgreementsServiceAgentConfig()
        )
        delivery_agent = DeliverServiceToCustomerOperationalAgent(
            DeliverServiceToCustomerOperationalAgentConfig()
        )

        # Define SLA
        sla_input = {
            "task_type": "manage_sla",
            "data": {
                "sla": {
                    "id": "SLA-001",
                    "metrics": [
                        {"metric": "response_time", "target": 2},  # hours
                        {"metric": "resolution_time", "target": 24}  # hours
                    ]
                }
            },
            "priority": "high"
        }
        sla_result = await sla_agent.execute(sla_input)

        # Deliver service within SLA
        delivery_input = {
            "task_type": "deliver_service",
            "data": {
                "service_request": {
                    "id": "SR-001",
                    "priority": "high"
                },
                "sla_requirements": sla_result.get('output', {})
            },
            "priority": "high"
        }
        delivery_result = await delivery_agent.execute(delivery_input)

        assert delivery_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_service_development_to_delivery(self):
        """
        Test workflow from service development to delivery.
        """
        from superstandard.agents.api.develop_manage_service_delivery_service_delivery_agent import (
            DevelopManageServiceDeliveryServiceDeliveryAgent,
            DevelopManageServiceDeliveryServiceDeliveryAgentConfig
        )
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgent,
            DeliverServiceToCustomerServiceDeliveryAgentConfig
        )

        development_agent = DevelopManageServiceDeliveryServiceDeliveryAgent(
            DevelopManageServiceDeliveryServiceDeliveryAgentConfig()
        )
        delivery_agent = DeliverServiceToCustomerServiceDeliveryAgent(
            DeliverServiceToCustomerServiceDeliveryAgentConfig()
        )

        # Develop service
        development_input = {
            "task_type": "develop_service_delivery",
            "data": {
                "service_definition": {
                    "service_name": "Premium Support",
                    "service_type": "managed_services"
                },
                "delivery_standards": {
                    "methodology": "ITIL",
                    "quality_gates": ["validation", "approval"]
                }
            },
            "priority": "high"
        }
        development_result = await development_agent.execute(development_input)

        # Deliver developed service
        delivery_input = {
            "task_type": "deliver_professional_service",
            "data": {
                "project": {
                    "id": "PROJ-001",
                    "service_type": "managed_services"
                },
                "service_definition": development_result.get('output', {})
            },
            "priority": "high"
        }
        delivery_result = await delivery_agent.execute(delivery_input)

        assert delivery_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_resource_planning_to_delivery(self):
        """
        Test integration from resource planning to service delivery.
        """
        from superstandard.agents.api.plan_for_align_service_delivery_resources_service_delivery_agent import (
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent,
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig
        )
        from superstandard.agents.api.deliver_service_to_customer_operational_agent import (
            DeliverServiceToCustomerOperationalAgent,
            DeliverServiceToCustomerOperationalAgentConfig
        )

        planning_agent = PlanForAlignServiceDeliveryResourcesServiceDeliveryAgent(
            PlanForAlignServiceDeliveryResourcesServiceDeliveryAgentConfig()
        )
        delivery_agent = DeliverServiceToCustomerOperationalAgent(
            DeliverServiceToCustomerOperationalAgentConfig()
        )

        # Plan resources
        planning_input = {
            "task_type": "plan_service_resources",
            "data": {
                "service_catalog": [
                    {"service_id": "SVC-001", "estimated_volume": 50}
                ],
                "current_resources": {"support_staff": 10}
            },
            "priority": "high"
        }
        planning_result = await planning_agent.execute(planning_input)

        # Deliver service with planned resources
        delivery_input = {
            "task_type": "deliver_service",
            "data": {
                "service_request": {"id": "SR-001"},
                "resource_allocation": planning_result.get('output', {})
            },
            "priority": "high"
        }
        delivery_result = await delivery_agent.execute(delivery_input)

        assert delivery_result['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
class TestCategory5Capabilities:
    """
    Test category-specific capabilities for Deliver Services agents.
    """

    @pytest.mark.asyncio
    async def test_service_agents_have_required_capabilities(self):
        """Verify all service agents have required service capabilities."""
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgent,
            DeliverServiceToCustomerServiceDeliveryAgentConfig
        )

        agent = DeliverServiceToCustomerServiceDeliveryAgent(
            DeliverServiceToCustomerServiceDeliveryAgentConfig()
        )

        required_capabilities = [
            "analysis",
            "execution"
        ]

        for capability in required_capabilities:
            assert capability in agent.capabilities_list, \
                f"Service agent should have {capability} capability"

    @pytest.mark.asyncio
    async def test_sla_management_capabilities(self):
        """Verify SLA management agents support compliance workflows."""
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgent,
            ManageServiceLevelAgreementsServiceAgentConfig
        )

        agent = ManageServiceLevelAgreementsServiceAgent(
            ManageServiceLevelAgreementsServiceAgentConfig()
        )

        # Test SLA monitoring capabilities
        sla_input = {
            "task_type": "monitor_sla",
            "data": {
                "sla_id": "SLA-001",
                "metrics": [
                    {"name": "uptime", "target": 0.99, "actual": 0.995}
                ]
            },
            "priority": "medium"
        }

        result = await agent.execute(sla_input)
        assert result is not None
        assert 'status' in result

    @pytest.mark.asyncio
    async def test_service_quality_assurance(self):
        """Test service quality assurance capabilities."""
        from superstandard.agents.api.deliver_service_to_customer_service_delivery_agent import (
            DeliverServiceToCustomerServiceDeliveryAgent,
            DeliverServiceToCustomerServiceDeliveryAgentConfig
        )

        agent = DeliverServiceToCustomerServiceDeliveryAgent(
            DeliverServiceToCustomerServiceDeliveryAgentConfig()
        )

        # Test quality assurance workflow
        qa_input = {
            "task_type": "quality_check",
            "data": {
                "deliverable": "implementation",
                "quality_criteria": {
                    "functionality": "complete",
                    "performance": "meets_requirements",
                    "security": "validated"
                }
            },
            "priority": "high"
        }

        result = await agent.execute(qa_input)
        assert result is not None


# ========================================================================
# Performance and Scale Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_5
@pytest.mark.slow
class TestCategory5Performance:
    """
    Performance tests for Category 5 agents.
    """

    @pytest.mark.asyncio
    async def test_concurrent_service_delivery(self):
        """Test multiple service delivery agents executing concurrently."""
        import asyncio
        from superstandard.agents.api.deliver_service_to_customer_operational_agent import (
            DeliverServiceToCustomerOperationalAgent,
            DeliverServiceToCustomerOperationalAgentConfig
        )

        # Create multiple agent instances
        agents = [
            DeliverServiceToCustomerOperationalAgent(
                DeliverServiceToCustomerOperationalAgentConfig()
            )
            for _ in range(3)
        ]

        # Execute concurrently
        input_data = MockDataGenerator.generate_service_input()
        tasks = [agent.execute(input_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        # Verify all completed
        assert len(results) == 3
        for result in results:
            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_sla_monitoring_performance(self):
        """Test SLA monitoring performance at scale."""
        from superstandard.agents.api.manage_service_level_agreements_service_agent import (
            ManageServiceLevelAgreementsServiceAgent,
            ManageServiceLevelAgreementsServiceAgentConfig
        )

        agent = ManageServiceLevelAgreementsServiceAgent(
            ManageServiceLevelAgreementsServiceAgentConfig()
        )

        # Monitor multiple SLAs
        import asyncio
        tasks = []
        for i in range(10):
            sla_input = {
                "task_type": "monitor_compliance",
                "data": {
                    "sla_id": f"SLA-{i:03d}",
                    "metrics": [
                        {"name": "uptime", "target": 0.99, "actual": 0.995}
                    ]
                },
                "priority": "medium"
            }
            tasks.append(agent.execute(sla_input))

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Utility Functions
# ========================================================================

def create_category_5_test_suite():
    """
    Create a complete test suite for Category 5 agents.

    Returns:
        List of test classes
    """
    return [
        TestPlanForAlignServiceDeliveryResourcesServiceDeliveryAgent,
        TestDevelopManageServiceDeliveryServiceDeliveryAgent,
        TestDesignServiceDeliveryProcessServiceAgent,
        TestManageServiceLevelAgreementsServiceAgent,
        TestDeliverServiceToCustomerOperationalAgent,
        TestDeliverServiceToCustomerServiceDeliveryAgent,
        TestCategory5Integration,
        TestCategory5Capabilities,
        TestCategory5Performance
    ]


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
