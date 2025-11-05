"""
Consensus Agent v1.0 - Architecturally Compliant
=================================================

AGENT METADATA:
--------------
Agent Type: consensus
Version: 1.0.0
Protocols: A2A, A2P, ACP, ANP, MCP
Capabilities: vote_aggregation, conflict_resolution, quorum_checking, weighted_voting

ARCHITECTURAL COMPLIANCE:
------------------------
✓ Standardized: Follows BaseAgent architecture with typed configuration
✓ Interoperable: Supports all 5 core protocols (A2A, A2P, ACP, ANP, MCP)
✓ Redeployable: Environment-based configuration, no hardcoded values
✓ Reusable: Clear interfaces, well-documented methods
✓ Atomic: Single responsibility - consensus building
✓ Composable: Can be combined with other agents in swarms
✓ Orchestratable: Async lifecycle methods for coordination
✓ Agnostic: No vendor/model/system dependencies

DOMAIN ALGORITHMS:
-----------------
- Weighted voting with confidence scoring
- Quorum checking (minimum participation)
- Conflict resolution with multi-factor scoring
- Proposal grouping and aggregation
- Consensus confidence calculation

USAGE:
------
    from library.agents.consensus_agent_v1 import (
        create_consensus_agent,
        ConsensusAgentConfig
    )

    # Create with environment configuration
    agent = await create_consensus_agent()

    # Execute consensus calculation
    result = await agent.execute({
        "action": "calculate_consensus",
        "proposals": [...]
    })
"""

import os
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# Resource monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import base framework
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin

# Agent metadata
AGENT_TYPE = "consensus"
AGENT_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ["A2A", "A2P", "ACP", "ANP", "MCP"]


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ConsensusAgentConfig:
    """
    Configuration for Consensus Agent

    All parameters can be set via environment variables with prefix:
    CONSENSUS_*

    Example:
        export CONSENSUS_MIN_CONFIDENCE_THRESHOLD=0.7
        export CONSENSUS_QUORUM_PERCENTAGE=0.6
    """
    # Logging
    log_level: str = "INFO"

    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 80

    # Protocol flags
    enable_a2a: bool = True
    enable_a2p: bool = True
    enable_acp: bool = True
    enable_anp: bool = True
    enable_mcp: bool = True

    # Consensus parameters
    min_confidence_threshold: float = 0.6
    quorum_percentage: float = 0.5
    min_proposals_for_quorum: int = 2

    # Conflict resolution weights
    weight_confidence: float = 0.4
    weight_priority: float = 0.3
    weight_timestamp: float = 0.2
    weight_agent_reputation: float = 0.1

    # Performance
    enable_cache: bool = True
    cache_ttl_seconds: int = 300
    enable_metrics: bool = True

    @classmethod
    def from_environment(cls) -> "ConsensusAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            # Logging
            log_level=os.getenv("CONSENSUS_LOG_LEVEL", "INFO"),

            # Resource limits
            max_memory_mb=int(os.getenv("CONSENSUS_MAX_MEMORY_MB", "512")),
            max_cpu_percent=int(os.getenv("CONSENSUS_MAX_CPU_PERCENT", "80")),

            # Protocol flags
            enable_a2a=os.getenv("CONSENSUS_ENABLE_A2A", "true").lower() == "true",
            enable_a2p=os.getenv("CONSENSUS_ENABLE_A2P", "true").lower() == "true",
            enable_acp=os.getenv("CONSENSUS_ENABLE_ACP", "true").lower() == "true",
            enable_anp=os.getenv("CONSENSUS_ENABLE_ANP", "true").lower() == "true",
            enable_mcp=os.getenv("CONSENSUS_ENABLE_MCP", "true").lower() == "true",

            # Consensus parameters
            min_confidence_threshold=float(os.getenv("CONSENSUS_MIN_CONFIDENCE_THRESHOLD", "0.6")),
            quorum_percentage=float(os.getenv("CONSENSUS_QUORUM_PERCENTAGE", "0.5")),
            min_proposals_for_quorum=int(os.getenv("CONSENSUS_MIN_PROPOSALS_FOR_QUORUM", "2")),

            # Conflict resolution weights
            weight_confidence=float(os.getenv("CONSENSUS_WEIGHT_CONFIDENCE", "0.4")),
            weight_priority=float(os.getenv("CONSENSUS_WEIGHT_PRIORITY", "0.3")),
            weight_timestamp=float(os.getenv("CONSENSUS_WEIGHT_TIMESTAMP", "0.2")),
            weight_agent_reputation=float(os.getenv("CONSENSUS_WEIGHT_AGENT_REPUTATION", "0.1")),

            # Performance
            enable_cache=os.getenv("CONSENSUS_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("CONSENSUS_CACHE_TTL_SECONDS", "300")),
            enable_metrics=os.getenv("CONSENSUS_ENABLE_METRICS", "true").lower() == "true",
        )


class ConflictType(Enum):
    """Types of conflicts between proposals"""
    VEHICLE_ASSIGNMENT = "vehicle_assignment"
    TIMING_CONFLICT = "timing_conflict"
    ROUTE_OVERLAP = "route_overlap"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    GENERAL = "general"


@dataclass
class Proposal:
    """A proposal from an agent"""
    agent_id: str
    proposal_type: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    priority: int = 5


@dataclass
class ConsensusResult:
    """Result of consensus calculation"""
    decision: str
    chosen_proposal: Optional[Proposal]
    vote_counts: Dict[str, float]
    confidence: float
    participating_agents: List[str]
    conflicts_resolved: int


# ============================================================================
# RESOURCE MONITORING
# ============================================================================

class ResourceMonitor:
    """Monitor agent resource usage"""

    def __init__(self, max_memory_mb: int, max_cpu_percent: int):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None

    def check_resources(self) -> Dict[str, Any]:
        """Check if resource usage is within limits"""
        if not self.process:
            return {"status": "ok", "reason": "monitoring_unavailable"}

        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            if memory_mb > self.max_memory_mb:
                return {
                    "status": "error",
                    "reason": f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB"
                }

            if cpu_percent > self.max_cpu_percent:
                return {
                    "status": "warning",
                    "reason": f"CPU usage {cpu_percent:.1f}% exceeds limit {self.max_cpu_percent}%"
                }

            return {
                "status": "ok",
                "memory_mb": round(memory_mb, 2),
                "cpu_percent": round(cpu_percent, 2)
            }
        except Exception as e:
            return {"status": "error", "reason": f"Monitoring error: {str(e)}"}


# ============================================================================
# MAIN AGENT
# ============================================================================

class ConsensusAgent(BaseAgent, ProtocolMixin):
    """
    Consensus Agent - Architecturally Compliant v1.0

    Aggregates proposals from multiple agents and reaches consensus using
    weighted voting with confidence scoring.

    Architectural Principles:
    - Standardized: BaseAgent + ProtocolMixin architecture
    - Interoperable: Full protocol support (A2A, A2P, ACP, ANP, MCP)
    - Redeployable: Environment-based configuration
    - Reusable: Clear public API with type hints
    - Atomic: Single responsibility - consensus building
    - Composable: Works in swarms with other agents
    - Orchestratable: Async lifecycle support
    - Agnostic: No vendor dependencies
    """

    def __init__(self, agent_id: str, config: ConsensusAgentConfig):
        """
        Initialize Consensus Agent

        Args:
            agent_id: Unique identifier for this agent instance
            config: Agent configuration
        """
        # Initialize BaseAgent (must be first for ABC)
        super(BaseAgent, self).__init__()

        # Set required attributes
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = AGENT_VERSION

        # Initialize ProtocolMixin
        ProtocolMixin.__init__(self)

        # Store configuration
        self.typed_config = config

        # Resource monitoring
        self._resource_monitor = ResourceMonitor(
            max_memory_mb=config.max_memory_mb,
            max_cpu_percent=config.max_cpu_percent
        )

        # State
        self._initialized = False
        self._metrics = {
            "consensus_calculated": 0,
            "proposals_processed": 0,
            "conflicts_resolved": 0,
            "unanimous_decisions": 0,
            "total_execution_time_ms": 0.0
        }

        # Cache for consensus results
        self._consensus_cache: Dict[str, tuple] = {}

        # Status
        self._status = "created"

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize agent

        Returns:
            Initialization result with status
        """
        if self._initialized:
            return {"status": "already_initialized", "agent_id": self.agent_id}

        try:
            # Check resources
            resource_check = self._resource_monitor.check_resources()
            if resource_check["status"] == "error":
                return {
                    "status": "error",
                    "reason": resource_check["reason"],
                    "agent_id": self.agent_id
                }

            self._initialized = True
            self._status = "ready"

            return {
                "status": "initialized",
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "version": self.version,
                "protocols": SUPPORTED_PROTOCOLS,
                "config": {
                    "min_confidence_threshold": self.typed_config.min_confidence_threshold,
                    "quorum_percentage": self.typed_config.quorum_percentage,
                    "min_proposals_for_quorum": self.typed_config.min_proposals_for_quorum
                }
            }

        except Exception as e:
            self._status = "error"
            return {
                "status": "error",
                "reason": f"Initialization failed: {str(e)}",
                "agent_id": self.agent_id
            }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute consensus task

        Args:
            input_data: Task with 'action' and parameters
                - action: "gather_proposals" | "calculate_consensus" | "resolve_conflicts"
                - Additional parameters based on action

        Returns:
            Execution result
        """
        start_time = time.time()

        if not self._initialized:
            return {
                "success": False,
                "error": "Agent not initialized",
                "agent_id": self.agent_id
            }

        # Check resources
        resource_check = self._resource_monitor.check_resources()
        if resource_check["status"] == "error":
            return {
                "success": False,
                "error": resource_check["reason"],
                "agent_id": self.agent_id
            }

        try:
            action = input_data.get("action")

            if action == "gather_proposals":
                result = await self._handle_gather_proposals(input_data)
            elif action == "calculate_consensus":
                result = await self._handle_consensus_calculation(input_data)
            elif action == "resolve_conflicts":
                result = await self._handle_conflict_resolution(input_data)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

            # Update metrics
            if self.typed_config.enable_metrics:
                execution_time_ms = (time.time() - start_time) * 1000
                self._metrics["total_execution_time_ms"] += execution_time_ms
                result["execution_time_ms"] = round(execution_time_ms, 2)

            result["agent_id"] = self.agent_id
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "agent_id": self.agent_id
            }

    async def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown agent gracefully

        Returns:
            Shutdown result with final metrics
        """
        try:
            # Clear cache
            self._consensus_cache.clear()

            self._initialized = False
            self._status = "shutdown"

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": self._metrics.copy()
            }

        except Exception as e:
            return {
                "status": "error",
                "reason": f"Shutdown failed: {str(e)}",
                "agent_id": self.agent_id
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health

        Returns:
            Health status with resource metrics
        """
        resource_check = self._resource_monitor.check_resources()

        return {
            "status": self._status,
            "initialized": self._initialized,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "version": self.version,
            "resources": resource_check,
            "metrics": self._metrics.copy() if self.typed_config.enable_metrics else {},
            "cache_size": len(self._consensus_cache),
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # BASEAGENT ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    async def _configure_data_sources(self):
        """Configure data sources - not required for consensus"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - consensus doesn't need external data"""
        return {}

    async def _execute_logic(
        self,
        input_data: Dict[str, Any],
        fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core execution logic - delegates to execute() method"""
        return await self.execute(input_data)

    # ========================================================================
    # DOMAIN METHODS - Consensus Building
    # ========================================================================

    def gather_proposals(
        self,
        agents: List[Dict[str, Any]],
        decision_context: Dict[str, Any]
    ) -> List[Proposal]:
        """
        Gather proposals from multiple agents

        Args:
            agents: List of agent dictionaries with their proposals
            decision_context: Context for the decision being made

        Returns:
            List of Proposal objects
        """
        proposals = []

        for agent_data in agents:
            agent_id = agent_data.get("agent_id", "unknown")
            proposal_data = agent_data.get("proposal", {})
            confidence = agent_data.get("confidence", 0.5)
            priority = agent_data.get("priority", 5)

            proposal = Proposal(
                agent_id=agent_id,
                proposal_type=proposal_data.get("type", "general"),
                data=proposal_data,
                confidence=confidence,
                timestamp=datetime.now(),
                priority=priority
            )

            proposals.append(proposal)

        self._metrics["proposals_processed"] += len(proposals)

        return proposals

    def calculate_consensus(
        self,
        proposals: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> ConsensusResult:
        """
        Calculate consensus from multiple proposals using weighted voting

        Args:
            proposals: List of proposal dictionaries
            weights: Optional custom weights for agents

        Returns:
            ConsensusResult with decision
        """
        if not proposals:
            return ConsensusResult(
                decision="no_proposals",
                chosen_proposal=None,
                vote_counts={},
                confidence=0.0,
                participating_agents=[],
                conflicts_resolved=0
            )

        # Convert dicts to Proposal objects
        proposal_objects = [self._dict_to_proposal(p) for p in proposals]

        # Check for quorum
        if not self._has_quorum(proposal_objects):
            return ConsensusResult(
                decision="no_quorum",
                chosen_proposal=None,
                vote_counts={},
                confidence=0.0,
                participating_agents=[p.agent_id for p in proposal_objects],
                conflicts_resolved=0
            )

        # Group proposals by decision option
        proposal_groups = self._group_proposals(proposal_objects)

        # Calculate weighted votes for each option
        vote_counts = {}

        for option, option_proposals in proposal_groups.items():
            total_weight = 0.0

            for proposal in option_proposals:
                # Weight = confidence * priority_factor
                priority_factor = proposal.priority / 10.0  # Normalize priority
                weight = proposal.confidence * priority_factor

                # Apply custom agent weights if provided
                if weights and proposal.agent_id in weights:
                    weight *= weights[proposal.agent_id]

                total_weight += weight

            vote_counts[option] = total_weight

        # Determine winner
        if not vote_counts:
            return ConsensusResult(
                decision="no_valid_votes",
                chosen_proposal=None,
                vote_counts={},
                confidence=0.0,
                participating_agents=[p.agent_id for p in proposal_objects],
                conflicts_resolved=0
            )

        winning_option = max(vote_counts, key=vote_counts.get)
        winning_proposals = proposal_groups[winning_option]

        # Calculate consensus confidence
        total_votes = sum(vote_counts.values())
        winning_percentage = vote_counts[winning_option] / total_votes if total_votes > 0 else 0
        avg_proposal_confidence = sum(p.confidence for p in winning_proposals) / len(winning_proposals)

        consensus_confidence = (winning_percentage + avg_proposal_confidence) / 2

        # Check if consensus is strong enough
        if consensus_confidence < self.typed_config.min_confidence_threshold:
            decision = "weak_consensus"
        else:
            decision = winning_option

        # Update metrics
        self._metrics["consensus_calculated"] += 1
        if len(proposal_groups) == 1:
            self._metrics["unanimous_decisions"] += 1

        return ConsensusResult(
            decision=decision,
            chosen_proposal=winning_proposals[0],
            vote_counts=vote_counts,
            confidence=consensus_confidence,
            participating_agents=[p.agent_id for p in proposal_objects],
            conflicts_resolved=len(proposal_groups) - 1
        )

    def resolve_conflicts(
        self,
        conflicting_proposals: List[Dict[str, Any]],
        conflict_type: str
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between proposals

        Args:
            conflicting_proposals: List of conflicting proposal dicts
            conflict_type: Type of conflict

        Returns:
            Resolution with chosen proposal
        """
        if not conflicting_proposals:
            return {
                "resolved": False,
                "reason": "No proposals provided"
            }

        # Convert to Proposal objects
        proposals = [self._dict_to_proposal(p) for p in conflicting_proposals]

        # Score each proposal based on resolution weights
        scored_proposals = []

        for proposal in proposals:
            score = 0.0

            # Confidence component
            score += proposal.confidence * self.typed_config.weight_confidence

            # Priority component
            priority_score = proposal.priority / 10.0
            score += priority_score * self.typed_config.weight_priority

            # Timestamp component (more recent = better)
            time_diff = (datetime.now() - proposal.timestamp).total_seconds()
            recency_score = max(0, 1.0 - (time_diff / 3600))  # Decay over 1 hour
            score += recency_score * self.typed_config.weight_timestamp

            # Agent reputation component (simplified - all agents have equal reputation here)
            score += 0.5 * self.typed_config.weight_agent_reputation

            scored_proposals.append((proposal, score))

        # Sort by score (descending)
        scored_proposals.sort(key=lambda x: x[1], reverse=True)

        winner = scored_proposals[0]

        self._metrics["conflicts_resolved"] += 1

        return {
            "resolved": True,
            "conflict_type": conflict_type,
            "chosen_proposal": self._proposal_to_dict(winner[0]),
            "resolution_score": round(winner[1], 3),
            "rejected_proposals": [self._proposal_to_dict(p[0]) for p in scored_proposals[1:]],
            "resolution_method": "weighted_scoring"
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _handle_gather_proposals(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle proposal gathering task"""
        agents = task.get("agents", [])
        decision_context = task.get("decision_context", {})

        proposals = self.gather_proposals(agents, decision_context)

        return {
            "success": True,
            "proposals": [self._proposal_to_dict(p) for p in proposals],
            "count": len(proposals)
        }

    async def _handle_consensus_calculation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle consensus calculation task"""
        proposals = task.get("proposals", [])
        weights = task.get("weights")

        result = self.calculate_consensus(proposals, weights)

        return {
            "success": True,
            "consensus": self._consensus_result_to_dict(result)
        }

    async def _handle_conflict_resolution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conflict resolution task"""
        conflicting_proposals = task.get("conflicting_proposals", [])
        conflict_type = task.get("conflict_type", "general")

        resolution = self.resolve_conflicts(conflicting_proposals, conflict_type)

        return {
            "success": True,
            "resolution": resolution
        }

    def _has_quorum(self, proposals: List[Proposal]) -> bool:
        """Check if we have enough proposals for quorum"""
        return len(proposals) >= self.typed_config.min_proposals_for_quorum

    def _group_proposals(self, proposals: List[Proposal]) -> Dict[str, List[Proposal]]:
        """Group proposals by their decision option"""
        groups = {}

        for proposal in proposals:
            # Use proposal type or data key as grouping
            option = proposal.data.get("option", proposal.proposal_type)

            if option not in groups:
                groups[option] = []

            groups[option].append(proposal)

        return groups

    def _dict_to_proposal(self, d: Dict[str, Any]) -> Proposal:
        """Convert dictionary to Proposal object"""
        timestamp = d.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return Proposal(
            agent_id=d.get("agent_id", "unknown"),
            proposal_type=d.get("proposal_type", "general"),
            data=d.get("data", {}),
            confidence=d.get("confidence", 0.5),
            timestamp=timestamp,
            priority=d.get("priority", 5)
        )

    def _proposal_to_dict(self, proposal: Proposal) -> Dict[str, Any]:
        """Convert Proposal to dictionary"""
        return {
            "agent_id": proposal.agent_id,
            "proposal_type": proposal.proposal_type,
            "data": proposal.data,
            "confidence": proposal.confidence,
            "timestamp": proposal.timestamp.isoformat(),
            "priority": proposal.priority
        }

    def _consensus_result_to_dict(self, result: ConsensusResult) -> Dict[str, Any]:
        """Convert ConsensusResult to dictionary"""
        return {
            "decision": result.decision,
            "chosen_proposal": self._proposal_to_dict(result.chosen_proposal) if result.chosen_proposal else None,
            "vote_counts": result.vote_counts,
            "confidence": round(result.confidence, 3),
            "participating_agents": result.participating_agents,
            "conflicts_resolved": result.conflicts_resolved,
            "unanimous": len(result.vote_counts) == 1 if result.vote_counts else False
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

async def create_consensus_agent(
    agent_id: str = None,
    config: ConsensusAgentConfig = None
) -> ConsensusAgent:
    """
    Factory function to create and initialize Consensus Agent

    Args:
        agent_id: Unique identifier (auto-generated if None)
        config: Agent configuration (uses environment if None)

    Returns:
        Initialized ConsensusAgent instance
    """
    if agent_id is None:
        agent_id = f"consensus_{int(time.time())}"

    if config is None:
        config = ConsensusAgentConfig.from_environment()

    agent = ConsensusAgent(agent_id=agent_id, config=config)
    await agent.initialize()

    return agent


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI interface for testing and demonstration"""
    import argparse

    parser = argparse.ArgumentParser(description="Consensus Agent v1.0")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    parser.add_argument("--agent-id", default="consensus_cli", help="Agent ID")

    args = parser.parse_args()

    # Create agent
    print(f"Creating Consensus Agent: {args.agent_id}")
    agent = await create_consensus_agent(agent_id=args.agent_id)

    if args.health_check:
        print("\nRunning health check...")
        health = await agent.health_check()
        print(f"Status: {health['status']}")
        print(f"Initialized: {health['initialized']}")
        print(f"Resources: {health['resources']}")
        print(f"Metrics: {health.get('metrics', {})}")

    if args.test:
        print("\nRunning test scenario...")

        # Test 1: Calculate consensus from multiple proposals
        print("\n1. Calculate consensus:")
        proposals = [
            {
                "agent_id": "agent_1",
                "proposal_type": "route_choice",
                "data": {"option": "route_a", "distance": 100},
                "confidence": 0.9,
                "priority": 8
            },
            {
                "agent_id": "agent_2",
                "proposal_type": "route_choice",
                "data": {"option": "route_a", "distance": 100},
                "confidence": 0.85,
                "priority": 7
            },
            {
                "agent_id": "agent_3",
                "proposal_type": "route_choice",
                "data": {"option": "route_b", "distance": 95},
                "confidence": 0.7,
                "priority": 6
            }
        ]

        result = await agent.execute({
            "action": "calculate_consensus",
            "proposals": proposals
        })

        print(f"Success: {result['success']}")
        if result['success']:
            consensus = result['consensus']
            print(f"Decision: {consensus['decision']}")
            print(f"Confidence: {consensus['confidence']:.3f}")
            print(f"Unanimous: {consensus['unanimous']}")
            print(f"Participating agents: {len(consensus['participating_agents'])}")
            print(f"Conflicts resolved: {consensus['conflicts_resolved']}")

        # Test 2: Resolve conflicts
        print("\n2. Resolve conflicts:")
        conflicting_proposals = [
            {
                "agent_id": "agent_1",
                "proposal_type": "vehicle_assignment",
                "data": {"vehicle": "v1", "route": "r1"},
                "confidence": 0.8,
                "priority": 7
            },
            {
                "agent_id": "agent_2",
                "proposal_type": "vehicle_assignment",
                "data": {"vehicle": "v1", "route": "r2"},
                "confidence": 0.75,
                "priority": 6
            }
        ]

        result = await agent.execute({
            "action": "resolve_conflicts",
            "conflicting_proposals": conflicting_proposals,
            "conflict_type": "vehicle_assignment"
        })

        print(f"Success: {result['success']}")
        if result['success']:
            resolution = result['resolution']
            print(f"Resolved: {resolution['resolved']}")
            print(f"Resolution score: {resolution.get('resolution_score', 'N/A')}")
            print(f"Chosen proposal: agent_{resolution['chosen_proposal']['agent_id']}")

        # Final health check
        print("\n3. Final health check:")
        health = await agent.health_check()
        print(f"Metrics: {health.get('metrics', {})}")

    # Shutdown
    print("\nShutting down agent...")
    shutdown_result = await agent.shutdown()
    print(f"Shutdown status: {shutdown_result['status']}")
    print(f"Final metrics: {shutdown_result.get('final_metrics', {})}")


if __name__ == "__main__":
    asyncio.run(main())
