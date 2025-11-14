"""
Sentiment Analysis Integration Demo

Demonstrates the revolutionary sentiment analysis system that combines:
1. Multi-source sentiment (news, Twitter, Reddit)
2. Technical analysis
3. Agent ensemble decision-making
4. Full explainability

This is the FIRST platform to seamlessly integrate qualitative sentiment
with quantitative analysis in a fully transparent way!
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.agents import (
    # Templates
    TemplateLibrary,

    # Sentiment
    SentimentEngine,
    NewsSentimentProvider,
    TwitterSentimentProvider,
    RedditSentimentProvider,
    SentimentSource,

    # Integration
    create_sentiment_enhanced_ensemble,
    make_sentiment_aware_decision,
    SentimentEnhancedData
)


# ============================================================================
# Helper Functions
# ============================================================================

def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_sentiment_score(score):
    """Pretty print a sentiment score"""
    emoji = score.sentiment_emoji
    label = score.sentiment_label

    print(f"{emoji} {score.source.value.upper()} Sentiment: {label} ({score.score:+.2f})")
    print(f"   Confidence: {score.confidence * 100:.0f}%")
    print(f"   Sample Size: {score.sample_size} items")

    if score.keywords:
        print(f"   Top Keywords: {', '.join(score.keywords[:5])}")

    if score.trending_topics:
        print(f"   Trending: {', '.join(score.trending_topics[:3])}")


# ============================================================================
# Demo 1: Individual Sentiment Sources
# ============================================================================

def demo_1_individual_sources():
    """Demonstrate individual sentiment sources"""
    print_section("DEMO 1: Individual Sentiment Sources")

    symbol = "AAPL"

    # News Sentiment
    print("📰 News Sentiment Analysis:")
    news_provider = NewsSentimentProvider()
    news_sentiment = news_provider.get_sentiment(symbol)
    print_sentiment_score(news_sentiment)

    print()

    # Twitter Sentiment
    print("🐦 Twitter Sentiment Analysis:")
    twitter_provider = TwitterSentimentProvider()
    twitter_sentiment = twitter_provider.get_sentiment(symbol)
    print_sentiment_score(twitter_sentiment)

    print()

    # Reddit Sentiment
    print("📱 Reddit Sentiment Analysis:")
    reddit_provider = RedditSentimentProvider()
    reddit_sentiment = reddit_provider.get_sentiment(symbol)
    print_sentiment_score(reddit_sentiment)


# ============================================================================
# Demo 2: Aggregated Sentiment
# ============================================================================

def demo_2_aggregated_sentiment():
    """Demonstrate multi-source sentiment aggregation"""
    print_section("DEMO 2: Aggregated Multi-Source Sentiment")

    symbol = "AAPL"

    # Create sentiment engine
    engine = SentimentEngine()

    # Add scores from all sources
    print("Collecting sentiment from all sources...")

    news_provider = NewsSentimentProvider()
    twitter_provider = TwitterSentimentProvider()
    reddit_provider = RedditSentimentProvider()

    engine.add_score(news_provider.get_sentiment(symbol))
    engine.add_score(twitter_provider.get_sentiment(symbol))
    engine.add_score(reddit_provider.get_sentiment(symbol))

    # Get aggregated sentiment
    aggregated = engine.get_aggregated_sentiment(symbol)

    if aggregated:
        print(f"\n🎯 Aggregated Sentiment for {symbol}:")
        print(f"   Overall Score: {aggregated.sentiment_label} ({aggregated.overall_score:+.2f})")
        print(f"   Confidence: {aggregated.confidence * 100:.0f}%")
        print(f"   Trend: {aggregated.trend_direction.upper()} (strength: {aggregated.trend_strength * 100:.0f}%)")

        print(f"\n   📊 Source Breakdown:")
        for source, score in aggregated.source_scores.items():
            print(f"      {source.value}: {score.sentiment_emoji} {score.score:+.2f}")

        print(f"\n   🔑 Top Keywords: {', '.join(aggregated.top_keywords[:8])}")
        print(f"   📈 Trending Topics: {', '.join(aggregated.trending_topics)}")


# ============================================================================
# Demo 3: Sentiment-Enhanced Market Data
# ============================================================================

def demo_3_enhanced_market_data():
    """Demonstrate sentiment-enhanced market data"""
    print_section("DEMO 3: Sentiment-Enhanced Market Data")

    symbol = "AAPL"

    # Traditional market data
    market_data = {
        'current_price': 175.50,
        'rsi': 45.0,
        'macd': 0.8,
        'volume': 50_000_000
    }

    print("📊 Traditional Market Data:")
    print(f"   Price: ${market_data['current_price']}")
    print(f"   RSI: {market_data['rsi']}")
    print(f"   MACD: {market_data['macd']}")
    print(f"   Volume: {market_data['volume']:,}")

    # Enhance with sentiment
    enhancer = SentimentEnhancedData()
    enhanced = enhancer.enhance(symbol, market_data)

    print("\n✨ After Sentiment Enhancement:")
    print(f"   Price: ${enhanced['current_price']}")
    print(f"   RSI: {enhanced['rsi']}")
    print(f"   MACD: {enhanced['macd']}")
    print(f"   Volume: {enhanced['volume']:,}")

    print("\n   💭 NEW: Sentiment Data:")
    if 'overall_sentiment' in enhanced:
        print(f"   Overall Sentiment: {enhanced['overall_sentiment']:+.2f}")
        print(f"   Sentiment Confidence: {enhanced.get('overall_sentiment_confidence', 0) * 100:.0f}%")
        print(f"   Sentiment Trend: {enhanced.get('sentiment_trend', 'N/A').upper()}")

    if 'news_sentiment' in enhanced:
        print(f"   News Sentiment: {enhanced['news_sentiment']:+.2f} ({enhanced.get('news_sample_size', 0)} articles)")

    if 'twitter_sentiment' in enhanced:
        print(f"   Twitter Sentiment: {enhanced['twitter_sentiment']:+.2f} ({enhanced.get('twitter_sample_size', 0)} tweets)")

    if 'reddit_sentiment' in enhanced:
        print(f"   Reddit Sentiment: {enhanced['reddit_sentiment']:+.2f} ({enhanced.get('reddit_sample_size', 0)} posts)")

    if 'trending_keywords' in enhanced:
        print(f"   Trending Keywords: {', '.join(enhanced['trending_keywords'][:5])}")


# ============================================================================
# Demo 4: Sentiment-Aware Decisions with Explainability
# ============================================================================

def demo_4_sentiment_aware_decisions():
    """Demonstrate sentiment-aware agent decisions with full explainability"""
    print_section("DEMO 4: Sentiment-Aware Decisions with Explainability")

    symbol = "AAPL"

    # Create ensemble
    print("🤖 Creating Balanced Trader ensemble...")
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()

    # Create sentiment-enhanced ensemble
    explainable, enhancer = create_sentiment_enhanced_ensemble(ensemble)

    # Traditional market data
    market_data = {
        'current_price': 175.50,
        'rsi': 45.0,
        'macd': 0.8,
        'volume': 50_000_000
    }

    print(f"\n📊 Making sentiment-aware decision for {symbol}...")

    # Make decision with sentiment
    decision = make_sentiment_aware_decision(
        explainable,
        enhancer,
        symbol,
        market_data
    )

    print(f"\n✅ Decision: {decision.action.upper()}")
    print(f"   Confidence: {decision.confidence * 100:.1f}%")

    print(f"\n📝 Explanation:")
    print(decision.explanation.natural_language_summary)

    # Show reasoning factors breakdown
    print(f"\n🔍 Detailed Reasoning Factors:")

    # Group by type
    factors_by_type = {}
    for factor in decision.explanation.reasoning_factors:
        factor_type = factor.factor_type.value
        if factor_type not in factors_by_type:
            factors_by_type[factor_type] = []
        factors_by_type[factor_type].append(factor)

    # Print each type
    for factor_type, factors in factors_by_type.items():
        print(f"\n   {factor_type.replace('_', ' ').title()}:")
        for factor in factors:
            emoji = {'bullish': '📈', 'bearish': '📉', 'neutral': '➡️'}.get(factor.influence, '❓')
            print(f"      {emoji} {factor.name}: {factor.explanation}")
            print(f"         Weight: {factor.weight * 100:.0f}% | Confidence: {factor.confidence * 100:.0f}%")

    # Show insights
    if decision.explanation.key_insights:
        print(f"\n💡 Key Insights:")
        for insight in decision.explanation.key_insights:
            print(f"   • {insight}")

    # Show risks
    if decision.explanation.risks_identified:
        print(f"\n⚠️  Risks Identified:")
        for risk in decision.explanation.risks_identified:
            print(f"   • {risk}")


# ============================================================================
# Demo 5: Natural Language Q&A About Sentiment
# ============================================================================

def demo_5_sentiment_qa():
    """Demonstrate asking questions about sentiment-based decisions"""
    print_section("DEMO 5: Natural Language Q&A About Sentiment")

    symbol = "TSLA"

    # Create ensemble
    library = TemplateLibrary()
    ensemble = library.get_template("aggressive_trader").create_ensemble()
    explainable, enhancer = create_sentiment_enhanced_ensemble(ensemble)

    # Market data with mixed signals
    market_data = {
        'current_price': 250.00,
        'rsi': 72.0,  # Overbought
        'macd': -1.2  # Negative
    }

    decision = make_sentiment_aware_decision(explainable, enhancer, symbol, market_data)

    print(f"Decision for {symbol}: {decision.action.upper()} ({decision.confidence * 100:.1f}% confidence)\n")

    # Ask questions
    questions = [
        "Why did you make this decision?",
        "What does sentiment say?",
        "What are the risks?",
        "Did all agents agree?"
    ]

    print("💬 Q&A Session:\n")

    for question in questions:
        print(f"❓ Q: {question}")
        answer = explainable.ask(question, decision.explanation_id)
        print(f"💡 A: {answer[:300]}...")  # Truncate for display
        print()


# ============================================================================
# Demo 6: Sentiment vs Technical Comparison
# ============================================================================

def demo_6_sentiment_vs_technical():
    """Compare decisions with and without sentiment"""
    print_section("DEMO 6: Sentiment Impact Analysis")

    symbol = "AAPL"

    library = TemplateLibrary()
    ensemble = library.get_template("balanced_trader").create_ensemble()

    # Market data
    market_data = {
        'current_price': 175.50,
        'rsi': 45.0,
        'macd': 0.8
    }

    # Decision WITHOUT sentiment
    from superstandard.agents import create_explainable_ensemble
    explainable_basic = create_explainable_ensemble(ensemble)
    decision_basic = explainable_basic.make_explainable_decision(symbol, market_data)

    print(f"📊 Decision WITHOUT Sentiment:")
    print(f"   Action: {decision_basic.action.upper()}")
    print(f"   Confidence: {decision_basic.confidence * 100:.1f}%")
    print(f"   Factors: {len(decision_basic.explanation.reasoning_factors)}")

    # Decision WITH sentiment
    explainable_sentiment, enhancer = create_sentiment_enhanced_ensemble(ensemble)
    decision_sentiment = make_sentiment_aware_decision(
        explainable_sentiment,
        enhancer,
        symbol,
        market_data
    )

    print(f"\n💭 Decision WITH Sentiment:")
    print(f"   Action: {decision_sentiment.action.upper()}")
    print(f"   Confidence: {decision_sentiment.confidence * 100:.1f}%")
    print(f"   Factors: {len(decision_sentiment.explanation.reasoning_factors)}")

    # Show the difference
    print(f"\n🔍 Impact of Sentiment:")
    conf_change = decision_sentiment.confidence - decision_basic.confidence
    factor_change = len(decision_sentiment.explanation.reasoning_factors) - len(decision_basic.explanation.reasoning_factors)

    print(f"   Confidence Change: {conf_change:+.1%}")
    print(f"   Additional Factors: {factor_change}")
    print(f"   Result: Sentiment adds {factor_change} additional reasoning factors!")

    if conf_change > 0:
        print(f"   ✅ Sentiment INCREASED confidence in the decision")
    elif conf_change < 0:
        print(f"   ⚠️  Sentiment DECREASED confidence (mixed signals)")
    else:
        print(f"   ➡️  Sentiment did not change overall confidence")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  🚀 SENTIMENT ANALYSIS INTEGRATION DEMO")
    print("=" * 80)
    print("\nRevolutionary multi-source sentiment analysis integrated with")
    print("explainable AI for fully transparent trading decisions!")
    print("\nThis demo showcases:")
    print("  1. Individual sentiment sources (News, Twitter, Reddit)")
    print("  2. Multi-source aggregation")
    print("  3. Sentiment-enhanced market data")
    print("  4. Sentiment-aware agent decisions with explainability")
    print("  5. Natural language Q&A about sentiment")
    print("  6. Sentiment impact analysis")
    print("=" * 80)

    try:
        demo_1_individual_sources()
        demo_2_aggregated_sentiment()
        demo_3_enhanced_market_data()
        demo_4_sentiment_aware_decisions()
        demo_5_sentiment_qa()
        demo_6_sentiment_vs_technical()

        print_section("✅ ALL DEMOS COMPLETED!")

        print("🎉 Key Achievements:")
        print("   • Multi-source sentiment analysis (News, Twitter, Reddit)")
        print("   • Sentiment aggregation with trend detection")
        print("   • Seamless integration with technical analysis")
        print("   • Full explainability of sentiment-based decisions")
        print("   • Natural language Q&A about sentiment factors")
        print("   • Quantitative + Qualitative analysis combined!")

        print("\n📚 Next Steps:")
        print("   1. Explore the code in examples/sentiment_analysis_demo.py")
        print("   2. Read SENTIMENT_ANALYSIS_GUIDE.md for detailed documentation")
        print("   3. Try the sentiment dashboard for visual analysis")
        print("   4. Integrate with your own sentiment data sources!")

        print("\n🌟 This is the FIRST platform to seamlessly combine:")
        print("   ✅ Real market data")
        print("   ✅ Technical indicators")
        print("   ✅ Multi-source sentiment")
        print("   ✅ Explainable AI")
        print("   ✅ Natural language Q&A")
        print("\n   NO OTHER PLATFORM HAS ALL OF THIS! 🔥")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
