"""
Sentiment Integration with Explainable AI

Seamlessly integrates sentiment analysis into the explainable AI system,
adding sentiment as powerful reasoning factors in agent decisions.

This creates the FIRST truly hybrid system combining:
- Quantitative analysis (technical indicators)
- Qualitative analysis (sentiment)
- Explainable AI (full transparency)
"""

from typing import Dict, Any, List
from datetime import timedelta

from .explainable_ai import ReasoningFactor, ReasoningFactorType
from .sentiment import (
    SentimentEngine,
    NewsSentimentProvider,
    TwitterSentimentProvider,
    RedditSentimentProvider,
    SentimentSource
)


# ============================================================================
# Sentiment-Enhanced Market Data
# ============================================================================

class SentimentEnhancedData:
    """
    Enhances market data with sentiment analysis

    Takes traditional technical market data and adds
    multi-source sentiment intelligence.

    Example:
        enhancer = SentimentEnhancedData()

        # Traditional market data
        market_data = {
            'current_price': 175.50,
            'rsi': 45.0,
            'macd': 0.8
        }

        # Add sentiment!
        enhanced = enhancer.enhance(symbol="AAPL", market_data=market_data)

        # Now includes:
        # - news_sentiment
        # - twitter_sentiment
        # - reddit_sentiment
        # - overall_sentiment
        # - sentiment_trend
        # - trending_keywords
    """

    def __init__(
        self,
        enable_news: bool = True,
        enable_twitter: bool = True,
        enable_reddit: bool = True
    ):
        """
        Initialize sentiment enhancer

        Args:
            enable_news: Enable news sentiment
            enable_twitter: Enable Twitter sentiment
            enable_reddit: Enable Reddit sentiment
        """
        self.enable_news = enable_news
        self.enable_twitter = enable_twitter
        self.enable_reddit = enable_reddit

        # Initialize sentiment engine
        self.sentiment_engine = SentimentEngine()

        # Initialize providers
        self.news_provider = NewsSentimentProvider() if enable_news else None
        self.twitter_provider = TwitterSentimentProvider() if enable_twitter else None
        self.reddit_provider = RedditSentimentProvider() if enable_reddit else None

    def enhance(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance market data with sentiment

        Args:
            symbol: Stock symbol
            market_data: Traditional market data

        Returns:
            Enhanced market data with sentiment
        """
        # Copy original data
        enhanced = dict(market_data)

        # Fetch sentiment from all sources
        if self.news_provider:
            news_sentiment = self.news_provider.get_sentiment(symbol)
            self.sentiment_engine.add_score(news_sentiment)
            enhanced['news_sentiment'] = news_sentiment.score
            enhanced['news_sentiment_confidence'] = news_sentiment.confidence
            enhanced['news_sample_size'] = news_sentiment.sample_size

        if self.twitter_provider:
            twitter_sentiment = self.twitter_provider.get_sentiment(symbol)
            self.sentiment_engine.add_score(twitter_sentiment)
            enhanced['twitter_sentiment'] = twitter_sentiment.score
            enhanced['twitter_sentiment_confidence'] = twitter_sentiment.confidence
            enhanced['twitter_sample_size'] = twitter_sentiment.sample_size

        if self.reddit_provider:
            reddit_sentiment = self.reddit_provider.get_sentiment(symbol)
            self.sentiment_engine.add_score(reddit_sentiment)
            enhanced['reddit_sentiment'] = reddit_sentiment.score
            enhanced['reddit_sentiment_confidence'] = reddit_sentiment.confidence
            enhanced['reddit_sample_size'] = reddit_sentiment.sample_size

        # Get aggregated sentiment
        aggregated = self.sentiment_engine.get_aggregated_sentiment(symbol)

        if aggregated:
            enhanced['overall_sentiment'] = aggregated.overall_score
            enhanced['overall_sentiment_confidence'] = aggregated.confidence
            enhanced['sentiment_trend'] = aggregated.trend_direction
            enhanced['sentiment_trend_strength'] = aggregated.trend_strength
            enhanced['trending_keywords'] = aggregated.top_keywords
            enhanced['trending_topics'] = aggregated.trending_topics

        return enhanced

    def get_sentiment_reasoning_factors(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> List[ReasoningFactor]:
        """
        Get sentiment as reasoning factors for explainable AI

        Args:
            symbol: Stock symbol
            market_data: Market data (should be enhanced)

        Returns:
            List of ReasoningFactor objects
        """
        factors = []

        # News sentiment
        if 'news_sentiment' in market_data:
            score = market_data['news_sentiment']
            confidence = market_data.get('news_sentiment_confidence', 0.5)
            sample_size = market_data.get('news_sample_size', 0)

            influence = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"

            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.SENTIMENT,
                name="News Sentiment",
                value=score,
                weight=0.20,  # 20% weight
                confidence=confidence,
                influence=influence,
                explanation=f"News sentiment {self._sentiment_label(score)} ({score:+.2f}) based on {sample_size} articles",
                supporting_data={
                    'sample_size': sample_size,
                    'source': 'news'
                }
            ))

        # Twitter sentiment
        if 'twitter_sentiment' in market_data:
            score = market_data['twitter_sentiment']
            confidence = market_data.get('twitter_sentiment_confidence', 0.5)
            sample_size = market_data.get('twitter_sample_size', 0)

            influence = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"

            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.SENTIMENT,
                name="Twitter Sentiment",
                value=score,
                weight=0.15,  # 15% weight
                confidence=confidence,
                influence=influence,
                explanation=f"Twitter sentiment {self._sentiment_label(score)} ({score:+.2f}) from {sample_size} tweets",
                supporting_data={
                    'sample_size': sample_size,
                    'source': 'twitter'
                }
            ))

        # Reddit sentiment
        if 'reddit_sentiment' in market_data:
            score = market_data['reddit_sentiment']
            confidence = market_data.get('reddit_sentiment_confidence', 0.5)
            sample_size = market_data.get('reddit_sample_size', 0)

            influence = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"

            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.SENTIMENT,
                name="Reddit Sentiment",
                value=score,
                weight=0.12,  # 12% weight
                confidence=confidence,
                influence=influence,
                explanation=f"Reddit sentiment {self._sentiment_label(score)} ({score:+.2f}) across {sample_size} posts",
                supporting_data={
                    'sample_size': sample_size,
                    'source': 'reddit'
                }
            ))

        # Overall aggregated sentiment
        if 'overall_sentiment' in market_data:
            score = market_data['overall_sentiment']
            confidence = market_data.get('overall_sentiment_confidence', 0.5)
            trend = market_data.get('sentiment_trend', 'neutral')
            keywords = market_data.get('trending_keywords', [])

            influence = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"

            keyword_str = ", ".join(keywords[:5]) if keywords else "N/A"

            factors.append(ReasoningFactor(
                factor_type=ReasoningFactorType.SENTIMENT,
                name="Overall Market Sentiment",
                value=score,
                weight=0.25,  # 25% weight for aggregated
                confidence=confidence,
                influence=influence,
                explanation=f"Multi-source sentiment {self._sentiment_label(score)} ({score:+.2f}), trending {trend}. Keywords: {keyword_str}",
                supporting_data={
                    'trend': trend,
                    'keywords': keywords
                }
            ))

        return factors

    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.5:
            return "very positive"
        elif score > 0.2:
            return "positive"
        elif score > -0.2:
            return "neutral"
        elif score > -0.5:
            return "negative"
        else:
            return "very negative"


# ============================================================================
# Integration Helper
# ============================================================================

def create_sentiment_enhanced_ensemble(ensemble, enable_all: bool = True):
    """
    Create a sentiment-enhanced explainable ensemble

    Args:
        ensemble: AgentEnsemble to enhance
        enable_all: Enable all sentiment sources

    Returns:
        Tuple of (ExplainableAgentEnsemble, SentimentEnhancedData)
    """
    from .explainable_ensemble import create_explainable_ensemble

    # Create explainable ensemble
    explainable = create_explainable_ensemble(ensemble)

    # Create sentiment enhancer
    enhancer = SentimentEnhancedData(
        enable_news=enable_all,
        enable_twitter=enable_all,
        enable_reddit=enable_all
    )

    return explainable, enhancer


# ============================================================================
# Complete Workflow Function
# ============================================================================

def make_sentiment_aware_decision(
    explainable_ensemble,
    sentiment_enhancer,
    symbol: str,
    market_data: Dict[str, Any]
):
    """
    Make a decision with full sentiment integration

    This is the complete workflow combining:
    1. Sentiment analysis from multiple sources
    2. Technical analysis
    3. Ensemble decision-making
    4. Full explainability

    Example:
        # Setup
        ensemble = TemplateLibrary().get_template("balanced_trader").create_ensemble()
        explainable, enhancer = create_sentiment_enhanced_ensemble(ensemble)

        # Make decision
        decision = make_sentiment_aware_decision(
            explainable,
            enhancer,
            symbol="AAPL",
            market_data={'current_price': 175.50, 'rsi': 45.0}
        )

        # Explanation now includes sentiment!
        print(decision.explanation.natural_language_summary)
    """
    # Step 1: Enhance market data with sentiment
    enhanced_data = sentiment_enhancer.enhance(symbol, market_data)

    # Step 2: Get sentiment reasoning factors
    sentiment_factors = sentiment_enhancer.get_sentiment_reasoning_factors(
        symbol,
        enhanced_data
    )

    # Step 3: Make explainable decision
    decision = explainable_ensemble.make_explainable_decision(
        symbol=symbol,
        market_data=enhanced_data
    )

    # Step 4: Add sentiment factors to explanation
    if decision.explanation:
        decision.explanation.reasoning_factors.extend(sentiment_factors)

        # Regenerate summary with sentiment
        decision.explanation.natural_language_summary = \
            explainable_ensemble.explanation_engine._generate_summary(decision.explanation)

    return decision
