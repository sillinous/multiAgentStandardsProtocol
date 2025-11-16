"""
🧠 Agent Semantic Protocol (ASP) v1.0 - Semantic Matching Demo
===============================================================

Demonstrates ASP capabilities for semantic interoperability:
- Agent capability declaration
- Semantic matching and discovery
- Ontology alignment
- Schema mapping
- APQC agent capability discovery

This example shows how agents can find each other based on semantic
capabilities rather than exact API specifications.
"""

import json
from datetime import datetime
from superstandard.protocols.asp_v1 import (
    # Core functionality
    SemanticRegistry,

    # Data models
    OntologyReference,
    SemanticParameter,
    QualityOfService,
    SemanticCapability,
    SchemaReference,
    DomainKnowledge,
    SemanticDeclaration,
    ASPMessage,

    # Enums
    Proficiency,
    QueryType,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_json(data: dict, title: str = None):
    """Pretty print JSON data."""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2))


def main():
    """Run the semantic matching demo."""

    print_section("ASP v1.0: Semantic Capability Discovery Demo")

    # ========================================================================
    # STEP 1: Create a Semantic Registry
    # ========================================================================

    print_section("STEP 1: Initialize Semantic Registry")

    registry = SemanticRegistry()
    print("✓ Semantic registry initialized")

    # ========================================================================
    # STEP 2: Register APQC Finance Agents
    # ========================================================================

    print_section("STEP 2: Register APQC Finance Agents")

    # Agent 1: Budget Planning Agent (APQC 9.2)
    budget_agent = SemanticDeclaration(
        agent_id="apqc_9_2_budget_planning_agent",
        ontologies=[
            OntologyReference(
                ontology_id="apqc:7.0.1",
                namespace="https://apqc.org/ontology/7.0.1",
                version="7.0.1",
                coverage=[
                    "FinancialResourceManagement",
                    "BudgetPlanning",
                    "CostAccounting"
                ]
            ),
            OntologyReference(
                ontology_id="schema.org:latest",
                namespace="https://schema.org/",
                coverage=["MonetaryAmount", "FinancialProduct"]
            )
        ],
        capabilities=[
            SemanticCapability(
                capability_id="perform_budget_planning",
                capability_name="Perform Budget Planning and Analysis",
                semantic_type="apqc:BudgetPlanning",
                inputs=[
                    SemanticParameter(
                        name="timeframe",
                        semantic_type="schema.org:DateTime",
                        constraints={"pattern": r"^\d{4}-Q[1-4]$"}
                    ),
                    SemanticParameter(
                        name="total_budget",
                        semantic_type="schema.org:MonetaryAmount",
                        unit="USD",
                        constraints={"range": {"min": 0}}
                    ),
                    SemanticParameter(
                        name="strategic_initiatives",
                        semantic_type="apqc:StrategicInitiative",
                        optional=True
                    )
                ],
                outputs=[
                    SemanticParameter(
                        name="budget_allocation",
                        semantic_type="fibo:BudgetAllocation"
                    ),
                    SemanticParameter(
                        name="financial_forecast",
                        semantic_type="fibo:FinancialForecast"
                    )
                ],
                quality_of_service=QualityOfService(
                    accuracy=0.95,
                    latency_ms=5000,
                    reliability=0.99
                )
            )
        ],
        schemas=[
            SchemaReference(
                schema_id="budget_allocation_v1",
                schema_uri="https://schemas.superstandard.org/budget_allocation/v1.json",
                schema_type="json-schema",
                semantic_mapping={
                    "total_amount": "schema.org:totalPrice",
                    "currency": "schema.org:priceCurrency",
                    "fiscal_year": "fibo:FiscalYear",
                    "line_items": "fibo:BudgetLineItem"
                }
            )
        ],
        domain_knowledge=[
            DomainKnowledge(
                domain="finance",
                subdomain="budgeting",
                proficiency=Proficiency.EXPERT.value,
                standards=["GAAP", "IFRS"],
                regulations=["SOX", "GDPR"]
            )
        ]
    )

    registry.register(budget_agent)
    print(f"✓ Registered: {budget_agent.agent_id}")
    print(f"  - Capabilities: {len(budget_agent.capabilities)}")
    print(f"  - Ontologies: {len(budget_agent.ontologies)}")
    print(f"  - Domain: {budget_agent.domain_knowledge[0].domain} ({budget_agent.domain_knowledge[0].proficiency})")

    # Agent 2: Financial Analysis Agent (APQC 9.3)
    analysis_agent = SemanticDeclaration(
        agent_id="apqc_9_3_financial_analysis_agent",
        ontologies=[
            OntologyReference(
                ontology_id="apqc:7.0.1",
                namespace="https://apqc.org/ontology/7.0.1",
                coverage=["FinancialAnalysis", "PerformanceMetrics", "RevenueAccounting"]
            ),
            OntologyReference(
                ontology_id="fibo:2023-Q4",
                namespace="https://spec.edmcouncil.org/fibo/ontology/",
                coverage=["FinancialStatement", "RevenueRecognition", "AccountingStandard"]
            )
        ],
        capabilities=[
            SemanticCapability(
                capability_id="perform_financial_analysis",
                capability_name="Perform Financial Statement Analysis",
                semantic_type="apqc:FinancialAnalysis",
                inputs=[
                    SemanticParameter(
                        name="financial_statements",
                        semantic_type="fibo:FinancialStatement"
                    ),
                    SemanticParameter(
                        name="analysis_period",
                        semantic_type="schema.org:DateTime"
                    )
                ],
                outputs=[
                    SemanticParameter(
                        name="financial_ratios",
                        semantic_type="fibo:FinancialRatio"
                    ),
                    SemanticParameter(
                        name="trend_analysis",
                        semantic_type="apqc:TrendAnalysis"
                    )
                ],
                quality_of_service=QualityOfService(
                    accuracy=0.98,
                    latency_ms=3000,
                    reliability=0.995
                )
            )
        ],
        domain_knowledge=[
            DomainKnowledge(
                domain="finance",
                subdomain="financial_analysis",
                proficiency=Proficiency.EXPERT.value,
                standards=["GAAP", "IFRS"],
                regulations=["SOX", "SEC"]
            )
        ]
    )

    registry.register(analysis_agent)
    print(f"✓ Registered: {analysis_agent.agent_id}")

    # Agent 3: Cost Management Agent (APQC 9.5)
    cost_agent = SemanticDeclaration(
        agent_id="apqc_9_5_cost_management_agent",
        ontologies=[
            OntologyReference(
                ontology_id="apqc:7.0.1",
                namespace="https://apqc.org/ontology/7.0.1",
                coverage=["CostAccounting", "CostManagement", "ExpenseTracking"]
            )
        ],
        capabilities=[
            SemanticCapability(
                capability_id="manage_costs",
                capability_name="Perform Cost Accounting and Management",
                semantic_type="apqc:CostAccounting",
                inputs=[
                    SemanticParameter(
                        name="cost_data",
                        semantic_type="apqc:CostData"
                    )
                ],
                outputs=[
                    SemanticParameter(
                        name="cost_analysis",
                        semantic_type="apqc:CostAnalysis"
                    )
                ]
            )
        ],
        domain_knowledge=[
            DomainKnowledge(
                domain="finance",
                subdomain="cost_accounting",
                proficiency=Proficiency.ADVANCED.value,
                standards=["GAAP"]
            )
        ]
    )

    registry.register(cost_agent)
    print(f"✓ Registered: {cost_agent.agent_id}")

    # ========================================================================
    # STEP 3: Semantic Discovery - Find Budget Planning Capabilities
    # ========================================================================

    print_section("STEP 3: Discover Budget Planning Capabilities")

    # Define what we're looking for
    required_capability = SemanticCapability(
        capability_id="need_budget_planning",
        semantic_type="apqc:BudgetPlanning",
        capability_name="Looking for budget planning capability"
    )

    print("Searching for agents with capability:")
    print(f"  Semantic Type: {required_capability.semantic_type}")
    print(f"  Minimum Match Score: 0.5")

    # Discover matching agents
    response = registry.discover_capabilities(required_capability, min_score=0.5)

    print(f"\n✓ Found {len(response.matches)} matching agent(s):\n")

    for match in response.matches:
        print(f"  Agent: {match.agent_id}")
        print(f"  Capability: {match.capability_id}")
        print(f"  Match Score: {match.match_score:.2f}")
        print(f"  Match Type: {match.match_type}")
        print(f"  Confidence: {match.confidence:.2f}")
        print()

    # ========================================================================
    # STEP 4: Semantic Discovery - Find Financial Analysis
    # ========================================================================

    print_section("STEP 4: Discover Financial Analysis Capabilities")

    required_analysis = SemanticCapability(
        capability_id="need_financial_analysis",
        semantic_type="apqc:FinancialAnalysis"
    )

    print("Searching for agents with capability:")
    print(f"  Semantic Type: {required_analysis.semantic_type}")

    response = registry.discover_capabilities(required_analysis, min_score=0.7)

    print(f"\n✓ Found {len(response.matches)} matching agent(s):\n")

    for match in response.matches:
        print(f"  Agent: {match.agent_id}")
        print(f"  Match Score: {match.match_score:.2f}")
        print()

    # ========================================================================
    # STEP 5: Partial Matching - Find Finance-Related Agents
    # ========================================================================

    print_section("STEP 5: Partial Matching - All Finance Agents")

    # Search for broader "Financial" capabilities
    required_financial = SemanticCapability(
        capability_id="need_anything_financial",
        semantic_type="apqc:Financial"  # Broader term
    )

    print("Searching for agents with capability:")
    print(f"  Semantic Type: {required_financial.semantic_type} (broad match)")
    print(f"  Minimum Match Score: 0.3")

    response = registry.discover_capabilities(required_financial, min_score=0.3)

    print(f"\n✓ Found {len(response.matches)} agent(s) with finance-related capabilities:\n")

    for match in response.matches:
        print(f"  Agent: {match.agent_id}")
        print(f"  Capability: {match.capability_id}")
        print(f"  Match Score: {match.match_score:.2f}")
        print(f"  Match Type: {match.match_type}")
        print()

    # ========================================================================
    # STEP 6: Ontology Alignment
    # ========================================================================

    print_section("STEP 6: Ontology Concept Alignment")

    # Align similar concepts from different ontologies
    alignments = [
        ("schema.org:MonetaryAmount", "fibo:MonetaryAmount"),
        ("apqc:BudgetPlanning", "apqc:BudgetAnalysis"),
        ("schema.org:totalRevenue", "fibo:Revenue"),
    ]

    print("Aligning ontology concepts:\n")

    for source, target in alignments:
        response = registry.align_ontologies(source, target)

        if response.alignments:
            alignment = response.alignments[0]
            print(f"Source: {alignment.source_concept}")
            print(f"Target: {alignment.target_concept}")
            print(f"Alignment Type: {alignment.alignment_type}")
            print(f"Confidence: {alignment.confidence:.2f}")

            if alignment.transformation:
                print(f"Transformation: {alignment.transformation.transformation_type}")

            print()
        else:
            print(f"No alignment found for {source} -> {target}\n")

    # ========================================================================
    # STEP 7: Create ASP Message
    # ========================================================================

    print_section("STEP 7: ASP Message Example")

    # Create a complete ASP message
    asp_message = ASPMessage(
        protocol="ASP",
        version="1.0.0",
        semantic_declaration=budget_agent
    )

    print("ASP Message Structure:")
    print_json(asp_message.to_dict())

    # ========================================================================
    # Summary
    # ========================================================================

    print_section("Demo Summary")

    print("✓ Successfully demonstrated:")
    print("  - Agent semantic declaration with APQC ontologies")
    print("  - Exact semantic capability matching")
    print("  - Partial/fuzzy semantic matching")
    print("  - Ontology concept alignment")
    print("  - Schema semantic mapping")
    print("  - Quality of Service specification")
    print("  - Domain knowledge representation")
    print()
    print("ASP enables agents to discover and interoperate based on")
    print("semantic meaning rather than rigid API specifications!")
    print()


if __name__ == "__main__":
    main()
