"""
Agent Index System
Provides quick indexing and lookup for all agents in the ecosystem.
Includes architecture debt tracking and fast agent identification.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class AgentStatus(str, Enum):
    """Agent development status"""

    PRODUCTION = "production"
    BETA = "beta"
    DEVELOPMENT = "development"
    PLANNED = "planned"
    DEPRECATED = "deprecated"


class ArchitectureDebtSeverity(str, Enum):
    """Severity levels for architecture debt"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ArchitectureDebtItem:
    """Architecture debt tracking item"""

    id: str
    agent_id: str
    title: str
    description: str
    severity: ArchitectureDebtSeverity
    category: str  # code_quality, documentation, testing, performance, security
    created_at: str
    estimated_effort_hours: Optional[int] = None
    assigned_to: Optional[str] = None
    status: str = "open"  # open, in_progress, resolved, wont_fix
    resolution_notes: Optional[str] = None


@dataclass
class AgentIndexEntry:
    """Quick index entry for an agent"""

    agent_id: str
    class_name: str
    file_path: str
    category: str
    status: AgentStatus
    description: Optional[str] = None
    capabilities: List[str] = None
    dependencies: List[str] = None
    registered: bool = False
    architecture_debt: List[str] = None  # List of debt item IDs
    last_updated: Optional[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.dependencies is None:
            self.dependencies = []
        if self.architecture_debt is None:
            self.architecture_debt = []


class AgentIndexSystem:
    """
    Fast agent indexing and lookup system.
    Provides O(1) lookups by agent_id, class_name, or file_path.
    """

    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file or Path(__file__).parent.parent / "agent_index.json"
        self.debt_file = self.index_file.parent / "architecture_debt.json"

        # Fast lookup indices
        self.agents_by_id: Dict[str, AgentIndexEntry] = {}
        self.agents_by_class: Dict[str, AgentIndexEntry] = {}
        self.agents_by_file: Dict[str, AgentIndexEntry] = {}
        self.agents_by_category: Dict[str, List[AgentIndexEntry]] = {}

        # Architecture debt tracking
        self.debt_items: Dict[str, ArchitectureDebtItem] = {}

        # Load existing index
        self.load()

    def load(self):
        """Load index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    for item in data.get("agents", []):
                        entry = AgentIndexEntry(**item)
                        self._add_to_indices(entry)
            except Exception as e:
                print(f"Error loading agent index: {e}")

        if self.debt_file.exists():
            try:
                with open(self.debt_file, "r") as f:
                    data = json.load(f)
                    for item in data.get("debt_items", []):
                        debt = ArchitectureDebtItem(**item)
                        self.debt_items[debt.id] = debt
            except Exception as e:
                print(f"Error loading architecture debt: {e}")

    def save(self):
        """Save index to disk"""
        # Save agent index
        data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_agents": len(self.agents_by_id),
            "agents": [asdict(agent) for agent in self.agents_by_id.values()],
        }

        with open(self.index_file, "w") as f:
            json.dump(data, f, indent=2)

        # Save architecture debt
        debt_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_items": len(self.debt_items),
            "debt_items": [asdict(item) for item in self.debt_items.values()],
        }

        with open(self.debt_file, "w") as f:
            json.dump(debt_data, f, indent=2)

    def _add_to_indices(self, entry: AgentIndexEntry):
        """Add entry to all indices"""
        self.agents_by_id[entry.agent_id] = entry
        self.agents_by_class[entry.class_name] = entry
        self.agents_by_file[entry.file_path] = entry

        if entry.category not in self.agents_by_category:
            self.agents_by_category[entry.category] = []
        self.agents_by_category[entry.category].append(entry)

    def index_agent(
        self,
        agent_id: str,
        class_name: str,
        file_path: str,
        category: str,
        status: AgentStatus = AgentStatus.DEVELOPMENT,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        registered: bool = False,
    ) -> AgentIndexEntry:
        """Add or update agent in index"""
        entry = AgentIndexEntry(
            agent_id=agent_id,
            class_name=class_name,
            file_path=file_path,
            category=category,
            status=status,
            description=description,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            registered=registered,
            last_updated=datetime.now().isoformat(),
        )

        self._add_to_indices(entry)
        self.save()
        return entry

    def get_by_id(self, agent_id: str) -> Optional[AgentIndexEntry]:
        """O(1) lookup by agent ID"""
        return self.agents_by_id.get(agent_id)

    def get_by_class(self, class_name: str) -> Optional[AgentIndexEntry]:
        """O(1) lookup by class name"""
        return self.agents_by_class.get(class_name)

    def get_by_file(self, file_path: str) -> Optional[AgentIndexEntry]:
        """O(1) lookup by file path"""
        return self.agents_by_file.get(file_path)

    def get_by_category(self, category: str) -> List[AgentIndexEntry]:
        """Get all agents in a category"""
        return self.agents_by_category.get(category, [])

    def get_all_agents(self) -> List[AgentIndexEntry]:
        """Get all indexed agents"""
        return list(self.agents_by_id.values())

    def get_unregistered_agents(self) -> List[AgentIndexEntry]:
        """Get all unregistered agents"""
        return [agent for agent in self.agents_by_id.values() if not agent.registered]

    def mark_registered(self, agent_id: str):
        """Mark an agent as registered"""
        if agent_id in self.agents_by_id:
            self.agents_by_id[agent_id].registered = True
            self.agents_by_id[agent_id].last_updated = datetime.now().isoformat()
            self.save()

    def add_architecture_debt(
        self,
        agent_id: str,
        title: str,
        description: str,
        severity: ArchitectureDebtSeverity,
        category: str,
        estimated_effort_hours: Optional[int] = None,
    ) -> ArchitectureDebtItem:
        """Add architecture debt item"""
        debt_id = f"debt_{len(self.debt_items) + 1:04d}"

        debt = ArchitectureDebtItem(
            id=debt_id,
            agent_id=agent_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            created_at=datetime.now().isoformat(),
            estimated_effort_hours=estimated_effort_hours,
        )

        self.debt_items[debt_id] = debt

        # Add to agent's debt list
        if agent_id in self.agents_by_id:
            self.agents_by_id[agent_id].architecture_debt.append(debt_id)

        self.save()
        return debt

    def get_debt_for_agent(self, agent_id: str) -> List[ArchitectureDebtItem]:
        """Get all debt items for an agent"""
        agent = self.agents_by_id.get(agent_id)
        if not agent:
            return []

        return [
            self.debt_items[debt_id]
            for debt_id in agent.architecture_debt
            if debt_id in self.debt_items
        ]

    def get_all_debt(self, status: Optional[str] = None) -> List[ArchitectureDebtItem]:
        """Get all architecture debt items, optionally filtered by status"""
        items = list(self.debt_items.values())
        if status:
            items = [item for item in items if item.status == status]
        return items

    def resolve_debt(self, debt_id: str, resolution_notes: str):
        """Mark debt item as resolved"""
        if debt_id in self.debt_items:
            self.debt_items[debt_id].status = "resolved"
            self.debt_items[debt_id].resolution_notes = resolution_notes
            self.save()

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        total = len(self.agents_by_id)
        registered = sum(1 for agent in self.agents_by_id.values() if agent.registered)

        by_category = {}
        for category, agents in self.agents_by_category.items():
            by_category[category] = len(agents)

        by_status = {}
        for agent in self.agents_by_id.values():
            status = agent.status.value
            by_status[status] = by_status.get(status, 0) + 1

        debt_stats = {
            "total": len(self.debt_items),
            "open": sum(1 for d in self.debt_items.values() if d.status == "open"),
            "in_progress": sum(1 for d in self.debt_items.values() if d.status == "in_progress"),
            "resolved": sum(1 for d in self.debt_items.values() if d.status == "resolved"),
            "by_severity": {},
        }

        for debt in self.debt_items.values():
            if debt.status != "resolved":
                severity = debt.severity.value
                debt_stats["by_severity"][severity] = debt_stats["by_severity"].get(severity, 0) + 1

        return {
            "total_agents": total,
            "registered_agents": registered,
            "unregistered_agents": total - registered,
            "registration_rate": f"{(registered / total * 100):.1f}%" if total > 0 else "0%",
            "by_category": by_category,
            "by_status": by_status,
            "architecture_debt": debt_stats,
        }

    def search(
        self, query: str, search_fields: Optional[List[str]] = None
    ) -> List[AgentIndexEntry]:
        """Search agents by query string"""
        if search_fields is None:
            search_fields = ["agent_id", "class_name", "description", "capabilities"]

        query_lower = query.lower()
        results = []

        for agent in self.agents_by_id.values():
            match = False

            if "agent_id" in search_fields and query_lower in agent.agent_id.lower():
                match = True
            if "class_name" in search_fields and query_lower in agent.class_name.lower():
                match = True
            if (
                "description" in search_fields
                and agent.description
                and query_lower in agent.description.lower()
            ):
                match = True
            if "capabilities" in search_fields:
                for cap in agent.capabilities:
                    if query_lower in cap.lower():
                        match = True
                        break

            if match:
                results.append(agent)

        return results


# Global instance
_agent_index = None


def get_agent_index() -> AgentIndexSystem:
    """Get global agent index instance"""
    global _agent_index
    if _agent_index is None:
        _agent_index = AgentIndexSystem()
    return _agent_index


# Convenience functions
def index_agent(*args, **kwargs) -> AgentIndexEntry:
    """Index an agent"""
    return get_agent_index().index_agent(*args, **kwargs)


def get_agent(agent_id: str) -> Optional[AgentIndexEntry]:
    """Quick lookup agent by ID"""
    return get_agent_index().get_by_id(agent_id)


def search_agents(query: str) -> List[AgentIndexEntry]:
    """Search for agents"""
    return get_agent_index().search(query)


def get_index_stats() -> Dict[str, Any]:
    """Get indexing statistics"""
    return get_agent_index().get_stats()


def track_debt(
    agent_id: str,
    title: str,
    description: str,
    severity: ArchitectureDebtSeverity = ArchitectureDebtSeverity.MEDIUM,
    category: str = "code_quality",
    estimated_effort_hours: Optional[int] = None,
) -> ArchitectureDebtItem:
    """Quick function to track architecture debt"""
    return get_agent_index().add_architecture_debt(
        agent_id, title, description, severity, category, estimated_effort_hours
    )
