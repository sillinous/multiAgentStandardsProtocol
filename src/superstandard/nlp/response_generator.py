"""
Response Generator - Convert Execution Results to Natural Language

Formats agent execution results into conversational natural language responses.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from .intent_parser import IntentType


class ResponseGenerator:
    """
    Generates natural language responses from agent execution results.

    Transforms structured data into human-friendly conversational responses.
    """

    def __init__(self):
        """Initialize response generator."""
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        intent_type: IntentType,
        result: Any,
        parameters: Dict[str, Any],
        execution_time_seconds: float = 0.0
    ) -> str:
        """
        Generate natural language response from execution result.

        Args:
            intent_type: Type of intent that was executed
            result: Execution result from agent
            parameters: Parameters used for execution
            execution_time_seconds: Time taken to execute

        Returns:
            Natural language response string
        """
        # Route to specific generator based on intent
        generators = {
            IntentType.DISCOVER_OPPORTUNITIES: self._generate_opportunities_response,
            IntentType.ANALYZE_COMPETITORS: self._generate_competitors_response,
            IntentType.GET_ECONOMIC_TRENDS: self._generate_economic_response,
            IntentType.ANALYZE_DEMOGRAPHICS: self._generate_demographics_response,
            IntentType.CONDUCT_RESEARCH: self._generate_research_response,
            IntentType.GET_SYSTEM_STATUS: self._generate_status_response,
            IntentType.HELP: self._generate_help_response,
        }

        generator = generators.get(intent_type, self._generate_generic_response)
        return generator(result, parameters, execution_time_seconds)

    def _generate_opportunities_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for opportunity discovery."""
        if not result or not isinstance(result, list):
            return "No opportunities found matching your criteria."

        opportunities = result
        industry = parameters.get("industry", "the target industry")
        geography = parameters.get("geography", "the target region")

        lines = []
        lines.append(f"🎯 Found {len(opportunities)} business opportunity{'ies' if len(opportunities) != 1 else 'y'} in {industry} ({geography})")
        lines.append(f"⏱️  Analysis completed in {execution_time:.1f}s")
        lines.append("")

        # Show top 5 opportunities
        for i, opp in enumerate(opportunities[:5], 1):
            confidence = getattr(opp, 'confidence_score', 0) * 100
            title = getattr(opp, 'title', 'Untitled')
            category = getattr(opp, 'category', 'General')
            revenue = getattr(opp, 'revenue_potential', 'N/A')
            description = getattr(opp, 'description', '')

            lines.append(f"{i}. {title}")
            lines.append(f"   💡 Category: {category}")
            lines.append(f"   📊 Confidence: {confidence:.1f}%")
            lines.append(f"   💰 Revenue Potential: {revenue}")

            if description:
                # Truncate long descriptions
                desc_preview = description[:150] + "..." if len(description) > 150 else description
                lines.append(f"   📝 {desc_preview}")
            lines.append("")

        if len(opportunities) > 5:
            lines.append(f"... and {len(opportunities) - 5} more opportunities")
            lines.append("")

        # Calculate average confidence
        avg_confidence = sum(getattr(opp, 'confidence_score', 0) for opp in opportunities) / len(opportunities) * 100
        lines.append(f"📈 Average Confidence: {avg_confidence:.1f}%")

        return "\n".join(lines)

    def _generate_competitors_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for competitor analysis."""
        domain = parameters.get("domain", "the target domain")

        if not result or 'competitors_list' not in result:
            return f"Could not analyze competitors for {domain}."

        competitors = result.get('competitors_list', [])
        metadata = result.get('metadata', {})
        data_source = metadata.get('data_source', 'Unknown')

        lines = []
        lines.append(f"🔍 Competitive Analysis for {domain}")
        lines.append(f"📊 Data Source: {data_source}")
        lines.append(f"⏱️  Analyzed in {execution_time:.1f}s")
        lines.append("")

        if competitors:
            lines.append(f"Found {len(competitors)} competitors:")
            lines.append("")

            for i, comp in enumerate(competitors[:10], 1):
                name = comp.get('name', comp.get('domain', 'Unknown'))
                similarity = comp.get('similarity_score', 0) * 100

                lines.append(f"{i}. {name}")
                lines.append(f"   Similarity: {similarity:.1f}%")

                if 'traffic_rank' in comp:
                    lines.append(f"   Traffic Rank: {comp['traffic_rank']:,}")
                if 'category' in comp:
                    lines.append(f"   Category: {comp['category']}")

                lines.append("")

        # Quality score
        if 'data_quality' in metadata:
            quality = metadata['data_quality'].get('overall_score', 0)
            lines.append(f"✅ Data Quality: {quality:.1f}%")

        return "\n".join(lines)

    def _generate_economic_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for economic trends."""
        geography = parameters.get("geography", "United States")

        if not result or 'indicators' not in result:
            return f"Could not fetch economic data for {geography}."

        indicators = result.get('indicators', {})
        metadata = result.get('metadata', {})

        lines = []
        lines.append(f"📈 Economic Trends for {geography}")
        lines.append(f"⏱️  Retrieved in {execution_time:.1f}s")
        lines.append("")

        if indicators:
            lines.append("Key Indicators:")
            lines.append("")

            for indicator_name, data in indicators.items():
                name = indicator_name.replace('_', ' ').title()
                if isinstance(data, dict):
                    current = data.get('current_value', 'N/A')
                    trend = data.get('trend', 'N/A')
                    lines.append(f"• {name}: {current}")
                    if trend and trend != 'N/A':
                        lines.append(f"  Trend: {trend}")
                else:
                    lines.append(f"• {name}: {data}")
                lines.append("")

        # Analysis summary
        if 'analysis_summary' in result:
            lines.append("Analysis:")
            lines.append(result['analysis_summary'])

        return "\n".join(lines)

    def _generate_demographics_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for demographics analysis."""
        geography = parameters.get("geography", "United States")

        if not result or 'demographics_summary' not in result:
            return f"Could not fetch demographics data for {geography}."

        summary = result.get('demographics_summary', {})

        lines = []
        lines.append(f"👥 Demographics Analysis for {geography}")
        lines.append(f"⏱️  Retrieved in {execution_time:.1f}s")
        lines.append("")

        # Population
        if 'population' in summary:
            pop = summary['population']
            if isinstance(pop, dict):
                total = pop.get('total', 'N/A')
                lines.append(f"Population: {total:,}" if isinstance(total, (int, float)) else f"Population: {total}")
            else:
                lines.append(f"Population: {pop:,}" if isinstance(pop, (int, float)) else f"Population: {pop}")
            lines.append("")

        # Age distribution
        if 'age_distribution' in summary:
            lines.append("Age Distribution:")
            age_dist = summary['age_distribution']
            if isinstance(age_dist, dict):
                for age_group, percentage in age_dist.items():
                    lines.append(f"  • {age_group}: {percentage}%")
            lines.append("")

        # Income
        if 'median_income' in summary:
            income = summary['median_income']
            lines.append(f"Median Income: ${income:,}" if isinstance(income, (int, float)) else f"Median Income: {income}")
            lines.append("")

        # Key insights
        if 'key_insights' in result:
            lines.append("Key Insights:")
            for insight in result['key_insights']:
                lines.append(f"  • {insight}")

        return "\n".join(lines)

    def _generate_research_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for market research."""
        survey_id = parameters.get("survey_id", "the survey")

        if not result or 'research_findings' not in result:
            return f"Could not retrieve research data from {survey_id}."

        findings = result.get('research_findings', {})

        lines = []
        lines.append(f"📊 Market Research Results")
        lines.append(f"⏱️  Analyzed in {execution_time:.1f}s")
        lines.append("")

        # Response count
        if 'total_responses' in findings:
            lines.append(f"Total Responses: {findings['total_responses']}")
            lines.append("")

        # Key findings
        if 'key_findings' in findings:
            lines.append("Key Findings:")
            for finding in findings['key_findings']:
                lines.append(f"  • {finding}")
            lines.append("")

        # Sentiment
        if 'sentiment_analysis' in findings:
            sentiment = findings['sentiment_analysis']
            lines.append("Sentiment Analysis:")
            for category, score in sentiment.items():
                lines.append(f"  • {category.title()}: {score}%")
            lines.append("")

        return "\n".join(lines)

    def _generate_status_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate response for system status."""
        if not result:
            return "System status unavailable."

        lines = []
        lines.append("🤖 Agentic Standards Protocol - System Status")
        lines.append("")

        if 'metrics' in result:
            metrics = result['metrics']
            lines.append("Metrics:")
            lines.append(f"  • Total Events: {metrics.get('total_events', 0)}")
            lines.append(f"  • Agents Executed: {metrics.get('total_agents_executed', 0)}")
            lines.append(f"  • Opportunities Discovered: {metrics.get('total_opportunities_discovered', 0)}")
            lines.append(f"  • Average Quality Score: {metrics.get('avg_quality_score', 0):.1f}%")
            lines.append("")

        if 'active_agents' in result:
            lines.append(f"Active Agents: {result['active_agents']}")

        if 'system_uptime_seconds' in result:
            uptime = result['system_uptime_seconds']
            if uptime < 60:
                uptime_str = f"{uptime:.0f}s"
            elif uptime < 3600:
                uptime_str = f"{uptime/60:.0f}m"
            else:
                uptime_str = f"{uptime/3600:.1f}h"
            lines.append(f"System Uptime: {uptime_str}")

        return "\n".join(lines)

    def _generate_help_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate help response."""
        return result if isinstance(result, str) else "Help information unavailable."

    def _generate_generic_response(
        self,
        result: Any,
        parameters: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Generate generic response for unknown intent types."""
        return f"Task completed in {execution_time:.1f}s.\n\nResult: {result}"

    def format_error(self, error: Exception, intent_type: IntentType) -> str:
        """Format an error into a user-friendly message."""
        error_type = type(error).__name__
        error_msg = str(error)

        lines = []
        lines.append(f"❌ Error executing {intent_type.value.replace('_', ' ')}")
        lines.append("")
        lines.append(f"Error Type: {error_type}")
        lines.append(f"Message: {error_msg}")
        lines.append("")
        lines.append("Tip: Try rephrasing your request or check the parameters.")

        return "\n".join(lines)
