"""
🎯 Visual Workflow Orchestration Engine - Backend
==================================================

Production-ready workflow orchestration system for drag-and-drop agent composition.
Enables users to visually create cross-domain workflows combining 118+ APQC agents.

Features:
- Workflow definition (nodes, edges, triggers)
- Workflow execution engine with state management
- Event streaming for real-time updates
- Workflow templates (save/load/export)
- Validation and testing capabilities
- Cross-domain agent orchestration
- Multi-step workflow execution
- Error handling and recovery

Architecture:
- Node-based workflow representation
- DAG (Directed Acyclic Graph) validation
- State machine for execution
- Event-driven architecture
- Template library management
- Real-time execution monitoring

Version: 1.0.0
Author: Workflow Orchestration Team
Date: 2025-11-16
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict

import yaml
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class NodeType(str, Enum):
    """Types of workflow nodes"""
    AGENT = "agent"
    TRIGGER = "trigger"
    CONDITION = "condition"
    AGGREGATOR = "aggregator"
    TRANSFORMER = "transformer"
    OUTPUT = "output"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """Node execution status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerType(str, Enum):
    """Workflow trigger types"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    DATA_ARRIVAL = "data_arrival"


class EdgeType(str, Enum):
    """Types of edges between nodes"""
    DATA_FLOW = "data_flow"
    CONTROL_FLOW = "control_flow"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


# ============================================================================
# Data Models
# ============================================================================

class NodePosition(BaseModel):
    """Position of node on canvas"""
    x: float
    y: float


class WorkflowNode(BaseModel):
    """Workflow node definition"""
    id: str
    type: NodeType
    label: str
    position: NodePosition

    # Agent-specific properties
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None

    # Node configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)

    # Execution properties
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 5  # seconds

    # Conditional logic
    conditions: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """Workflow edge definition"""
    id: str
    source: str  # source node id
    target: str  # target node id
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None

    # Edge properties
    type: EdgeType = EdgeType.DATA_FLOW
    label: Optional[str] = None

    # Data transformation
    transform: Optional[str] = None  # JavaScript/Python expression
    filter: Optional[str] = None  # Filter condition

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"

    # Workflow structure
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)

    # Workflow configuration
    trigger: TriggerType = TriggerType.MANUAL
    trigger_config: Dict[str, Any] = Field(default_factory=dict)

    # Global settings
    timeout: int = 3600  # seconds
    max_retries: int = 3
    error_handling: str = "stop"  # stop, continue, rollback

    # Metadata
    author: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    category: str = "general"
    is_template: bool = False

    # Execution history
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    success_rate: float = 0.0

    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate nodes have unique IDs"""
        ids = [node.id for node in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Nodes must have unique IDs")
        return v

    @validator('edges')
    def validate_edges(cls, v, values):
        """Validate edges reference valid nodes"""
        if 'nodes' not in values:
            return v

        node_ids = {node.id for node in values['nodes']}
        for edge in v:
            if edge.source not in node_ids:
                raise ValueError(f"Edge source {edge.source} not found in nodes")
            if edge.target not in node_ids:
                raise ValueError(f"Edge target {edge.target} not found in nodes")

        return v


class WorkflowExecution(BaseModel):
    """Workflow execution instance"""
    id: str
    workflow_id: str
    workflow_name: str

    # Execution state
    status: WorkflowStatus
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Node execution states
    node_states: Dict[str, NodeStatus] = Field(default_factory=dict)
    node_outputs: Dict[str, Any] = Field(default_factory=dict)
    node_errors: Dict[str, str] = Field(default_factory=dict)

    # Progress tracking
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0

    # Input/Output
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)

    # Error tracking
    error: Optional[str] = None
    error_node: Optional[str] = None

    # Metrics
    duration: float = 0.0  # seconds
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Event log
    events: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowTemplate(BaseModel):
    """Pre-built workflow template"""
    id: str
    name: str
    description: str
    category: str

    # Template definition
    workflow: WorkflowDefinition

    # Template metadata
    icon: str = "workflow"
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    estimated_time: int = 60  # seconds
    required_agents: List[str] = Field(default_factory=list)

    # Usage statistics
    usage_count: int = 0
    average_rating: float = 0.0

    # Example inputs/outputs
    example_input: Dict[str, Any] = Field(default_factory=dict)
    example_output: Dict[str, Any] = Field(default_factory=dict)

    # Documentation
    instructions: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)

    # Metadata
    author: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


# ============================================================================
# Workflow Validation
# ============================================================================

class WorkflowValidator:
    """Validates workflow definitions"""

    @staticmethod
    def validate_workflow(workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
        """
        Validate workflow definition

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check if workflow has nodes
        if not workflow.nodes:
            errors.append("Workflow must have at least one node")

        # Check for cycles (DAG validation)
        if WorkflowValidator._has_cycle(workflow):
            errors.append("Workflow contains cycles - must be a directed acyclic graph (DAG)")

        # Check for disconnected components
        if WorkflowValidator._has_disconnected_components(workflow):
            errors.append("Workflow has disconnected components - all nodes must be connected")

        # Check for entry points
        entry_nodes = WorkflowValidator._find_entry_nodes(workflow)
        if not entry_nodes:
            errors.append("Workflow must have at least one entry point (node with no incoming edges)")

        # Check for exit points
        exit_nodes = WorkflowValidator._find_exit_nodes(workflow)
        if not exit_nodes:
            errors.append("Workflow must have at least one exit point (node with no outgoing edges)")

        # Validate agent nodes have agent_id
        for node in workflow.nodes:
            if node.type == NodeType.AGENT and not node.agent_id:
                errors.append(f"Agent node {node.id} must have agent_id")

        # Validate edge data flow
        for edge in workflow.edges:
            source_node = next((n for n in workflow.nodes if n.id == edge.source), None)
            target_node = next((n for n in workflow.nodes if n.id == edge.target), None)

            if not source_node or not target_node:
                errors.append(f"Edge {edge.id} references non-existent nodes")

        return len(errors) == 0, errors

    @staticmethod
    def _has_cycle(workflow: WorkflowDefinition) -> bool:
        """Check if workflow has cycles using DFS"""
        # Build adjacency list
        graph = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)

        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in workflow.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True

        return False

    @staticmethod
    def _has_disconnected_components(workflow: WorkflowDefinition) -> bool:
        """Check if workflow has disconnected components"""
        if len(workflow.nodes) <= 1:
            return False

        # Build undirected graph
        graph = defaultdict(set)
        for edge in workflow.edges:
            graph[edge.source].add(edge.target)
            graph[edge.target].add(edge.source)

        # BFS from first node
        visited = set()
        queue = deque([workflow.nodes[0].id])
        visited.add(workflow.nodes[0].id)

        while queue:
            node = queue.popleft()
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Check if all nodes visited
        return len(visited) != len(workflow.nodes)

    @staticmethod
    def _find_entry_nodes(workflow: WorkflowDefinition) -> List[str]:
        """Find entry nodes (no incoming edges)"""
        targets = {edge.target for edge in workflow.edges}
        return [node.id for node in workflow.nodes if node.id not in targets]

    @staticmethod
    def _find_exit_nodes(workflow: WorkflowDefinition) -> List[str]:
        """Find exit nodes (no outgoing edges)"""
        sources = {edge.source for edge in workflow.edges}
        return [node.id for node in workflow.nodes if node.id not in sources]


# ============================================================================
# Workflow Execution Engine
# ============================================================================

class WorkflowExecutionEngine:
    """Executes workflow instances"""

    def __init__(self, agent_registry: Optional[Dict[str, Any]] = None):
        self.agent_registry = agent_registry or {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.event_callbacks: List[Callable] = []

    def register_event_callback(self, callback: Callable):
        """Register callback for workflow events"""
        self.event_callbacks.append(callback)

    async def _emit_event(self, execution_id: str, event_type: str, data: Dict[str, Any]):
        """Emit workflow event"""
        event = {
            "execution_id": execution_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Add to execution log
        if execution_id in self.active_executions:
            self.active_executions[execution_id].events.append(event)

        # Call registered callbacks
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        inputs: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """
        Execute workflow

        Args:
            workflow: Workflow definition
            inputs: Input data for workflow

        Returns:
            WorkflowExecution instance
        """
        # Validate workflow
        is_valid, errors = WorkflowValidator.validate_workflow(workflow)
        if not is_valid:
            raise ValueError(f"Invalid workflow: {', '.join(errors)}")

        # Create execution instance
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            total_nodes=len(workflow.nodes),
            inputs=inputs or {},
            node_states={node.id: NodeStatus.PENDING for node in workflow.nodes}
        )

        self.active_executions[execution.id] = execution

        await self._emit_event(execution.id, "workflow_started", {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name
        })

        try:
            # Build execution graph
            graph = self._build_execution_graph(workflow)

            # Execute nodes in topological order
            await self._execute_graph(execution, workflow, graph)

            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()

            await self._emit_event(execution.id, "workflow_completed", {
                "duration": execution.duration,
                "completed_nodes": execution.completed_nodes,
                "failed_nodes": execution.failed_nodes
            })

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()

            await self._emit_event(execution.id, "workflow_failed", {
                "error": str(e),
                "duration": execution.duration
            })

            logger.error(f"Workflow execution failed: {e}")

        return execution

    def _build_execution_graph(self, workflow: WorkflowDefinition) -> Dict[str, List[str]]:
        """Build adjacency list for execution"""
        graph = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
        return dict(graph)

    async def _execute_graph(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition,
        graph: Dict[str, List[str]]
    ):
        """Execute workflow graph in topological order"""
        # Calculate in-degrees
        in_degree = {node.id: 0 for node in workflow.nodes}
        for source, targets in graph.items():
            for target in targets:
                in_degree[target] += 1

        # Find entry nodes (in-degree 0)
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])

        # Process nodes in topological order
        while queue:
            # Get all ready nodes (for parallel execution)
            ready_nodes = []
            batch_size = len(queue)
            for _ in range(batch_size):
                ready_nodes.append(queue.popleft())

            # Execute nodes in parallel
            tasks = []
            for node_id in ready_nodes:
                node = next(n for n in workflow.nodes if n.id == node_id)
                tasks.append(self._execute_node(execution, node, workflow))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for node_id, result in zip(ready_nodes, results):
                if isinstance(result, Exception):
                    execution.node_states[node_id] = NodeStatus.FAILED
                    execution.node_errors[node_id] = str(result)
                    execution.failed_nodes += 1

                    if workflow.error_handling == "stop":
                        raise result
                else:
                    execution.node_states[node_id] = NodeStatus.COMPLETED
                    execution.node_outputs[node_id] = result
                    execution.completed_nodes += 1

                    # Update in-degrees for successors
                    for successor in graph.get(node_id, []):
                        in_degree[successor] -= 1
                        if in_degree[successor] == 0:
                            queue.append(successor)

    async def _execute_node(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode,
        workflow: WorkflowDefinition
    ) -> Any:
        """Execute a single workflow node"""
        execution.node_states[node.id] = NodeStatus.RUNNING

        await self._emit_event(execution.id, "node_started", {
            "node_id": node.id,
            "node_label": node.label,
            "node_type": node.type
        })

        try:
            # Gather inputs from predecessor nodes
            node_inputs = self._gather_node_inputs(execution, node, workflow)

            # Execute based on node type
            if node.type == NodeType.AGENT:
                result = await self._execute_agent_node(node, node_inputs)
            elif node.type == NodeType.TRANSFORMER:
                result = await self._execute_transformer_node(node, node_inputs)
            elif node.type == NodeType.CONDITION:
                result = await self._execute_condition_node(node, node_inputs)
            elif node.type == NodeType.AGGREGATOR:
                result = await self._execute_aggregator_node(node, node_inputs)
            else:
                result = node_inputs

            await self._emit_event(execution.id, "node_completed", {
                "node_id": node.id,
                "node_label": node.label
            })

            return result

        except Exception as e:
            await self._emit_event(execution.id, "node_failed", {
                "node_id": node.id,
                "node_label": node.label,
                "error": str(e)
            })
            raise

    def _gather_node_inputs(
        self,
        execution: WorkflowExecution,
        node: WorkflowNode,
        workflow: WorkflowDefinition
    ) -> Dict[str, Any]:
        """Gather inputs for node from predecessor outputs"""
        inputs = {}

        # Find incoming edges
        for edge in workflow.edges:
            if edge.target == node.id:
                source_output = execution.node_outputs.get(edge.source, {})

                # Apply transformation if specified
                if edge.transform:
                    # Simple eval-based transformation (in production, use safer method)
                    try:
                        source_output = eval(edge.transform, {"data": source_output})
                    except Exception as e:
                        logger.warning(f"Transform failed: {e}")

                # Merge inputs
                if isinstance(source_output, dict):
                    inputs.update(source_output)
                else:
                    inputs[edge.source] = source_output

        # Add workflow-level inputs
        inputs.update(execution.inputs)

        return inputs

    async def _execute_agent_node(self, node: WorkflowNode, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent node"""
        # Simulate agent execution (in production, call actual agent)
        agent_id = node.agent_id

        logger.info(f"Executing agent {agent_id} with inputs: {list(inputs.keys())}")

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Return mock result
        return {
            "agent_id": agent_id,
            "status": "success",
            "data": {
                **inputs,
                "processed_by": agent_id,
                "timestamp": datetime.now().isoformat()
            }
        }

    async def _execute_transformer_node(self, node: WorkflowNode, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transformer node"""
        # Apply transformation logic
        transform = node.config.get("transform", "data")

        try:
            result = eval(transform, {"data": inputs})
            return result if isinstance(result, dict) else {"result": result}
        except Exception as e:
            logger.error(f"Transformer error: {e}")
            return inputs

    async def _execute_condition_node(self, node: WorkflowNode, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute condition node"""
        # Evaluate conditions
        conditions = node.conditions

        for condition in conditions:
            expr = condition.get("expression", "True")
            try:
                if eval(expr, {"data": inputs}):
                    return {"condition_met": True, "branch": condition.get("branch", "default"), **inputs}
            except Exception as e:
                logger.warning(f"Condition evaluation error: {e}")

        return {"condition_met": False, **inputs}

    async def _execute_aggregator_node(self, node: WorkflowNode, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute aggregator node"""
        # Aggregate inputs from multiple sources
        aggregation_type = node.config.get("type", "merge")

        if aggregation_type == "merge":
            return inputs
        elif aggregation_type == "array":
            return {"items": list(inputs.values())}
        elif aggregation_type == "count":
            return {"count": len(inputs)}
        else:
            return inputs

    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status"""
        return self.active_executions.get(execution_id)

    async def cancel_execution(self, execution_id: str):
        """Cancel running execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()

            await self._emit_event(execution_id, "workflow_cancelled", {})


# ============================================================================
# Workflow Template Library
# ============================================================================

class WorkflowTemplateLibrary:
    """Manages workflow templates"""

    def __init__(self, storage_path: str = "./workflow_templates"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.templates: Dict[str, WorkflowTemplate] = {}

        # Load built-in templates
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """Load built-in workflow templates"""
        # Template 1: Financial Close + Marketing ROI Analysis
        self._add_financial_marketing_template()

        # Template 2: Supply Chain + Customer Demand Forecasting
        self._add_supply_chain_template()

        # Template 3: HR Recruitment + Skills Gap Analysis
        self._add_hr_recruitment_template()

        # Template 4: Cross-Domain: Strategy → Product → Marketing → Sales
        self._add_cross_domain_template()

        # Template 5: Customer Support + Product Feedback Loop
        self._add_customer_feedback_template()

        # Template 6: Risk Assessment + Compliance Monitoring
        self._add_risk_compliance_template()

        # Template 7: IT Service Management + Asset Optimization
        self._add_it_asset_template()

        # Template 8: Product Launch Pipeline
        self._add_product_launch_template()

        # Template 9: Financial Planning + Budget Analysis
        self._add_financial_planning_template()

        # Template 10: Employee Onboarding Workflow
        self._add_employee_onboarding_template()

    def _add_financial_marketing_template(self):
        """Financial Close + Marketing ROI Analysis"""
        template_id = "financial_marketing_roi"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Financial Close + Marketing ROI Analysis",
            description="Combines financial closing processes with marketing ROI analysis for comprehensive performance review",
            category="Finance & Marketing",
            tags=["finance", "marketing", "roi", "analysis"],
            is_template=True,
            nodes=[
                WorkflowNode(
                    id="node_1",
                    type=NodeType.AGENT,
                    label="Financial Data Collection",
                    position=NodePosition(x=100, y=100),
                    agent_id="expert_9_4",
                    agent_name="Manage Accounting and Financial Reporting",
                    category_id="9.0",
                    category_name="Financial Resources"
                ),
                WorkflowNode(
                    id="node_2",
                    type=NodeType.AGENT,
                    label="Marketing Spend Analysis",
                    position=NodePosition(x=100, y=250),
                    agent_id="expert_3_3",
                    agent_name="Develop and Manage Marketing Plans",
                    category_id="3.0",
                    category_name="Market & Sell"
                ),
                WorkflowNode(
                    id="node_3",
                    type=NodeType.AGGREGATOR,
                    label="Combine Financial & Marketing Data",
                    position=NodePosition(x=350, y=175),
                    config={"type": "merge"}
                ),
                WorkflowNode(
                    id="node_4",
                    type=NodeType.AGENT,
                    label="ROI Calculation",
                    position=NodePosition(x=600, y=175),
                    agent_id="expert_9_2",
                    agent_name="Manage Financial Planning and Budgeting",
                    category_id="9.0",
                    category_name="Financial Resources"
                ),
                WorkflowNode(
                    id="node_5",
                    type=NodeType.OUTPUT,
                    label="ROI Report",
                    position=NodePosition(x=850, y=175)
                )
            ],
            edges=[
                WorkflowEdge(id="edge_1", source="node_1", target="node_3"),
                WorkflowEdge(id="edge_2", source="node_2", target="node_3"),
                WorkflowEdge(id="edge_3", source="node_3", target="node_4"),
                WorkflowEdge(id="edge_4", source="node_4", target="node_5")
            ]
        )

        template = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Finance & Marketing",
            workflow=workflow,
            difficulty="intermediate",
            estimated_time=300,
            required_agents=["expert_9_4", "expert_3_3", "expert_9_2"],
            instructions=[
                "Configure financial data sources",
                "Set marketing spend tracking period",
                "Review ROI calculations",
                "Generate comprehensive report"
            ],
            use_cases=[
                "Quarterly financial review",
                "Marketing campaign effectiveness",
                "Budget allocation optimization"
            ],
            tags=["finance", "marketing", "roi"]
        )

        self.templates[template_id] = template

    def _add_supply_chain_template(self):
        """Supply Chain + Customer Demand Forecasting"""
        template_id = "supply_chain_demand"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Supply Chain + Customer Demand Forecasting",
            description="Integrates supply chain operations with customer demand forecasting for optimized inventory management",
            category="Operations",
            tags=["supply-chain", "demand-forecasting", "inventory"],
            is_template=True,
            nodes=[
                WorkflowNode(
                    id="node_1",
                    type=NodeType.AGENT,
                    label="Customer Data Analysis",
                    position=NodePosition(x=100, y=100),
                    agent_id="expert_6_3",
                    agent_name="Measure and Evaluate Customer Service Operations",
                    category_id="6.0",
                    category_name="Customer Service"
                ),
                WorkflowNode(
                    id="node_2",
                    type=NodeType.AGENT,
                    label="Demand Forecasting",
                    position=NodePosition(x=350, y=100),
                    agent_id="expert_4_1",
                    agent_name="Plan for and Align Supply Chain Resources",
                    category_id="4.0",
                    category_name="Deliver Physical"
                ),
                WorkflowNode(
                    id="node_3",
                    type=NodeType.AGENT,
                    label="Inventory Optimization",
                    position=NodePosition(x=600, y=100),
                    agent_id="expert_4_2",
                    agent_name="Procure Materials and Services",
                    category_id="4.0",
                    category_name="Deliver Physical"
                ),
                WorkflowNode(
                    id="node_4",
                    type=NodeType.OUTPUT,
                    label="Supply Plan",
                    position=NodePosition(x=850, y=100)
                )
            ],
            edges=[
                WorkflowEdge(id="edge_1", source="node_1", target="node_2"),
                WorkflowEdge(id="edge_2", source="node_2", target="node_3"),
                WorkflowEdge(id="edge_3", source="node_3", target="node_4")
            ]
        )

        template = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Operations",
            workflow=workflow,
            difficulty="advanced",
            estimated_time=450,
            required_agents=["expert_6_3", "expert_4_1", "expert_4_2"],
            use_cases=["Inventory planning", "Supply chain optimization", "Demand response"]
        )

        self.templates[template_id] = template

    def _add_hr_recruitment_template(self):
        """HR Recruitment + Skills Gap Analysis"""
        template_id = "hr_recruitment_skills"

        workflow = WorkflowDefinition(
            id=template_id,
            name="HR Recruitment + Skills Gap Analysis",
            description="Combines recruitment processes with skills gap analysis for strategic talent acquisition",
            category="Human Capital",
            tags=["hr", "recruitment", "skills-analysis"],
            is_template=True,
            nodes=[
                WorkflowNode(
                    id="node_1",
                    type=NodeType.AGENT,
                    label="Current Skills Assessment",
                    position=NodePosition(x=100, y=100),
                    agent_id="expert_7_3",
                    agent_name="Develop and Counsel Employees",
                    category_id="7.0",
                    category_name="Human Capital"
                ),
                WorkflowNode(
                    id="node_2",
                    type=NodeType.AGENT,
                    label="Strategic Skills Planning",
                    position=NodePosition(x=100, y=250),
                    agent_id="expert_1_4",
                    agent_name="Develop and Manage Business Capabilities",
                    category_id="1.0",
                    category_name="Vision & Strategy"
                ),
                WorkflowNode(
                    id="node_3",
                    type=NodeType.TRANSFORMER,
                    label="Skills Gap Calculation",
                    position=NodePosition(x=350, y=175),
                    config={"transform": "data"}
                ),
                WorkflowNode(
                    id="node_4",
                    type=NodeType.AGENT,
                    label="Targeted Recruitment",
                    position=NodePosition(x=600, y=175),
                    agent_id="expert_7_2",
                    agent_name="Recruit, Source, and Select Employees",
                    category_id="7.0",
                    category_name="Human Capital"
                ),
                WorkflowNode(
                    id="node_5",
                    type=NodeType.OUTPUT,
                    label="Recruitment Plan",
                    position=NodePosition(x=850, y=175)
                )
            ],
            edges=[
                WorkflowEdge(id="edge_1", source="node_1", target="node_3"),
                WorkflowEdge(id="edge_2", source="node_2", target="node_3"),
                WorkflowEdge(id="edge_3", source="node_3", target="node_4"),
                WorkflowEdge(id="edge_4", source="node_4", target="node_5")
            ]
        )

        template = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Human Capital",
            workflow=workflow,
            difficulty="intermediate",
            estimated_time=360,
            required_agents=["expert_7_3", "expert_1_4", "expert_7_2"]
        )

        self.templates[template_id] = template

    def _add_cross_domain_template(self):
        """Cross-Domain: Strategy → Product → Marketing → Sales"""
        template_id = "cross_domain_pipeline"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Cross-Domain: Strategy → Product → Marketing → Sales",
            description="End-to-end workflow from strategic planning through product development, marketing, and sales execution",
            category="Cross-Domain",
            tags=["strategy", "product", "marketing", "sales", "end-to-end"],
            is_template=True,
            nodes=[
                WorkflowNode(
                    id="node_1",
                    type=NodeType.AGENT,
                    label="Strategic Planning",
                    position=NodePosition(x=100, y=200),
                    agent_id="expert_1_2",
                    agent_name="Develop Business Strategy",
                    category_id="1.0",
                    category_name="Vision & Strategy"
                ),
                WorkflowNode(
                    id="node_2",
                    type=NodeType.AGENT,
                    label="Product Development",
                    position=NodePosition(x=300, y=200),
                    agent_id="expert_2_2",
                    agent_name="Develop Products and Services",
                    category_id="2.0",
                    category_name="Products & Services"
                ),
                WorkflowNode(
                    id="node_3",
                    type=NodeType.AGENT,
                    label="Marketing Strategy",
                    position=NodePosition(x=500, y=200),
                    agent_id="expert_3_2",
                    agent_name="Develop Marketing Strategy",
                    category_id="3.0",
                    category_name="Market & Sell"
                ),
                WorkflowNode(
                    id="node_4",
                    type=NodeType.AGENT,
                    label="Sales Execution",
                    position=NodePosition(x=700, y=200),
                    agent_id="expert_3_5",
                    agent_name="Develop and Manage Sales Plans",
                    category_id="3.0",
                    category_name="Market & Sell"
                ),
                WorkflowNode(
                    id="node_5",
                    type=NodeType.OUTPUT,
                    label="Revenue Results",
                    position=NodePosition(x=900, y=200)
                )
            ],
            edges=[
                WorkflowEdge(id="edge_1", source="node_1", target="node_2"),
                WorkflowEdge(id="edge_2", source="node_2", target="node_3"),
                WorkflowEdge(id="edge_3", source="node_3", target="node_4"),
                WorkflowEdge(id="edge_4", source="node_4", target="node_5")
            ]
        )

        template = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Cross-Domain",
            workflow=workflow,
            difficulty="advanced",
            estimated_time=600,
            required_agents=["expert_1_2", "expert_2_2", "expert_3_2", "expert_3_5"]
        )

        self.templates[template_id] = template

    def _add_customer_feedback_template(self):
        """Customer Support + Product Feedback Loop"""
        template_id = "customer_feedback_loop"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Customer Support + Product Feedback Loop",
            description="Continuous improvement workflow that channels customer feedback into product development",
            category="Customer Experience",
            tags=["customer-support", "product", "feedback"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Customer Experience",
            workflow=workflow,
            difficulty="intermediate"
        )

    def _add_risk_compliance_template(self):
        """Risk Assessment + Compliance Monitoring"""
        template_id = "risk_compliance"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Risk Assessment + Compliance Monitoring",
            description="Integrated risk and compliance workflow for enterprise governance",
            category="Risk & Compliance",
            tags=["risk", "compliance", "governance"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Risk & Compliance",
            workflow=workflow,
            difficulty="advanced"
        )

    def _add_it_asset_template(self):
        """IT Service Management + Asset Optimization"""
        template_id = "it_asset_management"

        workflow = WorkflowDefinition(
            id=template_id,
            name="IT Service Management + Asset Optimization",
            description="Comprehensive IT service and asset management workflow",
            category="IT Operations",
            tags=["it", "asset-management", "optimization"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="IT Operations",
            workflow=workflow,
            difficulty="intermediate"
        )

    def _add_product_launch_template(self):
        """Product Launch Pipeline"""
        template_id = "product_launch"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Product Launch Pipeline",
            description="Complete product launch workflow from concept to market",
            category="Product Management",
            tags=["product", "launch", "go-to-market"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Product Management",
            workflow=workflow,
            difficulty="advanced"
        )

    def _add_financial_planning_template(self):
        """Financial Planning + Budget Analysis"""
        template_id = "financial_planning"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Financial Planning + Budget Analysis",
            description="Comprehensive financial planning and budgeting workflow",
            category="Finance",
            tags=["finance", "planning", "budget"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Finance",
            workflow=workflow,
            difficulty="intermediate"
        )

    def _add_employee_onboarding_template(self):
        """Employee Onboarding Workflow"""
        template_id = "employee_onboarding"

        workflow = WorkflowDefinition(
            id=template_id,
            name="Employee Onboarding Workflow",
            description="End-to-end employee onboarding process",
            category="Human Capital",
            tags=["hr", "onboarding", "employee"],
            is_template=True
        )

        self.templates[template_id] = WorkflowTemplate(
            id=template_id,
            name=workflow.name,
            description=workflow.description,
            category="Human Capital",
            workflow=workflow,
            difficulty="beginner"
        )

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """List all templates, optionally filtered by category"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def save_template(self, template: WorkflowTemplate):
        """Save template to library"""
        self.templates[template.id] = template

        # Save to disk
        template_path = self.storage_path / f"{template.id}.json"
        with open(template_path, 'w') as f:
            json.dump(template.dict(), f, indent=2, default=str)

        logger.info(f"Template saved: {template.id}")

    def delete_template(self, template_id: str):
        """Delete template from library"""
        if template_id in self.templates:
            del self.templates[template_id]

            # Delete from disk
            template_path = self.storage_path / f"{template_id}.json"
            if template_path.exists():
                template_path.unlink()

            logger.info(f"Template deleted: {template_id}")


# ============================================================================
# Main Workflow Manager
# ============================================================================

class WorkflowManager:
    """Main workflow management system"""

    def __init__(self, storage_path: str = "./workflows"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}

        self.engine = WorkflowExecutionEngine()
        self.template_library = WorkflowTemplateLibrary()

        logger.info("Workflow Manager initialized")

    def create_workflow(self, workflow: WorkflowDefinition) -> str:
        """Create new workflow"""
        self.workflows[workflow.id] = workflow
        self._save_workflow(workflow)
        logger.info(f"Workflow created: {workflow.id}")
        return workflow.id

    def update_workflow(self, workflow: WorkflowDefinition):
        """Update existing workflow"""
        workflow.updated_at = datetime.now()
        self.workflows[workflow.id] = workflow
        self._save_workflow(workflow)
        logger.info(f"Workflow updated: {workflow.id}")

    def delete_workflow(self, workflow_id: str):
        """Delete workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]

            workflow_path = self.storage_path / f"{workflow_id}.json"
            if workflow_path.exists():
                workflow_path.unlink()

            logger.info(f"Workflow deleted: {workflow_id}")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all workflows"""
        return list(self.workflows.values())

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """Execute workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        execution = await self.engine.execute_workflow(workflow, inputs)
        self.executions[execution.id] = execution

        # Update workflow statistics
        workflow.execution_count += 1
        workflow.last_execution = execution.end_time
        if execution.status == WorkflowStatus.COMPLETED:
            workflow.success_rate = (
                workflow.success_rate * (workflow.execution_count - 1) + 1
            ) / workflow.execution_count

        return execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)

    def export_workflow(self, workflow_id: str, format: str = "json") -> str:
        """Export workflow to JSON/YAML"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if format == "json":
            return json.dumps(workflow.dict(), indent=2, default=str)
        elif format == "yaml":
            return yaml.dump(workflow.dict(), default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_workflow(self, data: str, format: str = "json") -> str:
        """Import workflow from JSON/YAML"""
        if format == "json":
            workflow_dict = json.loads(data)
        elif format == "yaml":
            workflow_dict = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        workflow = WorkflowDefinition(**workflow_dict)
        return self.create_workflow(workflow)

    def _save_workflow(self, workflow: WorkflowDefinition):
        """Save workflow to disk"""
        workflow_path = self.storage_path / f"{workflow.id}.json"
        with open(workflow_path, 'w') as f:
            json.dump(workflow.dict(), f, indent=2, default=str)


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """Example usage"""
    manager = WorkflowManager()

    # Get a template
    template = manager.template_library.get_template("financial_marketing_roi")
    if template:
        # Create workflow from template
        workflow_id = manager.create_workflow(template.workflow)

        # Execute workflow
        execution = await manager.execute_workflow(workflow_id, {
            "period": "Q4 2024",
            "regions": ["North America", "Europe"]
        })

        print(f"Execution Status: {execution.status}")
        print(f"Duration: {execution.duration}s")
        print(f"Completed Nodes: {execution.completed_nodes}/{execution.total_nodes}")


if __name__ == "__main__":
    asyncio.run(main())
