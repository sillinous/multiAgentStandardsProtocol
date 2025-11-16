#!/usr/bin/env python3
"""
CAIP v1.0 Compliance Automation Demo
=====================================

Demonstrates comprehensive compliance automation capabilities including:
- GDPR compliance checking (Right to Erasure, Data Protection)
- SOC2 control verification
- Policy enforcement with different modes
- Immutable audit logging with blockchain-style chaining
- Risk assessment and threat analysis
- Evidence collection
- Certification management

Author: SuperStandard Team
License: MIT
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.caip_v1 import (
    # Client and Engine
    CAIPClient,
    ComplianceEngine,
    # Enums
    ComplianceFramework,
    EnforcementMode,
    PolicyCategory,
    DataClassification,
    EventCategory,
    Severity,
    CertificationStatus,
    AssessmentType,
    # Data Models
    ComplianceScope,
    PolicySubject,
    PolicyObject,
    RiskScope,
    AuditActor,
    AuditResource,
    Certification,
    Control,
    ControlCategory,
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---\n")


async def demo_gdpr_compliance():
    """Demonstrate GDPR compliance checking."""
    print_section("1. GDPR COMPLIANCE CHECKING")

    client = CAIPClient(agent_id="apqc_10_5_compliance_agent_001")

    # Define scope for GDPR compliance check
    scope = ComplianceScope(
        system_components=[
            "user_api",
            "customer_database",
            "backup_system",
            "analytics_platform",
            "logging_service"
        ],
        data_categories=[
            "PII",  # Personally Identifiable Information
            "financial",
            "behavioral"
        ],
        processes=[
            "user_registration",
            "data_deletion",  # Right to Erasure
            "data_export",    # Right to Data Portability
            "consent_management",
            "breach_notification"
        ]
    )

    print("Performing GDPR compliance check...")
    print(f"Scope: {len(scope.system_components)} components, "
          f"{len(scope.data_categories)} data categories, "
          f"{len(scope.processes)} processes")

    check = await client.perform_compliance_check(
        frameworks=[ComplianceFramework.GDPR],
        scope=scope
    )

    print_subsection("Compliance Results")
    print(f"Check ID: {check.check_id}")
    print(f"Overall Status: {check.check_result.overall_status.value.upper()}")
    print(f"Compliance Score: {check.check_result.compliance_score:.1f}%")
    print(f"\nControl Summary:")
    print(f"  ✓ Passed: {check.check_result.controls_passed}")
    print(f"  ✗ Failed: {check.check_result.controls_failed}")
    print(f"  - Not Applicable: {check.check_result.controls_not_applicable}")

    # Show controls checked
    print_subsection("GDPR Controls Verified")
    for control in check.controls[:5]:  # Show first 5
        print(f"  • {control.control_id}: {control.control_name}")
        print(f"    Category: {control.control_category.value}")
        print(f"    Evidence Required: {', '.join(control.required_evidence)}")
        print()

    # Show findings if any
    if check.check_result.findings:
        print_subsection("Compliance Findings")
        for finding in check.check_result.findings[:3]:  # Show first 3
            print(f"  Finding: {finding.title}")
            print(f"  Severity: {finding.severity.value.upper()}")
            print(f"  Control: {finding.control_id}")
            print(f"  Description: {finding.description}")
            if finding.remediation:
                print(f"  Remediation Required: {'Yes' if finding.remediation.required else 'No'}")
                print(f"  Estimated Effort: {finding.remediation.estimated_effort}")
            print()

    # Show gaps
    if check.check_result.gaps:
        print_subsection("Compliance Gaps")
        for gap in check.check_result.gaps[:3]:  # Show first 3
            print(f"  Gap: {gap.description}")
            print(f"  Severity: {gap.severity.value.upper()}")
            print(f"  Impact: {gap.impact}")
            print(f"  Remediation Required: {'Yes' if gap.remediation_required else 'No'}")
            print()

    # Show evidence collected
    if check.check_result.evidence_collected:
        print_subsection("Evidence Collected")
        print(f"Total Evidence Items: {len(check.check_result.evidence_collected)}")
        for evidence in check.check_result.evidence_collected[:3]:  # Show first 3
            print(f"  • {evidence.description}")
            print(f"    Type: {evidence.evidence_type.value}")
            print(f"    Location: {evidence.location}")
            print(f"    Control: {evidence.control_id}")
            print()

    return client


async def demo_soc2_compliance(client: CAIPClient):
    """Demonstrate SOC2 compliance checking."""
    print_section("2. SOC2 CONTROL VERIFICATION")

    scope = ComplianceScope(
        system_components=[
            "production_api",
            "database_cluster",
            "monitoring_system",
            "backup_infrastructure"
        ],
        data_categories=["customer_data", "system_logs", "configuration_data"],
        processes=[
            "access_management",
            "change_management",
            "incident_response",
            "system_monitoring",
            "vendor_management"
        ]
    )

    print("Performing SOC2 Type II compliance check...")

    check = await client.perform_compliance_check(
        frameworks=[ComplianceFramework.SOC2],
        scope=scope
    )

    print_subsection("SOC2 Results")
    print(f"Trust Service Category: Common Criteria")
    print(f"Compliance Score: {check.check_result.compliance_score:.1f}%")
    print(f"Status: {check.check_result.overall_status.value.upper()}")

    print_subsection("SOC2 Controls Verified")
    soc2_controls = [c for c in check.controls if c.framework == "SOC2"]
    for control in soc2_controls[:4]:
        print(f"  • {control.control_id}: {control.control_name}")
        print(f"    Category: {control.control_category.value}")
        print()


async def demo_policy_enforcement(client: CAIPClient):
    """Demonstrate policy enforcement."""
    print_section("3. POLICY ENFORCEMENT")

    # Scenario 1: Allow - Public data access
    print_subsection("Scenario 1: Accessing Public Data")

    subject1 = PolicySubject(
        agent_id="apqc_9_2_financial_analyst_001",
        user_id="analyst_john"
    )

    obj1 = PolicyObject(
        resource_type="report",
        resource_id="quarterly_report_2025_q1",
        data_classification=DataClassification.PUBLIC
    )

    enforcement1 = await client.enforce_policy(
        policy_id="pol_data_access_001",
        policy_name="Data Access Control Policy",
        policy_category=PolicyCategory.ACCESS_CONTROL,
        action="view_report",
        subject=subject1,
        obj=obj1,
        enforcement_mode=EnforcementMode.MONITOR
    )

    print(f"Policy: {enforcement1.policy_name}")
    print(f"Action: {enforcement1.action}")
    print(f"Mode: {enforcement1.enforcement_mode.value}")
    print(f"Decision: {'✓ ALLOWED' if enforcement1.decision.allowed else '✗ BLOCKED'}")
    print(f"Reason: {enforcement1.decision.reason}")

    # Scenario 2: Warn - Confidential data access
    print_subsection("Scenario 2: Accessing Confidential Data")

    subject2 = PolicySubject(
        agent_id="apqc_3_0_marketing_002",
        user_id="marketing_sarah"
    )

    obj2 = PolicyObject(
        resource_type="customer_database",
        resource_id="db_customers_detailed",
        data_classification=DataClassification.CONFIDENTIAL
    )

    enforcement2 = await client.enforce_policy(
        policy_id="pol_data_classification_002",
        policy_name="Confidential Data Access Policy",
        policy_category=PolicyCategory.SECURITY,
        action="query_customer_data",
        subject=subject2,
        obj=obj2,
        enforcement_mode=EnforcementMode.WARN
    )

    print(f"Policy: {enforcement2.policy_name}")
    print(f"Action: {enforcement2.action}")
    print(f"Mode: {enforcement2.enforcement_mode.value}")
    print(f"Decision: {'✓ ALLOWED' if enforcement2.decision.allowed else '✗ BLOCKED'}")
    print(f"Reason: {enforcement2.decision.reason}")

    # Scenario 3: Block - Restricted data export
    print_subsection("Scenario 3: Exporting Restricted Data")

    subject3 = PolicySubject(
        agent_id="apqc_5_0_supplier_agent_003",
        user_id="external_vendor"
    )

    obj3 = PolicyObject(
        resource_type="financial_records",
        resource_id="db_financials_prod",
        data_classification=DataClassification.RESTRICTED
    )

    enforcement3 = await client.enforce_policy(
        policy_id="pol_data_export_003",
        policy_name="Data Export Restriction Policy",
        policy_category=PolicyCategory.DATA_GOVERNANCE,
        action="export_financial_data",
        subject=subject3,
        obj=obj3,
        enforcement_mode=EnforcementMode.BLOCK
    )

    print(f"Policy: {enforcement3.policy_name}")
    print(f"Action: {enforcement3.action}")
    print(f"Mode: {enforcement3.enforcement_mode.value}")
    print(f"Decision: {'✓ ALLOWED' if enforcement3.decision.allowed else '✗ BLOCKED'}")
    print(f"Reason: {enforcement3.decision.reason}")

    if not enforcement3.decision.allowed:
        print(f"Violated Policies: {', '.join(enforcement3.decision.violated_policies)}")
        print(f"Required Conditions: {', '.join(enforcement3.decision.required_conditions)}")


async def demo_audit_logging(client: CAIPClient):
    """Demonstrate immutable audit logging with blockchain-style chaining."""
    print_section("4. IMMUTABLE AUDIT LOGGING")

    print("Creating audit log chain with blockchain-style hashing...")

    # Create a series of audit logs
    logs = []

    # Log 1: User authentication
    print_subsection("Log 1: User Authentication")
    log1 = await client.log_audit_event(
        event_type="user_authentication",
        event_category=EventCategory.AUTHENTICATION,
        action="login_attempt",
        actor=AuditActor(
            user_id="user_12345",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        ),
        severity=Severity.INFO,
        details={
            "method": "multi_factor_authentication",
            "success": True
        },
        compliance_tags=["SOC2_CC6.1", "ISO27001_A.9.2"]
    )
    logs.append(log1)
    print(f"Log ID: {log1.log_id}")
    print(f"Event: {log1.event_type}")
    print(f"Chain Hash: {log1.chain_hash[:32]}...")
    print(f"Previous Hash: {log1.previous_hash or 'None (first log)'}")

    # Log 2: Data access
    print_subsection("Log 2: Customer Data Access")
    log2 = await client.log_audit_event(
        event_type="data_access",
        event_category=EventCategory.DATA_ACCESS,
        action="read_customer_financial_data",
        actor=AuditActor(
            agent_id="apqc_9_2_financial_001",
            user_id="user_12345"
        ),
        resource=AuditResource(
            resource_type="customer_record",
            resource_id="cust_67890",
            resource_name="Customer Financial Profile"
        ),
        details={
            "records_accessed": 1,
            "fields_accessed": ["balance", "transaction_history", "credit_score"],
            "purpose": "credit_risk_assessment",
            "retention_period_days": 2555  # 7 years
        },
        compliance_tags=["GDPR_Art30", "SOC2_CC6.1"]
    )
    logs.append(log2)
    print(f"Log ID: {log2.log_id}")
    print(f"Event: {log2.event_type}")
    print(f"Chain Hash: {log2.chain_hash[:32]}...")
    print(f"Previous Hash: {log2.previous_hash[:32]}...")
    print(f"Chain Valid: {'✓ Yes' if log2.verify_chain(log1) else '✗ No'}")

    # Log 3: Configuration change
    print_subsection("Log 3: Security Configuration Change")
    log3 = await client.log_audit_event(
        event_type="configuration_change",
        event_category=EventCategory.CONFIGURATION_CHANGE,
        action="update_firewall_rules",
        actor=AuditActor(
            agent_id="apqc_system_admin_001",
            user_id="admin_alice"
        ),
        resource=AuditResource(
            resource_type="firewall",
            resource_id="fw_prod_001",
            resource_name="Production Firewall"
        ),
        severity=Severity.WARNING,
        details={
            "rules_added": 3,
            "rules_modified": 1,
            "change_ticket": "CHG-2025-001234"
        },
        compliance_tags=["SOC2_CC6.6", "ISO27001_A.12.4"]
    )
    logs.append(log3)
    print(f"Log ID: {log3.log_id}")
    print(f"Event: {log3.event_type}")
    print(f"Severity: {log3.severity.value.upper()}")
    print(f"Chain Hash: {log3.chain_hash[:32]}...")

    # Log 4: Policy violation
    print_subsection("Log 4: Policy Violation Detected")
    log4 = await client.log_audit_event(
        event_type="policy_violation",
        event_category=EventCategory.POLICY_VIOLATION,
        action="unauthorized_data_export_attempt",
        actor=AuditActor(
            agent_id="apqc_3_0_marketing_002",
            user_id="user_99999"
        ),
        resource=AuditResource(
            resource_type="customer_database",
            resource_id="db_customers_prod"
        ),
        severity=Severity.CRITICAL,
        details={
            "violation_type": "unauthorized_export",
            "policy_id": "pol_data_export_003",
            "action_blocked": True,
            "records_attempted": 10000
        },
        compliance_tags=["GDPR_Art5", "SOC2_CC6.1"]
    )
    logs.append(log4)
    print(f"Log ID: {log4.log_id}")
    print(f"Event: {log4.event_type}")
    print(f"Severity: {log4.severity.value.upper()}")
    print(f"Action Blocked: {log4.details['action_blocked']}")

    # Verify entire audit chain
    print_subsection("Audit Chain Verification")
    print(f"Total Logs in Chain: {len(client.audit_chain)}")
    chain_valid = client.verify_audit_chain()
    print(f"Chain Integrity: {'✓ VALID' if chain_valid else '✗ COMPROMISED'}")

    # Show chain linkage
    print("\nChain Linkage:")
    for i, log in enumerate(logs):
        if i == 0:
            print(f"  Log {i + 1} (Genesis): {log.chain_hash[:16]}...")
        else:
            print(f"  Log {i + 1}: {log.chain_hash[:16]}... <- {log.previous_hash[:16]}...")


async def demo_risk_assessment(client: CAIPClient):
    """Demonstrate compliance risk assessment."""
    print_section("5. COMPLIANCE RISK ASSESSMENT")

    scope = RiskScope(
        systems=[
            "production_api",
            "customer_database",
            "payment_gateway",
            "backup_infrastructure",
            "third_party_integrations"
        ],
        data_assets=[
            "customer_PII",
            "financial_records",
            "payment_card_data",
            "healthcare_information",
            "proprietary_algorithms"
        ],
        processes=[
            "payment_processing",
            "data_backup_recovery",
            "third_party_data_sharing",
            "incident_response",
            "compliance_monitoring"
        ]
    )

    print("Performing comprehensive risk assessment...")
    print(f"Scope: {len(scope.systems)} systems, {len(scope.data_assets)} data assets, "
          f"{len(scope.processes)} processes")

    assessment = await client.assess_risk(
        scope=scope,
        assessment_type=AssessmentType.PERIODIC
    )

    print_subsection("Risk Assessment Results")
    print(f"Assessment ID: {assessment.assessment_id}")
    print(f"Assessment Type: {assessment.assessment_type.value}")
    print(f"Overall Risk Level: {assessment.overall_risk_level.value.upper()}")
    print(f"Assessed By: {assessment.assessed_by}")
    print(f"Assessed At: {assessment.assessed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Show threats
    print_subsection("Identified Threats")
    for threat in assessment.threats:
        print(f"  • {threat.threat_name} ({threat.threat_id})")
        print(f"    Category: {threat.threat_category.value}")
        print(f"    Likelihood: {threat.likelihood.value.upper()}")
        print(f"    Impact: {threat.impact.value.upper()}")
        print(f"    Risk Score: {threat.risk_score:.1f}/100")
        if threat.description:
            print(f"    Description: {threat.description}")
        print()

    # Show vulnerabilities
    print_subsection("Compliance Vulnerabilities")
    for vuln in assessment.vulnerabilities:
        print(f"  • {vuln.description}")
        print(f"    Severity: {vuln.severity.value.upper()}")
        print(f"    Affected Controls: {', '.join(vuln.affected_controls)}")
        print()

    # Show mitigation recommendations
    print_subsection("Mitigation Recommendations")
    # Sort by priority (critical first)
    priority_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
    sorted_recs = sorted(assessment.mitigation_recommendations,
                        key=lambda r: priority_order.get(r.priority, 4))

    for rec in sorted_recs:
        print(f"  [{rec.priority.value.upper()}] {rec.title}")
        print(f"    {rec.description}")
        print(f"    Estimated Effort: {rec.estimated_effort}")
        print(f"    Risk Reduction: {rec.risk_reduction}%")
        print()


async def demo_certification_management(client: CAIPClient):
    """Demonstrate certification management."""
    print_section("6. CERTIFICATION MANAGEMENT")

    # Register SOC2 Type II Certification
    print_subsection("SOC2 Type II Certification")

    soc2_cert = Certification(
        certification_id="cert_soc2_type2_2025",
        framework=ComplianceFramework.SOC2,
        status=CertificationStatus.ACHIEVED,
        certification_level="Type II",
        audit_firm="Deloitte & Touche LLP",
        issued_date="2025-01-15",
        expiration_date="2026-01-15",
        next_audit_date="2025-10-01",
        scope={
            "trust_service_categories": ["Security", "Availability", "Confidentiality"],
            "systems_covered": ["Production API", "Database", "Backup Systems"],
            "description": "Annual SOC2 Type II audit covering security controls"
        },
        certificate_url="https://certs.example.com/soc2-2025.pdf",
        readiness_score=95.5
    )

    client.register_certification(soc2_cert)

    print(f"Framework: {soc2_cert.framework.value}")
    print(f"Level: {soc2_cert.certification_level}")
    print(f"Status: {soc2_cert.status.value.upper()}")
    print(f"Audit Firm: {soc2_cert.audit_firm}")
    print(f"Issued: {soc2_cert.issued_date}")
    print(f"Expires: {soc2_cert.expiration_date}")
    print(f"Next Audit: {soc2_cert.next_audit_date}")
    print(f"Readiness Score: {soc2_cert.readiness_score:.1f}%")
    print(f"Valid: {'✓ Yes' if soc2_cert.is_valid() else '✗ No'}")
    print(f"Certificate URL: {soc2_cert.certificate_url}")

    # Register ISO27001 Certification
    print_subsection("ISO27001 Certification")

    iso_cert = Certification(
        certification_id="cert_iso27001_2025",
        framework=ComplianceFramework.ISO27001,
        status=CertificationStatus.MAINTAINED,
        certification_level="Information Security Management",
        audit_firm="BSI Group",
        issued_date="2024-03-01",
        expiration_date="2027-03-01",
        next_audit_date="2025-12-15",
        scope={
            "controls_implemented": ["A.9 Access Control", "A.12 Operations Security",
                                    "A.18 Compliance"],
            "locations": ["Primary Data Center", "DR Site"],
            "exclusions": "Physical security at office locations"
        },
        readiness_score=92.0
    )

    client.register_certification(iso_cert)

    print(f"Framework: {iso_cert.framework.value}")
    print(f"Status: {iso_cert.status.value.upper()}")
    print(f"Issued: {iso_cert.issued_date}")
    print(f"Expires: {iso_cert.expiration_date}")
    print(f"Readiness Score: {iso_cert.readiness_score:.1f}%")
    print(f"Valid: {'✓ Yes' if iso_cert.is_valid() else '✗ No'}")

    # Show all certifications
    print_subsection("All Active Certifications")
    all_certs = client.certifications.values()
    for cert in all_certs:
        print(f"  • {cert.framework.value}: {cert.status.value} "
              f"(expires {cert.expiration_date})")


async def demo_compliance_report_export(client: CAIPClient):
    """Demonstrate compliance report export."""
    print_section("7. COMPLIANCE REPORT EXPORT")

    # Perform a comprehensive multi-framework check
    scope = ComplianceScope(
        system_components=["api", "database", "logging", "monitoring"],
        data_categories=["PII", "financial", "healthcare"],
        processes=["data_processing", "access_control", "audit_logging"]
    )

    check = await client.perform_compliance_check(
        frameworks=[
            ComplianceFramework.GDPR,
            ComplianceFramework.SOC2,
            ComplianceFramework.HIPAA
        ],
        scope=scope
    )

    # Export report
    report = client.export_compliance_report(check)

    print("Exporting compliance report in CAIP format...")
    print_subsection("Report Structure")

    # Show report summary
    print(f"Protocol: {report['protocol']}")
    print(f"Version: {report['version']}")
    print(f"Operation: {report['operation']}")
    print(f"\nCheck ID: {report['compliance_check']['check_id']}")
    print(f"Frameworks: {', '.join(report['compliance_check']['framework'])}")
    print(f"Compliance Score: {report['compliance_check']['check_result']['compliance_score']:.1f}%")

    # Save to file
    output_file = Path(__file__).parent / "compliance_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Full report saved to: {output_file}")


async def main():
    """Run all CAIP demos."""
    print("\n" + "=" * 80)
    print("  CAIP v1.0 - Compliance Automation & Intelligence Protocol")
    print("  Comprehensive Demonstration")
    print("=" * 80)

    # Run all demos
    client = await demo_gdpr_compliance()
    await demo_soc2_compliance(client)
    await demo_policy_enforcement(client)
    await demo_audit_logging(client)
    await demo_risk_assessment(client)
    await demo_certification_management(client)
    await demo_compliance_report_export(client)

    # Final summary
    print_section("DEMONSTRATION SUMMARY")
    print(f"✓ GDPR Compliance Checking")
    print(f"✓ SOC2 Control Verification")
    print(f"✓ Policy Enforcement (Monitor, Warn, Block modes)")
    print(f"✓ Immutable Audit Logging with Blockchain-style Chaining")
    print(f"✓ Compliance Risk Assessment")
    print(f"✓ Certification Management")
    print(f"✓ Compliance Report Export")
    print(f"\nTotal Audit Logs Created: {len(client.audit_chain)}")
    print(f"Audit Chain Valid: {'✓ Yes' if client.verify_audit_chain() else '✗ No'}")
    print(f"Certifications Registered: {len(client.certifications)}")

    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
