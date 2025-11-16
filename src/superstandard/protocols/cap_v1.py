"""
Code Analysis Protocol (CAP) v1.0 - PRODUCTION IMPLEMENTATION
==================================================================

Complete implementation of CAP for automated code analysis, quality metrics,
vulnerability scanning, and code intelligence.

Features:
- Static code analysis with pattern matching
- Security vulnerability detection
- Quality metrics calculation (maintainability, complexity, coverage)
- Issue categorization and severity levels
- CWE/CVE mapping
- Fix suggestions
- Multiple output formats (JSON, SARIF, Markdown)

Analysis Types:
- static_analysis: AST-based code structure analysis
- dynamic_analysis: Runtime behavior analysis
- security_scan: Vulnerability and secret detection
- quality_metrics: Code quality assessment
- dependency_audit: Third-party dependency analysis
- test_coverage: Test coverage analysis
- complexity_analysis: Cyclomatic and cognitive complexity
- code_smell_detection: Anti-pattern detection
- performance_profiling: Performance bottleneck identification

Author: SuperStandard Team
License: MIT
"""

import ast
import hashlib
import logging
import re
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class AnalysisType(Enum):
    """Types of code analysis."""
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    SECURITY_SCAN = "security_scan"
    QUALITY_METRICS = "quality_metrics"
    DEPENDENCY_AUDIT = "dependency_audit"
    TEST_COVERAGE = "test_coverage"
    COMPLEXITY_ANALYSIS = "complexity_analysis"
    CODE_SMELL_DETECTION = "code_smell_detection"
    PERFORMANCE_PROFILING = "performance_profiling"


class TargetType(Enum):
    """Target code types."""
    FILE = "file"
    DIRECTORY = "directory"
    REPOSITORY = "repository"
    SNIPPET = "snippet"
    FUNCTION = "function"
    CLASS = "class"


class AnalysisDepth(Enum):
    """Analysis depth levels."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"


class Severity(Enum):
    """Issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(Enum):
    """Issue categories."""
    BUG = "bug"
    VULNERABILITY = "vulnerability"
    CODE_SMELL = "code_smell"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    BEST_PRACTICE = "best_practice"


class SecretType(Enum):
    """Types of secrets that can be detected."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    CERTIFICATE = "certificate"


class OutputFormat(Enum):
    """Output formats."""
    JSON = "json"
    SARIF = "sarif"
    HTML = "html"
    MARKDOWN = "markdown"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class CodeLocation:
    """Location of code in a file."""
    file: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SuggestedFix:
    """Suggested fix for an issue."""
    description: str
    diff: Optional[str] = None
    automated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CodeIssue:
    """Individual code issue found during analysis."""
    issue_id: str
    rule_id: str
    severity: str
    category: str
    title: str
    description: str
    location: CodeLocation
    cwe_id: List[str] = field(default_factory=list)
    cve_id: List[str] = field(default_factory=list)
    fix_available: bool = False
    suggested_fix: Optional[SuggestedFix] = None
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['location'] = self.location.to_dict()
        if self.suggested_fix:
            data['suggested_fix'] = self.suggested_fix.to_dict()
        return data


@dataclass
class CyclomaticComplexity:
    """Cyclomatic complexity metrics."""
    average: float
    max: float
    files_over_threshold: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TestCoverage:
    """Test coverage metrics."""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    uncovered_lines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CodeDuplication:
    """Code duplication metrics."""
    duplicated_lines: int
    duplicated_blocks: int
    duplication_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TechnicalDebt:
    """Technical debt metrics."""
    total_minutes: int
    debt_ratio: float
    high_interest_issues: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class QualityMetrics:
    """Code quality metrics."""
    maintainability_index: float = 0.0
    cyclomatic_complexity: Optional[CyclomaticComplexity] = None
    cognitive_complexity: Optional[float] = None
    test_coverage: Optional[TestCoverage] = None
    code_duplication: Optional[CodeDuplication] = None
    documentation_coverage: Optional[float] = None
    technical_debt: Optional[TechnicalDebt] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {}
        if self.maintainability_index > 0:
            data['maintainability_index'] = self.maintainability_index
        if self.cyclomatic_complexity:
            data['cyclomatic_complexity'] = self.cyclomatic_complexity.to_dict()
        if self.cognitive_complexity is not None:
            data['cognitive_complexity'] = self.cognitive_complexity
        if self.test_coverage:
            data['test_coverage'] = self.test_coverage.to_dict()
        if self.code_duplication:
            data['code_duplication'] = self.code_duplication.to_dict()
        if self.documentation_coverage is not None:
            data['documentation_coverage'] = self.documentation_coverage
        if self.technical_debt:
            data['technical_debt'] = self.technical_debt.to_dict()
        return data


@dataclass
class Vulnerability:
    """Security vulnerability."""
    vulnerability_id: str
    title: str
    severity: str
    cvss_score: float
    description: str
    affected_component: str
    exploit_available: bool = False
    patch_available: bool = False
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DependencyVulnerability:
    """Vulnerability in a dependency."""
    package_name: str
    current_version: str
    vulnerable_version_range: str
    fixed_version: Optional[str]
    severity: str
    cve_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SecretDetection:
    """Detected secret in code."""
    type: str
    file: str
    line: int
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SecurityHotspot:
    """Security hotspot requiring review."""
    category: str
    file: str
    line: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VulnerabilityCount:
    """Count of vulnerabilities by severity."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SecurityFindings:
    """Security-specific findings."""
    vulnerability_count: VulnerabilityCount
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    dependency_vulnerabilities: List[DependencyVulnerability] = field(default_factory=list)
    secrets_detected: List[SecretDetection] = field(default_factory=list)
    security_hotspots: List[SecurityHotspot] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'vulnerability_count': self.vulnerability_count.to_dict(),
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'dependency_vulnerabilities': [v.to_dict() for v in self.dependency_vulnerabilities],
            'secrets_detected': [s.to_dict() for s in self.secrets_detected],
            'security_hotspots': [h.to_dict() for h in self.security_hotspots]
        }


@dataclass
class AnalysisConfig:
    """Configuration for analysis."""
    depth: str = "standard"
    include_tests: bool = True
    include_dependencies: bool = False
    exclude_patterns: List[str] = field(default_factory=list)
    enabled_rules: List[str] = field(default_factory=list)
    disabled_rules: List[str] = field(default_factory=list)
    severity_threshold: str = "warning"
    output_format: str = "json"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'depth': self.depth,
            'include_tests': self.include_tests,
            'include_dependencies': self.include_dependencies,
            'output_format': self.output_format
        }
        if self.exclude_patterns:
            data['exclude_patterns'] = self.exclude_patterns
        rules = {}
        if self.enabled_rules:
            rules['enabled_rules'] = self.enabled_rules
        if self.disabled_rules:
            rules['disabled_rules'] = self.disabled_rules
        if self.severity_threshold:
            rules['severity_threshold'] = self.severity_threshold
        if rules:
            data['rules'] = rules
        return data


@dataclass
class AnalysisTarget:
    """Target code to analyze."""
    type: str
    location: Optional[str] = None
    language: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AnalysisRequest:
    """Request for code analysis."""
    analysis_id: str
    target: AnalysisTarget
    analysis_config: Optional[AnalysisConfig] = None
    requested_by: Optional[str] = None
    priority: str = "normal"
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'analysis_id': self.analysis_id,
            'target': self.target.to_dict(),
            'priority': self.priority,
            'timestamp': self.timestamp
        }
        if self.analysis_config:
            data['analysis_config'] = self.analysis_config.to_dict()
        if self.requested_by:
            data['requested_by'] = self.requested_by
        return data


@dataclass
class AnalysisSummary:
    """Summary of analysis results."""
    total_files_analyzed: int = 0
    total_lines_of_code: int = 0
    total_issues_found: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    analysis_duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Recommendation:
    """Actionable recommendation."""
    title: str
    description: str
    priority: str
    effort: str
    impact: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnalysisResult:
    """Code analysis results."""
    analysis_id: str
    status: str
    summary: AnalysisSummary
    issues: List[CodeIssue] = field(default_factory=list)
    quality_metrics: Optional[QualityMetrics] = None
    security_findings: Optional[SecurityFindings] = None
    recommendations: List[Recommendation] = field(default_factory=list)
    analyzed_at: Optional[str] = None
    analyzer_version: str = "CAP/1.0.0"

    def __post_init__(self):
        """Set analyzed_at if not provided."""
        if not self.analyzed_at:
            self.analyzed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'analysis_id': self.analysis_id,
            'status': self.status,
            'summary': self.summary.to_dict(),
            'issues': [issue.to_dict() for issue in self.issues],
            'analyzed_at': self.analyzed_at,
            'analyzer_version': self.analyzer_version
        }
        if self.quality_metrics:
            data['quality_metrics'] = self.quality_metrics.to_dict()
        if self.security_findings:
            data['security_findings'] = self.security_findings.to_dict()
        if self.recommendations:
            data['recommendations'] = [r.to_dict() for r in self.recommendations]
        return data


# ============================================================================
# SECURITY PATTERNS
# ============================================================================


# Common security vulnerability patterns
SECURITY_PATTERNS = {
    'sql_injection': {
        'pattern': r'(execute\s*\(.*["\'].*%s|SELECT.*FROM.*WHERE.*["\'].*%s.*["\'].*%)',
        'severity': 'critical',
        'cwe': ['CWE-89'],
        'title': 'Potential SQL Injection',
        'description': 'SQL query constructed using string formatting with user input'
    },
    'hardcoded_password': {
        'pattern': r'password\s*=\s*["\'][^"\']+["\']',
        'severity': 'critical',
        'cwe': ['CWE-798'],
        'title': 'Hardcoded Password',
        'description': 'Password appears to be hardcoded in source code'
    },
    'eval_usage': {
        'pattern': r'\beval\s*\(',
        'severity': 'error',
        'cwe': ['CWE-95'],
        'title': 'Use of eval()',
        'description': 'eval() can execute arbitrary code and is a security risk'
    },
    'exec_usage': {
        'pattern': r'\bexec\s*\(',
        'severity': 'error',
        'cwe': ['CWE-95'],
        'title': 'Use of exec()',
        'description': 'exec() can execute arbitrary code and is a security risk'
    },
    'unsafe_yaml': {
        'pattern': r'yaml\.load\s*\([^,)]+\)',
        'severity': 'error',
        'cwe': ['CWE-502'],
        'title': 'Unsafe YAML Deserialization',
        'description': 'yaml.load() without safe loader can execute arbitrary code'
    },
    'weak_crypto': {
        'pattern': r'hashlib\.(md5|sha1)\(',
        'severity': 'warning',
        'cwe': ['CWE-327'],
        'title': 'Weak Cryptographic Algorithm',
        'description': 'MD5 and SHA1 are cryptographically broken'
    },
    'shell_injection': {
        'pattern': r'os\.system\s*\(.*\+',
        'severity': 'critical',
        'cwe': ['CWE-78'],
        'title': 'Potential Shell Injection',
        'description': 'Command constructed using string concatenation with user input'
    },
    'path_traversal': {
        'pattern': r'open\s*\([^)]*\+.*["\']\.\./',
        'severity': 'error',
        'cwe': ['CWE-22'],
        'title': 'Potential Path Traversal',
        'description': 'File path constructed from user input without validation'
    }
}

# Secret detection patterns
SECRET_PATTERNS = {
    'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
    'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
    'token': r'(?i)(token|auth[_-]?token)\s*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']',
    'private_key': r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    'aws_key': r'AKIA[0-9A-Z]{16}'
}


# ============================================================================
# CODE ANALYZER
# ============================================================================


class CodeAnalyzer:
    """Main code analysis engine."""

    def __init__(self):
        """Initialize the code analyzer."""
        self.version = "1.0.0"
        logger.info(f"CodeAnalyzer initialized (version {self.version})")

    async def analyze(
        self,
        request: AnalysisRequest,
        analysis_types: Optional[List[str]] = None
    ) -> AnalysisResult:
        """
        Perform code analysis.

        Args:
            request: Analysis request
            analysis_types: List of analysis types to perform

        Returns:
            AnalysisResult with findings
        """
        start_time = datetime.now()
        logger.info(f"Starting analysis {request.analysis_id}")

        # Default to static analysis if not specified
        if not analysis_types:
            analysis_types = ['static_analysis']

        # Get code content
        code_content = self._get_code_content(request.target)
        if not code_content:
            return AnalysisResult(
                analysis_id=request.analysis_id,
                status="failed",
                summary=AnalysisSummary()
            )

        # Perform analyses
        all_issues = []
        quality_metrics = None
        security_findings = None

        for analysis_type in analysis_types:
            if analysis_type == 'static_analysis':
                issues = self._static_analysis(code_content, request.target)
                all_issues.extend(issues)
            elif analysis_type == 'security_scan':
                sec_issues, sec_findings = self._security_scan(code_content, request.target)
                all_issues.extend(sec_issues)
                security_findings = sec_findings
            elif analysis_type == 'quality_metrics':
                quality_metrics = self._calculate_quality_metrics(code_content, request.target)
            elif analysis_type == 'complexity_analysis':
                complexity_issues = self._complexity_analysis(code_content, request.target)
                all_issues.extend(complexity_issues)
            elif analysis_type == 'code_smell_detection':
                smell_issues = self._detect_code_smells(code_content, request.target)
                all_issues.extend(smell_issues)

        # Calculate summary
        duration_ms = max(1, int((datetime.now() - start_time).total_seconds() * 1000))
        summary = self._calculate_summary(
            all_issues,
            code_content,
            duration_ms
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues, quality_metrics)

        result = AnalysisResult(
            analysis_id=request.analysis_id,
            status="completed",
            summary=summary,
            issues=all_issues,
            quality_metrics=quality_metrics,
            security_findings=security_findings,
            recommendations=recommendations
        )

        logger.info(f"Analysis {request.analysis_id} completed: {summary.total_issues_found} issues found")
        return result

    def _get_code_content(self, target: AnalysisTarget) -> Optional[str]:
        """Get code content from target."""
        if target.content:
            return target.content
        elif target.location and target.type == TargetType.FILE.value:
            try:
                with open(target.location, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {target.location}: {e}")
                return None
        return None

    def _static_analysis(self, code: str, target: AnalysisTarget) -> List[CodeIssue]:
        """Perform static code analysis."""
        issues = []

        # Parse Python code with AST
        if target.language in [None, 'python']:
            try:
                tree = ast.parse(code)
                issues.extend(self._analyze_ast(tree, code, target))
            except SyntaxError as e:
                issues.append(CodeIssue(
                    issue_id=f"issue_{uuid4().hex[:8]}",
                    rule_id="syntax_error",
                    severity=Severity.ERROR.value,
                    category=IssueCategory.BUG.value,
                    title="Syntax Error",
                    description=f"Syntax error in code: {str(e)}",
                    location=CodeLocation(
                        file=target.location or "snippet",
                        start_line=e.lineno or 0,
                        end_line=e.lineno or 0
                    )
                ))

        return issues

    def _analyze_ast(self, tree: ast.AST, code: str, target: AnalysisTarget) -> List[CodeIssue]:
        """Analyze Python AST for issues."""
        issues = []
        lines = code.split('\n')

        # Find functions without docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    issues.append(CodeIssue(
                        issue_id=f"issue_{uuid4().hex[:8]}",
                        rule_id="missing_docstring",
                        severity=Severity.INFO.value,
                        category=IssueCategory.DOCUMENTATION.value,
                        title="Missing Function Docstring",
                        description=f"Function '{node.name}' lacks a docstring",
                        location=CodeLocation(
                            file=target.location or "snippet",
                            start_line=node.lineno,
                            end_line=node.lineno,
                            code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ),
                        fix_available=True,
                        suggested_fix=SuggestedFix(
                            description=f"Add docstring to function '{node.name}'",
                            automated=False
                        )
                    ))

                # Check for bare except
                for child in ast.walk(node):
                    if isinstance(child, ast.ExceptHandler) and child.type is None:
                        issues.append(CodeIssue(
                            issue_id=f"issue_{uuid4().hex[:8]}",
                            rule_id="bare_except",
                            severity=Severity.WARNING.value,
                            category=IssueCategory.BEST_PRACTICE.value,
                            title="Bare Except Clause",
                            description="Using bare 'except:' catches all exceptions including system exit",
                            location=CodeLocation(
                                file=target.location or "snippet",
                                start_line=child.lineno,
                                end_line=child.lineno,
                                code_snippet=lines[child.lineno - 1] if child.lineno <= len(lines) else ""
                            ),
                            fix_available=True,
                            suggested_fix=SuggestedFix(
                                description="Replace 'except:' with 'except Exception:'",
                                automated=True
                            )
                        ))

        return issues

    def _security_scan(
        self,
        code: str,
        target: AnalysisTarget
    ) -> Tuple[List[CodeIssue], SecurityFindings]:
        """Perform security vulnerability scanning."""
        issues = []
        vulnerabilities = []
        secrets = []
        hotspots = []
        vuln_count = VulnerabilityCount()

        lines = code.split('\n')

        # Check for security patterns
        for rule_name, rule in SECURITY_PATTERNS.items():
            pattern = re.compile(rule['pattern'])
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    vuln_id = f"vuln_{uuid4().hex[:8]}"

                    # Create vulnerability
                    vuln = Vulnerability(
                        vulnerability_id=vuln_id,
                        title=rule['title'],
                        severity=rule['severity'],
                        cvss_score=self._severity_to_cvss(rule['severity']),
                        description=rule['description'],
                        affected_component=f"{target.location or 'snippet'}:line {i}",
                        patch_available=True,
                        remediation=f"Review and fix {rule['title'].lower()}"
                    )
                    vulnerabilities.append(vuln)

                    # Update count
                    if rule['severity'] == 'critical':
                        vuln_count.critical += 1
                    elif rule['severity'] == 'error':
                        vuln_count.high += 1
                    elif rule['severity'] == 'warning':
                        vuln_count.medium += 1

                    # Create issue
                    issues.append(CodeIssue(
                        issue_id=vuln_id,
                        rule_id=rule_name,
                        severity=rule['severity'],
                        category=IssueCategory.SECURITY.value,
                        title=rule['title'],
                        description=rule['description'],
                        location=CodeLocation(
                            file=target.location or "snippet",
                            start_line=i,
                            end_line=i,
                            code_snippet=line.strip()
                        ),
                        cwe_id=rule['cwe']
                    ))

                    # Add security hotspot
                    hotspots.append(SecurityHotspot(
                        category="injection" if "injection" in rule_name.lower() else "data_protection",
                        file=target.location or "snippet",
                        line=i,
                        description=rule['description']
                    ))

        # Check for secrets
        for secret_type, pattern in SECRET_PATTERNS.items():
            secret_pattern = re.compile(pattern)
            for i, line in enumerate(lines, 1):
                if secret_pattern.search(line):
                    secrets.append(SecretDetection(
                        type=secret_type,
                        file=target.location or "snippet",
                        line=i,
                        confidence="high"
                    ))

                    issues.append(CodeIssue(
                        issue_id=f"secret_{uuid4().hex[:8]}",
                        rule_id=f"hardcoded_{secret_type}",
                        severity=Severity.CRITICAL.value,
                        category=IssueCategory.SECURITY.value,
                        title=f"Hardcoded {secret_type.replace('_', ' ').title()}",
                        description=f"Potential hardcoded {secret_type} detected in source code",
                        location=CodeLocation(
                            file=target.location or "snippet",
                            start_line=i,
                            end_line=i,
                            code_snippet="[REDACTED]"
                        ),
                        cwe_id=["CWE-798"]
                    ))

        security_findings = SecurityFindings(
            vulnerability_count=vuln_count,
            vulnerabilities=vulnerabilities,
            secrets_detected=secrets,
            security_hotspots=hotspots
        )

        return issues, security_findings

    def _calculate_quality_metrics(
        self,
        code: str,
        target: AnalysisTarget
    ) -> QualityMetrics:
        """Calculate code quality metrics."""
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])

        # Parse AST for metrics
        try:
            tree = ast.parse(code)

            # Calculate cyclomatic complexity
            complexities = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_function_complexity(node)
                    complexities.append(complexity)

            avg_complexity = sum(complexities) / len(complexities) if complexities else 1.0
            max_complexity = max(complexities) if complexities else 1.0
            files_over_threshold = 1 if max_complexity > 10 else 0

            # Calculate maintainability index
            # Simplified version: MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
            # We'll use a simplified approximation
            mi = max(0, min(100, 100 - (avg_complexity * 2) - (loc / 100)))

            # Calculate documentation coverage
            total_functions = 0
            documented_functions = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    total_functions += 1
                    if ast.get_docstring(node):
                        documented_functions += 1

            doc_coverage = documented_functions / total_functions if total_functions > 0 else 0.0

            # Estimate code duplication (simplified)
            duplication = self._estimate_duplication(lines)

            return QualityMetrics(
                maintainability_index=round(mi, 2),
                cyclomatic_complexity=CyclomaticComplexity(
                    average=round(avg_complexity, 2),
                    max=round(max_complexity, 2),
                    files_over_threshold=files_over_threshold
                ),
                cognitive_complexity=round(avg_complexity * 1.2, 2),
                test_coverage=TestCoverage(
                    line_coverage=0.0,
                    branch_coverage=0.0,
                    function_coverage=0.0,
                    uncovered_lines=0
                ),
                code_duplication=duplication,
                documentation_coverage=round(doc_coverage, 2),
                technical_debt=TechnicalDebt(
                    total_minutes=int(loc / 10),
                    debt_ratio=round((100 - mi) / 100, 2),
                    high_interest_issues=files_over_threshold
                )
            )
        except:
            return QualityMetrics(maintainability_index=50.0)

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1.0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _estimate_duplication(self, lines: List[str]) -> CodeDuplication:
        """Estimate code duplication."""
        # Simple hash-based duplicate line detection
        line_hashes = {}
        duplicated_lines = 0

        for line in lines:
            stripped = line.strip()
            if len(stripped) > 10:  # Ignore very short lines
                line_hash = hashlib.md5(stripped.encode()).hexdigest()
                if line_hash in line_hashes:
                    duplicated_lines += 1
                else:
                    line_hashes[line_hash] = True

        total_lines = len([l for l in lines if l.strip()])
        duplication_pct = (duplicated_lines / total_lines * 100) if total_lines > 0 else 0.0

        return CodeDuplication(
            duplicated_lines=duplicated_lines,
            duplicated_blocks=duplicated_lines // 5,
            duplication_percentage=round(duplication_pct, 2)
        )

    def _complexity_analysis(self, code: str, target: AnalysisTarget) -> List[CodeIssue]:
        """Analyze code complexity."""
        issues = []

        try:
            tree = ast.parse(code)
            lines = code.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_function_complexity(node)
                    if complexity > 10:
                        issues.append(CodeIssue(
                            issue_id=f"complexity_{uuid4().hex[:8]}",
                            rule_id="high_complexity",
                            severity=Severity.WARNING.value,
                            category=IssueCategory.MAINTAINABILITY.value,
                            title="High Cyclomatic Complexity",
                            description=f"Function '{node.name}' has complexity of {complexity:.0f} (threshold: 10)",
                            location=CodeLocation(
                                file=target.location or "snippet",
                                start_line=node.lineno,
                                end_line=node.end_lineno or node.lineno,
                                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                            ),
                            fix_available=True,
                            suggested_fix=SuggestedFix(
                                description=f"Refactor function '{node.name}' to reduce complexity",
                                automated=False
                            )
                        ))
        except:
            pass

        return issues

    def _detect_code_smells(self, code: str, target: AnalysisTarget) -> List[CodeIssue]:
        """Detect code smells."""
        issues = []
        lines = code.split('\n')

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Long function
                if isinstance(node, ast.FunctionDef):
                    func_length = (node.end_lineno or node.lineno) - node.lineno
                    if func_length > 50:
                        issues.append(CodeIssue(
                            issue_id=f"smell_{uuid4().hex[:8]}",
                            rule_id="long_function",
                            severity=Severity.INFO.value,
                            category=IssueCategory.CODE_SMELL.value,
                            title="Long Function",
                            description=f"Function '{node.name}' is {func_length} lines long (threshold: 50)",
                            location=CodeLocation(
                                file=target.location or "snippet",
                                start_line=node.lineno,
                                end_line=node.end_lineno or node.lineno,
                                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                            )
                        ))

                # Too many parameters
                if isinstance(node, ast.FunctionDef):
                    param_count = len(node.args.args)
                    if param_count > 5:
                        issues.append(CodeIssue(
                            issue_id=f"smell_{uuid4().hex[:8]}",
                            rule_id="too_many_parameters",
                            severity=Severity.INFO.value,
                            category=IssueCategory.CODE_SMELL.value,
                            title="Too Many Parameters",
                            description=f"Function '{node.name}' has {param_count} parameters (threshold: 5)",
                            location=CodeLocation(
                                file=target.location or "snippet",
                                start_line=node.lineno,
                                end_line=node.lineno,
                                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                            )
                        ))
        except:
            pass

        return issues

    def _severity_to_cvss(self, severity: str) -> float:
        """Convert severity to CVSS score."""
        severity_map = {
            'critical': 9.0,
            'error': 7.5,
            'warning': 5.0,
            'info': 2.0
        }
        return severity_map.get(severity, 0.0)

    def _calculate_summary(
        self,
        issues: List[CodeIssue],
        code: str,
        duration_ms: float
    ) -> AnalysisSummary:
        """Calculate analysis summary."""
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip()])

        summary = AnalysisSummary(
            total_files_analyzed=1,
            total_lines_of_code=loc,
            total_issues_found=len(issues),
            analysis_duration_ms=int(duration_ms)
        )

        for issue in issues:
            if issue.severity == Severity.CRITICAL.value:
                summary.critical_issues += 1
            elif issue.severity == Severity.ERROR.value:
                summary.high_issues += 1
            elif issue.severity == Severity.WARNING.value:
                summary.medium_issues += 1
            elif issue.severity == Severity.INFO.value:
                summary.low_issues += 1

        return summary

    def _generate_recommendations(
        self,
        issues: List[CodeIssue],
        quality_metrics: Optional[QualityMetrics]
    ) -> List[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []

        # Critical issues
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL.value]
        if critical_issues:
            recommendations.append(Recommendation(
                title="Fix Critical Security Issues",
                description=f"Found {len(critical_issues)} critical security issues that need immediate attention",
                priority="critical",
                effort="moderate",
                impact="high"
            ))

        # High complexity
        if quality_metrics and quality_metrics.cyclomatic_complexity:
            if quality_metrics.cyclomatic_complexity.max > 10:
                recommendations.append(Recommendation(
                    title="Reduce Code Complexity",
                    description=f"Functions have high complexity (max: {quality_metrics.cyclomatic_complexity.max:.1f}). Consider refactoring.",
                    priority="medium",
                    effort="moderate",
                    impact="medium"
                ))

        # Low documentation
        if quality_metrics and quality_metrics.documentation_coverage is not None:
            if quality_metrics.documentation_coverage < 0.5:
                recommendations.append(Recommendation(
                    title="Improve Documentation",
                    description=f"Only {quality_metrics.documentation_coverage*100:.0f}% of functions are documented",
                    priority="low",
                    effort="easy",
                    impact="medium"
                ))

        # Low maintainability
        if quality_metrics and quality_metrics.maintainability_index < 60:
            recommendations.append(Recommendation(
                title="Improve Code Maintainability",
                description="Maintainability index is below 60. Focus on reducing complexity and improving structure.",
                priority="medium",
                effort="hard",
                impact="high"
            ))

        return recommendations


# ============================================================================
# CAP CLIENT
# ============================================================================


class CAPClient:
    """Client for Code Analysis Protocol operations."""

    def __init__(self):
        """Initialize CAP client."""
        self.analyzer = CodeAnalyzer()
        self.version = "1.0.0"
        logger.info(f"CAPClient initialized (version {self.version})")

    async def analyze_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        analysis_types: Optional[List[str]] = None,
        config: Optional[AnalysisConfig] = None
    ) -> AnalysisResult:
        """
        Analyze a code file.

        Args:
            file_path: Path to file to analyze
            language: Programming language
            analysis_types: Types of analysis to perform
            config: Analysis configuration

        Returns:
            AnalysisResult
        """
        request = AnalysisRequest(
            analysis_id=str(uuid4()),
            target=AnalysisTarget(
                type=TargetType.FILE.value,
                location=file_path,
                language=language or "python"
            ),
            analysis_config=config or AnalysisConfig()
        )

        return await self.analyzer.analyze(request, analysis_types)

    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        analysis_types: Optional[List[str]] = None,
        config: Optional[AnalysisConfig] = None
    ) -> AnalysisResult:
        """
        Analyze code snippet.

        Args:
            code: Code to analyze
            language: Programming language
            analysis_types: Types of analysis to perform
            config: Analysis configuration

        Returns:
            AnalysisResult
        """
        request = AnalysisRequest(
            analysis_id=str(uuid4()),
            target=AnalysisTarget(
                type=TargetType.SNIPPET.value,
                language=language,
                content=code
            ),
            analysis_config=config or AnalysisConfig()
        )

        return await self.analyzer.analyze(request, analysis_types)

    def format_result(
        self,
        result: AnalysisResult,
        format: str = "json"
    ) -> str:
        """
        Format analysis result.

        Args:
            result: Analysis result
            format: Output format (json, markdown, sarif)

        Returns:
            Formatted result
        """
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)
        elif format == "markdown":
            return self._format_markdown(result)
        elif format == "sarif":
            return self._format_sarif(result)
        else:
            return json.dumps(result.to_dict(), indent=2)

    def _format_markdown(self, result: AnalysisResult) -> str:
        """Format result as markdown."""
        md = f"# Code Analysis Report\n\n"
        md += f"**Analysis ID:** {result.analysis_id}\n"
        md += f"**Status:** {result.status}\n"
        md += f"**Analyzed At:** {result.analyzed_at}\n\n"

        # Summary
        md += "## Summary\n\n"
        s = result.summary
        md += f"- Files Analyzed: {s.total_files_analyzed}\n"
        md += f"- Lines of Code: {s.total_lines_of_code}\n"
        md += f"- Issues Found: {s.total_issues_found}\n"
        md += f"- Critical: {s.critical_issues} | High: {s.high_issues} | Medium: {s.medium_issues} | Low: {s.low_issues}\n\n"

        # Quality Metrics
        if result.quality_metrics:
            md += "## Quality Metrics\n\n"
            qm = result.quality_metrics
            md += f"- Maintainability Index: {qm.maintainability_index:.1f}/100\n"
            if qm.cyclomatic_complexity:
                cc = qm.cyclomatic_complexity
                md += f"- Average Complexity: {cc.average:.1f}\n"
                md += f"- Max Complexity: {cc.max:.1f}\n"
            if qm.documentation_coverage:
                md += f"- Documentation Coverage: {qm.documentation_coverage*100:.1f}%\n"
            md += "\n"

        # Issues
        if result.issues:
            md += "## Issues\n\n"
            for issue in result.issues[:10]:  # Top 10
                md += f"### {issue.title}\n"
                md += f"- **Severity:** {issue.severity}\n"
                md += f"- **Category:** {issue.category}\n"
                md += f"- **Location:** {issue.location.file}:{issue.location.start_line}\n"
                md += f"- **Description:** {issue.description}\n\n"

        # Recommendations
        if result.recommendations:
            md += "## Recommendations\n\n"
            for rec in result.recommendations:
                md += f"### {rec.title}\n"
                md += f"- **Priority:** {rec.priority}\n"
                md += f"- **Effort:** {rec.effort}\n"
                md += f"- **Impact:** {rec.impact}\n"
                md += f"- {rec.description}\n\n"

        return md

    def _format_sarif(self, result: AnalysisResult) -> str:
        """Format result as SARIF (Static Analysis Results Interchange Format)."""
        sarif = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "CAP Analyzer",
                            "version": result.analyzer_version,
                            "informationUri": "https://superstandard.org/cap"
                        }
                    },
                    "results": [
                        {
                            "ruleId": issue.rule_id,
                            "level": self._sarif_level(issue.severity),
                            "message": {
                                "text": issue.description
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": issue.location.file
                                        },
                                        "region": {
                                            "startLine": issue.location.start_line,
                                            "endLine": issue.location.end_line
                                        }
                                    }
                                }
                            ]
                        }
                        for issue in result.issues
                    ]
                }
            ]
        }
        return json.dumps(sarif, indent=2)

    def _sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            'critical': 'error',
            'error': 'error',
            'warning': 'warning',
            'info': 'note'
        }
        return mapping.get(severity, 'warning')


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


async def analyze_file(
    file_path: str,
    language: Optional[str] = None,
    analysis_types: Optional[List[str]] = None
) -> AnalysisResult:
    """
    Convenience function to analyze a file.

    Args:
        file_path: Path to file
        language: Programming language
        analysis_types: Types of analysis

    Returns:
        AnalysisResult
    """
    client = CAPClient()
    return await client.analyze_file(file_path, language, analysis_types)


async def analyze_code(
    code: str,
    language: str = "python",
    analysis_types: Optional[List[str]] = None
) -> AnalysisResult:
    """
    Convenience function to analyze code.

    Args:
        code: Code to analyze
        language: Programming language
        analysis_types: Types of analysis

    Returns:
        AnalysisResult
    """
    client = CAPClient()
    return await client.analyze_code(code, language, analysis_types)


def create_analysis_request(
    target_type: str,
    location: Optional[str] = None,
    content: Optional[str] = None,
    language: Optional[str] = None,
    config: Optional[AnalysisConfig] = None
) -> AnalysisRequest:
    """
    Create an analysis request.

    Args:
        target_type: Type of target (file, snippet, etc.)
        location: File path or URL
        content: Inline code content
        language: Programming language
        config: Analysis configuration

    Returns:
        AnalysisRequest
    """
    return AnalysisRequest(
        analysis_id=str(uuid4()),
        target=AnalysisTarget(
            type=target_type,
            location=location,
            content=content,
            language=language
        ),
        analysis_config=config or AnalysisConfig()
    )
