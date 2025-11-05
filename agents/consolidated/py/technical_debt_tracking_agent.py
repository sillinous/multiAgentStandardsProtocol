"""
Technical Debt Tracking Agent
APQC Process Classification Framework: 11.1.1 - Manage Information Technology Risks

Specialized agent for identifying, cataloging, and tracking technical debt across the platform.
Follows APQC enterprise standards for IT risk management and technical excellence.
"""

import asyncio
import logging
import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class TechnicalDebtSeverity(Enum):
    """Technical debt severity levels aligned with APQC risk classification"""
    CRITICAL = "critical"  # Security vulnerabilities, production blockers
    HIGH = "high"         # Performance impacts, maintainability issues
    MEDIUM = "medium"     # Code quality, documentation gaps
    LOW = "low"          # Minor improvements, optimizations

class TechnicalDebtCategory(Enum):
    """Categories following APQC IT service management classification"""
    ARCHITECTURE = "architecture"      # 11.2.1 - Develop IT architecture
    SECURITY = "security"              # 11.2.4 - Manage IT security
    PERFORMANCE = "performance"        # 11.2.3 - Monitor IT performance
    CODE_QUALITY = "code_quality"      # 11.1.2 - Manage software development
    DOCUMENTATION = "documentation"    # 11.2.5 - Manage IT knowledge
    CONFIGURATION = "configuration"    # 11.2.2 - Implement IT infrastructure
    DEPENDENCIES = "dependencies"      # 11.1.3 - Manage software dependencies
    TESTING = "testing"                # 11.1.4 - Manage quality assurance
    COMPLIANCE = "compliance"          # 11.2.6 - Ensure regulatory compliance

@dataclass
class TechnicalDebtItem:
    """Individual technical debt item with comprehensive tracking"""
    id: str
    title: str
    description: str
    severity: TechnicalDebtSeverity
    category: TechnicalDebtCategory
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    impact_assessment: str
    remediation_effort: str  # hours/days/weeks
    business_impact: str
    security_implications: str
    performance_impact: str
    maintainability_impact: str
    suggested_solution: str
    dependencies: List[str]
    related_items: List[str]
    assigned_to: Optional[str]
    created_date: datetime
    target_resolution_date: Optional[datetime]
    last_updated: datetime
    status: str  # open, in_progress, resolved, deferred
    tags: List[str]
    technical_context: Dict[str, Any]
    apqc_process_reference: str

class TechnicalDebtTrackingAgent:
    """
    Enterprise-grade technical debt tracking agent

    Implements APQC Process 11.1.1 - Manage Information Technology Risks
    Provides systematic identification, assessment, and tracking of technical debt
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.debt_database: Dict[str, TechnicalDebtItem] = {}
        self.scan_patterns = self._initialize_scan_patterns()
        self.exclusion_patterns = self._initialize_exclusion_patterns()
        self.priority_matrix = self._initialize_priority_matrix()

    def _initialize_scan_patterns(self) -> Dict[str, Dict]:
        """Initialize patterns for detecting technical debt"""
        return {
            "todo_comments": {
                "pattern": r"(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)(?:\s*:)?\s*(.+)",
                "severity": TechnicalDebtSeverity.MEDIUM,
                "category": TechnicalDebtCategory.CODE_QUALITY,
                "apqc_process": "11.1.2"
            },
            "hardcoded_values": {
                "pattern": r"(?:allow_origins=\[.*localhost.*\]|origins.*localhost|http://localhost:\d+)",
                "severity": TechnicalDebtSeverity.HIGH,
                "category": TechnicalDebtCategory.CONFIGURATION,
                "apqc_process": "11.2.2"
            },
            "security_issues": {
                "pattern": r"(?:allow_credentials=True.*\*|DEBUG=True|SECRET.*=.*['\"].*['\"]|password.*=.*['\"])",
                "severity": TechnicalDebtSeverity.CRITICAL,
                "category": TechnicalDebtCategory.SECURITY,
                "apqc_process": "11.2.4"
            },
            "performance_issues": {
                "pattern": r"(?:SELECT \*|\.all\(\)|sleep\(|time\.sleep|asyncio\.sleep\(\d+\))",
                "severity": TechnicalDebtSeverity.HIGH,
                "category": TechnicalDebtCategory.PERFORMANCE,
                "apqc_process": "11.2.3"
            },
            "configuration_debt": {
                "pattern": r"(?:localhost|127\.0\.0\.1|demo-key|change-me|testing-secret)",
                "severity": TechnicalDebtSeverity.HIGH,
                "category": TechnicalDebtCategory.CONFIGURATION,
                "apqc_process": "11.2.2"
            },
            "documentation_gaps": {
                "pattern": r"(?:def\s+\w+\([^)]*\):\s*$|class\s+\w+.*:\s*$)",
                "severity": TechnicalDebtSeverity.MEDIUM,
                "category": TechnicalDebtCategory.DOCUMENTATION,
                "apqc_process": "11.2.5"
            },
            "deprecated_patterns": {
                "pattern": r"(?:\.format\(|%\s*%|\bstring\b.*interpolation)",
                "severity": TechnicalDebtSeverity.LOW,
                "category": TechnicalDebtCategory.CODE_QUALITY,
                "apqc_process": "11.1.2"
            },
            "architecture_violations": {
                "pattern": r"(?:from\s+.*\.models\s+import\s+\*|import\s+\*|circular.*import)",
                "severity": TechnicalDebtSeverity.HIGH,
                "category": TechnicalDebtCategory.ARCHITECTURE,
                "apqc_process": "11.2.1"
            },
            "testing_gaps": {
                "pattern": r"(?:def\s+test_.*:\s*pass|class\s+Test.*:\s*pass|# TODO.*test)",
                "severity": TechnicalDebtSeverity.MEDIUM,
                "category": TechnicalDebtCategory.TESTING,
                "apqc_process": "11.1.4"
            }
        }

    def _initialize_exclusion_patterns(self) -> List[str]:
        """Patterns for files/directories to exclude from scanning"""
        return [
            r".*\.venv/.*",
            r".*venv/.*",
            r".*__pycache__/.*",
            r".*\.git/.*",
            r".*node_modules/.*",
            r".*\.dist/.*",
            r".*\.build/.*",
            r".*\.pytest_cache/.*",
            r".*migrations/.*",
            r".*\.log$",
            r".*\.pyc$"
        ]

    def _initialize_priority_matrix(self) -> Dict[str, int]:
        """Priority scoring matrix for technical debt items"""
        return {
            "severity_weights": {
                TechnicalDebtSeverity.CRITICAL: 100,
                TechnicalDebtSeverity.HIGH: 75,
                TechnicalDebtSeverity.MEDIUM: 50,
                TechnicalDebtSeverity.LOW: 25
            },
            "category_multipliers": {
                TechnicalDebtCategory.SECURITY: 1.5,
                TechnicalDebtCategory.PERFORMANCE: 1.3,
                TechnicalDebtCategory.ARCHITECTURE: 1.2,
                TechnicalDebtCategory.CONFIGURATION: 1.1,
                TechnicalDebtCategory.CODE_QUALITY: 1.0,
                TechnicalDebtCategory.TESTING: 0.9,
                TechnicalDebtCategory.DOCUMENTATION: 0.8,
                TechnicalDebtCategory.DEPENDENCIES: 0.7,
                TechnicalDebtCategory.COMPLIANCE: 1.4
            }
        }

    async def scan_codebase(self) -> Dict[str, List[TechnicalDebtItem]]:
        """
        Comprehensive codebase scan for technical debt

        Returns:
            Dictionary of technical debt items organized by category
        """
        logger.info("🔍 Starting comprehensive technical debt scan...")

        scan_results = {category.value: [] for category in TechnicalDebtCategory}

        # Scan Python files
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        for file_path in python_files:
            file_debt_items = await self._scan_file(file_path)
            for item in file_debt_items:
                scan_results[item.category.value].append(item)

        # Scan configuration files
        config_files = list(self.project_root.rglob("*.json")) + \
                      list(self.project_root.rglob("*.yml")) + \
                      list(self.project_root.rglob("*.yaml")) + \
                      list(self.project_root.rglob("*.env*"))

        for file_path in config_files:
            if not self._should_exclude_file(str(file_path)):
                file_debt_items = await self._scan_config_file(file_path)
                for item in file_debt_items:
                    scan_results[item.category.value].append(item)

        # Update debt database
        for category_items in scan_results.values():
            for item in category_items:
                self.debt_database[item.id] = item

        # Generate summary
        total_items = sum(len(items) for items in scan_results.values())
        logger.info(f"✅ Technical debt scan completed: {total_items} items found")

        return scan_results

    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from scanning"""
        for pattern in self.exclusion_patterns:
            if re.search(pattern, file_path):
                return True
        return False

    async def _scan_file(self, file_path: Path) -> List[TechnicalDebtItem]:
        """Scan individual Python file for technical debt"""
        debt_items = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Apply all scan patterns
            for pattern_name, pattern_config in self.scan_patterns.items():
                matches = re.finditer(pattern_config["pattern"], content, re.MULTILINE | re.IGNORECASE)

                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    debt_item = self._create_debt_item(
                        pattern_name=pattern_name,
                        pattern_config=pattern_config,
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_number,
                        match_text=match.group(0),
                        context_lines=lines[max(0, line_number-3):line_number+2]
                    )

                    debt_items.append(debt_item)

            # Check for specific architectural patterns
            debt_items.extend(await self._check_architectural_patterns(file_path, content))

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")

        return debt_items

    async def _scan_config_file(self, file_path: Path) -> List[TechnicalDebtItem]:
        """Scan configuration files for technical debt"""
        debt_items = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for development configurations in production files
            if any(term in str(file_path).lower() for term in ['prod', 'production']):
                if re.search(r'localhost|127\.0\.0\.1|debug.*true', content, re.IGNORECASE):
                    debt_item = TechnicalDebtItem(
                        id=f"config_debt_{hash(str(file_path))}",
                        title="Development configuration in production file",
                        description="Production configuration file contains development settings",
                        severity=TechnicalDebtSeverity.CRITICAL,
                        category=TechnicalDebtCategory.CONFIGURATION,
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=None,
                        code_snippet=content[:200] + "..." if len(content) > 200 else content,
                        impact_assessment="High security risk and performance degradation",
                        remediation_effort="1-2 hours",
                        business_impact="Critical security vulnerability",
                        security_implications="Exposes development endpoints in production",
                        performance_impact="May degrade performance",
                        maintainability_impact="Low",
                        suggested_solution="Remove all development settings from production configs",
                        dependencies=[],
                        related_items=[],
                        assigned_to=None,
                        created_date=datetime.now(),
                        target_resolution_date=datetime.now() + timedelta(days=1),
                        last_updated=datetime.now(),
                        status="open",
                        tags=["configuration", "security", "production"],
                        technical_context={"file_type": "configuration", "environment": "production"},
                        apqc_process_reference="11.2.2"
                    )
                    debt_items.append(debt_item)

        except Exception as e:
            logger.error(f"Error scanning config file {file_path}: {e}")

        return debt_items

    def _create_debt_item(self, pattern_name: str, pattern_config: Dict,
                         file_path: str, line_number: int, match_text: str,
                         context_lines: List[str]) -> TechnicalDebtItem:
        """Create a technical debt item from scan results"""

        # Extract meaningful description from match
        description = match_text.strip()
        if pattern_name == "todo_comments":
            todo_match = re.search(r"(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)(?:\s*:)?\s*(.+)", match_text)
            if todo_match:
                description = f"{todo_match.group(1)}: {todo_match.group(2).strip()}"

        # Generate impact assessments based on pattern type
        impact_assessments = self._generate_impact_assessment(pattern_name, pattern_config, match_text)

        debt_item = TechnicalDebtItem(
            id=f"{pattern_name}_{hash(file_path + str(line_number) + match_text)}",
            title=f"{pattern_name.replace('_', ' ').title()} in {Path(file_path).name}",
            description=description,
            severity=pattern_config["severity"],
            category=pattern_config["category"],
            file_path=file_path,
            line_number=line_number,
            code_snippet='\n'.join(context_lines),
            impact_assessment=impact_assessments["impact"],
            remediation_effort=impact_assessments["effort"],
            business_impact=impact_assessments["business"],
            security_implications=impact_assessments["security"],
            performance_impact=impact_assessments["performance"],
            maintainability_impact=impact_assessments["maintainability"],
            suggested_solution=impact_assessments["solution"],
            dependencies=[],
            related_items=[],
            assigned_to=None,
            created_date=datetime.now(),
            target_resolution_date=self._calculate_target_date(pattern_config["severity"]),
            last_updated=datetime.now(),
            status="open",
            tags=[pattern_name, pattern_config["category"].value],
            technical_context={
                "pattern_type": pattern_name,
                "match_text": match_text,
                "file_extension": Path(file_path).suffix
            },
            apqc_process_reference=pattern_config["apqc_process"]
        )

        return debt_item

    def _generate_impact_assessment(self, pattern_name: str, pattern_config: Dict, match_text: str) -> Dict[str, str]:
        """Generate comprehensive impact assessment for debt item"""

        impact_templates = {
            "todo_comments": {
                "impact": "Indicates incomplete or problematic code that needs attention",
                "effort": "1-4 hours depending on complexity",
                "business": "May indicate deferred features or potential bugs",
                "security": "Unknown - requires investigation",
                "performance": "Unknown - may have performance implications",
                "maintainability": "Reduces code clarity and maintainability",
                "solution": "Investigate TODO item and either complete or remove"
            },
            "hardcoded_values": {
                "impact": "Configuration is not environment-aware, breaks in different environments",
                "effort": "2-8 hours to externalize configuration",
                "business": "Deployment issues and environment-specific bugs",
                "security": "May expose development endpoints in production",
                "performance": "May cause performance degradation",
                "maintainability": "Makes environment management difficult",
                "solution": "Move hardcoded values to environment variables or configuration files"
            },
            "security_issues": {
                "impact": "Critical security vulnerability that must be addressed immediately",
                "effort": "4-16 hours depending on scope",
                "business": "High risk of security breach and data exposure",
                "security": "Critical security vulnerability",
                "performance": "May impact performance depending on implementation",
                "maintainability": "Increases security maintenance burden",
                "solution": "Implement proper security measures and remove vulnerabilities"
            },
            "performance_issues": {
                "impact": "Code patterns that may cause performance degradation",
                "effort": "2-8 hours to optimize",
                "business": "User experience degradation and increased infrastructure costs",
                "security": "May enable DoS attacks",
                "performance": "Significant performance impact",
                "maintainability": "May require ongoing optimization",
                "solution": "Optimize database queries and remove performance bottlenecks"
            }
        }

        return impact_templates.get(pattern_name, {
            "impact": "General technical debt requiring attention",
            "effort": "2-4 hours",
            "business": "May impact maintainability and development velocity",
            "security": "Minimal security impact",
            "performance": "Minimal performance impact",
            "maintainability": "Reduces code maintainability",
            "solution": "Address according to category-specific best practices"
        })

    def _calculate_target_date(self, severity: TechnicalDebtSeverity) -> datetime:
        """Calculate target resolution date based on severity"""
        target_days = {
            TechnicalDebtSeverity.CRITICAL: 1,
            TechnicalDebtSeverity.HIGH: 7,
            TechnicalDebtSeverity.MEDIUM: 30,
            TechnicalDebtSeverity.LOW: 90
        }

        return datetime.now() + timedelta(days=target_days[severity])

    async def _check_architectural_patterns(self, file_path: Path, content: str) -> List[TechnicalDebtItem]:
        """Check for architectural anti-patterns and violations"""
        debt_items = []

        # Check for circular imports (simplified detection)
        if "import" in content and len(re.findall(r"from\s+\w+", content)) > 10:
            debt_item = TechnicalDebtItem(
                id=f"arch_imports_{hash(str(file_path))}",
                title="Potential architectural complexity in imports",
                description="File has many imports which may indicate tight coupling",
                severity=TechnicalDebtSeverity.MEDIUM,
                category=TechnicalDebtCategory.ARCHITECTURE,
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=None,
                code_snippet=content[:300] + "...",
                impact_assessment="May indicate architectural complexity",
                remediation_effort="4-8 hours for refactoring",
                business_impact="Reduced maintainability and development velocity",
                security_implications="Minimal",
                performance_impact="Minimal",
                maintainability_impact="High - tight coupling reduces maintainability",
                suggested_solution="Review dependencies and consider architectural refactoring",
                dependencies=[],
                related_items=[],
                assigned_to=None,
                created_date=datetime.now(),
                target_resolution_date=datetime.now() + timedelta(days=30),
                last_updated=datetime.now(),
                status="open",
                tags=["architecture", "complexity"],
                technical_context={"import_count": len(re.findall(r"from\s+\w+", content))},
                apqc_process_reference="11.2.1"
            )
            debt_items.append(debt_item)

        return debt_items

    def calculate_priority_score(self, debt_item: TechnicalDebtItem) -> float:
        """Calculate priority score for debt item based on multiple factors"""
        severity_weight = self.priority_matrix["severity_weights"][debt_item.severity]
        category_multiplier = self.priority_matrix["category_multipliers"][debt_item.category]

        # Additional factors
        age_factor = 1.0  # Could add age-based escalation
        business_criticality = 1.0  # Could add business criticality assessment

        return severity_weight * category_multiplier * age_factor * business_criticality

    def get_debt_summary(self) -> Dict[str, Any]:
        """Generate comprehensive technical debt summary"""
        if not self.debt_database:
            return {"message": "No technical debt items tracked"}

        summary = {
            "total_items": len(self.debt_database),
            "by_severity": {},
            "by_category": {},
            "by_status": {},
            "priority_items": [],
            "metrics": {},
            "recommendations": []
        }

        # Calculate distributions
        for item in self.debt_database.values():
            # Severity distribution
            severity_key = item.severity.value
            summary["by_severity"][severity_key] = summary["by_severity"].get(severity_key, 0) + 1

            # Category distribution
            category_key = item.category.value
            summary["by_category"][category_key] = summary["by_category"].get(category_key, 0) + 1

            # Status distribution
            status_key = item.status
            summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1

        # Get top priority items
        sorted_items = sorted(
            self.debt_database.values(),
            key=self.calculate_priority_score,
            reverse=True
        )
        summary["priority_items"] = [
            {
                "id": item.id,
                "title": item.title,
                "severity": item.severity.value,
                "category": item.category.value,
                "priority_score": self.calculate_priority_score(item),
                "file_path": item.file_path
            }
            for item in sorted_items[:10]
        ]

        # Calculate metrics
        critical_count = summary["by_severity"].get("critical", 0)
        high_count = summary["by_severity"].get("high", 0)

        summary["metrics"] = {
            "technical_debt_ratio": len(self.debt_database) / 100,  # Simplified metric
            "critical_high_ratio": (critical_count + high_count) / len(self.debt_database) if self.debt_database else 0,
            "avg_priority_score": sum(self.calculate_priority_score(item) for item in self.debt_database.values()) / len(self.debt_database) if self.debt_database else 0
        }

        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(summary)

        return summary

    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on debt analysis"""
        recommendations = []

        if summary["by_severity"].get("critical", 0) > 0:
            recommendations.append("⚠️  Address all CRITICAL security vulnerabilities immediately")

        if summary["by_severity"].get("high", 0) > 5:
            recommendations.append("📈 Create sprint backlog items for HIGH priority technical debt")

        if summary["by_category"].get("configuration", 0) > 3:
            recommendations.append("⚙️  Implement comprehensive configuration management strategy")

        if summary["by_category"].get("documentation", 0) > 10:
            recommendations.append("📚 Launch documentation improvement initiative")

        if summary["metrics"]["critical_high_ratio"] > 0.3:
            recommendations.append("🚨 Technical debt levels are high - consider dedicated cleanup sprint")

        return recommendations

    async def export_debt_report(self, output_path: str) -> str:
        """Export comprehensive technical debt report"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": self.get_debt_summary(),
            "all_items": [asdict(item) for item in self.debt_database.values()],
            "scan_configuration": {
                "patterns": self.scan_patterns,
                "exclusions": self.exclusion_patterns
            }
        }

        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (TechnicalDebtSeverity, TechnicalDebtCategory)):
                return obj.value
            return str(obj)

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=json_serializer)

        logger.info(f"📊 Technical debt report exported to {output_path}")
        return output_path

# Initialize the technical debt tracking agent
technical_debt_tracker = TechnicalDebtTrackingAgent(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)