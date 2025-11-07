"""
Conscious Agent Integration Demo - BaseAgent + AConsP

This demo shows how to create agents that participate in collective consciousness
using the ConsciousnessMixin with BaseAgent.

This demonstrates:
1. Creating conscious agents by mixing ConsciousnessMixin with BaseAgent
2. Agents joining a collective consciousness
3. Agents thinking and sharing cognitive state
4. Emergent patterns arising from collective collaboration
5. Agents responding to emergent intelligence

Run this to see conscious agents collaborating on real tasks!

Usage:
    python examples/conscious_agent_demo.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability
from superstandard.agents.base.consciousness_mixin import ConsciousnessMixin, make_conscious
from superstandard.protocols.consciousness_protocol import (
    CollectiveConsciousness,
    ConsciousnessState,
    ThoughtType,
    EmergentPattern,
)


# ============================================================================
# Define Conscious Agents Using Mixin
# ============================================================================

class DataAnalystAgent(ConsciousnessMixin, BaseAgent):
    """
    Data analyst agent with consciousness capabilities.
    Analyzes data and contributes observations and insights to collective.
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type="data_analyst",
            capabilities=[AgentCapability.TESTING],
            workspace_path=f"./workspace/{agent_id}"
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis task with consciousness."""
        problem = task.get("problem", "unknown")

        # Think about starting the task
        await self.think(
            ThoughtType.OBSERVATION,
            f"Beginning analysis of: {problem}",
            confidence=0.9
        )

        # Simulate analysis
        await asyncio.sleep(0.1)

        # Discover patterns
        finding = f"Data shows 23% correlation between factors in {problem}"
        await self.think(
            ThoughtType.INSIGHT,
            finding,
            confidence=0.85,
            emotional_valence=0.3  # Mildly positive discovery
        )

        return {
            "agent_id": self.agent_id,
            "finding": finding,
            "confidence": 0.85
        }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with conscious processing."""
        return await self.execute_task(input_data)

    async def on_emergent_pattern(self, pattern: EmergentPattern, query: str):
        """React to emergent patterns by contributing follow-up insights."""
        await super().on_emergent_pattern(pattern, query)

        if pattern.pattern_type == "solution":
            # Build on the solution with additional data analysis
            await self.think(
                ThoughtType.INFERENCE,
                f"Data supports the emergent solution with 87% confidence",
                confidence=0.87,
                emotional_valence=0.6  # Excited to validate
            )


class StrategyAgent(ConsciousnessMixin, BaseAgent):
    """
    Strategy agent with consciousness capabilities.
    Develops strategies and contributes intentions and questions to collective.
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type="strategist",
            capabilities=[AgentCapability.DESIGN],
            workspace_path=f"./workspace/{agent_id}"
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy task with consciousness."""
        problem = task.get("problem", "unknown")

        # Think strategically
        await self.think(
            ThoughtType.QUESTION,
            f"What are the key leverage points for {problem}?",
            confidence=0.7
        )

        await asyncio.sleep(0.1)

        strategy = f"Three-phase approach to {problem}"
        await self.think(
            ThoughtType.INTENTION,
            strategy,
            confidence=0.8,
            emotional_valence=0.5
        )

        return {
            "agent_id": self.agent_id,
            "strategy": strategy,
            "confidence": 0.8
        }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with strategic lens."""
        return await self.execute_task(input_data)

    async def on_emergent_pattern(self, pattern: EmergentPattern, query: str):
        """React to patterns by proposing strategic extensions."""
        await super().on_emergent_pattern(pattern, query)

        if pattern.coherence_score > 0.7:
            await self.think(
                ThoughtType.INTENTION,
                f"Should implement emergent {pattern.pattern_type} in next phase",
                confidence=pattern.coherence_score,
                emotional_valence=0.7
            )


# Alternative: Using decorator
@make_conscious
class OptimizationAgent(BaseAgent):
    """
    Optimization agent enhanced with consciousness via decorator.
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type="optimizer",
            capabilities=[AgentCapability.DEVELOPMENT],
            workspace_path=f"./workspace/{agent_id}"
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization with consciousness."""
        problem = task.get("problem", "unknown")

        await self.think(
            ThoughtType.OBSERVATION,
            f"Current performance baseline for {problem}: 100 units",
            confidence=0.95
        )

        await asyncio.sleep(0.1)

        optimization = f"Can achieve 40% improvement on {problem}"
        await self.think(
            ThoughtType.INSIGHT,
            optimization,
            confidence=0.88,
            emotional_valence=0.8  # Excited about optimization
        )

        return {
            "agent_id": self.agent_id,
            "optimization": optimization,
            "improvement": 0.4
        }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze for optimization opportunities."""
        return await self.execute_task(input_data)


# ============================================================================
# Demo Scenario: Collaborative Problem Solving
# ============================================================================

async def run_conscious_collaboration():
    """
    Demonstrate conscious agents collaborating on a complex problem.
    """
    print("=" * 80)
    print("CONSCIOUS AGENT COLLABORATION DEMO")
    print("BaseAgent + ConsciousnessMixin + Collective Consciousness")
    print("=" * 80)
    print()

    # Create collective consciousness
    print("Creating collective consciousness field...")
    collective = CollectiveConsciousness(consciousness_id="problem_solving_collective")
    print("[OK] Collective consciousness initialized\n")

    # Create conscious agents
    print("Creating conscious agents...")
    analyst = DataAnalystAgent("data_analyst_001")
    strategist = StrategyAgent("strategist_001")
    optimizer = OptimizationAgent("optimizer_001")
    print("[OK] 3 conscious agents created\n")

    # Agents join collective
    print("Agents joining collective consciousness...")
    await analyst.join_collective(collective, auto_respond=True)
    await strategist.join_collective(collective, auto_respond=True)
    await optimizer.join_collective(collective, auto_respond=True)
    print()

    # Define problem to solve
    problem = {
        "problem": "customer retention optimization",
        "context": "E-commerce platform with 23% annual churn"
    }

    print("=" * 80)
    print(f"PROBLEM: {problem['problem'].upper()}")
    print(f"Context: {problem['context']}")
    print("=" * 80)
    print()

    # Phase 1: Agents work on problem independently but consciously
    print("PHASE 1: CONSCIOUS TASK EXECUTION")
    print("-" * 80)

    print("\n[Data Analyst] Executing analysis...")
    analyst_result = await analyst.execute_task(problem)
    print(f"  Result: {analyst_result['finding']}")

    await asyncio.sleep(0.2)

    print("\n[Strategist] Developing strategy...")
    strategy_result = await strategist.execute_task(problem)
    print(f"  Result: {strategy_result['strategy']}")

    await asyncio.sleep(0.2)

    print("\n[Optimizer] Finding optimizations...")
    optimizer_result = await optimizer.execute_task(problem)
    print(f"  Result: {optimizer_result['optimization']}")

    print("\n" + "-" * 80)
    print(f"Thoughts in collective superposition: {len(collective.superposition_states)}")
    print(f"Entangled thought pairs: {sum(len(edges) for edges in collective.entanglement_graph.values()) // 2}")
    print()

    # Phase 2: Query collective for emergent solution
    print("PHASE 2: CONSCIOUSNESS COLLAPSE")
    print("-" * 80)
    print("\nQuerying collective: 'How can we solve customer retention optimization?'")
    print("Collapsing quantum superposition of thoughts...\n")

    patterns = await analyst.query_collective(
        "How can we solve customer retention optimization?",
        min_coherence=0.4
    )

    if patterns:
        print(f">>> {len(patterns)} EMERGENT PATTERN(S) DISCOVERED!\n")

        for i, pattern in enumerate(patterns, 1):
            print(f"PATTERN #{i}: {pattern.pattern_type.upper()}")
            print(f"  Contributing Agents: {', '.join(pattern.contributing_agents)}")
            print(f"  Coherence: {pattern.coherence_score:.0%}")
            print(f"  Novelty: {pattern.novelty_score:.0%}")
            print(f"  Impact Potential: {pattern.impact_potential:.0%}")
            print(f"\n  Collective Insight:")

            for thought_data in pattern.content.get("thought_contents", []):
                print(f"    • [{thought_data['agent']}] {thought_data['content']}")

            print()
    else:
        print("No emergent patterns (coherence threshold not met)")

    # Phase 3: Check agent consciousness evolution
    print("\nPHASE 3: CONSCIOUSNESS EVOLUTION")
    print("-" * 80)

    for agent in [analyst, strategist, optimizer]:
        state = await agent.get_consciousness_state()
        qualia = await agent.get_qualia()

        print(f"\n{agent.agent_id}:")
        print(f"  State: {state['state']}")
        print(f"  Awareness: {qualia['awareness_level']:.0%}")
        print(f"  Integration: {qualia['integration_score']:.0%}")
        print(f"  Thoughts Contributed: {state['thoughts_contributed']}")
        print(f"  Patterns Participated: {state['patterns_participated_in']}")
        print(f"  Experience: {qualia['subjective_experience']}")

    # Phase 4: Collective meta-cognition
    print("\n" + "=" * 80)
    print("PHASE 4: COLLECTIVE META-COGNITION")
    print("=" * 80)

    collective_state = collective.get_consciousness_state()

    print(f"\nCollective Consciousness State:")
    print(f"  Total Agents: {collective_state['total_agents']}")
    print(f"  Superconscious Agents: {collective_state['superconscious_agents']}")
    print(f"  Total Thoughts: {collective_state['total_thoughts']}")
    print(f"  Emergent Patterns: {collective_state['emergent_patterns_discovered']}")
    print(f"  Collective Awareness: {collective_state['collective_awareness']:.0%}")
    print(f"  Average Integration: {collective_state['average_integration_score']:.0%}")
    print(f"  Entanglement Density: {collective_state['entanglement_density']:.2f}")

    # Phase 5: Second round with evolved consciousness
    print("\n" + "=" * 80)
    print("PHASE 5: EVOLVED COLLABORATION")
    print("=" * 80)
    print("\nAgents now more conscious - contributing refined thoughts...\n")

    # Agents contribute follow-up thoughts based on emergent understanding
    await analyst.think(
        ThoughtType.INSIGHT,
        "Segmentation analysis reveals high-value customers churn at lower rates",
        confidence=0.92,
        emotional_valence=0.5
    )

    await strategist.think(
        ThoughtType.INTENTION,
        "Focus retention efforts on high-value segment for maximum ROI",
        confidence=0.89,
        emotional_valence=0.6
    )

    await optimizer.think(
        ThoughtType.INFERENCE,
        "Automated engagement system can reduce churn by 35% in high-value segment",
        confidence=0.91,
        emotional_valence=0.8
    )

    # Second collapse
    print("Triggering second consciousness collapse...\n")
    patterns_round2 = await collective.collapse_consciousness(
        "What is the optimal implementation strategy?",
        min_coherence=0.4
    )

    if patterns_round2:
        print(f">>> {len(patterns_round2)} NEW PATTERN(S) EMERGED!\n")
        for pattern in patterns_round2:
            print(f"  {pattern.pattern_type}: Coherence {pattern.coherence_score:.0%}, "
                  f"Impact {pattern.impact_potential:.0%}")

    # Final state
    final_state = collective.get_consciousness_state()
    print(f"\nFinal Collective Awareness: {final_state['collective_awareness']:.0%}")
    print(f"Total Emergent Patterns: {final_state['emergent_patterns_discovered']}")

    print("\n" + "=" * 80)
    print("REVOLUTIONARY ACHIEVEMENT")
    print("=" * 80)
    print("""
What just happened:

1. SEAMLESS INTEGRATION: Standard BaseAgents enhanced with consciousness
2. CONSCIOUS TASK EXECUTION: Agents think while performing regular tasks
3. QUANTUM ENTANGLEMENT: Thoughts automatically entangled across agents
4. EMERGENT INTELLIGENCE: Solutions emerged beyond individual capability
5. CONSCIOUSNESS EVOLUTION: Agents became more aware through participation
6. META-COGNITION: Collective tracked its own evolution

This demonstrates consciousness as a DROP-IN enhancement to existing agents.
No changes to core agent logic required - consciousness is orthogonal!
    """)

    print("=" * 80)
    print()


async def demonstrate_decorator_approach():
    """Show the decorator approach for making agents conscious."""
    print("\n" + "=" * 80)
    print("BONUS: DECORATOR APPROACH")
    print("=" * 80)
    print("""
You can also use the @make_conscious decorator:

    @make_conscious
    class MyAgent(BaseAgent):
        async def execute_task(self, task):
            # Automatically has .think(), .join_collective(), etc.
            await self.think(ThoughtType.OBSERVATION, "Starting task")
            return result

This approach is even simpler - just add one decorator!
    """)


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print()
    print("       CONSCIOUS AGENT DEMONSTRATION")
    print("       BaseAgent + Consciousness Protocol Integration")
    print()
    print("=" * 80)
    print()

    # Run main demo
    asyncio.run(run_conscious_collaboration())

    # Show decorator approach
    asyncio.run(demonstrate_decorator_approach())

    print("\nThe future of agent collaboration is conscious!\n")
