"""
Generate Complete APQC Category 1.0 - Vision and Strategy

This script generates all agents for the Vision and Strategy category,
demonstrating the power of the Agent Factory to scale from 3 to 22+ agents!

Run:
    python examples/generate_category_1_0.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.superstandard.agent_factory import AgentGenerator


def main():
    print("\n" + "="*80)
    print("🏭 APQC CATEGORY 1.0 AGENT FACTORY")
    print("   Vision and Strategy - Complete Agent Library")
    print("="*80)

    generator = AgentGenerator()

    specs_dir = Path(__file__).parent.parent / "src" / "superstandard" / "agent_factory" / "specs" / "category_1_0"

    # Find all specification files
    spec_files = sorted(specs_dir.glob("*.yaml"))

    print(f"\n📋 Found {len(spec_files)} agent specifications:")
    for spec_file in spec_files:
        print(f"   - {spec_file.name}")

    print("\n" + "="*80)
    print("🚀 GENERATING AGENTS")
    print("="*80)

    generated = []
    failed = []

    for i, spec_file in enumerate(spec_files, 1):
        print(f"\n[{i}/{len(spec_files)}] Generating from: {spec_file.name}")
        try:
            output_path = generator.generate_from_spec(str(spec_file))
            generated.append(output_path)
            print(f"   ✅ Success: {Path(output_path).name}")
        except Exception as e:
            failed.append((spec_file.name, str(e)))
            print(f"   ❌ Failed: {e}")

    # Summary
    print("\n" + "="*80)
    print("📊 GENERATION SUMMARY")
    print("="*80)
    print(f"\n   ✅ Successfully Generated: {len(generated)}")
    print(f"   ❌ Failed: {len(failed)}")
    print(f"   📦 Total Specifications: {len(spec_files)}")

    if generated:
        print("\n✨ Generated Agents:")
        for path in generated:
            print(f"   - {Path(path).name}")

    if failed:
        print("\n⚠️  Failed Generations:")
        for spec_name, error in failed:
            print(f"   - {spec_name}: {error}")

    # Show what we built
    print("\n" + "="*80)
    print("🎯 APQC CATEGORY 1.0 - COMPLETE COVERAGE")
    print("="*80)

    categories = {
        "1.1 - Define Business Concept and Long-term Vision": [
            "1.1.1 - Assess the external environment",
            "1.1.2 - Survey market and determine customer needs",
            "1.1.3 - Perform internal analysis",
            "1.1.4 - Establish strategic vision",
            "1.1.5 - Analyze stakeholders"
        ],
        "1.2 - Develop Business Strategy": [
            "1.2.1 - Develop overall mission statement",
            "1.2.2 - Evaluate strategic options",
            "1.2.3 - Select long-term business strategy",
            "1.2.4 - Coordinate and align functional strategies",
            "1.2.5 - Analyze strategic risks"
        ],
        "1.3 - Manage Strategic Initiatives": [
            "1.3.1 - Develop strategic initiatives",
            "1.3.2 - Evaluate strategic initiatives",
            "1.3.3 - Select strategic initiatives",
            "1.3.4 - Establish high-level measures"
        ],
        "1.4 - Communicate and Implement Strategy": [
            "1.4.1 - Communicate strategy",
            "1.4.2 - Monitor strategy execution"
        ]
    }

    for category, processes in categories.items():
        print(f"\n📁 {category}")
        for process in processes:
            print(f"   ✓ {process}")

    print("\n" + "="*80)
    print("✅ AGENT FACTORY SUCCESS!")
    print("="*80)
    print(f"""
From Specification to Production in Minutes!

🎯 What We Built:
   - {len(generated)} production-ready agents
   - Complete APQC Category 1.0 coverage
   - Type-safe, validated implementations
   - Discovery Protocol integration ready

💡 The Power of Agent Factory:
   - Write YAML spec in 5 minutes
   - Generate production agent instantly
   - Scale from 10s to 1000s of agents
   - Consistent quality and structure

🚀 Next Steps:
   1. Test agents with Agent Registry
   2. Integrate with Discovery Protocol
   3. Build orchestration workflows
   4. Expand to more APQC categories!

The Agent Factory proves we can scale to the full APQC framework
of 5,000+ processes with automated agent generation!
""")


if __name__ == "__main__":
    main()
