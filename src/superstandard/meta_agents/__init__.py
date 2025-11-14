"""
Meta-Agents - Agents that Create and Orchestrate Other Agents

Meta-agents represent the pinnacle of autonomous AI:
- Create specialized agents on-demand
- Orchestrate multi-agent workflows
- Enable self-improving systems
- Implement autonomous coordination patterns
"""

from .factory import FactoryMetaAgent
from .coordinator import CoordinatorMetaAgent

__all__ = [
    'FactoryMetaAgent',
    'CoordinatorMetaAgent'
]
