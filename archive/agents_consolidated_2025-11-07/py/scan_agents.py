"""
Agent Scanner - Automatic Agent Discovery and Registration

This tool scans the agent library, discovers all agents, analyzes their
compliance status, and registers them in the Agent Registry.

Features:
- Automatic agent discovery
- Compliance analysis
- Protocol detection
- Capability extraction
- Registry population
- Compliance reporting

Usage:
    python tools/scan_agents.py
    python tools/scan_agents.py --category logistics
    python tools/scan_agents.py --export report.json

Version: 1.0.0
Date: 2025-10-11
"""

import os
import sys
import re
import ast
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.core.agent_registry import AgentRegistry, ComplianceStatus, ArchitecturalLawVersion


class AgentScanner:
    """
    Scans agent library and analyzes compliance

    Detects:
    - BaseAgent inheritance
    - ProtocolMixin usage
    - Environment configuration
    - Health check methods
    - Resource monitoring
    - Protocol support
    - Capabilities
    """

    def __init__(self, library_path: Optional[str] = None):
        """Initialize scanner"""
        if library_path is None:
            library_path = str(Path(__file__).parent.parent / "library" / "agents")

        self.library_path = Path(library_path)
        self.agents_found = []

    def scan_all_agents(self) -> List[Dict[str, Any]]:
        """
        Scan entire agent library

        Returns:
            List of agent metadata dictionaries
        """
        print(f"\n{'='*60}")
        print(f"Scanning Agent Library: {self.library_path}")
        print(f"={'='*60}\n")

        agents = []

        # Scan each category directory
        for category_dir in self.library_path.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            print(f"[Category: {category_name}]")

            # Scan Python files in category
            for agent_file in category_dir.glob("*.py"):
                if agent_file.name.startswith("__"):
                    continue

                try:
                    agent_data = self.analyze_agent_file(agent_file, category_name)
                    if agent_data:
                        agents.append(agent_data)
                        status_icon = (
                            "[OK]"
                            if agent_data["compliance_status"] == ComplianceStatus.COMPLIANT.value
                            else "[!]"
                        )
                        print(
                            f"  {status_icon} {agent_data['agent_name']} v{agent_data['version']} - {agent_data['compliance_status']}"
                        )
                except Exception as e:
                    print(f"  [ERROR] {agent_file.name}: {e}")

            print()

        print(f"{'='*60}")
        print(f"Total Agents Found: {len(agents)}")
        print(f"{'='*60}\n")

        self.agents_found = agents
        return agents

    def analyze_agent_file(self, file_path: Path, category: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single agent file

        Returns:
            Agent metadata dict or None if not a valid agent
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse as Python
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        # Find agent class
        agent_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's an agent (has Agent in name or inherits from BaseAgent)
                if "Agent" in node.name:
                    agent_class = node
                    break

        if not agent_class:
            return None

        # Extract agent metadata
        agent_name = agent_class.name
        agent_type = self._extract_agent_type(content, agent_name)
        version = self._extract_version(content)

        # Analyze compliance
        compliance_data = self._analyze_compliance(content, tree)

        # Calculate relative path from ecosystem root
        try:
            ecosystem_root = Path(__file__).parent.parent
            rel_path = str(file_path.relative_to(ecosystem_root))
        except ValueError:
            # If relative_to fails, use the absolute path
            rel_path = str(file_path)

        return {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "category": category,
            "version": version,
            "file_path": rel_path,
            "compliance_status": compliance_data["status"].value,
            "law_version": ArchitecturalLawVersion.V1_0_0.value,
            "has_protocol_mixin": compliance_data["has_protocol_mixin"],
            "has_base_agent": compliance_data["has_base_agent"],
            "has_environment_config": compliance_data["has_environment_config"],
            "has_health_check": compliance_data["has_health_check"],
            "has_resource_monitoring": compliance_data["has_resource_monitoring"],
            "protocols_supported": compliance_data["protocols"],
            "capabilities": compliance_data["capabilities"],
            "notes": compliance_data["notes"],
        }

    def _extract_agent_type(self, content: str, agent_name: str) -> str:
        """Extract agent type from content"""
        # Try to find agent_type assignment
        match = re.search(r'agent_type\s*=\s*["\'](\w+)["\']', content)
        if match:
            return match.group(1)

        # Fallback: convert class name to snake_case
        agent_type = re.sub("Agent$", "", agent_name)
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", agent_type)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _extract_version(self, content: str) -> str:
        """Extract version from content"""
        # Try VERSION constant
        match = re.search(r'VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
        if match:
            return match.group(1)

        # Try version in docstring
        match = re.search(r"Version:\s*(\d+\.\d+\.\d+)", content)
        if match:
            return match.group(1)

        return "1.0.0"  # Default

    def _analyze_compliance(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """
        Analyze agent compliance with architectural standards

        Returns:
            Dict with compliance details
        """
        compliance = {
            "has_protocol_mixin": False,
            "has_base_agent": False,
            "has_environment_config": False,
            "has_health_check": False,
            "has_resource_monitoring": False,
            "protocols": [],
            "capabilities": [],
            "notes": [],
        }

        # Check for ProtocolMixin
        if "ProtocolMixin" in content:
            compliance["has_protocol_mixin"] = True
            compliance["protocols"] = ["A2A", "A2P", "ACP", "ANP", "MCP"]

        # Check for BaseAgent
        if "BaseAgent" in content:
            compliance["has_base_agent"] = True

        # Check for environment config
        if "from_environment" in content or "os.getenv" in content:
            compliance["has_environment_config"] = True

        # Check for health check
        if "health_check" in content:
            compliance["has_health_check"] = True

        # Check for resource monitoring
        if "_get_memory_usage" in content or "psutil" in content:
            compliance["has_resource_monitoring"] = True

        # Extract capabilities
        capabilities_match = re.search(r"capabilities_list\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if capabilities_match:
            caps_str = capabilities_match.group(1)
            caps = re.findall(r'["\'](\w+)["\']', caps_str)
            compliance["capabilities"] = caps

        # Determine compliance status
        if (
            compliance["has_protocol_mixin"]
            and compliance["has_base_agent"]
            and compliance["has_environment_config"]
            and compliance["has_health_check"]
            and compliance["has_resource_monitoring"]
        ):
            status = ComplianceStatus.COMPLIANT
            compliance["notes"].append("Fully compliant with architectural standards v1.0.0")
        elif compliance["has_base_agent"]:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            compliance["notes"].append("Has BaseAgent but missing compliance features")
        else:
            status = ComplianceStatus.NON_COMPLIANT
            compliance["notes"].append("Does not meet architectural standards")

        compliance["status"] = status
        compliance["notes"] = " | ".join(compliance["notes"])

        return compliance

    def register_agents(
        self, registry: AgentRegistry, agents: Optional[List[Dict[str, Any]]] = None
    ):
        """Register all scanned agents in registry"""
        if agents is None:
            agents = self.agents_found

        print(f"\n{'='*60}")
        print("Registering Agents in Registry")
        print(f"{'='*60}\n")

        for agent in agents:
            try:
                agent_id = registry.register_agent(
                    agent_name=agent["agent_name"],
                    agent_type=agent["agent_type"],
                    category=agent["category"],
                    version=agent["version"],
                    file_path=agent["file_path"],
                    compliance_status=ComplianceStatus(agent["compliance_status"]),
                    law_version=agent["law_version"],
                    protocols_supported=agent["protocols_supported"],
                    capabilities=agent["capabilities"],
                    has_protocol_mixin=agent["has_protocol_mixin"],
                    has_base_agent=agent["has_base_agent"],
                    has_environment_config=agent["has_environment_config"],
                    has_health_check=agent["has_health_check"],
                    has_resource_monitoring=agent["has_resource_monitoring"],
                    notes=agent["notes"],
                )

                # Add non-compliant agents to retrofit queue
                if agent["compliance_status"] != ComplianceStatus.COMPLIANT.value:
                    priority = (
                        5
                        if agent["compliance_status"] == ComplianceStatus.NON_COMPLIANT.value
                        else 3
                    )
                    registry.add_to_retrofit_queue(
                        agent_id=agent_id,
                        priority=priority,
                        notes=f"Auto-added by scanner: {agent['notes']}",
                    )

                print(f"[OK] Registered: {agent['agent_name']} ({agent_id})")

            except Exception as e:
                print(f"[ERROR] Error registering {agent['agent_name']}: {e}")

        print(f"\n{'='*60}")
        print(f"Registration Complete")
        print(f"{'='*60}\n")

    def generate_report(
        self, registry: AgentRegistry, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        report = registry.get_compliance_report()

        # Add scanner-specific data
        report["agents_scanned"] = len(self.agents_found)
        report["scan_timestamp"] = report["generated_at"]

        # Group by compliance status
        by_status = {}
        for agent in self.agents_found:
            status = agent["compliance_status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(
                {
                    "name": agent["agent_name"],
                    "version": agent["version"],
                    "category": agent["category"],
                    "notes": agent["notes"],
                }
            )
        report["agents_by_status"] = by_status

        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport exported to: {output_path}")

        return report

    def print_summary(self):
        """Print scan summary"""
        if not self.agents_found:
            print("No agents found")
            return

        # Count by status
        status_counts = {}
        for agent in self.agents_found:
            status = agent["compliance_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n{'='*60}")
        print("Scan Summary")
        print(f"{'='*60}\n")
        print(f"Total Agents: {len(self.agents_found)}")
        print(f"\nBy Compliance Status:")
        for status, count in sorted(status_counts.items()):
            pct = count / len(self.agents_found) * 100
            print(f"  {status:20} {count:3} ({pct:5.1f}%)")

        # Category breakdown
        category_counts = {}
        for agent in self.agents_found:
            cat = agent["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print(f"\nBy Category:")
        for cat, count in sorted(category_counts.items()):
            print(f"  {cat:20} {count:3}")

        print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Scan agent library and register in Agent Registry"
    )
    parser.add_argument("--category", "-c", help="Scan specific category only")
    parser.add_argument("--export", "-e", help="Export report to JSON file")
    parser.add_argument(
        "--no-register", action="store_true", help="Scan only, don't register in database"
    )
    parser.add_argument("--library-path", help="Path to agent library")
    parser.add_argument("--db-path", help="Path to registry database")

    args = parser.parse_args()

    # Create scanner
    scanner = AgentScanner(library_path=args.library_path)

    # Scan agents
    agents = scanner.scan_all_agents()

    # Filter by category if specified
    if args.category:
        agents = [a for a in agents if a["category"] == args.category]
        print(f"Filtered to category: {args.category} ({len(agents)} agents)\n")

    # Print summary
    scanner.print_summary()

    # Register in database
    if not args.no_register:
        registry = AgentRegistry(db_path=args.db_path)
        scanner.register_agents(registry, agents)

        # Generate and print compliance report
        report = scanner.generate_report(registry, output_path=args.export)

        print(f"\n{'='*60}")
        print("Compliance Report")
        print(f"{'='*60}\n")
        print(f"Compliance Rate: {report['compliance_rate']:.1f}%")
        print(f"Compliant: {report['overall_stats']['compliant']}")
        print(f"Partially Compliant: {report['overall_stats']['partially_compliant']}")
        print(f"Non-Compliant: {report['overall_stats']['non_compliant']}")
        print(f"Pending Retrofit: {report['overall_stats']['pending_retrofit']}")

        # Show retrofit queue
        retrofit_queue = registry.get_retrofit_queue(limit=10)
        if retrofit_queue:
            print(f"\nRetrofit Queue (Top 10 by priority):")
            for agent in retrofit_queue:
                print(
                    f"  [{agent['retrofit_priority']}] {agent['agent_name']} v{agent['version']} - {agent['category']}"
                )

        print(f"\n{'='*60}\n")

        registry.close()
    elif args.export:
        # Export without registering
        report = {
            "scan_timestamp": agents[0]["notes"] if agents else None,
            "agents_scanned": len(agents),
            "agents": agents,
        }
        with open(args.export, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nScan results exported to: {args.export}")


if __name__ == "__main__":
    main()
