"""
Conversational Trading Agent

The main agent for natural language trading interactions.
Combines query understanding, command execution, and explainable AI
into a conversational interface.

This is the FIRST conversational AI trader that can:
- Understand natural language
- Execute trading commands
- Explain decisions transparently
- Maintain conversation context
- Answer questions about its reasoning
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .query_processor import QueryProcessor, ProcessedQuery, QueryType, QueryIntent
from .command_interpreter import CommandInterpreter, CommandResult, CommandStatus


# ============================================================================
# Conversation Models
# ============================================================================

class ResponseType(str, Enum):
    """Type of response"""
    ANSWER = "answer"              # Answer to a question
    COMMAND_RESULT = "command_result"  # Result of command execution
    EXPLANATION = "explanation"    # Explanation of decision
    GREETING = "greeting"          # Greeting response
    ERROR = "error"                # Error message
    SUGGESTION = "suggestion"      # Suggestion for next action


@dataclass
class ConversationTurn:
    """Single turn in conversation"""

    # User input
    user_message: str
    processed_query: ProcessedQuery
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Agent response
    response: str = ""
    response_type: ResponseType = ResponseType.ANSWER
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_message': self.user_message,
            'query_type': self.processed_query.query_type.value,
            'intent': self.processed_query.intent.value,
            'response': self.response,
            'response_type': self.response_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }


@dataclass
class ConversationContext:
    """Context for ongoing conversation"""

    # Current state
    current_symbols: List[str] = field(default_factory=list)
    current_portfolio_value: float = 0.0
    recent_decisions: List[str] = field(default_factory=list)  # Decision IDs

    # Conversation state
    last_query_type: Optional[QueryType] = None
    last_intent: Optional[QueryIntent] = None
    awaiting_confirmation: bool = False
    confirmation_command: Optional[Any] = None

    # Metadata
    session_start: datetime = field(default_factory=datetime.utcnow)
    total_turns: int = 0


@dataclass
class ConversationHistory:
    """Full conversation history"""

    turns: List[ConversationTurn] = field(default_factory=list)
    context: ConversationContext = field(default_factory=ConversationContext)

    def add_turn(self, turn: ConversationTurn):
        """Add a turn to history"""
        self.turns.append(turn)
        self.context.total_turns += 1
        self.context.last_query_type = turn.processed_query.query_type
        self.context.last_intent = turn.processed_query.intent

    def get_recent_turns(self, limit: int = 5) -> List[ConversationTurn]:
        """Get recent conversation turns"""
        return self.turns[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'turns': [turn.to_dict() for turn in self.turns],
            'total_turns': len(self.turns),
            'session_start': self.context.session_start.isoformat()
        }


# ============================================================================
# Conversational Agent
# ============================================================================

class ConversationalAgent:
    """
    Main conversational trading agent

    Provides a natural language interface for trading, combining:
    - Query understanding (QueryProcessor)
    - Command execution (CommandInterpreter)
    - Decision explanation (ExplainableAgentEnsemble)
    - Conversation management

    Example:
        # Setup
        agent = ConversationalAgent(
            paper_trading_engine=engine,
            explainable_ensemble=ensemble
        )

        # Chat!
        response = agent.chat("What's the sentiment on AAPL?")
        print(response)

        response = agent.chat("Buy 100 shares of AAPL")
        print(response)

        response = agent.chat("Why did you recommend that?")
        print(response)
    """

    def __init__(
        self,
        paper_trading_engine=None,
        explainable_ensemble=None,
        sentiment_enhancer=None,
        enable_confirmations: bool = False
    ):
        """
        Initialize conversational agent

        Args:
            paper_trading_engine: Optional paper trading engine for execution
            explainable_ensemble: Optional explainable ensemble for decisions
            sentiment_enhancer: Optional sentiment enhancer for market data
            enable_confirmations: Require confirmation before executing commands
        """
        # Core components
        self.query_processor = QueryProcessor()
        self.command_interpreter = CommandInterpreter(paper_trading_engine)

        # AI components
        self.explainable_ensemble = explainable_ensemble
        self.sentiment_enhancer = sentiment_enhancer

        # Conversation state
        self.history = ConversationHistory()
        self.enable_confirmations = enable_confirmations

        # Response templates
        self._init_response_templates()

    def chat(self, user_message: str) -> str:
        """
        Main chat interface

        Args:
            user_message: User's natural language message

        Returns:
            Agent's response as natural language
        """
        # Process query
        processed_query = self.query_processor.process(user_message)

        # Create conversation turn
        turn = ConversationTurn(
            user_message=user_message,
            processed_query=processed_query
        )

        # Route to appropriate handler
        if processed_query.query_type == QueryType.GREETING:
            response = self._handle_greeting(turn)

        elif processed_query.query_type == QueryType.QUESTION:
            response = self._handle_question(turn)

        elif processed_query.query_type == QueryType.COMMAND:
            response = self._handle_command(turn)

        elif processed_query.query_type == QueryType.REQUEST:
            response = self._handle_request(turn)

        elif processed_query.query_type == QueryType.EXPLANATION:
            response = self._handle_explanation(turn)

        else:
            response = "I'm not sure I understood that. Could you rephrase?"
            turn.response_type = ResponseType.ERROR

        # Set response
        turn.response = response

        # Add to history
        self.history.add_turn(turn)

        return response

    def get_history(self) -> ConversationHistory:
        """Get conversation history"""
        return self.history

    def clear_history(self):
        """Clear conversation history"""
        self.history = ConversationHistory()

    def get_context(self) -> ConversationContext:
        """Get current conversation context"""
        return self.history.context

    # ========================================================================
    # Handler Methods
    # ========================================================================

    def _handle_greeting(self, turn: ConversationTurn) -> str:
        """Handle greeting"""
        turn.response_type = ResponseType.GREETING

        greetings = [
            "Hello! I'm your AI trading assistant. How can I help you today?",
            "Hi! Ready to discuss trading strategies and market opportunities!",
            "Hey there! What would you like to know about your portfolio?",
            "Hello! I can help you with trading decisions, sentiment analysis, and market insights."
        ]

        # Return a greeting based on time or context
        import random
        return random.choice(greetings)

    def _handle_question(self, turn: ConversationTurn) -> str:
        """Handle questions"""
        query = turn.processed_query
        intent = query.intent

        # Route to specific question handlers
        if intent == QueryIntent.WHY_DECISION:
            return self._answer_why_decision(turn)

        elif intent == QueryIntent.WHAT_SENTIMENT:
            return self._answer_sentiment_question(turn)

        elif intent == QueryIntent.HOW_CONFIDENT:
            return self._answer_confidence_question(turn)

        elif intent == QueryIntent.WHAT_RISK:
            return self._answer_risk_question(turn)

        else:
            # General question - try to answer from context
            if self.explainable_ensemble:
                # Try to answer using explainable AI
                recent_decision_id = (self.history.context.recent_decisions[-1]
                                     if self.history.context.recent_decisions else None)

                if recent_decision_id:
                    try:
                        answer = self.explainable_ensemble.ask(
                            question=query.original_text,
                            decision_id=recent_decision_id
                        )
                        turn.response_type = ResponseType.ANSWER
                        return answer
                    except:
                        pass

            return "I'm not sure how to answer that. Could you be more specific?"

    def _handle_command(self, turn: ConversationTurn) -> str:
        """Handle trading commands"""
        query = turn.processed_query

        # Interpret command
        command = self.command_interpreter.interpret(query)

        if not command:
            turn.response_type = ResponseType.ERROR
            return "I couldn't interpret that command. Try something like 'Buy 100 shares of AAPL'."

        # Check if confirmation is required
        if self.enable_confirmations and not self.history.context.awaiting_confirmation:
            self.history.context.awaiting_confirmation = True
            self.history.context.confirmation_command = command
            turn.response_type = ResponseType.SUGGESTION
            return f"⚠️  Are you sure you want to {command.command_type.value} {command.symbol or ''}? Say 'yes' to confirm."

        # Execute command
        result = self.command_interpreter.execute(command)

        # Clear confirmation state
        self.history.context.awaiting_confirmation = False
        self.history.context.confirmation_command = None

        # Store result
        turn.data['command_result'] = result.to_dict()
        turn.response_type = ResponseType.COMMAND_RESULT

        # Update context
        if command.symbol and command.symbol not in self.history.context.current_symbols:
            self.history.context.current_symbols.append(command.symbol)

        return result.message

    def _handle_request(self, turn: ConversationTurn) -> str:
        """Handle information requests"""
        query = turn.processed_query
        intent = query.intent

        if intent == QueryIntent.SHOW_PORTFOLIO:
            return self._show_portfolio(turn)

        elif intent == QueryIntent.SHOW_POSITIONS:
            return self._show_positions(turn)

        elif intent == QueryIntent.SHOW_PERFORMANCE:
            return self._show_performance(turn)

        elif intent == QueryIntent.FIND_OPPORTUNITIES:
            return self._find_opportunities(turn)

        else:
            return "I can show you your portfolio, positions, performance, or find opportunities. What would you like?"

    def _handle_explanation(self, turn: ConversationTurn) -> str:
        """Handle explanation requests"""
        query = turn.processed_query

        if query.intent == QueryIntent.EXPLAIN_DECISION:
            return self._explain_decision(turn)

        elif query.intent == QueryIntent.EXPLAIN_STRATEGY:
            return self._explain_strategy(turn)

        else:
            return "I can explain my decisions or strategy. What would you like to know?"

    # ========================================================================
    # Specific Answer Methods
    # ========================================================================

    def _answer_why_decision(self, turn: ConversationTurn) -> str:
        """Answer why a decision was made"""
        if not self.explainable_ensemble:
            return "I don't have access to decision explanations right now."

        recent_decision_id = (self.history.context.recent_decisions[-1]
                             if self.history.context.recent_decisions else None)

        if not recent_decision_id:
            return "I haven't made any recent decisions to explain."

        try:
            explanation = self.explainable_ensemble.get_explanation(recent_decision_id)
            if explanation:
                return explanation.natural_language_summary
        except:
            pass

        return "I can't find the explanation for that decision."

    def _answer_sentiment_question(self, turn: ConversationTurn) -> str:
        """Answer sentiment questions"""
        query = turn.processed_query
        symbol = query.symbols[0] if query.symbols else None

        if not symbol:
            # Get from context
            symbol = (self.history.context.current_symbols[-1]
                     if self.history.context.current_symbols else None)

        if not symbol:
            return "Which stock's sentiment would you like to know about?"

        if not self.sentiment_enhancer:
            return "I don't have access to sentiment data right now."

        # Get sentiment
        try:
            market_data = {}
            enhanced = self.sentiment_enhancer.enhance(symbol, market_data)

            if 'overall_sentiment' in enhanced:
                score = enhanced['overall_sentiment']
                trend = enhanced.get('sentiment_trend', 'neutral')
                keywords = enhanced.get('trending_keywords', [])

                sentiment_label = self._sentiment_label(score)

                response = f"💭 {symbol} Sentiment: {sentiment_label} ({score:+.2f})\n"
                response += f"   Trend: {trend.upper()}\n"

                if keywords:
                    response += f"   Keywords: {', '.join(keywords[:5])}"

                return response
        except Exception as e:
            return f"I couldn't fetch sentiment data: {str(e)}"

        return f"No sentiment data available for {symbol}."

    def _answer_confidence_question(self, turn: ConversationTurn) -> str:
        """Answer confidence questions"""
        if not self.history.context.recent_decisions:
            return "I haven't made any recent decisions to report confidence on."

        # Get last decision
        recent_decision_id = self.history.context.recent_decisions[-1]

        if self.explainable_ensemble:
            try:
                explanation = self.explainable_ensemble.get_explanation(recent_decision_id)
                if explanation:
                    # Find confidence from decision
                    confidence = explanation.metadata.get('confidence', 0)
                    return f"I'm {confidence * 100:.1f}% confident in that decision based on multiple factors including technical indicators and sentiment."
            except:
                pass

        return "I'm not sure about the confidence level for that decision."

    def _answer_risk_question(self, turn: ConversationTurn) -> str:
        """Answer risk questions"""
        if not self.explainable_ensemble or not self.history.context.recent_decisions:
            return "I haven't identified any specific risks yet."

        recent_decision_id = self.history.context.recent_decisions[-1]

        try:
            explanation = self.explainable_ensemble.get_explanation(recent_decision_id)
            if explanation and explanation.risks_identified:
                response = "⚠️  Risks Identified:\n"
                for i, risk in enumerate(explanation.risks_identified, 1):
                    response += f"   {i}. {risk}\n"
                return response.strip()
        except:
            pass

        return "No specific risks identified for the current situation."

    def _show_portfolio(self, turn: ConversationTurn) -> str:
        """Show portfolio information"""
        if not self.command_interpreter.paper_trading_engine:
            return "Portfolio tracking is not available. Please connect a paper trading engine."

        # Get portfolio from paper trading engine
        try:
            portfolio = self.command_interpreter.paper_trading_engine.get_portfolio_summary()

            response = "📊 Your Portfolio:\n"
            response += f"   Total Value: ${portfolio.get('total_value', 0):,.2f}\n"
            response += f"   Cash: ${portfolio.get('cash', 0):,.2f}\n"
            response += f"   Positions: {portfolio.get('position_count', 0)}\n"

            if portfolio.get('total_return'):
                ret = portfolio['total_return']
                emoji = "📈" if ret > 0 else "📉"
                response += f"   {emoji} Return: {ret:+.2f}%"

            return response
        except:
            return "💼 Portfolio: Connect paper trading to see details."

    def _show_positions(self, turn: ConversationTurn) -> str:
        """Show current positions"""
        if not self.command_interpreter.paper_trading_engine:
            return "Position tracking is not available."

        try:
            positions = self.command_interpreter.paper_trading_engine.get_positions()

            if not positions:
                return "You currently have no open positions."

            response = "📍 Current Positions:\n"
            for pos in positions:
                symbol = pos.get('symbol')
                qty = pos.get('quantity', 0)
                value = pos.get('market_value', 0)
                pnl = pos.get('unrealized_pl', 0)
                emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"

                response += f"   {emoji} {symbol}: {qty} shares (${value:,.2f}, {pnl:+.2f}%)\n"

            return response.strip()
        except:
            return "Could not retrieve positions."

    def _show_performance(self, turn: ConversationTurn) -> str:
        """Show performance metrics"""
        return "📈 Performance tracking coming soon! I'll be able to show you returns, win rate, and more."

    def _find_opportunities(self, turn: ConversationTurn) -> str:
        """Find trading opportunities"""
        return "🔍 Opportunity scanning coming soon! I'll analyze market data to find promising stocks."

    def _explain_decision(self, turn: ConversationTurn) -> str:
        """Explain a specific decision"""
        if not self.explainable_ensemble or not self.history.context.recent_decisions:
            return "No recent decisions to explain."

        recent_decision_id = self.history.context.recent_decisions[-1]

        try:
            explanation = self.explainable_ensemble.get_explanation(recent_decision_id)
            if explanation:
                return explanation.natural_language_summary
        except:
            pass

        return "I couldn't find an explanation for that decision."

    def _explain_strategy(self, turn: ConversationTurn) -> str:
        """Explain trading strategy"""
        return """
🎯 My Trading Strategy:

I use a multi-agent ensemble approach that combines:

1. **Technical Analysis** - RSI, MACD, moving averages
2. **Sentiment Analysis** - News, Twitter, Reddit sentiment
3. **Risk Management** - Position sizing, stop losses
4. **Explainable AI** - Full transparency in decisions

Each decision is made by multiple specialized agents voting together,
with full explanations of the reasoning behind each choice.
        """.strip()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.5:
            return "Very Positive 🚀"
        elif score > 0.2:
            return "Positive 📈"
        elif score > -0.2:
            return "Neutral ➡️"
        elif score > -0.5:
            return "Negative 📉"
        else:
            return "Very Negative 💀"

    def _init_response_templates(self):
        """Initialize response templates"""
        self.templates = {
            'unknown_symbol': "I'm not sure which stock you're referring to. Could you specify the symbol?",
            'need_more_info': "I need a bit more information. Could you be more specific?",
            'command_failed': "Sorry, I couldn't execute that command. {error}",
            'not_available': "That feature isn't available right now.",
        }


# ============================================================================
# Utility Functions
# ============================================================================

def create_conversational_agent(
    paper_trading_engine=None,
    explainable_ensemble=None,
    sentiment_enhancer=None
) -> ConversationalAgent:
    """
    Create a fully configured conversational agent

    Args:
        paper_trading_engine: Optional paper trading engine
        explainable_ensemble: Optional explainable ensemble
        sentiment_enhancer: Optional sentiment enhancer

    Returns:
        ConversationalAgent ready to chat
    """
    return ConversationalAgent(
        paper_trading_engine=paper_trading_engine,
        explainable_ensemble=explainable_ensemble,
        sentiment_enhancer=sentiment_enhancer
    )
