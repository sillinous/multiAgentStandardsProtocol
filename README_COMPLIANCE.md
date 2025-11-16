# SuperStandard Compliance Test Suite (SCTS)

A comprehensive testing framework for validating protocol compliance in the SuperStandard multi-agent ecosystem.

## Overview

The SuperStandard Compliance Test Suite (SCTS) provides a robust framework for testing agent implementations against formal protocol specifications. It supports four certification tiers (Bronze, Silver, Gold, Platinum) and validates compliance across five core protocols.

## Supported Protocols

| Protocol | Version | Description |
|----------|---------|-------------|
| **A2A** | v2.0 | Agent-to-Agent Protocol - Direct agent communication |
| **ASP** | v1.0 | Agent Semantic Protocol - Semantic interoperability |
| **TAP** | v1.0 | Temporal Agent Protocol - Time-travel queries |
| **ADP** | v1.0 | Agent Discovery Protocol - Agent/service discovery |
| **CIP** | v1.0 | Cognitive Interoperability Protocol - Reasoning capabilities |

## Certification Levels

### 🥉 Bronze Certification
**Required Pass Rate:** 80%

**Protocols Tested:** A2A

**Focus Areas:**
- Basic A2A message conformance
- Required field validation
- Message type support
- Protocol version compliance

**Use Case:** Entry-level certification for agents requiring basic communication capabilities.

---

### 🥈 Silver Certification
**Required Pass Rate:** 85%

**Protocols Tested:** A2A + ASP

**Focus Areas:**
- All Bronze requirements
- Semantic capability declaration
- Ontology understanding
- Cross-protocol integration (A2A + ASP)

**Use Case:** Agents requiring semantic interoperability and capability discovery.

---

### 🥇 Gold Certification
**Required Pass Rate:** 90%

**Protocols Tested:** A2A + ASP + TAP + ADP

**Focus Areas:**
- All Silver requirements
- Temporal query capabilities
- Agent discovery mechanisms
- Multi-protocol integration
- Performance benchmarks (latency)

**Use Case:** Enterprise-grade agents requiring temporal reasoning and discovery.

---

### 💎 Platinum Certification
**Required Pass Rate:** 95%

**Protocols Tested:** A2A + ASP + TAP + ADP + CIP

**Focus Areas:**
- All Gold requirements
- Cognitive reasoning capabilities
- Advanced security validation (JWT, DID)
- Comprehensive interoperability
- Stringent performance requirements (throughput)

**Use Case:** Advanced agents with cognitive reasoning and maximum interoperability.

## Installation

### Prerequisites

```bash
# Python 3.9 or higher
python --version

# Install dependencies
pip install pytest jsonschema
```

### Setup

```bash
# Clone repository
git clone <repository-url>
cd multiAgentStandardsProtocol

# Install in development mode (optional)
pip install -e .
```

## Quick Start

### Running Tests with Pytest

```bash
# Run Bronze certification
pytest tests/compliance/bronze_certification.py -v

# Run Silver certification
pytest tests/compliance/silver_certification.py -v

# Run Gold certification
pytest tests/compliance/gold_certification.py -v

# Run Platinum certification
pytest tests/compliance/platinum_certification.py -v

# Run all compliance tests
pytest tests/compliance/ -v
```

### Using the CLI Tool

```bash
# Test Bronze certification
python src/superstandard/cli_compliance.py test \
  --level bronze \
  --agent apqc_1_0_strategic \
  --name "Strategic Planning Agent"

# Test Platinum certification with report
python src/superstandard/cli_compliance.py test \
  --level platinum \
  --agent apqc_1_0_strategic \
  --name "Strategic Agent" \
  --output compliance_report.md \
  --format markdown

# Generate reports in both JSON and Markdown
python src/superstandard/cli_compliance.py test \
  --level gold \
  --agent test_agent \
  --format both \
  --output results

# List available certifications
python src/superstandard/cli_compliance.py list
```

## Test Categories

### 1. Protocol Conformance Tests
Validate messages against JSON Schema specifications.

**Example:**
```python
from compliance.validators import A2AValidator

validator = A2AValidator()
message = validator.create_sample_message()
is_valid, error = validator.validate_message(message)
```

### 2. Interoperability Tests
Test cross-protocol integration scenarios.

**Example:**
- A2A carrying ASP semantic declarations
- A2A + TAP temporal queries
- Multi-protocol workflows

### 3. Performance Benchmarks
Measure latency and throughput.

**Targets:**
- Message latency: <100ms (95th percentile)
- Throughput: >1000 messages/second

**Example:**
```python
from compliance.framework import PerformanceBenchmark

metrics = PerformanceBenchmark.measure_latency(validate_func, iterations=100)
print(f"P95 Latency: {metrics['p95_ms']:.2f}ms")
```

### 4. Security Validation
Basic security checks for authentication and encryption.

**Validations:**
- JWT token structure
- DID format (W3C spec)
- Security metadata in messages

## Framework Architecture

```
tests/compliance/
├── __init__.py                    # Package initialization
├── framework.py                   # Core test framework
├── report_generator.py            # Report generation utilities
├── bronze_certification.py        # Bronze tier tests
├── silver_certification.py        # Silver tier tests
├── gold_certification.py          # Gold tier tests
├── platinum_certification.py      # Platinum tier tests
└── validators/
    ├── __init__.py
    ├── a2a_validator.py          # A2A protocol validator
    ├── asp_validator.py          # ASP protocol validator
    ├── tap_validator.py          # TAP protocol validator
    ├── adp_validator.py          # ADP protocol validator
    └── cip_validator.py          # CIP protocol validator
```

## Creating Custom Tests

### Step 1: Define a Test Case

```python
from compliance.framework import ComplianceTestCase, TestCategory, TestResult
import time

class MyCustomTest(ComplianceTestCase):
    def __init__(self):
        super().__init__(
            test_id="CUSTOM-001",
            test_name="My Custom Test",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Your test logic here
        is_valid = True  # Replace with actual validation

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="Test failed"
            )
```

### Step 2: Add to Test Suite

```python
from compliance.framework import ComplianceTestSuite, CertificationLevel

suite = ComplianceTestSuite("Custom Suite", CertificationLevel.BRONZE)
suite.add_test(MyCustomTest())

results = suite.run_all()
```

## Generating Reports

### Programmatic Report Generation

```python
from compliance.report_generator import ComplianceReportGenerator
from pathlib import Path

# Generate Markdown report
generator = ComplianceReportGenerator()
markdown = generator.generate_markdown_report(report, Path("report.md"))

# Generate JSON report
json_report = generator.generate_json_report(report, Path("report.json"))

# Generate HTML badge
badge = generator.generate_html_badge(report)
```

### Report Formats

#### JSON Report
```json
{
  "report_id": "uuid",
  "agent_id": "apqc_1_0_strategic",
  "agent_name": "Strategic Agent",
  "certification_level": "platinum",
  "timestamp": "2025-11-16T...",
  "total_tests": 142,
  "tests_passed": 138,
  "tests_failed": 4,
  "pass_rate": 97.2,
  "protocols_compliant": ["A2A", "ASP", "TAP", "ADP", "CIP"],
  "certification_achieved": true
}
```

#### Markdown Report
Includes:
- Certification status badge
- Overall results table
- Protocol-by-protocol breakdown
- Detailed test results
- Failed test analysis
- Recommendations

## Performance Targets

| Metric | Target | Certification Level |
|--------|--------|---------------------|
| Message Latency (P95) | <100ms | Gold, Platinum |
| Throughput | >1000 msg/s | Platinum |
| Schema Validation | <10ms | All |

## Best Practices

### 1. Test Organization
- Group related tests in the same test suite
- Use descriptive test IDs (e.g., `BRONZE-A2A-001`)
- Keep test cases independent

### 2. Error Messages
- Provide clear, actionable error messages
- Include context (field names, expected vs actual)
- Use structured error reporting

### 3. Performance Testing
- Run performance tests in isolation
- Use consistent test environments
- Average multiple runs for stability

### 4. CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: Compliance Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install pytest jsonschema
      - run: pytest tests/compliance/bronze_certification.py
      - run: pytest tests/compliance/silver_certification.py
```

## Troubleshooting

### Common Issues

**Issue:** `FileNotFoundError: Schema file not found`
```bash
# Solution: Ensure you're running from project root
cd /path/to/multiAgentStandardsProtocol
pytest tests/compliance/
```

**Issue:** `ImportError: No module named 'compliance'`
```bash
# Solution: Add tests to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/multiAgentStandardsProtocol/tests"
```

**Issue:** Low pass rate
```bash
# Solution: Run with verbose output to see failures
pytest tests/compliance/bronze_certification.py -v -s
```

## Extending the Framework

### Adding a New Protocol Validator

```python
# tests/compliance/validators/new_protocol_validator.py
from ..framework import ProtocolValidator, get_schema_path

class NewProtocolValidator(ProtocolValidator):
    def __init__(self):
        super().__init__(get_schema_path("new_protocol"))

    def get_protocol_name(self) -> str:
        return "NEW"

    def get_protocol_version(self) -> str:
        return "1.0.0"

    # Add custom validation methods
    def validate_custom_field(self, message):
        # Implementation
        pass
```

### Adding a New Certification Level

1. Create new test file: `tests/compliance/diamond_certification.py`
2. Define test suite with appropriate tests
3. Set required pass rate
4. Update CLI tool to support new level

## API Reference

### Core Classes

#### `ProtocolValidator`
Base class for protocol validators.

**Methods:**
- `validate_message(message)` - Validate against schema
- `validate_required_fields(message, fields)` - Check required fields
- `validate_field_types(message, types)` - Validate field types

#### `ComplianceTestCase`
Base class for test cases.

**Methods:**
- `run()` - Execute test (abstract)
- `_create_result(result, duration_ms, ...)` - Create test result

#### `ComplianceTestSuite`
Container for test cases.

**Methods:**
- `add_test(test_case)` - Add test to suite
- `run_all()` - Run all tests

#### `ComplianceReport`
Compliance test report.

**Properties:**
- `pass_rate` - Overall pass percentage
- `certification_achieved` - Whether certification was achieved
- `to_dict()` - Convert to dictionary
- `to_json()` - Convert to JSON string

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution
- Additional protocol validators
- More comprehensive test coverage
- Performance optimizations
- Documentation improvements
- CI/CD integrations

## License

[Specify License]

## Support

- **Documentation:** See this README and inline code documentation
- **Issues:** Submit issues on GitHub
- **Discussions:** Join our community forum

## Roadmap

- [ ] Additional protocols (ANP, MCP, BAP, CAIP, CAP)
- [ ] Real-time test monitoring dashboard
- [ ] Historical compliance tracking
- [ ] Automated remediation suggestions
- [ ] Integration with agent registries
- [ ] Performance regression detection

## Acknowledgments

Built with the SuperStandard multi-agent protocol specifications and the JSON Schema validation framework.

---

**Version:** 1.0.0
**Last Updated:** 2025-11-16
**Maintained by:** SuperStandard Team
