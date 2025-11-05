"""
ManageRegulatoryComplianceTransportationAgent - APQC 10.3.2
Manage Transportation Regulatory Compliance
APQC ID: apqc_10_3_r1e2g3c4

This agent manages regulatory compliance for ride-sharing operations including
license verification, insurance tracking, regulation monitoring, and audit preparation.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageRegulatoryComplianceTransportationAgentConfig:
    apqc_agent_id: str = "apqc_10_3_r1e2g3c4"
    apqc_process_id: str = "10.3.2"
    agent_name: str = "manage_regulatory_compliance_transportation_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class ManageRegulatoryComplianceTransportationAgent(BaseAgent, ProtocolMixin):
    """
    APQC 10.3.2 - Manage Regulatory Compliance

    Skills:
    - regulatory_tracking: 0.93 (multi-jurisdiction compliance)
    - audit_preparation: 0.90 (documentation and reporting)
    - violation_detection: 0.88 (proactive compliance monitoring)
    - compliance_scoring: 0.86 (risk assessment)

    Use Cases:
    - Track driver license compliance
    - Monitor insurance requirements
    - Ensure local regulation adherence
    - Prepare for regulatory audits
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "10.3.2"

    def __init__(self, config: ManageRegulatoryComplianceTransportationAgentConfig):
        super().__init__(agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version)
        self.config = config
        self.skills = {
            'regulatory_tracking': 0.93,
            'audit_preparation': 0.90,
            'violation_detection': 0.88,
            'compliance_scoring': 0.86
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage regulatory compliance

        Input:
        {
            "jurisdiction": "San Francisco, CA",
            "compliance_area": "transportation_network_company",
            "driver_fleet": {
                "total_drivers": 1500,
                "active_drivers_last_30_days": 1200
            },
            "license_status": {
                "valid_licenses": 1450,
                "expiring_within_30_days": 35,
                "expired": 15,
                "pending_verification": 20
            },
            "insurance_status": {
                "compliant_policies": 1420,
                "expiring_within_30_days": 50,
                "non_compliant": 30
            },
            "vehicle_inspections": {
                "passed": 1380,
                "due_within_30_days": 80,
                "overdue": 40
            },
            "local_regulations": {
                "max_hours_per_day": 12,
                "required_break_hours": 1,
                "background_check_frequency_months": 12,
                "vehicle_age_limit_years": 10
            },
            "violations": [
                {
                    "driver_id": "DRV123",
                    "violation_type": "hours_exceeded",
                    "date": "2025-10-15",
                    "severity": "minor"
                }
            ],
            "upcoming_audit": {
                "scheduled_date": "2025-11-15",
                "audit_type": "annual_compliance",
                "auditor": "City Transportation Department"
            }
        }
        """
        jurisdiction = input_data.get('jurisdiction')
        driver_fleet = input_data.get('driver_fleet', {})
        license_status = input_data.get('license_status', {})
        insurance_status = input_data.get('insurance_status', {})
        vehicle_inspections = input_data.get('vehicle_inspections', {})
        local_regulations = input_data.get('local_regulations', {})
        violations = input_data.get('violations', [])
        upcoming_audit = input_data.get('upcoming_audit', {})

        # Calculate compliance scores
        compliance_scores = self._calculate_compliance_scores(
            driver_fleet, license_status, insurance_status, vehicle_inspections
        )

        # Detect compliance violations
        violation_analysis = self._analyze_violations(violations, driver_fleet)

        # Generate compliance report
        compliance_report = self._generate_compliance_report(
            compliance_scores, license_status, insurance_status, vehicle_inspections
        )

        # Prepare for audit
        audit_preparation = self._prepare_audit_materials(
            compliance_scores, compliance_report, upcoming_audit
        )

        # Identify compliance risks
        compliance_risks = self._identify_compliance_risks(
            license_status, insurance_status, vehicle_inspections, violations
        )

        # Generate remediation actions
        remediation_actions = self._generate_remediation_actions(
            compliance_risks, compliance_scores
        )

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "jurisdiction": jurisdiction,
                "compliance_scores": compliance_scores,
                "violation_analysis": violation_analysis,
                "compliance_report": compliance_report,
                "audit_preparation": audit_preparation,
                "compliance_risks": compliance_risks,
                "remediation_actions": remediation_actions,
                "summary": {
                    "overall_compliance_score": compliance_scores['overall_score'],
                    "compliance_status": compliance_scores['status'],
                    "high_risk_areas": len([r for r in compliance_risks if r['risk_level'] == 'high']),
                    "audit_readiness": audit_preparation['readiness_percentage']
                }
            }
        }

    def _calculate_compliance_scores(
        self,
        driver_fleet: Dict,
        licenses: Dict,
        insurance: Dict,
        inspections: Dict
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive compliance scores
        """
        total_drivers = driver_fleet.get('total_drivers', 0)

        # License Compliance Score
        valid_licenses = licenses.get('valid_licenses', 0)
        license_compliance_rate = (valid_licenses / total_drivers) if total_drivers > 0 else 0
        license_score = license_compliance_rate * 100

        # Insurance Compliance Score
        compliant_insurance = insurance.get('compliant_policies', 0)
        insurance_compliance_rate = (compliant_insurance / total_drivers) if total_drivers > 0 else 0
        insurance_score = insurance_compliance_rate * 100

        # Vehicle Inspection Score
        passed_inspections = inspections.get('passed', 0)
        inspection_compliance_rate = (passed_inspections / total_drivers) if total_drivers > 0 else 0
        inspection_score = inspection_compliance_rate * 100

        # Calculate weighted overall score
        weights = {
            'license': 0.35,
            'insurance': 0.35,
            'inspection': 0.30
        }

        overall_score = (
            license_score * weights['license'] +
            insurance_score * weights['insurance'] +
            inspection_score * weights['inspection']
        )

        # Determine compliance status
        if overall_score >= 95:
            status = 'excellent'
        elif overall_score >= 90:
            status = 'good'
        elif overall_score >= 85:
            status = 'acceptable'
        elif overall_score >= 80:
            status = 'needs_improvement'
        else:
            status = 'critical'

        return {
            'overall_score': round(overall_score, 1),
            'status': status,
            'component_scores': {
                'license_compliance': round(license_score, 1),
                'insurance_compliance': round(insurance_score, 1),
                'inspection_compliance': round(inspection_score, 1)
            },
            'compliance_rates': {
                'license': round(license_compliance_rate, 3),
                'insurance': round(insurance_compliance_rate, 3),
                'inspection': round(inspection_compliance_rate, 3)
            },
            'meets_regulatory_threshold': overall_score >= 90
        }

    def _analyze_violations(
        self,
        violations: List[Dict],
        driver_fleet: Dict
    ) -> Dict[str, Any]:
        """
        Analyze compliance violations
        """
        total_drivers = driver_fleet.get('active_drivers_last_30_days', 0)
        total_violations = len(violations)

        # Categorize violations by type
        violation_by_type = {}
        violation_by_severity = {'minor': 0, 'moderate': 0, 'major': 0, 'critical': 0}

        for violation in violations:
            vtype = violation.get('violation_type', 'unknown')
            severity = violation.get('severity', 'minor')

            violation_by_type[vtype] = violation_by_type.get(vtype, 0) + 1
            violation_by_severity[severity] = violation_by_severity.get(severity, 0) + 1

        # Calculate violation rate
        violation_rate = (total_violations / total_drivers) if total_drivers > 0 else 0

        # Determine violation status
        if violation_rate < 0.01:
            violation_status = 'excellent'
        elif violation_rate < 0.03:
            violation_status = 'good'
        elif violation_rate < 0.05:
            violation_status = 'concerning'
        else:
            violation_status = 'critical'

        # Identify most common violation
        most_common = max(violation_by_type.items(), key=lambda x: x[1])[0] if violation_by_type else 'none'

        return {
            'total_violations': total_violations,
            'violation_rate': round(violation_rate, 4),
            'violation_status': violation_status,
            'violations_by_type': violation_by_type,
            'violations_by_severity': violation_by_severity,
            'most_common_violation': most_common,
            'critical_violations': violation_by_severity.get('critical', 0),
            'requires_immediate_action': violation_by_severity.get('critical', 0) > 0
        }

    def _generate_compliance_report(
        self,
        scores: Dict,
        licenses: Dict,
        insurance: Dict,
        inspections: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report
        """
        report_sections = []

        # License section
        license_section = {
            'section': 'Driver License Compliance',
            'compliance_percentage': scores['component_scores']['license_compliance'],
            'status': 'compliant' if scores['component_scores']['license_compliance'] >= 90 else 'non_compliant',
            'details': {
                'valid_licenses': licenses.get('valid_licenses', 0),
                'expiring_soon': licenses.get('expiring_within_30_days', 0),
                'expired': licenses.get('expired', 0),
                'pending_verification': licenses.get('pending_verification', 0)
            },
            'findings': []
        }

        if licenses.get('expired', 0) > 0:
            license_section['findings'].append(f"{licenses.get('expired', 0)} drivers have expired licenses")
        if licenses.get('expiring_within_30_days', 0) > 10:
            license_section['findings'].append(f"{licenses.get('expiring_within_30_days', 0)} licenses expiring soon")

        report_sections.append(license_section)

        # Insurance section
        insurance_section = {
            'section': 'Insurance Compliance',
            'compliance_percentage': scores['component_scores']['insurance_compliance'],
            'status': 'compliant' if scores['component_scores']['insurance_compliance'] >= 90 else 'non_compliant',
            'details': {
                'compliant_policies': insurance.get('compliant_policies', 0),
                'expiring_soon': insurance.get('expiring_within_30_days', 0),
                'non_compliant': insurance.get('non_compliant', 0)
            },
            'findings': []
        }

        if insurance.get('non_compliant', 0) > 0:
            insurance_section['findings'].append(f"{insurance.get('non_compliant', 0)} drivers lack proper insurance")
        if insurance.get('expiring_within_30_days', 0) > 20:
            insurance_section['findings'].append(f"{insurance.get('expiring_within_30_days', 0)} policies expiring soon")

        report_sections.append(insurance_section)

        # Vehicle inspection section
        inspection_section = {
            'section': 'Vehicle Inspection Compliance',
            'compliance_percentage': scores['component_scores']['inspection_compliance'],
            'status': 'compliant' if scores['component_scores']['inspection_compliance'] >= 90 else 'non_compliant',
            'details': {
                'passed_inspections': inspections.get('passed', 0),
                'due_soon': inspections.get('due_within_30_days', 0),
                'overdue': inspections.get('overdue', 0)
            },
            'findings': []
        }

        if inspections.get('overdue', 0) > 0:
            inspection_section['findings'].append(f"{inspections.get('overdue', 0)} vehicles have overdue inspections")

        report_sections.append(inspection_section)

        return {
            'report_date': datetime.now().isoformat(),
            'overall_compliance': scores['overall_score'],
            'compliance_status': scores['status'],
            'sections': report_sections,
            'total_findings': sum(len(s['findings']) for s in report_sections),
            'ready_for_audit': scores['overall_score'] >= 90
        }

    def _prepare_audit_materials(
        self,
        scores: Dict,
        report: Dict,
        audit_info: Dict
    ) -> Dict[str, Any]:
        """
        Prepare materials for regulatory audit
        """
        if not audit_info:
            return {
                'audit_scheduled': False,
                'readiness_percentage': scores['overall_score']
            }

        audit_date = audit_info.get('scheduled_date')
        days_until_audit = 0

        if audit_date:
            try:
                audit_datetime = datetime.fromisoformat(audit_date.replace('Z', '+00:00'))
                days_until_audit = (audit_datetime - datetime.now()).days
            except:
                days_until_audit = 0

        # Required documents checklist
        required_documents = [
            {
                'document': 'Driver license records',
                'status': 'complete' if scores['component_scores']['license_compliance'] >= 95 else 'incomplete',
                'completion_percentage': scores['component_scores']['license_compliance']
            },
            {
                'document': 'Insurance certificates',
                'status': 'complete' if scores['component_scores']['insurance_compliance'] >= 95 else 'incomplete',
                'completion_percentage': scores['component_scores']['insurance_compliance']
            },
            {
                'document': 'Vehicle inspection reports',
                'status': 'complete' if scores['component_scores']['inspection_compliance'] >= 95 else 'incomplete',
                'completion_percentage': scores['component_scores']['inspection_compliance']
            },
            {
                'document': 'Background check records',
                'status': 'complete',  # Assumed
                'completion_percentage': 100
            },
            {
                'document': 'Driver training certificates',
                'status': 'complete',  # Assumed
                'completion_percentage': 100
            },
            {
                'document': 'Compliance violation log',
                'status': 'complete',
                'completion_percentage': 100
            }
        ]

        # Calculate readiness
        complete_docs = sum(1 for doc in required_documents if doc['status'] == 'complete')
        readiness_percentage = (complete_docs / len(required_documents)) * 100

        # Determine readiness status
        if readiness_percentage >= 95:
            readiness_status = 'ready'
        elif readiness_percentage >= 85:
            readiness_status = 'nearly_ready'
        else:
            readiness_status = 'not_ready'

        # Identify gaps
        gaps = [doc['document'] for doc in required_documents if doc['status'] == 'incomplete']

        return {
            'audit_scheduled': True,
            'audit_date': audit_date,
            'days_until_audit': days_until_audit,
            'audit_type': audit_info.get('audit_type'),
            'auditor': audit_info.get('auditor'),
            'readiness_percentage': round(readiness_percentage, 1),
            'readiness_status': readiness_status,
            'required_documents': required_documents,
            'documentation_gaps': gaps,
            'urgent': days_until_audit < 14 and readiness_percentage < 95
        }

    def _identify_compliance_risks(
        self,
        licenses: Dict,
        insurance: Dict,
        inspections: Dict,
        violations: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Identify compliance risks
        """
        risks = []

        # Expired licenses risk
        expired_licenses = licenses.get('expired', 0)
        if expired_licenses > 0:
            risks.append({
                'risk_category': 'license_compliance',
                'risk_type': 'expired_licenses',
                'risk_level': 'high' if expired_licenses > 20 else 'medium',
                'affected_count': expired_licenses,
                'description': f"{expired_licenses} drivers operating with expired licenses",
                'potential_penalty': 'Fines, service suspension, legal liability',
                'mitigation_deadline_days': 7
            })

        # Insurance non-compliance risk
        non_compliant_insurance = insurance.get('non_compliant', 0)
        if non_compliant_insurance > 0:
            risks.append({
                'risk_category': 'insurance_compliance',
                'risk_type': 'inadequate_insurance',
                'risk_level': 'critical' if non_compliant_insurance > 30 else 'high',
                'affected_count': non_compliant_insurance,
                'description': f"{non_compliant_insurance} drivers lack adequate insurance coverage",
                'potential_penalty': 'Immediate service suspension, significant fines',
                'mitigation_deadline_days': 3
            })

        # Overdue inspections risk
        overdue_inspections = inspections.get('overdue', 0)
        if overdue_inspections > 0:
            risks.append({
                'risk_category': 'vehicle_safety',
                'risk_type': 'overdue_inspections',
                'risk_level': 'high' if overdue_inspections > 30 else 'medium',
                'affected_count': overdue_inspections,
                'description': f"{overdue_inspections} vehicles operating with overdue inspections",
                'potential_penalty': 'Safety violations, fines, vehicle impoundment',
                'mitigation_deadline_days': 14
            })

        # Critical violations risk
        critical_violations = sum(1 for v in violations if v.get('severity') == 'critical')
        if critical_violations > 0:
            risks.append({
                'risk_category': 'regulatory_violations',
                'risk_type': 'critical_violations',
                'risk_level': 'critical',
                'affected_count': critical_violations,
                'description': f"{critical_violations} critical regulatory violations recorded",
                'potential_penalty': 'Operating license suspension, heavy fines',
                'mitigation_deadline_days': 1
            })

        # Sort by risk level
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        risks.sort(key=lambda x: risk_order.get(x['risk_level'], 4))

        return risks

    def _generate_remediation_actions(
        self,
        risks: List[Dict],
        scores: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate remediation actions for compliance risks
        """
        actions = []

        # Actions for each identified risk
        for risk in risks:
            if risk['risk_type'] == 'expired_licenses':
                actions.append({
                    'action': 'Suspend drivers with expired licenses immediately',
                    'priority': 'urgent',
                    'responsible_team': 'driver_operations',
                    'due_days': 1,
                    'estimated_effort_hours': risk['affected_count'] * 0.5,
                    'related_risk': risk['risk_type']
                })
                actions.append({
                    'action': 'Send automated renewal reminders to drivers',
                    'priority': 'high',
                    'responsible_team': 'compliance_team',
                    'due_days': 3,
                    'estimated_effort_hours': 2,
                    'related_risk': risk['risk_type']
                })

            elif risk['risk_type'] == 'inadequate_insurance':
                actions.append({
                    'action': 'Immediately deactivate non-compliant drivers',
                    'priority': 'critical',
                    'responsible_team': 'compliance_team',
                    'due_days': 0,
                    'estimated_effort_hours': risk['affected_count'] * 0.25,
                    'related_risk': risk['risk_type']
                })

            elif risk['risk_type'] == 'overdue_inspections':
                actions.append({
                    'action': 'Schedule mandatory inspections for overdue vehicles',
                    'priority': 'high',
                    'responsible_team': 'vehicle_operations',
                    'due_days': 7,
                    'estimated_effort_hours': risk['affected_count'] * 1.0,
                    'related_risk': risk['risk_type']
                })

            elif risk['risk_type'] == 'critical_violations':
                actions.append({
                    'action': 'Investigate and document all critical violations',
                    'priority': 'urgent',
                    'responsible_team': 'legal_compliance',
                    'due_days': 1,
                    'estimated_effort_hours': risk['affected_count'] * 2.0,
                    'related_risk': risk['risk_type']
                })

        # General improvement actions if score is low
        if scores['overall_score'] < 90:
            actions.append({
                'action': 'Implement automated compliance monitoring system',
                'priority': 'medium',
                'responsible_team': 'technology_team',
                'due_days': 30,
                'estimated_effort_hours': 40,
                'related_risk': 'overall_compliance'
            })

        return actions

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["jurisdiction", "driver_fleet", "license_status"],
            "properties": {
                "jurisdiction": {"type": "string"},
                "driver_fleet": {"type": "object"},
                "license_status": {"type": "object"},
                "insurance_status": {"type": "object"},
                "vehicle_inspections": {"type": "object"},
                "local_regulations": {"type": "object"},
                "violations": {"type": "array"},
                "upcoming_audit": {"type": "object"}
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "compliance_scores": {"type": "object"},
                "violation_analysis": {"type": "object"},
                "compliance_report": {"type": "object"},
                "audit_preparation": {"type": "object"},
                "compliance_risks": {"type": "array"},
                "remediation_actions": {"type": "array"}
            }
        }


def create_manage_regulatory_compliance_transportation_agent() -> ManageRegulatoryComplianceTransportationAgent:
    """Factory function to create ManageRegulatoryComplianceTransportationAgent"""
    config = ManageRegulatoryComplianceTransportationAgentConfig()
    return ManageRegulatoryComplianceTransportationAgent(config)
