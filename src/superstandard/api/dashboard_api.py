"""
Conversational Trading Dashboard API

FastAPI backend providing real-time data and WebSocket connections
for the revolutionary conversational trading dashboard.

Features:
- Real-time portfolio updates via WebSocket
- Live sentiment streaming
- Conversational chat interface
- Decision explanation endpoints
- Trade execution monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import asyncio
import uuid


# ============================================================================
# Dashboard Models
# ============================================================================

class EventType(str, Enum):
    """Types of dashboard events"""
    PORTFOLIO_UPDATE = "portfolio_update"
    TRADE_EXECUTED = "trade_executed"
    SENTIMENT_UPDATE = "sentiment_update"
    DECISION_MADE = "decision_made"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_STATUS = "system_status"


@dataclass
class DashboardEvent:
    """Event for real-time dashboard updates"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'event_id': self.event_id
        }


@dataclass
class PortfolioSnapshot:
    """Portfolio state snapshot"""
    total_value: float
    cash: float
    positions_value: float
    total_return: float
    total_return_pct: float
    positions: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_value': self.total_value,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'positions': self.positions,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SentimentSnapshot:
    """Sentiment state snapshot"""
    symbol: str
    overall_score: float
    overall_label: str
    trend: str
    news_score: Optional[float] = None
    twitter_score: Optional[float] = None
    reddit_score: Optional[float] = None
    keywords: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'overall_score': self.overall_score,
            'overall_label': self.overall_label,
            'trend': self.trend,
            'news_score': self.news_score,
            'twitter_score': self.twitter_score,
            'reddit_score': self.reddit_score,
            'keywords': self.keywords,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Set[WebSocket] = set()
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_count += 1
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, event: DashboardEvent):
        """Broadcast event to all connected clients"""
        if not self.active_connections:
            return

        message = json.dumps(event.to_dict())
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, event: DashboardEvent):
        """Send event to specific client"""
        try:
            await websocket.send_text(json.dumps(event.to_dict()))
        except Exception as e:
            print(f"Error sending to client: {e}")
            self.disconnect(websocket)


# ============================================================================
# Dashboard State
# ============================================================================

class DashboardState:
    """Central state management for dashboard"""

    def __init__(self):
        """Initialize dashboard state"""
        # Components (injected)
        self.conversational_agent = None
        self.paper_trading_engine = None
        self.sentiment_enhancer = None
        self.explainable_ensemble = None

        # State
        self.portfolio: Optional[PortfolioSnapshot] = None
        self.sentiment_cache: Dict[str, SentimentSnapshot] = {}
        self.recent_decisions: List[Dict[str, Any]] = []
        self.recent_trades: List[Dict[str, Any]] = []
        self.chat_history: List[Dict[str, Any]] = []

        # WebSocket manager
        self.connection_manager = ConnectionManager()

        # Event history (last 100 events)
        self.event_history: List[DashboardEvent] = []
        self.max_history = 100

    def set_components(
        self,
        conversational_agent=None,
        paper_trading_engine=None,
        sentiment_enhancer=None,
        explainable_ensemble=None
    ):
        """Inject components"""
        if conversational_agent:
            self.conversational_agent = conversational_agent
        if paper_trading_engine:
            self.paper_trading_engine = paper_trading_engine
        if sentiment_enhancer:
            self.sentiment_enhancer = sentiment_enhancer
        if explainable_ensemble:
            self.explainable_ensemble = explainable_ensemble

    async def broadcast_event(self, event: DashboardEvent):
        """Broadcast event to all clients and store in history"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Broadcast to clients
        await self.connection_manager.broadcast(event)

    async def update_portfolio(self):
        """Update portfolio snapshot and broadcast"""
        if not self.paper_trading_engine:
            return

        try:
            # Get portfolio data
            summary = self.paper_trading_engine.get_portfolio_summary()
            positions = self.paper_trading_engine.get_positions()

            # Create snapshot
            self.portfolio = PortfolioSnapshot(
                total_value=summary.get('total_value', 0.0),
                cash=summary.get('cash', 0.0),
                positions_value=summary.get('positions_value', 0.0),
                total_return=summary.get('total_return_dollars', 0.0),
                total_return_pct=summary.get('total_return', 0.0),
                positions=positions
            )

            # Broadcast update
            event = DashboardEvent(
                event_type=EventType.PORTFOLIO_UPDATE,
                data=self.portfolio.to_dict()
            )
            await self.broadcast_event(event)

        except Exception as e:
            print(f"Error updating portfolio: {e}")

    async def update_sentiment(self, symbol: str):
        """Update sentiment for symbol and broadcast"""
        if not self.sentiment_enhancer:
            return

        try:
            # Get sentiment
            market_data = {}
            enhanced = self.sentiment_enhancer.enhance(symbol, market_data)

            # Create snapshot
            sentiment = SentimentSnapshot(
                symbol=symbol,
                overall_score=enhanced.get('overall_sentiment', 0.0),
                overall_label=self._sentiment_label(enhanced.get('overall_sentiment', 0.0)),
                trend=enhanced.get('sentiment_trend', 'neutral'),
                news_score=enhanced.get('news_sentiment'),
                twitter_score=enhanced.get('twitter_sentiment'),
                reddit_score=enhanced.get('reddit_sentiment'),
                keywords=enhanced.get('trending_keywords', [])
            )

            # Cache it
            self.sentiment_cache[symbol] = sentiment

            # Broadcast update
            event = DashboardEvent(
                event_type=EventType.SENTIMENT_UPDATE,
                data=sentiment.to_dict()
            )
            await self.broadcast_event(event)

        except Exception as e:
            print(f"Error updating sentiment: {e}")

    async def process_chat_message(self, message: str) -> str:
        """Process chat message and broadcast"""
        if not self.conversational_agent:
            return "Conversational agent not configured."

        try:
            # Process message
            response = self.conversational_agent.chat(message)

            # Store in history
            chat_entry = {
                'user_message': message,
                'agent_response': response,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.chat_history.append(chat_entry)

            # Broadcast
            event = DashboardEvent(
                event_type=EventType.CHAT_MESSAGE,
                data=chat_entry
            )
            await self.broadcast_event(event)

            return response

        except Exception as e:
            print(f"Error processing chat: {e}")
            return f"Error: {str(e)}"

    async def record_trade(self, trade_data: Dict[str, Any]):
        """Record trade execution and broadcast"""
        self.recent_trades.append(trade_data)
        if len(self.recent_trades) > 50:
            self.recent_trades.pop(0)

        event = DashboardEvent(
            event_type=EventType.TRADE_EXECUTED,
            data=trade_data
        )
        await self.broadcast_event(event)

        # Update portfolio after trade
        await self.update_portfolio()

    async def record_decision(self, decision_data: Dict[str, Any]):
        """Record decision and broadcast"""
        self.recent_decisions.append(decision_data)
        if len(self.recent_decisions) > 50:
            self.recent_decisions.pop(0)

        event = DashboardEvent(
            event_type=EventType.DECISION_MADE,
            data=decision_data
        )
        await self.broadcast_event(event)

    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.5:
            return "Very Positive"
        elif score > 0.2:
            return "Positive"
        elif score > -0.2:
            return "Neutral"
        elif score > -0.5:
            return "Negative"
        else:
            return "Very Negative"


# ============================================================================
# FastAPI Application
# ============================================================================

# Global dashboard state
dashboard_state = DashboardState()


def create_dashboard_app(
    conversational_agent=None,
    paper_trading_engine=None,
    sentiment_enhancer=None,
    explainable_ensemble=None
) -> FastAPI:
    """
    Create FastAPI application for dashboard

    Args:
        conversational_agent: ConversationalAgent instance
        paper_trading_engine: PaperTradingEngine instance
        sentiment_enhancer: SentimentEnhancedData instance
        explainable_ensemble: ExplainableAgentEnsemble instance

    Returns:
        FastAPI application
    """
    app = FastAPI(title="Conversational Trading Dashboard API")

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set components
    dashboard_state.set_components(
        conversational_agent=conversational_agent,
        paper_trading_engine=paper_trading_engine,
        sentiment_enhancer=sentiment_enhancer,
        explainable_ensemble=explainable_ensemble
    )

    # ========================================================================
    # WebSocket Endpoints
    # ========================================================================

    @app.websocket("/ws/dashboard")
    async def websocket_dashboard(websocket: WebSocket):
        """Main dashboard WebSocket for real-time updates"""
        await dashboard_state.connection_manager.connect(websocket)

        try:
            # Send initial state
            if dashboard_state.portfolio:
                await dashboard_state.connection_manager.send_to(
                    websocket,
                    DashboardEvent(
                        event_type=EventType.PORTFOLIO_UPDATE,
                        data=dashboard_state.portfolio.to_dict()
                    )
                )

            # Listen for client messages (for chat)
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get('type') == 'chat':
                    # Process chat message
                    response = await dashboard_state.process_chat_message(
                        message_data.get('message', '')
                    )

        except WebSocketDisconnect:
            dashboard_state.connection_manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            dashboard_state.connection_manager.disconnect(websocket)

    # ========================================================================
    # REST API Endpoints
    # ========================================================================

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "Conversational Trading Dashboard API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/api/portfolio")
    async def get_portfolio():
        """Get current portfolio snapshot"""
        if not dashboard_state.portfolio:
            await dashboard_state.update_portfolio()

        if dashboard_state.portfolio:
            return dashboard_state.portfolio.to_dict()

        return {"error": "Portfolio not available"}

    @app.get("/api/sentiment/{symbol}")
    async def get_sentiment(symbol: str):
        """Get sentiment for symbol"""
        # Check cache first
        if symbol in dashboard_state.sentiment_cache:
            return dashboard_state.sentiment_cache[symbol].to_dict()

        # Update and return
        await dashboard_state.update_sentiment(symbol)

        if symbol in dashboard_state.sentiment_cache:
            return dashboard_state.sentiment_cache[symbol].to_dict()

        return {"error": f"Sentiment not available for {symbol}"}

    @app.post("/api/chat")
    async def chat(message: dict):
        """Process chat message"""
        user_message = message.get('message', '')

        if not user_message:
            raise HTTPException(status_code=400, detail="Message required")

        response = await dashboard_state.process_chat_message(user_message)

        return {
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    @app.get("/api/decisions")
    async def get_decisions(limit: int = 10):
        """Get recent decisions"""
        return {
            'decisions': dashboard_state.recent_decisions[-limit:],
            'count': len(dashboard_state.recent_decisions)
        }

    @app.get("/api/trades")
    async def get_trades(limit: int = 10):
        """Get recent trades"""
        return {
            'trades': dashboard_state.recent_trades[-limit:],
            'count': len(dashboard_state.recent_trades)
        }

    @app.get("/api/chat/history")
    async def get_chat_history(limit: int = 20):
        """Get chat history"""
        return {
            'history': dashboard_state.chat_history[-limit:],
            'count': len(dashboard_state.chat_history)
        }

    @app.get("/api/status")
    async def get_status():
        """Get system status"""
        return {
            'connections': len(dashboard_state.connection_manager.active_connections),
            'portfolio_loaded': dashboard_state.portfolio is not None,
            'conversational_agent': dashboard_state.conversational_agent is not None,
            'paper_trading': dashboard_state.paper_trading_engine is not None,
            'sentiment': dashboard_state.sentiment_enhancer is not None,
            'explainable_ai': dashboard_state.explainable_ensemble is not None,
            'timestamp': datetime.utcnow().isoformat()
        }

    @app.post("/api/portfolio/refresh")
    async def refresh_portfolio():
        """Manually refresh portfolio"""
        await dashboard_state.update_portfolio()
        return {"status": "refreshed"}

    @app.post("/api/sentiment/refresh/{symbol}")
    async def refresh_sentiment(symbol: str):
        """Manually refresh sentiment for symbol"""
        await dashboard_state.update_sentiment(symbol)
        return {"status": "refreshed", "symbol": symbol}

    return app


# ============================================================================
# Utility Functions
# ============================================================================

def get_dashboard_state() -> DashboardState:
    """Get global dashboard state"""
    return dashboard_state
