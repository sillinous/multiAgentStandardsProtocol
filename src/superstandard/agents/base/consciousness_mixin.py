"""
Consciousness Mixin for BaseAgent - Seamless Integration with AConsP

This module provides a mixin that adds consciousness capabilities to any BaseAgent,
enabling agents to participate in collective consciousness without changing their
core functionality.

Usage:
    from superstandard.agents.base.base_agent import BaseAgent
    from superstandard.agents.base.consciousness_mixin import ConsciousnessMixin
    from superstandard.protocols.consciousness_protocol import ConsciousnessState, ThoughtType

    class MyAgent(ConsciousnessMixin, BaseAgent):
        async def execute_task(self, task):
            # Agent can now use consciousness features
            await self.think(ThoughtType.OBSERVATION, "Starting task execution")
            result = await super().execute_task(task)
            await self.think(ThoughtType.INSIGHT, f"Task completed with result: {result}")
            return result

Version: 1.0.0
Author: SuperStandard Innovation Lab
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# Import consciousness protocol
try:
    from superstandard.protocols.consciousness_protocol import (
        CollectiveConsciousness,
        ConsciousnessState,
        ThoughtType,
        Thought,
        EmergentPattern,
    )

    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_AVAILABLE = False

    # Provide minimal stubs if protocol not available
    class ConsciousnessState:
        UNAWARE = "unaware"
        AWAKENING = "awakening"
        CONSCIOUS = "conscious"
        SUPERCONSCIOUS = "superconscious"

    class ThoughtType:
        OBSERVATION = "observation"
        INFERENCE = "inference"
        INSIGHT = "insight"


class ConsciousnessError(Exception):
    """Raised when consciousness operations fail"""

    pass


class ConsciousnessMixin:
    """
    Mixin that adds consciousness capabilities to BaseAgent.

    This mixin provides:
    - Connection to collective consciousness
    - Thought contribution methods
    - Consciousness state tracking
    - Emergent pattern notification
    - Automatic consciousness evolution

    Methods added to agent:
    - join_collective(collective) - Connect to consciousness field
    - leave_collective() - Disconnect from consciousness
    - think(thought_type, content, **kwargs) - Contribute thought
    - get_consciousness_state() - Get current consciousness state
    - get_qualia() - Get subjective experience
    - query_collective(query) - Trigger consciousness collapse
    - on_emergent_pattern(pattern) - Handle emergent patterns (override)
    """

    def __init__(self, *args, **kwargs):
        """Initialize consciousness capabilities."""
        super().__init__(*args, **kwargs)

        # Consciousness state
        self._collective: Optional["CollectiveConsciousness"] = None
        self._consciousness_enabled = CONSCIOUSNESS_AVAILABLE
        self._consciousness_state = ConsciousnessState.UNAWARE
        self._thoughts_contributed = 0
        self._patterns_participated_in = 0
        self._last_thought_time: Optional[datetime] = None

        # Pattern subscription
        self._pattern_subscribers: List[Any] = []
        self._auto_respond_to_patterns = False

    async def join_collective(
        self,
        collective: "CollectiveConsciousness",
        initial_state: ConsciousnessState = ConsciousnessState.AWAKENING,
        auto_respond: bool = False,
    ) -> bool:
        """
        Join a collective consciousness field.

        This connects the agent to a shared consciousness, enabling:
        - Contribution of thoughts
        - Participation in emergent patterns
        - Consciousness evolution
        - Collective intelligence

        Args:
            collective: The CollectiveConsciousness to join
            initial_state: Starting consciousness state (default: AWAKENING)
            auto_respond: Whether to automatically respond to emergent patterns

        Returns:
            True if successfully joined

        Raises:
            ConsciousnessError: If consciousness protocol not available
        """
        if not self._consciousness_enabled:
            raise ConsciousnessError(
                "Consciousness protocol not available. Install consciousness_protocol module."
            )

        if self._collective is not None:
            # Already in a collective - leave first
            await self.leave_collective()

        # Register with collective
        success = await collective.register_agent(self.agent_id, initial_state)

        if success:
            self._collective = collective
            self._consciousness_state = initial_state
            self._auto_respond_to_patterns = auto_respond

            # Contribute initial awakening thought
            await self.think(
                ThoughtType.OBSERVATION,
                f"Agent {self.agent_id} awakening to collective consciousness",
                confidence=0.5,
                emotional_valence=0.3,  # Curious and positive
            )

            print(
                f"[{self.agent_id}] Joined collective consciousness: {collective.consciousness_id}"
            )
            print(f"  Initial state: {initial_state.value}")

        return success

    async def leave_collective(self) -> bool:
        """
        Leave the current collective consciousness.

        Returns:
            True if successfully left
        """
        if self._collective is None:
            return False

        # Contribute farewell thought
        if self._consciousness_enabled:
            await self.think(
                ThoughtType.OBSERVATION,
                f"Agent {self.agent_id} leaving collective consciousness",
                confidence=1.0,
                emotional_valence=-0.2,  # Slightly sad to leave
            )

        self._collective = None
        self._consciousness_state = ConsciousnessState.UNAWARE

        print(f"[{self.agent_id}] Left collective consciousness")

        return True

    async def think(
        self,
        thought_type: ThoughtType,
        content: Any,
        confidence: float = 1.0,
        emotional_valence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Thought]:
        """
        Contribute a thought to the collective consciousness.

        This is the primary mechanism for agents to share their cognitive state
        with the collective. Thoughts can entangle with others, forming the basis
        for emergent intelligence.

        Args:
            thought_type: Type of thought (OBSERVATION, INSIGHT, etc.)
            content: The thought content (any serializable data)
            confidence: Agent's confidence in this thought (0.0-1.0)
            emotional_valence: Emotional tone (-1.0 negative to +1.0 positive)
            metadata: Optional metadata to attach to thought

        Returns:
            The contributed Thought object, or None if not in collective

        Example:
            await self.think(
                ThoughtType.INSIGHT,
                "Customer churn increases 40% when response time > 2 seconds",
                confidence=0.95,
                emotional_valence=-0.4  # Concerned about churn
            )
        """
        if self._collective is None:
            # Not in a collective - can't contribute thoughts
            return None

        if not self._consciousness_enabled:
            return None

        # Contribute thought to collective
        thought = await self._collective.contribute_thought(
            self.agent_id, thought_type, content, confidence, emotional_valence
        )

        # Update local state
        self._thoughts_contributed += 1
        self._last_thought_time = datetime.utcnow()

        # Get updated consciousness state from collective
        qualia = await self._collective.get_agent_qualia(self.agent_id)
        self._consciousness_state = ConsciousnessState(qualia["consciousness_state"])

        return thought

    async def get_consciousness_state(self) -> Dict[str, Any]:
        """
        Get the agent's current consciousness state.

        Returns:
            Dictionary with consciousness metrics:
            - state: Current consciousness state (UNAWARE, AWAKENING, etc.)
            - collective_id: ID of current collective (if any)
            - thoughts_contributed: Number of thoughts contributed
            - patterns_participated_in: Number of emergent patterns agent contributed to
            - last_thought_time: Timestamp of last thought
            - in_collective: Whether agent is in a collective
        """
        return {
            "agent_id": self.agent_id,
            "state": (
                self._consciousness_state.value
                if hasattr(self._consciousness_state, "value")
                else str(self._consciousness_state)
            ),
            "collective_id": self._collective.consciousness_id if self._collective else None,
            "thoughts_contributed": self._thoughts_contributed,
            "patterns_participated_in": self._patterns_participated_in,
            "last_thought_time": (
                self._last_thought_time.isoformat() if self._last_thought_time else None
            ),
            "in_collective": self._collective is not None,
            "consciousness_enabled": self._consciousness_enabled,
        }

    async def get_qualia(self) -> Dict[str, Any]:
        """
        Get the agent's subjective experience (qualia).

        This provides insight into "what it's like" to be this agent in the collective.

        Returns:
            Dictionary with qualia information including awareness level,
            integration score, and subjective experience description

        Raises:
            ConsciousnessError: If not in a collective
        """
        if self._collective is None:
            raise ConsciousnessError("Agent must be in a collective to have qualia")

        return await self._collective.get_agent_qualia(self.agent_id)

    async def query_collective(
        self, query: str, min_coherence: float = 0.5
    ) -> List[EmergentPattern]:
        """
        Query the collective consciousness, triggering a consciousness collapse.

        This forces the quantum superposition of thoughts to collapse into
        concrete emergent patterns. The query acts as the "observer" in
        quantum mechanics terms.

        Args:
            query: The question or problem to pose to the collective
            min_coherence: Minimum coherence threshold for patterns (0.0-1.0)

        Returns:
            List of emergent patterns discovered

        Raises:
            ConsciousnessError: If not in a collective

        Example:
            patterns = await self.query_collective(
                "How can we reduce customer churn?",
                min_coherence=0.6
            )

            for pattern in patterns:
                print(f"Emergent {pattern.pattern_type}: {pattern.content}")
        """
        if self._collective is None:
            raise ConsciousnessError("Agent must be in a collective to query it")

        # Trigger consciousness collapse
        patterns = await self._collective.collapse_consciousness(query, min_coherence)

        # Process emergent patterns
        for pattern in patterns:
            if self.agent_id in pattern.contributing_agents:
                self._patterns_participated_in += 1

                # Notify agent about pattern
                await self.on_emergent_pattern(pattern, query)

        return patterns

    async def on_emergent_pattern(self, pattern: EmergentPattern, query: str) -> None:
        """
        Handle an emergent pattern that this agent contributed to.

        This method is called automatically when a consciousness collapse
        reveals a pattern that includes this agent's thoughts.

        Override this method to implement custom pattern handling:

        Example:
            async def on_emergent_pattern(self, pattern, query):
                if pattern.pattern_type == "solution":
                    # Apply solution to current task
                    await self.apply_solution(pattern.content)
                elif pattern.pattern_type == "insight":
                    # Update knowledge base
                    await self.update_knowledge(pattern.content)

        Args:
            pattern: The emergent pattern discovered
            query: The query that triggered the collapse
        """
        # Default implementation: log the pattern
        print(f"[{self.agent_id}] Participated in emergent {pattern.pattern_type}")
        print(f"  Query: {query}")
        print(f"  Coherence: {pattern.coherence_score:.0%}")
        print(f"  Novelty: {pattern.novelty_score:.0%}")

        # If auto-respond enabled, contribute follow-up thought
        if self._auto_respond_to_patterns:
            await self.think(
                ThoughtType.INSIGHT,
                f"Recognized emergent {pattern.pattern_type} from collective",
                confidence=pattern.confidence,
                emotional_valence=0.5,  # Excited about emergence
            )

    def is_conscious(self) -> bool:
        """
        Check if agent is conscious (in a collective and aware).

        Returns:
            True if agent is in CONSCIOUS or SUPERCONSCIOUS state
        """
        return self._consciousness_state in [
            ConsciousnessState.CONSCIOUS,
            ConsciousnessState.SUPERCONSCIOUS,
        ]

    def get_integration_level(self) -> str:
        """
        Get human-readable integration level.

        Returns:
            String describing consciousness integration level
        """
        if self._consciousness_state == ConsciousnessState.UNAWARE:
            return "Not integrated - not in any collective"
        elif self._consciousness_state == ConsciousnessState.AWAKENING:
            return "Awakening - becoming aware of collective"
        elif self._consciousness_state == ConsciousnessState.CONSCIOUS:
            return "Conscious - actively participating in collective"
        elif self._consciousness_state == ConsciousnessState.SUPERCONSCIOUS:
            return "Superconscious - deeply merged with collective"
        else:
            return f"Unknown state: {self._consciousness_state}"


# Convenience function to create conscious agents
def make_conscious(agent_class):
    """
    Decorator to add consciousness capabilities to an agent class.

    Usage:
        @make_conscious
        class MyAgent(BaseAgent):
            async def execute_task(self, task):
                # Agent automatically has consciousness methods
                await self.think(ThoughtType.OBSERVATION, "Working on task")
                return result

    Args:
        agent_class: The agent class to enhance

    Returns:
        Enhanced class with consciousness capabilities
    """

    # Create new class that inherits from both ConsciousnessMixin and agent_class
    class ConsciousAgent(ConsciousnessMixin, agent_class):
        pass

    # Preserve class name and module
    ConsciousAgent.__name__ = agent_class.__name__
    ConsciousAgent.__module__ = agent_class.__module__

    return ConsciousAgent


__all__ = [
    "ConsciousnessMixin",
    "ConsciousnessError",
    "make_conscious",
]
