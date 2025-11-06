"""
Comprehensive Agent Scanner - Find ALL Agents

Scans entire autonomous-ecosystem directory for all agent files,
including:
- autonomous-ecosystem/agents/
- autonomous-ecosystem/library/ (all subdirectories)

Usage:
    python tools/scan_all_agents.py --export full_report.json

Version: 1.0.0
Date: 2025-10-11
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.scan_agents import AgentScanner
from library.core.agent_registry import AgentRegistry


def main():
    print("\n" + "=" * 60)
    print("Comprehensive Agent Scanner - Finding ALL Agents")
    print("=" * 60 + "\n")

    # Scan multiple directories
    directories_to_scan = [
        Path(__file__).parent.parent / "agents",
        Path(__file__).parent.parent / "library",
    ]

    all_agents = []
    registry = AgentRegistry()

    for base_dir in directories_to_scan:
        if not base_dir.exists():
            print(f"[SKIP] Directory not found: {base_dir}")
            continue

        print(f"\n[Scanning] {base_dir}")
        print("-" * 60)

        # Find all Python files recursively
        agent_files = []
        for root, dirs, files in os.walk(base_dir):
            # Skip __pycache__ and test directories
            dirs[:] = [d for d in dirs if d != "__pycache__" and "test" not in d.lower()]

            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    if "agent" in file.lower() or "Agent" in file:
                        agent_files.append(Path(root) / file)

        print(f"Found {len(agent_files)} potential agent files")

        # Analyze each file
        # Create scanner with correct base path for this directory
        scanner = AgentScanner(library_path=str(base_dir))
        for agent_file in agent_files:
            try:
                # Determine category from path
                relative_path = agent_file.relative_to(base_dir)
                if len(relative_path.parts) > 1:
                    category = relative_path.parts[0]
                else:
                    category = "root"

                agent_data = scanner.analyze_agent_file(agent_file, category)
                if agent_data:
                    all_agents.append(agent_data)
                    status = "[OK]" if agent_data["compliance_status"] == "compliant" else "[!]"
                    print(
                        f"  {status} {agent_data['agent_name']} v{agent_data['version']} ({category})"
                    )

            except Exception as e:
                print(f"  [ERROR] {agent_file.name}: {str(e)[:50]}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Total Agents Found: {len(all_agents)}")
    print(f"{'='*60}\n")

    # Count by status
    status_counts = {}
    for agent in all_agents:
        status = agent["compliance_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Compliance Breakdown:")
    for status, count in sorted(status_counts.items()):
        pct = count / len(all_agents) * 100
        print(f"  {status:25} {count:3} ({pct:5.1f}%)")

    # Register all agents
    print(f"\n{'='*60}")
    print("Registering in Database")
    print(f"{'='*60}\n")

    for agent in all_agents:
        try:
            from library.core.agent_registry import ComplianceStatus

            # Convert string status to enum
            status_str = agent["compliance_status"]
            if status_str == "compliant":
                compliance_status = ComplianceStatus.COMPLIANT
            elif status_str == "partially_compliant":
                compliance_status = ComplianceStatus.PARTIALLY_COMPLIANT
            elif status_str == "non_compliant":
                compliance_status = ComplianceStatus.NON_COMPLIANT
            else:
                compliance_status = ComplianceStatus.UNKNOWN

            agent_id = registry.register_agent(
                agent_name=agent["agent_name"],
                agent_type=agent["agent_type"],
                category=agent["category"],
                version=agent["version"],
                file_path=agent["file_path"],
                compliance_status=compliance_status,
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

            # Add non-compliant to retrofit queue
            if status_str != "compliant":
                priority = 5 if status_str == "non_compliant" else 3
                registry.add_to_retrofit_queue(agent_id, priority)

        except Exception as e:
            print(f"[ERROR] Registering {agent['agent_name']}: {str(e)[:80]}")

    print(f"\n[OK] All agents registered")

    # Generate report
    report = registry.get_compliance_report()

    print(f"\n{'='*60}")
    print("Final Compliance Report")
    print(f"{'='*60}\n")
    print(f"Total Agents: {report['overall_stats']['total_agents']}")
    print(f"Compliance Rate: {report['compliance_rate']:.1f}%")
    print(f"Compliant: {report['overall_stats']['compliant']}")
    print(f"Partially Compliant: {report['overall_stats']['partially_compliant']}")
    print(f"Non-Compliant: {report['overall_stats']['non_compliant']}")
    print(f"Pending Retrofit: {report['overall_stats']['pending_retrofit']}")

    # Export
    registry.export_to_json("full_agent_registry_report.json")
    print(f"\n[OK] Exported to: full_agent_registry_report.json")

    # Show top retrofit priorities
    retrofit_queue = registry.get_retrofit_queue(limit=20)
    if retrofit_queue:
        print(f"\n{'='*60}")
        print("Top 20 Retrofit Priorities")
        print(f"{'='*60}\n")
        for i, agent in enumerate(retrofit_queue, 1):
            print(
                f"{i:2}. [{agent['retrofit_priority']}] {agent['agent_name']:40} v{agent['version']:8} ({agent['category']})"
            )

    print(f"\n{'='*60}")
    print("Scan Complete!")
    print(f"{'='*60}\n")

    registry.close()


if __name__ == "__main__":
    main()
