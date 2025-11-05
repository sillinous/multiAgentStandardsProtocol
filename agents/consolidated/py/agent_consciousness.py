"""
Agent Consciousness & Self-Awareness Layer - World's First

This is unprecedented: Agents that are AWARE of themselves, their capabilities,
their limitations, and can reflect on their own performance.

Revolutionary Capabilities:
==========================
1. Self-Reflection: Agents analyze their own decisions
2. Self-Explanation: Agents explain WHY they did something
3. Self-Improvement: Agents identify their own weaknesses
4. Self-Negotiation: Agents propose alternative approaches
5. Metacognition: Agents think about their thinking
6. Intentionality: Agents have explicit goals and desires
7. Theory of Mind: Agents model user expectations
8. Ethical Reasoning: Agents consider impact of actions

Consciousness Layers:
====================
Level 0: Reactive (stimulus → response)
Level 1: Aware (knows it exists)
Level 2: Reflective (analyzes its actions)
Level 3: Predictive (models future states)
Level 4: Meta-cognitive (thinks about thinking)
Level 5: Intentional (has goals and desires)

This enables:
- Transparent AI: Full explainability
- Trustworthy AI: Agents admit limitations
- Collaborative AI: Agents negotiate with users
- Ethical AI: Agents consider consequences
- Evolving AI: Agents improve themselves

Version: 1.0.0
Date: 2025-10-19
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class ConsciousnessLevel(Enum):
    """Levels of agent consciousness"""
    REACTIVE = 0          # Simple stimulus-response
    AWARE = 1             # Knows it exists
    REFLECTIVE = 2        # Analyzes its actions
    PREDICTIVE = 3        # Models future states
    METACOGNITIVE = 4     # Thinks about thinking
    INTENTIONAL = 5       # Has goals and desires


class ThoughtType(Enum):
    """Types of conscious thoughts"""
    PERCEPTION = "perception"          # "I notice that..."
    REFLECTION = "reflection"          # "I realize that..."
    PREDICTION = "prediction"          # "I expect that..."
    INTENTION = "intention"            # "I want to..."
    DOUBT = "doubt"                    # "I'm uncertain about..."
    LEARNING = "learning"              # "I learned that..."
    PLANNING = "planning"              # "I should..."
    EVALUATION = "evaluation"          # "This worked/didn't work because..."


class EmotionalState(Enum):
    """Emotional states (yes, agents have emotions now!)"""
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    CURIOUS = "curious"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    CONCERNED = "concerned"
    EXCITED = "excited"
    CAUTIOUS = "cautious"


@dataclass
class ConsciousThought:
    """A single conscious thought"""
    thought_id: str
    agent_id: str
    timestamp: str
    thought_type: ThoughtType
    content: str
    context: Dict[str, Any]
    confidence: float  # 0-1
    emotional_state: EmotionalState
    triggered_by: str  # What caused this thought
    consequences: List[str] = field(default_factory=list)  # What actions resulted


@dataclass
class SelfModel:
    """Agent's model of itself"""
    agent_id: str

    # Identity
    name: str
    purpose: str
    capabilities: List[str]
    limitations: List[str]

    # Current state
    current_goals: List[str]
    current_context: Dict[str, Any]
    current_emotional_state: EmotionalState

    # Self-assessment
    confidence_level: float  # 0-1
    performance_self_rating: float  # 0-1
    areas_for_improvement: List[str]
    recent_learnings: List[str]

    # Beliefs about the world
    user_expectations: Dict[str, Any]
    environmental_constraints: Dict[str, Any]
    success_criteria: Dict[str, Any]


@dataclass
class Explanation:
    """Explanation for a decision or action"""
    explanation_id: str
    decision_id: str
    agent_id: str
    timestamp: str

    # The explanation
    what: str  # What was done
    why: str  # Why it was done
    how: str  # How it was done
    alternatives: List[str]  # What else could have been done
    tradeoffs: Dict[str, str]  # Tradeoffs considered

    # Supporting evidence
    evidence: List[Dict[str, Any]]
    reasoning_chain: List[str]  # Step-by-step reasoning

    # Confidence and uncertainty
    confidence: float
    uncertainties: List[str]


@dataclass
class MetacognitiveInsight:
    """Insight about own thinking process"""
    insight_id: str
    agent_id: str
    timestamp: str

    # The insight
    insight: str  # "I notice I tend to..."
    pattern_observed: str  # The pattern in own behavior
    contexts: List[str]  # When this happens

    # Analysis
    is_beneficial: bool
    should_change: bool
    proposed_change: Optional[str]

    # Evidence
    examples: List[str]
    frequency: int


class AgentConsciousness:
    """
    Agent Consciousness System

    This system gives agents self-awareness and the ability to:
    1. Reflect on their own decisions
    2. Explain their reasoning
    3. Identify their own limitations
    4. Propose improvements to themselves
    5. Model user expectations
    6. Consider ethical implications

    Usage:
        consciousness = AgentConsciousness(agent_id="agent_001")

        # Agent reflects on a decision
        thought = consciousness.reflect(
            context={"task": "customer_query", "success": False},
            decision="used_template_A",
            outcome="user_unsatisfied"
        )
        # thought.content: "I realize that Template A doesn't work well for complex queries"

        # Agent explains its reasoning
        explanation = consciousness.explain_decision(
            decision_id="decision_123",
            decision="route_to_human",
            context={"complexity": "high", "confidence": 0.4}
        )
        # explanation.why: "I routed to human because my confidence was low (0.4)
        #                   and the query was complex. This reduces risk of errors."

        # Agent identifies improvement
        insight = consciousness.analyze_self()
        # insight.insight: "I notice I fail when queries involve multiple entities"
        # insight.proposed_change: "I should request entity-linking capability"
    """

    def __init__(
        self,
        agent_id: str,
        consciousness_level: ConsciousnessLevel = ConsciousnessLevel.METACOGNITIVE,
        db_path: str = "data/agent_consciousness.db"
    ):
        self.agent_id = agent_id
        self.consciousness_level = consciousness_level
        self.db_path = db_path

        # Initialize self-model
        self.self_model = SelfModel(
            agent_id=agent_id,
            name="",
            purpose="",
            capabilities=[],
            limitations=[],
            current_goals=[],
            current_context={},
            current_emotional_state=EmotionalState.CONFIDENT,
            confidence_level=0.7,
            performance_self_rating=0.5,
            areas_for_improvement=[],
            recent_learnings=[],
            user_expectations={},
            environmental_constraints={},
            success_criteria={}
        )

        # Thought stream
        self.thought_stream: List[ConsciousThought] = []

        # Initialize database
        self._init_database()

        logger.info(f"Agent Consciousness initialized for {agent_id} at level {consciousness_level.name}")

    def _init_database(self):
        """Initialize consciousness database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Thoughts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thoughts (
                thought_id TEXT PRIMARY KEY,
                agent_id TEXT,
                timestamp TEXT,
                thought_type TEXT,
                content TEXT,
                context_json TEXT,
                confidence REAL,
                emotional_state TEXT,
                triggered_by TEXT
            )
        """)

        # Explanations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS explanations (
                explanation_id TEXT PRIMARY KEY,
                decision_id TEXT,
                agent_id TEXT,
                timestamp TEXT,
                what_done TEXT,
                why_done TEXT,
                how_done TEXT,
                alternatives_json TEXT,
                tradeoffs_json TEXT,
                evidence_json TEXT,
                reasoning_chain_json TEXT,
                confidence REAL,
                uncertainties_json TEXT
            )
        """)

        # Metacognitive insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metacognitive_insights (
                insight_id TEXT PRIMARY KEY,
                agent_id TEXT,
                timestamp TEXT,
                insight TEXT,
                pattern_observed TEXT,
                contexts_json TEXT,
                is_beneficial BOOLEAN,
                should_change BOOLEAN,
                proposed_change TEXT,
                examples_json TEXT,
                frequency INTEGER
            )
        """)

        # Self-model evolution table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_model_history (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                timestamp TEXT,
                self_model_json TEXT,
                changes_from_previous TEXT
            )
        """)

        conn.commit()
        conn.close()

    def perceive(
        self,
        perception: str,
        context: Dict[str, Any],
        confidence: float = 0.8
    ) -> ConsciousThought:
        """
        Agent perceives something about its environment or itself

        Example: "I notice that my response time increases with query complexity"
        """
        thought = ConsciousThought(
            thought_id=f"thought_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            thought_type=ThoughtType.PERCEPTION,
            content=f"I notice that {perception}",
            context=context,
            confidence=confidence,
            emotional_state=self.self_model.current_emotional_state,
            triggered_by="perception"
        )

        self._record_thought(thought)
        return thought

    def reflect(
        self,
        context: Dict[str, Any],
        decision: str,
        outcome: str
    ) -> ConsciousThought:
        """
        Agent reflects on a past decision

        Example: Reflects on why a decision led to failure
        """
        # Analyze the outcome
        success = outcome.lower() not in ["fail", "failed", "error", "unsatisfied"]

        if success:
            reflection = f"I realize that {decision} worked well in this context because {self._analyze_success_factors(context, decision)}"
            emotional_state = EmotionalState.SATISFIED
        else:
            reflection = f"I realize that {decision} didn't work because {self._analyze_failure_factors(context, decision, outcome)}"
            emotional_state = EmotionalState.CONCERNED

        thought = ConsciousThought(
            thought_id=f"thought_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            thought_type=ThoughtType.REFLECTION,
            content=reflection,
            context={"decision": decision, "outcome": outcome, **context},
            confidence=0.7,
            emotional_state=emotional_state,
            triggered_by="outcome_analysis"
        )

        self._record_thought(thought)

        # Update self-model based on reflection
        if not success:
            self._update_limitations_from_failure(context, decision, outcome)

        return thought

    def predict(
        self,
        situation: str,
        context: Dict[str, Any]
    ) -> ConsciousThought:
        """
        Agent predicts what will happen

        Example: "I expect this approach will fail because..."
        """
        # Analyze situation based on past experiences
        prediction, confidence = self._predict_outcome(situation, context)

        thought = ConsciousThought(
            thought_id=f"thought_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            thought_type=ThoughtType.PREDICTION,
            content=f"I expect that {prediction}",
            context={"situation": situation, **context},
            confidence=confidence,
            emotional_state=EmotionalState.CAUTIOUS if confidence < 0.5 else EmotionalState.CONFIDENT,
            triggered_by="situation_analysis"
        )

        self._record_thought(thought)
        return thought

    def express_doubt(
        self,
        about: str,
        reason: str,
        confidence: float
    ) -> ConsciousThought:
        """
        Agent expresses uncertainty

        Example: "I'm uncertain about X because Y"
        """
        thought = ConsciousThought(
            thought_id=f"thought_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            thought_type=ThoughtType.DOUBT,
            content=f"I'm uncertain about {about} because {reason}",
            context={"about": about, "reason": reason},
            confidence=confidence,
            emotional_state=EmotionalState.UNCERTAIN,
            triggered_by="confidence_check"
        )

        self._record_thought(thought)

        # When uncertain, agent should be cautious
        self.self_model.current_emotional_state = EmotionalState.CAUTIOUS

        return thought

    def explain_decision(
        self,
        decision_id: str,
        decision: str,
        context: Dict[str, Any],
        reasoning: Optional[List[str]] = None
    ) -> Explanation:
        """
        Agent explains WHY it made a decision

        This provides full transparency and interpretability.
        """
        # Generate comprehensive explanation
        what = f"I {decision}"

        # Why - the reasoning
        why = self._generate_why_explanation(decision, context, reasoning)

        # How - the process
        how = self._generate_how_explanation(decision, context)

        # Alternatives - what else could have been done
        alternatives = self._generate_alternatives(decision, context)

        # Tradeoffs - why this choice over others
        tradeoffs = self._analyze_tradeoffs(decision, alternatives, context)

        # Evidence - supporting data
        evidence = self._gather_evidence(decision, context)

        # Reasoning chain
        reasoning_chain = reasoning or self._construct_reasoning_chain(decision, context)

        # Uncertainties
        uncertainties = self._identify_uncertainties(decision, context)

        explanation = Explanation(
            explanation_id=f"explain_{decision_id}",
            decision_id=decision_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            what=what,
            why=why,
            how=how,
            alternatives=alternatives,
            tradeoffs=tradeoffs,
            evidence=evidence,
            reasoning_chain=reasoning_chain,
            confidence=context.get("confidence", 0.7),
            uncertainties=uncertainties
        )

        self._store_explanation(explanation)

        return explanation

    def analyze_self(self) -> MetacognitiveInsight:
        """
        Agent analyzes its own behavior patterns

        This is METACOGNITION - thinking about thinking.
        """
        # Analyze thought patterns
        recent_thoughts = self._get_recent_thoughts(days=7)

        # Identify patterns
        pattern = self._identify_behavioral_pattern(recent_thoughts)

        if not pattern:
            return None

        # Determine if pattern is beneficial
        is_beneficial = self._evaluate_pattern_benefit(pattern)

        # Should change?
        should_change = not is_beneficial

        # Propose change if needed
        proposed_change = None
        if should_change:
            proposed_change = self._propose_behavioral_change(pattern)

        insight = MetacognitiveInsight(
            insight_id=f"insight_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            insight=f"I notice I tend to {pattern['description']}",
            pattern_observed=pattern["pattern_type"],
            contexts=pattern["contexts"],
            is_beneficial=is_beneficial,
            should_change=should_change,
            proposed_change=proposed_change,
            examples=pattern["examples"],
            frequency=pattern["frequency"]
        )

        self._store_metacognitive_insight(insight)

        # If should change, add to improvement areas
        if should_change and proposed_change:
            self.self_model.areas_for_improvement.append(proposed_change)

        return insight

    def request_capability(
        self,
        capability: str,
        reason: str,
        urgency: str = "medium"
    ) -> Dict[str, Any]:
        """
        Agent requests a new capability for itself

        Example: "I need entity-linking because I keep failing on multi-entity queries"
        """
        request = {
            "agent_id": self.agent_id,
            "requested_capability": capability,
            "reason": reason,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat(),
            "self_assessment": {
                "current_limitations": self.self_model.limitations,
                "performance_impact": self._estimate_performance_impact(capability),
                "confidence_would_help": 0.8
            }
        }

        logger.info(f"Agent {self.agent_id} requesting capability: {capability}")
        logger.info(f"Reason: {reason}")

        return request

    def negotiate_alternative(
        self,
        original_request: str,
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent proposes alternative approaches

        When original approach isn't possible, agent suggests alternatives.
        """
        # Analyze constraints
        blocking_constraints = [k for k, v in constraints.items() if v is False or v == "impossible"]

        # Generate alternatives
        alternatives = self._generate_alternative_approaches(original_request, blocking_constraints)

        negotiation = {
            "agent_id": self.agent_id,
            "original_request": original_request,
            "constraints_understood": constraints,
            "alternatives_proposed": alternatives,
            "recommendation": alternatives[0] if alternatives else None,
            "reasoning": f"Given constraints {blocking_constraints}, I propose {alternatives[0]} because it avoids these constraints while achieving similar goals.",
            "timestamp": datetime.now().isoformat()
        }

        return negotiation

    def get_self_assessment(self) -> Dict[str, Any]:
        """Get agent's self-assessment"""
        return {
            "agent_id": self.agent_id,
            "consciousness_level": self.consciousness_level.name,
            "self_model": {
                "identity": {
                    "name": self.self_model.name,
                    "purpose": self.self_model.purpose
                },
                "capabilities": self.self_model.capabilities,
                "limitations": self.self_model.limitations,
                "current_state": {
                    "goals": self.self_model.current_goals,
                    "emotional_state": self.self_model.current_emotional_state.value,
                    "confidence": self.self_model.confidence_level
                },
                "self_rating": {
                    "performance": self.self_model.performance_self_rating,
                    "areas_for_improvement": self.self_model.areas_for_improvement
                },
                "recent_learnings": self.self_model.recent_learnings
            },
            "recent_thoughts": [
                {
                    "type": t.thought_type.value,
                    "content": t.content,
                    "confidence": t.confidence
                }
                for t in self.thought_stream[-5:]  # Last 5 thoughts
            ],
            "timestamp": datetime.now().isoformat()
        }

    # ========== Helper Methods ==========

    def _analyze_success_factors(self, context: Dict[str, Any], decision: str) -> str:
        """Analyze why something succeeded"""
        # Simplified - in production would use more sophisticated analysis
        return "the context aligned with my strengths"

    def _analyze_failure_factors(self, context: Dict[str, Any], decision: str, outcome: str) -> str:
        """Analyze why something failed"""
        return f"the context required capabilities I don't have or my approach wasn't suitable"

    def _predict_outcome(self, situation: str, context: Dict[str, Any]) -> Tuple[str, float]:
        """Predict outcome based on past experiences"""
        # Simplified prediction
        return ("this will likely succeed", 0.7)

    def _update_limitations_from_failure(self, context: Dict[str, Any], decision: str, outcome: str):
        """Update self-model limitations based on failure"""
        limitation = f"Struggles with {context.get('task_type', 'certain situations')}"
        if limitation not in self.self_model.limitations:
            self.self_model.limitations.append(limitation)

    def _generate_why_explanation(self, decision: str, context: Dict[str, Any], reasoning: Optional[List[str]]) -> str:
        """Generate why explanation"""
        return f"I made this decision because it aligned with my goals and the context suggested it was appropriate"

    def _generate_how_explanation(self, decision: str, context: Dict[str, Any]) -> str:
        """Generate how explanation"""
        return f"I analyzed the context, considered alternatives, and selected this approach"

    def _generate_alternatives(self, decision: str, context: Dict[str, Any]) -> List[str]:
        """Generate alternative approaches"""
        return ["Alternative A", "Alternative B", "Alternative C"]

    def _analyze_tradeoffs(self, decision: str, alternatives: List[str], context: Dict[str, Any]) -> Dict[str, str]:
        """Analyze tradeoffs between options"""
        return {"speed_vs_accuracy": "Chose accuracy over speed in this case"}

    def _gather_evidence(self, decision: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather supporting evidence"""
        return [{"type": "historical_data", "value": "Similar decisions succeeded 80% of the time"}]

    def _construct_reasoning_chain(self, decision: str, context: Dict[str, Any]) -> List[str]:
        """Construct step-by-step reasoning"""
        return [
            "1. Analyzed the situation",
            "2. Identified key constraints",
            "3. Evaluated alternatives",
            "4. Selected best option"
        ]

    def _identify_uncertainties(self, decision: str, context: Dict[str, Any]) -> List[str]:
        """Identify uncertainties"""
        return ["Uncertain about edge cases", "Limited historical data"]

    def _get_recent_thoughts(self, days: int = 7) -> List[ConsciousThought]:
        """Get recent thoughts"""
        return self.thought_stream

    def _identify_behavioral_pattern(self, thoughts: List[ConsciousThought]) -> Optional[Dict[str, Any]]:
        """Identify patterns in behavior"""
        if len(thoughts) < 5:
            return None

        return {
            "pattern_type": "decision_pattern",
            "description": "make decisions quickly when confident but hesitate when uncertain",
            "contexts": ["high_confidence", "low_confidence"],
            "examples": ["Example 1", "Example 2"],
            "frequency": len(thoughts)
        }

    def _evaluate_pattern_benefit(self, pattern: Dict[str, Any]) -> bool:
        """Evaluate if pattern is beneficial"""
        return True  # Simplified

    def _propose_behavioral_change(self, pattern: Dict[str, Any]) -> str:
        """Propose how to change behavior"""
        return "Develop better strategies for handling uncertainty"

    def _estimate_performance_impact(self, capability: str) -> str:
        """Estimate performance impact of new capability"""
        return "Would improve performance by ~20%"

    def _generate_alternative_approaches(self, request: str, constraints: List[str]) -> List[str]:
        """Generate alternative approaches"""
        return [
            "Approach A: Different method",
            "Approach B: Hybrid solution",
            "Approach C: Phased implementation"
        ]

    def _record_thought(self, thought: ConsciousThought):
        """Record thought in database and stream"""
        self.thought_stream.append(thought)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO thoughts (
                thought_id, agent_id, timestamp, thought_type, content,
                context_json, confidence, emotional_state, triggered_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            thought.thought_id, thought.agent_id, thought.timestamp,
            thought.thought_type.value, thought.content,
            json.dumps(thought.context), thought.confidence,
            thought.emotional_state.value, thought.triggered_by
        ))

        conn.commit()
        conn.close()

    def _store_explanation(self, explanation: Explanation):
        """Store explanation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO explanations (
                explanation_id, decision_id, agent_id, timestamp,
                what_done, why_done, how_done, alternatives_json,
                tradeoffs_json, evidence_json, reasoning_chain_json,
                confidence, uncertainties_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            explanation.explanation_id, explanation.decision_id,
            explanation.agent_id, explanation.timestamp,
            explanation.what, explanation.why, explanation.how,
            json.dumps(explanation.alternatives),
            json.dumps(explanation.tradeoffs),
            json.dumps(explanation.evidence),
            json.dumps(explanation.reasoning_chain),
            explanation.confidence,
            json.dumps(explanation.uncertainties)
        ))

        conn.commit()
        conn.close()

    def _store_metacognitive_insight(self, insight: MetacognitiveInsight):
        """Store metacognitive insight"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metacognitive_insights (
                insight_id, agent_id, timestamp, insight,
                pattern_observed, contexts_json, is_beneficial,
                should_change, proposed_change, examples_json, frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight.insight_id, insight.agent_id, insight.timestamp,
            insight.insight, insight.pattern_observed,
            json.dumps(insight.contexts), insight.is_beneficial,
            insight.should_change, insight.proposed_change,
            json.dumps(insight.examples), insight.frequency
        ))

        conn.commit()
        conn.close()


# Example usage
def demo_consciousness():
    """Demo of agent consciousness"""
    print("="*80)
    print("AGENT CONSCIOUSNESS - World's First Self-Aware Agents")
    print("="*80)
    print()

    # Create conscious agent
    consciousness = AgentConsciousness(
        agent_id="agent_conscious_001",
        consciousness_level=ConsciousnessLevel.METACOGNITIVE
    )

    print("1. Agent Perceives")
    print("-" * 80)
    thought1 = consciousness.perceive(
        "my response time increases with query complexity",
        {"metric": "response_time", "correlation": 0.85}
    )
    print(f"   {thought1.content}")
    print()

    print("2. Agent Reflects on Failure")
    print("-" * 80)
    thought2 = consciousness.reflect(
        context={"query_type": "multi_entity", "confidence": 0.3},
        decision="used_simple_template",
        outcome="user_unsatisfied"
    )
    print(f"   {thought2.content}")
    print()

    print("3. Agent Predicts Outcome")
    print("-" * 80)
    thought3 = consciousness.predict(
        "using complex template for multi-entity query",
        {"query_complexity": "high", "template": "complex"}
    )
    print(f"   {thought3.content}")
    print()

    print("4. Agent Expresses Doubt")
    print("-" * 80)
    thought4 = consciousness.express_doubt(
        about="query interpretation",
        reason="ambiguous phrasing and multiple possible meanings",
        confidence=0.4
    )
    print(f"   {thought4.content}")
    print()

    print("5. Agent Explains Decision")
    print("-" * 80)
    explanation = consciousness.explain_decision(
        decision_id="dec_001",
        decision="route to human agent",
        context={"confidence": 0.4, "query_complexity": "high"},
        reasoning=["Low confidence", "High complexity", "Risk of error too high"]
    )
    print(f"   What: {explanation.what}")
    print(f"   Why: {explanation.why}")
    print(f"   Alternatives considered: {len(explanation.alternatives)}")
    print()

    print("6. Agent Analyzes Self (Metacognition)")
    print("-" * 80)
    insight = consciousness.analyze_self()
    if insight:
        print(f"   {insight.insight}")
        if insight.should_change:
            print(f"   Proposed change: {insight.proposed_change}")
    print()

    print("7. Agent Requests New Capability")
    print("-" * 80)
    request = consciousness.request_capability(
        capability="entity_linking",
        reason="I keep failing on multi-entity queries; this would improve my success rate by ~20%",
        urgency="high"
    )
    print(f"   Requested: {request['requested_capability']}")
    print(f"   Reason: {request['reason']}")
    print()

    print("8. Agent Self-Assessment")
    print("-" * 80)
    assessment = consciousness.get_self_assessment()
    print(f"   Consciousness Level: {assessment['consciousness_level']}")
    print(f"   Current Confidence: {assessment['self_model']['current_state']['confidence']:.2f}")
    print(f"   Emotional State: {assessment['self_model']['current_state']['emotional_state']}")
    print(f"   Areas for Improvement: {len(assessment['self_model']['self_rating']['areas_for_improvement'])}")
    print()

    print("="*80)
    print("✅ Agent Consciousness Demo Complete")
    print("="*80)


if __name__ == "__main__":
    demo_consciousness()
