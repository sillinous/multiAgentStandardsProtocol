#!/usr/bin/env python3
"""
🌙 Agent Discovery Agent - Autonomous Agent Ecosystem Scanner

Discovers, registers, and maintains the complete agent registry.

This is a META-AGENT: monitors and manages the agent ecosystem itself.

Features:
- Auto-discovers all agent files in src/agents/
- Extracts metadata from docstrings and class definitions
- Automatically registers agents in orchestration system
- Validates agent structure and requirements
- Tracks agent changes and updates
- Generates agent inventory reports
- Identifies missing or broken agents

Usage:
    python src/agents/discovery_agent.py

Or as part of orchestration:
    orchestrator.run_agent('discovery_agent')
"""

import os
import sys
import ast
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import agent manager, but don't fail if unavailable (for standalone discovery)
try:
    from src.orchestration.agent_manager import (
        memory_manager, learning_manager, output_manager, AgentStatus
    )
    HAS_AGENT_MANAGER = True
except ImportError:
    HAS_AGENT_MANAGER = False

# Import BaseAgent optionally for full orchestration
try:
    from superstandard.agents.base.base_agent import BaseAgent
    HAS_BASE_AGENT = True
except ImportError:
    # Create minimal base class for standalone operation
    HAS_BASE_AGENT = False
    class BaseAgent:
        def __init__(self):
            self.name = "discovery_agent"

logger = logging.getLogger(__name__)


class AgentMetadata:
    """Metadata for discovered agent"""
    def __init__(self):
        self.name: str = ""
        self.filename: str = ""
        self.class_name: str = ""
        self.category: str = ""
        self.description: str = ""
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.dependencies: List[str] = []
        self.enabled: bool = True
        self.interval_minutes: int = 15
        self.is_meta_agent: bool = False
        self.is_autonomous: bool = False
        self.docstring: str = ""
        self.methods: List[str] = []
        self.imports: List[str] = []
        self.custom_fields: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'name': self.name,
            'filename': self.filename,
            'class_name': self.class_name,
            'category': self.category,
            'description': self.description,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'dependencies': self.dependencies,
            'enabled': self.enabled,
            'interval_minutes': self.interval_minutes,
            'is_meta_agent': self.is_meta_agent,
            'is_autonomous': self.is_autonomous,
            'methods': self.methods,
            'custom_fields': self.custom_fields
        }


class DiscoveryEngine:
    """Engine for discovering and analyzing agent files"""

    # Category mapping based on agent naming patterns and known agents
    CATEGORY_MAP = {
        'trading': 'Trading Execution',
        'copybot': 'Trading Execution',
        'risk': 'Risk Management',
        'compliance': 'Risk Management',
        'strategy': 'Strategy Development',
        'research': 'Strategy Development',
        'rbi': 'Strategy Development',
        'sniper': 'Strategy Development',
        'sentiment': 'Market Analysis',
        'whale': 'Market Analysis',
        'funding': 'Market Analysis',
        'liquidation': 'Market Analysis',
        'chartanalysis': 'Market Analysis',
        'chart': 'Market Analysis',
        'chat': 'Content Creation',
        'clips': 'Content Creation',
        'realtime_clips': 'Content Creation',
        'tweet': 'Content Creation',
        'video': 'Content Creation',
        'shortvid': 'Content Creation',
        'coingecko': 'Market Data',
        'housecoin': 'Market Data',
        'tx': 'Market Data',
        'solana': 'Specialized',
        'million': 'Specialized',
        'tiktok': 'Content Creation',
        'stream': 'Content Creation',
        'phone': 'Content Creation',
        'new_or_top': 'Market Analysis',
        'health_check': 'Infrastructure',
        'alert_management': 'Infrastructure',
        'focus': 'Strategy Development',
        'listingarb': 'Strategy Development',
        'fundingarb': 'Strategy Development',
        'example_unified': 'Specialized',
        'autonomous': 'Specialized',
        'polymarket': 'Market Analysis',
        'code_runner': 'Infrastructure',
    }

    def __init__(self, agents_dir: Path = None):
        if agents_dir is None:
            agents_dir = project_root / "src" / "agents"
        self.agents_dir = agents_dir
        self.discovered_agents: Dict[str, AgentMetadata] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def discover_all_agents(self) -> Dict[str, AgentMetadata]:
        """Discover all agent files in agents directory"""
        self.logger.info(f"Scanning for agents in {self.agents_dir}")

        agent_files = [
            f for f in self.agents_dir.glob("*_agent.py")
            if f.name not in ["base_agent.py", "discovery_agent.py"]
        ]

        self.logger.info(f"Found {len(agent_files)} agent files")

        for agent_file in sorted(agent_files):
            try:
                metadata = self._extract_metadata(agent_file)
                if metadata:
                    self.discovered_agents[metadata.name] = metadata
                    self.logger.debug(f"✓ Discovered: {metadata.name}")
            except Exception as e:
                self.logger.error(f"✗ Error discovering {agent_file.name}: {e}")

        return self.discovered_agents

    def _extract_metadata(self, agent_file: Path) -> Optional[AgentMetadata]:
        """Extract metadata from agent file"""
        try:
            with open(agent_file, 'r') as f:
                source_code = f.read()

            # Parse AST
            tree = ast.parse(source_code)

            # Find agent class
            agent_class = self._find_agent_class(tree)
            if not agent_class:
                # Handle script-only files (no Agent class)
                # Extract minimal metadata from module docstring
                return self._extract_script_metadata(agent_file, source_code, tree)

            metadata = AgentMetadata()
            metadata.filename = agent_file.name
            metadata.name = self._extract_agent_name(agent_file.name)

            # Extract class name
            metadata.class_name = agent_class.name

            # Extract docstring
            docstring = ast.get_docstring(agent_class)
            if docstring:
                metadata.docstring = docstring
                metadata.description = docstring.split('\n')[0]

            # Extract metadata from class attributes and docstring
            self._extract_from_class(agent_class, metadata)
            self._extract_from_docstring(metadata)

            # Auto-categorize if category still empty
            self._auto_categorize(metadata)

            # Extract methods
            metadata.methods = [
                node.name for node in ast.walk(agent_class)
                if isinstance(node, ast.FunctionDef)
            ]

            # Extract imports
            metadata.imports = self._extract_imports(tree)

            return metadata

        except Exception as e:
            self.logger.error(f"Error extracting metadata from {agent_file.name}: {e}")
            return None

    def _extract_script_metadata(self, agent_file: Path, source_code: str, tree: ast.AST) -> Optional[AgentMetadata]:
        """Extract metadata from script-only agent file (no Agent class)"""
        try:
            metadata = AgentMetadata()
            metadata.filename = agent_file.name
            metadata.name = self._extract_agent_name(agent_file.name)
            metadata.class_name = None  # No class in script files
            metadata.is_meta_agent = False

            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                metadata.docstring = module_docstring
                metadata.description = module_docstring.split('\n')[0]
            else:
                metadata.description = f"Script-based {metadata.name} agent"

            # Extract imports
            metadata.imports = self._extract_imports(tree)

            # Auto-categorize
            self._auto_categorize(metadata)

            return metadata

        except Exception as e:
            self.logger.error(f"Error extracting script metadata from {agent_file.name}: {e}")
            return None

    def _find_agent_class(self, tree: ast.AST) -> Optional[ast.ClassDef]:
        """Find the main agent class in AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it has Agent in name
                if 'Agent' in node.name:
                    return node
        return None

    def _extract_agent_name(self, filename: str) -> str:
        """Extract agent name from filename"""
        # trading_agent.py → trading_agent
        return filename.replace('_agent.py', '').replace('.py', '')

    def _extract_from_class(self, agent_class: ast.ClassDef, metadata: AgentMetadata):
        """Extract metadata from class definitions"""
        for node in agent_class.body:
            # Look for class variables
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if var_name == '__category__':
                            if isinstance(node.value, ast.Constant):
                                metadata.category = node.value.value
                        elif var_name == '__inputs__':
                            metadata.inputs = self._extract_list(node.value)
                        elif var_name == '__outputs__':
                            metadata.outputs = self._extract_list(node.value)
                        elif var_name == '__dependencies__':
                            metadata.dependencies = self._extract_list(node.value)
                        elif var_name == '__enabled__':
                            if isinstance(node.value, ast.Constant):
                                metadata.enabled = node.value.value
                        elif var_name == '__interval_minutes__':
                            if isinstance(node.value, ast.Constant):
                                metadata.interval_minutes = node.value.value
                        elif var_name == '__meta_agent__':
                            if isinstance(node.value, ast.Constant):
                                metadata.is_meta_agent = node.value.value

    def _extract_from_docstring(self, metadata: AgentMetadata):
        """Extract metadata from docstring"""
        if not metadata.docstring:
            return

        lines = metadata.docstring.split('\n')

        # Parse structured docstring
        section = None
        for line in lines:
            line = line.strip()

            # Check for section headers
            if line.startswith('Inputs:') or line.startswith('INPUT:'):
                section = 'inputs'
            elif line.startswith('Outputs:') or line.startswith('OUTPUT:'):
                section = 'outputs'
            elif line.startswith('Dependencies:') or line.startswith('DEPENDS:'):
                section = 'dependencies'
            elif line.startswith('Category:') or line.startswith('CATEGORY:'):
                section = 'category'
            elif line.startswith('Interval:') or line.startswith('INTERVAL:'):
                section = 'interval'
            elif line.startswith('Meta:') or line.startswith('META:'):
                section = 'meta'
            elif section and line:
                # Add to current section
                line_clean = line.lstrip('-• ').strip()
                if section == 'inputs' and line_clean:
                    if line_clean not in metadata.inputs:
                        metadata.inputs.append(line_clean)
                elif section == 'outputs' and line_clean:
                    if line_clean not in metadata.outputs:
                        metadata.outputs.append(line_clean)
                elif section == 'dependencies' and line_clean:
                    if line_clean not in metadata.dependencies:
                        metadata.dependencies.append(line_clean)
                elif section == 'category' and line_clean:
                    if not metadata.category:
                        metadata.category = line_clean
                elif section == 'interval' and line_clean:
                    try:
                        metadata.interval_minutes = int(line_clean.split()[0])
                    except:
                        pass

    def _auto_categorize(self, metadata: AgentMetadata):
        """Auto-assign category based on agent name if not already set"""
        if metadata.category:
            return  # Already has a category

        # Check naming patterns
        agent_short_name = metadata.name.replace('_agent', '')

        # Exact match in CATEGORY_MAP
        if agent_short_name in self.CATEGORY_MAP:
            metadata.category = self.CATEGORY_MAP[agent_short_name]
            return

        # Prefix matching (more specific first)
        for pattern, category in sorted(self.CATEGORY_MAP.items(), key=lambda x: -len(x[0])):
            if agent_short_name.startswith(pattern):
                metadata.category = category
                return

        # Default to Specialized
        metadata.category = 'Specialized'

    def _extract_list(self, node: ast.AST) -> List[str]:
        """Extract list from AST node"""
        items = []
        if isinstance(node, ast.List):
            for item in node.elts:
                if isinstance(item, ast.Constant):
                    items.append(item.value)
        return items

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract imported modules"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or '')
        return [i for i in imports if i]

    def validate_agent(self, metadata: AgentMetadata) -> Tuple[bool, List[str]]:
        """Validate discovered agent metadata"""
        errors = []

        if not metadata.name:
            errors.append("Missing agent name")
        # class_name can be None for script-only agents
        # Category is auto-assigned so we don't require it
        # Description is often just first line of docstring, which may be generic

        # Optional: inputs/outputs/dependencies can be empty

        return len(errors) == 0, errors


class AgentDiscoveryAgent(BaseAgent):
    """
    Meta-Agent: Discovers and registers all agents in the ecosystem.

    This agent scans the src/agents/ directory, extracts metadata from all
    agent files, and maintains the complete agent registry in the orchestration
    system.

    Category: Infrastructure

    Inputs:
        - none (autonomous scanner)

    Outputs:
        - agent_registry (updated agent metadata)
        - discovery_report (scan results and statistics)
        - validation_errors (any agents with issues)

    Dependencies:
        - none

    Execution:
        - Runs periodically or on-demand
        - Updates agent management system
        - Records learnings about agent ecosystem
        - Detects new/removed agents automatically
    """

    def __init__(self):
        super().__init__()
        self.name = "discovery_agent"
        self.discovery_engine = DiscoveryEngine()
        self.last_scan_time = None
        self.registry_file = Path(project_root) / "src" / "data" / "agent_registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Execute agent discovery and registration"""
        execution_id = f"discovery_{datetime.now().isoformat()}"

        try:
            start_time = datetime.now()

            # Discover all agents
            print("🔍 Scanning for agents...")
            discovered = self.discovery_engine.discover_all_agents()

            # Validate agents
            print(f"✓ Found {len(discovered)} agents, validating...")
            validation_results = self._validate_all_agents(discovered)

            # Build registry
            print("📝 Building registry...")
            registry = self._build_registry(discovered)

            # Save registry
            print("💾 Saving registry...")
            self._save_registry(registry)

            # Generate report
            report = self._generate_report(discovered, validation_results, registry)

            # Record learnings about ecosystem
            duration = (datetime.now() - start_time).total_seconds()
            self._record_ecosystem_learning(discovered, report, duration)

            # Store output (if available)
            if HAS_AGENT_MANAGER:
                output_manager.store_output(
                    agent_name=self.name,
                    execution_id=execution_id,
                    status=AgentStatus.SUCCESS,
                    output_data={
                        'agents_discovered': len(discovered),
                        'agents_valid': len([r for r in validation_results.values() if r[0]]),
                        'agents_with_issues': len([r for r in validation_results.values() if not r[0]]),
                        'registry_file': str(self.registry_file),
                        'report': report
                    },
                    duration_seconds=duration
                )

            # Share findings with ecosystem
            self._share_discovery_insights(discovered, report)

            print(f"✅ Discovery complete: {len(discovered)} agents found, {duration:.2f}s")
            self.last_scan_time = datetime.now()

            return {
                'success': True,
                'agents_discovered': len(discovered),
                'agents': discovered,
                'registry': registry,
                'report': report
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Discovery failed: {error_msg}")

            if HAS_AGENT_MANAGER:
                output_manager.store_output(
                    agent_name=self.name,
                    execution_id=execution_id,
                    status=AgentStatus.FAILED,
                    output_data={'error': error_msg},
                    errors=[error_msg]
                )

            return {
                'success': False,
                'error': error_msg
            }

    def _validate_all_agents(self, discovered: Dict[str, AgentMetadata]) -> Dict[str, Tuple[bool, List[str]]]:
        """Validate all discovered agents"""
        results = {}
        for name, metadata in discovered.items():
            is_valid, errors = self.discovery_engine.validate_agent(metadata)
            results[name] = (is_valid, errors)
            if is_valid:
                print(f"  ✓ {name}")
            else:
                print(f"  ⚠️  {name}: {', '.join(errors)}")
        return results

    def _build_registry(self, discovered: Dict[str, AgentMetadata]) -> Dict[str, Dict[str, Any]]:
        """Build complete agent registry"""
        registry = {}
        for name, metadata in discovered.items():
            registry[name] = metadata.to_dict()
        return registry

    def _save_registry(self, registry: Dict[str, Dict[str, Any]]):
        """Save registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'agents': registry,
                'total_agents': len(registry)
            }, f, indent=2)

    def _generate_report(self, discovered: Dict[str, AgentMetadata],
                        validation: Dict[str, Tuple[bool, List[str]]],
                        registry: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate discovery report"""
        # Categorize agents
        categories = {}
        for name, meta in discovered.items():
            cat = meta.category or 'Uncategorized'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)

        # Count validity
        valid_count = len([r for r in validation.values() if r[0]])
        invalid_count = len([r for r in validation.values() if not r[0]])

        return {
            'total_agents': len(discovered),
            'valid_agents': valid_count,
            'agents_with_issues': invalid_count,
            'categories': categories,
            'agents_by_category': {cat: len(agents) for cat, agents in categories.items()},
            'timestamp': datetime.now().isoformat()
        }

    def _record_ecosystem_learning(self, discovered: Dict[str, AgentMetadata],
                                   report: Dict[str, Any], duration: float):
        """Record learnings about the agent ecosystem"""
        try:
            learning_manager.record_learning(
                agent_name=self.name,
                category='insight',
                content={
                    'discovery_complete': True,
                    'agents_discovered': len(discovered),
                    'agent_categories': len(report['categories']),
                    'discovery_duration_seconds': duration,
                    'categories': report['agents_by_category'],
                    'timestamp': datetime.now().isoformat()
                },
                confidence=0.98,
                applicable_to=['orchestrator', 'health_check_agent', 'alert_management_agent']
            )
        except Exception as e:
            logger.warning(f"Could not record learning: {e}")

    def _share_discovery_insights(self, discovered: Dict[str, AgentMetadata],
                                 report: Dict[str, Any]):
        """Share discovery insights through shared memory"""
        try:
            memory_manager.store_memory(
                agent_name=self.name,
                category='observation',
                content={
                    'agent_ecosystem_snapshot': {
                        'total_agents': len(discovered),
                        'categories': report['agents_by_category'],
                        'scan_time': datetime.now().isoformat()
                    }
                },
                accessible_by=['orchestrator', 'health_check_agent']
            )
        except Exception as e:
            logger.warning(f"Could not share memory: {e}")

    def get_signals(self, token: str = None):
        """Not used for this meta-agent"""
        return self.run()


def main():
    """Run discovery agent standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)

    agent = AgentDiscoveryAgent()
    result = agent.run()

    # Pretty print results
    print("\n" + "="*80)
    print("📊 DISCOVERY REPORT")
    print("="*80)

    if result['success']:
        report = result['report']
        print(f"\n✅ Total Agents Discovered: {report['total_agents']}")
        print(f"✅ Valid Agents: {report['valid_agents']}")
        if report['agents_with_issues'] > 0:
            print(f"⚠️  Agents with Issues: {report['agents_with_issues']}")

        print(f"\n📁 Agents by Category:")
        for cat, count in sorted(report['agents_by_category'].items()):
            print(f"  • {cat}: {count}")

        print(f"\nRegistry saved to: {agent.registry_file}")
    else:
        print(f"\n❌ Discovery Failed: {result['error']}")

    print("="*80)


if __name__ == '__main__':
    main()
