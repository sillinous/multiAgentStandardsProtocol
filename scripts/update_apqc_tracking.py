#!/usr/bin/env python3
"""
APQC PCF Tracking Update Script

This script helps maintain the APQC_PCF_TRACKING.md and .json files.

Usage:
    python scripts/update_apqc_tracking.py --scan        # Scan repo and update counts
    python scripts/update_apqc_tracking.py --update <process_id> --status <field> <value>
    python scripts/update_apqc_tracking.py --add-note <process_id> <note>

Examples:
    # Mark business logic as partial for process 3.1
    python scripts/update_apqc_tracking.py --update 3.1 --business-logic PARTIAL

    # Add implementation note
    python scripts/update_apqc_tracking.py --add-note 3.1 "Implemented market segmentation algorithm"

    # Rescan repo for new implementations
    python scripts/update_apqc_tracking.py --scan
"""

import json
import os
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Tracking files
TRACKING_JSON = PROJECT_ROOT / "APQC_PCF_TRACKING.json"
TRACKING_MD = PROJECT_ROOT / "APQC_PCF_TRACKING.md"

# Agent locations to scan
AGENT_PATHS = [
    PROJECT_ROOT / "agents" / "consolidated" / "py",
    PROJECT_ROOT / "src" / "superstandard" / "agents"
]


def scan_apqc_implementations() -> Set[str]:
    """Scan codebase for APQC process implementations"""
    implementations = set()

    for base_path in AGENT_PATHS:
        if not base_path.exists():
            continue

        for py_file in base_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')

                # Look for APQC_PROCESS_ID declarations
                matches = re.findall(r'APQC_PROCESS_ID\s*=\s*"([0-9.]+)"', content)
                implementations.update(matches)

            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")

    return implementations


def load_tracking_data() -> Dict:
    """Load current tracking data"""
    if TRACKING_JSON.exists():
        with open(TRACKING_JSON, 'r') as f:
            return json.load(f)
    return {"metadata": {}, "processes": []}


def save_tracking_data(data: Dict):
    """Save tracking data to JSON"""
    data["metadata"]["last_updated"] = datetime.now().isoformat()

    with open(TRACKING_JSON, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Updated {TRACKING_JSON}")


def update_process_status(process_id: str, field: str, value: str):
    """Update a specific field for a process"""
    data = load_tracking_data()

    # Find the process
    process = None
    for p in data.get("processes", []):
        if p.get("process_id") == process_id:
            process = p
            break

    if not process:
        # Check level2_processes
        for p in data.get("level2_processes", []):
            if p.get("process_id") == process_id:
                process = p
                break

    if not process:
        print(f"❌ Process {process_id} not found in tracking data")
        return

    # Update the field
    old_value = process.get(field, "N/A")
    process[field] = value
    process["last_updated"] = datetime.now().isoformat()

    # Save
    save_tracking_data(data)
    print(f"✅ Updated {process_id}: {field} = {old_value} → {value}")


def add_note(process_id: str, note: str):
    """Add a note to a process"""
    data = load_tracking_data()

    # Find the process
    process = None
    for p in data.get("processes", []) + data.get("level2_processes", []):
        if p.get("process_id") == process_id:
            process = p
            break

    if not process:
        print(f"❌ Process {process_id} not found")
        return

    # Add note
    current_notes = process.get("notes", "")
    if current_notes:
        process["notes"] = f"{current_notes}; {note}"
    else:
        process["notes"] = note

    process["last_updated"] = datetime.now().isoformat()

    # Save
    save_tracking_data(data)
    print(f"✅ Added note to {process_id}")


def regenerate_markdown():
    """Regenerate the markdown tracking file from JSON"""
    data = load_tracking_data()

    print("📝 Regenerating APQC_PCF_TRACKING.md...")
    print("   (This would regenerate the full markdown table)")
    print("   TODO: Implement full markdown generation")
    # TODO: Implement markdown generation from JSON data


def main():
    parser = argparse.ArgumentParser(description="Update APQC PCF tracking files")

    parser.add_argument("--scan", action="store_true", help="Scan repo for implementations")
    parser.add_argument("--update", metavar="PROCESS_ID", help="Process ID to update")
    parser.add_argument("--status", metavar="FIELD", help="Status field to update")
    parser.add_argument("--value", metavar="VALUE", help="New value for status field")
    parser.add_argument("--add-note", metavar="PROCESS_ID", help="Add note to process")
    parser.add_argument("--note", metavar="TEXT", help="Note text")
    parser.add_argument("--regenerate-md", action="store_true", help="Regenerate markdown from JSON")

    args = parser.parse_args()

    if args.scan:
        print("🔍 Scanning repository for APQC implementations...")
        implementations = scan_apqc_implementations()
        print(f"✅ Found {len(implementations)} unique APQC process IDs")
        print(f"   Sample: {list(sorted(implementations))[:10]}")

        # TODO: Update tracking data with scan results
        print("\n⚠️  TODO: Integrate scan results into tracking data")

    elif args.update and args.status and args.value:
        update_process_status(args.update, args.status, args.value)

    elif args.add_note and args.note:
        add_note(args.add_note, args.note)

    elif args.regenerate_md:
        regenerate_markdown()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
