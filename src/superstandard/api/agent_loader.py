"""
PCF Agent Loader

Dynamically loads and instantiates PCF agents based on hierarchy ID.
Maintains registry of available agents and their metadata.
"""

import json
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from superstandard.agents.pcf.base import PCFBaseAgent


class AgentLoadError(Exception):
    """Raised when agent loading fails"""
    pass


class PCFAgentRegistry:
    """
    Registry and loader for PCF agents.

    Responsibilities:
    - Load PCF registry JSON
    - Find agent metadata by hierarchy ID
    - Dynamically import and instantiate agents
    - Cache agent instances
    - Provide search functionality
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        # Load PCF registry
        if registry_path is None:
            registry_path = (
                Path(__file__).parent.parent /
                'agents/pcf/metadata/pcf_registry.json'
            )

        with open(registry_path, 'r') as f:
            self.registry = json.load(f)

        self.logger.info(f"Loaded PCF registry with {self.registry['total_categories']} categories")

        # Build index for fast lookup
        self._hierarchy_index: Dict[str, Dict[str, Any]] = {}
        self._element_id_index: Dict[str, Dict[str, Any]] = {}
        self._build_index()

        # Agent instance cache
        self._agent_cache: Dict[str, PCFBaseAgent] = {}

        # Agent implementation mapping (hierarchy_id -> module path)
        self._agent_implementations: Dict[str, str] = {}
        self._discover_agent_implementations()

    def _build_index(self):
        """Build lookup indexes for fast retrieval"""
        for category in self.registry['categories']:
            self._index_element(category)

            for pg in category.get('process_groups', []):
                self._index_element(pg)

                for process in pg.get('processes', []):
                    self._index_element(process)

                    for activity in process.get('activities', []):
                        self._index_element(activity)

                        for task in activity.get('tasks', []):
                            self._index_element(task)

        self.logger.info(
            f"Built index with {len(self._hierarchy_index)} hierarchy IDs, "
            f"{len(self._element_id_index)} element IDs"
        )

    def _index_element(self, element: Dict[str, Any]):
        """Index a single PCF element"""
        hierarchy_id = element.get('hierarchy_id')
        element_id = element.get('element_id')

        if hierarchy_id:
            self._hierarchy_index[hierarchy_id] = element

        if element_id:
            self._element_id_index[element_id] = element

    def _discover_agent_implementations(self):
        """
        Discover implemented agents by scanning the agents directory.

        Looks for Python files matching the naming pattern.
        """
        agents_dir = Path(__file__).parent.parent / 'agents/pcf'

        # Currently, we only have 1.1.1.1 implemented
        # This will be expanded as more agents are created
        self._agent_implementations = {
            '1.1.1.1': 'superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_1_identify_competitors'
        }

        self.logger.info(f"Discovered {len(self._agent_implementations)} agent implementations")

    def get_metadata(self, hierarchy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get PCF metadata for a hierarchy ID.

        Args:
            hierarchy_id: PCF hierarchy ID (e.g., "1.1.1.1")

        Returns:
            Metadata dict or None if not found
        """
        return self._hierarchy_index.get(hierarchy_id)

    def get_metadata_by_element_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Get PCF metadata by element ID"""
        return self._element_id_index.get(element_id)

    def is_implemented(self, hierarchy_id: str) -> bool:
        """Check if agent is implemented"""
        return hierarchy_id in self._agent_implementations

    def get_agent(self, hierarchy_id: str, use_cache: bool = True) -> PCFBaseAgent:
        """
        Get or instantiate a PCF agent.

        Args:
            hierarchy_id: PCF hierarchy ID
            use_cache: Whether to use cached instance

        Returns:
            PCF agent instance

        Raises:
            AgentLoadError: If agent cannot be loaded
        """
        # Check cache
        if use_cache and hierarchy_id in self._agent_cache:
            self.logger.debug(f"Returning cached agent for {hierarchy_id}")
            return self._agent_cache[hierarchy_id]

        # Check if implemented
        if not self.is_implemented(hierarchy_id):
            raise AgentLoadError(
                f"Agent {hierarchy_id} not yet implemented. "
                f"Available: {list(self._agent_implementations.keys())}"
            )

        # Get module path
        module_path = self._agent_implementations[hierarchy_id]

        try:
            # Import module
            self.logger.info(f"Loading agent from {module_path}")
            module = importlib.import_module(module_path)

            # Find agent class (convention: ends with 'Agent')
            agent_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PCFBaseAgent) and
                    attr != PCFBaseAgent and
                    attr_name.endswith('Agent')):
                    agent_class = attr
                    break

            if agent_class is None:
                raise AgentLoadError(f"No agent class found in {module_path}")

            # Instantiate agent
            agent = agent_class()
            self.logger.info(f"Instantiated {agent_class.__name__} for {hierarchy_id}")

            # Cache it
            if use_cache:
                self._agent_cache[hierarchy_id] = agent

            return agent

        except Exception as e:
            self.logger.error(f"Failed to load agent {hierarchy_id}: {e}")
            raise AgentLoadError(f"Failed to load agent {hierarchy_id}: {str(e)}") from e

    def search(
        self,
        query: Optional[str] = None,
        level: Optional[int] = None,
        category_id: Optional[str] = None,
        has_implementation: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for PCF agents.

        Args:
            query: Text search query (searches name, description)
            level: Filter by PCF level (1-5)
            category_id: Filter by category
            has_implementation: Filter by implementation status
            limit: Max results
            offset: Pagination offset

        Returns:
            List of matching metadata dicts with relevance scores
        """
        results = []

        # Search through all indexed elements
        for hierarchy_id, metadata in self._hierarchy_index.items():
            # Apply filters
            if level is not None and metadata.get('level') != level:
                continue

            if category_id is not None:
                # Get category from hierarchy
                cat_id = hierarchy_id.split('.')[0] + '.0'
                if cat_id != category_id:
                    continue

            if has_implementation is not None:
                is_impl = self.is_implemented(hierarchy_id)
                if is_impl != has_implementation:
                    continue

            # Text search
            relevance_score = 1.0
            if query:
                query_lower = query.lower()
                name = metadata.get('name', '').lower()
                desc = metadata.get('description', '').lower()

                if query_lower in name:
                    relevance_score = 1.0
                elif query_lower in desc:
                    relevance_score = 0.7
                else:
                    # Partial match
                    words = query_lower.split()
                    matches = sum(1 for word in words if word in name or word in desc)
                    if matches == 0:
                        continue
                    relevance_score = matches / len(words) * 0.5

            # Add result
            result = {
                **metadata,
                'relevance_score': relevance_score,
                'is_implemented': self.is_implemented(hierarchy_id)
            }
            results.append(result)

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Paginate
        total = len(results)
        results = results[offset:offset + limit]

        return results

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all metadata indexed by hierarchy ID"""
        return self._hierarchy_index.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            'total_elements': len(self._hierarchy_index),
            'total_categories': self.registry['total_categories'],
            'implemented_agents': len(self._agent_implementations),
            'implementation_percentage': (
                len(self._agent_implementations) / len(self._hierarchy_index) * 100
                if self._hierarchy_index else 0
            ),
            'available_agents': list(self._agent_implementations.keys())
        }


# Global registry instance
_registry: Optional[PCFAgentRegistry] = None


def get_registry() -> PCFAgentRegistry:
    """Get global registry instance (singleton)"""
    global _registry
    if _registry is None:
        _registry = PCFAgentRegistry()
    return _registry
