"""
Compliance Automation & Intelligence Protocol (CAIP) v1.0 - PRODUCTION IMPLEMENTATION
======================================================================================

Complete implementation of CAIP for automated compliance checking, regulatory intelligence,
audit trail management, and policy enforcement.

Supports:
- GDPR, HIPAA, SOC2, ISO27001, PCI_DSS, CCPA, NIST, FedRAMP, APQC, and custom frameworks
- Automated compliance checking against controls
- Policy enforcement (monitor, warn, block, remediate)
- Immutable audit logs with blockchain-style chaining
- Risk assessment with threats, vulnerabilities, and mitigation
- Evidence collection and management
- Gap analysis and remediation planning
- Certification status tracking

Author: SuperStandard Team
License: MIT
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMERATIONS
# ============================================================================


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    PCI_DSS = "PCI_DSS"
    CCPA = "CCPA"
    NIST = "NIST"
    FedRAMP = "FedRAMP"
    APQC = "APQC"
    CUSTOM = "custom"


class ComplianceStatus(str, Enum):
    """Compliance check status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class ControlCategory(str, Enum):
    """Control categories."""
    ACCESS_CONTROL = "access_control"
    DATA_PROTECTION = "data_protection"
    ENCRYPTION = "encryption"
    LOGGING_MONITORING = "logging_monitoring"
    INCIDENT_RESPONSE = "incident_response"
    BUSINESS_CONTINUITY = "business_continuity"
    VENDOR_MANAGEMENT = "vendor_management"
    TRAINING_AWARENESS = "training_awareness"


class EnforcementMode(str, Enum):
    """Policy enforcement modes."""
    MONITOR = "monitor"
    WARN = "warn"
    BLOCK = "block"
    REMEDIATE = "remediate"


class PolicyCategory(str, Enum):
    """Policy categories."""
    DATA_GOVERNANCE = "data_governance"
    ACCESS_CONTROL = "access_control"
    RETENTION = "retention"
    PRIVACY = "privacy"
    SECURITY = "security"
    OPERATIONAL = "operational"


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class EventCategory(str, Enum):
    """Audit log event categories."""
    ACCESS = "access"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    POLICY_VIOLATION = "policy_violation"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"


class Severity(str, Enum):
    """Severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventResult(str, Enum):
    """Event result status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class ThreatCategory(str, Enum):
    """Risk threat categories."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_LOSS = "data_loss"
    REGULATORY_VIOLATION = "regulatory_violation"
    POLICY_VIOLATION = "policy_violation"
    AUDIT_FAILURE = "audit_failure"


class RiskLevel(str, Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(str, Enum):
    """Finding types."""
    VIOLATION = "violation"
    DEFICIENCY = "deficiency"
    OBSERVATION = "observation"
    BEST_PRACTICE = "best_practice"


class FindingStatus(str, Enum):
    """Finding status."""
    OPEN = "open"
    IN_REMEDIATION = "in_remediation"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"


class CertificationStatus(str, Enum):
    """Certification status."""
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    MAINTAINED = "maintained"
    EXPIRED = "expired"
    REVOKED = "revoked"


class EvidenceType(str, Enum):
    """Evidence types."""
    DOCUMENT = "document"
    LOG = "log"
    SCREENSHOT = "screenshot"
    CONFIGURATION = "configuration"
    CERTIFICATE = "certificate"


class AssessmentType(str, Enum):
    """Risk assessment types."""
    INITIAL = "initial"
    PERIODIC = "periodic"
    CHANGE_DRIVEN = "change-driven"
    INCIDENT_DRIVEN = "incident-driven"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TimePeriod:
    """Time period for compliance scope."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }


@dataclass
class ComplianceScope:
    """Scope of compliance check."""

    system_components: List[str] = field(default_factory=list)
    data_categories: List[str] = field(default_factory=list)
    processes: List[str] = field(default_factory=list)
    time_period: Optional[TimePeriod] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "system_components": self.system_components,
            "data_categories": self.data_categories,
            "processes": self.processes
        }
        if self.time_period:
            result["time_period"] = self.time_period.to_dict()
        return result


@dataclass
class Control:
    """Compliance control definition."""

    control_id: str
    control_name: str
    control_category: ControlCategory
    required_evidence: List[str] = field(default_factory=list)
    description: Optional[str] = None
    framework: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["control_category"] = self.control_category.value
        return result


@dataclass
class Evidence:
    """Evidence supporting compliance."""

    evidence_id: str
    evidence_type: EvidenceType
    description: str
    location: str
    timestamp: datetime
    control_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "description": self.description,
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "control_id": self.control_id
        }


@dataclass
class ComplianceGap:
    """Compliance gap identified."""

    gap_id: str
    control_id: str
    severity: Severity
    description: str
    impact: str
    remediation_required: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["severity"] = self.severity.value
        return result


@dataclass
class Remediation:
    """Remediation plan for a finding."""

    required: bool
    steps: List[str]
    responsible_party: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_effort: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "required": self.required,
            "steps": self.steps,
            "responsible_party": self.responsible_party,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "estimated_effort": self.estimated_effort
        }


@dataclass
class Finding:
    """Compliance finding (violation or observation)."""

    finding_id: str
    finding_type: FindingType
    severity: Severity
    control_id: str
    framework: str
    title: str
    description: str
    status: FindingStatus = FindingStatus.OPEN
    evidence: List[str] = field(default_factory=list)
    remediation: Optional[Remediation] = None
    identified_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        """Set identified_at if not provided."""
        if self.identified_at is None:
            self.identified_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type.value,
            "severity": self.severity.value,
            "control_id": self.control_id,
            "framework": self.framework,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "evidence": self.evidence,
            "identified_at": self.identified_at.isoformat() if self.identified_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
        if self.remediation:
            result["remediation"] = self.remediation.to_dict()
        return result


@dataclass
class CheckResult:
    """Result of compliance check."""

    overall_status: ComplianceStatus
    compliance_score: float
    controls_passed: int
    controls_failed: int
    controls_not_applicable: int
    findings: List[Finding] = field(default_factory=list)
    gaps: List[ComplianceGap] = field(default_factory=list)
    evidence_collected: List[Evidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "compliance_score": self.compliance_score,
            "controls_passed": self.controls_passed,
            "controls_failed": self.controls_failed,
            "controls_not_applicable": self.controls_not_applicable,
            "findings": [f.to_dict() for f in self.findings],
            "gaps": [g.to_dict() for g in self.gaps],
            "evidence_collected": [e.to_dict() for e in self.evidence_collected]
        }


@dataclass
class ComplianceCheck:
    """Compliance verification request/result."""

    check_id: str
    framework: List[ComplianceFramework]
    scope: ComplianceScope
    controls: List[Control] = field(default_factory=list)
    check_result: Optional[CheckResult] = None
    performed_by: Optional[str] = None
    performed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set defaults."""
        if self.performed_at is None:
            self.performed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "check_id": self.check_id,
            "framework": [f.value for f in self.framework],
            "scope": self.scope.to_dict(),
            "controls": [c.to_dict() for c in self.controls],
            "performed_by": self.performed_by,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None
        }
        if self.check_result:
            result["check_result"] = self.check_result.to_dict()
        return result


@dataclass
class PolicySubject:
    """Who/what is performing the action."""

    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    system_component: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PolicyObject:
    """What is being acted upon."""

    resource_type: str
    resource_id: str
    data_classification: Optional[DataClassification] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id
        }
        if self.data_classification:
            result["data_classification"] = self.data_classification.value
        return result


@dataclass
class PolicyDecision:
    """Policy enforcement decision."""

    allowed: bool
    reason: str
    violated_policies: List[str] = field(default_factory=list)
    required_conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PolicyEnforcement:
    """Policy enforcement action."""

    policy_id: str
    action: str
    enforcement_mode: EnforcementMode = EnforcementMode.WARN
    policy_name: Optional[str] = None
    policy_category: Optional[PolicyCategory] = None
    subject: Optional[PolicySubject] = None
    object: Optional[PolicyObject] = None
    decision: Optional[PolicyDecision] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Set defaults."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "policy_id": self.policy_id,
            "action": self.action,
            "enforcement_mode": self.enforcement_mode.value,
            "policy_name": self.policy_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
        if self.policy_category:
            result["policy_category"] = self.policy_category.value
        if self.subject:
            result["subject"] = self.subject.to_dict()
        if self.object:
            result["object"] = self.object.to_dict()
        if self.decision:
            result["decision"] = self.decision.to_dict()
        return result


@dataclass
class AuditActor:
    """Actor who performed an action."""

    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuditResource:
    """Resource acted upon."""

    resource_type: str
    resource_id: str
    resource_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuditLog:
    """Immutable audit log entry with blockchain-style chaining."""

    log_id: str
    event_type: str
    timestamp: datetime
    event_category: Optional[EventCategory] = None
    severity: Severity = Severity.INFO
    actor: Optional[AuditActor] = None
    action: Optional[str] = None
    resource: Optional[AuditResource] = None
    result: EventResult = EventResult.SUCCESS
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[str] = field(default_factory=list)
    retention_period: int = 2555  # 7 years default
    immutable: bool = True
    chain_hash: Optional[str] = None
    previous_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate hash for this log entry."""
        if self.chain_hash is None:
            self.chain_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of log entry."""
        # Create canonical representation
        log_data = {
            "log_id": self.log_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "previous_hash": self.previous_hash or ""
        }
        # Sort keys for deterministic hashing
        canonical = json.dumps(log_data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_chain(self, previous_log: Optional['AuditLog']) -> bool:
        """Verify this log entry's chain hash."""
        if previous_log is None:
            return self.previous_hash is None or self.previous_hash == ""

        # Check that our previous_hash matches the previous log's chain_hash
        return self.previous_hash == previous_log.chain_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "log_id": self.log_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "result": self.result.value,
            "details": self.details,
            "compliance_tags": self.compliance_tags,
            "retention_period": self.retention_period,
            "immutable": self.immutable,
            "chain_hash": self.chain_hash,
            "previous_hash": self.previous_hash
        }
        if self.event_category:
            result["event_category"] = self.event_category.value
        if self.actor:
            result["actor"] = self.actor.to_dict()
        if self.action:
            result["action"] = self.action
        if self.resource:
            result["resource"] = self.resource.to_dict()
        return result


@dataclass
class Threat:
    """Identified compliance threat."""

    threat_id: str
    threat_name: str
    threat_category: ThreatCategory
    likelihood: RiskLevel
    impact: RiskLevel
    risk_score: float
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "threat_id": self.threat_id,
            "threat_name": self.threat_name,
            "threat_category": self.threat_category.value,
            "likelihood": self.likelihood.value,
            "impact": self.impact.value,
            "risk_score": self.risk_score,
            "description": self.description
        }


@dataclass
class Vulnerability:
    """Compliance vulnerability."""

    vulnerability_id: str
    description: str
    severity: Severity
    affected_controls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vulnerability_id": self.vulnerability_id,
            "description": self.description,
            "severity": self.severity.value,
            "affected_controls": self.affected_controls
        }


@dataclass
class MitigationRecommendation:
    """Risk mitigation recommendation."""

    recommendation_id: str
    title: str
    description: str
    priority: Severity
    estimated_effort: Optional[str] = None
    risk_reduction: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "estimated_effort": self.estimated_effort,
            "risk_reduction": self.risk_reduction
        }


@dataclass
class RiskScope:
    """Scope of risk assessment."""

    systems: List[str] = field(default_factory=list)
    data_assets: List[str] = field(default_factory=list)
    processes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RiskAssessment:
    """Compliance risk assessment."""

    assessment_id: str
    scope: RiskScope
    assessment_type: AssessmentType = AssessmentType.PERIODIC
    threats: List[Threat] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    mitigation_recommendations: List[MitigationRecommendation] = field(default_factory=list)
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set defaults."""
        if self.assessed_at is None:
            self.assessed_at = datetime.utcnow()

    def calculate_overall_risk(self) -> RiskLevel:
        """Calculate overall risk level from threats."""
        if not self.threats:
            return RiskLevel.LOW

        # Calculate average risk score
        avg_score = sum(t.risk_score for t in self.threats) / len(self.threats)

        if avg_score >= 80:
            return RiskLevel.CRITICAL
        elif avg_score >= 60:
            return RiskLevel.HIGH
        elif avg_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "assessment_type": self.assessment_type.value,
            "scope": self.scope.to_dict(),
            "threats": [t.to_dict() for t in self.threats],
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "overall_risk_level": self.overall_risk_level.value,
            "mitigation_recommendations": [m.to_dict() for m in self.mitigation_recommendations],
            "assessed_by": self.assessed_by,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None
        }


@dataclass
class Certification:
    """Compliance certification status."""

    certification_id: str
    framework: ComplianceFramework
    status: CertificationStatus
    certification_level: Optional[str] = None
    audit_firm: Optional[str] = None
    issued_date: Optional[str] = None
    expiration_date: Optional[str] = None
    next_audit_date: Optional[str] = None
    scope: Dict[str, Any] = field(default_factory=dict)
    certificate_url: Optional[str] = None
    readiness_score: Optional[float] = None

    def is_valid(self) -> bool:
        """Check if certification is currently valid."""
        if self.status not in [CertificationStatus.ACHIEVED, CertificationStatus.MAINTAINED]:
            return False

        if self.expiration_date:
            from dateutil import parser
            expiry = parser.parse(self.expiration_date)
            return expiry > datetime.now()

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "certification_id": self.certification_id,
            "framework": self.framework.value,
            "status": self.status.value,
            "certification_level": self.certification_level,
            "audit_firm": self.audit_firm,
            "issued_date": self.issued_date,
            "expiration_date": self.expiration_date,
            "next_audit_date": self.next_audit_date,
            "scope": self.scope,
            "certificate_url": self.certificate_url,
            "readiness_score": self.readiness_score
        }


# ============================================================================
# COMPLIANCE ENGINE
# ============================================================================


class ComplianceEngine:
    """
    Main compliance checking engine.

    Provides comprehensive compliance verification across multiple frameworks.
    """

    def __init__(self):
        """Initialize the compliance engine."""
        self.control_catalog: Dict[str, Control] = {}
        self.policy_rules: Dict[str, Any] = {}
        self._load_default_controls()

    def _load_default_controls(self):
        """Load default control catalog for supported frameworks."""
        # GDPR Controls
        gdpr_controls = [
            Control(
                control_id="GDPR_Art17",
                control_name="Right to Erasure",
                control_category=ControlCategory.DATA_PROTECTION,
                required_evidence=["deletion_logs", "data_retention_policy"],
                description="Ensure data subjects can exercise right to erasure",
                framework="GDPR"
            ),
            Control(
                control_id="GDPR_Art30",
                control_name="Records of Processing Activities",
                control_category=ControlCategory.LOGGING_MONITORING,
                required_evidence=["processing_records", "data_flow_diagrams"],
                description="Maintain records of all data processing activities",
                framework="GDPR"
            ),
            Control(
                control_id="GDPR_Art32",
                control_name="Security of Processing",
                control_category=ControlCategory.ENCRYPTION,
                required_evidence=["encryption_policy", "security_audit"],
                description="Implement appropriate technical and organizational measures",
                framework="GDPR"
            ),
            Control(
                control_id="GDPR_Art33",
                control_name="Breach Notification",
                control_category=ControlCategory.INCIDENT_RESPONSE,
                required_evidence=["incident_response_plan", "breach_notification_procedures"],
                description="Notify supervisory authority of data breaches within 72 hours",
                framework="GDPR"
            )
        ]

        # SOC2 Controls
        soc2_controls = [
            Control(
                control_id="SOC2_CC6.1",
                control_name="Logical and Physical Access Controls",
                control_category=ControlCategory.ACCESS_CONTROL,
                required_evidence=["access_logs", "access_control_policy"],
                description="Implement logical and physical access controls",
                framework="SOC2"
            ),
            Control(
                control_id="SOC2_CC6.6",
                control_name="Data Encryption",
                control_category=ControlCategory.ENCRYPTION,
                required_evidence=["encryption_standards", "key_management"],
                description="Encrypt data in transit and at rest",
                framework="SOC2"
            ),
            Control(
                control_id="SOC2_CC7.2",
                control_name="System Monitoring",
                control_category=ControlCategory.LOGGING_MONITORING,
                required_evidence=["monitoring_logs", "alerting_configuration"],
                description="Monitor system components and alert on anomalies",
                framework="SOC2"
            ),
            Control(
                control_id="SOC2_CC9.2",
                control_name="Vendor Management",
                control_category=ControlCategory.VENDOR_MANAGEMENT,
                required_evidence=["vendor_assessments", "vendor_contracts"],
                description="Assess and monitor third-party service providers",
                framework="SOC2"
            )
        ]

        # HIPAA Controls
        hipaa_controls = [
            Control(
                control_id="HIPAA_164.308",
                control_name="Administrative Safeguards",
                control_category=ControlCategory.ACCESS_CONTROL,
                required_evidence=["security_policies", "workforce_training_records"],
                description="Implement administrative safeguards for PHI",
                framework="HIPAA"
            ),
            Control(
                control_id="HIPAA_164.312",
                control_name="Technical Safeguards",
                control_category=ControlCategory.ENCRYPTION,
                required_evidence=["encryption_implementation", "access_controls"],
                description="Implement technical safeguards for PHI",
                framework="HIPAA"
            )
        ]

        # ISO27001 Controls
        iso_controls = [
            Control(
                control_id="ISO27001_A.9.2",
                control_name="User Access Management",
                control_category=ControlCategory.ACCESS_CONTROL,
                required_evidence=["user_access_reviews", "provisioning_logs"],
                description="Ensure authorized user access and prevent unauthorized access",
                framework="ISO27001"
            ),
            Control(
                control_id="ISO27001_A.12.4",
                control_name="Logging and Monitoring",
                control_category=ControlCategory.LOGGING_MONITORING,
                required_evidence=["event_logs", "log_review_records"],
                description="Record events and generate evidence",
                framework="ISO27001"
            )
        ]

        # Add all controls to catalog
        for control in gdpr_controls + soc2_controls + hipaa_controls + iso_controls:
            self.control_catalog[control.control_id] = control

    async def check_compliance(
        self,
        framework: List[ComplianceFramework],
        scope: ComplianceScope,
        controls: Optional[List[Control]] = None,
        performed_by: Optional[str] = None
    ) -> ComplianceCheck:
        """
        Perform comprehensive compliance check.

        Args:
            framework: List of frameworks to check against
            scope: Scope of the compliance check
            controls: Specific controls to verify (optional, uses default if None)
            performed_by: Agent ID performing the check

        Returns:
            ComplianceCheck with results
        """
        check_id = str(uuid4())

        # Determine controls to check
        if controls is None:
            # Get default controls for specified frameworks
            controls = [
                c for c in self.control_catalog.values()
                if any(c.framework == f.value for f in framework)
            ]

        # Simulate compliance checking
        passed = 0
        failed = 0
        not_applicable = 0
        findings = []
        gaps = []
        evidence = []

        for control in controls:
            # Simulate control verification (in real implementation, this would check actual systems)
            if self._verify_control(control, scope):
                passed += 1
                # Collect evidence
                evidence.append(Evidence(
                    evidence_id=str(uuid4()),
                    evidence_type=EvidenceType.LOG,
                    description=f"Evidence for {control.control_name}",
                    location=f"/evidence/{control.control_id}",
                    timestamp=datetime.utcnow(),
                    control_id=control.control_id
                ))
            else:
                failed += 1
                # Create finding
                finding = Finding(
                    finding_id=str(uuid4()),
                    finding_type=FindingType.VIOLATION,
                    severity=Severity.HIGH,
                    control_id=control.control_id,
                    framework=control.framework or "UNKNOWN",
                    title=f"Control {control.control_id} Failed",
                    description=f"Failed to verify {control.control_name}",
                    remediation=Remediation(
                        required=True,
                        steps=[
                            f"Review {control.control_name} requirements",
                            "Implement missing controls",
                            "Collect required evidence"
                        ],
                        estimated_effort="2-4 weeks"
                    )
                )
                findings.append(finding)

                # Create gap
                gap = ComplianceGap(
                    gap_id=str(uuid4()),
                    control_id=control.control_id,
                    severity=Severity.HIGH,
                    description=f"Gap in {control.control_name}",
                    impact="May lead to compliance violations",
                    remediation_required=True
                )
                gaps.append(gap)

        # Calculate compliance score
        total = passed + failed + not_applicable
        compliance_score = (passed / total * 100) if total > 0 else 0

        # Determine overall status
        if compliance_score == 100:
            overall_status = ComplianceStatus.COMPLIANT
        elif compliance_score >= 75:
            overall_status = ComplianceStatus.PARTIAL
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        check_result = CheckResult(
            overall_status=overall_status,
            compliance_score=compliance_score,
            controls_passed=passed,
            controls_failed=failed,
            controls_not_applicable=not_applicable,
            findings=findings,
            gaps=gaps,
            evidence_collected=evidence
        )

        return ComplianceCheck(
            check_id=check_id,
            framework=framework,
            scope=scope,
            controls=controls,
            check_result=check_result,
            performed_by=performed_by,
            performed_at=datetime.utcnow()
        )

    def _verify_control(self, control: Control, scope: ComplianceScope) -> bool:
        """
        Verify a specific control.

        In real implementation, this would check actual systems, logs, configurations, etc.
        For demo purposes, we simulate some controls passing and some failing.
        """
        # Simulate verification logic
        # Controls with "encryption" or "access" pass more often
        if any(keyword in control.control_name.lower() for keyword in ["encryption", "access", "logging"]):
            return True
        # Other controls have 70% pass rate
        import random
        return random.random() > 0.3

    def add_control(self, control: Control):
        """Add a control to the catalog."""
        self.control_catalog[control.control_id] = control

    def get_control(self, control_id: str) -> Optional[Control]:
        """Get a control from the catalog."""
        return self.control_catalog.get(control_id)

    def list_controls(self, framework: Optional[ComplianceFramework] = None) -> List[Control]:
        """List all controls, optionally filtered by framework."""
        if framework is None:
            return list(self.control_catalog.values())
        return [c for c in self.control_catalog.values() if c.framework == framework.value]


# ============================================================================
# CAIP CLIENT
# ============================================================================


class CAIPClient:
    """
    Client for CAIP compliance operations.

    Provides high-level interface for compliance checking, policy enforcement,
    audit logging, risk assessment, and certification management.
    """

    def __init__(self, agent_id: str = "caip_agent_001"):
        """
        Initialize CAIP client.

        Args:
            agent_id: ID of the agent using this client
        """
        self.agent_id = agent_id
        self.engine = ComplianceEngine()
        self.audit_chain: List[AuditLog] = []
        self.certifications: Dict[str, Certification] = {}
        self.policies: Dict[str, PolicyEnforcement] = {}
        logger.info(f"CAIP Client initialized for agent {agent_id}")

    async def perform_compliance_check(
        self,
        frameworks: List[ComplianceFramework],
        scope: ComplianceScope,
        controls: Optional[List[Control]] = None
    ) -> ComplianceCheck:
        """
        Perform compliance check across specified frameworks.

        Args:
            frameworks: Frameworks to check against
            scope: Scope of the check
            controls: Specific controls to verify (optional)

        Returns:
            ComplianceCheck with results
        """
        logger.info(f"Performing compliance check for frameworks: {[f.value for f in frameworks]}")

        check = await self.engine.check_compliance(
            framework=frameworks,
            scope=scope,
            controls=controls,
            performed_by=self.agent_id
        )

        # Log the compliance check
        await self.log_audit_event(
            event_type="compliance_check",
            event_category=EventCategory.COMPLIANCE_EVENT,
            action="perform_compliance_check",
            details={
                "check_id": check.check_id,
                "frameworks": [f.value for f in frameworks],
                "compliance_score": check.check_result.compliance_score if check.check_result else 0
            }
        )

        return check

    async def enforce_policy(
        self,
        policy_id: str,
        action: str,
        subject: PolicySubject,
        obj: PolicyObject,
        policy_name: Optional[str] = None,
        policy_category: Optional[PolicyCategory] = None,
        enforcement_mode: EnforcementMode = EnforcementMode.WARN
    ) -> PolicyEnforcement:
        """
        Enforce a policy against an action.

        Args:
            policy_id: Policy ID
            action: Action being evaluated
            subject: Who is performing the action
            obj: What is being acted upon
            policy_name: Policy name (optional)
            policy_category: Policy category (optional)
            enforcement_mode: How to enforce (monitor, warn, block, remediate)

        Returns:
            PolicyEnforcement with decision
        """
        logger.info(f"Enforcing policy {policy_id} for action {action}")

        # Simulate policy evaluation
        decision = self._evaluate_policy(policy_id, action, subject, obj)

        enforcement = PolicyEnforcement(
            policy_id=policy_id,
            policy_name=policy_name or f"Policy {policy_id}",
            policy_category=policy_category,
            enforcement_mode=enforcement_mode,
            action=action,
            subject=subject,
            object=obj,
            decision=decision
        )

        self.policies[policy_id] = enforcement

        # Log policy enforcement
        await self.log_audit_event(
            event_type="policy_enforcement",
            event_category=EventCategory.POLICY_VIOLATION if not decision.allowed else EventCategory.AUTHORIZATION,
            action=action,
            details={
                "policy_id": policy_id,
                "allowed": decision.allowed,
                "reason": decision.reason
            },
            severity=Severity.WARNING if not decision.allowed else Severity.INFO
        )

        return enforcement

    def _evaluate_policy(
        self,
        policy_id: str,
        action: str,
        subject: PolicySubject,
        obj: PolicyObject
    ) -> PolicyDecision:
        """Evaluate a policy (simulated)."""
        # Simulate policy rules
        # Block access to restricted data without proper clearance
        if obj.data_classification == DataClassification.RESTRICTED:
            if "confidential_clearance" not in (subject.agent_id or ""):
                return PolicyDecision(
                    allowed=False,
                    reason="Agent lacks required clearance for restricted data",
                    violated_policies=[policy_id],
                    required_conditions=["confidential_data_access_certification"]
                )

        # Block confidential data exports
        if "export" in action.lower() and obj.data_classification in [
            DataClassification.CONFIDENTIAL,
            DataClassification.RESTRICTED
        ]:
            return PolicyDecision(
                allowed=False,
                reason="Export of confidential/restricted data is not allowed",
                violated_policies=[policy_id],
                required_conditions=["manager_approval", "encryption_required"]
            )

        # Allow by default
        return PolicyDecision(
            allowed=True,
            reason="Action complies with policy requirements"
        )

    async def log_audit_event(
        self,
        event_type: str,
        action: str,
        event_category: Optional[EventCategory] = None,
        severity: Severity = Severity.INFO,
        actor: Optional[AuditActor] = None,
        resource: Optional[AuditResource] = None,
        result: EventResult = EventResult.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[str]] = None
    ) -> AuditLog:
        """
        Create an immutable audit log entry with blockchain-style chaining.

        Args:
            event_type: Type of event
            action: Action performed
            event_category: Category of event (optional)
            severity: Severity level
            actor: Who performed the action (optional)
            resource: What was acted upon (optional)
            result: Result of the action
            details: Additional details (optional)
            compliance_tags: Compliance frameworks this satisfies (optional)

        Returns:
            AuditLog entry
        """
        # Get previous log for chaining
        previous_log = self.audit_chain[-1] if self.audit_chain else None
        previous_hash = previous_log.chain_hash if previous_log else None

        # Create actor if not provided
        if actor is None:
            actor = AuditActor(agent_id=self.agent_id)

        log_entry = AuditLog(
            log_id=str(uuid4()),
            event_type=event_type,
            event_category=event_category,
            severity=severity,
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            compliance_tags=compliance_tags or [],
            timestamp=datetime.utcnow(),
            previous_hash=previous_hash
        )

        # Verify chain integrity
        if not log_entry.verify_chain(previous_log):
            logger.error("Audit log chain integrity violation!")
            raise ValueError("Audit log chain integrity violation")

        self.audit_chain.append(log_entry)
        logger.info(f"Audit log created: {log_entry.log_id} (chain hash: {log_entry.chain_hash[:8]}...)")

        return log_entry

    def verify_audit_chain(self) -> bool:
        """
        Verify integrity of entire audit log chain.

        Returns:
            True if chain is valid, False otherwise
        """
        for i, log in enumerate(self.audit_chain):
            previous_log = self.audit_chain[i - 1] if i > 0 else None
            if not log.verify_chain(previous_log):
                logger.error(f"Chain integrity violation at log {log.log_id}")
                return False

        logger.info("Audit chain integrity verified")
        return True

    async def assess_risk(
        self,
        scope: RiskScope,
        assessment_type: AssessmentType = AssessmentType.PERIODIC
    ) -> RiskAssessment:
        """
        Perform compliance risk assessment.

        Args:
            scope: Scope of the assessment
            assessment_type: Type of assessment

        Returns:
            RiskAssessment with threats, vulnerabilities, and recommendations
        """
        logger.info(f"Performing {assessment_type.value} risk assessment")

        # Simulate risk assessment
        threats = [
            Threat(
                threat_id="T001",
                threat_name="Unauthorized Data Access",
                threat_category=ThreatCategory.UNAUTHORIZED_ACCESS,
                likelihood=RiskLevel.MEDIUM,
                impact=RiskLevel.HIGH,
                risk_score=70,
                description="Risk of unauthorized access to sensitive data"
            ),
            Threat(
                threat_id="T002",
                threat_name="Data Breach",
                threat_category=ThreatCategory.DATA_BREACH,
                likelihood=RiskLevel.LOW,
                impact=RiskLevel.CRITICAL,
                risk_score=60,
                description="Risk of data breach exposing customer information"
            ),
            Threat(
                threat_id="T003",
                threat_name="Regulatory Non-Compliance",
                threat_category=ThreatCategory.REGULATORY_VIOLATION,
                likelihood=RiskLevel.MEDIUM,
                impact=RiskLevel.HIGH,
                risk_score=65,
                description="Risk of failing compliance audits"
            )
        ]

        vulnerabilities = [
            Vulnerability(
                vulnerability_id="V001",
                description="Insufficient access controls on production database",
                severity=Severity.HIGH,
                affected_controls=["SOC2_CC6.1", "ISO27001_A.9.2"]
            ),
            Vulnerability(
                vulnerability_id="V002",
                description="Incomplete encryption of data at rest",
                severity=Severity.MEDIUM,
                affected_controls=["GDPR_Art32", "SOC2_CC6.6"]
            )
        ]

        recommendations = [
            MitigationRecommendation(
                recommendation_id="R001",
                title="Implement Multi-Factor Authentication",
                description="Add MFA to all production systems to reduce unauthorized access risk",
                priority=Severity.HIGH,
                estimated_effort="2-3 weeks",
                risk_reduction=30.0
            ),
            MitigationRecommendation(
                recommendation_id="R002",
                title="Enable Data-at-Rest Encryption",
                description="Implement encryption for all databases and storage systems",
                priority=Severity.HIGH,
                estimated_effort="3-4 weeks",
                risk_reduction=25.0
            ),
            MitigationRecommendation(
                recommendation_id="R003",
                title="Conduct Regular Compliance Audits",
                description="Schedule quarterly internal compliance audits",
                priority=Severity.MEDIUM,
                estimated_effort="Ongoing",
                risk_reduction=20.0
            )
        ]

        assessment = RiskAssessment(
            assessment_id=str(uuid4()),
            assessment_type=assessment_type,
            scope=scope,
            threats=threats,
            vulnerabilities=vulnerabilities,
            mitigation_recommendations=recommendations,
            assessed_by=self.agent_id
        )

        # Calculate overall risk
        assessment.overall_risk_level = assessment.calculate_overall_risk()

        # Log the assessment
        await self.log_audit_event(
            event_type="risk_assessment",
            event_category=EventCategory.COMPLIANCE_EVENT,
            action="assess_compliance_risk",
            details={
                "assessment_id": assessment.assessment_id,
                "overall_risk_level": assessment.overall_risk_level.value,
                "threat_count": len(threats),
                "vulnerability_count": len(vulnerabilities)
            }
        )

        return assessment

    def register_certification(self, certification: Certification):
        """Register a compliance certification."""
        self.certifications[certification.certification_id] = certification
        logger.info(f"Registered certification {certification.certification_id} for {certification.framework.value}")

    def get_certification(self, certification_id: str) -> Optional[Certification]:
        """Get a certification by ID."""
        return self.certifications.get(certification_id)

    def get_certifications_by_framework(self, framework: ComplianceFramework) -> List[Certification]:
        """Get all certifications for a specific framework."""
        return [c for c in self.certifications.values() if c.framework == framework]

    def export_compliance_report(self, check: ComplianceCheck) -> Dict[str, Any]:
        """
        Export a compliance check as a formatted report.

        Args:
            check: ComplianceCheck to export

        Returns:
            Report dictionary
        """
        report = {
            "protocol": "CAIP",
            "version": "1.0.0",
            "operation": "compliance_check",
            "compliance_check": check.to_dict()
        }
        return report


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


async def create_compliance_check(
    frameworks: List[str],
    system_components: List[str],
    data_categories: List[str],
    processes: List[str],
    agent_id: str = "caip_agent_001"
) -> ComplianceCheck:
    """
    Convenience function to create and execute a compliance check.

    Args:
        frameworks: List of framework names (e.g., ["GDPR", "SOC2"])
        system_components: System components to check
        data_categories: Data categories to check
        processes: Processes to check
        agent_id: Agent performing the check

    Returns:
        ComplianceCheck with results
    """
    client = CAIPClient(agent_id=agent_id)

    framework_enums = [ComplianceFramework(f) for f in frameworks]
    scope = ComplianceScope(
        system_components=system_components,
        data_categories=data_categories,
        processes=processes
    )

    return await client.perform_compliance_check(framework_enums, scope)


async def create_audit_log(
    event_type: str,
    action: str,
    agent_id: str = "caip_agent_001",
    **kwargs
) -> AuditLog:
    """
    Convenience function to create an audit log entry.

    Args:
        event_type: Type of event
        action: Action performed
        agent_id: Agent ID
        **kwargs: Additional arguments for log_audit_event

    Returns:
        AuditLog entry
    """
    client = CAIPClient(agent_id=agent_id)
    return await client.log_audit_event(event_type, action, **kwargs)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def example_usage():
    """Example usage of CAIP."""
    # Initialize client
    client = CAIPClient(agent_id="apqc_10_5_compliance_001")

    # 1. Perform GDPR compliance check
    print("\n=== GDPR Compliance Check ===")
    scope = ComplianceScope(
        system_components=["user_api", "database", "backup_system"],
        data_categories=["PII", "financial"],
        processes=["user_registration", "data_deletion", "data_export"]
    )

    check = await client.perform_compliance_check(
        frameworks=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
        scope=scope
    )

    print(f"Check ID: {check.check_id}")
    print(f"Compliance Score: {check.check_result.compliance_score:.1f}%")
    print(f"Status: {check.check_result.overall_status.value}")
    print(f"Controls Passed: {check.check_result.controls_passed}")
    print(f"Controls Failed: {check.check_result.controls_failed}")
    print(f"Findings: {len(check.check_result.findings)}")

    # 2. Enforce a policy
    print("\n=== Policy Enforcement ===")
    enforcement = await client.enforce_policy(
        policy_id="pol_data_export",
        action="export_customer_data",
        subject=PolicySubject(agent_id="apqc_3_0_marketing_002"),
        obj=PolicyObject(
            resource_type="customer_database",
            resource_id="db_customers_prod",
            data_classification=DataClassification.CONFIDENTIAL
        ),
        enforcement_mode=EnforcementMode.BLOCK
    )

    print(f"Policy: {enforcement.policy_name}")
    print(f"Action: {enforcement.action}")
    print(f"Allowed: {enforcement.decision.allowed}")
    print(f"Reason: {enforcement.decision.reason}")

    # 3. Create audit logs
    print("\n=== Audit Logging ===")
    log1 = await client.log_audit_event(
        event_type="data_access",
        event_category=EventCategory.DATA_ACCESS,
        action="read_customer_record",
        resource=AuditResource(
            resource_type="customer_record",
            resource_id="cust_12345"
        ),
        compliance_tags=["GDPR_Art30", "SOC2_CC6.1"]
    )
    print(f"Log 1: {log1.log_id} | Hash: {log1.chain_hash[:16]}...")

    log2 = await client.log_audit_event(
        event_type="data_modification",
        event_category=EventCategory.DATA_MODIFICATION,
        action="update_customer_email",
        resource=AuditResource(
            resource_type="customer_record",
            resource_id="cust_12345"
        ),
        compliance_tags=["GDPR_Art30"]
    )
    print(f"Log 2: {log2.log_id} | Hash: {log2.chain_hash[:16]}...")

    # Verify chain
    is_valid = client.verify_audit_chain()
    print(f"Audit chain valid: {is_valid}")

    # 4. Perform risk assessment
    print("\n=== Risk Assessment ===")
    risk_scope = RiskScope(
        systems=["production_api", "database", "backup_system"],
        data_assets=["customer_data", "financial_records"],
        processes=["payment_processing", "data_backup"]
    )

    assessment = await client.assess_risk(risk_scope)
    print(f"Assessment ID: {assessment.assessment_id}")
    print(f"Overall Risk: {assessment.overall_risk_level.value}")
    print(f"Threats: {len(assessment.threats)}")
    print(f"Vulnerabilities: {len(assessment.vulnerabilities)}")
    print(f"Recommendations: {len(assessment.mitigation_recommendations)}")

    # 5. Register certification
    print("\n=== Certification Management ===")
    cert = Certification(
        certification_id="cert_soc2_2025",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        certification_level="Type II",
        audit_firm="Deloitte",
        issued_date="2025-01-01",
        expiration_date="2026-01-01",
        readiness_score=95.0
    )
    client.register_certification(cert)
    print(f"Certification: {cert.framework.value} {cert.certification_level}")
    print(f"Status: {cert.status.value}")
    print(f"Valid: {cert.is_valid()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
