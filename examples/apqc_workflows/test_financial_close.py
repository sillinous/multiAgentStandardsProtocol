"""
Quick Test Script for Financial Close Automation
=================================================

Validates that the financial close workflow executes successfully.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.apqc_workflows.financial_close_automation import (
    FinancialCloseOrchestrator,
    CloseStatus,
)


async def test_financial_close():
    """Test the complete financial close workflow."""
    print("\n" + "=" * 80)
    print("TESTING FINANCIAL CLOSE AUTOMATION")
    print("=" * 80 + "\n")

    # Initialize orchestrator
    orchestrator = FinancialCloseOrchestrator()

    # Verify initial state
    assert orchestrator.close_status == CloseStatus.PENDING
    assert len(orchestrator.agents) == 8
    print("✓ Orchestrator initialized successfully")
    print(f"✓ Loaded {len(orchestrator.agents)} APQC Category 9 agents")

    # Execute financial close
    period_end = datetime(2025, 11, 30, 23, 59, 59)
    company_name = "Test Company Inc"

    try:
        results = await orchestrator.execute_financial_close(
            period_end=period_end,
            company_name=company_name
        )

        # Validate results
        assert results["status"] == "completed"
        assert results["close_id"] == orchestrator.close_id
        assert "metrics" in results
        assert "financial_statements" in results

        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print(f"✓ Close Status: {results['status']}")
        print(f"✓ Duration: {results['metrics']['duration_seconds']:.2f} seconds")
        print(f"✓ Automation Rate: {results['metrics']['automation_rate']}")
        print(f"✓ Cost Savings: ${results['metrics']['cost_savings_usd']:,.2f}")
        print(f"✓ Journal Entries: {results['metrics']['journal_entries']}")
        print(f"✓ Reconciliations: {results['metrics']['reconciliations']}")
        print(f"✓ Variances: {results['metrics']['variances']}")

        # Validate financial statements
        assert "balance_sheet" in results["financial_statements"]
        assert "income_statement" in results["financial_statements"]
        assert "cash_flow" in results["financial_statements"]
        print(f"✓ Financial Statements Generated: 3")

        # Validate metrics
        metrics = results["metrics"]
        assert metrics["journal_entries"] > 0
        assert metrics["reconciliations"] > 0
        assert float(metrics["automation_rate"].rstrip('%')) > 90

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        raise


if __name__ == "__main__":
    success = asyncio.run(test_financial_close())
    sys.exit(0 if success else 1)
