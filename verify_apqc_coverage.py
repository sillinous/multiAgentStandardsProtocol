#!/usr/bin/env python3
"""
Verify APQC PCF Coverage
========================

Check which APQC PCF items we have vs. the complete APQC PCF 7.0.1 specification.

The complete APQC PCF 7.0.1 has approximately 1,100+ Level 5 tasks.
We need to identify any missing items.
"""

import os
import re
from collections import defaultdict

def scan_existing_agents():
    """Scan what APQC IDs we currently have"""
    existing = set()

    for root, dirs, files in os.walk("generated_agents_v2"):
        for file in files:
            if file.endswith("_agent.py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    match = re.search(r'APQC Task:\s+([\d.]+)', content)
                    if match:
                        existing.add(match.group(1))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    return existing

def main():
    print("=" * 80)
    print("APQC PCF COVERAGE VERIFICATION")
    print("=" * 80)
    print()

    existing = scan_existing_agents()
    print(f"Currently have: {len(existing)} unique APQC Level 5 tasks")
    print()

    # Group by category
    by_category = defaultdict(list)
    for task_id in sorted(existing):
        category = task_id.split('.')[0]
        by_category[category].append(task_id)

    print("By Category:")
    for cat in sorted(by_category.keys(), key=int):
        tasks = by_category[cat]
        print(f"  Category {cat}: {len(tasks)} tasks")
        if len(tasks) <= 10:
            for task in tasks:
                print(f"    - {task}")
    print()

    # Note about APQC PCF 7.0.1
    print("NOTE: The official APQC PCF 7.0.1 contains approximately 1,100+ Level 5 tasks.")
    print(f"We currently have {len(existing)} tasks ({len(existing)/1100*100:.1f}% coverage estimate).")
    print()
    print("This suggests we may be missing ~" + str(1100 - len(existing)) + " tasks.")
    print()

    # Check if we have systematic coverage or gaps
    print("Coverage Analysis:")
    for cat in sorted(by_category.keys(), key=int):
        tasks = sorted(by_category[cat])
        print(f"\nCategory {cat}:")

        # Extract process groups (X.Y)
        processes = set()
        for task in tasks:
            parts = task.split('.')
            if len(parts) >= 2:
                processes.add(f"{parts[0]}.{parts[1]}")

        print(f"  Process Groups covered: {len(processes)}")
        print(f"  Tasks: {sorted(tasks)[:5]}{'...' if len(tasks) > 5 else ''}")

if __name__ == "__main__":
    main()
