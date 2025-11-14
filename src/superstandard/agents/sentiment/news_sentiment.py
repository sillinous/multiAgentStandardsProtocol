"""
News Sentiment Provider

Analyzes sentiment from financial news sources including:
- News APIs (NewsAPI, Alpha Vantage, etc.)
- RSS feeds
- Financial news websites
- Press releases
- Analyst reports

In production, integrate with real news APIs.
This implementation provides the framework and mock data for testing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import random

from .sentiment_engine import SentimentScore, SentimentSource
from .sentiment_analyzer import TextSentimentAnalyzer, KeywordExtractor


# ============================================================================
# News Models
# ============================================================================

@dataclass
class NewsArticle:
    """News article"""

    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    symbol: Optional[str] = None
    author: Optional[str] = None
    sentiment_score: Optional[float] = None

    def to_dict(self):
        return {
            'title': self.title,
            'source': self.source,
            'url': self.url,
            'published_at': self.published_at.isoformat(),
            'symbol': self.symbol,
            'author': self.author,
            'sentiment_score': self.sentiment_score
        }


# ============================================================================
# News Sentiment Provider
# ============================================================================

class NewsSentimentProvider:
    """
    Provides sentiment analysis from financial news

    Fetches and analyzes news articles to determine market sentiment.

    Example:
        provider = NewsSentimentProvider()

        # Analyze news sentiment
        sentiment = provider.get_sentiment("AAPL")

        print(f"News Sentiment: {sentiment.sentiment_label}")
        print(f"Sample Size: {sentiment.sample_size} articles")
        print(f"Keywords: {sentiment.keywords}")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider

        Args:
            api_key: Optional API key for news service
        """
        self.api_key = api_key
        self.analyzer = TextSentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()

    def get_sentiment(
        self,
        symbol: str,
        time_window: timedelta = timedelta(hours=24)
    ) -> SentimentScore:
        """
        Get news sentiment for symbol

        Args:
            symbol: Stock symbol
            time_window: Time window for articles

        Returns:
            SentimentScore
        """
        # Fetch articles
        articles = self._fetch_articles(symbol, time_window)

        if not articles:
            # No news available
            return SentimentScore(
                source=SentimentSource.NEWS,
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                sample_size=0
            )

        # Analyze each article
        scores = []
        confidences = []
        all_keywords = []

        for article in articles:
            # Analyze title and content
            full_text = f"{article.title} {article.content}"
            score, confidence = self.analyzer.analyze(full_text)

            scores.append(score)
            confidences.append(confidence)

            # Extract keywords
            keywords = self.keyword_extractor.extract(full_text, top_n=5)
            all_keywords.extend(keywords)

            # Store in article
            article.sentiment_score = score

        # Calculate aggregate
        avg_score = sum(scores) / len(scores)
        avg_confidence = sum(confidences) / len(confidences)

        # Extract top keywords across all articles
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, _ in keyword_counts.most_common(10)]

        # Identify trending topics
        trending_topics = self._identify_trending_topics(articles)

        return SentimentScore(
            source=SentimentSource.NEWS,
            symbol=symbol,
            score=avg_score,
            confidence=avg_confidence,
            sample_size=len(articles),
            keywords=top_keywords,
            trending_topics=trending_topics,
            raw_data={
                'articles': [a.to_dict() for a in articles[:10]]  # Include top 10
            }
        )

    def _fetch_articles(
        self,
        symbol: str,
        time_window: timedelta
    ) -> List[NewsArticle]:
        """
        Fetch news articles for symbol

        In production, this would call a real news API like:
        - NewsAPI.org
        - Alpha Vantage News
        - Finnhub News
        - Custom scraper

        For now, returns mock data for testing.
        """
        if self.api_key:
            # TODO: Implement real API integration
            # Example: NewsAPI integration
            #  https://newsapi.org/docs/endpoints/everything
            pass

        # Mock data for testing
        return self._generate_mock_articles(symbol)

    def _generate_mock_articles(self, symbol: str) -> List[NewsArticle]:
        """Generate mock news articles for testing"""

        mock_articles = [
            NewsArticle(
                title=f"{symbol} Reports Strong Q4 Earnings, Beats Expectations",
                content=f"{symbol} announced record-breaking earnings today, surpassing analyst expectations. The company reported strong revenue growth driven by innovation and market expansion. Investors are bullish on future prospects.",
                source="Financial Times",
                url=f"https://example.com/news/1",
                published_at=datetime.now() - timedelta(hours=2),
                symbol=symbol,
                author="Jane Smith"
            ),
            NewsArticle(
                title=f"Analysts Upgrade {symbol} Stock to Buy",
                content=f"Major investment banks upgraded {symbol} stock rating to 'Buy' citing strong fundamentals and growth potential. The company's recent product launches have been well-received by the market.",
                source="Bloomberg",
                url=f"https://example.com/news/2",
                published_at=datetime.now() - timedelta(hours=5),
                symbol=symbol,
                author="John Doe"
            ),
            NewsArticle(
                title=f"{symbol} Announces New AI Initiative",
                content=f"{symbol} unveiled plans for major AI integration across its product line. The initiative is expected to drive significant revenue growth and operational efficiency. Tech analysts are optimistic about the company's direction.",
                source="Reuters",
                url=f"https://example.com/news/3",
                published_at=datetime.now() - timedelta(hours=12),
                symbol=symbol,
                author="Tech Desk"
            ),
            NewsArticle(
                title=f"Market Volatility Impacts {symbol} Trading",
                content=f"Recent market turbulence has affected {symbol} stock price, though analysts remain cautiously optimistic. The company's strong balance sheet positions it well to weather economic uncertainty.",
                source="WSJ",
                url=f"https://example.com/news/4",
                published_at=datetime.now() - timedelta(hours=18),
                symbol=symbol,
                author="Market Watch"
            ),
            NewsArticle(
                title=f"{symbol} CEO Discusses Future Growth Strategy",
                content=f"In an exclusive interview, {symbol}'s CEO outlined ambitious growth plans for the coming year. Focus areas include international expansion and new product development. Investor sentiment remains positive.",
                source="CNBC",
                url=f"https://example.com/news/5",
                published_at=datetime.now() - timedelta(hours=24),
                symbol=symbol,
                author="Business Reporter"
            )
        ]

        return mock_articles

    def _identify_trending_topics(self, articles: List[NewsArticle]) -> List[str]:
        """Identify trending topics across articles"""
        all_text = " ".join(f"{a.title} {a.content}" for a in articles)

        # Extract common phrases
        phrases = self.keyword_extractor.extract_phrases(all_text, top_n=5)

        return phrases


# ============================================================================
# Utility Functions
# ============================================================================

def create_news_sentiment_provider(api_key: Optional[str] = None) -> NewsSentimentProvider:
    """Create a news sentiment provider"""
    return NewsSentimentProvider(api_key=api_key)
