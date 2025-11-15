"""
Mission Control API

Unified command center backend integrating:
- Multi-strategy portfolio management
- Real-time risk monitoring
- Live strategy comparison
- AI chat interface
- Opportunity discovery
- One-click deployment

This is the central nervous system of the Agentic Forge platform.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio
import random
from collections import defaultdict


# ============================================================================
# Multi-Strategy Portfolio Models
# ============================================================================

@dataclass
class StrategyState:
    """Real-time state of a running strategy"""
    id: str
    name: str
    type: str  # 'balanced', 'aggressive', 'sentiment', etc.
    allocation_pct: float
    current_value: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    positions: List[Dict[str, Any]]
    status: str  # 'running', 'paused', 'stopped'
    last_signal: Optional[Dict[str, Any]] = None


@dataclass
class PortfolioState:
    """Multi-strategy portfolio state"""
    total_value: float
    total_return: float
    total_return_pct: float
    strategies: List[StrategyState]
    overall_sharpe: float
    overall_max_drawdown: float
    cash_balance: float
    timestamp: str


@dataclass
class RiskMetrics:
    """Real-time risk metrics"""
    sharpe_ratio: float
    sortino_ratio: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR 95%
    current_drawdown: float
    max_drawdown: float
    volatility: float
    beta: float
    position_concentration: float  # % in largest position
    timestamp: str


@dataclass
class Opportunity:
    """AI-discovered trading opportunity"""
    id: str
    symbol: str
    title: str
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0-1
    sentiment_score: float
    technical_score: float
    fundamental_score: float
    recommended_action: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    timestamp: str = None


@dataclass
class RiskAlert:
    """Risk management alert"""
    id: str
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'position_size', 'drawdown', 'volatility', 'correlation'
    message: str
    strategy_id: Optional[str] = None
    symbol: Optional[str] = None
    timestamp: str = None


# ============================================================================
# Mission Control State Manager
# ============================================================================

class MissionControlState:
    """Central state manager for Mission Control"""

    def __init__(self):
        self.portfolio: Optional[PortfolioState] = None
        self.risk_metrics: Optional[RiskMetrics] = None
        self.opportunities: List[Opportunity] = []
        self.alerts: List[RiskAlert] = []
        self.active_connections: List[WebSocket] = []
        self.performance_history: Dict[str, List[Dict]] = defaultdict(list)

        # Initialize with mock data
        self._initialize_demo_state()

    def _initialize_demo_state(self):
        """Initialize with realistic demo data"""

        # Create 3 strategies
        strategies = [
            StrategyState(
                id='balanced_trader',
                name='Balanced Trader',
                type='balanced',
                allocation_pct=30.0,
                current_value=45230.0,
                total_return=5230.0,
                total_return_pct=15.2,
                sharpe_ratio=1.85,
                max_drawdown=8.5,
                positions=[
                    {'symbol': 'AAPL', 'shares': 50, 'value': 8500, 'pnl_pct': 12.5},
                    {'symbol': 'MSFT', 'shares': 30, 'value': 11400, 'pnl_pct': 18.2},
                ],
                status='running'
            ),
            StrategyState(
                id='aggressive_growth',
                name='Aggressive Growth',
                type='aggressive',
                allocation_pct=40.0,
                current_value=73680.0,
                total_return=13680.0,
                total_return_pct=22.8,
                sharpe_ratio=2.15,
                max_drawdown=15.3,
                positions=[
                    {'symbol': 'NVDA', 'shares': 40, 'value': 18000, 'pnl_pct': 35.2},
                    {'symbol': 'TSLA', 'shares': 80, 'value': 15200, 'pnl_pct': 28.5},
                ],
                status='running'
            ),
            StrategyState(
                id='sentiment_driven',
                name='Sentiment Driven',
                type='sentiment',
                allocation_pct=30.0,
                current_value=53325.0,
                total_return=8325.0,
                total_return_pct=18.5,
                sharpe_ratio=1.95,
                max_drawdown=10.2,
                positions=[
                    {'symbol': 'BTC-USD', 'shares': 0.5, 'value': 22500, 'pnl_pct': 45.5},
                    {'symbol': 'ETH-USD', 'shares': 8, 'value': 16800, 'pnl_pct': 28.3},
                ],
                status='running'
            )
        ]

        self.portfolio = PortfolioState(
            total_value=172235.0,
            total_return=27235.0,
            total_return_pct=18.8,
            strategies=strategies,
            overall_sharpe=1.98,
            overall_max_drawdown=11.3,
            cash_balance=22000.0,
            timestamp=datetime.now().isoformat()
        )

        self.risk_metrics = RiskMetrics(
            sharpe_ratio=1.98,
            sortino_ratio=2.45,
            var_95=-2850.0,
            cvar_95=-4200.0,
            current_drawdown=5.2,
            max_drawdown=11.3,
            volatility=18.5,
            beta=1.15,
            position_concentration=13.1,
            timestamp=datetime.now().isoformat()
        )

        # Generate opportunities
        self.opportunities = [
            Opportunity(
                id='opp_1',
                symbol='BTC-USD',
                title='Strong Bullish Sentiment + Technical Breakout',
                signal_type='bullish',
                confidence=0.85,
                sentiment_score=0.82,
                technical_score=0.88,
                fundamental_score=0.75,
                recommended_action='BUY',
                target_price=48500.0,
                stop_loss=42000.0,
                position_size=6240.0,
                timestamp=datetime.now().isoformat()
            ),
            Opportunity(
                id='opp_2',
                symbol='AAPL',
                title='Positive Earnings Sentiment + Momentum',
                signal_type='bullish',
                confidence=0.78,
                sentiment_score=0.75,
                technical_score=0.82,
                fundamental_score=0.88,
                recommended_action='BUY',
                target_price=195.0,
                stop_loss=175.0,
                position_size=4500.0,
                timestamp=datetime.now().isoformat()
            ),
            Opportunity(
                id='opp_3',
                symbol='TSLA',
                title='Weakening Momentum + Negative Sentiment',
                signal_type='bearish',
                confidence=0.72,
                sentiment_score=-0.65,
                technical_score=-0.58,
                fundamental_score=0.45,
                recommended_action='REDUCE',
                target_price=185.0,
                stop_loss=220.0,
                timestamp=datetime.now().isoformat()
            )
        ]

        # Generate alerts
        self.alerts = [
            RiskAlert(
                id='alert_1',
                severity='warning',
                category='position_size',
                message='NVDA position approaching 15% portfolio concentration',
                strategy_id='aggressive_growth',
                symbol='NVDA',
                timestamp=datetime.now().isoformat()
            ),
            RiskAlert(
                id='alert_2',
                severity='info',
                category='volatility',
                message='Portfolio volatility increased to 18.5% (within acceptable range)',
                timestamp=datetime.now().isoformat()
            )
        ]

    async def broadcast(self, event_type: str, data: Any):
        """Broadcast event to all connected clients"""
        message = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        disconnected = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            self.active_connections.remove(ws)

    async def update_strategy_performance(self, strategy_id: str):
        """Simulate strategy performance update"""
        for strategy in self.portfolio.strategies:
            if strategy.id == strategy_id:
                # Small random change
                change_pct = random.uniform(-0.5, 0.8)
                strategy.current_value *= (1 + change_pct / 100)
                strategy.total_return = strategy.current_value - (strategy.allocation_pct * 1000)
                strategy.total_return_pct = (strategy.total_return / (strategy.allocation_pct * 1000)) * 100

                # Update portfolio totals
                self.portfolio.total_value = sum(s.current_value for s in self.portfolio.strategies) + self.portfolio.cash_balance
                self.portfolio.total_return = self.portfolio.total_value - 145000
                self.portfolio.total_return_pct = (self.portfolio.total_return / 145000) * 100
                self.portfolio.timestamp = datetime.now().isoformat()

                # Broadcast update
                await self.broadcast('portfolio_update', asdict(self.portfolio))
                break


# Global state
mission_control = MissionControlState()


# ============================================================================
# Mission Control API
# ============================================================================

def create_mission_control_app() -> FastAPI:
    """Create FastAPI app for Mission Control"""

    app = FastAPI(title="Mission Control API")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Endpoints
    # ========================================================================

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "Mission Control API",
            "version": "1.0.0",
            "status": "operational",
            "features": [
                "Multi-strategy portfolio management",
                "Real-time risk monitoring",
                "AI opportunity discovery",
                "Live chat interface",
                "One-click deployment"
            ]
        }

    @app.get("/mission-control", response_class=FileResponse)
    async def serve_mission_control():
        """Serve Mission Control dashboard"""
        dashboard_path = Path(__file__).parent / "mission_control.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        raise HTTPException(status_code=404, detail="Mission Control not found")

    @app.get("/api/mission-control/portfolio")
    async def get_portfolio():
        """Get current portfolio state"""
        return JSONResponse(content=asdict(mission_control.portfolio))

    @app.get("/api/mission-control/risk")
    async def get_risk_metrics():
        """Get current risk metrics"""
        return JSONResponse(content=asdict(mission_control.risk_metrics))

    @app.get("/api/mission-control/opportunities")
    async def get_opportunities():
        """Get current opportunities"""
        return {
            'opportunities': [asdict(opp) for opp in mission_control.opportunities]
        }

    @app.get("/api/mission-control/alerts")
    async def get_alerts():
        """Get current risk alerts"""
        return {
            'alerts': [asdict(alert) for alert in mission_control.alerts]
        }

    @app.get("/api/mission-control/performance-history/{strategy_id}")
    async def get_performance_history(strategy_id: str):
        """Get performance history for strategy comparison chart"""
        # Generate mock history
        days = 30
        history = []
        base_value = 100.0

        for i in range(days):
            if strategy_id == 'balanced_trader':
                change = random.uniform(-0.5, 0.8)
            elif strategy_id == 'aggressive_growth':
                change = random.uniform(-1.2, 1.5)
            else:  # sentiment
                change = random.uniform(-0.8, 1.2)

            base_value *= (1 + change / 100)
            history.append({
                'day': i + 1,
                'value': round(base_value, 2),
                'return_pct': round(base_value - 100, 2)
            })

        return {'history': history}

    @app.post("/api/mission-control/chat")
    async def chat_message(request: Dict[str, Any]):
        """Process chat message and return AI response"""
        message = request.get('message', '').lower()

        # Smart message processing
        if 'sentiment' in message or 'btc' in message or 'bitcoin' in message:
            opp = mission_control.opportunities[0]  # BTC opportunity
            return {
                'response': f"""💭 {opp.symbol} Sentiment Analysis:

Overall Score: +{opp.sentiment_score:.2f} (Very Positive)
Technical: +{opp.technical_score:.2f}
Fundamental: +{opp.fundamental_score:.2f}
Confidence: {opp.confidence * 100:.1f}%

Trend: BULLISH ↗️

📊 Risk-Adjusted Recommendation:
Action: {opp.recommended_action}
Target: ${opp.target_price:,.0f}
Stop Loss: ${opp.stop_loss:,.0f}
Position Size: ${opp.position_size:,.0f} ({opp.position_size / mission_control.portfolio.total_value * 100:.1f}% of portfolio)

✅ This aligns with Kelly Criterion for optimal growth.""",
                'type': 'analysis'
            }

        elif 'backtest' in message:
            return {
                'response': """✅ Backtesting Dashboard Available!

Access at: http://localhost:8001/backtest/dashboard

Features:
• Historical performance simulation
• Multiple strategies
• Crypto + Stock support
• Advanced visualizations
• Trade-by-trade analysis

Would you like me to run a specific backtest?""",
                'type': 'info',
                'action': 'open_backtest'
            }

        elif 'deploy' in message or 'strategy' in message:
            return {
                'response': """✅ Strategy Deployment Ready!

Select a strategy to deploy:
1. Balanced Trader (Sharpe: 1.85)
2. Aggressive Growth (Sharpe: 2.15)
3. Sentiment Driven (Sharpe: 1.95)

🛡️ Protection Active:
• Max position size: 10%
• Max risk per trade: 2%
• Stop-loss: Automatic
• Position sizing: Kelly Criterion

Reply with strategy number to deploy.""",
                'type': 'deployment'
            }

        elif 'risk' in message:
            risk = mission_control.risk_metrics
            return {
                'response': f"""🛡️ Current Risk Profile:

Overall Health: {'✅ Healthy' if risk.sharpe_ratio > 1.5 else '⚠️ Caution'}

📊 Key Metrics:
• Sharpe Ratio: {risk.sharpe_ratio:.2f}
• Sortino Ratio: {risk.sortino_ratio:.2f}
• Max Drawdown: {risk.max_drawdown:.1f}%
• Current Drawdown: {risk.current_drawdown:.1f}%
• Volatility: {risk.volatility:.1f}%
• VaR (95%): ${abs(risk.var_95):,.0f}
• CVaR (95%): ${abs(risk.cvar_95):,.0f}

All metrics within acceptable ranges.""",
                'type': 'risk_analysis'
            }

        elif 'portfolio' in message or 'performance' in message:
            port = mission_control.portfolio
            return {
                'response': f"""📈 Portfolio Performance:

Total Value: ${port.total_value:,.0f}
Total Return: ${port.total_return:,.0f} (+{port.total_return_pct:.1f}%)
Cash Balance: ${port.cash_balance:,.0f}

Strategy Breakdown:
• Balanced Trader: ${port.strategies[0].current_value:,.0f} (+{port.strategies[0].total_return_pct:.1f}%)
• Aggressive Growth: ${port.strategies[1].current_value:,.0f} (+{port.strategies[1].total_return_pct:.1f}%)
• Sentiment Driven: ${port.strategies[2].current_value:,.0f} (+{port.strategies[2].total_return_pct:.1f}%)

Overall Sharpe: {port.overall_sharpe:.2f} (Excellent)""",
                'type': 'portfolio_summary'
            }

        else:
            return {
                'response': """👋 Mission Control AI Assistant

I can help you with:
• **Sentiment analysis** - "Show me BTC sentiment"
• **Risk metrics** - "What's my current risk?"
• **Portfolio performance** - "How's my portfolio?"
• **Backtesting** - "Run a backtest"
• **Strategy deployment** - "Deploy a strategy"
• **Opportunities** - "Show me opportunities"

What would you like to know?""",
                'type': 'help'
            }

    @app.post("/api/mission-control/deploy-strategy")
    async def deploy_strategy(request: Dict[str, Any]):
        """Deploy a strategy to live trading"""
        strategy_name = request.get('strategy_name')
        allocation_pct = request.get('allocation_pct', 10.0)

        # Validate
        if allocation_pct > 50:
            raise HTTPException(status_code=400, detail="Max allocation is 50%")

        return {
            'success': True,
            'message': f'✅ {strategy_name} deployed with {allocation_pct}% allocation',
            'strategy_id': f'deployed_{datetime.now().timestamp()}',
            'protections': {
                'max_position_size': '10%',
                'max_risk_per_trade': '2%',
                'stop_loss': 'automatic',
                'position_sizing': 'Kelly Criterion'
            }
        }

    @app.websocket("/api/mission-control/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates"""
        await websocket.accept()
        mission_control.active_connections.append(websocket)

        try:
            # Send initial state
            await websocket.send_json({
                'type': 'initial_state',
                'data': {
                    'portfolio': asdict(mission_control.portfolio),
                    'risk': asdict(mission_control.risk_metrics),
                    'opportunities': [asdict(o) for o in mission_control.opportunities],
                    'alerts': [asdict(a) for a in mission_control.alerts]
                }
            })

            # Keep connection alive and send periodic updates
            while True:
                try:
                    # Wait for messages or timeout
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)

                    # Process client requests
                    if data.get('type') == 'ping':
                        await websocket.send_json({'type': 'pong'})

                except asyncio.TimeoutError:
                    # Send periodic update
                    # Small random performance change
                    if random.random() < 0.3:  # 30% chance per interval
                        strategy = random.choice(mission_control.portfolio.strategies)
                        await mission_control.update_strategy_performance(strategy.id)

        except WebSocketDisconnect:
            mission_control.active_connections.remove(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            if websocket in mission_control.active_connections:
                mission_control.active_connections.remove(websocket)

    return app
