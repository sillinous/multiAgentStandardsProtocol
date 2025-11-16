"""
Comprehensive tests for Compliance Automation & Intelligence Protocol (CAIP) v1.0
==================================================================================

Tests cover:
- Compliance checking across multiple frameworks
- Policy enforcement with different modes
- Immutable audit logging with blockchain-style chaining
- Risk assessment and threat analysis
- Evidence collection and management
- Gap analysis
- Remediation planning
- Certification status tracking

Author: SuperStandard Team
License: MIT
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.superstandard.protocols.caip_v1 import (
    # Enums
    ComplianceFramework,
    ComplianceStatus,
    ControlCategory,
    EnforcementMode,
    PolicyCategory,
    DataClassification,
    EventCategory,
    Severity,
    EventResult,
    ThreatCategory,
    RiskLevel,
    FindingType,
    FindingStatus,
    CertificationStatus,
    EvidenceType,
    AssessmentType,
    # Data Models
    TimePeriod,
    ComplianceScope,
    Control,
    Evidence,
    ComplianceGap,
    Remediation,
    Finding,
    CheckResult,
    ComplianceCheck,
    PolicySubject,
    PolicyObject,
    PolicyDecision,
    PolicyEnforcement,
    AuditActor,
    AuditResource,
    AuditLog,
    Threat,
    Vulnerability,
    MitigationRecommendation,
    RiskScope,
    RiskAssessment,
    Certification,
    # Engine and Client
    ComplianceEngine,
    CAIPClient,
    # Convenience functions
    create_compliance_check,
    create_audit_log,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def compliance_engine():
    """Create a compliance engine."""
    return ComplianceEngine()


@pytest.fixture
def caip_client():
    """Create a CAIP client."""
    return CAIPClient(agent_id="test_agent_001")


@pytest.fixture
def sample_scope():
    """Create a sample compliance scope."""
    return ComplianceScope(
        system_components=["api", "database", "logging"],
        data_categories=["PII", "financial"],
        processes=["user_registration", "payment_processing"]
    )


@pytest.fixture
def sample_control():
    """Create a sample control."""
    return Control(
        control_id="TEST_001",
        control_name="Test Access Control",
        control_category=ControlCategory.ACCESS_CONTROL,
        required_evidence=["access_logs", "policy_document"],
        description="Test control for access management",
        framework="TEST"
    )


# ============================================================================
# TESTS: DATA MODELS
# ============================================================================


def test_time_period_to_dict():
    """Test TimePeriod to_dict method."""
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    period = TimePeriod(start_date=start, end_date=end)

    result = period.to_dict()
    assert result["start_date"] == start.isoformat()
    assert result["end_date"] == end.isoformat()


def test_compliance_scope_to_dict(sample_scope):
    """Test ComplianceScope to_dict method."""
    result = sample_scope.to_dict()
    assert result["system_components"] == ["api", "database", "logging"]
    assert result["data_categories"] == ["PII", "financial"]
    assert result["processes"] == ["user_registration", "payment_processing"]


def test_control_to_dict(sample_control):
    """Test Control to_dict method."""
    result = sample_control.to_dict()
    assert result["control_id"] == "TEST_001"
    assert result["control_name"] == "Test Access Control"
    assert result["control_category"] == "access_control"


def test_evidence_creation():
    """Test Evidence creation and to_dict."""
    evidence = Evidence(
        evidence_id="ev_001",
        evidence_type=EvidenceType.LOG,
        description="Access log evidence",
        location="/logs/access.log",
        timestamp=datetime.utcnow(),
        control_id="TEST_001"
    )

    result = evidence.to_dict()
    assert result["evidence_id"] == "ev_001"
    assert result["evidence_type"] == "log"
    assert result["control_id"] == "TEST_001"


def test_compliance_gap_creation():
    """Test ComplianceGap creation."""
    gap = ComplianceGap(
        gap_id="gap_001",
        control_id="GDPR_Art17",
        severity=Severity.HIGH,
        description="Missing data deletion process",
        impact="Cannot fulfill right to erasure requests",
        remediation_required=True
    )

    result = gap.to_dict()
    assert result["gap_id"] == "gap_001"
    assert result["severity"] == "high"
    assert result["remediation_required"] is True


def test_finding_with_remediation():
    """Test Finding with remediation plan."""
    remediation = Remediation(
        required=True,
        steps=["Step 1", "Step 2"],
        responsible_party="Security Team",
        estimated_effort="2 weeks"
    )

    finding = Finding(
        finding_id="find_001",
        finding_type=FindingType.VIOLATION,
        severity=Severity.CRITICAL,
        control_id="SOC2_CC6.1",
        framework="SOC2",
        title="Access Control Violation",
        description="Insufficient access controls detected",
        remediation=remediation
    )

    assert finding.status == FindingStatus.OPEN
    assert finding.identified_at is not None

    result = finding.to_dict()
    assert result["finding_type"] == "violation"
    assert result["remediation"]["required"] is True
    assert len(result["remediation"]["steps"]) == 2


def test_check_result_calculation():
    """Test CheckResult with score calculation."""
    result = CheckResult(
        overall_status=ComplianceStatus.PARTIAL,
        compliance_score=87.5,
        controls_passed=14,
        controls_failed=2,
        controls_not_applicable=1
    )

    assert result.compliance_score == 87.5
    assert result.overall_status == ComplianceStatus.PARTIAL


def test_policy_subject_to_dict():
    """Test PolicySubject serialization."""
    subject = PolicySubject(
        agent_id="agent_001",
        user_id="user_123"
    )

    result = subject.to_dict()
    assert result["agent_id"] == "agent_001"
    assert result["user_id"] == "user_123"
    assert "system_component" not in result  # Should be filtered out


def test_policy_object_with_classification():
    """Test PolicyObject with data classification."""
    obj = PolicyObject(
        resource_type="database",
        resource_id="db_prod_001",
        data_classification=DataClassification.CONFIDENTIAL
    )

    result = obj.to_dict()
    assert result["data_classification"] == "confidential"


def test_policy_decision():
    """Test PolicyDecision for allowed and denied actions."""
    # Denied decision
    denied = PolicyDecision(
        allowed=False,
        reason="Insufficient permissions",
        violated_policies=["pol_001"],
        required_conditions=["manager_approval"]
    )

    assert denied.allowed is False
    assert len(denied.violated_policies) == 1

    # Allowed decision
    allowed = PolicyDecision(
        allowed=True,
        reason="All requirements met"
    )

    assert allowed.allowed is True
    assert len(allowed.violated_policies) == 0


# ============================================================================
# TESTS: AUDIT LOGGING
# ============================================================================


def test_audit_log_hash_calculation():
    """Test audit log hash calculation."""
    log = AuditLog(
        log_id="log_001",
        event_type="test_event",
        timestamp=datetime.utcnow(),
        action="test_action"
    )

    assert log.chain_hash is not None
    assert len(log.chain_hash) == 64  # SHA-256 produces 64 hex characters


def test_audit_log_chaining():
    """Test blockchain-style audit log chaining."""
    # First log
    log1 = AuditLog(
        log_id="log_001",
        event_type="event_1",
        timestamp=datetime.utcnow(),
        action="action_1"
    )

    # Second log chained to first
    log2 = AuditLog(
        log_id="log_002",
        event_type="event_2",
        timestamp=datetime.utcnow(),
        action="action_2",
        previous_hash=log1.chain_hash
    )

    # Verify chain
    assert log2.verify_chain(log1) is True
    assert log2.previous_hash == log1.chain_hash


def test_audit_log_chain_tampering_detection():
    """Test that tampering breaks the chain."""
    log1 = AuditLog(
        log_id="log_001",
        event_type="event_1",
        timestamp=datetime.utcnow(),
        action="action_1"
    )

    # Create log2 with wrong previous_hash
    log2 = AuditLog(
        log_id="log_002",
        event_type="event_2",
        timestamp=datetime.utcnow(),
        action="action_2",
        previous_hash="wrong_hash"
    )

    # Verify should fail
    assert log2.verify_chain(log1) is False


def test_audit_log_with_actor_and_resource():
    """Test audit log with full actor and resource information."""
    actor = AuditActor(
        agent_id="agent_001",
        user_id="user_123",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0"
    )

    resource = AuditResource(
        resource_type="customer_record",
        resource_id="cust_456",
        resource_name="Customer Profile"
    )

    log = AuditLog(
        log_id="log_001",
        event_type="data_access",
        event_category=EventCategory.DATA_ACCESS,
        timestamp=datetime.utcnow(),
        actor=actor,
        action="read_customer_data",
        resource=resource,
        result=EventResult.SUCCESS,
        compliance_tags=["GDPR_Art30", "SOC2_CC6.1"]
    )

    result = log.to_dict()
    assert result["actor"]["agent_id"] == "agent_001"
    assert result["resource"]["resource_type"] == "customer_record"
    assert "GDPR_Art30" in result["compliance_tags"]


@pytest.mark.asyncio
async def test_audit_log_immutability(caip_client):
    """Test that audit logs are immutable and chained."""
    # Create first log
    log1 = await caip_client.log_audit_event(
        event_type="test_event_1",
        action="test_action_1"
    )

    # Create second log
    log2 = await caip_client.log_audit_event(
        event_type="test_event_2",
        action="test_action_2"
    )

    # Verify chain
    assert log2.previous_hash == log1.chain_hash
    assert caip_client.verify_audit_chain() is True


@pytest.mark.asyncio
async def test_audit_chain_verification_multiple_entries(caip_client):
    """Test audit chain verification with multiple entries."""
    # Create chain of 5 logs
    for i in range(5):
        await caip_client.log_audit_event(
            event_type=f"event_{i}",
            action=f"action_{i}"
        )

    # Verify entire chain
    assert len(caip_client.audit_chain) == 5
    assert caip_client.verify_audit_chain() is True


# ============================================================================
# TESTS: COMPLIANCE ENGINE
# ============================================================================


def test_compliance_engine_initialization(compliance_engine):
    """Test compliance engine initializes with default controls."""
    assert len(compliance_engine.control_catalog) > 0

    # Check for GDPR controls
    gdpr_controls = [c for c in compliance_engine.control_catalog.values() if c.framework == "GDPR"]
    assert len(gdpr_controls) > 0

    # Check for SOC2 controls
    soc2_controls = [c for c in compliance_engine.control_catalog.values() if c.framework == "SOC2"]
    assert len(soc2_controls) > 0


def test_compliance_engine_add_control(compliance_engine):
    """Test adding custom control to engine."""
    initial_count = len(compliance_engine.control_catalog)

    custom_control = Control(
        control_id="CUSTOM_001",
        control_name="Custom Control",
        control_category=ControlCategory.DATA_PROTECTION,
        required_evidence=["evidence_1"],
        framework="CUSTOM"
    )

    compliance_engine.add_control(custom_control)

    assert len(compliance_engine.control_catalog) == initial_count + 1
    assert compliance_engine.get_control("CUSTOM_001") == custom_control


def test_compliance_engine_list_controls(compliance_engine):
    """Test listing controls by framework."""
    # List all controls
    all_controls = compliance_engine.list_controls()
    assert len(all_controls) > 0

    # List GDPR controls only
    gdpr_controls = compliance_engine.list_controls(ComplianceFramework.GDPR)
    assert all(c.framework == "GDPR" for c in gdpr_controls)

    # List SOC2 controls only
    soc2_controls = compliance_engine.list_controls(ComplianceFramework.SOC2)
    assert all(c.framework == "SOC2" for c in soc2_controls)


@pytest.mark.asyncio
async def test_compliance_check_gdpr(compliance_engine, sample_scope):
    """Test GDPR compliance check."""
    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR],
        scope=sample_scope,
        performed_by="test_agent"
    )

    assert check.check_id is not None
    assert ComplianceFramework.GDPR in check.framework
    assert check.check_result is not None
    assert check.check_result.compliance_score >= 0
    assert check.check_result.compliance_score <= 100


@pytest.mark.asyncio
async def test_compliance_check_multiple_frameworks(compliance_engine, sample_scope):
    """Test compliance check across multiple frameworks."""
    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR, ComplianceFramework.SOC2, ComplianceFramework.HIPAA],
        scope=sample_scope,
        performed_by="test_agent"
    )

    assert len(check.framework) == 3
    assert check.check_result is not None

    # Should have controls from multiple frameworks
    frameworks_in_controls = set(c.framework for c in check.controls)
    assert len(frameworks_in_controls) > 1


@pytest.mark.asyncio
async def test_compliance_check_with_specific_controls(compliance_engine, sample_scope):
    """Test compliance check with specific controls."""
    specific_controls = [
        compliance_engine.get_control("GDPR_Art17"),
        compliance_engine.get_control("SOC2_CC6.1")
    ]

    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
        scope=sample_scope,
        controls=specific_controls,
        performed_by="test_agent"
    )

    assert len(check.controls) == 2
    assert check.controls[0].control_id == "GDPR_Art17"
    assert check.controls[1].control_id == "SOC2_CC6.1"


@pytest.mark.asyncio
async def test_compliance_check_status_determination(compliance_engine, sample_scope):
    """Test that compliance status is correctly determined."""
    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR],
        scope=sample_scope,
        performed_by="test_agent"
    )

    result = check.check_result

    # Status should match score
    if result.compliance_score == 100:
        assert result.overall_status == ComplianceStatus.COMPLIANT
    elif result.compliance_score >= 75:
        assert result.overall_status == ComplianceStatus.PARTIAL
    else:
        assert result.overall_status == ComplianceStatus.NON_COMPLIANT


@pytest.mark.asyncio
async def test_compliance_check_generates_findings(compliance_engine, sample_scope):
    """Test that failed controls generate findings."""
    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
        scope=sample_scope,
        performed_by="test_agent"
    )

    result = check.check_result

    # If controls failed, should have findings
    if result.controls_failed > 0:
        assert len(result.findings) > 0
        assert len(result.gaps) > 0

        # Check finding structure
        for finding in result.findings:
            assert finding.finding_id is not None
            assert finding.control_id is not None
            assert finding.remediation is not None
            assert finding.remediation.required is True


@pytest.mark.asyncio
async def test_compliance_check_collects_evidence(compliance_engine, sample_scope):
    """Test that passed controls collect evidence."""
    check = await compliance_engine.check_compliance(
        framework=[ComplianceFramework.GDPR],
        scope=sample_scope,
        performed_by="test_agent"
    )

    result = check.check_result

    # If controls passed, should have evidence
    if result.controls_passed > 0:
        assert len(result.evidence_collected) > 0

        # Check evidence structure
        for evidence in result.evidence_collected:
            assert evidence.evidence_id is not None
            assert evidence.evidence_type is not None
            assert evidence.control_id is not None


# ============================================================================
# TESTS: CAIP CLIENT
# ============================================================================


def test_caip_client_initialization():
    """Test CAIP client initialization."""
    client = CAIPClient(agent_id="test_agent_123")

    assert client.agent_id == "test_agent_123"
    assert client.engine is not None
    assert len(client.audit_chain) == 0
    assert len(client.certifications) == 0


@pytest.mark.asyncio
async def test_caip_client_compliance_check(caip_client, sample_scope):
    """Test compliance check through client."""
    check = await caip_client.perform_compliance_check(
        frameworks=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
        scope=sample_scope
    )

    assert check is not None
    assert check.check_result is not None
    assert check.performed_by == caip_client.agent_id

    # Should have created audit log
    assert len(caip_client.audit_chain) > 0


@pytest.mark.asyncio
async def test_caip_client_policy_enforcement_allow(caip_client):
    """Test policy enforcement that allows action."""
    subject = PolicySubject(agent_id="agent_001")
    obj = PolicyObject(
        resource_type="report",
        resource_id="report_123",
        data_classification=DataClassification.INTERNAL
    )

    enforcement = await caip_client.enforce_policy(
        policy_id="pol_001",
        action="view_report",
        subject=subject,
        obj=obj,
        enforcement_mode=EnforcementMode.WARN
    )

    assert enforcement.decision is not None
    # Internal data with view action should be allowed
    assert enforcement.decision.allowed is True


@pytest.mark.asyncio
async def test_caip_client_policy_enforcement_block(caip_client):
    """Test policy enforcement that blocks action."""
    subject = PolicySubject(agent_id="agent_002")
    obj = PolicyObject(
        resource_type="database",
        resource_id="db_prod",
        data_classification=DataClassification.RESTRICTED
    )

    enforcement = await caip_client.enforce_policy(
        policy_id="pol_002",
        action="access_database",
        subject=subject,
        obj=obj,
        enforcement_mode=EnforcementMode.BLOCK
    )

    assert enforcement.decision is not None
    # Restricted data without clearance should be blocked
    assert enforcement.decision.allowed is False
    assert len(enforcement.decision.violated_policies) > 0


@pytest.mark.asyncio
async def test_caip_client_policy_enforcement_export_block(caip_client):
    """Test that confidential data export is blocked."""
    subject = PolicySubject(agent_id="agent_003")
    obj = PolicyObject(
        resource_type="customer_data",
        resource_id="customers",
        data_classification=DataClassification.CONFIDENTIAL
    )

    enforcement = await caip_client.enforce_policy(
        policy_id="pol_export",
        action="export_customer_data",
        subject=subject,
        obj=obj,
        enforcement_mode=EnforcementMode.BLOCK
    )

    assert enforcement.decision.allowed is False
    assert "export" in enforcement.decision.reason.lower() or "confidential" in enforcement.decision.reason.lower()


@pytest.mark.asyncio
async def test_caip_client_risk_assessment(caip_client):
    """Test risk assessment through client."""
    scope = RiskScope(
        systems=["api", "database"],
        data_assets=["customer_data", "financial_records"],
        processes=["payment_processing"]
    )

    assessment = await caip_client.assess_risk(scope)

    assert assessment.assessment_id is not None
    assert assessment.overall_risk_level is not None
    assert len(assessment.threats) > 0
    assert len(assessment.vulnerabilities) > 0
    assert len(assessment.mitigation_recommendations) > 0
    assert assessment.assessed_by == caip_client.agent_id


@pytest.mark.asyncio
async def test_caip_client_risk_assessment_calculation(caip_client):
    """Test risk level calculation in assessment."""
    scope = RiskScope(systems=["test_system"])

    assessment = await caip_client.assess_risk(scope)

    # Calculate expected risk level
    calculated_risk = assessment.calculate_overall_risk()

    # Should match the overall_risk_level
    assert assessment.overall_risk_level == calculated_risk


def test_caip_client_certification_registration(caip_client):
    """Test certification registration."""
    cert = Certification(
        certification_id="cert_001",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        certification_level="Type II",
        readiness_score=95.0
    )

    caip_client.register_certification(cert)

    # Should be able to retrieve it
    retrieved = caip_client.get_certification("cert_001")
    assert retrieved == cert


def test_caip_client_get_certifications_by_framework(caip_client):
    """Test getting certifications by framework."""
    # Register multiple certifications
    cert1 = Certification(
        certification_id="cert_soc2",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED
    )
    cert2 = Certification(
        certification_id="cert_iso",
        framework=ComplianceFramework.ISO27001,
        status=CertificationStatus.IN_PROGRESS
    )
    cert3 = Certification(
        certification_id="cert_soc2_2",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.MAINTAINED
    )

    caip_client.register_certification(cert1)
    caip_client.register_certification(cert2)
    caip_client.register_certification(cert3)

    # Get SOC2 certifications
    soc2_certs = caip_client.get_certifications_by_framework(ComplianceFramework.SOC2)
    assert len(soc2_certs) == 2

    # Get ISO27001 certifications
    iso_certs = caip_client.get_certifications_by_framework(ComplianceFramework.ISO27001)
    assert len(iso_certs) == 1


def test_caip_client_export_compliance_report(caip_client, sample_scope):
    """Test exporting compliance report."""
    # Create a compliance check
    check = ComplianceCheck(
        check_id="check_001",
        framework=[ComplianceFramework.GDPR],
        scope=sample_scope,
        check_result=CheckResult(
            overall_status=ComplianceStatus.COMPLIANT,
            compliance_score=100.0,
            controls_passed=10,
            controls_failed=0,
            controls_not_applicable=0
        )
    )

    report = caip_client.export_compliance_report(check)

    assert report["protocol"] == "CAIP"
    assert report["version"] == "1.0.0"
    assert report["operation"] == "compliance_check"
    assert report["compliance_check"]["check_id"] == "check_001"


# ============================================================================
# TESTS: RISK ASSESSMENT
# ============================================================================


def test_threat_creation():
    """Test threat creation and serialization."""
    threat = Threat(
        threat_id="T001",
        threat_name="Unauthorized Access",
        threat_category=ThreatCategory.UNAUTHORIZED_ACCESS,
        likelihood=RiskLevel.MEDIUM,
        impact=RiskLevel.HIGH,
        risk_score=70.0,
        description="Risk of unauthorized data access"
    )

    result = threat.to_dict()
    assert result["threat_category"] == "unauthorized_access"
    assert result["likelihood"] == "medium"
    assert result["impact"] == "high"


def test_vulnerability_creation():
    """Test vulnerability creation."""
    vuln = Vulnerability(
        vulnerability_id="V001",
        description="Weak password policy",
        severity=Severity.HIGH,
        affected_controls=["SOC2_CC6.1", "ISO27001_A.9.2"]
    )

    result = vuln.to_dict()
    assert len(result["affected_controls"]) == 2


def test_mitigation_recommendation():
    """Test mitigation recommendation."""
    rec = MitigationRecommendation(
        recommendation_id="R001",
        title="Implement MFA",
        description="Add multi-factor authentication",
        priority=Severity.HIGH,
        estimated_effort="2 weeks",
        risk_reduction=30.0
    )

    result = rec.to_dict()
    assert result["risk_reduction"] == 30.0
    assert result["priority"] == "high"


def test_risk_assessment_overall_risk_calculation():
    """Test overall risk level calculation."""
    threats = [
        Threat("T1", "Threat 1", ThreatCategory.DATA_BREACH, RiskLevel.HIGH, RiskLevel.HIGH, 85.0),
        Threat("T2", "Threat 2", ThreatCategory.DATA_LOSS, RiskLevel.MEDIUM, RiskLevel.MEDIUM, 50.0),
        Threat("T3", "Threat 3", ThreatCategory.AUDIT_FAILURE, RiskLevel.LOW, RiskLevel.LOW, 25.0)
    ]

    assessment = RiskAssessment(
        assessment_id="risk_001",
        scope=RiskScope(systems=["test"]),
        threats=threats
    )

    # Average score: (85 + 50 + 25) / 3 = 53.33
    # Should be MEDIUM (40-60 range)
    calculated = assessment.calculate_overall_risk()
    assert calculated == RiskLevel.MEDIUM


def test_risk_assessment_critical_level():
    """Test risk assessment with critical level."""
    threats = [
        Threat("T1", "Threat 1", ThreatCategory.DATA_BREACH, RiskLevel.CRITICAL, RiskLevel.CRITICAL, 90.0),
        Threat("T2", "Threat 2", ThreatCategory.DATA_LOSS, RiskLevel.HIGH, RiskLevel.CRITICAL, 85.0),
    ]

    assessment = RiskAssessment(
        assessment_id="risk_002",
        scope=RiskScope(systems=["prod"]),
        threats=threats
    )

    # Average: (90 + 85) / 2 = 87.5 -> CRITICAL (>= 80)
    assert assessment.calculate_overall_risk() == RiskLevel.CRITICAL


# ============================================================================
# TESTS: CERTIFICATION
# ============================================================================


def test_certification_is_valid():
    """Test certification validity check."""
    from dateutil import parser

    # Valid certification
    valid_cert = Certification(
        certification_id="cert_001",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        expiration_date="2026-12-31"
    )

    assert valid_cert.is_valid() is True

    # Expired certification
    expired_cert = Certification(
        certification_id="cert_002",
        framework=ComplianceFramework.ISO27001,
        status=CertificationStatus.EXPIRED,
        expiration_date="2020-12-31"
    )

    assert expired_cert.is_valid() is False

    # In progress certification
    in_progress_cert = Certification(
        certification_id="cert_003",
        framework=ComplianceFramework.HIPAA,
        status=CertificationStatus.IN_PROGRESS
    )

    assert in_progress_cert.is_valid() is False


def test_certification_to_dict():
    """Test certification serialization."""
    cert = Certification(
        certification_id="cert_001",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        certification_level="Type II",
        audit_firm="Deloitte",
        issued_date="2025-01-01",
        expiration_date="2026-01-01",
        readiness_score=95.0,
        certificate_url="https://example.com/cert.pdf"
    )

    result = cert.to_dict()
    assert result["framework"] == "SOC2"
    assert result["status"] == "achieved"
    assert result["certification_level"] == "Type II"
    assert result["readiness_score"] == 95.0


# ============================================================================
# TESTS: CONVENIENCE FUNCTIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_compliance_check_convenience():
    """Test convenience function for compliance check."""
    check = await create_compliance_check(
        frameworks=["GDPR", "SOC2"],
        system_components=["api", "database"],
        data_categories=["PII"],
        processes=["user_management"],
        agent_id="test_agent"
    )

    assert check is not None
    assert len(check.framework) == 2
    assert ComplianceFramework.GDPR in check.framework
    assert ComplianceFramework.SOC2 in check.framework


@pytest.mark.asyncio
async def test_create_audit_log_convenience():
    """Test convenience function for audit log."""
    log = await create_audit_log(
        event_type="test_event",
        action="test_action",
        agent_id="test_agent",
        severity=Severity.INFO
    )

    assert log is not None
    assert log.event_type == "test_event"
    assert log.action == "test_action"
    assert log.severity == Severity.INFO


# ============================================================================
# TESTS: INTEGRATION SCENARIOS
# ============================================================================


@pytest.mark.asyncio
async def test_full_gdpr_compliance_workflow(caip_client):
    """Test complete GDPR compliance workflow."""
    # 1. Perform compliance check
    scope = ComplianceScope(
        system_components=["user_api", "database", "backup_system"],
        data_categories=["PII", "financial"],
        processes=["user_registration", "data_deletion", "data_export"]
    )

    check = await caip_client.perform_compliance_check(
        frameworks=[ComplianceFramework.GDPR],
        scope=scope
    )

    assert check is not None
    assert check.check_result.compliance_score >= 0

    # 2. If there are findings, create remediation plan
    if check.check_result.controls_failed > 0:
        assert len(check.check_result.findings) > 0
        for finding in check.check_result.findings:
            assert finding.remediation is not None

    # 3. Perform risk assessment
    risk_scope = RiskScope(
        systems=scope.system_components,
        data_assets=scope.data_categories,
        processes=scope.processes
    )

    assessment = await caip_client.assess_risk(risk_scope)
    assert assessment is not None

    # 4. Verify audit trail
    assert caip_client.verify_audit_chain() is True


@pytest.mark.asyncio
async def test_multi_framework_compliance_and_certification(caip_client):
    """Test compliance across multiple frameworks with certification."""
    # Check compliance for multiple frameworks
    scope = ComplianceScope(
        system_components=["api", "database"],
        data_categories=["PII", "PHI", "financial"],
        processes=["payment_processing", "healthcare_records"]
    )

    check = await caip_client.perform_compliance_check(
        frameworks=[
            ComplianceFramework.GDPR,
            ComplianceFramework.HIPAA,
            ComplianceFramework.SOC2
        ],
        scope=scope
    )

    assert len(check.framework) == 3

    # Register certifications
    soc2_cert = Certification(
        certification_id="cert_soc2",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        readiness_score=check.check_result.compliance_score
    )

    caip_client.register_certification(soc2_cert)

    # Verify certification
    retrieved = caip_client.get_certification("cert_soc2")
    assert retrieved.framework == ComplianceFramework.SOC2


@pytest.mark.asyncio
async def test_policy_enforcement_with_audit_trail(caip_client):
    """Test policy enforcement creates proper audit trail."""
    initial_log_count = len(caip_client.audit_chain)

    # Enforce a policy
    subject = PolicySubject(agent_id="agent_001")
    obj = PolicyObject(
        resource_type="customer_data",
        resource_id="db_customers",
        data_classification=DataClassification.CONFIDENTIAL
    )

    enforcement = await caip_client.enforce_policy(
        policy_id="pol_data_access",
        action="export_data",
        subject=subject,
        obj=obj,
        enforcement_mode=EnforcementMode.BLOCK
    )

    # Should have created audit log
    assert len(caip_client.audit_chain) > initial_log_count

    # Verify audit chain
    assert caip_client.verify_audit_chain() is True

    # Check that the log contains policy information
    latest_log = caip_client.audit_chain[-1]
    assert latest_log.event_type == "policy_enforcement"
    assert "policy_id" in latest_log.details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
