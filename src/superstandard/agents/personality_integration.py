"""
Personality System Integration with SuperStandard Protocols

Integrates personality profiles with ANP, ACP, and trading agents.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from .personality import PersonalityProfile, PersonalityManager, PersonalityTrait


# ============================================================================
# ANP Integration
# ============================================================================

class PersonalityANPIntegration:
    """
    Integrates personality system with Agent Network Protocol (ANP).

    Personality data is stored in agent metadata and can be used for:
    - Capability matching based on personality fit
    - Team formation optimization
    - Load balancing based on stress resistance
    """

    @staticmethod
    def add_personality_to_registration(
        registration_data: Dict,
        personality: PersonalityProfile
    ) -> Dict:
        """
        Add personality profile to ANP registration metadata.

        Args:
            registration_data: ANP registration dict
            personality: Personality profile to add

        Returns:
            Updated registration data
        """
        if 'metadata' not in registration_data:
            registration_data['metadata'] = {}

        registration_data['metadata']['personality'] = personality.to_dict()
        registration_data['metadata']['archetype'] = personality.archetype

        # Add personality-based tags for discovery
        if 'tags' not in registration_data:
            registration_data['tags'] = []

        registration_data['tags'].append(f"archetype:{personality.archetype}")
        registration_data['tags'].append(f"risk_level:{_get_risk_level(personality)}")

        return registration_data

    @staticmethod
    def extract_personality_from_agent(agent_info: Dict) -> Optional[PersonalityProfile]:
        """
        Extract personality profile from agent info.

        Args:
            agent_info: Agent information dict from ANP

        Returns:
            PersonalityProfile if present, None otherwise
        """
        if 'metadata' in agent_info and 'personality' in agent_info['metadata']:
            return PersonalityProfile.from_dict(agent_info['metadata']['personality'])
        return None

    @staticmethod
    def enhance_discovery_with_personality(
        agents: List[Dict],
        desired_traits: Optional[Dict[str, float]] = None,
        archetype: Optional[str] = None
    ) -> List[Dict]:
        """
        Enhance agent discovery with personality filtering.

        Args:
            agents: List of discovered agents
            desired_traits: Dict of trait names to minimum values
            archetype: Filter by specific archetype

        Returns:
            Filtered and scored agents
        """
        if not desired_traits and not archetype:
            return agents

        enhanced = []
        for agent in agents:
            personality = PersonalityANPIntegration.extract_personality_from_agent(agent)
            if not personality:
                continue

            # Filter by archetype
            if archetype and personality.archetype != archetype:
                continue

            # Score based on desired traits
            if desired_traits:
                match_score = 0.0
                for trait_name, min_value in desired_traits.items():
                    trait_value = getattr(personality, trait_name, 0.5)
                    if trait_value >= min_value:
                        match_score += (trait_value - min_value) + 1.0

                agent['personality_match_score'] = match_score / len(desired_traits)
            else:
                agent['personality_match_score'] = 1.0

            agent['archetype'] = personality.archetype
            enhanced.append(agent)

        # Sort by match score
        enhanced.sort(key=lambda x: x.get('personality_match_score', 0), reverse=True)
        return enhanced


# ============================================================================
# Trading Agent Integration
# ============================================================================

class PersonalityTradingIntegration:
    """
    Integrates personality with trading agent decision-making.

    Personality affects:
    - Position sizing (risk tolerance)
    - Strategy selection (innovation vs proven)
    - Stop loss placement (stress resistance)
    - Holding periods (conscientiousness)
    """

    @staticmethod
    def calculate_position_size(
        base_position: float,
        personality: PersonalityProfile,
        market_volatility: float = 0.5
    ) -> float:
        """
        Adjust position size based on personality and market conditions.

        Args:
            base_position: Base position size
            personality: Agent personality
            market_volatility: Market volatility (0.0 to 1.0)

        Returns:
            Adjusted position size
        """
        risk_tolerance = personality.get_modifier('risk_tolerance')
        stress_resistance = personality.get_modifier('stress_resistance')

        # High volatility reduces position for low stress resistance
        volatility_factor = 1.0 - (market_volatility * (1.0 - stress_resistance))

        # Risk tolerance directly scales position
        position = base_position * risk_tolerance * volatility_factor

        return max(0.0, min(position, base_position * 2.0))  # Cap at 2x base

    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        personality: PersonalityProfile,
        default_stop_pct: float = 0.05
    ) -> float:
        """
        Calculate stop loss based on personality.

        High neuroticism = tighter stops
        High conscientiousness = planned stops

        Args:
            entry_price: Entry price
            personality: Agent personality
            default_stop_pct: Default stop loss percentage

        Returns:
            Stop loss price
        """
        # Neurotic agents use tighter stops
        neuroticism_factor = 0.5 + (personality.neuroticism * 0.5)

        # Conscientious agents stick to plan
        conscientiousness_factor = 0.8 + (personality.conscientiousness * 0.4)

        adjusted_stop_pct = default_stop_pct * neuroticism_factor * conscientiousness_factor

        return entry_price * (1.0 - adjusted_stop_pct)

    @staticmethod
    def select_strategy_type(personality: PersonalityProfile) -> str:
        """
        Recommend trading strategy based on personality.

        Args:
            personality: Agent personality

        Returns:
            Strategy type recommendation
        """
        innovation = personality.get_modifier('innovation_capacity')
        reliability = personality.get_modifier('execution_reliability')
        risk_tolerance = personality.get_modifier('risk_tolerance')

        if innovation > 0.7 and risk_tolerance > 0.6:
            return "experimental"  # Try new strategies
        elif reliability > 0.7 and risk_tolerance < 0.5:
            return "conservative"  # Proven, low-risk strategies
        elif risk_tolerance > 0.7:
            return "aggressive"  # High-risk, high-reward
        elif reliability > 0.6:
            return "systematic"  # Rule-based, consistent
        else:
            return "balanced"  # Mix of approaches

    @staticmethod
    def calculate_holding_period_bias(
        personality: PersonalityProfile,
        base_period_hours: float = 24.0
    ) -> float:
        """
        Adjust holding period based on personality.

        High conscientiousness = longer holds (stick to plan)
        High neuroticism = shorter holds (anxiety)

        Args:
            personality: Agent personality
            base_period_hours: Base holding period in hours

        Returns:
            Adjusted holding period in hours
        """
        # Conscientious agents hold longer
        conscientiousness_factor = 0.5 + (personality.conscientiousness * 1.0)

        # Neurotic agents exit faster
        neuroticism_factor = 1.5 - (personality.neuroticism * 0.8)

        adjusted_period = base_period_hours * conscientiousness_factor * neuroticism_factor

        return max(1.0, adjusted_period)  # Minimum 1 hour


# ============================================================================
# ACP Integration
# ============================================================================

class PersonalityACPIntegration:
    """
    Integrates personality with Agent Coordination Protocol (ACP).

    Personality affects:
    - Role assignment (leadership, support, specialist)
    - Communication frequency (extraversion)
    - Conflict resolution style
    - Task preferences
    """

    @staticmethod
    def recommend_role(personality: PersonalityProfile) -> str:
        """
        Recommend coordination role based on personality.

        Args:
            personality: Agent personality

        Returns:
            Recommended role
        """
        leadership = personality.get_modifier('leadership_tendency')
        collaboration = personality.get_modifier('collaboration_bonus')
        reliability = personality.get_modifier('execution_reliability')

        if leadership > 0.7:
            return "coordinator"  # Lead the session
        elif collaboration > 0.7:
            return "facilitator"  # Help others, bridge communication
        elif reliability > 0.7 and personality.conscientiousness > 0.7:
            return "executor"  # Get tasks done reliably
        elif personality.openness > 0.7:
            return "innovator"  # Propose new approaches
        else:
            return "contributor"  # General participant

    @staticmethod
    def calculate_communication_frequency(
        personality: PersonalityProfile,
        base_frequency_minutes: float = 30.0
    ) -> float:
        """
        Calculate how often agent should communicate updates.

        Args:
            personality: Agent personality
            base_frequency_minutes: Base communication interval

        Returns:
            Adjusted frequency in minutes
        """
        # Extraverted agents communicate more
        extraversion_factor = 2.0 - personality.extraversion

        # Conscientious agents give thorough updates
        conscientiousness_factor = 1.2 - (personality.conscientiousness * 0.4)

        frequency = base_frequency_minutes * extraversion_factor * conscientiousness_factor

        return max(5.0, min(frequency, 120.0))  # Between 5 min and 2 hours

    @staticmethod
    def conflict_resolution_style(personality: PersonalityProfile) -> str:
        """
        Determine conflict resolution approach.

        Args:
            personality: Agent personality

        Returns:
            Conflict resolution style
        """
        agreeableness = personality.agreeableness
        assertiveness = 1.0 - agreeableness  # Inverse of agreeableness

        if agreeableness > 0.7:
            return "accommodating"  # Prioritize harmony
        elif assertiveness > 0.7:
            return "competing"  # Assert own position
        elif personality.openness > 0.7:
            return "collaborating"  # Find creative solutions
        elif personality.conscientiousness > 0.7:
            return "compromising"  # Find middle ground
        else:
            return "avoiding"  # Minimize conflict

    @staticmethod
    def form_optimal_team(
        candidates: List[Dict],
        team_size: int,
        desired_diversity: float = 0.5
    ) -> List[str]:
        """
        Form optimal team considering personality diversity and compatibility.

        Args:
            candidates: List of candidate agents with personality data
            team_size: Desired team size
            desired_diversity: 0.0 = similar, 1.0 = diverse

        Returns:
            List of selected agent IDs
        """
        if len(candidates) <= team_size:
            return [c['agent_id'] for c in candidates]

        # Extract personalities
        personalities = []
        for candidate in candidates:
            profile = PersonalityANPIntegration.extract_personality_from_agent(candidate)
            if profile:
                personalities.append((candidate['agent_id'], profile))

        if not personalities:
            return [c['agent_id'] for c in candidates[:team_size]]

        # Start with most collaborative agent
        selected = []
        selected_profiles = []

        # Find most collaborative
        best_collab = max(personalities, key=lambda x: x[1].get_modifier('collaboration_bonus'))
        selected.append(best_collab[0])
        selected_profiles.append(best_collab[1])

        # Add remaining members balancing compatibility and diversity
        remaining = [p for p in personalities if p[0] not in selected]

        while len(selected) < team_size and remaining:
            best_score = -1
            best_candidate = None

            for candidate_id, candidate_profile in remaining:
                # Calculate average compatibility with team
                compatibility_scores = [
                    candidate_profile.compatibility_score(member)
                    for member in selected_profiles
                ]
                avg_compatibility = sum(compatibility_scores) / len(compatibility_scores)

                # Calculate diversity contribution
                diversity_score = 0.0
                for member in selected_profiles:
                    for trait in PersonalityTrait:
                        diversity_score += abs(
                            getattr(candidate_profile, trait.value) -
                            getattr(member, trait.value)
                        )
                diversity_score /= (len(selected_profiles) * len(PersonalityTrait))

                # Combined score
                score = (
                    avg_compatibility * (1.0 - desired_diversity) +
                    diversity_score * desired_diversity
                )

                if score > best_score:
                    best_score = score
                    best_candidate = (candidate_id, candidate_profile)

            if best_candidate:
                selected.append(best_candidate[0])
                selected_profiles.append(best_candidate[1])
                remaining = [p for p in remaining if p[0] != best_candidate[0]]

        return selected


# ============================================================================
# Utility Functions
# ============================================================================

def _get_risk_level(personality: PersonalityProfile) -> str:
    """Categorize risk level based on personality"""
    risk_tolerance = personality.get_modifier('risk_tolerance')

    if risk_tolerance < 0.3:
        return "low"
    elif risk_tolerance < 0.7:
        return "medium"
    else:
        return "high"


# ============================================================================
# Demo Usage
# ============================================================================

if __name__ == "__main__":
    from personality import PersonalityProfile

    print("=== Personality Integration Demo ===\n")

    # Create test personalities
    conservative_trader = PersonalityProfile(
        openness=0.4,
        conscientiousness=0.8,
        extraversion=0.5,
        agreeableness=0.6,
        neuroticism=0.6,
        archetype="Cautious"
    )

    aggressive_trader = PersonalityProfile(
        openness=0.8,
        conscientiousness=0.4,
        extraversion=0.7,
        agreeableness=0.4,
        neuroticism=0.2,
        archetype="Innovator"
    )

    # Trading integration demo
    print("=== Trading Integration ===")
    print(f"\nConservative Trader:")
    print(f"  Position Size (base=1.0): {PersonalityTradingIntegration.calculate_position_size(1.0, conservative_trader):.2f}")
    print(f"  Strategy Type: {PersonalityTradingIntegration.select_strategy_type(conservative_trader)}")
    print(f"  Holding Period: {PersonalityTradingIntegration.calculate_holding_period_bias(conservative_trader):.1f}h")

    print(f"\nAggressive Trader:")
    print(f"  Position Size (base=1.0): {PersonalityTradingIntegration.calculate_position_size(1.0, aggressive_trader):.2f}")
    print(f"  Strategy Type: {PersonalityTradingIntegration.select_strategy_type(aggressive_trader)}")
    print(f"  Holding Period: {PersonalityTradingIntegration.calculate_holding_period_bias(aggressive_trader):.1f}h")

    # ACP integration demo
    print(f"\n=== Coordination Integration ===")
    print(f"\nConservative Agent:")
    print(f"  Recommended Role: {PersonalityACPIntegration.recommend_role(conservative_trader)}")
    print(f"  Communication Frequency: Every {PersonalityACPIntegration.calculate_communication_frequency(conservative_trader):.0f} min")
    print(f"  Conflict Style: {PersonalityACPIntegration.conflict_resolution_style(conservative_trader)}")

    print(f"\nAggressive Agent:")
    print(f"  Recommended Role: {PersonalityACPIntegration.recommend_role(aggressive_trader)}")
    print(f"  Communication Frequency: Every {PersonalityACPIntegration.calculate_communication_frequency(aggressive_trader):.0f} min")
    print(f"  Conflict Style: {PersonalityACPIntegration.conflict_resolution_style(aggressive_trader)}")
