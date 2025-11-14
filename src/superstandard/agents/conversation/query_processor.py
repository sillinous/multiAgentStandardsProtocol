"""
Natural Language Query Processor

Processes natural language queries and determines user intent.
Enables users to ask questions and give commands in plain English.

Features:
- Intent classification (question, command, request)
- Entity extraction (symbols, amounts, dates)
- Query understanding
- Context awareness
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import re


# ============================================================================
# Query Models
# ============================================================================

class QueryType(str, Enum):
    """Type of query"""
    QUESTION = "question"           # "Why did you sell?"
    COMMAND = "command"             # "Buy 100 shares of AAPL"
    REQUEST = "request"             # "Show me my portfolio"
    GREETING = "greeting"           # "Hello"
    EXPLANATION = "explanation"     # "Explain this decision"


class QueryIntent(str, Enum):
    """Intent behind the query"""
    # Questions
    WHY_DECISION = "why_decision"           # "Why did you buy?"
    WHAT_SENTIMENT = "what_sentiment"       # "What's the sentiment?"
    HOW_CONFIDENT = "how_confident"         # "How confident are you?"
    WHAT_RISK = "what_risk"                 # "What are the risks?"

    # Commands
    BUY = "buy"                             # "Buy AAPL"
    SELL = "sell"                           # "Sell my TSLA"
    ADJUST_RISK = "adjust_risk"             # "Make me more conservative"
    STOP_TRADING = "stop_trading"           # "Stop trading"

    # Requests
    SHOW_PORTFOLIO = "show_portfolio"       # "Show portfolio"
    SHOW_POSITIONS = "show_positions"       # "What do I own?"
    SHOW_PERFORMANCE = "show_performance"   # "How am I doing?"
    FIND_OPPORTUNITIES = "find_opportunities" # "Find good stocks"

    # Explanations
    EXPLAIN_DECISION = "explain_decision"   # "Explain that decision"
    EXPLAIN_STRATEGY = "explain_strategy"   # "Explain your strategy"

    # Other
    GREETING = "greeting"                   # "Hello"
    UNKNOWN = "unknown"                     # Couldn't determine


@dataclass
class ProcessedQuery:
    """Processed natural language query"""

    original_text: str
    query_type: QueryType
    intent: QueryIntent
    confidence: float  # 0.0 to 1.0

    # Extracted entities
    symbols: List[str] = field(default_factory=list)
    amount: Optional[float] = None
    timeframe: Optional[str] = None

    # Additional context
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_text': self.original_text,
            'query_type': self.query_type.value,
            'intent': self.intent.value,
            'confidence': self.confidence,
            'symbols': self.symbols,
            'amount': self.amount,
            'timeframe': self.timeframe,
            'parameters': self.parameters
        }


# ============================================================================
# Query Processor
# ============================================================================

class QueryProcessor:
    """
    Processes natural language queries to determine intent

    Analyzes user input to understand what they want and extract
    relevant information like stock symbols, amounts, etc.

    Example:
        processor = QueryProcessor()

        query = processor.process("Why did you sell my AAPL shares?")

        print(f"Intent: {query.intent}")  # WHY_DECISION
        print(f"Symbols: {query.symbols}")  # ['AAPL']
        print(f"Type: {query.query_type}")  # QUESTION
    """

    # Pattern matching keywords
    WHY_KEYWORDS = {'why', 'reason', 'reasoning', 'because', 'how come'}
    WHAT_KEYWORDS = {'what', 'which', 'tell me'}
    HOW_KEYWORDS = {'how', 'describe'}

    BUY_KEYWORDS = {'buy', 'purchase', 'acquire', 'long', 'calls'}
    SELL_KEYWORDS = {'sell', 'dump', 'exit', 'short', 'puts', 'close'}

    SHOW_KEYWORDS = {'show', 'display', 'list', 'view', 'see'}

    GREETING_KEYWORDS = {'hi', 'hello', 'hey', 'greetings', 'good morning',
                        'good afternoon', 'good evening'}

    # Sentiment keywords
    SENTIMENT_KEYWORDS = {'sentiment', 'feeling', 'mood', 'buzz', 'vibe'}

    # Risk keywords
    RISK_KEYWORDS = {'risk', 'danger', 'risky', 'safe', 'conservative',
                    'aggressive', 'careful'}

    # Confidence keywords
    CONFIDENCE_KEYWORDS = {'confident', 'sure', 'certain', 'confidence'}

    # Portfolio keywords
    PORTFOLIO_KEYWORDS = {'portfolio', 'holdings', 'positions', 'own', 'have'}

    # Performance keywords
    PERFORMANCE_KEYWORDS = {'performance', 'doing', 'returns', 'profit',
                           'loss', 'p&l', 'pnl'}

    # Opportunity keywords
    OPPORTUNITY_KEYWORDS = {'opportunity', 'opportunities', 'find', 'recommend',
                           'suggest', 'good', 'best'}

    def __init__(self):
        """Initialize query processor"""
        pass

    def process(self, text: str) -> ProcessedQuery:
        """
        Process a natural language query

        Args:
            text: User's query in natural language

        Returns:
            ProcessedQuery with detected intent and entities
        """
        if not text or not text.strip():
            return ProcessedQuery(
                original_text=text,
                query_type=QueryType.UNKNOWN,
                intent=QueryIntent.UNKNOWN,
                confidence=0.0
            )

        # Normalize
        text_lower = text.lower().strip()

        # Extract entities
        symbols = self._extract_symbols(text)
        amount = self._extract_amount(text)
        timeframe = self._extract_timeframe(text)

        # Determine query type and intent
        query_type = self._determine_query_type(text_lower)
        intent = self._determine_intent(text_lower, query_type)

        # Calculate confidence
        confidence = self._calculate_confidence(text_lower, intent)

        return ProcessedQuery(
            original_text=text,
            query_type=query_type,
            intent=intent,
            confidence=confidence,
            symbols=symbols,
            amount=amount,
            timeframe=timeframe
        )

    def _determine_query_type(self, text: str) -> QueryType:
        """Determine the type of query"""

        # Check for greetings
        if any(greeting in text for greeting in self.GREETING_KEYWORDS):
            return QueryType.GREETING

        # Check for questions (starts with question words or ends with ?)
        if text.endswith('?') or any(word in text for word in
                                     self.WHY_KEYWORDS | self.WHAT_KEYWORDS | self.HOW_KEYWORDS):
            return QueryType.QUESTION

        # Check for commands (imperative verbs)
        if any(word in text for word in self.BUY_KEYWORDS | self.SELL_KEYWORDS):
            return QueryType.COMMAND

        # Check for requests (show, display, etc.)
        if any(word in text for word in self.SHOW_KEYWORDS):
            return QueryType.REQUEST

        # Check for explanations
        if 'explain' in text or 'tell me about' in text:
            return QueryType.EXPLANATION

        return QueryType.QUESTION  # Default to question

    def _determine_intent(self, text: str, query_type: QueryType) -> QueryIntent:
        """Determine the intent behind the query"""

        # Greetings
        if query_type == QueryType.GREETING:
            return QueryIntent.GREETING

        # Questions
        if query_type == QueryType.QUESTION:
            if any(word in text for word in self.WHY_KEYWORDS):
                if any(word in text for word in self.BUY_KEYWORDS | self.SELL_KEYWORDS):
                    return QueryIntent.WHY_DECISION

            if any(word in text for word in self.SENTIMENT_KEYWORDS):
                return QueryIntent.WHAT_SENTIMENT

            if any(word in text for word in self.CONFIDENCE_KEYWORDS):
                return QueryIntent.HOW_CONFIDENT

            if any(word in text for word in self.RISK_KEYWORDS):
                return QueryIntent.WHAT_RISK

        # Commands
        if query_type == QueryType.COMMAND:
            if any(word in text for word in self.BUY_KEYWORDS):
                return QueryIntent.BUY

            if any(word in text for word in self.SELL_KEYWORDS):
                return QueryIntent.SELL

            if any(word in text for word in self.RISK_KEYWORDS):
                if 'conservative' in text or 'safe' in text or 'careful' in text:
                    return QueryIntent.ADJUST_RISK
                if 'aggressive' in text or 'risky' in text:
                    return QueryIntent.ADJUST_RISK

            if 'stop' in text:
                return QueryIntent.STOP_TRADING

        # Requests
        if query_type == QueryType.REQUEST:
            if any(word in text for word in self.PORTFOLIO_KEYWORDS):
                return QueryIntent.SHOW_PORTFOLIO

            if 'position' in text:
                return QueryIntent.SHOW_POSITIONS

            if any(word in text for word in self.PERFORMANCE_KEYWORDS):
                return QueryIntent.SHOW_PERFORMANCE

            if any(word in text for word in self.OPPORTUNITY_KEYWORDS):
                return QueryIntent.FIND_OPPORTUNITIES

        # Explanations
        if query_type == QueryType.EXPLANATION:
            if 'decision' in text:
                return QueryIntent.EXPLAIN_DECISION
            if 'strategy' in text:
                return QueryIntent.EXPLAIN_STRATEGY

        return QueryIntent.UNKNOWN

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        symbols = []

        # Pattern 1: $SYMBOL format
        dollar_symbols = re.findall(r'\$([A-Z]{1,5})\b', text)
        symbols.extend(dollar_symbols)

        # Pattern 2: Standalone uppercase 2-5 letter words (likely symbols)
        # But exclude common words
        common_words = {'I', 'AM', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'TO',
                       'MY', 'ME', 'US', 'IT', 'IS', 'AT', 'ON', 'IN', 'OF'}

        words = text.split()
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?();:')

            # Check if it looks like a symbol
            if (clean_word.isupper() and
                2 <= len(clean_word) <= 5 and
                clean_word not in common_words and
                clean_word.isalpha()):
                if clean_word not in symbols:
                    symbols.append(clean_word)

        return symbols

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount or share quantity"""

        # Pattern: number followed by "shares" or "dollars"
        share_pattern = r'(\d+(?:\.\d+)?)\s*(?:shares?|stocks?)'
        match = re.search(share_pattern, text.lower())
        if match:
            return float(match.group(1))

        # Pattern: $amount
        dollar_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(dollar_pattern, text)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)

        # Pattern: standalone number (if context suggests it's an amount)
        if 'buy' in text.lower() or 'sell' in text.lower():
            number_pattern = r'\b(\d+(?:\.\d+)?)\b'
            match = re.search(number_pattern, text)
            if match:
                return float(match.group(1))

        return None

    def _extract_timeframe(self, text: str) -> Optional[str]:
        """Extract timeframe references"""

        timeframes = {
            'today': 'today',
            'yesterday': 'yesterday',
            'this week': 'week',
            'last week': 'last_week',
            'this month': 'month',
            'last month': 'last_month',
            'this year': 'year',
            'recently': 'recent',
            'latest': 'latest'
        }

        text_lower = text.lower()
        for phrase, timeframe in timeframes.items():
            if phrase in text_lower:
                return timeframe

        return None

    def _calculate_confidence(self, text: str, intent: QueryIntent) -> float:
        """Calculate confidence in intent detection"""

        if intent == QueryIntent.UNKNOWN:
            return 0.0

        # Start with base confidence
        confidence = 0.5

        # Increase confidence based on keyword matches
        keyword_sets = {
            QueryIntent.WHY_DECISION: self.WHY_KEYWORDS,
            QueryIntent.WHAT_SENTIMENT: self.SENTIMENT_KEYWORDS,
            QueryIntent.HOW_CONFIDENT: self.CONFIDENCE_KEYWORDS,
            QueryIntent.WHAT_RISK: self.RISK_KEYWORDS,
            QueryIntent.BUY: self.BUY_KEYWORDS,
            QueryIntent.SELL: self.SELL_KEYWORDS,
            QueryIntent.SHOW_PORTFOLIO: self.PORTFOLIO_KEYWORDS,
            QueryIntent.SHOW_PERFORMANCE: self.PERFORMANCE_KEYWORDS,
            QueryIntent.FIND_OPPORTUNITIES: self.OPPORTUNITY_KEYWORDS
        }

        if intent in keyword_sets:
            keywords = keyword_sets[intent]
            matches = sum(1 for keyword in keywords if keyword in text)
            confidence += min(matches * 0.15, 0.4)

        # Cap at 1.0
        return min(confidence, 1.0)


# ============================================================================
# Utility Functions
# ============================================================================

def quick_process(text: str) -> ProcessedQuery:
    """Quick process a query"""
    processor = QueryProcessor()
    return processor.process(text)
