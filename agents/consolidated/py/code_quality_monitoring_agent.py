"""
Code Quality Monitoring Agent
APQC Process Classification Framework: 11.1.4 - Manage Quality Assurance

Specialized agent for continuous monitoring of code quality metrics,
automated violation detection, and quality trend analysis.
"""

import asyncio
import logging
import ast
import json
import os
import subprocess
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class QualityMetricType(Enum):
    """Types of quality metrics following APQC quality management standards"""

    COMPLEXITY = "complexity"  # 11.1.4.1 - Manage code complexity
    COVERAGE = "coverage"  # 11.1.4.2 - Monitor test coverage
    MAINTAINABILITY = "maintainability"  # 11.1.4.3 - Assess maintainability
    RELIABILITY = "reliability"  # 11.1.4.4 - Monitor reliability
    SECURITY = "security"  # 11.1.4.5 - Assess security quality
    PERFORMANCE = "performance"  # 11.1.4.6 - Monitor performance
    DOCUMENTATION = "documentation"  # 11.1.4.7 - Track documentation quality
    DUPLICATION = "duplication"  # 11.1.4.8 - Monitor code duplication
    STYLE = "style"  # 11.1.4.9 - Enforce coding standards
    DEPENDENCY = "dependency"  # 11.1.4.10 - Monitor dependencies


class QualityViolationSeverity(Enum):
    """Severity levels for quality violations"""

    BLOCKER = "blocker"  # Prevents deployment
    CRITICAL = "critical"  # Major quality issue
    MAJOR = "major"  # Significant quality issue
    MINOR = "minor"  # Minor quality issue
    INFO = "info"  # Informational


class QualityTrend(Enum):
    """Quality trend indicators"""

    IMPROVING = "improving"  # Quality metrics improving
    STABLE = "stable"  # Quality metrics stable
    DEGRADING = "degrading"  # Quality metrics degrading
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class QualityMetric:
    """Individual quality metric measurement"""

    metric_type: QualityMetricType
    name: str
    value: float
    threshold: Optional[float]
    unit: str
    file_path: Optional[str] = None
    component: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityViolation:
    """Quality violation detected by monitoring"""

    id: str
    violation_type: str
    severity: QualityViolationSeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    column_number: Optional[int]
    rule_id: str
    rule_description: str
    suggested_fix: Optional[str]
    auto_fixable: bool
    technical_debt_minutes: int
    detected_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Comprehensive quality report"""

    report_id: str
    generated_at: datetime
    project_root: str
    overall_score: float
    grade: str  # A, B, C, D, F
    metrics: List[QualityMetric]
    violations: List[QualityViolation]
    trends: Dict[str, QualityTrend]
    recommendations: List[str]
    improvement_plan: Dict[str, Any]
    comparison_data: Optional[Dict[str, Any]] = None


@dataclass
class QualityGate:
    """Quality gate definition for deployment pipeline"""

    name: str
    description: str
    conditions: List[Dict[str, Any]]  # metric conditions that must be met
    blocking: bool  # Whether failure blocks deployment
    severity_threshold: QualityViolationSeverity


class CodeQualityMonitoringAgent:
    """
    Enterprise-grade code quality monitoring agent

    Implements APQC Process 11.1.4 - Manage Quality Assurance
    Provides continuous monitoring, violation detection, and quality insights
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.quality_history: deque = deque(maxlen=100)  # Store last 100 reports
        self.quality_gates = self._initialize_quality_gates()
        self.metric_thresholds = self._initialize_metric_thresholds()
        self.monitoring_config = self._initialize_monitoring_config()
        self.baseline_metrics: Optional[Dict[str, float]] = None

    def _initialize_quality_gates(self) -> List[QualityGate]:
        """Initialize quality gates for CI/CD pipeline"""
        return [
            QualityGate(
                name="Security Gate",
                description="Blocks deployment if security vulnerabilities found",
                conditions=[
                    {"metric": "security_violations", "operator": "==", "value": 0},
                    {"metric": "security_hotspots", "operator": "<=", "value": 2},
                ],
                blocking=True,
                severity_threshold=QualityViolationSeverity.CRITICAL,
            ),
            QualityGate(
                name="Reliability Gate",
                description="Ensures minimum reliability standards",
                conditions=[
                    {"metric": "reliability_rating", "operator": "<=", "value": 2},
                    {"metric": "bugs", "operator": "<=", "value": 10},
                ],
                blocking=True,
                severity_threshold=QualityViolationSeverity.MAJOR,
            ),
            QualityGate(
                name="Maintainability Gate",
                description="Ensures code maintainability standards",
                conditions=[
                    {"metric": "maintainability_rating", "operator": "<=", "value": 2},
                    {"metric": "code_smells", "operator": "<=", "value": 50},
                    {"metric": "technical_debt_ratio", "operator": "<=", "value": 5.0},
                ],
                blocking=False,
                severity_threshold=QualityViolationSeverity.MAJOR,
            ),
            QualityGate(
                name="Coverage Gate",
                description="Ensures minimum test coverage",
                conditions=[
                    {"metric": "line_coverage", "operator": ">=", "value": 80.0},
                    {"metric": "branch_coverage", "operator": ">=", "value": 70.0},
                ],
                blocking=False,
                severity_threshold=QualityViolationSeverity.MINOR,
            ),
        ]

    def _initialize_metric_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize thresholds for various quality metrics"""
        return {
            "complexity": {
                "cyclomatic_complexity_per_function": 10.0,
                "cognitive_complexity_per_function": 15.0,
                "cyclomatic_complexity_per_file": 50.0,
            },
            "maintainability": {
                "maintainability_index_min": 60.0,
                "lines_of_code_per_function": 50.0,
                "functions_per_file": 20.0,
            },
            "duplication": {"duplication_percentage": 3.0, "duplicated_lines": 100},
            "documentation": {"comment_density": 20.0, "public_documented_api": 90.0},
            "security": {"security_hotspots": 0, "vulnerabilities": 0},
            "reliability": {"bugs_per_kloc": 1.0, "reliability_rating": 2.0},
        }

    def _initialize_monitoring_config(self) -> Dict[str, Any]:
        """Initialize monitoring configuration"""
        return {
            "scan_frequency": "on_commit",  # on_commit, hourly, daily
            "exclude_patterns": [
                "*/test/*",
                "*/tests/*",
                "*_test.py",
                "*test_*.py",
                "*/migrations/*",
                "*/venv/*",
                "*/.venv/*",
                "*/node_modules/*",
                "*/.git/*",
            ],
            "include_file_extensions": [".py", ".js", ".ts", ".tsx"],
            "enable_auto_fix": False,
            "quality_gate_enforcement": True,
            "trend_analysis_window_days": 30,
            "baseline_update_frequency": "weekly",
        }

    async def run_quality_analysis(self, baseline_comparison: bool = True) -> QualityReport:
        """
        Run comprehensive quality analysis

        Args:
            baseline_comparison: Whether to compare against baseline metrics

        Returns:
            Comprehensive quality report
        """
        logger.info("🔍 Starting comprehensive code quality analysis...")

        report_id = f"quality_report_{int(time.time())}"
        start_time = datetime.now()

        # Step 1: Collect all quality metrics
        metrics = await self._collect_quality_metrics()

        # Step 2: Detect quality violations
        violations = await self._detect_quality_violations()

        # Step 3: Calculate overall quality score
        overall_score, grade = await self._calculate_overall_score(metrics, violations)

        # Step 4: Analyze trends
        trends = await self._analyze_quality_trends(metrics)

        # Step 5: Generate recommendations
        recommendations = await self._generate_recommendations(metrics, violations, trends)

        # Step 6: Create improvement plan
        improvement_plan = await self._create_improvement_plan(violations, metrics)

        # Step 7: Baseline comparison
        comparison_data = None
        if baseline_comparison and self.baseline_metrics:
            comparison_data = await self._compare_with_baseline(metrics)

        # Create comprehensive report
        report = QualityReport(
            report_id=report_id,
            generated_at=start_time,
            project_root=str(self.project_root),
            overall_score=overall_score,
            grade=grade,
            metrics=metrics,
            violations=violations,
            trends=trends,
            recommendations=recommendations,
            improvement_plan=improvement_plan,
            comparison_data=comparison_data,
        )

        # Store in history
        self.quality_history.append(report)

        # Update baseline if needed
        await self._update_baseline_if_needed(metrics)

        analysis_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"✅ Quality analysis completed in {analysis_time:.2f}s - Grade: {grade} ({overall_score:.1f}/100)"
        )

        return report

    async def _collect_quality_metrics(self) -> List[QualityMetric]:
        """Collect all quality metrics from the codebase"""
        metrics = []

        # Collect complexity metrics
        complexity_metrics = await self._collect_complexity_metrics()
        metrics.extend(complexity_metrics)

        # Collect maintainability metrics
        maintainability_metrics = await self._collect_maintainability_metrics()
        metrics.extend(maintainability_metrics)

        # Collect duplication metrics
        duplication_metrics = await self._collect_duplication_metrics()
        metrics.extend(duplication_metrics)

        # Collect documentation metrics
        documentation_metrics = await self._collect_documentation_metrics()
        metrics.extend(documentation_metrics)

        # Collect security metrics
        security_metrics = await self._collect_security_metrics()
        metrics.extend(security_metrics)

        # Collect dependency metrics
        dependency_metrics = await self._collect_dependency_metrics()
        metrics.extend(dependency_metrics)

        # Collect style metrics
        style_metrics = await self._collect_style_metrics()
        metrics.extend(style_metrics)

        return metrics

    async def _collect_complexity_metrics(self) -> List[QualityMetric]:
        """Collect code complexity metrics"""
        metrics = []
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        total_cyclomatic_complexity = 0
        total_cognitive_complexity = 0
        total_functions = 0
        file_complexities = []

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    tree = ast.parse(content)

                file_complexity = self._calculate_file_complexity(tree)
                file_complexities.append(file_complexity)

                # Collect function-level complexity
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_complexity = self._calculate_cyclomatic_complexity(node)
                        total_cyclomatic_complexity += func_complexity
                        total_functions += 1

                        # Check against thresholds
                        threshold = self.metric_thresholds["complexity"][
                            "cyclomatic_complexity_per_function"
                        ]
                        metrics.append(
                            QualityMetric(
                                metric_type=QualityMetricType.COMPLEXITY,
                                name="cyclomatic_complexity_function",
                                value=func_complexity,
                                threshold=threshold,
                                unit="complexity_units",
                                file_path=str(file_path.relative_to(self.project_root)),
                                component=f"{file_path.stem}.{node.name}",
                                context={"function_name": node.name, "line_number": node.lineno},
                            )
                        )

            except Exception as e:
                logger.error(f"Error analyzing complexity for {file_path}: {e}")

        # Calculate aggregated metrics
        if total_functions > 0:
            avg_cyclomatic_complexity = total_cyclomatic_complexity / total_functions
            metrics.append(
                QualityMetric(
                    metric_type=QualityMetricType.COMPLEXITY,
                    name="average_cyclomatic_complexity",
                    value=avg_cyclomatic_complexity,
                    threshold=self.metric_thresholds["complexity"][
                        "cyclomatic_complexity_per_function"
                    ],
                    unit="complexity_units",
                    context={"total_functions": total_functions},
                )
            )

        if file_complexities:
            avg_file_complexity = statistics.mean(file_complexities)
            metrics.append(
                QualityMetric(
                    metric_type=QualityMetricType.COMPLEXITY,
                    name="average_file_complexity",
                    value=avg_file_complexity,
                    threshold=self.metric_thresholds["complexity"][
                        "cyclomatic_complexity_per_file"
                    ],
                    unit="complexity_units",
                    context={"total_files": len(file_complexities)},
                )
            )

        return metrics

    async def _collect_maintainability_metrics(self) -> List[QualityMetric]:
        """Collect maintainability metrics"""
        metrics = []
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        total_loc = 0
        total_functions = 0
        maintainability_indices = []

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = [line for line in content.split("\n") if line.strip()]
                    total_loc += len(lines)

                tree = ast.parse(content)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                total_functions += len(functions)

                # Calculate maintainability index for file
                maintainability_index = self._calculate_maintainability_index(content, tree)
                maintainability_indices.append(maintainability_index)

                metrics.append(
                    QualityMetric(
                        metric_type=QualityMetricType.MAINTAINABILITY,
                        name="maintainability_index",
                        value=maintainability_index,
                        threshold=self.metric_thresholds["maintainability"][
                            "maintainability_index_min"
                        ],
                        unit="index_points",
                        file_path=str(file_path.relative_to(self.project_root)),
                        context={"lines_of_code": len(lines), "function_count": len(functions)},
                    )
                )

            except Exception as e:
                logger.error(f"Error analyzing maintainability for {file_path}: {e}")

        # Aggregated metrics
        if maintainability_indices:
            avg_maintainability = statistics.mean(maintainability_indices)
            metrics.append(
                QualityMetric(
                    metric_type=QualityMetricType.MAINTAINABILITY,
                    name="average_maintainability_index",
                    value=avg_maintainability,
                    threshold=self.metric_thresholds["maintainability"][
                        "maintainability_index_min"
                    ],
                    unit="index_points",
                    context={"total_files": len(maintainability_indices)},
                )
            )

        metrics.append(
            QualityMetric(
                metric_type=QualityMetricType.MAINTAINABILITY,
                name="total_lines_of_code",
                value=total_loc,
                threshold=None,
                unit="lines",
                context={"total_functions": total_functions},
            )
        )

        return metrics

    async def _collect_duplication_metrics(self) -> List[QualityMetric]:
        """Collect code duplication metrics"""
        metrics = []

        # Simple duplication detection based on similar line patterns
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        all_lines = []
        line_counts = defaultdict(int)

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                for line in lines:
                    # Normalize line for duplication detection
                    normalized_line = re.sub(r"\s+", " ", line.lower())
                    if len(normalized_line) > 10:  # Only consider substantial lines
                        line_counts[normalized_line] += 1
                        all_lines.append(line)

            except Exception as e:
                logger.error(f"Error analyzing duplication for {file_path}: {e}")

        # Calculate duplication metrics
        duplicated_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        total_lines = len(all_lines)
        duplication_percentage = (duplicated_lines / total_lines * 100) if total_lines > 0 else 0

        metrics.append(
            QualityMetric(
                metric_type=QualityMetricType.DUPLICATION,
                name="duplication_percentage",
                value=duplication_percentage,
                threshold=self.metric_thresholds["duplication"]["duplication_percentage"],
                unit="percentage",
                context={"duplicated_lines": duplicated_lines, "total_lines": total_lines},
            )
        )

        metrics.append(
            QualityMetric(
                metric_type=QualityMetricType.DUPLICATION,
                name="duplicated_lines",
                value=duplicated_lines,
                threshold=self.metric_thresholds["duplication"]["duplicated_lines"],
                unit="lines",
                context={"total_files": len(python_files)},
            )
        )

        return metrics

    async def _collect_documentation_metrics(self) -> List[QualityMetric]:
        """Collect documentation quality metrics"""
        metrics = []
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        total_comments = 0
        total_code_lines = 0

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Count comments
                comment_lines = [line for line in lines if line.strip().startswith("#")]
                total_comments += len(comment_lines)

                # Count non-empty code lines
                code_lines = [
                    line for line in lines if line.strip() and not line.strip().startswith("#")
                ]
                total_code_lines += len(code_lines)

                tree = ast.parse(content)

                # Analyze functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1

                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                        if ast.get_docstring(node):
                            documented_classes += 1

            except Exception as e:
                logger.error(f"Error analyzing documentation for {file_path}: {e}")

        # Calculate documentation metrics
        function_doc_percentage = (
            (documented_functions / total_functions * 100) if total_functions > 0 else 0
        )
        class_doc_percentage = (
            (documented_classes / total_classes * 100) if total_classes > 0 else 0
        )
        comment_density = (total_comments / total_code_lines * 100) if total_code_lines > 0 else 0

        metrics.extend(
            [
                QualityMetric(
                    metric_type=QualityMetricType.DOCUMENTATION,
                    name="function_documentation_percentage",
                    value=function_doc_percentage,
                    threshold=self.metric_thresholds["documentation"]["public_documented_api"],
                    unit="percentage",
                    context={
                        "documented_functions": documented_functions,
                        "total_functions": total_functions,
                    },
                ),
                QualityMetric(
                    metric_type=QualityMetricType.DOCUMENTATION,
                    name="class_documentation_percentage",
                    value=class_doc_percentage,
                    threshold=self.metric_thresholds["documentation"]["public_documented_api"],
                    unit="percentage",
                    context={
                        "documented_classes": documented_classes,
                        "total_classes": total_classes,
                    },
                ),
                QualityMetric(
                    metric_type=QualityMetricType.DOCUMENTATION,
                    name="comment_density",
                    value=comment_density,
                    threshold=self.metric_thresholds["documentation"]["comment_density"],
                    unit="percentage",
                    context={
                        "total_comments": total_comments,
                        "total_code_lines": total_code_lines,
                    },
                ),
            ]
        )

        return metrics

    async def _collect_security_metrics(self) -> List[QualityMetric]:
        """Collect security-related quality metrics"""
        metrics = []

        # Security patterns to detect
        security_patterns = {
            "hardcoded_secrets": r"(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
            "sql_injection": r"execute\s*\(\s*['\"].*%.*['\"]|\+.*['\"].*SELECT",
            "command_injection": r"os\.system\s*\(|subprocess\.(call|run|Popen)\s*\(",
            "unsafe_eval": r"eval\s*\(|exec\s*\(",
            "unsafe_pickle": r"pickle\.loads\s*\(|cPickle\.loads\s*\(",
            "weak_crypto": r"md5\(|sha1\(|DES\(|RC4\(",
            "hardcoded_urls": r"https?://[^'\"]*(?:localhost|127\.0\.0\.1)",
            "debug_code": r"print\s*\(.*password|print\s*\(.*secret",
        }

        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        security_issues = defaultdict(int)
        total_files_scanned = 0

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                total_files_scanned += 1

                for issue_type, pattern in security_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    security_issues[issue_type] += len(matches)

            except Exception as e:
                logger.error(f"Error analyzing security for {file_path}: {e}")

        # Create metrics for each security issue type
        total_security_issues = sum(security_issues.values())

        for issue_type, count in security_issues.items():
            metrics.append(
                QualityMetric(
                    metric_type=QualityMetricType.SECURITY,
                    name=f"security_{issue_type}",
                    value=count,
                    threshold=self.metric_thresholds["security"]["security_hotspots"],
                    unit="count",
                    context={"issue_type": issue_type},
                )
            )

        # Overall security score
        security_score = max(0, 100 - (total_security_issues * 10))
        metrics.append(
            QualityMetric(
                metric_type=QualityMetricType.SECURITY,
                name="security_score",
                value=security_score,
                threshold=80.0,
                unit="score",
                context={
                    "total_issues": total_security_issues,
                    "files_scanned": total_files_scanned,
                },
            )
        )

        return metrics

    async def _collect_dependency_metrics(self) -> List[QualityMetric]:
        """Collect dependency-related metrics"""
        metrics = []

        # Analyze import statements
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        all_imports = set()
        external_imports = set()
        internal_imports = set()
        import_counts = defaultdict(int)

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Extract imports
                import_matches = re.findall(
                    r"^(?:from\s+([a-zA-Z_][a-zA-Z0-9_.]*)|import\s+([a-zA-Z_][a-zA-Z0-9_.]*)).*$",
                    content,
                    re.MULTILINE,
                )

                for match in import_matches:
                    import_name = match[0] or match[1]
                    if import_name:
                        all_imports.add(import_name)
                        import_counts[import_name] += 1

                        if import_name.startswith("app.") or not "." in import_name.split(".")[0]:
                            internal_imports.add(import_name)
                        else:
                            external_imports.add(import_name)

            except Exception as e:
                logger.error(f"Error analyzing dependencies for {file_path}: {e}")

        # Calculate dependency metrics
        total_dependencies = len(all_imports)
        external_dependency_ratio = (
            len(external_imports) / total_dependencies if total_dependencies > 0 else 0
        )

        # Find most used dependencies
        most_used = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        metrics.extend(
            [
                QualityMetric(
                    metric_type=QualityMetricType.DEPENDENCY,
                    name="total_dependencies",
                    value=total_dependencies,
                    threshold=None,
                    unit="count",
                    context={"external": len(external_imports), "internal": len(internal_imports)},
                ),
                QualityMetric(
                    metric_type=QualityMetricType.DEPENDENCY,
                    name="external_dependency_ratio",
                    value=external_dependency_ratio * 100,
                    threshold=70.0,  # Warning if >70% external
                    unit="percentage",
                    context={"most_used": most_used[:5]},
                ),
            ]
        )

        return metrics

    async def _collect_style_metrics(self) -> List[QualityMetric]:
        """Collect code style metrics"""
        metrics = []

        # Style violations to check
        style_patterns = {
            "long_lines": r".{120,}",  # Lines longer than 120 characters
            "trailing_whitespace": r"\s+$",
            "mixed_indentation": r"^(\t+ +| +\t+)",
            "missing_docstrings": r"^(def|class)\s+\w+.*:\s*$",
            "unused_imports": r"^import\s+\w+$|^from\s+\w+\s+import\s+\w+$",
        }

        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        style_violations = defaultdict(int)
        total_lines = 0

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                total_lines += len(lines)

                for i, line in enumerate(lines):
                    for violation_type, pattern in style_patterns.items():
                        if re.search(pattern, line):
                            style_violations[violation_type] += 1

            except Exception as e:
                logger.error(f"Error analyzing style for {file_path}: {e}")

        # Calculate style metrics
        total_violations = sum(style_violations.values())
        style_score = (
            max(0, 100 - (total_violations / total_lines * 100)) if total_lines > 0 else 100
        )

        for violation_type, count in style_violations.items():
            metrics.append(
                QualityMetric(
                    metric_type=QualityMetricType.STYLE,
                    name=f"style_{violation_type}",
                    value=count,
                    threshold=total_lines * 0.05,  # 5% threshold
                    unit="count",
                    context={"violation_type": violation_type},
                )
            )

        metrics.append(
            QualityMetric(
                metric_type=QualityMetricType.STYLE,
                name="style_score",
                value=style_score,
                threshold=80.0,
                unit="score",
                context={"total_violations": total_violations, "total_lines": total_lines},
            )
        )

        return metrics

    def _calculate_file_complexity(self, tree: ast.AST) -> int:
        """Calculate complexity for an entire file"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += self._calculate_cyclomatic_complexity(node)
        return complexity

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ExceptHandler, ast.comprehension)):
                complexity += 1

        return complexity

    def _calculate_maintainability_index(self, content: str, tree: ast.AST) -> float:
        """Calculate maintainability index for code"""
        # Simplified maintainability index calculation
        lines_of_code = len([line for line in content.split("\n") if line.strip()])
        cyclomatic_complexity = sum(
            self._calculate_cyclomatic_complexity(node)
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

        # Halstead volume approximation
        halstead_volume = lines_of_code * 8.2  # Simplified

        # Maintainability Index formula (simplified)
        if lines_of_code > 0:
            maintainability_index = max(
                0,
                (
                    171
                    - 5.2 * (halstead_volume / 1000)
                    - 0.23 * cyclomatic_complexity
                    - 16.2 * (lines_of_code / 1000)
                )
                * 100
                / 171,
            )
        else:
            maintainability_index = 100

        return maintainability_index

    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from analysis"""
        for pattern in self.monitoring_config["exclude_patterns"]:
            if pattern in file_path:
                return True
        return False

    async def _detect_quality_violations(self) -> List[QualityViolation]:
        """Detect quality violations across the codebase"""
        violations = []

        # Detect violations from collected metrics
        # This would typically integrate with linting tools like pylint, flake8, bandit, etc.

        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        for file_path in python_files:
            file_violations = await self._analyze_file_violations(file_path)
            violations.extend(file_violations)

        return violations

    async def _analyze_file_violations(self, file_path: Path) -> List[QualityViolation]:
        """Analyze a single file for quality violations"""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            tree = ast.parse(content)

            # Check for various violations
            for i, line in enumerate(lines, 1):
                # Long line violation
                if len(line) > 120:
                    violations.append(
                        QualityViolation(
                            id=f"long_line_{file_path}_{i}",
                            violation_type="style",
                            severity=QualityViolationSeverity.MINOR,
                            title="Line too long",
                            description=f"Line {i} is {len(line)} characters long (max 120)",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=i,
                            column_number=120,
                            rule_id="E501",
                            rule_description="Line too long",
                            suggested_fix="Break line into multiple lines",
                            auto_fixable=False,
                            technical_debt_minutes=2,
                        )
                    )

                # Security violation - hardcoded password
                if re.search(r"password\s*=\s*['\"][^'\"]{3,}['\"]", line, re.IGNORECASE):
                    violations.append(
                        QualityViolation(
                            id=f"hardcoded_password_{file_path}_{i}",
                            violation_type="security",
                            severity=QualityViolationSeverity.CRITICAL,
                            title="Hardcoded password detected",
                            description="Password appears to be hardcoded in source code",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=i,
                            column_number=None,
                            rule_id="S106",
                            rule_description="Hardcoded credentials should not be used",
                            suggested_fix="Use environment variables or secure configuration",
                            auto_fixable=False,
                            technical_debt_minutes=30,
                        )
                    )

            # Check function complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        violations.append(
                            QualityViolation(
                                id=f"complex_function_{file_path}_{node.lineno}",
                                violation_type="complexity",
                                severity=QualityViolationSeverity.MAJOR,
                                title="Function too complex",
                                description=f"Function '{node.name}' has cyclomatic complexity of {complexity}",
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                rule_id="C901",
                                rule_description="Function is too complex",
                                suggested_fix="Break function into smaller functions",
                                auto_fixable=False,
                                technical_debt_minutes=60,
                            )
                        )

        except Exception as e:
            logger.error(f"Error analyzing violations for {file_path}: {e}")

        return violations

    async def _calculate_overall_score(
        self, metrics: List[QualityMetric], violations: List[QualityViolation]
    ) -> Tuple[float, str]:
        """Calculate overall quality score and grade"""
        # Calculate base score from metrics
        metric_scores = []

        for metric in metrics:
            if metric.threshold is not None:
                if metric.name in ["security_score", "style_score", "maintainability_index"]:
                    # Higher is better
                    score = min(100, (metric.value / metric.threshold) * 100)
                else:
                    # Lower is better (violations, complexity)
                    score = max(0, 100 - ((metric.value / metric.threshold) * 100))
                metric_scores.append(score)

        base_score = statistics.mean(metric_scores) if metric_scores else 50

        # Apply violation penalties
        violation_penalty = 0
        for violation in violations:
            if violation.severity == QualityViolationSeverity.BLOCKER:
                violation_penalty += 20
            elif violation.severity == QualityViolationSeverity.CRITICAL:
                violation_penalty += 10
            elif violation.severity == QualityViolationSeverity.MAJOR:
                violation_penalty += 5
            elif violation.severity == QualityViolationSeverity.MINOR:
                violation_penalty += 1

        overall_score = max(0, base_score - violation_penalty)

        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return overall_score, grade

    async def _analyze_quality_trends(
        self, current_metrics: List[QualityMetric]
    ) -> Dict[str, QualityTrend]:
        """Analyze quality trends over time"""
        trends = {}

        if len(self.quality_history) < 2:
            return {metric.name: QualityTrend.UNKNOWN for metric in current_metrics}

        # Get previous report for comparison
        previous_report = self.quality_history[-1] if self.quality_history else None

        if previous_report:
            previous_metrics = {m.name: m.value for m in previous_report.metrics}

            for metric in current_metrics:
                if metric.name in previous_metrics:
                    current_value = metric.value
                    previous_value = previous_metrics[metric.name]

                    # Determine if higher or lower is better
                    if metric.name in [
                        "security_score",
                        "style_score",
                        "maintainability_index",
                        "function_documentation_percentage",
                        "class_documentation_percentage",
                    ]:
                        # Higher is better
                        if current_value > previous_value * 1.05:  # 5% improvement threshold
                            trends[metric.name] = QualityTrend.IMPROVING
                        elif current_value < previous_value * 0.95:  # 5% degradation threshold
                            trends[metric.name] = QualityTrend.DEGRADING
                        else:
                            trends[metric.name] = QualityTrend.STABLE
                    else:
                        # Lower is better (violations, complexity)
                        if current_value < previous_value * 0.95:  # 5% improvement (reduction)
                            trends[metric.name] = QualityTrend.IMPROVING
                        elif current_value > previous_value * 1.05:  # 5% degradation (increase)
                            trends[metric.name] = QualityTrend.DEGRADING
                        else:
                            trends[metric.name] = QualityTrend.STABLE
                else:
                    trends[metric.name] = QualityTrend.UNKNOWN

        return trends

    async def _generate_recommendations(
        self,
        metrics: List[QualityMetric],
        violations: List[QualityViolation],
        trends: Dict[str, QualityTrend],
    ) -> List[str]:
        """Generate actionable quality improvement recommendations"""
        recommendations = []

        # Critical violations
        critical_violations = [
            v for v in violations if v.severity == QualityViolationSeverity.CRITICAL
        ]
        if critical_violations:
            recommendations.append(
                f"🚨 CRITICAL: Address {len(critical_violations)} critical violations immediately - they block deployment"
            )

        # Security issues
        security_violations = [v for v in violations if v.violation_type == "security"]
        if security_violations:
            recommendations.append(
                f"🔒 Security: Fix {len(security_violations)} security vulnerabilities to prevent breaches"
            )

        # Complexity issues
        complexity_violations = [v for v in violations if v.violation_type == "complexity"]
        if complexity_violations:
            recommendations.append(
                f"🧩 Complexity: Refactor {len(complexity_violations)} complex functions to improve maintainability"
            )

        # Documentation gaps
        doc_metrics = [m for m in metrics if m.metric_type == QualityMetricType.DOCUMENTATION]
        low_doc_metrics = [m for m in doc_metrics if m.threshold and m.value < m.threshold]
        if low_doc_metrics:
            recommendations.append(
                f"📚 Documentation: Improve documentation coverage - {len(low_doc_metrics)} metrics below threshold"
            )

        # Degrading trends
        degrading_trends = [
            name for name, trend in trends.items() if trend == QualityTrend.DEGRADING
        ]
        if degrading_trends:
            recommendations.append(
                f"📉 Trends: Monitor degrading quality in {len(degrading_trends)} areas: {', '.join(degrading_trends[:3])}"
            )

        # Technical debt
        total_debt_minutes = sum(v.technical_debt_minutes for v in violations)
        if total_debt_minutes > 480:  # 8 hours
            recommendations.append(
                f"⏰ Technical Debt: {total_debt_minutes // 60:.1f} hours of technical debt - plan remediation sprint"
            )

        # Positive reinforcement
        improving_trends = [
            name for name, trend in trends.items() if trend == QualityTrend.IMPROVING
        ]
        if improving_trends:
            recommendations.append(
                f"✅ Good progress: Quality improving in {len(improving_trends)} areas - keep up the momentum"
            )

        return recommendations

    async def _create_improvement_plan(
        self, violations: List[QualityViolation], metrics: List[QualityMetric]
    ) -> Dict[str, Any]:
        """Create structured improvement plan"""
        plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_initiatives": [],
            "estimated_effort_hours": 0,
        }

        # Sort violations by severity and impact
        sorted_violations = sorted(
            violations,
            key=lambda v: (
                {"blocker": 5, "critical": 4, "major": 3, "minor": 2, "info": 1}[v.severity.value],
                v.technical_debt_minutes,
            ),
            reverse=True,
        )

        total_effort_minutes = 0

        for violation in sorted_violations[:20]:  # Top 20 violations
            effort_hours = violation.technical_debt_minutes / 60
            total_effort_minutes += violation.technical_debt_minutes

            action_item = {
                "violation_id": violation.id,
                "title": violation.title,
                "file": violation.file_path,
                "severity": violation.severity.value,
                "effort_hours": effort_hours,
                "suggested_fix": violation.suggested_fix,
            }

            if violation.severity in [
                QualityViolationSeverity.BLOCKER,
                QualityViolationSeverity.CRITICAL,
            ]:
                plan["immediate_actions"].append(action_item)
            elif violation.severity == QualityViolationSeverity.MAJOR:
                plan["short_term_goals"].append(action_item)
            else:
                plan["long_term_initiatives"].append(action_item)

        plan["estimated_effort_hours"] = total_effort_minutes / 60

        return plan

    async def _compare_with_baseline(self, current_metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Compare current metrics with baseline"""
        if not self.baseline_metrics:
            return {"message": "No baseline metrics available"}

        comparison = {
            "improved_metrics": [],
            "degraded_metrics": [],
            "stable_metrics": [],
            "new_metrics": [],
        }

        current_metric_dict = {m.name: m.value for m in current_metrics}

        for metric_name, current_value in current_metric_dict.items():
            if metric_name in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric_name]
                change_percentage = (
                    ((current_value - baseline_value) / baseline_value * 100)
                    if baseline_value != 0
                    else 0
                )

                metric_info = {
                    "name": metric_name,
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percentage": change_percentage,
                }

                # Determine if higher or lower is better
                if metric_name in ["security_score", "style_score", "maintainability_index"]:
                    # Higher is better
                    if change_percentage > 5:
                        comparison["improved_metrics"].append(metric_info)
                    elif change_percentage < -5:
                        comparison["degraded_metrics"].append(metric_info)
                    else:
                        comparison["stable_metrics"].append(metric_info)
                else:
                    # Lower is better
                    if change_percentage < -5:
                        comparison["improved_metrics"].append(metric_info)
                    elif change_percentage > 5:
                        comparison["degraded_metrics"].append(metric_info)
                    else:
                        comparison["stable_metrics"].append(metric_info)
            else:
                comparison["new_metrics"].append({"name": metric_name, "current": current_value})

        return comparison

    async def _update_baseline_if_needed(self, metrics: List[QualityMetric]):
        """Update baseline metrics if criteria met"""
        # Update baseline weekly or if significant improvement
        if not self.baseline_metrics or datetime.now().weekday() == 0:  # Monday

            self.baseline_metrics = {m.name: m.value for m in metrics}
            logger.info("📊 Baseline metrics updated")

    async def check_quality_gates(self, report: QualityReport) -> Dict[str, Any]:
        """Check if quality gates are passed"""
        gate_results = []

        for gate in self.quality_gates:
            gate_result = {
                "name": gate.name,
                "description": gate.description,
                "passed": True,
                "blocking": gate.blocking,
                "failed_conditions": [],
            }

            # Check each condition
            for condition in gate.conditions:
                metric_name = condition["metric"]
                operator = condition["operator"]
                expected_value = condition["value"]

                # Find the metric value
                metric_value = None
                for metric in report.metrics:
                    if metric.name == metric_name:
                        metric_value = metric.value
                        break

                if metric_value is not None:
                    condition_passed = False

                    if operator == "<=":
                        condition_passed = metric_value <= expected_value
                    elif operator == ">=":
                        condition_passed = metric_value >= expected_value
                    elif operator == "==":
                        condition_passed = metric_value == expected_value
                    elif operator == "<":
                        condition_passed = metric_value < expected_value
                    elif operator == ">":
                        condition_passed = metric_value > expected_value

                    if not condition_passed:
                        gate_result["passed"] = False
                        gate_result["failed_conditions"].append(
                            {
                                "metric": metric_name,
                                "expected": f"{operator} {expected_value}",
                                "actual": metric_value,
                            }
                        )

            gate_results.append(gate_result)

        # Overall gate status
        blocking_failures = [g for g in gate_results if not g["passed"] and g["blocking"]]
        all_passed = all(g["passed"] for g in gate_results)

        return {
            "overall_status": "PASSED" if all_passed else "FAILED",
            "blocking_failures": len(blocking_failures),
            "deployment_allowed": len(blocking_failures) == 0,
            "gate_results": gate_results,
        }

    async def export_quality_report(self, report: QualityReport, output_path: str) -> str:
        """Export quality report to file"""
        report_data = asdict(report)

        # Convert datetime objects for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (QualityMetricType, QualityViolationSeverity, QualityTrend)):
                return obj.value
            return str(obj)

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2, default=json_serializer)

        logger.info(f"📊 Quality report exported to {output_path}")
        return output_path


# Initialize the code quality monitoring agent
quality_monitor = CodeQualityMonitoringAgent(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
