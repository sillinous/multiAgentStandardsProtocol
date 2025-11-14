"""
Conversational Trading Interface Demo

Demonstrates the revolutionary natural language trading interface that lets you
TALK TO YOUR AI TRADER like a human assistant!

This is the FIRST platform to combine:
1. Natural language understanding
2. Trading command execution
3. Sentiment analysis
4. Explainable AI
5. Conversational memory

You can literally chat with your AI trader and it understands you!
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.agents import (
    # Core conversation
    ConversationalAgent,
    QueryProcessor,
    CommandInterpreter,

    # Templates and ensembles
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,
    SentimentEnhancedData,

    # Paper trading
    PaperTradingEngine,
    PaperTradingConfig,
    TradingMode
)


# ============================================================================
# Helper Functions
# ============================================================================

def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def chat_demo(agent: ConversationalAgent, messages: list):
    """Demo a conversation"""
    for i, message in enumerate(messages, 1):
        print(f"👤 User: {message}")
        response = agent.chat(message)
        print(f"🤖 Agent: {response}")
        print()


# ============================================================================
# Demo 1: Basic Conversation
# ============================================================================

def demo_1_basic_conversation():
    """Demonstrate basic conversational interaction"""
    print_section("DEMO 1: Basic Conversation")

    # Create agent (no trading engine yet)
    agent = ConversationalAgent()

    messages = [
        "Hello!",
        "What can you do?",
        "Tell me about your strategy",
    ]

    chat_demo(agent, messages)


# ============================================================================
# Demo 2: Query Understanding
# ============================================================================

def demo_2_query_understanding():
    """Demonstrate natural language query understanding"""
    print_section("DEMO 2: Query Understanding")

    processor = QueryProcessor()

    queries = [
        "Buy 100 shares of AAPL",
        "What's the sentiment on TSLA?",
        "Why did you sell my NVDA shares?",
        "Show me my portfolio",
        "Make me more conservative",
        "Stop trading"
    ]

    print("Understanding different types of queries:\n")

    for query_text in queries:
        query = processor.process(query_text)

        print(f"📝 '{query_text}'")
        print(f"   Type: {query.query_type.value}")
        print(f"   Intent: {query.intent.value}")
        print(f"   Confidence: {query.confidence * 100:.0f}%")

        if query.symbols:
            print(f"   Symbols: {', '.join(query.symbols)}")
        if query.amount:
            print(f"   Amount: {query.amount}")

        print()


# ============================================================================
# Demo 3: Trading Commands
# ============================================================================

def demo_3_trading_commands():
    """Demonstrate trading command execution"""
    print_section("DEMO 3: Trading Commands")

    # Create paper trading engine
    config = PaperTradingConfig(
        initial_cash=100000.0,
        trading_mode=TradingMode.PAPER
    )

    paper_engine = PaperTradingEngine(config=config)

    # Create agent with paper trading
    agent = ConversationalAgent(paper_trading_engine=paper_engine)

    messages = [
        "Buy 50 shares of AAPL",
        "Buy 30 shares of TSLA",
        "Show me my portfolio",
        "Sell 25 shares of AAPL",
        "Show me my positions"
    ]

    chat_demo(agent, messages)


# ============================================================================
# Demo 4: Sentiment Integration
# ============================================================================

def demo_4_sentiment_integration():
    """Demonstrate sentiment analysis in conversations"""
    print_section("DEMO 4: Sentiment Integration")

    # Create sentiment enhancer
    sentiment_enhancer = SentimentEnhancedData()

    # Create agent with sentiment
    agent = ConversationalAgent(sentiment_enhancer=sentiment_enhancer)

    messages = [
        "What's the sentiment on AAPL?",
        "How is Twitter feeling about TSLA?",
        "Is the news positive on NVDA?",
    ]

    chat_demo(agent, messages)


# ============================================================================
# Demo 5: Explainable AI Integration
# ============================================================================

def demo_5_explainable_ai():
    """Demonstrate explainability in conversations"""
    print_section("DEMO 5: Explainable AI Integration")

    # Create ensemble
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()

    # Create explainable ensemble with sentiment
    explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

    # Create paper trading
    config = PaperTradingConfig(initial_cash=100000.0)
    paper_engine = PaperTradingEngine(config=config)

    # Create full agent
    agent = ConversationalAgent(
        paper_trading_engine=paper_engine,
        explainable_ensemble=explainable,
        sentiment_enhancer=sentiment_enhancer
    )

    # Make a decision first
    from superstandard.agents import make_sentiment_aware_decision

    market_data = {
        'current_price': 175.50,
        'rsi': 45.0,
        'macd': 0.8
    }

    decision = make_sentiment_aware_decision(
        explainable,
        sentiment_enhancer,
        "AAPL",
        market_data
    )

    # Store decision ID in context
    agent.history.context.recent_decisions.append(decision.explanation_id)
    agent.history.context.current_symbols.append("AAPL")

    print(f"✅ Made decision for AAPL: {decision.action.upper()} ({decision.confidence * 100:.1f}% confidence)\n")

    # Now ask questions about it
    messages = [
        "Why did you make that decision?",
        "How confident are you?",
        "What are the risks?",
        "Did all agents agree?"
    ]

    chat_demo(agent, messages)


# ============================================================================
# Demo 6: Full Conversation Flow
# ============================================================================

def demo_6_full_conversation():
    """Demonstrate a complete natural conversation"""
    print_section("DEMO 6: Full Conversation Flow")

    # Setup full agent
    library = TemplateLibrary()
    ensemble = library.get_template("aggressive_trader").create_ensemble()
    explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

    config = PaperTradingConfig(initial_cash=100000.0)
    paper_engine = PaperTradingEngine(config=config)

    agent = ConversationalAgent(
        paper_trading_engine=paper_engine,
        explainable_ensemble=explainable,
        sentiment_enhancer=sentiment_enhancer
    )

    # Natural conversation
    messages = [
        "Hi! I'm new to trading.",
        "What's the sentiment on AAPL right now?",
        "Sounds good! Buy 100 shares of AAPL.",
        "Show me my portfolio.",
        "How confident are you in this AAPL position?",
        "What are the main risks?",
        "Make me more conservative.",
        "Show me my positions again."
    ]

    print("💬 Having a natural conversation with your AI trader:\n")
    chat_demo(agent, messages)


# ============================================================================
# Demo 7: Query Types Showcase
# ============================================================================

def demo_7_query_types_showcase():
    """Showcase all different query types"""
    print_section("DEMO 7: All Query Types")

    # Create full agent
    library = TemplateLibrary()
    ensemble = library.get_template("balanced_trader").create_ensemble()
    explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

    agent = ConversationalAgent(
        explainable_ensemble=explainable,
        sentiment_enhancer=sentiment_enhancer
    )

    print("Testing all query types:\n")

    query_examples = {
        "GREETING": ["Hello!", "Hey there!", "Good morning!"],
        "QUESTION": [
            "What's the sentiment on TSLA?",
            "How confident are you?",
            "Why did you sell?"
        ],
        "COMMAND": [
            "Buy 50 shares of AAPL",
            "Sell all TSLA",
            "Make me more aggressive"
        ],
        "REQUEST": [
            "Show me my portfolio",
            "List my positions",
            "Find good opportunities"
        ],
        "EXPLANATION": [
            "Explain your strategy",
            "Tell me about your decision"
        ]
    }

    for query_type, examples in query_examples.items():
        print(f"\n📋 {query_type}:")
        for example in examples:
            print(f"   👤 {example}")
            response = agent.chat(example)
            print(f"   🤖 {response[:100]}..." if len(response) > 100 else f"   🤖 {response}")


# ============================================================================
# Demo 8: Conversation History
# ============================================================================

def demo_8_conversation_history():
    """Demonstrate conversation history tracking"""
    print_section("DEMO 8: Conversation History")

    agent = ConversationalAgent()

    # Have a conversation
    messages = [
        "Hello!",
        "What can you do?",
        "Tell me about sentiment analysis",
        "How do you make decisions?"
    ]

    for msg in messages:
        agent.chat(msg)

    # Show history
    history = agent.get_history()

    print(f"📚 Conversation History:\n")
    print(f"   Total turns: {len(history.turns)}")
    print(f"   Session started: {history.context.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n   Recent conversation:")

    for turn in history.get_recent_turns(limit=3):
        print(f"\n   👤 {turn.user_message}")
        print(f"   🤖 {turn.response[:80]}..." if len(turn.response) > 80 else f"   🤖 {turn.response}")
        print(f"      Type: {turn.query_type.value} | Intent: {turn.intent.value}")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  🗣️  CONVERSATIONAL TRADING INTERFACE DEMO")
    print("=" * 80)
    print("\nTalk to your AI trader in plain English!")
    print("\nThis demo showcases:")
    print("  1. Basic conversation")
    print("  2. Natural language understanding")
    print("  3. Trading command execution")
    print("  4. Sentiment analysis integration")
    print("  5. Explainable AI integration")
    print("  6. Full conversation flow")
    print("  7. All query types")
    print("  8. Conversation history")
    print("=" * 80)

    try:
        demo_1_basic_conversation()
        demo_2_query_understanding()
        demo_3_trading_commands()
        demo_4_sentiment_integration()
        demo_5_explainable_ai()
        demo_6_full_conversation()
        demo_7_query_types_showcase()
        demo_8_conversation_history()

        print_section("✅ ALL DEMOS COMPLETED!")

        print("🎉 Key Achievements:")
        print("   • Natural language understanding")
        print("   • Trading command execution")
        print("   • Sentiment analysis integration")
        print("   • Explainable AI integration")
        print("   • Full conversation memory")
        print("   • Multi-turn dialogue")

        print("\n💡 What This Means:")
        print("   You can now TALK to your AI trader like a human assistant!")
        print("   Ask questions, give commands, and get explanations - all in plain English!")

        print("\n📚 Next Steps:")
        print("   1. Try the interactive chat interface")
        print("   2. Integrate with your own trading strategies")
        print("   3. Customize the conversation responses")
        print("   4. Add more command types")

        print("\n🌟 This is REVOLUTIONARY because:")
        print("   ✅ First conversational AI trader")
        print("   ✅ Natural language understanding")
        print("   ✅ Sentiment + Technical + Explainability")
        print("   ✅ Full conversation context")
        print("   ✅ Command execution from natural language")
        print("\n   NO OTHER PLATFORM HAS THIS! 🔥")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
