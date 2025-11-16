"""
Bronze Certification Test Suite
Core protocols: A2A (Agent-to-Agent Communication)

Bronze certification validates:
- Basic A2A message conformance
- Required field validation
- Message type support
- Basic interoperability

Required pass rate: 80%
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
)
from .validators import A2AValidator


class A2ASchemaConformanceTest(ComplianceTestCase):
    """Test A2A message conforms to JSON schema"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-001",
            test_name="A2A Schema Conformance",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Create sample message
        message = self.validator.create_sample_message()

        # Validate against schema
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


class A2ARequiredFieldsTest(ComplianceTestCase):
    """Test A2A message contains all required fields"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-002",
            test_name="A2A Required Fields",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()

        # Check required fields
        required_fields = [
            "envelope",
            "envelope.protocol",
            "envelope.version",
            "envelope.message_id",
            "envelope.from_agent",
            "envelope.to_agent",
            "envelope.timestamp",
            "envelope.message_type",
            "payload",
            "payload.content"
        ]

        is_valid, missing = self.validator.validate_required_fields(message, required_fields)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Missing required fields: {', '.join(missing)}"
            )


class A2AEnvelopeValidationTest(ComplianceTestCase):
    """Test A2A envelope structure and content"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-003",
            test_name="A2A Envelope Validation",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, errors = self.validator.validate_envelope(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Envelope validation errors: {'; '.join(errors)}"
            )


class A2APayloadValidationTest(ComplianceTestCase):
    """Test A2A payload structure"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-004",
            test_name="A2A Payload Validation",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, errors = self.validator.validate_payload(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Payload validation errors: {'; '.join(errors)}"
            )


class A2AMessageTypesTest(ComplianceTestCase):
    """Test A2A supports all required message types"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-005",
            test_name="A2A Message Types Support",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Test key message types
        test_types = ["request", "response", "task_assignment", "status_update", "error"]
        failed_types = []

        for msg_type in test_types:
            message = self.validator.create_sample_message()
            message['envelope']['message_type'] = msg_type

            is_valid, error = self.validator.validate_message(message)
            if not is_valid:
                failed_types.append(msg_type)

        duration_ms = (time.perf_counter() - start) * 1000

        if len(failed_types) == 0:
            return self._create_result(
                TestResult.PASSED,
                duration_ms,
                details={"tested_types": test_types}
            )
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Failed message types: {', '.join(failed_types)}"
            )


class A2AInvalidMessageTest(ComplianceTestCase):
    """Test A2A validator rejects invalid messages"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-006",
            test_name="A2A Invalid Message Rejection",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Test with missing envelope
        invalid_message = {"payload": {"content": "test"}}
        is_valid, _ = self.validator.validate_message(invalid_message)

        duration_ms = (time.perf_counter() - start) * 1000

        # Should be invalid
        if not is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="Validator should reject message without envelope"
            )


class A2ATimestampFormatTest(ComplianceTestCase):
    """Test A2A timestamp is in ISO 8601 format"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-007",
            test_name="A2A Timestamp Format",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        timestamp = message['envelope']['timestamp']

        # Validate timestamp format
        is_valid = self.validator._is_valid_iso8601(timestamp)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Invalid timestamp format: {timestamp}"
            )


class A2AMessageIDFormatTest(ComplianceTestCase):
    """Test A2A message_id is valid UUID"""

    def __init__(self):
        super().__init__(
            test_id="BRONZE-A2A-008",
            test_name="A2A Message ID Format",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = A2AValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        message_id = message['envelope']['message_id']

        # Validate UUID format
        is_valid = self.validator._is_valid_uuid(message_id)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Invalid message_id UUID format: {message_id}"
            )


# Pytest integration
class TestBronzeCertification:
    """Bronze certification test suite for pytest"""

    @pytest.fixture(scope="class")
    def test_suite(self):
        """Create and populate test suite"""
        suite = ComplianceTestSuite("Bronze Certification", CertificationLevel.BRONZE)

        # Add all test cases
        suite.add_test(A2ASchemaConformanceTest())
        suite.add_test(A2ARequiredFieldsTest())
        suite.add_test(A2AEnvelopeValidationTest())
        suite.add_test(A2APayloadValidationTest())
        suite.add_test(A2AMessageTypesTest())
        suite.add_test(A2AInvalidMessageTest())
        suite.add_test(A2ATimestampFormatTest())
        suite.add_test(A2AMessageIDFormatTest())

        return suite

    def test_bronze_certification(self, test_suite):
        """Run all Bronze certification tests"""
        results = test_suite.run_all()

        # Count results
        passed = sum(1 for r in results if r.result == TestResult.PASSED)
        failed = sum(1 for r in results if r.result == TestResult.FAILED)
        total = len(results)

        # Print results
        print(f"\n{'='*60}")
        print(f"BRONZE CERTIFICATION RESULTS")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {(passed/total)*100:.1f}%")
        print(f"{'='*60}\n")

        # Print failed tests
        if failed > 0:
            print("FAILED TESTS:")
            for result in results:
                if result.result == TestResult.FAILED:
                    print(f"  - {result.test_name}: {result.error_message}")
            print()

        # Create protocol compliance result
        protocol_result = ProtocolComplianceResult(
            protocol_name="A2A",
            protocol_version="2.0.0",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=0,
            errors=0,
            test_results=results
        )

        # Assert minimum pass rate (80% for Bronze)
        assert protocol_result.pass_rate >= 80.0, \
            f"Bronze certification requires 80% pass rate, got {protocol_result.pass_rate:.1f}%"


if __name__ == "__main__":
    # Run tests directly
    suite = ComplianceTestSuite("Bronze Certification", CertificationLevel.BRONZE)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(A2ARequiredFieldsTest())
    suite.add_test(A2AEnvelopeValidationTest())
    suite.add_test(A2APayloadValidationTest())
    suite.add_test(A2AMessageTypesTest())
    suite.add_test(A2AInvalidMessageTest())
    suite.add_test(A2ATimestampFormatTest())
    suite.add_test(A2AMessageIDFormatTest())

    results = suite.run_all()

    # Print results
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    print(f"\nBronze Certification: {passed}/{len(results)} tests passed")
