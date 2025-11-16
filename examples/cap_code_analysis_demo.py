"""
Code Analysis Protocol (CAP) v1.0 - Interactive Demo
====================================================

This demo showcases the complete capabilities of CAP including:
- Static code analysis
- Security vulnerability scanning
- Quality metrics calculation
- Issue detection and reporting
- Multiple output formats

Run this demo to see CAP in action analyzing real Python code.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.protocols.cap_v1 import (
    CAPClient,
    AnalysisConfig,
    AnalysisDepth,
    OutputFormat
)


# ============================================================================
# SAMPLE CODE TO ANALYZE
# ============================================================================


SAMPLE_CODE_SECURE = """
def calculate_order_total(items: list) -> float:
    '''Calculate the total price of items in an order.

    Args:
        items: List of items with 'price' and 'quantity' keys

    Returns:
        Total price as a float

    Raises:
        ValueError: If items list is empty or invalid
    '''
    if not items:
        raise ValueError("Items list cannot be empty")

    total = 0.0
    for item in items:
        if 'price' not in item or 'quantity' not in item:
            raise ValueError(f"Invalid item: {item}")
        total += item['price'] * item['quantity']

    return round(total, 2)


class OrderProcessor:
    '''Processes customer orders with proper validation.'''

    def __init__(self, tax_rate: float = 0.08):
        '''Initialize order processor.

        Args:
            tax_rate: Tax rate as decimal (default 8%)
        '''
        self.tax_rate = tax_rate

    def process_order(self, order_items: list) -> dict:
        '''Process an order and calculate totals.

        Args:
            order_items: List of order items

        Returns:
            Dictionary with subtotal, tax, and total
        '''
        subtotal = calculate_order_total(order_items)
        tax = round(subtotal * self.tax_rate, 2)
        total = round(subtotal + tax, 2)

        return {
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
"""


SAMPLE_CODE_VULNERABLE = """
import os
import hashlib
import yaml

class UserAuthentication:
    def __init__(self):
        # SECURITY ISSUE: Hardcoded credentials
        self.admin_password = "admin123"
        self.api_key = "FAKE_API_KEY_FOR_DEMO_NOT_REAL"
        self.secret_token = "super_secret_token_12345"

    def authenticate_user(self, username, password):
        # SECURITY ISSUE: SQL injection vulnerability
        query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
        return self.execute_query(query)

    def hash_password(self, password):
        # SECURITY ISSUE: Weak cryptographic algorithm
        return hashlib.md5(password.encode()).hexdigest()

    def load_config(self, config_file):
        # SECURITY ISSUE: Unsafe YAML deserialization
        with open(config_file) as f:
            return yaml.load(f)

    def execute_command(self, user_command):
        # SECURITY ISSUE: Shell injection vulnerability
        os.system("ls -la " + user_command)

    def process_data(self, user_input):
        # SECURITY ISSUE: Use of eval
        result = eval(user_input)
        return result

def process_file_upload(filename, content):
    # SECURITY ISSUE: Path traversal vulnerability
    file_path = "/uploads/" + filename
    with open(file_path, 'w') as f:
        f.write(content)
"""


SAMPLE_CODE_COMPLEX = """
def complex_business_logic(customer_type, order_value, items, shipping_country,
                          payment_method, coupon_code, is_premium, order_date):
    # COMPLEXITY ISSUE: Too many parameters
    # COMPLEXITY ISSUE: High cyclomatic complexity

    discount = 0
    shipping_cost = 0
    tax_rate = 0

    if customer_type == "retail":
        if order_value > 1000:
            if is_premium:
                if payment_method == "credit":
                    discount = 0.15
                elif payment_method == "debit":
                    discount = 0.10
                else:
                    discount = 0.05
            else:
                if payment_method == "credit":
                    discount = 0.10
                else:
                    discount = 0.05
        elif order_value > 500:
            if is_premium:
                discount = 0.10
            else:
                discount = 0.05
        else:
            discount = 0.02
    elif customer_type == "wholesale":
        if order_value > 5000:
            discount = 0.25
        elif order_value > 2000:
            discount = 0.20
        else:
            discount = 0.15

    if shipping_country == "US":
        if order_value > 100:
            shipping_cost = 0
        else:
            shipping_cost = 10
        tax_rate = 0.08
    elif shipping_country == "CA":
        if order_value > 150:
            shipping_cost = 0
        else:
            shipping_cost = 15
        tax_rate = 0.12
    elif shipping_country == "UK":
        shipping_cost = 20
        tax_rate = 0.20
    else:
        shipping_cost = 30
        tax_rate = 0.10

    if coupon_code:
        if coupon_code == "SAVE10":
            discount += 0.10
        elif coupon_code == "SAVE20":
            discount += 0.20

    subtotal = order_value * (1 - discount)
    tax = subtotal * tax_rate
    total = subtotal + tax + shipping_cost

    return {
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'shipping': shipping_cost,
        'total': total
    }


def long_function_with_many_responsibilities():
    # CODE SMELL: Function too long
    # CODE SMELL: Doing too many things
    print("Starting initialization...")
    config = {}
    config['setting1'] = 'value1'
    config['setting2'] = 'value2'
    config['setting3'] = 'value3'

    print("Loading data...")
    data = []
    for i in range(100):
        data.append(i)

    print("Processing data...")
    results = []
    for item in data:
        if item % 2 == 0:
            results.append(item * 2)
        else:
            results.append(item * 3)

    print("Filtering results...")
    filtered = []
    for r in results:
        if r > 50:
            filtered.append(r)

    print("Sorting results...")
    filtered.sort()

    print("Calculating statistics...")
    total = sum(filtered)
    average = total / len(filtered)
    maximum = max(filtered)
    minimum = min(filtered)

    print("Formatting output...")
    output = {
        'total': total,
        'average': average,
        'max': maximum,
        'min': minimum,
        'count': len(filtered)
    }

    print("Validating output...")
    if output['total'] > 0:
        if output['average'] > 0:
            if output['max'] > output['min']:
                print("Valid output")

    print("Saving to database...")
    # Database save logic here
    print("Sending notifications...")
    # Notification logic here
    print("Logging results...")
    # Logging logic here
    print("Cleaning up...")
    # Cleanup logic here

    return output
"""


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n--- {title} ---\n")


async def demo_secure_code_analysis():
    """Demo: Analyzing well-written secure code."""
    print_header("Demo 1: Analyzing Secure, Well-Written Code")

    client = CAPClient()

    print("Analyzing secure Python code with proper documentation...")
    print("Code features:")
    print("- Proper type hints")
    print("- Comprehensive docstrings")
    print("- Input validation")
    print("- Error handling")

    result = await client.analyze_code(
        SAMPLE_CODE_SECURE,
        analysis_types=['static_analysis', 'security_scan', 'quality_metrics']
    )

    print_section("Analysis Results")
    print(f"Status: {result.status}")
    print(f"Files analyzed: {result.summary.total_files_analyzed}")
    print(f"Lines of code: {result.summary.total_lines_of_code}")
    print(f"Issues found: {result.summary.total_issues_found}")
    print(f"  Critical: {result.summary.critical_issues}")
    print(f"  High: {result.summary.high_issues}")
    print(f"  Medium: {result.summary.medium_issues}")
    print(f"  Low: {result.summary.low_issues}")

    if result.quality_metrics:
        print_section("Quality Metrics")
        qm = result.quality_metrics
        print(f"Maintainability Index: {qm.maintainability_index:.1f}/100")
        if qm.cyclomatic_complexity:
            print(f"Average Complexity: {qm.cyclomatic_complexity.average:.1f}")
        if qm.documentation_coverage:
            print(f"Documentation Coverage: {qm.documentation_coverage*100:.1f}%")

    if result.issues:
        print_section("Issues Detected")
        for issue in result.issues[:5]:
            print(f"\n{issue.severity.upper()}: {issue.title}")
            print(f"  Category: {issue.category}")
            print(f"  Location: Line {issue.location.start_line}")
            print(f"  Description: {issue.description}")


async def demo_security_scanning():
    """Demo: Security vulnerability detection."""
    print_header("Demo 2: Security Vulnerability Scanning")

    client = CAPClient()

    print("Scanning code with multiple security vulnerabilities...")
    print("Expected findings:")
    print("- Hardcoded credentials")
    print("- SQL injection")
    print("- Weak cryptography")
    print("- Shell injection")
    print("- Unsafe deserialization")

    result = await client.analyze_code(
        SAMPLE_CODE_VULNERABLE,
        analysis_types=['security_scan']
    )

    print_section("Security Scan Results")
    print(f"Total issues found: {result.summary.total_issues_found}")
    print(f"Critical issues: {result.summary.critical_issues}")

    if result.security_findings:
        sf = result.security_findings
        vc = sf.vulnerability_count

        print_section("Vulnerability Summary")
        print(f"Critical: {vc.critical}")
        print(f"High: {vc.high}")
        print(f"Medium: {vc.medium}")
        print(f"Low: {vc.low}")

        if sf.secrets_detected:
            print_section(f"Secrets Detected: {len(sf.secrets_detected)}")
            for secret in sf.secrets_detected:
                print(f"  - {secret.type} at line {secret.line} (confidence: {secret.confidence})")

        if sf.vulnerabilities:
            print_section("Top Vulnerabilities")
            for vuln in sf.vulnerabilities[:5]:
                print(f"\n{vuln.severity.upper()}: {vuln.title}")
                print(f"  CVSS Score: {vuln.cvss_score}/10")
                print(f"  Component: {vuln.affected_component}")
                print(f"  Description: {vuln.description}")
                if vuln.remediation:
                    print(f"  Remediation: {vuln.remediation}")

        if sf.security_hotspots:
            print_section(f"Security Hotspots: {len(sf.security_hotspots)}")
            for hotspot in sf.security_hotspots[:3]:
                print(f"  - {hotspot.category} at {hotspot.file}:{hotspot.line}")

    if result.recommendations:
        print_section("Security Recommendations")
        for rec in result.recommendations:
            print(f"\n{rec.priority.upper()}: {rec.title}")
            print(f"  Effort: {rec.effort} | Impact: {rec.impact}")
            print(f"  {rec.description}")


async def demo_complexity_analysis():
    """Demo: Code complexity and smell detection."""
    print_header("Demo 3: Complexity Analysis & Code Smell Detection")

    client = CAPClient()

    print("Analyzing complex code with code smells...")
    print("Expected findings:")
    print("- High cyclomatic complexity")
    print("- Too many parameters")
    print("- Long function")
    print("- Low maintainability")

    result = await client.analyze_code(
        SAMPLE_CODE_COMPLEX,
        analysis_types=['complexity_analysis', 'code_smell_detection', 'quality_metrics']
    )

    print_section("Complexity Analysis Results")

    if result.quality_metrics:
        qm = result.quality_metrics
        print(f"Maintainability Index: {qm.maintainability_index:.1f}/100")

        if qm.cyclomatic_complexity:
            cc = qm.cyclomatic_complexity
            print(f"\nCyclomatic Complexity:")
            print(f"  Average: {cc.average:.1f}")
            print(f"  Maximum: {cc.max:.1f}")
            print(f"  Functions over threshold: {cc.files_over_threshold}")

        if qm.cognitive_complexity:
            print(f"\nCognitive Complexity: {qm.cognitive_complexity:.1f}")

        if qm.technical_debt:
            td = qm.technical_debt
            print(f"\nTechnical Debt:")
            print(f"  Estimated time: {td.total_minutes} minutes")
            print(f"  Debt ratio: {td.debt_ratio:.2%}")

    print_section("Complexity Issues")
    complexity_issues = [i for i in result.issues if i.category in ['maintainability', 'code_smell']]
    print(f"Found {len(complexity_issues)} complexity/smell issues\n")

    for issue in complexity_issues[:5]:
        print(f"{issue.severity.upper()}: {issue.title}")
        print(f"  Line {issue.location.start_line}: {issue.description}")
        if issue.suggested_fix:
            print(f"  Suggestion: {issue.suggested_fix.description}")
        print()


async def demo_output_formats():
    """Demo: Different output formats."""
    print_header("Demo 4: Multiple Output Formats")

    client = CAPClient()

    print("Analyzing code and generating reports in different formats...")

    result = await client.analyze_code(
        SAMPLE_CODE_VULNERABLE,
        analysis_types=['static_analysis', 'security_scan']
    )

    # JSON Format
    print_section("JSON Format (excerpt)")
    json_output = client.format_result(result, format="json")
    # Print first 500 characters
    print(json_output[:500] + "...\n")

    # Markdown Format
    print_section("Markdown Format")
    md_output = client.format_result(result, format="markdown")
    # Print first 800 characters
    print(md_output[:800] + "...\n")

    # SARIF Format
    print_section("SARIF Format (excerpt)")
    sarif_output = client.format_result(result, format="sarif")
    # Print first 400 characters
    print(sarif_output[:400] + "...\n")

    print("All three formats contain the same analysis data in different structures.")
    print("- JSON: For programmatic consumption")
    print("- Markdown: For human-readable reports")
    print("- SARIF: For integration with security tools")


async def demo_comprehensive_report():
    """Demo: Comprehensive analysis report."""
    print_header("Demo 5: Comprehensive Code Analysis Report")

    client = CAPClient()

    print("Running comprehensive analysis with all available analyzers...")

    result = await client.analyze_code(
        SAMPLE_CODE_VULNERABLE,
        analysis_types=[
            'static_analysis',
            'security_scan',
            'quality_metrics',
            'complexity_analysis',
            'code_smell_detection'
        ]
    )

    print_section("Executive Summary")
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Status: {result.status}")
    print(f"Analyzer Version: {result.analyzer_version}")
    print(f"Analysis Duration: {result.summary.analysis_duration_ms}ms")

    print_section("Code Metrics")
    print(f"Files Analyzed: {result.summary.total_files_analyzed}")
    print(f"Lines of Code: {result.summary.total_lines_of_code}")

    print_section("Issues Summary")
    print(f"Total Issues: {result.summary.total_issues_found}")
    print(f"  Critical: {result.summary.critical_issues}")
    print(f"  High: {result.summary.high_issues}")
    print(f"  Medium: {result.summary.medium_issues}")
    print(f"  Low: {result.summary.low_issues}")

    # Issue breakdown by category
    if result.issues:
        categories = {}
        for issue in result.issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1

        print_section("Issues by Category")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")

    # Quality assessment
    if result.quality_metrics:
        print_section("Quality Assessment")
        qm = result.quality_metrics
        mi = qm.maintainability_index

        if mi >= 80:
            grade = "A - Excellent"
        elif mi >= 60:
            grade = "B - Good"
        elif mi >= 40:
            grade = "C - Fair"
        elif mi >= 20:
            grade = "D - Poor"
        else:
            grade = "F - Critical"

        print(f"Maintainability: {mi:.1f}/100 ({grade})")

    # Top recommendations
    if result.recommendations:
        print_section(f"Top {min(3, len(result.recommendations))} Recommendations")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"\n{i}. {rec.title}")
            print(f"   Priority: {rec.priority} | Effort: {rec.effort} | Impact: {rec.impact}")
            print(f"   {rec.description}")

    print_section("Analysis Complete")
    print("Use the CAP API to integrate this analysis into your workflow!")


async def demo_file_analysis():
    """Demo: Analyzing an actual file."""
    print_header("Demo 6: Analyzing a Real Python File")

    import tempfile
    from pathlib import Path

    # Create a temporary file with sample code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_CODE_VULNERABLE)
        temp_file = f.name

    try:
        client = CAPClient()

        print(f"Analyzing file: {temp_file}")

        result = await client.analyze_file(
            temp_file,
            language="python",
            analysis_types=['security_scan', 'quality_metrics']
        )

        print_section("File Analysis Results")
        print(f"File: {temp_file}")
        print(f"Lines of code: {result.summary.total_lines_of_code}")
        print(f"Issues found: {result.summary.total_issues_found}")

        if result.security_findings:
            print(f"\nSecurity Issues:")
            print(f"  Vulnerabilities: {len(result.security_findings.vulnerabilities)}")
            print(f"  Secrets detected: {len(result.security_findings.secrets_detected)}")

        print("\nFile analysis complete!")

    finally:
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)


# ============================================================================
# MAIN DEMO RUNNER
# ============================================================================


async def run_all_demos():
    """Run all CAP demonstrations."""
    print("\n" + "=" * 80)
    print("  CODE ANALYSIS PROTOCOL (CAP) v1.0 - COMPREHENSIVE DEMO")
    print("  Showcasing automated code analysis, security scanning, and quality metrics")
    print("=" * 80)

    demos = [
        ("Secure Code Analysis", demo_secure_code_analysis),
        ("Security Vulnerability Scanning", demo_security_scanning),
        ("Complexity & Code Smells", demo_complexity_analysis),
        ("Output Formats", demo_output_formats),
        ("Comprehensive Report", demo_comprehensive_report),
        ("File Analysis", demo_file_analysis),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            await demo_func()

            if i < len(demos):
                print("\n" + "-" * 80)
                input("Press Enter to continue to next demo...")

        except Exception as e:
            print(f"\nError in demo '{name}': {e}")
            import traceback
            traceback.print_exc()

    print_header("All Demos Complete!")
    print("\nCAP v1.0 provides:")
    print("  ✓ Static code analysis")
    print("  ✓ Security vulnerability detection")
    print("  ✓ Quality metrics calculation")
    print("  ✓ Complexity analysis")
    print("  ✓ Code smell detection")
    print("  ✓ Multiple output formats (JSON, SARIF, Markdown)")
    print("  ✓ Actionable recommendations")
    print("\nIntegrate CAP into your development workflow today!")
    print("\nVisit https://superstandard.org/cap for full documentation\n")


if __name__ == "__main__":
    asyncio.run(run_all_demos())
