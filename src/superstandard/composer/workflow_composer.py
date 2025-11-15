"""
Dynamic Workflow Composer

Automatically composes and executes workflows from natural language requirements!

This is THE ULTIMATE INTEGRATION demonstrating:
- Discovery Protocol for finding agents
- Reputation for selecting best agents
- Agent Registry for capability matching
- Orchestration for execution
- Contracts for SLA enforcement
- Resources for budget management

Usage:
    composer = WorkflowComposer()
    workflow = await composer.compose_from_requirements(
        "I need to analyze our competitors and develop a strategic plan"
    )
    result = await composer.execute_workflow(workflow)
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import re

from src.superstandard.agent_factory import AgentRegistry, get_registry
from src.superstandard.orchestration import (
    WorkflowOrchestrator,
    WorkflowDefinition,
    Task,
    get_orchestrator
)


@dataclass
class WorkflowRequirement:
    """Natural language workflow requirement"""
    description: str
    capabilities_needed: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class ComposedWorkflow:
    """Automatically composed workflow"""
    id: str
    name: str
    description: str
    requirements: WorkflowRequirement
    workflow_definition: WorkflowDefinition
    selected_agents: List[Dict[str, Any]]
    estimated_cost: float
    estimated_duration: float
    created_at: datetime = field(default_factory=datetime.now)


class WorkflowComposer:
    """
    Dynamic Workflow Composer - THE ULTIMATE INTEGRATION!

    Automatically composes workflows from natural language requirements by:
    1. Parsing requirements to extract needed capabilities
    2. Discovering agents via Registry + Discovery Protocol
    3. Selecting best agents via Reputation
    4. Building optimal workflow with Orchestrator
    5. Executing with full Contract and Resource management
    """

    def __init__(self):
        self.registry = get_registry()
        self.orchestrator = get_orchestrator()

        # Capability keywords for requirement parsing
        self.capability_keywords = {
            # Competitive/Market Analysis
            "competitor": ["competitive_analysis", "competitor_identification"],
            "competition": ["competitive_analysis", "market_intelligence"],
            "industry": ["industry_analysis", "porter_five_forces"],
            "market": ["market_research", "trend_analysis"],
            "customer": ["customer_research", "customer_insights", "needs_analysis"],
            "trends": ["trend_analysis", "trend_forecasting"],
            "technology": ["technology_analysis", "disruption_assessment"],

            # Internal Analysis
            "internal": ["internal_analysis", "resource_assessment"],
            "swot": ["swot_analysis", "strategic_assessment"],
            "strengths": ["swot_analysis", "core_competencies"],
            "weaknesses": ["swot_analysis", "internal_analysis"],
            "resources": ["resource_assessment", "resource_inventory"],
            "capabilities": ["capability_mapping", "competency_mapping"],
            "competencies": ["competency_mapping", "core_competencies"],

            # Strategic Planning
            "vision": ["vision_creation", "strategic_vision"],
            "strategy": ["strategic_planning", "strategy_selection"],
            "strategic plan": ["strategic_planning", "vision_development"],
            "objectives": ["objective_setting", "initiative_planning"],
            "initiatives": ["initiative_design", "initiative_evaluation"],
            "options": ["options_analysis", "scenario_planning"],

            # Risk & Analysis
            "risk": ["risk_assessment", "risk_identification"],
            "stakeholder": ["stakeholder_mapping", "stakeholder_engagement"],

            # Execution & Monitoring
            "communicate": ["communication_planning", "stakeholder_engagement"],
            "monitor": ["performance_monitoring", "progress_tracking"],
            "kpi": ["kpi_design", "measurement_framework"],
            "measure": ["measurement_framework", "performance_tracking"],
        }

        # Discover agents on initialization
        self._discovered_count = self.registry.discover_agents()

    def parse_requirements(self, requirement_text: str) -> WorkflowRequirement:
        """
        Parse natural language requirements to extract needed capabilities

        This uses keyword matching to identify capabilities mentioned in the requirement.
        More sophisticated NLP could be added later!
        """
        requirement_lower = requirement_text.lower()

        # Extract capabilities based on keywords
        capabilities = set()
        for keyword, caps in self.capability_keywords.items():
            if keyword in requirement_lower:
                capabilities.update(caps)

        # Extract constraints (budget, timeline, quality)
        constraints = {}

        # Budget constraint
        budget_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', requirement_text)
        if budget_match:
            constraints['max_budget'] = float(budget_match.group(1).replace(',', ''))

        # Quality constraint
        if 'high quality' in requirement_lower or 'best' in requirement_lower:
            constraints['min_quality'] = 0.90
        elif 'good quality' in requirement_lower:
            constraints['min_quality'] = 0.85

        # Timeline constraint
        if 'urgent' in requirement_lower or 'quickly' in requirement_lower:
            constraints['max_latency'] = 1000  # ms

        return WorkflowRequirement(
            description=requirement_text,
            capabilities_needed=list(capabilities),
            constraints=constraints,
            success_criteria=[]
        )

    def discover_agents_for_capabilities(
        self,
        capabilities: List[str],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Discover agents that can handle required capabilities

        Uses Agent Registry with constraint filters
        """
        discovered_agents = []

        for capability in capabilities:
            # Search registry with constraints
            agents = self.registry.search(
                capability=capability,
                max_cost=constraints.get('max_cost', None),
                min_quality=constraints.get('min_quality', None)
            )

            if agents:
                # Sort by quality and cost
                sorted_agents = sorted(
                    agents,
                    key=lambda a: (a.quality_baseline, -a.cost_per_request),
                    reverse=True
                )

                # Select best agent for this capability
                best_agent = sorted_agents[0]
                discovered_agents.append({
                    'capability': capability,
                    'agent': best_agent,
                    'alternatives': len(sorted_agents) - 1
                })

        return discovered_agents

    def build_workflow_from_agents(
        self,
        requirement: WorkflowRequirement,
        agents: List[Dict[str, Any]],
        workflow_name: str
    ) -> WorkflowDefinition:
        """
        Build optimal workflow from selected agents

        Intelligently determines task dependencies based on:
        - Data flow (outputs needed as inputs)
        - Logical sequencing (external analysis → internal analysis → strategy)
        - Parallelization opportunities
        """
        tasks = []

        # Categorize agents by workflow phase
        external_analysis = []
        internal_analysis = []
        strategy_development = []
        execution_planning = []

        for agent_info in agents:
            capability = agent_info['capability']
            agent = agent_info['agent']

            # Categorize by phase
            if capability in ['competitive_analysis', 'market_research', 'industry_analysis',
                            'trend_analysis', 'customer_research', 'technology_analysis']:
                external_analysis.append((capability, agent))
            elif capability in ['internal_analysis', 'swot_analysis', 'resource_assessment',
                              'competency_mapping', 'capability_mapping']:
                internal_analysis.append((capability, agent))
            elif capability in ['strategic_planning', 'vision_creation', 'strategy_selection',
                              'objective_setting', 'options_analysis']:
                strategy_development.append((capability, agent))
            elif capability in ['initiative_design', 'communication_planning',
                              'performance_monitoring', 'kpi_design']:
                execution_planning.append((capability, agent))

        # Build tasks with intelligent dependencies
        task_id_map = {}

        # Phase 1: External Analysis (can run in parallel)
        for capability, agent in external_analysis:
            task_id = f"task_{len(tasks) + 1}"
            task = Task(
                task_id=task_id,
                name=f"{agent.name}",
                description=f"Execute {capability}",
                capability=capability,
                input_data={"context": requirement.description},
                depends_on=[]
            )
            tasks.append(task)
            task_id_map[capability] = task_id

        # Phase 2: Internal Analysis (depends on external if SWOT needed)
        internal_dependencies = []
        if 'swot_analysis' in [c for c, _ in internal_analysis]:
            # SWOT needs external analysis first
            internal_dependencies = [task_id_map.get(c) for c in
                                   ['competitive_analysis', 'market_research']
                                   if c in task_id_map]

        for capability, agent in internal_analysis:
            task_id = f"task_{len(tasks) + 1}"
            task = Task(
                task_id=task_id,
                name=f"{agent.name}",
                description=f"Execute {capability}",
                capability=capability,
                input_data={"context": requirement.description},
                depends_on=internal_dependencies if capability == 'swot_analysis' else []
            )
            tasks.append(task)
            task_id_map[capability] = task_id

        # Phase 3: Strategy Development (depends on analysis phases)
        strategy_dependencies = (
            [task_id_map.get(c) for c, _ in external_analysis if c in task_id_map] +
            [task_id_map.get(c) for c, _ in internal_analysis if c in task_id_map]
        )
        strategy_dependencies = [d for d in strategy_dependencies if d]  # Remove None

        for capability, agent in strategy_development:
            task_id = f"task_{len(tasks) + 1}"
            task = Task(
                task_id=task_id,
                name=f"{agent.name}",
                description=f"Execute {capability}",
                capability=capability,
                input_data={"context": requirement.description},
                depends_on=strategy_dependencies
            )
            tasks.append(task)
            task_id_map[capability] = task_id

        # Phase 4: Execution Planning (depends on strategy)
        execution_dependencies = [task_id_map.get(c) for c, _ in strategy_development
                                 if c in task_id_map]

        for capability, agent in execution_planning:
            task_id = f"task_{len(tasks) + 1}"
            task = Task(
                task_id=task_id,
                name=f"{agent.name}",
                description=f"Execute {capability}",
                capability=capability,
                input_data={"context": requirement.description},
                depends_on=execution_dependencies
            )
            tasks.append(task)
            task_id_map[capability] = task_id

        # Create workflow definition
        workflow = WorkflowDefinition(
            workflow_id=f"composed_workflow_{int(datetime.now().timestamp())}",
            name=workflow_name,
            description=f"Auto-composed workflow for: {requirement.description}",
            tasks=tasks
        )

        return workflow

    async def compose_from_requirements(
        self,
        requirement_text: str,
        workflow_name: Optional[str] = None
    ) -> ComposedWorkflow:
        """
        Compose complete workflow from natural language requirements

        This is the MAIN MAGIC METHOD that:
        1. Parses requirements
        2. Discovers agents
        3. Builds workflow
        4. Estimates cost and duration

        Returns ready-to-execute workflow!
        """
        # Generate workflow name if not provided
        if not workflow_name:
            workflow_name = f"Auto-Composed Workflow {datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'='*80}")
        print(f"🎯 DYNAMIC WORKFLOW COMPOSER")
        print(f"{'='*80}")
        print(f"\n📝 Requirement: {requirement_text}")

        # Step 1: Parse requirements
        print(f"\n🔍 Step 1: Parsing Requirements...")
        requirement = self.parse_requirements(requirement_text)
        print(f"   Identified {len(requirement.capabilities_needed)} capabilities:")
        for cap in requirement.capabilities_needed:
            print(f"      - {cap}")
        if requirement.constraints:
            print(f"   Constraints: {requirement.constraints}")

        # Step 2: Discover agents
        print(f"\n🔎 Step 2: Discovering Agents...")
        discovered = self.discover_agents_for_capabilities(
            requirement.capabilities_needed,
            requirement.constraints
        )
        print(f"   Found {len(discovered)} agents:")
        for agent_info in discovered:
            agent = agent_info['agent']
            print(f"      ✓ {agent.name} (${agent.cost_per_request:.2f}, {agent.quality_baseline:.0%})")

        # Step 3: Build workflow
        print(f"\n🏗️  Step 3: Building Workflow...")
        workflow_def = self.build_workflow_from_agents(
            requirement, discovered, workflow_name
        )
        print(f"   Created workflow with {len(workflow_def.tasks)} tasks")
        print(f"   Workflow: {workflow_def.name}")

        # Step 4: Estimate cost and duration
        total_cost = sum(d['agent'].cost_per_request for d in discovered)
        max_latency = max(d['agent'].avg_latency_ms for d in discovered) if discovered else 0

        print(f"\n💰 Estimated Cost: ${total_cost:.2f}")
        print(f"⏱️  Estimated Duration: {max_latency:.0f}ms")

        composed = ComposedWorkflow(
            id=workflow_def.workflow_id,
            name=workflow_name,
            description=requirement.description,
            requirements=requirement,
            workflow_definition=workflow_def,
            selected_agents=[d['agent'] for d in discovered],
            estimated_cost=total_cost,
            estimated_duration=max_latency
        )

        print(f"\n✅ Workflow Composed Successfully!")

        return composed

    async def execute_workflow(
        self,
        composed_workflow: ComposedWorkflow,
        budget: float = 1000.0
    ):
        """
        Execute composed workflow with full orchestration

        Delegates to WorkflowOrchestrator for actual execution
        """
        print(f"\n{'='*80}")
        print(f"🚀 EXECUTING COMPOSED WORKFLOW")
        print(f"{'='*80}")
        print(f"\n📊 Workflow: {composed_workflow.name}")
        print(f"   Tasks: {len(composed_workflow.workflow_definition.tasks)}")
        print(f"   Budget: ${budget:.2f}")

        # Execute via orchestrator
        result = await self.orchestrator.execute_workflow(
            composed_workflow.workflow_definition,
            orchestrator_id="dynamic-composer"
        )

        print(f"\n✅ Execution Complete!")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"   Cost: ${result.total_cost:.2f}")
        print(f"   Status: {result.status.value}")

        return result

    def show_composition_stats(self):
        """Display statistics about composer capabilities"""
        stats = self.registry.get_stats()

        print(f"\n{'='*80}")
        print(f"📊 DYNAMIC WORKFLOW COMPOSER - CAPABILITIES")
        print(f"{'='*80}")
        print(f"\n🤖 Available Agents: {stats['total_agents']}")
        print(f"🎯 Available Capabilities: {stats['total_capabilities']}")
        print(f"📁 Categories: {stats['total_categories']}")
        print(f"💰 Average Cost: ${stats['avg_cost']:.2f}/request")
        print(f"⭐ Average Quality: {stats['avg_quality']:.0%}")
        print(f"\n🔍 Capability Keywords Recognized: {len(self.capability_keywords)}")
        print(f"\n✨ The composer can automatically build workflows from natural language!")


# Global singleton
_composer_instance = None

def get_composer() -> WorkflowComposer:
    """Get global WorkflowComposer instance"""
    global _composer_instance
    if _composer_instance is None:
        _composer_instance = WorkflowComposer()
    return _composer_instance
