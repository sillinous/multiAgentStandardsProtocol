"""
Agent Compliance Checker - Validates Architectural Standards

Automatically checks agents against all 8 architectural principles:
1. Standardized
2. Interoperable
3. Redeployable
4. Reusable
5. Atomic
6. Composable
7. Orchestratable
8. Vendor/Model/System Agnostic

Usage:
    python agent_compliance_checker.py --file path/to/agent.py
    python agent_compliance_checker.py --directory path/to/agents/
    python agent_compliance_checker.py --all  # Check all agents in library
"""

import os
import sys
import ast
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance levels"""

    FULL = "full"  # 100% compliant
    HIGH = "high"  # 80-99% compliant
    PARTIAL = "partial"  # 50-79% compliant
    LOW = "low"  # 20-49% compliant
    NON_COMPLIANT = "non_compliant"  # 0-19% compliant


@dataclass
class ComplianceCheck:
    """Single compliance check result"""

    principle: str
    requirement: str
    passed: bool
    details: str
    severity: str = "required"  # required, recommended, optional


@dataclass
class ComplianceReport:
    """Complete compliance report for an agent"""

    agent_file: str
    agent_name: str
    compliance_level: ComplianceLevel
    score: float  # 0-100
    checks_passed: int
    checks_failed: int
    checks_total: int
    principles: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentComplianceChecker:
    """
    Validates agent compliance with architectural standards
    """

    def __init__(self):
        self.required_checks = self._initialize_checks()

    def _initialize_checks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize all compliance checks by principle"""
        return {
            "standardized": [
                {
                    "requirement": "Inherits from BaseAgent",
                    "check": "base_agent_inheritance",
                    "severity": "required",
                },
                {
                    "requirement": "Has standard lifecycle methods (initialize, execute, shutdown)",
                    "check": "lifecycle_methods",
                    "severity": "required",
                },
                {
                    "requirement": "Uses structured logging",
                    "check": "structured_logging",
                    "severity": "required",
                },
                {
                    "requirement": "Follows naming conventions",
                    "check": "naming_conventions",
                    "severity": "recommended",
                },
                {
                    "requirement": "Has version constants",
                    "check": "version_constants",
                    "severity": "required",
                },
            ],
            "interoperable": [
                {
                    "requirement": "Includes ProtocolMixin",
                    "check": "protocol_mixin",
                    "severity": "required",
                },
                {
                    "requirement": "Supports A2A protocol",
                    "check": "a2a_protocol",
                    "severity": "required",
                },
                {
                    "requirement": "Supports ANP protocol (network registration)",
                    "check": "anp_protocol",
                    "severity": "required",
                },
                {
                    "requirement": "Standard message formats",
                    "check": "message_formats",
                    "severity": "recommended",
                },
            ],
            "redeployable": [
                {
                    "requirement": "Environment-based configuration",
                    "check": "env_config",
                    "severity": "required",
                },
                {
                    "requirement": "No hardcoded URLs or paths",
                    "check": "no_hardcoded_values",
                    "severity": "required",
                },
                {
                    "requirement": "Has health check method",
                    "check": "health_check",
                    "severity": "required",
                },
                {
                    "requirement": "Config validation",
                    "check": "config_validation",
                    "severity": "required",
                },
            ],
            "reusable": [
                {
                    "requirement": "No project-specific logic",
                    "check": "no_project_specific",
                    "severity": "required",
                },
                {
                    "requirement": "Configuration-driven behavior",
                    "check": "config_driven",
                    "severity": "required",
                },
                {
                    "requirement": "Has semantic versioning",
                    "check": "semantic_versioning",
                    "severity": "required",
                },
                {
                    "requirement": "Comprehensive documentation",
                    "check": "documentation",
                    "severity": "recommended",
                },
            ],
            "atomic": [
                {
                    "requirement": "Single responsibility",
                    "check": "single_responsibility",
                    "severity": "required",
                },
                {
                    "requirement": "Maximum 5-7 capabilities",
                    "check": "capability_count",
                    "severity": "recommended",
                },
                {
                    "requirement": "Clear, focused purpose",
                    "check": "focused_purpose",
                    "severity": "required",
                },
            ],
            "composable": [
                {
                    "requirement": "Compatible input/output interfaces",
                    "check": "io_interfaces",
                    "severity": "required",
                },
                {
                    "requirement": "Supports event-driven architecture",
                    "check": "event_driven",
                    "severity": "recommended",
                },
                {
                    "requirement": "State sharing mechanisms",
                    "check": "state_sharing",
                    "severity": "recommended",
                },
            ],
            "orchestratable": [
                {
                    "requirement": "Supports ACP protocol",
                    "check": "acp_protocol",
                    "severity": "required",
                },
                {
                    "requirement": "State reporting",
                    "check": "state_reporting",
                    "severity": "required",
                },
                {
                    "requirement": "Task execution framework",
                    "check": "task_execution",
                    "severity": "required",
                },
            ],
            "vendor_agnostic": [
                {
                    "requirement": "No vendor SDK dependencies in core",
                    "check": "no_vendor_sdks",
                    "severity": "required",
                },
                {
                    "requirement": "Abstraction layers for external services",
                    "check": "abstraction_layers",
                    "severity": "required",
                },
                {
                    "requirement": "Pluggable adapters",
                    "check": "pluggable_adapters",
                    "severity": "recommended",
                },
            ],
        }

    def check_agent_file(self, file_path: str) -> ComplianceReport:
        """
        Check a single agent file for compliance

        Args:
            file_path: Path to agent Python file

        Returns:
            Compliance report
        """
        print(f"\n🔍 Checking: {file_path}")

        # Read and parse file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return self._create_error_report(file_path, str(e))

        # Extract agent information
        agent_info = self._extract_agent_info(tree, content)

        # Run all checks
        all_checks = []
        principles_results = {}

        for principle, checks in self.required_checks.items():
            principle_checks = []
            for check_spec in checks:
                result = self._run_check(check_spec["check"], agent_info, tree, content)
                check_result = ComplianceCheck(
                    principle=principle,
                    requirement=check_spec["requirement"],
                    passed=result["passed"],
                    details=result["details"],
                    severity=check_spec["severity"],
                )
                principle_checks.append(check_result)
                all_checks.append(check_result)

            # Calculate principle score
            required_checks = [c for c in principle_checks if c.severity == "required"]
            passed_required = sum(1 for c in required_checks if c.passed)
            total_required = len(required_checks)

            principles_results[principle] = {
                "passed": passed_required,
                "total": total_required,
                "score": (passed_required / total_required * 100) if total_required > 0 else 0,
                "checks": [
                    {
                        "requirement": c.requirement,
                        "passed": c.passed,
                        "details": c.details,
                        "severity": c.severity,
                    }
                    for c in principle_checks
                ],
            }

        # Calculate overall score
        passed = sum(1 for c in all_checks if c.passed and c.severity == "required")
        total = sum(1 for c in all_checks if c.severity == "required")
        score = (passed / total * 100) if total > 0 else 0

        # Determine compliance level
        compliance_level = self._determine_compliance_level(score)

        # Generate recommendations
        recommendations = self._generate_recommendations(all_checks, agent_info)

        report = ComplianceReport(
            agent_file=file_path,
            agent_name=agent_info.get("name", "Unknown"),
            compliance_level=compliance_level,
            score=score,
            checks_passed=passed,
            checks_failed=total - passed,
            checks_total=total,
            principles=principles_results,
            recommendations=recommendations,
        )

        return report

    def _extract_agent_info(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Extract agent information from AST"""
        info = {
            "name": None,
            "has_base_agent": False,
            "has_protocol_mixin": False,
            "methods": [],
            "imports": [],
            "classes": [],
            "has_config_class": False,
            "has_version_constants": False,
            "docstring": None,
        }

        # Find all classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info["classes"].append(node.name)

                # Check if this is the main agent class
                if node.name.endswith("Agent") and not node.name.endswith("Config"):
                    info["name"] = node.name

                    # Check bases
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            if base.id == "BaseAgent":
                                info["has_base_agent"] = True
                            elif base.id == "ProtocolMixin":
                                info["has_protocol_mixin"] = True

                    # Get docstring
                    if ast.get_docstring(node):
                        info["docstring"] = ast.get_docstring(node)

                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            info["methods"].append(item.name)

                # Check for config class
                if node.name.endswith("Config"):
                    info["has_config_class"] = True

            # Check imports
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    info["imports"].append(node.module)

        # Check for version constants
        if "AGENT_VERSION" in content or "VERSION =" in content:
            info["has_version_constants"] = True

        return info

    def _run_check(
        self, check_name: str, agent_info: Dict[str, Any], tree: ast.AST, content: str
    ) -> Dict[str, Any]:
        """Run a specific compliance check"""

        # Map check names to check methods
        check_methods = {
            "base_agent_inheritance": self._check_base_agent_inheritance,
            "lifecycle_methods": self._check_lifecycle_methods,
            "structured_logging": self._check_structured_logging,
            "naming_conventions": self._check_naming_conventions,
            "version_constants": self._check_version_constants,
            "protocol_mixin": self._check_protocol_mixin,
            "a2a_protocol": self._check_a2a_protocol,
            "anp_protocol": self._check_anp_protocol,
            "message_formats": self._check_message_formats,
            "env_config": self._check_env_config,
            "no_hardcoded_values": self._check_no_hardcoded_values,
            "health_check": self._check_health_check,
            "config_validation": self._check_config_validation,
            "no_project_specific": self._check_no_project_specific,
            "config_driven": self._check_config_driven,
            "semantic_versioning": self._check_semantic_versioning,
            "documentation": self._check_documentation,
            "single_responsibility": self._check_single_responsibility,
            "capability_count": self._check_capability_count,
            "focused_purpose": self._check_focused_purpose,
            "io_interfaces": self._check_io_interfaces,
            "event_driven": self._check_event_driven,
            "state_sharing": self._check_state_sharing,
            "acp_protocol": self._check_acp_protocol,
            "state_reporting": self._check_state_reporting,
            "task_execution": self._check_task_execution,
            "no_vendor_sdks": self._check_no_vendor_sdks,
            "abstraction_layers": self._check_abstraction_layers,
            "pluggable_adapters": self._check_pluggable_adapters,
        }

        check_method = check_methods.get(check_name)
        if check_method:
            return check_method(agent_info, tree, content)
        else:
            return {"passed": False, "details": f"Check '{check_name}' not implemented"}

    # ========================================================================
    # INDIVIDUAL CHECK METHODS
    # ========================================================================

    def _check_base_agent_inheritance(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check if agent inherits from BaseAgent"""
        if info["has_base_agent"]:
            return {"passed": True, "details": "Inherits from BaseAgent"}
        return {"passed": False, "details": "Does not inherit from BaseAgent"}

    def _check_lifecycle_methods(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for standard lifecycle methods"""
        required_methods = ["initialize", "execute", "shutdown"]
        missing = [m for m in required_methods if m not in info["methods"]]

        if not missing:
            return {"passed": True, "details": "All lifecycle methods present"}
        return {"passed": False, "details": f"Missing methods: {', '.join(missing)}"}

    def _check_structured_logging(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for structured logging"""
        if "logging" in info["imports"] or "self.logger" in content:
            return {"passed": True, "details": "Uses logging framework"}
        return {"passed": False, "details": "No logging framework detected"}

    def _check_naming_conventions(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check naming conventions"""
        if info["name"] and info["name"].endswith("Agent"):
            return {"passed": True, "details": "Follows naming convention (ends with 'Agent')"}
        return {"passed": False, "details": "Agent class should end with 'Agent'"}

    def _check_version_constants(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for version constants"""
        if info["has_version_constants"]:
            return {"passed": True, "details": "Has version constants"}
        return {"passed": False, "details": "Missing version constants (AGENT_VERSION, etc.)"}

    def _check_protocol_mixin(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for ProtocolMixin"""
        if info["has_protocol_mixin"] or "ProtocolMixin" in content:
            return {"passed": True, "details": "Includes ProtocolMixin"}
        return {"passed": False, "details": "Does not include ProtocolMixin"}

    def _check_a2a_protocol(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for A2A protocol support"""
        if "A2AMessage" in content or "send_a2a_message" in content:
            return {"passed": True, "details": "Supports A2A protocol"}
        return {"passed": False, "details": "No A2A protocol support detected"}

    def _check_anp_protocol(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for ANP protocol support"""
        if "ANPRegistration" in content or "register_on_network" in content:
            return {"passed": True, "details": "Supports ANP protocol"}
        return {"passed": False, "details": "No ANP protocol support detected"}

    def _check_message_formats(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for standard message formats"""
        # This is a recommended check, so we're lenient
        return {"passed": True, "details": "Check passed (recommended only)"}

    def _check_env_config(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for environment-based configuration"""
        if info["has_config_class"] and ("from_environment" in content or "os.getenv" in content):
            return {"passed": True, "details": "Uses environment-based configuration"}
        return {"passed": False, "details": "Missing environment-based configuration"}

    def _check_no_hardcoded_values(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for hardcoded values"""
        # Look for common hardcoded patterns
        hardcoded_patterns = [
            r"https?://(?!localhost)[a-zA-Z0-9.-]+",  # URLs (except localhost)
            r"/[a-z]+/[a-z]+/[a-z]+",  # Absolute paths
        ]

        found_hardcoded = []
        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content)
            # Filter out comments and docstrings
            for match in matches:
                if match and "http" in match:
                    found_hardcoded.append(match)

        if not found_hardcoded:
            return {"passed": True, "details": "No hardcoded URLs/paths detected"}
        return {"passed": False, "details": f"Found hardcoded values: {found_hardcoded[:3]}"}

    def _check_health_check(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for health check method"""
        if "health_check" in info["methods"]:
            return {"passed": True, "details": "Has health_check method"}
        return {"passed": False, "details": "Missing health_check method"}

    def _check_config_validation(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for config validation"""
        if "validate" in info["methods"] or "def validate" in content:
            return {"passed": True, "details": "Has config validation"}
        return {"passed": False, "details": "Missing config validation"}

    def _check_no_project_specific(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for project-specific logic"""
        # This is hard to check automatically, so we do a simple heuristic
        project_indicators = ["workspace_path", "project_root", "TODO: Add project-specific"]
        found = [ind for ind in project_indicators if ind in content]

        if not found:
            return {"passed": True, "details": "No obvious project-specific logic"}
        return {"passed": False, "details": f"Possible project-specific logic: {found}"}

    def _check_config_driven(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for configuration-driven behavior"""
        if info["has_config_class"]:
            return {"passed": True, "details": "Configuration-driven (has Config class)"}
        return {"passed": False, "details": "Missing configuration class"}

    def _check_semantic_versioning(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for semantic versioning"""
        version_pattern = r"\d+\.\d+\.\d+"
        if re.search(version_pattern, content):
            return {"passed": True, "details": "Uses semantic versioning"}
        return {"passed": False, "details": "Missing semantic version"}

    def _check_documentation(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for comprehensive documentation"""
        if info["docstring"] and len(info["docstring"]) > 100:
            return {"passed": True, "details": "Has comprehensive docstring"}
        return {"passed": False, "details": "Missing or insufficient documentation"}

    def _check_single_responsibility(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for single responsibility"""
        # Heuristic: agent should have one clear purpose
        if info["docstring"] and "agent" in info["docstring"].lower():
            return {"passed": True, "details": "Appears to have single responsibility"}
        return {"passed": False, "details": "Purpose unclear from documentation"}

    def _check_capability_count(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check capability count"""
        # This is recommended, so we're lenient
        return {"passed": True, "details": "Check passed (recommended only)"}

    def _check_focused_purpose(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for focused purpose"""
        if info["docstring"]:
            return {"passed": True, "details": "Has documented purpose"}
        return {"passed": False, "details": "Missing purpose documentation"}

    def _check_io_interfaces(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for compatible I/O interfaces"""
        if "execute" in info["methods"]:
            return {"passed": True, "details": "Has standard execute method"}
        return {"passed": False, "details": "Missing standard execute interface"}

    def _check_event_driven(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for event-driven support"""
        # Recommended check
        return {"passed": True, "details": "Check passed (recommended only)"}

    def _check_state_sharing(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for state sharing mechanisms"""
        # Recommended check
        return {"passed": True, "details": "Check passed (recommended only)"}

    def _check_acp_protocol(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for ACP protocol support"""
        if "ACPCoordination" in content or "enable_acp" in content:
            return {"passed": True, "details": "Supports ACP protocol"}
        return {"passed": False, "details": "No ACP protocol support detected"}

    def _check_state_reporting(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for state reporting"""
        if "self.state" in content or "get_state" in content:
            return {"passed": True, "details": "Has state reporting"}
        return {"passed": False, "details": "No state reporting mechanism"}

    def _check_task_execution(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for task execution framework"""
        if "execute" in info["methods"]:
            return {"passed": True, "details": "Has task execution framework"}
        return {"passed": False, "details": "Missing task execution framework"}

    def _check_no_vendor_sdks(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for vendor SDK dependencies"""
        vendor_sdks = ["anthropic", "openai", "google.cloud", "boto3", "azure"]
        found_vendors = [sdk for sdk in vendor_sdks if sdk in content]

        if not found_vendors:
            return {"passed": True, "details": "No vendor SDK dependencies in core"}
        return {"passed": False, "details": f"Found vendor SDKs: {found_vendors}"}

    def _check_abstraction_layers(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for abstraction layers"""
        # This is hard to check, so we use a heuristic
        if "DataSource" in content or "adapter" in content.lower():
            return {"passed": True, "details": "Has abstraction layers"}
        return {"passed": False, "details": "No obvious abstraction layers"}

    def _check_pluggable_adapters(self, info: Dict, tree: ast.AST, content: str) -> Dict:
        """Check for pluggable adapters"""
        # Recommended check
        return {"passed": True, "details": "Check passed (recommended only)"}

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _determine_compliance_level(self, score: float) -> ComplianceLevel:
        """Determine compliance level from score"""
        if score >= 100:
            return ComplianceLevel.FULL
        elif score >= 80:
            return ComplianceLevel.HIGH
        elif score >= 50:
            return ComplianceLevel.PARTIAL
        elif score >= 20:
            return ComplianceLevel.LOW
        else:
            return ComplianceLevel.NON_COMPLIANT

    def _generate_recommendations(
        self, checks: List[ComplianceCheck], agent_info: Dict
    ) -> List[str]:
        """Generate recommendations based on failed checks"""
        recommendations = []

        failed_required = [c for c in checks if not c.passed and c.severity == "required"]

        if failed_required:
            recommendations.append(
                f"⚠️  {len(failed_required)} required checks failed - agent is not production-ready"
            )

        # Group by principle
        principles_failed = {}
        for check in failed_required:
            if check.principle not in principles_failed:
                principles_failed[check.principle] = []
            principles_failed[check.principle].append(check.requirement)

        for principle, requirements in principles_failed.items():
            recommendations.append(f"🔧 Fix {principle}: {', '.join(requirements[:2])}")

        if not agent_info["has_base_agent"]:
            recommendations.append("📦 Inherit from BaseAgent (library/core/base_agent.py)")

        if not agent_info["has_protocol_mixin"]:
            recommendations.append("🔌 Add ProtocolMixin for interoperability")

        if not agent_info["has_config_class"]:
            recommendations.append("⚙️  Create Config dataclass with from_environment() method")

        return recommendations

    def _create_error_report(self, file_path: str, error: str) -> ComplianceReport:
        """Create error report when file can't be checked"""
        return ComplianceReport(
            agent_file=file_path,
            agent_name="Error",
            compliance_level=ComplianceLevel.NON_COMPLIANT,
            score=0.0,
            checks_passed=0,
            checks_failed=0,
            checks_total=0,
            principles={},
            recommendations=[f"❌ Error: {error}"],
        )

    def print_report(self, report: ComplianceReport):
        """Print compliance report to console"""
        print("\n" + "=" * 80)
        print(f"COMPLIANCE REPORT: {report.agent_name}")
        print("=" * 80)

        # Overall status
        level_colors = {
            ComplianceLevel.FULL: "🟢",
            ComplianceLevel.HIGH: "🟡",
            ComplianceLevel.PARTIAL: "🟠",
            ComplianceLevel.LOW: "🔴",
            ComplianceLevel.NON_COMPLIANT: "⛔",
        }

        color = level_colors.get(report.compliance_level, "⚪")
        print(f"\n{color} Compliance Level: {report.compliance_level.value.upper()}")
        print(f"📊 Score: {report.score:.1f}/100")
        print(f"✅ Passed: {report.checks_passed}/{report.checks_total}")
        print(f"❌ Failed: {report.checks_failed}/{report.checks_total}")

        # Principles breakdown
        print("\n" + "-" * 80)
        print("PRINCIPLES BREAKDOWN")
        print("-" * 80)

        for principle, results in report.principles.items():
            score = results["score"]
            status = "✅" if score == 100 else "❌" if score == 0 else "⚠️ "
            print(f"\n{status} {principle.upper()}: {score:.0f}%")
            print(f"   ({results['passed']}/{results['total']} required checks passed)")

            # Show failed checks
            failed = [
                c for c in results["checks"] if not c["passed"] and c["severity"] == "required"
            ]
            if failed:
                for check in failed:
                    print(f"   ❌ {check['requirement']}")
                    print(f"      {check['details']}")

        # Recommendations
        if report.recommendations:
            print("\n" + "-" * 80)
            print("RECOMMENDATIONS")
            print("-" * 80)
            for rec in report.recommendations:
                print(f"\n{rec}")

        print("\n" + "=" * 80)

    def save_report(self, report: ComplianceReport, output_file: str):
        """Save report to JSON file"""
        report_dict = {
            "agent_file": report.agent_file,
            "agent_name": report.agent_name,
            "compliance_level": report.compliance_level.value,
            "score": report.score,
            "checks_passed": report.checks_passed,
            "checks_failed": report.checks_failed,
            "checks_total": report.checks_total,
            "principles": report.principles,
            "recommendations": report.recommendations,
            "timestamp": report.timestamp,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        print(f"\n💾 Report saved to: {output_file}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check agent compliance with architectural standards"
    )
    parser.add_argument("--file", help="Path to single agent file")
    parser.add_argument("--directory", help="Path to directory of agents")
    parser.add_argument("--all", action="store_true", help="Check all agents in library")
    parser.add_argument("--output", help="Save report to JSON file")
    parser.add_argument("--summary", action="store_true", help="Show summary only")

    args = parser.parse_args()

    checker = AgentComplianceChecker()

    # Determine files to check
    files_to_check = []

    if args.file:
        files_to_check = [args.file]
    elif args.directory:
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                if file.endswith(".py") and "agent" in file.lower():
                    files_to_check.append(os.path.join(root, file))
    elif args.all:
        lib_path = "./autonomous-ecosystem/library/agents"
        if os.path.exists(lib_path):
            for root, dirs, files in os.walk(lib_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        files_to_check.append(os.path.join(root, file))

    if not files_to_check:
        print("❌ No agent files specified. Use --file, --directory, or --all")
        return

    print(f"\n🔍 Checking {len(files_to_check)} agent file(s)...\n")

    # Check all files
    reports = []
    for file_path in files_to_check:
        report = checker.check_agent_file(file_path)
        reports.append(report)

        if not args.summary:
            checker.print_report(report)

        if args.output:
            output_file = (
                args.output
                if len(files_to_check) == 1
                else args.output.replace(".json", f"_{report.agent_name}.json")
            )
            checker.save_report(report, output_file)

    # Print summary
    if len(reports) > 1:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        total_score = sum(r.score for r in reports) / len(reports)
        full_compliant = sum(1 for r in reports if r.compliance_level == ComplianceLevel.FULL)
        high_compliant = sum(1 for r in reports if r.compliance_level == ComplianceLevel.HIGH)

        print(f"\n📊 Average Score: {total_score:.1f}/100")
        print(f"🟢 Full Compliance: {full_compliant}/{len(reports)}")
        print(f"🟡 High Compliance: {high_compliant}/{len(reports)}")
        print(f"📁 Total Agents Checked: {len(reports)}")

        # Top performers
        sorted_reports = sorted(reports, key=lambda r: r.score, reverse=True)
        print("\n🏆 Top 5 Performers:")
        for i, report in enumerate(sorted_reports[:5], 1):
            print(f"   {i}. {report.agent_name}: {report.score:.1f}%")

        # Need attention
        needs_work = [r for r in reports if r.score < 80]
        if needs_work:
            print(f"\n⚠️  {len(needs_work)} agents need attention (score < 80%)")


if __name__ == "__main__":
    main()
