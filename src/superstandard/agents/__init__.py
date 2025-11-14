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
from .pareto_evolution import (
    ParetoEvolutionEngine,
    ParetoEvolutionConfig,
    ParetoEvolutionResult,
    ObjectiveType,
    Objective,
    MultiObjectiveScore,
    MultiObjectiveEvaluator,
    NSGA2
)
from .continuous_evolution import (
    ContinuousEvolutionEngine,
    ContinuousEvolutionConfig,
    DegradationDetectionConfig,
    ABTestConfig,
    ABTest,
    ABTestStatus,
    EvolutionTrigger,
    PerformanceMetrics,
    PerformanceDegradationDetector,
    EvolutionEvent
)
from .market_data import (
    AlpacaClient,
    AlpacaConfig,
    MarketDataBar,
    Position,
    Order,
    OrderSide,
    OrderType,
    TimeInForce,
    AccountInfo,
    RealMarketDataAdapter,
    RealDataConfig,
    create_real_data_adapter,
    PaperTradingEngine,
    PaperTradingConfig,
    TradingMode,
    TradeExecutionResult
)
from .explainable_ai import (
    DecisionExplanationEngine,
    DecisionExplanation,
    ReasoningFactor,
    ReasoningFactorType,
    AgentContribution,
    DecisionTreeVisualizer
)
from .explainable_ensemble import (
    ExplainableAgentEnsemble,
    ExplainableDecision,
    create_explainable_ensemble
)
from .decision_replay import (
    DecisionReplayEngine,
    DecisionTimeline,
    ReplayFrame
)
from .sentiment import (
    SentimentScore,
    SentimentSource,
    SentimentEngine,
    SentimentAggregator,
    NewsArticle,
    NewsSentimentProvider,
    SocialPost,
    TwitterSentimentProvider,
    RedditSentimentProvider,
    TextSentimentAnalyzer,
    KeywordExtractor
)
from .sentiment_integration import (
    SentimentEnhancedData,
    create_sentiment_enhanced_ensemble,
    make_sentiment_aware_decision
)
from .conversation import (
    QueryProcessor,
    QueryIntent,
    QueryType,
    ProcessedQuery,
    CommandInterpreter,
    TradingCommand,
    CommandType,
    CommandResult,
    ConversationalAgent,
    ConversationContext,
    ConversationHistory
)
from .risk_management import (
    RiskMetrics,
    RiskMetricsCalculator,
    quick_risk_assessment,
    PositionSize,
    PositionSizingMethod,
    PositionSizingCalculator,
    calculate_optimal_position
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
    'HistoricalDataGenerator',

    # Multi-Objective Pareto Evolution
    'ParetoEvolutionEngine',
    'ParetoEvolutionConfig',
    'ParetoEvolutionResult',
    'ObjectiveType',
    'Objective',
    'MultiObjectiveScore',
    'MultiObjectiveEvaluator',
    'NSGA2',

    # Continuous Evolution in Production
    'ContinuousEvolutionEngine',
    'ContinuousEvolutionConfig',
    'DegradationDetectionConfig',
    'ABTestConfig',
    'ABTest',
    'ABTestStatus',
    'EvolutionTrigger',
    'PerformanceMetrics',
    'PerformanceDegradationDetector',
    'EvolutionEvent',

    # Real Market Data Integration
    'AlpacaClient',
    'AlpacaConfig',
    'MarketDataBar',
    'Position',
    'Order',
    'OrderSide',
    'OrderType',
    'TimeInForce',
    'AccountInfo',
    'RealMarketDataAdapter',
    'RealDataConfig',
    'create_real_data_adapter',
    'PaperTradingEngine',
    'PaperTradingConfig',
    'TradingMode',
    'TradeExecutionResult',

    # Explainable AI
    'DecisionExplanationEngine',
    'DecisionExplanation',
    'ReasoningFactor',
    'ReasoningFactorType',
    'AgentContribution',
    'DecisionTreeVisualizer',
    'ExplainableAgentEnsemble',
    'ExplainableDecision',
    'create_explainable_ensemble',
    'DecisionReplayEngine',
    'DecisionTimeline',
    'ReplayFrame',

    # Sentiment Analysis
    'SentimentScore',
    'SentimentSource',
    'SentimentEngine',
    'SentimentAggregator',
    'NewsArticle',
    'NewsSentimentProvider',
    'SocialPost',
    'TwitterSentimentProvider',
    'RedditSentimentProvider',
    'TextSentimentAnalyzer',
    'KeywordExtractor',
    'SentimentEnhancedData',
    'create_sentiment_enhanced_ensemble',
    'make_sentiment_aware_decision',

    # Natural Language Interface
    'QueryProcessor',
    'QueryIntent',
    'QueryType',
    'ProcessedQuery',
    'CommandInterpreter',
    'TradingCommand',
    'CommandType',
    'CommandResult',
    'ConversationalAgent',
    'ConversationContext',
    'ConversationHistory',

    # Risk Management
    'RiskMetrics',
    'RiskMetricsCalculator',
    'quick_risk_assessment',
    'PositionSize',
    'PositionSizingMethod',
    'PositionSizingCalculator',
    'calculate_optimal_position'
]
