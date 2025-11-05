#!/usr/bin/env python3
"""
Comprehensive Agent Audit Script
Discovers all agent classes in the codebase and compares them against the registered agents.
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import requests

class AgentAuditor:
    """Audits all agents in the codebase"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.discovered_agents: List[Dict[str, Any]] = []
        self.registered_agents: List[Dict[str, Any]] = []
        self.agent_classes: Set[str] = set()

    def discover_agent_classes(self, file_path: Path) -> List[Dict[str, Any]]:
        """Discover agent classes in a Python file using AST parsing"""
        agents = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's an agent class
                    is_agent = False
                    bases = []

                    # Check base classes
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                            if 'Agent' in base.id or 'agent' in base.id.lower():
                                is_agent = True
                        elif isinstance(base, ast.Attribute):
                            bases.append(base.attr)
                            if 'Agent' in base.attr or 'agent' in base.attr.lower():
                                is_agent = True

                    # Also check if class name suggests it's an agent
                    if 'Agent' in node.name or 'agent' in node.name.lower():
                        is_agent = True

                    if is_agent:
                        # Extract metadata from class
                        agent_info = {
                            'class_name': node.name,
                            'file_path': str(file_path.relative_to(self.base_dir)),
                            'bases': bases,
                            'methods': [],
                            'attributes': {}
                        }

                        # Extract methods and attributes
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                agent_info['methods'].append(item.name)
                            elif isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        try:
                                            if isinstance(item.value, ast.Constant):
                                                agent_info['attributes'][target.id] = item.value.value
                                        except:
                                            pass

                        # Extract docstring
                        docstring = ast.get_docstring(node)
                        if docstring:
                            agent_info['description'] = docstring.strip()[:200]

                        agents.append(agent_info)
                        self.agent_classes.add(node.name)

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return agents

    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan a directory for agent files"""
        agents = []
        dir_path = self.base_dir / directory

        if not dir_path.exists():
            return agents

        for file_path in dir_path.rglob("*.py"):
            if file_path.name != "__init__.py":
                file_agents = self.discover_agent_classes(file_path)
                agents.extend(file_agents)

        return agents

    def get_registered_agents(self) -> List[Dict[str, Any]]:
        """Get list of registered agents from API"""
        try:
            response = requests.get("http://localhost:8000/api/v1/agent-library")
            if response.status_code == 200:
                data = response.json()
                return data.get('agents', [])
        except Exception as e:
            print(f"Error fetching registered agents: {e}")

        return []

    def perform_audit(self) -> Dict[str, Any]:
        """Perform comprehensive agent audit"""
        print("Starting comprehensive agent audit...")

        # Scan all agent directories
        directories_to_scan = [
            "app/agents",
            "app/technical_debt_management",
            "app/a2a_communication",
        ]

        print("\n1. Discovering agents in codebase...")
        for directory in directories_to_scan:
            print(f"   Scanning: {directory}")
            agents = self.scan_directory(directory)
            self.discovered_agents.extend(agents)

        print(f"\n   ✓ Discovered {len(self.discovered_agents)} agent classes")
        print(f"   ✓ Unique class names: {len(self.agent_classes)}")

        # Get registered agents
        print("\n2. Fetching registered agents from API...")
        self.registered_agents = self.get_registered_agents()
        print(f"   ✓ Found {len(self.registered_agents)} registered agents")

        # Compare and identify missing agents
        print("\n3. Comparing discovered vs registered agents...")
        registered_ids = {agent['id'] for agent in self.registered_agents}
        registered_names = {agent['name'].lower() for agent in self.registered_agents}
        registered_files = {agent.get('file_path', '').lower() for agent in self.registered_agents}

        missing_agents = []
        for agent in self.discovered_agents:
            # Check if agent is registered by various criteria
            class_name_lower = agent['class_name'].lower()
            file_path_lower = agent['file_path'].lower()

            # Generate potential agent ID
            potential_id = class_name_lower.replace('agent', '').replace('_', '')

            # Check various matching criteria
            is_registered = (
                potential_id in {rid.lower() for rid in registered_ids} or
                class_name_lower in registered_names or
                any(class_name_lower in rname for rname in registered_names) or
                any(file_path_lower in rf for rf in registered_files)
            )

            if not is_registered:
                missing_agents.append(agent)

        print(f"   ✓ Found {len(missing_agents)} potentially unregistered agents")

        # Generate report
        report = {
            'summary': {
                'discovered_agents': len(self.discovered_agents),
                'unique_classes': len(self.agent_classes),
                'registered_agents': len(self.registered_agents),
                'potentially_missing': len(missing_agents),
                'registration_rate': f"{((len(self.registered_agents) / len(self.discovered_agents)) * 100):.1f}%" if self.discovered_agents else "N/A"
            },
            'discovered_agents': self.discovered_agents,
            'registered_agents': self.registered_agents,
            'missing_agents': missing_agents,
            'agent_classes': list(self.agent_classes)
        }

        return report

    def generate_report_file(self, report: Dict[str, Any]):
        """Generate comprehensive audit report"""
        output_file = self.base_dir / "AGENT_AUDIT_REPORT.md"

        with open(output_file, 'w') as f:
            f.write("# Comprehensive Agent Audit Report\n\n")
            f.write(f"**Generated:** October 17, 2025\n\n")

            # Summary
            f.write("## Executive Summary\n\n")
            summary = report['summary']
            f.write(f"- **Discovered Agent Classes:** {summary['discovered_agents']}\n")
            f.write(f"- **Unique Class Names:** {summary['unique_classes']}\n")
            f.write(f"- **Registered in Library:** {summary['registered_agents']}\n")
            f.write(f"- **Potentially Missing:** {summary['potentially_missing']}\n")
            f.write(f"- **Registration Rate:** {summary['registration_rate']}\n\n")

            # Missing Agents
            if report['missing_agents']:
                f.write("## Unregistered Agents\n\n")
                f.write("The following agent classes were discovered but are not registered:\n\n")

                for agent in report['missing_agents']:
                    f.write(f"### {agent['class_name']}\n\n")
                    f.write(f"- **File:** `{agent['file_path']}`\n")
                    if agent.get('description'):
                        f.write(f"- **Description:** {agent['description']}\n")
                    if agent['bases']:
                        f.write(f"- **Base Classes:** {', '.join(agent['bases'])}\n")
                    if agent['methods']:
                        key_methods = [m for m in agent['methods'] if not m.startswith('_')][:5]
                        f.write(f"- **Key Methods:** {', '.join(key_methods)}\n")
                    f.write("\n")

            # All Discovered Agents by Category
            f.write("## All Discovered Agents by Directory\n\n")

            # Group by directory
            by_directory = {}
            for agent in report['discovered_agents']:
                dir_name = str(Path(agent['file_path']).parent)
                if dir_name not in by_directory:
                    by_directory[dir_name] = []
                by_directory[dir_name].append(agent)

            for directory, agents in sorted(by_directory.items()):
                f.write(f"### {directory}\n\n")
                for agent in agents:
                    f.write(f"- **{agent['class_name']}** (`{Path(agent['file_path']).name}`)\n")
                f.write("\n")

            # Registered Agents
            f.write("## Currently Registered Agents\n\n")
            f.write(f"Total: {len(report['registered_agents'])} agents\n\n")

            # Group by category
            by_category = {}
            for agent in report['registered_agents']:
                category = agent.get('category', 'unknown')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(agent)

            for category, agents in sorted(by_category.items()):
                f.write(f"### {category.upper().replace('_', ' ')}\n\n")
                for agent in agents:
                    status = agent.get('status', 'unknown')
                    f.write(f"- **{agent['name']}** (`{agent['id']}`) - {status}\n")
                f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            if report['missing_agents']:
                f.write("1. **Register Missing Agents:** Review and register the identified unregistered agents\n")
                f.write("2. **Categorize Agents:** Assign appropriate categories (CORE_UTILITY, APQC_FRAMEWORK, etc.)\n")
                f.write("3. **Update Metadata:** Add descriptions, capabilities, and ROI impact for each agent\n")
                f.write("4. **Create Agent Index:** Implement quick indexing feature for architecture debt tracking\n")
                f.write("5. **Update Agent Factory:** Add agent identification function for dynamic discovery\n")
            else:
                f.write("✓ All discovered agents appear to be registered!\n")

        print(f"\n✓ Report saved to: {output_file}")

        # Also save JSON version
        json_file = self.base_dir / "AGENT_AUDIT_REPORT.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ JSON data saved to: {json_file}")

def main():
    auditor = AgentAuditor()
    report = auditor.perform_audit()
    auditor.generate_report_file(report)

    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)
    print(f"\nDiscovered: {report['summary']['discovered_agents']} agent classes")
    print(f"Registered: {report['summary']['registered_agents']} agents")
    print(f"Missing: {report['summary']['potentially_missing']} agents")
    print(f"Registration Rate: {report['summary']['registration_rate']}")
    print("\nSee AGENT_AUDIT_REPORT.md for full details.")

if __name__ == "__main__":
    main()
