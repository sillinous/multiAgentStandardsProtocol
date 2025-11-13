"""Agent implementations organized by category"""

from .personality import PersonalityProfile
from .genetic_breeding import (
    AgentGenome,
    EvolutionEngine,
    CrossoverMethod,
    SelectionStrategy
)
from .agent_ensemble import (
    AgentEnsemble,
    AgentSpecialist,
    SpecialistType,
    SimpleRegimeDetector
)
from .ensemble_templates import (
    EnsembleTemplate,
    SpecialistTemplate,
    TemplateLibrary,
    TemplateCategory,
    RiskLevel
)
from .backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    MarketBar,
    Trade,
    HistoricalDataGenerator
)

__all__ = [
    # Personality System
    'PersonalityProfile',

    # Genetic Breeding
    'AgentGenome',
    'EvolutionEngine',
    'CrossoverMethod',
    'SelectionStrategy',

    # Agent Ensemble
    'AgentEnsemble',
    'AgentSpecialist',
    'SpecialistType',
    'SimpleRegimeDetector',

    # Ensemble Templates
    'EnsembleTemplate',
    'SpecialistTemplate',
    'TemplateLibrary',
    'TemplateCategory',
    'RiskLevel',

    # Backtesting Engine
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'BacktestMetrics',
    'MarketBar',
    'Trade',
    'HistoricalDataGenerator'
]
