"""
Agent Analysis & Registry Generator

Analyzes all agents in the consolidated directory and generates:
1. Master agent catalog (JSON)
2. Agent classification taxonomy
3. Duplicate detection report
4. Markdown catalog for documentation

Usage:
    python scripts/analyze_agents.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import ast


class AgentAnalyzer:
    """Analyzes agent files and extracts metadata"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.agents = []
        self.categories = defaultdict(list)
        self.duplicates = defaultdict(list)
        self.stats = {
            "total_files": 0,
            "python_agents": 0,
            "markdown_specs": 0,
            "rust_agents": 0,
            "protocols_found": set(),
            "base_classes": defaultdict(int)
        }

    def analyze_python_agent(self, file_path: Path) -> Dict:
        """Extract metadata from Python agent file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract class name
            class_match = re.search(r'class\s+(\w+Agent\w*)', content)
            class_name = class_match.group(1) if class_match else file_path.stem

            # Extract docstring
            doc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
            description = doc_match.group(1).strip() if doc_match else "No description"

            # Extract base classes/protocols
            base_classes = []
            if class_match:
                full_class = re.search(r'class\s+\w+\(([^)]+)\)', content)
                if full_class:
                    base_classes = [b.strip() for b in full_class.group(1).split(',')]

            # Extract capabilities/methods
            methods = re.findall(r'def\s+(\w+)\(', content)
            capabilities = [m for m in methods if not m.startswith('_')]

            # Detect protocol usage
            protocols = []
            if 'ANP' in content or 'AgentNetworkProtocol' in content:
                protocols.append('ANP')
            if 'ACP' in content or 'CoordinationProtocol' in content:
                protocols.append('ACP')
            if 'BAP' in content or 'BlockchainProtocol' in content:
                protocols.append('BAP')

            # Categorize by file name patterns
            category = self._categorize_agent(file_path.stem)

            return {
                "name": class_name,
                "file": str(file_path.relative_to(self.base_path)),
                "type": "python",
                "category": category,
                "description": description[:200],
                "base_classes": base_classes,
                "capabilities": capabilities[:10],
                "protocols": protocols,
                "line_count": len(content.split('\n'))
            }

        except Exception as e:
            return {
                "name": file_path.stem,
                "file": str(file_path.relative_to(self.base_path)),
                "type": "python",
                "category": "unknown",
                "description": f"Error analyzing: {str(e)}",
                "error": True
            }

    def analyze_markdown_spec(self, file_path: Path) -> Dict:
        """Extract metadata from Markdown specification"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract title (first # heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem

            # Extract description (first paragraph after title)
            desc_match = re.search(r'^#.+?\n\n(.+?)(?:\n\n|\Z)', content, re.DOTALL | re.MULTILINE)
            description = desc_match.group(1).strip() if desc_match else "No description"

            category = self._categorize_agent(file_path.stem)

            return {
                "name": title,
                "file": str(file_path.relative_to(self.base_path)),
                "type": "markdown",
                "category": category,
                "description": description[:200],
                "line_count": len(content.split('\n'))
            }

        except Exception as e:
            return {
                "name": file_path.stem,
                "file": str(file_path.relative_to(self.base_path)),
                "type": "markdown",
                "category": "unknown",
                "description": f"Error analyzing: {str(e)}",
                "error": True
            }

    def _categorize_agent(self, name: str) -> str:
        """Categorize agent by name patterns"""
        name_lower = name.lower()

        categories_map = {
            "infrastructure": ["base_agent", "baseagent", "registry", "factory", "template", "generator", "core", "foundation"],
            "data": ["data", "collector", "scraper", "extractor", "parser", "ingestion", "etl", "pipeline"],
            "analysis": ["analyst", "analyzer", "analysis", "insight", "metric", "analytics", "anomaly", "detection", "statistics", "sentiment"],
            "coordination": ["coordinator", "orchestrator", "manager", "scheduler", "workflow", "task", "job"],
            "communication": ["messenger", "notifier", "reporter", "publisher", "notification", "alert", "email"],
            "monitoring": ["monitor", "tracker", "observer", "watcher", "apm", "aiops", "observability", "telemetry", "logging"],
            "testing": ["test", "validator", "verifier", "qa", "quality", "validation", "verification"],
            "security": ["security", "auth", "compliance", "audit", "encryption", "permission", "access"],
            "blockchain": ["blockchain", "wallet", "nft", "token", "contract", "crypto", "defi", "trading", "arbitrage"],
            "finance": ["financial", "finance", "revenue", "profit", "cost", "budget", "invoice", "payment", "transaction"],
            "trading": ["trading", "trader", "trade", "market", "price", "portfolio", "risk", "strategy", "autonomous_trading", "autonomous_risk", "autonomous_strategy"],
            "api": ["api", "endpoint", "service", "client", "rest", "graphql", "http"],
            "ui": ["ui", "ux", "frontend", "interface", "design", "accessibility", "usability"],
            "backend": ["backend", "server", "database", "storage", "db"],
            "devops": ["deploy", "deployment", "ci", "cd", "build", "docker", "kubernetes", "infrastructure", "automation"],
            "business": ["business", "sales", "marketing", "customer", "crm", "relationship", "lead"],
            "research": ["research", "investigation", "discovery", "exploration", "competitive", "market_research"],
            "operations": ["operation", "ops", "process", "execution", "runner", "executor"],
            "ml_ai": ["ml", "machine_learning", "ai", "model", "training", "prediction", "neural", "deep_learning"],
            "reporting": ["report", "dashboard", "visualization", "chart", "graph", "presentation"],
            "integration": ["integration", "connector", "adapter", "bridge", "sync", "webhook"]
        }

        for category, keywords in categories_map.items():
            if any(kw in name_lower for kw in keywords):
                return category

        return "general"

    def analyze_all(self):
        """Analyze all agent files in consolidated directory"""
        print("Analyzing consolidated agents...")

        # Analyze Python files
        py_dir = self.base_path / "agents" / "consolidated" / "py"
        if py_dir.exists():
            for file_path in py_dir.glob("*.py"):
                agent_data = self.analyze_python_agent(file_path)
                self.agents.append(agent_data)
                self.categories[agent_data["category"]].append(agent_data["name"])
                self.stats["python_agents"] += 1
                self.stats["total_files"] += 1

                # Track base classes
                for base in agent_data.get("base_classes", []):
                    self.stats["base_classes"][base] += 1

                # Track protocols
                for protocol in agent_data.get("protocols", []):
                    self.stats["protocols_found"].add(protocol)

        # Analyze Markdown files
        md_dir = self.base_path / "agents" / "consolidated" / "md"
        if md_dir.exists():
            for file_path in md_dir.glob("*.md"):
                agent_data = self.analyze_markdown_spec(file_path)
                self.agents.append(agent_data)
                self.categories[agent_data["category"]].append(agent_data["name"])
                self.stats["markdown_specs"] += 1
                self.stats["total_files"] += 1

        print(f"Analyzed {self.stats['total_files']} files")
        print(f"  - {self.stats['python_agents']} Python agents")
        print(f"  - {self.stats['markdown_specs']} Markdown specifications")

    def detect_duplicates(self):
        """Detect potential duplicate agents by name similarity"""
        from difflib import SequenceMatcher

        names = [a["name"] for a in self.agents]

        for i, name1 in enumerate(names):
            for j, name2 in enumerate(names[i+1:], i+1):
                similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                if similarity > 0.85:  # 85% similar
                    self.duplicates[name1].append(name2)

    def generate_json_catalog(self, output_path: str):
        """Generate JSON catalog"""
        catalog = {
            "metadata": {
                "generated": str(Path.cwd()),
                "total_agents": len(self.agents),
                "categories": dict(self.categories),
                "statistics": {
                    **self.stats,
                    "protocols_found": list(self.stats["protocols_found"]),
                    "base_classes": dict(self.stats["base_classes"])
                }
            },
            "agents": sorted(self.agents, key=lambda x: x["name"])
        }

        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)

        print(f"\nJSON catalog saved to: {output_path}")

    def generate_markdown_catalog(self, output_path: str):
        """Generate Markdown catalog"""
        lines = [
            "# Agent Catalog - SuperStandard v1.0",
            "",
            f"**Total Agents:** {len(self.agents)}",
            f"**Python Implementations:** {self.stats['python_agents']}",
            f"**Markdown Specifications:** {self.stats['markdown_specs']}",
            "",
            "## Categories",
            ""
        ]

        # Category breakdown
        for category, agents in sorted(self.categories.items()):
            lines.append(f"### {category.title()} ({len(agents)} agents)")
            lines.append("")
            for agent in sorted(agents):
                agent_data = next(a for a in self.agents if a["name"] == agent)
                lines.append(f"- **{agent}**")
                lines.append(f"  - File: `{agent_data['file']}`")
                lines.append(f"  - Type: {agent_data['type']}")
                if "protocols" in agent_data and agent_data["protocols"]:
                    lines.append(f"  - Protocols: {', '.join(agent_data['protocols'])}")
                lines.append("")

        # Duplicate detection
        if self.duplicates:
            lines.append("## Potential Duplicates")
            lines.append("")
            lines.append("Agents with similar names (may need consolidation):")
            lines.append("")
            for name, similars in self.duplicates.items():
                lines.append(f"- **{name}** similar to: {', '.join(similars)}")
            lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Files:** {self.stats['total_files']}")
        lines.append(f"- **Python Agents:** {self.stats['python_agents']}")
        lines.append(f"- **Markdown Specs:** {self.stats['markdown_specs']}")
        lines.append(f"- **Protocols Used:** {', '.join(sorted(self.stats['protocols_found']))}")
        lines.append("")

        if self.stats["base_classes"]:
            lines.append("### Base Classes")
            lines.append("")
            for base_class, count in sorted(self.stats["base_classes"].items(), key=lambda x: -x[1]):
                lines.append(f"- **{base_class}:** {count} agents")
            lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"Markdown catalog saved to: {output_path}")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("SuperStandard Agent Analysis & Registry Generator")
    print("="*70 + "\n")

    base_path = Path(__file__).parent.parent
    analyzer = AgentAnalyzer(base_path)

    # Analyze all agents
    analyzer.analyze_all()

    # Detect duplicates
    print("\nDetecting potential duplicates...")
    analyzer.detect_duplicates()
    if analyzer.duplicates:
        print(f"Found {len(analyzer.duplicates)} potential duplicate groups")

    # Generate catalogs
    print("\nGenerating catalogs...")
    analyzer.generate_json_catalog(base_path / "AGENT_CATALOG.json")
    analyzer.generate_markdown_catalog(base_path / "AGENT_CATALOG.md")

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    print(f"\nCatalog files created:")
    print("  - AGENT_CATALOG.json (machine-readable)")
    print("  - AGENT_CATALOG.md (human-readable)")


if __name__ == "__main__":
    main()
