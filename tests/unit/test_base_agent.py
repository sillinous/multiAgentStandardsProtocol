"""
Unit Tests for BaseAgent

Comprehensive tests for the canonical BaseAgent implementation ensuring:
- Proper initialization and configuration
- Protocol compliance (A2A, ANP, ACP)
- Capability management
- Message handling
- Lifecycle management
"""

import pytest
import asyncio
from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    def __init__(
        self,
        agent_id="test-agent",
        agent_type="testing",
        capabilities=None,
        workspace_path="./test_workspace",
    ):
        if capabilities is None:
            capabilities = [AgentCapability.TESTING]
        super().__init__(agent_id, agent_type, capabilities, workspace_path)

    async def execute_task(self, task_description: str, context: dict = None):
        """Required execute_task implementation."""
        return {
            "status": "success",
            "result": f"processed: {task_description}",
            "agent_id": self.agent_id,
        }

    async def analyze_result(self, result: dict, expected: dict = None):
        """Required analyze_result implementation."""
        return {
            "analysis": "test analysis",
            "passed": True,
            "result": result,
        }


@pytest.mark.unit
class TestBaseAgentInitialization:
    """Test BaseAgent initialization and configuration."""

    def test_agent_creation(self):
        """Test basic agent creation."""
        agent = ConcreteTestAgent()
        assert agent is not None
        assert agent.agent_id == "test-agent"

    def test_agent_id_assigned(self):
        """Test that agent ID is properly assigned."""
        agent = ConcreteTestAgent()
        assert hasattr(agent, "agent_id")
        assert agent.agent_id == "test-agent"

    def test_capabilities_initialization(self):
        """Test capabilities are properly initialized."""
        agent = ConcreteTestAgent()
        assert hasattr(agent, "capabilities")
        assert AgentCapability.TESTING in agent.capabilities

    def test_custom_config(self):
        """Test agent with custom configuration."""
        agent = ConcreteTestAgent(
            agent_id="custom-test",
            agent_type="custom",
            capabilities=[AgentCapability.DEVELOPMENT, AgentCapability.TESTING],
        )
        assert agent.agent_id == "custom-test"
        assert agent.agent_type == "custom"
        assert AgentCapability.TESTING in agent.capabilities


@pytest.mark.unit
@pytest.mark.asyncio
class TestBaseAgentExecution:
    """Test BaseAgent execution functionality."""

    async def test_execute_basic(self):
        """Test basic execution."""
        agent = ConcreteTestAgent()
        result = await agent.execute_task("test_input")
        assert result["status"] == "success"
        assert "processed: test_input" in result["result"]

    async def test_execute_with_context(self):
        """Test execution with context."""
        agent = ConcreteTestAgent()
        result = await agent.execute_task("task", context={"key": "value"})
        assert result["status"] == "success"
        assert result["agent_id"] == "test-agent"

    async def test_analyze_result(self):
        """Test result analysis."""
        agent = ConcreteTestAgent()
        test_result = {"test": "data"}
        analysis = await agent.analyze_result(test_result)
        assert "analysis" in analysis
        assert analysis["passed"] is True


@pytest.mark.unit
class TestBaseAgentCapabilities:
    """Test capability management."""

    def test_has_capability(self):
        """Test capability checking."""
        agent = ConcreteTestAgent()
        assert "test" in agent.config.get("capabilities", [])

    def test_add_capability(self):
        """Test adding new capabilities."""
        agent = ConcreteTestAgent()
        capabilities = agent.config.get("capabilities", [])
        capabilities.append("new_capability")
        assert "new_capability" in agent.config["capabilities"]

    def test_multiple_capabilities(self):
        """Test agent with multiple capabilities."""
        config = {
            "agent_id": "multi-cap",
            "name": "MultiCapAgent",
            "description": "Multi-capability agent",
            "capabilities": ["cap1", "cap2", "cap3"],
        }
        agent = ConcreteTestAgent(config)
        assert len(agent.config["capabilities"]) == 3
        assert "cap1" in agent.config["capabilities"]
        assert "cap2" in agent.config["capabilities"]
        assert "cap3" in agent.config["capabilities"]


@pytest.mark.unit
class TestBaseAgentConfiguration:
    """Test configuration management."""

    def test_config_immutability_options(self):
        """Test configuration modification patterns."""
        agent = ConcreteTestAgent()
        original_name = agent.config.get("name")

        # Modify config
        agent.config["name"] = "ModifiedName"
        assert agent.config["name"] == "ModifiedName"
        assert agent.config["name"] != original_name

    def test_config_dict_access(self):
        """Test dictionary-style config access."""
        agent = ConcreteTestAgent()
        assert agent.config.get("name") is not None
        assert agent.config.get("nonexistent") is None
        assert agent.config.get("nonexistent", "default") == "default"

    def test_config_contains_required_fields(self):
        """Test config has all required fields."""
        agent = ConcreteTestAgent()
        required_fields = ["agent_id", "name", "description", "capabilities"]
        for field in required_fields:
            assert field in agent.config, f"Missing required field: {field}"


@pytest.mark.unit
class TestBaseAgentProtocolCompliance:
    """Test protocol compliance features."""

    def test_agent_has_protocol_attributes(self):
        """Test agent has protocol-related attributes."""
        agent = ConcreteTestAgent()
        # BaseAgent should have config for protocol support
        assert hasattr(agent, "config")

    def test_agent_metadata(self):
        """Test agent metadata handling."""
        config = {
            "agent_id": "meta-test",
            "name": "MetaTestAgent",
            "description": "Test metadata",
            "capabilities": [],
            "metadata": {
                "version": "1.0.0",
                "author": "test",
                "protocol:a2a": "1.0",
                "protocol:anp": "1.0",
            },
        }
        agent = ConcreteTestAgent(config)
        assert agent.config.get("metadata", {}).get("version") == "1.0.0"
        assert "protocol:a2a" in agent.config.get("metadata", {})


@pytest.mark.unit
class TestBaseAgentLifecycle:
    """Test agent lifecycle management."""

    def test_agent_creation_lifecycle(self):
        """Test agent creation process."""
        agent = ConcreteTestAgent()
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert isinstance(agent, ConcreteTestAgent)

    @pytest.mark.asyncio
    async def test_agent_execution_lifecycle(self):
        """Test agent execution lifecycle."""
        agent = ConcreteTestAgent()

        # Execute multiple times
        result1 = await agent.execute("input1")
        result2 = await agent.execute("input2")
        result3 = await agent.execute("input3")

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result3["status"] == "success"

    def test_agent_config_persistence(self):
        """Test config persists across method calls."""
        agent = ConcreteTestAgent()
        original_id = agent.config["agent_id"]

        # Call execute (would normally be async)
        _ = asyncio.run(agent.execute("test"))

        # Config should persist
        assert agent.config["agent_id"] == original_id


@pytest.mark.unit
class TestBaseAgentInheritance:
    """Test BaseAgent inheritance patterns."""

    def test_subclass_creation(self):
        """Test creating subclass of BaseAgent."""

        class CustomAgent(BaseAgent):
            async def execute(self, input_data):
                return {"custom": True}

        agent = CustomAgent({"agent_id": "custom", "name": "Custom", "description": "Test", "capabilities": []})
        assert isinstance(agent, BaseAgent)
        assert isinstance(agent, CustomAgent)

    def test_method_override(self):
        """Test overriding BaseAgent methods."""

        class OverrideAgent(BaseAgent):
            async def execute(self, input_data):
                return {"overridden": True, "input": input_data}

        agent = OverrideAgent({"agent_id": "override", "name": "Override", "description": "Test", "capabilities": []})
        result = asyncio.run(agent.execute("test"))
        assert result["overridden"] is True


@pytest.mark.unit
class TestBaseAgentEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_capabilities(self):
        """Test agent with no capabilities."""
        config = {
            "agent_id": "no-cap",
            "name": "NoCapAgent",
            "description": "No capabilities",
            "capabilities": [],
        }
        agent = ConcreteTestAgent(config)
        assert len(agent.config["capabilities"]) == 0

    def test_minimal_config(self):
        """Test agent with minimal configuration."""
        config = {
            "agent_id": "minimal",
            "name": "Minimal",
            "description": "Minimal config",
            "capabilities": [],
        }
        agent = ConcreteTestAgent(config)
        assert agent.config["agent_id"] == "minimal"

    @pytest.mark.asyncio
    async def test_execute_with_none(self):
        """Test execution with None input."""
        agent = ConcreteTestAgent()
        result = await agent.execute(None)
        assert "status" in result


# Integration test for import path
@pytest.mark.unit
class TestCanonicalImport:
    """Test canonical import path works correctly."""

    def test_canonical_import(self):
        """Test importing from canonical path."""
        from superstandard.agents.base.base_agent import BaseAgent as CanonicalBaseAgent

        agent = ConcreteTestAgent()
        assert isinstance(agent, CanonicalBaseAgent)

    def test_import_consistency(self):
        """Test multiple imports reference same class."""
        from superstandard.agents.base.base_agent import BaseAgent as Import1
        from superstandard.agents.base.base_agent import BaseAgent as Import2

        assert Import1 is Import2  # Same class object
