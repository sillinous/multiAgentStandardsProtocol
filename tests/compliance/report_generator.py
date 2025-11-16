"""
Compliance Report Generator
Generates compliance reports in JSON and Markdown formats
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .framework import (
    ComplianceReport,
    TestResult,
    TestCaseResult,
    ProtocolComplianceResult,
    CertificationLevel,
)


class ComplianceReportGenerator:
    """Generate compliance reports in various formats"""

    @staticmethod
    def generate_json_report(report: ComplianceReport, output_path: Optional[Path] = None) -> str:
        """
        Generate JSON compliance report

        Args:
            report: ComplianceReport instance
            output_path: Optional path to save report

        Returns:
            JSON string
        """
        report_dict = report.to_dict()

        # Convert test results to dict format
        for protocol_result in report_dict['protocol_results']:
            protocol_result['test_results'] = [
                {
                    'test_id': tr.test_id,
                    'test_name': tr.test_name,
                    'category': tr.category.value,
                    'result': tr.result.value,
                    'duration_ms': tr.duration_ms,
                    'error_message': tr.error_message,
                    'details': tr.details,
                    'timestamp': tr.timestamp
                }
                for tr in protocol_result['test_results']
            ]

        json_output = json.dumps(report_dict, indent=2)

        if output_path:
            output_path.write_text(json_output)

        return json_output

    @staticmethod
    def generate_markdown_report(report: ComplianceReport, output_path: Optional[Path] = None) -> str:
        """
        Generate Markdown compliance report

        Args:
            report: ComplianceReport instance
            output_path: Optional path to save report

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# SuperStandard Compliance Report")
        lines.append("")
        lines.append(f"**Report ID:** `{report.report_id}`")
        lines.append(f"**Agent ID:** `{report.agent_id}`")
        lines.append(f"**Agent Name:** {report.agent_name}")
        lines.append(f"**Certification Level:** {report.certification_level.value.upper()}")
        lines.append(f"**Timestamp:** {report.timestamp}")
        lines.append("")

        # Certification Status
        status_emoji = "✅" if report.certification_achieved else "❌"
        status_text = "ACHIEVED" if report.certification_achieved else "NOT ACHIEVED"
        lines.append(f"## Certification Status: {status_emoji} {status_text}")
        lines.append("")

        # Overall Results
        lines.append("## Overall Results")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Total Tests** | {report.total_tests} |")
        lines.append(f"| **Passed** | {report.tests_passed} ✅ |")
        lines.append(f"| **Failed** | {report.tests_failed} ❌ |")
        lines.append(f"| **Skipped** | {report.tests_skipped} ⏭️ |")
        lines.append(f"| **Errors** | {report.tests_error} ⚠️ |")
        lines.append(f"| **Pass Rate** | {report.pass_rate:.1f}% |")
        lines.append("")

        # Protocol Compliance
        lines.append("## Protocol Compliance")
        lines.append("")

        if report.protocol_results:
            lines.append("| Protocol | Version | Tests | Passed | Failed | Pass Rate | Status |")
            lines.append("|----------|---------|-------|--------|--------|-----------|--------|")

            for protocol_result in report.protocol_results:
                status = "✅" if protocol_result.pass_rate >= 90.0 else "⚠️"
                lines.append(
                    f"| {protocol_result.protocol_name} | "
                    f"{protocol_result.protocol_version} | "
                    f"{protocol_result.total_tests} | "
                    f"{protocol_result.passed} | "
                    f"{protocol_result.failed} | "
                    f"{protocol_result.pass_rate:.1f}% | "
                    f"{status} |"
                )
            lines.append("")

        # Detailed Test Results
        lines.append("## Detailed Test Results")
        lines.append("")

        for protocol_result in report.protocol_results:
            lines.append(f"### {protocol_result.protocol_name} v{protocol_result.protocol_version}")
            lines.append("")

            if protocol_result.test_results:
                lines.append("| Test ID | Test Name | Category | Result | Duration |")
                lines.append("|---------|-----------|----------|--------|----------|")

                for test_result in protocol_result.test_results:
                    result_emoji = {
                        TestResult.PASSED: "✅",
                        TestResult.FAILED: "❌",
                        TestResult.SKIPPED: "⏭️",
                        TestResult.ERROR: "⚠️"
                    }.get(test_result.result, "❓")

                    lines.append(
                        f"| {test_result.test_id} | "
                        f"{test_result.test_name} | "
                        f"{test_result.category.value} | "
                        f"{result_emoji} {test_result.result.value} | "
                        f"{test_result.duration_ms:.2f}ms |"
                    )

                lines.append("")

                # Failed tests details
                failed_tests = [t for t in protocol_result.test_results if t.result == TestResult.FAILED]
                if failed_tests:
                    lines.append(f"#### Failed Tests for {protocol_result.protocol_name}")
                    lines.append("")

                    for test_result in failed_tests:
                        lines.append(f"**{test_result.test_id}: {test_result.test_name}**")
                        lines.append(f"- Error: {test_result.error_message}")
                        if test_result.details:
                            lines.append(f"- Details: {json.dumps(test_result.details, indent=2)}")
                        lines.append("")

        # Performance Metrics
        if report.performance_metrics:
            lines.append("## Performance Metrics")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(report.performance_metrics, indent=2))
            lines.append("```")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, recommendation in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {recommendation}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by SuperStandard Compliance Test Suite (SCTS)*")
        lines.append(f"*Report generated on {datetime.utcnow().isoformat()}Z*")

        markdown_output = "\n".join(lines)

        if output_path:
            output_path.write_text(markdown_output)

        return markdown_output

    @staticmethod
    def generate_summary_report(reports: List[ComplianceReport]) -> str:
        """
        Generate summary report for multiple agents

        Args:
            reports: List of ComplianceReport instances

        Returns:
            Markdown summary
        """
        lines = []

        lines.append("# SuperStandard Compliance Summary")
        lines.append("")
        lines.append(f"**Total Agents Tested:** {len(reports)}")
        lines.append(f"**Report Generated:** {datetime.utcnow().isoformat()}Z")
        lines.append("")

        # Summary table
        lines.append("## Agent Compliance Summary")
        lines.append("")
        lines.append("| Agent ID | Agent Name | Certification Level | Pass Rate | Status |")
        lines.append("|----------|------------|---------------------|-----------|--------|")

        for report in reports:
            status = "✅" if report.certification_achieved else "❌"
            lines.append(
                f"| {report.agent_id} | "
                f"{report.agent_name} | "
                f"{report.certification_level.value.upper()} | "
                f"{report.pass_rate:.1f}% | "
                f"{status} |"
            )

        lines.append("")

        # Statistics
        certified_count = sum(1 for r in reports if r.certification_achieved)
        avg_pass_rate = sum(r.pass_rate for r in reports) / len(reports) if reports else 0

        lines.append("## Overall Statistics")
        lines.append("")
        lines.append(f"- **Certified Agents:** {certified_count}/{len(reports)} ({certified_count/len(reports)*100:.1f}%)")
        lines.append(f"- **Average Pass Rate:** {avg_pass_rate:.1f}%")
        lines.append("")

        # Certification levels breakdown
        level_counts = {}
        for report in reports:
            level = report.certification_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        lines.append("## Certification Levels")
        lines.append("")
        for level in ["bronze", "silver", "gold", "platinum"]:
            count = level_counts.get(level, 0)
            lines.append(f"- **{level.upper()}:** {count} agents")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_html_badge(report: ComplianceReport) -> str:
        """
        Generate HTML badge for certification status

        Args:
            report: ComplianceReport instance

        Returns:
            HTML string
        """
        if report.certification_achieved:
            color = {
                CertificationLevel.BRONZE: "#CD7F32",
                CertificationLevel.SILVER: "#C0C0C0",
                CertificationLevel.GOLD: "#FFD700",
                CertificationLevel.PLATINUM: "#E5E4E2"
            }.get(report.certification_level, "#808080")

            status_text = f"{report.certification_level.value.upper()} CERTIFIED"
            badge_class = "certified"
        else:
            color = "#FF0000"
            status_text = "NOT CERTIFIED"
            badge_class = "not-certified"

        html = f"""
<div class="superstandard-badge {badge_class}" style="
    display: inline-block;
    padding: 8px 16px;
    background-color: {color};
    color: white;
    font-weight: bold;
    border-radius: 4px;
    font-family: sans-serif;
">
    {status_text} ({report.pass_rate:.1f}%)
</div>
"""
        return html.strip()


def create_sample_report() -> ComplianceReport:
    """Create a sample compliance report for demonstration"""
    from .framework import create_compliance_report

    # Create sample test results
    test_results = [
        TestCaseResult(
            test_id="TEST-001",
            test_name="Sample Test 1",
            category=TestCategory.PROTOCOL_CONFORMANCE,
            result=TestResult.PASSED,
            duration_ms=15.5
        ),
        TestCaseResult(
            test_id="TEST-002",
            test_name="Sample Test 2",
            category=TestCategory.INTEROPERABILITY,
            result=TestResult.PASSED,
            duration_ms=23.2
        ),
        TestCaseResult(
            test_id="TEST-003",
            test_name="Sample Test 3",
            category=TestCategory.PERFORMANCE,
            result=TestResult.FAILED,
            duration_ms=105.8,
            error_message="Performance threshold exceeded"
        ),
    ]

    # Create sample protocol results
    protocol_results = [
        ProtocolComplianceResult(
            protocol_name="A2A",
            protocol_version="2.0.0",
            total_tests=10,
            passed=9,
            failed=1,
            skipped=0,
            errors=0,
            test_results=test_results
        )
    ]

    # Create report
    report = create_compliance_report(
        agent_id="apqc_1_0_strategic",
        agent_name="Strategic Planning Agent",
        certification_level=CertificationLevel.BRONZE,
        test_results=test_results,
        protocol_results=protocol_results
    )

    return report


if __name__ == "__main__":
    # Generate sample report
    from .framework import TestCategory

    report = create_sample_report()
    generator = ComplianceReportGenerator()

    # Generate JSON
    json_report = generator.generate_json_report(report)
    print("JSON Report:")
    print(json_report)
    print("\n" + "="*80 + "\n")

    # Generate Markdown
    markdown_report = generator.generate_markdown_report(report)
    print("Markdown Report:")
    print(markdown_report)
    print("\n" + "="*80 + "\n")

    # Generate HTML Badge
    badge = generator.generate_html_badge(report)
    print("HTML Badge:")
    print(badge)
