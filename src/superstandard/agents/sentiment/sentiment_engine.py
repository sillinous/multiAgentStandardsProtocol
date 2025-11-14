"""
Core Sentiment Analysis Engine

Provides multi-source sentiment analysis for trading decisions,
combining news, social media, and other qualitative data sources.

Features:
- Multi-source sentiment aggregation
- Real-time sentiment scoring
- Historical sentiment tracking
- Trend analysis
- Source weighting and confidence
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import statistics


# ============================================================================
# Sentiment Models
# ============================================================================

class SentimentSource(str, Enum):
    """Sentiment data sources"""
    NEWS = "news"
    TWITTER = "twitter"
    REDDIT = "reddit"
    EARNINGS_CALL = "earnings_call"
    SEC_FILING = "sec_filing"
    ANALYST_RATING = "analyst_rating"
    CUSTOM = "custom"


@dataclass
class SentimentScore:
    """Sentiment score from a single source"""

    source: SentimentSource
    symbol: str
    score: float  # -1.0 (very negative) to +1.0 (very positive)
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Additional context
    sample_size: int = 0  # Number of items analyzed
    keywords: List[str] = field(default_factory=list)
    trending_topics: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def sentiment_label(self) -> str:
        """Human-readable sentiment label"""
        if self.score > 0.5:
            return "Very Positive"
        elif self.score > 0.2:
            return "Positive"
        elif self.score > -0.2:
            return "Neutral"
        elif self.score > -0.5:
            return "Negative"
        else:
            return "Very Negative"

    @property
    def sentiment_emoji(self) -> str:
        """Emoji representation"""
        if self.score > 0.5:
            return "🚀"
        elif self.score > 0.2:
            return "📈"
        elif self.score > -0.2:
            return "➡️"
        elif self.score > -0.5:
            return "📉"
        else:
            return "💀"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source.value,
            'symbol': self.symbol,
            'score': self.score,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'sentiment_label': self.sentiment_label,
            'sentiment_emoji': self.sentiment_emoji,
            'sample_size': self.sample_size,
            'keywords': self.keywords,
            'trending_topics': self.trending_topics
        }


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment from multiple sources"""

    symbol: str
    overall_score: float  # Weighted average
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

    # Source breakdown
    source_scores: Dict[SentimentSource, SentimentScore] = field(default_factory=dict)

    # Trends
    trend_direction: str = "neutral"  # "bullish", "bearish", "neutral"
    trend_strength: float = 0.0  # 0.0 to 1.0

    # Keywords across all sources
    top_keywords: List[str] = field(default_factory=list)
    trending_topics: List[str] = field(default_factory=list)

    @property
    def sentiment_label(self) -> str:
        """Human-readable label"""
        if self.overall_score > 0.5:
            return "Very Positive"
        elif self.overall_score > 0.2:
            return "Positive"
        elif self.overall_score > -0.2:
            return "Neutral"
        elif self.overall_score > -0.5:
            return "Negative"
        else:
            return "Very Negative"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'overall_score': self.overall_score,
            'confidence': self.confidence,
            'sentiment_label': self.sentiment_label,
            'timestamp': self.timestamp.isoformat(),
            'source_scores': {
                source.value: score.to_dict()
                for source, score in self.source_scores.items()
            },
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength,
            'top_keywords': self.top_keywords,
            'trending_topics': self.trending_topics
        }


# ============================================================================
# Sentiment Engine
# ============================================================================

class SentimentEngine:
    """
    Core sentiment analysis engine

    Aggregates sentiment from multiple sources, tracks trends,
    and provides comprehensive sentiment intelligence.

    Example:
        engine = SentimentEngine()

        # Add sentiment scores from various sources
        engine.add_score(news_sentiment)
        engine.add_score(twitter_sentiment)
        engine.add_score(reddit_sentiment)

        # Get aggregated sentiment
        sentiment = engine.get_aggregated_sentiment("AAPL")

        print(f"Sentiment: {sentiment.sentiment_label}")
        print(f"Score: {sentiment.overall_score:.2f}")
        print(f"Top Keywords: {sentiment.top_keywords}")
    """

    def __init__(
        self,
        source_weights: Optional[Dict[SentimentSource, float]] = None
    ):
        """
        Initialize sentiment engine

        Args:
            source_weights: Optional weights for each source (defaults to equal)
        """
        self.source_weights = source_weights or {
            SentimentSource.NEWS: 0.30,
            SentimentSource.TWITTER: 0.20,
            SentimentSource.REDDIT: 0.15,
            SentimentSource.EARNINGS_CALL: 0.20,
            SentimentSource.ANALYST_RATING: 0.15
        }

        # Storage
        self.sentiment_scores: Dict[str, List[SentimentScore]] = {}
        self.sentiment_history: Dict[str, List[AggregatedSentiment]] = {}

    def add_score(self, score: SentimentScore):
        """Add a sentiment score"""
        symbol = score.symbol

        if symbol not in self.sentiment_scores:
            self.sentiment_scores[symbol] = []

        self.sentiment_scores[symbol].append(score)

        # Keep only recent scores (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.sentiment_scores[symbol] = [
            s for s in self.sentiment_scores[symbol]
            if s.timestamp > cutoff
        ]

    def get_aggregated_sentiment(
        self,
        symbol: str,
        time_window: Optional[timedelta] = None
    ) -> Optional[AggregatedSentiment]:
        """
        Get aggregated sentiment for a symbol

        Args:
            symbol: Stock symbol
            time_window: Optional time window (defaults to last 6 hours)

        Returns:
            AggregatedSentiment or None
        """
        if symbol not in self.sentiment_scores:
            return None

        # Filter by time window
        time_window = time_window or timedelta(hours=6)
        cutoff = datetime.now() - time_window

        recent_scores = [
            s for s in self.sentiment_scores[symbol]
            if s.timestamp > cutoff
        ]

        if not recent_scores:
            return None

        # Group by source
        source_scores: Dict[SentimentSource, SentimentScore] = {}
        for score in recent_scores:
            # Keep most recent score per source
            if score.source not in source_scores or \
               score.timestamp > source_scores[score.source].timestamp:
                source_scores[score.source] = score

        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        confidence_sum = 0.0

        for source, score in source_scores.items():
            weight = self.source_weights.get(source, 0.1)
            weighted_sum += score.score * weight * score.confidence
            confidence_sum += score.confidence * weight
            total_weight += weight

        if total_weight == 0:
            return None

        overall_score = weighted_sum / total_weight
        overall_confidence = confidence_sum / total_weight

        # Extract keywords and topics
        all_keywords = []
        all_topics = []

        for score in source_scores.values():
            all_keywords.extend(score.keywords)
            all_topics.extend(score.trending_topics)

        # Count frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Top keywords
        top_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        top_keywords = [k for k, _ in top_keywords]

        # Detect trend
        trend_direction, trend_strength = self._detect_trend(symbol)

        # Create aggregated sentiment
        aggregated = AggregatedSentiment(
            symbol=symbol,
            overall_score=overall_score,
            confidence=overall_confidence,
            source_scores=source_scores,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            top_keywords=top_keywords,
            trending_topics=list(set(all_topics))[:5]
        )

        # Store in history
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = []

        self.sentiment_history[symbol].append(aggregated)

        # Keep last 100 aggregations
        self.sentiment_history[symbol] = self.sentiment_history[symbol][-100:]

        return aggregated

    def _detect_trend(self, symbol: str) -> tuple[str, float]:
        """
        Detect sentiment trend direction and strength

        Returns:
            (direction, strength) where direction is "bullish", "bearish", or "neutral"
        """
        if symbol not in self.sentiment_history or \
           len(self.sentiment_history[symbol]) < 3:
            return "neutral", 0.0

        # Get recent history
        recent = self.sentiment_history[symbol][-10:]

        # Calculate trend
        scores = [s.overall_score for s in recent]

        # Linear regression slope
        n = len(scores)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(scores)

        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "neutral", 0.0

        slope = numerator / denominator

        # Determine direction and strength
        if slope > 0.05:
            return "bullish", min(abs(slope) * 2, 1.0)
        elif slope < -0.05:
            return "bearish", min(abs(slope) * 2, 1.0)
        else:
            return "neutral", 0.0

    def get_sentiment_history(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[AggregatedSentiment]:
        """Get historical aggregated sentiment"""
        if symbol not in self.sentiment_history:
            return []

        return self.sentiment_history[symbol][-limit:]

    def get_source_breakdown(
        self,
        symbol: str
    ) -> Dict[SentimentSource, SentimentScore]:
        """Get breakdown by source"""
        sentiment = self.get_aggregated_sentiment(symbol)
        if not sentiment:
            return {}

        return sentiment.source_scores


# ============================================================================
# Sentiment Aggregator (Utility)
# ============================================================================

class SentimentAggregator:
    """
    Utility for aggregating multiple sentiment engines

    Useful for combining different analysis strategies
    """

    @staticmethod
    def combine_scores(
        scores: List[SentimentScore],
        weights: Optional[List[float]] = None
    ) -> float:
        """
        Combine multiple scores with optional weights

        Args:
            scores: List of sentiment scores
            weights: Optional weights (defaults to equal)

        Returns:
            Combined score (-1.0 to +1.0)
        """
        if not scores:
            return 0.0

        if weights is None:
            weights = [1.0] * len(scores)

        if len(scores) != len(weights):
            raise ValueError("Scores and weights must have same length")

        total_weight = 0.0
        weighted_sum = 0.0

        for score, weight in zip(scores, weights):
            # Weight by confidence
            effective_weight = weight * score.confidence
            weighted_sum += score.score * effective_weight
            total_weight += effective_weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    @staticmethod
    def normalize_score(score: float, old_min: float, old_max: float) -> float:
        """
        Normalize score to -1.0 to +1.0 range

        Args:
            score: Original score
            old_min: Original minimum value
            old_max: Original maximum value

        Returns:
            Normalized score
        """
        # Normalize to 0-1
        if old_max == old_min:
            return 0.0

        normalized = (score - old_min) / (old_max - old_min)

        # Convert to -1 to +1
        return (normalized * 2.0) - 1.0
