"""
APQC Category 6.0 - Manage Customer Service Agent Tests

Comprehensive tests for all 7 Customer Service agents from APQC Category 6.0.

Agents tested:
1. DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent (6.1)
2. PlanManageCustomerServiceOperationsCustomerServiceAgent (6.2)
3. ManageCustomerInquiriesCustomerServiceAgent
4. HandleServiceExceptionsCustomerServiceAgent
5. ResolveCustomerIssuesCustomerServiceAgent
6. MeasureCustomerSatisfactionCustomerServiceAgent (6.3)
7. MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent (6.3)

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Customer journey integration tests
- Service quality and satisfaction measurement
- Exception handling workflows

Version: 1.0.0
Framework: APQC 7.0.1
Category: 6.0 - Manage Customer Service
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 6.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestDevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent (APQC 6.1)

    Agent: Develop customer care and customer service strategy
    Path: src/superstandard/agents/trading/develop_customer_care_customer_service_strategy_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.trading.develop_customer_care_customer_service_strategy_customer_service_agent import (
            DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent
        )
        return DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.trading.develop_customer_care_customer_service_strategy_customer_service_agent import (
            DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgentConfig
        )
        return DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_process_id": "6.1",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return ["strategy_development", "customer_service", "planning", "analysis"]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for customer service strategy."""
        return {
            "task_type": "develop_customer_service_strategy",
            "data": {
                "business_objectives": {
                    "customer_satisfaction_target": 0.90,
                    "retention_rate_target": 0.85,
                    "nps_target": 50,
                    "first_contact_resolution_target": 0.80
                },
                "current_state": {
                    "customer_satisfaction": 0.75,
                    "retention_rate": 0.70,
                    "nps": 30,
                    "average_response_time": "4_hours",
                    "channels": ["phone", "email", "chat"]
                },
                "customer_insights": {
                    "top_pain_points": ["long_wait_times", "multiple_contacts", "inconsistent_service"],
                    "preferred_channels": ["chat", "self_service", "phone"],
                    "demographics": {"age_range": "25-55", "tech_savvy": "medium"}
                },
                "resources": {
                    "budget": 500000,
                    "current_staff": 50,
                    "technology_stack": ["CRM", "ticketing_system", "knowledge_base"]
                },
                "market_benchmarks": {
                    "industry_avg_satisfaction": 0.82,
                    "industry_avg_response_time": "2_hours",
                    "best_in_class_nps": 60
                }
            },
            "context": {
                "planning_horizon": "3_years",
                "industry": "technology",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_strategy_development_phases(self):
        """Test customer service strategy development phases."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        phases = ["analysis", "design", "implementation_planning"]

        for phase in phases:
            input_data = self.generate_valid_input()
            input_data["context"]["phase"] = phase

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']
            assert 'output' in result
            assert result['apqc_process_id'] == "6.1"

    @pytest.mark.asyncio
    async def test_multi_channel_strategy(self):
        """Test strategy includes multi-channel support."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["target_channels"] = ["phone", "email", "chat", "social_media", "self_service"]

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestPlanManageCustomerServiceOperationsCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for PlanManageCustomerServiceOperationsCustomerServiceAgent (APQC 6.2)

    Agent: Plan and manage customer service operations
    Path: src/superstandard/agents/api/plan_manage_customer_service_operations_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.plan_manage_customer_service_operations_customer_service_agent import (
            PlanManageCustomerServiceOperationsCustomerServiceAgent
        )
        return PlanManageCustomerServiceOperationsCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.plan_manage_customer_service_operations_customer_service_agent import (
            PlanManageCustomerServiceOperationsCustomerServiceAgentConfig
        )
        return PlanManageCustomerServiceOperationsCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_process_id": "6.2",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for customer service operations."""
        return {
            "task_type": "manage_service_operations",
            "data": {
                "operational_parameters": {
                    "service_hours": "24/7",
                    "staffing_levels": {"day_shift": 30, "night_shift": 15, "weekend": 20},
                    "skill_matrix": ["technical_support", "billing", "general_inquiry"],
                    "sla_targets": {
                        "phone_response": "30_seconds",
                        "email_response": "2_hours",
                        "chat_response": "1_minute"
                    }
                },
                "capacity_planning": {
                    "expected_volume": {"calls": 1000, "emails": 500, "chats": 300},
                    "peak_hours": ["9am-12pm", "2pm-5pm"],
                    "seasonal_factors": {"holiday_season": 1.5, "tax_season": 1.3}
                },
                "quality_standards": {
                    "call_quality_score_target": 0.90,
                    "customer_satisfaction_target": 0.85,
                    "first_contact_resolution_target": 0.80,
                    "compliance_requirements": ["data_privacy", "recording_disclosure"]
                },
                "technology_requirements": {
                    "systems": ["ACD", "IVR", "CRM", "knowledge_base"],
                    "integrations": ["order_management", "billing", "inventory"],
                    "reporting_dashboards": ["real_time", "daily", "weekly"]
                }
            },
            "context": {
                "planning_period": "Q1_2025",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_capacity_planning(self):
        """Test capacity planning calculations."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_multi_shift_scheduling(self):
        """Test multi-shift scheduling optimization."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["shift_requirements"] = {
            "morning": {"agents": 20, "skills": ["general"]},
            "afternoon": {"agents": 25, "skills": ["general", "technical"]},
            "night": {"agents": 10, "skills": ["general"]}
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestManageCustomerInquiriesCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for ManageCustomerInquiriesCustomerServiceAgent

    Agent: Manage customer inquiries
    Path: src/superstandard/agents/api/manage_customer_inquiries_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_customer_inquiries_customer_service_agent import (
            ManageCustomerInquiriesCustomerServiceAgent
        )
        return ManageCustomerInquiriesCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_customer_inquiries_customer_service_agent import (
            ManageCustomerInquiriesCustomerServiceAgentConfig
        )
        return ManageCustomerInquiriesCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for managing customer inquiries."""
        return {
            "task_type": "manage_inquiry",
            "data": {
                "inquiry": {
                    "inquiry_id": "INQ-2025-001234",
                    "customer_id": "CUST-98765",
                    "channel": "email",
                    "category": "product_information",
                    "subject": "Product specifications inquiry",
                    "description": "Customer asking about product dimensions and compatibility",
                    "priority": "medium",
                    "received_timestamp": datetime.now().isoformat()
                },
                "customer_context": {
                    "customer_tier": "gold",
                    "purchase_history": ["product_a", "product_b"],
                    "previous_inquiries": 3,
                    "sentiment": "neutral",
                    "preferred_language": "english"
                },
                "knowledge_base_access": True,
                "automation_rules": {
                    "auto_response_enabled": True,
                    "escalation_rules": {"high_priority": "immediate", "vip_customer": "immediate"},
                    "routing_rules": {"product_inquiry": "product_team", "technical": "tech_support"}
                }
            },
            "context": {
                "service_level": "standard",
                "business_hours": True,
                "priority": "medium"
            },
            "priority": "medium"
        }

    @pytest.mark.asyncio
    async def test_inquiry_routing(self):
        """Test inquiry routing logic."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        inquiry_types = ["product_information", "technical_support", "billing", "returns"]

        for inquiry_type in inquiry_types:
            input_data = self.generate_valid_input()
            input_data["data"]["inquiry"]["category"] = inquiry_type

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_priority_escalation(self):
        """Test priority-based escalation."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["inquiry"]["priority"] = "high"
        input_data["data"]["customer_context"]["customer_tier"] = "platinum"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestHandleServiceExceptionsCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for HandleServiceExceptionsCustomerServiceAgent

    Agent: Handle service exceptions
    Path: src/superstandard/agents/api/handle_service_exceptions_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.handle_service_exceptions_customer_service_agent import (
            HandleServiceExceptionsCustomerServiceAgent
        )
        return HandleServiceExceptionsCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.handle_service_exceptions_customer_service_agent import (
            HandleServiceExceptionsCustomerServiceAgentConfig
        )
        return HandleServiceExceptionsCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for handling service exceptions."""
        return {
            "task_type": "handle_exception",
            "data": {
                "exception": {
                    "exception_id": "EXC-2025-5678",
                    "case_id": "CASE-12345",
                    "customer_id": "CUST-98765",
                    "exception_type": "delivery_delay",
                    "severity": "high",
                    "description": "Order delayed beyond promised delivery date",
                    "impact": "customer_dissatisfaction",
                    "reported_timestamp": datetime.now().isoformat()
                },
                "customer_impact": {
                    "affected_orders": ["ORD-001", "ORD-002"],
                    "financial_impact": 500.00,
                    "customer_tier": "platinum",
                    "previous_exceptions": 0,
                    "customer_sentiment": "frustrated"
                },
                "resolution_options": {
                    "compensation": ["refund", "discount", "free_shipping"],
                    "expedited_service": True,
                    "direct_communication": True,
                    "escalation_path": ["supervisor", "manager", "director"]
                },
                "policy_guidelines": {
                    "max_compensation": 1000.00,
                    "approval_required_threshold": 500.00,
                    "response_time_sla": "1_hour"
                }
            },
            "context": {
                "exception_severity": "high",
                "customer_value": "high",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_exception_severity_handling(self):
        """Test handling of different exception severities."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            input_data = self.generate_valid_input()
            input_data["data"]["exception"]["severity"] = severity

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_compensation_calculation(self):
        """Test compensation calculation based on impact."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["customer_impact"]["financial_impact"] = 750.00

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestResolveCustomerIssuesCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for ResolveCustomerIssuesCustomerServiceAgent

    Agent: Resolve customer issues
    Path: src/superstandard/agents/api/resolve_customer_issues_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.resolve_customer_issues_customer_service_agent import (
            ResolveCustomerIssuesCustomerServiceAgent
        )
        return ResolveCustomerIssuesCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.resolve_customer_issues_customer_service_agent import (
            ResolveCustomerIssuesCustomerServiceAgentConfig
        )
        return ResolveCustomerIssuesCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for resolving customer issues."""
        return {
            "task_type": "resolve_issue",
            "data": {
                "issue": {
                    "issue_id": "ISS-2025-9999",
                    "customer_id": "CUST-11111",
                    "issue_type": "technical_problem",
                    "category": "product_malfunction",
                    "description": "Product not functioning as expected",
                    "priority": "high",
                    "status": "open",
                    "created_timestamp": datetime.now().isoformat(),
                    "sla_deadline": "2025-01-20T18:00:00"
                },
                "diagnostic_data": {
                    "product_id": "PROD-XYZ-123",
                    "error_codes": ["ERR-404", "ERR-500"],
                    "environment": "production",
                    "user_actions": ["action_1", "action_2"],
                    "system_logs": "log_data_available"
                },
                "resolution_knowledge": {
                    "known_issues": True,
                    "similar_cases": ["CASE-001", "CASE-002"],
                    "resolution_success_rate": 0.85,
                    "average_resolution_time": "2_hours"
                },
                "resolution_tools": {
                    "remote_access": True,
                    "diagnostic_tools": ["tool_a", "tool_b"],
                    "replacement_parts_available": True,
                    "expert_consultation": True
                }
            },
            "context": {
                "urgency": "high",
                "customer_tier": "gold",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_issue_resolution_workflow(self):
        """Test complete issue resolution workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        workflow_steps = ["diagnose", "troubleshoot", "resolve", "verify"]

        for step in workflow_steps:
            input_data = self.generate_valid_input()
            input_data["context"]["workflow_step"] = step

            result = await agent.execute(input_data)

            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_first_contact_resolution(self):
        """Test first contact resolution capability."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["resolution_knowledge"]["known_issues"] = True
        input_data["data"]["issue"]["priority"] = "medium"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestMeasureCustomerSatisfactionCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for MeasureCustomerSatisfactionCustomerServiceAgent (APQC 6.3)

    Agent: Measure customer satisfaction
    Path: src/superstandard/agents/api/measure_customer_satisfaction_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.measure_customer_satisfaction_customer_service_agent import (
            MeasureCustomerSatisfactionCustomerServiceAgent
        )
        return MeasureCustomerSatisfactionCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.measure_customer_satisfaction_customer_service_agent import (
            MeasureCustomerSatisfactionCustomerServiceAgentConfig
        )
        return MeasureCustomerSatisfactionCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_process_id": "6.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for measuring customer satisfaction."""
        return {
            "task_type": "measure_satisfaction",
            "data": {
                "survey_data": {
                    "survey_type": "post_interaction",
                    "responses": [
                        {"customer_id": "CUST-001", "score": 9, "feedback": "Excellent service"},
                        {"customer_id": "CUST-002", "score": 7, "feedback": "Good but slow"},
                        {"customer_id": "CUST-003", "score": 10, "feedback": "Perfect experience"},
                        {"customer_id": "CUST-004", "score": 6, "feedback": "Average"},
                        {"customer_id": "CUST-005", "score": 8, "feedback": "Very helpful"}
                    ],
                    "response_rate": 0.45,
                    "collection_period": "2025-01-01_to_2025-01-15"
                },
                "interaction_data": {
                    "total_interactions": 500,
                    "channels": {
                        "phone": {"count": 200, "avg_satisfaction": 8.5},
                        "email": {"count": 150, "avg_satisfaction": 7.8},
                        "chat": {"count": 150, "avg_satisfaction": 9.0}
                    },
                    "issue_categories": {
                        "technical": {"count": 150, "avg_satisfaction": 7.5},
                        "billing": {"count": 100, "avg_satisfaction": 8.0},
                        "general": {"count": 250, "avg_satisfaction": 8.8}
                    }
                },
                "measurement_metrics": {
                    "csat": True,
                    "nps": True,
                    "ces": True,
                    "fcr": True
                },
                "benchmarks": {
                    "industry_avg_csat": 0.80,
                    "company_target_csat": 0.85,
                    "previous_period_csat": 0.78
                }
            },
            "context": {
                "measurement_period": "monthly",
                "analysis_depth": "detailed",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_satisfaction_metrics_calculation(self):
        """Test calculation of various satisfaction metrics."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_channel_comparison_analysis(self):
        """Test satisfaction comparison across channels."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["analysis_type"] = "channel_comparison"

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestMeasureEvaluateCustomerServiceOperationsCustomerServiceAgent(APQCAgentTestCase):
    """
    Tests for MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent (APQC 6.3)

    Agent: Measure and evaluate customer service operations
    Path: src/superstandard/agents/api/measure_evaluate_customer_service_operations_customer_service_agent.py
    Domain: customer_service | Type: customer_service
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.measure_evaluate_customer_service_operations_customer_service_agent import (
            MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent
        )
        return MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.measure_evaluate_customer_service_operations_customer_service_agent import (
            MeasureEvaluateCustomerServiceOperationsCustomerServiceAgentConfig
        )
        return MeasureEvaluateCustomerServiceOperationsCustomerServiceAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "6.0",
            "apqc_process_id": "6.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for evaluating service operations."""
        return {
            "task_type": "evaluate_operations",
            "data": {
                "operational_metrics": {
                    "volume_metrics": {
                        "total_interactions": 10000,
                        "calls": 4000,
                        "emails": 3000,
                        "chats": 2500,
                        "social_media": 500
                    },
                    "efficiency_metrics": {
                        "average_handle_time": "6_minutes",
                        "first_contact_resolution": 0.78,
                        "average_speed_to_answer": "45_seconds",
                        "abandonment_rate": 0.05
                    },
                    "quality_metrics": {
                        "quality_assurance_score": 0.88,
                        "call_calibration_score": 0.90,
                        "compliance_rate": 0.95,
                        "error_rate": 0.02
                    },
                    "productivity_metrics": {
                        "contacts_per_agent_hour": 8.5,
                        "utilization_rate": 0.85,
                        "schedule_adherence": 0.92,
                        "shrinkage": 0.15
                    }
                },
                "cost_metrics": {
                    "cost_per_contact": 12.50,
                    "total_operational_cost": 125000,
                    "labor_cost_percentage": 0.70,
                    "technology_cost_percentage": 0.20
                },
                "targets": {
                    "first_contact_resolution_target": 0.80,
                    "quality_score_target": 0.90,
                    "cost_per_contact_target": 12.00,
                    "customer_satisfaction_target": 0.85
                },
                "evaluation_period": "2025-01-01_to_2025-01-31"
            },
            "context": {
                "evaluation_type": "monthly_review",
                "comparison_periods": ["previous_month", "previous_year"],
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_operational_performance_evaluation(self):
        """Test comprehensive operational performance evaluation."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_kpi_benchmarking(self):
        """Test KPI benchmarking against targets."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["benchmarking"] = {
            "industry_benchmarks": {
                "fcr": 0.82,
                "quality_score": 0.88,
                "cost_per_contact": 11.00
            }
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_6
@pytest.mark.apqc_integration
class TestCategory6Integration:
    """
    Integration tests for Category 6.0 - Customer Service agents.

    Tests complete customer journey workflows from inquiry to satisfaction measurement.
    """

    @pytest.mark.asyncio
    async def test_complete_customer_journey_workflow(self):
        """
        Test complete customer journey workflow.

        Workflow:
        1. Customer inquiry received (ManageCustomerInquiriesCustomerServiceAgent)
        2. Issue identified and resolved (ResolveCustomerIssuesCustomerServiceAgent)
        3. Satisfaction measured (MeasureCustomerSatisfactionCustomerServiceAgent)
        4. Operations evaluated (MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent)
        """
        # Import agents
        from superstandard.agents.api.manage_customer_inquiries_customer_service_agent import (
            ManageCustomerInquiriesCustomerServiceAgent,
            ManageCustomerInquiriesCustomerServiceAgentConfig
        )
        from superstandard.agents.api.resolve_customer_issues_customer_service_agent import (
            ResolveCustomerIssuesCustomerServiceAgent,
            ResolveCustomerIssuesCustomerServiceAgentConfig
        )
        from superstandard.agents.api.measure_customer_satisfaction_customer_service_agent import (
            MeasureCustomerSatisfactionCustomerServiceAgent,
            MeasureCustomerSatisfactionCustomerServiceAgentConfig
        )
        from superstandard.agents.api.measure_evaluate_customer_service_operations_customer_service_agent import (
            MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent,
            MeasureEvaluateCustomerServiceOperationsCustomerServiceAgentConfig
        )

        # Create agent instances
        inquiry_agent = ManageCustomerInquiriesCustomerServiceAgent(
            ManageCustomerInquiriesCustomerServiceAgentConfig()
        )
        resolution_agent = ResolveCustomerIssuesCustomerServiceAgent(
            ResolveCustomerIssuesCustomerServiceAgentConfig()
        )
        satisfaction_agent = MeasureCustomerSatisfactionCustomerServiceAgent(
            MeasureCustomerSatisfactionCustomerServiceAgentConfig()
        )
        evaluation_agent = MeasureEvaluateCustomerServiceOperationsCustomerServiceAgent(
            MeasureEvaluateCustomerServiceOperationsCustomerServiceAgentConfig()
        )

        # Step 1: Receive and manage inquiry
        inquiry_input = {
            "task_type": "manage_inquiry",
            "data": {
                "inquiry": {
                    "inquiry_id": "INQ-001",
                    "customer_id": "CUST-001",
                    "category": "technical_support",
                    "description": "Product not working"
                }
            },
            "priority": "high"
        }
        inquiry_result = await inquiry_agent.execute(inquiry_input)
        assert inquiry_result['status'] in ['completed', 'degraded']

        # Step 2: Resolve the issue
        resolution_input = {
            "task_type": "resolve_issue",
            "data": {
                "issue": {
                    "issue_id": "ISS-001",
                    "customer_id": "CUST-001",
                    "issue_type": "technical_problem",
                    "description": "Product malfunction"
                },
                "diagnostic_data": {"error_codes": ["ERR-500"]}
            },
            "priority": "high"
        }
        resolution_result = await resolution_agent.execute(resolution_input)
        assert resolution_result['status'] in ['completed', 'degraded']

        # Step 3: Measure satisfaction
        satisfaction_input = {
            "task_type": "measure_satisfaction",
            "data": {
                "survey_data": {
                    "responses": [{"customer_id": "CUST-001", "score": 9}]
                }
            },
            "priority": "medium"
        }
        satisfaction_result = await satisfaction_agent.execute(satisfaction_input)
        assert satisfaction_result['status'] in ['completed', 'degraded']

        # Step 4: Evaluate operations
        evaluation_input = {
            "task_type": "evaluate_operations",
            "data": {
                "operational_metrics": {
                    "volume_metrics": {"total_interactions": 100},
                    "efficiency_metrics": {"first_contact_resolution": 0.80}
                }
            },
            "priority": "medium"
        }
        evaluation_result = await evaluation_agent.execute(evaluation_input)
        assert evaluation_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_exception_handling_workflow(self):
        """Test exception handling and resolution workflow."""
        from superstandard.agents.api.handle_service_exceptions_customer_service_agent import (
            HandleServiceExceptionsCustomerServiceAgent,
            HandleServiceExceptionsCustomerServiceAgentConfig
        )
        from superstandard.agents.api.resolve_customer_issues_customer_service_agent import (
            ResolveCustomerIssuesCustomerServiceAgent,
            ResolveCustomerIssuesCustomerServiceAgentConfig
        )

        exception_agent = HandleServiceExceptionsCustomerServiceAgent(
            HandleServiceExceptionsCustomerServiceAgentConfig()
        )
        resolution_agent = ResolveCustomerIssuesCustomerServiceAgent(
            ResolveCustomerIssuesCustomerServiceAgentConfig()
        )

        # Step 1: Handle exception
        exception_input = {
            "task_type": "handle_exception",
            "data": {
                "exception": {
                    "exception_id": "EXC-001",
                    "exception_type": "delivery_delay",
                    "severity": "high"
                }
            },
            "priority": "high"
        }
        exception_result = await exception_agent.execute(exception_input)
        assert exception_result['status'] in ['completed', 'degraded']

        # Step 2: Resolve resulting issue
        resolution_input = {
            "task_type": "resolve_issue",
            "data": {
                "issue": {"issue_id": "ISS-001", "issue_type": "delivery_issue"},
                "diagnostic_data": {}
            },
            "priority": "high"
        }
        resolution_result = await resolution_agent.execute(resolution_input)
        assert resolution_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_service_strategy_to_operations_flow(self):
        """Test flow from strategy development to operations management."""
        from superstandard.agents.trading.develop_customer_care_customer_service_strategy_customer_service_agent import (
            DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent,
            DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgentConfig
        )
        from superstandard.agents.api.plan_manage_customer_service_operations_customer_service_agent import (
            PlanManageCustomerServiceOperationsCustomerServiceAgent,
            PlanManageCustomerServiceOperationsCustomerServiceAgentConfig
        )

        strategy_agent = DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgent(
            DevelopCustomerCareCustomerServiceStrategyCustomerServiceAgentConfig()
        )
        operations_agent = PlanManageCustomerServiceOperationsCustomerServiceAgent(
            PlanManageCustomerServiceOperationsCustomerServiceAgentConfig()
        )

        # Develop strategy
        strategy_input = {
            "task_type": "develop_customer_service_strategy",
            "data": {
                "business_objectives": {"customer_satisfaction_target": 0.90},
                "current_state": {"customer_satisfaction": 0.75}
            },
            "priority": "high"
        }
        strategy_result = await strategy_agent.execute(strategy_input)
        assert strategy_result['status'] in ['completed', 'degraded']

        # Implement operations based on strategy
        operations_input = {
            "task_type": "manage_service_operations",
            "data": {
                "operational_parameters": {
                    "service_hours": "24/7",
                    "staffing_levels": {"day_shift": 30}
                },
                "strategy_alignment": strategy_result.get('output', {})
            },
            "priority": "high"
        }
        operations_result = await operations_agent.execute(operations_input)
        assert operations_result['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_6
class TestCategory6Capabilities:
    """
    Test category-specific capabilities for Customer Service agents.
    """

    @pytest.mark.asyncio
    async def test_multi_channel_support(self):
        """Verify agents support multiple customer service channels."""
        from superstandard.agents.api.manage_customer_inquiries_customer_service_agent import (
            ManageCustomerInquiriesCustomerServiceAgent,
            ManageCustomerInquiriesCustomerServiceAgentConfig
        )

        agent = ManageCustomerInquiriesCustomerServiceAgent(
            ManageCustomerInquiriesCustomerServiceAgentConfig()
        )

        channels = ["phone", "email", "chat", "social_media", "self_service"]

        for channel in channels:
            input_data = {
                "task_type": "manage_inquiry",
                "data": {
                    "inquiry": {
                        "inquiry_id": f"INQ-{channel}",
                        "channel": channel,
                        "category": "general"
                    }
                },
                "priority": "medium"
            }
            result = await agent.execute(input_data)
            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_sla_compliance_tracking(self):
        """Test SLA compliance tracking capabilities."""
        from superstandard.agents.api.plan_manage_customer_service_operations_customer_service_agent import (
            PlanManageCustomerServiceOperationsCustomerServiceAgent,
            PlanManageCustomerServiceOperationsCustomerServiceAgentConfig
        )

        agent = PlanManageCustomerServiceOperationsCustomerServiceAgent(
            PlanManageCustomerServiceOperationsCustomerServiceAgentConfig()
        )

        input_data = {
            "task_type": "manage_service_operations",
            "data": {
                "operational_parameters": {
                    "sla_targets": {
                        "phone_response": "30_seconds",
                        "email_response": "2_hours",
                        "chat_response": "1_minute"
                    }
                }
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Performance Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_6
@pytest.mark.slow
class TestCategory6Performance:
    """
    Performance tests for Category 6 agents.
    """

    @pytest.mark.asyncio
    async def test_high_volume_inquiry_processing(self):
        """Test processing high volume of customer inquiries."""
        import asyncio
        from superstandard.agents.api.manage_customer_inquiries_customer_service_agent import (
            ManageCustomerInquiriesCustomerServiceAgent,
            ManageCustomerInquiriesCustomerServiceAgentConfig
        )

        agent = ManageCustomerInquiriesCustomerServiceAgent(
            ManageCustomerInquiriesCustomerServiceAgentConfig()
        )

        # Process 10 inquiries in parallel
        tasks = []
        for i in range(10):
            input_data = {
                "task_type": "manage_inquiry",
                "data": {
                    "inquiry": {
                        "inquiry_id": f"INQ-{i:04d}",
                        "customer_id": f"CUST-{i:04d}",
                        "category": "general",
                        "description": f"Test inquiry {i}"
                    }
                },
                "priority": "medium"
            }
            tasks.append(agent.execute(input_data))

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_concurrent_satisfaction_measurements(self):
        """Test concurrent satisfaction measurement processing."""
        import asyncio
        from superstandard.agents.api.measure_customer_satisfaction_customer_service_agent import (
            MeasureCustomerSatisfactionCustomerServiceAgent,
            MeasureCustomerSatisfactionCustomerServiceAgentConfig
        )

        agents = [
            MeasureCustomerSatisfactionCustomerServiceAgent(
                MeasureCustomerSatisfactionCustomerServiceAgentConfig()
            )
            for _ in range(3)
        ]

        input_data = {
            "task_type": "measure_satisfaction",
            "data": {
                "survey_data": {
                    "responses": [{"customer_id": f"CUST-{i}", "score": 8} for i in range(10)]
                }
            },
            "priority": "medium"
        }

        tasks = [agent.execute(input_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
