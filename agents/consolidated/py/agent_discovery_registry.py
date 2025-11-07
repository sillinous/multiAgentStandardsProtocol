"""
Enterprise Agent Discovery and Registry System
Dynamic agent instantiation, capability matching, and lifecycle management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Type, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import json
import importlib
import inspect
from pathlib import Path
from abc import ABC, abstractmethod

# Import existing A2A infrastructure
from backend.app.a2a_communication.interfaces import (
    AgentIdentifier,
    AgentCapability,
    AgentTeam,
    BaseAgent,
    ProcessStatus,
    Priority,
    AgentMessage,
    AgentResponse,
)
from backend.app.a2a_communication.agent_registry import AgentRegistry
from backend.app.a2a_communication.message_bus import message_bus
from backend.app.a2a_communication.knowledge_manager import knowledge_manager

logger = logging.getLogger(__name__)


class AgentLibraryType(str, Enum):
    """Categories of reusable agents"""

    CORE_UTILITY = "core_utility"
    API_INTEGRATION = "api_integration"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    SYSTEM_MAINTENANCE = "system_maintenance"
    COORDINATION = "coordination"
    ORCHESTRATION = "orchestration"


class CapabilityDomain(str, Enum):
    """APQC-aligned capability domains"""

    STRATEGY_DEVELOPMENT = "1.0_develop_vision_strategy"
    PRODUCT_DEVELOPMENT = "2.0_develop_manage_products"
    MARKETING_SALES = "3.0_market_sell_products"
    SERVICE_DELIVERY = "4.0_deliver_products_services"
    CUSTOMER_SERVICE = "5.0_manage_customer_service"
    HUMAN_RESOURCES = "6.0_develop_manage_human_capital"
    IT_MANAGEMENT = "11.0_manage_information_technology"
    FINANCIAL_RESOURCES = "12.0_manage_financial_resources"
    KNOWLEDGE_IMPROVEMENT = "13.0_manage_knowledge_improvement"


@dataclass
class AgentCapabilityProfile:
    """Comprehensive agent capability profile"""

    agent_id: str
    capability_domains: List[CapabilityDomain]
    reusable_functions: List[str]
    integration_patterns: Dict[str, Any]
    performance_metrics: Dict[str, float]
    resource_requirements: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    quality_standards: Dict[str, float] = field(default_factory=dict)
    scaling_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentLibraryEntry:
    """Registry entry for reusable agents"""

    entry_id: str
    agent_type: AgentLibraryType
    agent_class: str
    capability_profile: AgentCapabilityProfile
    instantiation_template: Dict[str, Any]
    usage_patterns: List[str]
    performance_benchmarks: Dict[str, float]
    compatibility_matrix: Dict[str, List[str]]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_rate: float = 1.0


class ReusableAgentLibrary:
    """Central library for reusable agent components"""

    def __init__(self):
        self.registry: Dict[str, AgentLibraryEntry] = {}
        self.capability_index: Dict[CapabilityDomain, Set[str]] = {}
        self.function_index: Dict[str, Set[str]] = {}
        self.pattern_index: Dict[str, Set[str]] = {}
        self.active_instances: Dict[str, BaseAgent] = {}
        self.performance_tracker: Dict[str, List[Dict[str, Any]]] = {}
        self._initialize_library()

    def _initialize_library(self):
        """Initialize the library with predefined agent types"""
        self._register_core_utility_agents()
        self._register_api_integration_agents()
        self._register_business_intelligence_agents()
        self._register_system_maintenance_agents()
        self._register_coordination_agents()

    def _register_core_utility_agents(self):
        """Register core utility agents"""

        # Data Validation Agent
        data_validation_profile = AgentCapabilityProfile(
            agent_id="data_validation_agent",
            capability_domains=[CapabilityDomain.IT_MANAGEMENT],
            reusable_functions=[
                "validate_api_input",
                "sanitize_user_content",
                "normalize_data_format",
                "assess_data_quality",
            ],
            integration_patterns={
                "validation_pipeline": "input -> validate -> sanitize -> normalize",
                "quality_assessment": "data -> analyze -> score -> recommend",
            },
            performance_metrics={"validation_speed": 0.95, "accuracy": 0.99},
            resource_requirements={"cpu": "low", "memory": "medium", "network": "low"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="core_data_validation",
                agent_type=AgentLibraryType.CORE_UTILITY,
                agent_class="DataValidationAgent",
                capability_profile=data_validation_profile,
                instantiation_template={
                    "validation_rules": "configurable",
                    "sanitization_level": "high",
                    "quality_thresholds": {"accuracy": 0.95, "completeness": 0.90},
                },
                usage_patterns=["input_validation", "data_quality", "security_sanitization"],
                performance_benchmarks={"throughput": 1000, "latency": 50},
                compatibility_matrix={"works_with": ["all"], "conflicts_with": []},
            )
        )

        # Error Recovery Agent
        error_recovery_profile = AgentCapabilityProfile(
            agent_id="error_recovery_agent",
            capability_domains=[CapabilityDomain.IT_MANAGEMENT],
            reusable_functions=[
                "execute_with_retry",
                "activate_circuit_breaker",
                "route_error",
                "calculate_backoff_delay",
            ],
            integration_patterns={
                "retry_strategy": "attempt -> backoff -> retry -> escalate",
                "circuit_breaker": "monitor -> threshold -> break -> recover",
            },
            performance_metrics={"recovery_rate": 0.98, "error_reduction": 0.85},
            resource_requirements={"cpu": "low", "memory": "low", "network": "medium"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="core_error_recovery",
                agent_type=AgentLibraryType.CORE_UTILITY,
                agent_class="ErrorRecoveryAgent",
                capability_profile=error_recovery_profile,
                instantiation_template={
                    "retry_strategies": ["exponential_backoff", "linear", "fixed"],
                    "circuit_breaker_thresholds": {"failure_rate": 0.5, "timeout": 30},
                    "escalation_policies": "configurable",
                },
                usage_patterns=["api_resilience", "system_recovery", "fault_tolerance"],
                performance_benchmarks={"recovery_time": 5, "success_rate": 0.98},
                compatibility_matrix={"works_with": ["all"], "conflicts_with": []},
            )
        )

    def _register_api_integration_agents(self):
        """Register API integration agents"""

        # OpenAI Integration Agent
        openai_profile = AgentCapabilityProfile(
            agent_id="openai_integration_agent",
            capability_domains=[
                CapabilityDomain.PRODUCT_DEVELOPMENT,
                CapabilityDomain.IT_MANAGEMENT,
            ],
            reusable_functions=[
                "optimize_prompt",
                "manage_token_budget",
                "validate_ai_response",
                "track_api_costs",
                "select_optimal_model",
            ],
            integration_patterns={
                "ai_request_flow": "prompt -> optimize -> request -> validate -> track",
                "cost_optimization": "budget -> monitor -> optimize -> alert",
            },
            performance_metrics={"response_quality": 0.92, "cost_efficiency": 0.88},
            resource_requirements={"cpu": "medium", "memory": "medium", "network": "high"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="api_openai_integration",
                agent_type=AgentLibraryType.API_INTEGRATION,
                agent_class="OpenAIIntegrationAgent",
                capability_profile=openai_profile,
                instantiation_template={
                    "model_preferences": ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
                    "cost_limits": {"daily": 100, "monthly": 2000},
                    "quality_thresholds": {"relevance": 0.9, "accuracy": 0.85},
                },
                usage_patterns=["content_generation", "analysis", "summarization"],
                performance_benchmarks={"response_time": 3000, "quality_score": 0.92},
                compatibility_matrix={
                    "works_with": ["content_agents", "analysis_agents"],
                    "conflicts_with": [],
                },
            )
        )

    def _register_business_intelligence_agents(self):
        """Register business intelligence agents"""

        # Market Opportunity Analysis Agent
        market_analysis_profile = AgentCapabilityProfile(
            agent_id="market_opportunity_analysis_agent",
            capability_domains=[
                CapabilityDomain.STRATEGY_DEVELOPMENT,
                CapabilityDomain.MARKETING_SALES,
            ],
            reusable_functions=[
                "analyze_market_opportunity",
                "score_opportunity_dimensions",
                "assess_competitive_landscape",
                "forecast_market_size",
                "calculate_timing_window",
            ],
            integration_patterns={
                "comprehensive_analysis": "data -> analyze -> score -> validate -> report",
                "collaborative_intelligence": "coordinate -> aggregate -> synthesize -> optimize",
            },
            performance_metrics={"analysis_accuracy": 0.89, "prediction_reliability": 0.82},
            resource_requirements={"cpu": "high", "memory": "high", "network": "medium"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="bi_market_opportunity",
                agent_type=AgentLibraryType.BUSINESS_INTELLIGENCE,
                agent_class="MarketOpportunityAnalysisAgent",
                capability_profile=market_analysis_profile,
                instantiation_template={
                    "analysis_depth": ["basic", "comprehensive", "deep"],
                    "data_sources": ["trends", "competitors", "customers", "financial"],
                    "scoring_models": "ml_enhanced",
                },
                usage_patterns=["market_research", "opportunity_discovery", "strategic_planning"],
                performance_benchmarks={"analysis_time": 900, "accuracy": 0.89},
                compatibility_matrix={
                    "works_with": ["trend_analysis", "competitive_intel", "financial_modeling"],
                    "conflicts_with": [],
                },
            )
        )

    def _register_system_maintenance_agents(self):
        """Register system maintenance agents"""

        # System Performance Agent
        performance_profile = AgentCapabilityProfile(
            agent_id="system_performance_agent",
            capability_domains=[CapabilityDomain.IT_MANAGEMENT],
            reusable_functions=[
                "collect_performance_metrics",
                "detect_performance_bottlenecks",
                "optimize_resource_utilization",
                "model_performance_trends",
                "execute_scaling_decisions",
            ],
            integration_patterns={
                "continuous_monitoring": "collect -> analyze -> optimize -> scale",
                "predictive_maintenance": "trend -> predict -> prevent -> optimize",
            },
            performance_metrics={"monitoring_coverage": 0.99, "optimization_impact": 0.75},
            resource_requirements={"cpu": "medium", "memory": "high", "network": "medium"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="sys_performance_monitor",
                agent_type=AgentLibraryType.SYSTEM_MAINTENANCE,
                agent_class="SystemPerformanceAgent",
                capability_profile=performance_profile,
                instantiation_template={
                    "monitoring_scope": ["cpu", "memory", "disk", "network", "application"],
                    "optimization_strategy": ["reactive", "proactive", "predictive"],
                    "scaling_policies": "auto_configured",
                },
                usage_patterns=["performance_monitoring", "resource_optimization", "scaling"],
                performance_benchmarks={"response_time": 100, "accuracy": 0.95},
                compatibility_matrix={"works_with": ["all_system_agents"], "conflicts_with": []},
            )
        )

    def _register_coordination_agents(self):
        """Register coordination and orchestration agents"""

        # Workflow Coordinator Agent
        workflow_profile = AgentCapabilityProfile(
            agent_id="workflow_coordinator_agent",
            capability_domains=[
                CapabilityDomain.IT_MANAGEMENT,
                CapabilityDomain.STRATEGY_DEVELOPMENT,
            ],
            reusable_functions=[
                "orchestrate_workflow",
                "adapt_process_dynamically",
                "optimize_resource_allocation",
                "monitor_workflow_performance",
                "handle_workflow_exceptions",
            ],
            integration_patterns={
                "multi_agent_orchestration": "plan -> coordinate -> execute -> monitor -> optimize",
                "adaptive_workflow": "monitor -> analyze -> adapt -> execute -> validate",
            },
            performance_metrics={"orchestration_efficiency": 0.93, "adaptation_speed": 0.87},
            resource_requirements={"cpu": "high", "memory": "high", "network": "high"},
        )

        self.register_agent(
            AgentLibraryEntry(
                entry_id="coord_workflow_orchestrator",
                agent_type=AgentLibraryType.COORDINATION,
                agent_class="WorkflowCoordinatorAgent",
                capability_profile=workflow_profile,
                instantiation_template={
                    "orchestration_strategies": ["sequential", "parallel", "adaptive"],
                    "resource_optimization": "ml_enhanced",
                    "exception_handling": "comprehensive",
                },
                usage_patterns=[
                    "workflow_orchestration",
                    "process_coordination",
                    "resource_management",
                ],
                performance_benchmarks={"coordination_time": 200, "success_rate": 0.96},
                compatibility_matrix={"works_with": ["all"], "conflicts_with": []},
            )
        )

    def register_agent(self, entry: AgentLibraryEntry):
        """Register a new agent in the library"""
        self.registry[entry.entry_id] = entry

        # Update capability index
        for domain in entry.capability_profile.capability_domains:
            if domain not in self.capability_index:
                self.capability_index[domain] = set()
            self.capability_index[domain].add(entry.entry_id)

        # Update function index
        for function in entry.capability_profile.reusable_functions:
            if function not in self.function_index:
                self.function_index[function] = set()
            self.function_index[function].add(entry.entry_id)

        # Update pattern index
        for pattern in entry.usage_patterns:
            if pattern not in self.pattern_index:
                self.pattern_index[pattern] = set()
            self.pattern_index[pattern].add(entry.entry_id)

        logger.info(f"Registered agent: {entry.entry_id} of type {entry.agent_type}")

    def discover_agents_by_capability(
        self, capability_domain: CapabilityDomain
    ) -> List[AgentLibraryEntry]:
        """Discover agents by capability domain"""
        agent_ids = self.capability_index.get(capability_domain, set())
        return [self.registry[agent_id] for agent_id in agent_ids]

    def discover_agents_by_function(self, function_name: str) -> List[AgentLibraryEntry]:
        """Discover agents by specific function"""
        agent_ids = self.function_index.get(function_name, set())
        return [self.registry[agent_id] for agent_id in agent_ids]

    def discover_agents_by_pattern(self, usage_pattern: str) -> List[AgentLibraryEntry]:
        """Discover agents by usage pattern"""
        agent_ids = self.pattern_index.get(usage_pattern, set())
        return [self.registry[agent_id] for agent_id in agent_ids]

    def find_optimal_agent(self, requirements: Dict[str, Any]) -> Optional[AgentLibraryEntry]:
        """Find the optimal agent for specific requirements"""
        candidates = []

        # Filter by capability domains
        if "capability_domains" in requirements:
            for domain in requirements["capability_domains"]:
                candidates.extend(self.discover_agents_by_capability(domain))

        # Filter by required functions
        if "required_functions" in requirements:
            function_candidates = []
            for function in requirements["required_functions"]:
                function_candidates.extend(self.discover_agents_by_function(function))
            candidates = (
                list(set(candidates) & set(function_candidates))
                if candidates
                else function_candidates
            )

        # Filter by usage patterns
        if "usage_patterns" in requirements:
            pattern_candidates = []
            for pattern in requirements["usage_patterns"]:
                pattern_candidates.extend(self.discover_agents_by_pattern(pattern))
            candidates = (
                list(set(candidates) & set(pattern_candidates))
                if candidates
                else pattern_candidates
            )

        if not candidates:
            return None

        # Score candidates based on performance and compatibility
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_agent_score(candidate, requirements)
            scored_candidates.append((candidate, score))

        # Return highest scoring agent
        return max(scored_candidates, key=lambda x: x[1])[0] if scored_candidates else None

    def _calculate_agent_score(
        self, agent: AgentLibraryEntry, requirements: Dict[str, Any]
    ) -> float:
        """Calculate agent suitability score"""
        score = 0.0

        # Performance metrics score
        performance_weight = 0.3
        if "performance_requirements" in requirements:
            perf_req = requirements["performance_requirements"]
            for metric, required_value in perf_req.items():
                if metric in agent.performance_benchmarks:
                    agent_value = agent.performance_benchmarks[metric]
                    if isinstance(required_value, (int, float)):
                        # Higher is better for most metrics
                        score += performance_weight * min(agent_value / required_value, 1.0)

        # Success rate score
        success_weight = 0.3
        score += success_weight * agent.success_rate

        # Usage frequency score (more used = more reliable)
        usage_weight = 0.2
        max_usage = max([a.usage_count for a in self.registry.values()], default=1)
        score += usage_weight * (agent.usage_count / max_usage)

        # Compatibility score
        compatibility_weight = 0.2
        if "existing_agents" in requirements:
            existing = requirements["existing_agents"]
            compatible_count = len(
                [a for a in existing if a in agent.compatibility_matrix.get("works_with", [])]
            )
            conflict_count = len(
                [a for a in existing if a in agent.compatibility_matrix.get("conflicts_with", [])]
            )
            score += compatibility_weight * (compatible_count / max(len(existing), 1)) - (
                conflict_count * 0.5
            )

        return score

    async def instantiate_agent(
        self, entry_id: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAgent]:
        """Instantiate an agent from the library"""
        if entry_id not in self.registry:
            logger.error(f"Agent entry {entry_id} not found in library")
            return None

        entry = self.registry[entry_id]

        try:
            # Create agent configuration
            agent_config = entry.instantiation_template.copy()
            if config:
                agent_config.update(config)

            # Create unique agent identifier
            agent_id = f"{entry.agent_class}_{uuid.uuid4().hex[:8]}"

            # Instantiate the agent (this would import and create the actual agent class)
            agent_instance = await self._create_agent_instance(
                entry.agent_class, agent_id, agent_config
            )

            if agent_instance:
                self.active_instances[agent_id] = agent_instance
                entry.usage_count += 1
                logger.info(f"Successfully instantiated agent: {agent_id}")
                return agent_instance

        except Exception as e:
            logger.error(f"Failed to instantiate agent {entry_id}: {str(e)}")
            return None

    async def _create_agent_instance(
        self, agent_class: str, agent_id: str, config: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        """Create actual agent instance (implementation depends on agent architecture)"""
        # This is a placeholder - actual implementation would:
        # 1. Import the agent class
        # 2. Create instance with config
        # 3. Initialize with A2A communication
        # 4. Register with message bus

        # For now, return a mock agent
        class MockAgent(BaseAgent):
            def __init__(self, identifier: str, capabilities: List[AgentCapability]):
                super().__init__(identifier, capabilities)
                self.config = config

        capabilities = [
            AgentCapability(name=f"{agent_class}_capability", description="Mock capability")
        ]
        agent = MockAgent(AgentIdentifier(id=agent_id, name=agent_class), capabilities)
        return agent

    def get_library_statistics(self) -> Dict[str, Any]:
        """Get library usage and performance statistics"""
        stats = {
            "total_agents": len(self.registry),
            "active_instances": len(self.active_instances),
            "agents_by_type": {},
            "agents_by_capability": {},
            "performance_summary": {},
        }

        # Count by type
        for entry in self.registry.values():
            agent_type = entry.agent_type.value
            stats["agents_by_type"][agent_type] = stats["agents_by_type"].get(agent_type, 0) + 1

        # Count by capability
        for domain, agent_ids in self.capability_index.items():
            stats["agents_by_capability"][domain.value] = len(agent_ids)

        # Performance summary
        total_usage = sum(entry.usage_count for entry in self.registry.values())
        avg_success_rate = sum(entry.success_rate for entry in self.registry.values()) / len(
            self.registry
        )

        stats["performance_summary"] = {
            "total_usage": total_usage,
            "average_success_rate": avg_success_rate,
            "most_used_agent": (
                max(self.registry.values(), key=lambda x: x.usage_count).entry_id
                if self.registry
                else None
            ),
        }

        return stats


# Global library instance
reusable_agent_library = ReusableAgentLibrary()


# Convenience functions for agent discovery and instantiation
async def discover_agent(
    capability_domain: CapabilityDomain = None, function_name: str = None, usage_pattern: str = None
) -> List[AgentLibraryEntry]:
    """Discover agents by various criteria"""
    if capability_domain:
        return reusable_agent_library.discover_agents_by_capability(capability_domain)
    elif function_name:
        return reusable_agent_library.discover_agents_by_function(function_name)
    elif usage_pattern:
        return reusable_agent_library.discover_agents_by_pattern(usage_pattern)
    else:
        return list(reusable_agent_library.registry.values())


async def find_optimal_agent_for_task(requirements: Dict[str, Any]) -> Optional[AgentLibraryEntry]:
    """Find the optimal agent for a specific task"""
    return reusable_agent_library.find_optimal_agent(requirements)


async def instantiate_reusable_agent(
    entry_id: str, config: Optional[Dict[str, Any]] = None
) -> Optional[BaseAgent]:
    """Instantiate a reusable agent"""
    return await reusable_agent_library.instantiate_agent(entry_id, config)


async def get_agent_library_stats() -> Dict[str, Any]:
    """Get library statistics"""
    return reusable_agent_library.get_library_statistics()
