"""
Ensemble Templates - Pre-configured ensemble setups for one-click deployment

Provides curated ensemble configurations optimized for different trading styles,
market types, and risk profiles. Makes ensemble deployment accessible to everyone!

Templates include:
- Personality-tuned specialists
- Optimal voting thresholds
- Market-specific configurations
- Risk-adjusted setups

This is how you make autonomous agents accessible to non-technical users!

Author: Agentic Forge
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from superstandard.agents.personality import PersonalityProfile
from superstandard.agents.genetic_breeding import AgentGenome
from superstandard.agents.agent_ensemble import SpecialistType


# ============================================================================
# Template Categories
# ============================================================================

class TemplateCategory(str, Enum):
    """Categories for ensemble templates"""
    TRADING_STYLE = "trading_style"      # Aggressive, conservative, balanced
    MARKET_TYPE = "market_type"          # Crypto, forex, stocks, commodities
    RISK_PROFILE = "risk_profile"        # High risk, medium risk, low risk
    TIME_HORIZON = "time_horizon"        # Day trading, swing, position
    STRATEGY_TYPE = "strategy_type"      # Trend following, mean reversion, breakout


class RiskLevel(str, Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# Specialist Template
# ============================================================================

@dataclass
class SpecialistTemplate:
    """
    Template for a specialist agent.

    Defines personality traits, fitness expectations, and specialist type.
    """
    specialist_type: SpecialistType
    name: str
    description: str

    # Personality traits (OCEAN model)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Expected performance
    expected_fitness: float = 0.6
    expected_sharpe: float = 1.0

    # Metadata
    optimized_for: str = "general"

    def to_genome(self, agent_id: Optional[str] = None, generation: int = 0) -> AgentGenome:
        """Convert template to AgentGenome"""
        from uuid import uuid4

        if not agent_id:
            agent_id = f"template_{self.specialist_type.value}_{uuid4().hex[:8]}"

        personality = PersonalityProfile(
            openness=self.openness,
            conscientiousness=self.conscientiousness,
            extraversion=self.extraversion,
            agreeableness=self.agreeableness,
            neuroticism=self.neuroticism
        )

        return AgentGenome(
            agent_id=agent_id,
            generation=generation,
            personality=personality,
            parents=[],
            fitness_score=self.expected_fitness,
            mutations=[]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export template data"""
        return {
            'specialist_type': self.specialist_type.value,
            'name': self.name,
            'description': self.description,
            'personality': {
                'openness': self.openness,
                'conscientiousness': self.conscientiousness,
                'extraversion': self.extraversion,
                'agreeableness': self.agreeableness,
                'neuroticism': self.neuroticism
            },
            'expected_fitness': self.expected_fitness,
            'expected_sharpe': self.expected_sharpe,
            'optimized_for': self.optimized_for
        }


# ============================================================================
# Ensemble Template
# ============================================================================

@dataclass
class EnsembleTemplate:
    """
    Complete ensemble template with specialists, configuration, and metadata.

    This is a one-click deployable ensemble configuration!
    """
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    risk_level: RiskLevel

    # Ensemble configuration
    use_voting: bool = False
    voting_threshold: float = 0.6

    # Specialists
    specialists: List[SpecialistTemplate] = field(default_factory=list)

    # Metadata
    optimized_for: str = "general markets"
    recommended_capital: float = 10000.0
    recommended_timeframe: str = "1h"
    tags: List[str] = field(default_factory=list)

    # Performance expectations
    expected_annual_return: float = 0.15
    expected_max_drawdown: float = 0.20
    expected_sharpe_ratio: float = 1.5

    # Author info
    author: str = "Agentic Forge"
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Export complete template data"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'risk_level': self.risk_level.value,
            'configuration': {
                'use_voting': self.use_voting,
                'voting_threshold': self.voting_threshold
            },
            'specialists': [s.to_dict() for s in self.specialists],
            'metadata': {
                'optimized_for': self.optimized_for,
                'recommended_capital': self.recommended_capital,
                'recommended_timeframe': self.recommended_timeframe,
                'tags': self.tags
            },
            'performance_expectations': {
                'annual_return': self.expected_annual_return,
                'max_drawdown': self.expected_max_drawdown,
                'sharpe_ratio': self.expected_sharpe_ratio
            },
            'author': self.author,
            'version': self.version,
            'specialist_count': len(self.specialists)
        }


# ============================================================================
# Template Library
# ============================================================================

class TemplateLibrary:
    """
    Curated library of ensemble templates.

    Provides pre-configured ensembles for common use cases.
    """

    @staticmethod
    def get_all_templates() -> List[EnsembleTemplate]:
        """Get all available templates"""
        return [
            TemplateLibrary.aggressive_trader(),
            TemplateLibrary.conservative_trader(),
            TemplateLibrary.balanced_trader(),
            TemplateLibrary.crypto_specialist(),
            TemplateLibrary.trend_follower(),
            TemplateLibrary.mean_reversion(),
            TemplateLibrary.breakout_hunter(),
            TemplateLibrary.all_weather(),
            TemplateLibrary.day_trader(),
            TemplateLibrary.swing_trader()
        ]

    @staticmethod
    def get_template(template_id: str) -> Optional[EnsembleTemplate]:
        """Get template by ID"""
        templates = {t.template_id: t for t in TemplateLibrary.get_all_templates()}
        return templates.get(template_id)

    @staticmethod
    def get_templates_by_category(category: TemplateCategory) -> List[EnsembleTemplate]:
        """Get templates by category"""
        return [t for t in TemplateLibrary.get_all_templates() if t.category == category]

    @staticmethod
    def get_templates_by_risk(risk_level: RiskLevel) -> List[EnsembleTemplate]:
        """Get templates by risk level"""
        return [t for t in TemplateLibrary.get_all_templates() if t.risk_level == risk_level]

    # ========================================================================
    # Trading Style Templates
    # ========================================================================

    @staticmethod
    def aggressive_trader() -> EnsembleTemplate:
        """Aggressive trading ensemble - High risk, high reward"""
        return EnsembleTemplate(
            template_id="aggressive_trader",
            name="Aggressive Trader",
            description="High-frequency, high-risk ensemble optimized for maximum returns. "
                       "Uses aggressive specialists with high openness and low conscientiousness.",
            category=TemplateCategory.TRADING_STYLE,
            risk_level=RiskLevel.VERY_HIGH,
            use_voting=False,  # Direct routing for speed
            voting_threshold=0.7,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Aggressive Bull",
                    description="Highly aggressive bull market trader",
                    openness=0.9,
                    conscientiousness=0.3,
                    extraversion=0.8,
                    agreeableness=0.4,
                    neuroticism=0.6,
                    expected_fitness=0.70,
                    optimized_for="strong uptrends"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Volatility Trader",
                    description="Thrives in high volatility",
                    openness=0.85,
                    conscientiousness=0.4,
                    extraversion=0.7,
                    agreeableness=0.5,
                    neuroticism=0.5,
                    expected_fitness=0.68,
                    optimized_for="volatile markets"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Aggressive Bear",
                    description="Aggressive short seller",
                    openness=0.8,
                    conscientiousness=0.35,
                    extraversion=0.6,
                    agreeableness=0.3,
                    neuroticism=0.7,
                    expected_fitness=0.65,
                    optimized_for="sharp declines"
                )
            ],
            optimized_for="high volatility markets, crypto, meme stocks",
            recommended_capital=5000.0,
            recommended_timeframe="5m-15m",
            tags=["aggressive", "high-risk", "high-frequency", "crypto"],
            expected_annual_return=0.50,
            expected_max_drawdown=0.40,
            expected_sharpe_ratio=1.2
        )

    @staticmethod
    def conservative_trader() -> EnsembleTemplate:
        """Conservative trading ensemble - Low risk, steady returns"""
        return EnsembleTemplate(
            template_id="conservative_trader",
            name="Conservative Trader",
            description="Risk-averse ensemble focused on capital preservation and steady gains. "
                       "Uses highly conscientious specialists with low neuroticism.",
            category=TemplateCategory.TRADING_STYLE,
            risk_level=RiskLevel.LOW,
            use_voting=True,  # Voting for safety
            voting_threshold=0.65,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Conservative Bull",
                    description="Cautious bull market trader",
                    openness=0.4,
                    conscientiousness=0.9,
                    extraversion=0.4,
                    agreeableness=0.7,
                    neuroticism=0.2,
                    expected_fitness=0.68,
                    optimized_for="stable uptrends"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Conservative Bear",
                    description="Risk-aware bear trader",
                    openness=0.35,
                    conscientiousness=0.95,
                    extraversion=0.3,
                    agreeableness=0.8,
                    neuroticism=0.15,
                    expected_fitness=0.70,
                    optimized_for="gradual declines"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.SIDEWAYS_SPECIALIST,
                    name="Range Trader",
                    description="Expert in sideways markets",
                    openness=0.45,
                    conscientiousness=0.85,
                    extraversion=0.5,
                    agreeableness=0.75,
                    neuroticism=0.25,
                    expected_fitness=0.65,
                    optimized_for="range-bound markets"
                )
            ],
            optimized_for="stable markets, blue-chip stocks, indices",
            recommended_capital=25000.0,
            recommended_timeframe="1h-4h",
            tags=["conservative", "low-risk", "capital-preservation", "stocks"],
            expected_annual_return=0.12,
            expected_max_drawdown=0.10,
            expected_sharpe_ratio=2.0
        )

    @staticmethod
    def balanced_trader() -> EnsembleTemplate:
        """Balanced trading ensemble - Moderate risk, good returns"""
        return EnsembleTemplate(
            template_id="balanced_trader",
            name="Balanced Trader",
            description="Well-rounded ensemble balancing risk and reward. "
                       "Uses moderate specialists suitable for most market conditions.",
            category=TemplateCategory.TRADING_STYLE,
            risk_level=RiskLevel.MEDIUM,
            use_voting=False,
            voting_threshold=0.6,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Balanced Bull",
                    description="Moderate bull trader",
                    openness=0.6,
                    conscientiousness=0.65,
                    extraversion=0.6,
                    agreeableness=0.6,
                    neuroticism=0.4,
                    expected_fitness=0.72,
                    optimized_for="bull markets"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Balanced Bear",
                    description="Moderate bear trader",
                    openness=0.55,
                    conscientiousness=0.7,
                    extraversion=0.5,
                    agreeableness=0.55,
                    neuroticism=0.45,
                    expected_fitness=0.70,
                    optimized_for="bear markets"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Balanced Volatility",
                    description="Moderate volatility trader",
                    openness=0.65,
                    conscientiousness=0.6,
                    extraversion=0.65,
                    agreeableness=0.6,
                    neuroticism=0.4,
                    expected_fitness=0.68,
                    optimized_for="volatile markets"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.GENERALIST,
                    name="All-Rounder",
                    description="Works in all conditions",
                    openness=0.6,
                    conscientiousness=0.65,
                    extraversion=0.6,
                    agreeableness=0.65,
                    neuroticism=0.35,
                    expected_fitness=0.65,
                    optimized_for="all markets"
                )
            ],
            optimized_for="diverse markets, ETFs, major pairs",
            recommended_capital=15000.0,
            recommended_timeframe="30m-1h",
            tags=["balanced", "medium-risk", "versatile", "all-markets"],
            expected_annual_return=0.25,
            expected_max_drawdown=0.20,
            expected_sharpe_ratio=1.5
        )

    # ========================================================================
    # Market Type Templates
    # ========================================================================

    @staticmethod
    def crypto_specialist() -> EnsembleTemplate:
        """Crypto-optimized ensemble"""
        return EnsembleTemplate(
            template_id="crypto_specialist",
            name="Crypto Specialist",
            description="Ensemble optimized for cryptocurrency markets. "
                       "Handles extreme volatility and 24/7 trading.",
            category=TemplateCategory.MARKET_TYPE,
            risk_level=RiskLevel.HIGH,
            use_voting=True,
            voting_threshold=0.55,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Crypto Volatility Expert",
                    description="Thrives in crypto volatility",
                    openness=0.85,
                    conscientiousness=0.5,
                    extraversion=0.8,
                    agreeableness=0.5,
                    neuroticism=0.5,
                    expected_fitness=0.72,
                    optimized_for="crypto volatility"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Crypto Bull",
                    description="Rides crypto pumps",
                    openness=0.8,
                    conscientiousness=0.45,
                    extraversion=0.85,
                    agreeableness=0.45,
                    neuroticism=0.55,
                    expected_fitness=0.70,
                    optimized_for="crypto bull runs"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Crypto Bear",
                    description="Profits from crypto crashes",
                    openness=0.75,
                    conscientiousness=0.5,
                    extraversion=0.6,
                    agreeableness=0.4,
                    neuroticism=0.6,
                    expected_fitness=0.68,
                    optimized_for="crypto crashes"
                )
            ],
            optimized_for="BTC, ETH, major altcoins, 24/7 markets",
            recommended_capital=5000.0,
            recommended_timeframe="15m-1h",
            tags=["crypto", "high-volatility", "24/7", "altcoins"],
            expected_annual_return=0.60,
            expected_max_drawdown=0.45,
            expected_sharpe_ratio=1.3
        )

    # ========================================================================
    # Strategy Type Templates
    # ========================================================================

    @staticmethod
    def trend_follower() -> EnsembleTemplate:
        """Trend following ensemble"""
        return EnsembleTemplate(
            template_id="trend_follower",
            name="Trend Follower",
            description="Ensemble specialized in identifying and riding trends. "
                       "Waits for confirmation before entering positions.",
            category=TemplateCategory.STRATEGY_TYPE,
            risk_level=RiskLevel.MEDIUM,
            use_voting=False,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Uptrend Follower",
                    description="Follows bullish trends",
                    openness=0.5,
                    conscientiousness=0.75,
                    extraversion=0.6,
                    agreeableness=0.6,
                    neuroticism=0.3,
                    expected_fitness=0.74,
                    optimized_for="uptrends"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Downtrend Follower",
                    description="Follows bearish trends",
                    openness=0.45,
                    conscientiousness=0.8,
                    extraversion=0.5,
                    agreeableness=0.55,
                    neuroticism=0.35,
                    expected_fitness=0.72,
                    optimized_for="downtrends"
                )
            ],
            optimized_for="trending markets, momentum plays",
            recommended_capital=10000.0,
            recommended_timeframe="1h-4h",
            tags=["trend-following", "momentum", "medium-risk"],
            expected_annual_return=0.30,
            expected_max_drawdown=0.18,
            expected_sharpe_ratio=1.7
        )

    @staticmethod
    def mean_reversion() -> EnsembleTemplate:
        """Mean reversion ensemble"""
        return EnsembleTemplate(
            template_id="mean_reversion",
            name="Mean Reversion",
            description="Ensemble that profits from price returning to average. "
                       "Buys oversold and sells overbought conditions.",
            category=TemplateCategory.STRATEGY_TYPE,
            risk_level=RiskLevel.MEDIUM,
            use_voting=True,
            voting_threshold=0.6,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.SIDEWAYS_SPECIALIST,
                    name="Range Trader",
                    description="Trades within ranges",
                    openness=0.5,
                    conscientiousness=0.8,
                    extraversion=0.5,
                    agreeableness=0.7,
                    neuroticism=0.3,
                    expected_fitness=0.70,
                    optimized_for="range-bound"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Reversion Trader",
                    description="Catches reversions",
                    openness=0.55,
                    conscientiousness=0.75,
                    extraversion=0.55,
                    agreeableness=0.65,
                    neuroticism=0.35,
                    expected_fitness=0.68,
                    optimized_for="mean reversion"
                )
            ],
            optimized_for="oscillating markets, sideways action",
            recommended_capital=12000.0,
            recommended_timeframe="30m-2h",
            tags=["mean-reversion", "range-trading", "oscillator"],
            expected_annual_return=0.22,
            expected_max_drawdown=0.15,
            expected_sharpe_ratio=1.8
        )

    @staticmethod
    def breakout_hunter() -> EnsembleTemplate:
        """Breakout trading ensemble"""
        return EnsembleTemplate(
            template_id="breakout_hunter",
            name="Breakout Hunter",
            description="Ensemble that catches explosive breakout moves. "
                       "High risk but potentially high reward.",
            category=TemplateCategory.STRATEGY_TYPE,
            risk_level=RiskLevel.HIGH,
            use_voting=False,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Breakout Specialist",
                    description="Catches breakouts",
                    openness=0.85,
                    conscientiousness=0.45,
                    extraversion=0.8,
                    agreeableness=0.5,
                    neuroticism=0.55,
                    expected_fitness=0.68,
                    optimized_for="breakouts"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Bullish Breakout",
                    description="Upside breakouts",
                    openness=0.8,
                    conscientiousness=0.5,
                    extraversion=0.75,
                    agreeableness=0.55,
                    neuroticism=0.5,
                    expected_fitness=0.70,
                    optimized_for="bull breakouts"
                )
            ],
            optimized_for="consolidation breakouts, range breaks",
            recommended_capital=8000.0,
            recommended_timeframe="15m-1h",
            tags=["breakout", "high-risk", "explosive-moves"],
            expected_annual_return=0.40,
            expected_max_drawdown=0.30,
            expected_sharpe_ratio=1.4
        )

    @staticmethod
    def all_weather() -> EnsembleTemplate:
        """All-weather ensemble"""
        return EnsembleTemplate(
            template_id="all_weather",
            name="All Weather",
            description="Robust ensemble designed to perform in all market conditions. "
                       "Maximum diversification across specialist types.",
            category=TemplateCategory.TRADING_STYLE,
            risk_level=RiskLevel.LOW,
            use_voting=True,
            voting_threshold=0.55,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Bull Specialist",
                    description="Bull markets",
                    openness=0.6,
                    conscientiousness=0.7,
                    extraversion=0.6,
                    agreeableness=0.65,
                    neuroticism=0.3,
                    expected_fitness=0.70
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Bear Specialist",
                    description="Bear markets",
                    openness=0.55,
                    conscientiousness=0.75,
                    extraversion=0.5,
                    agreeableness=0.6,
                    neuroticism=0.35,
                    expected_fitness=0.68
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Volatility Specialist",
                    description="Volatile markets",
                    openness=0.65,
                    conscientiousness=0.65,
                    extraversion=0.65,
                    agreeableness=0.6,
                    neuroticism=0.4,
                    expected_fitness=0.66
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.SIDEWAYS_SPECIALIST,
                    name="Sideways Specialist",
                    description="Range markets",
                    openness=0.5,
                    conscientiousness=0.8,
                    extraversion=0.5,
                    agreeableness=0.7,
                    neuroticism=0.3,
                    expected_fitness=0.64
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.GENERALIST,
                    name="Generalist",
                    description="All markets",
                    openness=0.6,
                    conscientiousness=0.7,
                    extraversion=0.6,
                    agreeableness=0.65,
                    neuroticism=0.35,
                    expected_fitness=0.67
                )
            ],
            optimized_for="all market conditions, maximum robustness",
            recommended_capital=20000.0,
            recommended_timeframe="1h-4h",
            tags=["all-weather", "diversified", "robust", "low-risk"],
            expected_annual_return=0.18,
            expected_max_drawdown=0.12,
            expected_sharpe_ratio=1.9
        )

    # ========================================================================
    # Time Horizon Templates
    # ========================================================================

    @staticmethod
    def day_trader() -> EnsembleTemplate:
        """Day trading ensemble"""
        return EnsembleTemplate(
            template_id="day_trader",
            name="Day Trader",
            description="Fast-paced ensemble for intraday trading. "
                       "Closes all positions before market close.",
            category=TemplateCategory.TIME_HORIZON,
            risk_level=RiskLevel.HIGH,
            use_voting=False,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.VOLATILE_SPECIALIST,
                    name="Intraday Volatility",
                    description="Intraday moves",
                    openness=0.8,
                    conscientiousness=0.5,
                    extraversion=0.8,
                    agreeableness=0.5,
                    neuroticism=0.5,
                    expected_fitness=0.68,
                    optimized_for="intraday"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Intraday Bull",
                    description="Morning rallies",
                    openness=0.75,
                    conscientiousness=0.55,
                    extraversion=0.75,
                    agreeableness=0.55,
                    neuroticism=0.45,
                    expected_fitness=0.70,
                    optimized_for="intraday uptrends"
                )
            ],
            optimized_for="liquid markets, high volume",
            recommended_capital=5000.0,
            recommended_timeframe="1m-15m",
            tags=["day-trading", "intraday", "high-frequency"],
            expected_annual_return=0.35,
            expected_max_drawdown=0.25,
            expected_sharpe_ratio=1.4
        )

    @staticmethod
    def swing_trader() -> EnsembleTemplate:
        """Swing trading ensemble"""
        return EnsembleTemplate(
            template_id="swing_trader",
            name="Swing Trader",
            description="Medium-term ensemble holding positions for days to weeks. "
                       "Captures larger price swings.",
            category=TemplateCategory.TIME_HORIZON,
            risk_level=RiskLevel.MEDIUM,
            use_voting=True,
            voting_threshold=0.6,
            specialists=[
                SpecialistTemplate(
                    specialist_type=SpecialistType.BULL_SPECIALIST,
                    name="Swing Bull",
                    description="Multi-day upswings",
                    openness=0.6,
                    conscientiousness=0.7,
                    extraversion=0.6,
                    agreeableness=0.6,
                    neuroticism=0.35,
                    expected_fitness=0.72,
                    optimized_for="swing highs"
                ),
                SpecialistTemplate(
                    specialist_type=SpecialistType.BEAR_SPECIALIST,
                    name="Swing Bear",
                    description="Multi-day downswings",
                    openness=0.55,
                    conscientiousness=0.75,
                    extraversion=0.55,
                    agreeableness=0.55,
                    neuroticism=0.4,
                    expected_fitness=0.70,
                    optimized_for="swing lows"
                )
            ],
            optimized_for="trending markets, multi-day swings",
            recommended_capital=15000.0,
            recommended_timeframe="4h-1d",
            tags=["swing-trading", "multi-day", "medium-term"],
            expected_annual_return=0.28,
            expected_max_drawdown=0.18,
            expected_sharpe_ratio=1.6
        )


# ============================================================================
# Template Registry
# ============================================================================

# Global template registry
TEMPLATE_REGISTRY = {
    t.template_id: t for t in TemplateLibrary.get_all_templates()
}
