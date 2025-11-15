"""
Workflow Template Library

Pre-built workflow templates for common business scenarios!

This library provides ready-to-use workflows spanning multiple APQC categories,
demonstrating complete business process automation.

Usage:
    from src.superstandard.templates import get_template_library

    library = get_template_library()
    template = library.get_template("new_product_launch")
    workflow = template.instantiate(params={"budget": 100000})
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..orchestration import WorkflowDefinition, Task


@dataclass
class WorkflowTemplate:
    """Pre-built workflow template"""
    template_id: str
    name: str
    description: str
    categories: List[str]  # APQC categories involved
    capabilities_required: List[str]
    estimated_duration: str  # e.g., "2-4 weeks"
    estimated_cost_range: str  # e.g., "$500-$1000"
    business_value: str
    use_cases: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    tasks_template: List[Dict[str, Any]] = field(default_factory=list)

    def instantiate(self, params: Optional[Dict[str, Any]] = None) -> WorkflowDefinition:
        """
        Instantiate template into actual workflow

        Args:
            params: Template parameters (budget, timeline, etc.)

        Returns:
            WorkflowDefinition ready for execution
        """
        # Merge parameters
        workflow_params = {**self.parameters, **(params or {})}

        # Create tasks from template
        tasks = []
        for i, task_template in enumerate(self.tasks_template, 1):
            task = Task(
                task_id=f"task_{i}",
                name=task_template["name"],
                capability=task_template["capability"],
                description=task_template.get("description", ""),
                depends_on=task_template.get("depends_on", []),
                input_data=task_template.get("input_data", {}),
                max_cost=workflow_params.get("max_cost_per_task"),
                min_quality=workflow_params.get("min_quality", 0.85)
            )
            tasks.append(task)

        # Create workflow
        workflow = WorkflowDefinition(
            workflow_id=f"{self.template_id}_{int(datetime.now().timestamp())}",
            name=f"{self.name} - {datetime.now().strftime('%Y-%m-%d')}",
            description=self.description,
            tasks=tasks,
            total_budget=workflow_params.get("total_budget", 1000.0),
            metadata={
                "template_id": self.template_id,
                "template_name": self.name,
                "categories": self.categories,
                "use_case": workflow_params.get("use_case", "General"),
                **workflow_params
            }
        )

        return workflow


class WorkflowTemplateLibrary:
    """Library of pre-built workflow templates"""

    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all pre-built templates"""

        # Template 1: New Product Launch (Cross-category mega-workflow!)
        self.templates["new_product_launch"] = WorkflowTemplate(
            template_id="new_product_launch",
            name="New Product Launch - Strategy to Market",
            description="Complete new product launch from strategic planning through development to marketing",
            categories=["1.0 - Vision and Strategy", "2.0 - Product Development", "3.0 - Marketing and Sales"],
            capabilities_required=[
                "market_research", "competitive_analysis", "strategic_planning",
                "product_ideation", "requirements_elicitation", "product_design",
                "prototype_development", "user_testing", "product_testing",
                "launch_planning", "brand_strategy", "campaign_planning"
            ],
            estimated_duration="3-6 months",
            estimated_cost_range="$100-$200",
            business_value="Launch successful new product with market validation and strategic alignment",
            use_cases=[
                "New product introduction",
                "Market expansion with new offering",
                "Innovation initiative",
                "Competitive response product"
            ],
            tasks_template=[
                # Phase 1: Strategic Foundation (Category 1.0)
                {"name": "Market Research & Analysis", "capability": "market_research", "depends_on": []},
                {"name": "Competitive Analysis", "capability": "competitive_analysis", "depends_on": []},
                {"name": "Strategic Planning", "capability": "strategic_planning", "depends_on": ["task_1", "task_2"]},

                # Phase 2: Product Development (Category 2.0)
                {"name": "Product Ideation", "capability": "product_ideation", "depends_on": ["task_3"]},
                {"name": "Requirements Gathering", "capability": "requirements_elicitation", "depends_on": ["task_4"]},
                {"name": "Product Design", "capability": "product_design", "depends_on": ["task_5"]},
                {"name": "Prototype Development", "capability": "prototype_development", "depends_on": ["task_6"]},
                {"name": "User Testing", "capability": "user_testing", "depends_on": ["task_7"]},
                {"name": "Product Testing & QA", "capability": "product_testing", "depends_on": ["task_8"]},

                # Phase 3: Go-to-Market (Category 3.0)
                {"name": "Brand Strategy", "capability": "brand_strategy", "depends_on": ["task_9"]},
                {"name": "Market Segmentation", "capability": "market_segmentation", "depends_on": ["task_9"]},
                {"name": "Campaign Planning", "capability": "campaign_planning", "depends_on": ["task_10", "task_11"]},
                {"name": "Launch Execution", "capability": "launch_planning", "depends_on": ["task_12"]},
            ]
        )

        # Template 2: Marketing Campaign Development
        self.templates["marketing_campaign"] = WorkflowTemplate(
            template_id="marketing_campaign",
            name="Integrated Marketing Campaign",
            description="Plan and execute integrated marketing campaign across channels",
            categories=["3.0 - Marketing and Sales"],
            capabilities_required=[
                "market_segmentation", "campaign_planning", "content_strategy",
                "digital_marketing", "marketing_analytics"
            ],
            estimated_duration="1-2 months",
            estimated_cost_range="$40-$80",
            business_value="Drive lead generation and brand awareness through integrated campaign",
            use_cases=[
                "Product launch campaign",
                "Brand awareness initiative",
                "Lead generation campaign",
                "Seasonal promotion"
            ],
            tasks_template=[
                {"name": "Market Segmentation", "capability": "market_segmentation", "depends_on": []},
                {"name": "Campaign Planning", "capability": "campaign_planning", "depends_on": ["task_1"]},
                {"name": "Content Strategy", "capability": "content_strategy", "depends_on": ["task_2"]},
                {"name": "Digital Marketing Execution", "capability": "digital_marketing", "depends_on": ["task_3"]},
                {"name": "Campaign Analytics", "capability": "marketing_analytics", "depends_on": ["task_4"]},
            ]
        )

        # Template 3: Product Enhancement Cycle
        self.templates["product_enhancement"] = WorkflowTemplate(
            template_id="product_enhancement",
            name="Product Enhancement Cycle",
            description="Identify, prioritize, and implement product enhancements based on performance and feedback",
            categories=["2.0 - Product Development", "3.0 - Marketing and Sales"],
            capabilities_required=[
                "performance_monitoring", "market_research", "enhancement_identification",
                "requirements_elicitation", "product_design", "product_testing"
            ],
            estimated_duration="2-3 months",
            estimated_cost_range="$60-$100",
            business_value="Improve product-market fit and customer satisfaction through data-driven enhancements",
            use_cases=[
                "Continuous product improvement",
                "Feature prioritization",
                "Customer feedback response",
                "Competitive feature parity"
            ],
            tasks_template=[
                {"name": "Product Performance Monitoring", "capability": "performance_monitoring", "depends_on": []},
                {"name": "Market Research", "capability": "market_research", "depends_on": []},
                {"name": "Enhancement Identification", "capability": "enhancement_identification", "depends_on": ["task_1", "task_2"]},
                {"name": "Requirements Gathering", "capability": "requirements_elicitation", "depends_on": ["task_3"]},
                {"name": "Enhancement Design", "capability": "product_design", "depends_on": ["task_4"]},
                {"name": "Testing & Validation", "capability": "product_testing", "depends_on": ["task_5"]},
            ]
        )

        # Template 4: Strategic Planning Cycle
        self.templates["strategic_planning"] = WorkflowTemplate(
            template_id="strategic_planning",
            name="Annual Strategic Planning",
            description="Comprehensive annual strategic planning cycle",
            categories=["1.0 - Vision and Strategy"],
            capabilities_required=[
                "market_research", "competitive_analysis", "internal_analysis",
                "swot_analysis", "strategic_planning", "strategic_vision",
                "initiative_design", "kpi_design"
            ],
            estimated_duration="1-2 months",
            estimated_cost_range="$80-$120",
            business_value="Align organization around clear strategy and initiatives for the year",
            use_cases=[
                "Annual planning process",
                "Strategic review and refresh",
                "New CEO strategic planning",
                "Pivotal year planning"
            ],
            tasks_template=[
                {"name": "Market Research", "capability": "market_research", "depends_on": []},
                {"name": "Competitive Analysis", "capability": "competitive_analysis", "depends_on": []},
                {"name": "Internal Analysis", "capability": "internal_analysis", "depends_on": []},
                {"name": "SWOT Analysis", "capability": "swot_analysis", "depends_on": ["task_1", "task_2", "task_3"]},
                {"name": "Strategic Vision Development", "capability": "vision_creation", "depends_on": ["task_4"]},
                {"name": "Strategic Planning", "capability": "strategic_planning", "depends_on": ["task_5"]},
                {"name": "Initiative Design", "capability": "initiative_design", "depends_on": ["task_6"]},
                {"name": "KPI Design", "capability": "kpi_design", "depends_on": ["task_7"]},
            ]
        )

        # Template 5: Sales Pipeline Optimization
        self.templates["sales_optimization"] = WorkflowTemplate(
            template_id="sales_optimization",
            name="Sales Pipeline Optimization",
            description="Optimize sales pipeline and improve conversion rates",
            categories=["3.0 - Marketing and Sales"],
            capabilities_required=[
                "pipeline_management", "sales_enablement", "lead_generation",
                "marketing_analytics", "customer_acquisition"
            ],
            estimated_duration="1 month",
            estimated_cost_range="$40-$60",
            business_value="Increase sales efficiency and conversion rates",
            use_cases=[
                "Sales performance improvement",
                "Pipeline health optimization",
                "Sales team enablement",
                "Lead quality improvement"
            ],
            tasks_template=[
                {"name": "Pipeline Analysis", "capability": "pipeline_management", "depends_on": []},
                {"name": "Lead Generation Review", "capability": "lead_generation", "depends_on": []},
                {"name": "Analytics & Insights", "capability": "marketing_analytics", "depends_on": ["task_1", "task_2"]},
                {"name": "Sales Enablement", "capability": "sales_enablement", "depends_on": ["task_3"]},
                {"name": "Acquisition Strategy Update", "capability": "acquisition_strategy", "depends_on": ["task_3"]},
            ]
        )

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(self) -> List[WorkflowTemplate]:
        """List all available templates"""
        return list(self.templates.values())

    def search_templates(
        self,
        category: Optional[str] = None,
        capability: Optional[str] = None,
        use_case: Optional[str] = None
    ) -> List[WorkflowTemplate]:
        """Search templates by criteria"""
        results = list(self.templates.values())

        if category:
            results = [t for t in results if category in t.categories]

        if capability:
            results = [t for t in results if capability in t.capabilities_required]

        if use_case:
            use_case_lower = use_case.lower()
            results = [t for t in results
                      if any(use_case_lower in uc.lower() for uc in t.use_cases)]

        return results

    def show_catalog(self):
        """Display template catalog"""
        print("\n" + "="*80)
        print("📚 WORKFLOW TEMPLATE LIBRARY")
        print("="*80)
        print(f"\n   Available Templates: {len(self.templates)}")

        for template in self.list_templates():
            print(f"\n📋 {template.name}")
            print(f"   ID: {template.template_id}")
            print(f"   Categories: {', '.join(template.categories)}")
            print(f"   Duration: {template.estimated_duration}")
            print(f"   Cost: {template.estimated_cost_range}")
            print(f"   Tasks: {len(template.tasks_template)}")
            print(f"   Value: {template.business_value}")


# Global singleton
_template_library = None

def get_template_library() -> WorkflowTemplateLibrary:
    """Get global template library instance"""
    global _template_library
    if _template_library is None:
        _template_library = WorkflowTemplateLibrary()
    return _template_library
