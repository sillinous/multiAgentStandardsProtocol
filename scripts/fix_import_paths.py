#!/usr/bin/env python3
"""
Fix Import Paths Script

This script updates all import paths across the codebase to reflect the new
Python-First directory structure.

Old paths:
- from src.superstandard.agents.base.base_agent import BaseAgent
- from src.superstandard.agents.base.base_agent import BaseAgent
- from src.superstandard.agents.base.base_agent import EnhancedBaseAgent
- from src.superstandard.agents.base.base_agent import BaseAgent

New path:
- from src.superstandard.agents.base.base_agent import BaseAgent

Usage:
    python scripts/fix_import_paths.py --dry-run  # Preview changes
    python scripts/fix_import_paths.py --execute  # Apply changes
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

# Import patterns to replace
IMPORT_PATTERNS = [
    # BaseAgent imports
    (r"from\s+agents\.base_agent\s+import", "from src.superstandard.agents.base.base_agent import"),
    (
        r"from\s+agents\.consolidated\.py\.base_agent_v1\s+import",
        "from src.superstandard.agents.base.base_agent import",
    ),
    (
        r"from\s+library\.core\.base_agent\s+import",
        "from src.superstandard.agents.base.base_agent import",
    ),
    (
        r"from\s+autonomous_ecosystem\.library\.core\.enhanced_base_agent\s+import",
        "from src.superstandard.agents.base.base_agent import",
    ),
    (r"from\s+src\.base_agent\s+import", "from src.superstandard.agents.base.base_agent import"),
    # Protocol imports (if any old ones remain)
    (
        r"from\s+crates\.agentic_protocols\.python\.anp_implementation\s+import",
        "from src.superstandard.protocols.anp_implementation import",
    ),
    (
        r"from\s+crates\.agentic_protocols\.python\.acp_implementation\s+import",
        "from src.superstandard.protocols.acp_implementation import",
    ),
    # Relative imports that need to be updated
    (r"from\s+\.base_agent\s+import", "from src.superstandard.agents.base.base_agent import"),
    (r"from\s+\.base_agent_v1\s+import", "from src.superstandard.agents.base.base_agent import"),
]

# Additional patterns for specific imports
CLASS_SPECIFIC_PATTERNS = [
    # Replace specific BaseAgent class references
    (
        r"from\s+agents\.base_agent\s+import\s+BaseAgent",
        "from src.superstandard.agents.base.base_agent import BaseAgent",
    ),
    (
        r"from\s+library\.core\.base_agent\s+import\s+BaseAgent",
        "from src.superstandard.agents.base.base_agent import BaseAgent",
    ),
]


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the directory tree."""
    python_files = []
    exclude_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        "env",
        "archive",
        ".snapshots",
    }

    for path in root_dir.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        python_files.append(path)

    return python_files


def analyze_imports(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Analyze a file and return lines that need import updates.
    Returns: List of (line_number, original_line, suggested_replacement)
    """
    changes = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return changes

    for line_num, line in enumerate(lines, 1):
        original_line = line
        updated_line = line

        # Check each pattern
        for pattern, replacement in IMPORT_PATTERNS:
            if re.search(pattern, line):
                updated_line = re.sub(pattern, replacement, updated_line)

        # If line changed, record it
        if updated_line != original_line:
            changes.append((line_num, original_line.strip(), updated_line.strip()))

    return changes


def update_file(file_path: Path, dry_run: bool = True) -> int:
    """
    Update import paths in a file.
    Returns: Number of lines changed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return 0

    original_content = content
    changes_made = 0

    # Apply all patterns
    for pattern, replacement in IMPORT_PATTERNS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes_made += 1
            content = new_content

    # If content changed and not dry run, write it back
    if content != original_content:
        if not dry_run:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return changes_made
            except Exception as e:
                print(f"❌ Error writing {file_path}: {e}")
                return 0
        else:
            return changes_made

    return 0


def main():
    parser = argparse.ArgumentParser(description="Fix import paths in Python files")
    parser.add_argument(
        "--execute", action="store_true", help="Execute changes (default is dry-run)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Root directory to search (default: current directory)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Default to dry-run if neither flag is specified
    dry_run = not args.execute or args.dry_run

    root_dir = Path(args.path).resolve()

    print("=" * 70)
    print("SuperStandard Import Path Fixer")
    print("=" * 70)
    print(f"\nMode: {'DRY RUN (preview only)' if dry_run else 'EXECUTE (making changes)'}")
    print(f"Root directory: {root_dir}\n")

    # Find all Python files
    print("Finding Python files...")
    python_files = find_python_files(root_dir)
    print(f"Found {len(python_files)} Python files\n")

    # Analyze and update files
    files_with_changes = 0
    total_changes = 0

    print("Analyzing imports...")
    print("-" * 70)

    for file_path in python_files:
        # Analyze the file first
        changes = analyze_imports(file_path)

        if changes:
            files_with_changes += 1
            relative_path = file_path.relative_to(root_dir)

            print(f"\n📄 {relative_path}")
            print(f"   {len(changes)} import(s) to update:")

            if args.verbose:
                for line_num, original, updated in changes[:5]:  # Show max 5 per file
                    print(f"   Line {line_num}:")
                    print(f"     OLD: {original}")
                    print(f"     NEW: {updated}")
                if len(changes) > 5:
                    print(f"   ... and {len(changes) - 5} more")

            # Update the file
            num_changes = update_file(file_path, dry_run)
            total_changes += num_changes

            if not dry_run:
                print(f"   ✅ Updated {num_changes} import(s)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files scanned: {len(python_files)}")
    print(f"Files with changes: {files_with_changes}")
    print(f"Total import statements updated: {total_changes}")

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files were modified")
        print("Run with --execute to apply changes")
    else:
        print("\n✅ Changes applied successfully!")

    print("=" * 70)

    return 0 if total_changes == 0 else 1


if __name__ == "__main__":
    exit(main())
