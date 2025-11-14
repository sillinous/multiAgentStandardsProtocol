"""
Natural Language Processing for Agent Invocation

This package provides LLM-powered natural language understanding for
invoking autonomous agents through conversational interfaces.

Features:
- Intent classification
- Parameter extraction
- Agent capability mapping
- Natural language response generation
"""

from .intent_parser import IntentParser, Intent
from .parameter_extractor import ParameterExtractor
from .agent_mapper import AgentMapper, AgentCapability
from .response_generator import ResponseGenerator

__all__ = [
    'IntentParser',
    'Intent',
    'ParameterExtractor',
    'AgentMapper',
    'AgentCapability',
    'ResponseGenerator'
]
