"""
Explainable AI Demo - Transparent Agent Decision Making

Demonstrates the revolutionary explainable AI system that makes every
agent decision fully transparent and understandable.

Features demonstrated:
1. Full decision explanations with reasoning chains
2. Visual decision trees
3. Natural language Q&A about decisions
4. Agent contribution breakdowns
5. Confidence analysis
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superstandard.agents import (
    # Templates
    TemplateLibrary,

    # Explainable AI
    create_explainable_ensemble,
    DecisionTreeVisualizer
)


# ============================================================================
# Demo Setup
# ============================================================================

def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_decision_tree(tree_dict: dict, indent: int = 0):
    """Pretty print decision tree"""
    label = tree_dict['label']
    value = tree_dict['value']
    weight = tree_dict['weight']

    # Create visual weight bar
    bar_length = int(weight * 20)
    bar = "█" * bar_length + "░" * (20 - bar_length)

    prefix = "  " * indent
    if indent == 0:
        print(f"{prefix}🎯 {label}: {value}")
    else:
        print(f"{prefix}├─ {label}: {value}")
        print(f"{prefix}│  Weight: [{bar}] {weight * 100:.0f}%")

    # Print children
    for child in tree_dict.get('children', []):
        print_decision_tree(child, indent + 1)


# ============================================================================
# Demo 1: Basic Explainable Decision
# ============================================================================

def demo_1_basic_explanation():
    """Demonstrate basic explainable decision"""
    print_section("DEMO 1: Basic Explainable Decision")

    # Create ensemble
    print("🤖 Creating Balanced Trader ensemble...")
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()

    # Wrap with explainability
    explainable = create_explainable_ensemble(ensemble)

    # Make explainable decision
    print("\n📊 Making decision for AAPL...")
    market_data = {
        'current_price': 175.50,
        'rsi': 45.0,  # Slightly bullish
        'macd': 0.8,  # Positive crossover
        'volume': 50_000_000,
        'trend': 'bullish'
    }

    decision = explainable.make_explainable_decision(
        symbol="AAPL",
        market_data=market_data
    )

    print(f"\n✅ Decision: {decision.action.upper()}")
    print(f"   Confidence: {decision.confidence * 100:.1f}%")
    print(f"\n📝 Explanation:")
    print(decision.explanation.natural_language_summary)

    if decision.explanation.key_insights:
        print(f"\n💡 Key Insights:")
        for insight in decision.explanation.key_insights:
            print(f"   • {insight}")

    if decision.explanation.risks_identified:
        print(f"\n⚠️  Risks Identified:")
        for risk in decision.explanation.risks_identified:
            print(f"   • {risk}")

    return decision


# ============================================================================
# Demo 2: Reasoning Factor Breakdown
# ============================================================================

def demo_2_reasoning_breakdown():
    """Show detailed reasoning factor breakdown"""
    print_section("DEMO 2: Reasoning Factor Breakdown")

    # Create ensemble
    library = TemplateLibrary()
    template = library.get_template("aggressive_trader")
    ensemble = template.create_ensemble()
    explainable = create_explainable_ensemble(ensemble)

    # Make decision
    market_data = {
        'current_price': 250.00,
        'rsi': 72.0,  # Overbought!
        'macd': -1.2,  # Negative
        'volume': 80_000_000,
        'trend': 'bearish'
    }

    decision = explainable.make_explainable_decision(
        symbol="TSLA",
        market_data=market_data
    )

    print(f"Decision: {decision.action.upper()} TSLA")
    print(f"Confidence: {decision.confidence * 100:.1f}%\n")

    # Show all reasoning factors
    print("🔍 Detailed Reasoning Factors:\n")

    for i, factor in enumerate(decision.explanation.reasoning_factors, 1):
        # Emoji based on influence
        emoji = {
            'bullish': '📈',
            'bearish': '📉',
            'neutral': '➡️'
        }.get(factor.influence, '❓')

        print(f"{i}. {emoji} {factor.name}")
        print(f"   Type: {factor.factor_type.value.replace('_', ' ').title()}")
        print(f"   Value: {factor.value}")
        print(f"   Weight: {factor.weight * 100:.0f}%")
        print(f"   Confidence: {factor.confidence * 100:.0f}%")
        print(f"   Influence: {factor.influence.upper()}")
        print(f"   Explanation: {factor.explanation}")
        print()

    return decision


# ============================================================================
# Demo 3: Agent Contribution Analysis
# ============================================================================

def demo_3_agent_contributions():
    """Show individual agent contributions"""
    print_section("DEMO 3: Agent Contribution Analysis")

    # Create diverse ensemble
    library = TemplateLibrary()
    template = library.get_template("diverse_council")
    ensemble = template.create_ensemble()
    explainable = create_explainable_ensemble(ensemble)

    # Make decision
    market_data = {
        'current_price': 100.00,
        'rsi': 50.0,
        'macd': 0.0,
        'volume': 30_000_000,
        'trend': 'neutral'
    }

    decision = explainable.make_explainable_decision(
        symbol="SPY",
        market_data=market_data
    )

    print(f"Decision: {decision.action.upper()} SPY\n")

    # Show agent votes
    print("🤖 Individual Agent Contributions:\n")

    votes = {}
    for contrib in decision.explanation.agent_contributions:
        votes[contrib.vote] = votes.get(contrib.vote, 0) + 1

        # Vote emoji
        vote_emoji = {
            'buy': '✅',
            'sell': '❌',
            'hold': '⏸️'
        }.get(contrib.vote, '❓')

        print(f"{vote_emoji} {contrib.agent_name}")
        print(f"   Specialist Type: {contrib.specialist_type}")
        print(f"   Vote: {contrib.vote.upper()}")
        print(f"   Confidence: {contrib.confidence * 100:.1f}%")
        print(f"   Reasoning: {contrib.reasoning}")
        print()

    # Show vote distribution
    print("📊 Vote Distribution:")
    total_agents = len(decision.explanation.agent_contributions)
    for vote, count in sorted(votes.items()):
        pct = (count / total_agents) * 100
        bar = "█" * int(pct / 5)
        print(f"   {vote.upper():6} [{bar:<20}] {count}/{total_agents} ({pct:.0f}%)")

    return decision


# ============================================================================
# Demo 4: Natural Language Q&A
# ============================================================================

def demo_4_natural_language_qa(decision):
    """Demonstrate natural language question answering"""
    print_section("DEMO 4: Natural Language Q&A")

    # Get the explainable ensemble (simplified - using global)
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()
    explainable = create_explainable_ensemble(ensemble)

    # Recreate the decision in the engine
    explainable.explanation_engine.explanations[decision.explanation_id] = decision.explanation

    questions = [
        "Why did you make this decision?",
        "What were the top factors?",
        "How confident were you?",
        "Did all agents agree?",
        "What risks did you identify?"
    ]

    print("💬 Ask the AI about its decision:\n")

    for question in questions:
        print(f"❓ Q: {question}")
        answer = explainable.ask(question, decision.explanation_id)
        print(f"💡 A: {answer}")
        print()


# ============================================================================
# Demo 5: Visual Decision Tree
# ============================================================================

def demo_5_decision_tree(decision):
    """Show visual decision tree"""
    print_section("DEMO 5: Visual Decision Tree")

    # Get the explainable ensemble
    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()
    explainable = create_explainable_ensemble(ensemble)

    # Add decision to engine
    explainable.explanation_engine.explanations[decision.explanation_id] = decision.explanation

    # Get decision tree
    tree_dict = explainable.get_decision_tree(decision.explanation_id)

    if tree_dict:
        print("🌳 Decision Tree Visualization:\n")
        print_decision_tree(tree_dict)
    else:
        print("No decision tree available.")


# ============================================================================
# Demo 6: Decision Comparison
# ============================================================================

def demo_6_decision_comparison():
    """Compare decisions from different ensembles"""
    print_section("DEMO 6: Ensemble Comparison")

    library = TemplateLibrary()

    # Same market data
    market_data = {
        'current_price': 150.00,
        'rsi': 65.0,
        'macd': 1.5,
        'volume': 60_000_000,
        'trend': 'bullish'
    }

    ensembles = [
        ("Conservative", "conservative_portfolio"),
        ("Balanced", "balanced_trader"),
        ("Aggressive", "aggressive_trader")
    ]

    print("📊 How different ensembles analyze the same market data:\n")
    print(f"Market Data: AAPL @ $150.00, RSI: 65, MACD: +1.5 (bullish)\n")

    for name, template_id in ensembles:
        template = library.get_template(template_id)
        ensemble = template.create_ensemble()
        explainable = create_explainable_ensemble(ensemble)

        decision = explainable.make_explainable_decision(
            symbol="AAPL",
            market_data=market_data
        )

        print(f"🤖 {name} Ensemble:")
        print(f"   Decision: {decision.action.upper()}")
        print(f"   Confidence: {decision.confidence * 100:.1f}%")
        print(f"   Summary: {decision.explanation.natural_language_summary.split('.')[0]}...")
        print()


# ============================================================================
# Demo 7: Outcome Tracking
# ============================================================================

def demo_7_outcome_tracking():
    """Demonstrate outcome tracking and learning"""
    print_section("DEMO 7: Outcome Tracking")

    library = TemplateLibrary()
    template = library.get_template("balanced_trader")
    ensemble = template.create_ensemble()
    explainable = create_explainable_ensemble(ensemble)

    # Make decision
    market_data = {
        'current_price': 180.00,
        'rsi': 55.0,
        'macd': 0.5,
        'volume': 45_000_000,
        'trend': 'bullish'
    }

    decision = explainable.make_explainable_decision(
        symbol="AAPL",
        market_data=market_data
    )

    print(f"📊 Initial Decision: {decision.action.upper()} AAPL @ $180.00")
    print(f"   Confidence: {decision.confidence * 100:.1f}%")

    # Simulate trade execution and outcome
    print("\n⏳ Simulating trade execution...")

    explainable.update_outcome(
        decision_id=decision.explanation_id,
        executed=True,
        execution_price=180.50,
        outcome="success",
        actual_return=0.05  # 5% return
    )

    # Get updated explanation
    updated = explainable.get_explanation(decision.explanation_id)

    print(f"\n✅ Trade Executed at: ${updated.execution_price:.2f}")
    print(f"   Outcome: {updated.outcome.upper()}")
    print(f"   Actual Return: {updated.actual_return * 100:+.2f}%")
    print(f"\n💡 The agent can now learn from this outcome for future decisions!")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  🚀 EXPLAINABLE AI SYSTEM DEMO")
    print("=" * 80)
    print("\nMaking AI trading decisions transparent and understandable!")
    print("\nThis demo showcases:")
    print("  1. Full decision explanations with reasoning chains")
    print("  2. Detailed reasoning factor breakdowns")
    print("  3. Individual agent contribution analysis")
    print("  4. Natural language Q&A about decisions")
    print("  5. Visual decision tree representations")
    print("  6. Ensemble comparison")
    print("  7. Outcome tracking and learning")
    print("=" * 80)

    try:
        # Run demos
        decision1 = demo_1_basic_explanation()
        decision2 = demo_2_reasoning_breakdown()
        decision3 = demo_3_agent_contributions()
        demo_4_natural_language_qa(decision1)
        demo_5_decision_tree(decision1)
        demo_6_decision_comparison()
        demo_7_outcome_tracking()

        print_section("✅ ALL DEMOS COMPLETED!")

        print("🎉 Key Achievements:")
        print("   • Full transparency into agent decision-making")
        print("   • Natural language explanations anyone can understand")
        print("   • Visual decision trees for intuitive comprehension")
        print("   • Individual agent accountability")
        print("   • Outcome tracking for continuous learning")
        print("\n📚 Next Steps:")
        print("   1. Explore the code in examples/explainable_ai_demo.py")
        print("   2. Read EXPLAINABLE_AI_GUIDE.md for detailed documentation")
        print("   3. Try the interactive dashboard at /explainable-dashboard")
        print("   4. Ask your own questions about agent decisions!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
