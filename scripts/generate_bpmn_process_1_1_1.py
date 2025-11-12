"""
BPMN Model Generator Script

Generates BPMN 2.0 XML for Process 1.1.1 "Assess External Environment"
with all 7 activity agents as service tasks.

Usage:
    python scripts/generate_bpmn_process_1_1_1.py
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from superstandard.agents.pcf.generators.bpmn_generator import BPMNGenerator


def load_pcf_registry():
    """Load PCF registry"""
    registry_path = Path(__file__).parent.parent / 'src/superstandard/agents/pcf/metadata/pcf_registry.json'
    with open(registry_path, 'r') as f:
        return json.load(f)


def find_process_metadata(registry, hierarchy_id):
    """Find process metadata in registry"""
    # Navigate through categories -> process_groups -> processes
    for category in registry['categories']:
        for pg in category.get('process_groups', []):
            for process in pg.get('processes', []):
                if process['hierarchy_id'] == hierarchy_id:
                    return process
    return None


def main():
    """Generate BPMN model for Process 1.1.1"""
    print("="*80)
    print("BPMN Model Generator - Process 1.1.1")
    print("="*80)

    # Load registry
    print("\n1. Loading PCF Registry...")
    registry = load_pcf_registry()
    print(f"   ✓ Loaded {registry['total_categories']} categories")

    # Find Process 1.1.1
    print("\n2. Finding Process 1.1.1 metadata...")
    process_metadata = find_process_metadata(registry, "1.1.1")

    if not process_metadata:
        print("   ✗ Process 1.1.1 not found!")
        return 1

    print(f"   ✓ Found: {process_metadata['name']}")
    print(f"   ✓ Activities: {len(process_metadata.get('activities', []))}")

    # Generate BPMN
    print("\n3. Generating BPMN 2.0 XML...")
    generator = BPMNGenerator()

    bpmn_xml = generator.generate_from_pcf_metadata(
        process_metadata,
        bpm_system="camunda"
    )

    print("   ✓ BPMN XML generated")

    # Save to file
    output_dir = Path(__file__).parent.parent / 'src/superstandard/agents/pcf/bpmn_models'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / 'process_1_1_1_assess_external_environment.bpmn'

    print(f"\n4. Saving BPMN model...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(bpmn_xml)

    print(f"   ✓ Saved to: {output_path}")

    # Summary
    print("\n" + "="*80)
    print("BPMN Model Generation Complete!")
    print("="*80)
    print(f"\nProcess: {process_metadata['name']}")
    print(f"Element ID: {process_metadata['element_id']}")
    print(f"Hierarchy ID: {process_metadata['hierarchy_id']}")
    print(f"Activities: {len(process_metadata.get('activities', []))}")
    print(f"\nBPMN File: {output_path}")
    print("\nNext Steps:")
    print("  1. Import this BPMN file into Camunda Modeler")
    print("  2. View the visual process workflow")
    print("  3. Deploy to Camunda BPM engine")
    print("  4. Execute the process!")
    print("\n" + "="*80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
