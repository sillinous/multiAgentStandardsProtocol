"""
AI Service Layer for Agent Processing
======================================

Provides LLM integration for intelligent agent processing.
Supports multiple providers with automatic fallback.

Usage:
    from superstandard.services.ai_service import ai_service

    # Analyze text
    result = await ai_service.analyze(
        "Analyze this customer feedback for sentiment and key issues",
        data={"text": customer_feedback}
    )

    # Generate recommendations
    recommendations = await ai_service.generate_recommendations(
        context={"domain": "finance", "issue": "late payments"},
        constraints=["cost-effective", "quick implementation"]
    )

    # Make decisions
    decision = await ai_service.make_decision(
        options=["approve", "reject", "escalate"],
        context={"risk_score": 0.7, "amount": 50000}
    )

Providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Local (Ollama)
    - Mock (for testing/demo)
"""

import os
import json
import asyncio
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class AIConfig:
    """AI Service configuration"""
    provider: AIProvider = AIProvider.MOCK
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_count: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )


# =============================================================================
# Response Cache
# =============================================================================

class ResponseCache:
    """Simple in-memory cache for AI responses"""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple] = {}  # key -> (response, expiry)
        self.ttl = ttl_seconds

    def _make_key(self, prompt: str, context: Dict) -> str:
        """Generate cache key from prompt and context"""
        content = json.dumps({"prompt": prompt, "context": context}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, prompt: str, context: Dict) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        key = self._make_key(prompt, context)
        if key in self.cache:
            response, expiry = self.cache[key]
            if datetime.now() < expiry:
                logger.debug(f"Cache hit for key {key}")
                return response
            else:
                del self.cache[key]
        return None

    def set(self, prompt: str, context: Dict, response: Dict):
        """Cache a response"""
        key = self._make_key(prompt, context)
        expiry = datetime.now() + timedelta(seconds=self.ttl)
        self.cache[key] = (response, expiry)
        logger.debug(f"Cached response for key {key}")

    def clear(self):
        """Clear all cached responses"""
        self.cache.clear()


# =============================================================================
# Provider Implementations
# =============================================================================

class BaseAIProvider(ABC):
    """Base class for AI providers"""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion for a prompt"""
        pass

    @abstractmethod
    async def analyze(self, prompt: str, data: Dict) -> Dict:
        """Analyze data with a prompt"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class MockAIProvider(BaseAIProvider):
    """Mock provider for testing and demo purposes"""

    def __init__(self):
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    async def complete(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        await asyncio.sleep(0.1)  # Simulate latency

        # Generate contextual mock responses
        prompt_lower = prompt.lower()

        if "sentiment" in prompt_lower:
            return json.dumps({
                "sentiment": "positive",
                "confidence": 0.85,
                "key_phrases": ["good quality", "fast delivery", "recommend"]
            })
        elif "recommend" in prompt_lower:
            return json.dumps({
                "recommendations": [
                    {"action": "Optimize process flow", "priority": "high", "impact": "significant"},
                    {"action": "Enhance monitoring", "priority": "medium", "impact": "moderate"},
                    {"action": "Update documentation", "priority": "low", "impact": "minor"}
                ]
            })
        elif "decision" in prompt_lower or "approve" in prompt_lower:
            return json.dumps({
                "decision": "approve",
                "confidence": 0.82,
                "reasoning": "All criteria met within acceptable thresholds",
                "conditions": ["Standard review period applies"]
            })
        elif "risk" in prompt_lower:
            return json.dumps({
                "risk_level": "medium",
                "risk_score": 0.45,
                "factors": ["market volatility", "timeline constraints"],
                "mitigations": ["diversify approach", "establish contingency"]
            })
        elif "extract" in prompt_lower or "parse" in prompt_lower:
            return json.dumps({
                "extracted_data": {
                    "entities": ["Entity A", "Entity B"],
                    "amounts": [1000, 2500],
                    "dates": ["2025-01-15", "2025-02-28"],
                    "categories": ["Category 1", "Category 2"]
                },
                "confidence": 0.9
            })
        elif "summarize" in prompt_lower or "summary" in prompt_lower:
            return json.dumps({
                "summary": "The analysis indicates positive outcomes with moderate risk factors. Key metrics are within expected ranges.",
                "key_points": [
                    "Performance metrics exceed baseline",
                    "Resource utilization is optimal",
                    "Minor improvements identified"
                ],
                "word_count": 45
            })
        else:
            return json.dumps({
                "response": "Analysis complete",
                "status": "success",
                "insights": ["Pattern detected", "Threshold met", "Action recommended"],
                "confidence": 0.75
            })

    async def analyze(self, prompt: str, data: Dict) -> Dict:
        response = await self.complete(f"{prompt}\n\nData: {json.dumps(data)}")
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"response": response, "status": "success"}


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. Run: pip install openai")
                return None
        return self._client

    async def complete(self, prompt: str, **kwargs) -> str:
        client = await self._get_client()
        if not client:
            raise RuntimeError("OpenAI client not available")

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        return response.choices[0].message.content

    async def analyze(self, prompt: str, data: Dict) -> Dict:
        full_prompt = f"""Analyze the following data and respond in JSON format.

{prompt}

Data:
{json.dumps(data, indent=2)}

Respond with valid JSON only."""

        response = await self.complete(full_prompt)
        try:
            # Try to extract JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"response": response, "parse_error": True}


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic package not installed. Run: pip install anthropic")
                return None
        return self._client

    async def complete(self, prompt: str, **kwargs) -> str:
        client = await self._get_client()
        if not client:
            raise RuntimeError("Anthropic client not available")

        response = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def analyze(self, prompt: str, data: Dict) -> Dict:
        full_prompt = f"""Analyze the following data and respond in JSON format.

{prompt}

Data:
{json.dumps(data, indent=2)}

Respond with valid JSON only, no markdown formatting."""

        response = await self.complete(full_prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"response": response, "parse_error": True}


class OllamaProvider(BaseAIProvider):
    """Local Ollama provider"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import httpx
                response = httpx.get(f"{self.base_url}/api/tags", timeout=2)
                self._available = response.status_code == 200
            except Exception:
                self._available = False
        return self._available

    async def complete(self, prompt: str, **kwargs) -> str:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx not installed. Run: pip install httpx")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            result = response.json()
            return result.get("response", "")

    async def analyze(self, prompt: str, data: Dict) -> Dict:
        full_prompt = f"""{prompt}

Data: {json.dumps(data)}

Respond in JSON format only."""

        response = await self.complete(full_prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"response": response, "parse_error": True}


# =============================================================================
# Main AI Service
# =============================================================================

class AIService:
    """
    Main AI service with multi-provider support and caching.

    Automatically selects the best available provider and handles fallbacks.
    """

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.cache = ResponseCache(ttl_seconds=self.config.cache_ttl_seconds)
        self.providers: Dict[AIProvider, BaseAIProvider] = {}
        self.stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "provider_calls": {},
            "errors": 0
        }
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available providers"""
        # Always add mock provider
        self.providers[AIProvider.MOCK] = MockAIProvider()

        # Add OpenAI if configured
        if self.config.openai_api_key:
            self.providers[AIProvider.OPENAI] = OpenAIProvider(
                api_key=self.config.openai_api_key,
                model=self.config.model if "gpt" in self.config.model else "gpt-4"
            )

        # Add Anthropic if configured
        if self.config.anthropic_api_key:
            self.providers[AIProvider.ANTHROPIC] = AnthropicProvider(
                api_key=self.config.anthropic_api_key,
                model=self.config.model if "claude" in self.config.model else "claude-3-sonnet-20240229"
            )

        # Add Ollama
        self.providers[AIProvider.OLLAMA] = OllamaProvider(
            base_url=self.config.ollama_base_url
        )

        logger.info(f"AI Service initialized with providers: {list(self.providers.keys())}")

    def _get_provider(self) -> BaseAIProvider:
        """Get the best available provider"""
        # Try configured provider first
        if self.config.provider in self.providers:
            provider = self.providers[self.config.provider]
            if provider.is_available():
                return provider

        # Fallback order: OpenAI -> Anthropic -> Ollama -> Mock
        fallback_order = [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.OLLAMA, AIProvider.MOCK]
        for provider_type in fallback_order:
            if provider_type in self.providers:
                provider = self.providers[provider_type]
                if provider.is_available():
                    logger.info(f"Using fallback provider: {provider_type}")
                    return provider

        # Default to mock
        return self.providers[AIProvider.MOCK]

    async def analyze(
        self,
        prompt: str,
        data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze data using AI.

        Args:
            prompt: Analysis prompt/instructions
            data: Data to analyze
            use_cache: Whether to use cached responses

        Returns:
            Analysis results as dictionary
        """
        self.stats["total_calls"] += 1
        data = data or {}

        # Check cache
        if use_cache and self.config.cache_enabled:
            cached = self.cache.get(prompt, data)
            if cached:
                self.stats["cache_hits"] += 1
                return {**cached, "_cached": True}

        # Get provider and make call
        provider = self._get_provider()
        provider_name = type(provider).__name__

        try:
            result = await provider.analyze(prompt, data)
            result["_provider"] = provider_name
            result["_timestamp"] = datetime.now().isoformat()

            # Update stats
            self.stats["provider_calls"][provider_name] = \
                self.stats["provider_calls"].get(provider_name, 0) + 1

            # Cache result
            if use_cache and self.config.cache_enabled:
                self.cache.set(prompt, data, result)

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"AI analysis error: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "_provider": provider_name
            }

    async def generate_recommendations(
        self,
        context: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on context.

        Args:
            context: Context information (domain, issue, current_state, etc.)
            constraints: Constraints to consider
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommendations with priority and rationale
        """
        prompt = f"""Based on the following context, generate up to {max_recommendations} actionable recommendations.

Context: {json.dumps(context, indent=2)}

{"Constraints: " + ", ".join(constraints) if constraints else ""}

For each recommendation, provide:
1. action: Specific action to take
2. priority: high/medium/low
3. impact: Expected impact
4. rationale: Why this is recommended
5. effort: Estimated effort (low/medium/high)

Respond in JSON format with a "recommendations" array."""

        result = await self.analyze(prompt, context)

        if "recommendations" in result:
            return result["recommendations"]
        elif "response" in result:
            return [{"action": result["response"], "priority": "medium", "impact": "unknown"}]
        return []

    async def make_decision(
        self,
        options: List[str],
        context: Dict[str, Any],
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Make a decision from available options.

        Args:
            options: Available options/choices
            context: Context for decision making
            criteria: Criteria to consider

        Returns:
            Decision with confidence and reasoning
        """
        prompt = f"""Make a decision from the following options based on the context.

Options: {", ".join(options)}
Context: {json.dumps(context, indent=2)}
{"Criteria: " + ", ".join(criteria) if criteria else ""}

Provide:
1. decision: The chosen option
2. confidence: Confidence level (0-1)
3. reasoning: Why this option was chosen
4. alternatives: Brief note on why other options weren't chosen
5. conditions: Any conditions or caveats

Respond in JSON format."""

        result = await self.analyze(prompt, {"options": options, **context})
        return result

    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract entities from text.

        Args:
            text: Text to extract entities from
            entity_types: Types of entities to look for (e.g., ["person", "organization", "date"])

        Returns:
            Extracted entities by type
        """
        types_str = ", ".join(entity_types) if entity_types else "all relevant entities"
        prompt = f"""Extract {types_str} from the following text.

For each entity found, provide:
- value: The extracted value
- type: Entity type
- confidence: Extraction confidence (0-1)
- context: Brief context where found

Respond in JSON format with an "entities" array."""

        return await self.analyze(prompt, {"text": text})

    async def assess_risk(
        self,
        scenario: Dict[str, Any],
        risk_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assess risk for a scenario.

        Args:
            scenario: Scenario details
            risk_categories: Categories to assess (e.g., ["financial", "operational", "compliance"])

        Returns:
            Risk assessment with scores and mitigations
        """
        categories_str = ", ".join(risk_categories) if risk_categories else "all relevant categories"
        prompt = f"""Assess the risk for the following scenario across {categories_str}.

For each risk identified, provide:
- category: Risk category
- level: Risk level (low/medium/high/critical)
- score: Numeric score (0-1)
- description: Brief description
- likelihood: Probability of occurrence
- impact: Potential impact
- mitigations: Suggested mitigations

Also provide:
- overall_risk_level: Overall assessment
- overall_risk_score: Combined score (0-1)
- key_concerns: Top concerns to address

Respond in JSON format."""

        return await self.analyze(prompt, scenario)

    async def summarize(
        self,
        content: str,
        max_length: Optional[int] = None,
        focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize content.

        Args:
            content: Content to summarize
            max_length: Maximum summary length (words)
            focus: Specific focus area

        Returns:
            Summary with key points
        """
        length_str = f" in approximately {max_length} words" if max_length else ""
        focus_str = f" Focus on: {focus}." if focus else ""

        prompt = f"""Summarize the following content{length_str}.{focus_str}

Provide:
- summary: The summary text
- key_points: List of key points (3-5)
- themes: Main themes identified
- sentiment: Overall sentiment (positive/negative/neutral)

Respond in JSON format."""

        return await self.analyze(prompt, {"content": content})

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache.cache),
            "available_providers": [
                p.value for p, impl in self.providers.items()
                if impl.is_available()
            ]
        }


# =============================================================================
# Global Instance
# =============================================================================

# Create global AI service instance
ai_service = AIService()


def get_ai_service() -> AIService:
    """Get the global AI service instance"""
    return ai_service


# =============================================================================
# Convenience Functions
# =============================================================================

async def analyze(prompt: str, data: Optional[Dict] = None) -> Dict:
    """Convenience function for analysis"""
    return await ai_service.analyze(prompt, data)


async def recommend(context: Dict, constraints: Optional[List[str]] = None) -> List[Dict]:
    """Convenience function for recommendations"""
    return await ai_service.generate_recommendations(context, constraints)


async def decide(options: List[str], context: Dict) -> Dict:
    """Convenience function for decisions"""
    return await ai_service.make_decision(options, context)


async def assess_risk(scenario: Dict) -> Dict:
    """Convenience function for risk assessment"""
    return await ai_service.assess_risk(scenario)


async def summarize(content: str, max_length: Optional[int] = None) -> Dict:
    """Convenience function for summarization"""
    return await ai_service.summarize(content, max_length)
