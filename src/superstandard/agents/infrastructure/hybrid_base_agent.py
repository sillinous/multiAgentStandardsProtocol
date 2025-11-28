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

    
    async def _process_local(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process local task with AI-powered analysis.

        Implements APQC process: 
        Domain: default

        Uses smart processing for intelligent analysis, recommendations,
        and decision-making capabilities.
        """
        from superstandard.services.smart_processing import get_processor
        from datetime import datetime

        task_type = input_data.get("task_type", "default")
        self.log("info", f"Processing {task_type} task with AI-powered analysis")

        start_time = datetime.now()

        # Get domain-specific smart processor
        processor = get_processor("default")

        # Prepare context for processing
        processing_context = {
            "apqc_process": "",
            "apqc_id": self.APQC_PROCESS_ID,
            "agent_capabilities": self.capabilities_list,
            "input_data": input_data.get("data", {}),
            "task_context": input_data.get("context", {}),
            "priority": input_data.get("priority", "medium"),
        }

        # Execute smart processing
        processing_result = await processor.process(processing_context, task_type)

        # Extract analysis results
        analysis_results = processing_result.get("analysis", {})
        if not analysis_results:
            analysis_results = {
                "status": processing_result.get("status", "completed"),
                "domain": processing_result.get("domain", "default"),
                "insights": processing_result.get("insights", [])
            }

        # Generate recommendations if not provided
        recommendations = []
        if "recommendations" in processing_result:
            recommendations = processing_result["recommendations"]
        elif "optimization_recommendations" in processing_result:
            recommendations = processing_result["optimization_recommendations"]
        elif "resolution_recommendations" in processing_result:
            recommendations = processing_result["resolution_recommendations"]
        else:
            # Generate default recommendations based on analysis
            recommendations = [{
                "type": "process_optimization",
                "priority": "medium",
                "action": "Review analysis results and implement suggested improvements",
                "confidence": 0.75
            }]

        # Make decisions based on context
        decisions = []
        if "decision" in processing_result or "recommendation" in processing_result:
            decisions.append({
                "decision_type": processing_result.get("decision", processing_result.get("recommendation", "proceed")),
                "confidence": processing_result.get("confidence", 0.8),
                "rationale": processing_result.get("reasoning", "Based on AI analysis"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            decisions.append({
                "decision_type": "proceed",
                "confidence": 0.85,
                "rationale": "Analysis complete, proceeding with standard workflow",
                "timestamp": datetime.now().isoformat()
            })

        # Generate artifacts
        artifacts = []
        if input_data.get("generate_report", False):
            artifacts.append({
                "type": "analysis_report",
                "name": f"{self.config.agent_name}_ai_report",
                "format": "json",
                "content_summary": "AI-powered analysis results",
                "generated_at": datetime.now().isoformat()
            })

        # Compute metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = {
            "processing_time_ms": processing_time,
            "ai_powered": True,
            "processor_used": processor.domain,
            "recommendations_count": len(recommendations),
            "decisions_count": len(decisions),
            "confidence_score": decisions[0].get("confidence", 0.8) if decisions else 0.8
        }

        # Generate events
        events = [{
            "event_type": "ai_task_completed",
            "agent_id": self.config.agent_id,
            "apqc_process": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "summary": f"AI-powered processing of {task_type} task completed",
            "ai_enhanced": True
        }]

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "output": {
                "analysis": analysis_results,
                "recommendations": recommendations,
                "decisions": decisions,
                "artifacts": artifacts,
                "metrics": metrics,
                "events": events,
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
