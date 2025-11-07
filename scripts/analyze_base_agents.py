"""
BaseAgent Analysis and Consolidation Tool

Analyzes all BaseAgent implementations and recommends consolidation strategy.

Usage:
    python scripts/analyze_base_agents.py
"""

import os
from pathlib import Path
import re


class BaseAgentAnalyzer:
    """Analyzes BaseAgent implementations"""

    def __init__(self, agents_dir: str):
        self.agents_dir = Path(agents_dir)
        self.base_agents = []

    def find_base_agents(self):
        """Find all files containing BaseAgent"""
        print("Searching for BaseAgent implementations...")

        py_dir = self.agents_dir / "py"
        if not py_dir.exists():
            print(f"Error: {py_dir} does not exist")
            return

        # Find files with "base_agent" in name
        for file in py_dir.glob("*base_agent*.py"):
            self.analyze_file(file)

        # Find files that define BaseAgent class
        for file in py_dir.glob("*.py"):
            if "base_agent" not in file.name.lower():
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if re.search(r"^class\s+BaseAgent", content, re.MULTILINE):
                            self.analyze_file(file)
                except:
                    pass

    def analyze_file(self, file_path: Path):
        """Analyze a BaseAgent file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract key information
            analysis = {
                "file": file_path.name,
                "path": str(file_path),
                "size": len(content),
                "lines": len(content.split("\n")),
                "classes": [],
                "imports": [],
                "features": [],
                "protocols": [],
            }

            # Find classes
            for match in re.finditer(r"^class\s+(\w+)", content, re.MULTILINE):
                analysis["classes"].append(match.group(1))

            # Find imports
            for match in re.finditer(r"^(?:from|import)\s+(.+?)(?:\s|$)", content, re.MULTILINE):
                imp = match.group(1).strip()
                if imp and not imp.startswith("#"):
                    analysis["imports"].append(imp[:50])

            # Detect features
            if "ABC" in content or "abstract" in content.lower():
                analysis["features"].append("Abstract Base Class")
            if "ProtocolMixin" in content:
                analysis["features"].append("Protocol Support")
            if "async def" in content:
                analysis["features"].append("Async Operations")
            if "logging" in content:
                analysis["features"].append("Logging")
            if "ExchangeManager" in content:
                analysis["features"].append("Trading/Exchange")
            if "learning" in content.lower():
                analysis["features"].append("Learning System")
            if "tool" in content.lower() and "discovery" in content.lower():
                analysis["features"].append("Tool Discovery")
            if "collaborative" in content.lower():
                analysis["features"].append("Collaboration")

            # Detect protocols
            if "A2A" in content:
                analysis["protocols"].append("A2A")
            if "ANP" in content:
                analysis["protocols"].append("ANP")
            if "ACP" in content:
                analysis["protocols"].append("ACP")
            if "BAP" in content or "Blockchain" in content:
                analysis["protocols"].append("BAP")

            self.base_agents.append(analysis)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def print_analysis(self):
        """Print analysis results"""
        print("\n" + "=" * 70)
        print("BASEAGENT ANALYSIS RESULTS")
        print("=" * 70)

        print(f"\nFound {len(self.base_agents)} BaseAgent implementations:\n")

        # Sort by size
        sorted_agents = sorted(self.base_agents, key=lambda x: -x["lines"])

        for i, agent in enumerate(sorted_agents, 1):
            print(f"{i}. {agent['file']}")
            print(f"   Size: {agent['lines']} lines ({agent['size']} bytes)")
            print(f"   Classes: {', '.join(agent['classes'][:5])}")
            if agent["protocols"]:
                print(f"   Protocols: {', '.join(agent['protocols'])}")
            if agent["features"]:
                print(f"   Features: {', '.join(agent['features'][:5])}")
            print()

    def generate_recommendations(self):
        """Generate consolidation recommendations"""
        print("=" * 70)
        print("CONSOLIDATION RECOMMENDATIONS")
        print("=" * 70)

        # Categorize by type
        trading_specific = []
        protocol_compliant = []
        enhanced = []
        basic = []

        for agent in self.base_agents:
            if "Trading/Exchange" in agent["features"]:
                trading_specific.append(agent)
            elif "Protocol Support" in agent["features"]:
                if any(
                    f in agent["features"]
                    for f in ["Learning System", "Tool Discovery", "Collaboration"]
                ):
                    enhanced.append(agent)
                else:
                    protocol_compliant.append(agent)
            else:
                basic.append(agent)

        print("\n### Category Analysis\n")
        print(f"Trading-Specific: {len(trading_specific)} implementations")
        for agent in trading_specific:
            print(f"  - {agent['file']} ({agent['lines']} lines)")

        print(f"\nProtocol-Compliant Base: {len(protocol_compliant)} implementations")
        for agent in protocol_compliant:
            print(f"  - {agent['file']} ({agent['lines']} lines)")

        print(f"\nEnhanced Base: {len(enhanced)} implementations")
        for agent in enhanced:
            print(f"  - {agent['file']} ({agent['lines']} lines)")

        print(f"\nBasic/Other: {len(basic)} implementations")
        for agent in basic:
            print(f"  - {agent['file']} ({agent['lines']} lines)")

        print("\n### Recommended Strategy\n")

        if protocol_compliant:
            canonical = max(protocol_compliant, key=lambda x: x["lines"])
            print(f"[OK] CANONICAL BASE: {canonical['file']}")
            print(f"   Reason: Protocol-compliant, general-purpose")
            print(f"   Features: {', '.join(canonical['features'])}")
            print(f"   Protocols: {', '.join(canonical['protocols'])}")
            print()

        if enhanced:
            enhanced_agent = max(enhanced, key=lambda x: x["lines"])
            print(f"[OK] ENHANCED BASE: {enhanced_agent['file']}")
            print(f"   Reason: Extends base with learning/collaboration")
            print(f"   Action: Keep as optional enhanced version")
            print()

        if trading_specific:
            trading = trading_specific[0]
            print(f"[OK] TRADING BASE: {trading['file']}")
            print(f"   Reason: Specialized for trading agents")
            print(f"   Action: Keep in trading/ subdirectory")
            print()

        print("### Consolidation Steps\n")
        print("1. Choose canonical protocol-compliant base (base_agent_v1.py)")
        print("2. Move trading-specific base to trading/base_agent.py")
        print("3. Keep enhanced base as optional extension")
        print("4. Archive/delete other variants")
        print("5. Update all agent imports to use canonical base")
        print()

    def generate_report(self, output_path: str):
        """Generate detailed report"""
        lines = [
            "# BaseAgent Consolidation Report",
            "",
            f"## Analysis Summary",
            "",
            f"**Total BaseAgent Implementations Found:** {len(self.base_agents)}",
            "",
            "## Detailed Analysis",
            "",
        ]

        for agent in sorted(self.base_agents, key=lambda x: -x["lines"]):
            lines.append(f"### {agent['file']}")
            lines.append(f"- **Lines:** {agent['lines']}")
            lines.append(f"- **Size:** {agent['size']} bytes")
            lines.append(f"- **Classes:** {', '.join(agent['classes'])}")
            if agent["protocols"]:
                lines.append(f"- **Protocols:** {', '.join(agent['protocols'])}")
            if agent["features"]:
                lines.append(f"- **Features:** {', '.join(agent['features'])}")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\nDetailed report saved to: {output_path}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("SuperStandard BaseAgent Analysis Tool")
    print("=" * 70)

    base_path = Path(__file__).parent.parent
    agents_dir = base_path / "agents" / "consolidated"

    analyzer = BaseAgentAnalyzer(agents_dir)
    analyzer.find_base_agents()
    analyzer.print_analysis()
    analyzer.generate_recommendations()
    analyzer.generate_report(base_path / "BASEAGENT_ANALYSIS.md")

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
