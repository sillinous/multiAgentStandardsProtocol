"""
Explainable AI System for Agent Decision Transparency

Provides comprehensive explanations for agent decisions through:
- Decision reasoning chains
- Visual decision trees
- Confidence breakdowns
- Counterfactual analysis
- Natural language summaries
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json


# ============================================================================
# Decision Reasoning Models
# ============================================================================

class ReasoningFactorType(str, Enum):
    """Types of reasoning factors"""
    TECHNICAL_INDICATOR = "technical_indicator"
    SENTIMENT = "sentiment"
    PATTERN_RECOGNITION = "pattern_recognition"
    ENSEMBLE_CONSENSUS = "ensemble_consensus"
    REGIME_DETECTION = "regime_detection"
    RISK_ASSESSMENT = "risk_assessment"
    HISTORICAL_PERFORMANCE = "historical_performance"
    MARKET_CONDITIONS = "market_conditions"


@dataclass
class ReasoningFactor:
    """A single factor contributing to a decision"""

    factor_type: ReasoningFactorType
    name: str
    value: Any
    weight: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    influence: str  # "bullish", "bearish", "neutral"
    explanation: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'factor_type': self.factor_type.value,
            'name': self.name,
            'value': self.value,
            'weight': self.weight,
            'confidence': self.confidence,
            'influence': self.influence,
            'explanation': self.explanation,
            'supporting_data': self.supporting_data
        }


@dataclass
class AgentContribution:
    """Individual agent's contribution to ensemble decision"""

    agent_id: str
    agent_name: str
    specialist_type: str
    vote: str  # "buy", "sell", "hold"
    confidence: float
    reasoning: str
    personality_traits: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'specialist_type': self.specialist_type,
            'vote': self.vote,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'personality_traits': self.personality_traits
        }


@dataclass
class DecisionExplanation:
    """Comprehensive explanation of an agent decision"""

    decision_id: str
    timestamp: datetime
    symbol: str
    decision: str  # "buy", "sell", "hold"
    confidence: float

    # Reasoning breakdown
    reasoning_factors: List[ReasoningFactor] = field(default_factory=list)
    agent_contributions: List[AgentContribution] = field(default_factory=list)

    # Context
    market_context: Dict[str, Any] = field(default_factory=dict)
    portfolio_context: Dict[str, Any] = field(default_factory=dict)

    # Summary
    natural_language_summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    risks_identified: List[str] = field(default_factory=list)

    # Outcome (filled in after execution)
    executed: bool = False
    execution_price: Optional[float] = None
    outcome: Optional[str] = None  # "success", "failure"
    actual_return: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'decision': self.decision,
            'confidence': self.confidence,
            'reasoning_factors': [f.to_dict() for f in self.reasoning_factors],
            'agent_contributions': [a.to_dict() for a in self.agent_contributions],
            'market_context': self.market_context,
            'portfolio_context': self.portfolio_context,
            'natural_language_summary': self.natural_language_summary,
            'key_insights': self.key_insights,
            'risks_identified': self.risks_identified,
            'executed': self.executed,
            'execution_price': self.execution_price,
            'outcome': self.outcome,
            'actual_return': self.actual_return
        }


# ============================================================================
# Decision Explanation Engine
# ============================================================================

class DecisionExplanationEngine:
    """
    Engine for generating comprehensive decision explanations

    Features:
    - Tracks all reasoning factors
    - Generates natural language summaries
    - Creates visual decision trees
    - Provides counterfactual analysis

    Example:
        engine = DecisionExplanationEngine()

        # Create explanation for decision
        explanation = engine.explain_decision(
            ensemble=ensemble,
            decision=decision,
            symbol="AAPL",
            market_data=market_data
        )

        # Get natural language summary
        summary = engine.generate_summary(explanation)

        # Query the decision
        answer = engine.answer_question(
            explanation,
            "Why did you choose to buy?"
        )
    """

    def __init__(self):
        self.explanations: Dict[str, DecisionExplanation] = {}

    def explain_decision(
        self,
        decision_id: str,
        symbol: str,
        decision: str,
        confidence: float,
        reasoning_factors: List[ReasoningFactor],
        agent_contributions: List[AgentContribution],
        market_context: Optional[Dict[str, Any]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> DecisionExplanation:
        """
        Create comprehensive explanation for a decision

        Args:
            decision_id: Unique identifier
            symbol: Stock symbol
            decision: "buy", "sell", or "hold"
            confidence: Decision confidence (0-1)
            reasoning_factors: List of factors that influenced decision
            agent_contributions: Individual agent votes
            market_context: Market conditions at decision time
            portfolio_context: Portfolio state at decision time

        Returns:
            DecisionExplanation object
        """
        explanation = DecisionExplanation(
            decision_id=decision_id,
            timestamp=datetime.now(),
            symbol=symbol,
            decision=decision,
            confidence=confidence,
            reasoning_factors=reasoning_factors,
            agent_contributions=agent_contributions,
            market_context=market_context or {},
            portfolio_context=portfolio_context or {}
        )

        # Generate natural language summary
        explanation.natural_language_summary = self._generate_summary(explanation)

        # Extract key insights
        explanation.key_insights = self._extract_insights(explanation)

        # Identify risks
        explanation.risks_identified = self._identify_risks(explanation)

        # Store explanation
        self.explanations[decision_id] = explanation

        return explanation

    def _generate_summary(self, explanation: DecisionExplanation) -> str:
        """Generate natural language summary of decision"""

        action = explanation.decision.upper()
        symbol = explanation.symbol
        conf = explanation.confidence * 100

        # Find top factors
        top_factors = sorted(
            explanation.reasoning_factors,
            key=lambda f: f.weight * f.confidence,
            reverse=True
        )[:3]

        # Count agent votes
        votes = {}
        for contrib in explanation.agent_contributions:
            votes[contrib.vote] = votes.get(contrib.vote, 0) + 1

        summary = f"Decision: {action} {symbol} with {conf:.1f}% confidence.\n\n"

        # Explain top factors
        if top_factors:
            summary += "Key factors:\n"
            for i, factor in enumerate(top_factors, 1):
                influence_emoji = {
                    'bullish': '📈',
                    'bearish': '📉',
                    'neutral': '➡️'
                }.get(factor.influence, '❓')

                summary += (
                    f"{i}. {influence_emoji} {factor.name}: {factor.explanation} "
                    f"(weight: {factor.weight * 100:.0f}%)\n"
                )

        # Ensemble consensus
        if explanation.agent_contributions:
            total_agents = len(explanation.agent_contributions)
            consensus_vote = max(votes.items(), key=lambda x: x[1])[0]
            consensus_pct = (votes[consensus_vote] / total_agents) * 100

            summary += (
                f"\nEnsemble consensus: {votes[consensus_vote]}/{total_agents} "
                f"agents voted {consensus_vote.upper()} ({consensus_pct:.0f}% agreement)"
            )

        return summary

    def _extract_insights(self, explanation: DecisionExplanation) -> List[str]:
        """Extract key insights from decision"""
        insights = []

        # High confidence insights
        if explanation.confidence > 0.8:
            insights.append(
                f"Very high confidence decision ({explanation.confidence * 100:.1f}%) "
                "suggests strong conviction across multiple factors"
            )

        # Strong consensus
        if explanation.agent_contributions:
            votes = {}
            for contrib in explanation.agent_contributions:
                votes[contrib.vote] = votes.get(contrib.vote, 0) + 1

            total = len(explanation.agent_contributions)
            max_votes = max(votes.values())

            if max_votes / total > 0.8:
                insights.append(
                    f"{max_votes}/{total} agents agree - strong ensemble consensus"
                )

        # Dominant factor
        if explanation.reasoning_factors:
            top_factor = max(
                explanation.reasoning_factors,
                key=lambda f: f.weight * f.confidence
            )
            if top_factor.weight > 0.4:
                insights.append(
                    f"Primary driver: {top_factor.name} "
                    f"({top_factor.influence} signal)"
                )

        return insights

    def _identify_risks(self, explanation: DecisionExplanation) -> List[str]:
        """Identify potential risks in decision"""
        risks = []

        # Low confidence warning
        if explanation.confidence < 0.5:
            risks.append(
                f"⚠️ Low confidence ({explanation.confidence * 100:.1f}%) - "
                "consider reducing position size"
            )

        # Split decision
        if explanation.agent_contributions:
            votes = {}
            for contrib in explanation.agent_contributions:
                votes[contrib.vote] = votes.get(contrib.vote, 0) + 1

            if len(votes) > 1:
                total = len(explanation.agent_contributions)
                max_votes = max(votes.values())
                if max_votes / total < 0.6:
                    risks.append(
                        "⚠️ Split ensemble decision - agents disagree on best action"
                    )

        # Conflicting factors
        influences = [f.influence for f in explanation.reasoning_factors]
        if 'bullish' in influences and 'bearish' in influences:
            risks.append(
                "⚠️ Mixed signals - some factors bullish, others bearish"
            )

        return risks

    def get_explanation(self, decision_id: str) -> Optional[DecisionExplanation]:
        """Retrieve explanation by ID"""
        return self.explanations.get(decision_id)

    def update_outcome(
        self,
        decision_id: str,
        executed: bool,
        execution_price: Optional[float] = None,
        outcome: Optional[str] = None,
        actual_return: Optional[float] = None
    ):
        """Update explanation with execution outcome"""
        if decision_id in self.explanations:
            explanation = self.explanations[decision_id]
            explanation.executed = executed
            explanation.execution_price = execution_price
            explanation.outcome = outcome
            explanation.actual_return = actual_return

    def get_recent_explanations(
        self,
        limit: int = 10,
        symbol: Optional[str] = None
    ) -> List[DecisionExplanation]:
        """Get recent decision explanations"""
        explanations = list(self.explanations.values())

        if symbol:
            explanations = [e for e in explanations if e.symbol == symbol]

        # Sort by timestamp descending
        explanations.sort(key=lambda e: e.timestamp, reverse=True)

        return explanations[:limit]

    def answer_question(
        self,
        decision_id: str,
        question: str
    ) -> str:
        """
        Answer natural language questions about a decision

        Example questions:
        - "Why did you buy?"
        - "What were the top factors?"
        - "How confident were you?"
        - "Did all agents agree?"
        """
        explanation = self.get_explanation(decision_id)
        if not explanation:
            return "Decision not found."

        question_lower = question.lower()

        # Why questions
        if 'why' in question_lower:
            if 'buy' in question_lower or 'sell' in question_lower or 'hold' in question_lower:
                return explanation.natural_language_summary

        # Factor questions
        if 'factor' in question_lower or 'reason' in question_lower:
            top_factors = sorted(
                explanation.reasoning_factors,
                key=lambda f: f.weight * f.confidence,
                reverse=True
            )[:3]

            answer = "Top factors:\n"
            for i, factor in enumerate(top_factors, 1):
                answer += f"{i}. {factor.name}: {factor.explanation}\n"
            return answer

        # Confidence questions
        if 'confident' in question_lower or 'sure' in question_lower:
            return (
                f"Confidence: {explanation.confidence * 100:.1f}%\n"
                f"{explanation.natural_language_summary}"
            )

        # Agent agreement
        if 'agent' in question_lower and ('agree' in question_lower or 'consensus' in question_lower):
            votes = {}
            for contrib in explanation.agent_contributions:
                votes[contrib.vote] = votes.get(contrib.vote, 0) + 1

            total = len(explanation.agent_contributions)
            answer = f"Agent votes ({total} total):\n"
            for vote, count in votes.items():
                pct = (count / total) * 100
                answer += f"  {vote.upper()}: {count} ({pct:.0f}%)\n"
            return answer

        # Risk questions
        if 'risk' in question_lower:
            if explanation.risks_identified:
                return "Risks identified:\n" + "\n".join(explanation.risks_identified)
            return "No significant risks identified."

        # Default
        return explanation.natural_language_summary


# ============================================================================
# Decision Tree Visualizer
# ============================================================================

class DecisionTreeNode:
    """Node in decision tree visualization"""

    def __init__(
        self,
        label: str,
        value: Any,
        weight: float = 1.0,
        children: Optional[List['DecisionTreeNode']] = None
    ):
        self.label = label
        self.value = value
        self.weight = weight
        self.children = children or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for visualization"""
        return {
            'label': self.label,
            'value': str(self.value),
            'weight': self.weight,
            'children': [child.to_dict() for child in self.children]
        }


class DecisionTreeVisualizer:
    """
    Creates visual decision trees from explanations

    Generates hierarchical tree structure showing:
    - Decision at root
    - Major factors as branches
    - Sub-factors as leaves
    - Weights as branch thickness
    """

    def create_tree(self, explanation: DecisionExplanation) -> DecisionTreeNode:
        """Create decision tree from explanation"""

        # Root node: final decision
        root = DecisionTreeNode(
            label=f"{explanation.decision.upper()} {explanation.symbol}",
            value=f"Confidence: {explanation.confidence * 100:.1f}%",
            weight=explanation.confidence
        )

        # Group factors by type
        factors_by_type = {}
        for factor in explanation.reasoning_factors:
            factor_type = factor.factor_type.value
            if factor_type not in factors_by_type:
                factors_by_type[factor_type] = []
            factors_by_type[factor_type].append(factor)

        # Create branch for each factor type
        for factor_type, factors in factors_by_type.items():
            # Calculate total weight for this type
            total_weight = sum(f.weight for f in factors)

            type_node = DecisionTreeNode(
                label=factor_type.replace('_', ' ').title(),
                value=f"{len(factors)} factors",
                weight=total_weight / len(explanation.reasoning_factors)
            )

            # Add individual factors as children
            for factor in factors:
                factor_node = DecisionTreeNode(
                    label=factor.name,
                    value=factor.explanation[:50] + "..." if len(factor.explanation) > 50 else factor.explanation,
                    weight=factor.weight
                )
                type_node.children.append(factor_node)

            root.children.append(type_node)

        # Add ensemble consensus branch
        if explanation.agent_contributions:
            consensus_node = DecisionTreeNode(
                label="Ensemble Consensus",
                value=f"{len(explanation.agent_contributions)} agents",
                weight=0.15  # Fixed weight for consensus
            )

            # Group by vote
            votes = {}
            for contrib in explanation.agent_contributions:
                if contrib.vote not in votes:
                    votes[contrib.vote] = []
                votes[contrib.vote].append(contrib)

            # Add vote groups
            for vote, agents in votes.items():
                vote_node = DecisionTreeNode(
                    label=f"{vote.upper()}",
                    value=f"{len(agents)} agents",
                    weight=len(agents) / len(explanation.agent_contributions)
                )
                consensus_node.children.append(vote_node)

            root.children.append(consensus_node)

        return root
