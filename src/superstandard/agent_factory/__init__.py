"""
Agent Factory - Automated Agent Generation System

Generate production-ready agents from YAML/JSON specifications at scale!

This enables us to scale from 10s to 1000s of agents effortlessly.

Usage:
    from src.superstandard.agent_factory import AgentGenerator, AgentRegistry

    # Generate single agent
    generator = AgentGenerator()
    generator.generate_from_spec("specs/my_agent.yaml")

    # Generate entire APQC category
    generator.generate_category("1.0")  # Vision & Strategy

    # Discover and search agents
    registry = AgentRegistry()
    registry.discover_agents()
    agents = registry.search(capability="competitive_analysis")
"""

from .generator import AgentGenerator, AgentSpec
from .registry import AgentRegistry, RegisteredAgent, get_registry

__all__ = ['AgentGenerator', 'AgentSpec', 'AgentRegistry', 'RegisteredAgent', 'get_registry']
