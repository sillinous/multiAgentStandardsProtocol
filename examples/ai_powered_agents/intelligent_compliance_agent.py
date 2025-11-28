"""
Intelligent Compliance & Risk Management Agent - Example Implementation

Demonstrates AI-powered compliance and risk management capabilities:
- Regulatory compliance monitoring and assessment
- Policy violation detection and alerting
- Risk scoring and prioritization
- Audit trail generation and analysis
- Control effectiveness evaluation
- Compliance forecasting and gap analysis

This is a reference implementation showing best practices for
building AI-powered APQC-compliant risk and compliance agents.

APQC Categories:
- 10.0 Manage Enterprise Risk, Compliance, Remediation, & Resiliency
- 10.1 Manage enterprise risk
- 10.2 Manage compliance
- 10.3 Manage remediation efforts
- 10.4 Manage business resiliency
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import json


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_APPLICABLE = "not_applicable"


class RegulatoryFramework(Enum):
    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    CCPA = "ccpa"
    CUSTOM = "custom"


@dataclass
class ComplianceConfig:
    """Configuration for the Compliance & Risk Agent"""
    agent_id: str = "intelligent_compliance_001"
    agent_name: str = "Intelligent Compliance & Risk Agent"

    # AI Configuration
    ai_provider: str = "auto"
    confidence_threshold: float = 0.80
    max_analysis_depth: int = 3

    # Compliance Modes
    enable_regulatory_monitoring: bool = True
    enable_policy_monitoring: bool = True
    enable_risk_assessment: bool = True
    enable_audit_analysis: bool = True
    enable_control_testing: bool = True
    enable_gap_analysis: bool = True

    # Regulatory Frameworks
    active_frameworks: List[str] = field(default_factory=lambda: ["sox", "gdpr", "soc2"])

    # Thresholds
    risk_threshold: float = 0.6
    compliance_threshold: float = 0.9
    control_effectiveness_threshold: float = 0.8
    alert_on_violations: bool = True

    # Scheduling
    continuous_monitoring: bool = True
    assessment_frequency_days: int = 30


class IntelligentComplianceAgent:
    """
    AI-Powered Compliance & Risk Management Agent

    Capabilities:
    - Multi-framework regulatory compliance monitoring
    - Real-time policy violation detection
    - AI-driven risk scoring and prioritization
    - Automated audit trail analysis
    - Control testing and effectiveness scoring
    - Predictive compliance gap analysis

    Integration:
    - Uses smart_processing for risk analysis
    - Integrates with AIService for compliance reasoning
    - APQC Process: 10.0 - Manage Enterprise Risk
    """

    APQC_CATEGORY_ID = "10.0"
    APQC_PROCESS_IDS = ["10.1", "10.2", "10.3", "10.4"]

    def __init__(self, config: Optional[ComplianceConfig] = None):
        self.config = config or ComplianceConfig()
        self.compliance_cache = {}
        self.risk_register = {}
        self.violation_log = []
        self.state = {
            "assessments_performed": 0,
            "violations_detected": 0,
            "risks_identified": 0,
            "controls_tested": 0,
            "last_assessment": None
        }

    async def assess_compliance(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered compliance assessment

        Args:
            compliance_data: Dict containing:
                - policies: Active policies and procedures
                - controls: Implemented controls
                - audit_logs: Recent audit trail data
                - incidents: Security/compliance incidents
                - risk_register: Current risk register
                - framework_requirements: Specific framework requirements

        Returns:
            Comprehensive compliance assessment with AI-driven insights
        """
        from superstandard.services.smart_processing import get_processor
        from superstandard.services.ai_service import get_ai_service

        start_time = datetime.now()

        # Get processor and AI service
        processor = get_processor("operations")  # Risk/compliance uses operations
        ai_service = get_ai_service()

        results = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "apqc_category": self.APQC_CATEGORY_ID,
            "agent_id": self.config.agent_id,
            "frameworks_assessed": self.config.active_frameworks,
            "components": {}
        }

        # Step 1: Regulatory Compliance Assessment
        if self.config.enable_regulatory_monitoring:
            regulatory = await self._assess_regulatory_compliance(
                compliance_data.get("framework_requirements", {}),
                compliance_data.get("controls", []),
                ai_service
            )
            results["components"]["regulatory_compliance"] = regulatory

        # Step 2: Policy Monitoring
        if self.config.enable_policy_monitoring:
            policy = await self._monitor_policies(
                compliance_data.get("policies", []),
                compliance_data.get("audit_logs", []),
                ai_service
            )
            results["components"]["policy_compliance"] = policy

        # Step 3: Risk Assessment
        if self.config.enable_risk_assessment:
            risk = await self._assess_risks(
                compliance_data.get("risk_register", {}),
                compliance_data.get("incidents", []),
                ai_service
            )
            results["components"]["risk_assessment"] = risk

        # Step 4: Audit Analysis
        if self.config.enable_audit_analysis:
            audit = await self._analyze_audit_trails(
                compliance_data.get("audit_logs", []),
                processor
            )
            results["components"]["audit_analysis"] = audit

        # Step 5: Control Testing
        if self.config.enable_control_testing:
            controls = await self._test_controls(
                compliance_data.get("controls", []),
                ai_service
            )
            results["components"]["control_testing"] = controls

        # Step 6: Gap Analysis
        if self.config.enable_gap_analysis:
            gaps = await self._perform_gap_analysis(
                results["components"],
                ai_service
            )
            results["components"]["gap_analysis"] = gaps

        # Generate overall compliance score
        results["overall_compliance"] = self._calculate_overall_compliance(results["components"])

        # Generate recommendations
        results["recommendations"] = await self._generate_recommendations(results, ai_service)

        # Update state
        self.state["assessments_performed"] += 1
        self.state["last_assessment"] = datetime.now().isoformat()

        # Calculate processing time
        results["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000

        return results

    async def _assess_regulatory_compliance(
        self,
        requirements: Dict[str, Any],
        controls: List[Dict[str, Any]],
        ai_service
    ) -> Dict[str, Any]:
        """Assess compliance against regulatory frameworks"""

        framework_results = {}

        for framework in self.config.active_frameworks:
            framework_reqs = requirements.get(framework, {})

            # AI-powered compliance analysis
            compliance_analysis = await ai_service.analyze(
                prompt=f"""Assess compliance with {framework.upper()} framework:

                Requirements: {json.dumps(list(framework_reqs.keys())[:10])}
                Controls Implemented: {len(controls)}

                Evaluate:
                1. Coverage of key requirements
                2. Control mapping adequacy
                3. Evidence documentation status
                4. Known compliance gaps
                5. Risk areas requiring attention

                Provide compliance score (0-100) and detailed findings.
                """,
                data={"framework": framework, "requirements": framework_reqs}
            )

            compliance_score = compliance_analysis.get("compliance_score", 75)

            if compliance_score >= 90:
                status = ComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = ComplianceStatus.PARTIALLY_COMPLIANT
            else:
                status = ComplianceStatus.NON_COMPLIANT

            framework_results[framework] = {
                "framework": framework.upper(),
                "compliance_score": compliance_score,
                "status": status.value,
                "requirements_count": len(framework_reqs),
                "controls_mapped": compliance_analysis.get("controls_mapped", 0),
                "gaps_identified": compliance_analysis.get("gaps", []),
                "findings": compliance_analysis.get("findings", []),
                "recommendations": compliance_analysis.get("recommendations", [])
            }

        # Calculate aggregate score
        scores = [r["compliance_score"] for r in framework_results.values()]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "assessment_date": datetime.now().isoformat(),
            "frameworks_assessed": len(framework_results),
            "framework_results": framework_results,
            "aggregate_compliance_score": round(avg_score, 1),
            "critical_gaps": [
                g for f in framework_results.values()
                for g in f.get("gaps_identified", [])
                if g.get("severity") == "critical"
            ]
        }

    async def _monitor_policies(
        self,
        policies: List[Dict[str, Any]],
        audit_logs: List[Dict[str, Any]],
        ai_service
    ) -> Dict[str, Any]:
        """Monitor policy compliance and detect violations"""

        violations = []
        policy_status = {}

        for policy in policies[:20]:  # Limit for demo
            policy_id = policy.get("id", "unknown")
            policy_name = policy.get("name", policy_id)
            policy_rules = policy.get("rules", [])

            # Find related audit events
            related_events = [
                log for log in audit_logs
                if log.get("policy_id") == policy_id or
                any(rule in str(log) for rule in policy_rules[:5])
            ]

            # AI violation detection
            violation_analysis = await ai_service.analyze(
                prompt=f"""Analyze audit logs for policy violations:

                Policy: {policy_name}
                Rules: {json.dumps(policy_rules[:5])}
                Related Events: {len(related_events)}

                Identify:
                1. Potential violations
                2. Violation severity (critical/high/medium/low)
                3. Affected users/systems
                4. Remediation requirements
                """,
                data={"policy": policy, "events": related_events[:10]}
            )

            detected_violations = violation_analysis.get("violations", [])

            if detected_violations:
                violations.extend([
                    {
                        "policy_id": policy_id,
                        "policy_name": policy_name,
                        **v
                    }
                    for v in detected_violations
                ])
                self.state["violations_detected"] += len(detected_violations)

            policy_status[policy_id] = {
                "policy_name": policy_name,
                "status": "violated" if detected_violations else "compliant",
                "violation_count": len(detected_violations),
                "last_checked": datetime.now().isoformat()
            }

        # Log violations
        self.violation_log.extend(violations)

        return {
            "monitoring_date": datetime.now().isoformat(),
            "policies_monitored": len(policies),
            "policy_status": policy_status,
            "total_violations": len(violations),
            "violations_by_severity": {
                "critical": len([v for v in violations if v.get("severity") == "critical"]),
                "high": len([v for v in violations if v.get("severity") == "high"]),
                "medium": len([v for v in violations if v.get("severity") == "medium"]),
                "low": len([v for v in violations if v.get("severity") == "low"])
            },
            "recent_violations": violations[:10]
        }

    async def _assess_risks(
        self,
        risk_register: Dict[str, Any],
        incidents: List[Dict[str, Any]],
        ai_service
    ) -> Dict[str, Any]:
        """AI-powered risk assessment and prioritization"""

        risks = risk_register.get("risks", [])
        risk_assessments = []

        for risk in risks[:15]:  # Limit for demo
            risk_id = risk.get("id", "unknown")

            # Find related incidents
            related_incidents = [
                inc for inc in incidents
                if inc.get("risk_category") == risk.get("category")
            ]

            # AI risk analysis
            risk_analysis = await ai_service.assess_risk(
                scenario={
                    "risk_id": risk_id,
                    "risk_description": risk.get("description", ""),
                    "current_controls": risk.get("controls", []),
                    "historical_incidents": len(related_incidents),
                    "last_assessment": risk.get("last_assessment"),
                    "inherent_risk": risk.get("inherent_risk", 0.5)
                },
                risk_categories=["operational", "financial", "compliance", "reputational"]
            )

            residual_risk = risk_analysis.get("overall_risk_score", 0.5)

            if residual_risk >= 0.8:
                level = RiskLevel.CRITICAL
            elif residual_risk >= 0.6:
                level = RiskLevel.HIGH
            elif residual_risk >= 0.4:
                level = RiskLevel.MEDIUM
            elif residual_risk >= 0.2:
                level = RiskLevel.LOW
            else:
                level = RiskLevel.MINIMAL

            risk_assessments.append({
                "risk_id": risk_id,
                "risk_name": risk.get("name", risk_id),
                "category": risk.get("category", "general"),
                "residual_risk_score": round(residual_risk, 2),
                "risk_level": level.value,
                "trend": risk_analysis.get("trend", "stable"),
                "key_factors": risk_analysis.get("key_concerns", []),
                "mitigations": risk_analysis.get("mitigations", []),
                "related_incidents": len(related_incidents)
            })

            # Update risk register cache
            self.risk_register[risk_id] = residual_risk

        # Sort by risk score (highest first)
        risk_assessments.sort(key=lambda x: x["residual_risk_score"], reverse=True)
        self.state["risks_identified"] += len(risk_assessments)

        return {
            "assessment_date": datetime.now().isoformat(),
            "risks_assessed": len(risk_assessments),
            "risk_assessments": risk_assessments,
            "risk_distribution": {
                "critical": len([r for r in risk_assessments if r["risk_level"] == "critical"]),
                "high": len([r for r in risk_assessments if r["risk_level"] == "high"]),
                "medium": len([r for r in risk_assessments if r["risk_level"] == "medium"]),
                "low": len([r for r in risk_assessments if r["risk_level"] == "low"]),
                "minimal": len([r for r in risk_assessments if r["risk_level"] == "minimal"])
            },
            "top_risks": risk_assessments[:5],
            "average_risk_score": round(
                sum(r["residual_risk_score"] for r in risk_assessments) / len(risk_assessments)
                if risk_assessments else 0,
                2
            )
        }

    async def _analyze_audit_trails(
        self,
        audit_logs: List[Dict[str, Any]],
        processor
    ) -> Dict[str, Any]:
        """Analyze audit trails for anomalies and patterns"""

        # Process audit logs
        analysis_result = await processor.process(
            {
                "audit_logs": audit_logs[:100],
                "analysis_type": "audit_trail"
            },
            task_type="audit_analysis"
        )

        # Categorize events
        event_categories = {}
        for log in audit_logs:
            category = log.get("category", "general")
            event_categories[category] = event_categories.get(category, 0) + 1

        # Identify anomalies
        anomalies = []
        for log in audit_logs:
            if log.get("risk_flag") or log.get("severity") == "critical":
                anomalies.append({
                    "timestamp": log.get("timestamp"),
                    "event": log.get("event"),
                    "user": log.get("user"),
                    "severity": log.get("severity", "medium")
                })

        return {
            "analysis_date": datetime.now().isoformat(),
            "logs_analyzed": len(audit_logs),
            "event_categories": event_categories,
            "anomalies_detected": len(anomalies),
            "anomaly_details": anomalies[:10],
            "patterns": analysis_result.get("result", {}).get("patterns", []),
            "high_risk_activities": [
                log for log in audit_logs
                if log.get("risk_level") in ["high", "critical"]
            ][:10]
        }

    async def _test_controls(
        self,
        controls: List[Dict[str, Any]],
        ai_service
    ) -> Dict[str, Any]:
        """Test control effectiveness"""

        control_results = []

        for control in controls[:15]:  # Limit for demo
            control_id = control.get("id", "unknown")

            # AI control effectiveness analysis
            effectiveness_analysis = await ai_service.analyze(
                prompt=f"""Evaluate control effectiveness:

                Control: {control.get('name', control_id)}
                Type: {control.get('type', 'preventive')}
                Implementation: {control.get('implementation_status', 'unknown')}
                Last Tested: {control.get('last_test_date', 'never')}
                Test Results: {control.get('test_results', 'none')}

                Assess:
                1. Design effectiveness (0-100)
                2. Operating effectiveness (0-100)
                3. Coverage adequacy
                4. Improvement recommendations
                """,
                data={"control": control}
            )

            design_score = effectiveness_analysis.get("design_effectiveness", 75)
            operating_score = effectiveness_analysis.get("operating_effectiveness", 70)
            overall_score = (design_score + operating_score) / 2

            control_results.append({
                "control_id": control_id,
                "control_name": control.get("name", control_id),
                "control_type": control.get("type", "preventive"),
                "design_effectiveness": design_score,
                "operating_effectiveness": operating_score,
                "overall_effectiveness": round(overall_score, 1),
                "status": "effective" if overall_score >= self.config.control_effectiveness_threshold * 100 else "needs_improvement",
                "recommendations": effectiveness_analysis.get("recommendations", [])
            })

        self.state["controls_tested"] += len(control_results)

        # Calculate statistics
        effective_controls = len([c for c in control_results if c["status"] == "effective"])

        return {
            "testing_date": datetime.now().isoformat(),
            "controls_tested": len(control_results),
            "control_results": control_results,
            "effective_controls": effective_controls,
            "effectiveness_rate": round(effective_controls / len(control_results) * 100, 1) if control_results else 0,
            "average_effectiveness": round(
                sum(c["overall_effectiveness"] for c in control_results) / len(control_results)
                if control_results else 0,
                1
            ),
            "controls_needing_improvement": [
                c for c in control_results if c["status"] == "needs_improvement"
            ]
        }

    async def _perform_gap_analysis(
        self,
        assessment_components: Dict[str, Any],
        ai_service
    ) -> Dict[str, Any]:
        """Perform comprehensive gap analysis"""

        # Gather findings from all components
        regulatory_gaps = assessment_components.get("regulatory_compliance", {}).get("critical_gaps", [])
        policy_violations = assessment_components.get("policy_compliance", {}).get("total_violations", 0)
        high_risks = assessment_components.get("risk_assessment", {}).get("risk_distribution", {}).get("high", 0)
        control_gaps = len(assessment_components.get("control_testing", {}).get("controls_needing_improvement", []))

        # AI gap analysis
        gap_analysis = await ai_service.analyze(
            prompt=f"""Perform comprehensive compliance gap analysis:

            Regulatory Gaps: {len(regulatory_gaps)}
            Policy Violations: {policy_violations}
            High/Critical Risks: {high_risks}
            Control Deficiencies: {control_gaps}

            Provide:
            1. Priority ranking of gaps
            2. Root cause analysis
            3. Remediation roadmap
            4. Resource requirements
            5. Timeline recommendations
            """,
            data={"components": assessment_components}
        )

        return {
            "analysis_date": datetime.now().isoformat(),
            "total_gaps_identified": len(regulatory_gaps) + control_gaps,
            "gap_summary": {
                "regulatory": len(regulatory_gaps),
                "policy": policy_violations,
                "risk": high_risks,
                "control": control_gaps
            },
            "priority_ranking": gap_analysis.get("priority_ranking", []),
            "root_causes": gap_analysis.get("root_causes", []),
            "remediation_roadmap": gap_analysis.get("remediation_roadmap", []),
            "estimated_effort": gap_analysis.get("effort_estimate", "medium"),
            "recommended_timeline": gap_analysis.get("timeline", "90 days")
        }

    def _calculate_overall_compliance(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compliance score"""

        scores = []

        # Regulatory compliance score
        if "regulatory_compliance" in components:
            scores.append(components["regulatory_compliance"].get("aggregate_compliance_score", 0))

        # Control effectiveness
        if "control_testing" in components:
            scores.append(components["control_testing"].get("average_effectiveness", 0))

        # Risk score (inverted - lower risk = higher compliance)
        if "risk_assessment" in components:
            avg_risk = components["risk_assessment"].get("average_risk_score", 0.5)
            scores.append((1 - avg_risk) * 100)

        overall_score = sum(scores) / len(scores) if scores else 0

        if overall_score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT

        return {
            "overall_score": round(overall_score, 1),
            "status": status.value,
            "component_scores": {
                "regulatory": components.get("regulatory_compliance", {}).get("aggregate_compliance_score", 0),
                "controls": components.get("control_testing", {}).get("average_effectiveness", 0),
                "risk_adjusted": round((1 - components.get("risk_assessment", {}).get("average_risk_score", 0.5)) * 100, 1)
            }
        }

    async def _generate_recommendations(
        self,
        assessment_results: Dict[str, Any],
        ai_service
    ) -> List[Dict[str, Any]]:
        """Generate prioritized compliance recommendations"""

        overall = assessment_results.get("overall_compliance", {})
        components = assessment_results.get("components", {})

        recommendations = await ai_service.generate_recommendations(
            context={
                "overall_compliance_score": overall.get("overall_score", 0),
                "compliance_status": overall.get("status", "unknown"),
                "critical_gaps": len(components.get("gap_analysis", {}).get("priority_ranking", [])),
                "high_risks": components.get("risk_assessment", {}).get("risk_distribution", {}).get("high", 0),
                "control_deficiencies": len(components.get("control_testing", {}).get("controls_needing_improvement", []))
            },
            constraints=["actionable", "prioritized", "compliance_focused"],
            max_recommendations=5
        )

        return [
            {
                "id": i + 1,
                "action": rec.get("action", ""),
                "priority": rec.get("priority", "medium"),
                "impact": rec.get("impact", "unknown"),
                "category": rec.get("category", "compliance"),
                "rationale": rec.get("rationale", ""),
                "effort": rec.get("effort", "medium")
            }
            for i, rec in enumerate(recommendations)
        ]

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state and statistics"""
        return {
            **self.state,
            "config": {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name,
                "active_frameworks": self.config.active_frameworks,
                "continuous_monitoring": self.config.continuous_monitoring
            },
            "risk_register_size": len(self.risk_register),
            "violation_log_size": len(self.violation_log)
        }


# =============================================================================
# Example Usage
# =============================================================================

async def demo_compliance_agent():
    """Demonstrate the Compliance & Risk Agent"""

    print("=" * 60)
    print("Intelligent Compliance & Risk Agent Demo")
    print("=" * 60)

    # Create agent with custom config
    config = ComplianceConfig(
        agent_name="Demo Compliance Agent",
        active_frameworks=["sox", "gdpr", "soc2"],
        risk_threshold=0.5,
        compliance_threshold=0.85
    )

    agent = IntelligentComplianceAgent(config)

    # Sample compliance data
    compliance_data = {
        "framework_requirements": {
            "sox": {
                "financial_reporting": "accurate financial statements",
                "internal_controls": "effective internal controls",
                "audit_committee": "independent audit committee"
            },
            "gdpr": {
                "data_protection": "protect personal data",
                "consent": "obtain valid consent",
                "data_portability": "enable data portability"
            },
            "soc2": {
                "security": "system security controls",
                "availability": "system availability controls",
                "confidentiality": "data confidentiality controls"
            }
        },
        "controls": [
            {"id": "CTL-001", "name": "Access Control", "type": "preventive", "implementation_status": "implemented"},
            {"id": "CTL-002", "name": "Change Management", "type": "preventive", "implementation_status": "implemented"},
            {"id": "CTL-003", "name": "Incident Response", "type": "detective", "implementation_status": "partial"},
            {"id": "CTL-004", "name": "Data Encryption", "type": "preventive", "implementation_status": "implemented"},
            {"id": "CTL-005", "name": "Backup & Recovery", "type": "corrective", "implementation_status": "implemented"}
        ],
        "policies": [
            {"id": "POL-001", "name": "Data Protection Policy", "rules": ["encrypt_pii", "access_logging"]},
            {"id": "POL-002", "name": "Acceptable Use Policy", "rules": ["authorized_access", "no_sharing"]},
            {"id": "POL-003", "name": "Incident Response Policy", "rules": ["report_24h", "escalation"]}
        ],
        "audit_logs": [
            {"timestamp": "2025-01-15T10:00:00", "event": "login", "user": "admin", "category": "access"},
            {"timestamp": "2025-01-15T10:30:00", "event": "data_export", "user": "analyst", "category": "data", "risk_flag": True},
            {"timestamp": "2025-01-15T11:00:00", "event": "config_change", "user": "admin", "category": "system", "severity": "high"}
        ],
        "risk_register": {
            "risks": [
                {"id": "RISK-001", "name": "Data Breach", "category": "security", "inherent_risk": 0.7, "controls": ["CTL-001", "CTL-004"]},
                {"id": "RISK-002", "name": "System Downtime", "category": "operational", "inherent_risk": 0.5, "controls": ["CTL-005"]},
                {"id": "RISK-003", "name": "Regulatory Fine", "category": "compliance", "inherent_risk": 0.6, "controls": ["CTL-002"]}
            ]
        },
        "incidents": [
            {"id": "INC-001", "type": "security", "risk_category": "security", "severity": "medium"}
        ]
    }

    print("\n1. Running comprehensive compliance assessment...")
    results = await agent.assess_compliance(compliance_data)

    print(f"\n   Status: {results['status']}")
    print(f"   AI-Powered: {results['ai_powered']}")
    print(f"   Processing Time: {results['processing_time_ms']:.1f}ms")
    print(f"   Frameworks Assessed: {', '.join(results['frameworks_assessed'])}")

    # Print overall compliance
    overall = results.get("overall_compliance", {})
    print(f"\n2. Overall Compliance:")
    print(f"   - Score: {overall['overall_score']}%")
    print(f"   - Status: {overall['status'].upper()}")

    # Print component summaries
    components = results.get("components", {})

    if "regulatory_compliance" in components:
        reg = components["regulatory_compliance"]
        print(f"\n3. Regulatory Compliance:")
        print(f"   - Frameworks Assessed: {reg['frameworks_assessed']}")
        print(f"   - Aggregate Score: {reg['aggregate_compliance_score']}%")

    if "risk_assessment" in components:
        risk = components["risk_assessment"]
        print(f"\n4. Risk Assessment:")
        print(f"   - Risks Assessed: {risk['risks_assessed']}")
        print(f"   - Average Risk Score: {risk['average_risk_score']}")
        print(f"   - High/Critical Risks: {risk['risk_distribution']['high'] + risk['risk_distribution']['critical']}")

    if "control_testing" in components:
        ctrl = components["control_testing"]
        print(f"\n5. Control Testing:")
        print(f"   - Controls Tested: {ctrl['controls_tested']}")
        print(f"   - Effectiveness Rate: {ctrl['effectiveness_rate']}%")

    if "gap_analysis" in components:
        gap = components["gap_analysis"]
        print(f"\n6. Gap Analysis:")
        print(f"   - Total Gaps: {gap['total_gaps_identified']}")
        print(f"   - Recommended Timeline: {gap['recommended_timeline']}")

    # Print recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n7. AI Recommendations ({len(recommendations)}):")
        for rec in recommendations[:3]:
            print(f"   [{rec['priority'].upper()}] {rec['action']}")

    # Print agent state
    print(f"\n8. Agent State:")
    state = agent.get_state()
    print(f"   - Assessments Performed: {state['assessments_performed']}")
    print(f"   - Violations Detected: {state['violations_detected']}")
    print(f"   - Risks Identified: {state['risks_identified']}")
    print(f"   - Controls Tested: {state['controls_tested']}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(demo_compliance_agent())
