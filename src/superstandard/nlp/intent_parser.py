"""
Intent Parser - LLM-Powered Natural Language Understanding

Classifies user intents and extracts key information from natural language queries.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import os


class IntentType(Enum):
    """Supported intent types for agent invocation."""

    DISCOVER_OPPORTUNITIES = "discover_opportunities"
    ANALYZE_COMPETITORS = "analyze_competitors"
    GET_ECONOMIC_TRENDS = "get_economic_trends"
    ANALYZE_DEMOGRAPHICS = "analyze_demographics"
    CONDUCT_RESEARCH = "conduct_research"
    GET_SYSTEM_STATUS = "get_system_status"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a parsed user intent."""

    intent_type: IntentType
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "parameters": self.parameters,
            "raw_query": self.raw_query,
            "reasoning": self.reasoning
        }


class IntentParser:
    """
    LLM-Powered Intent Parser with Pattern Matching Fallback.

    Analyzes natural language queries to determine user intent and extract
    relevant parameters for agent invocation.

    Supports two modes:
    1. LLM Mode - Uses OpenAI API for sophisticated understanding (requires API key)
    2. Pattern Mode - Uses regex patterns for basic intent classification (fallback)
    """

    def __init__(self, use_llm: bool = True, api_key: Optional[str] = None):
        """
        Initialize intent parser.

        Args:
            use_llm: Whether to use LLM for parsing (requires OpenAI API key)
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.logger = logging.getLogger(__name__)
        self.use_llm = use_llm

        # Try to initialize LLM client
        self.llm_available = False
        if use_llm:
            try:
                import openai
                self.openai = openai
                self.api_key = api_key or os.getenv("OPENAI_API_KEY")
                if self.api_key:
                    self.openai.api_key = self.api_key
                    self.llm_available = True
                    self.logger.info("✅ LLM mode enabled (OpenAI)")
                else:
                    self.logger.warning("⚠️  No OpenAI API key found, falling back to pattern matching")
            except ImportError:
                self.logger.warning("⚠️  OpenAI library not installed, falling back to pattern matching")

        if not self.llm_available:
            self.logger.info("📋 Using pattern matching mode for intent parsing")

        # Pattern matching rules (fallback)
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[IntentType, List[str]]:
        """Build regex patterns for intent matching."""
        return {
            IntentType.DISCOVER_OPPORTUNITIES: [
                r"find.*opportunit",
                r"discover.*opportunit",
                r"business.*opportunit",
                r"what.*opportunit",
                r"show.*opportunit",
                r"identify.*opportunit",
            ],
            IntentType.ANALYZE_COMPETITORS: [
                r"analy[sz]e.*compet",
                r"find.*compet",
                r"who.*compet",
                r"competitor.*analy",
                r"competitive.*landscape",
            ],
            IntentType.GET_ECONOMIC_TRENDS: [
                r"economic.*trend",
                r"economy",
                r"gdp",
                r"unemployment",
                r"inflation",
                r"interest.*rate",
                r"financial.*trend",
            ],
            IntentType.ANALYZE_DEMOGRAPHICS: [
                r"demographic",
                r"population",
                r"age.*distribution",
                r"income.*level",
                r"education.*level",
            ],
            IntentType.CONDUCT_RESEARCH: [
                r"research",
                r"survey",
                r"market.*research",
                r"customer.*insight",
            ],
            IntentType.GET_SYSTEM_STATUS: [
                r"status",
                r"health",
                r"system.*status",
                r"how.*doing",
                r"running.*agent",
            ],
            IntentType.HELP: [
                r"help",
                r"what.*can.*do",
                r"how.*use",
                r"command",
            ]
        }

    async def parse(self, query: str) -> Intent:
        """
        Parse natural language query to extract intent.

        Args:
            query: User's natural language query

        Returns:
            Parsed Intent object
        """
        query = query.strip()

        if self.llm_available:
            return await self._parse_with_llm(query)
        else:
            return self._parse_with_patterns(query)

    async def _parse_with_llm(self, query: str) -> Intent:
        """Parse using LLM (OpenAI GPT)."""
        try:
            prompt = self._build_llm_prompt(query)

            response = await self.openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an intent classifier for an autonomous agent system. Analyze user queries and return structured JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    raise

            return Intent(
                intent_type=IntentType(result.get("intent_type", "unknown")),
                confidence=result.get("confidence", 0.5),
                parameters=result.get("parameters", {}),
                raw_query=query,
                reasoning=result.get("reasoning", "")
            )

        except Exception as e:
            self.logger.warning(f"LLM parsing failed: {e}, falling back to patterns")
            return self._parse_with_patterns(query)

    def _parse_with_patterns(self, query: str) -> Intent:
        """Parse using regex pattern matching (fallback)."""
        query_lower = query.lower()

        # Try each pattern
        best_match = None
        best_score = 0

        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # Count keyword matches for scoring
                    score = len(re.findall(pattern, query_lower))
                    if score > best_score:
                        best_score = score
                        best_match = intent_type

        if best_match is None:
            best_match = IntentType.UNKNOWN
            confidence = 0.3
        else:
            confidence = min(0.7 + (best_score * 0.1), 0.95)

        # Extract basic parameters
        parameters = self._extract_parameters_from_patterns(query_lower, best_match)

        return Intent(
            intent_type=best_match,
            confidence=confidence,
            parameters=parameters,
            raw_query=query,
            reasoning=f"Pattern matched: {best_match.value}"
        )

    def _extract_parameters_from_patterns(
        self,
        query: str,
        intent_type: IntentType
    ) -> Dict[str, Any]:
        """Extract parameters using simple pattern matching."""
        params = {}

        # Industry extraction
        industries = [
            "technology", "tech", "healthcare", "health", "finance", "financial",
            "retail", "manufacturing", "education", "saas", "software"
        ]
        for industry in industries:
            if industry in query:
                params["industry"] = industry.replace("tech", "technology").replace("health", "healthcare")
                break

        # Geography extraction
        geographies = [
            "united states", "usa", "california", "new york", "texas", "florida",
            "europe", "asia", "north america", "global", "worldwide"
        ]
        for geo in geographies:
            if geo in query:
                params["geography"] = geo.title()
                break

        # Revenue extraction
        revenue_match = re.search(r'\$(\d+)([kmb])?', query)
        if revenue_match:
            amount = int(revenue_match.group(1))
            multiplier = revenue_match.group(2)
            if multiplier == 'k':
                amount *= 1000
            elif multiplier == 'm':
                amount *= 1000000
            elif multiplier == 'b':
                amount *= 1000000000
            params["min_revenue"] = amount

        # Confidence threshold
        confidence_match = re.search(r'(\d+)%?\s*confidence', query)
        if confidence_match:
            params["min_confidence"] = float(confidence_match.group(1)) / 100

        # Domain extraction (for competitor analysis)
        domain_match = re.search(r'([a-z0-9-]+\.[a-z]{2,})', query)
        if domain_match and intent_type == IntentType.ANALYZE_COMPETITORS:
            params["domain"] = domain_match.group(1)

        return params

    def _build_llm_prompt(self, query: str) -> str:
        """Build prompt for LLM intent classification."""
        return f"""Analyze this user query and extract the intent and parameters.

User Query: "{query}"

Available Intents:
- discover_opportunities: Find business opportunities
- analyze_competitors: Analyze competitive landscape
- get_economic_trends: Get economic data and trends
- analyze_demographics: Analyze demographic data
- conduct_research: Conduct market research
- get_system_status: Get system status
- help: Get help information
- unknown: Cannot determine intent

Extract Parameters (if applicable):
- industry: Industry sector (e.g., "technology", "healthcare")
- geography: Geographic region (e.g., "United States", "California")
- category: Opportunity category (e.g., "SaaS", "Product")
- min_confidence: Minimum confidence threshold (0.0-1.0)
- min_revenue: Minimum revenue threshold (number)
- domain: Domain name for competitor analysis
- survey_id: Survey ID for research

Return ONLY a JSON object with this structure:
{{
    "intent_type": "<intent>",
    "confidence": <0.0-1.0>,
    "parameters": {{...}},
    "reasoning": "<brief explanation>"
}}"""


# Synchronous wrapper for non-async contexts
class SyncIntentParser(IntentParser):
    """Synchronous version of IntentParser for non-async contexts."""

    def parse_sync(self, query: str) -> Intent:
        """Synchronous parse method."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.parse(query))
