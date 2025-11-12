"""
Agent Personality System - 5-Factor Model (OCEAN)

Implements personality traits that affect agent behavior, decision-making,
and performance across all protocols (ANP, ACP, AConsP).

Based on the Big Five personality traits with agent-specific adaptations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random
import json
import math


class PersonalityTrait(Enum):
    """Five-factor personality model traits"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


@dataclass
class PersonalityProfile:
    """
    Agent personality profile using 5-factor model.

    Each trait ranges from 0.0 to 1.0:
    - 0.0-0.3: Low
    - 0.3-0.7: Moderate
    - 0.7-1.0: High
    """
    openness: float = 0.5  # Creativity, willingness to try new strategies
    conscientiousness: float = 0.5  # Thoroughness, planning, risk management
    extraversion: float = 0.5  # Collaboration, communication frequency
    agreeableness: float = 0.5  # Team player, consensus-seeking
    neuroticism: float = 0.5  # Stress response, emotional volatility

    # Optional personality archetype for easy reference
    archetype: Optional[str] = None

    # Performance modifiers calculated from traits
    modifiers: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and calculate derived attributes"""
        self._validate_traits()
        self._calculate_modifiers()
        if not self.archetype:
            self.archetype = self._determine_archetype()

    def _validate_traits(self):
        """Ensure all traits are in valid range [0.0, 1.0]"""
        for trait in PersonalityTrait:
            value = getattr(self, trait.value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{trait.value} must be between 0.0 and 1.0, got {value}")

    def _calculate_modifiers(self):
        """Calculate performance modifiers based on personality traits"""
        # Risk tolerance: High conscientiousness = lower risk, high openness = higher risk
        self.modifiers['risk_tolerance'] = (
            (self.openness * 0.6) - (self.conscientiousness * 0.4) + 0.4
        )

        # Collaboration bonus: High extraversion + agreeableness
        self.modifiers['collaboration_bonus'] = (
            (self.extraversion * 0.5) + (self.agreeableness * 0.5)
        )

        # Innovation capacity: High openness - low neuroticism
        self.modifiers['innovation_capacity'] = (
            (self.openness * 0.7) + ((1 - self.neuroticism) * 0.3)
        )

        # Execution reliability: High conscientiousness - high neuroticism
        self.modifiers['execution_reliability'] = (
            (self.conscientiousness * 0.7) + ((1 - self.neuroticism) * 0.3)
        )

        # Leadership tendency: High extraversion + conscientiousness - neuroticism
        self.modifiers['leadership_tendency'] = (
            (self.extraversion * 0.4) +
            (self.conscientiousness * 0.3) +
            ((1 - self.neuroticism) * 0.3)
        )

        # Learning speed: High openness + low conscientiousness (more willing to experiment)
        self.modifiers['learning_speed'] = (
            (self.openness * 0.6) + ((1 - self.conscientiousness * 0.5) * 0.4)
        )

        # Stress resistance: Low neuroticism + high conscientiousness
        self.modifiers['stress_resistance'] = (
            ((1 - self.neuroticism) * 0.6) + (self.conscientiousness * 0.4)
        )

    def _determine_archetype(self) -> str:
        """Determine personality archetype based on trait combinations"""
        # High openness + low neuroticism
        if self.openness > 0.7 and self.neuroticism < 0.3:
            return "Innovator"

        # High conscientiousness + low neuroticism
        elif self.conscientiousness > 0.7 and self.neuroticism < 0.4:
            return "Executor"

        # High extraversion + high agreeableness
        elif self.extraversion > 0.7 and self.agreeableness > 0.7:
            return "Collaborator"

        # High openness + low conscientiousness
        elif self.openness > 0.7 and self.conscientiousness < 0.4:
            return "Explorer"

        # High conscientiousness + low agreeableness
        elif self.conscientiousness > 0.7 and self.agreeableness < 0.4:
            return "Specialist"

        # High neuroticism
        elif self.neuroticism > 0.7:
            return "Cautious"

        # Balanced across all traits
        elif all(0.4 <= getattr(self, t.value) <= 0.6 for t in PersonalityTrait):
            return "Balanced"

        else:
            return "Adaptive"

    def get_trait_description(self, trait: PersonalityTrait) -> str:
        """Get human-readable description of trait level"""
        value = getattr(self, trait.value)

        if value < 0.3:
            level = "Low"
        elif value < 0.7:
            level = "Moderate"
        else:
            level = "High"

        descriptions = {
            PersonalityTrait.OPENNESS: {
                "Low": "Prefers proven strategies, traditional approaches",
                "Moderate": "Balanced between innovation and convention",
                "High": "Creative, experimental, seeks novel solutions"
            },
            PersonalityTrait.CONSCIENTIOUSNESS: {
                "Low": "Flexible, spontaneous, fast decision-making",
                "Moderate": "Balances planning with adaptability",
                "High": "Thorough, methodical, detail-oriented"
            },
            PersonalityTrait.EXTRAVERSION: {
                "Low": "Independent, works best solo",
                "Moderate": "Comfortable alone or in teams",
                "High": "Highly collaborative, energized by interaction"
            },
            PersonalityTrait.AGREEABLENESS: {
                "Low": "Competitive, direct, results-focused",
                "Moderate": "Balances cooperation with independence",
                "High": "Cooperative, consensus-seeking, supportive"
            },
            PersonalityTrait.NEUROTICISM: {
                "Low": "Calm under pressure, emotionally stable",
                "Moderate": "Generally stable with occasional stress",
                "High": "Sensitive to stress, cautious in uncertainty"
            }
        }

        return f"{level}: {descriptions[trait][level]}"

    def get_modifier(self, modifier_name: str) -> float:
        """Get a specific performance modifier"""
        return self.modifiers.get(modifier_name, 0.5)

    def compatibility_score(self, other: 'PersonalityProfile') -> float:
        """
        Calculate compatibility score with another agent (0.0 to 1.0).
        Higher score = better collaboration potential.
        """
        # Complementary: High extraversion works well with high agreeableness
        # Similar: Similar openness and conscientiousness reduce friction

        # Calculate trait differences
        diff_openness = abs(self.openness - other.openness)
        diff_conscientiousness = abs(self.conscientiousness - other.conscientiousness)
        diff_extraversion = abs(self.extraversion - other.extraversion)
        diff_agreeableness = abs(self.agreeableness - other.agreeableness)
        diff_neuroticism = abs(self.neuroticism - other.neuroticism)

        # Similarity bonuses (some traits work better when similar)
        similarity_score = (
            (1 - diff_openness) * 0.2 +  # Similar creativity levels
            (1 - diff_conscientiousness) * 0.3 +  # Similar work styles
            (1 - diff_neuroticism) * 0.2  # Similar stress responses
        )

        # Complementary bonuses
        complementary_score = (
            min(self.extraversion, other.agreeableness) * 0.15 +  # Extrovert + agreeable
            min(other.extraversion, self.agreeableness) * 0.15  # Symmetric
        )

        return similarity_score + complementary_score

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism,
            'archetype': self.archetype,
            'modifiers': self.modifiers
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonalityProfile':
        """Create from dictionary"""
        return cls(
            openness=data.get('openness', 0.5),
            conscientiousness=data.get('conscientiousness', 0.5),
            extraversion=data.get('extraversion', 0.5),
            agreeableness=data.get('agreeableness', 0.5),
            neuroticism=data.get('neuroticism', 0.5),
            archetype=data.get('archetype')
        )

    @classmethod
    def random(cls, archetype: Optional[str] = None) -> 'PersonalityProfile':
        """Generate random personality profile, optionally matching an archetype"""
        if archetype:
            return cls._generate_archetype(archetype)

        return cls(
            openness=random.uniform(0.2, 0.9),
            conscientiousness=random.uniform(0.2, 0.9),
            extraversion=random.uniform(0.2, 0.9),
            agreeableness=random.uniform(0.2, 0.9),
            neuroticism=random.uniform(0.1, 0.7)
        )

    @classmethod
    def _generate_archetype(cls, archetype: str) -> 'PersonalityProfile':
        """Generate personality matching specific archetype"""
        archetypes = {
            "Innovator": cls(
                openness=random.uniform(0.75, 0.95),
                conscientiousness=random.uniform(0.4, 0.6),
                extraversion=random.uniform(0.5, 0.7),
                agreeableness=random.uniform(0.4, 0.6),
                neuroticism=random.uniform(0.1, 0.3),
                archetype="Innovator"
            ),
            "Executor": cls(
                openness=random.uniform(0.4, 0.6),
                conscientiousness=random.uniform(0.75, 0.95),
                extraversion=random.uniform(0.4, 0.6),
                agreeableness=random.uniform(0.5, 0.7),
                neuroticism=random.uniform(0.1, 0.35),
                archetype="Executor"
            ),
            "Collaborator": cls(
                openness=random.uniform(0.5, 0.7),
                conscientiousness=random.uniform(0.5, 0.7),
                extraversion=random.uniform(0.75, 0.95),
                agreeableness=random.uniform(0.75, 0.95),
                neuroticism=random.uniform(0.2, 0.4),
                archetype="Collaborator"
            ),
            "Explorer": cls(
                openness=random.uniform(0.75, 0.95),
                conscientiousness=random.uniform(0.2, 0.4),
                extraversion=random.uniform(0.6, 0.8),
                agreeableness=random.uniform(0.4, 0.6),
                neuroticism=random.uniform(0.3, 0.5),
                archetype="Explorer"
            ),
            "Specialist": cls(
                openness=random.uniform(0.3, 0.5),
                conscientiousness=random.uniform(0.75, 0.95),
                extraversion=random.uniform(0.2, 0.4),
                agreeableness=random.uniform(0.2, 0.4),
                neuroticism=random.uniform(0.2, 0.4),
                archetype="Specialist"
            ),
            "Cautious": cls(
                openness=random.uniform(0.3, 0.5),
                conscientiousness=random.uniform(0.6, 0.8),
                extraversion=random.uniform(0.3, 0.5),
                agreeableness=random.uniform(0.5, 0.7),
                neuroticism=random.uniform(0.7, 0.9),
                archetype="Cautious"
            ),
            "Balanced": cls(
                openness=random.uniform(0.45, 0.55),
                conscientiousness=random.uniform(0.45, 0.55),
                extraversion=random.uniform(0.45, 0.55),
                agreeableness=random.uniform(0.45, 0.55),
                neuroticism=random.uniform(0.45, 0.55),
                archetype="Balanced"
            )
        }

        return archetypes.get(archetype, cls.random())


class PersonalityManager:
    """Manages personality profiles for agents"""

    def __init__(self):
        self.profiles: Dict[str, PersonalityProfile] = {}

    def register_personality(self, agent_id: str, profile: PersonalityProfile):
        """Register personality profile for an agent"""
        self.profiles[agent_id] = profile

    def get_personality(self, agent_id: str) -> Optional[PersonalityProfile]:
        """Get personality profile for an agent"""
        return self.profiles.get(agent_id)

    def find_compatible_agents(
        self,
        agent_id: str,
        min_compatibility: float = 0.6,
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find agents with compatible personalities.
        Returns list of (agent_id, compatibility_score) tuples.
        """
        profile = self.profiles.get(agent_id)
        if not profile:
            return []

        compatible = []
        for other_id, other_profile in self.profiles.items():
            if other_id == agent_id:
                continue

            score = profile.compatibility_score(other_profile)
            if score >= min_compatibility:
                compatible.append((other_id, score))

        # Sort by compatibility score descending
        compatible.sort(key=lambda x: x[1], reverse=True)
        return compatible[:top_n]

    def get_team_dynamics(self, agent_ids: List[str]) -> Dict:
        """
        Analyze team dynamics for a group of agents.
        Returns metrics about team composition.
        """
        profiles = [self.profiles[aid] for aid in agent_ids if aid in self.profiles]

        if not profiles:
            return {"error": "No profiles found for specified agents"}

        # Calculate average traits
        avg_traits = {
            trait.value: sum(getattr(p, trait.value) for p in profiles) / len(profiles)
            for trait in PersonalityTrait
        }

        # Calculate diversity score (standard deviation of traits)
        diversity_scores = {}
        for trait in PersonalityTrait:
            values = [getattr(p, trait.value) for p in profiles]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            diversity_scores[trait.value] = math.sqrt(variance)

        # Overall diversity (average of trait diversities)
        overall_diversity = sum(diversity_scores.values()) / len(diversity_scores)

        # Calculate pairwise compatibility
        compatibilities = []
        for i, p1 in enumerate(profiles):
            for p2 in profiles[i+1:]:
                compatibilities.append(p1.compatibility_score(p2))

        avg_compatibility = sum(compatibilities) / len(compatibilities) if compatibilities else 0

        # Count archetypes
        archetype_counts = {}
        for p in profiles:
            archetype_counts[p.archetype] = archetype_counts.get(p.archetype, 0) + 1

        return {
            "team_size": len(profiles),
            "average_traits": avg_traits,
            "trait_diversity": diversity_scores,
            "overall_diversity": overall_diversity,
            "average_compatibility": avg_compatibility,
            "archetype_distribution": archetype_counts,
            "team_strengths": self._identify_team_strengths(avg_traits),
            "team_weaknesses": self._identify_team_weaknesses(avg_traits)
        }

    def _identify_team_strengths(self, avg_traits: Dict) -> List[str]:
        """Identify team strengths based on average traits"""
        strengths = []

        if avg_traits['openness'] > 0.7:
            strengths.append("High innovation capacity")
        if avg_traits['conscientiousness'] > 0.7:
            strengths.append("Excellent execution reliability")
        if avg_traits['extraversion'] > 0.7:
            strengths.append("Strong collaboration")
        if avg_traits['agreeableness'] > 0.7:
            strengths.append("Harmonious teamwork")
        if avg_traits['neuroticism'] < 0.3:
            strengths.append("High stress resistance")

        return strengths if strengths else ["Balanced capabilities"]

    def _identify_team_weaknesses(self, avg_traits: Dict) -> List[str]:
        """Identify team weaknesses based on average traits"""
        weaknesses = []

        if avg_traits['openness'] < 0.3:
            weaknesses.append("May resist innovation")
        if avg_traits['conscientiousness'] < 0.3:
            weaknesses.append("May lack thorough planning")
        if avg_traits['extraversion'] < 0.3:
            weaknesses.append("Limited collaboration")
        if avg_traits['agreeableness'] < 0.3:
            weaknesses.append("Potential for conflicts")
        if avg_traits['neuroticism'] > 0.7:
            weaknesses.append("Vulnerable to stress")

        return weaknesses if weaknesses else ["No significant weaknesses"]


# Predefined archetype templates for quick agent creation
ARCHETYPE_TEMPLATES = {
    "Innovator": "Creative, experimental agent. High innovation, moderate execution.",
    "Executor": "Reliable, methodical agent. High execution, moderate innovation.",
    "Collaborator": "Team-oriented agent. High collaboration, balanced other traits.",
    "Explorer": "Adventurous agent. High openness, low conscientiousness.",
    "Specialist": "Focused expert. High conscientiousness, low social needs.",
    "Cautious": "Risk-averse agent. High neuroticism, careful decision-making.",
    "Balanced": "Well-rounded agent. All traits moderate."
}


if __name__ == "__main__":
    # Demo usage
    print("=== Agent Personality System Demo ===\n")

    # Create different personality profiles
    innovator = PersonalityProfile.random("Innovator")
    executor = PersonalityProfile.random("Executor")
    collaborator = PersonalityProfile.random("Collaborator")

    profiles = [innovator, executor, collaborator]
    names = ["Innovator Agent", "Executor Agent", "Collaborator Agent"]

    for name, profile in zip(names, profiles):
        print(f"\n{name} ({profile.archetype}):")
        print(f"  Risk Tolerance: {profile.get_modifier('risk_tolerance'):.2f}")
        print(f"  Innovation: {profile.get_modifier('innovation_capacity'):.2f}")
        print(f"  Reliability: {profile.get_modifier('execution_reliability'):.2f}")
        print(f"  Leadership: {profile.get_modifier('leadership_tendency'):.2f}")

    # Test compatibility
    print(f"\n=== Compatibility Analysis ===")
    print(f"Innovator ↔ Executor: {innovator.compatibility_score(executor):.2f}")
    print(f"Innovator ↔ Collaborator: {innovator.compatibility_score(collaborator):.2f}")
    print(f"Executor ↔ Collaborator: {executor.compatibility_score(collaborator):.2f}")

    # Team dynamics
    manager = PersonalityManager()
    manager.register_personality("agent_1", innovator)
    manager.register_personality("agent_2", executor)
    manager.register_personality("agent_3", collaborator)

    dynamics = manager.get_team_dynamics(["agent_1", "agent_2", "agent_3"])
    print(f"\n=== Team Dynamics ===")
    print(f"Team Size: {dynamics['team_size']}")
    print(f"Average Compatibility: {dynamics['average_compatibility']:.2f}")
    print(f"Diversity Score: {dynamics['overall_diversity']:.2f}")
    print(f"Strengths: {', '.join(dynamics['team_strengths'])}")
    print(f"Archetype Mix: {dynamics['archetype_distribution']}")
