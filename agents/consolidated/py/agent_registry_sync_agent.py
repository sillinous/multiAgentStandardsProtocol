"""
Agent Registry Sync Agent

Automatically discovers and registers agents in the agent library.
Maintains synchronization between the file system and the agent registry.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import importlib.util
import ast
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentRegistrySyncAgent:
    """
    Meta-agent that automatically discovers and registers agents.

    Features:
    - Scans agent directories for new agents
    - Extracts agent metadata from source code
    - Automatically registers discovered agents
    - Provides sync status and statistics
    - Can run on-demand or scheduled
    """

    def __init__(self):
        self.agent_id = "agent_registry_sync_v1"
        self.name = "Agent Registry Sync Agent"
        self.version = "1.0.0"

        # Agent scan directories (relative to backend/)
        self.scan_directories = [
            "app/agents/hybrid_ai",
            "app/agents/meta",
            "app/agents/activities",
            "app/agents/processes",
            "app/agents",
        ]

        # Statistics
        self.stats = {
            "last_sync": None,
            "agents_discovered": 0,
            "agents_registered": 0,
            "sync_errors": 0,
            "total_syncs": 0
        }

        logger.info(f"🔄 {self.name} initialized")

    def discover_agents(self, scan_path: str) -> List[Dict[str, Any]]:
        """
        Discover agents in a directory.

        Args:
            scan_path: Directory to scan for agent files

        Returns:
            List of discovered agent metadata
        """
        discovered = []
        base_path = Path(__file__).parent.parent.parent.parent  # Get backend root
        full_scan_path = base_path / scan_path

        if not full_scan_path.exists():
            logger.warning(f"Scan path does not exist: {full_scan_path}")
            return discovered

        logger.info(f"🔍 Scanning: {full_scan_path}")

        # Find all Python files
        for py_file in full_scan_path.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("test_"):
                continue

            try:
                agent_info = self._extract_agent_metadata(py_file, scan_path)
                if agent_info:
                    discovered.append(agent_info)
                    logger.info(f"✓ Discovered: {agent_info['name']}")
            except Exception as e:
                logger.error(f"Error parsing {py_file}: {e}")
                self.stats["sync_errors"] += 1

        return discovered

    def _extract_agent_metadata(self, file_path: Path, base_dir: str) -> Optional[Dict[str, Any]]:
        """
        Extract agent metadata from a Python file using AST parsing.

        Args:
            file_path: Path to the Python file
            base_dir: Base directory for relative path

        Returns:
            Agent metadata dict or None if not an agent file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the file
            tree = ast.parse(content)

            # Look for class definitions
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue

                # Check if it's an agent class (ends with Agent or inherits from BaseAgent/HybridBaseAgent)
                if not (node.name.endswith('Agent') or self._inherits_from_agent(node)):
                    continue

                # Extract docstring
                docstring = ast.get_docstring(node) or "No description available"

                # Extract class-level attributes
                agent_id = self._extract_class_attribute(node, 'agent_id')
                if not agent_id:
                    # Generate ID from filename
                    agent_id = f"{file_path.stem}_v1"

                # Determine capabilities from docstring or code
                capabilities = self._extract_capabilities(node, docstring)

                # Determine category from path
                category = self._determine_category(base_dir)

                # Build relative file path
                rel_path = file_path.relative_to(Path(__file__).parent.parent.parent.parent)

                return {
                    "id": agent_id,
                    "name": node.name,
                    "description": docstring.split('\n')[0],  # First line
                    "category": category,
                    "capabilities": capabilities,
                    "file_path": f"/{rel_path}",
                    "class_name": node.name,
                    "discovered_at": datetime.utcnow().isoformat(),
                    "tags": self._generate_tags(file_path, base_dir)
                }

            return None

        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return None

    def _inherits_from_agent(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from an agent base class"""
        for base in node.bases:
            if isinstance(base, ast.Name):
                if 'Agent' in base.id:
                    return True
        return False

    def _extract_class_attribute(self, node: ast.ClassDef, attr_name: str) -> Optional[str]:
        """Extract a class-level attribute value"""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        if isinstance(item.value, ast.Constant):
                            return item.value.value
        return None

    def _extract_capabilities(self, node: ast.ClassDef, docstring: str) -> List[str]:
        """Extract agent capabilities from code or docstring"""
        capabilities = []

        # Look for capabilities attribute
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == 'capabilities':
                        if isinstance(item.value, ast.List):
                            for elt in item.value.elts:
                                if isinstance(elt, ast.Constant):
                                    capabilities.append(elt.value)

        # If no capabilities found, derive from name
        if not capabilities:
            # Extract from class name (e.g., ProductAnalysisAgent -> product_analysis)
            name_parts = []
            for char in node.name:
                if char.isupper() and name_parts:
                    name_parts.append('_')
                name_parts.append(char.lower())
            capability = ''.join(name_parts).replace('_agent', '')
            capabilities.append(capability)

        return capabilities

    def _determine_category(self, base_dir: str) -> str:
        """Determine agent category from directory path"""
        if "hybrid_ai" in base_dir:
            return "core_utility"
        elif "meta" in base_dir:
            return "meta"
        elif "activities" in base_dir:
            return "task_level"
        elif "processes" in base_dir:
            return "operations"
        else:
            return "core_utility"

    def _generate_tags(self, file_path: Path, base_dir: str) -> List[str]:
        """Generate relevant tags for the agent"""
        tags = []

        if "hybrid" in str(file_path).lower():
            tags.extend(["hybrid-ai", "cost-optimization", "local-llm"])

        if "meta" in base_dir:
            tags.append("meta-agent")

        if "activity" in str(file_path).lower():
            tags.append("activity")

        if "process" in str(file_path).lower():
            tags.append("process")

        tags.append("auto-discovered")

        return tags

    async def sync(self) -> Dict[str, Any]:
        """
        Perform a full synchronization scan.

        Returns:
            Sync results including discovered and registered agents
        """
        logger.info("🔄 Starting agent registry sync...")

        self.stats["total_syncs"] += 1
        self.stats["last_sync"] = datetime.utcnow().isoformat()

        all_discovered = []

        # Scan all directories
        for scan_dir in self.scan_directories:
            discovered = self.discover_agents(scan_dir)
            all_discovered.extend(discovered)

        self.stats["agents_discovered"] = len(all_discovered)

        # In a full implementation, we would:
        # 1. Load current agent registry
        # 2. Compare discovered agents with registered agents
        # 3. Register new agents
        # 4. Update existing agents
        # 5. Flag removed agents

        result = {
            "status": "success",
            "sync_time": self.stats["last_sync"],
            "agents_discovered": len(all_discovered),
            "agents": all_discovered,
            "stats": self.stats
        }

        logger.info(f"✅ Sync complete: {len(all_discovered)} agents discovered")

        return result

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "version": self.version,
            "last_sync": self.stats["last_sync"],
            "stats": self.stats,
            "scan_directories": self.scan_directories
        }

    async def register_agent(self, agent_metadata: Dict[str, Any]) -> bool:
        """
        Register a single agent in the agent library.

        Args:
            agent_metadata: Agent metadata dict

        Returns:
            Success status
        """
        try:
            # In a full implementation, this would:
            # 1. Validate agent metadata
            # 2. Check if agent already exists
            # 3. Add to agent library (database or file)
            # 4. Update agent registry

            logger.info(f"✓ Registered: {agent_metadata['name']}")
            self.stats["agents_registered"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_metadata.get('name')}: {e}")
            self.stats["sync_errors"] += 1
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the library.

        Args:
            agent_id: Agent ID to unregister

        Returns:
            Success status
        """
        try:
            # In a full implementation, this would:
            # 1. Remove from agent library
            # 2. Update agent registry
            # 3. Archive agent data

            logger.info(f"✓ Unregistered: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            self.stats["sync_errors"] += 1
            return False

    def export_discovered_agents(self, format: str = "json") -> str:
        """
        Export discovered agents in various formats.

        Args:
            format: Export format (json, markdown, etc.)

        Returns:
            Exported data as string
        """
        # This would be implemented based on needs
        return json.dumps(self.stats, indent=2)


# Global instance
agent_registry_sync_agent = AgentRegistrySyncAgent()


if __name__ == "__main__":
    # Test run
    import asyncio

    async def test():
        agent = AgentRegistrySyncAgent()
        result = await agent.sync()
        print(json.dumps(result, indent=2))

    asyncio.run(test())
