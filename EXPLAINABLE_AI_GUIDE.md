# Explainable AI System Guide 🔍✨

**Complete transparency into agent decision-making through visual explanations, natural language summaries, and decision replay.**

## Table of Contents

1. [Overview](#overview)
2. [Why Explainable AI Matters](#why-explainable-ai-matters)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Decision Explanations](#decision-explanations)
6. [Visual Decision Trees](#visual-decision-trees)
7. [Natural Language Q&A](#natural-language-qa)
8. [Decision Replay System](#decision-replay-system)
9. [Dashboard Interface](#dashboard-interface)
10. [API Reference](#api-reference)
11. [Best Practices](#best-practices)
12. [Advanced Features](#advanced-features)

---

## Overview

The Explainable AI System makes every agent decision fully transparent and understandable by providing:

✅ **Full Decision Explanations** - Complete reasoning chains showing WHY decisions were made
✅ **Visual Decision Trees** - Intuitive tree visualizations of decision factors
✅ **Natural Language Q&A** - Ask questions about decisions in plain English
✅ **Decision Replay** - Time-travel through historical decisions
✅ **Outcome Tracking** - Learn from successes and failures
✅ **Pattern Recognition** - Identify trends across decisions

**This solves the #1 barrier to AI adoption: TRUST** 🎯

---

## Why Explainable AI Matters

### The Problem

Traditional AI trading systems are "black boxes":
- Users don't know WHY decisions were made
- Can't debug when things go wrong
- Hard to trust with real money
- Impossible to learn from
- Regulatory compliance challenges

### Our Solution

**Full transparency through explainability:**

```
Traditional AI              Explainable AI
═══════════════            ═══════════════
Input → 🔲 → Decision      Input → 🔍 → Decision
         ❓                         │
    "Why did it                    ├─ Reasoning Factors
     decide that?"                 ├─ Agent Contributions
                                   ├─ Confidence Analysis
                                   ├─ Risk Assessment
                                   └─ Natural Language Summary
                                        ✓ "I chose BUY because..."
```

---

## Quick Start

### Installation

Already installed! The explainable AI system is included with the platform.

### Basic Usage

```python
from superstandard.agents import (
    TemplateLibrary,
    create_explainable_ensemble
)

# 1. Create ensemble
library = TemplateLibrary()
template = library.get_template("balanced_trader")
ensemble = template.create_ensemble()

# 2. Wrap with explainability
explainable = create_explainable_ensemble(ensemble)

# 3. Make explainable decision
market_data = {
    'current_price': 175.50,
    'rsi': 45.0,
    'macd': 0.8,
    'volume': 50_000_000
}

decision = explainable.make_explainable_decision(
    symbol="AAPL",
    market_data=market_data
)

# 4. View explanation
print(decision.explanation.natural_language_summary)

# Output:
# Decision: BUY AAPL with 78% confidence.
#
# Key factors:
# 1. 📈 RSI: RSI at 45.0 indicates bullish momentum (weight: 20%)
# 2. 📈 MACD: MACD signal suggests bullish trend (weight: 18%)
# 3. 📊 Agent Consensus: Ensemble voted BUY with 78% confidence (weight: 30%)
#
# Ensemble consensus: 4/5 agents voted BUY (80% agreement)
```

### Run the Demo

```bash
python examples/explainable_ai_demo.py
```

---

## Core Concepts

### 1. Decision Explanation

Every decision includes:

```python
@dataclass
class DecisionExplanation:
    decision_id: str                         # Unique identifier
    timestamp: datetime                      # When decision was made
    symbol: str                              # Stock symbol
    decision: str                            # "buy", "sell", or "hold"
    confidence: float                        # 0.0 to 1.0

    reasoning_factors: List[ReasoningFactor] # WHY this decision
    agent_contributions: List[AgentContribution]  # Individual agent votes

    natural_language_summary: str            # Plain English explanation
    key_insights: List[str]                  # Important takeaways
    risks_identified: List[str]              # Potential risks

    # Outcome (filled after execution)
    executed: bool
    execution_price: Optional[float]
    outcome: Optional[str]                   # "success" or "failure"
    actual_return: Optional[float]
```

### 2. Reasoning Factors

Factors that influenced the decision:

```python
class ReasoningFactorType(Enum):
    TECHNICAL_INDICATOR = "technical_indicator"    # RSI, MACD, etc.
    SENTIMENT = "sentiment"                        # News, social media
    PATTERN_RECOGNITION = "pattern_recognition"    # Chart patterns
    ENSEMBLE_CONSENSUS = "ensemble_consensus"      # Agent agreement
    REGIME_DETECTION = "regime_detection"          # Market regime
    RISK_ASSESSMENT = "risk_assessment"            # Risk analysis
    HISTORICAL_PERFORMANCE = "historical_performance"  # Past results
    MARKET_CONDITIONS = "market_conditions"        # Volume, volatility

@dataclass
class ReasoningFactor:
    factor_type: ReasoningFactorType
    name: str                 # e.g., "RSI"
    value: Any                # e.g., 45.0
    weight: float             # 0.0 to 1.0 (how important)
    confidence: float         # 0.0 to 1.0 (how certain)
    influence: str            # "bullish", "bearish", "neutral"
    explanation: str          # Plain English description
```

### 3. Agent Contributions

Individual agent votes:

```python
@dataclass
class AgentContribution:
    agent_id: str
    agent_name: str
    specialist_type: str       # "bull_specialist", etc.
    vote: str                  # "buy", "sell", "hold"
    confidence: float
    reasoning: str
    personality_traits: Dict[str, float]
```

---

## Decision Explanations

### Creating Explanations

```python
from superstandard.agents import create_explainable_ensemble

# Wrap any ensemble
explainable = create_explainable_ensemble(ensemble)

# Make explainable decision
decision = explainable.make_explainable_decision(
    symbol="TSLA",
    market_data={
        'current_price': 250.00,
        'rsi': 72.0,  # Overbought
        'macd': -1.2,
        'volume': 80_000_000
    }
)
```

### Accessing Explanation Details

```python
# Natural language summary
print(decision.explanation.natural_language_summary)

# Key insights
for insight in decision.explanation.key_insights:
    print(f"💡 {insight}")

# Identified risks
for risk in decision.explanation.risks_identified:
    print(f"⚠️ {risk}")

# Reasoning factors breakdown
for factor in decision.explanation.reasoning_factors:
    print(f"{factor.name}: {factor.explanation}")
    print(f"  Weight: {factor.weight * 100:.0f}%")
    print(f"  Influence: {factor.influence}")

# Agent contributions
for agent in decision.explanation.agent_contributions:
    print(f"{agent.agent_name}: {agent.vote} ({agent.confidence * 100:.1f}%)")
```

### Updating with Outcome

```python
# After trade executes
explainable.update_outcome(
    decision_id=decision.explanation_id,
    executed=True,
    execution_price=250.50,
    outcome="success",
    actual_return=0.05  # 5% return
)

# Agent can now learn from this outcome!
```

---

## Visual Decision Trees

### Creating Decision Trees

```python
from superstandard.agents import DecisionTreeVisualizer

visualizer = DecisionTreeVisualizer()
tree = visualizer.create_tree(decision.explanation)

# Get tree as dictionary for visualization
tree_dict = tree.to_dict()
```

### Tree Structure

```
🎯 BUY AAPL (Confidence: 78%)
├─ Technical Indicators [38%]
│  ├─ RSI: RSI at 45.0 indicates bullish momentum
│  ├─ MACD: MACD signal suggests bullish trend
│  └─ Trading Volume: 50,000,000 shares
├─ Market Regime [25%]
│  └─ Detected bull market conditions
├─ Ensemble Consensus [30%]
│  ├─ BUY: 4 agents
│  └─ HOLD: 1 agent
└─ Risk Assessment [7%]
    └─ Low risk identified
```

### Using with Dashboard

The decision tree is automatically rendered in the dashboard:

```html
<!-- Access at http://localhost:8080/explainable-dashboard -->
```

---

## Natural Language Q&A

### Asking Questions

```python
# Ask questions in plain English
answer = explainable.ask(
    "Why did you buy AAPL?",
    decision.explanation_id
)
print(answer)

# More questions
questions = [
    "What were the top factors?",
    "How confident were you?",
    "Did all agents agree?",
    "What risks did you identify?",
    "Why not sell instead?"
]

for question in questions:
    answer = explainable.ask(question, decision.explanation_id)
    print(f"Q: {question}")
    print(f"A: {answer}\n")
```

### Supported Question Types

| Question Type | Example | Response |
|--------------|---------|----------|
| Why questions | "Why did you buy?" | Full reasoning summary |
| Factor questions | "What were the top factors?" | Top 3 factors with explanations |
| Confidence questions | "How confident were you?" | Confidence % + breakdown |
| Agent agreement | "Did all agents agree?" | Vote distribution |
| Risk questions | "What are the risks?" | Identified risks |

---

## Decision Replay System

### Recording Decisions

```python
from superstandard.agents import DecisionReplayEngine

# Create replay engine
replay_engine = DecisionReplayEngine()

# Record decisions as they happen
replay_engine.record_decision(decision1)
replay_engine.record_decision(decision2)
replay_engine.record_decision(decision3)
```

### Creating Replays

```python
# Replay all decisions for a symbol
replay = replay_engine.create_replay(symbol="AAPL")

# Step through replay
for frame in replay:
    print(f"\nFrame {frame.frame_number}/{frame.total_frames}")
    print(f"Time: {frame.timestamp}")
    print(frame.decision.natural_language_summary)
    print("-" * 80)
```

### Time Range Filtering

```python
from datetime import datetime, timedelta

# Replay decisions from last 30 days
replay = replay_engine.create_replay(
    symbol="AAPL",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
```

### Pattern Analysis

```python
# Analyze decision patterns
analysis = replay_engine.analyze_decision_pattern(
    symbol="AAPL",
    time_window=timedelta(days=30)
)

print(f"Total Decisions: {analysis['total_decisions']}")
print(f"Decision Distribution: {analysis['decision_distribution']}")
print(f"Average Confidence: {analysis['average_confidence'] * 100:.1f}%")
print(f"Success Rate: {analysis['success_rate'] * 100:.1f}%")
print(f"Most Common: {analysis['most_common_decision']}")
```

### Learning Insights

```python
# Extract learning insights
insights = replay_engine.get_learning_insights(
    symbol="AAPL",
    min_decisions=10
)

for insight in insights:
    print(insight)

# Example output:
# ✅ Higher confidence decisions (82%) are more likely to succeed
#    than lower confidence ones (65%)
# 📊 Observed 4 consecutive BUY decisions - agent identified sustained bullish trend
# 📈 Agent is improving! Success rate increased from 58% to 71%
```

### Exporting Replay Data

```python
# Export as JSON
json_data = replay_engine.export_replay_data("AAPL", format="json")

# Export as CSV
csv_data = replay_engine.export_replay_data("AAPL", format="csv")

# Save to file
with open("aapl_decisions.json", "w") as f:
    f.write(json_data)
```

---

## Dashboard Interface

### Accessing the Dashboard

```bash
# Start the API server
python -m uvicorn src.superstandard.api.server:app --host 0.0.0.0 --port 8080

# Open in browser
http://localhost:8080/explainable-dashboard
```

### Dashboard Features

#### 1. Decision Summary Card
- Current decision (BUY/SELL/HOLD)
- Confidence visualization
- Natural language summary
- Key insights
- Risk warnings

#### 2. Reasoning Factors Card
- All factors that influenced decision
- Visual weight bars
- Influence indicators (bullish/bearish/neutral)
- Confidence scores

#### 3. Agent Contributions Card
- Individual agent votes
- Vote distribution chart
- Specialist type breakdown
- Confidence levels

#### 4. Decision Tree Card
- Visual tree representation
- Interactive exploration
- Weight-based branch sizing

#### 5. Natural Language Q&A Card
- Ask questions in plain English
- Instant answers
- Suggested questions
- Conversation history

### Interactive Features

- **Real-time updates** - Live decision streaming
- **Question answering** - Type any question
- **Hover tooltips** - Additional details on hover
- **Responsive design** - Works on all devices
- **Dark/Light themes** - Choose your preference

---

## API Reference

### ExplainableAgentEnsemble

```python
class ExplainableAgentEnsemble:
    def __init__(self, ensemble: AgentEnsemble)

    def make_explainable_decision(
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> ExplainableDecision

    def ask(question: str, decision_id: str) -> str

    def get_decision_tree(decision_id: str) -> Optional[Dict[str, Any]]

    def get_explanation(decision_id: str) -> Optional[DecisionExplanation]

    def update_outcome(
        decision_id: str,
        executed: bool,
        execution_price: Optional[float] = None,
        outcome: Optional[str] = None,
        actual_return: Optional[float] = None
    )

    def get_recent_decisions(
        limit: int = 10,
        symbol: Optional[str] = None
    ) -> List[DecisionExplanation]
```

### DecisionExplanationEngine

```python
class DecisionExplanationEngine:
    def explain_decision(
        decision_id: str,
        symbol: str,
        decision: str,
        confidence: float,
        reasoning_factors: List[ReasoningFactor],
        agent_contributions: List[AgentContribution],
        market_context: Optional[Dict[str, Any]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> DecisionExplanation

    def answer_question(decision_id: str, question: str) -> str

    def get_explanation(decision_id: str) -> Optional[DecisionExplanation]

    def update_outcome(
        decision_id: str,
        executed: bool,
        execution_price: Optional[float] = None,
        outcome: Optional[str] = None,
        actual_return: Optional[float] = None
    )
```

### DecisionReplayEngine

```python
class DecisionReplayEngine:
    def record_decision(decision: DecisionExplanation)

    def create_replay(
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ReplayFrame]

    def analyze_decision_pattern(
        symbol: str,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]

    def get_learning_insights(
        symbol: str,
        min_decisions: int = 10
    ) -> List[str]

    def export_replay_data(symbol: str, format: str = 'json') -> str
```

---

## Best Practices

### 1. Always Use Explainable Ensembles for Production

```python
# ✅ Good: Explainable from the start
explainable = create_explainable_ensemble(ensemble)

# ❌ Bad: Black box decisions
decision = ensemble.make_decision(market_data)
```

### 2. Log All Decisions for Learning

```python
# ✅ Good: Record all decisions
replay_engine = DecisionReplayEngine()
replay_engine.record_decision(decision.explanation)

# Later, analyze patterns and improve
insights = replay_engine.get_learning_insights("AAPL")
```

### 3. Update Outcomes for Continuous Learning

```python
# ✅ Good: Track outcomes
explainable.update_outcome(
    decision_id=decision.explanation_id,
    executed=True,
    execution_price=price,
    outcome="success" if profit > 0 else "failure",
    actual_return=profit / capital
)
```

### 4. Use Natural Language Q&A for Debugging

```python
# ✅ Good: Ask questions when confused
if decision.action == "sell" and expected == "buy":
    reason = explainable.ask("Why did you sell?", decision.explanation_id)
    print(f"Debug: {reason}")
```

### 5. Monitor Confidence Trends

```python
# ✅ Good: Track confidence over time
recent = explainable.get_recent_decisions(limit=100, symbol="AAPL")
avg_confidence = statistics.mean(d.confidence for d in recent)

if avg_confidence < 0.5:
    print("⚠️ Warning: Low average confidence - investigate!")
```

---

## Advanced Features

### Custom Reasoning Factors

```python
from superstandard.agents import ReasoningFactor, ReasoningFactorType

# Add custom factors
custom_factor = ReasoningFactor(
    factor_type=ReasoningFactorType.SENTIMENT,
    name="Twitter Sentiment",
    value=0.75,
    weight=0.15,
    confidence=0.80,
    influence="bullish",
    explanation="Twitter sentiment 75% positive for $AAPL",
    supporting_data={"tweet_count": 1500, "positive_ratio": 0.75}
)
```

### Integration with Continuous Evolution

```python
from superstandard.agents import ContinuousEvolutionEngine

# Continuous evolution with explainability
evolution_engine = ContinuousEvolutionEngine(config)
explainable = create_explainable_ensemble(ensemble)

# Monitor decisions during evolution
evolution_engine.start_monitoring(ensemble_id)

# Decisions are automatically explainable!
```

### Integration with Paper Trading

```python
from superstandard.agents import PaperTradingEngine, PaperTradingConfig

# Paper trading with full explainability
trading_engine = PaperTradingEngine(PaperTradingConfig(...))
explainable = create_explainable_ensemble(ensemble)

# Make explainable decision
decision = explainable.make_explainable_decision(symbol, market_data)

# Execute with full audit trail
result = trading_engine.execute_decision(symbol, decision)

# Update outcome
if result.success:
    explainable.update_outcome(
        decision.explanation_id,
        executed=True,
        execution_price=result.price,
        outcome="success" if result.success else "failure"
    )
```

---

## Troubleshooting

### "Explanation not found"

```python
# Make sure you're using the correct decision_id
explanation = explainable.get_explanation(decision.explanation_id)
if not explanation:
    print("Decision ID not found - may have been recorded to different engine")
```

### Low Quality Explanations

```python
# Ensure rich market data is provided
market_data = {
    'current_price': 150.00,
    'rsi': 45.0,           # ✅ Include technical indicators
    'macd': 0.8,           # ✅ More factors = better explanations
    'volume': 50_000_000,
    'trend': 'bullish'     # ✅ Include regime detection
}
```

### Natural Language Answers Don't Make Sense

```python
# Check that explanation was properly created
if decision.explanation:
    print(decision.explanation.natural_language_summary)
else:
    print("Explanation not created - check ensemble configuration")
```

---

## Examples

### Example 1: Complete Workflow

```python
from superstandard.agents import (
    TemplateLibrary,
    create_explainable_ensemble,
    DecisionReplayEngine
)

# Setup
library = TemplateLibrary()
ensemble = library.get_template("balanced_trader").create_ensemble()
explainable = create_explainable_ensemble(ensemble)
replay_engine = DecisionReplayEngine()

# Make decision
market_data = {'current_price': 150.00, 'rsi': 45.0, 'macd': 0.8}
decision = explainable.make_explainable_decision("AAPL", market_data)

# Show explanation
print(decision.explanation.natural_language_summary)

# Ask questions
answer = explainable.ask("Why did you buy?", decision.explanation_id)
print(answer)

# Record for replay
replay_engine.record_decision(decision.explanation)

# Later: Analyze patterns
insights = replay_engine.get_learning_insights("AAPL")
for insight in insights:
    print(insight)
```

### Example 2: Debugging Wrong Decision

```python
# Decision seems wrong, let's understand why
decision = explainable.make_explainable_decision("TSLA", market_data)

if decision.action == "buy" and expected == "sell":
    print("🤔 Unexpected decision, investigating...\n")

    # Check reasoning factors
    print("Top Factors:")
    for factor in sorted(decision.explanation.reasoning_factors,
                         key=lambda f: f.weight * f.confidence,
                         reverse=True)[:3]:
        print(f"  {factor.name}: {factor.explanation}")

    # Check agent votes
    print("\nAgent Votes:")
    for agent in decision.explanation.agent_contributions:
        print(f"  {agent.agent_name}: {agent.vote} ({agent.confidence * 100:.1f}%)")

    # Ask why
    answer = explainable.ask("Why did you buy instead of sell?", decision.explanation_id)
    print(f"\nExplanation: {answer}")
```

---

## Next Steps

1. **Run the Demo**
   ```bash
   python examples/explainable_ai_demo.py
   ```

2. **Try the Dashboard**
   ```bash
   http://localhost:8080/explainable-dashboard
   ```

3. **Integrate with Your Code**
   - Wrap ensembles with `create_explainable_ensemble()`
   - Record decisions for replay
   - Ask questions when debugging

4. **Build Custom UIs**
   - Use the API to build custom visualizations
   - Export replay data for external analysis
   - Create custom reports

---

## Resources

- **Code Examples**: `examples/explainable_ai_demo.py`
- **Dashboard**: `src/superstandard/api/explainable_dashboard.html`
- **API Documentation**: This guide
- **Platform Guide**: `COMPLETE_PLATFORM_GUIDE.md`

---

**Built with the Agentic Forge Platform** 🚀

*Making AI decisions transparent, understandable, and trustworthy.*
