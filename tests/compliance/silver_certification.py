"""
Silver Certification Test Suite
Protocols: A2A + ASP (Semantic Discovery)

Silver certification validates:
- All Bronze requirements
- ASP semantic capabilities
- Semantic discovery and alignment
- Cross-protocol integration

Required pass rate: 85%
"""

import pytest
import time
from typing import Dict, Any, List

from .framework import (
    CertificationLevel,
    TestCategory,
    TestResult,
    TestCaseResult,
    ProtocolComplianceResult,
    ComplianceTestCase,
    ComplianceTestSuite,
)
from .validators import A2AValidator, ASPValidator
from .bronze_certification import (
    A2ASchemaConformanceTest,
    A2ARequiredFieldsTest,
    A2AEnvelopeValidationTest,
    A2APayloadValidationTest,
)


class ASPSchemaConformanceTest(ComplianceTestCase):
    """Test ASP message conforms to JSON schema"""

    def __init__(self):
        super().__init__(
            test_id="SILVER-ASP-001",
            test_name="ASP Schema Conformance",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = ASPValidator()

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


class ASPSemanticDeclarationTest(ComplianceTestCase):
    """Test ASP semantic declaration structure"""

    def __init__(self):
        super().__init__(
            test_id="SILVER-ASP-002",
            test_name="ASP Semantic Declaration",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = ASPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        message = self.validator.create_sample_message()
        is_valid, errors = self.validator.validate_semantic_declaration(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Semantic declaration errors: {'; '.join(errors)}"
            )


class ASPSemanticQueryTest(ComplianceTestCase):
    """Test ASP semantic query validation"""

    def __init__(self):
        super().__init__(
            test_id="SILVER-ASP-003",
            test_name="ASP Semantic Query",
            category=TestCategory.PROTOCOL_CONFORMANCE
        )
        self.validator = ASPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Create message with semantic query
        message = self.validator.create_sample_message()
        message['semantic_query'] = {
            "query_type": "capability_match",
            "query": {"capabilities": ["strategic_planning"]}
        }

        is_valid, errors = self.validator.validate_semantic_query(message)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message=f"Semantic query errors: {'; '.join(errors)}"
            )


class A2AASPInteroperabilityTest(ComplianceTestCase):
    """Test A2A can carry ASP semantic discovery payload"""

    def __init__(self):
        super().__init__(
            test_id="SILVER-INTER-001",
            test_name="A2A + ASP Interoperability",
            category=TestCategory.INTEROPERABILITY
        )
        self.a2a_validator = A2AValidator()
        self.asp_validator = ASPValidator()

    def run(self) -> TestCaseResult:
        start = time.perf_counter()

        # Create A2A message carrying ASP semantic declaration
        a2a_message = self.a2a_validator.create_sample_message()
        asp_declaration = self.asp_validator.create_sample_message()

        # Embed ASP in A2A payload
        a2a_message['payload']['content'] = asp_declaration
        a2a_message['envelope']['message_type'] = 'discovery'

        # Validate A2A message
        is_valid_a2a, error_a2a = self.a2a_validator.validate_message(a2a_message)

        # Validate embedded ASP content
        asp_content = a2a_message['payload']['content']
        is_valid_asp, error_asp = self.asp_validator.validate_message(asp_content)

        duration_ms = (time.perf_counter() - start) * 1000

        if is_valid_a2a and is_valid_asp:
            return self._create_result(TestResult.PASSED, duration_ms)
        else:
            errors = []
            if not is_valid_a2a:
                errors.append(f"A2A: {error_a2a}")
            if not is_valid_asp:
                errors.append(f"ASP: {error_asp}")
            return self._create_result(
                TestResult.FAILED,
                duration_ms,
                error_message="; ".join(errors)
            )


# Pytest integration
class TestSilverCertification:
    """Silver certification test suite for pytest"""

    @pytest.fixture(scope="class")
    def test_suite(self):
        """Create and populate test suite"""
        suite = ComplianceTestSuite("Silver Certification", CertificationLevel.SILVER)

        # Add Bronze tests (A2A)
        suite.add_test(A2ASchemaConformanceTest())
        suite.add_test(A2ARequiredFieldsTest())
        suite.add_test(A2AEnvelopeValidationTest())
        suite.add_test(A2APayloadValidationTest())

        # Add Silver tests (ASP)
        suite.add_test(ASPSchemaConformanceTest())
        suite.add_test(ASPSemanticDeclarationTest())
        suite.add_test(ASPSemanticQueryTest())

        # Add interoperability tests
        suite.add_test(A2AASPInteroperabilityTest())

        return suite

    def test_silver_certification(self, test_suite):
        """Run all Silver certification tests"""
        results = test_suite.run_all()

        passed = sum(1 for r in results if r.result == TestResult.PASSED)
        failed = sum(1 for r in results if r.result == TestResult.FAILED)
        total = len(results)

        print(f"\n{'='*60}")
        print(f"SILVER CERTIFICATION RESULTS")
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
        assert pass_rate >= 85.0, \
            f"Silver certification requires 85% pass rate, got {pass_rate:.1f}%"


if __name__ == "__main__":
    suite = ComplianceTestSuite("Silver Certification", CertificationLevel.SILVER)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(ASPSchemaConformanceTest())
    suite.add_test(ASPSemanticDeclarationTest())
    suite.add_test(ASPSemanticQueryTest())
    suite.add_test(A2AASPInteroperabilityTest())

    results = suite.run_all()
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    print(f"\nSilver Certification: {passed}/{len(results)} tests passed")
