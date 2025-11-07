"""
Agent Registry - Central registry for discovering and managing agents

The registry provides:
- Agent discovery and search
- Category-based browsing
- Metadata management
- Version tracking
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import json
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AgentMetadata:
    """Metadata for a registered agent"""

    name: str
    category: str
    type: str  # "python", "markdown", "rust"
    file: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "SuperStandard"
    tags: List[str] = None
    dependencies: List[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AgentRegistry:
    """
    Central registry for all agents in SuperStandard

    Provides fast lookup, search, and discovery of agents.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.agents_path = self.base_path / "src" / "superstandard" / "agents"
        self.catalog_path = self.base_path / "AGENT_CATALOG.json"
        self._agents: Dict[str, AgentMetadata] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load agents from catalog"""
        if not self.catalog_path.exists():
            return

        with open(self.catalog_path) as f:
            catalog = json.load(f)

        for agent_data in catalog.get("agents", []):
            if agent_data.get("type") == "python":
                metadata = AgentMetadata(
                    name=agent_data.get("name", "Unknown"),
                    category=agent_data.get("category", "general"),
                    type=agent_data.get("type", "python"),
                    file=agent_data.get("file", ""),
                    description=agent_data.get("description", "")[
                        :200
                    ],  # Truncate long descriptions
                )
                self._agents[metadata.name] = metadata

    def discover_agents(self) -> List[AgentMetadata]:
        """
        Discover all agents by scanning directories

        Returns:
            List of agent metadata
        """
        agents = []

        if not self.agents_path.exists():
            return agents

        # Scan all category directories
        for category_dir in self.agents_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue

            category = category_dir.name

            # Find all Python files
            for agent_file in category_dir.glob("*.py"):
                if agent_file.name.startswith("_"):
                    continue

                # Extract basic info
                name = agent_file.stem
                relative_path = str(agent_file.relative_to(self.base_path))

                # Try to extract metadata from file
                metadata = self._extract_metadata(agent_file, name, category)
                metadata.file = relative_path

                agents.append(metadata)
                self._agents[name] = metadata

        return agents

    def _extract_metadata(self, file_path: Path, name: str, category: str) -> AgentMetadata:
        """Extract metadata from agent file"""

        description = ""
        version = "1.0.0"
        author = "SuperStandard"
        tags = [category]

        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract from docstring
            if '"""' in content:
                parts = content.split('"""')
                if len(parts) >= 2:
                    description = parts[1].strip().split("\n")[0][:200]

            # Extract from AGENT_METADATA dict if exists
            if "AGENT_METADATA" in content:
                # Simple extraction (could use AST for better parsing)
                for line in content.split("\n"):
                    if '"version"' in line and ":" in line:
                        version = line.split(":")[-1].strip(' ",')
                    if '"author"' in line and ":" in line:
                        author = line.split(":")[-1].strip(' ",')

        except Exception:
            pass  # Use defaults if extraction fails

        return AgentMetadata(
            name=name,
            category=category,
            type="python",
            file=str(file_path),
            description=description,
            version=version,
            author=author,
            tags=tags,
        )

    def get_agent(self, name: str) -> Optional[AgentMetadata]:
        """
        Get agent by name

        Args:
            name: Agent name

        Returns:
            Agent metadata or None if not found
        """
        return self._agents.get(name)

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentMetadata]:
        """
        Search agents

        Args:
            query: Search query (searches name and description)
            category: Filter by category
            tags: Filter by tags

        Returns:
            List of matching agents
        """
        query_lower = query.lower()
        results = []

        for agent in self._agents.values():
            # Category filter
            if category and agent.category != category:
                continue

            # Tags filter
            if tags and not any(tag in agent.tags for tag in tags):
                continue

            # Query match (name or description)
            if query_lower in agent.name.lower() or query_lower in agent.description.lower():
                results.append(agent)

        return results

    def by_category(self, category: str) -> List[AgentMetadata]:
        """
        Get all agents in a category

        Args:
            category: Category name

        Returns:
            List of agents in category
        """
        return [agent for agent in self._agents.values() if agent.category == category]

    def list_categories(self) -> List[str]:
        """
        Get all available categories

        Returns:
            List of category names
        """
        categories = set()
        for agent in self._agents.values():
            categories.add(agent.category)
        return sorted(list(categories))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Statistics dictionary
        """
        categories = {}
        for agent in self._agents.values():
            cat = agent.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_agents": len(self._agents),
            "categories": len(categories),
            "agents_by_category": categories,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def register_agent(self, metadata: AgentMetadata):
        """
        Register a new agent

        Args:
            metadata: Agent metadata
        """
        self._agents[metadata.name] = metadata

    def save_catalog(self, output_path: Optional[Path] = None):
        """
        Save catalog to file

        Args:
            output_path: Output file path (defaults to AGENT_CATALOG.json)
        """
        output_path = output_path or self.catalog_path

        catalog = {
            "generated_at": datetime.now().isoformat(),
            "total_agents": len(self._agents),
            "agents": [agent.to_dict() for agent in self._agents.values()],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)

    def __len__(self) -> int:
        """Get number of registered agents"""
        return len(self._agents)

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"<AgentRegistry: {len(self._agents)} agents, {len(self.list_categories())} categories>"
        )


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get global registry instance

    Returns:
        AgentRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def discover_all() -> List[AgentMetadata]:
    """
    Discover all agents in the system

    Returns:
        List of all agent metadata
    """
    registry = get_registry()
    return registry.discover_agents()


def search_agents(query: str, category: Optional[str] = None) -> List[AgentMetadata]:
    """
    Search for agents

    Args:
        query: Search query
        category: Optional category filter

    Returns:
        List of matching agents
    """
    registry = get_registry()
    return registry.search(query, category=category)


def get_agent(name: str) -> Optional[AgentMetadata]:
    """
    Get agent by name

    Args:
        name: Agent name

    Returns:
        Agent metadata or None
    """
    registry = get_registry()
    return registry.get_agent(name)


# Example usage
if __name__ == "__main__":
    # Create registry
    registry = AgentRegistry()

    # Discover agents
    print("Discovering agents...")
    agents = registry.discover_agents()
    print(f"Found {len(agents)} agents")

    # Get statistics
    stats = registry.get_stats()
    print(f"\nStatistics:")
    print(f"  Total: {stats['total_agents']}")
    print(f"  Categories: {stats['categories']}")
    print(f"\n  Top categories:")
    for cat, count in stats["top_categories"][:5]:
        print(f"    {cat}: {count} agents")

    # Search example
    print(f"\nSearching for 'trading'...")
    results = registry.search("trading")
    print(f"Found {len(results)} results")
    for agent in results[:5]:
        print(f"  - {agent.name} ({agent.category})")

    # Save catalog
    print(f"\nSaving catalog...")
    registry.save_catalog()
    print(f"Saved to {registry.catalog_path}")
