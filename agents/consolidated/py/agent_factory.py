"""
Agent Factory API Router - Global Agent Factory as a Service (AgentFaaS)

This router exposes the Global Agent Factory capabilities as RESTful APIs, enabling
developers worldwide to generate production-ready agents that continuously improve.

Core Endpoints:
- POST /api/v1/factory/create-agent - Generate a new agent with auto-optimization
- POST /api/v1/factory/agents/{agent_id}/performance - Report agent performance (factory learns!)
- POST /api/v1/factory/evolve - Trigger factory evolution cycle
- GET /api/v1/factory/status - Get comprehensive factory status

Template Endpoints:
- GET /api/v1/factory/templates - List available templates
- GET /api/v1/factory/templates/{template_id} - Get template details
- POST /api/v1/factory/templates/recommend - Get template recommendations

Agent Endpoints:
- GET /api/v1/factory/agents/{agent_id} - Get generated agent
- GET /api/v1/factory/agents/{agent_id}/download - Download agent package
- GET /api/v1/factory/agents/{agent_id}/readme - Get agent README

Analytics Endpoints:
- GET /api/v1/factory/statistics - Factory statistics
- GET /api/v1/factory/insights - Factory insights
- GET /api/v1/factory/research/latest - Latest research integrations
- GET /api/v1/factory/performance/{agent_id} - Agent performance data

New Features in v2.0:
- Self-evolution engine
- Performance tracking and learning
- Automatic template optimization
- Research intelligence integration
- Predictive quality analysis
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import io
import zipfile

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add autonomous-ecosystem to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "autonomous-ecosystem"))

from library.core.agent_template_system import (
    AgentTemplateSystem,
    AgentSpecification,
    ComplianceFramework,
    PerformanceTier,
    DeploymentFormat,
    APQCCategory,
)
from library.core.agent_code_generator import AgentCodeGenerator
from library.agents.factory.research_intelligence_agent import ResearchIntelligenceAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/factory", tags=["Agent Factory"])

# Initialize factory systems
# V2: Now using Global Agent Factory
# Commented out due to import issues - using legacy systems directly
# from library.factory.global_agent_factory import get_factory, GlobalAgentFactory

# factory: Optional[GlobalAgentFactory] = None  # Will be initialized on startup

# Legacy systems (primary for now)
# Initialize at module level to ensure they're ready when routes are called
from pathlib import Path as PathlibPath

PathlibPath("data").mkdir(exist_ok=True)

logger.info("Initializing Agent Factory systems at module load...")
template_system = AgentTemplateSystem(db_path="data/agent_templates.db")
code_generator = AgentCodeGenerator(
    db_path="data/agent_generation.db", template_system=template_system
)
research_agent = None
logger.info("Agent Factory systems initialized at module load")


# ============================================================================
# Request/Response Models
# ============================================================================


class AgentCreationRequest(BaseModel):
    """Request to create a new agent"""

    agent_name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Agent description")
    business_objective: str = Field(..., description="Business objective")

    # Template selection
    template_id: Optional[str] = Field(None, description="Specific template ID to use")
    apqc_process: Optional[str] = Field(
        None, description="APQC process (e.g., '1.3' for Strategic Initiatives)"
    )

    # Customization
    custom_capabilities: List[str] = Field(
        default_factory=list, description="Additional capabilities"
    )
    integration_targets: List[str] = Field(
        default_factory=list, description="Agents to integrate with"
    )

    # Compliance
    compliance_frameworks: List[str] = Field(
        default_factory=list, description="Compliance frameworks (gdpr, hipaa, soc2, etc.)"
    )
    data_residency: Optional[str] = Field(
        None, description="Data residency requirement (e.g., 'EU', 'US')"
    )
    encryption_required: bool = Field(True, description="Require data encryption")

    # Performance
    performance_tier: str = Field(
        "optimized", description="Performance tier: basic, optimized, enterprise"
    )
    max_response_time_ms: int = Field(1000, description="Maximum response time in milliseconds")
    concurrent_users: int = Field(100, description="Expected concurrent users")

    # Deployment
    deployment_format: str = Field(
        "docker", description="Deployment format: docker, kubernetes, serverless, standalone"
    )
    cloud_provider: Optional[str] = Field(None, description="Cloud provider: aws, azure, gcp")

    # Additional
    industry: Optional[str] = Field(None, description="Industry vertical")
    organization_size: Optional[str] = Field(
        None, description="Organization size: startup, smb, enterprise"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "Customer Service Optimizer",
                "description": "Optimizes customer service operations with AI-powered insights",
                "business_objective": "Reduce response time by 60% while improving customer satisfaction by 35%",
                "apqc_process": "5.1",
                "compliance_frameworks": ["gdpr", "soc2"],
                "performance_tier": "enterprise",
                "deployment_format": "kubernetes",
            }
        }


class AgentCreationResponse(BaseModel):
    """Response from agent creation"""

    agent_id: str
    agent_name: str
    template_id: str
    status: str  # success, pending, failed
    message: str

    # Generated artifacts
    generated_date: str
    version: str
    lines_of_code: int
    code_quality_score: float

    # Download info
    download_url: str
    documentation_url: str

    # Compliance
    compliance_checks: Dict[str, bool]

    # Pricing (placeholder)
    pricing_tier: str
    estimated_monthly_cost: float


class TemplateListItem(BaseModel):
    """Template list item"""

    template_id: str
    name: str
    description: str
    apqc_process: str
    apqc_category: str
    business_value: str
    success_rate: float
    usage_count: int
    estimated_dev_time_hours: int


class TemplateRecommendationRequest(BaseModel):
    """Request for template recommendations"""

    business_objective: str
    industry: Optional[str] = None
    apqc_process: Optional[str] = None


class ResearchIntegrationItem(BaseModel):
    """Research integration item"""

    paper_id: str
    paper_title: str
    algorithm_name: str
    integration_status: str
    performance_improvement: Optional[float] = None
    integrated_date: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/create-agent", response_model=AgentCreationResponse)
async def create_agent(request: AgentCreationRequest, background_tasks: BackgroundTasks):
    """
    Create a new production-ready agent from specification.

    This is the primary endpoint for agent generation. It:
    1. Validates the specification
    2. Selects or recommends a template
    3. Generates agent code, tests, and documentation
    4. Performs compliance checks
    5. Packages the agent for deployment

    Returns a complete agent package ready for deployment.
    """
    try:
        logger.info(f"Creating agent: {request.agent_name}")

        # Convert request to AgentSpecification
        spec = AgentSpecification(
            agent_name=request.agent_name,
            description=request.description,
            business_objective=request.business_objective,
            template_id=request.template_id,
            apqc_process=request.apqc_process,
            custom_capabilities=request.custom_capabilities,
            integration_targets=request.integration_targets,
            compliance_frameworks=(
                [ComplianceFramework(cf) for cf in request.compliance_frameworks]
                if request.compliance_frameworks
                else []
            ),
            data_residency=request.data_residency,
            encryption_required=request.encryption_required,
            performance_tier=PerformanceTier(request.performance_tier),
            max_response_time_ms=request.max_response_time_ms,
            concurrent_users=request.concurrent_users,
            deployment_format=DeploymentFormat(request.deployment_format),
            cloud_provider=request.cloud_provider,
            industry=request.industry,
            organization_size=request.organization_size,
        )

        # Generate agent
        generated = code_generator.generate_agent(spec)

        # Record usage in template system
        if hasattr(generated, "template_id"):
            template_system.record_usage(
                template_id=generated.template_id,
                agent_name=generated.agent_name,
                deployment_format=spec.deployment_format,
                compliance_frameworks=spec.compliance_frameworks,
                success=True,
                performance_metrics={
                    "lines_of_code": generated.lines_of_code,
                    "code_quality_score": generated.code_quality_score,
                },
            )

        # Determine pricing tier
        pricing_tier = "standard"
        if spec.performance_tier == PerformanceTier.ENTERPRISE:
            pricing_tier = "premium"
        elif spec.performance_tier == PerformanceTier.BASIC:
            pricing_tier = "basic"

        # Calculate estimated cost (placeholder)
        base_cost = {"basic": 49, "standard": 99, "premium": 249}
        estimated_monthly_cost = base_cost.get(pricing_tier, 99)

        return AgentCreationResponse(
            agent_id=generated.agent_id,
            agent_name=generated.agent_name,
            template_id=generated.template_id,
            status="success",
            message=f"Agent '{generated.agent_name}' generated successfully",
            generated_date=generated.generated_date.isoformat(),
            version=generated.version,
            lines_of_code=generated.lines_of_code,
            code_quality_score=generated.code_quality_score,
            download_url=f"/api/v1/factory/agents/{generated.agent_id}/download",
            documentation_url=f"/api/v1/factory/agents/{generated.agent_id}/readme",
            compliance_checks=generated.compliance_checks,
            pricing_tier=pricing_tier,
            estimated_monthly_cost=estimated_monthly_cost,
        )

    except ValueError as e:
        logger.error(f"Validation error creating agent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/templates", response_model=List[TemplateListItem])
async def list_templates(
    apqc_category: Optional[str] = Query(None, description="Filter by APQC category"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    min_success_rate: float = Query(0.0, description="Minimum success rate"),
):
    """
    List all available agent templates.

    Templates are APQC-aligned blueprints for common business processes.
    Each template includes pre-configured capabilities, compliance requirements,
    and performance optimizations.
    """
    try:
        # Convert apqc_category string to enum if provided
        category_enum = None
        if apqc_category:
            try:
                category_enum = APQCCategory(apqc_category)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid APQC category: {apqc_category}"
                )

        # Search templates
        results = template_system.search_templates(
            apqc_category=category_enum, keyword=keyword, min_success_rate=min_success_rate
        )

        # Get full template details for each result
        templates = []
        for result in results:
            template_data = template_system.get_template(result["template_id"])
            if template_data:
                # template_data is an AgentTemplate dataclass, access attributes directly
                templates.append(
                    TemplateListItem(
                        template_id=result["template_id"],
                        name=result["name"],
                        description=result.get("description", ""),
                        apqc_process=result.get("apqc_process", ""),
                        apqc_category=(
                            template_data.apqc_category.value
                            if hasattr(template_data, "apqc_category")
                            else ""
                        ),
                        business_value=result.get("business_value", ""),
                        success_rate=result.get("success_rate", 0.0),
                        usage_count=(
                            template_data.usage_count
                            if hasattr(template_data, "usage_count")
                            else 0
                        ),
                        estimated_dev_time_hours=(
                            template_data.estimated_dev_time_hours
                            if hasattr(template_data, "estimated_dev_time_hours")
                            else 0
                        ),
                    )
                )

        return templates

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Get detailed information about a specific template.

    Returns full template specification including:
    - Capabilities and requirements
    - Compliance frameworks
    - Performance characteristics
    - Example use cases
    - Success metrics
    """
    try:
        template = template_system.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/recommend")
async def recommend_templates(request: TemplateRecommendationRequest):
    """
    Get template recommendations based on business objective.

    Uses AI-powered matching to recommend the best templates for your use case.
    Considers:
    - Business objective similarity
    - Industry alignment
    - APQC process match
    - Success rate history
    """
    try:
        spec = AgentSpecification(
            agent_name="Recommendation Query",
            description="",
            business_objective=request.business_objective,
            apqc_process=request.apqc_process,
            industry=request.industry,
        )

        recommendations = template_system.recommend_template(spec)

        return {"recommendations": recommendations, "total_count": len(recommendations)}

    except Exception as e:
        logger.error(f"Error recommending templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get details about a generated agent.

    Returns agent metadata, generation details, and compliance status.
    """
    try:
        agent = code_generator.get_generated_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/download")
async def download_agent(agent_id: str):
    """
    Download generated agent as a ZIP package.

    Package includes:
    - Agent Python code
    - Test suite
    - requirements.txt
    - Dockerfile
    - README.md
    - Configuration examples
    """
    try:
        agent = code_generator.get_generated_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add agent code
            if isinstance(agent, dict):
                zip_file.writestr(f"{agent_id}/{agent_id}.py", agent.get("agent_code", ""))
                zip_file.writestr(
                    f"{agent_id}/tests/test_{agent_id}.py", agent.get("test_code", "")
                )
                zip_file.writestr(f"{agent_id}/README.md", agent.get("readme_md", ""))
                zip_file.writestr(f"{agent_id}/requirements.txt", agent.get("requirements_txt", ""))
                zip_file.writestr(f"{agent_id}/Dockerfile", agent.get("dockerfile", ""))
            else:
                zip_file.writestr(f"{agent_id}/{agent_id}.py", agent.agent_code)
                zip_file.writestr(f"{agent_id}/tests/test_{agent_id}.py", agent.test_code)
                zip_file.writestr(f"{agent_id}/README.md", agent.readme_md)
                zip_file.writestr(f"{agent_id}/requirements.txt", agent.requirements_txt)
                zip_file.writestr(f"{agent_id}/Dockerfile", agent.dockerfile)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={agent_id}.zip"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/readme")
async def get_agent_readme(agent_id: str):
    """Get agent README documentation"""
    try:
        agent = code_generator.get_generated_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        if isinstance(agent, dict):
            readme = agent.get("readme_md", "")
        else:
            readme = agent.readme_md

        return {"agent_id": agent_id, "readme": readme}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting README: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_factory_statistics():
    """
    Get comprehensive factory statistics.

    Returns metrics on:
    - Total agents generated
    - Template usage
    - Code quality averages
    - Research integrations
    - Compliance trends
    """
    try:
        # Template statistics
        template_stats = template_system.get_statistics()

        # Generation statistics
        generation_stats = code_generator.get_statistics()

        # Research statistics (if available)
        research_stats = {}
        global research_agent
        if research_agent:
            try:
                research_result = await research_agent.execute(
                    {"action": "get_insights", "time_range_days": 30}
                )
                if research_result.get("status") == "success":
                    research_stats = research_result.get("data", {})
            except Exception as e:
                logger.warning(f"Could not get research stats: {str(e)}")

        return {
            "templates": template_stats,
            "generation": generation_stats,
            "research": research_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/latest", response_model=List[ResearchIntegrationItem])
async def get_latest_research(
    limit: int = Query(10, description="Number of items to return"),
    status: Optional[str] = Query(
        None, description="Filter by status: discovered, integrated, validated"
    ),
):
    """
    Get latest research integrations from Research Intelligence Agent.

    Shows cutting-edge algorithms and techniques that have been automatically
    discovered and integrated into the factory.
    """
    try:
        global research_agent

        # Lazy initialize research agent
        if research_agent is None:
            research_agent = ResearchIntelligenceAgent()

        # Get insights
        result = await research_agent.execute({"action": "get_insights", "time_range_days": 30})

        if result.get("status") != "success":
            return []

        data = result.get("data", {})
        integrations = data.get("recent_integrations", [])

        # Convert to response format
        items = []
        for integration in integrations[:limit]:
            # Filter by status if provided
            if status and integration.get("integration_status") != status:
                continue

            items.append(
                ResearchIntegrationItem(
                    paper_id=integration.get("paper_id", ""),
                    paper_title=integration.get("paper_title", ""),
                    algorithm_name=integration.get("algorithm_name", ""),
                    integration_status=integration.get("integration_status", "discovered"),
                    performance_improvement=integration.get("performance_improvement"),
                    integrated_date=integration.get("integrated_date", datetime.now().isoformat()),
                )
            )

        return items

    except Exception as e:
        logger.error(f"Error getting research integrations: {str(e)}")
        # Return empty list instead of error to avoid breaking the API
        return []


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agent Factory API",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "self-evolution",
            "performance-tracking",
            "research-integration",
            "auto-optimization",
        ],
    }


# ============================================================================
# NEW V2.0 Endpoints - Self-Evolution & Intelligence
# ============================================================================


@router.post("/agents/{agent_id}/performance")
async def report_agent_performance(agent_id: str, metrics: Dict[str, Any]):
    """
    Report agent performance data - Factory learns from this!

    This is where the magic happens. Every time you report performance,
    the factory learns and improves. Your data helps make better agents
    for everyone.

    Performance Metrics:
    - deployment_success: bool
    - total_executions: int
    - successful_executions: int
    - avg_response_time: float (ms)
    - user_satisfaction: float (1-5)
    - business_value: float

    Returns:
    - Analysis of the performance
    - Factory learning status
    - Insights discovered
    """
    try:
        global factory

        if not factory:
            raise HTTPException(status_code=503, detail="Factory not initialized")

        # Report performance to factory
        result = await factory.report_performance(agent_id, metrics)

        return {
            "status": "success",
            "agent_id": agent_id,
            "factory_learning": result.get("factory_learning"),
            "reward_signal": result.get("reward"),
            "insights_count": result.get("insights_count"),
            "message": "Performance data recorded - factory is learning!",
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reporting performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evolve")
async def trigger_evolution(background_tasks: BackgroundTasks):
    """
    Trigger factory evolution cycle

    Forces the factory to evolve immediately based on accumulated data.
    Normally this happens automatically every 24 hours, but you can
    trigger it manually.

    Evolution Process:
    1. Apply validated insights to templates
    2. Integrate latest research findings
    3. Optimize templates based on performance
    4. Update factory statistics

    Returns progress of evolution cycle.
    """
    try:
        global factory

        if not factory:
            raise HTTPException(status_code=503, detail="Factory not initialized")

        # Trigger evolution in background
        logger.info("Manual evolution cycle triggered")

        evolution_results = await factory.evolve()

        return {
            "status": "completed",
            "templates_evolved": evolution_results["templates_evolved"],
            "insights_applied": evolution_results["insights_applied"],
            "research_integrated": evolution_results["research_integrated"],
            "improvements": evolution_results.get("improvements", []),
            "message": "Factory evolution cycle completed",
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_factory_status():
    """
    Get comprehensive factory status

    Returns detailed information about:
    - Factory operational status
    - Evolution strategy
    - Performance statistics
    - Learning metrics
    - Insights discovered
    - Research integration status

    This endpoint shows you how well the factory is learning and improving.
    """
    try:
        global factory

        if not factory:
            # Return basic status if factory not initialized
            return {
                "status": "initializing",
                "message": "Factory is starting up",
                "timestamp": datetime.now().isoformat(),
            }

        # Get comprehensive status
        status = await factory.get_factory_status()

        return {**status, "api_version": "2.0.0", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error getting factory status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_factory_insights(
    insight_type: Optional[str] = Query(
        None, description="Filter by type: pattern, best_practice, optimization"
    ),
    limit: int = Query(50, description="Number of insights to return"),
):
    """
    Get factory insights

    Insights are patterns and best practices discovered by the factory
    from analyzing agent performance data.

    Types of insights:
    - pattern: Discovered patterns in successful agents
    - anti_pattern: Patterns in unsuccessful agents (what to avoid)
    - best_practice: Validated best practices
    - optimization: Performance optimizations that work

    Each insight includes:
    - Confidence score
    - Supporting evidence (sample size)
    - Impact level
    - Application areas
    """
    try:
        global factory

        if not factory:
            raise HTTPException(status_code=503, detail="Factory not initialized")

        # Get insights
        insights = await factory.get_insights(insight_type=insight_type)

        # Limit results
        insights = insights[:limit]

        return {
            "status": "success",
            "total_insights": len(insights),
            "insights": insights,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{agent_id}")
async def get_agent_performance(agent_id: str):
    """
    Get detailed performance data for a specific agent

    Returns all tracked performance metrics for an agent:
    - Deployment metrics
    - Runtime performance
    - Quality scores
    - User satisfaction
    - Business value

    This data is used by the factory to learn and improve.
    """
    try:
        global factory

        if not factory:
            raise HTTPException(status_code=503, detail="Factory not initialized")

        if agent_id not in factory.performance_data:
            raise HTTPException(
                status_code=404, detail=f"No performance data for agent: {agent_id}"
            )

        perf_data = factory.performance_data[agent_id]

        return {
            "status": "success",
            "agent_id": agent_id,
            "template_id": perf_data.template_id,
            "generated_date": perf_data.generated_date,
            "deployment": {
                "success": perf_data.deployment_success,
                "time_seconds": perf_data.deployment_time_seconds,
                "issues": perf_data.deployment_issues,
            },
            "runtime": {
                "total_executions": perf_data.total_executions,
                "successful_executions": perf_data.successful_executions,
                "error_rate": perf_data.error_rate,
                "avg_response_time_ms": perf_data.average_response_time_ms,
            },
            "quality": {
                "code_quality_score": perf_data.code_quality_score,
                "test_coverage": perf_data.test_coverage,
                "security_score": perf_data.security_score,
            },
            "business": {
                "user_satisfaction": perf_data.user_satisfaction_score,
                "business_value": perf_data.business_value_delivered,
                "cost_efficiency": perf_data.cost_efficiency,
            },
            "feedback": {
                "user_feedback_count": len(perf_data.user_feedback),
                "issue_reports_count": len(perf_data.issue_reports),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Initialize on startup
# ============================================================================


@router.on_event("startup")
async def startup_event():
    """Initialize factory on startup"""
    global factory, template_system, code_generator, research_agent

    logger.info("Agent Factory API v2.0 starting up...")

    # Verify databases exist
    Path("data").mkdir(exist_ok=True)

    # Initialize factory systems directly (legacy mode)
    global template_system, code_generator, research_agent

    logger.info("Initializing Agent Factory systems...")
    template_system = AgentTemplateSystem(db_path="data/agent_templates.db")
    code_generator = AgentCodeGenerator(
        db_path="data/agent_generation.db", template_system=template_system
    )

    logger.info("✅ Agent Factory systems initialized")

    # Note: Global Agent Factory (V2) is temporarily disabled due to import conflicts
    # Using direct initialization of template system and code generator instead

    logger.info("Agent Factory API ready")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Agent Factory API shutting down...")
