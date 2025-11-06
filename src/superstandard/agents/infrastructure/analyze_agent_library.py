"""
Agent Library Analysis Tool

Comprehensive analysis of all agents in the library:
- Inventory and cataloging
- Compliance assessment
- Completeness evaluation
- Gap identification
- Indexing recommendations

Usage:
    python analyze_agent_library.py
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class AgentAnalysis:
    """Analysis result for a single agent"""

    file_path: str
    agent_name: str
    agent_class: Optional[str]
    agent_type: Optional[str]
    category: str

    # Compliance checks
    has_base_agent: bool
    has_protocol_mixin: bool
    has_config_dataclass: bool
    has_execute_method: bool
    has_health_check: bool
    has_input_schema: bool
    has_output_schema: bool
    has_from_environment: bool

    # Documentation
    has_docstring: bool
    has_apqc_metadata: bool
    apqc_category_id: Optional[str]
    apqc_process_id: Optional[str]

    # Code quality
    line_count: int
    has_todo_comments: int
    has_placeholder_impl: bool

    # Overall assessment
    compliance_score: float
    completeness_score: float
    is_production_ready: bool
    issues: List[str]
    recommendations: List[str]


class AgentLibraryAnalyzer:
    """Analyze the entire agent library"""

    def __init__(self, library_path: str = "library"):
        self.library_path = Path(library_path)
        self.agents: List[AgentAnalysis] = []

    def analyze_all(self) -> Dict[str, Any]:
        """Analyze all agents in the library"""
        print("=" * 80)
        print("AGENT LIBRARY ANALYSIS")
        print("=" * 80)
        print(f"\nScanning: {self.library_path.absolute()}")

        # Find all Python files
        agent_files = list(self.library_path.rglob("*.py"))
        agent_files = [
            f for f in agent_files if not f.name.startswith("__") and "test" not in f.name.lower()
        ]

        print(f"Found {len(agent_files)} agent files\n")

        # Analyze each agent
        for agent_file in agent_files:
            try:
                analysis = self._analyze_agent_file(agent_file)
                if analysis:
                    self.agents.append(analysis)
            except Exception as e:
                print(f"[ERROR] Failed to analyze {agent_file}: {e}")

        # Generate report
        return self._generate_report()

    def _analyze_agent_file(self, file_path: Path) -> Optional[AgentAnalysis]:
        """Analyze a single agent file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except:
            return None

        # Parse AST
        try:
            tree = ast.parse(content)
        except:
            return None

        # Extract information
        agent_name = file_path.stem
        category = self._get_category_from_path(file_path)

        # Find agent class
        agent_class = None
        has_base_agent = "BaseAgent" in content
        has_protocol_mixin = "ProtocolMixin" in content

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "Agent" in node.name and not node.name.endswith("Config"):
                    agent_class = node.name
                    break

        # Check for key components
        has_config_dataclass = "@dataclass" in content and "Config" in content
        has_execute_method = bool(re.search(r"async def execute\(", content))
        has_health_check = bool(re.search(r"async def health_check\(", content))
        has_input_schema = "get_input_schema" in content
        has_output_schema = "get_output_schema" in content
        has_from_environment = "from_environment" in content

        # Documentation
        has_docstring = bool(re.search(r'"""[\s\S]*?"""', content))
        has_apqc_metadata = "APQC" in content or "apqc" in content

        # Extract APQC metadata
        apqc_category_match = re.search(r'apqc_category_id["\s:=]+([0-9.]+)', content)
        apqc_process_match = re.search(r'apqc_process_id["\s:=]+([0-9.]+)', content)
        apqc_category_id = apqc_category_match.group(1) if apqc_category_match else None
        apqc_process_id = apqc_process_match.group(1) if apqc_process_match else None

        # Extract agent type
        agent_type_match = re.search(r'agent_type["\s:=]+"([^"]+)"', content)
        agent_type = agent_type_match.group(1) if agent_type_match else None

        # Code quality
        line_count = len(lines)
        has_todo_comments = len(re.findall(r"# TODO", content, re.IGNORECASE))
        has_placeholder_impl = "# Placeholder" in content or "pass  # TODO" in content

        # Calculate compliance score
        compliance_checks = [
            has_base_agent,
            has_protocol_mixin,
            has_config_dataclass,
            has_execute_method,
            has_health_check,
            has_input_schema,
            has_output_schema,
            has_from_environment,
        ]
        compliance_score = sum(compliance_checks) / len(compliance_checks)

        # Calculate completeness score
        completeness_checks = [
            has_docstring,
            has_apqc_metadata,
            line_count > 100,
            has_todo_comments == 0,
            not has_placeholder_impl,
            agent_class is not None,
        ]
        completeness_score = sum(completeness_checks) / len(completeness_checks)

        # Identify issues
        issues = []
        if not has_base_agent:
            issues.append("Missing BaseAgent inheritance")
        if not has_protocol_mixin:
            issues.append("Missing ProtocolMixin")
        if not has_execute_method:
            issues.append("Missing execute() method")
        if not has_health_check:
            issues.append("Missing health_check() method")
        if has_placeholder_impl:
            issues.append("Contains placeholder implementation")
        if has_todo_comments > 0:
            issues.append(f"{has_todo_comments} TODO comments")
        if not has_apqc_metadata:
            issues.append("Missing APQC metadata")

        # Recommendations
        recommendations = []
        if compliance_score < 0.8:
            recommendations.append("Add missing compliance features")
        if not has_docstring:
            recommendations.append("Add comprehensive docstring")
        if has_todo_comments > 0:
            recommendations.append("Complete TODO items")
        if line_count < 100:
            recommendations.append("Implement full functionality")

        # Production readiness
        is_production_ready = (
            compliance_score >= 0.9
            and completeness_score >= 0.8
            and not has_placeholder_impl
            and has_todo_comments == 0
        )

        return AgentAnalysis(
            file_path=str(file_path.relative_to(self.library_path)),
            agent_name=agent_name,
            agent_class=agent_class,
            agent_type=agent_type,
            category=category,
            has_base_agent=has_base_agent,
            has_protocol_mixin=has_protocol_mixin,
            has_config_dataclass=has_config_dataclass,
            has_execute_method=has_execute_method,
            has_health_check=has_health_check,
            has_input_schema=has_input_schema,
            has_output_schema=has_output_schema,
            has_from_environment=has_from_environment,
            has_docstring=has_docstring,
            has_apqc_metadata=has_apqc_metadata,
            apqc_category_id=apqc_category_id,
            apqc_process_id=apqc_process_id,
            line_count=line_count,
            has_todo_comments=has_todo_comments,
            has_placeholder_impl=has_placeholder_impl,
            compliance_score=compliance_score,
            completeness_score=completeness_score,
            is_production_ready=is_production_ready,
            issues=issues,
            recommendations=recommendations,
        )

    def _get_category_from_path(self, file_path: Path) -> str:
        """Extract category from file path"""
        parts = file_path.parts
        if "apqc" in parts:
            idx = parts.index("apqc")
            if idx + 1 < len(parts):
                return f"APQC {parts[idx + 1]}"
        elif "agents" in parts:
            idx = parts.index("agents")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return "unknown"

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        total_agents = len(self.agents)

        if total_agents == 0:
            return {"error": "No agents found", "total_agents": 0}

        # Overall statistics
        production_ready = sum(1 for a in self.agents if a.is_production_ready)
        avg_compliance = sum(a.compliance_score for a in self.agents) / total_agents
        avg_completeness = sum(a.completeness_score for a in self.agents) / total_agents

        # Compliance breakdown
        compliance_full = sum(1 for a in self.agents if a.compliance_score >= 0.9)
        compliance_partial = sum(1 for a in self.agents if 0.5 <= a.compliance_score < 0.9)
        compliance_none = sum(1 for a in self.agents if a.compliance_score < 0.5)

        # Category breakdown
        categories = {}
        for agent in self.agents:
            cat = agent.category
            if cat not in categories:
                categories[cat] = {
                    "total": 0,
                    "production_ready": 0,
                    "avg_compliance": 0,
                    "agents": [],
                }
            categories[cat]["total"] += 1
            categories[cat]["production_ready"] += 1 if agent.is_production_ready else 0
            categories[cat]["avg_compliance"] += agent.compliance_score
            categories[cat]["agents"].append(agent.agent_name)

        # Calculate averages
        for cat_data in categories.values():
            cat_data["avg_compliance"] /= cat_data["total"]

        # Most common issues
        all_issues = []
        for agent in self.agents:
            all_issues.extend(agent.issues)

        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Agents needing work
        needs_work = [
            {
                "name": a.agent_name,
                "category": a.category,
                "compliance": f"{a.compliance_score:.1%}",
                "completeness": f"{a.completeness_score:.1%}",
                "issues": len(a.issues),
            }
            for a in sorted(self.agents, key=lambda x: (x.compliance_score, x.completeness_score))[
                :20
            ]
        ]

        report = {
            "generated_at": datetime.now().isoformat(),
            "library_path": str(self.library_path.absolute()),
            "summary": {
                "total_agents": total_agents,
                "production_ready": production_ready,
                "production_ready_rate": f"{production_ready/total_agents:.1%}",
                "avg_compliance_score": f"{avg_compliance:.1%}",
                "avg_completeness_score": f"{avg_completeness:.1%}",
                "compliance_breakdown": {
                    "full_compliance (>=90%)": compliance_full,
                    "partial_compliance (50-90%)": compliance_partial,
                    "low_compliance (<50%)": compliance_none,
                },
            },
            "by_category": categories,
            "top_issues": [{"issue": issue, "count": count} for issue, count in top_issues],
            "agents_needing_work": needs_work,
            "agents_details": [asdict(a) for a in self.agents],
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print formatted report"""
        print("\n" + "=" * 80)
        print("ANALYSIS REPORT")
        print("=" * 80)

        summary = report["summary"]
        print(f"\n{summary['total_agents']} total agents found")
        print(
            f"Production Ready: {summary['production_ready']} ({summary['production_ready_rate']})"
        )
        print(f"Average Compliance: {summary['avg_compliance_score']}")
        print(f"Average Completeness: {summary['avg_completeness_score']}")

        print(f"\nCompliance Breakdown:")
        for level, count in summary["compliance_breakdown"].items():
            print(f"  {level}: {count}")

        print(f"\nTop Issues ({len(report['top_issues'])} types):")
        for item in report["top_issues"][:5]:
            print(f"  {item['count']:3d}x - {item['issue']}")

        print(f"\nAgents by Category ({len(report['by_category'])} categories):")
        for cat, data in sorted(
            report["by_category"].items(), key=lambda x: x[1]["total"], reverse=True
        )[:10]:
            print(
                f"  {cat:30s} - {data['total']:3d} agents ({data['production_ready']:3d} ready, {data['avg_compliance']:.0%} avg compliance)"
            )

        print(f"\nTop 10 Agents Needing Work:")
        for i, agent in enumerate(report["agents_needing_work"][:10], 1):
            print(
                f"  {i:2d}. {agent['name']:40s} - C:{agent['compliance']:5s} Comp:{agent['completeness']:5s} ({agent['issues']} issues)"
            )

        print("\n" + "=" * 80)

    def export_to_json(
        self, report: Dict[str, Any], output_path: str = "agent_library_analysis.json"
    ):
        """Export report to JSON"""
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report exported to: {output_path}")


def main():
    """Main entry point"""
    # Determine library path
    script_dir = Path(__file__).parent.parent
    library_path = script_dir / "library"

    if not library_path.exists():
        print(f"ERROR: Library path not found: {library_path}")
        return

    # Run analysis
    analyzer = AgentLibraryAnalyzer(str(library_path))
    report = analyzer.analyze_all()

    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    # Print report
    analyzer.print_report(report)

    # Export to JSON
    output_path = script_dir / "agent_library_analysis.json"
    analyzer.export_to_json(report, str(output_path))

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    summary = report["summary"]
    production_ready = summary["production_ready"]
    total = summary["total_agents"]

    if production_ready < total * 0.5:
        print("\n[PRIORITY: HIGH] Less than 50% of agents are production-ready")
        print("  Action: Focus on completing core agents first")

    if report["top_issues"]:
        top_issue = report["top_issues"][0]
        print(
            f"\n[PRIORITY: HIGH] Most common issue: {top_issue['issue']} ({top_issue['count']} agents)"
        )
        print("  Action: Create batch retrofit script to fix this issue across all agents")

    low_compliance = summary["compliance_breakdown"].get("low_compliance (<50%)", 0)
    if low_compliance > 0:
        print(f"\n[PRIORITY: MEDIUM] {low_compliance} agents with low compliance")
        print("  Action: Review architectural standards and update agents")

    print("\n[RECOMMENDED] Next Steps:")
    print("  1. Review agent_library_analysis.json for detailed breakdown")
    print("  2. Prioritize production-readying core/frequently-used agents")
    print("  3. Create retrofit scripts for common issues")
    print("  4. Set up automated compliance checking in CI/CD")
    print("  5. Document agent development standards")
    print("  6. Create agent templates for new development")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
