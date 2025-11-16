"""
APQC Category 8.0 - Manage Information Technology Agent Tests

Comprehensive tests for all 8 Information Technology agents from APQC Category 8.0.

Agents tested:
1. ManageItEnterpriseArchitectureTechnologyAgent (8.1)
2. DesignItSolutionsTechnologyAgent (8.2)
3. DeployItSolutionsTechnologyAgent
4. ManageItInfrastructureTechnologyAgent (8.3)
5. ManageItSecurityPrivacyTechnologyAgent (8.4)
6. ManageItServicesOperationsTechnologyAgent
7. DevelopManageItCustomerRelationshipsTechnologyAgent
8. ManageBusinessOfItTechnologyAgent

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- IT service management workflow integration
- Security and compliance testing
- Infrastructure and deployment automation

Version: 1.0.0
Framework: APQC 7.0.1
Category: 8.0 - Manage Information Technology
"""

import pytest
from typing import Dict, Any
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 8.0 Agent Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestManageItEnterpriseArchitectureTechnologyAgent(APQCAgentTestCase):
    """
    Tests for ManageItEnterpriseArchitectureTechnologyAgent (APQC 8.1)

    Agent: Manage IT enterprise architecture
    Path: src/superstandard/agents/infrastructure/manage_it_enterprise_architecture_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.infrastructure.manage_it_enterprise_architecture_technology_agent import (
            ManageItEnterpriseArchitectureTechnologyAgent
        )
        return ManageItEnterpriseArchitectureTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.infrastructure.manage_it_enterprise_architecture_technology_agent import (
            ManageItEnterpriseArchitectureTechnologyAgentConfig
        )
        return ManageItEnterpriseArchitectureTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_process_id": "8.1",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for enterprise architecture management."""
        return {
            "task_type": "manage_enterprise_architecture",
            "data": {
                "architecture_domains": {
                    "business": {
                        "capabilities": ["crm", "erp", "analytics"],
                        "processes": ["order_to_cash", "procure_to_pay"]
                    },
                    "application": {
                        "current_state": ["legacy_crm", "custom_erp", "excel_reporting"],
                        "target_state": ["cloud_crm", "saas_erp", "bi_platform"],
                        "gaps": ["real_time_analytics", "mobile_access"]
                    },
                    "data": {
                        "master_data": ["customer", "product", "supplier"],
                        "data_quality": 0.85,
                        "data_governance": "maturing"
                    },
                    "technology": {
                        "platforms": ["aws", "azure"],
                        "standards": ["rest_api", "microservices", "containers"],
                        "tech_stack": ["python", "react", "postgresql"]
                    }
                },
                "governance": {
                    "framework": "togaf",
                    "review_cycle": "quarterly",
                    "stakeholders": ["cto", "enterprise_architects", "business_leaders"]
                },
                "transformation_roadmap": {
                    "initiatives": ["cloud_migration", "api_strategy", "data_platform"],
                    "timeline": "24_months",
                    "budget": 5000000
                }
            },
            "context": {
                "organization_size": "enterprise",
                "industry": "technology",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_architecture_assessment(self):
        """Test architecture assessment capabilities."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "assess_architecture"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_architecture_governance(self):
        """Test architecture governance processes."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["data"]["governance"]["compliance_check"] = True

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestDesignItSolutionsTechnologyAgent(APQCAgentTestCase):
    """
    Tests for DesignItSolutionsTechnologyAgent (APQC 8.2)

    Agent: Design IT solutions
    Path: src/superstandard/agents/ui/design_it_solutions_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.ui.design_it_solutions_technology_agent import (
            DesignItSolutionsTechnologyAgent
        )
        return DesignItSolutionsTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.ui.design_it_solutions_technology_agent import (
            DesignItSolutionsTechnologyAgentConfig
        )
        return DesignItSolutionsTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_process_id": "8.2",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for IT solution design."""
        return {
            "task_type": "design_solution",
            "data": {
                "requirements": {
                    "functional": [
                        "user_authentication",
                        "data_processing",
                        "reporting_dashboard",
                        "api_integration"
                    ],
                    "non_functional": {
                        "performance": "sub_second_response",
                        "scalability": "10000_concurrent_users",
                        "availability": "99.9_percent",
                        "security": "soc2_compliant"
                    }
                },
                "design_patterns": {
                    "architecture": "microservices",
                    "integration": "event_driven",
                    "data": "cqrs",
                    "ui": "responsive_spa"
                },
                "technology_stack": {
                    "frontend": ["react", "typescript", "tailwind"],
                    "backend": ["python", "fastapi", "celery"],
                    "data": ["postgresql", "redis", "elasticsearch"],
                    "infrastructure": ["kubernetes", "aws", "terraform"]
                },
                "quality_attributes": {
                    "maintainability": "high",
                    "testability": "automated",
                    "observability": "comprehensive",
                    "security": "zero_trust"
                }
            },
            "context": {
                "project_type": "greenfield",
                "timeline": "6_months",
                "team_size": 8,
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_solution_architecture_design(self):
        """Test solution architecture design."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result

    @pytest.mark.asyncio
    async def test_technology_selection(self):
        """Test technology selection and recommendations."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "select_technology"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestDeployItSolutionsTechnologyAgent(APQCAgentTestCase):
    """
    Tests for DeployItSolutionsTechnologyAgent

    Agent: Deploy IT solutions
    Path: src/superstandard/agents/devops/deploy_it_solutions_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.devops.deploy_it_solutions_technology_agent import (
            DeployItSolutionsTechnologyAgent
        )
        return DeployItSolutionsTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.devops.deploy_it_solutions_technology_agent import (
            DeployItSolutionsTechnologyAgentConfig
        )
        return DeployItSolutionsTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for IT solution deployment."""
        return {
            "task_type": "deploy_solution",
            "data": {
                "deployment_config": {
                    "environment": "production",
                    "region": "us-east-1",
                    "platform": "kubernetes",
                    "strategy": "blue_green"
                },
                "application": {
                    "name": "customer_portal",
                    "version": "2.5.0",
                    "container_image": "registry.example.com/customer-portal:2.5.0",
                    "replicas": 3,
                    "resources": {
                        "cpu": "500m",
                        "memory": "1Gi"
                    }
                },
                "infrastructure": {
                    "compute": ["ec2", "eks"],
                    "storage": ["ebs", "s3"],
                    "networking": ["vpc", "load_balancer", "route53"],
                    "security": ["waf", "secrets_manager", "kms"]
                },
                "cicd": {
                    "pipeline": "github_actions",
                    "stages": ["build", "test", "security_scan", "deploy"],
                    "approval_gates": ["qa", "production"],
                    "rollback_enabled": True
                },
                "monitoring": {
                    "metrics": ["prometheus", "cloudwatch"],
                    "logging": ["elk_stack", "cloudwatch_logs"],
                    "tracing": ["jaeger"],
                    "alerting": ["pagerduty", "slack"]
                }
            },
            "context": {
                "deployment_window": "2025-01-20T02:00:00Z",
                "change_ticket": "CHG-12345",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_deployment_execution(self):
        """Test deployment execution."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_rollback_capability(self):
        """Test rollback capability."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "rollback_deployment"
        input_data["data"]["rollback_to_version"] = "2.4.0"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestManageItInfrastructureTechnologyAgent(APQCAgentTestCase):
    """
    Tests for ManageItInfrastructureTechnologyAgent (APQC 8.3)

    Agent: Manage IT infrastructure
    Path: src/superstandard/agents/devops/manage_it_infrastructure_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.devops.manage_it_infrastructure_technology_agent import (
            ManageItInfrastructureTechnologyAgent
        )
        return ManageItInfrastructureTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.devops.manage_it_infrastructure_technology_agent import (
            ManageItInfrastructureTechnologyAgentConfig
        )
        return ManageItInfrastructureTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_process_id": "8.3",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for infrastructure management."""
        return {
            "task_type": "manage_infrastructure",
            "data": {
                "infrastructure_inventory": {
                    "compute": {
                        "vms": 150,
                        "containers": 500,
                        "serverless_functions": 75
                    },
                    "storage": {
                        "block_storage_tb": 100,
                        "object_storage_tb": 500,
                        "databases": 25
                    },
                    "network": {
                        "vpcs": 5,
                        "load_balancers": 10,
                        "cdn_distributions": 3
                    }
                },
                "capacity_planning": {
                    "current_utilization": {
                        "compute": 0.65,
                        "storage": 0.70,
                        "network": 0.45
                    },
                    "growth_projection": {
                        "monthly_growth_rate": 0.05,
                        "forecasted_demand": "12_months"
                    },
                    "scaling_thresholds": {
                        "scale_up": 0.80,
                        "scale_down": 0.40
                    }
                },
                "operations": {
                    "automation": ["terraform", "ansible", "cloudformation"],
                    "monitoring": ["prometheus", "grafana", "nagios"],
                    "backup_recovery": {
                        "rpo_hours": 4,
                        "rto_hours": 2,
                        "backup_frequency": "daily"
                    },
                    "patch_management": {
                        "schedule": "monthly",
                        "testing_required": True,
                        "maintenance_window": "sunday_02:00_06:00"
                    }
                },
                "cost_optimization": {
                    "monthly_spend": 100000,
                    "optimization_targets": ["right_sizing", "reserved_instances", "spot_instances"],
                    "savings_goal": 0.20
                }
            },
            "context": {
                "infrastructure_type": "hybrid_cloud",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_capacity_planning(self):
        """Test capacity planning functionality."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "plan_capacity"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_infrastructure_monitoring(self):
        """Test infrastructure monitoring."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "monitor_infrastructure"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestManageItSecurityPrivacyTechnologyAgent(APQCAgentTestCase):
    """
    Tests for ManageItSecurityPrivacyTechnologyAgent (APQC 8.4)

    Agent: Manage IT security and privacy
    Path: src/superstandard/agents/security/manage_it_security_privacy_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.security.manage_it_security_privacy_technology_agent import (
            ManageItSecurityPrivacyTechnologyAgent
        )
        return ManageItSecurityPrivacyTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.security.manage_it_security_privacy_technology_agent import (
            ManageItSecurityPrivacyTechnologyAgentConfig
        )
        return ManageItSecurityPrivacyTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_process_id": "8.4",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for security and privacy management."""
        return {
            "task_type": "manage_security_privacy",
            "data": {
                "security_framework": {
                    "standard": "nist_csf",
                    "maturity_level": "level_3",
                    "compliance_requirements": ["soc2", "iso27001", "gdpr", "ccpa"]
                },
                "threat_landscape": {
                    "identified_threats": [
                        "ransomware",
                        "phishing",
                        "data_breach",
                        "insider_threat",
                        "ddos"
                    ],
                    "risk_scores": {
                        "critical": 5,
                        "high": 12,
                        "medium": 25,
                        "low": 40
                    }
                },
                "security_controls": {
                    "preventive": [
                        "firewall",
                        "waf",
                        "antivirus",
                        "mfa",
                        "encryption"
                    ],
                    "detective": [
                        "siem",
                        "ids_ips",
                        "vulnerability_scanning",
                        "log_monitoring"
                    ],
                    "responsive": [
                        "incident_response_plan",
                        "backup_recovery",
                        "disaster_recovery"
                    ]
                },
                "privacy_management": {
                    "data_classification": {
                        "pii": True,
                        "phi": False,
                        "financial": True,
                        "confidential": True
                    },
                    "data_protection": {
                        "encryption_at_rest": True,
                        "encryption_in_transit": True,
                        "tokenization": True,
                        "anonymization": True
                    },
                    "privacy_policies": {
                        "data_retention": "7_years",
                        "data_deletion": "automated",
                        "consent_management": True,
                        "data_subject_rights": ["access", "deletion", "portability"]
                    }
                },
                "security_operations": {
                    "soc": {
                        "coverage": "24x7",
                        "analysts": 8,
                        "tools": ["splunk", "crowdstrike", "palo_alto"]
                    },
                    "vulnerability_management": {
                        "scan_frequency": "weekly",
                        "patch_sla": {
                            "critical": "24_hours",
                            "high": "7_days",
                            "medium": "30_days"
                        }
                    },
                    "incident_response": {
                        "response_time": "15_minutes",
                        "escalation_levels": 3,
                        "runbooks": 25
                    }
                }
            },
            "context": {
                "organization_type": "financial_services",
                "priority": "critical"
            },
            "priority": "critical"
        }

    @pytest.mark.asyncio
    async def test_security_assessment(self):
        """Test security assessment capabilities."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "assess_security"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_privacy_compliance(self):
        """Test privacy compliance management."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "manage_privacy_compliance"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_incident_response(self):
        """Test incident response workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "respond_to_incident"
        input_data["data"]["incident"] = {
            "type": "data_breach",
            "severity": "critical",
            "affected_systems": ["customer_database"],
            "detected_at": "2025-01-15T10:30:00Z"
        }

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestManageItServicesOperationsTechnologyAgent(APQCAgentTestCase):
    """
    Tests for ManageItServicesOperationsTechnologyAgent

    Agent: Manage IT services and operations
    Path: src/superstandard/agents/api/manage_it_services_operations_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.manage_it_services_operations_technology_agent import (
            ManageItServicesOperationsTechnologyAgent
        )
        return ManageItServicesOperationsTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.manage_it_services_operations_technology_agent import (
            ManageItServicesOperationsTechnologyAgentConfig
        )
        return ManageItServicesOperationsTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for IT service operations."""
        return {
            "task_type": "manage_it_services",
            "data": {
                "service_catalog": {
                    "services": [
                        {
                            "name": "email_hosting",
                            "tier": "standard",
                            "sla": "99.9_percent",
                            "users": 1000
                        },
                        {
                            "name": "cloud_storage",
                            "tier": "premium",
                            "sla": "99.95_percent",
                            "capacity_gb": 10000
                        },
                        {
                            "name": "application_hosting",
                            "tier": "enterprise",
                            "sla": "99.99_percent",
                            "applications": 25
                        }
                    ]
                },
                "service_desk": {
                    "ticket_volume": {
                        "incidents": 500,
                        "service_requests": 300,
                        "changes": 50,
                        "problems": 10
                    },
                    "performance_metrics": {
                        "first_response_time_minutes": 15,
                        "resolution_time_hours": 4,
                        "customer_satisfaction": 4.2,
                        "first_call_resolution": 0.65
                    },
                    "staffing": {
                        "tier_1": 10,
                        "tier_2": 5,
                        "tier_3": 3,
                        "coverage": "24x7"
                    }
                },
                "itil_processes": {
                    "incident_management": {
                        "enabled": True,
                        "automation_rate": 0.40,
                        "escalation_matrix": True
                    },
                    "change_management": {
                        "enabled": True,
                        "approval_workflow": "multi_stage",
                        "cab_meetings": "weekly"
                    },
                    "problem_management": {
                        "enabled": True,
                        "root_cause_analysis": True,
                        "knowledge_base": True
                    },
                    "service_level_management": {
                        "sla_monitoring": True,
                        "reporting": "monthly",
                        "breach_alerting": True
                    }
                },
                "automation": {
                    "tools": ["servicenow", "ansible", "python_scripts"],
                    "automated_workflows": 35,
                    "time_savings_hours_monthly": 200
                }
            },
            "context": {
                "itsm_framework": "itil_v4",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_service_desk_operations(self):
        """Test service desk operations."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "manage_service_desk"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_sla_monitoring(self):
        """Test SLA monitoring and reporting."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "monitor_sla"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestDevelopManageItCustomerRelationshipsTechnologyAgent(APQCAgentTestCase):
    """
    Tests for DevelopManageItCustomerRelationshipsTechnologyAgent

    Agent: Develop and manage IT customer relationships
    Path: src/superstandard/agents/business/develop_manage_it_customer_relationships_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.business.develop_manage_it_customer_relationships_technology_agent import (
            DevelopManageItCustomerRelationshipsTechnologyAgent
        )
        return DevelopManageItCustomerRelationshipsTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.business.develop_manage_it_customer_relationships_technology_agent import (
            DevelopManageItCustomerRelationshipsTechnologyAgentConfig
        )
        return DevelopManageItCustomerRelationshipsTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for IT customer relationship management."""
        return {
            "task_type": "manage_it_customer_relationships",
            "data": {
                "stakeholders": {
                    "internal": {
                        "business_units": ["sales", "marketing", "operations", "finance"],
                        "executives": ["ceo", "cfo", "coo"],
                        "employees": 500
                    },
                    "external": {
                        "vendors": 20,
                        "partners": 10,
                        "consultants": 5
                    }
                },
                "relationship_management": {
                    "communication": {
                        "regular_meetings": "monthly",
                        "status_reports": "weekly",
                        "newsletters": "quarterly",
                        "satisfaction_surveys": "biannual"
                    },
                    "engagement_metrics": {
                        "satisfaction_score": 4.1,
                        "engagement_rate": 0.75,
                        "adoption_rate": 0.80
                    }
                },
                "business_alignment": {
                    "strategic_initiatives": [
                        "digital_transformation",
                        "cloud_adoption",
                        "data_analytics",
                        "automation"
                    ],
                    "business_value": {
                        "cost_savings": 1000000,
                        "productivity_gains": "15_percent",
                        "revenue_enablement": 5000000
                    }
                },
                "support_model": {
                    "account_managers": 3,
                    "relationship_reviews": "quarterly",
                    "escalation_path": ["service_desk", "it_manager", "cio"]
                }
            },
            "context": {
                "organization_model": "centralized_it",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @pytest.mark.asyncio
    async def test_stakeholder_engagement(self):
        """Test stakeholder engagement management."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


@pytest.mark.apqc
@pytest.mark.apqc_category_8
class TestManageBusinessOfItTechnologyAgent(APQCAgentTestCase):
    """
    Tests for ManageBusinessOfItTechnologyAgent

    Agent: Manage business of IT
    Path: src/superstandard/agents/business/manage_business_of_it_technology_agent.py
    Domain: technology | Type: technology
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.business.manage_business_of_it_technology_agent import (
            ManageBusinessOfItTechnologyAgent
        )
        return ManageBusinessOfItTechnologyAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.business.manage_business_of_it_technology_agent import (
            ManageBusinessOfItTechnologyAgentConfig
        )
        return ManageBusinessOfItTechnologyAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "8.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for IT business management."""
        return {
            "task_type": "manage_it_business",
            "data": {
                "financial_management": {
                    "budget": {
                        "annual_budget": 10000000,
                        "categories": {
                            "personnel": 0.50,
                            "infrastructure": 0.25,
                            "software": 0.15,
                            "projects": 0.10
                        },
                        "variance_threshold": 0.05
                    },
                    "cost_allocation": {
                        "method": "activity_based",
                        "chargeback_enabled": True,
                        "transparency": "high"
                    },
                    "roi_tracking": {
                        "projects": 15,
                        "average_roi": 2.5,
                        "payback_period_months": 18
                    }
                },
                "portfolio_management": {
                    "projects": {
                        "in_progress": 12,
                        "planned": 8,
                        "completed_ytd": 20
                    },
                    "prioritization": {
                        "criteria": ["business_value", "strategic_alignment", "risk", "cost"],
                        "framework": "weighted_scoring"
                    },
                    "resource_allocation": {
                        "available_capacity": 10000,
                        "allocated_capacity": 8500,
                        "utilization": 0.85
                    }
                },
                "vendor_management": {
                    "vendors": {
                        "strategic": 5,
                        "preferred": 15,
                        "approved": 50
                    },
                    "contract_value": 5000000,
                    "performance_tracking": {
                        "sla_compliance": 0.95,
                        "quality_score": 4.0,
                        "cost_competitiveness": "good"
                    }
                },
                "performance_management": {
                    "kpis": {
                        "system_availability": 0.998,
                        "incident_resolution_time": 4.2,
                        "project_on_time_delivery": 0.80,
                        "customer_satisfaction": 4.1,
                        "cost_per_user": 2000
                    },
                    "benchmarking": {
                        "peer_comparison": True,
                        "industry_standards": True
                    }
                },
                "governance": {
                    "framework": "cobit",
                    "policies": 25,
                    "compliance_audits": "annual",
                    "steering_committee": "monthly"
                }
            },
            "context": {
                "it_operating_model": "hybrid",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_it_financial_management(self):
        """Test IT financial management."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "manage_it_finance"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_it_portfolio_management(self):
        """Test IT portfolio management."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = self.generate_valid_input()
        input_data["task_type"] = "manage_it_portfolio"

        result = await agent.execute(input_data)
        assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Category Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_8
@pytest.mark.apqc_integration
class TestCategory8Integration:
    """
    Integration tests for Category 8.0 - Information Technology agents.

    Tests complete IT service management workflows.
    """

    @pytest.mark.asyncio
    async def test_complete_it_solution_lifecycle(self):
        """
        Test complete IT solution lifecycle.

        Workflow:
        1. Enterprise architecture planning
        2. Solution design
        3. Solution deployment
        4. Infrastructure management
        5. Security and privacy management
        6. Service operations
        """
        # Import agents
        from superstandard.agents.infrastructure.manage_it_enterprise_architecture_technology_agent import (
            ManageItEnterpriseArchitectureTechnologyAgent,
            ManageItEnterpriseArchitectureTechnologyAgentConfig
        )
        from superstandard.agents.ui.design_it_solutions_technology_agent import (
            DesignItSolutionsTechnologyAgent,
            DesignItSolutionsTechnologyAgentConfig
        )
        from superstandard.agents.devops.deploy_it_solutions_technology_agent import (
            DeployItSolutionsTechnologyAgent,
            DeployItSolutionsTechnologyAgentConfig
        )
        from superstandard.agents.api.manage_it_services_operations_technology_agent import (
            ManageItServicesOperationsTechnologyAgent,
            ManageItServicesOperationsTechnologyAgentConfig
        )

        # Create agents
        architecture_agent = ManageItEnterpriseArchitectureTechnologyAgent(
            ManageItEnterpriseArchitectureTechnologyAgentConfig()
        )
        design_agent = DesignItSolutionsTechnologyAgent(
            DesignItSolutionsTechnologyAgentConfig()
        )
        deploy_agent = DeployItSolutionsTechnologyAgent(
            DeployItSolutionsTechnologyAgentConfig()
        )
        operations_agent = ManageItServicesOperationsTechnologyAgent(
            ManageItServicesOperationsTechnologyAgentConfig()
        )

        # Execute workflow
        arch_result = await architecture_agent.execute(MockDataGenerator.generate_strategic_input())
        assert arch_result['status'] in ['completed', 'degraded']

        design_result = await design_agent.execute(MockDataGenerator.generate_operational_input())
        assert design_result['status'] in ['completed', 'degraded']

        deploy_result = await deploy_agent.execute(MockDataGenerator.generate_operational_input())
        assert deploy_result['status'] in ['completed', 'degraded']

        ops_result = await operations_agent.execute(MockDataGenerator.generate_service_input())
        assert ops_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_security_and_compliance_workflow(self):
        """Test security and compliance workflow."""
        from superstandard.agents.security.manage_it_security_privacy_technology_agent import (
            ManageItSecurityPrivacyTechnologyAgent,
            ManageItSecurityPrivacyTechnologyAgentConfig
        )
        from superstandard.agents.devops.manage_it_infrastructure_technology_agent import (
            ManageItInfrastructureTechnologyAgent,
            ManageItInfrastructureTechnologyAgentConfig
        )

        security_agent = ManageItSecurityPrivacyTechnologyAgent(
            ManageItSecurityPrivacyTechnologyAgentConfig()
        )
        infrastructure_agent = ManageItInfrastructureTechnologyAgent(
            ManageItInfrastructureTechnologyAgentConfig()
        )

        # Execute security assessment
        security_result = await security_agent.execute(MockDataGenerator.generate_operational_input())
        assert security_result['status'] in ['completed', 'degraded']

        # Execute infrastructure hardening
        infra_result = await infrastructure_agent.execute(MockDataGenerator.generate_operational_input())
        assert infra_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_it_business_alignment(self):
        """Test IT and business alignment."""
        from superstandard.agents.business.manage_business_of_it_technology_agent import (
            ManageBusinessOfItTechnologyAgent,
            ManageBusinessOfItTechnologyAgentConfig
        )
        from superstandard.agents.business.develop_manage_it_customer_relationships_technology_agent import (
            DevelopManageItCustomerRelationshipsTechnologyAgent,
            DevelopManageItCustomerRelationshipsTechnologyAgentConfig
        )

        business_agent = ManageBusinessOfItTechnologyAgent(
            ManageBusinessOfItTechnologyAgentConfig()
        )
        relationship_agent = DevelopManageItCustomerRelationshipsTechnologyAgent(
            DevelopManageItCustomerRelationshipsTechnologyAgentConfig()
        )

        business_result = await business_agent.execute(MockDataGenerator.generate_strategic_input())
        assert business_result['status'] in ['completed', 'degraded']

        relationship_result = await relationship_agent.execute(MockDataGenerator.generate_strategic_input())
        assert relationship_result['status'] in ['completed', 'degraded']


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
