"""
Agent Library Management API

Provides comprehensive endpoints for managing, discovering, and tracking
the complete agent ecosystem including APQC, industry-specific, and custom agents.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.utils.serialization import enum_value
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import json
import os

router = APIRouter()


# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class AgentStatus(str, Enum):
    """Agent development status"""
    PRODUCTION = "production"
    BETA = "beta"
    DEVELOPMENT = "development"
    TEMPLATE = "template"
    PLANNED = "planned"
    DEPRECATED = "deprecated"


class AgentCategory(str, Enum):
    """Agent categories"""
    APQC_FRAMEWORK = "apqc_framework"
    INDUSTRY_SWARM = "industry_swarm"
    CORE_UTILITY = "core_utility"
    DEVELOPMENT = "development"
    TESTING = "testing"
    ANALYTICS = "analytics"
    CUSTOMER_SERVICE = "customer_service"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    SECURITY = "security"
    FINANCE = "finance"
    META = "meta"
    MOBILITY = "mobility"
    TASK_LEVEL = "task_level"


class Industry(str, Enum):
    """Supported industries for swarms"""
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    LOGISTICS = "logistics"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    GENERAL = "general"


class Agent(BaseModel):
    """Agent model"""
    id: str
    name: str
    version: str = "1.0.0"
    category: AgentCategory
    status: AgentStatus
    description: str
    capabilities: List[str] = []
    use_cases: List[str] = []
    dependencies: List[str] = []
    roi_impact: Optional[str] = None
    file_path: Optional[str] = None
    documentation_url: Optional[str] = None
    apqc_category: Optional[str] = None
    industry: Optional[Industry] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = []
    metrics: Optional[Dict[str, Any]] = None


class AgentSwarm(BaseModel):
    """Agent swarm model"""
    id: str
    name: str
    description: str
    category: AgentCategory
    industry: Optional[Industry] = None
    agents: List[str]  # Agent IDs
    coordination_pattern: str
    use_cases: List[str]
    estimated_roi: Optional[str] = None
    status: AgentStatus
    deployment_count: int = 0


class RoadmapItem(BaseModel):
    """Development roadmap item"""
    id: str
    title: str
    description: str
    category: AgentCategory
    priority: str  # high, medium, low
    status: str  # planned, in_progress, completed, blocked
    agents_included: List[str]
    estimated_completion: Optional[str] = None
    progress_percentage: int = 0
    dependencies: List[str] = []


class LibraryStats(BaseModel):
    """Library statistics"""
    total_agents: int
    total_swarms: int
    by_status: Dict[str, int]
    by_category: Dict[str, int]
    production_ready: int
    in_development: int
    templates_available: int
    apqc_coverage: float
    recent_additions: List[Agent]


# ============================================================================
# DATA AGGREGATION FUNCTIONS
# ============================================================================

def get_all_agents() -> List[Agent]:
    """
    Aggregate all agents from various sources:
    - APQC agents
    - Industry swarm agents
    - Core library agents
    - Backend agents
    - Task-level agents
    """
    agents = []

    # APQC Agents (62 agents)
    apqc_categories = [
        ("1_0", "Vision & Strategy"),
        ("2_0", "Product Development"),
        ("3_0", "Marketing & Sales"),
        ("4_0", "Supply Chain & Delivery"),
        ("5_0", "Service Delivery"),
        ("6_0", "Customer Service"),
        ("7_0", "Human Capital"),
        ("8_0", "Financial Management"),
        ("9_0", "Asset Management"),
        ("10_0", "Risk & Compliance"),
        ("11_0", "External Relations"),
        ("12_0", "Capability Development"),
        ("13_0", "Information Technology"),
    ]

    apqc_agent_mapping = {
        "1_0": [
            "define_business_concept_long-term_vision_strategic_agent",
            "develop_business_strategy_strategic_agent",
            "develop_manage_innovation_strategic_agent",
            "manage_strategic_initiatives_strategic_agent"
        ],
        "2_0": [
            "govern_manage_product_service_development_creative_agent",
            "generate_define_new_product_service_ideas_creative_agent",
            "design_prototype_products_creative_agent",
            "test_market_for_new_products_services_creative_agent",
            "prepare_for_production_creative_agent",
            "manage_product_service_lifecycle_creative_agent"
        ],
        "3_0": [
            "understand_markets,_customers,_capabilities_sales_marketing_agent",
            "develop_marketing_strategy_sales_marketing_agent",
            "develop_sales_strategy_sales_marketing_agent",
            "develop_manage_marketing_plans_sales_marketing_agent",
            "develop_manage_sales_plans_sales_marketing_agent",
            "conduct_customer_research_sales_marketing_agent",
            "analyze_market_trends_sales_marketing_agent",
            "manage_product_portfolio_sales_marketing_agent",
            "manage_pricing_sales_marketing_agent"
        ],
        "4_0": [
            "plan_for_align_supply_chain_resources_operational_agent",
            "procure_materials_services_operational_agent",
            "produce_manufacture_deliver_product_operational_agent",
            "deliver_service_to_customer_operational_agent",
            "manage_logistics_warehousing_operational_agent",
            "schedule_production_operational_agent",
            "forecast_demand_operational_agent",
            "manage_supplier_relationships_operational_agent",
            "optimize_inventory_operational_agent"
        ],
        "5_0": [
            "plan_for_align_service_delivery_resources_service_delivery_agent",
            "develop_manage_service_delivery_service_delivery_agent",
            "deliver_service_to_customer_service_delivery_agent",
            "design_service_delivery_process_service_agent"
        ],
        "6_0": [
            "develop_customer_care_customer_service_strategy_customer_service_agent",
            "plan_manage_customer_service_operations_customer_service_agent",
            "measure_evaluate_customer_service_operations_customer_service_agent",
            "manage_customer_inquiries_customer_service_agent",
            "resolve_customer_issues_customer_service_agent"
        ],
        "7_0": [
            "develop_manage_hr_planning,_policies,_strategies_human_capital_agent",
            "recruit,_source,_select_employees_human_capital_agent",
            "develop_counsel_employees_human_capital_agent",
            "reward_retain_employees_human_capital_agent",
            "redeploy_retire_employees_human_capital_agent",
            "manage_employee_information_human_capital_agent",
            "source_candidates_human_capital_agent",
            "develop_employee_competencies_human_capital_agent",
            "manage_performance_human_capital_agent"
        ],
        "8_0": [
            "perform_planning_management_accounting_financial_agent",
            "perform_revenue_accounting_financial_agent",
            "perform_general_accounting_reporting_financial_agent",
            "manage_fixed_asset_project_accounting_financial_agent",
            "process_payroll_financial_agent",
            "manage_treasury_operations_financial_agent",
            "process_accounts_payable_financial_agent",
            "perform_cost_accounting_financial_agent",
            "process_accounts_receivable_financial_agent"
        ],
        "9_0": [
            "design_construct_acquire_productive_assets_asset_management_agent",
            "maintain_productive_assets_asset_management_agent",
            "dispose_of_productive_assets_asset_management_agent",
            "perform_preventive_maintenance_asset_management_agent",
            "optimize_asset_utilization_asset_management_agent"
        ],
        "10_0": [
            "manage_enterprise_risk_risk_compliance_agent",
            "manage_business_policies_procedures_risk_compliance_agent",
            "manage_business_resiliency_risk_compliance_agent",
            "manage_regulatory_legal_compliance_risk_compliance_agent",
            "manage_environmental_health_safety_risk_compliance_agent",
            "develop_enterprise_risk_strategy_risk_agent",
            "assess_risks_risk_compliance_agent"
        ],
        "11_0": [
            "manage_government_industry_relationships_relationship_management_agent",
            "build_investor_relationships_relationship_management_agent",
            "manage_relations_with_board_of_directors_relationship_management_agent",
            "manage_legal_ethical_issues_relationship_management_agent",
            "manage_public_relations_relationship_management_agent"
        ],
        "12_0": [
            "manage_business_processes_capability_development_agent",
            "manage_enterprise_quality_capability_development_agent",
            "manage_portfolio_of_enterprise_programs_projects_capability_development_agent",
            "manage_change_capability_development_agent",
            "develop_manage_enterprise-wide_knowledge_management_capability_development_agent",
            "initiate_projects_capability_development_agent",
            "execute_projects_capability_development_agent"
        ],
        "13_0": [
            "manage_business_of_it_technology_agent",
            "develop_manage_it_customer_relationships_technology_agent",
            "manage_it_enterprise_architecture_technology_agent",
            "manage_it_infrastructure_technology_agent",
            "manage_it_services_operations_technology_agent",
            "manage_it_security_privacy_technology_agent",
            "design_it_solutions_technology_agent",
            "deploy_it_solutions_technology_agent"
        ],
    }

    for cat_id, cat_name in apqc_categories:
        if cat_id in apqc_agent_mapping:
            for agent_name in apqc_agent_mapping[cat_id]:
                agents.append(Agent(
                    id=f"apqc_{cat_id}_{agent_name}",
                    name=agent_name.replace("_", " ").title(),
                    category=AgentCategory.APQC_FRAMEWORK,
                    status=AgentStatus.PRODUCTION,
                    description=f"APQC {cat_name} process agent",
                    capabilities=[f"APQC {cat_name}"],
                    apqc_category=f"{cat_id} - {cat_name}",
                    file_path=f"/autonomous-ecosystem/library/agents/apqc/{cat_id}/{agent_name}.py",
                    tags=["apqc", cat_id, "enterprise"]
                ))

    # Core Library Agents
    core_agents = [
        ("base_agent_v1", "Base Agent", "Foundation agent class", AgentStatus.PRODUCTION),
        ("message_routing_agent", "Message Routing Agent", "Enterprise A2A communication hub with priority routing, load balancing, and health monitoring", AgentStatus.PRODUCTION),
        ("design_agent_v1", "Design Agent", "UI/UX design automation", AgentStatus.PRODUCTION),
        ("development_agent_v1", "Development Agent", "Code generation and development", AgentStatus.PRODUCTION),
        ("development_agent_v2", "Enhanced Development Agent", "Advanced code generation", AgentStatus.PRODUCTION),
        ("testing_agent_v1", "Testing Agent", "Automated testing", AgentStatus.PRODUCTION),
        ("qa_agent_v1", "QA Agent", "Quality assurance", AgentStatus.PRODUCTION),
        ("orchestrator_agent_v1", "Orchestrator Agent", "Multi-agent orchestration", AgentStatus.PRODUCTION),
    ]

    for agent_id, name, desc, status in core_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.CORE_UTILITY,
            status=status,
            description=desc,
            file_path=f"/autonomous-ecosystem/library/{agent_id}.py",
            tags=["core", "library"]
        ))

    # Hybrid AI Agents (5 agents) - ZERO credits when using local LLM
    hybrid_ai_agents = [
        ("product_analysis_agent_v1", "Product Analysis Agent", "Hybrid AI agent for product categorization and analysis with automatic local/cloud routing (ZERO credits in local mode)", AgentStatus.PRODUCTION, "80%+ cost savings", ["product_categorization", "feature_extraction", "target_audience_analysis", "hybrid_processing"]),
        ("text_summarization_agent_v1", "Text Summarization Agent", "Hybrid AI agent for text summarization with automatic local/cloud routing (ZERO credits in local mode)", AgentStatus.PRODUCTION, "80%+ cost savings", ["text_summarization", "content_condensing", "key_points_extraction", "hybrid_processing"]),
        ("sentiment_analysis_agent_v1", "Sentiment Analysis Agent", "Hybrid AI agent for sentiment classification with automatic local/cloud routing (ZERO credits in local mode)", AgentStatus.PRODUCTION, "80%+ cost savings", ["sentiment_classification", "confidence_scoring", "key_point_extraction", "hybrid_processing"]),
        ("feature_extraction_agent_v1", "Feature Extraction Agent", "Hybrid AI agent for feature and specification extraction with automatic local/cloud routing (ZERO credits in local mode)", AgentStatus.PRODUCTION, "80%+ cost savings", ["feature_identification", "specification_extraction", "benefit_analysis", "hybrid_processing"]),
        ("classification_agent_v1", "Classification Agent", "Hybrid AI agent for multi-class classification with automatic local/cloud routing (ZERO credits in local mode)", AgentStatus.PRODUCTION, "80%+ cost savings", ["product_classification", "multi_class_classification", "custom_taxonomy", "hybrid_processing"]),
    ]

    for agent_id, name, desc, status, roi, caps in hybrid_ai_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.CORE_UTILITY,
            status=status,
            description=desc,
            capabilities=caps,
            roi_impact=roi,
            file_path=f"/backend/app/agents/hybrid_ai/{agent_id.replace('_v1', '')}.py",
            tags=["hybrid-ai", "cost-optimization", "local-llm", "zero-credits", "ollama"]
        ))

    # Mobility Agents (12 agents)
    mobility_agents = [
        ("traffic_prediction_agent_v1", "Traffic Prediction", "Predicts traffic patterns", AgentStatus.PRODUCTION, "22% faster trip times"),
        ("route_discovery_agent_v1", "Route Discovery", "Optimal route discovery", AgentStatus.PRODUCTION, "35% distance savings"),
        ("matching_optimization_agent_v1", "Matching Optimization", "Driver-rider matching", AgentStatus.PRODUCTION, "18% higher satisfaction"),
        ("handoff_coordination_agent_v1", "Handoff Coordination", "Multi-driver coordination", AgentStatus.PRODUCTION, "28% higher utilization"),
        ("consensus_agent_v1", "Consensus Agent", "Distributed decision making", AgentStatus.PRODUCTION, "40% reduction in conflicts"),
        ("spatiotemporal_routing_agent_v1", "Spatiotemporal Routing", "Time-aware routing", AgentStatus.BETA, "30% better ETA accuracy"),
        ("geospatial_broadcast_agent_v1", "Geospatial Broadcast", "Location-based messaging", AgentStatus.BETA, None),
        ("ride_matching_agent_v1", "Ride Matching", "Intelligent ride matching", AgentStatus.BETA, None),
        ("german_traffic_agent", "German Traffic Agent", "Germany-specific traffic", AgentStatus.DEVELOPMENT, None),
    ]

    for agent_id, name, desc, status, roi in mobility_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.MOBILITY,
            status=status,
            description=desc,
            roi_impact=roi,
            file_path=f"/autonomous-ecosystem/library/agents/{agent_id}.py",
            tags=["mobility", "routing", "optimization"]
        ))

    # Technical Debt Management Agents (6 agents)
    tech_debt_agents = [
        ("technical_debt_tracking_agent", "Technical Debt Tracker", "Tracks technical debt"),
        ("architecture_review_agent", "Architecture Reviewer", "Reviews architecture"),
        ("refactoring_coordinator_agent", "Refactoring Coordinator", "Coordinates refactoring"),
        ("code_quality_monitoring_agent", "Code Quality Monitor", "Monitors code quality"),
        ("documentation_maintenance_agent", "Documentation Maintainer", "Maintains documentation"),
        ("agent_ecosystem_coordinator", "Ecosystem Coordinator", "Coordinates agent ecosystem"),
    ]

    for agent_id, name, desc in tech_debt_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.DEVELOPMENT,
            status=AgentStatus.PRODUCTION,
            description=desc,
            file_path=f"/backend/app/technical_debt_management/{agent_id}.py",
            tags=["technical-debt", "development", "maintenance"]
        ))

    # Product Enrichment Agents (7 agents)
    product_enrichment_agents = [
        ("product_intelligence_agent", "Product Intelligence Agent", "Extracts comprehensive product information using AI", ["product_intelligence", "data_extraction", "ai_analysis"]),
        ("image_discovery_agent", "Image Discovery Agent", "Finds high-quality product images", ["image_search", "visual_content", "quality_assessment"]),
        ("market_analysis_agent", "Market Analysis Agent", "Analyzes market opportunity and trends", ["market_research", "trend_analysis", "opportunity_scoring"]),
        ("competitive_intelligence_agent", "Competitive Intelligence Agent", "Analyzes competitive landscape", ["competitor_analysis", "market_positioning", "intelligence_gathering"]),
        ("pricing_strategy_agent", "Pricing Strategy Agent", "Determines optimal pricing strategies", ["pricing_optimization", "competitive_pricing", "value_based_pricing"]),
        ("customer_profiling_agent", "Customer Profiling Agent", "Creates detailed customer personas", ["customer_segmentation", "persona_development", "target_audience"]),
        ("business_model_agent", "Business Model Agent", "Creates business model recommendations", ["business_planning", "revenue_models", "value_proposition"]),
    ]

    for agent_id, name, desc, caps in product_enrichment_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.ANALYTICS,
            status=AgentStatus.PRODUCTION,
            description=desc,
            capabilities=caps,
            file_path=f"/backend/app/agents/product_enrichment_agents.py",
            tags=["product-enrichment", "ai-analysis", "market-research"]
        ))

    # Workflow Coordination Agents (3 agents)
    workflow_agents = [
        ("enrichment_workflow_coordinator", "Enrichment Workflow Coordinator", "Coordinates multi-agent enrichment workflows (APQC 13.2.1.5)", ["workflow_orchestration", "task_management", "agent_coordination"]),
        ("market_opportunity_scoring_agent", "Market Opportunity Scoring Agent", "Calculates market opportunity scores (APQC 3.1.2.5)", ["opportunity_scoring", "market_analysis", "data_aggregation"]),
        ("product_data_validation_agent", "Product Data Validation Agent", "Validates product data quality (APQC 3.3.3.5)", ["data_validation", "quality_assurance", "completeness_check"]),
    ]

    for agent_id, name, desc, caps in workflow_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.TASK_LEVEL,
            status=AgentStatus.PRODUCTION,
            description=desc,
            capabilities=caps,
            file_path=f"/backend/app/agents/{agent_id}.py",
            tags=["workflow", "coordination", "apqc-level-5"]
        ))

    # Meta Agents (2 agents)
    meta_agents = [
        ("agent_registry_sync_agent", "Agent Registry Sync Agent", "Automatically discovers and registers agents using AST parsing", ["agent_discovery", "registry_management", "metadata_extraction"]),
        ("agent_registry_updater", "Agent Registry Updater", "Updates agent registry across APQC levels", ["registry_updates", "apqc_mapping", "metadata_management"]),
    ]

    for agent_id, name, desc, caps in meta_agents:
        agents.append(Agent(
            id=agent_id,
            name=name,
            category=AgentCategory.META,
            status=AgentStatus.PRODUCTION,
            description=desc,
            capabilities=caps,
            file_path=f"/backend/app/agents/meta/{agent_id}.py",
            tags=["meta-agent", "self-improvement", "automation"]
        ))

    return agents


def get_all_swarms() -> List[AgentSwarm]:
    """Get all agent swarms"""
    swarms = []

    # Industry Swarms
    industry_swarms = [
        ("healthcare_swarm_001", "Healthcare Operations Swarm", Industry.HEALTHCARE,
         17, "hierarchical_with_feedback", "$500K - $2M annually"),
        ("finserv_swarm_001", "Financial Services Operations Swarm", Industry.FINANCIAL_SERVICES,
         20, "event_driven_with_escalation", "$2M - $10M annually"),
        ("logistics_swarm_001", "Supply Chain & Logistics Swarm", Industry.LOGISTICS,
         20, "distributed_consensus", "$1M - $5M annually"),
        ("manufacturing_swarm_001", "Smart Manufacturing Swarm", Industry.MANUFACTURING,
         20, "real_time_orchestration", "$3M - $15M annually"),
        ("retail_swarm_001", "Retail Operations Swarm", Industry.RETAIL,
         20, "customer_centric_orchestration", "$500K - $3M annually"),
        ("technology_swarm_001", "SaaS & Technology Operations Swarm", Industry.TECHNOLOGY,
         20, "continuous_deployment_pipeline", "$1M - $5M annually"),
    ]

    for swarm_id, name, industry, agent_count, pattern, roi in industry_swarms:
        swarms.append(AgentSwarm(
            id=swarm_id,
            name=name,
            description=f"Complete {industry.value} operations agent team",
            category=AgentCategory.INDUSTRY_SWARM,
            industry=industry,
            agents=[f"{industry.value}_agent_{i}" for i in range(agent_count)],
            coordination_pattern=pattern,
            use_cases=[f"{industry.value} use case {i}" for i in range(3)],
            estimated_roi=roi,
            status=AgentStatus.PRODUCTION
        ))

    # Functional Swarms
    swarms.append(AgentSwarm(
        id="mobility_routing_swarm",
        name="Mobility Routing Swarm",
        description="Production-ready mobility and routing optimization",
        category=AgentCategory.MOBILITY,
        agents=["traffic_prediction_agent_v1", "route_discovery_agent_v1",
                "matching_optimization_agent_v1", "handoff_coordination_agent_v1",
                "consensus_agent_v1"],
        coordination_pattern="distributed_consensus",
        use_cases=["Ride-sharing optimization", "Fleet management", "Traffic prediction"],
        estimated_roi="$60M+ annually",
        status=AgentStatus.PRODUCTION,
        deployment_count=1
    ))

    return swarms


def get_library_stats() -> LibraryStats:
    """Get comprehensive library statistics"""
    agents = get_all_agents()
    swarms = get_all_swarms()

    by_status = {}
    by_category = {}

    for agent in agents:
        # Use enum values (plain identifiers) as keys for JSON compatibility
        status_key = enum_value(agent.status)
        category_key = enum_value(agent.category)

        by_status[status_key] = by_status.get(status_key, 0) + 1
        by_category[category_key] = by_category.get(category_key, 0) + 1

    return LibraryStats(
        total_agents=len(agents),
        total_swarms=len(swarms),
        by_status=by_status,
        by_category=by_category,
        # these counters must look up by the serialized key values
        production_ready=by_status.get(AgentStatus.PRODUCTION.value, 0),
        in_development=by_status.get(AgentStatus.DEVELOPMENT.value, 0),
        templates_available=by_status.get(AgentStatus.TEMPLATE.value, 0),
        apqc_coverage=100.0,  # Full APQC coverage
        recent_additions=agents[:5]
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/agents", response_model=List[Agent])
async def list_agents(
    category: Optional[AgentCategory] = None,
    status: Optional[AgentStatus] = None,
    industry: Optional[Industry] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    limit: int = 100,
    offset: int = 0
):
    """
    List all agents with optional filtering
    """
    agents = get_all_agents()

    # Apply filters
    if category:
        agents = [a for a in agents if a.category == category]

    if status:
        agents = [a for a in agents if a.status == status]

    if industry:
        agents = [a for a in agents if a.industry == industry]

    if search:
        search_lower = search.lower()
        agents = [a for a in agents if
                 search_lower in a.name.lower() or
                 search_lower in a.description.lower()]

    if tags:
        agents = [a for a in agents if any(tag in a.tags for tag in tags)]

    # Pagination
    return agents[offset:offset + limit]


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get detailed information about a specific agent"""
    agents = get_all_agents()
    agent = next((a for a in agents if a.id == agent_id), None)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.get("/swarms", response_model=List[AgentSwarm])
async def list_swarms(
    category: Optional[AgentCategory] = None,
    industry: Optional[Industry] = None,
    status: Optional[AgentStatus] = None
):
    """List all agent swarms with optional filtering"""
    swarms = get_all_swarms()

    if category:
        swarms = [s for s in swarms if s.category == category]

    if industry:
        swarms = [s for s in swarms if s.industry == industry]

    if status:
        swarms = [s for s in swarms if s.status == status]

    return swarms


@router.get("/swarms/{swarm_id}", response_model=AgentSwarm)
async def get_swarm(swarm_id: str):
    """Get detailed information about a specific swarm"""
    swarms = get_all_swarms()
    swarm = next((s for s in swarms if s.id == swarm_id), None)

    if not swarm:
        raise HTTPException(status_code=404, detail="Swarm not found")

    return swarm


@router.get("/stats", response_model=LibraryStats)
async def get_stats():
    """Get comprehensive library statistics"""
    return get_library_stats()


@router.get("/categories")
async def list_categories():
    """List all available categories"""
    return {
        "categories": [cat.value for cat in AgentCategory],
        "industries": [ind.value for ind in Industry],
        "statuses": [status.value for status in AgentStatus]
    }


@router.get("/roadmap")
async def get_roadmap():
    """Get development roadmap"""
    roadmap = [
        RoadmapItem(
            id="phase_1",
            title="Core Mobility Swarm",
            description="Production deployment of mobility routing agents",
            category=AgentCategory.MOBILITY,
            priority="high",
            status="completed",
            agents_included=["traffic_prediction_agent_v1", "route_discovery_agent_v1"],
            progress_percentage=100,
            estimated_completion="2025-10-01"
        ),
        RoadmapItem(
            id="phase_2",
            title="Industry Swarms Expansion",
            description="Deploy healthcare, finserv, and logistics swarms",
            category=AgentCategory.INDUSTRY_SWARM,
            priority="high",
            status="in_progress",
            agents_included=["healthcare_swarm_001", "finserv_swarm_001"],
            progress_percentage=60,
            estimated_completion="2025-11-15"
        ),
        RoadmapItem(
            id="phase_3",
            title="APQC Level 2 Agents",
            description="Complete APQC sub-process agent development",
            category=AgentCategory.APQC_FRAMEWORK,
            priority="medium",
            status="planned",
            agents_included=[],
            progress_percentage=0,
            estimated_completion="2025-12-31"
        ),
    ]

    return {"roadmap": roadmap}


@router.get("/apqc/coverage")
async def get_apqc_coverage():
    """Get APQC framework coverage analysis"""
    return {
        "total_categories": 13,
        "categories_covered": 13,
        "coverage_percentage": 100.0,
        "level_1_coverage": 100.0,
        "level_2_coverage": 75.0,
        "categories": [
            {"id": "1.0", "name": "Vision & Strategy", "agents": 4, "coverage": 100},
            {"id": "2.0", "name": "Product Development", "agents": 6, "coverage": 100},
            {"id": "3.0", "name": "Marketing & Sales", "agents": 9, "coverage": 100},
            {"id": "4.0", "name": "Supply Chain", "agents": 9, "coverage": 100},
            {"id": "5.0", "name": "Service Delivery", "agents": 4, "coverage": 100},
            {"id": "6.0", "name": "Customer Service", "agents": 5, "coverage": 100},
            {"id": "7.0", "name": "Human Capital", "agents": 9, "coverage": 100},
            {"id": "8.0", "name": "Financial Management", "agents": 9, "coverage": 100},
            {"id": "9.0", "name": "Asset Management", "agents": 5, "coverage": 100},
            {"id": "10.0", "name": "Risk & Compliance", "agents": 7, "coverage": 100},
            {"id": "11.0", "name": "External Relations", "agents": 5, "coverage": 100},
            {"id": "12.0", "name": "Capability Development", "agents": 7, "coverage": 100},
            {"id": "13.0", "name": "Information Technology", "agents": 8, "coverage": 100},
        ]
    }


@router.post("/agents/{agent_id}/metrics")
async def update_agent_metrics(agent_id: str, metrics: Dict[str, Any]):
    """Update agent performance metrics"""
    # This would typically update a database
    return {"status": "success", "agent_id": agent_id, "metrics": metrics}
