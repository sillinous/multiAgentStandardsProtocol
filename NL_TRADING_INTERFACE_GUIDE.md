# Natural Language Trading Interface Guide 🗣️💹

**Revolutionary conversational AI trader - Talk to your trading system in plain English!**

## Table of Contents

1. [Overview](#overview)
2. [Why Natural Language?](#why-natural-language)
3. [Quick Start](#quick-start)
4. [Core Components](#core-components)
5. [Query Understanding](#query-understanding)
6. [Trading Commands](#trading-commands)
7. [Conversational Agent](#conversational-agent)
8. [Integration](#integration)
9. [API Reference](#api-reference)
10. [Examples](#examples)
11. [Best Practices](#best-practices)

---

## Overview

The Natural Language Trading Interface is the **FIRST conversational AI trader** that lets you interact with your trading system using plain English.

✅ **Natural language understanding** - Ask questions and give commands naturally
✅ **Trading execution** - Execute trades with simple commands
✅ **Sentiment integration** - Ask about market sentiment
✅ **Explainable AI** - Get transparent explanations of decisions
✅ **Conversation memory** - Multi-turn dialogue with context
✅ **Portfolio management** - Check status and performance

**This is revolutionary because you can literally CHAT with your AI trader like a human assistant!**

---

## Why Natural Language?

### The Problem

Traditional trading systems require:
- Complex APIs with specific parameters
- Remembering exact command syntax
- No conversational context
- Difficult to ask "why" questions

### Our Solution

**Just talk naturally:**

```
❌ Old Way:
api.place_order(symbol="AAPL", side="buy", quantity=100, order_type="market")

✅ New Way:
"Buy 100 shares of AAPL"
```

**Ask questions naturally:**

```
❌ Old Way:
sentiment_data = api.get_sentiment("AAPL")
print(sentiment_data['overall_score'])

✅ New Way:
"What's the sentiment on AAPL?"
"Why did you recommend buying it?"
"How confident are you?"
```

---

## Quick Start

### Installation

Already included! No additional dependencies.

### Basic Usage

```python
from superstandard.agents import ConversationalAgent

# Create agent
agent = ConversationalAgent()

# Chat!
response = agent.chat("Hello!")
print(response)

response = agent.chat("What's the sentiment on AAPL?")
print(response)

response = agent.chat("Buy 100 shares of AAPL")
print(response)
```

### Full Setup

```python
from superstandard.agents import (
    ConversationalAgent,
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,
    PaperTradingEngine,
    PaperTradingConfig
)

# Create ensemble
library = TemplateLibrary()
ensemble = library.get_template("balanced_trader").create_ensemble()

# Add sentiment + explainability
explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

# Create paper trading
config = PaperTradingConfig(initial_cash=100000.0)
paper_engine = PaperTradingEngine(config=config)

# Create conversational agent
agent = ConversationalAgent(
    paper_trading_engine=paper_engine,
    explainable_ensemble=explainable,
    sentiment_enhancer=sentiment_enhancer
)

# Now you can chat!
agent.chat("What's the sentiment on TSLA?")
agent.chat("Buy 50 shares of TSLA")
agent.chat("Why did you recommend that?")
```

### Run the Demo

```bash
python examples/conversational_trading_demo.py
```

---

## Core Components

### 1. Query Processor

Understands natural language queries and extracts intent.

```python
from superstandard.agents import QueryProcessor

processor = QueryProcessor()

# Process a query
query = processor.process("Buy 100 shares of AAPL")

print(query.query_type)     # COMMAND
print(query.intent)         # BUY
print(query.symbols)        # ['AAPL']
print(query.amount)         # 100.0
print(query.confidence)     # 0.85
```

**Capabilities:**
- Intent classification (question, command, request, greeting, explanation)
- Entity extraction (stock symbols, amounts, timeframes)
- Confidence scoring
- Support for multiple query patterns

### 2. Command Interpreter

Converts natural language commands into trading actions.

```python
from superstandard.agents import CommandInterpreter

interpreter = CommandInterpreter(paper_trading_engine=engine)

# Interpret and execute
query = processor.process("Buy 100 shares of AAPL")
command = interpreter.interpret(query)
result = interpreter.execute(command)

print(result.message)  # "✅ Bought 100 shares of AAPL at $175.50"
print(result.status)   # SUCCESS
```

**Supported Commands:**
- Buy/Sell orders
- Risk adjustment
- Trading control (start/stop)
- Portfolio requests

### 3. Conversational Agent

Main orchestrator combining all components.

```python
from superstandard.agents import ConversationalAgent

agent = ConversationalAgent(
    paper_trading_engine=engine,
    explainable_ensemble=explainable,
    sentiment_enhancer=sentiment_enhancer
)

# Chat interface
response = agent.chat("What's the sentiment on AAPL?")
# "💭 AAPL Sentiment: Positive (+0.75)
#    Trend: BULLISH
#    Keywords: growth, earnings, innovation, bullish, strong"

# Conversation history
history = agent.get_history()
recent = history.get_recent_turns(limit=5)
```

---

## Query Understanding

### Query Types

The system recognizes 5 types of queries:

| Type | Example | Description |
|------|---------|-------------|
| **QUESTION** | "What's the sentiment on AAPL?" | Asking for information |
| **COMMAND** | "Buy 100 shares of TSLA" | Trading action to execute |
| **REQUEST** | "Show me my portfolio" | Information retrieval |
| **GREETING** | "Hello!" | Conversation initiation |
| **EXPLANATION** | "Explain your strategy" | Request for explanation |

### Query Intents

More specific than types, intents capture what the user wants:

**Questions:**
- `WHY_DECISION` - "Why did you buy AAPL?"
- `WHAT_SENTIMENT` - "What's the sentiment on TSLA?"
- `HOW_CONFIDENT` - "How confident are you?"
- `WHAT_RISK` - "What are the risks?"

**Commands:**
- `BUY` - "Buy 100 shares of AAPL"
- `SELL` - "Sell all my TSLA"
- `ADJUST_RISK` - "Make me more conservative"
- `STOP_TRADING` - "Stop trading"

**Requests:**
- `SHOW_PORTFOLIO` - "Show my portfolio"
- `SHOW_POSITIONS` - "What do I own?"
- `SHOW_PERFORMANCE` - "How am I doing?"
- `FIND_OPPORTUNITIES` - "Find good stocks"

**Explanations:**
- `EXPLAIN_DECISION` - "Explain that decision"
- `EXPLAIN_STRATEGY` - "Explain your strategy"

### Entity Extraction

The system automatically extracts:

**Stock Symbols:**
```python
# Pattern 1: $SYMBOL
"Buy $AAPL"  → ['AAPL']

# Pattern 2: Uppercase words
"What's the sentiment on TSLA?"  → ['TSLA']

# Multiple symbols
"Compare AAPL and MSFT"  → ['AAPL', 'MSFT']
```

**Amounts:**
```python
# Share quantities
"Buy 100 shares of AAPL"  → amount: 100.0

# Dollar amounts
"Invest $5000 in TSLA"  → amount: 5000.0

# Implied from context
"Buy AAPL"  → amount: 10.0 (default)
```

**Timeframes:**
```python
"Show performance this week"  → timeframe: 'week'
"What happened yesterday?"  → timeframe: 'yesterday'
"Recent decisions"  → timeframe: 'recent'
```

---

## Trading Commands

### Buy Orders

```python
# Basic buy
"Buy AAPL"
"Purchase 100 shares of TSLA"
"Acquire 50 shares of NVDA"
"Go long on MSFT"

# With amounts
"Buy 100 shares of AAPL"
"Invest $5000 in TSLA"
"Buy $NVDA worth $1000"
```

### Sell Orders

```python
# Basic sell
"Sell AAPL"
"Dump my TSLA"
"Exit NVDA position"
"Close my MSFT"

# Partial sell
"Sell 50 shares of AAPL"
"Sell half my TSLA"

# Sell all
"Sell all my AAPL"
"Sell everything"
```

### Risk Adjustment

```python
# Conservative
"Make me more conservative"
"Be more careful"
"Reduce risk"

# Balanced
"Switch to balanced mode"
"Be moderate"

# Aggressive
"Make me more aggressive"
"Take more risks"
"Be bold"
```

### Trading Control

```python
# Stop trading
"Stop trading"
"Pause trading"
"Halt all trades"

# Start trading
"Start trading"
"Resume trading"
"Begin trading"
```

---

## Conversational Agent

### Creating an Agent

```python
from superstandard.agents import ConversationalAgent

# Minimal agent (no trading)
agent = ConversationalAgent()

# With paper trading
from superstandard.agents import PaperTradingEngine, PaperTradingConfig

config = PaperTradingConfig(initial_cash=100000.0)
engine = PaperTradingEngine(config=config)

agent = ConversationalAgent(paper_trading_engine=engine)

# Full agent with all features
from superstandard.agents import (
    TemplateLibrary,
    create_sentiment_enhanced_ensemble
)

library = TemplateLibrary()
ensemble = library.get_template("balanced_trader").create_ensemble()
explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

agent = ConversationalAgent(
    paper_trading_engine=engine,
    explainable_ensemble=explainable,
    sentiment_enhancer=sentiment_enhancer
)
```

### Chat Interface

```python
# Single turn
response = agent.chat("Hello!")
print(response)

# Multi-turn conversation
messages = [
    "What's the sentiment on AAPL?",
    "Sounds good! Buy 100 shares.",
    "Show me my portfolio.",
    "How confident are you in this position?"
]

for msg in messages:
    print(f"👤 {msg}")
    print(f"🤖 {agent.chat(msg)}\n")
```

### Conversation History

```python
# Get full history
history = agent.get_history()

print(f"Total turns: {len(history.turns)}")
print(f"Session start: {history.context.session_start}")

# Get recent turns
recent = history.get_recent_turns(limit=5)

for turn in recent:
    print(f"User: {turn.user_message}")
    print(f"Agent: {turn.response}")
    print(f"Type: {turn.query_type}, Intent: {turn.intent}")

# Get conversation context
context = agent.get_context()

print(f"Current symbols: {context.current_symbols}")
print(f"Recent decisions: {context.recent_decisions}")
print(f"Trading enabled: {agent.command_interpreter.trading_enabled}")
print(f"Risk level: {agent.command_interpreter.current_risk_level}")
```

### Conversation Context

The agent maintains context across turns:

```python
# First turn
"What's the sentiment on AAPL?"  # Stores 'AAPL' in context

# Second turn (references context)
"Buy 100 shares"  # Knows you mean AAPL from context

# Third turn
"Why did you recommend that?"  # References recent decision
```

---

## Integration

### With Explainable AI

```python
from superstandard.agents import (
    ConversationalAgent,
    create_explainable_ensemble,
    make_sentiment_aware_decision
)

# Create explainable ensemble
ensemble = library.get_template("balanced_trader").create_ensemble()
explainable = create_explainable_ensemble(ensemble)

# Create agent
agent = ConversationalAgent(explainable_ensemble=explainable)

# Make a decision
decision = explainable.make_explainable_decision(
    symbol="AAPL",
    market_data={'current_price': 175.50, 'rsi': 45.0}
)

# Store in context
agent.history.context.recent_decisions.append(decision.explanation_id)

# Now ask questions about it!
answer = agent.chat("Why did you make that decision?")
# Returns the full explanation with reasoning factors!

answer = agent.chat("How confident are you?")
# Returns confidence level from the decision

answer = agent.chat("What are the risks?")
# Returns identified risks from the explanation
```

### With Sentiment Analysis

```python
from superstandard.agents import (
    ConversationalAgent,
    SentimentEnhancedData
)

# Create sentiment enhancer
sentiment_enhancer = SentimentEnhancedData()

# Create agent
agent = ConversationalAgent(sentiment_enhancer=sentiment_enhancer)

# Ask sentiment questions
agent.chat("What's the sentiment on AAPL?")
# "💭 AAPL Sentiment: Positive (+0.75)
#    Trend: BULLISH
#    Keywords: growth, innovation, bullish"

agent.chat("What's Twitter saying about TSLA?")
# Returns Twitter-specific sentiment
```

### With Paper Trading

```python
from superstandard.agents import (
    ConversationalAgent,
    PaperTradingEngine,
    PaperTradingConfig,
    TradingMode
)

# Create paper trading engine
config = PaperTradingConfig(
    initial_cash=100000.0,
    trading_mode=TradingMode.PAPER,
    max_position_size=10000.0
)

engine = PaperTradingEngine(config=config)

# Create agent
agent = ConversationalAgent(paper_trading_engine=engine)

# Execute trades
agent.chat("Buy 100 shares of AAPL")
# "✅ Bought 100 shares of AAPL at $175.50"

agent.chat("Show my portfolio")
# "📊 Your Portfolio:
#    Total Value: $117,550.00
#    Cash: $82,450.00
#    Positions: 1
#    📈 Return: +17.55%"
```

---

## API Reference

### QueryProcessor

```python
class QueryProcessor:
    def process(self, text: str) -> ProcessedQuery:
        """Process natural language query"""
```

### ProcessedQuery

```python
@dataclass
class ProcessedQuery:
    original_text: str
    query_type: QueryType
    intent: QueryIntent
    confidence: float
    symbols: List[str]
    amount: Optional[float]
    timeframe: Optional[str]
    parameters: Dict[str, Any]
```

### CommandInterpreter

```python
class CommandInterpreter:
    def __init__(
        self,
        paper_trading_engine=None,
        default_quantity: float = 10.0,
        max_position_size: float = 10000.0
    )

    def interpret(self, query: ProcessedQuery) -> Optional[TradingCommand]
    def execute(self, command: TradingCommand) -> CommandResult
    def interpret_and_execute(self, query: ProcessedQuery) -> CommandResult

    def get_command_history(self, limit: int = 10) -> List[CommandResult]
    def get_trading_status(self) -> Dict[str, Any]
```

### ConversationalAgent

```python
class ConversationalAgent:
    def __init__(
        self,
        paper_trading_engine=None,
        explainable_ensemble=None,
        sentiment_enhancer=None,
        enable_confirmations: bool = False
    )

    def chat(self, user_message: str) -> str

    def get_history(self) -> ConversationHistory
    def get_context(self) -> ConversationContext
    def clear_history(self)
```

---

## Examples

### Example 1: Simple Chat

```python
from superstandard.agents import ConversationalAgent

agent = ConversationalAgent()

print(agent.chat("Hello!"))
# "Hello! I'm your AI trading assistant. How can I help you today?"

print(agent.chat("What can you do?"))
# "I can help you with trading decisions, sentiment analysis, and market insights."
```

### Example 2: Trading Commands

```python
from superstandard.agents import (
    ConversationalAgent,
    PaperTradingEngine,
    PaperTradingConfig
)

config = PaperTradingConfig(initial_cash=100000.0)
engine = PaperTradingEngine(config=config)
agent = ConversationalAgent(paper_trading_engine=engine)

# Execute trades
agent.chat("Buy 100 shares of AAPL")
# "✅ Bought 100 shares of AAPL at $175.50"

agent.chat("Show my portfolio")
# "📊 Your Portfolio: ..."

agent.chat("Sell 50 shares of AAPL")
# "✅ Sold 50 shares of AAPL at $176.00"
```

### Example 3: Sentiment Questions

```python
from superstandard.agents import (
    ConversationalAgent,
    SentimentEnhancedData
)

sentiment_enhancer = SentimentEnhancedData()
agent = ConversationalAgent(sentiment_enhancer=sentiment_enhancer)

response = agent.chat("What's the sentiment on AAPL?")
print(response)
# "💭 AAPL Sentiment: Positive (+0.75)
#    Trend: BULLISH
#    Keywords: growth, earnings, innovation"
```

### Example 4: Full Integration

```python
from superstandard.agents import (
    ConversationalAgent,
    TemplateLibrary,
    create_sentiment_enhanced_ensemble,
    PaperTradingEngine,
    PaperTradingConfig
)

# Setup
library = TemplateLibrary()
ensemble = library.get_template("balanced_trader").create_ensemble()
explainable, sentiment_enhancer = create_sentiment_enhanced_ensemble(ensemble)

config = PaperTradingConfig(initial_cash=100000.0)
engine = PaperTradingEngine(config=config)

agent = ConversationalAgent(
    paper_trading_engine=engine,
    explainable_ensemble=explainable,
    sentiment_enhancer=sentiment_enhancer
)

# Have a conversation
conversation = [
    "What's the sentiment on TSLA?",
    "Looks good! Buy 50 shares.",
    "Why did you recommend that?",
    "How confident are you?",
    "Show my portfolio."
]

for msg in conversation:
    print(f"👤 {msg}")
    print(f"🤖 {agent.chat(msg)}\n")
```

---

## Best Practices

### 1. Use Full Integration

```python
# ✅ Good: Full integration for best experience
agent = ConversationalAgent(
    paper_trading_engine=engine,
    explainable_ensemble=explainable,
    sentiment_enhancer=sentiment_enhancer
)

# ❌ Limited: Missing features
agent = ConversationalAgent()  # No trading, sentiment, or explanations
```

### 2. Provide Clear Commands

```python
# ✅ Good: Clear and specific
"Buy 100 shares of AAPL"
"What's the sentiment on TSLA?"

# ⚠️  Acceptable but less clear
"Buy AAPL"  # Uses default quantity
"How's TSLA doing?"  # May not trigger sentiment
```

### 3. Use Conversation Context

```python
# ✅ Good: Natural follow-up questions
"What's the sentiment on AAPL?"
"How confident are you?"  # References AAPL from context
"Buy 100 shares"  # References AAPL

# ❌ Less efficient: Repeating information
"What's the sentiment on AAPL?"
"How confident are you in AAPL?"  # Unnecessary repetition
"Buy 100 shares of AAPL"
```

### 4. Check Trading Status

```python
# ✅ Good: Monitor status
status = agent.command_interpreter.get_trading_status()
print(f"Trading enabled: {status['trading_enabled']}")
print(f"Risk level: {status['risk_level']}")

# View command history
history = agent.command_interpreter.get_command_history(limit=10)
```

### 5. Handle Errors Gracefully

```python
# ✅ Good: Check response types
response = agent.chat("Some ambiguous query")

# Get the turn to check type
last_turn = agent.history.turns[-1]

if last_turn.response_type == ResponseType.ERROR:
    print("Need to clarify the query")
elif last_turn.response_type == ResponseType.COMMAND_RESULT:
    print("Command was executed")
```

---

## Troubleshooting

### "I don't understand that command"

- **Issue**: Query processor can't determine intent
- **Fix**: Be more specific with commands
  ```python
  ❌ "Do something with AAPL"
  ✅ "Buy 100 shares of AAPL"
  ```

### "No symbol specified"

- **Issue**: Symbol not extracted from text
- **Fix**: Use clear symbol format
  ```python
  ❌ "Buy some Apple stock"
  ✅ "Buy AAPL" or "Buy $AAPL"
  ```

### "Sentiment data not available"

- **Issue**: Sentiment enhancer not connected
- **Fix**: Pass sentiment_enhancer to agent
  ```python
  enhancer = SentimentEnhancedData()
  agent = ConversationalAgent(sentiment_enhancer=enhancer)
  ```

### "Can't explain that decision"

- **Issue**: No explainable ensemble or recent decisions
- **Fix**: Ensure explainable ensemble is connected and decisions are made
  ```python
  agent = ConversationalAgent(explainable_ensemble=explainable)
  # Make a decision first, then ask about it
  ```

---

## Next Steps

1. **Run the Demo**
   ```bash
   python examples/conversational_trading_demo.py
   ```

2. **Integrate with Your System**
   - Connect your paper trading engine
   - Add your ensembles
   - Customize responses

3. **Extend Functionality**
   - Add new query intents
   - Implement custom commands
   - Enhance conversation memory

4. **Build a UI**
   - Create a chat interface
   - Add voice input
   - Build a mobile app

---

**Built with the Agentic Forge Platform** 🚀

*The FIRST platform with a conversational AI trader - talk to your trading system in plain English!*
