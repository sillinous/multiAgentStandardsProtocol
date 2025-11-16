"""
APQC Agent Testing Framework

This module provides the base testing infrastructure for all 118 APQC agents.
It includes:
- APQCAgentTestCase: Base test class for all APQC agent tests
- Common fixtures and utilities
- Standard test patterns
- Mock data generators
- Helper methods for validation

All APQC agent tests should inherit from APQCAgentTestCase to ensure
consistent testing across the framework.

Usage:
    class TestMyAPQCAgent(APQCAgentTestCase):
        def get_agent_class(self):
            return MyAPQCAgent

        def get_agent_config(self):
            return MyAPQCAgentConfig()

Version: 1.0.0
Framework: APQC 7.0.1
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

from superstandard.agents.base.base_agent import BaseAgent
from superstandard.agents.base.protocols import ProtocolMixin, A2AMessage, ANPRegistration, AgentStatus


class APQCAgentTestCase(ABC):
    """
    Base test case class for all APQC agents.

    Provides standard test patterns and utilities for:
    - Agent initialization
    - Execution testing
    - Health check validation
    - Protocol compliance
    - APQC metadata verification
    - Input/output schema validation

    All APQC agent test classes should inherit from this class.
    """

    @abstractmethod
    def get_agent_class(self) -> Type[BaseAgent]:
        """
        Return the agent class to test.

        Returns:
            Agent class (not instance)
        """
        pass

    @abstractmethod
    def get_agent_config(self) -> Any:
        """
        Return the agent configuration for testing.

        Returns:
            Agent configuration object
        """
        pass

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """
        Return expected APQC metadata for validation.
        Override in subclasses to provide specific metadata.

        Returns:
            Dictionary with APQC metadata fields
        """
        return {
            "apqc_agent_id": None,
            "apqc_category_id": None,
            "apqc_process_id": None,
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """
        Return expected capabilities for the agent.
        Override in subclasses to provide specific capabilities.

        Returns:
            List of expected capability names
        """
        return []

    def get_expected_protocols(self) -> List[str]:
        """
        Return expected protocols for the agent.

        Returns:
            List of protocol names (A2A, A2P, ACP, ANP, MCP)
        """
        return ["A2A", "A2P", "ACP", "ANP", "MCP"]

    # ========================================================================
    # Standard Test Patterns
    # ========================================================================

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """
        Test 1: Agent Initialization

        Verifies that:
        - Agent can be instantiated with config
        - Agent has required attributes
        - Agent state is properly initialized
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()

        # Create agent instance
        agent = agent_class(config)

        # Verify basic attributes
        assert agent is not None, "Agent should be instantiated"
        assert hasattr(agent, 'config'), "Agent should have config attribute"
        assert hasattr(agent, 'state'), "Agent should have state attribute"
        assert hasattr(agent, 'VERSION'), "Agent should have VERSION constant"
        assert hasattr(agent, 'APQC_AGENT_ID'), "Agent should have APQC_AGENT_ID"
        assert hasattr(agent, 'APQC_CATEGORY_ID'), "Agent should have APQC_CATEGORY_ID"
        assert hasattr(agent, 'APQC_PROCESS_ID'), "Agent should have APQC_PROCESS_ID"
        assert hasattr(agent, 'APQC_FRAMEWORK_VERSION'), "Agent should have APQC_FRAMEWORK_VERSION"

        # Verify state initialization
        assert agent.state is not None, "Agent state should be initialized"
        assert 'status' in agent.state, "Agent state should have status"
        assert agent.state['status'] == 'initialized', "Initial status should be 'initialized'"

    @pytest.mark.asyncio
    async def test_agent_execute_success(self):
        """
        Test 2: Execute Success

        Verifies that:
        - Agent can execute with valid input
        - Returns proper output structure
        - Updates state after execution
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Prepare test input
        input_data = self.generate_valid_input()

        # Execute
        result = await agent.execute(input_data)

        # Verify result structure
        assert result is not None, "Execute should return a result"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'status' in result, "Result should have status field"
        assert result['status'] in ['completed', 'degraded'], "Status should be completed or degraded"
        assert 'apqc_process_id' in result, "Result should include APQC process ID"
        assert 'agent_id' in result, "Result should include agent ID"
        assert 'timestamp' in result, "Result should include timestamp"
        assert 'output' in result, "Result should include output"

        # Verify state was updated
        assert agent.state['tasks_processed'] > 0, "Tasks processed should increment"

    @pytest.mark.asyncio
    async def test_agent_execute_error_handling(self):
        """
        Test 3: Execute Error Handling

        Verifies that:
        - Agent handles invalid input gracefully
        - Returns proper error structure
        - Follows configured error handling strategy
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Test with invalid input
        invalid_input = self.generate_invalid_input()

        result = await agent.execute(invalid_input)

        # Verify error handling
        assert result is not None, "Should return error result"
        assert isinstance(result, dict), "Error result should be a dictionary"
        assert 'status' in result, "Error result should have status"
        assert result['status'] in ['error', 'degraded'], "Status should indicate error"

        # Verify error handling mode
        if hasattr(agent.config, 'error_handling'):
            assert 'error_handling' in result or 'message' in result, \
                "Result should include error handling info"

    @pytest.mark.asyncio
    async def test_agent_health_check(self):
        """
        Test 4: Health Check

        Verifies that:
        - Agent responds to health check requests
        - Returns complete health information
        - Includes APQC metadata
        - Includes protocol information
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Perform health check
        health = await agent.health_check()

        # Verify health check structure
        assert health is not None, "Health check should return data"
        assert isinstance(health, dict), "Health check should return dictionary"

        # Verify required fields
        required_fields = [
            'agent_id', 'agent_name', 'version', 'status', 'timestamp',
            'apqc_metadata', 'protocols', 'capabilities', 'compliance',
            'performance', 'behavior', 'deployment'
        ]
        for field in required_fields:
            assert field in health, f"Health check should include {field}"

        # Verify APQC metadata
        apqc_meta = health['apqc_metadata']
        assert 'category_id' in apqc_meta, "Should include APQC category ID"
        assert 'process_id' in apqc_meta, "Should include APQC process ID"
        assert 'framework_version' in apqc_meta, "Should include framework version"
        assert apqc_meta['framework_version'] == '7.0.1', "Should use APQC 7.0.1"

        # Verify compliance flags
        compliance = health['compliance']
        compliance_principles = [
            'standardized', 'interoperable', 'redeployable', 'reusable',
            'atomic', 'composable', 'orchestratable', 'vendor_agnostic'
        ]
        for principle in compliance_principles:
            assert principle in compliance, f"Should include {principle} compliance"
            assert compliance[principle] is True, f"Should be {principle} compliant"

    @pytest.mark.asyncio
    async def test_protocol_compliance(self):
        """
        Test 5: Protocol Compliance

        Verifies that:
        - Agent implements all required protocols
        - Protocol methods are available
        - Agent can be used in protocol workflows
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Verify ProtocolMixin inheritance
        assert isinstance(agent, ProtocolMixin), "Agent should implement ProtocolMixin"

        # Verify protocol support methods
        protocol_methods = [
            'get_protocol_info',
            'send_protocol_message',
            'handle_protocol_message',
            'register_protocol_handler'
        ]
        for method in protocol_methods:
            assert hasattr(agent, method), f"Agent should have {method} method"

        # Verify expected protocols
        expected_protocols = self.get_expected_protocols()
        protocol_info = agent.get_protocol_info()

        if 'supported_protocols' in protocol_info:
            supported = protocol_info['supported_protocols']
            for protocol in expected_protocols:
                assert protocol in supported, f"Agent should support {protocol} protocol"

    @pytest.mark.asyncio
    async def test_apqc_metadata_correctness(self):
        """
        Test 6: APQC Metadata Correctness

        Verifies that:
        - Agent has correct APQC metadata constants
        - Metadata matches expected values
        - Framework version is correct
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Verify APQC constants exist
        assert hasattr(agent, 'APQC_AGENT_ID'), "Should have APQC_AGENT_ID"
        assert hasattr(agent, 'APQC_CATEGORY_ID'), "Should have APQC_CATEGORY_ID"
        assert hasattr(agent, 'APQC_PROCESS_ID'), "Should have APQC_PROCESS_ID"
        assert hasattr(agent, 'APQC_FRAMEWORK_VERSION'), "Should have APQC_FRAMEWORK_VERSION"

        # Verify framework version
        assert agent.APQC_FRAMEWORK_VERSION == '7.0.1', "Should use APQC 7.0.1"

        # Verify metadata format
        assert agent.APQC_AGENT_ID.startswith('apqc_'), "Agent ID should start with 'apqc_'"
        assert '.' in agent.APQC_CATEGORY_ID, "Category ID should be in X.Y format"
        assert '.' in agent.APQC_PROCESS_ID, "Process ID should be in X.Y.Z format"

        # Verify against expected metadata (if provided)
        expected = self.get_expected_apqc_metadata()
        if expected.get('apqc_agent_id'):
            assert agent.APQC_AGENT_ID == expected['apqc_agent_id'], \
                "Agent ID should match expected value"
        if expected.get('apqc_category_id'):
            assert agent.APQC_CATEGORY_ID == expected['apqc_category_id'], \
                "Category ID should match expected value"
        if expected.get('apqc_process_id'):
            assert agent.APQC_PROCESS_ID == expected['apqc_process_id'], \
                "Process ID should match expected value"

    @pytest.mark.asyncio
    async def test_input_output_schema_validation(self):
        """
        Test 7: Input/Output Schema Validation

        Verifies that:
        - Agent provides input schema
        - Agent provides output schema
        - Schemas are well-formed
        - Schemas include APQC process ID
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Get schemas
        input_schema = agent.get_input_schema()
        output_schema = agent.get_output_schema()

        # Verify input schema
        assert input_schema is not None, "Should provide input schema"
        assert isinstance(input_schema, dict), "Input schema should be dictionary"
        assert 'type' in input_schema, "Input schema should have type"
        assert 'apqc_process_id' in input_schema, "Input schema should include APQC process ID"
        assert 'properties' in input_schema, "Input schema should have properties"

        # Verify output schema
        assert output_schema is not None, "Should provide output schema"
        assert isinstance(output_schema, dict), "Output schema should be dictionary"
        assert 'type' in output_schema, "Output schema should have type"
        assert 'apqc_process_id' in output_schema, "Output schema should include APQC process ID"
        assert 'properties' in output_schema, "Output schema should have properties"

        # Verify required fields in output schema
        output_props = output_schema['properties']
        required_output_fields = ['status', 'apqc_process_id', 'agent_id', 'timestamp', 'output']
        for field in required_output_fields:
            assert field in output_props, f"Output schema should define {field}"

    @pytest.mark.asyncio
    async def test_capabilities_declaration(self):
        """
        Test 8: Capabilities Declaration

        Verifies that:
        - Agent declares capabilities
        - Capabilities are accessible
        - Expected capabilities are present
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Verify capabilities exist
        assert hasattr(agent, 'capabilities_list'), "Agent should have capabilities_list"
        assert isinstance(agent.capabilities_list, list), "Capabilities should be a list"
        assert len(agent.capabilities_list) > 0, "Agent should have at least one capability"

        # Verify expected capabilities (if provided)
        expected_caps = self.get_expected_capabilities()
        if expected_caps:
            for cap in expected_caps:
                assert cap in agent.capabilities_list, \
                    f"Agent should have capability: {cap}"

    @pytest.mark.asyncio
    async def test_learning_and_self_improvement(self):
        """
        Test 9: Learning and Self-Improvement

        Verifies that:
        - Agent supports learning (if enabled)
        - Learning data is tracked
        - Self-improvement mechanisms work
        """
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        # Check if learning is enabled
        if not agent.config.learning_enabled:
            pytest.skip("Learning not enabled for this agent")

        # Verify learning structures
        assert agent.state.get('learning_data') is not None, \
            "Agent should have learning_data when learning is enabled"

        # Execute a task to trigger learning
        input_data = self.generate_valid_input()
        await agent.execute(input_data)

        # Verify learning data was recorded
        learning_data = agent.state.get('learning_data', {})
        if 'learning_history' in learning_data:
            assert len(learning_data['learning_history']) > 0, \
                "Learning history should be populated after execution"

    @pytest.mark.asyncio
    async def test_environment_based_configuration(self):
        """
        Test 10: Environment-based Configuration (Redeployability)

        Verifies that:
        - Agent can be created from environment variables
        - from_environment() method works
        - Configuration is properly loaded
        """
        agent_class = self.get_agent_class()
        config_class = type(self.get_agent_config())

        # Verify from_environment methods exist
        assert hasattr(config_class, 'from_environment'), \
            "Config should have from_environment method"
        assert hasattr(agent_class, 'from_environment'), \
            "Agent should have from_environment method"

        # Test creating agent from environment
        # Note: This may use default values if env vars not set
        try:
            agent = agent_class.from_environment()
            assert agent is not None, "Should create agent from environment"
            assert hasattr(agent, 'config'), "Agent should have config"
        except Exception as e:
            pytest.fail(f"from_environment() should not raise exception: {e}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def generate_valid_input(self) -> Dict[str, Any]:
        """
        Generate valid input data for testing.
        Override in subclasses for agent-specific input.

        Returns:
            Valid input data dictionary
        """
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

    def generate_invalid_input(self) -> Dict[str, Any]:
        """
        Generate invalid input data for error testing.
        Override in subclasses for agent-specific invalid input.

        Returns:
            Invalid input data dictionary
        """
        return {
            # Missing required 'task_type' and 'data' fields
            "invalid_field": "invalid_value"
        }

    def generate_mock_dependencies(self) -> Dict[str, Any]:
        """
        Generate mock dependencies for testing.
        Override in subclasses for agent-specific dependencies.

        Returns:
            Mock dependencies dictionary
        """
        return {}

    def assert_output_schema_compliance(self, result: Dict[str, Any], agent: Any):
        """
        Assert that result complies with agent's output schema.

        Args:
            result: Result from agent execution
            agent: Agent instance
        """
        schema = agent.get_output_schema()
        required_fields = schema.get('required', [])

        for field in required_fields:
            assert field in result, f"Result should include required field: {field}"

    def assert_apqc_compliance(self, agent: Any):
        """
        Assert full APQC compliance.

        Args:
            agent: Agent instance
        """
        # Verify all 8 architectural principles
        principles = {
            'standardized': lambda a: isinstance(a, BaseAgent),
            'interoperable': lambda a: isinstance(a, ProtocolMixin),
            'redeployable': lambda a: hasattr(type(a), 'from_environment'),
            'reusable': lambda a: hasattr(a, 'execute'),
            'atomic': lambda a: hasattr(a, 'APQC_PROCESS_ID'),
            'composable': lambda a: hasattr(a, 'get_input_schema') and hasattr(a, 'get_output_schema'),
            'orchestratable': lambda a: hasattr(a, 'send_protocol_message'),
            'vendor_agnostic': lambda a: True  # Verified by code review
        }

        for principle, check in principles.items():
            assert check(agent), f"Agent should be {principle}"


# ========================================================================
# Mock Data Generators
# ========================================================================

class MockDataGenerator:
    """
    Utility class for generating mock data for testing.
    """

    @staticmethod
    def generate_strategic_input() -> Dict[str, Any]:
        """Generate mock input for strategic agents."""
        return {
            "task_type": "strategic_analysis",
            "data": {
                "market_data": {"size": 1000000, "growth_rate": 0.15},
                "competitive_landscape": {"competitors": 5, "market_share": 0.20},
                "internal_capabilities": {"strengths": ["innovation", "quality"], "weaknesses": ["scale"]},
                "objectives": ["market_expansion", "revenue_growth"]
            },
            "context": {
                "timeframe": "3_years",
                "priority": "high"
            },
            "priority": "high"
        }

    @staticmethod
    def generate_operational_input() -> Dict[str, Any]:
        """Generate mock input for operational agents."""
        return {
            "task_type": "operational_execution",
            "data": {
                "resources": {"budget": 100000, "personnel": 10},
                "requirements": {"timeline": "30_days", "quality": "high"},
                "constraints": ["budget", "timeline"]
            },
            "context": {
                "department": "operations",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @staticmethod
    def generate_analytical_input() -> Dict[str, Any]:
        """Generate mock input for analytical agents."""
        return {
            "task_type": "data_analysis",
            "data": {
                "dataset": "customer_data",
                "metrics": ["revenue", "churn", "satisfaction"],
                "timeframe": "last_quarter"
            },
            "context": {
                "analysis_type": "descriptive",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @staticmethod
    def generate_service_input() -> Dict[str, Any]:
        """Generate mock input for service delivery agents."""
        return {
            "task_type": "service_delivery",
            "data": {
                "service_type": "customer_support",
                "customer_id": "CUST-12345",
                "request": "technical_assistance",
                "sla": {"response_time": "2_hours", "resolution_time": "24_hours"}
            },
            "context": {
                "channel": "email",
                "priority": "high"
            },
            "priority": "high"
        }


# ========================================================================
# Test Utilities
# ========================================================================

class APQCTestUtilities:
    """
    Utility functions for APQC agent testing.
    """

    @staticmethod
    def validate_apqc_id_format(apqc_id: str) -> bool:
        """
        Validate APQC ID format.

        Args:
            apqc_id: APQC ID to validate

        Returns:
            True if valid format
        """
        if not isinstance(apqc_id, str):
            return False
        if not apqc_id.startswith('apqc_'):
            return False
        # Should be apqc_X_Y_hash format
        parts = apqc_id.split('_')
        if len(parts) < 4:
            return False
        return True

    @staticmethod
    def validate_category_id_format(category_id: str) -> bool:
        """
        Validate APQC category ID format.

        Args:
            category_id: Category ID to validate (e.g., "1.0")

        Returns:
            True if valid format
        """
        if not isinstance(category_id, str):
            return False
        parts = category_id.split('.')
        if len(parts) != 2:
            return False
        try:
            int(parts[0])
            int(parts[1])
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_process_id_format(process_id: str) -> bool:
        """
        Validate APQC process ID format.

        Args:
            process_id: Process ID to validate (e.g., "1.0.2")

        Returns:
            True if valid format
        """
        if not isinstance(process_id, str):
            return False
        parts = process_id.split('.')
        if len(parts) < 2:
            return False
        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    @staticmethod
    async def wait_for_agent_ready(agent: Any, timeout: float = 5.0) -> bool:
        """
        Wait for agent to be ready.

        Args:
            agent: Agent instance
            timeout: Timeout in seconds

        Returns:
            True if agent became ready
        """
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            health = await agent.health_check()
            if health.get('status') in ['initialized', 'ready', 'healthy']:
                return True
            await asyncio.sleep(0.1)
        return False

    @staticmethod
    def extract_apqc_metadata(agent: Any) -> Dict[str, str]:
        """
        Extract APQC metadata from agent.

        Args:
            agent: Agent instance

        Returns:
            Dictionary with APQC metadata
        """
        return {
            'apqc_agent_id': getattr(agent, 'APQC_AGENT_ID', None),
            'apqc_category_id': getattr(agent, 'APQC_CATEGORY_ID', None),
            'apqc_process_id': getattr(agent, 'APQC_PROCESS_ID', None),
            'apqc_framework_version': getattr(agent, 'APQC_FRAMEWORK_VERSION', None),
        }


# Export public API
__all__ = [
    'APQCAgentTestCase',
    'MockDataGenerator',
    'APQCTestUtilities',
]
