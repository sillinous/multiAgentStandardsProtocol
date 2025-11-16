"""
Platinum Certification Test Suite
All Protocols: A2A + ASP + TAP + ADP + CIP (Cognitive Interoperability)

Platinum certification validates:
- All Gold requirements
- CIP cognitive reasoning capabilities
- Advanced security validation
- Comprehensive interoperability
- Stringent performance requirements

Required pass rate: 95%
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
    SecurityValidator,
)
from .validators import (
    A2AValidator,
    ASPValidator,
    TAPValidator,
    ADPValidator,
    CIPValidator,
)
from .bronze_certification import A2ASchemaConformanceTest
from .silver_certification import ASPSchemaConformanceTest
from .gold_certification import (
    TAPSchemaConformanceTest,
    ADPSchemaConformanceTest,
    MessageLatencyBenchmarkTest,
)


class CIPSchemaConformanceTest(ComplianceTestCase):
    """Test CIP message conforms to JSON schema"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-CIP-001",
            test_name="CIP Schema Conformance",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = CIPValidator()

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


class CIPReasoningRequestTest(ComplianceTestCase):
    """Test CIP reasoning request validation"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-CIP-002",
            test_name="CIP Reasoning Request",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = CIPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, errors = self.validator.validate_reasoning_request(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Reasoning request errors: {'; '.join(errors)}"
            )


class CIPReasoningTypesTest(ComplianceTestCase):
    """Test CIP supports multiple reasoning types"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-CIP-003",
            test_name="CIP Reasoning Types",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = CIPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        reasoning_types = ["deductive", "inductive", "abductive", "causal"]
        failed_types = []

        for reasoning_type in reasoning_types:
            message = self.validator.create_sample_message()
            message['reasoning_request']['reasoning_type'] = reasoning_type

            is_valid, errors = self.validator.validate_reasoning_request(message)
            if not is_valid:
                failed_types.append(reasoning_type)

        duration_ms = (time.perf_counter() - start) * 1000

        if len(failed_types) == 0:
            return self._create_result(
                TestResult.PASSED,
                duration_ms,
                details={"tested_types": reasoning_types}
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Failed reasoning types: {', '.join(failed_types)}"
            )


class CIPConfidenceLevelsTest(ComplianceTestCase):
    """Test CIP confidence level validation"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-CIP-004",
            test_name="CIP Confidence Levels",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = CIPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Create response with confidence
        message = {
            "protocol": "CIP",
            "version": "1.0.0",
            "reasoning_response": {
                "conclusion": "Market analysis is required",
                "confidence": {
                    "level": "high",
                    "score": 0.85
                }
            }
        }

        is_valid, errors = self.validator.validate_reasoning_response(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Confidence validation errors: {'; '.join(errors)}"
            )


class JWTSecurityValidationTest(ComplianceTestCase):
    """Test JWT token structure validation"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-SEC-001",
            test_name="JWT Security Validation",
            category=TestCategory.SECURITY
        )

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Valid JWT structure (header.payload.signature)
        valid_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        is_valid, error = SecurityValidator.validate_jwt_structure(valid_jwt)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"JWT validation failed: {error}"
            )


class DIDFormatValidationTest(ComplianceTestCase):
    """Test DID (Decentralized Identifier) format validation"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-SEC-002",
            test_name="DID Format Validation",
            category=TestCategory.SECURITY
        )

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Valid DID format
        valid_did = "did:example:123456789abcdefghi"
        is_valid, error = SecurityValidator.validate_did_format(valid_did)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"DID validation failed: {error}"
            )


class A2ASecurityMetadataTest(ComplianceTestCase):
    """Test A2A security metadata validation"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-SEC-003",
            test_name="A2A Security Metadata",
            category=TestCategory.SECURITY
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Create A2A message with security metadata
        message = self.validator.create_sample_message()
        message['envelope']['security'] = {
            "authentication": {
                "method": "jwt",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
            },
            "encryption": {
                "algorithm": "aes-256-gcm",
                "key_id": "key_12345"
            }
        }

        is_valid, errors = self.validator.validate_security(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Security metadata errors: {'; '.join(errors)}"
            )


class ThroughputBenchmarkTest(ComplianceTestCase):
    """Test message throughput meets performance targets"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-PERF-001",
            test_name="Message Throughput Benchmark",
            category=TestCategory.PERFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Measure throughput
        def process_message():
            message = self.validator.create_sample_message()
            self.validator.validate_message(message)

        metrics = PerformanceBenchmark.measure_throughput(process_message, duration_seconds=1.0)

        duration_ms = (time.perf_counter() - start) * 1000

        # Target: 1000 messages/second
        if metrics['ops_per_second'] >= 1000:
            return self._create_result(
                TestResult.PASSED,
                duration_ms,
                details=metrics
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Throughput {metrics['ops_per_second']:.0f} ops/s below 1000 ops/s target",
                details=metrics
            )


class ComprehensiveInteroperabilityTest(ComplianceTestCase):
    """Test comprehensive interoperability across all protocols"""

    def __init__(self):
        super().__init__(
            test_id="PLATINUM-INTER-001",
            test_name="Comprehensive Interoperability",
            category=TestCategory.INTEROPERABILITY
        )
        self.a2a_validator = A2AValidator()
        self.asp_validator = ASPValidator()
        self.tap_validator = TAPValidator()
        self.adp_validator = ADPValidator()
        self.cip_validator = CIPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Complex scenario integrating all 5 protocols
        protocols_valid = []
        errors = []

        # 1. Use ADP to discover cognitive agents
        adp_msg = self.adp_validator.create_sample_message()
        is_valid, error = self.adp_validator.validate_message(adp_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"ADP: {error}")

        # 2. Use ASP to check semantic capabilities
        asp_msg = self.asp_validator.create_sample_message()
        is_valid, error = self.asp_validator.validate_message(asp_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"ASP: {error}")

        # 3. Use A2A to send reasoning request
        a2a_msg = self.a2a_validator.create_sample_message()
        cip_request = self.cip_validator.create_sample_message()
        a2a_msg['payload']['content'] = cip_request
        is_valid, error = self.a2a_validator.validate_message(a2a_msg)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"A2A: {error}")

        # 4. Use CIP for cognitive reasoning
        is_valid, error = self.cip_validator.validate_message(cip_request)
        protocols_valid.append(is_valid)
        if not is_valid:
            errors.append(f"CIP: {error}")

        # 5. Use TAP for historical context
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
                details={"protocols_tested": ["ADP", "ASP", "A2A", "CIP", "TAP"]}
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="; ".join(errors)
            )


# Pytest integration
class TestPlatinumCertification:
    """Platinum certification test suite for pytest"""

    @pytest.fixture(scope="class")
    def test_suite(self):
        """Create and populate test suite"""
        suite = ComplianceTestSuite("Platinum Certification", CertificationLevel.PLATINUM)

        # Core protocol conformance
        suite.add_test(A2ASchemaConformanceTest())
        suite.add_test(ASPSchemaConformanceTest())
        suite.add_test(TAPSchemaConformanceTest())
        suite.add_test(ADPSchemaConformanceTest())
        suite.add_test(CIPSchemaConformanceTest())

        # CIP-specific tests
        suite.add_test(CIPReasoningRequestTest())
        suite.add_test(CIPReasoningTypesTest())
        suite.add_test(CIPConfidenceLevelsTest())

        # Security tests
        suite.add_test(JWTSecurityValidationTest())
        suite.add_test(DIDFormatValidationTest())
        suite.add_test(A2ASecurityMetadataTest())

        # Performance tests
        suite.add_test(MessageLatencyBenchmarkTest())
        suite.add_test(ThroughputBenchmarkTest())

        # Interoperability tests
        suite.add_test(ComprehensiveInteroperabilityTest())

        return suite

    def test_platinum_certification(self, test_suite):
        """Run all Platinum certification tests"""
        results = test_suite.run_all()

        passed = sum(1 for r in results if r.result == TestResult.PASSED)
        failed = sum(1 for r in results if r.result == TestResult.FAILED)
        total = len(results)

        print(f"\n{'='*60}")
        print(f"PLATINUM CERTIFICATION RESULTS")
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
        assert pass_rate >= 95.0, \
            f"Platinum certification requires 95% pass rate, got {pass_rate:.1f}%"


if __name__ == "__main__":
    suite = ComplianceTestSuite("Platinum Certification", CertificationLevel.PLATINUM)

    # Add all tests
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(ASPSchemaConformanceTest())
    suite.add_test(TAPSchemaConformanceTest())
    suite.add_test(ADPSchemaConformanceTest())
    suite.add_test(CIPSchemaConformanceTest())
    suite.add_test(CIPReasoningRequestTest())
    suite.add_test(JWTSecurityValidationTest())
    suite.add_test(DIDFormatValidationTest())
    suite.add_test(MessageLatencyBenchmarkTest())
    suite.add_test(ThroughputBenchmarkTest())
    suite.add_test(ComprehensiveInteroperabilityTest())

    results = suite.run_all()
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    print(f"\nPlatinum Certification: {passed}/{len(results)} tests passed")
