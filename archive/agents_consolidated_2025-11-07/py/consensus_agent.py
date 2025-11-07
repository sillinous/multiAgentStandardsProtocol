"""
Consensus Agent for Mobility Routing Swarm

Aggregates proposals from multiple agents and reaches consensus using
vote aggregation with confidence weighting.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


class ConflictType(Enum):
    """Types of conflicts between proposals"""

    VEHICLE_ASSIGNMENT = "vehicle_assignment"
    TIMING_CONFLICT = "timing_conflict"
    ROUTE_OVERLAP = "route_overlap"
    CAPACITY_EXCEEDED = "capacity_exceeded"


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


class ConsensusAgent(BaseAgent):
    """
    Agent responsible for reaching consensus among multiple agents.
    Uses vote aggregation with confidence weighting.
    """

    def __init__(
        self,
        agent_id: str = "consensus_agent",
        workspace_path: str = "./autonomous-ecosystem/workspace",
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="consensus",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path,
        )

        # Configuration
        self.min_confidence_threshold = 0.6
        self.quorum_percentage = 0.5  # Need 50% of agents to participate
        self.conflict_resolution_weights = {
            "confidence": 0.4,
            "priority": 0.3,
            "timestamp": 0.2,
            "agent_reputation": 0.1,
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute consensus task

        Args:
            task: Task with 'action' and parameters

        Returns:
            Task execution result
        """
        action = task.get("action")

        if action == "gather_proposals":
            return await self._handle_gather_proposals(task)
        elif action == "calculate_consensus":
            return await self._handle_consensus_calculation(task)
        elif action == "resolve_conflicts":
            return await self._handle_conflict_resolution(task)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze consensus patterns and decision quality

        Args:
            input_data: Consensus data to analyze

        Returns:
            Analysis results with metrics
        """
        decisions = input_data.get("decisions", [])

        if not decisions:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_decisions": 0,
                "recommendations": ["No decisions to analyze"],
            }

        # Calculate metrics
        avg_confidence = sum(d.get("confidence", 0) for d in decisions) / len(decisions)
        unanimous = sum(1 for d in decisions if d.get("unanimous", False))
        conflicts = sum(d.get("conflicts_resolved", 0) for d in decisions)

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_decisions": len(decisions),
            "average_confidence": round(avg_confidence, 3),
            "unanimous_decisions": unanimous,
            "total_conflicts_resolved": conflicts,
            "consensus_quality": self._calculate_consensus_quality(
                avg_confidence, unanimous, len(decisions)
            ),
            "recommendations": self._generate_consensus_recommendations(
                avg_confidence, unanimous, conflicts
            ),
        }

        return analysis

    def gather_proposals(
        self, agents: List[Dict[str, Any]], decision_context: Dict[str, Any]
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
                priority=priority,
            )

            proposals.append(proposal)

        return proposals

    def calculate_consensus(
        self, proposals: List[Dict[str, Any]], weights: Optional[Dict[str, float]] = None
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
                conflicts_resolved=0,
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
                conflicts_resolved=0,
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
                conflicts_resolved=0,
            )

        winning_option = max(vote_counts, key=vote_counts.get)
        winning_proposals = proposal_groups[winning_option]

        # Calculate consensus confidence
        total_votes = sum(vote_counts.values())
        winning_percentage = vote_counts[winning_option] / total_votes if total_votes > 0 else 0
        avg_proposal_confidence = sum(p.confidence for p in winning_proposals) / len(
            winning_proposals
        )

        consensus_confidence = (winning_percentage + avg_proposal_confidence) / 2

        # Check if consensus is strong enough
        if consensus_confidence < self.min_confidence_threshold:
            return ConsensusResult(
                decision="weak_consensus",
                chosen_proposal=winning_proposals[0],
                vote_counts=vote_counts,
                confidence=consensus_confidence,
                participating_agents=[p.agent_id for p in proposal_objects],
                conflicts_resolved=0,
            )

        return ConsensusResult(
            decision=winning_option,
            chosen_proposal=winning_proposals[0],
            vote_counts=vote_counts,
            confidence=consensus_confidence,
            participating_agents=[p.agent_id for p in proposal_objects],
            conflicts_resolved=len(proposal_groups) - 1,
        )

    def resolve_conflicts(
        self, conflicting_proposals: List[Dict[str, Any]], conflict_type: str
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
            return {"resolved": False, "reason": "No proposals provided"}

        # Convert to Proposal objects
        proposals = [self._dict_to_proposal(p) for p in conflicting_proposals]

        # Score each proposal based on resolution weights
        scored_proposals = []

        for proposal in proposals:
            score = 0.0

            # Confidence component
            score += proposal.confidence * self.conflict_resolution_weights["confidence"]

            # Priority component
            priority_score = proposal.priority / 10.0
            score += priority_score * self.conflict_resolution_weights["priority"]

            # Timestamp component (more recent = better)
            time_diff = (datetime.now() - proposal.timestamp).total_seconds()
            recency_score = max(0, 1.0 - (time_diff / 3600))  # Decay over 1 hour
            score += recency_score * self.conflict_resolution_weights["timestamp"]

            # Agent reputation component (simplified - all agents have equal reputation here)
            score += 0.5 * self.conflict_resolution_weights["agent_reputation"]

            scored_proposals.append((proposal, score))

        # Sort by score (descending)
        scored_proposals.sort(key=lambda x: x[1], reverse=True)

        winner = scored_proposals[0]

        return {
            "resolved": True,
            "conflict_type": conflict_type,
            "chosen_proposal": self._proposal_to_dict(winner[0]),
            "resolution_score": round(winner[1], 3),
            "rejected_proposals": [self._proposal_to_dict(p[0]) for p in scored_proposals[1:]],
            "resolution_method": "weighted_scoring",
        }

    async def _handle_gather_proposals(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle proposal gathering task"""
        agents = task.get("agents", [])
        decision_context = task.get("decision_context", {})

        proposals = self.gather_proposals(agents, decision_context)

        return {
            "success": True,
            "proposals": [self._proposal_to_dict(p) for p in proposals],
            "count": len(proposals),
            "agent_id": self.agent_id,
        }

    async def _handle_consensus_calculation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle consensus calculation task"""
        proposals = task.get("proposals", [])
        weights = task.get("weights")

        result = self.calculate_consensus(proposals, weights)

        return {
            "success": True,
            "consensus": self._consensus_result_to_dict(result),
            "agent_id": self.agent_id,
        }

    async def _handle_conflict_resolution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conflict resolution task"""
        conflicting_proposals = task.get("conflicting_proposals", [])
        conflict_type = task.get("conflict_type", "general")

        resolution = self.resolve_conflicts(conflicting_proposals, conflict_type)
        resolution["agent_id"] = self.agent_id

        return {"success": True, "resolution": resolution}

    def _has_quorum(self, proposals: List[Proposal]) -> bool:
        """Check if we have enough proposals for quorum"""
        # Simplified: need at least 2 proposals
        return len(proposals) >= 2

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
            priority=d.get("priority", 5),
        )

    def _proposal_to_dict(self, proposal: Proposal) -> Dict[str, Any]:
        """Convert Proposal to dictionary"""
        return {
            "agent_id": proposal.agent_id,
            "proposal_type": proposal.proposal_type,
            "data": proposal.data,
            "confidence": proposal.confidence,
            "timestamp": proposal.timestamp.isoformat(),
            "priority": proposal.priority,
        }

    def _consensus_result_to_dict(self, result: ConsensusResult) -> Dict[str, Any]:
        """Convert ConsensusResult to dictionary"""
        return {
            "decision": result.decision,
            "chosen_proposal": (
                self._proposal_to_dict(result.chosen_proposal) if result.chosen_proposal else None
            ),
            "vote_counts": result.vote_counts,
            "confidence": round(result.confidence, 3),
            "participating_agents": result.participating_agents,
            "conflicts_resolved": result.conflicts_resolved,
            "unanimous": len(result.vote_counts) == 1 if result.vote_counts else False,
        }

    def _calculate_consensus_quality(
        self, avg_confidence: float, unanimous: int, total: int
    ) -> str:
        """Calculate overall consensus quality"""
        unanimous_rate = unanimous / total if total > 0 else 0

        if avg_confidence >= 0.8 and unanimous_rate >= 0.7:
            return "Excellent"
        elif avg_confidence >= 0.7 and unanimous_rate >= 0.5:
            return "Good"
        elif avg_confidence >= 0.6:
            return "Fair"
        else:
            return "Poor"

    def _generate_consensus_recommendations(
        self, avg_confidence: float, unanimous: int, conflicts: int
    ) -> List[str]:
        """Generate consensus recommendations"""
        recommendations = []

        if avg_confidence < 0.6:
            recommendations.append("Low confidence decisions - improve agent coordination")

        if conflicts > 5:
            recommendations.append(
                f"High conflict rate ({conflicts} conflicts) - review agent alignment"
            )

        if unanimous > 0:
            recommendations.append(f"{unanimous} unanimous decisions indicate good agent agreement")

        if avg_confidence >= 0.8:
            recommendations.append("Strong consensus achieved - system working well")

        if not recommendations:
            recommendations.append("Consensus system operating normally")

        return recommendations
