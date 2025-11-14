# Sentiment Analysis Integration Guide 💭📊

**Revolutionary multi-source sentiment analysis seamlessly integrated with explainable AI for fully transparent qualitative + quantitative trading decisions.**

## Table of Contents

1. [Overview](#overview)
2. [Why Sentiment Analysis Matters](#why-sentiment-analysis-matters)
3. [Quick Start](#quick-start)
4. [Core Components](#core-components)
5. [Sentiment Sources](#sentiment-sources)
6. [Integration with Explainable AI](#integration-with-explainable-ai)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## Overview

The Sentiment Analysis System provides multi-source market sentiment intelligence, combining:

✅ **News Sentiment** - Financial news from major sources
✅ **Twitter Sentiment** - Social media buzz and trending topics
✅ **Reddit Sentiment** - Community sentiment from investment subreddits
✅ **Aggregated Sentiment** - Multi-source weighted aggregation
✅ **Trend Detection** - Identify improving/declining sentiment
✅ **Explainable Integration** - Full transparency in decisions

**This is the FIRST platform to seamlessly combine qualitative sentiment with quantitative analysis in a fully explainable way!** 🎯

---

## Why Sentiment Analysis Matters

### The Problem

Traditional quant trading systems ignore qualitative data:
- Miss major news events
- Ignore social media trends
- No sentiment context
- Pure technical analysis can be blind

### Our Solution

**Hybrid Quant + Qualitative Analysis:**

```
Before (Quant Only)          After (Hybrid)
════════════════════         ══════════════
Technical Indicators    →    Technical Indicators
Price Action           →    Price Action
Volume                 →    Volume
                            + News Sentiment 📰
                            + Twitter Buzz 🐦
                            + Reddit Consensus 📱
                            + Trending Topics 🔥
                            ────────────────────
                            = COMPLETE PICTURE ✨
```

---

## Quick Start

### Installation

Already included! No additional dependencies for mock data.

For production with real APIs:
```bash
pip install newsapi-python  # News API
pip install tweepy          # Twitter API
pip install praw            # Reddit API
```

### Basic Usage

```python
from superstandard.agents import (
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,
    make_sentiment_aware_decision
)

# 1. Create ensemble
library = TemplateLibrary()
ensemble = library.get_template("balanced_trader").create_ensemble()

# 2. Add sentiment intelligence
explainable, enhancer = create_sentiment_enhanced_ensemble(ensemble)

# 3. Make sentiment-aware decision
market_data = {
    'current_price': 175.50,
    'rsi': 45.0,
    'macd': 0.8
}

decision = make_sentiment_aware_decision(
    explainable,
    enhancer,
    symbol="AAPL",
    market_data=market_data
)

# 4. View explanation (now includes sentiment!)
print(decision.explanation.natural_language_summary)

# Output includes sentiment factors:
# "Key factors:
#  1. 📈 RSI: Bullish momentum at 45.0
#  2. 💭 News Sentiment: Positive (+0.75) based on 127 articles
#  3. 📱 Twitter Sentiment: Very positive (+0.82) from 1,247 tweets
#  4. 📊 Overall Market Sentiment: Positive (+0.78), trending bullish"
```

### Run the Demo

```bash
python examples/sentiment_analysis_demo.py
```

---

## Core Components

### 1. Sentiment Score

Every sentiment analysis returns a `SentimentScore`:

```python
@dataclass
class SentimentScore:
    source: SentimentSource           # Where it came from
    symbol: str                       # Stock symbol
    score: float                      # -1.0 to +1.0
    confidence: float                 # 0.0 to 1.0
    sample_size: int                  # Number of items analyzed
    keywords: List[str]               # Top keywords found
    trending_topics: List[str]        # Trending topics

    # Properties
    sentiment_label: str              # "Very Positive", "Positive", etc.
    sentiment_emoji: str              # 🚀, 📈, ➡️, 📉, 💀
```

**Score Interpretation:**
- `+0.5 to +1.0` = Very Positive 🚀
- `+0.2 to +0.5` = Positive 📈
- `-0.2 to +0.2` = Neutral ➡️
- `-0.5 to -0.2` = Negative 📉
- `-1.0 to -0.5` = Very Negative 💀

### 2. Sentiment Engine

Central engine for multi-source aggregation:

```python
from superstandard.agents import SentimentEngine

engine = SentimentEngine()

# Add scores from different sources
engine.add_score(news_sentiment)
engine.add_score(twitter_sentiment)
engine.add_score(reddit_sentiment)

# Get aggregated sentiment
aggregated = engine.get_aggregated_sentiment("AAPL")

print(f"Overall: {aggregated.overall_score:+.2f}")
print(f"Trend: {aggregated.trend_direction}")
print(f"Keywords: {aggregated.top_keywords}")
```

### 3. Sentiment Enhanced Data

Automatically enhances market data with sentiment:

```python
from superstandard.agents import SentimentEnhancedData

enhancer = SentimentEnhancedData()

# Traditional data
market_data = {'current_price': 175.50, 'rsi': 45.0}

# Enhance with sentiment
enhanced = enhancer.enhance("AAPL", market_data)

# Now includes:
# - news_sentiment
# - twitter_sentiment
# - reddit_sentiment
# - overall_sentiment
# - sentiment_trend
# - trending_keywords
```

---

## Sentiment Sources

### News Sentiment

Analyzes financial news articles:

```python
from superstandard.agents import NewsSentimentProvider

provider = NewsSentimentProvider()
sentiment = provider.get_sentiment("AAPL")

print(f"News: {sentiment.sentiment_label}")
print(f"Sample: {sentiment.sample_size} articles")
print(f"Keywords: {sentiment.keywords}")
```

**Sources Supported** (in production):
- NewsAPI.org
- Alpha Vantage News
- Finnhub News
- Custom RSS feeds
- Financial websites

### Twitter Sentiment

Analyzes tweets mentioning the stock:

```python
from superstandard.agents import TwitterSentimentProvider

provider = TwitterSentimentProvider()
sentiment = provider.get_sentiment("AAPL")

print(f"Twitter: {sentiment.sentiment_label}")
print(f"Sample: {sentiment.sample_size} tweets")
print(f"Trending: {sentiment.trending_topics}")
```

**Features:**
- Engagement weighting (popular tweets matter more)
- Hashtag extraction
- Trending topic identification
- Bot filtering (in production)

### Reddit Sentiment

Analyzes posts from investment subreddits:

```python
from superstandard.agents import RedditSentimentProvider

provider = RedditSentimentProvider()
sentiment = provider.get_sentiment("AAPL")

print(f"Reddit: {sentiment.sentiment_label}")
print(f"Sample: {sentiment.sample_size} posts")
```

**Subreddits Monitored:**
- r/wallstreetbets
- r/stocks
- r/investing
- r/options
- r/stockmarket

---

## Integration with Explainable AI

### Sentiment as Reasoning Factors

Sentiment automatically becomes reasoning factors in decisions:

```python
decision = make_sentiment_aware_decision(
    explainable,
    enhancer,
    symbol="AAPL",
    market_data=market_data
)

# Reasoning factors now include:
for factor in decision.explanation.reasoning_factors:
    if factor.factor_type == ReasoningFactorType.SENTIMENT:
        print(f"{factor.name}: {factor.explanation}")

# Output:
# News Sentiment: Positive (+0.75) based on 127 articles
# Twitter Sentiment: Very positive (+0.82) from 1,247 tweets
# Overall Market Sentiment: Positive (+0.78), trending bullish
```

### Natural Language Q&A

Ask questions about sentiment:

```python
# Ask about sentiment
answer = explainable.ask("What does sentiment say?", decision.explanation_id)
print(answer)

# Ask about specific sources
answer = explainable.ask("What's the Twitter sentiment?", decision.explanation_id)
print(answer)
```

### Decision Replay with Sentiment

Track sentiment trends over time:

```python
from superstandard.agents import DecisionReplayEngine

replay = DecisionReplayEngine()

# Record decisions with sentiment
replay.record_decision(decision.explanation)

# Analyze sentiment patterns
insights = replay.get_learning_insights("AAPL")
# "✅ Positive sentiment correlates with +15% higher success rate"
```

---

## API Reference

### SentimentEngine

```python
class SentimentEngine:
    def __init__(source_weights: Dict[SentimentSource, float])
    def add_score(score: SentimentScore)
    def get_aggregated_sentiment(symbol: str) -> AggregatedSentiment
    def get_sentiment_history(symbol: str, limit: int) -> List[AggregatedSentiment]
```

### NewsSentimentProvider

```python
class NewsSentimentProvider:
    def __init__(api_key: Optional[str])
    def get_sentiment(symbol: str, time_window: timedelta) -> SentimentScore
```

### TwitterSentimentProvider

```python
class TwitterSentimentProvider:
    def __init__(api_key: Optional[str])
    def get_sentiment(
        symbol: str,
        time_window: timedelta,
        min_engagement: int
    ) -> SentimentScore
```

### RedditSentimentProvider

```python
class RedditSentimentProvider:
    def __init__(api_key: Optional[str])
    def get_sentiment(
        symbol: str,
        time_window: timedelta,
        min_upvotes: int
    ) -> SentimentScore
```

### SentimentEnhancedData

```python
class SentimentEnhancedData:
    def __init__(
        enable_news: bool = True,
        enable_twitter: bool = True,
        enable_reddit: bool = True
    )

    def enhance(symbol: str, market_data: Dict) -> Dict

    def get_sentiment_reasoning_factors(
        symbol: str,
        market_data: Dict
    ) -> List[ReasoningFactor]
```

### Integration Functions

```python
def create_sentiment_enhanced_ensemble(ensemble):
    """Create ensemble with sentiment intelligence"""

def make_sentiment_aware_decision(
    explainable_ensemble,
    sentiment_enhancer,
    symbol: str,
    market_data: Dict
):
    """Make decision with full sentiment + explainability"""
```

---

## Best Practices

### 1. Use Multiple Sources

```python
# ✅ Good: Multi-source for robust sentiment
enhancer = SentimentEnhancedData(
    enable_news=True,
    enable_twitter=True,
    enable_reddit=True
)

# ❌ Bad: Single source can be biased
enhancer = SentimentEnhancedData(
    enable_news=True,
    enable_twitter=False,
    enable_reddit=False
)
```

### 2. Weight Sources Appropriately

```python
# ✅ Good: Customize weights for your strategy
engine = SentimentEngine(source_weights={
    SentimentSource.NEWS: 0.40,        # News most important
    SentimentSource.TWITTER: 0.30,     # Twitter second
    SentimentSource.REDDIT: 0.30       # Reddit third
})
```

### 3. Consider Sample Size

```python
# ✅ Good: Check sample size
if sentiment.sample_size < 5:
    print("⚠️  Low sample size, sentiment may not be reliable")
```

### 4. Monitor Trends

```python
# ✅ Good: Track sentiment trends
aggregated = engine.get_aggregated_sentiment("AAPL")
if aggregated.trend_direction == "declining":
    print("⚠️  Sentiment trending negative")
```

### 5. Combine with Technical Analysis

```python
# ✅ Good: Use sentiment + technical together
decision = make_sentiment_aware_decision(
    explainable,
    enhancer,
    symbol,
    {
        'current_price': 175.50,
        'rsi': 45.0,              # Technical
        'macd': 0.8,              # Technical
        # Sentiment added automatically!
    }
)
```

---

## Examples

### Example 1: Basic Sentiment Analysis

```python
from superstandard.agents import NewsSentimentProvider

provider = NewsSentimentProvider()
sentiment = provider.get_sentiment("AAPL")

print(f"{sentiment.sentiment_emoji} {sentiment.sentiment_label}")
print(f"Score: {sentiment.score:+.2f}")
print(f"Confidence: {sentiment.confidence * 100:.0f}%")
print(f"Keywords: {', '.join(sentiment.keywords[:5])}")
```

### Example 2: Multi-Source Aggregation

```python
from superstandard.agents import (
    SentimentEngine,
    NewsSentimentProvider,
    TwitterSentimentProvider,
    RedditSentimentProvider
)

engine = SentimentEngine()
symbol = "TSLA"

# Add all sources
engine.add_score(NewsSentimentProvider().get_sentiment(symbol))
engine.add_score(TwitterSentimentProvider().get_sentiment(symbol))
engine.add_score(RedditSentimentProvider().get_sentiment(symbol))

# Get aggregated
aggregated = engine.get_aggregated_sentiment(symbol)

print(f"Overall: {aggregated.overall_score:+.2f}")
print(f"Trend: {aggregated.trend_direction}")
```

### Example 3: Sentiment-Aware Trading

```python
from superstandard.agents import (
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,
    make_sentiment_aware_decision
)

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

# Explanation includes sentiment!
print(decision.explanation.natural_language_summary)
```

### Example 4: Production Integration

```python
# Production setup with real APIs
import os

from superstandard.agents import (
    NewsSentimentProvider,
    TwitterSentimentProvider,
    RedditSentimentProvider,
    SentimentEngine
)

# Initialize with API keys
news = NewsSentimentProvider(api_key=os.getenv('NEWS_API_KEY'))
twitter = TwitterSentimentProvider(api_key=os.getenv('TWITTER_API_KEY'))
reddit = RedditSentimentProvider(api_key=os.getenv('REDDIT_API_KEY'))

# Use in production
engine = SentimentEngine()
engine.add_score(news.get_sentiment("AAPL"))
engine.add_score(twitter.get_sentiment("AAPL"))
engine.add_score(reddit.get_sentiment("AAPL"))

sentiment = engine.get_aggregated_sentiment("AAPL")
```

---

## Production Deployment

### API Keys Setup

```bash
# .env file
NEWS_API_KEY=your_newsapi_key
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

### Real API Integration

For production, replace mock providers with real API calls:

**News API**: https://newsapi.org/docs/
**Twitter API**: https://developer.twitter.com/en/docs/twitter-api
**Reddit API**: https://praw.readthedocs.io/

---

## Troubleshooting

### "No sentiment data"
- Check API keys are set
- Verify symbol is valid
- Check time window isn't too narrow

### "Low confidence scores"
- Increase sample size (expand time window)
- Add more sentiment sources
- Check for mixed/conflicting signals

### "Sentiment doesn't match expectations"
- Review sample data in `raw_data` field
- Check keywords for context
- Verify source weights are appropriate

---

## Next Steps

1. **Run the Demo**
   ```bash
   python examples/sentiment_analysis_demo.py
   ```

2. **Integrate with Your Strategy**
   - Add sentiment to your ensembles
   - Track sentiment trends over time
   - Combine with explainable AI

3. **Production Deployment**
   - Get API keys for real sources
   - Implement caching for rate limits
   - Monitor sentiment data quality

---

**Built with the Agentic Forge Platform** 🚀

*The ONLY platform combining quantitative analysis + qualitative sentiment + explainable AI!*
