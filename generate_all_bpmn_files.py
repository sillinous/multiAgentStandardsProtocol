#!/usr/bin/env python3
"""Quick script to generate all BPMN files for already-finalized agents"""

import sys
sys.path.insert(0, '.')

from finalize_all_level5_agents import scan_all_agents, generate_bpmn_file
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("GENERATING ALL BPMN 2.0 FILES")
    print("=" * 80)
    print()

    agents = scan_all_agents()
    print(f"Found {len(agents)} agents")
    print()

    success_count = 0
    failed_count = 0

    for i, agent in enumerate(agents, 1):
        try:
            print(f"[{i}/{len(agents)}] {agent.apqc_id} - {agent.apqc_name}")
            bpmn_path = generate_bpmn_file(agent)
            success_count += 1
            if i % 50 == 0:
                print(f"  Progress: {success_count} BPMN files generated")
        except Exception as e:
            logger.error(f"Failed: {agent.apqc_id}: {e}")
            failed_count += 1

    print()
    print("=" * 80)
    print(f"✅ Successfully generated: {success_count} BPMN files")
    print(f"❌ Failed: {failed_count}")
    print("=" * 80)

if __name__ == "__main__":
    main()
