"""
Hybrid Base Agent - Enhanced Base Class for All Agents

Provides automatic local/cloud routing for AI operations.
All future agents should inherit from this class to get:
- ZERO credit local processing
- Automatic cloud fallback
- Quality-based routing
- Cost tracking
- A2A capability discovery
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from openai import OpenAI
import os

from app.ollama_service import ollama_service

logger = logging.getLogger(__name__)


class QualityMode(Enum):
    """Quality modes for AI processing"""

    FAST = "fast"  # Local LLM only (ZERO credits)
    AUTO = "auto"  # Smart routing based on complexity
    HIGH = "high"  # Cloud API (premium quality)


class TaskComplexity(Enum):
    """Task complexity assessment"""

    SIMPLE = "simple"  # Use local LLM
    MODERATE = "moderate"  # Prefer local, cloud if needed
    COMPLEX = "complex"  # Requires cloud API


class HybridBaseAgent:
    """
    Enhanced base class for all agents with hybrid AI capabilities.

    Features:
    - Automatic local/cloud routing
    - ZERO credits when using local LLM
    - Quality mode selection
    - Cost tracking and optimization
    - Consistent interface across all agents

    Usage:
        class MyAgent(HybridBaseAgent):
            def __init__(self):
                super().__init__(
                    name="My Agent",
                    agent_id="my_agent_v1",
                    version="1.0.0",
                    capabilities=["capability1", "capability2"]
                )

            def _process_local(self, input_data, **kwargs):
                # Implement local processing (ZERO credits)
                return result

            def _process_cloud(self, input_data, **kwargs):
                # Implement cloud processing (uses credits)
                return result

            def _assess_complexity(self, input_data, **kwargs):
                # Optional: custom complexity assessment
                return TaskComplexity.SIMPLE
    """

    def __init__(
        self, name: str, agent_id: str = None, version: str = "1.0.0", capabilities: list = None
    ):
        self.name = name
        self.agent_id = agent_id or f"{name.lower().replace(' ', '_')}_v1"
        self.version = version
        self.capabilities = capabilities or []

        # OpenAI client for cloud processing
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        # Ollama client for local processing
        self.ollama = ollama_service

        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "local_requests": 0,
            "cloud_requests": 0,
            "credits_saved": 0.0,
            "failed_requests": 0,
        }

        logger.info(f"🤖 Hybrid Agent '{name}' initialized (Ollama: {self.ollama.available})")

    async def execute(
        self,
        input_data: Any,
        quality: str = "auto",
        force_local: bool = False,
        force_cloud: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute agent task with automatic routing.

        Args:
            input_data: Primary input for the agent
            quality: "fast" (local), "auto" (smart), "high" (cloud)
            force_local: Force local processing
            force_cloud: Force cloud processing
            **kwargs: Additional agent-specific parameters

        Returns:
            {
                "result": ...,  # Agent-specific result
                "method": "local" or "cloud",
                "credits_used": 0 or float,
                "processing_time_ms": float,
                "confidence": float,
                **agent_specific_fields
            }
        """
        self.stats["total_requests"] += 1
        start_time = datetime.utcnow()

        try:
            # Determine processing method
            method = self._determine_method(
                input_data=input_data,
                quality=quality,
                force_local=force_local,
                force_cloud=force_cloud,
                **kwargs,
            )

            # Execute processing
            if method == "local":
                result = await self._process_local(input_data, **kwargs)
                self.stats["local_requests"] += 1
                self.stats["credits_saved"] += self._estimate_credit_cost(input_data)
                credits_used = 0
            else:
                result = await self._process_cloud(input_data, **kwargs)
                self.stats["cloud_requests"] += 1
                credits_used = self._estimate_credit_cost(input_data)

            # Add metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            response = {
                "result": result,
                "method": method,
                "credits_used": credits_used,
                "processing_time_ms": processing_time,
                "agent_id": self.agent_id,
                "agent_name": self.name,
            }

            if method == "local":
                response["cost_saved"] = f"${credits_used:.3f}"
            else:
                response["cost_incurred"] = f"${credits_used:.3f}"

            logger.info(f"✅ {self.name} completed via {method} ({processing_time:.0f}ms)")

            return response

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"❌ {self.name} failed: {e}")

            # Attempt fallback if local failed
            if method == "local" and self.openai_client:
                logger.info("⚠️ Local failed, attempting cloud fallback")
                try:
                    result = await self._process_cloud(input_data, **kwargs)
                    self.stats["cloud_requests"] += 1
                    return {
                        "result": result,
                        "method": "cloud",
                        "credits_used": self._estimate_credit_cost(input_data),
                        "fallback": True,
                        "agent_id": self.agent_id,
                    }
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")

            raise

    def _determine_method(
        self, input_data: Any, quality: str, force_local: bool, force_cloud: bool, **kwargs
    ) -> str:
        """
        Determine whether to use local or cloud processing.

        Override this method for custom routing logic.
        """

        # Forced routing
        if force_local:
            if not self.ollama.available:
                logger.warning("Local forced but Ollama unavailable, using cloud")
                return "cloud"
            return "local"

        if force_cloud:
            return "cloud"

        # Quality-based routing
        if quality == "fast":
            return "local" if self.ollama.available else "cloud"

        if quality == "high":
            return "cloud"

        # Auto mode: assess complexity
        if not self.ollama.available:
            return "cloud"

        complexity = self._assess_complexity(input_data, **kwargs)

        if complexity == TaskComplexity.SIMPLE:
            return "local"
        elif complexity == TaskComplexity.COMPLEX:
            return "cloud"
        else:  # MODERATE
            # Prefer local for moderate complexity
            return "local" if self.ollama.available else "cloud"

    def _assess_complexity(self, input_data: Any, **kwargs) -> TaskComplexity:
        """
        Assess task complexity for routing decisions.

        Override this method for agent-specific complexity assessment.

        Default logic:
        - Small inputs (<500 chars) = SIMPLE
        - Medium inputs (500-2000 chars) = MODERATE
        - Large inputs (>2000 chars) = COMPLEX
        """
        try:
            input_str = str(input_data)
            length = len(input_str)

            if length < 500:
                return TaskComplexity.SIMPLE
            elif length < 2000:
                return TaskComplexity.MODERATE
            else:
                return TaskComplexity.COMPLEX
        except:
            return TaskComplexity.MODERATE

    async def _process_local(self, input_data: Any, **kwargs) -> Any:
        """
        Process using local LLM - ZERO CREDITS.

        Override this method with agent-specific local processing logic.

        Raises:
            NotImplementedError if not overridden
        """
        raise NotImplementedError(f"{self.name} must implement _process_local() method")

    async def _process_cloud(self, input_data: Any, **kwargs) -> Any:
        """
        Process using cloud API - USES CREDITS.

        Override this method with agent-specific cloud processing logic.

        Raises:
            NotImplementedError if not overridden
        """
        raise NotImplementedError(f"{self.name} must implement _process_cloud() method")

    def _estimate_credit_cost(self, input_data: Any) -> float:
        """
        Estimate credit cost for this operation.

        Override for more accurate agent-specific estimates.
        Default: $0.01 per request
        """
        return 0.01

    async def call_openai(
        self,
        prompt: str,
        system_message: str = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        response_format: dict = None,
        max_tokens: int = 1000,
    ) -> str:
        """
        Helper method to call OpenAI API.

        Args:
            prompt: User prompt
            system_message: System message (optional)
            model: Model to use
            temperature: Creativity level
            response_format: Response format (e.g., {"type": "json_object"})
            max_tokens: Maximum tokens

        Returns:
            Response text from OpenAI
        """
        if not self.openai_client:
            raise Exception("OpenAI client not available (no API key)")

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.openai_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def call_ollama(
        self, prompt: str, model: str = None, temperature: float = 0.7, max_tokens: int = 500
    ) -> str:
        """
        Helper method to call Ollama local LLM.

        Args:
            prompt: Text prompt
            model: Model name (defaults to phi3:3.8b)
            temperature: Creativity level
            max_tokens: Maximum tokens

        Returns:
            Response text from Ollama
        """
        return await self.ollama.generate(
            prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total = self.stats["total_requests"]
        return {
            **self.stats,
            "local_percentage": (self.stats["local_requests"] / total * 100) if total > 0 else 0,
            "cloud_percentage": (self.stats["cloud_requests"] / total * 100) if total > 0 else 0,
            "success_rate": (
                ((total - self.stats["failed_requests"]) / total * 100) if total > 0 else 0
            ),
            "estimated_cost_saved": self.stats["credits_saved"] * 1.0,
            "ollama_available": self.ollama.available,
        }

    def get_capabilities_manifest(self) -> Dict[str, Any]:
        """
        Return agent capabilities for A2A discovery.

        Override to add agent-specific details.
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "hybrid_mode": True,
            "supports_local": self.ollama.available,
            "supports_cloud": self.openai_client is not None,
            "cost": {"local": "FREE (0 credits)", "cloud": "~$0.01-0.02 per request"},
            "quality_modes": ["fast", "auto", "high"],
            "input_schema": {
                "input_data": "any (agent-specific)",
                "quality": "string (fast/auto/high)",
                "force_local": "boolean",
                "force_cloud": "boolean",
            },
        }


class LegacyAgentAdapter(HybridBaseAgent):
    """
    Adapter for existing agents without hybrid capabilities.

    Wraps legacy agents to add hybrid routing without modifying original code.
    """

    def __init__(self, legacy_agent_instance, name: str = None):
        super().__init__(
            name=name or getattr(legacy_agent_instance, "name", "Legacy Agent"),
            agent_id=f"legacy_{legacy_agent_instance.__class__.__name__.lower()}_v1",
        )
        self.legacy_agent = legacy_agent_instance

    async def _process_local(self, input_data: Any, **kwargs) -> Any:
        """Use Ollama for simple analysis"""
        # Generic local processing for legacy agents
        prompt = f"Analyze: {input_data}"
        return await self.call_ollama(prompt)

    async def _process_cloud(self, input_data: Any, **kwargs) -> Any:
        """Delegate to legacy agent's analyze method"""
        if hasattr(self.legacy_agent, "analyze"):
            result = self.legacy_agent.analyze(input_data, kwargs.get("context"))
            if hasattr(result, "data"):
                return result.data
            return result
        else:
            raise NotImplementedError("Legacy agent must have analyze() method")
