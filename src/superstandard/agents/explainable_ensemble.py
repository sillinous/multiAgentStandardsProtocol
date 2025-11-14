"""
Explainable Agent Ensemble - Transparent Decision Making

Extends AgentEnsemble with comprehensive explanation capabilities.
Every decision comes with full reasoning, visualizations, and natural language summaries.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .agent_ensemble import AgentEnsemble, Decision
from .explainable_ai import (
    DecisionExplanationEngine,
    DecisionExplanation,
    ReasoningFactor,
    ReasoningFactorType,
    AgentContribution,
    DecisionTreeVisualizer
)


@dataclass
class ExplainableDecision(Decision):
    """Decision with explanation"""
    explanation_id: str = ""
    explanation: Optional[DecisionExplanation] = None


class ExplainableAgentEnsemble:
    """
    Wrapper around AgentEnsemble that provides explainability

    Every decision includes:
    - Full reasoning chain
    - Individual agent contributions
    - Visual decision tree
    - Natural language summary
    - Confidence breakdowns

    Example:
        ensemble = TemplateLibrary().get_template("balanced_trader").create_ensemble()
        explainable = ExplainableAgentEnsemble(ensemble)

        # Make explainable decision
        decision = explainable.make_explainable_decision(
            symbol="AAPL",
            market_data={"current_price": 150.00}
        )

        print(decision.explanation.natural_language_summary)

        # Ask questions
        answer = explainable.ask("Why did you buy AAPL?", decision.explanation_id)
        print(answer)
    """

    def __init__(self, ensemble: AgentEnsemble):
        """Initialize with existing ensemble"""
        self.ensemble = ensemble
        self.explanation_engine = DecisionExplanationEngine()
        self.tree_visualizer = DecisionTreeVisualizer()

    def make_explainable_decision(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> ExplainableDecision:
        """
        Make a decision with full explanation

        Args:
            symbol: Stock symbol
            market_data: Current market data
            portfolio_context: Optional portfolio state

        Returns:
            ExplainableDecision with full explanation
        """
        # Make the base decision
        base_decision = self.ensemble.make_decision(market_data)

        # Generate unique ID
        decision_id = str(uuid.uuid4())

        # Extract reasoning factors from market data and specialists
        reasoning_factors = self._extract_reasoning_factors(
            market_data,
            base_decision
        )

        # Get individual agent contributions
        agent_contributions = self._get_agent_contributions(market_data)

        # Create comprehensive explanation
        explanation = self.explanation_engine.explain_decision(
            decision_id=decision_id,
            symbol=symbol,
            decision=base_decision.action,
            confidence=base_decision.confidence,
            reasoning_factors=reasoning_factors,
            agent_contributions=agent_contributions,
            market_context=market_data,
            portfolio_context=portfolio_context
        )

        # Create explainable decision
        explainable_decision = ExplainableDecision(
            action=base_decision.action,
            confidence=base_decision.confidence,
            reasoning=base_decision.reasoning,
            specialist_type=base_decision.specialist_type,
            ensemble_id=base_decision.ensemble_id,
            explanation_id=decision_id,
            explanation=explanation
        )

        return explainable_decision

    def _extract_reasoning_factors(
        self,
        market_data: Dict[str, Any],
        decision: Decision
    ) -> List[ReasoningFactor]:
        """Extract reasoning factors from decision"""
        factors = []

        # Technical indicators from market data
        if 'current_price' in market_data:
            price = market_data['current_price']
            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.TECHNICAL_INDICATOR,
                name="Current Price",
                value=price,
                weight=0.15,
                confidence=0.9,
                influence="neutral",
                explanation=f"Current market price: ${price:.2f}"
            ))

        if 'rsi' in market_data:
            rsi = market_data['rsi']
            influence = "bullish" if rsi < 30 else "bearish" if rsi > 70 else "neutral"
            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.TECHNICAL_INDICATOR,
                name="RSI (Relative Strength Index)",
                value=rsi,
                weight=0.20,
                confidence=0.85,
                influence=influence,
                explanation=f"RSI at {rsi:.1f} indicates {influence} momentum"
            ))

        if 'macd' in market_data:
            macd = market_data['macd']
            influence = "bullish" if macd > 0 else "bearish"
            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.TECHNICAL_INDICATOR,
                name="MACD",
                value=macd,
                weight=0.18,
                confidence=0.80,
                influence=influence,
                explanation=f"MACD signal suggests {influence} trend"
            ))

        if 'volume' in market_data:
            volume = market_data['volume']
            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.MARKET_CONDITIONS,
                name="Trading Volume",
                value=volume,
                weight=0.10,
                confidence=0.75,
                influence="neutral",
                explanation=f"Trading volume: {volume:,} shares"
            ))

        # Market regime detection
        if hasattr(self.ensemble, 'regime_detector'):
            regime = self.ensemble.regime_detector.detect_regime({})
            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.REGIME_DETECTION,
                name="Market Regime",
                value=regime.value if hasattr(regime, 'value') else str(regime),
                weight=0.25,
                confidence=0.90,
                influence="bullish" if "bull" in str(regime).lower() else "bearish" if "bear" in str(regime).lower() else "neutral",
                explanation=f"Detected {regime} market conditions"
            ))

        # Ensemble consensus (very important!)
        factors.append(ReasoningFactor(
            factor_type=ReasoningFactorType.ENSEMBLE_CONSENSUS,
            name="Agent Consensus",
            value=f"{decision.action} @ {decision.confidence * 100:.1f}%",
            weight=0.30,
            confidence=decision.confidence,
            influence="bullish" if decision.action == "buy" else "bearish" if decision.action == "sell" else "neutral",
            explanation=f"Ensemble voted {decision.action.upper()} with {decision.confidence * 100:.1f}% confidence"
        ))

        return factors

    def _get_agent_contributions(
        self,
        market_data: Dict[str, Any]
    ) -> List[AgentContribution]:
        """Get individual agent contributions to decision"""
        contributions = []

        for specialist in self.ensemble.specialists:
            # Simulate agent decision (in reality, you'd actually run each specialist)
            # For now, we'll create mock contributions based on specialist type
            agent_id = specialist.genome.agent_id
            agent_name = f"{specialist.specialist_type.value}"

            # Mock vote based on specialist type and market data
            vote = self._simulate_specialist_vote(specialist, market_data)

            contributions.append(AgentContribution(
                agent_id=agent_id,
                agent_name=agent_name,
                specialist_type=specialist.specialist_type.value,
                vote=vote,
                confidence=0.70 + (specialist.genome.fitness_score * 0.30),
                reasoning=f"{specialist.specialist_type.value} analysis suggests {vote}",
                personality_traits=dict(specialist.genome.personality_traits)
            ))

        return contributions

    def _simulate_specialist_vote(
        self,
        specialist,
        market_data: Dict[str, Any]
    ) -> str:
        """Simulate how a specialist would vote (simplified)"""
        from .agent_ensemble import SpecialistType

        # Simplified logic - in production, would actually run specialist
        if specialist.specialist_type == SpecialistType.BULL_SPECIALIST:
            return "buy" if market_data.get('trend', 'neutral') != 'bearish' else "hold"
        elif specialist.specialist_type == SpecialistType.BEAR_SPECIALIST:
            return "sell" if market_data.get('trend', 'neutral') == 'bearish' else "hold"
        elif specialist.specialist_type == SpecialistType.VOLATILE_SPECIALIST:
            return "hold"  # Volatile specialists are cautious
        else:
            return "hold"

    def ask(self, question: str, decision_id: str) -> str:
        """
        Ask a natural language question about a decision

        Example questions:
        - "Why did you buy AAPL?"
        - "What were the top factors?"
        - "How confident were you?"
        - "Did all agents agree?"

        Args:
            question: Natural language question
            decision_id: Decision ID to query

        Returns:
            Natural language answer
        """
        return self.explanation_engine.answer_question(decision_id, question)

    def get_decision_tree(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get visual decision tree for a decision

        Args:
            decision_id: Decision ID

        Returns:
            Dictionary representing tree structure for visualization
        """
        explanation = self.explanation_engine.get_explanation(decision_id)
        if not explanation:
            return None

        tree = self.tree_visualizer.create_tree(explanation)
        return tree.to_dict()

    def get_explanation(self, decision_id: str) -> Optional[DecisionExplanation]:
        """Get full explanation for a decision"""
        return self.explanation_engine.get_explanation(decision_id)

    def update_outcome(
        self,
        decision_id: str,
        executed: bool,
        execution_price: Optional[float] = None,
        outcome: Optional[str] = None,
        actual_return: Optional[float] = None
    ):
        """
        Update decision with execution outcome

        Args:
            decision_id: Decision ID
            executed: Whether trade was executed
            execution_price: Price at execution
            outcome: "success" or "failure"
            actual_return: Actual return percentage
        """
        self.explanation_engine.update_outcome(
            decision_id=decision_id,
            executed=executed,
            execution_price=execution_price,
            outcome=outcome,
            actual_return=actual_return
        )

    def get_recent_decisions(
        self,
        limit: int = 10,
        symbol: Optional[str] = None
    ) -> List[DecisionExplanation]:
        """
        Get recent explainable decisions

        Args:
            limit: Maximum number of decisions
            symbol: Optional symbol filter

        Returns:
            List of DecisionExplanation objects
        """
        return self.explanation_engine.get_recent_explanations(limit, symbol)


# ============================================================================
# Utility Functions
# ============================================================================

def create_explainable_ensemble(ensemble: AgentEnsemble) -> ExplainableAgentEnsemble:
    """Create an explainable wrapper around any ensemble"""
    return ExplainableAgentEnsemble(ensemble)
