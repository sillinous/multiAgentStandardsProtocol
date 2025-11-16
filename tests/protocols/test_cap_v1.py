"""
Comprehensive tests for Code Analysis Protocol (CAP) v1.0

Tests cover:
- Analysis request creation
- Static code analysis
- Security scanning
- Quality metrics calculation
- Issue detection
- Output formatting
- All analysis types
"""

import pytest
import json
import asyncio
from pathlib import Path
import tempfile

from src.superstandard.protocols.cap_v1 import (
    # Core classes
    CAPClient,
    CodeAnalyzer,

    # Data models
    AnalysisRequest,
    AnalysisResult,
    AnalysisTarget,
    AnalysisConfig,
    CodeIssue,
    CodeLocation,
    QualityMetrics,
    SecurityFindings,
    CyclomaticComplexity,
    TestCoverage,
    CodeDuplication,
    TechnicalDebt,
    Vulnerability,
    SecretDetection,
    SecurityHotspot,
    VulnerabilityCount,
    SuggestedFix,
    Recommendation,

    # Enums
    AnalysisType,
    TargetType,
    Severity,
    IssueCategory,

    # Functions
    analyze_file,
    analyze_code,
    create_analysis_request
)


# ============================================================================
# TEST DATA
# ============================================================================


SAMPLE_PYTHON_CODE = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def process_user_query(query):
    # Security issue: SQL injection vulnerability
    sql = "SELECT * FROM users WHERE name = '%s'" % query
    return execute(sql)

def unsafe_eval(user_input):
    # Security issue: use of eval
    return eval(user_input)

class DataProcessor:
    def __init__(self):
        # Security issue: hardcoded password
        self.password = "secret123"
        self.api_key = "FAKE_API_KEY_TESTING_ONLY_NOT_REAL"
"""

COMPLEX_PYTHON_CODE = """
def complex_function(a, b, c, d, e, f, g):
    # Very complex function with high cyclomatic complexity
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                result = a + b + c + d + e + f + g
                            else:
                                result = a - g
                        else:
                            result = a - f
                    else:
                        result = a - e
                else:
                    result = a - d
            else:
                result = a - c
        else:
            result = a - b
    else:
        result = -1

    for i in range(10):
        if i % 2 == 0:
            result += i
        else:
            result -= i

    while result > 100:
        result -= 10

    try:
        result = result / a
    except:
        result = 0

    return result
"""

CODE_WITH_SMELLS = """
def very_long_function_that_does_too_many_things():
    # This function is intentionally very long
    print("Line 1")
    print("Line 2")
    print("Line 3")
    print("Line 4")
    print("Line 5")
    print("Line 6")
    print("Line 7")
    print("Line 8")
    print("Line 9")
    print("Line 10")
    print("Line 11")
    print("Line 12")
    print("Line 13")
    print("Line 14")
    print("Line 15")
    print("Line 16")
    print("Line 17")
    print("Line 18")
    print("Line 19")
    print("Line 20")
    print("Line 21")
    print("Line 22")
    print("Line 23")
    print("Line 24")
    print("Line 25")
    print("Line 26")
    print("Line 27")
    print("Line 28")
    print("Line 29")
    print("Line 30")
    print("Line 31")
    print("Line 32")
    print("Line 33")
    print("Line 34")
    print("Line 35")
    print("Line 36")
    print("Line 37")
    print("Line 38")
    print("Line 39")
    print("Line 40")
    print("Line 41")
    print("Line 42")
    print("Line 43")
    print("Line 44")
    print("Line 45")
    print("Line 46")
    print("Line 47")
    print("Line 48")
    print("Line 49")
    print("Line 50")
    print("Line 51")
    print("Line 52")
    return "done"

def too_many_params(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
"""

DOCUMENTED_CODE = """
def add(a, b):
    '''Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    '''
    return a + b

class Calculator:
    '''A simple calculator class.'''

    def multiply(self, a, b):
        '''Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b
        '''
        return a * b
"""


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def client():
    """Create a CAP client."""
    return CAPClient()


@pytest.fixture
def analyzer():
    """Create a code analyzer."""
    return CodeAnalyzer()


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_PYTHON_CODE)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# DATA MODEL TESTS
# ============================================================================


def test_code_location_creation():
    """Test CodeLocation creation."""
    location = CodeLocation(
        file="test.py",
        start_line=10,
        end_line=15,
        start_column=5,
        end_column=20,
        code_snippet="print('hello')"
    )

    assert location.file == "test.py"
    assert location.start_line == 10
    assert location.end_line == 15
    assert location.code_snippet == "print('hello')"

    # Test to_dict
    data = location.to_dict()
    assert data['file'] == "test.py"
    assert 'code_snippet' in data


def test_code_issue_creation():
    """Test CodeIssue creation."""
    location = CodeLocation(file="test.py", start_line=5, end_line=5)
    issue = CodeIssue(
        issue_id="issue_001",
        rule_id="security/sql-injection",
        severity=Severity.CRITICAL.value,
        category=IssueCategory.SECURITY.value,
        title="SQL Injection",
        description="Potential SQL injection vulnerability",
        location=location,
        cwe_id=["CWE-89"],
        fix_available=True
    )

    assert issue.issue_id == "issue_001"
    assert issue.severity == "critical"
    assert issue.category == "security"
    assert "CWE-89" in issue.cwe_id

    # Test to_dict
    data = issue.to_dict()
    assert data['title'] == "SQL Injection"
    assert 'location' in data


def test_quality_metrics_creation():
    """Test QualityMetrics creation."""
    metrics = QualityMetrics(
        maintainability_index=75.5,
        cyclomatic_complexity=CyclomaticComplexity(
            average=4.2,
            max=12.0,
            files_over_threshold=2
        ),
        test_coverage=TestCoverage(
            line_coverage=0.85,
            branch_coverage=0.75,
            function_coverage=0.90,
            uncovered_lines=150
        ),
        documentation_coverage=0.80
    )

    assert metrics.maintainability_index == 75.5
    assert metrics.cyclomatic_complexity.average == 4.2
    assert metrics.test_coverage.line_coverage == 0.85
    assert metrics.documentation_coverage == 0.80

    # Test to_dict
    data = metrics.to_dict()
    assert 'maintainability_index' in data
    assert 'cyclomatic_complexity' in data


def test_security_findings_creation():
    """Test SecurityFindings creation."""
    vuln_count = VulnerabilityCount(critical=2, high=5, medium=10, low=3)
    findings = SecurityFindings(
        vulnerability_count=vuln_count,
        vulnerabilities=[
            Vulnerability(
                vulnerability_id="vuln_001",
                title="SQL Injection",
                severity="critical",
                cvss_score=9.1,
                description="SQL injection in user query",
                affected_component="auth.py:line 42"
            )
        ],
        secrets_detected=[
            SecretDetection(
                type="api_key",
                file="config.py",
                line=10,
                confidence="high"
            )
        ]
    )

    assert findings.vulnerability_count.critical == 2
    assert len(findings.vulnerabilities) == 1
    assert len(findings.secrets_detected) == 1

    # Test to_dict
    data = findings.to_dict()
    assert 'vulnerability_count' in data
    assert 'vulnerabilities' in data


def test_analysis_request_creation():
    """Test AnalysisRequest creation."""
    target = AnalysisTarget(
        type=TargetType.FILE.value,
        location="/path/to/file.py",
        language="python"
    )

    config = AnalysisConfig(
        depth="deep",
        include_tests=True,
        severity_threshold="warning"
    )

    request = AnalysisRequest(
        analysis_id="test_123",
        target=target,
        analysis_config=config,
        requested_by="test_agent",
        priority="high"
    )

    assert request.analysis_id == "test_123"
    assert request.target.type == "file"
    assert request.analysis_config.depth == "deep"
    assert request.priority == "high"
    assert request.timestamp is not None

    # Test to_dict
    data = request.to_dict()
    assert data['analysis_id'] == "test_123"
    assert 'target' in data
    assert 'analysis_config' in data


def test_analysis_result_creation():
    """Test AnalysisResult creation."""
    from src.superstandard.protocols.cap_v1 import AnalysisSummary

    summary = AnalysisSummary(
        total_files_analyzed=10,
        total_lines_of_code=5000,
        total_issues_found=25,
        critical_issues=2,
        high_issues=5
    )

    result = AnalysisResult(
        analysis_id="test_123",
        status="completed",
        summary=summary
    )

    assert result.analysis_id == "test_123"
    assert result.status == "completed"
    assert result.summary.total_issues_found == 25
    assert result.analyzer_version == "CAP/1.0.0"
    assert result.analyzed_at is not None

    # Test to_dict
    data = result.to_dict()
    assert data['status'] == "completed"
    assert 'summary' in data


# ============================================================================
# STATIC ANALYSIS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_static_analysis_basic(client):
    """Test basic static analysis."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['static_analysis']
    )

    assert result.status == "completed"
    assert result.summary.total_files_analyzed == 1
    assert result.summary.total_lines_of_code > 0
    assert len(result.issues) > 0


@pytest.mark.asyncio
async def test_static_analysis_missing_docstrings(client):
    """Test detection of missing docstrings."""
    code = """
def function_without_docstring(x):
    return x * 2

def another_function(y):
    return y + 1
"""

    result = await client.analyze_code(code, analysis_types=['static_analysis'])

    # Should find missing docstrings
    docstring_issues = [i for i in result.issues if i.rule_id == 'missing_docstring']
    assert len(docstring_issues) >= 2


@pytest.mark.asyncio
async def test_static_analysis_bare_except(client):
    """Test detection of bare except clauses."""
    code = """
def risky_function():
    try:
        dangerous_operation()
    except:
        pass
"""

    result = await client.analyze_code(code, analysis_types=['static_analysis'])

    # Should find bare except
    bare_except = [i for i in result.issues if i.rule_id == 'bare_except']
    assert len(bare_except) >= 1
    assert bare_except[0].severity == Severity.WARNING.value


@pytest.mark.asyncio
async def test_static_analysis_syntax_error(client):
    """Test handling of syntax errors."""
    code = """
def broken_function(
    # Missing closing parenthesis and body
"""

    result = await client.analyze_code(code, analysis_types=['static_analysis'])

    # Should detect syntax error
    syntax_errors = [i for i in result.issues if i.rule_id == 'syntax_error']
    assert len(syntax_errors) >= 1


# ============================================================================
# SECURITY SCAN TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_security_scan_sql_injection(client):
    """Test SQL injection detection."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    assert result.security_findings is not None

    # Should find SQL injection
    sql_issues = [i for i in result.issues if 'sql' in i.rule_id.lower()]
    assert len(sql_issues) >= 1
    assert sql_issues[0].severity == Severity.CRITICAL.value
    assert "CWE-89" in sql_issues[0].cwe_id


@pytest.mark.asyncio
async def test_security_scan_eval_usage(client):
    """Test detection of eval() usage."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    # Should find eval usage
    eval_issues = [i for i in result.issues if 'eval' in i.rule_id.lower()]
    assert len(eval_issues) >= 1
    assert "CWE-95" in eval_issues[0].cwe_id


@pytest.mark.asyncio
async def test_security_scan_hardcoded_secrets(client):
    """Test detection of hardcoded secrets."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    assert result.security_findings is not None
    assert len(result.security_findings.secrets_detected) >= 2

    # Should find password and API key
    secret_types = {s.type for s in result.security_findings.secrets_detected}
    assert 'password' in secret_types or 'api_key' in secret_types


@pytest.mark.asyncio
async def test_security_scan_vulnerability_count(client):
    """Test vulnerability counting."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    assert result.security_findings is not None
    vuln_count = result.security_findings.vulnerability_count

    # Should have some critical vulnerabilities
    assert vuln_count.critical > 0


@pytest.mark.asyncio
async def test_security_scan_hotspots(client):
    """Test security hotspot detection."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    assert result.security_findings is not None
    assert len(result.security_findings.security_hotspots) > 0


@pytest.mark.asyncio
async def test_security_scan_shell_injection(client):
    """Test shell injection detection."""
    code = """
import os
def run_command(user_input):
    os.system("ls " + user_input)
"""

    result = await client.analyze_code(code, analysis_types=['security_scan'])

    # Should find shell injection
    shell_issues = [i for i in result.issues if 'shell' in i.rule_id.lower()]
    assert len(shell_issues) >= 1
    assert shell_issues[0].severity == Severity.CRITICAL.value


@pytest.mark.asyncio
async def test_security_scan_weak_crypto(client):
    """Test weak cryptography detection."""
    code = """
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""

    result = await client.analyze_code(code, analysis_types=['security_scan'])

    # Should find weak crypto
    crypto_issues = [i for i in result.issues if 'crypto' in i.rule_id.lower()]
    assert len(crypto_issues) >= 1


# ============================================================================
# QUALITY METRICS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_quality_metrics_calculation(client):
    """Test quality metrics calculation."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['quality_metrics']
    )

    assert result.quality_metrics is not None
    assert result.quality_metrics.maintainability_index >= 0
    assert result.quality_metrics.maintainability_index <= 100


@pytest.mark.asyncio
async def test_quality_metrics_complexity(client):
    """Test cyclomatic complexity calculation."""
    result = await client.analyze_code(
        COMPLEX_PYTHON_CODE,
        analysis_types=['quality_metrics']
    )

    assert result.quality_metrics is not None
    assert result.quality_metrics.cyclomatic_complexity is not None

    cc = result.quality_metrics.cyclomatic_complexity
    assert cc.average > 1.0  # Complex code should have high complexity
    assert cc.max > 10.0


@pytest.mark.asyncio
async def test_quality_metrics_documentation(client):
    """Test documentation coverage calculation."""
    result = await client.analyze_code(
        DOCUMENTED_CODE,
        analysis_types=['quality_metrics']
    )

    assert result.quality_metrics is not None
    assert result.quality_metrics.documentation_coverage is not None
    assert result.quality_metrics.documentation_coverage > 0.5  # Well documented


@pytest.mark.asyncio
async def test_quality_metrics_duplication(client):
    """Test code duplication detection."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['quality_metrics']
    )

    assert result.quality_metrics is not None
    assert result.quality_metrics.code_duplication is not None

    dup = result.quality_metrics.code_duplication
    assert dup.duplication_percentage >= 0
    assert dup.duplication_percentage <= 100


@pytest.mark.asyncio
async def test_quality_metrics_technical_debt(client):
    """Test technical debt calculation."""
    result = await client.analyze_code(
        COMPLEX_PYTHON_CODE,
        analysis_types=['quality_metrics']
    )

    assert result.quality_metrics is not None
    assert result.quality_metrics.technical_debt is not None

    debt = result.quality_metrics.technical_debt
    assert debt.total_minutes >= 0
    assert debt.debt_ratio >= 0


# ============================================================================
# COMPLEXITY ANALYSIS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_complexity_analysis_high_complexity(client):
    """Test detection of high complexity functions."""
    result = await client.analyze_code(
        COMPLEX_PYTHON_CODE,
        analysis_types=['complexity_analysis']
    )

    # Should find high complexity issues
    complexity_issues = [i for i in result.issues if i.rule_id == 'high_complexity']
    assert len(complexity_issues) >= 1
    assert complexity_issues[0].category == IssueCategory.MAINTAINABILITY.value


@pytest.mark.asyncio
async def test_complexity_analysis_simple_code(client):
    """Test complexity analysis on simple code."""
    code = """
def simple_add(a, b):
    return a + b

def simple_multiply(a, b):
    return a * b
"""

    result = await client.analyze_code(code, analysis_types=['complexity_analysis'])

    # Should find no or few complexity issues
    complexity_issues = [i for i in result.issues if i.rule_id == 'high_complexity']
    assert len(complexity_issues) == 0


# ============================================================================
# CODE SMELL DETECTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_code_smell_long_function(client):
    """Test detection of long functions."""
    result = await client.analyze_code(
        CODE_WITH_SMELLS,
        analysis_types=['code_smell_detection']
    )

    # Should find long function
    long_func = [i for i in result.issues if i.rule_id == 'long_function']
    assert len(long_func) >= 1
    assert long_func[0].category == IssueCategory.CODE_SMELL.value


@pytest.mark.asyncio
async def test_code_smell_too_many_parameters(client):
    """Test detection of too many parameters."""
    result = await client.analyze_code(
        CODE_WITH_SMELLS,
        analysis_types=['code_smell_detection']
    )

    # Should find too many parameters
    param_issues = [i for i in result.issues if i.rule_id == 'too_many_parameters']
    assert len(param_issues) >= 1


# ============================================================================
# MULTI-TYPE ANALYSIS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_analysis_types(client):
    """Test running multiple analysis types together."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['static_analysis', 'security_scan', 'quality_metrics']
    )

    assert result.status == "completed"
    assert len(result.issues) > 0
    assert result.quality_metrics is not None
    assert result.security_findings is not None


@pytest.mark.asyncio
async def test_comprehensive_analysis(client):
    """Test comprehensive analysis with all types."""
    result = await client.analyze_code(
        COMPLEX_PYTHON_CODE,
        analysis_types=[
            'static_analysis',
            'security_scan',
            'quality_metrics',
            'complexity_analysis',
            'code_smell_detection'
        ]
    )

    assert result.status == "completed"
    assert result.summary.total_issues_found > 0


# ============================================================================
# FILE ANALYSIS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_file(client, temp_python_file):
    """Test analyzing a file."""
    result = await client.analyze_file(
        temp_python_file,
        analysis_types=['security_scan']
    )

    assert result.status == "completed"
    assert result.summary.total_files_analyzed == 1


@pytest.mark.asyncio
async def test_analyze_nonexistent_file(client):
    """Test handling of nonexistent file."""
    result = await client.analyze_file(
        "/nonexistent/file.py",
        analysis_types=['static_analysis']
    )

    assert result.status == "failed"


# ============================================================================
# RECOMMENDATIONS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_recommendations_critical_issues(client):
    """Test recommendations for critical issues."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan']
    )

    # Should have recommendations for critical issues
    critical_recs = [r for r in result.recommendations if r.priority == 'critical']
    assert len(critical_recs) > 0


@pytest.mark.asyncio
async def test_recommendations_complexity(client):
    """Test recommendations for high complexity."""
    result = await client.analyze_code(
        COMPLEX_PYTHON_CODE,
        analysis_types=['quality_metrics']
    )

    # Should have recommendations about complexity
    assert len(result.recommendations) > 0


@pytest.mark.asyncio
async def test_recommendations_documentation(client):
    """Test recommendations for low documentation."""
    code = """
def func1():
    return 1

def func2():
    return 2

def func3():
    return 3
"""

    result = await client.analyze_code(
        code,
        analysis_types=['quality_metrics']
    )

    # Should recommend improving documentation
    doc_recs = [r for r in result.recommendations if 'documentation' in r.title.lower()]
    assert len(doc_recs) > 0


# ============================================================================
# OUTPUT FORMAT TESTS
# ============================================================================


def test_format_json(client):
    """Test JSON output format."""
    from src.superstandard.protocols.cap_v1 import AnalysisSummary

    result = AnalysisResult(
        analysis_id="test_123",
        status="completed",
        summary=AnalysisSummary(total_files_analyzed=1)
    )

    json_output = client.format_result(result, format="json")

    # Should be valid JSON
    data = json.loads(json_output)
    assert data['analysis_id'] == "test_123"
    assert data['status'] == "completed"


def test_format_markdown(client):
    """Test Markdown output format."""
    from src.superstandard.protocols.cap_v1 import AnalysisSummary

    result = AnalysisResult(
        analysis_id="test_123",
        status="completed",
        summary=AnalysisSummary(
            total_files_analyzed=10,
            total_issues_found=5
        )
    )

    md_output = client.format_result(result, format="markdown")

    assert "# Code Analysis Report" in md_output
    assert "test_123" in md_output
    assert "## Summary" in md_output


def test_format_sarif(client):
    """Test SARIF output format."""
    from src.superstandard.protocols.cap_v1 import AnalysisSummary

    location = CodeLocation(file="test.py", start_line=10, end_line=10)
    issue = CodeIssue(
        issue_id="issue_001",
        rule_id="test_rule",
        severity=Severity.ERROR.value,
        category=IssueCategory.BUG.value,
        title="Test Issue",
        description="Test description",
        location=location
    )

    result = AnalysisResult(
        analysis_id="test_123",
        status="completed",
        summary=AnalysisSummary(),
        issues=[issue]
    )

    sarif_output = client.format_result(result, format="sarif")

    # Should be valid JSON
    data = json.loads(sarif_output)
    assert data['version'] == "2.1.0"
    assert 'runs' in data
    assert len(data['runs'][0]['results']) == 1


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_code_function():
    """Test convenience analyze_code function."""
    result = await analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['static_analysis']
    )

    assert result.status == "completed"
    assert isinstance(result, AnalysisResult)


@pytest.mark.asyncio
async def test_analyze_file_function(temp_python_file):
    """Test convenience analyze_file function."""
    result = await analyze_file(
        temp_python_file,
        analysis_types=['security_scan']
    )

    assert result.status == "completed"
    assert isinstance(result, AnalysisResult)


def test_create_analysis_request_function():
    """Test create_analysis_request function."""
    request = create_analysis_request(
        target_type="file",
        location="/path/to/file.py",
        language="python"
    )

    assert isinstance(request, AnalysisRequest)
    assert request.target.type == "file"
    assert request.target.location == "/path/to/file.py"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
async def test_empty_code_analysis(client):
    """Test analysis of empty code."""
    result = await client.analyze_code("", analysis_types=['static_analysis'])

    # Should handle gracefully
    assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_non_python_code(client):
    """Test analysis of non-Python code."""
    javascript_code = """
function hello() {
    console.log("Hello");
}
"""

    result = await client.analyze_code(
        javascript_code,
        language="javascript",
        analysis_types=['static_analysis']
    )

    # Should handle gracefully
    assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_analysis_with_config(client):
    """Test analysis with custom configuration."""
    config = AnalysisConfig(
        depth="deep",
        include_tests=False,
        severity_threshold="error"
    )

    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['static_analysis'],
        config=config
    )

    assert result.status == "completed"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_analysis_duration(client):
    """Test that analysis completes in reasonable time."""
    import time

    start = time.time()
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['static_analysis', 'security_scan']
    )
    duration = time.time() - start

    # Should complete in under 5 seconds
    assert duration < 5.0
    assert result.summary.analysis_duration_ms > 0


@pytest.mark.asyncio
async def test_large_code_analysis(client):
    """Test analysis of larger code."""
    # Generate large code
    large_code = "\n".join([
        f"def function_{i}():\n    return {i}"
        for i in range(100)
    ])

    result = await client.analyze_code(
        large_code,
        analysis_types=['static_analysis']
    )

    assert result.status == "completed"
    assert result.summary.total_files_analyzed == 1


# ============================================================================
# SUMMARY CALCULATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_summary_calculation(client):
    """Test summary statistics calculation."""
    result = await client.analyze_code(
        SAMPLE_PYTHON_CODE,
        analysis_types=['security_scan', 'static_analysis']
    )

    summary = result.summary

    # Verify summary fields
    assert summary.total_files_analyzed >= 0
    assert summary.total_lines_of_code > 0
    assert summary.total_issues_found >= 0

    # Verify issue counts add up
    total_counted = (
        summary.critical_issues +
        summary.high_issues +
        summary.medium_issues +
        summary.low_issues
    )
    assert total_counted == summary.total_issues_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
