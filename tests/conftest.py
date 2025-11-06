"""
Pytest Configuration and Shared Fixtures

Provides common test fixtures, configuration, and utilities for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Also add old location for backwards compatibility testing
sys.path.insert(0, str(project_root / "agents" / "consolidated" / "py"))


@pytest.fixture
def base_agent_class():
    """Provide the canonical BaseAgent class."""
    from superstandard.agents.base.base_agent import BaseAgent

    return BaseAgent


@pytest.fixture
def sample_agent_config():
    """Provide sample agent configuration for testing."""
    return {
        "agent_id": "test-agent-001",
        "name": "TestAgent",
        "description": "Agent for testing",
        "capabilities": ["test", "validate"],
        "version": "1.0.0",
        "metadata": {"test": True, "environment": "test"},
    }


@pytest.fixture
def mock_agent(base_agent_class, sample_agent_config):
    """Create a mock agent instance for testing."""

    class MockAgent(base_agent_class):
        """Mock agent implementation for testing."""

        def __init__(self, config=None):
            super().__init__(config or sample_agent_config)

        async def execute(self, input_data):
            """Mock execute method."""
            return {"status": "success", "input": input_data, "output": "mock_result"}

    return MockAgent


@pytest.fixture
def temp_agent_dir(tmp_path):
    """Provide temporary directory for agent files."""
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    return agent_dir


# Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for protocols")
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "protocol: Protocol compliance tests (ANP, ACP, BAP)")
