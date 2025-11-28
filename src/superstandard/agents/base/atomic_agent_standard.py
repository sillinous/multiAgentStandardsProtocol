"""
Atomic Agent Standardization Framework
========================================

This module defines the standardization framework for all APQC Level 5 atomic agents.
Every atomic agent MUST implement this standard to ensure interoperability,
composability, and reusability across the entire ecosystem.

Design Philosophy: BOTTOM-UP
- Start with the most atomic unit (Level 5 APQC task)
- Standardize each atomic agent individually
- Build composition patterns from standardized atoms
- Enable unlimited workflows from atomic building blocks

Version: 2.0.0
Date: 2025-11-17
Framework: APQC PCF 7.0.1
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from datetime import datetime
from enum import Enum
import uuid
import json
import logging


# ============================================================================
# Core Type Definitions
# ============================================================================

class AgentCapabilityLevel(Enum):
    """Standardized capability proficiency levels"""
    NOVICE = "novice"              # 0-25% proficiency
    INTERMEDIATE = "intermediate"   # 26-50% proficiency
    ADVANCED = "advanced"           # 51-75% proficiency
    EXPERT = "expert"               # 76-100% proficiency


class ExecutionMode(Enum):
    """How the atomic agent executes"""
    SYNCHRONOUS = "synchronous"     # Immediate execution
    ASYNCHRONOUS = "asynchronous"   # Background execution
    STREAMING = "streaming"         # Progressive results
    BATCH = "batch"                 # Bulk processing


class AgentState(Enum):
    """Atomic agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ExecutionStatus(Enum):
    """Execution status for agent task results"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


# ============================================================================
# Input/Output Standards
# ============================================================================

@dataclass
class AtomicAgentInput:
    """
    Standardized input for atomic agents.
    Every atomic agent receives this structure.
    """
    # Core required fields
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    task_description: str = ""

    # Data payload
    data: Dict[str, Any] = field(default_factory=dict)

    # Execution context
    context: Dict[str, Any] = field(default_factory=dict)

    # Execution parameters
    priority: int = 5  # 1 (lowest) to 10 (highest)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3

    # Provenance
    source_agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'task_description': self.task_description,
            'data': self.data,
            'context': self.context,
            'priority': self.priority,
            'timeout_seconds': self.timeout_seconds,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'source_agent_id': self.source_agent_id,
            'workflow_id': self.workflow_id,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


@dataclass
class AtomicAgentOutput:
    """
    Standardized output from atomic agents.
    Every atomic agent returns this structure.
    """
    # Task identification
    task_id: str
    agent_id: str

    # Execution result
    success: bool
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    result_data: Dict[str, Any] = field(default_factory=dict)

    # Error information (if failed)
    error: Optional[str] = None
    error_message: Optional[str] = None  # Alias for error
    error_details: Dict[str, Any] = field(default_factory=dict)

    # Execution metadata
    execution_time_ms: float = 0.0
    retry_count: int = 0

    # Business metadata (APQC context)
    apqc_level5_id: str = ""
    apqc_level5_name: str = ""
    apqc_category: str = ""

    # Metrics and observability
    metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    # Provenance
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'success': self.success,
            'status': self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            'result_data': self.result_data,
            'error': self.error,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'execution_time_ms': self.execution_time_ms,
            'retry_count': self.retry_count,
            'apqc_level5_id': self.apqc_level5_id,
            'apqc_level5_name': self.apqc_level5_name,
            'apqc_category': self.apqc_category,
            'metrics': self.metrics,
            'logs': self.logs,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


# ============================================================================
# Capability Declaration
# ============================================================================

@dataclass
class AtomicCapability:
    """
    Declares what an atomic agent can do.
    Used for discovery, composition, and validation.
    """
    # Capability identity
    capability_id: str
    capability_name: str
    description: str

    # APQC mapping
    apqc_level5_id: str
    apqc_level5_name: str
    apqc_category_id: str
    apqc_category_name: str

    # Proficiency
    proficiency_level: AgentCapabilityLevel = AgentCapabilityLevel.INTERMEDIATE
    confidence_score: float = 0.7  # 0.0 to 1.0

    # Input/Output schema
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # Requirements
    required_integrations: List[str] = field(default_factory=list)
    required_api_keys: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)

    # Performance characteristics
    avg_execution_time_ms: float = 100.0
    max_execution_time_ms: float = 1000.0
    throughput_per_second: float = 10.0

    # Metadata
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'capability_id': self.capability_id,
            'capability_name': self.capability_name,
            'description': self.description,
            'apqc_level5_id': self.apqc_level5_id,
            'apqc_level5_name': self.apqc_level5_name,
            'apqc_category_id': self.apqc_category_id,
            'apqc_category_name': self.apqc_category_name,
            'proficiency_level': self.proficiency_level.value,
            'confidence_score': self.confidence_score,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'required_integrations': self.required_integrations,
            'required_api_keys': self.required_api_keys,
            'required_permissions': self.required_permissions,
            'avg_execution_time_ms': self.avg_execution_time_ms,
            'max_execution_time_ms': self.max_execution_time_ms,
            'throughput_per_second': self.throughput_per_second,
            'version': self.version,
            'tags': self.tags,
            'metadata': self.metadata
        }


# ============================================================================
# Business Logic Interface
# ============================================================================

class AtomicBusinessLogic(ABC):
    """
    Abstract base class for atomic agent business logic.
    Every atomic agent MUST implement these methods.
    """

    @abstractmethod
    async def validate_input(self, agent_input: AtomicAgentInput) -> tuple[bool, Optional[str]]:
        """
        Validate input before execution.

        Args:
            agent_input: Standardized input

        Returns:
            (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def execute_atomic_task(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """
        Execute the atomic business task.
        This is the core business logic unique to each agent.

        Args:
            agent_input: Standardized input

        Returns:
            Standardized output
        """
        pass

    @abstractmethod
    async def handle_error(self, error: Exception, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """
        Handle errors during execution.

        Args:
            error: The exception that occurred
            agent_input: The input that caused the error

        Returns:
            Error output
        """
        pass

    async def transform_output(self, output: AtomicAgentOutput) -> AtomicAgentOutput:
        """
        Optional: Transform output before returning.
        Can be overridden for custom transformations.

        Args:
            output: Raw output

        Returns:
            Transformed output
        """
        return output


# ============================================================================
# Standard Atomic Agent Base Class
# ============================================================================

class StandardAtomicAgent(ABC):
    """
    Standardized base class for all APQC Level 5 atomic agents.

    Every atomic agent inherits from this class and implements:
    1. Capability declaration
    2. Business logic (via AtomicBusinessLogic)
    3. Protocol support
    4. Observability
    5. Lifecycle management
    """

    def __init__(
        self,
        agent_id: str,
        apqc_level5_id: str,
        apqc_level5_name: str,
        apqc_category_id: str,
        apqc_category_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize atomic agent.

        Args:
            agent_id: Unique agent identifier
            apqc_level5_id: APQC Level 5 task ID (e.g., "1.1.1.1")
            apqc_level5_name: APQC Level 5 task name
            apqc_category_id: APQC Category ID (e.g., "1.0")
            apqc_category_name: APQC Category name
            config: Optional configuration
        """
        self.agent_id = agent_id
        self.apqc_level5_id = apqc_level5_id
        self.apqc_level5_name = apqc_level5_name
        self.apqc_category_id = apqc_category_id
        self.apqc_category_name = apqc_category_name
        self.config = config or {}

        # State management
        self.state = AgentState.INITIALIZING
        self.created_at = datetime.utcnow()
        self.last_execution_at: Optional[datetime] = None

        # Metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time_ms = 0.0

        # Logging
        self.logger = logging.getLogger(f"AtomicAgent.{agent_id}")

        # Business logic instance (to be set by subclass)
        self._business_logic: Optional[AtomicBusinessLogic] = None

        # Capability declaration (to be set by subclass)
        self._capability: Optional[AtomicCapability] = None

        # Protocol handlers
        self._protocol_handlers: Dict[str, Callable] = {}

        # State
        self.state = AgentState.READY

    @abstractmethod
    def declare_capability(self) -> AtomicCapability:
        """
        Declare what this atomic agent can do.
        MUST be implemented by every atomic agent.

        Returns:
            Capability declaration
        """
        pass

    @abstractmethod
    def create_business_logic(self) -> AtomicBusinessLogic:
        """
        Create the business logic instance.
        MUST be implemented by every atomic agent.

        Returns:
            Business logic implementation
        """
        pass

    def get_capability(self) -> AtomicCapability:
        """Get agent capability"""
        if not self._capability:
            self._capability = self.declare_capability()
        return self._capability

    def get_business_logic(self) -> AtomicBusinessLogic:
        """Get business logic instance"""
        if not self._business_logic:
            self._business_logic = self.create_business_logic()
        return self._business_logic

    async def execute(self, agent_input: AtomicAgentInput) -> AtomicAgentOutput:
        """
        Execute the atomic agent.
        This is the main entry point for all atomic agents.

        Args:
            agent_input: Standardized input

        Returns:
            Standardized output
        """
        start_time = datetime.utcnow()
        self.state = AgentState.EXECUTING
        self.total_executions += 1

        try:
            # Get business logic
            business_logic = self.get_business_logic()

            # Validate input
            is_valid, error_msg = await business_logic.validate_input(agent_input)
            if not is_valid:
                return self._create_error_output(
                    agent_input,
                    f"Input validation failed: {error_msg}",
                    start_time
                )

            # Execute atomic task
            self.logger.info(f"Executing atomic task: {self.apqc_level5_name}")
            output = await business_logic.execute_atomic_task(agent_input)

            # Transform output
            output = await business_logic.transform_output(output)

            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            output.execution_time_ms = execution_time
            self.total_execution_time_ms += execution_time

            if output.success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            self.last_execution_at = datetime.utcnow()
            self.state = AgentState.COMPLETED

            return output

        except Exception as e:
            self.logger.error(f"Atomic task execution failed: {e}")
            self.failed_executions += 1
            self.state = AgentState.FAILED

            business_logic = self.get_business_logic()
            return await business_logic.handle_error(e, agent_input)

    def _create_error_output(
        self,
        agent_input: AtomicAgentInput,
        error_message: str,
        start_time: datetime
    ) -> AtomicAgentOutput:
        """Create standardized error output"""
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return AtomicAgentOutput(
            task_id=agent_input.task_id,
            agent_id=self.agent_id,
            success=False,
            error=error_message,
            execution_time_ms=execution_time,
            retry_count=agent_input.retry_count,
            apqc_level5_id=self.apqc_level5_id,
            apqc_level5_name=self.apqc_level5_name,
            apqc_category=self.apqc_category_name
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        avg_execution_time = (
            self.total_execution_time_ms / self.total_executions
            if self.total_executions > 0
            else 0.0
        )

        success_rate = (
            self.successful_executions / self.total_executions
            if self.total_executions > 0
            else 0.0
        )

        return {
            'agent_id': self.agent_id,
            'apqc_level5_id': self.apqc_level5_id,
            'state': self.state.value,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': success_rate,
            'avg_execution_time_ms': avg_execution_time,
            'total_execution_time_ms': self.total_execution_time_ms,
            'created_at': self.created_at.isoformat(),
            'last_execution_at': self.last_execution_at.isoformat() if self.last_execution_at else None
        }

    def register_protocol_handler(self, protocol: str, handler: Callable) -> None:
        """Register a protocol message handler"""
        self._protocol_handlers[protocol] = handler

    async def handle_protocol_message(self, protocol: str, message: Dict[str, Any]) -> Any:
        """Handle incoming protocol message"""
        handler = self._protocol_handlers.get(protocol)
        if handler:
            return await handler(message)
        else:
            raise ValueError(f"No handler registered for protocol: {protocol}")


# ============================================================================
# Atomic Agent Registry
# ============================================================================

class AtomicAgentRegistry:
    """
    Registry for all atomic agents.
    Enables discovery, lookup, and composition.
    """

    def __init__(self):
        self._agents: Dict[str, StandardAtomicAgent] = {}
        self._capabilities: Dict[str, AtomicCapability] = {}
        self._apqc_index: Dict[str, List[str]] = {}  # APQC ID -> agent IDs

    def register(self, agent: StandardAtomicAgent) -> None:
        """Register an atomic agent"""
        self._agents[agent.agent_id] = agent
        capability = agent.get_capability()
        self._capabilities[agent.agent_id] = capability

        # Index by APQC ID
        if capability.apqc_level5_id not in self._apqc_index:
            self._apqc_index[capability.apqc_level5_id] = []
        self._apqc_index[capability.apqc_level5_id].append(agent.agent_id)

    def unregister(self, agent_id: str) -> None:
        """Unregister an atomic agent"""
        if agent_id in self._agents:
            capability = self._capabilities[agent_id]
            self._apqc_index[capability.apqc_level5_id].remove(agent_id)
            del self._agents[agent_id]
            del self._capabilities[agent_id]

    def get_agent(self, agent_id: str) -> Optional[StandardAtomicAgent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)

    def get_capability(self, agent_id: str) -> Optional[AtomicCapability]:
        """Get capability by agent ID"""
        return self._capabilities.get(agent_id)

    def find_by_apqc_id(self, apqc_id: str) -> List[StandardAtomicAgent]:
        """Find agents by APQC Level 5 ID"""
        agent_ids = self._apqc_index.get(apqc_id, [])
        return [self._agents[aid] for aid in agent_ids]

    def find_by_capability(self, capability_name: str) -> List[StandardAtomicAgent]:
        """Find agents by capability name"""
        matching = []
        for agent_id, capability in self._capabilities.items():
            if capability_name.lower() in capability.capability_name.lower():
                matching.append(self._agents[agent_id])
        return matching

    def get_all_capabilities(self) -> List[AtomicCapability]:
        """Get all registered capabilities"""
        return list(self._capabilities.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_agents = len(self._agents)
        categories = {}

        for capability in self._capabilities.values():
            cat = capability.apqc_category_name
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_agents': total_agents,
            'total_capabilities': len(self._capabilities),
            'agents_by_category': categories,
            'apqc_coverage': len(self._apqc_index)
        }


# ============================================================================
# Global Registry Instance
# ============================================================================

# Singleton registry for all atomic agents
ATOMIC_AGENT_REGISTRY = AtomicAgentRegistry()


# ============================================================================
# Exports
# ============================================================================

# Alias for backward compatibility with generated agents
AtomicAgentStandard = StandardAtomicAgent

__all__ = [
    # Enums
    'AgentCapabilityLevel',
    'ExecutionMode',
    'AgentState',
    'ExecutionStatus',

    # Data structures
    'AtomicAgentInput',
    'AtomicAgentOutput',
    'AtomicCapability',

    # Base classes
    'AtomicBusinessLogic',
    'StandardAtomicAgent',
    'AtomicAgentStandard',  # Alias

    # Registry
    'AtomicAgentRegistry',
    'ATOMIC_AGENT_REGISTRY',
]
