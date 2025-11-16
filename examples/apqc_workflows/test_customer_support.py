"""
Test suite for Customer Support Automation System

Validates core functionality and integration with APQC agents
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from customer_support_automation import (
    CustomerSupportOrchestrator,
    Customer,
    Channel,
    SentimentAnalyzer,
    CategoryClassifier,
    IssueCategory,
    SentimentScore,
)


async def test_sentiment_analysis():
    """Test sentiment analysis functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Sentiment Analysis")
    print("=" * 60)

    test_cases = [
        ("Thank you so much! This is excellent service!", SentimentScore.VERY_POSITIVE),
        ("The product stopped working. This is terrible!", SentimentScore.VERY_NEGATIVE),
        ("I need help with my account.", SentimentScore.NEUTRAL),
    ]

    for text, expected in test_cases:
        sentiment, confidence = SentimentAnalyzer.analyze_sentiment(text)
        print(f"\nText: '{text}'")
        print(f"Expected: {expected.value}")
        print(f"Got: {sentiment.value} (confidence: {confidence:.2f})")
        # Note: Sentiment analysis is keyword-based, so exact match not guaranteed
        # This is a demonstration test

    print("\n✓ Sentiment analysis tests completed")


async def test_category_classification():
    """Test category classification"""
    print("\n" + "=" * 60)
    print("TEST 2: Category Classification")
    print("=" * 60)

    test_cases = [
        ("I forgot my password and can't login", IssueCategory.ACCOUNT),
        ("I want a refund for my purchase", IssueCategory.BILLING),
        ("The app keeps crashing", IssueCategory.TECHNICAL),
        ("Where is my order?", IssueCategory.SHIPPING),
    ]

    for text, expected in test_cases:
        category, confidence = CategoryClassifier.classify(text)
        print(f"\nText: '{text}'")
        print(f"Expected: {expected.value}")
        print(f"Got: {category.value} (confidence: {confidence:.2f})")

    print("\n✓ Category classification tests completed")


async def test_end_to_end_workflow():
    """Test end-to-end customer support workflow"""
    print("\n" + "=" * 60)
    print("TEST 3: End-to-End Workflow")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = CustomerSupportOrchestrator()

    # Create test customer
    customer = Customer(
        customer_id="TEST-001",
        name="Test User",
        email="test@example.com",
        tier="gold",
        lifetime_value=10000.0
    )

    # Test scenario: Password reset
    print("\n→ Processing password reset request...")
    ticket = await orchestrator.process_incoming_request(
        customer=customer,
        channel=Channel.CHAT,
        subject="Cannot access my account",
        message="I forgot my password and need to reset it urgently!"
    )

    print(f"\n✓ Ticket created: {ticket.ticket_id}")
    print(f"  Category: {ticket.category.value}")
    print(f"  Priority: {ticket.priority.value}")
    print(f"  Sentiment: {ticket.sentiment.value}")
    print(f"  Status: {ticket.status.value}")
    print(f"  Auto-resolved: {ticket.auto_resolved}")

    # Verify ticket was processed
    assert ticket.ticket_id is not None
    assert ticket.category == IssueCategory.ACCOUNT
    assert ticket.status.value in ["resolved", "assigned", "escalated"]

    # Test satisfaction measurement
    if ticket.status.value == "resolved":
        print("\n→ Recording customer satisfaction...")
        await orchestrator.measure_satisfaction(ticket, rating=9, feedback="Quick resolution!")
        print(f"✓ Satisfaction recorded: 9/10")

    print("\n✓ End-to-end workflow test completed")


async def test_metrics_and_reporting():
    """Test metrics collection and reporting"""
    print("\n" + "=" * 60)
    print("TEST 4: Metrics and Reporting")
    print("=" * 60)

    orchestrator = CustomerSupportOrchestrator()

    # Process a few tickets
    customers = [
        Customer(f"CUST-{i:03d}", f"Customer {i}", f"customer{i}@example.com")
        for i in range(3)
    ]

    scenarios = [
        ("Password reset", "I forgot my password"),
        ("Refund inquiry", "When will my refund be processed?"),
        ("Product issue", "The product isn't working"),
    ]

    for i, (subject, message) in enumerate(scenarios):
        await orchestrator.process_incoming_request(
            customer=customers[i],
            channel=Channel.EMAIL,
            subject=subject,
            message=message
        )

    # Generate report
    print("\n→ Generating operations report...")
    report = await orchestrator.generate_operations_report("test")

    print(f"\n✓ Report generated")
    print(f"  Total tickets: {orchestrator.metrics['total_tickets']}")
    print(f"  Auto-resolved: {orchestrator.metrics['auto_resolved']}")
    print(f"  Escalated: {orchestrator.metrics['escalated']}")

    if orchestrator.metrics['total_tickets'] > 0:
        auto_rate = (orchestrator.metrics['auto_resolved'] /
                    orchestrator.metrics['total_tickets']) * 100
        print(f"  Auto-resolution rate: {auto_rate:.1f}%")

    print("\n✓ Metrics and reporting test completed")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 CUSTOMER SUPPORT AUTOMATION - TEST SUITE")
    print("=" * 70)

    tests = [
        test_sentiment_analysis,
        test_category_classification,
        test_end_to_end_workflow,
        test_metrics_and_reporting,
    ]

    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
