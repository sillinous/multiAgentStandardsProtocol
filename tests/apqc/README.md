# APQC Agent Testing Framework

Comprehensive testing infrastructure for all 118 APQC agents implementing the APQC Process Classification Framework v7.0.1.

## Overview

This testing framework provides production-quality tests for the complete APQC agent ecosystem, ensuring:
- ✅ All agents are properly initialized
- ✅ Execution workflows function correctly
- ✅ Health checks report accurate status
- ✅ Protocol compliance (A2A, A2P, ACP, ANP, MCP)
- ✅ APQC metadata correctness
- ✅ Input/output schema validation
- ✅ Integration across agent categories

## Framework Structure

```
tests/apqc/
├── __init__.py                                  # Package initialization
├── README.md                                    # This file
├── conftest.py                                  # Pytest fixtures and configuration
├── test_apqc_framework.py                       # Base testing framework
├── test_apqc_category_1_vision_strategy.py      # Category 1.0 tests (22 agents)
├── test_apqc_category_2_products_services.py    # Category 2.0 tests (4 agents)
├── test_apqc_category_3_market_sell.py          # Category 3.0 tests (13 agents)
└── test_apqc_categories_4_13_template.py        # Template for remaining categories
```

## Test Coverage

### Completed (39 agents)
- **Category 1.0 - Vision and Strategy**: 22 agents ✅
- **Category 2.0 - Products and Services**: 4 agents ✅
- **Category 3.0 - Market and Sell**: 13 agents ✅

### Template Available (79 agents)
- **Category 4.0 - Deliver Physical Products**: 11 agents
- **Category 5.0 - Deliver Services**: 6 agents
- **Category 6.0 - Customer Service**: 8 agents
- **Category 7.0 - Human Capital**: 11 agents
- **Category 8.0 - Information Technology**: 8 agents
- **Category 9.0 - Financial Resources**: 14 agents
- **Category 10.0 - Assets**: 12 agents
- **Category 11.0 - Risk, Compliance**: 7 agents
- **Category 12.0 - External Relationships**: 5 agents
- **Category 13.0 - Business Capabilities**: 13 agents

## Standard Test Patterns

Each agent has minimum 10 standard tests:

1. **test_agent_initialization**: Verify agent instantiation and configuration
2. **test_agent_execute_success**: Test successful execution with valid input
3. **test_agent_execute_error_handling**: Test error handling with invalid input
4. **test_agent_health_check**: Verify health check reporting
5. **test_protocol_compliance**: Validate protocol implementations
6. **test_apqc_metadata_correctness**: Verify APQC metadata
7. **test_input_output_schema_validation**: Validate schemas
8. **test_capabilities_declaration**: Verify capabilities
9. **test_learning_and_self_improvement**: Test learning features
10. **test_environment_based_configuration**: Test redeployability

## Usage

### Running Tests

```bash
# Run all APQC tests
pytest tests/apqc/ -v

# Run specific category
pytest tests/apqc/ -m apqc_category_1 -v
pytest tests/apqc/ -m apqc_category_2 -v
pytest tests/apqc/ -m apqc_category_3 -v

# Run integration tests only
pytest tests/apqc/ -m apqc_integration -v

# Run with coverage report
pytest tests/apqc/ --cov=src/superstandard/agents --cov-report=html

# Run specific test file
pytest tests/apqc/test_apqc_category_1_vision_strategy.py -v

# Run specific test class
pytest tests/apqc/test_apqc_category_1_vision_strategy.py::TestDevelopBusinessStrategyStrategicAgent -v

# Run with detailed output
pytest tests/apqc/ -vv --tb=long

# Run in parallel (requires pytest-xdist)
pytest tests/apqc/ -n auto
```

### Writing New Tests

To create tests for a new category:

1. **Copy the template**:
   ```bash
   cp tests/apqc/test_apqc_categories_4_13_template.py \
      tests/apqc/test_apqc_category_4_deliver_products.py
   ```

2. **Customize for your category**:
   ```python
   import pytest
   from test_apqc_framework import APQCAgentTestCase

   @pytest.mark.apqc
   @pytest.mark.apqc_category_4
   class TestYourAgent(APQCAgentTestCase):
       def get_agent_class(self):
           from superstandard.agents.your.path import YourAgent
           return YourAgent

       def get_agent_config(self):
           from superstandard.agents.your.path import YourAgentConfig
           return YourAgentConfig()

       def get_expected_apqc_metadata(self):
           return {
               "apqc_category_id": "4.0",
               "apqc_process_id": "4.1",
               "apqc_framework_version": "7.0.1"
           }

       def generate_valid_input(self):
           return {
               "task_type": "your_task",
               "data": { ... },
               "priority": "high"
           }
   ```

3. **Add category-specific tests**:
   ```python
   @pytest.mark.asyncio
   async def test_category_specific_feature(self):
       """Test category-specific functionality."""
       agent = self.get_agent_class()(self.get_agent_config())
       # Your test logic here
   ```

4. **Add integration tests**:
   ```python
   @pytest.mark.apqc_integration
   class TestCategory4Integration:
       @pytest.mark.asyncio
       async def test_workflow(self):
           """Test multi-agent workflow."""
           # Integration test logic
   ```

## Base Test Class

All APQC agent tests inherit from `APQCAgentTestCase`:

```python
from test_apqc_framework import APQCAgentTestCase

class TestMyAgent(APQCAgentTestCase):
    # Required methods
    def get_agent_class(self): ...
    def get_agent_config(self): ...

    # Optional overrides
    def get_expected_apqc_metadata(self): ...
    def get_expected_capabilities(self): ...
    def generate_valid_input(self): ...
    def generate_invalid_input(self): ...
```

## Test Fixtures

Common fixtures available in `conftest.py`:

### Data Fixtures
- `base_input_data`: Generic input structure
- `strategic_input_data`: Strategic agent input
- `operational_input_data`: Operational agent input
- `sales_marketing_input_data`: Sales/marketing input
- `service_delivery_input_data`: Service delivery input
- `financial_input_data`: Financial agent input
- `hr_input_data`: HR agent input

### Mock Fixtures
- `mock_knowledge_graph`: Mock knowledge graph service
- `mock_vector_db`: Mock vector database
- `mock_event_bus`: Mock event bus
- `mock_external_api`: Mock external API
- `mock_llm_service`: Mock LLM service

### Factory Fixtures
- `create_test_agent_config`: Create test agent configurations
- `create_mock_agent`: Create mock agent instances
- `assert_apqc_compliance`: Assert APQC compliance

## Test Utilities

### MockDataGenerator

Generate mock data for testing:

```python
from test_apqc_framework import MockDataGenerator

# Strategic input
input_data = MockDataGenerator.generate_strategic_input()

# Operational input
input_data = MockDataGenerator.generate_operational_input()

# Analytical input
input_data = MockDataGenerator.generate_analytical_input()

# Service input
input_data = MockDataGenerator.generate_service_input()
```

### APQCTestUtilities

Utility functions for APQC testing:

```python
from test_apqc_framework import APQCTestUtilities

# Validate APQC ID format
is_valid = APQCTestUtilities.validate_apqc_id_format("apqc_1_0_hash")

# Validate category ID format
is_valid = APQCTestUtilities.validate_category_id_format("1.0")

# Validate process ID format
is_valid = APQCTestUtilities.validate_process_id_format("1.0.2")

# Wait for agent to be ready
ready = await APQCTestUtilities.wait_for_agent_ready(agent)

# Extract APQC metadata
metadata = APQCTestUtilities.extract_apqc_metadata(agent)
```

## Pytest Markers

Use markers to organize and filter tests:

```python
@pytest.mark.apqc                    # All APQC tests
@pytest.mark.apqc_category_1         # Category 1 tests
@pytest.mark.apqc_category_2         # Category 2 tests
@pytest.mark.apqc_integration        # Integration tests
@pytest.mark.slow                    # Slow-running tests
```

Run specific markers:
```bash
pytest -m "apqc_category_1"
pytest -m "apqc_integration"
pytest -m "not slow"
```

## Integration Tests

Integration tests validate workflows across multiple agents:

```python
@pytest.mark.apqc_integration
class TestCategoryIntegration:
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test workflow across multiple agents."""
        # Create agents
        agent1 = Agent1(Config1())
        agent2 = Agent2(Config2())
        agent3 = Agent3(Config3())

        # Execute workflow
        result1 = await agent1.execute(input_data)
        result2 = await agent2.execute(result1['output'])
        result3 = await agent3.execute(result2['output'])

        # Verify workflow completion
        assert result3['status'] == 'completed'
```

## Performance Testing

Performance tests verify scalability and efficiency:

```python
@pytest.mark.slow
class TestPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Test concurrent agent execution."""
        import asyncio

        agents = [Agent(Config()) for _ in range(10)]
        tasks = [agent.execute(input_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r['status'] == 'completed' for r in results)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: APQC Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run APQC tests
        run: |
          pytest tests/apqc/ -v --cov=src/superstandard/agents
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

1. **Use the base test class**: Always inherit from `APQCAgentTestCase`
2. **Follow naming conventions**: `Test{AgentName}` for test classes
3. **Include docstrings**: Document what each test validates
4. **Use fixtures**: Leverage fixtures for common test data
5. **Test happy and sad paths**: Include both success and error cases
6. **Keep tests focused**: One test per specific behavior
7. **Use async/await**: All agent tests should be async
8. **Mock external dependencies**: Don't make real API calls
9. **Assert multiple conditions**: Verify comprehensive behavior
10. **Add integration tests**: Test agent collaboration

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/project/src"
```

**Async Test Errors**:
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Coverage Not Working**:
```bash
# Install pytest-cov
pip install pytest-cov
```

## Contributing

When adding new APQC agents:

1. Create agent implementation
2. Create test class inheriting from `APQCAgentTestCase`
3. Implement all required methods
4. Add category-specific tests
5. Add integration tests if applicable
6. Update this README with new agent count
7. Run tests: `pytest tests/apqc/ -v`
8. Ensure coverage > 80%

## Reference

- **APQC Framework**: v7.0.1
- **Architectural Principles**: 8 (Standardized, Interoperable, Redeployable, Reusable, Atomic, Composable, Orchestratable, Vendor Agnostic)
- **Protocols**: 5 (A2A, A2P, ACP, ANP, MCP)
- **Total Agents**: 118
- **Test Coverage**: 39/118 complete, 79/118 template available

## Support

For questions or issues:
- Review agent audit report: `APQC_AGENTS_AUDIT_REPORT.md`
- Check agent implementation: `src/superstandard/agents/`
- Review base agent: `src/superstandard/agents/base/base_agent.py`
- Check protocols: `src/superstandard/agents/base/protocols.py`

---

**Version**: 1.0.0
**Framework**: APQC 7.0.1
**Last Updated**: 2025-11-16
