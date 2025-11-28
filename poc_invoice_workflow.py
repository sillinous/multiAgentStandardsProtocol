#!/usr/bin/env python3
"""
Multi-Agent Invoice Processing Workflow POC
============================================

Demonstrates MULTIPLE APQC agents working together in a coordinated workflow.

This POC shows:
1. Multi-agent orchestration (4 agents in sequence)
2. Data flowing between agents
3. Each agent adding business value
4. End-to-end invoice processing automation
5. Measurable performance across the pipeline

Workflow Pipeline:
    Raw Invoice → [Extract] → [Validate] → [Calculate] → [Approve] → Decision

Agents Used:
- 9.1.1.6: Gather financial data (Extract invoice fields)
- 9.1.1.7: Validate data accuracy (Validate invoice)
- 9.1.1.8: Perform calculations (Calculate totals & enrichments)
- 9.1.1.9: Plan reporting (Generate approval recommendation)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from superstandard.agents.base.atomic_agent_standard import (
    AtomicAgentInput,
    AtomicAgentOutput,
    ExecutionStatus
)


# ============================================================================
# RAW INVOICE DATA (As received from email/OCR/API)
# ============================================================================

RAW_INVOICES = [
    {
        "source": "email",
        "raw_text": "Invoice INV-2025-001 from Acme Corp for Software License",
        "extracted_fields": {
            "invoice_number": "INV-2025-001",
            "vendor_name": "Acme Corp",
            "date": "2025-11-15",
            "items": [
                {"desc": "Software License", "qty": 10, "price": 450.00},
                {"desc": "Support Contract", "qty": 1, "price": 500.00}
            ]
        }
    },
    {
        "source": "api",
        "raw_text": "Purchase Order PO-2025-456",
        "extracted_fields": {
            "invoice_number": "INV-2025-002",
            "vendor_name": "Office Supplies Inc",
            "date": "2025-11-16",
            "items": [
                {"desc": "Paper Reams", "qty": 10, "price": 25.00},
                {"desc": "Pens", "qty": 20, "price": 5.00}
            ]
        }
    },
    {
        "source": "ocr",
        "raw_text": "INVOICE - Consulting Services",
        "extracted_fields": {
            "invoice_number": "INV-2025-003",
            "vendor_name": "Unknown Vendor",
            "date": "2025-11-17",
            "items": [
                {"desc": "Consulting Services", "qty": 1, "price": 10000.00}
            ]
        }
    }
]

# Master data
VENDOR_MASTER = {
    "Acme Corp": {"vendor_id": "VNDR-1001", "approved": True, "risk_level": "low", "payment_terms": "Net 30"},
    "Office Supplies Inc": {"vendor_id": "VNDR-1002", "approved": True, "risk_level": "low", "payment_terms": "Net 15"},
    "Trusted Partner LLC": {"vendor_id": "VNDR-1003", "approved": True, "risk_level": "medium", "payment_terms": "Net 45"}
}

GL_ACCOUNT_MAP = {
    "Software License": "6000-Software",
    "Support Contract": "6000-Software",
    "Paper Reams": "6100-Office-Supplies",
    "Pens": "6100-Office-Supplies",
    "Consulting Services": "6200-Consulting"
}

TAX_RATES = {
    "6000-Software": 0.10,
    "6100-Office-Supplies": 0.10,
    "6200-Consulting": 0.10,
    "default": 0.10
}


# ============================================================================
# AGENT 1: Extract Invoice Data (9.1.1.6)
# ============================================================================

class InvoiceExtractionAgent:
    """
    APQC 9.1.1.6: Gather financial data

    Extracts and structures invoice data from various sources.
    Performs initial data extraction and enrichment.
    """

    def __init__(self):
        self.agent_id = "9.1.1.6"
        self.name = "Extract Invoice Data"

    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """Extract and structure invoice data"""
        start_time = datetime.now()

        try:
            raw_invoice = agent_input.data.get("raw_invoice", {})
            extracted = raw_invoice.get("extracted_fields", {})

            # Extract basic fields
            invoice_data = {
                "invoice_id": extracted.get("invoice_number", "UNKNOWN"),
                "vendor_name": extracted.get("vendor_name", ""),
                "date": extracted.get("date", ""),
                "source": raw_invoice.get("source", "unknown"),
                "line_items": []
            }

            # Process line items
            for item in extracted.get("items", []):
                line_item = {
                    "description": item.get("desc", ""),
                    "quantity": item.get("qty", 0),
                    "unit_price": item.get("price", 0.0),
                    "amount": item.get("qty", 0) * item.get("price", 0.0)
                }
                invoice_data["line_items"].append(line_item)

            # Enrich with vendor data
            vendor_info = VENDOR_MASTER.get(invoice_data["vendor_name"])
            if vendor_info:
                invoice_data["vendor_id"] = vendor_info["vendor_id"]
                invoice_data["vendor_approved"] = vendor_info["approved"]
                invoice_data["vendor_risk"] = vendor_info["risk_level"]
                invoice_data["payment_terms"] = vendor_info["payment_terms"]
            else:
                invoice_data["vendor_id"] = "UNKNOWN"
                invoice_data["vendor_approved"] = False
                invoice_data["vendor_risk"] = "high"

            # Assign GL accounts
            for item in invoice_data["line_items"]:
                gl_account = GL_ACCOUNT_MAP.get(item["description"], "UNKNOWN")
                item["gl_account"] = gl_account

            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.SUCCESS,
                success=True,
                result_data={
                    "invoice": invoice_data,
                    "extraction_summary": {
                        "fields_extracted": len(invoice_data),
                        "line_items_count": len(invoice_data["line_items"]),
                        "vendor_enriched": vendor_info is not None,
                        "gl_accounts_assigned": sum(1 for item in invoice_data["line_items"] if item.get("gl_account") != "UNKNOWN")
                    }
                },
                execution_time_ms=execution_time_ms,
                apqc_level5_id="9.1.1.6",
                apqc_level5_name="Gather financial data"
            )

        except Exception as e:
            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                error_message=str(e),
                result_data={"error": str(e)}
            )


# ============================================================================
# AGENT 2: Validate Invoice Data (9.1.1.7)
# ============================================================================

class InvoiceValidationAgent:
    """
    APQC 9.1.1.7: Validate data accuracy

    Validates invoice data for completeness, accuracy, and compliance.
    """

    def __init__(self):
        self.agent_id = "9.1.1.7"
        self.name = "Validate Invoice Data"

    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """Validate invoice data"""
        start_time = datetime.now()

        try:
            invoice = agent_input.data.get("invoice", {})

            validation_results = {
                "invoice_id": invoice.get("invoice_id"),
                "checks_performed": [],
                "issues": [],
                "warnings": [],
                "is_valid": True
            }

            # Check 1: Required fields
            required_fields = ["invoice_id", "vendor_name", "date", "line_items"]
            missing_fields = [f for f in required_fields if not invoice.get(f)]
            if missing_fields:
                validation_results["issues"].append(f"Missing required fields: {', '.join(missing_fields)}")
                validation_results["is_valid"] = False
            validation_results["checks_performed"].append("required_fields")

            # Check 2: Vendor validation
            if not invoice.get("vendor_approved", False):
                validation_results["issues"].append(f"Vendor {invoice.get('vendor_name')} is not approved")
                validation_results["is_valid"] = False
            validation_results["checks_performed"].append("vendor_approval")

            # Check 3: GL accounts
            invalid_gl = [item for item in invoice.get("line_items", []) if item.get("gl_account") == "UNKNOWN"]
            if invalid_gl:
                validation_results["issues"].append(f"Invalid GL accounts for {len(invalid_gl)} line items")
                validation_results["is_valid"] = False
            validation_results["checks_performed"].append("gl_accounts")

            # Check 4: Line item amounts
            for idx, item in enumerate(invoice.get("line_items", [])):
                expected_amount = item.get("quantity", 0) * item.get("unit_price", 0)
                actual_amount = item.get("amount", 0)
                if abs(expected_amount - actual_amount) > 0.01:
                    validation_results["issues"].append(f"Line item {idx+1} amount mismatch")
                    validation_results["is_valid"] = False
            validation_results["checks_performed"].append("line_item_math")

            # Warning: High risk vendor
            if invoice.get("vendor_risk") == "high":
                validation_results["warnings"].append("High risk vendor - requires additional review")

            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.SUCCESS,
                success=True,
                result_data={
                    "validation": validation_results,
                    "invoice": invoice  # Pass through
                },
                execution_time_ms=execution_time_ms,
                apqc_level5_id="9.1.1.7",
                apqc_level5_name="Validate data accuracy"
            )

        except Exception as e:
            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                error_message=str(e),
                result_data={"error": str(e)}
            )


# ============================================================================
# AGENT 3: Calculate Invoice Totals (9.1.1.8)
# ============================================================================

class InvoiceCalculationAgent:
    """
    APQC 9.1.1.8: Perform calculations

    Calculates invoice totals, tax, and final amounts.
    """

    def __init__(self):
        self.agent_id = "9.1.1.8"
        self.name = "Calculate Invoice Totals"

    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """Calculate invoice totals"""
        start_time = datetime.now()

        try:
            invoice = agent_input.data.get("invoice", {})
            validation = agent_input.data.get("validation", {})

            # Calculate subtotal
            subtotal = sum(item.get("amount", 0) for item in invoice.get("line_items", []))

            # Calculate tax by GL account
            tax_details = []
            total_tax = 0.0
            for item in invoice.get("line_items", []):
                gl_account = item.get("gl_account", "")
                tax_rate = TAX_RATES.get(gl_account, TAX_RATES["default"])
                item_tax = round(item.get("amount", 0) * tax_rate, 2)
                total_tax += item_tax
                tax_details.append({
                    "line_item": item.get("description"),
                    "amount": item.get("amount"),
                    "tax_rate": tax_rate,
                    "tax": item_tax
                })

            # Calculate total
            total = round(subtotal + total_tax, 2)

            calculations = {
                "subtotal": round(subtotal, 2),
                "tax": round(total_tax, 2),
                "total": total,
                "tax_details": tax_details,
                "currency": "USD"
            }

            # Add calculations to invoice
            invoice["subtotal"] = calculations["subtotal"]
            invoice["tax"] = calculations["tax"]
            invoice["total"] = calculations["total"]

            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.SUCCESS,
                success=True,
                result_data={
                    "calculations": calculations,
                    "invoice": invoice,  # Pass through with calculations
                    "validation": validation  # Pass through
                },
                execution_time_ms=execution_time_ms,
                apqc_level5_id="9.1.1.8",
                apqc_level5_name="Perform calculations"
            )

        except Exception as e:
            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                error_message=str(e),
                result_data={"error": str(e)}
            )


# ============================================================================
# AGENT 4: Generate Approval Recommendation (9.1.1.9)
# ============================================================================

class ApprovalRecommendationAgent:
    """
    APQC 9.1.1.9: Plan reporting

    Generates approval recommendations based on validation and calculations.
    """

    def __init__(self):
        self.agent_id = "9.1.1.9"
        self.name = "Generate Approval Recommendation"
        self.approval_thresholds = {
            "auto_approve": 1000.00,
            "manager": 5000.00,
            "director": 10000.00
        }

    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """Generate approval recommendation"""
        start_time = datetime.now()

        try:
            invoice = agent_input.data.get("invoice", {})
            validation = agent_input.data.get("validation", {})
            calculations = agent_input.data.get("calculations", {})

            total = calculations.get("total", 0)
            is_valid = validation.get("is_valid", False)
            vendor_risk = invoice.get("vendor_risk", "high")

            # Determine recommendation
            if not is_valid:
                recommendation = {
                    "action": "REJECT",
                    "reason": "Validation failed",
                    "approver": "System",
                    "requires_manual_review": True,
                    "issues": validation.get("issues", [])
                }
            elif vendor_risk == "high":
                recommendation = {
                    "action": "MANUAL_REVIEW",
                    "reason": "High risk vendor",
                    "approver": "CFO",
                    "requires_manual_review": True
                }
            elif total >= self.approval_thresholds["director"]:
                recommendation = {
                    "action": "APPROVE",
                    "reason": f"Amount ${total:,.2f} requires director approval",
                    "approver": "Finance Director",
                    "requires_manual_review": True,
                    "auto_approve": False
                }
            elif total >= self.approval_thresholds["manager"]:
                recommendation = {
                    "action": "APPROVE",
                    "reason": f"Amount ${total:,.2f} requires manager approval",
                    "approver": "Finance Manager",
                    "requires_manual_review": True,
                    "auto_approve": False
                }
            elif total >= self.approval_thresholds["auto_approve"]:
                recommendation = {
                    "action": "APPROVE",
                    "reason": f"Amount ${total:,.2f} requires AP manager approval",
                    "approver": "AP Manager",
                    "requires_manual_review": False,
                    "auto_approve": False
                }
            else:
                recommendation = {
                    "action": "AUTO_APPROVE",
                    "reason": f"Amount ${total:,.2f} below auto-approve threshold",
                    "approver": "System",
                    "requires_manual_review": False,
                    "auto_approve": True
                }

            # Add confidence score
            confidence_factors = []
            confidence_score = 1.0

            if vendor_risk == "low":
                confidence_factors.append("Trusted vendor")
            else:
                confidence_score -= 0.2
                confidence_factors.append("Vendor risk concern")

            if is_valid:
                confidence_factors.append("All validations passed")
            else:
                confidence_score -= 0.5
                confidence_factors.append("Validation issues")

            if len(validation.get("warnings", [])) > 0:
                confidence_score -= 0.1

            recommendation["confidence_score"] = max(0.0, confidence_score)
            recommendation["confidence_factors"] = confidence_factors

            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.SUCCESS,
                success=True,
                result_data={
                    "recommendation": recommendation,
                    "invoice": invoice,
                    "validation": validation,
                    "calculations": calculations
                },
                execution_time_ms=execution_time_ms,
                apqc_level5_id="9.1.1.9",
                apqc_level5_name="Plan reporting"
            )

        except Exception as e:
            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                error_message=str(e),
                result_data={"error": str(e)}
            )


# ============================================================================
# WORKFLOW ORCHESTRATOR
# ============================================================================

class InvoiceProcessingWorkflow:
    """
    Multi-agent workflow orchestrator for invoice processing.

    Coordinates 4 agents in sequence, passing data between them.
    """

    def __init__(self):
        self.agents = {
            "extract": InvoiceExtractionAgent(),
            "validate": InvoiceValidationAgent(),
            "calculate": InvoiceCalculationAgent(),
            "approve": ApprovalRecommendationAgent()
        }

    async def process_invoice(self, raw_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single invoice through the complete workflow"""
        workflow_start = datetime.now()
        workflow_id = f"workflow_{datetime.now().timestamp()}"

        results = {
            "workflow_id": workflow_id,
            "invoice_id": raw_invoice.get("extracted_fields", {}).get("invoice_number", "UNKNOWN"),
            "stages": {},
            "final_decision": None,
            "total_execution_time_ms": 0,
            "success": True
        }

        try:
            # Stage 1: Extract
            extract_input = AtomicAgentInput(
                task_id=f"{workflow_id}_extract",
                task_description="Extract invoice data",
                data={"raw_invoice": raw_invoice},
                workflow_id=workflow_id
            )
            extract_output = await self.agents["extract"].execute_atomic_task(extract_input)
            results["stages"]["extract"] = {
                "success": extract_output.success,
                "execution_time_ms": extract_output.execution_time_ms,
                "data": extract_output.result_data
            }

            if not extract_output.success:
                results["success"] = False
                results["error"] = "Extraction failed"
                return results

            # Stage 2: Validate
            validate_input = AtomicAgentInput(
                task_id=f"{workflow_id}_validate",
                task_description="Validate invoice data",
                data=extract_output.result_data,
                workflow_id=workflow_id
            )
            validate_output = await self.agents["validate"].execute_atomic_task(validate_input)
            results["stages"]["validate"] = {
                "success": validate_output.success,
                "execution_time_ms": validate_output.execution_time_ms,
                "data": validate_output.result_data
            }

            if not validate_output.success:
                results["success"] = False
                results["error"] = "Validation failed"
                return results

            # Stage 3: Calculate
            calculate_input = AtomicAgentInput(
                task_id=f"{workflow_id}_calculate",
                task_description="Calculate invoice totals",
                data=validate_output.result_data,
                workflow_id=workflow_id
            )
            calculate_output = await self.agents["calculate"].execute_atomic_task(calculate_input)
            results["stages"]["calculate"] = {
                "success": calculate_output.success,
                "execution_time_ms": calculate_output.execution_time_ms,
                "data": calculate_output.result_data
            }

            if not calculate_output.success:
                results["success"] = False
                results["error"] = "Calculation failed"
                return results

            # Stage 4: Approve
            approve_input = AtomicAgentInput(
                task_id=f"{workflow_id}_approve",
                task_description="Generate approval recommendation",
                data=calculate_output.result_data,
                workflow_id=workflow_id
            )
            approve_output = await self.agents["approve"].execute_atomic_task(approve_input)
            results["stages"]["approve"] = {
                "success": approve_output.success,
                "execution_time_ms": approve_output.execution_time_ms,
                "data": approve_output.result_data
            }

            if not approve_output.success:
                results["success"] = False
                results["error"] = "Approval recommendation failed"
                return results

            # Set final decision
            results["final_decision"] = approve_output.result_data.get("recommendation")

            # Calculate total time
            workflow_end = datetime.now()
            results["total_execution_time_ms"] = (workflow_end - workflow_start).total_seconds() * 1000

            return results

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            return results


# ============================================================================
# POC EXECUTION
# ============================================================================

async def run_multi_agent_poc():
    """Run the multi-agent workflow POC"""
    print("=" * 80)
    print("MULTI-AGENT INVOICE PROCESSING WORKFLOW POC")
    print("=" * 80)
    print()
    print("Workflow: Raw Invoice → Extract → Validate → Calculate → Approve")
    print(f"Agents: 4 (9.1.1.6, 9.1.1.7, 9.1.1.8, 9.1.1.9)")
    print(f"Test Invoices: {len(RAW_INVOICES)}")
    print()

    workflow = InvoiceProcessingWorkflow()
    all_results = []

    for idx, raw_invoice in enumerate(RAW_INVOICES, 1):
        invoice_id = raw_invoice.get("extracted_fields", {}).get("invoice_number", f"Invoice {idx}")
        vendor = raw_invoice.get("extracted_fields", {}).get("vendor_name", "Unknown")

        print(f"\n{'=' * 80}")
        print(f"Processing {idx}/{len(RAW_INVOICES)}: {invoice_id} ({vendor})")
        print(f"{'=' * 80}\n")

        result = await workflow.process_invoice(raw_invoice)
        all_results.append(result)

        # Display workflow execution
        if result["success"]:
            print(f"✅ Workflow completed successfully in {result['total_execution_time_ms']:.2f}ms\n")

            # Stage 1: Extract
            extract_data = result["stages"]["extract"]["data"]
            print(f"[Stage 1] Extract ({result['stages']['extract']['execution_time_ms']:.2f}ms)")
            print(f"  - Fields extracted: {extract_data.get('extraction_summary', {}).get('fields_extracted', 0)}")
            print(f"  - Line items: {extract_data.get('extraction_summary', {}).get('line_items_count', 0)}")
            print(f"  - Vendor enriched: {'Yes' if extract_data.get('extraction_summary', {}).get('vendor_enriched') else 'No'}")

            # Stage 2: Validate
            validation_data = result["stages"]["validate"]["data"]
            validation = validation_data.get("validation", {})
            print(f"\n[Stage 2] Validate ({result['stages']['validate']['execution_time_ms']:.2f}ms)")
            print(f"  - Valid: {'✅ Yes' if validation.get('is_valid') else '❌ No'}")
            print(f"  - Checks performed: {len(validation.get('checks_performed', []))}")
            if validation.get("issues"):
                print(f"  - Issues: {len(validation.get('issues', []))}")
                for issue in validation.get("issues", []):
                    print(f"    • {issue}")

            # Stage 3: Calculate
            calc_data = result["stages"]["calculate"]["data"]
            calcs = calc_data.get("calculations", {})
            print(f"\n[Stage 3] Calculate ({result['stages']['calculate']['execution_time_ms']:.2f}ms)")
            print(f"  - Subtotal: ${calcs.get('subtotal', 0):,.2f}")
            print(f"  - Tax: ${calcs.get('tax', 0):,.2f}")
            print(f"  - Total: ${calcs.get('total', 0):,.2f}")

            # Stage 4: Approve
            approve_data = result["stages"]["approve"]["data"]
            recommendation = approve_data.get("recommendation", {})
            print(f"\n[Stage 4] Approve ({result['stages']['approve']['execution_time_ms']:.2f}ms)")
            action_icon = "✅" if recommendation.get("action") in ["APPROVE", "AUTO_APPROVE"] else "❌"
            print(f"  - Decision: {action_icon} {recommendation.get('action')}")
            print(f"  - Approver: {recommendation.get('approver')}")
            print(f"  - Reason: {recommendation.get('reason')}")
            print(f"  - Confidence: {recommendation.get('confidence_score', 0)*100:.0f}%")
            print(f"  - Manual review required: {'Yes' if recommendation.get('requires_manual_review') else 'No'}")
        else:
            print(f"❌ Workflow failed: {result.get('error')}")

    # Summary
    print(f"\n\n{'=' * 80}")
    print("WORKFLOW SUMMARY")
    print(f"{'=' * 80}")

    successful_workflows = sum(1 for r in all_results if r["success"])
    print(f"Total Workflows Executed: {len(all_results)}")
    print(f"Successful: {successful_workflows}")
    print(f"Failed: {len(all_results) - successful_workflows}")

    avg_time = sum(r.get("total_execution_time_ms", 0) for r in all_results if r["success"]) / max(successful_workflows, 1)
    print(f"\nPerformance:")
    print(f"  Average End-to-End Time: {avg_time:.2f}ms")
    print(f"  Throughput: {len(all_results) / (sum(r.get('total_execution_time_ms', 0) for r in all_results) / 1000):.2f} invoices/second")

    # Decisions
    decisions = {}
    for r in all_results:
        if r.get("final_decision"):
            action = r["final_decision"].get("action")
            decisions[action] = decisions.get(action, 0) + 1

    print(f"\nDecisions:")
    for action, count in decisions.items():
        print(f"  {action}: {count}")

    print(f"\n{'=' * 80}")
    print("✅ MULTI-AGENT WORKFLOW POC COMPLETE!")
    print("  - 4 agents working together in coordinated pipeline")
    print("  - Data flowing seamlessly between stages")
    print("  - End-to-end automation demonstrated")
    print(f"{'=' * 80}\n")

    return all_results


if __name__ == "__main__":
    results = asyncio.run(run_multi_agent_poc())
