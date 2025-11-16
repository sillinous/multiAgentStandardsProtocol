"""
APQC Testing Fixtures

Pytest fixtures and configuration for APQC agent testing.
Provides common test data, mocks, and agent factory fixtures.

Version: 1.0.0
Framework: APQC 7.0.1
"""

import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


# ========================================================================
# Pytest Configuration
# ========================================================================

def pytest_configure(config):
    """Register custom pytest markers for APQC tests."""
    config.addinivalue_line(
        "markers",
        "apqc: Tests for APQC framework agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_1: Tests for APQC Category 1.0 - Vision and Strategy agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_2: Tests for APQC Category 2.0 - Products and Services agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_3: Tests for APQC Category 3.0 - Market and Sell agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_4: Tests for APQC Category 4.0 - Deliver Physical Products agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_5: Tests for APQC Category 5.0 - Deliver Services agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_6: Tests for APQC Category 6.0 - Customer Service agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_7: Tests for APQC Category 7.0 - Human Capital agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_8: Tests for APQC Category 8.0 - Information Technology agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_9: Tests for APQC Category 9.0 - Financial Resources agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_10: Tests for APQC Category 10.0 - Assets agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_11: Tests for APQC Category 11.0 - Risk, Compliance agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_12: Tests for APQC Category 12.0 - External Relationships agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_category_13: Tests for APQC Category 13.0 - Business Capabilities agents"
    )
    config.addinivalue_line(
        "markers",
        "apqc_integration: Integration tests across multiple APQC agents"
    )


# ========================================================================
# Common Test Data Fixtures
# ========================================================================

@pytest.fixture
def apqc_framework_version():
    """APQC framework version."""
    return "7.0.1"


@pytest.fixture
def test_timestamp():
    """Current timestamp for testing."""
    return datetime.now().isoformat()


@pytest.fixture
def base_input_data():
    """Base input data structure for agent testing."""
    return {
        "task_type": "test_task",
        "data": {
            "test_field": "test_value",
            "timestamp": datetime.now().isoformat()
        },
        "context": {
            "environment": "test",
            "priority": "medium"
        },
        "priority": "medium"
    }


@pytest.fixture
def strategic_input_data():
    """Input data for strategic agents."""
    return {
        "task_type": "strategic_planning",
        "data": {
            "market_analysis": {
                "market_size": 1000000,
                "growth_rate": 0.15,
                "trends": ["digital_transformation", "sustainability"]
            },
            "competitive_landscape": {
                "competitors": 5,
                "market_share": 0.20,
                "competitive_advantages": ["innovation", "quality"]
            },
            "internal_capabilities": {
                "strengths": ["innovation", "quality", "customer_service"],
                "weaknesses": ["scale", "geographic_reach"],
                "opportunities": ["market_expansion", "new_products"],
                "threats": ["new_entrants", "regulation"]
            },
            "objectives": ["market_expansion", "revenue_growth", "innovation"]
        },
        "context": {
            "timeframe": "3_years",
            "priority": "high",
            "stakeholders": ["board", "executives", "investors"]
        },
        "priority": "high"
    }


@pytest.fixture
def operational_input_data():
    """Input data for operational agents."""
    return {
        "task_type": "operational_execution",
        "data": {
            "resources": {
                "budget": 100000,
                "personnel": 10,
                "equipment": ["servers", "software"]
            },
            "requirements": {
                "timeline": "30_days",
                "quality_standard": "high",
                "deliverables": ["report", "implementation"]
            },
            "constraints": ["budget", "timeline", "resources"]
        },
        "context": {
            "department": "operations",
            "priority": "medium",
            "dependencies": []
        },
        "priority": "medium"
    }


@pytest.fixture
def sales_marketing_input_data():
    """Input data for sales and marketing agents."""
    return {
        "task_type": "marketing_campaign",
        "data": {
            "target_market": {
                "segments": ["enterprise", "mid_market"],
                "geography": ["north_america", "europe"],
                "demographics": {"industry": "technology", "size": "1000+"}
            },
            "campaign_goals": {
                "leads": 1000,
                "conversion_rate": 0.05,
                "revenue_target": 500000
            },
            "budget": 50000,
            "channels": ["digital", "events", "content_marketing"]
        },
        "context": {
            "quarter": "Q1_2025",
            "priority": "high"
        },
        "priority": "high"
    }


@pytest.fixture
def service_delivery_input_data():
    """Input data for service delivery agents."""
    return {
        "task_type": "service_delivery",
        "data": {
            "service_type": "customer_support",
            "customer_id": "CUST-12345",
            "request": {
                "type": "technical_assistance",
                "description": "Integration issue with API",
                "severity": "high"
            },
            "sla": {
                "response_time": "2_hours",
                "resolution_time": "24_hours"
            }
        },
        "context": {
            "channel": "email",
            "priority": "high",
            "escalation_path": ["tier_2", "tier_3", "engineering"]
        },
        "priority": "high"
    }


@pytest.fixture
def financial_input_data():
    """Input data for financial agents."""
    return {
        "task_type": "financial_analysis",
        "data": {
            "transactions": [
                {"amount": 1000, "type": "revenue", "date": "2025-01-15"},
                {"amount": 500, "type": "expense", "date": "2025-01-16"}
            ],
            "period": "Q1_2025",
            "analysis_type": "profitability",
            "metrics": ["revenue", "costs", "profit_margin", "roi"]
        },
        "context": {
            "business_unit": "product_division",
            "priority": "medium"
        },
        "priority": "medium"
    }


@pytest.fixture
def hr_input_data():
    """Input data for human capital agents."""
    return {
        "task_type": "recruitment",
        "data": {
            "position": {
                "title": "Senior Software Engineer",
                "department": "engineering",
                "level": "senior",
                "skills_required": ["python", "kubernetes", "microservices"]
            },
            "candidates": 50,
            "timeline": "60_days",
            "budget": 150000
        },
        "context": {
            "hiring_urgency": "high",
            "priority": "high"
        },
        "priority": "high"
    }


# ========================================================================
# Mock Objects and Services
# ========================================================================

@pytest.fixture
def mock_knowledge_graph():
    """Mock knowledge graph service."""
    mock = Mock()
    mock.query = AsyncMock(return_value={"results": []})
    mock.store = AsyncMock(return_value={"status": "success"})
    return mock


@pytest.fixture
def mock_vector_db():
    """Mock vector database service."""
    mock = Mock()
    mock.search = AsyncMock(return_value={"matches": []})
    mock.insert = AsyncMock(return_value={"status": "success"})
    return mock


@pytest.fixture
def mock_event_bus():
    """Mock event bus service."""
    mock = Mock()
    mock.publish = AsyncMock(return_value={"status": "published"})
    mock.subscribe = AsyncMock(return_value={"status": "subscribed"})
    return mock


@pytest.fixture
def mock_external_api():
    """Mock external API service."""
    mock = Mock()
    mock.get = AsyncMock(return_value={"status": "success", "data": {}})
    mock.post = AsyncMock(return_value={"status": "success", "data": {}})
    return mock


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "text": "Generated response",
        "tokens": 100,
        "model": "test-model"
    })
    return mock


# ========================================================================
# Agent Factory Fixtures
# ========================================================================

@pytest.fixture
def agent_workspace(tmp_path):
    """Temporary workspace for agent testing."""
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()
    return str(workspace)


@pytest.fixture
def create_test_agent_config():
    """Factory fixture for creating test agent configurations."""
    def _create_config(
        agent_id: str = "test-agent-001",
        agent_type: str = "strategic",
        domain: str = "strategy",
        **kwargs
    ):
        """Create a test agent configuration."""
        from dataclasses import dataclass, field

        @dataclass
        class TestAgentConfig:
            # APQC Metadata
            apqc_agent_id: str = "apqc_test_001"
            apqc_category_id: str = "1.0"
            apqc_process_id: str = "1.0.1"
            apqc_process_name: str = "Test Process"

            # Agent Identity
            agent_id: str = agent_id
            agent_name: str = f"{agent_id}_name"
            agent_type: str = agent_type
            domain: str = domain
            version: str = "1.0.0"

            # Behavior Configuration
            autonomous_level: float = 0.6
            collaboration_mode: str = "orchestrated"
            learning_enabled: bool = True
            self_improvement: bool = True

            # Resource Configuration
            compute_mode: str = "adaptive"
            memory_mode: str = "adaptive"
            api_budget_mode: str = "dynamic"
            priority: str = "high"

            # Quality Configuration
            testing_required: bool = True
            qa_threshold: float = 0.85
            consensus_weight: float = 1.0
            error_handling: str = "graceful_degradation"

            # Deployment Configuration
            runtime: str = "ray_actor"
            scaling: str = "horizontal"
            health_checks: bool = True
            monitoring: bool = True

            # Environment Variables
            log_level: str = "INFO"
            max_retries: int = 3
            timeout_seconds: int = 300

            @classmethod
            def from_environment(cls):
                """Create from environment variables."""
                return cls()

        # Apply any additional kwargs
        config = TestAgentConfig()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    return _create_config


@pytest.fixture
def create_mock_agent():
    """Factory fixture for creating mock APQC agents."""
    def _create_agent(
        agent_class=None,
        config=None,
        **kwargs
    ):
        """Create a mock APQC agent for testing."""
        if agent_class is None:
            from superstandard.agents.base.base_agent import BaseAgent
            from superstandard.agents.base.protocols import ProtocolMixin

            class MockAPQCAgent(BaseAgent, ProtocolMixin):
                """Mock APQC agent for testing."""

                VERSION = "1.0.0"
                MIN_COMPATIBLE_VERSION = "1.0.0"
                APQC_AGENT_ID = "apqc_mock_001"
                APQC_CATEGORY_ID = "1.0"
                APQC_PROCESS_ID = "1.0.1"
                APQC_FRAMEWORK_VERSION = "7.0.1"

                def __init__(self, config):
                    from superstandard.agents.base.base_agent import AgentCapability
                    super().__init__(
                        agent_id=config.agent_id,
                        agent_type=config.agent_type,
                        capabilities=[AgentCapability.TESTING],
                        workspace_path=kwargs.get('workspace_path', './test_workspace')
                    )
                    self.config = config
                    self.capabilities_list = ["testing", "analysis"]
                    self.state = {
                        "status": "initialized",
                        "tasks_processed": 0,
                        "last_activity": datetime.now().isoformat(),
                        "performance_metrics": {},
                        "learning_data": {} if config.learning_enabled else None
                    }

                async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                    """Mock execute method."""
                    self.state["tasks_processed"] += 1
                    return {
                        "status": "completed",
                        "apqc_process_id": self.APQC_PROCESS_ID,
                        "agent_id": self.config.agent_id,
                        "timestamp": datetime.now().isoformat(),
                        "output": {
                            "analysis": {},
                            "recommendations": [],
                            "decisions": [],
                            "artifacts": [],
                            "metrics": {},
                            "events": []
                        }
                    }

                async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                    """Mock execute_task method."""
                    return await self.execute(task)

                async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                    """Mock analyze method."""
                    return {"analysis": "mock analysis", "result": "success"}

                async def health_check(self) -> Dict[str, Any]:
                    """Mock health check."""
                    return {
                        "agent_id": self.config.agent_id,
                        "agent_name": self.config.agent_name,
                        "version": self.VERSION,
                        "status": self.state["status"],
                        "timestamp": datetime.now().isoformat(),
                        "apqc_metadata": {
                            "category_id": self.APQC_CATEGORY_ID,
                            "process_id": self.APQC_PROCESS_ID,
                            "framework_version": self.APQC_FRAMEWORK_VERSION
                        },
                        "protocols": ["A2A", "A2P", "ACP", "ANP", "MCP"],
                        "capabilities": self.capabilities_list,
                        "compliance": {
                            "standardized": True,
                            "interoperable": True,
                            "redeployable": True,
                            "reusable": True,
                            "atomic": True,
                            "composable": True,
                            "orchestratable": True,
                            "vendor_agnostic": True
                        },
                        "performance": {
                            "tasks_processed": self.state["tasks_processed"],
                            "memory_mb": 0.0,
                            "last_activity": self.state["last_activity"]
                        },
                        "behavior": {
                            "autonomous_level": self.config.autonomous_level,
                            "learning_enabled": self.config.learning_enabled,
                            "collaboration_mode": self.config.collaboration_mode
                        },
                        "deployment": {
                            "runtime": self.config.runtime,
                            "scaling": self.config.scaling,
                            "monitoring": self.config.monitoring
                        }
                    }

                def get_input_schema(self) -> Dict[str, Any]:
                    """Mock get input schema."""
                    return {
                        "type": "object",
                        "apqc_process_id": self.APQC_PROCESS_ID,
                        "properties": {
                            "task_type": {"type": "string"},
                            "data": {"type": "object"},
                            "context": {"type": "object"},
                            "priority": {"type": "string"}
                        },
                        "required": ["task_type", "data"]
                    }

                def get_output_schema(self) -> Dict[str, Any]:
                    """Mock get output schema."""
                    return {
                        "type": "object",
                        "apqc_process_id": self.APQC_PROCESS_ID,
                        "properties": {
                            "status": {"type": "string"},
                            "apqc_process_id": {"type": "string"},
                            "agent_id": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "output": {"type": "object"}
                        },
                        "required": ["status", "apqc_process_id", "agent_id", "timestamp", "output"]
                    }

                @classmethod
                def from_environment(cls):
                    """Create from environment."""
                    from dataclasses import dataclass

                    @dataclass
                    class MockConfig:
                        agent_id: str = "mock-agent"
                        agent_name: str = "mock_agent"
                        agent_type: str = "mock"
                        autonomous_level: float = 0.6
                        learning_enabled: bool = True
                        collaboration_mode: str = "orchestrated"
                        runtime: str = "ray_actor"
                        scaling: str = "horizontal"
                        monitoring: bool = True

                        @classmethod
                        def from_environment(cls):
                            return cls()

                    return cls(MockConfig())

            agent_class = MockAPQCAgent

        if config is None:
            from dataclasses import dataclass

            @dataclass
            class DefaultConfig:
                agent_id: str = "test-agent"
                agent_name: str = "test_agent"
                agent_type: str = "test"
                autonomous_level: float = 0.6
                learning_enabled: bool = True
                collaboration_mode: str = "orchestrated"
                runtime: str = "ray_actor"
                scaling: str = "horizontal"
                monitoring: bool = True

            config = DefaultConfig()

        return agent_class(config)

    return _create_agent


# ========================================================================
# Helper Fixtures
# ========================================================================

@pytest.fixture
def assert_apqc_compliance():
    """Helper fixture for asserting APQC compliance."""
    def _assert_compliance(agent, expected_metadata=None):
        """Assert agent is APQC compliant."""
        from superstandard.agents.base.base_agent import BaseAgent
        from superstandard.agents.base.protocols import ProtocolMixin

        # Check inheritance
        assert isinstance(agent, BaseAgent), "Agent must inherit from BaseAgent"
        assert isinstance(agent, ProtocolMixin), "Agent must implement ProtocolMixin"

        # Check APQC metadata
        assert hasattr(agent, 'APQC_AGENT_ID'), "Must have APQC_AGENT_ID"
        assert hasattr(agent, 'APQC_CATEGORY_ID'), "Must have APQC_CATEGORY_ID"
        assert hasattr(agent, 'APQC_PROCESS_ID'), "Must have APQC_PROCESS_ID"
        assert hasattr(agent, 'APQC_FRAMEWORK_VERSION'), "Must have APQC_FRAMEWORK_VERSION"

        # Check framework version
        assert agent.APQC_FRAMEWORK_VERSION == "7.0.1", "Must use APQC 7.0.1"

        # Validate expected metadata if provided
        if expected_metadata:
            if 'apqc_agent_id' in expected_metadata:
                assert agent.APQC_AGENT_ID == expected_metadata['apqc_agent_id']
            if 'apqc_category_id' in expected_metadata:
                assert agent.APQC_CATEGORY_ID == expected_metadata['apqc_category_id']
            if 'apqc_process_id' in expected_metadata:
                assert agent.APQC_PROCESS_ID == expected_metadata['apqc_process_id']

        return True

    return _assert_compliance


# ========================================================================
# Export Public API
# ========================================================================

__all__ = [
    'apqc_framework_version',
    'test_timestamp',
    'base_input_data',
    'strategic_input_data',
    'operational_input_data',
    'sales_marketing_input_data',
    'service_delivery_input_data',
    'financial_input_data',
    'hr_input_data',
    'mock_knowledge_graph',
    'mock_vector_db',
    'mock_event_bus',
    'mock_external_api',
    'mock_llm_service',
    'agent_workspace',
    'create_test_agent_config',
    'create_mock_agent',
    'assert_apqc_compliance',
]
