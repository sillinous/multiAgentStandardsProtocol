"""
Duplicate Agent Consolidation Tool

Analyzes duplicate agents and creates consolidation recommendations.

Usage:
    python scripts/consolidate_duplicates.py
"""

import json
from pathlib import Path
from collections import defaultdict
import os


class DuplicateConsolidator:
    """Analyzes and consolidates duplicate agents"""

    def __init__(self, catalog_path: str):
        with open(catalog_path) as f:
            self.catalog = json.load(f)

        self.agents = self.catalog["agents"]
        self.duplicates = defaultdict(list)
        self.consolidation_plan = []

    def analyze_duplicates(self):
        """Build duplicate groups from catalog"""
        # Find duplicates from agent names
        name_groups = defaultdict(list)
        for agent in self.agents:
            base_name = agent["name"].lower().replace("_", "").replace("-", "")
            name_groups[base_name].append(agent)

        # Only keep groups with 2+ agents
        for base_name, agents in name_groups.items():
            if len(agents) > 1:
                self.duplicates[agents[0]["name"]] = agents

    def create_consolidation_plan(self):
        """Create consolidation recommendations"""
        print("\n" + "=" * 70)
        print("DUPLICATE CONSOLIDATION ANALYSIS")
        print("=" * 70)

        # Sort by severity (most duplicates first)
        sorted_dups = sorted(self.duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        critical_count = 0
        high_count = 0
        medium_count = 0

        for primary_name, duplicates in sorted_dups:
            count = len(duplicates)

            # Categorize by severity
            if count >= 10:
                severity = "CRITICAL"
                critical_count += 1
            elif count >= 5:
                severity = "HIGH"
                high_count += 1
            else:
                severity = "MEDIUM"
                medium_count += 1

            # Create recommendation
            recommendation = {
                "primary": primary_name,
                "duplicates": duplicates,
                "count": count,
                "severity": severity,
                "action": self._recommend_action(duplicates),
            }

            self.consolidation_plan.append(recommendation)

        print(f"\nDuplicate Summary:")
        print(f"  CRITICAL (10+ duplicates): {critical_count} groups")
        print(f"  HIGH (5-9 duplicates): {high_count} groups")
        print(f"  MEDIUM (2-4 duplicates): {medium_count} groups")
        print(f"  Total: {len(sorted_dups)} duplicate groups")

    def _recommend_action(self, duplicates):
        """Recommend consolidation action"""
        # Check if mix of Python and Markdown
        types = set(d["type"] for d in duplicates)

        if "python" in types and "markdown" in types:
            return "MERGE: Keep Python implementation, use Markdown as documentation"

        # Check for version suffixes
        names = [d["name"] for d in duplicates]
        if any("_v" in n.lower() for n in names):
            return "VERSION: Keep latest version, archive older versions"

        # Check for identical files from different sources
        files = set(d["file"] for d in duplicates)
        if len(files) == len(duplicates):
            return "REVIEW: Different implementations - manual review needed"

        return "EXACT_DUP: Identical files - delete duplicates, keep one"

    def generate_report(self, output_path: str):
        """Generate consolidation report"""
        lines = [
            "# Duplicate Agent Consolidation Report",
            "",
            f"**Total Duplicate Groups:** {len(self.consolidation_plan)}",
            f"**Total Duplicate Files:** {sum(r['count'] for r in self.consolidation_plan)}",
            "",
            "## Summary by Severity",
            "",
        ]

        # Group by severity
        by_severity = defaultdict(list)
        for rec in self.consolidation_plan:
            by_severity[rec["severity"]].append(rec)

        for severity in ["CRITICAL", "HIGH", "MEDIUM"]:
            if severity in by_severity:
                lines.append(f"### {severity} Priority ({len(by_severity[severity])} groups)")
                lines.append("")

                for rec in sorted(by_severity[severity], key=lambda x: -x["count"]):
                    lines.append(f"#### {rec['primary']} ({rec['count']} duplicates)")
                    lines.append(f"**Action:** {rec['action']}")
                    lines.append("")
                    lines.append("**Files:**")
                    for dup in rec["duplicates"]:
                        lines.append(f"- `{dup['file']}` ({dup['type']})")
                    lines.append("")

        # Add consolidation steps
        lines.extend(
            [
                "## Recommended Consolidation Steps",
                "",
                "### Phase 1: Critical Duplicates (10+ copies)",
                "1. **BaseAgent consolidation** - Choose canonical base agent implementation",
                "2. Update all other agents to inherit from canonical base",
                "3. Archive old base agent versions",
                "",
                "### Phase 2: High Priority (5-9 copies)",
                "1. Review each group manually",
                "2. Identify best implementation",
                "3. Merge features if needed",
                "4. Archive redundant versions",
                "",
                "### Phase 3: Medium Priority (2-4 copies)",
                "1. Python vs Markdown: Keep Python, use MD as docs",
                "2. Versioned agents: Keep latest, document changes",
                "3. Different implementations: Review for unique features",
                "",
                "## Automation Opportunities",
                "",
                "Could automate:",
                "- Exact duplicate detection and deletion",
                "- Version number extraction and comparison",
                "- Python/Markdown pairing",
                "- File similarity analysis",
                "",
            ]
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\nConsolidation report saved to: {output_path}")

    def print_top_duplicates(self, limit=10):
        """Print top duplicate groups"""
        print(f"\nTop {limit} Duplicate Groups:")
        print("=" * 70)

        sorted_plan = sorted(self.consolidation_plan, key=lambda x: -x["count"])
        for i, rec in enumerate(sorted_plan[:limit], 1):
            print(f"\n{i}. {rec['primary']} - {rec['count']} copies ({rec['severity']})")
            print(f"   Action: {rec['action']}")
            print(f"   Files:")
            for dup in rec["duplicates"][:3]:
                print(f"     - {dup['file']}")
            if len(rec["duplicates"]) > 3:
                print(f"     ... and {len(rec['duplicates']) - 3} more")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("SuperStandard Duplicate Consolidation Tool")
    print("=" * 70)

    base_path = Path(__file__).parent.parent
    catalog_path = base_path / "AGENT_CATALOG.json"

    consolidator = DuplicateConsolidator(catalog_path)

    print("\nAnalyzing duplicates...")
    consolidator.analyze_duplicates()

    print("Creating consolidation plan...")
    consolidator.create_consolidation_plan()

    consolidator.print_top_duplicates(limit=15)

    consolidator.generate_report(base_path / "DUPLICATE_CONSOLIDATION_PLAN.md")

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review DUPLICATE_CONSOLIDATION_PLAN.md")
    print("2. Start with CRITICAL priority items")
    print("3. Create backup before deleting files")
    print("4. Update imports/references after consolidation")


if __name__ == "__main__":
    main()
