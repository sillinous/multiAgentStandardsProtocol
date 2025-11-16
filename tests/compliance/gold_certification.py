"""
Gold Certification Test Suite
Protocols: A2A + ASP + TAP (Temporal Queries) + ADP (Discovery)

Gold certification validates:
- All Silver requirements
- TAP temporal query capabilities
- ADP agent discovery
- Multi-protocol integration
- Performance benchmarks

Required pass rate: 90%
"""

import pytest
import time
from typing import Dict, Any

from .framework import (
    CertificationLevel,
    TestCategory,
    TestResult,
    TestCaseResult,
    ProtocolComplianceResult,
    ComplianceTestCase,
    ComplianceTestSuite,
    PerformanceBenchmark,
)
from .validators import A2AValidator, ASPValidator, TAPValidator, ADPValidator
from .bronze_certification import (
    A2ASchemaConformanceTest,
    A2ARequiredFieldsTest,
)
from .silver_certification import (
    ASPSchemaConformanceTest,
    ASPSemanticDeclarationTest,
)


class TAPSchemaConformanceTest(ComplianceTestCase):
    """Test TAP message conforms to JSON schema"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-TAP-001",
            test_name="TAP Schema Conformance",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = TAPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, error = self.validator.validate_message(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Schema validation failed: {error}"
            )


class TAPTemporalQueryTest(ComplianceTestCase):
    """Test TAP temporal query validation"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-TAP-002",
            test_name="TAP Temporal Query",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = TAPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, errors = self.validator.validate_temporal_query(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Temporal query errors: {'; '.join(errors)}"
            )


class ADPSchemaConformanceTest(ComplianceTestCase):
    """Test ADP message conforms to JSON schema"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-ADP-001",
            test_name="ADP Schema Conformance",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = ADPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, error = self.validator.validate_message(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Schema validation failed: {error}"
            )


class ADPDiscoveryTest(ComplianceTestCase):
    """Test ADP discovery request/response"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-ADP-002",
            test_name="ADP Discovery Request/Response",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = ADPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Test discovery request
        request = self.validator.create_sample_message()
        is_valid_req, errors_req = self.validator.validate_discovery_request(request)

        # Test discovery response
        response = {
            "protocol": "ADP",
            "version": "1.0.0",
            "discovery_response": {
                "agents": [
                    {
                        "agent_id": "agent_1",
                        "agent_name": "Test Agent",
                        "status": "online",
                        "capabilities": ["strategic_planning"]
                    }
                ]
            }
        }
        is_valid_resp, errors_resp = self.validator.validate_discovery_response(response)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid_req and is_valid_resp:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            errors = []
            if not is_valid_req:
                errors.append(f"Request: {'; '.join(errors_req)}")
            if not is_valid_resp:
                errors.append(f"Response: {'; '.join(errors_resp)}")
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="; ".join(errors)
            )


class MessageLatencyBenchmarkTest(ComplianceTestCase):
    """Test message processing latency meets performance targets"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-PERF-001",
            test_name="Message Latency Benchmark",
            category=TestCategory.PERFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Measure validation latency
        def validate_message():
            message = self.validator.create_sample_message()
            self.validator.validate_message(message)

        metrics = PerformanceBenchmark.measure_latency(validate_message, iterations=100)

        duration_ms = (time.perf_counter() - start) * 1000

        # Target: P95 latency < 100ms
        if metrics['p95_ms'] < 100:
            return self._create_result(
                TestResult.PASSED,
                duration_ms,
                details=metrics
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"P95 latency {metrics['p95_ms']:.2f}ms exceeds 100ms target",
                details=metrics
            )


class MultiProtocolIntegrationTest(ComplianceTestCase):
    """Test integration across A2A, ASP, TAP, and ADP"""

    def __init__(self):
        super().__init__(
            test_id="GOLD-INTER-001",
            test_name="Multi-Protocol Integration",
            category=TestCategory.INTEROPERABILITY
        )
        self.a2a_validator = A2AValidator()
        self.asp_validator = ASPValidator()
        self.tap_validator = TAPValidator()
        self.adp_validator = ADPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Scenario: Use ADP to discover agents, ASP to check capabilities,
        # A2A to communicate, TAP for temporal queries

        protocols_valid = []
        errors = []

        # 1. ADP discovery
        adp_msg = self.adp_validator.create_sample_message()
        is_valid, error = self.adp_validator.validate_message(adp_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"ADP: {error}")

        # 2. ASP capability check
        asp_msg = self.asp_validator.create_sample_message()
        is_valid, error = self.asp_validator.validate_message(asp_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"ASP: {error}")

        # 3. A2A communication
        a2a_msg = self.a2a_validator.create_sample_message()
        is_valid, error = self.a2a_validator.validate_message(a2a_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"A2A: {error}")

        # 4. TAP temporal query
        tap_msg = self.tap_validator.create_sample_message()
        is_valid, error = self.tap_validator.validate_message(tap_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"TAP: {error}")

        duration_ms = (time.perf_counter() - start) * 1000

        if all(protocols_valid):
            return self._create_result(
                TestResult.PASSED,
                duration_ms,
                details={"protocols_tested": ["ADP", "ASP", "A2A", "TAP"]}
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="; ".join(errors)
            )


# Pytest integration
class TestGoldCertification:
    """Gold certification test suite for pytest"""

    @pytest.fixture(scope="class")
    def test_suite(self):
        """Create and populate test suite"""
        suite = ComplianceTestSuite("Gold Certification", CertificationLevel.GOLD)

        # Core protocol tests
        suite.add_test(A2ASchemaConformanceTest())
        suite.add_test(ASPSchemaConformanceTest())
        suite.add_test(TAPSchemaConformanceTest())
        suite.add_test(ADPSchemaConformanceTest())

        # Protocol-specific tests
        suite.add_test(TAPTemporalQueryTest())
        suite.add_test(ADPDiscoveryTest())

        # Performance tests
        suite.add_test(MessageLatencyBenchmarkTest())

        # Integration tests
        suite.add_test(MultiProtocolIntegrationTest())

        return suite

    def test_gold_certification(self, test_suite):
        """Run all Gold certification tests"""
        results = test_suite.run_all()

        passed = sum(1 for r in results if r.result == TestResult.PASSED)
        failed = sum(1 for r in results if r.result == TestResult.FAILED)
        total = len(results)

        print(f"\n{'='*60}")
        print(f"GOLD CERTIFICATION RESULTS")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {(passed/total)*100:.1f}%")
        print(f"{'='*60}\n")

        if failed > 0:
            print("FAILED TESTS:")
            for result in results:
                if result.result == TestResult.FAILED:
                    print(f"  - {result.test_name}: {result.error_message}")
            print()

        pass_rate = (passed / total) * 100
        assert pass_rate >= 90.0, \
            f"Gold certification requires 90% pass rate, got {pass_rate:.1f}%"


if __name__ == "__main__":
    suite = ComplianceTestSuite("Gold Certification", CertificationLevel.GOLD)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(TAPSchemaConformanceTest())
    suite.add_test(ADPSchemaConformanceTest())
    suite.add_test(MessageLatencyBenchmarkTest())
    suite.add_test(MultiProtocolIntegrationTest())

    results = suite.run_all()
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    print(f"\nGold Certification: {passed}/{len(results)} tests passed")
