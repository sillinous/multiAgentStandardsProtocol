"""
PCF Base Agent - Foundation for all APQC PCF agents

This module provides the base classes for implementing APQC Process Classification
Framework (PCF) agents with full BPMN 2.0 integration and BPM system compatibility.

Key Features:
- Hierarchical delegation (Category → Process Group → Process → Activity → Task)
- BPMN 2.0 model generation
- KPI tracking aligned with APQC metrics
- Protocol integration (A2A, MCP, ANP, ACP)
- Industry variant support
- BPM system integration (Camunda, Activiti, IBM, SAP, etc.)

Version: 1.0.0
Date: 2024-11-12
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
import json
import logging

# Import from existing SuperStandard platform
try:
    from agents.consolidated.py.base_agent_v1 import BaseAgent
except ImportError:
    # Fallback for development
    class BaseAgent:
        def __init__(self, agent_id: str, agent_type: str):
            self.agent_id = agent_id
            self.agent_type = agent_type
            self.logger = logging.getLogger(self.__class__.__name__)


# ============================================================================
# Data Classes for PCF Metadata
# ============================================================================

@dataclass
class PCFMetadata:
    """
    Metadata for PCF agent alignment with APQC standards.

    Every PCF agent includes complete lineage information for
    traceability, benchmarking, and BPMN integration.
    """
    # Identifiers
    pcf_element_id: str          # 5-digit unique ID (e.g., "10022")
    hierarchy_id: str            # Positional ID (e.g., "1.1.1.1")
    level: int                   # 1-5 (Category to Task)
    level_name: str              # "Category", "Process Group", etc.

    # Category (Level 1)
    category_id: str             # "1.0" through "13.0"
    category_name: str           # "Develop Vision and Strategy"

    # Process Group (Level 2)
    process_group_id: Optional[str] = None
    process_group_name: Optional[str] = None

    # Process (Level 3)
    process_id: Optional[str] = None
    process_name: Optional[str] = None

    # Activity (Level 4)
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None

    # Task (Level 5)
    task_id: Optional[str] = None
    task_name: Optional[str] = None

    # Variants and versioning
    industry_variant: Optional[str] = "cross-industry"
    pcf_version: str = "7.4"

    # Hierarchy relationships
    parent_element_id: Optional[str] = None
    child_element_ids: List[str] = field(default_factory=list)

    # APQC metrics
    kpis: List[Dict[str, Any]] = field(default_factory=list)
    benchmarking_enabled: bool = True

    # BPMN integration
    bpmn_model_path: Optional[str] = None
    bpmn_service_task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization"""
        return {
            'pcf_element_id': self.pcf_element_id,
            'hierarchy_id': self.hierarchy_id,
            'level': self.level,
            'level_name': self.level_name,
            'category': {
                'id': self.category_id,
                'name': self.category_name
            },
            'process_group': {
                'id': self.process_group_id,
                'name': self.process_group_name
            } if self.level >= 2 else None,
            'process': {
                'id': self.process_id,
                'name': self.process_name
            } if self.level >= 3 else None,
            'activity': {
                'id': self.activity_id,
                'name': self.activity_name
            } if self.level >= 4 else None,
            'task': {
                'id': self.task_id,
                'name': self.task_name
            } if self.level == 5 else None,
            'industry_variant': self.industry_variant,
            'pcf_version': self.pcf_version,
            'kpis': self.kpis,
            'bpmn_model_path': self.bpmn_model_path
        }


@dataclass
class PCFAgentConfig:
    """Configuration for PCF agents"""
    agent_id: str
    pcf_metadata: PCFMetadata

    # Operational settings
    execution_timeout: int = 300  # seconds
    retry_count: int = 3
    log_level: str = "INFO"

    # Protocol settings
    enable_a2a: bool = True
    enable_mcp: bool = True
    enable_anp: bool = True
    enable_acp: bool = True

    # Performance tracking
    track_kpis: bool = True
    report_to_apqc: bool = False

    # Composition settings
    allow_delegation: bool = True
    delegate_to_children: bool = True
    aggregate_child_results: bool = True

    # BPMN integration
    bpm_integration_enabled: bool = True
    bpm_system_type: Optional[str] = None  # "camunda", "activiti", "ibm", etc.


# ============================================================================
# KPI Tracking
# ============================================================================

class KPITracker:
    """
    Tracks Key Performance Indicators aligned with APQC metrics.

    Supports real-time tracking, historical analysis, and benchmarking
    against APQC standards.
    """

    def __init__(self, kpi_definitions: List[Dict[str, Any]]):
        self.kpi_definitions = kpi_definitions
        self.measurements: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    async def record_execution(
        self,
        execution_time: float,
        success: bool,
        metadata: Dict[str, Any]
    ):
        """Record an execution with KPI measurements"""
        measurement = {
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time,
            'success': success,
            'kpis': {},
            'metadata': metadata
        }

        # Extract KPI values from metadata
        for kpi_def in self.kpi_definitions:
            kpi_name = kpi_def['name']
            if kpi_name in metadata:
                measurement['kpis'][kpi_name] = metadata[kpi_name]

        self.measurements.append(measurement)
        self.logger.debug(f"Recorded KPI measurement: {measurement}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current KPI metrics"""
        if not self.measurements:
            return {}

        latest = self.measurements[-1]
        return latest['kpis']

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical summary of KPIs"""
        if not self.measurements:
            return {}

        stats = {
            'total_executions': len(self.measurements),
            'success_rate': sum(1 for m in self.measurements if m['success']) / len(self.measurements),
            'avg_execution_time': sum(m['execution_time'] for m in self.measurements) / len(self.measurements),
            'kpis': {}
        }

        # Calculate statistics for each KPI
        for kpi_def in self.kpi_definitions:
            kpi_name = kpi_def['name']
            values = [m['kpis'].get(kpi_name) for m in self.measurements if kpi_name in m['kpis']]

            if values:
                if kpi_def['type'] in ['count', 'number', 'percentage', 'duration']:
                    stats['kpis'][kpi_name] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'count': len(values)
                    }

        return stats


# ============================================================================
# PCF Base Agent
# ============================================================================

class PCFBaseAgent(BaseAgent, ABC):
    """
    Base class for all APQC PCF agents.

    Provides:
    - PCF metadata management
    - Hierarchical delegation to child agents
    - KPI tracking aligned with APQC measures
    - Protocol integration (A2A, MCP, ANP, ACP)
    - BPMN 2.0 model generation
    - BPM system integration
    - Industry variant support

    Usage:
        class MyProcessAgent(ProcessAgentBase):
            async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                # Implement process logic
                return {"success": True, "output": result}
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(
            agent_id=config.agent_id,
            agent_type=f"pcf_{config.pcf_metadata.level_name.lower().replace(' ', '_')}"
        )

        self.config = config
        self.pcf_metadata = config.pcf_metadata
        self.child_agents: Dict[str, 'PCFBaseAgent'] = {}
        self.kpi_tracker = KPITracker(self.pcf_metadata.kpis)

        # Set up logging
        logging.basicConfig(level=getattr(logging, config.log_level))
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info(
            f"Initialized {self.__class__.__name__} - "
            f"PCF {self.pcf_metadata.hierarchy_id} ({self.pcf_metadata.pcf_element_id})"
        )

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the PCF process.

        Must be implemented by concrete agents.

        Args:
            input_data: Input parameters for execution

        Returns:
            Dictionary with keys:
                - success: bool
                - output_data: Dict (process outputs)
                - metadata: Dict (execution metadata)
        """
        pass

    async def execute_with_hierarchy(
        self,
        input_data: Dict[str, Any],
        delegate_to_children: bool = None
    ) -> Dict[str, Any]:
        """
        Execute process with optional hierarchical delegation.

        Pattern:
        1. Pre-process input
        2. If delegate_to_children and has children:
           - Distribute work to child agents
           - Aggregate results
        3. Else:
           - Execute own logic
        4. Post-process and return

        Args:
            input_data: Input parameters
            delegate_to_children: Override config setting

        Returns:
            Execution result dictionary
        """
        start_time = datetime.now()

        # Use config default if not specified
        if delegate_to_children is None:
            delegate_to_children = self.config.delegate_to_children

        self.logger.info(
            f"Starting execution - PCF {self.pcf_metadata.hierarchy_id}, "
            f"delegate={delegate_to_children}, children={len(self.child_agents)}"
        )

        try:
            # Pre-processing
            processed_input = await self._preprocess_input(input_data)

            # Execution strategy
            if delegate_to_children and self.child_agents:
                self.logger.debug(f"Delegating to {len(self.child_agents)} child agents")
                result = await self._delegate_to_children(processed_input)
            else:
                self.logger.debug("Executing directly (no delegation)")
                result = await self.execute(processed_input)

            # Post-processing
            final_result = await self._postprocess_output(result)

            # Track KPIs
            if self.config.track_kpis:
                execution_time = (datetime.now() - start_time).total_seconds()
                await self.kpi_tracker.record_execution(
                    execution_time=execution_time,
                    success=final_result.get('success', False),
                    metadata=final_result.get('metadata', {})
                )

            self.logger.info(
                f"Execution completed - PCF {self.pcf_metadata.hierarchy_id}, "
                f"success={final_result.get('success', False)}, "
                f"duration={(datetime.now() - start_time).total_seconds():.2f}s"
            )

            return final_result

        except Exception as e:
            self.logger.error(
                f"Execution failed - PCF {self.pcf_metadata.hierarchy_id}: {str(e)}",
                exc_info=True
            )

            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'metadata': {
                    'pcf_element_id': self.pcf_metadata.pcf_element_id,
                    'hierarchy_id': self.pcf_metadata.hierarchy_id,
                    'timestamp': datetime.now().isoformat()
                }
            }

    async def _delegate_to_children(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delegate execution to child agents in the PCF hierarchy.

        Executes child agents sequentially or in parallel depending on
        the process logic.
        """
        import asyncio

        results = []

        # Execute all children (can be made parallel with asyncio.gather)
        for child_id, child_agent in self.child_agents.items():
            self.logger.debug(f"Executing child agent: {child_id}")
            child_result = await child_agent.execute_with_hierarchy(input_data)
            results.append(child_result)

        # Aggregate child results
        return await self._aggregate_child_results(results)

    async def _aggregate_child_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate results from child agents.

        Default implementation - override for custom aggregation logic.
        """
        all_successful = all(r.get('success', False) for r in results)

        aggregated = {
            'success': all_successful,
            'child_results': results,
            'summary': self._create_summary(results),
            'metadata': {
                'pcf_element_id': self.pcf_metadata.pcf_element_id,
                'hierarchy_id': self.pcf_metadata.hierarchy_id,
                'total_children': len(results),
                'successful_children': sum(1 for r in results if r.get('success', False)),
                'timestamp': datetime.now().isoformat()
            }
        }

        # Merge all child outputs
        if self.config.aggregate_child_results:
            aggregated['aggregated_outputs'] = {}
            for i, result in enumerate(results):
                if 'output_data' in result:
                    aggregated['aggregated_outputs'][f'child_{i}'] = result['output_data']

        return aggregated

    async def _preprocess_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pre-process input data.

        Override for custom input validation/transformation.
        """
        return input_data

    async def _postprocess_output(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-process output data.

        Override for custom output formatting/enrichment.
        """
        # Ensure required fields
        if 'metadata' not in output_data:
            output_data['metadata'] = {}

        # Add PCF metadata
        output_data['metadata'].update({
            'pcf_element_id': self.pcf_metadata.pcf_element_id,
            'hierarchy_id': self.pcf_metadata.hierarchy_id,
            'level': self.pcf_metadata.level,
            'timestamp': datetime.now().isoformat()
        })

        return output_data

    def _create_summary(self, results: List[Dict[str, Any]]) -> str:
        """Create human-readable summary of results"""
        success_count = sum(1 for r in results if r.get('success', False))
        return (
            f"Completed {success_count}/{len(results)} child processes successfully. "
            f"PCF Process: {self.pcf_metadata.hierarchy_id} - {self.pcf_metadata.activity_name or self.pcf_metadata.process_name}"
        )

    def register_child_agent(self, child: 'PCFBaseAgent'):
        """Register a child agent in the PCF hierarchy"""
        self.child_agents[child.config.agent_id] = child
        self.logger.debug(
            f"Registered child agent: {child.config.agent_id} "
            f"(PCF {child.pcf_metadata.hierarchy_id})"
        )

    def get_pcf_lineage(self) -> Dict[str, Any]:
        """Get complete PCF lineage of this agent"""
        return self.pcf_metadata.to_dict()

    def get_kpi_statistics(self) -> Dict[str, Any]:
        """Get KPI statistics for this agent"""
        return self.kpi_tracker.get_statistics()

    def to_openapi_spec(self) -> Dict[str, Any]:
        """
        Generate OpenAPI specification for this agent's execution endpoint.

        Used for BPM system integration and service catalog.
        """
        return {
            'paths': {
                f'/api/pcf/{self.pcf_metadata.hierarchy_id}/execute': {
                    'post': {
                        'summary': f'Execute {self.pcf_metadata.activity_name or self.pcf_metadata.process_name}',
                        'description': f'PCF Element: {self.pcf_metadata.pcf_element_id}',
                        'operationId': f'execute_{self.pcf_metadata.hierarchy_id.replace(".", "_")}',
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'input_data': {'type': 'object'},
                                            'execution_mode': {
                                                'type': 'string',
                                                'enum': ['sync', 'async', 'delegate_to_children']
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        'responses': {
                            '200': {
                                'description': 'Execution successful',
                                'content': {
                                    'application/json': {
                                        'schema': {
                                            'type': 'object',
                                            'properties': {
                                                'success': {'type': 'boolean'},
                                                'output_data': {'type': 'object'},
                                                'metadata': {'type': 'object'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }


# ============================================================================
# Level-Specific Base Classes
# ============================================================================

class CategoryAgentBase(PCFBaseAgent):
    """
    Base for Level 1 (Category) agents.

    Categories orchestrate entire functional areas (e.g., "Develop Vision and Strategy").
    Typically delegate to Process Group agents.
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(config)
        assert config.pcf_metadata.level == 1, "Must be Level 1 (Category)"


class ProcessGroupAgentBase(PCFBaseAgent):
    """
    Base for Level 2 (Process Group) agents.

    Process Groups coordinate related processes (e.g., "Define business concept").
    Typically delegate to Process agents.
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(config)
        assert config.pcf_metadata.level == 2, "Must be Level 2 (Process Group)"


class ProcessAgentBase(PCFBaseAgent):
    """
    Base for Level 3 (Process) agents.

    Processes are the core business logic (e.g., "Assess external environment").
    May delegate to Activity agents or execute directly.
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(config)
        assert config.pcf_metadata.level == 3, "Must be Level 3 (Process)"


class ActivityAgentBase(PCFBaseAgent):
    """
    Base for Level 4 (Activity) agents.

    Activities are key execution steps (e.g., "Identify competitors").
    Usually atomic, but may delegate to Task agents for very detailed processes.
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(config)
        assert config.pcf_metadata.level == 4, "Must be Level 4 (Activity)"


class TaskAgentBase(PCFBaseAgent):
    """
    Base for Level 5 (Task) agents.

    Tasks are granular work elements (e.g., specific IT maintenance steps).
    Always atomic - no delegation.
    """

    def __init__(self, config: PCFAgentConfig):
        super().__init__(config)
        assert config.pcf_metadata.level == 5, "Must be Level 5 (Task)"

    async def _delegate_to_children(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tasks never delegate - always execute directly"""
        return await self.execute(input_data)
