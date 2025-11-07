"""
Python-First Migration Script

Transforms SuperStandard from mixed Rust/Python to clean Python-First architecture.

Phase 1: Directory restructuring
Phase 2: Move protocols
Phase 3: Organize agents by category
Phase 4: Update imports
Phase 5: Create __init__.py files

Usage:
    python scripts/python_first_migration.py --execute
    python scripts/python_first_migration.py --dry-run  # Preview changes
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List
import re
import sys


class PythonFirstMigration:
    def __init__(self, base_path: Path, dry_run: bool = True):
        self.base_path = base_path
        self.dry_run = dry_run
        self.src_path = base_path / "src" / "superstandard"
        self.old_agents_path = base_path / "agents" / "consolidated" / "py"
        self.catalog_path = base_path / "AGENT_CATALOG.json"

        # Category structure (from our analysis)
        self.categories = {
            "base": "Base agent implementations",
            "infrastructure": "Registry, factory, template agents",
            "coordination": "Orchestration and workflow management",
            "trading": "Trading and market strategies",
            "api": "Service integrations and endpoints",
            "testing": "QA, validation, verification",
            "analysis": "Data analysis and insights",
            "data": "Data collection and processing",
            "monitoring": "System monitoring and observability",
            "security": "Auth, compliance, audit",
            "blockchain": "Blockchain and crypto operations",
            "finance": "Financial operations",
            "communication": "Messaging and notifications",
            "devops": "Deployment and CI/CD",
            "business": "Sales, marketing, CRM",
            "research": "Research and investigation",
            "operations": "Process execution",
            "ml_ai": "Machine learning and AI",
            "reporting": "Dashboards and visualization",
            "integration": "Connectors and adapters",
            "backend": "Backend services",
            "ui": "UI/UX and frontend",
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with level"""
        prefix = "[DRY-RUN]" if self.dry_run else "[EXECUTE]"
        print(f"{prefix} [{level}] {message}")

    def load_catalog(self) -> Dict:
        """Load agent catalog"""
        if not self.catalog_path.exists():
            self.log("AGENT_CATALOG.json not found - run analyze_agents.py first", "ERROR")
            sys.exit(1)

        with open(self.catalog_path) as f:
            return json.load(f)

    def phase1_create_structure(self):
        """Phase 1: Create new directory structure"""
        self.log("=" * 70)
        self.log("PHASE 1: Creating Python-First Directory Structure")
        self.log("=" * 70)

        # Create category directories under src/superstandard/agents/
        agents_base = self.src_path / "agents"

        for category, description in self.categories.items():
            category_path = agents_base / category
            if not self.dry_run:
                category_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created: {category_path.relative_to(self.base_path)}")

        # Create protocols directory
        protocols_path = self.src_path / "protocols"
        if not self.dry_run:
            protocols_path.mkdir(parents=True, exist_ok=True)
        self.log(f"Created: {protocols_path.relative_to(self.base_path)}")

        self.log(f"[OK] Phase 1 Complete: Created {len(self.categories)} category directories")

    def phase2_move_protocols(self):
        """Phase 2: Move Python protocols from Rust crate to proper location"""
        self.log("=" * 70)
        self.log("PHASE 2: Moving Python Protocol Implementations")
        self.log("=" * 70)

        rust_protocols = self.base_path / "crates" / "agentic_protocols" / "python"
        target_protocols = self.src_path / "protocols"

        if not rust_protocols.exists():
            self.log("No Python protocols found in Rust crate", "WARNING")
            return

        for py_file in rust_protocols.glob("*.py"):
            target_file = target_protocols / py_file.name
            if not self.dry_run:
                shutil.copy2(py_file, target_file)
            self.log(f"Moved: {py_file.name} -> protocols/{py_file.name}")

        self.log("[OK] Phase 2 Complete: Moved protocol implementations")

    def phase3_organize_agents(self):
        """Phase 3: Organize agents by category"""
        self.log("=" * 70)
        self.log("PHASE 3: Organizing Agents by Category")
        self.log("=" * 70)

        catalog = self.load_catalog()
        moved_count = 0

        for agent in catalog["agents"]:
            if agent["type"] != "python":
                continue

            source_path = self.base_path / agent["file"]
            if not source_path.exists():
                continue

            # Determine target category
            category = agent.get("category", "general")
            if category == "general":
                category = "infrastructure"  # Default for uncategorized
            elif category not in self.categories:
                self.log(f"Unknown category '{category}' for {agent['name']}", "WARNING")
                category = "infrastructure"

            # Special case: base_agent_v1.py -> base/base_agent.py
            filename = source_path.name
            if filename == "base_agent_v1.py":
                category = "base"
                filename = "base_agent.py"  # Rename to canonical name

            target_path = self.src_path / "agents" / category / filename

            if not self.dry_run:
                shutil.copy2(source_path, target_path)

            self.log(f"Organized: {agent['name']} -> agents/{category}/{filename}")
            moved_count += 1

        self.log(f"[OK] Phase 3 Complete: Organized {moved_count} agents into categories")

    def phase4_create_init_files(self):
        """Phase 4: Create __init__.py files for all packages"""
        self.log("=" * 70)
        self.log("PHASE 4: Creating Package __init__.py Files")
        self.log("=" * 70)

        # Root package
        self._create_init(self.src_path, "SuperStandard - Production Multi-Agent Platform")

        # Agents package
        agents_path = self.src_path / "agents"
        self._create_init(agents_path, "Agent implementations organized by category")

        # Category packages
        for category, description in self.categories.items():
            category_path = agents_path / category
            self._create_init(category_path, description)

        # Protocols package
        protocols_path = self.src_path / "protocols"
        self._create_init(protocols_path, "Protocol implementations (ANP, ACP, BAP)")

        self.log("[OK] Phase 4 Complete: Created package structure")

    def _create_init(self, path: Path, docstring: str):
        """Create __init__.py with docstring"""
        init_file = path / "__init__.py"

        if not self.dry_run:
            with open(init_file, "w") as f:
                f.write(f'"""{docstring}"""\n')

        self.log(f"Created: {init_file.relative_to(self.base_path)}")

    def phase5_create_manifests(self):
        """Phase 5: Create category manifests"""
        self.log("=" * 70)
        self.log("PHASE 5: Creating Category Manifests")
        self.log("=" * 70)

        catalog = self.load_catalog()
        category_agents = {}

        # Group agents by category
        for agent in catalog["agents"]:
            if agent["type"] != "python":
                continue
            category = agent.get("category", "infrastructure")
            if category not in category_agents:
                category_agents[category] = []
            category_agents[category].append(
                {
                    "name": agent["name"],
                    "file": agent["file"],
                    "description": agent.get("description", ""),
                }
            )

        # Create manifest for each category
        for category, agents in category_agents.items():
            if category not in self.categories:
                continue

            manifest_path = self.src_path / "agents" / category / "MANIFEST.md"

            if not self.dry_run:
                with open(manifest_path, "w", encoding="utf-8") as f:
                    f.write(f"# {category.title()} Agents\n\n")
                    f.write(f"{self.categories[category]}\n\n")
                    f.write(f"**Total Agents**: {len(agents)}\n\n")
                    f.write("## Agents in this Category\n\n")
                    for agent in sorted(agents, key=lambda x: x["name"]):
                        desc = agent.get("description", "No description available")
                        desc_preview = desc[:100] if len(desc) > 100 else desc
                        f.write(f"- **{agent['name']}**: {desc_preview}...\n")

            self.log(f"Created: agents/{category}/MANIFEST.md ({len(agents)} agents)")

        self.log("[OK] Phase 5 Complete: Created category manifests")

    def run(self):
        """Execute all phases"""
        mode = "DRY RUN" if self.dry_run else "EXECUTION"
        self.log(f"\n{'='*70}")
        self.log(f"PYTHON-FIRST MIGRATION - {mode} MODE")
        self.log(f"{'='*70}\n")

        self.phase1_create_structure()
        print()
        self.phase2_move_protocols()
        print()
        self.phase3_organize_agents()
        print()
        self.phase4_create_init_files()
        print()
        self.phase5_create_manifests()

        self.log(f"\n{'='*70}")
        if self.dry_run:
            self.log("DRY RUN COMPLETE - No files were modified")
            self.log("Run with --execute to apply changes")
        else:
            self.log("MIGRATION COMPLETE!")
            self.log("Next steps:")
            self.log("1. Update imports in all agents")
            self.log("2. Archive old agents/consolidated directory")
            self.log("3. Archive Rust crates")
        self.log(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Python-First Migration Tool")
    parser.add_argument(
        "--execute", action="store_true", help="Execute migration (default is dry-run)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    args = parser.parse_args()

    # Default to dry-run unless --execute specified
    dry_run = not args.execute or args.dry_run

    base_path = Path(__file__).parent.parent
    migration = PythonFirstMigration(base_path, dry_run=dry_run)
    migration.run()


if __name__ == "__main__":
    main()
