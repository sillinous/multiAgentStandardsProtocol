#!/usr/bin/env python3
"""
SuperStandard Compliance CLI Tool
Command-line interface for running compliance tests and generating reports
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests"))

from compliance.framework import (
    CertificationLevel,
    ComplianceReport,
    ComplianceTestSuite,
    create_compliance_report,
    ProtocolComplianceResult,
)
from compliance.report_generator import ComplianceReportGenerator


def run_bronze_certification(agent_id: str, agent_name: str) -> ComplianceReport:
    """Run Bronze certification tests"""
    from compliance.bronze_certification import (
        A2ASchemaConformanceTest,
        A2ARequiredFieldsTest,
        A2AEnvelopeValidationTest,
        A2APayloadValidationTest,
        A2AMessageTypesTest,
        A2AInvalidMessageTest,
        A2ATimestampFormatTest,
        A2AMessageIDFormatTest,
    )

    suite = ComplianceTestSuite("Bronze Certification", CertificationLevel.BRONZE)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(A2ARequiredFieldsTest())
    suite.add_test(A2AEnvelopeValidationTest())
    suite.add_test(A2APayloadValidationTest())
    suite.add_test(A2AMessageTypesTest())
    suite.add_test(A2AInvalidMessageTest())
    suite.add_test(A2ATimestampFormatTest())
    suite.add_test(A2AMessageIDFormatTest())

    results = suite.run_all()

    # Create protocol results
    from compliance.framework import TestResult
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    failed = sum(1 for r in results if r.result == TestResult.FAILED)
    skipped = sum(1 for r in results if r.result == TestResult.SKIPPED)
    errors = sum(1 for r in results if r.result == TestResult.ERROR)

    protocol_results = [
        ProtocolComplianceResult(
            protocol_name="A2A",
            protocol_version="2.0.0",
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            test_results=results
        )
    ]

    return create_compliance_report(
        agent_id=agent_id,
        agent_name=agent_name,
        certification_level=CertificationLevel.BRONZE,
        test_results=results,
        protocol_results=protocol_results
    )


def run_silver_certification(agent_id: str, agent_name: str) -> ComplianceReport:
    """Run Silver certification tests"""
    from compliance.silver_certification import (
        A2ASchemaConformanceTest,
        A2ARequiredFieldsTest,
        A2AEnvelopeValidationTest,
        A2APayloadValidationTest,
        ASPSchemaConformanceTest,
        ASPSemanticDeclarationTest,
        ASPSemanticQueryTest,
        A2AASPInteroperabilityTest,
    )

    suite = ComplianceTestSuite("Silver Certification", CertificationLevel.SILVER)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(A2ARequiredFieldsTest())
    suite.add_test(A2AEnvelopeValidationTest())
    suite.add_test(A2APayloadValidationTest())
    suite.add_test(ASPSchemaConformanceTest())
    suite.add_test(ASPSemanticDeclarationTest())
    suite.add_test(ASPSemanticQueryTest())
    suite.add_test(A2AASPInteroperabilityTest())

    results = suite.run_all()

    from compliance.framework import TestResult
    passed = sum(1 for r in results if r.result == TestResult.PASSED)
    failed = sum(1 for r in results if r.result == TestResult.FAILED)
    skipped = sum(1 for r in results if r.result == TestResult.SKIPPED)
    errors = sum(1 for r in results if r.result == TestResult.ERROR)

    # Separate results by protocol
    a2a_results = [r for r in results if 'A2A' in r.test_id]
    asp_results = [r for r in results if 'ASP' in r.test_id]

    protocol_results = [
        ProtocolComplianceResult(
            protocol_name="A2A",
            protocol_version="2.0.0",
            total_tests=len(a2a_results),
            passed=sum(1 for r in a2a_results if r.result == TestResult.PASSED),
            failed=sum(1 for r in a2a_results if r.result == TestResult.FAILED),
            skipped=0,
            errors=0,
            test_results=a2a_results
        ),
        ProtocolComplianceResult(
            protocol_name="ASP",
            protocol_version="1.0.0",
            total_tests=len(asp_results),
            passed=sum(1 for r in asp_results if r.result == TestResult.PASSED),
            failed=sum(1 for r in asp_results if r.result == TestResult.FAILED),
            skipped=0,
            errors=0,
            test_results=asp_results
        )
    ]

    return create_compliance_report(
        agent_id=agent_id,
        agent_name=agent_name,
        certification_level=CertificationLevel.SILVER,
        test_results=results,
        protocol_results=protocol_results
    )


def run_gold_certification(agent_id: str, agent_name: str) -> ComplianceReport:
    """Run Gold certification tests"""
    from compliance.gold_certification import (
        A2ASchemaConformanceTest,
        ASPSchemaConformanceTest,
        TAPSchemaConformanceTest,
        TAPTemporalQueryTest,
        ADPSchemaConformanceTest,
        ADPDiscoveryTest,
        MessageLatencyBenchmarkTest,
        MultiProtocolIntegrationTest,
    )

    suite = ComplianceTestSuite("Gold Certification", CertificationLevel.GOLD)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(ASPSchemaConformanceTest())
    suite.add_test(TAPSchemaConformanceTest())
    suite.add_test(TAPTemporalQueryTest())
    suite.add_test(ADPSchemaConformanceTest())
    suite.add_test(ADPDiscoveryTest())
    suite.add_test(MessageLatencyBenchmarkTest())
    suite.add_test(MultiProtocolIntegrationTest())

    results = suite.run_all()

    from compliance.framework import TestResult

    # Separate results by protocol
    protocol_map = {
        'A2A': [],
        'ASP': [],
        'TAP': [],
        'ADP': []
    }

    for result in results:
        for proto in protocol_map.keys():
            if proto in result.test_id:
                protocol_map[proto].append(result)
                break

    protocol_results = []
    version_map = {'A2A': '2.0.0', 'ASP': '1.0.0', 'TAP': '1.0.0', 'ADP': '1.0.0'}

    for proto, proto_results in protocol_map.items():
        if proto_results:
            protocol_results.append(
                ProtocolComplianceResult(
                    protocol_name=proto,
                    protocol_version=version_map[proto],
                    total_tests=len(proto_results),
                    passed=sum(1 for r in proto_results if r.result == TestResult.PASSED),
                    failed=sum(1 for r in proto_results if r.result == TestResult.FAILED),
                    skipped=0,
                    errors=0,
                    test_results=proto_results
                )
            )

    return create_compliance_report(
        agent_id=agent_id,
        agent_name=agent_name,
        certification_level=CertificationLevel.GOLD,
        test_results=results,
        protocol_results=protocol_results
    )


def run_platinum_certification(agent_id: str, agent_name: str) -> ComplianceReport:
    """Run Platinum certification tests"""
    from compliance.platinum_certification import (
        A2ASchemaConformanceTest,
        ASPSchemaConformanceTest,
        TAPSchemaConformanceTest,
        ADPSchemaConformanceTest,
        CIPSchemaConformanceTest,
        CIPReasoningRequestTest,
        CIPReasoningTypesTest,
        CIPConfidenceLevelsTest,
        JWTSecurityValidationTest,
        DIDFormatValidationTest,
        A2ASecurityMetadataTest,
        MessageLatencyBenchmarkTest,
        ThroughputBenchmarkTest,
        ComprehensiveInteroperabilityTest,
    )

    suite = ComplianceTestSuite("Platinum Certification", CertificationLevel.PLATINUM)
    suite.add_test(A2ASchemaConformanceTest())
    suite.add_test(ASPSchemaConformanceTest())
    suite.add_test(TAPSchemaConformanceTest())
    suite.add_test(ADPSchemaConformanceTest())
    suite.add_test(CIPSchemaConformanceTest())
    suite.add_test(CIPReasoningRequestTest())
    suite.add_test(CIPReasoningTypesTest())
    suite.add_test(CIPConfidenceLevelsTest())
    suite.add_test(JWTSecurityValidationTest())
    suite.add_test(DIDFormatValidationTest())
    suite.add_test(A2ASecurityMetadataTest())
    suite.add_test(MessageLatencyBenchmarkTest())
    suite.add_test(ThroughputBenchmarkTest())
    suite.add_test(ComprehensiveInteroperabilityTest())

    results = suite.run_all()

    from compliance.framework import TestResult

    # Separate results by protocol
    protocol_map = {
        'A2A': [],
        'ASP': [],
        'TAP': [],
        'ADP': [],
        'CIP': []
    }

    for result in results:
        for proto in protocol_map.keys():
            if proto in result.test_id:
                protocol_map[proto].append(result)
                break

    protocol_results = []
    version_map = {'A2A': '2.0.0', 'ASP': '1.0.0', 'TAP': '1.0.0', 'ADP': '1.0.0', 'CIP': '1.0.0'}

    for proto, proto_results in protocol_map.items():
        if proto_results:
            protocol_results.append(
                ProtocolComplianceResult(
                    protocol_name=proto,
                    protocol_version=version_map[proto],
                    total_tests=len(proto_results),
                    passed=sum(1 for r in proto_results if r.result == TestResult.PASSED),
                    failed=sum(1 for r in proto_results if r.result == TestResult.FAILED),
                    skipped=0,
                    errors=0,
                    test_results=proto_results
                )
            )

    return create_compliance_report(
        agent_id=agent_id,
        agent_name=agent_name,
        certification_level=CertificationLevel.PLATINUM,
        test_results=results,
        protocol_results=protocol_results
    )


def cmd_test(args):
    """Run compliance tests"""
    print(f"Running {args.level.upper()} certification tests...")
    print(f"Agent ID: {args.agent}")
    print(f"Agent Name: {args.name}")
    print()

    # Map level to function
    level_map = {
        'bronze': run_bronze_certification,
        'silver': run_silver_certification,
        'gold': run_gold_certification,
        'platinum': run_platinum_certification,
    }

    runner = level_map[args.level]
    report = runner(args.agent, args.name)

    # Print summary
    print(f"\n{'='*80}")
    print(f"{args.level.upper()} CERTIFICATION RESULTS")
    print(f"{'='*80}")
    print(f"Total Tests: {report.total_tests}")
    print(f"Passed: {report.tests_passed} ✅")
    print(f"Failed: {report.tests_failed} ❌")
    print(f"Skipped: {report.tests_skipped} ⏭️")
    print(f"Errors: {report.tests_error} ⚠️")
    print(f"Pass Rate: {report.pass_rate:.1f}%")
    print()

    status = "ACHIEVED ✅" if report.certification_achieved else "NOT ACHIEVED ❌"
    print(f"Certification Status: {status}")
    print(f"{'='*80}\n")

    # Save report if output specified
    if args.output:
        output_path = Path(args.output)

        if args.format == 'json':
            ComplianceReportGenerator.generate_json_report(report, output_path)
            print(f"JSON report saved to: {output_path}")
        elif args.format == 'markdown':
            ComplianceReportGenerator.generate_markdown_report(report, output_path)
            print(f"Markdown report saved to: {output_path}")
        elif args.format == 'both':
            json_path = output_path.with_suffix('.json')
            md_path = output_path.with_suffix('.md')
            ComplianceReportGenerator.generate_json_report(report, json_path)
            ComplianceReportGenerator.generate_markdown_report(report, md_path)
            print(f"JSON report saved to: {json_path}")
            print(f"Markdown report saved to: {md_path}")

    return 0 if report.certification_achieved else 1


def cmd_report(args):
    """Generate compliance report from existing results"""
    print(f"Generating compliance report for agent: {args.agent}")

    # This is a placeholder - in a real implementation, you would load
    # test results from a database or file
    print("Note: This command requires integration with a test results database.")
    print("For now, please use the 'test' command which generates reports automatically.")

    return 0


def cmd_list(args):
    """List available certification levels and protocols"""
    print("Available Certification Levels:")
    print()
    print("1. BRONZE")
    print("   - Core protocols: A2A")
    print("   - Required pass rate: 80%")
    print()
    print("2. SILVER")
    print("   - Protocols: A2A + ASP")
    print("   - Required pass rate: 85%")
    print()
    print("3. GOLD")
    print("   - Protocols: A2A + ASP + TAP + ADP")
    print("   - Required pass rate: 90%")
    print()
    print("4. PLATINUM")
    print("   - Protocols: A2A + ASP + TAP + ADP + CIP")
    print("   - Required pass rate: 95%")
    print()
    print("Supported Protocols:")
    print("  - A2A: Agent-to-Agent Protocol v2.0")
    print("  - ASP: Agent Semantic Protocol v1.0")
    print("  - TAP: Temporal Agent Protocol v1.0")
    print("  - ADP: Agent Discovery Protocol v1.0")
    print("  - CIP: Cognitive Interoperability Protocol v1.0")

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SuperStandard Compliance Test Suite (SCTS) CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Bronze certification
  %(prog)s test --level bronze --agent apqc_1_0_strategic --name "Strategic Agent"

  # Run Platinum certification with report output
  %(prog)s test --level platinum --agent apqc_1_0_strategic --output report.md

  # Generate report in both formats
  %(prog)s test --level gold --agent test_agent --format both --output results

  # List available certifications
  %(prog)s list
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run compliance tests')
    test_parser.add_argument(
        '--level',
        choices=['bronze', 'silver', 'gold', 'platinum'],
        required=True,
        help='Certification level to test'
    )
    test_parser.add_argument(
        '--agent',
        required=True,
        help='Agent ID to test'
    )
    test_parser.add_argument(
        '--name',
        default='Test Agent',
        help='Agent name (default: Test Agent)'
    )
    test_parser.add_argument(
        '--output',
        help='Output file path for report'
    )
    test_parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='markdown',
        help='Report format (default: markdown)'
    )
    test_parser.set_defaults(func=cmd_test)

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate compliance report')
    report_parser.add_argument(
        '--agent',
        required=True,
        help='Agent ID'
    )
    report_parser.add_argument(
        '--output',
        required=True,
        help='Output file path'
    )
    report_parser.add_argument(
        '--format',
        choices=['json', 'markdown'],
        default='markdown',
        help='Report format'
    )
    report_parser.set_defaults(func=cmd_report)

    # List command
    list_parser = subparsers.add_parser('list', help='List certification levels and protocols')
    list_parser.set_defaults(func=cmd_list)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
