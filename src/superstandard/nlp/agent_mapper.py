"""
Agent Mapper - Maps Intents to Agent Capabilities

Routes user intents to the appropriate agents or orchestrators for execution.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, Awaitable
from .intent_parser import IntentType


@dataclass
class AgentCapability:
    """Represents an agent's capability to handle an intent."""

    intent_type: IntentType
    agent_name: str
    agent_class: str
    orchestrator: Optional[str] = None
    description: str = ""
    estimated_duration_seconds: float = 10.0
    requires_dashboard: bool = True


class AgentMapper:
    """
    Maps user intents to agent capabilities and execution handlers.

    This is the critical bridge between natural language understanding
    and autonomous agent execution.
    """

    def __init__(self):
        """Initialize agent mapper."""
        self.logger = logging.getLogger(__name__)

        # Build capability map
        self.capabilities = self._build_capabilities()

        # Execution handlers
        self.handlers: Dict[IntentType, Callable[[Dict[str, Any]], Awaitable[Any]]] = {}

    def _build_capabilities(self) -> Dict[IntentType, AgentCapability]:
        """Build agent capability mappings."""
        return {
            IntentType.DISCOVER_OPPORTUNITIES: AgentCapability(
                intent_type=IntentType.DISCOVER_OPPORTUNITIES,
                agent_name="OpportunityDiscoveryOrchestrator",
                agent_class="superstandard.orchestration.opportunity_discovery.OpportunityDiscoveryOrchestrator",
                orchestrator="OpportunityDiscoveryOrchestrator",
                description="Discovers business opportunities using 4 specialized agents",
                estimated_duration_seconds=30.0,
                requires_dashboard=True
            ),
            IntentType.ANALYZE_COMPETITORS: AgentCapability(
                intent_type=IntentType.ANALYZE_COMPETITORS,
                agent_name="IdentifyCompetitorsAgent",
                agent_class="superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_1_identify_competitors_PRODUCTION.IdentifyCompetitorsAgentProduction",
                description="Analyzes competitive landscape using SimilarWeb data",
                estimated_duration_seconds=10.0,
                requires_dashboard=True
            ),
            IntentType.GET_ECONOMIC_TRENDS: AgentCapability(
                intent_type=IntentType.GET_ECONOMIC_TRENDS,
                agent_name="IdentifyEconomicTrendsAgent",
                agent_class="superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_2_identify_economic_trends_PRODUCTION.IdentifyEconomicTrendsAgentProduction",
                description="Analyzes economic trends using FRED data",
                estimated_duration_seconds=10.0,
                requires_dashboard=True
            ),
            IntentType.ANALYZE_DEMOGRAPHICS: AgentCapability(
                intent_type=IntentType.ANALYZE_DEMOGRAPHICS,
                agent_name="AnalyzeDemographicsAgent",
                agent_class="superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_5_analyze_demographics_PRODUCTION.AnalyzeDemographicsAgentProduction",
                description="Analyzes demographics using US Census data",
                estimated_duration_seconds=10.0,
                requires_dashboard=True
            ),
            IntentType.CONDUCT_RESEARCH: AgentCapability(
                intent_type=IntentType.CONDUCT_RESEARCH,
                agent_name="ConductResearchAgent",
                agent_class="superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_2_understand_market.a_1_1_2_1_conduct_research_PRODUCTION.ConductResearchAgentProduction",
                description="Conducts market research using Qualtrics data",
                estimated_duration_seconds=15.0,
                requires_dashboard=True
            ),
            IntentType.GET_SYSTEM_STATUS: AgentCapability(
                intent_type=IntentType.GET_SYSTEM_STATUS,
                agent_name="SystemStatusHandler",
                agent_class="builtin",
                description="Returns system status and dashboard statistics",
                estimated_duration_seconds=0.1,
                requires_dashboard=False
            ),
            IntentType.HELP: AgentCapability(
                intent_type=IntentType.HELP,
                agent_name="HelpHandler",
                agent_class="builtin",
                description="Provides help information",
                estimated_duration_seconds=0.1,
                requires_dashboard=False
            )
        }

    def get_capability(self, intent_type: IntentType) -> Optional[AgentCapability]:
        """Get agent capability for an intent type."""
        return self.capabilities.get(intent_type)

    def can_handle(self, intent_type: IntentType) -> bool:
        """Check if an intent can be handled."""
        return intent_type in self.capabilities

    def register_handler(
        self,
        intent_type: IntentType,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    ):
        """
        Register an execution handler for an intent type.

        Args:
            intent_type: Intent type to handle
            handler: Async function that executes the intent
        """
        self.handlers[intent_type] = handler
        self.logger.info(f"Registered handler for {intent_type.value}")

    async def execute(
        self,
        intent_type: IntentType,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute an intent with given parameters.

        Args:
            intent_type: Intent to execute
            parameters: Validated parameters

        Returns:
            Execution result

        Raises:
            ValueError: If intent cannot be handled or no handler registered
        """
        if not self.can_handle(intent_type):
            raise ValueError(f"Cannot handle intent: {intent_type.value}")

        handler = self.handlers.get(intent_type)
        if handler is None:
            raise ValueError(f"No handler registered for intent: {intent_type.value}")

        capability = self.get_capability(intent_type)
        self.logger.info(
            f"Executing {capability.agent_name} for {intent_type.value}"
        )

        result = await handler(parameters)
        return result

    def get_all_capabilities(self) -> Dict[IntentType, AgentCapability]:
        """Get all registered capabilities."""
        return self.capabilities.copy()

    def get_help_text(self) -> str:
        """Get human-readable help text for all capabilities."""
        lines = ["Available Commands:\n"]

        for intent_type, capability in self.capabilities.items():
            if intent_type in [IntentType.HELP, IntentType.UNKNOWN]:
                continue

            lines.append(f"• {intent_type.value.replace('_', ' ').title()}")
            lines.append(f"  Agent: {capability.agent_name}")
            lines.append(f"  {capability.description}")
            if capability.orchestrator:
                lines.append(f"  Type: Orchestrator (multi-agent)")
            lines.append(f"  Est. Duration: ~{capability.estimated_duration_seconds}s")
            lines.append("")

        return "\n".join(lines)

    def get_capability_summary(self) -> Dict[str, Any]:
        """Get summary of all capabilities."""
        return {
            "total_capabilities": len(self.capabilities),
            "orchestrators": len([c for c in self.capabilities.values() if c.orchestrator]),
            "single_agents": len([c for c in self.capabilities.values() if not c.orchestrator and c.agent_class != "builtin"]),
            "builtins": len([c for c in self.capabilities.values() if c.agent_class == "builtin"]),
            "capabilities": {
                intent.value: {
                    "agent_name": cap.agent_name,
                    "description": cap.description,
                    "is_orchestrator": cap.orchestrator is not None,
                    "estimated_duration_seconds": cap.estimated_duration_seconds
                }
                for intent, cap in self.capabilities.items()
                if intent not in [IntentType.UNKNOWN]
            }
        }
