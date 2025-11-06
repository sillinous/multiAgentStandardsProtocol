"""
OnboardDriversHumanCapitalAgent - APQC 7.1.2
Driver Onboarding and Compliance Verification
APQC ID: apqc_7_1_o1n2b3d4

This agent manages the complete driver onboarding process including background checks,
document verification, training completion tracking, and readiness assessment.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class OnboardDriversHumanCapitalAgentConfig:
    apqc_agent_id: str = "apqc_7_1_o1n2b3d4"
    apqc_process_id: str = "7.1.2"
    agent_name: str = "onboard_drivers_human_capital_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class OnboardDriversHumanCapitalAgent(BaseAgent, ProtocolMixin):
    """
    APQC 7.1.2 - Onboard Drivers

    Skills:
    - compliance_verification: 0.90 (regulatory compliance checking)
    - readiness_assessment: 0.88 (driver qualification scoring)
    - document_validation: 0.86 (automated document verification)
    - background_check: 0.84 (risk assessment and screening)

    Use Cases:
    - Process driver applications
    - Verify licenses and insurance
    - Conduct background checks
    - Track training completion
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "7.1.2"

    def __init__(self, config: OnboardDriversHumanCapitalAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "compliance_verification": 0.90,
            "readiness_assessment": 0.88,
            "document_validation": 0.86,
            "background_check": 0.84,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process driver onboarding

        Input:
        {
            "applicant": {
                "applicant_id": "APP12345",
                "name": "John Driver",
                "email": "john@example.com",
                "phone": "+1-555-0123",
                "application_date": "2025-10-15T10:00:00"
            },
            "documents": {
                "drivers_license": {
                    "number": "D1234567",
                    "state": "CA",
                    "expiration_date": "2027-10-18",
                    "verified": true
                },
                "insurance": {
                    "policy_number": "INS789456",
                    "expiration_date": "2026-06-01",
                    "verified": true
                },
                "vehicle_registration": {
                    "plate_number": "ABC123",
                    "expiration_date": "2026-03-15",
                    "verified": true
                }
            },
            "background_check": {
                "criminal_record": "clear",
                "driving_record_points": 0,
                "accidents_last_3_years": 0,
                "completed_date": "2025-10-16T14:30:00"
            },
            "training": {
                "platform_training_completed": true,
                "safety_training_completed": true,
                "customer_service_training_completed": false,
                "completion_percentage": 66
            },
            "vehicle_inspection": {
                "passed": true,
                "inspection_date": "2025-10-17T09:00:00",
                "issues": []
            }
        }
        """
        applicant = input_data.get("applicant", {})
        documents = input_data.get("documents", {})
        background_check = input_data.get("background_check", {})
        training = input_data.get("training", {})
        vehicle_inspection = input_data.get("vehicle_inspection", {})

        # Verify compliance requirements
        compliance_status = self._verify_compliance(documents, background_check, vehicle_inspection)

        # Validate documents
        document_validation = self._validate_documents(documents)

        # Assess background check results
        background_assessment = self._assess_background_check(background_check)

        # Evaluate training completion
        training_status = self._evaluate_training(training)

        # Calculate overall readiness score
        readiness_score = self._calculate_readiness_score(
            compliance_status, document_validation, background_assessment, training_status
        )

        # Generate onboarding decision
        decision = self._generate_onboarding_decision(
            readiness_score, compliance_status, training_status
        )

        # Create action items
        action_items = self._generate_action_items(
            compliance_status, document_validation, training_status
        )

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "applicant_id": applicant.get("applicant_id"),
                "compliance_status": compliance_status,
                "document_validation": document_validation,
                "background_assessment": background_assessment,
                "training_status": training_status,
                "readiness_score": readiness_score,
                "onboarding_decision": decision,
                "action_items": action_items,
                "summary": {
                    "decision": decision["status"],
                    "readiness_percentage": readiness_score["overall_percentage"],
                    "pending_items": len(action_items),
                    "estimated_completion_date": decision.get("estimated_activation_date"),
                },
            },
        }

    def _verify_compliance(
        self,
        documents: Dict[str, Any],
        background_check: Dict[str, Any],
        vehicle_inspection: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify all compliance requirements are met
        """
        requirements = []

        # Driver's License Compliance
        license = documents.get("drivers_license", {})
        license_valid = self._check_document_expiration(license.get("expiration_date"))

        requirements.append(
            {
                "requirement": "valid_drivers_license",
                "category": "documentation",
                "status": (
                    "compliant" if license.get("verified") and license_valid else "non_compliant"
                ),
                "verified": license.get("verified", False),
                "expiration_date": license.get("expiration_date"),
                "days_until_expiration": self._days_until_expiration(
                    license.get("expiration_date")
                ),
            }
        )

        # Insurance Compliance
        insurance = documents.get("insurance", {})
        insurance_valid = self._check_document_expiration(insurance.get("expiration_date"))

        requirements.append(
            {
                "requirement": "valid_insurance",
                "category": "documentation",
                "status": (
                    "compliant"
                    if insurance.get("verified") and insurance_valid
                    else "non_compliant"
                ),
                "verified": insurance.get("verified", False),
                "expiration_date": insurance.get("expiration_date"),
                "days_until_expiration": self._days_until_expiration(
                    insurance.get("expiration_date")
                ),
            }
        )

        # Vehicle Registration Compliance
        registration = documents.get("vehicle_registration", {})
        registration_valid = self._check_document_expiration(registration.get("expiration_date"))

        requirements.append(
            {
                "requirement": "valid_vehicle_registration",
                "category": "documentation",
                "status": (
                    "compliant"
                    if registration.get("verified") and registration_valid
                    else "non_compliant"
                ),
                "verified": registration.get("verified", False),
                "expiration_date": registration.get("expiration_date"),
                "days_until_expiration": self._days_until_expiration(
                    registration.get("expiration_date")
                ),
            }
        )

        # Background Check Compliance
        criminal_clear = background_check.get("criminal_record") == "clear"
        driving_points = background_check.get("driving_record_points", 0)
        accidents = background_check.get("accidents_last_3_years", 0)

        background_compliant = criminal_clear and driving_points <= 3 and accidents <= 1

        requirements.append(
            {
                "requirement": "background_check",
                "category": "background",
                "status": "compliant" if background_compliant else "non_compliant",
                "criminal_record": background_check.get("criminal_record"),
                "driving_points": driving_points,
                "accidents": accidents,
                "completed": background_check.get("completed_date") is not None,
            }
        )

        # Vehicle Inspection Compliance
        inspection_passed = vehicle_inspection.get("passed", False)

        requirements.append(
            {
                "requirement": "vehicle_inspection",
                "category": "vehicle",
                "status": "compliant" if inspection_passed else "non_compliant",
                "passed": inspection_passed,
                "inspection_date": vehicle_inspection.get("inspection_date"),
                "issues": vehicle_inspection.get("issues", []),
            }
        )

        # Calculate overall compliance
        compliant_count = sum(1 for r in requirements if r["status"] == "compliant")
        compliance_percentage = (compliant_count / len(requirements) * 100) if requirements else 0

        overall_status = (
            "fully_compliant" if compliant_count == len(requirements) else "partially_compliant"
        )

        return {
            "requirements": requirements,
            "compliant_count": compliant_count,
            "total_requirements": len(requirements),
            "compliance_percentage": round(compliance_percentage, 1),
            "overall_status": overall_status,
        }

    def _check_document_expiration(self, expiration_date: Optional[str]) -> bool:
        """Check if document is valid (not expired)"""
        if not expiration_date:
            return False

        try:
            exp_date = datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
            return exp_date > datetime.now()
        except:
            return False

    def _days_until_expiration(self, expiration_date: Optional[str]) -> Optional[int]:
        """Calculate days until document expires"""
        if not expiration_date:
            return None

        try:
            exp_date = datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
            delta = exp_date - datetime.now()
            return max(0, delta.days)
        except:
            return None

    def _validate_documents(self, documents: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all submitted documents
        """
        validations = []

        for doc_type, doc_data in documents.items():
            verified = doc_data.get("verified", False)
            expiration = doc_data.get("expiration_date")

            valid = verified and self._check_document_expiration(expiration)

            # Check for expiration warnings (within 90 days)
            days_until_exp = self._days_until_expiration(expiration)
            expiring_soon = days_until_exp is not None and days_until_exp < 90

            validations.append(
                {
                    "document_type": doc_type,
                    "verified": verified,
                    "valid": valid,
                    "expiration_date": expiration,
                    "days_until_expiration": days_until_exp,
                    "expiring_soon": expiring_soon,
                    "status": (
                        "valid"
                        if valid
                        else (
                            "expired"
                            if not self._check_document_expiration(expiration)
                            else "unverified"
                        )
                    ),
                }
            )

        valid_count = sum(1 for v in validations if v["valid"])
        expiring_count = sum(1 for v in validations if v.get("expiring_soon"))

        return {
            "validations": validations,
            "valid_documents": valid_count,
            "total_documents": len(validations),
            "documents_expiring_soon": expiring_count,
            "all_documents_valid": valid_count == len(validations),
        }

    def _assess_background_check(self, background_check: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess background check results and calculate risk score
        """
        criminal_record = background_check.get("criminal_record", "pending")
        driving_points = background_check.get("driving_record_points", 0)
        accidents = background_check.get("accidents_last_3_years", 0)

        # Calculate risk score (0-100, lower is better)
        risk_score = 0

        # Criminal record impact
        if criminal_record == "clear":
            risk_score += 0
        elif criminal_record == "minor":
            risk_score += 30
        elif criminal_record == "major":
            risk_score += 80
        else:  # pending or unknown
            risk_score += 50

        # Driving points impact (each point adds 10 to risk)
        risk_score += driving_points * 10

        # Accidents impact (each accident adds 15 to risk)
        risk_score += accidents * 15

        # Determine risk level
        if risk_score <= 20:
            risk_level = "low"
            approval_recommendation = "approve"
        elif risk_score <= 40:
            risk_level = "moderate"
            approval_recommendation = "approve_with_monitoring"
        elif risk_score <= 60:
            risk_level = "high"
            approval_recommendation = "conditional_approval"
        else:
            risk_level = "critical"
            approval_recommendation = "reject"

        return {
            "criminal_record_status": criminal_record,
            "driving_points": driving_points,
            "accidents_last_3_years": accidents,
            "risk_score": min(100, risk_score),
            "risk_level": risk_level,
            "approval_recommendation": approval_recommendation,
            "completed": background_check.get("completed_date") is not None,
            "completed_date": background_check.get("completed_date"),
        }

    def _evaluate_training(self, training: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate training completion status
        """
        required_modules = {
            "platform_training_completed": {"weight": 0.40, "mandatory": True},
            "safety_training_completed": {"weight": 0.40, "mandatory": True},
            "customer_service_training_completed": {"weight": 0.20, "mandatory": False},
        }

        completed_modules = []
        pending_modules = []

        total_weight = 0
        completed_weight = 0

        for module, config in required_modules.items():
            weight = config["weight"]
            mandatory = config["mandatory"]
            completed = training.get(module, False)

            total_weight += weight
            if completed:
                completed_weight += weight
                completed_modules.append(
                    {
                        "module": module.replace("_completed", ""),
                        "status": "completed",
                        "mandatory": mandatory,
                        "weight": weight,
                    }
                )
            else:
                pending_modules.append(
                    {
                        "module": module.replace("_completed", ""),
                        "status": "pending",
                        "mandatory": mandatory,
                        "weight": weight,
                    }
                )

        completion_percentage = (completed_weight / total_weight * 100) if total_weight > 0 else 0

        # Check if all mandatory modules are completed
        mandatory_modules = [m for m, c in required_modules.items() if c["mandatory"]]
        mandatory_completed = all(training.get(m, False) for m in mandatory_modules)

        training_status = (
            "completed"
            if mandatory_completed and len(pending_modules) == 0
            else "mandatory_completed" if mandatory_completed else "incomplete"
        )

        return {
            "completed_modules": completed_modules,
            "pending_modules": pending_modules,
            "completion_percentage": round(completion_percentage, 1),
            "mandatory_completed": mandatory_completed,
            "training_status": training_status,
            "total_modules": len(required_modules),
            "completed_count": len(completed_modules),
        }

    def _calculate_readiness_score(
        self,
        compliance: Dict[str, Any],
        documents: Dict[str, Any],
        background: Dict[str, Any],
        training: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate overall driver readiness score
        """
        # Component weights
        weights = {"compliance": 0.30, "documents": 0.20, "background": 0.25, "training": 0.25}

        # Calculate component scores (0-100)
        compliance_score = compliance["compliance_percentage"]
        documents_score = (
            (documents["valid_documents"] / documents["total_documents"] * 100)
            if documents["total_documents"] > 0
            else 0
        )
        background_score = 100 - background["risk_score"]  # Invert risk score
        training_score = training["completion_percentage"]

        # Calculate weighted overall score
        overall_score = (
            compliance_score * weights["compliance"]
            + documents_score * weights["documents"]
            + background_score * weights["background"]
            + training_score * weights["training"]
        )

        # Determine readiness level
        if overall_score >= 90:
            readiness_level = "ready"
        elif overall_score >= 75:
            readiness_level = "nearly_ready"
        elif overall_score >= 50:
            readiness_level = "in_progress"
        else:
            readiness_level = "not_ready"

        return {
            "overall_percentage": round(overall_score, 1),
            "readiness_level": readiness_level,
            "component_scores": {
                "compliance": round(compliance_score, 1),
                "documents": round(documents_score, 1),
                "background": round(background_score, 1),
                "training": round(training_score, 1),
            },
            "weights": weights,
        }

    def _generate_onboarding_decision(
        self, readiness: Dict[str, Any], compliance: Dict[str, Any], training: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate final onboarding decision
        """
        readiness_level = readiness["readiness_level"]
        compliance_status = compliance["overall_status"]
        training_status = training["training_status"]

        # Decision logic
        if (
            readiness_level == "ready"
            and compliance_status == "fully_compliant"
            and training_status == "completed"
        ):
            status = "approved"
            reason = "All requirements met"
            estimated_days = 0
        elif (
            readiness_level in ["ready", "nearly_ready"]
            and compliance_status == "fully_compliant"
            and training_status == "mandatory_completed"
        ):
            status = "conditionally_approved"
            reason = "Mandatory requirements met, optional training pending"
            estimated_days = 3
        elif readiness_level in ["in_progress", "nearly_ready"]:
            status = "pending"
            reason = "Additional requirements needed"
            estimated_days = 7
        else:
            status = "rejected"
            reason = "Does not meet minimum requirements"
            estimated_days = None

        estimated_activation = None
        if estimated_days is not None:
            estimated_activation = (datetime.now() + timedelta(days=estimated_days)).isoformat()

        return {
            "status": status,
            "reason": reason,
            "readiness_level": readiness_level,
            "estimated_days_to_activation": estimated_days,
            "estimated_activation_date": estimated_activation,
            "requires_manual_review": status in ["conditionally_approved", "rejected"],
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_action_items(
        self, compliance: Dict[str, Any], documents: Dict[str, Any], training: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate action items for pending requirements
        """
        action_items = []

        # Compliance action items
        for req in compliance["requirements"]:
            if req["status"] == "non_compliant":
                action_items.append(
                    {
                        "category": req["category"],
                        "requirement": req["requirement"],
                        "action": f"Complete {req['requirement'].replace('_', ' ')}",
                        "priority": (
                            "high"
                            if req["category"] in ["documentation", "background"]
                            else "medium"
                        ),
                        "status": "pending",
                    }
                )

        # Document expiration warnings
        for validation in documents["validations"]:
            if validation.get("expiring_soon"):
                action_items.append(
                    {
                        "category": "documentation",
                        "requirement": validation["document_type"],
                        "action": f"Renew {validation['document_type']} - expires in {validation['days_until_expiration']} days",
                        "priority": "medium",
                        "status": "warning",
                    }
                )

        # Training action items
        for module in training["pending_modules"]:
            priority = "high" if module["mandatory"] else "low"
            action_items.append(
                {
                    "category": "training",
                    "requirement": module["module"],
                    "action": f"Complete {module['module'].replace('_', ' ')} training",
                    "priority": priority,
                    "status": "pending",
                }
            )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        action_items.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return action_items

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for driver onboarding"""
        return {
            "type": "object",
            "required": ["applicant", "documents", "background_check", "training"],
            "properties": {
                "applicant": {"type": "object"},
                "documents": {"type": "object"},
                "background_check": {"type": "object"},
                "training": {"type": "object"},
                "vehicle_inspection": {"type": "object"},
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "compliance_status": {"type": "object"},
                "document_validation": {"type": "object"},
                "background_assessment": {"type": "object"},
                "training_status": {"type": "object"},
                "readiness_score": {"type": "object"},
                "onboarding_decision": {"type": "object"},
                "action_items": {"type": "array"},
            },
        }


def create_onboard_drivers_human_capital_agent() -> OnboardDriversHumanCapitalAgent:
    """Factory function to create OnboardDriversHumanCapitalAgent"""
    config = OnboardDriversHumanCapitalAgentConfig()
    return OnboardDriversHumanCapitalAgent(config)
