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
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "requires_api_key: Tests requiring API keys")


# ============================================================================
# Advanced Feature Fixtures (Continuous Evolution, Pareto, Backtesting)
# ============================================================================

@pytest.fixture
def sample_genome():
    """Sample AgentGenome for testing"""
    from superstandard.agents import AgentGenome

    return AgentGenome(
        agent_id="test-agent-123",
        generation=0,
        personality_traits={
            'openness': 0.7,
            'conscientiousness': 0.8,
            'extraversion': 0.5,
            'agreeableness': 0.6,
            'neuroticism': 0.3
        },
        fitness_score=0.75
    )


@pytest.fixture
def sample_genomes():
    """List of sample genomes for population tests"""
    from superstandard.agents import AgentGenome

    return [
        AgentGenome(
            agent_id=f"agent-{i}",
            generation=0,
            personality_traits={
                'openness': 0.5 + (i * 0.1),
                'conscientiousness': 0.6 + (i * 0.05),
                'extraversion': 0.4 + (i * 0.08),
                'agreeableness': 0.7 - (i * 0.05),
                'neuroticism': 0.3 + (i * 0.04)
            },
            fitness_score=0.5 + (i * 0.05)
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_market_data():
    """Sample market data for backtesting"""
    from superstandard.agents.backtest_engine import MarketBar
    from datetime import datetime, timedelta

    bars = []
    base_price = 100.0

    for i in range(100):
        # Simulate price movement
        change = (i % 10 - 5) * 0.5  # Creates waves
        price = base_price + change

        bars.append(MarketBar(
            timestamp=datetime.now() - timedelta(days=100-i),
            open=price - 0.5,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=1000000 + (i * 10000)
        ))

    return bars


@pytest.fixture
def sample_objectives():
    """Sample objectives for Pareto evolution"""
    from superstandard.agents.pareto_evolution import Objective, ObjectiveType

    return [
        Objective(objective_type=ObjectiveType.RETURN, minimize=False, weight=1.0),
        Objective(objective_type=ObjectiveType.SHARPE_RATIO, minimize=False, weight=1.0),
        Objective(objective_type=ObjectiveType.MAX_DRAWDOWN, minimize=True, weight=1.0)
    ]


@pytest.fixture
async def api_client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from superstandard.api.server import app

    return TestClient(app)
