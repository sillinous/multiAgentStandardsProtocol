#!/usr/bin/env python3
"""
Import Path Migration Script - Phase 8

Standardizes all BaseAgent imports across the codebase to use the canonical
import path: from superstandard.agents.base.base_agent import BaseAgent

This script:
1. Scans all Python files for BaseAgent imports
2. Identifies and replaces inconsistent import patterns
3. Validates syntax after changes
4. Generates detailed migration report
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import ast


class ImportMigrator:
    """Automated import path migration tool."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes = []
        self.errors = []
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """Build regex patterns for all known import variations."""
        # All the patterns we've seen in the wild
        old_patterns = [
            r"from\s+src\.base_agent\s+import",
            r"from\s+library\.core\.base_agent_v1\s+import",
            r"from\s+library\.core\.base_agent\s+import",
            r"from\s+core\.base_agent_v1\s+import",
            r"from\s+agents\.base_agent\s+import",
            r"from\s+src\.agents\.base_agent\s+import",
            r"from\s+app\.agents\.base_agent\s+import",
            r"from\s+autonomous_ecosystem\.library\.core\.enhanced_base_agent\s+import\s+EnhancedBaseAgent",
            r"from\s+\.base_agent\s+import",  # Relative import
            r"from\s+\.base_agent_v1\s+import",  # Relative import
        ]

        # Compile patterns
        patterns = []
        for pattern in old_patterns:
            compiled = re.compile(pattern)
            patterns.append((compiled, pattern))

        return patterns

    def scan_file(self, filepath: Path) -> List[str]:
        """Scan a file for import patterns that need updating."""
        try:
            content = filepath.read_text(encoding="utf-8")
            matches = []

            for pattern, pattern_str in self.patterns:
                if pattern.search(content):
                    matches.append(pattern_str)

            return matches
        except Exception as e:
            self.errors.append(f"Error reading {filepath}: {e}")
            return []

    def fix_imports(self, filepath: Path, dry_run: bool = False) -> bool:
        """Fix imports in a single file."""
        try:
            content = filepath.read_text(encoding="utf-8")
            original_content = content
            modified = False

            # Pattern 1: from XXX.base_agent import BaseAgent
            content, count1 = re.subn(
                r"from\s+(src|library\.core|core|agents|src\.agents|app\.agents)\.base_agent(_v1)?\s+import\s+BaseAgent",
                "from superstandard.agents.base.base_agent import BaseAgent",
                content,
            )
            modified = modified or count1 > 0

            # Pattern 2: from XXX.enhanced_base_agent import EnhancedBaseAgent
            content, count2 = re.subn(
                r"from\s+autonomous_ecosystem\.library\.core\.enhanced_base_agent\s+import\s+EnhancedBaseAgent",
                "from superstandard.agents.base.base_agent import BaseAgent",
                content,
            )
            modified = modified or count2 > 0

            # Pattern 3: Relative imports within agents/ (convert to absolute for clarity)
            if "/agents/" in str(filepath) or "\\agents\\" in str(filepath):
                # Only fix if not in base/ itself
                if "/base/" not in str(filepath) and "\\base\\" not in str(filepath):
                    content, count3 = re.subn(
                        r"from\s+\.base_agent(_v1)?\s+import",
                        "from superstandard.agents.base.base_agent import",
                        content,
                    )
                    modified = modified or count3 > 0

            # Pattern 4: Import statements with multiple items
            content, count4 = re.subn(
                r"from\s+(src|library\.core|core|agents)\.base_agent(_v1)?\s+import\s+BaseAgent,\s*(\w+)",
                r"from superstandard.agents.base.base_agent import BaseAgent, \3",
                content,
            )
            modified = modified or count4 > 0

            if modified:
                if not dry_run:
                    # Validate syntax before writing
                    try:
                        ast.parse(content)
                        filepath.write_text(content, encoding="utf-8")
                        self.changes.append(
                            {
                                "file": str(filepath),
                                "patterns_fixed": count1 + count2 + count3 + count4,
                            }
                        )
                        return True
                    except SyntaxError as e:
                        self.errors.append(f"Syntax error in {filepath} after changes: {e}")
                        return False
                else:
                    self.changes.append(
                        {
                            "file": str(filepath),
                            "patterns_fixed": count1 + count2 + count3 + count4,
                            "dry_run": True,
                        }
                    )
                    return True

            return False

        except Exception as e:
            self.errors.append(f"Error processing {filepath}: {e}")
            return False

    def migrate_directory(self, directory: Path, dry_run: bool = False) -> Dict:
        """Migrate all Python files in a directory."""
        python_files = list(directory.rglob("*.py"))
        results = {"total": len(python_files), "modified": 0, "errors": 0}

        for filepath in python_files:
            # Skip __pycache__ and venv directories
            if "__pycache__" in str(filepath) or "venv" in str(filepath):
                continue

            if self.fix_imports(filepath, dry_run):
                results["modified"] += 1

        results["errors"] = len(self.errors)
        return results

    def generate_report(self) -> str:
        """Generate migration report."""
        report = []
        report.append("=" * 80)
        report.append("IMPORT PATH MIGRATION REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Total files modified: {len(self.changes)}")
        report.append(f"Total errors: {len(self.errors)}")
        report.append("")

        if self.changes:
            report.append("MODIFIED FILES:")
            report.append("-" * 80)
            for change in self.changes[:50]:  # Show first 50
                dry_run_marker = " [DRY RUN]" if change.get("dry_run") else ""
                report.append(
                    f"  {change['file']} - {change['patterns_fixed']} patterns fixed{dry_run_marker}"
                )
            if len(self.changes) > 50:
                report.append(f"  ... and {len(self.changes) - 50} more files")
            report.append("")

        if self.errors:
            report.append("ERRORS:")
            report.append("-" * 80)
            for error in self.errors[:20]:  # Show first 20 errors
                report.append(f"  {error}")
            if len(self.errors) > 20:
                report.append(f"  ... and {len(self.errors) - 20} more errors")
            report.append("")

        report.append("=" * 80)
        report.append("MIGRATION COMPLETE")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate BaseAgent imports to canonical path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to project root (default: current directory)",
    )

    args = parser.parse_args()

    project_root = Path(args.path).resolve()
    print(f"Project root: {project_root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print("")

    migrator = ImportMigrator(project_root)

    # Migrate both old and new structures
    directories = [
        project_root / "src" / "superstandard" / "agents",
        project_root / "agents" / "consolidated" / "py",
    ]

    for directory in directories:
        if directory.exists():
            print(f"Processing: {directory}")
            results = migrator.migrate_directory(directory, args.dry_run)
            print(f"  Total files: {results['total']}")
            print(f"  Modified: {results['modified']}")
            print(f"  Errors: {results['errors']}")
            print("")

    # Generate and print report
    report = migrator.generate_report()
    print(report)

    # Save report to file
    report_path = project_root / "import_migration_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {report_path}")

    return 0 if len(migrator.errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
