"""
Social Media Sentiment Provider

Analyzes sentiment from social media sources including:
- Twitter/X
- Reddit (r/wallstreetbets, r/stocks, etc.)
- StockTwits
- Discord servers
- Other forums

In production, integrate with real social media APIs.
This implementation provides the framework and mock data for testing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import random

from .sentiment_engine import SentimentScore, SentimentSource
from .sentiment_analyzer import TextSentimentAnalyzer, KeywordExtractor


# ============================================================================
# Social Media Models
# ============================================================================

@dataclass
class SocialPost:
    """Social media post"""

    content: str
    author: str
    platform: str  # "twitter", "reddit", etc.
    posted_at: datetime
    symbol: Optional[str] = None
    likes: int = 0
    retweets: int = 0  # Or upvotes for Reddit
    replies: int = 0
    url: Optional[str] = None
    sentiment_score: Optional[float] = None

    @property
    def engagement(self) -> int:
        """Total engagement"""
        return self.likes + self.retweets + self.replies

    def to_dict(self):
        return {
            'content': self.content[:200] + "..." if len(self.content) > 200 else self.content,
            'author': self.author,
            'platform': self.platform,
            'posted_at': self.posted_at.isoformat(),
            'symbol': self.symbol,
            'engagement': self.engagement,
            'sentiment_score': self.sentiment_score
        }


# ============================================================================
# Twitter Sentiment Provider
# ============================================================================

class TwitterSentimentProvider:
    """
    Provides sentiment analysis from Twitter/X

    Analyzes tweets mentioning specific stocks or tickers.

    Example:
        provider = TwitterSentimentProvider()

        sentiment = provider.get_sentiment("AAPL")

        print(f"Twitter Sentiment: {sentiment.sentiment_label}")
        print(f"Sample: {sentiment.sample_size} tweets")
        print(f"Trending: {sentiment.trending_topics}")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider

        Args:
            api_key: Optional Twitter API key
        """
        self.api_key = api_key
        self.analyzer = TextSentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()

    def get_sentiment(
        self,
        symbol: str,
        time_window: timedelta = timedelta(hours=6),
        min_engagement: int = 0
    ) -> SentimentScore:
        """
        Get Twitter sentiment for symbol

        Args:
            symbol: Stock symbol
            time_window: Time window for tweets
            min_engagement: Minimum engagement threshold

        Returns:
            SentimentScore
        """
        # Fetch tweets
        tweets = self._fetch_tweets(symbol, time_window)

        # Filter by engagement
        tweets = [t for t in tweets if t.engagement >= min_engagement]

        if not tweets:
            return SentimentScore(
                source=SentimentSource.TWITTER,
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                sample_size=0
            )

        # Analyze each tweet
        scores = []
        confidences = []
        all_keywords = []

        for tweet in tweets:
            score, confidence = self.analyzer.analyze(tweet.content)

            # Weight by engagement (more engaged tweets matter more)
            weight = min(tweet.engagement / 1000.0, 2.0)  # Cap at 2x weight
            scores.append(score * weight)
            confidences.append(confidence * weight)

            # Extract keywords
            keywords = self.keyword_extractor.extract(tweet.content, top_n=3)
            all_keywords.extend(keywords)

            tweet.sentiment_score = score

        # Calculate weighted average
        total_weight = sum(min(t.engagement / 1000.0, 2.0) for t in tweets)
        avg_score = sum(scores) / total_weight if total_weight > 0 else 0.0
        avg_confidence = sum(confidences) / total_weight if total_weight > 0 else 0.0

        # Extract trending keywords
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, _ in keyword_counts.most_common(10)]

        # Identify trending hashtags
        trending_topics = self._extract_hashtags(tweets)

        return SentimentScore(
            source=SentimentSource.TWITTER,
            symbol=symbol,
            score=avg_score,
            confidence=min(avg_confidence, 1.0),
            sample_size=len(tweets),
            keywords=top_keywords,
            trending_topics=trending_topics,
            raw_data={
                'top_tweets': [t.to_dict() for t in sorted(tweets, key=lambda x: x.engagement, reverse=True)[:5]]
            }
        )

    def _fetch_tweets(self, symbol: str, time_window: timedelta) -> List[SocialPost]:
        """
        Fetch tweets for symbol

        In production, use Twitter API v2:
        https://developer.twitter.com/en/docs/twitter-api

        For now, returns mock data.
        """
        if self.api_key:
            # TODO: Implement real Twitter API integration
            pass

        return self._generate_mock_tweets(symbol)

    def _generate_mock_tweets(self, symbol: str) -> List[SocialPost]:
        """Generate mock tweets for testing"""

        mock_tweets = [
            SocialPost(
                content=f"${symbol} to the moon! 🚀 Strong earnings + AI innovation = bullish AF. Loading up more calls.",
                author="@trader_pro",
                platform="twitter",
                posted_at=datetime.now() - timedelta(hours=1),
                symbol=symbol,
                likes=245,
                retweets=89,
                replies=34
            ),
            SocialPost(
                content=f"${symbol} breakout confirmed! Technical setup looking beautiful. Target: +20% 📈",
                author="@chart_wizard",
                platform="twitter",
                posted_at=datetime.now() - timedelta(hours=2),
                symbol=symbol,
                likes=156,
                retweets=67,
                replies=23
            ),
            SocialPost(
                content=f"Just bought ${symbol} dip. Long-term holder here. Fundamentals too strong to ignore.",
                author="@value_investor",
                platform="twitter",
                posted_at=datetime.now() - timedelta(hours=3),
                symbol=symbol,
                likes=423,
                retweets=145,
                replies=78
            ),
            SocialPost(
                content=f"${symbol} looking risky here. Overbought on RSI, might see some profit-taking soon.",
                author="@cautious_trader",
                platform="twitter",
                posted_at=datetime.now() - timedelta(hours=4),
                symbol=symbol,
                likes=98,
                retweets=45,
                replies=56
            ),
            SocialPost(
                content=f"${symbol} earnings call was 🔥 Management guidance exceeded expectations. This is going higher.",
                author="@earnings_watcher",
                platform="twitter",
                posted_at=datetime.now() - timedelta(hours=5),
                symbol=symbol,
                likes=312,
                retweets=123,
                replies=67
            )
        ]

        return mock_tweets

    def _extract_hashtags(self, tweets: List[SocialPost]) -> List[str]:
        """Extract trending hashtags from tweets"""
        hashtags = []

        for tweet in tweets:
            # Find hashtags
            import re
            found = re.findall(r'#\w+', tweet.content)
            hashtags.extend(found)

        # Count and return top 5
        from collections import Counter
        counts = Counter(hashtags)
        return [tag for tag, _ in counts.most_common(5)]


# ============================================================================
# Reddit Sentiment Provider
# ============================================================================

class RedditSentimentProvider:
    """
    Provides sentiment analysis from Reddit

    Focuses on investment-related subreddits like:
    - r/wallstreetbets
    - r/stocks
    - r/investing
    - r/options

    Example:
        provider = RedditSentimentProvider()

        sentiment = provider.get_sentiment("AAPL")

        print(f"Reddit Sentiment: {sentiment.sentiment_label}")
        print(f"Sample: {sentiment.sample_size} posts")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider

        Args:
            api_key: Optional Reddit API credentials
        """
        self.api_key = api_key
        self.analyzer = TextSentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()

        # Subreddits to monitor
        self.subreddits = [
            'wallstreetbets',
            'stocks',
            'investing',
            'options',
            'stockmarket'
        ]

    def get_sentiment(
        self,
        symbol: str,
        time_window: timedelta = timedelta(hours=24),
        min_upvotes: int = 10
    ) -> SentimentScore:
        """
        Get Reddit sentiment for symbol

        Args:
            symbol: Stock symbol
            time_window: Time window for posts
            min_upvotes: Minimum upvote threshold

        Returns:
            SentimentScore
        """
        # Fetch posts
        posts = self._fetch_posts(symbol, time_window)

        # Filter by upvotes
        posts = [p for p in posts if p.likes >= min_upvotes]

        if not posts:
            return SentimentScore(
                source=SentimentSource.REDDIT,
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                sample_size=0
            )

        # Analyze each post
        scores = []
        confidences = []
        all_keywords = []

        for post in posts:
            score, confidence = self.analyzer.analyze(post.content)

            # Weight by upvotes
            weight = min(post.likes / 100.0, 2.0)  # Cap at 2x
            scores.append(score * weight)
            confidences.append(confidence * weight)

            # Extract keywords
            keywords = self.keyword_extractor.extract(post.content, top_n=3)
            all_keywords.extend(keywords)

            post.sentiment_score = score

        # Calculate weighted average
        total_weight = sum(min(p.likes / 100.0, 2.0) for p in posts)
        avg_score = sum(scores) / total_weight if total_weight > 0 else 0.0
        avg_confidence = sum(confidences) / total_weight if total_weight > 0 else 0.0

        # Extract trending keywords
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, _ in keyword_counts.most_common(10)]

        # Trending topics
        trending = self._identify_trending_topics(posts)

        return SentimentScore(
            source=SentimentSource.REDDIT,
            symbol=symbol,
            score=avg_score,
            confidence=min(avg_confidence, 1.0),
            sample_size=len(posts),
            keywords=top_keywords,
            trending_topics=trending,
            raw_data={
                'top_posts': [p.to_dict() for p in sorted(posts, key=lambda x: x.likes, reverse=True)[:5]]
            }
        )

    def _fetch_posts(self, symbol: str, time_window: timedelta) -> List[SocialPost]:
        """
        Fetch Reddit posts for symbol

        In production, use Reddit API (PRAW):
        https://praw.readthedocs.io/

        For now, returns mock data.
        """
        if self.api_key:
            # TODO: Implement real Reddit API integration
            pass

        return self._generate_mock_posts(symbol)

    def _generate_mock_posts(self, symbol: str) -> List[SocialPost]:
        """Generate mock Reddit posts for testing"""

        mock_posts = [
            SocialPost(
                content=f"{symbol} DD: Why I'm All-In 🚀\n\nBeen doing deep research on {symbol} and the fundamentals are insane. Revenue growth, expanding margins, innovation pipeline. This is a 10-bagger waiting to happen. Position: 500 shares + Jan calls.",
                author="DeepValue42",
                platform="reddit",
                posted_at=datetime.now() - timedelta(hours=6),
                symbol=symbol,
                likes=1247,
                retweets=0,  # Reddit doesn't have retweets, using for upvotes
                replies=234
            ),
            SocialPost(
                content=f"{symbol} is printing money right now. Just closed my position for 40% gain. Thanks WSB! 💎🙌",
                author="TendieHunter",
                platform="reddit",
                posted_at=datetime.now() - timedelta(hours=12),
                symbol=symbol,
                likes=892,
                retweets=0,
                replies=156
            ),
            SocialPost(
                content=f"Thoughts on {symbol}? Considering a position but valuation seems high. Anyone have analysis?",
                author="CautiousInvestor",
                platform="reddit",
                posted_at=datetime.now() - timedelta(hours=18),
                symbol=symbol,
                likes=234,
                retweets=0,
                replies=89
            ),
            SocialPost(
                content=f"{symbol} is a long-term hold for me. Don't care about short-term volatility. The thesis is solid.",
                author="PatientCapital",
                platform="reddit",
                posted_at=datetime.now() - timedelta(hours=20),
                symbol=symbol,
                likes=567,
                retweets=0,
                replies=123
            )
        ]

        return mock_posts

    def _identify_trending_topics(self, posts: List[SocialPost]) -> List[str]:
        """Identify trending topics from posts"""
        all_text = " ".join(p.content for p in posts)
        phrases = self.keyword_extractor.extract_phrases(all_text, top_n=3)
        return phrases


# ============================================================================
# Utility Functions
# ============================================================================

def create_twitter_provider(api_key: Optional[str] = None) -> TwitterSentimentProvider:
    """Create a Twitter sentiment provider"""
    return TwitterSentimentProvider(api_key=api_key)


def create_reddit_provider(api_key: Optional[str] = None) -> RedditSentimentProvider:
    """Create a Reddit sentiment provider"""
    return RedditSentimentProvider(api_key=api_key)
