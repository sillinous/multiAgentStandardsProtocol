"""
SuperStandard Compliance Test Suite (SCTS) Framework
Core testing infrastructure for protocol compliance validation
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import jsonschema
from jsonschema import Draft202012Validator, ValidationError


class CertificationLevel(Enum):
    """Certification tiers for SuperStandard compliance"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class TestCategory(Enum):
    """Test category classifications"""
    PROTOCOL_CONFORMANCE = "protocol_conformance"
    INTEROPERABILITY = "interoperability"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestResult(Enum):
    """Test execution results"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCaseResult:
    """Individual test case result"""
    test_id: str
    test_name: str
    category: TestCategory
    result: TestResult
    duration_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ProtocolComplianceResult:
    """Protocol-specific compliance results"""
    protocol_name: str
    protocol_version: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    test_results: List[TestCaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100


@dataclass
class ComplianceReport:
    """Complete compliance test report"""
    report_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    agent_name: str = ""
    certification_level: CertificationLevel = CertificationLevel.BRONZE
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_tests: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    tests_error: int = 0
    protocols_tested: List[str] = field(default_factory=list)
    protocols_compliant: List[str] = field(default_factory=list)
    protocol_results: List[ProtocolComplianceResult] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    certification_achieved: bool = False

    @property
    def pass_rate(self) -> float:
        """Calculate overall pass rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.tests_passed / self.total_tests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        result = asdict(self)
        result['certification_level'] = self.certification_level.value
        result['pass_rate'] = self.pass_rate
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class ProtocolValidator(ABC):
    """Abstract base class for protocol validators"""

    def __init__(self, schema_path: Path):
        """
        Initialize protocol validator

        Args:
            schema_path: Path to JSON schema file
        """
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = Draft202012Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file"""
        with open(self.schema_path, 'r') as f:
            return json.load(f)

    @abstractmethod
    def get_protocol_name(self) -> str:
        """Return protocol name"""
        pass

    @abstractmethod
    def get_protocol_version(self) -> str:
        """Return protocol version"""
        pass

    def validate_message(self, message: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a message against the protocol schema

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.validator.validate(message)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def validate_required_fields(self, message: Dict[str, Any], required_fields: List[str]) -> tuple[bool, List[str]]:
        """
        Check for required fields

        Args:
            message: Message to check
            required_fields: List of required field paths (dot notation)

        Returns:
            Tuple of (all_present, missing_fields)
        """
        missing = []
        for field_path in required_fields:
            parts = field_path.split('.')
            current = message
            try:
                for part in parts:
                    current = current[part]
            except (KeyError, TypeError):
                missing.append(field_path)

        return len(missing) == 0, missing

    def validate_field_types(self, message: Dict[str, Any], field_types: Dict[str, type]) -> tuple[bool, List[str]]:
        """
        Validate field types

        Args:
            message: Message to validate
            field_types: Dict mapping field paths to expected types

        Returns:
            Tuple of (all_valid, invalid_fields)
        """
        invalid = []
        for field_path, expected_type in field_types.items():
            parts = field_path.split('.')
            current = message
            try:
                for part in parts:
                    current = current[part]
                if not isinstance(current, expected_type):
                    invalid.append(f"{field_path} (expected {expected_type.__name__}, got {type(current).__name__})")
            except (KeyError, TypeError):
                # Field doesn't exist, already caught by required_fields check
                pass

        return len(invalid) == 0, invalid


class ComplianceTestCase(ABC):
    """Abstract base class for compliance test cases"""

    def __init__(self, test_id: str, test_name: str, category: TestCategory):
        """
        Initialize test case

        Args:
            test_id: Unique test identifier
            test_name: Human-readable test name
            category: Test category
        """
        self.test_id = test_id
        self.test_name = test_name
        self.category = category

    @abstractmethod
    def run(self) -> TestCaseResult:
        """Execute the test case"""
        pass

    def _create_result(
        self,
        result: TestResult,
        duration_ms: float,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> TestCaseResult:
        """Helper to create TestCaseResult"""
        return TestCaseResult(
            test_id=self.test_id,
            test_name=self.test_name,
            category=self.category,
            result=result,
            duration_ms=duration_ms,
            error_message=error_message,
            details=details
        )


class ComplianceTestSuite:
    """Container for compliance test cases"""

    def __init__(self, name: str, certification_level: CertificationLevel):
        """
        Initialize test suite

        Args:
            name: Suite name
            certification_level: Target certification level
        """
        self.name = name
        self.certification_level = certification_level
        self.test_cases: List[ComplianceTestCase] = []

    def add_test(self, test_case: ComplianceTestCase):
        """Add a test case to the suite"""
        self.test_cases.append(test_case)

    def run_all(self) -> List[TestCaseResult]:
        """Run all test cases in the suite"""
        results = []
        for test_case in self.test_cases:
            try:
                result = test_case.run()
                results.append(result)
            except Exception as e:
                # Handle unexpected errors
                results.append(TestCaseResult(
                    test_id=test_case.test_id,
                    test_name=test_case.test_name,
                    category=test_case.category,
                    result=TestResult.ERROR,
                    duration_ms=0.0,
                    error_message=f"Unexpected error: {str(e)}"
                ))
        return results


class PerformanceBenchmark:
    """Performance benchmarking utilities"""

    @staticmethod
    def measure_latency(func, iterations: int = 100) -> Dict[str, float]:
        """
        Measure function latency

        Args:
            func: Function to measure
            iterations: Number of iterations

        Returns:
            Dict with min, max, mean, p95, p99 latencies in milliseconds
        """
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        latencies.sort()
        return {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "mean_ms": sum(latencies) / len(latencies),
            "p95_ms": latencies[int(len(latencies) * 0.95)],
            "p99_ms": latencies[int(len(latencies) * 0.99)],
            "iterations": iterations
        }

    @staticmethod
    def measure_throughput(func, duration_seconds: float = 1.0) -> Dict[str, float]:
        """
        Measure throughput

        Args:
            func: Function to measure
            duration_seconds: Test duration in seconds

        Returns:
            Dict with throughput metrics
        """
        start = time.perf_counter()
        end = start + duration_seconds
        count = 0

        while time.perf_counter() < end:
            func()
            count += 1

        actual_duration = time.perf_counter() - start
        return {
            "total_operations": count,
            "duration_seconds": actual_duration,
            "ops_per_second": count / actual_duration
        }


class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def validate_jwt_structure(token: str) -> tuple[bool, Optional[str]]:
        """
        Validate JWT token structure (basic check)

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, error_message)
        """
        parts = token.split('.')
        if len(parts) != 3:
            return False, "JWT must have 3 parts (header.payload.signature)"

        # Check each part is base64url encoded
        for i, part in enumerate(parts):
            if not part or not all(c.isalnum() or c in '-_' for c in part):
                return False, f"JWT part {i} is not valid base64url"

        return True, None

    @staticmethod
    def validate_did_format(did: str) -> tuple[bool, Optional[str]]:
        """
        Validate DID format (basic W3C DID spec check)

        Args:
            did: Decentralized Identifier string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not did.startswith("did:"):
            return False, "DID must start with 'did:'"

        parts = did.split(':')
        if len(parts) < 3:
            return False, "DID must have format 'did:method:identifier'"

        return True, None


def get_schema_path(protocol_name: str) -> Path:
    """
    Get path to protocol schema file

    Args:
        protocol_name: Protocol name (e.g., 'a2a', 'asp')

    Returns:
        Path to schema file
    """
    base_path = Path(__file__).parent.parent.parent / "specifications" / "schemas"

    # Map protocol names to schema files
    schema_files = {
        "a2a": "a2a-v2.0.schema.json",
        "asp": "asp-v1.0.schema.json",
        "tap": "tap-v1.0.schema.json",
        "adp": "adp-v1.0.schema.json",
        "cip": "cip-v1.0.schema.json",
    }

    schema_file = schema_files.get(protocol_name.lower())
    if not schema_file:
        raise ValueError(f"Unknown protocol: {protocol_name}")

    schema_path = base_path / schema_file
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    return schema_path


def create_compliance_report(
    agent_id: str,
    agent_name: str,
    certification_level: CertificationLevel,
    test_results: List[TestCaseResult],
    protocol_results: List[ProtocolComplianceResult]
) -> ComplianceReport:
    """
    Create a compliance report from test results

    Args:
        agent_id: Agent identifier
        agent_name: Agent name
        certification_level: Target certification level
        test_results: List of test case results
        protocol_results: List of protocol compliance results

    Returns:
        ComplianceReport instance
    """
    report = ComplianceReport(
        agent_id=agent_id,
        agent_name=agent_name,
        certification_level=certification_level
    )

    # Aggregate test results
    report.total_tests = len(test_results)
    report.tests_passed = sum(1 for r in test_results if r.result == TestResult.PASSED)
    report.tests_failed = sum(1 for r in test_results if r.result == TestResult.FAILED)
    report.tests_skipped = sum(1 for r in test_results if r.result == TestResult.SKIPPED)
    report.tests_error = sum(1 for r in test_results if r.result == TestResult.ERROR)

    # Protocol results
    report.protocol_results = protocol_results
    report.protocols_tested = [p.protocol_name for p in protocol_results]
    report.protocols_compliant = [
        p.protocol_name for p in protocol_results
        if p.pass_rate >= 90.0  # 90% pass rate for compliance
    ]

    # Determine certification achievement
    required_pass_rate = {
        CertificationLevel.BRONZE: 80.0,
        CertificationLevel.SILVER: 85.0,
        CertificationLevel.GOLD: 90.0,
        CertificationLevel.PLATINUM: 95.0
    }

    report.certification_achieved = report.pass_rate >= required_pass_rate[certification_level]

    # Generate recommendations
    if not report.certification_achieved:
        report.recommendations.append(
            f"Pass rate {report.pass_rate:.1f}% is below required {required_pass_rate[certification_level]:.1f}% for {certification_level.value} certification"
        )

    for protocol_result in protocol_results:
        if protocol_result.pass_rate < 90.0:
            report.recommendations.append(
                f"Improve {protocol_result.protocol_name} compliance (current: {protocol_result.pass_rate:.1f}%)"
            )

    return report
