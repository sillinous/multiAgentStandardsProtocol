"""
Package APQC Agent Blueprints for Gumroad Product
Creates enriched, contextually rich agent documentation
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Load APQC Framework
with open("APQC_FRAMEWORK.json", "r") as f:
    framework = json.load(f)

# Create lookup for APQC processes
apqc_lookup = {}
for category in framework["categories"]:
    cat_id = category["id"]
    cat_name = category["name"]
    for i, process in enumerate(category["processes"], 1):
        process_id = f"{cat_id}.{i}"
        apqc_lookup[process_id] = {
            "category_id": cat_id,
            "category_name": cat_name,
            "process_id": process_id,
            "process_name": process,
            "process_number": process.split(" ")[0],  # e.g., "1.1"
        }

# Count and analyze agents
total_agents = 0
agents_by_category = {}

for category_dir in sorted(Path("apqc_agents").iterdir()):
    if category_dir.is_dir():
        agents_file = category_dir / "agents.json"
        if agents_file.exists():
            with open(agents_file, "r") as f:
                agents = json.load(f)
                count = len(agents)
                total_agents += count
                cat_id = category_dir.name
                agents_by_category[cat_id] = {"count": count, "agents": agents}

print(f"\n{'='*60}")
print(f"APQC AGENT BLUEPRINT PACKAGE ANALYSIS")
print(f"{'='*60}\n")

print(f"Framework Version: {framework['framework_version']}")
print(f"Total Categories: {len(framework['categories'])}")
print(f"Total Agents: {total_agents}\n")

print(f"{'Category':<8} {'Agents':<8} {'Name':<45}")
print(f"{'-'*60}")

for cat in framework["categories"]:
    cat_id = cat["id"].replace(".", "_")
    count = agents_by_category.get(cat_id, {}).get("count", 0)
    print(f"{cat['id']:<8} {count:<8} {cat['name']:<45}")

print(f"\n{'='*60}\n")

# Create enriched documentation
print("Creating enriched agent documentation...")

enriched_agents = []

for cat_id, data in agents_by_category.items():
    for agent in data["agents"]:
        # Get APQC context
        process_id = agent["metadata"].get("process_id", "")
        apqc_context = apqc_lookup.get(process_id, {})

        enriched = {
            **agent,
            "apqc_context": {
                "framework_version": framework["framework_version"],
                "category": {
                    "id": apqc_context.get("category_id", ""),
                    "name": apqc_context.get("category_name", ""),
                },
                "process": {
                    "id": apqc_context.get("process_id", ""),
                    "name": apqc_context.get("process_name", ""),
                    "number": apqc_context.get("process_number", ""),
                },
            },
            "business_value": {
                "description": f"Automates {apqc_context.get('process_name', 'business process')}",
                "impact_areas": [apqc_context.get("category_name", "")],
                "typical_use_cases": [
                    f"Process automation for {apqc_context.get('process_name', '')}",
                    "Decision support and analysis",
                    "Cross-functional collaboration",
                ],
            },
            "implementation": {
                "deployment_type": agent["deployment"]["runtime"],
                "scaling_strategy": agent["deployment"]["scaling"],
                "minimum_requirements": {
                    "compute": agent["resources"]["compute"],
                    "memory": agent["resources"]["memory"],
                },
            },
        }

        enriched_agents.append(enriched)

print(f"[OK] Enriched {len(enriched_agents)} agents with APQC context and business value\n")

# Save enriched agents
output_dir = Path("../revenue/product_package")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "enriched_agents.json", "w") as f:
    json.dump(enriched_agents, f, indent=2)

print(f"[OK] Saved enriched agents to: {output_dir / 'enriched_agents.json'}")
print(f"\nPackage ready for distribution!")
