"""
Natural Language Chat Interface for Agentic Standards Protocol

Interactive conversational CLI for invoking autonomous agents using natural language.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.superstandard.nlp.intent_parser import IntentParser, IntentType
from src.superstandard.nlp.parameter_extractor import ParameterExtractor
from src.superstandard.nlp.agent_mapper import AgentMapper
from src.superstandard.nlp.response_generator import ResponseGenerator
from src.superstandard.services.factory import ServiceFactory
from src.superstandard.monitoring.dashboard import get_dashboard

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress agent logs for cleaner chat
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class NaturalLanguageChatInterface:
    """
    Natural Language Chat Interface for Autonomous Agents.

    Allows users to interact with the agent platform using plain English.
    """

    def __init__(self, use_llm: bool = False):
        """
        Initialize chat interface.

        Args:
            use_llm: Whether to use LLM for intent parsing (requires OpenAI API key)
        """
        self.intent_parser = IntentParser(use_llm=use_llm)
        self.parameter_extractor = ParameterExtractor()
        self.agent_mapper = AgentMapper()
        self.response_generator = ResponseGenerator()

        self.service_factory = ServiceFactory()
        self.dashboard = get_dashboard()

        # Register handlers
        self._register_handlers()

        # Session state
        self.session_start = datetime.utcnow()
        self.query_count = 0

    def _register_handlers(self):
        """Register execution handlers for each intent type."""
        self.agent_mapper.register_handler(
            IntentType.DISCOVER_OPPORTUNITIES,
            self._handle_discover_opportunities
        )
        self.agent_mapper.register_handler(
            IntentType.ANALYZE_COMPETITORS,
            self._handle_analyze_competitors
        )
        self.agent_mapper.register_handler(
            IntentType.GET_ECONOMIC_TRENDS,
            self._handle_get_economic_trends
        )
        self.agent_mapper.register_handler(
            IntentType.ANALYZE_DEMOGRAPHICS,
            self._handle_analyze_demographics
        )
        self.agent_mapper.register_handler(
            IntentType.CONDUCT_RESEARCH,
            self._handle_conduct_research
        )
        self.agent_mapper.register_handler(
            IntentType.GET_SYSTEM_STATUS,
            self._handle_get_system_status
        )
        self.agent_mapper.register_handler(
            IntentType.HELP,
            self._handle_help
        )

    async def _handle_discover_opportunities(self, parameters: dict) -> list:
        """Handle opportunity discovery requests."""
        from src.superstandard.orchestration.opportunity_discovery import (
            OpportunityDiscoveryOrchestrator
        )

        orchestrator = OpportunityDiscoveryOrchestrator(
            service_factory=self.service_factory,
            dashboard_state=self.dashboard
        )

        opportunities = await orchestrator.discover_opportunities(
            industry=parameters.get("industry", "technology"),
            geography=parameters.get("geography", "United States"),
            min_confidence=parameters.get("min_confidence", 0.75)
        )

        return opportunities

    async def _handle_analyze_competitors(self, parameters: dict) -> dict:
        """Handle competitor analysis requests."""
        from src.superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_1_identify_competitors_PRODUCTION import (
            IdentifyCompetitorsAgentProduction
        )

        agent = IdentifyCompetitorsAgentProduction(
            service_factory=self.service_factory
        )

        result = await agent.execute({
            "domain": parameters.get("domain"),
            "limit": parameters.get("limit", 10)
        })

        return result

    async def _handle_get_economic_trends(self, parameters: dict) -> dict:
        """Handle economic trends requests."""
        from src.superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_2_identify_economic_trends_PRODUCTION import (
            IdentifyEconomicTrendsAgentProduction
        )

        agent = IdentifyEconomicTrendsAgentProduction(
            service_factory=self.service_factory
        )

        result = await agent.execute({
            "geography": parameters.get("geography", "United States"),
            "indicators": parameters.get("indicators", ["gdp", "unemployment", "inflation"]),
            "years": parameters.get("years", 5)
        })

        return result

    async def _handle_analyze_demographics(self, parameters: dict) -> dict:
        """Handle demographics analysis requests."""
        from src.superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_1_assess_external.a_1_1_1_5_analyze_demographics_PRODUCTION import (
            AnalyzeDemographicsAgentProduction
        )

        agent = AnalyzeDemographicsAgentProduction(
            service_factory=self.service_factory
        )

        result = await agent.execute({
            "geography": parameters.get("geography", "United States"),
            "year": parameters.get("year", 2020)
        })

        return result

    async def _handle_conduct_research(self, parameters: dict) -> dict:
        """Handle market research requests."""
        from src.superstandard.agents.pcf.category_01_vision_strategy.pg_1_1_define_vision.p_1_1_2_understand_market.a_1_1_2_1_conduct_research_PRODUCTION import (
            ConductResearchAgentProduction
        )

        agent = ConductResearchAgentProduction(
            service_factory=self.service_factory
        )

        result = await agent.execute({
            "survey_id": parameters.get("survey_id"),
            "industry": parameters.get("industry", "")
        })

        return result

    async def _handle_get_system_status(self, parameters: dict) -> dict:
        """Handle system status requests."""
        return self.dashboard.get_dashboard_stats()

    async def _handle_help(self, parameters: dict) -> str:
        """Handle help requests."""
        return self.agent_mapper.get_help_text()

    async def process_query(self, query: str) -> str:
        """
        Process a natural language query.

        Args:
            query: User's natural language query

        Returns:
            Natural language response
        """
        self.query_count += 1
        start_time = time.time()

        try:
            # Step 1: Parse intent
            print("🤔 Understanding your request...")
            intent = await self.intent_parser.parse(query)

            if intent.intent_type == IntentType.UNKNOWN:
                return (
                    "I'm not sure what you're asking for. Try one of these:\n"
                    "• Find business opportunities in [industry]\n"
                    "• Analyze competitors for [domain]\n"
                    "• Show economic trends\n"
                    "• Analyze demographics for [location]\n"
                    "• Type 'help' for more options"
                )

            print(f"✅ Intent: {intent.intent_type.value.replace('_', ' ').title()}")
            if intent.confidence < 0.7:
                print(f"⚠️  Confidence: {intent.confidence*100:.0f}% (low confidence, best guess)")

            # Step 2: Extract and validate parameters
            try:
                parameters = self.parameter_extractor.extract_and_validate(
                    intent.intent_type,
                    intent.parameters
                )
            except ValueError as e:
                return f"Parameter error: {e}\n\n{self.parameter_extractor.get_parameter_help(intent.intent_type)}"

            # Show parameters
            if parameters:
                print(f"📋 Parameters: {', '.join(f'{k}={v}' for k, v in parameters.items())}")

            # Step 3: Get capability
            capability = self.agent_mapper.get_capability(intent.intent_type)
            if capability:
                print(f"🤖 Agent: {capability.agent_name}")
                if capability.requires_dashboard:
                    dashboard_path = Path(__file__).parent.parent.parent.parent / "dashboard.html"
                    print(f"📊 Dashboard: file://{dashboard_path.absolute()}")

            # Step 4: Execute
            print(f"⚙️  Executing...")
            print()

            result = await self.agent_mapper.execute(intent.intent_type, parameters)

            # Step 5: Generate response
            execution_time = time.time() - start_time
            response = self.response_generator.generate(
                intent.intent_type,
                result,
                parameters,
                execution_time
            )

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            execution_time = time.time() - start_time
            return self.response_generator.format_error(e, intent.intent_type)

    def print_welcome(self):
        """Print welcome message."""
        print()
        print("=" * 80)
        print("🤖 Agentic Standards Protocol - Natural Language Interface")
        print("=" * 80)
        print()
        print("Talk to autonomous agents in plain English!")
        print()
        print("Examples:")
        print("  • Find me business opportunities in healthcare")
        print("  • Analyze competitors for stripe.com")
        print("  • What are the economic trends?")
        print("  • Show demographics for California")
        print("  • help")
        print()
        print("Type 'exit' or 'quit' to exit")
        print("=" * 80)
        print()

    async def run_interactive(self):
        """Run interactive chat loop."""
        self.print_welcome()

        while True:
            try:
                # Get user input
                query = input("You: ").strip()

                if not query:
                    continue

                # Check for exit
                if query.lower() in ['exit', 'quit', 'bye', 'q']:
                    print()
                    print("👋 Thanks for using the Agentic Standards Protocol!")
                    print(f"   Session stats: {self.query_count} queries processed")
                    print()
                    break

                # Process query
                print()
                response = await self.process_query(query)

                # Print response
                print()
                print("Agent:")
                print(response)
                print()
                print("-" * 80)
                print()

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Type 'exit' to quit or continue asking questions.")
                print()
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                logger.error(f"Unexpected error: {e}", exc_info=True)


async def main():
    """Main entry point for chat interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Natural Language Chat Interface for Agentic Standards Protocol"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM for intent parsing (requires OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query mode (non-interactive)"
    )

    args = parser.parse_args()

    chat = NaturalLanguageChatInterface(use_llm=args.llm)

    if args.query:
        # Single query mode
        response = await chat.process_query(args.query)
        print()
        print(response)
        print()
    else:
        # Interactive mode
        await chat.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
