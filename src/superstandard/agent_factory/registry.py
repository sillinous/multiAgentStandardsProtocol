"""
Agent Registry & Catalog System

Searchable registry of all available agents with marketplace-like capabilities.

Integrates with Discovery Protocol to make all agents discoverable and usable.

Features:
- Auto-discovery of generated agents
- Capability-based search
- Category/process filtering
- Agent marketplace view
- Discovery Protocol integration

Usage:
    from src.superstandard.agent_factory import AgentRegistry

    # Create registry
    registry = AgentRegistry()

    # Discover all agents
    await registry.discover_agents()

    # Search by capability
    agents = registry.search(capability="competitive_analysis")

    # Get by category
    agents = registry.get_by_category("Vision and Strategy")
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class RegisteredAgent:
    """Registered agent in the catalog"""
    agent_id: str
    name: str
    apqc_process: str
    apqc_category: str
    capabilities: List[str]
    cost_per_request: float
    avg_latency_ms: float
    quality_baseline: float
    description: str = ""
    file_path: str = ""
    class_name: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentRegistry:
    """
    Agent Registry & Catalog System

    Manages a searchable catalog of all available agents.
    Integrates with Discovery Protocol for seamless agent usage.
    """

    def __init__(self, agents_dir: str = None):
        self.agents_dir = Path(agents_dir) if agents_dir else Path(__file__).parent.parent.parent.parent / "agents" / "generated"
        self.agents: Dict[str, RegisteredAgent] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> agent_ids
        self.category_index: Dict[str, List[str]] = {}  # category -> agent_ids

    def discover_agents(self) -> int:
        """
        Auto-discover all agents in the agents directory

        Returns number of agents discovered
        """
        if not self.agents_dir.exists():
            print(f"⚠️  Agents directory not found: {self.agents_dir}")
            return 0

        discovered = 0

        # Find all Python files
        for agent_file in self.agents_dir.glob("*.py"):
            if agent_file.name.startswith("__"):
                continue

            try:
                agent_info = self._load_agent_metadata(agent_file)
                if agent_info:
                    self._register_agent(agent_info)
                    discovered += 1
            except Exception as e:
                print(f"⚠️  Failed to load {agent_file.name}: {e}")

        # Build indexes
        self._build_indexes()

        print(f"✅ Discovered {discovered} agents")
        return discovered

    def _load_agent_metadata(self, file_path: Path) -> Optional[RegisteredAgent]:
        """Load agent metadata from Python file"""
        # Load the module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[file_path.stem] = module
        spec.loader.exec_module(module)

        # Get AGENT_METADATA
        if not hasattr(module, 'AGENT_METADATA'):
            return None

        metadata = module.AGENT_METADATA

        # Extract class name (first class in module)
        class_name = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and not name.startswith('_'):
                class_name = name
                break

        return RegisteredAgent(
            agent_id=metadata['agent_id'],
            name=metadata['name'],
            apqc_process=metadata['apqc_process'],
            apqc_category=metadata['apqc_category'],
            capabilities=metadata['capabilities'],
            cost_per_request=metadata['cost_per_request'],
            avg_latency_ms=metadata['avg_latency_ms'],
            quality_baseline=metadata.get('quality_baseline', 0.85),
            file_path=str(file_path),
            class_name=class_name or "",
            metadata=metadata
        )

    def _register_agent(self, agent: RegisteredAgent):
        """Register agent in catalog"""
        self.agents[agent.agent_id] = agent

    def _build_indexes(self):
        """Build search indexes"""
        self.capabilities_index.clear()
        self.category_index.clear()

        for agent_id, agent in self.agents.items():
            # Index by capabilities
            for capability in agent.capabilities:
                if capability not in self.capabilities_index:
                    self.capabilities_index[capability] = []
                self.capabilities_index[capability].append(agent_id)

            # Index by category
            if agent.apqc_category not in self.category_index:
                self.category_index[agent.apqc_category] = []
            self.category_index[agent.apqc_category].append(agent_id)

    def search(
        self,
        capability: str = None,
        category: str = None,
        max_cost: float = None,
        min_quality: float = None
    ) -> List[RegisteredAgent]:
        """
        Search for agents matching criteria

        Args:
            capability: Required capability
            category: APQC category
            max_cost: Maximum cost per request
            min_quality: Minimum quality baseline

        Returns:
            List of matching agents
        """
        results = []

        # Start with all agents or filter by capability
        if capability:
            agent_ids = self.capabilities_index.get(capability, [])
            candidates = [self.agents[aid] for aid in agent_ids]
        elif category:
            agent_ids = self.category_index.get(category, [])
            candidates = [self.agents[aid] for aid in agent_ids]
        else:
            candidates = list(self.agents.values())

        # Apply filters
        for agent in candidates:
            if max_cost and agent.cost_per_request > max_cost:
                continue
            if min_quality and agent.quality_baseline < min_quality:
                continue
            results.append(agent)

        # Sort by quality (highest first)
        results.sort(key=lambda a: a.quality_baseline, reverse=True)

        return results

    def get_by_id(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_by_category(self, category: str) -> List[RegisteredAgent]:
        """Get all agents in a category"""
        return self.search(category=category)

    def get_capabilities(self) -> List[str]:
        """Get all unique capabilities"""
        return sorted(self.capabilities_index.keys())

    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        return sorted(self.category_index.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_agents": len(self.agents),
            "total_capabilities": len(self.capabilities_index),
            "total_categories": len(self.category_index),
            "avg_cost": sum(a.cost_per_request for a in self.agents.values()) / len(self.agents) if self.agents else 0,
            "avg_quality": sum(a.quality_baseline for a in self.agents.values()) / len(self.agents) if self.agents else 0
        }

    def export_catalog(self, output_path: str = None) -> str:
        """
        Export catalog to JSON

        Returns path to exported file
        """
        if output_path is None:
            output_path = "agent_catalog.json"

        catalog = {
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "capabilities": self.get_capabilities(),
            "categories": self.get_categories(),
            "stats": self.get_stats()
        }

        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)

        print(f"✅ Exported catalog to: {output_path}")
        return output_path

    def show_marketplace(self):
        """Display marketplace view of all agents"""
        print("\n" + "="*80)
        print("🏪 AGENT MARKETPLACE")
        print("="*80)

        if not self.agents:
            print("\n   No agents available")
            return

        # Group by category
        for category in sorted(self.get_categories()):
            agents = self.get_by_category(category)

            print(f"\n📁 {category} ({len(agents)} agents)")
            print("   " + "-"*76)

            for agent in sorted(agents, key=lambda a: a.apqc_process):
                print(f"\n   {agent.name}")
                print(f"      ID: {agent.agent_id}")
                print(f"      Process: {agent.apqc_process}")
                print(f"      Capabilities: {', '.join(agent.capabilities)}")
                print(f"      Cost: ${agent.cost_per_request:.2f}/req")
                print(f"      Quality: {agent.quality_baseline:.0%}")
                print(f"      Latency: {agent.avg_latency_ms:.0f}ms")

        # Show summary
        stats = self.get_stats()
        print("\n" + "="*80)
        print("📊 MARKETPLACE STATISTICS")
        print("="*80)
        print(f"\n   Total Agents: {stats['total_agents']}")
        print(f"   Categories: {stats['total_categories']}")
        print(f"   Capabilities: {stats['total_capabilities']}")
        print(f"   Avg Cost: ${stats['avg_cost']:.2f}/request")
        print(f"   Avg Quality: {stats['avg_quality']:.0%}")
        print()

    async def register_with_discovery(self, discovery_service):
        """
        Register all agents with Discovery Protocol

        Args:
            discovery_service: Discovery service instance
        """
        from ..protocols.discovery import AgentCapability, AgentMetadata

        registered = 0

        for agent in self.agents.values():
            capabilities = [
                AgentCapability(
                    name=cap,
                    version="1.0.0",
                    description=f"{cap} capability"
                )
                for cap in agent.capabilities
            ]

            metadata = AgentMetadata(
                cost_per_request=agent.cost_per_request,
                avg_latency_ms=agent.avg_latency_ms,
                reputation_score=agent.quality_baseline,
                tags=["apqc", agent.apqc_category.lower().replace(" ", "_")]
            )

            await discovery_service.register_agent(
                agent_id=agent.agent_id,
                name=agent.name,
                agent_type=agent.apqc_process,
                capabilities=capabilities,
                metadata=metadata
            )

            registered += 1

        print(f"✅ Registered {registered} agents with Discovery Protocol")
        return registered


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create global registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


__all__ = ['AgentRegistry', 'RegisteredAgent', 'get_registry']
