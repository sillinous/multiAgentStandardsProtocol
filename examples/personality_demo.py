"""
Personality System Demo - Create diverse agents and visualize personalities

This demo:
1. Creates agents with different personality archetypes
2. Registers them with ANP including personality data
3. Demonstrates personality-driven decision making
4. Shows team compatibility analysis
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from superstandard.agents.personality import PersonalityProfile, PersonalityManager
from superstandard.agents.personality_integration import (
    PersonalityANPIntegration,
    PersonalityTradingIntegration,
    PersonalityACPIntegration
)
from superstandard.protocols.anp_implementation import AgentNetworkRegistry, ANPRegistration


async def create_demo_agents():
    """Create diverse agents with different personalities"""

    # Initialize personality manager
    personality_manager = PersonalityManager()

    # Initialize ANP registry
    registry = AgentNetworkRegistry()
    await registry.start()

    print("=== Creating Diverse Agent Personalities ===\n")

    # Define demo agents with specific archetypes
    agent_configs = [
        {
            "agent_id": "alpha_trader",
            "agent_type": "trading",
            "archetype": "Innovator",
            "capabilities": ["trading", "market_analysis", "risk_assessment"]
        },
        {
            "agent_id": "beta_executor",
            "agent_type": "trading",
            "archetype": "Executor",
            "capabilities": ["trading", "order_execution", "portfolio_management"]
        },
        {
            "agent_id": "gamma_coordinator",
            "agent_type": "coordination",
            "archetype": "Collaborator",
            "capabilities": ["coordination", "task_management", "communication"]
        },
        {
            "agent_id": "delta_researcher",
            "agent_type": "analysis",
            "archetype": "Explorer",
            "capabilities": ["research", "data_analysis", "pattern_recognition"]
        },
        {
            "agent_id": "epsilon_specialist",
            "agent_type": "analysis",
            "archetype": "Specialist",
            "capabilities": ["technical_analysis", "quantitative_modeling"]
        },
        {
            "agent_id": "zeta_cautious",
            "agent_type": "trading",
            "archetype": "Cautious",
            "capabilities": ["risk_management", "compliance", "audit"]
        },
        {
            "agent_id": "eta_balanced",
            "agent_type": "general",
            "archetype": "Balanced",
            "capabilities": ["general_purpose", "multi_task", "adaptive"]
        }
    ]

    registered_agents = []

    for config in agent_configs:
        # Generate personality for archetype
        personality = PersonalityProfile.random(config["archetype"])
        personality_manager.register_personality(config["agent_id"], personality)

        print(f"\n{'='*60}")
        print(f"Agent: {config['agent_id']}")
        print(f"Type: {config['agent_type']}")
        print(f"Archetype: {personality.archetype}")
        print(f"\nPersonality Traits:")
        print(f"  Openness:          {personality.openness:.2f} (Innovation: {personality.get_modifier('innovation_capacity'):.2f})")
        print(f"  Conscientiousness: {personality.conscientiousness:.2f} (Reliability: {personality.get_modifier('execution_reliability'):.2f})")
        print(f"  Extraversion:      {personality.extraversion:.2f} (Collaboration: {personality.get_modifier('collaboration_bonus'):.2f})")
        print(f"  Agreeableness:     {personality.agreeableness:.2f}")
        print(f"  Neuroticism:       {personality.neuroticism:.2f} (Stress Resistance: {personality.get_modifier('stress_resistance'):.2f})")

        # Show personality-driven behaviors
        if config["agent_type"] == "trading":
            print(f"\nTrading Behavior:")
            print(f"  Position Size (base=1.0): {PersonalityTradingIntegration.calculate_position_size(1.0, personality):.2f}x")
            print(f"  Strategy Type: {PersonalityTradingIntegration.select_strategy_type(personality)}")
            print(f"  Holding Period: {PersonalityTradingIntegration.calculate_holding_period_bias(personality):.1f} hours")
            print(f"  Stop Loss (5% default): {PersonalityTradingIntegration.calculate_stop_loss(100, personality, 0.05):.2f}")

        if config["agent_type"] == "coordination":
            print(f"\nCoordination Style:")
            print(f"  Recommended Role: {PersonalityACPIntegration.recommend_role(personality)}")
            print(f"  Communication Frequency: Every {PersonalityACPIntegration.calculate_communication_frequency(personality):.0f} minutes")
            print(f"  Conflict Resolution: {PersonalityACPIntegration.conflict_resolution_style(personality)}")

        # Create ANP registration with personality
        registration_data = {
            "agent_id": config["agent_id"],
            "agent_type": config["agent_type"],
            "capabilities": config["capabilities"],
            "endpoints": {"api": f"http://localhost:8000/agents/{config['agent_id']}"},
            "metadata": {
                "personality": personality.to_dict(),
                "archetype": personality.archetype
            }
        }

        # Register with ANP
        registration = ANPRegistration(**registration_data)
        result = await registry.register_agent(registration)

        if result["success"]:
            print(f"\n✅ Registered with ANP")
            registered_agents.append(config["agent_id"])
        else:
            print(f"\n❌ Registration failed: {result.get('error')}")

    # Team Dynamics Analysis
    print(f"\n\n{'='*60}")
    print("=== TEAM DYNAMICS ANALYSIS ===")
    print(f"{'='*60}\n")

    dynamics = personality_manager.get_team_dynamics(registered_agents)

    print(f"Team Size: {dynamics['team_size']} agents")
    print(f"\nArchetype Distribution:")
    for archetype, count in dynamics['archetype_distribution'].items():
        print(f"  {archetype}: {count}")

    print(f"\nAverage Traits:")
    for trait, value in dynamics['average_traits'].items():
        print(f"  {trait.capitalize()}: {value:.2f}")

    print(f"\nTeam Strengths:")
    for strength in dynamics['team_strengths']:
        print(f"  ✅ {strength}")

    if dynamics['team_weaknesses']:
        print(f"\nTeam Weaknesses:")
        for weakness in dynamics['team_weaknesses']:
            print(f"  ⚠️  {weakness}")

    print(f"\nOverall Team Diversity: {dynamics['overall_diversity']:.2f}")
    print(f"Average Compatibility: {dynamics['average_compatibility']:.2f}")

    # Compatibility Matrix
    print(f"\n\n{'='*60}")
    print("=== AGENT COMPATIBILITY MATRIX ===")
    print(f"{'='*60}\n")

    for agent_id in registered_agents[:3]:  # Show top 3 for brevity
        compatible = personality_manager.find_compatible_agents(agent_id, min_compatibility=0.0, top_n=5)
        print(f"\n{agent_id} - Most Compatible Agents:")
        for partner_id, score in compatible:
            print(f"  {partner_id}: {score:.2f} compatibility")

    # Team Formation
    print(f"\n\n{'='*60}")
    print("=== OPTIMAL TEAM FORMATION ===")
    print(f"{'='*60}\n")

    # Get agents with personality data
    all_agents_data = []
    for agent_id in registered_agents:
        agent_info = registry.agents.get(agent_id)
        if agent_info:
            all_agents_data.append(agent_info.__dict__)

    # Form optimal trading team (3 agents, moderate diversity)
    trading_team = PersonalityACPIntegration.form_optimal_team(
        all_agents_data,
        team_size=3,
        desired_diversity=0.5
    )

    print("Optimal Trading Team (balanced diversity):")
    for agent_id in trading_team:
        personality = personality_manager.get_personality(agent_id)
        print(f"  {agent_id} ({personality.archetype})")

    # Form specialized team (high diversity)
    diverse_team = PersonalityACPIntegration.form_optimal_team(
        all_agents_data,
        team_size=4,
        desired_diversity=0.9
    )

    print("\nHighly Diverse Team (maximum variety):")
    for agent_id in diverse_team:
        personality = personality_manager.get_personality(agent_id)
        print(f"  {agent_id} ({personality.archetype})")

    # Performance Prediction
    print(f"\n\n{'='*60}")
    print("=== PERFORMANCE PREDICTIONS ===")
    print(f"{'='*60}\n")

    print("Predicted Performance in Different Scenarios:\n")

    scenarios = [
        ("High-Pressure Trading", ["stress_resistance", "execution_reliability"]),
        ("Creative Problem Solving", ["innovation_capacity", "learning_speed"]),
        ("Team Collaboration", ["collaboration_bonus", "leadership_tendency"]),
        ("Risk Management", ["stress_resistance", "execution_reliability"])
    ]

    for scenario_name, key_modifiers in scenarios:
        print(f"{scenario_name}:")
        scores = []
        for agent_id in registered_agents:
            personality = personality_manager.get_personality(agent_id)
            score = sum(personality.get_modifier(mod) for mod in key_modifiers) / len(key_modifiers)
            scores.append((agent_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        for rank, (agent_id, score) in enumerate(scores[:3], 1):
            print(f"  {rank}. {agent_id}: {score:.2f}")
        print()

    print(f"\n{'='*60}")
    print("✅ Demo Complete!")
    print(f"{'='*60}\n")
    print("🌐 View the personality dashboard at: http://localhost:8080/dashboard/personality")
    print("📊 All agents registered with personality profiles!")

    await registry.stop()


if __name__ == "__main__":
    asyncio.run(create_demo_agents())
