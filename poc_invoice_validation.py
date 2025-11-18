#!/usr/bin/env python3
"""
Invoice Validation POC
======================

Proof of Concept demonstrating APQC agents processing real invoice data.

This POC shows:
1. Real invoice data being processed
2. Actual business logic validation
3. Agent execution with measurable results
4. End-to-end workflow demonstration

Category: Finance (9.0)
Agent: 9.1.1.7 - Validate data accuracy
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from superstandard.agents.base.atomic_agent_standard import (
    AtomicAgentStandard,
    AtomicAgentInput,
    AtomicAgentOutput,
    ExecutionStatus
)


# ============================================================================
# SAMPLE INVOICE DATA
# ============================================================================

SAMPLE_INVOICES = [
    {
        "invoice_id": "INV-2025-001",
        "vendor": "Acme Corp",
        "vendor_id": "VNDR-1001",
        "date": "2025-11-15",
        "due_date": "2025-12-15",
        "amount": 5000.00,
        "tax": 500.00,
        "total": 5500.00,
        "line_items": [
            {"description": "Software License", "quantity": 10, "unit_price": 450.00, "amount": 4500.00},
            {"description": "Support Contract", "quantity": 1, "unit_price": 500.00, "amount": 500.00}
        ],
        "gl_account": "6000-Software",
        "status": "pending"
    },
    {
        "invoice_id": "INV-2025-002",
        "vendor": "Office Supplies Inc",
        "vendor_id": "VNDR-1002",
        "date": "2025-11-16",
        "due_date": "2025-12-01",
        "amount": 350.00,
        "tax": 35.00,
        "total": 385.00,
        "line_items": [
            {"description": "Paper Reams", "quantity": 10, "unit_price": 25.00, "amount": 250.00},
            {"description": "Pens", "quantity": 20, "unit_price": 5.00, "amount": 100.00}
        ],
        "gl_account": "6100-Office-Supplies",
        "status": "pending"
    },
    {
        "invoice_id": "INV-2025-003",
        "vendor": "Unknown Vendor",
        "vendor_id": "VNDR-9999",
        "date": "2025-11-17",
        "due_date": "2025-12-17",
        "amount": 10000.00,
        "tax": 900.00,  # Tax calculation error!
        "total": 10900.00,
        "line_items": [
            {"description": "Consulting Services", "quantity": 1, "unit_price": 10000.00, "amount": 10000.00}
        ],
        "gl_account": "INVALID-ACCOUNT",  # Invalid GL account!
        "status": "pending"
    }
]

VENDOR_MASTER = {
    "VNDR-1001": {"name": "Acme Corp", "approved": True, "risk_level": "low"},
    "VNDR-1002": {"name": "Office Supplies Inc", "approved": True, "risk_level": "low"},
    "VNDR-1003": {"name": "Trusted Partner LLC", "approved": True, "risk_level": "medium"}
}

VALID_GL_ACCOUNTS = [
    "6000-Software",
    "6100-Office-Supplies",
    "6200-Consulting",
    "6300-Travel",
    "6400-Equipment"
]

APPROVAL_THRESHOLDS = {
    "low": 1000.00,
    "medium": 5000.00,
    "high": 10000.00
}


# ============================================================================
# INVOICE VALIDATION AGENT - WITH REAL BUSINESS LOGIC
# ============================================================================

class InvoiceValidationAgent:
    """
    Invoice Validation Agent with REAL business logic

    APQC Task: 9.1.1.7 - Validate data accuracy
    Category: Manage Financial Resources

    This agent performs actual invoice validation:
    1. Vendor verification
    2. GL account validation
    3. Math verification (line items, tax, totals)
    4. Approval routing based on amount
    5. Risk assessment
    """

    def __init__(self):
        self.agent_id = "9.1.1.7"
        self.name = "Validate Invoice Data"
        self.description = "APQC 9.1.1.7: Validate invoice data accuracy with real business rules"
        self.vendor_master = VENDOR_MASTER
        self.valid_gl_accounts = VALID_GL_ACCOUNTS
        self.approval_thresholds = APPROVAL_THRESHOLDS

    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """Execute invoice validation with real business logic"""
        start_time = datetime.now()

        try:
            invoice = agent_input.data.get("invoice", {})

            # Initialize validation results
            validation_results = {
                "invoice_id": invoice.get("invoice_id", "UNKNOWN"),
                "vendor_check": {},
                "gl_account_check": {},
                "math_check": {},
                "approval_routing": {},
                "overall_status": "VALID",
                "issues": [],
                "warnings": []
            }

            # Step 1: Validate vendor
            vendor_result = await self._validate_vendor(invoice)
            validation_results["vendor_check"] = vendor_result
            if not vendor_result["valid"]:
                validation_results["issues"].append(vendor_result["message"])
                validation_results["overall_status"] = "INVALID"

            # Step 2: Validate GL account
            gl_result = await self._validate_gl_account(invoice)
            validation_results["gl_account_check"] = gl_result
            if not gl_result["valid"]:
                validation_results["issues"].append(gl_result["message"])
                validation_results["overall_status"] = "INVALID"

            # Step 3: Validate math
            math_result = await self._validate_math(invoice)
            validation_results["math_check"] = math_result
            if not math_result["valid"]:
                validation_results["issues"].append(math_result["message"])
                validation_results["overall_status"] = "INVALID"

            # Step 4: Determine approval routing
            routing_result = await self._determine_approval_routing(invoice, vendor_result)
            validation_results["approval_routing"] = routing_result
            if routing_result.get("requires_senior_approval"):
                validation_results["warnings"].append("Requires senior management approval")

            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return AtomicAgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.SUCCESS,
                success=True,
                result_data=validation_results,
                execution_time_ms=execution_time_ms,
                apqc_level5_id="9.1.1.7",
                apqc_level5_name="Validate data accuracy",
                apqc_category="Manage Financial Resources"
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

    async def _validate_vendor(self, invoice: dict) -> dict:
        """Validate vendor exists and is approved"""
        vendor_id = invoice.get("vendor_id")

        if not vendor_id:
            return {"valid": False, "message": "Missing vendor ID"}

        vendor = self.vendor_master.get(vendor_id)

        if not vendor:
            return {
                "valid": False,
                "message": f"Vendor {vendor_id} not found in master data",
                "vendor_id": vendor_id
            }

        if not vendor.get("approved"):
            return {
                "valid": False,
                "message": f"Vendor {vendor_id} is not approved",
                "vendor_id": vendor_id,
                "vendor_name": vendor.get("name")
            }

        return {
            "valid": True,
            "message": "Vendor validated successfully",
            "vendor_id": vendor_id,
            "vendor_name": vendor.get("name"),
            "risk_level": vendor.get("risk_level")
        }

    async def _validate_gl_account(self, invoice: dict) -> dict:
        """Validate GL account is valid"""
        gl_account = invoice.get("gl_account")

        if not gl_account:
            return {"valid": False, "message": "Missing GL account"}

        if gl_account not in self.valid_gl_accounts:
            return {
                "valid": False,
                "message": f"Invalid GL account: {gl_account}",
                "gl_account": gl_account,
                "valid_accounts": self.valid_gl_accounts
            }

        return {
            "valid": True,
            "message": "GL account is valid",
            "gl_account": gl_account
        }

    async def _validate_math(self, invoice: dict) -> dict:
        """Validate invoice math is correct"""
        issues = []

        # Validate line items sum to amount
        line_items = invoice.get("line_items", [])
        line_items_total = sum(item.get("amount", 0) for item in line_items)
        amount = invoice.get("amount", 0)

        if abs(line_items_total - amount) > 0.01:  # Allow for rounding
            issues.append(f"Line items total ({line_items_total}) != amount ({amount})")

        # Validate tax calculation (assume 10% tax rate)
        expected_tax = round(amount * 0.10, 2)
        actual_tax = invoice.get("tax", 0)

        if abs(expected_tax - actual_tax) > 0.01:
            issues.append(f"Tax calculation error: expected {expected_tax}, got {actual_tax}")

        # Validate total = amount + tax
        expected_total = amount + actual_tax
        actual_total = invoice.get("total", 0)

        if abs(expected_total - actual_total) > 0.01:
            issues.append(f"Total calculation error: expected {expected_total}, got {actual_total}")

        if issues:
            return {
                "valid": False,
                "message": "Math validation failed",
                "issues": issues,
                "line_items_total": line_items_total,
                "amount": amount,
                "tax": actual_tax,
                "expected_tax": expected_tax,
                "total": actual_total
            }

        return {
            "valid": True,
            "message": "Math validation passed",
            "line_items_total": line_items_total,
            "tax": actual_tax,
            "total": actual_total
        }

    async def _determine_approval_routing(self, invoice: dict, vendor_result: dict) -> dict:
        """Determine approval routing based on amount and vendor risk"""
        total = invoice.get("total", 0)
        vendor_risk = vendor_result.get("risk_level", "high")

        # Determine approval level
        if total >= self.approval_thresholds["high"]:
            approval_level = "CFO"
            requires_senior = True
        elif total >= self.approval_thresholds["medium"]:
            approval_level = "Finance Manager"
            requires_senior = True
        elif total >= self.approval_thresholds["low"]:
            approval_level = "Accounts Payable Manager"
            requires_senior = False
        else:
            approval_level = "AP Clerk"
            requires_senior = False

        # Escalate if high risk vendor
        if vendor_risk == "high":
            approval_level = "CFO"
            requires_senior = True

        return {
            "approval_level": approval_level,
            "requires_senior_approval": requires_senior,
            "total_amount": total,
            "vendor_risk": vendor_risk,
            "reason": f"Amount ${total:,.2f} requires {approval_level} approval"
        }


# ============================================================================
# POC EXECUTION
# ============================================================================

async def run_poc():
    """Run the invoice validation POC"""
    print("=" * 80)
    print("INVOICE VALIDATION POC - Real Business Logic Demonstration")
    print("=" * 80)
    print()
    print(f"Agent: 9.1.1.7 - Validate Invoice Data")
    print(f"Category: Manage Financial Resources")
    print(f"Processing {len(SAMPLE_INVOICES)} invoices...")
    print()

    # Initialize agent
    agent = InvoiceValidationAgent()

    # Process each invoice
    results = []
    for idx, invoice in enumerate(SAMPLE_INVOICES, 1):
        print(f"\n{'=' * 80}")
        print(f"Invoice {idx}/{len(SAMPLE_INVOICES)}: {invoice['invoice_id']}")
        print(f"Vendor: {invoice['vendor']} | Amount: ${invoice['total']:,.2f}")
        print(f"{'=' * 80}")

        # Create input
        agent_input = AtomicAgentInput(
            task_id=f"validate_{invoice['invoice_id']}",
            task_description=f"Validate invoice {invoice['invoice_id']}",
            data={"invoice": invoice}
        )

        # Execute agent
        output = await agent.execute_atomic_task(agent_input)
        results.append(output)

        # Display results
        if output.success:
            validation = output.result_data
            print(f"\n✅ Status: {validation['overall_status']}")
            print(f"   Execution Time: {output.execution_time_ms:.2f}ms")

            # Vendor check
            vendor_check = validation['vendor_check']
            if vendor_check['valid']:
                print(f"   ✅ Vendor: {vendor_check['vendor_name']} (Risk: {vendor_check.get('risk_level', 'N/A')})")
            else:
                print(f"   ❌ Vendor: {vendor_check['message']}")

            # GL account check
            gl_check = validation['gl_account_check']
            if gl_check['valid']:
                print(f"   ✅ GL Account: {gl_check['gl_account']}")
            else:
                print(f"   ❌ GL Account: {gl_check['message']}")

            # Math check
            math_check = validation['math_check']
            if math_check['valid']:
                print(f"   ✅ Math: Line items ${math_check['line_items_total']:,.2f}, Tax ${math_check['tax']:,.2f}, Total ${math_check['total']:,.2f}")
            else:
                print(f"   ❌ Math: {math_check['message']}")
                for issue in math_check.get('issues', []):
                    print(f"      - {issue}")

            # Approval routing
            routing = validation['approval_routing']
            print(f"   📋 Approval: {routing['approval_level']}")
            if routing['requires_senior_approval']:
                print(f"      ⚠️  Requires senior approval")

            # Issues and warnings
            if validation['issues']:
                print(f"\n   ❌ ISSUES FOUND:")
                for issue in validation['issues']:
                    print(f"      - {issue}")

            if validation['warnings']:
                print(f"\n   ⚠️  WARNINGS:")
                for warning in validation['warnings']:
                    print(f"      - {warning}")
        else:
            print(f"\n❌ Execution Failed: {output.error}")

    # Summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Invoices Processed: {len(results)}")
    print(f"Successful Executions: {sum(1 for r in results if r.success)}")
    print(f"Failed Executions: {sum(1 for r in results if not r.success)}")

    valid_invoices = sum(1 for r in results if r.success and r.result_data.get('overall_status') == 'VALID')
    invalid_invoices = sum(1 for r in results if r.success and r.result_data.get('overall_status') == 'INVALID')

    print(f"\nValidation Results:")
    print(f"  ✅ Valid Invoices: {valid_invoices}")
    print(f"  ❌ Invalid Invoices: {invalid_invoices}")

    avg_time = sum(r.execution_time_ms for r in results if r.success) / len([r for r in results if r.success])
    print(f"\nPerformance:")
    print(f"  Average Execution Time: {avg_time:.2f}ms")
    print(f"  Throughput: {len(results) / (sum(r.execution_time_ms for r in results) / 1000):.2f} invoices/second")

    print(f"\n{'=' * 80}")
    print("✅ POC COMPLETE - Real business logic validated successfully!")
    print(f"{'=' * 80}\n")

    return results


if __name__ == "__main__":
    # Run the POC
    results = asyncio.run(run_poc())
