#!/usr/bin/env python3
"""
Fix Class Names Script

This script fixes invalid class names that contain commas or hyphens.

Usage:
    python scripts/fix_class_names.py
"""

import re
from pathlib import Path

# Files with invalid class names
FILES_TO_FIX = [
    "agents/consolidated/py/develop_manage_hr_planning_policies_strategies_human_capital_agent.py",
    "agents/consolidated/py/recruit_source_select_employees_human_capital_agent.py",
    "agents/consolidated/py/understand_markets_customers_capabilities_sales_marketing_agent.py",
    "agents/consolidated/py/define_business_concept_long_term_vision_strategic_agent.py",
    "agents/consolidated/py/develop_manage_enterprise_wide_knowledge_management_capability_development_agent.py",
    "agents/consolidated/py/revenue_optimizer_agent_v1.py",
    "src/superstandard/agents/api/develop_manage_hr_planning_policies_strategies_human_capital_agent.py",
    "src/superstandard/agents/api/recruit_source_select_employees_human_capital_agent.py",
    "src/superstandard/agents/blockchain/define_business_concept_long_term_vision_strategic_agent.py",
    "src/superstandard/agents/infrastructure/develop_manage_enterprise_wide_knowledge_management_capability_development_agent.py",
    "src/superstandard/agents/trading/understand_markets_customers_capabilities_sales_marketing_agent.py",
]


def fix_class_names(file_path: str):
    """Fix class names by removing commas and hyphens."""
    path = Path(file_path)
    if not path.exists():
        print(f"⚠️  Skipping {file_path} (not found)")
        return

    print(f"📄 Fixing {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Fix class names with commas
    content = re.sub(r"class (\w+),(\w+),(\w+)(\w+):", r"class \1\2\3\4:", content)

    # Fix class names with hyphens (more complex pattern)
    content = re.sub(r"class (\w+)-(\w+)(\w+):", r"class \1\2\3:", content)

    # Fix specific patterns
    content = re.sub(
        r"DevelopManageHrPlanning,Policies,StrategiesHumanCapitalAgent",
        "DevelopManageHrPlanningPoliciesStrategiesHumanCapitalAgent",
        content,
    )

    content = re.sub(
        r"Recruit,Source,SelectEmployeesHumanCapitalAgent",
        "RecruitSourceSelectEmployeesHumanCapitalAgent",
        content,
    )

    content = re.sub(
        r"UnderstandMarkets,Customers,CapabilitiesSalesMarketingAgent",
        "UnderstandMarketsCustomersCapabilitiesSalesMarketingAgent",
        content,
    )

    content = re.sub(
        r"DefineBusinessConceptLong-termVisionStrategicAgent",
        "DefineBusinessConceptLongTermVisionStrategicAgent",
        content,
    )

    content = re.sub(
        r"DevelopManageEnterprise-wideKnowledgeManagementCapabilityDevelopmentAgent",
        "DevelopManageEnterpriseWideKnowledgeManagementCapabilityDevelopmentAgent",
        content,
    )

    # Fix the syntax error in revenue_optimizer_agent_v1.py
    content = re.sub(
        r'"specialty = "revenue_optimization"', r'"specialty": "revenue_optimization"', content
    )

    # Fix function names with commas and hyphens
    content = re.sub(
        r"def create_develop_manage_hr_planning,_policies,_strategies_human_capital_agent",
        "def create_develop_manage_hr_planning_policies_strategies_human_capital_agent",
        content,
    )

    content = re.sub(
        r"def create_recruit,_source,_select_employees_human_capital_agent",
        "def create_recruit_source_select_employees_human_capital_agent",
        content,
    )

    content = re.sub(
        r"def create_understand_markets,_customers,_capabilities_sales_marketing_agent",
        "def create_understand_markets_customers_capabilities_sales_marketing_agent",
        content,
    )

    content = re.sub(
        r"def create_develop_manage_enterprise-wide_knowledge_management_capability_development_agent",
        "def create_develop_manage_enterprise_wide_knowledge_management_capability_development_agent",
        content,
    )

    content = re.sub(
        r"def create_define_business_concept_long-term_vision_strategic_agent",
        "def create_define_business_concept_long_term_vision_strategic_agent",
        content,
    )

    # Fix syntax error on line 25 of revenue_optimizer_agent_v1.py
    # Change "specialty = "revenue_optimization" to "specialty": "revenue_optimization"
    content = re.sub(r'specialty = "', r'specialty": "', content)

    if content != original_content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Fixed class names")
    else:
        print(f"  ℹ️  No changes needed")


def main():
    print("=" * 70)
    print("SuperStandard Class Name Fixer")
    print("=" * 70 + "\n")

    for file_path in FILES_TO_FIX:
        fix_class_names(file_path)

    print("\n" + "=" * 70)
    print("✅ All class names fixed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
